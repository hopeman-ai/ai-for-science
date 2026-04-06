"""Critic 에이전트 — 정책 콘텐츠의 사실 정확성·최신성·근거 충분성을 평가"""

import json
from datetime import datetime

from ai_for_science.config import settings
from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.evaluation.evidence import EvidenceStore
from ai_for_science.evaluation.rules import RuleEngine
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticVerdict,
    ContentStatus,
    ReviewStatus,
)
from ai_for_science.schemas.models import AgentMessage, AgentType


class CriticAgent(BaseAgent):
    """서비스 콘텐츠를 비평하고 품질을 평가하는 에이전트

    평가 기준:
      1. 사실 정확성        2. 공식 출처 기반 여부
      3. 최신성             4. 근거 충분성
      5. 사실/해석 구분     6. 국가 간 비교 균형성
      7. 과도한 단정 표현   8. 핵심 누락
      9. 표현 명확성        10. 공개 가능 수준
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,   # 기존 enum 재활용
            name="Critic Agent",
            description="정책 콘텐츠의 신뢰성, 최신성, 근거 충분성을 평가합니다.",
        )
        self.evidence_store = EvidenceStore()
        self.rule_engine = RuleEngine(self.evidence_store)

    async def process(self, input_data: dict) -> AgentMessage:
        """단일 섹션 또는 전체 평가 수행"""
        target = input_data.get("target", "all")
        content = input_data.get("content", {})

        if target == "all":
            evaluation = self.evaluate_all(content)
        else:
            evaluation = self.evaluate_section(target, content)

        return AgentMessage(
            sender=self.agent_type,
            content=json.dumps(evaluation.model_dump(), ensure_ascii=False, indent=2),
            metadata={"evaluation_id": evaluation.evaluation_id, "score": evaluation.score},
        )

    def evaluate_section(self, section: str, content: dict) -> CriticEvaluation:
        """단일 섹션 규칙 기반 평가"""
        return self.rule_engine.evaluate_section(section, content)

    def evaluate_all(self, data: dict) -> CriticEvaluation:
        """전체 서비스 콘텐츠 일괄 평가 (종합 점수)"""
        strategies = data.get("strategies", {})
        platform = data.get("platform", {})

        all_issues = []
        all_ev_checks = []
        all_fr_checks = []
        section_scores = []

        # 1) 국가별 전략 요약 평가
        countries = strategies.get("countries", {})
        for country_code, country_data in countries.items():
            section = f"countries.{country_code}"
            ev = self.rule_engine.evaluate_section(section, country_data)
            all_issues.extend(ev.issues)
            all_ev_checks.extend(ev.evidence_checks)
            all_fr_checks.extend(ev.freshness_checks)
            section_scores.append(ev.score)

        # 2) 비교표 평가
        comparisons = strategies.get("comparisons", {})
        for dim_code, dim_data in comparisons.items():
            section = f"comparisons.{dim_code}"
            ev = self.rule_engine.evaluate_section(section, dim_data)
            all_issues.extend(ev.issues)
            all_ev_checks.extend(ev.evidence_checks)
            all_fr_checks.extend(ev.freshness_checks)
            section_scores.append(ev.score)

        # 3) PEST 진단 평가
        pest = strategies.get("overview", {}).get("korea_pest", {})
        if pest:
            ev = self.rule_engine.evaluate_section("overview.korea_pest", pest)
            all_issues.extend(ev.issues)
            section_scores.append(ev.score)

        # 4) 실행 전략 평가
        execution = platform.get("execution_strategy", {})
        if execution:
            ev = self.rule_engine.evaluate_section("execution_strategy", execution)
            all_issues.extend(ev.issues)
            section_scores.append(ev.score)

        # 5) 인사이트 평가
        insights = platform.get("insights", {})
        if insights:
            ev = self.rule_engine.evaluate_section("insights", insights)
            all_issues.extend(ev.issues)
            section_scores.append(ev.score)

        # 종합 점수
        avg_score = round(sum(section_scores) / len(section_scores)) if section_scores else 0
        verdict = self.rule_engine._determine_verdict(avg_score, all_issues)

        return CriticEvaluation(
            evaluation_id=f"eval_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target="all",
            score=avg_score,
            verdict=verdict,
            summary=f"전체 평가 점수: {avg_score}/100 | {len(section_scores)}개 섹션 평가 | 이슈 {len(all_issues)}건",
            issues=all_issues,
            evidence_checks=all_ev_checks,
            freshness_checks=all_fr_checks,
            recommendation=self.rule_engine._build_recommendation(verdict, all_issues),
        )

    def get_content_status(self, evaluation: CriticEvaluation) -> ContentStatus:
        """평가 결과를 ContentStatus로 변환"""
        return ContentStatus(
            section=evaluation.target,
            status=self.rule_engine.score_to_status(evaluation.score, evaluation.verdict),
            last_critic_score=evaluation.score,
            last_evaluated_at=evaluation.evaluated_at,
            evaluation_history=[evaluation.evaluation_id],
        )

    def save_evaluation(self, evaluation: CriticEvaluation):
        """평가 결과를 파일로 저장"""
        out_dir = settings.OUTPUTS_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{evaluation.evaluation_id}.json"
        path.write_text(
            json.dumps(evaluation.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
