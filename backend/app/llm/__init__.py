from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.fallback import DeterministicFallbackProvider
from app.llm.ollama import OllamaProvider
from app.llm.openai_compatible import OpenAICompatibleProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    if settings.llm_provider == "openai_compatible" and settings.openai_base_url:
        return OpenAICompatibleProvider(settings)
    return DeterministicFallbackProvider()

