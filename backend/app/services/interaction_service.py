from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Feedback, Interaction, Viewing


class InteractionService:
    def __init__(self, db: Session):
        self.db = db

    def applicant_features(self, applicant_id: str) -> dict[str, float]:
        interactions = list(
            self.db.scalars(select(Interaction).where(Interaction.applicant_id == applicant_id).order_by(Interaction.timestamp))
        )
        viewings = list(self.db.scalars(select(Viewing).where(Viewing.applicant_id == applicant_id)))
        feedback = list(self.db.scalars(select(Feedback).where(Feedback.applicant_id == applicant_id)))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        last_ts = max((i.timestamp for i in interactions), default=now)
        days_since_last = max((now - last_ts).days, 0)
        response_events = sum(1 for i in interactions if i.event_type in {"MESSAGE_RECEIVED", "FEEDBACK", "ENQUIRY"})
        outbound_events = sum(1 for i in interactions if i.event_type in {"MESSAGE_SENT", "FOLLOW_UP"})
        applications = sum(1 for i in interactions if i.event_type in {"APPLICATION_STARTED", "APPLICATION_SUBMITTED"})
        positive_feedback = sum(1 for f in feedback if f.rating >= 4 or f.sentiment > 0.35)
        negative_feedback = sum(1 for f in feedback if f.rating <= 2 or f.sentiment < -0.25)
        cancellations = sum(1 for i in interactions if i.event_type == "VIEWING_CANCELLED")
        no_response = sum(1 for i in interactions if i.event_type == "NO_RESPONSE")
        gaps = [
            (interactions[idx].timestamp - interactions[idx - 1].timestamp).total_seconds() / 86400
            for idx in range(1, len(interactions))
        ]
        return {
            "number_of_interactions": float(len(interactions)),
            "days_since_last_interaction": float(days_since_last),
            "viewings": float(len(viewings)),
            "positive_feedback": float(positive_feedback),
            "negative_feedback": float(negative_feedback),
            "applications": float(applications),
            "messages": float(sum(1 for i in interactions if i.event_type.startswith("MESSAGE"))),
            "response_rate": float(response_events / max(outbound_events, 1)),
            "avg_days_between_interactions": float(sum(gaps) / len(gaps)) if gaps else 30.0,
            "cancellations": float(cancellations),
            "no_response_events": float(no_response),
        }

    def property_counts(self, property_id: str) -> dict[str, int]:
        rows = self.db.execute(
            select(Interaction.event_type, func.count())
            .where(Interaction.property_id == property_id)
            .group_by(Interaction.event_type)
        ).all()
        return {event: int(count) for event, count in rows}

    def property_objections(self, property_id: str) -> Counter:
        feedback = self.db.scalars(select(Feedback).where(Feedback.property_id == property_id)).all()
        counter: Counter = Counter()
        for row in feedback:
            for objection in row.objections.split("|"):
                if objection:
                    counter[objection] += 1
        return counter
