#!/usr/bin/env python
from __future__ import annotations

import pickle
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{ROOT / 'property_intelligence.db'}"
sys.path.append(str(ROOT))

from app.db.session import SessionLocal
from app.rag.embeddings import get_embedding_provider
from app.rag.ingestion import build_documents_from_db, chunk_text
from sklearn.feature_extraction.text import TfidfVectorizer


def main() -> None:
    model_dir = ROOT.parent / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        docs = build_documents_from_db(db)
        chunks = []
        for doc in docs:
            for idx, text in enumerate(chunk_text(doc["text"], chunk_size=90, overlap=15)):
                chunk = dict(doc)
                chunk["document_id"] = f"{doc['document_id']}:chunk:{idx}"
                chunk["chunk_id"] = chunk["document_id"]
                chunk["index_position"] = len(chunks)
                chunk["text"] = text
                chunks.append(chunk)
        provider = get_embedding_provider()
        texts = [chunk["text"] for chunk in chunks]
        started = time.perf_counter()
        vectors = provider.embed(texts)
        lexical = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, norm="l2").fit(texts)
        lexical_matrix = lexical.transform(texts)
        with (model_dir / "rag_index.pkl").open("wb") as fh:
            pickle.dump({
                "chunks": chunks,
                "vectors": vectors,
                "lexical_vectorizer": lexical,
                "lexical_matrix": lexical_matrix,
                "embedding_provider": provider.provider,
                "embedding_model": provider.model_name,
                "embedding_device": provider.device,
                "embedding_dimension": provider.dimension,
                "index_seconds": round(time.perf_counter() - started, 3),
            }, fh, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Indexed {len(docs)} documents into {len(chunks)} chunks with {provider.provider} on {provider.device} in {time.perf_counter() - started:.2f}s.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
