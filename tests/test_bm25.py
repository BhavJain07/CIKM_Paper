from provbench_rag.retrieval.bm25.index import BM25Index


def test_bm25_orders_by_relevance():
    idx = BM25Index()
    idx.add_document("a", "the cat sat on the mat")
    idx.add_document("b", "quantum chromodynamics phase transitions")
    ranked = idx.score("cat mat")
    assert ranked[0][0] == "a"
