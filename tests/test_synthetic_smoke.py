from pathlib import Path

from provbench_rag.io import iter_jsonl
from provbench_rag.schema import DocumentRecord, QueryRecord
from provbench_rag.synthetic.generator import generate_synthetic_release


def test_generate_small_release(tmp_path: Path):
    out = tmp_path / "syn"
    stats = generate_synthetic_release(out, instances_per_family=2, seed=1)
    assert stats.queries == 10
    assert stats.clusters == 10
    docs = list(iter_jsonl(out / "documents.jsonl", DocumentRecord))
    assert len(docs) >= 10
    qs = list(iter_jsonl(out / "queries.jsonl", QueryRecord))
    assert len(qs) == 10
