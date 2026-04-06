import json

from ai_for_science.config import settings
from ai_for_science.core.agent_base import BaseAgent
from ai_for_science.schemas.models import AgentMessage, AgentType, Reference


class ReferenceAgent(BaseAgent):
    """레퍼런스 문서를 관리하고 출처 정보를 제공하는 에이전트"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.REFERENCE,
            name="Reference Agent",
            description="참고 문서의 출처를 관리하고, 신뢰성 있는 레퍼런스 정보와 링크를 제공합니다.",
        )
        self.references = self._load_references()

    def _load_references(self) -> list[dict]:
        """레퍼런스 데이터 로드"""
        ref_path = settings.DATA_DIR / "references" / "sources.json"
        if ref_path.exists():
            return json.loads(ref_path.read_text(encoding="utf-8"))
        return []

    async def process(self, input_data: dict) -> AgentMessage:
        query = input_data.get("query", "")
        countries = input_data.get("countries")

        relevant_refs = self._find_relevant_references(query, countries)

        system_prompt = self._load_prompt("reference_system")
        refs_text = json.dumps(
            [r.model_dump() for r in relevant_refs],
            ensure_ascii=False,
            indent=2,
        )

        content = await self.llm.chat_with_system(
            system_prompt,
            f"질문: {query}\n\n관련 레퍼런스:\n{refs_text}",
        )

        return AgentMessage(
            sender=self.agent_type,
            content=content,
            references=relevant_refs,
        )

    def _find_relevant_references(
        self, query: str, countries: list[str] | None
    ) -> list[Reference]:
        """질의와 관련된 레퍼런스 검색"""
        if not self.references:
            return self._get_default_references()

        results = []
        for ref_data in self.references:
            if countries and ref_data.get("country") not in countries:
                continue
            results.append(Reference(**ref_data))

        return results if results else self._get_default_references()

    def _get_default_references(self) -> list[Reference]:
        """기본 레퍼런스 목록"""
        return [
            Reference(
                title="AI for Science 推進について",
                source="文部科学省",
                url="https://www.mext.go.jp/b_menu/shingi/chousa/shinkou/073/siryo/mext_00002.html",
                country="japan",
                description="일본의 AI for Science 추진 전략 및 연구 시스템 혁신 방안",
            ),
            Reference(
                title="National AI Research Resource (NAIRR) Task Force Final Report",
                source="NSF",
                url="https://www.ai.gov/nairrtf/",
                country="usa",
                description="미국 국가 AI 연구 자원(NAIRR) 태스크포스 최종 보고서",
            ),
            Reference(
                title="European Strategy for AI in Science",
                source="European Commission",
                url="https://research-and-innovation.ec.europa.eu/strategy/support-policy-making/scientific-support-eu-policies/european-strategy-ai-science_en",
                country="eu",
                description="유럽의 AI for Science 전략 및 RAISE 프로젝트",
            ),
            Reference(
                title="AI Continent Action Plan",
                source="European Commission",
                url="https://digital-strategy.ec.europa.eu/en/library/ai-continent-action-plan",
                country="eu",
                description="유럽 AI 대륙 행동 계획",
            ),
            Reference(
                title="국무원 'AI+' 행동방안",
                source="中国国务院",
                url="https://www.gov.cn/zhengce/content/202307/content_6893556.htm",
                country="china",
                description="중국 AI+ 행동방안 및 산업 혁신 플랫폼 전략",
            ),
        ]
