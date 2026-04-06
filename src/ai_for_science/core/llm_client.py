from openai import OpenAI

from ai_for_science.config import settings


class LLMClient:
    """OpenAI ChatGPT LLM 클라이언트"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE

    async def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int = 2000,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def chat_with_system(
        self, system_prompt: str, user_message: str, **kwargs
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, **kwargs)


llm_client = LLMClient()
