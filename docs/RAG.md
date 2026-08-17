# RAG

Documents are generated from property descriptions, applicant profiles, conversations, viewing feedback and interaction history.

Chunks include:

- document id
- document type
- applicant id
- property id
- timestamp
- source

Embeddings use `BAAI/bge-base-en-v1.5` through sentence-transformers, with CUDA selected automatically when available. Indexing is batched and persists the embedding model/device metadata. If the optional embedding dependencies are unavailable, the system uses a deterministic hashing-vector fallback and labels it explicitly.

Retrieval supports semantic candidate generation, TF-IDF lexical candidate generation, metadata filtering, hybrid scoring, lexical/domain-aware reranking, deduplication and source citations. The local index is loaded once per process rather than rebuilding embeddings for each request.
