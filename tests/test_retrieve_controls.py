"""Control rankers: deterministic random, oracle promotion, semantic-only path."""

from pathlib import Path

import pytest

from provbench_rag.experiments.eval_suite import evaluate_methods
from provbench_rag.methods.retrieve import (
    rank_control_oracle_pool,
    rank_control_random_pool,
    rank_control_semantic_only,
    rank_pacer,
)
from provbench_rag.provenance.scoring import PACERWeights
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.synthetic.generator import generate_synthetic_release


def test_control_random_is_deterministic_per_query(tmp_path: Path):
    d = tmp_path / "d"
    generate_synthetic_release(d, instances_per_family=2, seed=1)
    from provbench_rag.io import iter_jsonl
    from provbench_rag.schema import DocumentRecord, QueryRecord

    docs = {x.doc_id: x for x in iter_jsonl(d / "documents.jsonl", DocumentRecord)}
    queries = list(iter_jsonl(d / "queries.jsonl", QueryRecord))
    index = BM25Index()
    for doc in docs.values():
        index.add_document(doc.doc_id, doc.text)
    q = queries[0]
    a = rank_control_random_pool(index, docs, q, 30, 5)
    b = rank_control_random_pool(index, docs, q, 30, 5)
    assert a == b
    c = rank_control_random_pool(index, docs, queries[1], 30, 5)
    assert a != c or q.query_id == queries[1].query_id


def test_semantic_only_matches_unit_weight_pacer(tmp_path: Path):
    d = tmp_path / "d"
    generate_synthetic_release(d, instances_per_family=2, seed=2)
    from provbench_rag.io import iter_jsonl
    from provbench_rag.schema import DocumentRecord, QueryRecord

    docs = {x.doc_id: x for x in iter_jsonl(d / "documents.jsonl", DocumentRecord)}
    q = list(iter_jsonl(d / "queries.jsonl", QueryRecord))[0]
    index = BM25Index()
    for doc in docs.values():
        index.add_document(doc.doc_id, doc.text)
    w = PACERWeights(alpha=1.0, beta=0.0, gamma=0.0, delta=0.0, eta=0.0)
    a = rank_control_semantic_only(index, docs, q, 40, 10)
    b = rank_pacer(index, docs, q, 40, 10, w)
    assert a == b


def test_oracle_puts_preferred_first_when_in_pool(tmp_path: Path):
    d = tmp_path / "d"
    generate_synthetic_release(d, instances_per_family=8, seed=3)
    from provbench_rag.io import iter_jsonl
    from provbench_rag.schema import DocumentRecord, QueryRecord

    docs = {x.doc_id: x for x in iter_jsonl(d / "documents.jsonl", DocumentRecord)}
    queries = list(iter_jsonl(d / "queries.jsonl", QueryRecord))
    index = BM25Index()
    for doc in docs.values():
        index.add_document(doc.doc_id, doc.text)
    for q in queries:
        if q.abstain_required or not q.preferred_source_ids:
            continue
        pref = q.preferred_source_ids[0]
        pool = {did for did, _ in index.score(q.query_text)[:80]}
        if pref in pool:
            ranked = rank_control_oracle_pool(index, docs, q, 80, 10)
            assert ranked[0] == pref
            return
    pytest.skip("no query with preferred doc in BM25 top-80 pool in this fixture")


def test_get_ranker_accepts_all_control_names(tmp_path: Path):
    d = tmp_path / "d"
    generate_synthetic_release(d, instances_per_family=1, seed=4)
    r = evaluate_methods(
        d / "documents.jsonl",
        d / "queries.jsonl",
        [
            "control_random_pool",
            "control_semantic_only",
            "control_oracle_pool",
            "bm25",
            "pacer",
        ],
        k=3,
        pool_k=20,
    )
    for m in (
        "control_random_pool",
        "control_semantic_only",
        "control_oracle_pool",
        "bm25",
        "pacer",
    ):
        assert m in r["methods"]
    assert r["methods"]["control_oracle_pool"]["psa_at_1_non_abstain"] >= r["methods"]["control_random_pool"][
        "psa_at_1_non_abstain"
    ]
