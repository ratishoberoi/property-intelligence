#!/usr/bin/env python
from __future__ import annotations

import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, classification_report, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data" / "processed"
MODELS = ROOT.parent / "models"
FEATURES = [
    "number_of_interactions",
    "days_since_last_interaction",
    "viewings",
    "positive_feedback",
    "negative_feedback",
    "applications",
    "messages",
    "response_rate",
    "avg_days_between_interactions",
    "cancellations",
    "no_response_events",
]


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    features = build_features()
    labels = pd.read_csv(DATA / "labels.csv")
    frame = features.merge(labels, on="applicant_id", how="left").fillna({"converted": 0, "intent_label": "LOW"})
    train, test = train_test_split(frame, test_size=0.25, random_state=42, stratify=frame["intent_label"])
    intent_model = RandomForestClassifier(n_estimators=120, min_samples_leaf=4, random_state=42, class_weight="balanced")
    intent_model.fit(train[FEATURES], train["intent_label"])
    intent_pred = intent_model.predict(test[FEATURES])
    conv_model = LogisticRegression(max_iter=1000, class_weight="balanced")
    conv_model.fit(train[FEATURES], train["converted"])
    conv_prob = conv_model.predict_proba(test[FEATURES])[:, 1]
    conv_pred = (conv_prob >= 0.5).astype(int)
    metrics = {
        "intent": {
            "accuracy": round(float(accuracy_score(test["intent_label"], intent_pred)), 4),
            "f1_macro": round(float(f1_score(test["intent_label"], intent_pred, average="macro", zero_division=0)), 4),
            "classification_report": classification_report(test["intent_label"], intent_pred, zero_division=0, output_dict=True),
        },
        "conversion": {
            "roc_auc": round(float(roc_auc_score(test["converted"], conv_prob)), 4) if test["converted"].nunique() > 1 else 0.0,
            "pr_auc": round(float(average_precision_score(test["converted"], conv_prob)), 4),
            "precision": round(float(precision_score(test["converted"], conv_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(test["converted"], conv_pred, zero_division=0)), 4),
        },
        "synthetic_data_notice": "Prototype models trained only on deterministic synthetic data.",
    }
    joblib.dump({"intent_model": intent_model, "intent_features": FEATURES, "metrics": metrics["intent"]}, MODELS / "intent_model.joblib")
    joblib.dump({"conversion_model": conv_model, "conversion_features": FEATURES, "metrics": metrics["conversion"]}, MODELS / "conversion_model.joblib")
    (MODELS / "model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2)[:4000])


def build_features() -> pd.DataFrame:
    interactions = pd.read_csv(DATA / "interactions.csv", parse_dates=["timestamp"])
    viewings = pd.read_csv(DATA / "viewings.csv")
    feedback = pd.read_csv(DATA / "feedback.csv")
    applicants = pd.read_csv(DATA / "applicants.csv")
    now = pd.Timestamp("2026-08-13")
    grouped = interactions.groupby("applicant_id")
    rows = []
    for applicant_id in applicants.applicant_id:
        group = grouped.get_group(applicant_id) if applicant_id in grouped.groups else pd.DataFrame(columns=interactions.columns)
        fb = feedback[feedback.applicant_id == applicant_id]
        vg = viewings[viewings.applicant_id == applicant_id]
        event_counts = group.event_type.value_counts() if not group.empty else pd.Series(dtype=int)
        timestamps = group.timestamp.sort_values() if not group.empty else pd.Series(dtype="datetime64[ns]")
        gaps = timestamps.diff().dt.total_seconds().dropna() / 86400 if len(timestamps) > 1 else pd.Series(dtype=float)
        last = timestamps.max() if len(timestamps) else now - pd.Timedelta(days=60)
        rows.append(
            {
                "applicant_id": applicant_id,
                "number_of_interactions": float(len(group)),
                "days_since_last_interaction": float(max((now - last).days, 0)),
                "viewings": float(len(vg)),
                "positive_feedback": float((fb.rating >= 4).sum()) if not fb.empty else 0.0,
                "negative_feedback": float((fb.rating <= 2).sum()) if not fb.empty else 0.0,
                "applications": float(event_counts.get("APPLICATION_STARTED", 0) + event_counts.get("APPLICATION_SUBMITTED", 0)),
                "messages": float(event_counts.get("MESSAGE_RECEIVED", 0) + event_counts.get("MESSAGE_SENT", 0)),
                "response_rate": float(event_counts.get("MESSAGE_RECEIVED", 0) / max(event_counts.get("MESSAGE_SENT", 0), 1)),
                "avg_days_between_interactions": float(gaps.mean()) if len(gaps) else 30.0,
                "cancellations": float(event_counts.get("VIEWING_CANCELLED", 0)),
                "no_response_events": float(event_counts.get("NO_RESPONSE", 0)),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()

