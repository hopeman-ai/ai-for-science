"""Reviser 에이전트 — Critic 피드백을 반영하여 콘텐츠를 자동 수정"""

import json
import re
from datetime import datetime

from ai_for_science.config import settings
from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.evaluation.evidence import EvidenceStore
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticIssue,
    IssueType,
    RevisionItem,
    RevisionResult,
    Severity,
)
from ai_for_science.schemas.models import AgentMessage, AgentType


# 자동 수정 가능한 과도한 단정 표현 → 완화 표현 매핑
SOFTENING_MAP = {
    "전략이 없다": "독립 전략이 별도로 마련되지 않은 상황이다",
    "전략 부재": "독립 전략이 아직 수립되지 않은 상태",
    "완전히 부재": "아직 충분히 마련되지 않은 상태",
    "전혀 없다": "아직 구체화되지 않은 상태이다",
    "절대적으로": "상당 부분",
    "압도적": "상대적으로 높은",
}


class ReviserAgent(BaseAgent):
    """Critic 평가 결과를 반영하여 콘텐츠를 수정하는 에이전트

    자동 수정 범위:
      - overclaim: 과도한 단정 표현 완화
      - source_unclear: 출처 불명확 표현 플래깅
      - imbalance: 불균형 경고 메모 추가
      - outdated: 과거 연도 참조에 주석 추가

    자동 수정 불가 (escalate):
      - evidence_gap (HIGH): 근거 자체가 없는 경우
      - inconsistency: 데이터 간 불일치
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            name="Reviser Agent",
            description="Critic 피드백을 반영하여 정책 콘텐츠를 자동 수정합니다.",
        )
        self.evidence_store = EvidenceStore()

    async def process(self, input_data: dict) -> AgentMessage:
        """Critic 평가와 원본 콘텐츠를 받아 수정 결과 반환"""
        evaluation_data = input_data.get("evaluation", {})
        content = input_data.get("content", {})

        evaluation = CriticEvaluation(**evaluation_data)
        result = self.revise(evaluation, content)

        return AgentMessage(
            sender=self.agent_type,
            content=json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
            metadata={
                "revision_id": result.revision_id,
                "items_count": len(result.items),
            },
        )

    def revise(self, evaluation: CriticEvaluation, content: dict) -> RevisionResult:
        """Critic 평가의 이슈를 순회하며 자동 수정 가능한 항목을 처리"""
        items: list[RevisionItem] = []

        for issue in evaluation.issues:
            revision = self._try_fix(issue, content)
            if revision:
                items.append(revision)

        needs_re_eval = len(items) > 0
        return RevisionResult(
            revision_id=f"rev_{evaluation.evaluation_id}_{datetime.now().strftime('%H%M%S')}",
            evaluation_id=evaluation.evaluation_id,
            items=items,
            summary=self._build_summary(items, evaluation),
            requires_re_evaluation=needs_re_eval,
        )

    def _try_fix(self, issue: CriticIssue, content: dict) -> RevisionItem | None:
        """이슈 유형별 자동 수정 시도"""
        if issue.type == IssueType.OVERCLAIM:
            return self._fix_overclaim(issue, content)
        if issue.type == IssueType.SOURCE_UNCLEAR:
            return self._fix_source_unclear(issue, content)
        if issue.type == IssueType.OUTDATED and issue.severity != Severity.HIGH:
            return self._fix_outdated(issue, content)
        if issue.type == IssueType.IMBALANCE and issue.severity == Severity.LOW:
            return self._flag_imbalance(issue)
        # HIGH evidence_gap, inconsistency 등은 자동 수정 불가
        return None

    def _fix_overclaim(self, issue: CriticIssue, content: dict) -> RevisionItem | None:
        """과도한 단정 표현을 완화"""
        original = issue.problem_text

        # 직접 매핑 우선
        for pattern, replacement in SOFTENING_MAP.items():
            if pattern in original:
                return RevisionItem(
                    target_section=issue.target_section,
                    original_text=original,
                    revised_text=original.replace(pattern, replacement),
                    revision_reason=f"단정 표현 완화: '{pattern}' → '{replacement}'",
                    issue_type=IssueType.OVERCLAIM,
                )

        # 일반적 완화 처리
        revised = original
        softeners = [
            (r"반드시\s*(.*?)\s*해야\s*한다", r"\1할 필요가 있다"),
            (r"유일하게", "주요하게"),
            (r"가장\s+뛰어나", "상대적으로 앞선"),
        ]
        for pat, repl in softeners:
            revised = re.sub(pat, repl, revised)

        if revised != original:
            return RevisionItem(
                target_section=issue.target_section,
                original_text=original,
                revised_text=revised,
                revision_reason="과도한 단정 표현을 근거 기반 표현으로 완화",
                issue_type=IssueType.OVERCLAIM,
            )
        return None

    def _fix_source_unclear(self, issue: CriticIssue, content: dict) -> RevisionItem | None:
        """출처 불명확 표현에 주석 추가"""
        original = issue.problem_text
        return RevisionItem(
            target_section=issue.target_section,
            original_text=original,
            revised_text=f"{original} [출처 확인 필요]",
            revision_reason="출처가 불명확한 표현에 검토 플래그 추가",
            issue_type=IssueType.SOURCE_UNCLEAR,
        )

    def _fix_outdated(self, issue: CriticIssue, content: dict) -> RevisionItem | None:
        """과거 연도 참조에 최신 자료 갱신 주석 추가"""
        original = issue.problem_text
        return RevisionItem(
            target_section=issue.target_section,
            original_text=original,
            revised_text=f"{original} [최신 자료 기준으로 갱신 검토 필요]",
            revision_reason="과거 자료 참조를 최신 자료 기준으로 갱신 권고",
            issue_type=IssueType.OUTDATED,
        )

    def _flag_imbalance(self, issue: CriticIssue) -> RevisionItem:
        """불균형 경고 메모"""
        return RevisionItem(
            target_section=issue.target_section,
            original_text=issue.problem_text,
            revised_text=f"{issue.problem_text} [비교 균형 조정 필요]",
            revision_reason="국가 간 비교 설명 분량의 균형 조정 권고",
            issue_type=IssueType.IMBALANCE,
        )

    def apply_revisions(self, content: dict, result: RevisionResult) -> dict:
        """수정 결과를 실제 콘텐츠에 적용 (in-place 아닌 복사본 반환)"""
        import copy
        revised = copy.deepcopy(content)
        text = json.dumps(revised, ensure_ascii=False)

        for item in result.items:
            if item.original_text in text:
                text = text.replace(item.original_text, item.revised_text, 1)

        return json.loads(text)

    def save_revision(self, result: RevisionResult):
        """수정 결과를 파일로 저장"""
        out_dir = settings.OUTPUTS_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{result.revision_id}.json"
        path.write_text(
            json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def _build_summary(self, items: list[RevisionItem], evaluation: CriticEvaluation) -> str:
        total = len(evaluation.issues)
        fixed = len(items)
        remaining = total - fixed
        types = {}
        for item in items:
            types[item.issue_type.value] = types.get(item.issue_type.value, 0) + 1
        type_str = ", ".join(f"{k}: {v}건" for k, v in types.items())
        return (
            f"전체 이슈 {total}건 중 {fixed}건 자동 수정 완료, "
            f"{remaining}건 수동 검토 필요. "
            f"수정 유형: {type_str or '없음'}"
        )
