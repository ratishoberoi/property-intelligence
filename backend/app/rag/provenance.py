from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Applicant, Conversation, Feedback, Interaction, Property
from app.schemas.intelligence import Citation


_CACHE: dict[str, dict[str, Any]] = {}


def register(citation: Citation, chunk: dict[str, Any]) -> None:
    _CACHE[citation.citation_id or ""] = {"citation": citation, "chunk": dict(chunk)}


def get_provenance(db: Session, citation_id: str, query: str | None = None) -> dict[str, Any]:
    cached = _CACHE.get(citation_id)
    if cached is None and query:
        from app.rag.retrieval import RetrievalService

        RetrievalService(db).query(query, limit=max(int(citation_id[1:]) if citation_id[1:].isdigit() else 5, 5))
        cached = _CACHE.get(citation_id)
    if cached is None:
        raise KeyError(citation_id)

    citation: Citation = cached["citation"]
    chunk = cached["chunk"]
    source = _source_record(db, chunk)
    if source is None:
        raise LookupError(f"Source record {chunk.get('source_record_id')} was not found")
    index_path = (get_settings().model_dir / "rag_index.pkl").resolve()
    return {
        "citation_id": citation.citation_id,
        "source_type": citation.document_type,
        "source_table": chunk.get("source_table"),
        "source_record_id": chunk.get("source_record_id"),
        "applicant_id": citation.applicant_id,
        "applicant_name": source.get("applicant_name"),
        "property_id": citation.property_id,
        "property_area": source.get("property_area"),
        "timestamp": citation.timestamp,
        "channel": chunk.get("channel"),
        "synthetic": bool(chunk.get("synthetic", True)),
        "indexed": index_path.exists(),
        "source_record": source,
        "original_source_text": source.get("source_text"),
        "rag_document": {
            "document_id": chunk.get("document_id", "").rsplit(":chunk:", 1)[0],
            "document_type": chunk.get("document_type"),
            "source_record_id": chunk.get("source_record_id"),
            "metadata": {key: chunk.get(key) for key in ("applicant_id", "property_id", "timestamp", "source", "channel", "synthetic")},
        },
        "rag_chunk": {
            "chunk_id": chunk.get("document_id"),
            "chunk_text": chunk.get("text"),
            "index_position": chunk.get("index_position"),
            "embedding_index": str(index_path),
        },
        "retrieval": {
            "semantic_score": citation.semantic_score,
            "lexical_score": citation.lexical_score,
            "hybrid_score": citation.hybrid_score,
            "rerank_score": citation.rerank_score,
            "rank": int(citation.citation_id[1:]) if citation.citation_id and citation.citation_id[1:].isdigit() else None,
            "selection_reason": citation.selection_reason,
        },
    }


def _source_record(db: Session, chunk: dict[str, Any]) -> dict[str, Any] | None:
    table = chunk.get("source_table")
    record_id = chunk.get("source_record_id")
    row = None
    source_text = chunk.get("source_text")
    if table == "conversations":
        row = db.get(Conversation, record_id)
        if row:
            source_text = row.body
            return _base_source(db, row.applicant_id, row.property_id, source_text, {"conversation_id": row.conversation_id, "timestamp": row.timestamp.isoformat(), "direction": row.direction, "channel": row.channel, "subject": row.subject, "body": row.body, "sentiment": row.sentiment})
    elif table == "interactions":
        row = db.get(Interaction, record_id)
        if row:
            source_text = row.message
            return _base_source(db, row.applicant_id, row.property_id, source_text, {"interaction_id": row.interaction_id, "timestamp": row.timestamp.isoformat(), "channel": row.channel, "event_type": row.event_type, "message": row.message, "sentiment": row.sentiment, "intent": row.intent})
    elif table == "feedback":
        row = db.get(Feedback, record_id)
        if row:
            source_text = row.comments
            return _base_source(db, row.applicant_id, row.property_id, source_text, {"feedback_id": row.feedback_id, "viewing_id": row.viewing_id, "timestamp": row.timestamp.isoformat(), "rating": row.rating, "sentiment": row.sentiment, "objections": row.objections, "comments": row.comments})
    elif table == "applicants":
        row = db.get(Applicant, record_id)
        if row:
            return _base_source(db, row.applicant_id, None, source_text, {"applicant_id": row.applicant_id, "name": row.name, "budget_min": row.budget_min, "budget_max": row.budget_max, "preferred_areas": row.preferred_areas, "bedrooms_required": row.bedrooms_required})
    elif table == "properties":
        row = db.get(Property, record_id)
        if row:
            return _base_source(db, None, row.property_id, source_text, {"property_id": row.property_id, "area": row.area, "property_type": row.property_type, "bedrooms": row.bedrooms, "rent_pcm": row.rent_pcm, "description": row.description})
    return None


def _base_source(db: Session, applicant_id: str | None, property_id: str | None, source_text: str | None, fields: dict[str, Any]) -> dict[str, Any]:
    applicant = db.get(Applicant, applicant_id) if applicant_id else None
    prop = db.get(Property, property_id) if property_id else None
    return {"source_text": source_text, "applicant_name": applicant.name if applicant else None, "property_area": prop.area if prop else None, **fields}
