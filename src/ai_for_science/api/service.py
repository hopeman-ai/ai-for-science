from ai_for_science.agents import (
    AnalysisAgent,
    InsightAgent,
    OrchestratorAgent,
    ReferenceAgent,
    ResearchAgent,
)
from ai_for_science.schemas.models import ServiceResponse, UserQuery


class AgentService:
    """멀티 에이전트 시스템을 관리하는 서비스 레이어"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.agents = {
            "research": ResearchAgent(),
            "analysis": AnalysisAgent(),
            "insight": InsightAgent(),
            "reference": ReferenceAgent(),
        }

    async def process_query(self, query: UserQuery) -> ServiceResponse:
        """사용자 질의를 멀티 에이전트 파이프라인으로 처리"""
        result = await self.orchestrator.route_and_aggregate(query, self.agents)

        return ServiceResponse(
            answer=result.get("answer", ""),
            comparisons=result.get("comparisons", []),
            references=result.get("references", []),
            insights=result.get("insights", []),
        )
