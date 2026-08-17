from collections import Counter
import re


TOKEN_RE = re.compile(r"[a-z0-9]+")


def _terms(text: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(text.lower()))


class HybridReranker:
    def rerank(self, query: str, hits: list[tuple[dict, float]]) -> list[tuple[dict, float]]:
        q_terms = _terms(query)
        scored: list[tuple[dict, float]] = []
        for chunk, semantic in hits:
            text_terms = _terms(chunk.get("text", ""))
            lexical = sum(min(text_terms[t], count) for t, count in q_terms.items()) / max(len(q_terms), 1)
            metadata_boost = 0.04 if any(term in (chunk.get("source", "").lower()) for term in q_terms) else 0.0
            scored.append((chunk, semantic * 0.78 + lexical * 0.18 + metadata_boost))
        return sorted(scored, key=lambda item: item[1], reverse=True)
