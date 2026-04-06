from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.models import AgentMessage, AgentType, UserQuery


class OrchestratorAgent(BaseAgent):
    """사용자 질의를 분석하고 적절한 에이전트로 라우팅하는 오케스트레이터"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            name="Orchestrator Agent",
            description="사용자 질의를 분석하여 적절한 에이전트에 작업을 분배하고 결과를 통합합니다.",
        )

    async def process(self, input_data: dict) -> AgentMessage:
        query = input_data.get("query", "")
        routing = await self._analyze_query(query)
        return AgentMessage(
            sender=self.agent_type,
            content=routing,
            metadata={"routing_plan": routing},
        )

    async def _analyze_query(self, query: str) -> str:
        system_prompt = self._load_prompt("orchestrator_system")
        return await self.llm.chat_with_system(system_prompt, query)

    async def route_and_aggregate(
        self, query: UserQuery, agents: dict[str, BaseAgent]
    ) -> dict:
        """질의를 분석하고, 필요한 에이전트를 호출하여 결과를 통합"""
        routing_result = await self.process({"query": query.question})

        results = {}
        agent_keys = self._determine_agents(query)

        for key in agent_keys:
            if key in agents:
                result = await agents[key].process({
                    "query": query.question,
                    "countries": [c.value for c in query.countries] if query.countries else None,
                    "dimensions": [d.value for d in query.dimensions] if query.dimensions else None,
                })
                results[key] = result

        return await self._aggregate_results(query.question, results)

    def _determine_agents(self, query: UserQuery) -> list[str]:
        """질의 유형에 따라 호출할 에이전트 결정"""
        agents = ["research"]
        if query.dimensions or query.countries:
            agents.append("analysis")
        agents.append("insight")
        agents.append("reference")
        return agents

    async def _aggregate_results(
        self, query: str, results: dict[str, AgentMessage]
    ) -> dict:
        """여러 에이전트의 결과를 하나의 응답으로 통합"""
        combined_content = []
        all_references = []
        all_comparisons = []
        all_insights = []

        for agent_name, message in results.items():
            combined_content.append(f"[{agent_name}]\n{message.content}")
            all_references.extend(message.references)
            all_comparisons.extend(message.comparisons)

        system_prompt = self._load_prompt("orchestrator_aggregate")
        combined_text = "\n\n".join(combined_content)
        final_answer = await self.llm.chat_with_system(
            system_prompt,
            f"사용자 질문: {query}\n\n에이전트 결과:\n{combined_text}",
        )

        return {
            "answer": final_answer,
            "comparisons": all_comparisons,
            "references": all_references,
            "insights": all_insights,
        }
