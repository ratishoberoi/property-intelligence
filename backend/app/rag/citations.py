from app.schemas.intelligence import Citation


def citation_from_chunk(chunk: dict, score: float) -> Citation:
    text = chunk.get("text", "")
    excerpt = text[:260] + ("..." if len(text) > 260 else "")
    return Citation(
        citation_id=f"C{str(chunk.get('citation_index', 0)).zfill(2)}",
        document_id=chunk.get("document_id"),
        source_record_id=chunk.get("source_record_id"),
        source_table=chunk.get("source_table"),
        chunk_id=chunk.get("document_id"),
        channel=chunk.get("channel"),
        synthetic=bool(chunk.get("synthetic", True)),
        indexed=True,
        source=chunk.get("source", "Unknown source"),
        document_type=chunk.get("document_type", "unknown"),
        applicant_id=chunk.get("applicant_id") or None,
        property_id=chunk.get("property_id") or None,
        timestamp=str(chunk.get("timestamp") or "") or None,
        excerpt=excerpt,
        score=round(float(score), 3),
        semantic_score=round(float(chunk["_semantic_score"]), 3) if "_semantic_score" in chunk else None,
        lexical_score=round(float(chunk["_lexical_score"]), 3) if "_lexical_score" in chunk else None,
        hybrid_score=round(float(chunk["_hybrid_score"]), 3) if "_hybrid_score" in chunk else None,
        rerank_score=round(float(score), 3),
        selection_reason=chunk.get("_selection_reason"),
    )
