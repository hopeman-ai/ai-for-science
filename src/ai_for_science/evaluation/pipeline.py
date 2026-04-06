"""평가 파이프라인 — Critic → Router → Reviser → Critic 재검증 흐름 관리

워크플로우:
  1. Critic이 콘텐츠를 근거자료 기반으로 평가
  2. Router가 평가 결과를 분석하여 분기 결정
     - PASS    → 게시 가능
     - REVISE  → Reviser가 경미한 수정 후 재검증
     - REWRITE → Reviser가 구조적 수정 후 재검증
     - HOLD    → 근거 부족, 게시 보류
     - ESCALATE → 사람 검토 필요
  3. Reviser 수정 후 Critic 재평가 (최대 max_iterations)
  4. 2회 이상 실패 시 human_review로 전환
"""

import json
from dataclasses import dataclass, field
from datetime import datetime

from ai_for_science.agents.critic.agent import CriticAgent
from ai_for_science.agents.router.agent import RouterAgent
from ai_for_science.agents.reviser.agent import ReviserAgent
from ai_for_science.config import settings
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticVerdict,
    RouterDecision,
    RevisionResult,
    RoutingResult,
)


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    initial_evaluation: CriticEvaluation | None = None
    routing: RoutingResult | None = None
    revision: RevisionResult | None = None
    final_evaluation: CriticEvaluation | None = None
    route: str = ""        # "publish" | "revised" | "rewrite" | "hold" | "escalate" | "human_review"
    iterations: int = 0

    def to_dict(self) -> dict:
        return {
            "route": self.route,
            "iterations": self.iterations,
            "initial_score": self.initial_evaluation.score if self.initial_evaluation else 0,
            "final_score": self.final_evaluation.score if self.final_evaluation else 0,
            "initial_verdict": self.initial_evaluation.verdict.value if self.initial_evaluation else "",
            "final_verdict": self.final_evaluation.verdict.value if self.final_evaluation else "",
            "router_decision": self.routing.decision.value if self.routing else "",
            "revision_items": len(self.revision.items) if self.revision else 0,
            "issues_total": len(self.final_evaluation.issues) if self.final_evaluation else 0,
        }


class EvaluationPipeline:
    """Critic → Router → Reviser → Critic 재검증 파이프라인"""

    def __init__(self, max_iterations: int = 2):
        self.critic = CriticAgent()
        self.router = RouterAgent()
        self.reviser = ReviserAgent()
        self.max_iterations = max_iterations

    def run_section(self, section: str, content: dict) -> PipelineResult:
        """단일 섹션 평가-라우팅-수정 파이프라인 실행"""
        result = PipelineResult()

        # ── 1. Critic 평가 ────────────────────────────
        evaluation = self.critic.evaluate_section(section, content)
        result.initial_evaluation = evaluation
        result.iterations = 1

        # ── 2. Router 판단 ────────────────────────────
        routing = self.router.route(evaluation)
        result.routing = routing

        # ── 3. 분기 처리 ─────────────────────────────
        if routing.decision == RouterDecision.PASS:
            result.final_evaluation = evaluation
            result.route = "publish"
            return result

        if routing.decision == RouterDecision.ESCALATE:
            result.final_evaluation = evaluation
            result.route = "escalate"
            return result

        if routing.decision == RouterDecision.HOLD:
            result.final_evaluation = evaluation
            result.route = "hold"
            return result

        # ── 4. REVISE / REWRITE → Reviser → 재검증 ──
        current_content = content
        current_eval = evaluation

        for i in range(self.max_iterations):
            # Reviser 수정
            revision = self.reviser.revise(current_eval, current_content)
            result.revision = revision

            if not revision.items:
                break

            # 수정 적용
            current_content = self.reviser.apply_revisions(current_content, revision)

            # Critic 재평가
            current_eval = self.critic.evaluate_section(section, current_content)
            result.iterations += 1

            # Router 재판단
            re_routing = self.router.route(current_eval)

            if re_routing.decision == RouterDecision.PASS:
                result.routing = re_routing
                break

        result.final_evaluation = current_eval

        # 2회 이상 실패 시 human_review
        if result.iterations > self.max_iterations and current_eval.verdict != CriticVerdict.PASS:
            result.route = "human_review"
        elif current_eval.verdict == CriticVerdict.PASS:
            result.route = "revised"
        else:
            result.route = routing.decision.value

        return result

    def run_all(self, strategies: dict, platform: dict) -> dict:
        """전체 서비스 콘텐츠 파이프라인 실행"""
        results = {}

        # 국가별 전략 평가
        countries = strategies.get("countries", {})
        for code, data in countries.items():
            section = f"countries.{code}"
            results[section] = self.run_section(section, data)

        # 비교표 평가
        comparisons = strategies.get("comparisons", {})
        for dim, data in comparisons.items():
            section = f"comparisons.{dim}"
            results[section] = self.run_section(section, data)

        # PEST 진단 평가
        pest = strategies.get("overview", {}).get("korea_pest", {})
        if pest:
            results["overview.korea_pest"] = self.run_section("overview.korea_pest", pest)

        # 실행 전략 평가
        execution = platform.get("execution_strategy", {})
        if execution:
            results["execution_strategy"] = self.run_section("execution_strategy", execution)

        # 인사이트 평가
        insights = platform.get("insights", {})
        if insights:
            results["insights"] = self.run_section("insights", insights)

        return results

    def save_results(self, results: dict[str, PipelineResult]):
        """전체 파이프라인 결과를 저장"""
        out_dir = settings.OUTPUTS_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)

        summary = {}
        for section, pr in results.items():
            summary[section] = pr.to_dict()
            if pr.final_evaluation:
                self.critic.save_evaluation(pr.final_evaluation)
            if pr.routing:
                self.router.save_routing(pr.routing)
            if pr.revision:
                self.reviser.save_revision(pr.revision)

        summary_path = out_dir / "pipeline_summary.json"
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return summary_path
