import json

from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.models import (
    AgentMessage,
    AgentType,
    ComparisonDimension,
    ComparisonEntry,
)

DIMENSION_LABELS = {
    ComparisonDimension.STRATEGY_TYPE: "전략 유형",
    ComparisonDimension.CORE_OBJECTIVE: "핵심 목표",
    ComparisonDimension.INFRASTRUCTURE: "인프라 전략",
    ComparisonDimension.DATA_STRATEGY: "데이터 전략",
    ComparisonDimension.TALENT: "인재 전략",
    ComparisonDimension.INDUSTRY_LINKAGE: "산업 연계",
    ComparisonDimension.GOVERNANCE: "거버넌스",
    ComparisonDimension.INTERNATIONAL_COOPERATION: "국제 협력",
}


class AnalysisAgent(BaseAgent):
    """비교 항목 기반으로 국가별 AI for Science 전략을 비교 분석하는 에이전트"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ANALYSIS,
            name="Analysis Agent",
            description="정해진 비교 항목에 따라 국가별 전략을 체계적으로 비교 분석합니다.",
        )

    async def process(self, input_data: dict) -> AgentMessage:
        query = input_data.get("query", "")
        countries = input_data.get("countries")
        dimensions = input_data.get("dimensions")

        if not dimensions:
            dimensions = [d.value for d in ComparisonDimension]

        comparisons = await self._compare_strategies(query, countries, dimensions)
        summary = await self._generate_summary(query, comparisons)

        return AgentMessage(
            sender=self.agent_type,
            content=summary,
            comparisons=comparisons,
        )

    async def _compare_strategies(
        self,
        query: str,
        countries: list[str] | None,
        dimensions: list[str],
    ) -> list[ComparisonEntry]:
        """각 비교 항목별로 국가 전략 비교"""
        system_prompt = self._load_prompt("analysis_system")

        dimension_labels = {
            d: DIMENSION_LABELS.get(ComparisonDimension(d), d) for d in dimensions
        }

        user_message = (
            f"질문: {query}\n"
            f"비교 대상 국가: {countries or ['japan', 'china', 'usa', 'eu']}\n"
            f"비교 항목: {json.dumps(dimension_labels, ensure_ascii=False)}\n\n"
            "각 비교 항목별로 국가별 전략을 JSON 형식으로 비교 분석해주세요.\n"
            '응답 형식:\n[{{"dimension": "항목코드", "dimension_label": "항목명", '
            '"country_data": {{"japan": "...", "china": "...", "usa": "...", "eu": "..."}}}}]'
        )

        response = await self.llm.chat_with_system(system_prompt, user_message)

        try:
            parsed = json.loads(self._extract_json(response))
            return [ComparisonEntry(**entry) for entry in parsed]
        except (json.JSONDecodeError, ValueError):
            return self._get_default_comparisons(dimensions)

    async def _generate_summary(
        self, query: str, comparisons: list[ComparisonEntry]
    ) -> str:
        """비교 분석 결과 요약"""
        comparison_text = "\n".join(
            f"### {c.dimension_label}\n"
            + "\n".join(f"- **{k}**: {v}" for k, v in c.country_data.items())
            for c in comparisons
        )

        system_prompt = self._load_prompt("analysis_summary")
        return await self.llm.chat_with_system(
            system_prompt,
            f"질문: {query}\n\n비교 분석 결과:\n{comparison_text}",
        )

    def _extract_json(self, text: str) -> str:
        """응답에서 JSON 부분 추출"""
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()
        if "[" in text:
            start = text.index("[")
            end = text.rindex("]") + 1
            return text[start:end]
        return text

    def _get_default_comparisons(self, dimensions: list[str]) -> list[ComparisonEntry]:
        """기본 비교 데이터"""
        defaults = {
            "strategy_type": {
                "japan": "연구 시스템 혁신 - 과학 연구 시스템 자체를 AI 중심으로 재설계",
                "china": "산업 혁신 플랫폼 - AI for Science를 산업 혁신과 직접 연결",
                "usa": "AI 연구 인프라 - AI 연구 인프라 접근성 확대에 집중",
                "eu": "연구 네트워크 - 유럽 연구 생태계 통합 및 공동 활용",
            },
            "core_objective": {
                "japan": "연구생산성 및 연구시스템 병목 문제 해결",
                "china": "과학발견의 산업 적용 속도 문제 해결",
                "usa": "AI 컴퓨팅 자원의 불균형 문제 해결",
                "eu": "유럽 연구 시스템의 분산 문제 해결",
            },
            "infrastructure": {
                "japan": "AI 연구플랫폼 중심의 통합 인프라",
                "china": "AI + HPC(슈퍼컴퓨팅 네트워크) + 산업데이터",
                "usa": "NAIRR(국가 AI 연구 자원) 구축",
                "eu": "슈퍼컴퓨터, 연구장비, 데이터 센터 공동활용",
            },
        }

        return [
            ComparisonEntry(
                dimension=ComparisonDimension(d),
                dimension_label=DIMENSION_LABELS.get(ComparisonDimension(d), d),
                country_data=defaults.get(d, {}),
            )
            for d in dimensions
            if d in defaults
        ]
