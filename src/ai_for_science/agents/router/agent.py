"""Router 에이전트 — Critic 평가 결과를 분석하여 pass/revise/rewrite/hold/escalate 판단"""

import json
from datetime import datetime

from ai_for_science.config import settings
from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticIssue,
    IssueType,
    RouterAction,
    RouterActionType,
    RouterDecision,
    RoutingResult,
    Severity,
)
from ai_for_science.schemas.models import AgentMessage, AgentType


class RouterAgent(BaseAgent):
    """Critic 평가 결과를 분석하여 다음 액션을 결정하는 에이전트

    판단 기준:
      - score ≥ 90 + HIGH 이슈 없음 → PASS
      - score 75~89, 경미한 이슈만 → REVISE
      - score 60~74 또는 구조적 문제 → REWRITE
      - 공식 출처 부족 또는 최신 문서 미반영 → HOLD
      - 최신 대표 문서와 직접 충돌 → ESCALATE
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            name="Router Agent",
            description="Critic 평가를 분석하여 게시/수정/재작성/보류 여부를 판단합니다.",
        )

    async def process(self, input_data: dict) -> AgentMessage:
        evaluation_data = input_data.get("evaluation", {})
        evaluation = CriticEvaluation(**evaluation_data)
        result = self.route(evaluation)
        return AgentMessage(
            sender=self.agent_type,
            content=json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
            metadata={"decision": result.decision.value},
        )

    def route(self, evaluation: CriticEvaluation) -> RoutingResult:
        """Critic 평가 결과를 분석하여 라우팅 결정"""
        score = evaluation.score
        issues = evaluation.issues

        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        medium_issues = [i for i in issues if i.severity == Severity.MEDIUM]

        # ── 규칙 기반 판단 ─────────────────────────────

        # 1) ESCALATE: 최신 대표 문서와 직접 충돌
        has_critical_outdated = any(
            i.type == IssueType.OUTDATED and i.severity == Severity.HIGH
            for i in issues
        )
        has_critical_inconsistency = any(
            i.type == IssueType.INCONSISTENCY and i.severity == Severity.HIGH
            for i in issues
        )
        if has_critical_outdated or has_critical_inconsistency:
            return self._build_result(
                evaluation, RouterDecision.ESCALATE,
                "최신 대표 문서와 충돌하는 고위험 이슈가 발견되었습니다. 사람 검토가 필요합니다.",
                Severity.HIGH, "human_review",
            )

        # 2) HOLD: 공식 출처 부족 (HIGH evidence_gap)
        has_evidence_gap_high = any(
            i.type == IssueType.EVIDENCE_GAP and i.severity == Severity.HIGH
            for i in issues
        )
        if has_evidence_gap_high:
            return self._build_result(
                evaluation, RouterDecision.HOLD,
                "공식 출처가 부족합니다. 근거자료를 확보한 후 재작성이 필요합니다.",
                Severity.HIGH, "human_review",
            )

        # 3) PASS: 고득점 + 고위험 이슈 없음
        if score >= 90 and not high_issues:
            return self._build_result(
                evaluation, RouterDecision.PASS,
                "근거 기반 검증 통과. 게시 가능합니다.",
                Severity.LOW, "publish",
            )

        # 4) REWRITE: 구조적 오류 또는 핵심 누락
        has_missing_high = any(
            i.type == IssueType.MISSING and i.severity == Severity.HIGH
            for i in issues
        )
        if score < 60 or has_missing_high or len(high_issues) >= 2:
            return self._build_result(
                evaluation, RouterDecision.REWRITE,
                "구조적 문제 또는 핵심 내용 누락이 있어 재작성이 필요합니다.",
                Severity.HIGH, "reviser",
            )

        # 5) REVISE: 경미한 수정
        if score >= 75:
            return self._build_result(
                evaluation, RouterDecision.REVISE,
                "경미한 수정이 필요합니다. 자동 수정 후 재검증합니다.",
                Severity.MEDIUM, "reviser",
            )

        # 6) REWRITE: 그 외 60~74점 구간
        return self._build_result(
            evaluation, RouterDecision.REWRITE,
            "중대한 수정이 필요합니다.",
            Severity.HIGH, "reviser",
        )

    def _build_result(
        self,
        evaluation: CriticEvaluation,
        decision: RouterDecision,
        reason: str,
        priority: Severity,
        send_to: str,
    ) -> RoutingResult:
        """라우팅 결과 생성"""
        actions = self._derive_actions(evaluation.issues, decision)
        return RoutingResult(
            routing_id=f"route_{evaluation.evaluation_id}",
            evaluation_id=evaluation.evaluation_id,
            decision=decision,
            reason=reason,
            priority=priority,
            required_actions=actions,
            send_to=send_to,
        )

    def _derive_actions(
        self, issues: list[CriticIssue], decision: RouterDecision
    ) -> list[RouterAction]:
        """이슈 목록에서 구체적 조치 항목을 도출"""
        actions = []
        for issue in issues:
            if issue.severity == Severity.LOW and decision == RouterDecision.PASS:
                continue

            action_type = self._issue_to_action(issue.type, issue.severity, decision)
            actions.append(RouterAction(
                section=issue.target_section,
                action=action_type,
                reason=issue.reason,
            ))
        return actions

    def _issue_to_action(
        self, issue_type: IssueType, severity: Severity, decision: RouterDecision
    ) -> RouterActionType:
        """이슈 유형을 조치 유형으로 매핑"""
        if decision == RouterDecision.REWRITE:
            return RouterActionType.REWRITE

        mapping = {
            IssueType.EVIDENCE_GAP: RouterActionType.ADD_EVIDENCE,
            IssueType.OUTDATED: RouterActionType.EDIT,
            IssueType.OVERCLAIM: RouterActionType.EDIT,
            IssueType.MISSING: RouterActionType.ADD_MISSING,
            IssueType.INCONSISTENCY: RouterActionType.REWRITE,
            IssueType.IMBALANCE: RouterActionType.EDIT,
            IssueType.SOURCE_UNCLEAR: RouterActionType.EDIT,
        }
        return mapping.get(issue_type, RouterActionType.EDIT)

    def save_routing(self, result: RoutingResult):
        """라우팅 결과를 파일로 저장"""
        out_dir = settings.OUTPUTS_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{result.routing_id}.json"
        path.write_text(
            json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
