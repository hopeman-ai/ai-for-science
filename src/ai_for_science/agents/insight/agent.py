from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.models import AgentMessage, AgentType


class InsightAgent(BaseAgent):
    """비교 분석 결과를 바탕으로 전략적 시사점을 생성하는 에이전트"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.INSIGHT,
            name="Insight Agent",
            description="국가별 전략 비교 결과로부터 전략적 시사점과 한국에 대한 정책 제언을 생성합니다.",
        )

    async def process(self, input_data: dict) -> AgentMessage:
        query = input_data.get("query", "")
        countries = input_data.get("countries")
        dimensions = input_data.get("dimensions")

        system_prompt = self._load_prompt("insight_system")

        user_message = (
            f"질문: {query}\n"
            f"분석 대상 국가: {countries or ['japan', 'china', 'usa', 'eu']}\n"
            f"분석 항목: {dimensions or '전체'}\n\n"
            "위 국가들의 AI for Science 전략을 비교하여 다음을 도출해주세요:\n"
            "1. 각 국가 전략의 핵심 차별점\n"
            "2. 국가 간 공통점과 차이점에서 발견되는 패턴\n"
            "3. 한국에 대한 전략적 시사점 및 정책 제언\n"
            "4. 한국이 벤치마크할 수 있는 구체적 사례"
        )

        content = await self.llm.chat_with_system(system_prompt, user_message)

        return AgentMessage(
            sender=self.agent_type,
            content=content,
            metadata={"type": "insight"},
        )
