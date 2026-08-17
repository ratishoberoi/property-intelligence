import httpx
from app.config import Settings
from app.llm.base import LLMProvider, LLMRequest


class OpenAICompatibleProvider(LLMProvider):
    name = "openai_compatible"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: LLMRequest) -> str:
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"} if self.settings.openai_api_key else {}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.settings.openai_base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.settings.openai_model,
                    "messages": [{"role": "user", "content": request.prompt}],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

