#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{ROOT / 'property_intelligence.db'}"
sys.path.append(str(ROOT))

from app.db.session import SessionLocal
from app.rag.answer import GroundedAnswerGenerator
from app.rag.provenance import get_provenance
from app.rag.retrieval import RetrievalService


QUERY = "Why is Sarah a strong candidate for this property?"


def main() -> None:
    db = SessionLocal()
    try:
        retriever = RetrievalService(db)
        citations = retriever.query(QUERY, limit=8, applicant_id="A-DEMO-SARAH")
        answer = GroundedAnswerGenerator().generate(QUERY, "Sarah is a strong candidate based on the retrieved evidence.", citations, [])
        print("QUERY")
        print(QUERY)
        print("\nPIPELINE")
        print("QUERY -> NORMALIZATION -> FILTERS -> VECTOR RETRIEVAL + LEXICAL RETRIEVAL -> HYBRID MERGE -> RERANKING -> TOP EVIDENCE -> GROUNDED ANSWER")
        print(json.dumps(retriever.last_metadata, indent=2, default=str))
        print("\nEVIDENCE CHAIN")
        for citation in citations[:3]:
            provenance = get_provenance(db, citation.citation_id or "")
            print(json.dumps({
                "citation": citation.model_dump(),
                "source_record": provenance["source_record"],
                "rag_document": provenance["rag_document"],
                "rag_chunk": provenance["rag_chunk"],
                "retrieval": provenance["retrieval"],
            }, indent=2, default=str))
        print("\nFINAL GROUNDED ANSWER")
        print(json.dumps(answer.__dict__, indent=2, default=str))
    finally:
        db.close()


if __name__ == "__main__":
    main()
