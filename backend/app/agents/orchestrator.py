from __future__ import annotations

import asyncio
import logging
from sqlalchemy.orm import Session
from app.agents.action_agent import NextBestActionAgent
from app.agents.applicant_agent import ApplicantIntelligenceAgent
from app.agents.base import AgentContext, AgentState
from app.agents.intent_agent import RAGAgent
from app.agents.property_agent import PropertyMatchingAgent
from app.llm import get_llm_provider
from app.llm.base import LLMRequest
from app.schemas.intelligence import ApplicantIntelligenceResponse
from app.services.applicant_service import ApplicantService

logger = logging.getLogger(__name__)


class IntelligenceOrchestrator:
    """Coordinates independent agents and aggregates a typed final intelligence response."""

    def __init__(self, db: Session):
        self.db = db

    async def run(self, context: AgentContext) -> AgentState:
        state = AgentState(context=context)
        matching_agent = PropertyMatchingAgent(self.db)
        applicant_agent = ApplicantIntelligenceAgent(self.db)
        rag_agent = RAGAgent(self.db)
        matching_result, applicant_result, rag_result = await asyncio.gather(
            matching_agent.run(context), applicant_agent.run(context), rag_agent.run(context)
        )
        state.matching_result = matching_result.output if matching_result.ok else []
        state.applicant_result = applicant_result.output if applicant_result.ok else None
        state.rag_result = rag_result.output if rag_result.ok else []
        state.errors.extend(matching_result.errors + applicant_result.errors + rag_result.errors)
        if state.applicant_result:
            action_result = await NextBestActionAgent(self.db, state.matching_result, state.applicant_result).run(context)
            state.action_result = action_result.output
            state.errors.extend(action_result.errors)
        state.final_response = await self._aggregate(state)
        logger.info(
            "Intelligence request completed",
            extra={
                "extra": {
                    "applicant_id": context.applicant_id,
                    "property_id": context.property_id,
                    "agents_called": ["matching", "applicant", "rag", "action"],
                    "retrieval_count": len(state.rag_result or []),
                    "final_action": getattr(state.action_result, "action", None),
                    "errors": state.errors,
                }
            },
        )
        return state

    async def _aggregate(self, state: AgentState):
        if not state.context.applicant_id:
            return None
        applicant = ApplicantService(self.db).get(state.context.applicant_id)
        if not applicant or not state.applicant_result:
            return None
        prompt = self._prompt(state)
        try:
            explanation = await get_llm_provider().generate(LLMRequest(prompt=prompt, citations=state.rag_result or []))
        except Exception:
            explanation = self._deterministic_explanation(state)
        return ApplicantIntelligenceResponse(
            applicant=applicant,
            top_matches=state.matching_result or [],
            intent=state.applicant_result["intent"],
            conversion=state.applicant_result["conversion"],
            key_signals=state.applicant_result["intent"].key_signals + state.applicant_result["conversion"].top_positive_factors,
            recommended_action=state.action_result,
            explanation=explanation,
            sources=state.rag_result or [],
        )

    def _prompt(self, state: AgentState) -> str:
        action = getattr(state.action_result, "action", "recommend next action")
        top = state.matching_result[0] if state.matching_result else None
        prop_text = f"Top match is {top.property.property_id} at {top.match_score}%." if top else "No strong property match."
        return (
            f"Explain why the estate agent should choose action {action}. "
            f"{prop_text} Ground the explanation in applicant history and property evidence."
        )

    def _deterministic_explanation(self, state: AgentState) -> str:
        action = getattr(state.action_result, "action", "WAIT")
        signals = "; ".join(state.applicant_result["intent"].key_signals[:2]) if state.applicant_result else "Limited evidence."
        return f"Recommended action is {action} because {signals}"

