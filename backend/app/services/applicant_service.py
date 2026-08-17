from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Conversation, Feedback, Interaction, Viewing


class ApplicantService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, limit: int = 50, offset: int = 0, search: str | None = None) -> list[Applicant]:
        stmt = select(Applicant).order_by(Applicant.name).offset(offset).limit(limit)
        if search:
            stmt = stmt.where(Applicant.name.ilike(f"%{search}%"))
        return list(self.db.scalars(stmt))

    def get(self, applicant_id: str) -> Applicant | None:
        return self.db.get(Applicant, applicant_id)

    def find_by_name_fragment(self, name: str) -> Applicant | None:
        return self.db.scalars(select(Applicant).where(Applicant.name.ilike(f"%{name}%")).limit(1)).first()

    def interactions(self, applicant_id: str, limit: int = 100) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(Interaction.applicant_id == applicant_id)
            .order_by(Interaction.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def conversations(self, applicant_id: str, limit: int = 30) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.applicant_id == applicant_id)
            .order_by(Conversation.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def feedback(self, applicant_id: str, limit: int = 30) -> list[Feedback]:
        stmt = (
            select(Feedback)
            .where(Feedback.applicant_id == applicant_id)
            .order_by(Feedback.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def viewings(self, applicant_id: str, limit: int = 50) -> list[Viewing]:
        stmt = (
            select(Viewing)
            .where(Viewing.applicant_id == applicant_id)
            .order_by(Viewing.scheduled_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def active_count(self) -> int:
        active_events = ["ENQUIRY", "QUALIFIED", "VIEWING_BOOKED", "PROPERTY_VIEW", "MESSAGE_RECEIVED"]
        stmt = select(func.count(func.distinct(Interaction.applicant_id))).where(Interaction.event_type.in_(active_events))
        return int(self.db.scalar(stmt) or 0)

