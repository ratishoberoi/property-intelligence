# Final CTO Audit

## Scope

Property Intelligence is a local-first portfolio demonstration using synthetic estate-agency data. It has two role-based demo workspaces: an agency operations workspace and a Sarah Mitchell client workspace. Role selection is demo navigation, not production authentication.

## Architecture inventory

- **Frontend:** Next.js App Router, React, TypeScript, CSS design system, role-aware `AppShell`.
- **API:** FastAPI routes for applicants, properties, dashboard, matching, intelligence, agents, search, RAG, provenance and persisted workflow.
- **Database:** SQLAlchemy models with SQLite by default and PostgreSQL/pgvector Docker configuration. Tables are created at startup with `Base.metadata.create_all`; no Alembic revision files currently exist.
- **ML:** Explainable matching engine, synthetic intent classifier, conversion scorer and policy-based next-best-action engine.
- **RAG:** Documents are generated from applicant/property profiles, conversations, interactions and feedback. The persisted index stores BGE vectors and TF-IDF artifacts; query-time retrieval merges semantic and lexical candidates, reranks and produces citations.
- **Grounding:** The default answer layer is deterministic and extractive. It can only formulate an answer from supplied citations and refuses unsupported fact questions. Optional LLM adapters exist but are not required for the default demo.
- **Workflow:** `ClientPreference`, `SavedProperty`, `ViewingRequest`, `Application` and `ActivityEvent` persist the shared client/agency loop. Client question requests also create a conversation and interaction event.
- **Provenance:** Citation IDs map to cached retrieval chunks and source table/record lookup through `/api/rag/provenance/{citation_id}`.

## Data flow

`synthetic CSV → seed database → RAG ingestion → BGE/TF-IDF index → hybrid retrieval → reranking → citation/provenance → grounded answer`

`client action → workflow API → SQLite/Postgres → agency inbox/timeline → agency status action → client state`

## Known release boundaries

1. Demo role selection does not provide authentication or authorization suitable for production.
2. Workflow client access is deliberately scoped to `A-DEMO-SARAH`; a real deployment needs identity-backed authorization.
3. Schema changes use startup `create_all`; production deployment needs versioned Alembic migrations.
4. Docker Compose is present, but this host has Docker Engine without the Compose plugin, so Docker runtime verification is blocked here.
5. Matching evaluation is based on synthetic rule labels and remains weaker than the retrieval evaluation; it is a regression signal, not business validation.

## Runtime audit evidence

- Python `3.12.3`, Node `18.19.1`, npm `9.2.0`.
- NVIDIA `GeForce RTX 5090`; CUDA available; PyTorch CUDA available.
- Index: `6503` chunks, `768` dimensions, `BAAI/bge-base-en-v1.5`, CUDA; recorded build time `3.078s`.
- First live BGE query after process startup measured about `7.2s` including model load; warmed concurrent queries measured approximately `228–388ms`.
- A concurrent query audit initially found and fixed a provider initialization race that could combine a 384-dimension fallback query with the 768-dimension index and return `500`. After the fix, all 12 queries returned `200` with `semantic_available=true`.
- A 15-query agency search audit returned `15/15` HTTP `200`; the Tesla query refused as expected. Sequential average latency was `759.3ms`, with first model load dominating the maximum.
- On a clean process, `/health` measured approximately `9ms` and the client workflow state approximately `15ms`. Repeated server-rendered intelligence page navigation can saturate the single local Uvicorn worker while models are evaluating; use multiple workers or an async job/model-serving boundary for a multi-user deployment.

### RAG query audit

| Query class | Result | Citation | Grounded/refused |
|---|---|---:|---|
| Match explanation | Retrieved property, preference and viewing evidence | 5 | Grounded |
| Transport links | Retrieved property and commute evidence | 5 | Grounded |
| Amenities | Retrieved property profile evidence | 5 | Grounded |
| Recommendation rationale | Retrieved Sarah/property evidence | 5 | Grounded |
| Conversation history | Retrieved conversation records | 5 | Grounded |
| Budget | Retrieved property/applicant evidence | 5 | Grounded |
| Bedrooms | Retrieved property profile evidence | 5 | Grounded |
| Applicant concerns | Retrieved property/applicant evidence | 5 | Grounded |
| Tesla ownership | No supporting evidence | 5 | Refused |
| Exact salary | No supporting evidence | 5 | Refused |
| Child's school | No supporting evidence | 5 | Refused |
| Two dogs | No supporting evidence | 5 | Refused |

Offline metrics: Recall@5 `0.4896`, Recall@10 `0.7188`, MRR `0.8264`, NDCG@5 `0.5294`, NDCG@10 `0.6171`, citation coverage `1.0`, groundedness `1.0`, unsupported-claim rate `0.0`, evaluated retrieval latency `771.29ms`.

### Provenance proof

For the Sarah/P-DEMO-01 query, five live citations were traced through `/api/rag/provenance/{citation_id}`. C01→conversation `C-1`, C02→conversation `C-3`, C03→conversation `C-5`, C04→conversation `C-4`, and C05→interaction `I-1`; each returned original source text, generated document, chunk ID, index position and retrieval scores.

## Audit commands

```bash
make test
make eval
make rag-provenance
```

The live demo runs at `http://localhost:3000`; API health is `http://localhost:8000/health`.

## Release verdict

The local functional loop, RAG provenance chain, API workflow states, responsive route matrix and production image builds are verified. This is **ready for a controlled local CTO demo**, not a production deployment: demo role selection is not authentication, migrations are not versioned, Docker Compose is unavailable on the audit host, and repeated SSR intelligence navigation should be moved behind a multi-worker/async serving boundary before broader use.
