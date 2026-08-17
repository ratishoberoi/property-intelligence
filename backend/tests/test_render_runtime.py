import os
import subprocess
import sys

from fastapi.testclient import TestClient

from app.main import app
from app.rag.provenance import get_provenance
from app.rag.retrieval import RetrievalService


def test_app_import_does_not_initialize_torch_or_sentence_transformers():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(__file__))
    result = subprocess.run(
        [sys.executable, "-c", "import sys; from app.main import app; assert 'torch' not in sys.modules; assert 'sentence_transformers' not in sys.modules"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_rag_status_reports_unloaded_model_without_initializing_it():
    response = TestClient(app).get("/api/rag/status")
    assert response.status_code == 200
    body = response.json()
    assert body["embedding"]["loaded"] is False
    assert body["embedding"]["model_loaded"] is False


def test_lexical_render_rag_returns_citations_and_provenance(db):
    citations = RetrievalService(db).query("Why is Sarah a strong candidate for this property?", limit=3, applicant_id="A-T1", property_id="P-T1")
    assert citations
    assert all(citation.synthetic and citation.indexed for citation in citations)
    provenance = get_provenance(db, citations[0].citation_id)
    assert provenance["source_record_id"] in {"A-T1", "P-T1"}
    assert provenance["rag_chunk"]["chunk_text"]


def test_search_and_adversarial_refusal_are_available_in_render_mode():
    client = TestClient(app)
    search = client.post(
        "/api/search",
        json={"query": "Why is Sarah a strong candidate for this property?", "applicant_id": "A-T1", "property_id": "P-T1", "limit": 3},
    )
    assert search.status_code == 200
    assert search.json()["citations"]

    refusal = client.post(
        "/api/search",
        json={"query": "Did Sarah say she owns a Tesla?", "applicant_id": "A-T1", "property_id": "P-T1", "limit": 3},
    )
    assert refusal.status_code == 200
    assert "do not establish" in refusal.json()["answer"].lower()
