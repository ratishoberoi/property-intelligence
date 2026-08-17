from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Conversation, Feedback, Interaction, Property, Viewing


def chunk_text(text: str, chunk_size: int = 650, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
        start += max(1, chunk_size - overlap)
    return chunks


def build_documents_from_db(db: Session, applicant_id: str | None = None, property_id: str | None = None) -> list[dict]:
    docs: list[dict] = []
    applicants = db.scalars(select(Applicant).where(Applicant.applicant_id == applicant_id) if applicant_id else select(Applicant)).all()
    properties = db.scalars(select(Property).where(Property.property_id == property_id) if property_id else select(Property)).all()
    for applicant in applicants:
        text = (
            f"Applicant profile for {applicant.name}. Budget £{applicant.budget_min}-£{applicant.budget_max}. "
            f"Preferred areas {applicant.preferred_areas}. Bedrooms {applicant.bedrooms_required}. "
            f"Types {applicant.property_types}. Amenities {applicant.amenities_preferences}. "
            f"Pets {applicant.pets}. Parking required {applicant.parking_required}."
        )
        docs.append(_doc("applicant_profile", applicant.applicant_id, None, None, "Applicant profile", text, applicant.applicant_id, "applicants", None, text))
    for prop in properties:
        text = (
            f"Property {prop.property_id} in {prop.area}, {prop.city}. {prop.bedrooms} bedrooms, "
            f"£{prop.rent_pcm} pcm, {prop.property_type}. Amenities {prop.amenities}. "
            f"Parking {prop.parking}, balcony {prop.balcony}, garden {prop.garden}. {prop.description}"
        )
        docs.append(_doc("property_description", None, prop.property_id, None, f"Property {prop.property_id}", text, prop.property_id, "properties", None, prop.description))
    conv_stmt = select(Conversation)
    inter_stmt = select(Interaction)
    fb_stmt = select(Feedback)
    if applicant_id:
        conv_stmt = conv_stmt.where(Conversation.applicant_id == applicant_id)
        inter_stmt = inter_stmt.where(Interaction.applicant_id == applicant_id)
        fb_stmt = fb_stmt.where(Feedback.applicant_id == applicant_id)
    if property_id:
        conv_stmt = conv_stmt.where(Conversation.property_id == property_id)
        inter_stmt = inter_stmt.where(Interaction.property_id == property_id)
        fb_stmt = fb_stmt.where(Feedback.property_id == property_id)
    for row in db.scalars(conv_stmt.limit(1000)):
        docs.append(_doc("conversation", row.applicant_id, row.property_id, row.timestamp, f"Conversation - {row.subject}", row.body, row.conversation_id, "conversations", row.channel, row.body))
    for row in db.scalars(inter_stmt.limit(1500)):
        docs.append(
            _doc(
                "interaction_history",
                row.applicant_id,
                row.property_id,
                row.timestamp,
                f"Interaction - {row.event_type}",
                f"{row.event_type} via {row.channel}. Intent {row.intent}. Sentiment {row.sentiment}. {row.message}",
                row.interaction_id,
                "interactions",
                row.channel,
                row.message,
            )
        )
    for row in db.scalars(fb_stmt.limit(1000)):
        docs.append(
            _doc(
                "viewing_feedback",
                row.applicant_id,
                row.property_id,
                row.timestamp,
                "Viewing feedback",
                f"Rating {row.rating}. Sentiment {row.sentiment}. Objections {row.objections}. Comments: {row.comments}",
                row.feedback_id,
                "feedback",
                None,
                row.comments,
            )
        )
    return docs


def _doc(
    doc_type: str,
    applicant_id: str | None,
    property_id: str | None,
    timestamp: datetime | None,
    source: str,
    text: str,
    source_record_id: str,
    source_table: str,
    channel: str | None,
    source_text: str,
) -> dict:
    return {
        "document_id": f"{doc_type}:{applicant_id or ''}:{property_id or ''}:{timestamp or source}",
        "document_type": doc_type,
        "applicant_id": applicant_id,
        "property_id": property_id,
        "timestamp": timestamp.isoformat() if timestamp else None,
        "source": source,
        "text": text,
        "source_record_id": source_record_id,
        "source_table": source_table,
        "channel": channel,
        "source_text": source_text,
        "synthetic": True,
    }
