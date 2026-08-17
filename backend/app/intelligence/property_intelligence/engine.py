from collections import Counter
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Feedback, Interaction, Property
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.rag.retrieval import RetrievalService
from app.schemas.domain import split_pipe
from app.schemas.intelligence import PropertyIntelligenceResponse


class PropertyIntelligenceEngine:
    def __init__(self, db: Session):
        self.db = db
        self.matcher = PropertyMatchingEngine(db)

    def analyze(self, prop: Property) -> PropertyIntelligenceResponse:
        interactions = list(self.db.scalars(select(Interaction).where(Interaction.property_id == prop.property_id)))
        applicants = list(self.db.scalars(select(Applicant).limit(400)))
        matches = [self.matcher.score_property(applicant, prop) for applicant in applicants]
        strong = [m for m in matches if m.match_score >= 80]
        qualified = [m for m in matches if m.match_score >= 65]
        avg = round(sum(m.match_score for m in qualified) / max(len(qualified), 1), 1)
        counts = Counter(i.event_type for i in interactions)
        viewings = counts["VIEWING_BOOKED"] + counts["PROPERTY_VIEW"]
        applications = counts["APPLICATION_STARTED"] + counts["APPLICATION_SUBMITTED"]
        viewing_conversion = round(counts["VIEWING_BOOKED"] / max(counts["PROPERTY_VIEW"], 1), 3)
        application_conversion = round(applications / max(viewings, 1), 3)
        feedback = list(self.db.scalars(select(Feedback).where(Feedback.property_id == prop.property_id)))
        objections = Counter()
        for row in feedback:
            objections.update(split_pipe(row.objections))
        preferences = Counter()
        for applicant in applicants:
            if self.matcher.score_property(applicant, prop).match_score >= 65:
                preferences.update(split_pipe(applicant.amenities_preferences))
        demand_score = len(qualified) * 0.5 + counts["PROPERTY_VIEW"] * 0.8 + counts["VIEWING_BOOKED"] * 2
        demand = "HIGH" if demand_score >= 55 else "MEDIUM" if demand_score >= 25 else "LOW"
        segments = Counter(a.employment_type for a in applicants if self.matcher.score_property(a, prop).match_score >= 65)
        recommended = self._recommend(prop, demand, application_conversion, objections)
        top_applicants = sorted(
            [{"applicant_id": a.applicant_id, "name": a.name, "match_score": self.matcher.score_property(a, prop).match_score} for a in applicants],
            key=lambda item: item["match_score"],
            reverse=True,
        )[:8]
        return PropertyIntelligenceResponse(
            property=prop,
            demand=demand,
            qualified_applicants=len(qualified),
            strong_matches=len(strong),
            average_match_score=avg,
            viewing_conversion=viewing_conversion,
            application_conversion=application_conversion,
            top_applicant_concern=objections.most_common(1)[0][0] if objections else "NONE",
            top_applicant_preference=preferences.most_common(1)[0][0] if preferences else "NONE",
            popular_amenities=[name for name, _ in preferences.most_common(5)],
            applicant_segments=dict(segments.most_common()),
            recommended_action=recommended,
            top_matching_applicants=top_applicants,
            sources=RetrievalService(self.db).query(
                f"Demand, viewing feedback and applicant activity for property {prop.property_id}",
                limit=5,
                property_id=prop.property_id,
            ),
        )

    def _recommend(self, prop: Property, demand: str, application_conversion: float, objections: Counter) -> str:
        if demand == "HIGH" and application_conversion < 0.18:
            concern = objections.most_common(1)[0][0] if objections else "conversion friction"
            return f"Investigate {concern.lower()} objections and improve follow-up after viewings."
        if objections.get("PRICE", 0) >= 3:
            return "Review pricing or lead messaging with value and transport benefits."
        if demand == "LOW":
            return "Refresh property description and target applicants with matching amenities."
        return "Prioritise high-match applicants and keep follow-up within 24 hours of viewing."
