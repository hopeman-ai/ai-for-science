from abc import ABC, abstractmethod

from ai_for_science.config import settings
from ai_for_science.core.llm_client import llm_client
from ai_for_science.schemas.models import AgentMessage, AgentType


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.llm = llm_client

    @abstractmethod
    async def process(self, input_data: dict) -> AgentMessage:
        """에이전트의 핵심 처리 로직"""
        pass

    def _load_prompt(self, prompt_name: str) -> str:
        """configs/prompts 디렉토리에서 프롬프트 템플릿 로드"""
        path = settings.PROMPTS_DIR / f"{prompt_name}.md"
        return path.read_text(encoding="utf-8")
