import re
import time
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Feedback, Interaction, Property, Viewing
from app.db.session import SessionLocal
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.intelligence.intent.model import ApplicantIntentModel
from app.intelligence.lead_scoring.model import ConversionScorer
from app.intelligence.next_best_action.engine import NextBestActionEngine
from app.rag.retrieval import RetrievalService
from app.rag.answer import GroundedAnswerGenerator
from app.schemas.domain import SearchRequest
from app.schemas.intelligence import SearchResponse
from app.services.applicant_service import ApplicantService
from app.services.interaction_service import InteractionService
from app.config import get_settings

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_search_sync, request),
            timeout=get_settings().search_timeout_seconds,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail={"error_code": "SEARCH_TIMEOUT", "message": "Search exceeded the local timeout. Try a narrower question."}) from None
    except Exception as exc:
        logger.exception("Search request failed", extra={"extra": {"error": str(exc)}})
        raise HTTPException(status_code=500, detail={"error_code": "SEARCH_FAILED", "message": "Search could not be completed."}) from exc


def _search_sync(request: SearchRequest):
    db = SessionLocal()
    try:
        return _search_with_session(request, db)
    finally:
        db.close()


def _search_with_session(request: SearchRequest, db: Session):
    started = time.perf_counter()
    query = request.query.strip()
    applicant = _resolve_applicant(db, query, request.applicant_id)
    property_id = request.property_id or _extract_property_id(query)
    retriever = RetrievalService(db)
    citations = retriever.query(query, limit=request.limit, applicant_id=applicant.applicant_id if applicant else None, property_id=property_id)
    properties = []
    applicants: list[dict] = []
    normalized_query = query.lower()
    if "previously viewed" in normalized_query or "similar to sarah" in normalized_query:
        properties = _similar_to_viewed(db, request.limit)
        answer = f"Returned {len(properties)} properties similar to Sarah's previously viewed stock, ranked by her fit and budget."
    elif applicant and "objection" in normalized_query:
        objections = _applicant_objections(db, applicant.applicant_id)
        if objections:
            summary = ", ".join(f"{name.replace('_', ' ').lower()} ({count})" for name, count in objections[:3])
            answer = f"{applicant.name}'s main objections are {summary}. These are derived from recorded viewing feedback."
        else:
            answer = f"No recorded objections were found for {applicant.name}'s recent viewing feedback."
    elif applicant and ("high-value" in normalized_query or "high value" in normalized_query or "intent" in normalized_query):
        features = InteractionService(db).applicant_features(applicant.applicant_id)
        intent = ApplicantIntentModel().predict(features)
        matcher = PropertyMatchingEngine(db)
        properties = matcher.match(applicant, request.limit)
        average_match = sum(item.match_score for item in properties) / max(len(properties), 1)
        conversion = ConversionScorer().predict(features, average_match)
        answer = (
            f"{applicant.name} is a {intent.intent} intent applicant with a "
            f"{round(conversion.conversion_probability * 100)}% synthetic conversion estimate. "
            f"Key signals: {'; '.join(intent.key_signals[:2]) or 'recorded engagement activity.'}"
        )
    elif applicant:
        matcher = PropertyMatchingEngine(db)
        if property_id:
            prop = db.get(Property, property_id)
            properties = [matcher.score_property(applicant, prop)] if prop else []
        else:
            properties = matcher.match(applicant, request.limit)
        top = properties[0] if properties else None
        if top:
            positives = "; ".join(top.explanation.positives[:2])
            answer = f"{applicant.name} is a {top.match_score}% match for {top.property.property_id}: {positives}"
        else:
            answer = f"No property match was found for {applicant.name} under the requested constraints."
    elif "similar propert" in normalized_query or "under" in normalized_query and "£" in normalized_query:
        properties = _similar_properties(db, query, request.limit)
        answer = f"Returned {len(properties)} properties ranked by fit for the demo applicant and the requested rent constraint."
    elif "contact today" in normalized_query or "who should" in normalized_query and "contact" in normalized_query:
        applicants = _contact_today(db, request.limit)
        answer = f"Prioritized {len(applicants)} applicants using intent, conversion signals, recent activity and next-best-action policy."
    elif "high demand" in query.lower() and "low application" in query.lower():
        props = _high_demand_low_conversion(db, request.limit)
        answer = "These properties show relatively high demand signals but weaker application conversion."
        properties = props
    else:
        applicants = _candidate_applicants(db, query, request.limit)
        answer = "Returned applicants and evidence matching the query constraints."
    grounded = GroundedAnswerGenerator().generate(query, answer, citations, properties)
    retrieval = dict(retriever.last_metadata)
    retrieval["request_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
    retrieval["index_chunks"] = len(retriever._chunks or [])
    return SearchResponse(
        answer=grounded.answer,
        applicants=applicants,
        properties=properties,
        citations=citations,
        retrieval=retrieval,
        generation={"model": grounded.model, "grounded": True, "evidence": grounded.evidence, "inference": grounded.inference, "action": grounded.action},
    )


def _applicant_objections(db: Session, applicant_id: str) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for feedback in db.scalars(select(Feedback).where(Feedback.applicant_id == applicant_id)):
        for objection in (part.strip() for part in feedback.objections.split("|")):
            if objection:
                counts[objection] = counts.get(objection, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)


def _similar_properties(db: Session, query: str, limit: int):
    max_rent_match = re.search(r"under\s+£?(\d+)", query.lower())
    max_rent = int(max_rent_match.group(1)) if max_rent_match else None
    applicant = db.get(Applicant, "A-DEMO-SARAH")
    if not applicant:
        return []
    stmt = select(Property)
    if max_rent is not None:
        stmt = stmt.where(Property.rent_pcm <= max_rent)
    candidates = list(db.scalars(stmt.limit(500)))
    matcher = PropertyMatchingEngine(db)
    return sorted((matcher.score_property(applicant, prop) for prop in candidates), key=lambda match: match.match_score, reverse=True)[:limit]


def _contact_today(db: Session, limit: int) -> list[dict]:
    intent_model = ApplicantIntentModel()
    conversion_model = ConversionScorer()
    matcher = PropertyMatchingEngine(db)
    action_engine = NextBestActionEngine()
    interactions = list(db.scalars(select(Interaction)))
    feedback = list(db.scalars(select(Feedback)))
    viewings = list(db.scalars(select(Viewing)))
    by_applicant: dict[str, list] = defaultdict(list)
    feedback_by_applicant: dict[str, list] = defaultdict(list)
    viewings_by_applicant: dict[str, list] = defaultdict(list)
    for row in interactions:
        by_applicant[row.applicant_id].append(row)
    for row in feedback:
        feedback_by_applicant[row.applicant_id].append(row)
    for row in viewings:
        viewings_by_applicant[row.applicant_id].append(row)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ranked: list[tuple[float, dict]] = []
    for applicant in db.scalars(select(Applicant).limit(80)):
        rows = by_applicant[applicant.applicant_id]
        applicant_feedback = feedback_by_applicant[applicant.applicant_id]
        last_ts = max((row.timestamp for row in rows), default=now)
        response_events = sum(row.event_type in {"MESSAGE_RECEIVED", "FEEDBACK", "ENQUIRY"} for row in rows)
        outbound_events = sum(row.event_type in {"MESSAGE_SENT", "FOLLOW_UP"} for row in rows)
        features = {
            "number_of_interactions": float(len(rows)),
            "days_since_last_interaction": float(max((now - last_ts).days, 0)),
            "viewings": float(len(viewings_by_applicant[applicant.applicant_id])),
            "positive_feedback": float(sum(row.rating >= 4 or row.sentiment > 0.35 for row in applicant_feedback)),
            "negative_feedback": float(sum(row.rating <= 2 or row.sentiment < -0.25 for row in applicant_feedback)),
            "applications": float(sum(row.event_type in {"APPLICATION_STARTED", "APPLICATION_SUBMITTED"} for row in rows)),
            "messages": float(sum(row.event_type.startswith("MESSAGE") for row in rows)),
            "response_rate": float(response_events / max(outbound_events, 1)),
            "avg_days_between_interactions": 30.0,
            "cancellations": float(sum(row.event_type == "VIEWING_CANCELLED" for row in rows)),
            "no_response_events": float(sum(row.event_type == "NO_RESPONSE" for row in rows)),
        }
        intent = intent_model.predict(features)
        priority = intent.confidence + min(features["applications"], 2) * 0.2 + min(features["viewings"], 5) * 0.05
        ranked.append((priority, {"applicant": applicant, "features": features, "intent": intent}))
    ranked.sort(key=lambda row: row[0], reverse=True)
    results: list[tuple[float, dict]] = []
    for priority, item in ranked[:max(limit * 4, 12)]:
        applicant = item["applicant"]
        features = item["features"]
        intent = item["intent"]
        matches = matcher.match(applicant, 3)
        conversion = conversion_model.predict(features, sum(m.match_score for m in matches) / max(len(matches), 1))
        action = action_engine.recommend(intent, conversion, matches, [])
        results.append((priority + conversion.conversion_probability, {
            "applicant_id": applicant.applicant_id,
            "name": applicant.name,
            "intent": intent.intent,
            "conversion_probability": conversion.conversion_probability,
            "recommended_action": action.action,
            "reason": action.reason,
        }))
    return [item for _, item in sorted(results, key=lambda row: row[0], reverse=True)[:limit]]


def _similar_to_viewed(db: Session, limit: int):
    applicant = db.get(Applicant, "A-DEMO-SARAH")
    if not applicant:
        return []
    viewed_ids = list(db.scalars(
        select(Interaction.property_id)
        .where(Interaction.applicant_id == applicant.applicant_id)
        .where(Interaction.event_type.in_(["PROPERTY_VIEW", "VIEWING_BOOKED", "FEEDBACK"]))
        .where(Interaction.property_id.is_not(None))
        .limit(30)
    ))
    viewed = list(db.scalars(select(Property).where(Property.property_id.in_(viewed_ids))))
    areas = {prop.area for prop in viewed}
    bedrooms = {prop.bedrooms for prop in viewed}
    candidates = list(db.scalars(select(Property).where(Property.property_id.not_in(viewed_ids)).where(Property.area.in_(areas)).where(Property.bedrooms.in_(bedrooms)).limit(500)))
    matcher = PropertyMatchingEngine(db)
    return sorted((matcher.score_property(applicant, prop) for prop in candidates), key=lambda match: match.match_score, reverse=True)[:limit]


def _resolve_applicant(db: Session, query: str, applicant_id: str | None) -> Applicant | None:
    service = ApplicantService(db)
    if applicant_id:
        return service.get(applicant_id)
    for candidate in db.scalars(select(Applicant).limit(200)):
        first = candidate.name.split()[0].lower()
        full = candidate.name.lower()
        if full in query.lower() or first in query.lower():
            return candidate
    return None


def _extract_property_id(query: str) -> str | None:
    match = re.search(r"P-[A-Z0-9-]+|P\d+", query, flags=re.I)
    if not match:
        return None
    value = match.group(0).upper()
    return value if value.startswith("P-") else value.replace("P", "P-", 1)


def _candidate_applicants(db: Session, query: str, limit: int) -> list[dict]:
    max_rent_match = re.search(r"under\s+£?(\d+)", query.lower())
    bedrooms_match = re.search(r"(\d+)[-\s]?bed", query.lower())
    area_terms = ["Canary Wharf", "Stratford", "Greenwich", "Shoreditch", "Islington", "Camden", "Hackney", "Chelsea", "Fulham", "Wimbledon", "Croydon", "Battersea", "Clapham"]
    stmt = select(Applicant).limit(limit * 3)
    if max_rent_match:
        stmt = stmt.where(Applicant.budget_max <= int(max_rent_match.group(1)) + 250)
    if bedrooms_match:
        stmt = stmt.where(Applicant.bedrooms_required == int(bedrooms_match.group(1)))
    rows = list(db.scalars(stmt))
    selected = []
    for app in rows:
        if any(area.lower() in query.lower() and area in app.preferred_areas for area in area_terms) or not area_terms:
            selected.append({"applicant_id": app.applicant_id, "name": app.name, "budget_max": app.budget_max, "preferred_areas": app.preferred_areas})
    return selected[:limit] or [{"applicant_id": app.applicant_id, "name": app.name, "budget_max": app.budget_max, "preferred_areas": app.preferred_areas} for app in rows[:limit]]


def _high_demand_low_conversion(db: Session, limit: int):
    sarah = db.get(Applicant, "A-DEMO-SARAH") or db.scalars(select(Applicant).limit(1)).first()
    if not sarah:
        return []
    rows = db.execute(
        select(Interaction.property_id, Interaction.event_type, func.count())
        .where(Interaction.property_id.is_not(None))
        .group_by(Interaction.property_id, Interaction.event_type)
    ).all()
    by_property: dict[str, dict[str, int]] = {}
    for property_id, event_type, count in rows:
        by_property.setdefault(property_id, {})[event_type] = int(count)
    ranked_ids: list[tuple[str, float]] = []
    for property_id, counts in by_property.items():
        demand = counts.get("PROPERTY_VIEW", 0) + counts.get("VIEWING_BOOKED", 0) * 2
        applications = counts.get("APPLICATION_STARTED", 0) + counts.get("APPLICATION_SUBMITTED", 0)
        application_conversion = applications / max(demand, 1)
        if demand >= 5 and application_conversion <= 0.18:
            ranked_ids.append((property_id, demand * (1 - application_conversion)))
    ranked_ids.sort(key=lambda item: item[1], reverse=True)
    props = [db.get(Property, property_id) for property_id, _ in ranked_ids[: limit * 4]]
    props = [prop for prop in props if prop is not None]
    engine = PropertyMatchingEngine(db)
    return sorted([engine.score_property(sarah, p) for p in props], key=lambda m: m.match_score, reverse=True)[:limit]
