from __future__ import annotations

import math
import time
from sqlalchemy.orm import Session
from app.rag.answer import GroundedAnswerGenerator
from app.rag.retrieval import RetrievalService

GOLDEN = [
    {
        "question": "Why is Sarah a good candidate for P-DEMO-01?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": "P-DEMO-01",
        "expected_types": {"applicant_profile", "property_description", "conversation", "viewing_feedback"},
    },
    {
        "question": "What are Sarah's main objections?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": None,
        "expected_types": {"conversation", "viewing_feedback"},
    },
    {
        "question": "Which properties are suitable for applicants looking for 2 bedrooms under £2800?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": None,
        "expected_types": {"property_description", "applicant_profile"},
    },
    {
        "question": "What evidence supports Sarah's application activity for P-DEMO-01?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": "P-DEMO-01",
        "expected_types": {"interaction_history", "conversation", "viewing_feedback"},
    },
    {
        "question": "What did Sarah ask about tenancy terms and move-in timing?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": "P-DEMO-01",
        "expected_types": {"conversation", "interaction_history"},
    },
    {
        "question": "Which evidence describes the property attributes Sarah prefers?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": "P-DEMO-01",
        "expected_types": {"property_description", "applicant_profile"},
    },
    {
        "question": "What changed in Sarah's recent behaviour?",
        "applicant_id": "A-DEMO-SARAH",
        "property_id": None,
        "expected_types": {"interaction_history", "viewing_feedback", "conversation"},
    },
    {
        "question": "What demand and viewing evidence exists for P-DEMO-01?",
        "applicant_id": None,
        "property_id": "P-DEMO-01",
        "expected_types": {"interaction_history", "viewing_feedback", "property_description"},
    },
]


def evaluate_retrieval(db: Session, k: int = 5) -> dict[str, float]:
    retriever = RetrievalService(db)
    recalls5, recalls10, reciprocal, ndcg5, ndcg10, coverage, groundedness = [], [], [], [], [], [], []
    latencies, generation_latencies = [], []
    for item in GOLDEN:
        started = time.perf_counter()
        hits = retriever.query(item["question"], limit=max(k, 10), applicant_id=item["applicant_id"], property_id=item["property_id"])
        latencies.append((time.perf_counter() - started) * 1000)
        expected = item["expected_types"]
        types = [hit.document_type for hit in hits]
        recalls5.append(len(set(types[:5]) & expected) / len(expected))
        recalls10.append(len(set(types[:10]) & expected) / len(expected))
        first = next((idx + 1 for idx, t in enumerate(types) if t in expected), None)
        reciprocal.append(1 / first if first else 0)
        coverage.append(sum(1 for hit in hits[:5] if hit.source and hit.excerpt and hit.citation_id) / max(min(len(hits), 5), 1))
        ndcg5.append(_ndcg(types[:5], expected))
        ndcg10.append(_ndcg(types[:10], expected))
        generation_started = time.perf_counter()
        answer = GroundedAnswerGenerator().generate(item["question"], "Evidence summary", hits[:5], [])
        generation_latencies.append((time.perf_counter() - generation_started) * 1000)
        groundedness.append(float(all(citation.citation_id in answer.answer or citation.citation_id in " ".join(answer.evidence) for citation in hits[:min(3, len(hits))])))
    return {
        "recall_at_5": round(sum(recalls5) / len(recalls5), 4),
        "recall_at_10": round(sum(recalls10) / len(recalls10), 4),
        "mrr": round(sum(reciprocal) / len(reciprocal), 4),
        "ndcg_at_5": round(sum(ndcg5) / len(ndcg5), 4),
        "ndcg_at_10": round(sum(ndcg10) / len(ndcg10), 4),
        "citation_coverage": round(sum(coverage) / len(coverage), 4),
        "answer_groundedness": round(sum(groundedness) / len(groundedness), 4),
        "unsupported_claim_rate": round(1 - sum(groundedness) / len(groundedness), 4),
        "retrieval_latency_ms": round(sum(latencies) / len(latencies), 2),
        "generation_latency_ms": round(sum(generation_latencies) / len(generation_latencies), 2),
        "golden_questions": len(GOLDEN),
    }


def _ndcg(types: list[str], expected: set[str]) -> float:
    seen: set[str] = set()
    gains = []
    for value in types:
        gain = 1 if value in expected and value not in seen else 0
        seen.add(value)
        gains.append(gain)
    dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
    ideal = sum(1 / math.log2(index + 2) for index in range(min(len(expected), len(types))))
    return dcg / ideal if ideal else 0.0
