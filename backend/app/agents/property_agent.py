from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.services.applicant_service import ApplicantService


class PropertyMatchingAgent(BaseAgent):
    name = "property_matching_agent"

    def __init__(self, db: Session):
        self.db = db

    async def _run(self, context: AgentContext):
        if not context.applicant_id:
            return []
        applicant = ApplicantService(self.db).get(context.applicant_id)
        if not applicant:
            raise ValueError("Applicant not found")
        return PropertyMatchingEngine(self.db).match(applicant, context.limit)

