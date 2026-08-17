import httpx
from app.config import Settings
from app.llm.base import LLMProvider, LLMRequest


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: LLMRequest) -> str:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={"model": self.settings.ollama_model, "prompt": request.prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "")

