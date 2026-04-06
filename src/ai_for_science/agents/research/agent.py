import json

from ai_for_science.config import settings
from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.models import AgentMessage, AgentType, Reference


class ResearchAgent(BaseAgent):
    """국가별 AI for Science 전략 문서를 검색하고 정보를 추출하는 에이전트"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCH,
            name="Research Agent",
            description="국가별 전략 문서를 검색하고 핵심 정보를 추출합니다.",
        )
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> dict:
        """data/processed 디렉토리에서 정제된 국가전략 데이터 로드"""
        kb_path = settings.DATA_DIR / "processed" / "strategies.json"
        if kb_path.exists():
            return json.loads(kb_path.read_text(encoding="utf-8"))
        return {}

    async def process(self, input_data: dict) -> AgentMessage:
        query = input_data.get("query", "")
        countries = input_data.get("countries")

        context = self._retrieve_context(query, countries)

        system_prompt = self._load_prompt("research_system")
        user_message = f"질문: {query}\n\n참고 데이터:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        content = await self.llm.chat_with_system(system_prompt, user_message)
        references = self._get_references(countries)

        return AgentMessage(
            sender=self.agent_type,
            content=content,
            references=references,
        )

    def _retrieve_context(self, query: str, countries: list[str] | None) -> dict:
        """질의와 관련된 국가전략 컨텍스트 검색"""
        if not self.knowledge_base:
            return self._get_default_context()

        if countries:
            return {c: self.knowledge_base.get(c, {}) for c in countries}
        return self.knowledge_base

    def _get_references(self, countries: list[str] | None) -> list[Reference]:
        """참고문헌 목록 반환"""
        ref_path = settings.DATA_DIR / "references" / "sources.json"
        if not ref_path.exists():
            return []

        all_refs = json.loads(ref_path.read_text(encoding="utf-8"))

        references = []
        for ref_data in all_refs:
            if countries and ref_data.get("country") not in countries:
                continue
            references.append(Reference(**ref_data))
        return references

    def _get_default_context(self) -> dict:
        """기본 국가전략 비교 컨텍스트 (샘플 데이터)"""
        return {
            "japan": {
                "strategy_type": "연구 시스템 혁신",
                "key_features": [
                    "AI 기반 과학 혁신 전략",
                    "AI 기반 연구 자동화",
                    "과학 연구 시스템 자체를 AI 중심으로 재설계",
                ],
            },
            "china": {
                "strategy_type": "산업 혁신 플랫폼",
                "key_features": [
                    "국가 AI + 산업전환",
                    "AI for Science를 산업 혁신 플랫폼으로 사용",
                ],
            },
            "usa": {
                "strategy_type": "AI 연구 인프라",
                "key_features": [
                    "AI 연구 인프라 전략",
                    "NAIRR 구축으로 AI 컴퓨팅 자원 불균형 해소",
                ],
            },
            "eu": {
                "strategy_type": "연구 네트워크",
                "key_features": [
                    "연구 협력 네트워크 전략",
                    "유럽 연구 생태계 통합",
                ],
            },
        }
