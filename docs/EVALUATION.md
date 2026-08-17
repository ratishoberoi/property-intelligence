# Evaluation

Evaluation is mandatory but limited by synthetic data.

Implemented metrics:

- Matching: Precision@10, Recall@10, NDCG@10
- RAG: Recall@5/10, MRR, NDCG@5/10, citation coverage, deterministic answer groundedness, unsupported-claim rate and measured latency.
- Intent: accuracy and macro F1 from training output
- Conversion: ROC-AUC, PR-AUC, precision, recall
- Next Best Action: offline agreement with synthetic ground-truth rules

Limitations:

- Synthetic labels encode assumptions and are not proof of production performance.
- Offline RAG golden questions are small and intended for regression testing.
- Golden questions cover applicant profiles, property attributes, objections, conversations, viewing feedback, application history, budget/location constraints and cross-document reasoning. Relevance is defined as retrieval of at least one expected domain document type for each question; this is a regression signal, not a human preference study.
- No real customer data is included or implied.
