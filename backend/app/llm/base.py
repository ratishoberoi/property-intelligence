from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.schemas.intelligence import Citation


class LLMRequest(BaseModel):
    prompt: str
    citations: list[Citation] = []


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, request: LLMRequest) -> str:
        raise NotImplementedError

