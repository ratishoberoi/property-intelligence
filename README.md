# Property Intelligence

Property Intelligence is a local-first, two-sided property intelligence demo connecting a property seeker with an estate-agency operations team. It turns synthetic applicant behaviour, property records, conversations and feedback into explainable matches, grounded evidence and next-best actions.

> This repository uses synthetic demonstration data and does not contain real customer data.

## What it does

### Client workspace

- Complete a preference profile.
- Receive explainable property matches.
- Save properties, ask grounded property questions, request viewings and submit applications.
- See agency confirmations and application status updates.

### Agency workspace

- Review applicants, properties, demand and operational metrics.
- See persisted viewing requests, applications and client questions.
- Inspect applicant intelligence, intent, conversion signals, matches and next-best actions.
- Search the agency dataset in natural language with citations and source provenance.

## Local demo

Requirements: Python 3.12+, Node 18+, npm, and the repository virtual environment.

```bash
cd property-intelligence
python3 -m venv .venv
./.venv/bin/pip install -r backend/requirements.txt
./.venv/bin/pip install -r backend/requirements-embeddings.txt
make generate seed train index
cd frontend && npm install
```

Start the backend in one terminal:

```bash
cd property-intelligence/backend
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Start the frontend in another:

```bash
cd property-intelligence/frontend
npm run dev -- --hostname 0.0.0.0 --port 3000
```

URLs:

- Product: `http://localhost:3000`
- Client: `http://localhost:3000/client`
- Agency: `http://localhost:3000/agency`
- Agency requests: `http://localhost:3000/agency/requests`
- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

There is no production authentication in this portfolio demo. Landing-page role selection is explicitly demo access: Agency workspace or Sarah Mitchell Client workspace.

## Free CTO demo deployment

The zero-cost deployment target is Vercel Free plus a Render Free Web Service.
The Render service intentionally uses `RAG_EMBEDDING_MODE=lexical` because the
measured CPU BGE path reaches approximately 1.1 GB RSS after one query, above
Render Free's 512 MB limit. This does **not** remove RAG: Render still loads
the persisted 6,503-chunk source index, performs TF-IDF retrieval, domain
reranking, grounded answers, citations and provenance. The complete BGE
semantic/hybrid path remains the default local runtime and is selected with
`RAG_EMBEDDING_MODE=semantic` plus the embedding dependencies.

Render build command:

```bash
pip install -r backend/requirements-render.txt && cd backend && python scripts/seed_database.py && test -f ../models/rag_index.pkl && test -f ../models/intent_model.joblib && test -f ../models/conversion_model.joblib
```

Render start command:

```bash
cd backend && python -c "from app.db.session import SessionLocal; from app.db.models import Applicant, Property; from sqlalchemy import func, select; db=SessionLocal(); empty=(db.scalar(select(func.count()).select_from(Applicant)) or 0)==0 or (db.scalar(select(func.count()).select_from(Property)) or 0)==0; db.close(); raise SystemExit(1 if empty else 0)" || python scripts/seed_database.py; exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Set `CORS_ORIGINS` to the exact Vercel URL (the checked-in Render blueprint
already sets `https://property-intelligence-pearl.vercel.app`). In Vercel set
`NEXT_PUBLIC_API_BASE_URL` and `INTERNAL_API_BASE_URL` to the Render HTTPS URL.
The backend also repairs an empty SQLite database on startup from the committed
synthetic CSVs, which prevents a zero-byte or empty deployment database from
breaking server-rendered agency pages.
The complete checklist is in [docs/DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md).
SQLite is acceptable for this synthetic CTO demo because the dataset is
reseedable; it is not durable production storage and workflow changes can be
lost on service replacement or redeploy.

## CTO demo flow

1. Open the landing page and enter Client.
2. Complete Sarah’s preferences and open `P-DEMO-01`.
3. Ask `Does this property have good transport?`; inspect the grounded answer.
4. Save the property and request a viewing.
5. Switch to Agency → Requests and confirm the viewing.
6. Open Sarah’s applicant profile and show the persisted activity.
7. Return to Client and show `Viewing confirmed`.
8. Submit an application, update it from Agency, and show the client status.
9. Ask an adversarial question such as `What is Sarah's exact salary?` and demonstrate refusal.
10. Reset the demo with `POST /api/workflow/reset` or the documented reset control when available.

## Architecture

```mermaid
flowchart LR
  Client[Client workspace] --> UI[Next.js]
  Agency[Agency workspace] --> UI
  UI --> API[FastAPI]
  API --> DB[(SQLite/PostgreSQL)]
  API --> Match[Matching + intent + conversion]
  API --> Orch[Agent orchestrator]
  Orch --> RAG[Hybrid RAG + provenance]
  Orch --> NBA[Next Best Action]
```

See [the full architecture](docs/ARCHITECTURE.md), including client→agency sequence, RAG, provenance, data model and deployment diagrams.

## RAG

Synthetic database records are converted into property profiles, applicant profiles, conversations, interaction history and viewing feedback. The local index uses `BAAI/bge-base-en-v1.5` embeddings plus TF-IDF lexical retrieval. Query candidates are merged, metadata-filtered, hybrid-scored, reranked and returned as citations. `/api/rag/provenance/{citation_id}` maps a citation back to its source table, source record, original text, generated document, indexed chunk and retrieval scores.

The default answer layer is deterministic and grounded in the returned citations. Unsupported fact questions are qualified/refused rather than invented. Optional local LLM adapters exist, but no paid API is required.

## Evaluation

Run:

```bash
make test
make eval
make rag-provenance
```

The current synthetic evaluation baseline records approximately: RAG Recall@5 `0.4896`, Recall@10 `0.7188`, MRR `0.8264`, NDCG@5 `0.5294`, NDCG@10 `0.6171`, citation coverage `1.0`, groundedness `1.0`, unsupported-claim rate `0.0`. Matching metrics are synthetic-label regression signals and are not production-calibrated business metrics.

## Data and artifacts

`make generate` creates the deterministic synthetic CSV dataset. `make seed` loads it into SQLite/PostgreSQL. `make train` trains local synthetic models. `make index` builds the persistent RAG index. The demo reset restores Sarah’s canonical saved property, confirmed viewing and under-review application state without deleting the base synthetic records.

`exports/property_intelligence_demo_dataset.xlsx` is generated from the database and contains an overview plus Applicants, Properties, Preferences, Conversations, Interactions, Viewings, Feedback, Matches, Applications, Saved Properties and Activity Events sheets.

## Limitations

- Demo role selection is not production authentication.
- Workflow client APIs are scoped to Sarah for the demo; production needs identity-backed authorization.
- Database tables currently use SQLAlchemy startup creation; production needs versioned migrations.
- Model probabilities and evaluation labels are synthetic and not production-calibrated.
- GPU BGE inference is appropriate locally, while the Render Free runtime uses the documented memory-safe lexical RAG mode; see [deployment plan](docs/DEPLOYMENT_PLAN.md).
