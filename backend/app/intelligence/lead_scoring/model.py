from __future__ import annotations

import math
from pathlib import Path
from typing import Any
import joblib
from app.schemas.intelligence import ConversionResult


class ConversionScorer:
    """Prototype conversion probability model trained on synthetic data when available."""

    def __init__(self, model_path: Path | None = None):
        self.model_bundle: dict[str, Any] | None = None
        if model_path and model_path.exists():
            self.model_bundle = joblib.load(model_path)

    def predict(self, features: dict[str, float], avg_match_score: float) -> ConversionResult:
        enriched = dict(features)
        enriched["property_match_quality"] = avg_match_score / 100
        if self.model_bundle:
            try:
                return self._predict_model(enriched)
            except Exception:
                pass
        return self._predict_rules(enriched)

    def _predict_model(self, features: dict[str, float]) -> ConversionResult:
        cols = self.model_bundle["conversion_features"]
        model = self.model_bundle["conversion_model"]
        row = [[features.get(col, 0.0) for col in cols]]
        prob = float(model.predict_proba(row)[0][1])
        return ConversionResult(
            conversion_probability=round(prob, 3),
            top_positive_factors=self._positive(features),
            top_negative_factors=self._negative(features),
            features={k: round(v, 3) for k, v in features.items()},
        )

    def _predict_rules(self, f: dict[str, float]) -> ConversionResult:
        z = -2.0
        z += f["property_match_quality"] * 2.1
        z += min(f["viewings"], 4) * 0.32
        z += min(f["positive_feedback"], 4) * 0.42
        z += min(f["applications"], 2) * 0.95
        z += min(f["response_rate"], 2) * 0.25
        z -= min(f["negative_feedback"], 4) * 0.34
        z -= min(f["days_since_last_interaction"], 45) * 0.025
        z -= min(f["no_response_events"], 5) * 0.22
        prob = 1 / (1 + math.exp(-z))
        return ConversionResult(
            conversion_probability=round(prob, 3),
            top_positive_factors=self._positive(f),
            top_negative_factors=self._negative(f),
            features={k: round(v, 3) for k, v in f.items()},
        )

    def _positive(self, f: dict[str, float]) -> list[str]:
        factors: list[str] = []
        if f.get("property_match_quality", 0) >= 0.78:
            factors.append("High average property match quality.")
        if f["positive_feedback"] >= 1:
            factors.append("Positive viewing feedback.")
        if f["viewings"] >= 2:
            factors.append("Multiple completed or booked viewings.")
        if f["applications"] >= 1:
            factors.append("Application activity already recorded.")
        if f["days_since_last_interaction"] <= 3:
            factors.append("Recent engagement.")
        return factors or ["Some engagement signals are present."]

    def _negative(self, f: dict[str, float]) -> list[str]:
        factors: list[str] = []
        if f["negative_feedback"] >= 1:
            factors.append("Negative feedback or objections in viewing history.")
        if f["no_response_events"] >= 2:
            factors.append("Repeated no-response events.")
        if f["days_since_last_interaction"] > 14:
            factors.append("No recent interaction.")
        if f.get("property_match_quality", 1) < 0.55:
            factors.append("Current property match quality is weak.")
        return factors

