from pathlib import Path

from provbench_rag.experiments.eval_suite import evaluate_methods


def test_evaluate_tiny_dataset(tmp_path: Path):
    from provbench_rag.synthetic.generator import generate_synthetic_release

    d = tmp_path / "d"
    generate_synthetic_release(d, instances_per_family=3, seed=0)
    r = evaluate_methods(
        d / "documents.jsonl",
        d / "queries.jsonl",
        ["bm25", "pacer"],
        k=5,
        pool_k=30,
    )
    assert "bm25" in r["methods"]
    assert "pacer" in r["methods"]
    assert r["methods"]["pacer"]["psa_at_1_non_abstain"] >= r["methods"]["bm25"]["psa_at_1_non_abstain"]
