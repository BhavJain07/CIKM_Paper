from datetime import date

from provbench_rag.evaluation.answer_metrics import exact_match, token_f1
from provbench_rag.evaluation.provenance_metrics import preferred_source_accuracy, provenance_f1
from provbench_rag.evaluation.retrieval_metrics import ndcg_at_k, recall_at_k
from provbench_rag.evaluation.support_metrics import minimality_penalty, prov_score, sufficiency_score
from provbench_rag.provenance.scoring import pacerscore_normalized
from provbench_rag.schema import DocumentRecord, QueryRecord


def test_answer_metrics():
    assert exact_match(" 30 days ", "30 days.")
    assert token_f1("a b c", "b c d") > 0


def test_provenance_metrics():
    assert preferred_source_accuracy(["x", "y"], ["y"]) == 1.0
    prec, rec, f1 = provenance_f1(["y", "z"], ["y"])
    assert f1 > 0


def test_retrieval_metrics():
    rel = {"a", "b"}
    r = ["a", "c", "b", "d"]
    assert recall_at_k(r, rel, 2) == 0.5
    assert ndcg_at_k(r, rel, 3) > 0


def test_support_and_provscore():
    assert sufficiency_score(["a", "b"], ["a"]) == 1.0
    assert minimality_penalty(["a"], ["a"]) == 1.0
    assert minimality_penalty(["a", "b", "c"], ["a"]) < 1.0
    assert prov_score(1, 1, 1, 1, 1) == 1.0


def test_pacer_prefers_official():
    q = QueryRecord(
        query_id="q",
        query_text="t",
        domain="d",
        query_time=date(2024, 9, 1),
        query_jurisdiction="US",
        gold_answer="g",
        acceptable_answers=[],
        gold_evidence_ids=["o"],
        minimal_evidence_ids=["o"],
        preferred_source_ids=["o"],
    )
    official = DocumentRecord(
        doc_id="o",
        cluster_id="c",
        source_url="u",
        source_type="gov",
        authority_level=5,
        publication_date=date(2024, 6, 1),
        validity_start=date(2024, 6, 1),
        validity_end=date(2025, 12, 31),
        jurisdiction="US",
        original_or_copy_label="original",
        text="x",
        paragraph_spans=[],
    )
    blog = official.model_copy(
        update={
            "doc_id": "b",
            "authority_level": 2,
            "original_or_copy_label": "summary",
        }
    )
    s_off = pacerscore_normalized(official, q, 0.8)
    s_blog = pacerscore_normalized(blog, q, 0.8)
    assert s_off > s_blog
