from __future__ import annotations

import logging
from threading import Lock
import numpy as np
import torch
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize
from app.config import get_settings

logger = logging.getLogger(__name__)
_provider: EmbeddingProvider | None = None
_provider_lock = Lock()


class EmbeddingProvider:
    """Embeds text with sentence-transformers when available, otherwise deterministic hashing vectors."""

    def __init__(self, model_name: str, device: str = "auto", batch_size: int = 256):
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self.device = "cuda" if device == "auto" and torch.cuda.is_available() else device
        if self.device == "auto":
            self.device = "cpu"
        self.fallback = HashingVectorizer(n_features=384, alternate_sign=False, norm="l2")
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name, device=self.device)
            self.provider = "sentence-transformers"
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as exc:
            logger.warning("Embedding model unavailable; using hashing fallback", extra={"extra": {"error": str(exc)}})
            self.provider = "hashing"
            self.dimension = 384

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        if self.model is not None:
            encoded_texts = texts
            if self.model_name.lower().startswith("baai/bge"):
                encoded_texts = [
                    text if text.startswith("Represent this sentence") else f"Represent this sentence for searching relevant passages: {text}"
                    for text in texts
                ]
            vectors = self.model.encode(
                encoded_texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return np.asarray(vectors, dtype=np.float32)
        return normalize(self.fallback.transform(texts)).toarray().astype(np.float32)


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is not None:
        return _provider
    with _provider_lock:
        if _provider is not None:
            return _provider
        settings = get_settings()
        _provider = EmbeddingProvider(settings.embedding_model, settings.embedding_device, settings.embedding_batch_size)
        return _provider
