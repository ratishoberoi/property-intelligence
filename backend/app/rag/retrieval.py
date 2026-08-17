from __future__ import annotations

import pickle
import re
import time
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.rag.citations import citation_from_chunk
from app.rag.embeddings import get_embedding_provider
from app.rag.ingestion import build_documents_from_db
from app.rag.reranker import HybridReranker
from app.rag.provenance import register
from app.schemas.intelligence import Citation


class RetrievalService:
    """Local hybrid retriever with metadata filtering and citation generation."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.reranker = HybridReranker()
        self._chunks: list[dict] | None = None
        self._vectors: np.ndarray | None = None
        self._lexical_vectorizer: TfidfVectorizer | None = None
        self._lexical_matrix: csr_matrix | None = None
        self.last_metadata: dict = {}
        self._load_or_build()

    def query(
        self,
        query: str,
        limit: int = 5,
        applicant_id: str | None = None,
        property_id: str | None = None,
        document_types: list[str] | None = None,
    ) -> list[Citation]:
        started = time.perf_counter()
        chunks, vectors, lexical_matrix = self._filtered(applicant_id, property_id, document_types)
        if not chunks:
            self.last_metadata = {"query": query, "filtered_chunks": 0, "returned": 0, "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
            return []
        q_vec = get_embedding_provider().embed([query])[0]
        semantic_available = q_vec.shape[0] == vectors.shape[1]
        if not semantic_available:
            # A stale or unavailable embedding provider must not crash search. Lexical
            # retrieval remains usable while the index/model is repaired or rebuilt.
            q_vec = np.zeros(vectors.shape[1], dtype=np.float32)
        semantic_scores = vectors @ q_vec
        lexical_scores = self._lexical_scores(query, chunks, lexical_matrix)
        candidate_count = max(limit * 8, 40)
        candidate_indices = set(np.argsort(semantic_scores)[::-1][:candidate_count].tolist())
        candidate_indices.update(np.argsort(lexical_scores)[::-1][:candidate_count].tolist())
        hits = []
        for idx in candidate_indices:
            semantic_score = float(semantic_scores[idx])
            lexical_score = float(lexical_scores[idx])
            hybrid = 0.90 * semantic_score + 0.10 * lexical_score
            chunk = dict(chunks[idx])
            chunk.update({"_semantic_score": semantic_score, "_lexical_score": lexical_score, "_hybrid_score": hybrid})
            hits.append((chunk, hybrid))
        reranked = self.reranker.rerank(query, hits)
        unique: list[tuple[dict, float]] = []
        seen: set[str] = set()
        for chunk, score in reranked:
            content_key = re.sub(r"\s+", " ", str(chunk.get("text") or "").strip().lower())
            key = f"{chunk.get('document_type', 'unknown')}:{content_key}"
            if key in seen:
                continue
            seen.add(key)
            unique.append((chunk, score))
            if len(unique) >= limit:
                break
        citations = []
        for index, (chunk, score) in enumerate(unique, start=1):
            chunk["citation_index"] = index
            chunk["_selection_reason"] = "Hybrid semantic/lexical candidate with metadata filtering and reranking."
            citation = citation_from_chunk(chunk, score)
            citations.append(citation)
            register(citation, chunk)
        self.last_metadata = {
            "query": query,
            "filtered_chunks": len(chunks),
            "semantic_candidates": min(candidate_count, len(chunks)),
            "lexical_candidates": min(candidate_count, len(chunks)),
            "merged_candidates": len(hits),
            "returned": len(citations),
            "top_k": limit,
            "strategy": "BGE semantic + TF-IDF lexical + hybrid reranker",
            "embedding_model": get_embedding_provider().model_name,
            "embedding_device": get_embedding_provider().device,
            "embedding_dimension": get_embedding_provider().dimension,
            "semantic_available": semantic_available,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        return citations

    def _load_or_build(self) -> None:
        index_path = self.settings.model_dir / "rag_index.pkl"
        if index_path.exists():
            try:
                with index_path.open("rb") as fh:
                    payload = pickle.load(fh)
                self._chunks = payload["chunks"]
                self._vectors = payload["vectors"]
                self._lexical_vectorizer = payload.get("lexical_vectorizer")
                self._lexical_matrix = payload.get("lexical_matrix")
                return
            except Exception:
                pass
        self._chunks = build_documents_from_db(self.db)
        texts = [chunk["text"] for chunk in self._chunks]
        self._vectors = get_embedding_provider().embed(texts)
        self._lexical_vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, norm="l2").fit(texts)
        self._lexical_matrix = self._lexical_vectorizer.transform(texts)

    def _lexical_scores(self, query: str, chunks: list[dict], lexical_matrix: csr_matrix | None) -> np.ndarray:
        if self._lexical_vectorizer is None or lexical_matrix is None:
            return np.zeros(len(chunks), dtype=np.float32)
        query_vector = self._lexical_vectorizer.transform([query])
        scores = (lexical_matrix @ query_vector.T).toarray().ravel()
        return scores.astype(np.float32)

    def _filtered(
        self,
        applicant_id: str | None,
        property_id: str | None,
        document_types: list[str] | None,
    ) -> tuple[list[dict], np.ndarray, csr_matrix | None]:
        assert self._chunks is not None and self._vectors is not None
        idxs: list[int] = []
        for idx, chunk in enumerate(self._chunks):
            if applicant_id and chunk.get("applicant_id") not in {applicant_id, None}:
                continue
            if property_id and chunk.get("property_id") not in {property_id, None}:
                continue
            if document_types and chunk.get("document_type") not in document_types:
                continue
            idxs.append(idx)
        return (
            [self._chunks[i] for i in idxs],
            self._vectors[idxs] if idxs else np.zeros((0, self._vectors.shape[1])),
            self._lexical_matrix[idxs] if idxs and self._lexical_matrix is not None else None,
        )
