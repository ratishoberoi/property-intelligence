from __future__ import annotations

import math
from pathlib import Path
from typing import Any
import joblib
from app.schemas.intelligence import IntentResult


INTENT_ORDER = ["DORMANT", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"]


class ApplicantIntentModel:
    """Applicant intent scorer with optional trained sklearn model and deterministic fallback."""

    def __init__(self, model_path: Path | None = None):
        self.model_bundle: dict[str, Any] | None = None
        if model_path and model_path.exists():
            self.model_bundle = joblib.load(model_path)

    def predict(self, features: dict[str, float]) -> IntentResult:
        if self.model_bundle:
            try:
                return self._predict_model(features)
            except Exception:
                pass
        return self._predict_rules(features)

    def _predict_model(self, features: dict[str, float]) -> IntentResult:
        cols = self.model_bundle["intent_features"]
        model = self.model_bundle["intent_model"]
        classes = list(model.classes_)
        row = [[features.get(col, 0.0) for col in cols]]
        probabilities = model.predict_proba(row)[0]
        prob_map = {label: round(float(prob), 3) for label, prob in zip(classes, probabilities, strict=False)}
        intent = max(prob_map, key=prob_map.get)
        return IntentResult(
            intent=intent,
            confidence=prob_map[intent],
            probabilities={label: prob_map.get(label, 0.0) for label in INTENT_ORDER},
            features=features,
            key_signals=self._signals(features),
        )

    def _predict_rules(self, f: dict[str, float]) -> IntentResult:
        score = 0.0
        score += min(f["number_of_interactions"], 20) * 0.035
        score += min(f["viewings"], 5) * 0.09
        score += min(f["positive_feedback"], 4) * 0.12
        score += min(f["applications"], 2) * 0.22
        score += min(f["messages"], 12) * 0.025
        score += min(f["response_rate"], 2) * 0.08
        score -= min(f["days_since_last_interaction"], 60) * 0.01
        score -= min(f["negative_feedback"], 4) * 0.1
        score -= min(f["cancellations"], 3) * 0.08
        score -= min(f["no_response_events"], 5) * 0.07
        score = max(0.0, min(1.0, score))
        if score >= 0.82:
            label = "VERY_HIGH"
        elif score >= 0.62:
            label = "HIGH"
        elif score >= 0.38:
            label = "MEDIUM"
        elif score >= 0.18:
            label = "LOW"
        else:
            label = "DORMANT"
        probabilities = self._soft_distribution(label, score)
        return IntentResult(
            intent=label,
            confidence=probabilities[label],
            probabilities=probabilities,
            features={k: round(v, 3) for k, v in f.items()},
            key_signals=self._signals(f),
        )

    def _soft_distribution(self, label: str, score: float) -> dict[str, float]:
        centers = {"DORMANT": 0.05, "LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.72, "VERY_HIGH": 0.9}
        raw = {k: math.exp(-abs(score - center) * 7) for k, center in centers.items()}
        total = sum(raw.values())
        return {k: round(v / total, 3) for k, v in raw.items()}

    def _signals(self, f: dict[str, float]) -> list[str]:
        signals: list[str] = []
        if f["viewings"] >= 2:
            signals.append("Multiple property viewings indicate active search behaviour.")
        if f["positive_feedback"] > f["negative_feedback"]:
            signals.append("Recent feedback is more positive than negative.")
        if f["applications"] > 0:
            signals.append("Applicant has already started or submitted an application.")
        if f["days_since_last_interaction"] <= 3:
            signals.append("Applicant engaged within the last three days.")
        if f["no_response_events"] >= 2:
            signals.append("Repeated no-response events reduce urgency.")
        if not signals:
            signals.append("Intent is primarily inferred from aggregate engagement history.")
        return signals

