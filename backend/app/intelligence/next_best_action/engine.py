from app.schemas.intelligence import ConversionResult, IntentResult, NextBestAction, PropertyMatch


class NextBestActionEngine:
    """Rules-based action policy grounded in engagement, conversion and recent objections."""

    def recommend(
        self,
        intent: IntentResult,
        conversion: ConversionResult,
        matches: list[PropertyMatch],
        recent_objections: list[str],
    ) -> NextBestAction:
        price_sensitive = "PRICE" in recent_objections
        terms_question = "TERMS" in recent_objections
        transport_question = "TRANSPORT" in recent_objections
        if conversion.conversion_probability >= 0.62 and intent.intent in {"HIGH", "VERY_HIGH"} and terms_question:
            return NextBestAction(
                action="SEND_APPLICATION_LINK",
                priority="HIGH",
                confidence=0.9,
                reason="High conversion probability plus tenancy-term engagement indicates readiness to apply.",
                recommended_properties=matches[:1],
            )
        if price_sensitive and matches:
            affordable = sorted(matches, key=lambda m: m.property.rent_pcm)[:3]
            return NextBestAction(
                action="RECOMMEND_LOWER_PRICE_OPTIONS",
                priority="HIGH" if intent.intent in {"HIGH", "VERY_HIGH"} else "MEDIUM",
                confidence=0.86,
                reason="Recent history shows price sensitivity, so lower-rent strong matches should be sent first.",
                recommended_properties=affordable,
            )
        if transport_question and matches:
            return NextBestAction(
                action="SEND_SIMILAR_PROPERTIES",
                priority="HIGH",
                confidence=0.84,
                reason="Applicant asked about transport, so send similar matches with area and connectivity evidence.",
                recommended_properties=matches[:3],
            )
        if intent.intent in {"HIGH", "VERY_HIGH"} and conversion.conversion_probability >= 0.45:
            return NextBestAction(
                action="SCHEDULE_VIEWING",
                priority="HIGH",
                confidence=0.81,
                reason="Engagement and match quality are strong enough to move from recommendation to viewing.",
                recommended_properties=matches[:2],
            )
        if intent.intent == "MEDIUM" and matches:
            return NextBestAction(
                action="FOLLOW_UP_NOW",
                priority="MEDIUM",
                confidence=0.72,
                reason="Applicant has moderate intent and eligible matches; a prompt follow-up can clarify requirements.",
                recommended_properties=matches[:2],
            )
        if intent.intent in {"LOW", "DORMANT"}:
            return NextBestAction(
                action="REQUEST_MORE_INFORMATION",
                priority="LOW",
                confidence=0.68,
                reason="Recent engagement is limited, so the next step is to refresh requirements before recommending stock.",
                recommended_properties=[],
            )
        return NextBestAction(
            action="WAIT",
            priority="LOW",
            confidence=0.55,
            reason="No immediate action has stronger supporting evidence than waiting for new engagement.",
            recommended_properties=[m for m in matches if m.match_score >= 70][:3],
        )
