from __future__ import annotations

from dataclasses import dataclass
import re
from app.schemas.intelligence import Citation, PropertyMatch


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    evidence: list[str]
    inference: str
    action: str
    model: str = "local-extractive-grounded"


class GroundedAnswerGenerator:
    """Offline answer composer that can only quote supplied structured evidence."""

    def generate(
        self,
        query: str,
        base_answer: str,
        citations: list[Citation],
        properties: list[PropertyMatch],
    ) -> GroundedAnswer:
        if not citations:
            return GroundedAnswer(
                answer="The system could not retrieve enough evidence to answer confidently.",
                evidence=[],
                inference="No supported inference was generated.",
                action="Collect more applicant or property evidence before acting.",
            )
        evidence = [f"[{citation.citation_id}] {citation.excerpt}" for citation in citations[:3]]
        if _is_unsupported_fact_question(query, citations):
            return GroundedAnswer(
                answer="The available synthetic records do not establish that fact. No retrieved evidence supports a confident answer.",
                evidence=evidence,
                inference="No supported inference was generated.",
                action="Do not act on this claim; collect a source record that explicitly establishes it.",
            )
        top = properties[0] if properties else None
        inference = "The retrieved evidence supports the operational answer, but does not prove future conversion."
        if top:
            inference = f"The strongest retrieved match is {top.property.property_id} at {top.match_score}% based on the existing explainable matcher."
        action = "Use the cited evidence to decide the next contact or viewing step."
        if top:
            action = f"Prioritize {top.property.property_id} and verify the cited objections before contacting the applicant."
        return GroundedAnswer(
            answer=f"Retrieved evidence supports this assessment: {' '.join(evidence)}",
            evidence=evidence,
            inference=inference,
            action=action,
        )


def _is_unsupported_fact_question(query: str, citations: list[Citation]) -> bool:
    normalized = query.lower().strip()
    fact_question = normalized.startswith(("did ", "does ", "what was ", "what is ", "what school ", "where does "))
    if not fact_question:
        return False
    ignored = {"did", "tell", "the", "agent", "say", "said", "what", "was", "is", "does", "where", "does", "sarah", "exact", "her", "she"}
    number_words = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
    query_terms = {term for term in re.findall(r"[a-z0-9]+", normalized) if term not in ignored and term not in number_words and not term.isdigit() and len(term) > 2}
    evidence_text = " ".join(citation.excerpt.lower() for citation in citations)
    evidence_terms = set(re.findall(r"[a-z0-9]+", evidence_text))
    return bool(query_terms) and not query_terms.intersection(evidence_terms)
