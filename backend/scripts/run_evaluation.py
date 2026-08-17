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
from app.evaluation.ranking_eval import evaluate_matching
from app.evaluation.recommendation_eval import evaluate_next_best_action
from app.evaluation.retrieval_eval import evaluate_retrieval


def main() -> None:
    db = SessionLocal()
    try:
        metrics = {
            "matching": evaluate_matching(db),
            "rag": evaluate_retrieval(db),
            "next_best_action": evaluate_next_best_action(db),
            "notice": "Evaluation is offline and uses synthetic labels/rules; it is not evidence of real-world business lift.",
        }
    finally:
        db.close()
    out = ROOT.parent / "models" / "evaluation_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
