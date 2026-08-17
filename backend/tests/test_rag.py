from app.rag.reranker import HybridReranker


def test_hybrid_reranker_tokenizes_lowercase_and_punctuation():
    hits = [
        ({"text": "Sarah asked about transport, budget, and tenancy terms.", "source": "Conversation"}, 0.4),
        ({"text": "Unrelated property description.", "source": "Property"}, 0.5),
    ]

    ranked = HybridReranker().rerank("What are Sarah's budget objections?", hits)

    assert ranked[0][0]["source"] == "Conversation"
    assert ranked[0][1] > ranked[1][1]
