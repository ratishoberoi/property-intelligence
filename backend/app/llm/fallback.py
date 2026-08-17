from app.llm.base import LLMProvider, LLMRequest


class DeterministicFallbackProvider(LLMProvider):
    name = "deterministic_fallback"

    async def generate(self, request: LLMRequest) -> str:
        if not request.citations:
            return "The available structured data supports the recommendation, but no retrieval evidence was found."
        evidence = "; ".join(f"{c.source}: {c.excerpt}" for c in request.citations[:3])
        return f"Based on retrieved evidence, {request.prompt.strip()} Evidence: {evidence}"

