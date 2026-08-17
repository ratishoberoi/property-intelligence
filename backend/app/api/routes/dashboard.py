from collections import Counter
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Interaction, Property, Viewing
from app.db.session import get_db
from app.intelligence.intent.model import ApplicantIntentModel
from app.intelligence.lead_scoring.model import ConversionScorer
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.intelligence.next_best_action.engine import NextBestActionEngine
from app.services.applicant_service import ApplicantService
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    applicants = int(db.scalar(select(func.count()).select_from(Applicant)) or 0)
    properties = int(db.scalar(select(func.count()).select_from(Property)) or 0)
    viewings = int(db.scalar(select(func.count()).select_from(Viewing)) or 0)
    applications = int(db.scalar(select(func.count()).select_from(Interaction).where(Interaction.event_type.in_(["APPLICATION_STARTED", "APPLICATION_SUBMITTED"]))) or 0)
    intent_model = ApplicantIntentModel()
    matcher = PropertyMatchingEngine(db)
    match_scores: list[float] = []
    high_intent = 0
    for idx, applicant in enumerate(db.scalars(select(Applicant))):
        intent = intent_model.predict(InteractionService(db).applicant_features(applicant.applicant_id))
        high_intent += int(intent.intent in {"HIGH", "VERY_HIGH"})
        if idx < 120:
            matches = matcher.match(applicant, 3)
            match_scores.extend(match.match_score for match in matches)
    return {
        "total_applicants": applicants,
        "active_applicants": min(applicants, high_intent + applications),
        "high_intent_applicants": high_intent,
        "properties": properties,
        "upcoming_viewings": viewings,
        "applications": applications,
        "average_match_score": round(sum(match_scores) / max(len(match_scores), 1), 1),
        "conversion_probability": round(applications / max(applicants, 1), 3),
        "demo_applicant_id": "A-DEMO-SARAH",
    }


@router.get("/trends")
def trends(db: Session = Depends(get_db)):
    events = Counter(row[0] for row in db.execute(select(Interaction.event_type)).all())
    funnel_order = ["ENQUIRY", "QUALIFIED", "VIEWING_BOOKED", "APPLICATION_STARTED", "OFFER_MADE"]
    intent_distribution = {"VERY_HIGH": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "DORMANT": 0}
    intent_model = ApplicantIntentModel()
    conversion_model = ConversionScorer()
    interaction_service = InteractionService(db)
    matcher = PropertyMatchingEngine(db)
    action_counts: Counter[str] = Counter()
    for applicant in db.scalars(select(Applicant).limit(120)):
        features = interaction_service.applicant_features(applicant.applicant_id)
        result = intent_model.predict(features)
        intent_distribution[result.intent] += 1
        matches = matcher.match(applicant, 5)
        avg_match = sum(match.match_score for match in matches) / max(len(matches), 1)
        conversion = conversion_model.predict(features, avg_match)
        objections: list[str] = []
        for feedback in ApplicantService(db).feedback(applicant.applicant_id, 10):
            objections.extend(part for part in feedback.objections.split("|") if part)
        action = NextBestActionEngine().recommend(result, conversion, matches, objections)
        action_counts[action.action] += 1
    return {
        "funnel": [{"stage": stage, "count": events.get(stage, 0)} for stage in funnel_order],
        "intent_distribution": [{"intent": k, "count": v} for k, v in intent_distribution.items()],
        "next_best_actions": [{"action": action, "count": count} for action, count in action_counts.most_common()],
        "conversion_trends": _conversion_trends(db),
    }


def _conversion_trends(db: Session) -> list[dict[str, float | str]]:
    latest = db.scalar(select(func.max(Interaction.timestamp))) or datetime(2026, 8, 13)
    start = latest - timedelta(weeks=5)
    rows = db.execute(
        select(Interaction.timestamp, Interaction.event_type).where(Interaction.timestamp >= start)
    ).all()
    buckets = [{"week": f"W-{5 - idx}", "views": 0, "applications": 0} for idx in range(5)]
    for timestamp, event_type in rows:
        idx = min(4, max(0, int((timestamp - start).days // 7)))
        if event_type in {"PROPERTY_VIEW", "VIEWING_BOOKED"}:
            buckets[idx]["views"] += 1
        if event_type in {"APPLICATION_STARTED", "APPLICATION_SUBMITTED"}:
            buckets[idx]["applications"] += 1
    return [
        {"week": str(bucket["week"]), "conversion": round(float(bucket["applications"]) / max(float(bucket["views"]), 1.0), 3)}
        for bucket in buckets
    ]
