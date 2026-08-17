FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_DIR=/app/models \
    DATA_DIR=/app/data/processed \
    EMBEDDING_DEVICE=cpu \
    HF_HOME=/opt/huggingface \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements-hf.txt ./
RUN pip install --no-cache-dir -r requirements-hf.txt

COPY backend/app ./app
COPY backend/scripts ./scripts
COPY models ./models
COPY data/processed ./data/processed

ARG EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL}

RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
import os

model_name = os.environ["EMBEDDING_MODEL"]
model = SentenceTransformer(model_name, device="cpu")
assert model.get_sentence_embedding_dimension() == 768
print(f"Cached {model_name} ({model.get_sentence_embedding_dimension()} dimensions)")
PY

RUN python - <<'PY'
import pickle
from pathlib import Path

with Path("/app/models/rag_index.pkl").open("rb") as handle:
    payload = pickle.load(handle)
assert len(payload["chunks"]) > 0
assert payload["vectors"].shape[1] == 768
assert payload["embedding_provider"] == "sentence-transformers"
print(f"Validated RAG index: {len(payload['chunks'])} chunks")
PY

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl --fail http://127.0.0.1:${PORT:-7860}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
