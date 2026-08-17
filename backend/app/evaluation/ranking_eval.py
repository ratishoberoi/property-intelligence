from __future__ import annotations

import math
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Interaction
from app.intelligence.matching.engine import PropertyMatchingEngine


def evaluate_matching(db: Session, k: int = 10) -> dict[str, float]:
    applicants = list(db.scalars(select(Applicant).limit(120)))
    engine = PropertyMatchingEngine(db)
    precisions, recalls, ndcgs = [], [], []
    total_positive_labels = 0
    excluded_positive_labels = 0
    for applicant in applicants:
        positives = set(
            db.scalars(
                select(Interaction.property_id)
                .where(Interaction.applicant_id == applicant.applicant_id)
                .where(Interaction.event_type.in_(["VIEWING_BOOKED", "APPLICATION_STARTED", "APPLICATION_SUBMITTED", "OFFER_ACCEPTED"]))
            )
        )
        positives.discard(None)
        if not positives:
            continue
        candidate_ids = {prop.property_id for prop in engine._hard_filter(applicant)}
        total_positive_labels += len(positives)
        excluded_positive_labels += len(positives - candidate_ids)
        positives &= candidate_ids
        if not positives:
            continue
        ranked = [m.property.property_id for m in engine.match(applicant, k)]
        hits = [1 if pid in positives else 0 for pid in ranked]
        precisions.append(sum(hits) / k)
        recalls.append(sum(hits) / len(positives))
        dcg = sum(hit / math.log2(idx + 2) for idx, hit in enumerate(hits))
        ideal = sum(1 / math.log2(idx + 2) for idx in range(min(len(positives), k)))
        ndcgs.append(dcg / ideal if ideal else 0)
    return {
        "precision_at_10": round(_mean(precisions), 4),
        "recall_at_10": round(_mean(recalls), 4),
        "ndcg_at_10": round(_mean(ndcgs), 4),
        "evaluated_applicants": len(precisions),
        "positive_labels": total_positive_labels,
        "excluded_by_hard_filters": excluded_positive_labels,
        "label_eligibility_rate": round((total_positive_labels - excluded_positive_labels) / max(total_positive_labels, 1), 4),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)
