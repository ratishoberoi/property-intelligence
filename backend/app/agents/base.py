from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
T = TypeVar("T")


class AgentContext(BaseModel):
    request_id: str
    applicant_id: str | None = None
    property_id: str | None = None
    query: str | None = None
    limit: int = 5


class AgentResult(BaseModel, Generic[T]):
    agent_name: str
    ok: bool
    latency_ms: float
    output: T | None = None
    errors: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    context: AgentContext
    matching_result: Any | None = None
    applicant_result: Any | None = None
    rag_result: Any | None = None
    action_result: Any | None = None
    final_response: Any | None = None
    errors: list[str] = Field(default_factory=list)


class BaseAgent(Generic[T]):
    name = "base_agent"
    timeout_seconds = 6.0

    async def run(self, context: AgentContext) -> AgentResult[T]:
        start = time.perf_counter()
        try:
            output = await asyncio.wait_for(self._run(context), timeout=self.timeout_seconds)
            return AgentResult(agent_name=self.name, ok=True, latency_ms=(time.perf_counter() - start) * 1000, output=output)
        except Exception as exc:
            logger.exception("Agent failed", extra={"extra": {"agent": self.name, "error": str(exc)}})
            return AgentResult(agent_name=self.name, ok=False, latency_ms=(time.perf_counter() - start) * 1000, errors=[str(exc)])

    async def _run(self, context: AgentContext) -> T:
        raise NotImplementedError

