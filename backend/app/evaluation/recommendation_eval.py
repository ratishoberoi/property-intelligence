from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Applicant
from app.intelligence.intent.model import ApplicantIntentModel
from app.intelligence.lead_scoring.model import ConversionScorer
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.intelligence.next_best_action.engine import NextBestActionEngine
from app.services.applicant_service import ApplicantService
from app.services.interaction_service import InteractionService


def evaluate_next_best_action(db: Session) -> dict[str, float]:
    applicants = list(db.scalars(select(Applicant).limit(120)))
    agree = 0
    total = 0
    intent_model = ApplicantIntentModel()
    conversion_model = ConversionScorer()
    for applicant in applicants:
        features = InteractionService(db).applicant_features(applicant.applicant_id)
        matches = PropertyMatchingEngine(db).match(applicant, 5)
        avg = sum(m.match_score for m in matches) / max(len(matches), 1)
        intent = intent_model.predict(features)
        conversion = conversion_model.predict(features, avg)
        objections = []
        for fb in ApplicantService(db).feedback(applicant.applicant_id, 10):
            objections.extend([part for part in fb.objections.split("|") if part])
        predicted = NextBestActionEngine().recommend(intent, conversion, matches, objections).action
        expected = synthetic_policy(intent.intent, conversion.conversion_probability, objections)
        agree += int(predicted == expected)
        total += 1
    return {"policy_agreement": round(agree / max(total, 1), 4), "evaluated_applicants": total}


def synthetic_policy(intent: str, conversion: float, objections: list[str]) -> str:
    if "PRICE" in objections:
        return "RECOMMEND_LOWER_PRICE_OPTIONS"
    if conversion >= 0.62 and intent in {"HIGH", "VERY_HIGH"} and "TERMS" in objections:
        return "SEND_APPLICATION_LINK"
    if "TRANSPORT" in objections:
        return "SEND_SIMILAR_PROPERTIES"
    if intent in {"HIGH", "VERY_HIGH"} and conversion >= 0.45:
        return "SCHEDULE_VIEWING"
    if intent == "MEDIUM":
        return "FOLLOW_UP_NOW"
    return "REQUEST_MORE_INFORMATION"

