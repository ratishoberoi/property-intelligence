# RAG Provenance

The RAG corpus is built from the synthetic SQLite database by `backend/app/rag/ingestion.py` and indexed by `backend/scripts/build_index.py`. Every indexed chunk carries:

- `source_table` and `source_record_id`
- applicant/property IDs and timestamp
- channel where the source has one
- original source text
- generated document ID and chunk ID
- index position and `synthetic: true`

`GET /api/rag/provenance/{citation_id}` resolves the citation created by the most recent retrieval in the running process. Supplying `?query=...` allows the endpoint to rerun a query when no in-memory citation exists. Citation labels such as `C01` are query-local rank labels; the durable identity is `source_table` + `source_record_id` + `chunk_id`.

Run `make rag-provenance` for a complete database → document → chunk → retrieval → answer report.

All records are synthetic demonstration data generated deterministically with seed `42`; they are not real customer conversations.
