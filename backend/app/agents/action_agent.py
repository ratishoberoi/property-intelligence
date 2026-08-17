from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.intelligence.next_best_action.engine import NextBestActionEngine
from app.services.applicant_service import ApplicantService


class NextBestActionAgent(BaseAgent):
    name = "next_best_action_agent"

    def __init__(self, db: Session, matches, applicant_result):
        self.db = db
        self.matches = matches or []
        self.applicant_result = applicant_result or {}

    async def _run(self, context: AgentContext):
        objections: list[str] = []
        if context.applicant_id:
            for fb in ApplicantService(self.db).feedback(context.applicant_id, limit=10):
                objections.extend([part for part in fb.objections.split("|") if part])
        return NextBestActionEngine().recommend(
            intent=self.applicant_result["intent"],
            conversion=self.applicant_result["conversion"],
            matches=self.matches,
            recent_objections=objections,
        )

