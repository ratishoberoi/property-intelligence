from pathlib import Path
from sqlalchemy.orm import Session
from app.agents.base import AgentContext, BaseAgent
from app.config import get_settings
from app.intelligence.intent.model import ApplicantIntentModel
from app.intelligence.lead_scoring.model import ConversionScorer
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.services.applicant_service import ApplicantService
from app.services.interaction_service import InteractionService


class ApplicantIntelligenceAgent(BaseAgent):
    name = "applicant_intelligence_agent"

    def __init__(self, db: Session):
        self.db = db
        model_dir = get_settings().model_dir
        self.intent = ApplicantIntentModel(model_dir / "intent_model.joblib")
        self.conversion = ConversionScorer(model_dir / "conversion_model.joblib")

    async def _run(self, context: AgentContext):
        if not context.applicant_id:
            raise ValueError("Applicant id is required")
        applicant = ApplicantService(self.db).get(context.applicant_id)
        if not applicant:
            raise ValueError("Applicant not found")
        features = InteractionService(self.db).applicant_features(context.applicant_id)
        matches = PropertyMatchingEngine(self.db).match(applicant, 5)
        avg_match = sum(m.match_score for m in matches) / max(len(matches), 1)
        return {
            "intent": self.intent.predict(features),
            "conversion": self.conversion.predict(features, avg_match),
            "features": features,
        }

