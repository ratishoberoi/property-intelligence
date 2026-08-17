from app.intelligence.intent.model import ApplicantIntentModel


def test_intent_rules_label_high_engagement():
    result = ApplicantIntentModel().predict(
        {
            "number_of_interactions": 14,
            "days_since_last_interaction": 1,
            "viewings": 3,
            "positive_feedback": 2,
            "negative_feedback": 0,
            "applications": 1,
            "messages": 6,
            "response_rate": 1.2,
            "avg_days_between_interactions": 2,
            "cancellations": 0,
            "no_response_events": 0,
        }
    )
    assert result.intent in {"HIGH", "VERY_HIGH"}
    assert result.confidence > 0

