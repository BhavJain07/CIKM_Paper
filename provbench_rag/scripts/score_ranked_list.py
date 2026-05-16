"""Re-score candidate documents with PACER; semantic term from BM25 scores."""

from __future__ import annotations

import argparse
import json

from provbench_rag.io import iter_jsonl
from provbench_rag.provenance.scoring import pacerscore_normalized
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.schema import DocumentRecord, QueryRecord


def _minmax(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    lo = min(scores.values())
    hi = max(scores.values())
    span = max(hi - lo, 1e-12)
    return {k: (v - lo) / span for k, v in scores.items()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("documents_jsonl")
    ap.add_argument("queries_jsonl")
    ap.add_argument("--pool-k", type=int, default=50, help="BM25 pool size before PACER rerank")
    ap.add_argument("--out-k", type=int, default=20)
    args = ap.parse_args(argv)

    docs = {d.doc_id: d for d in iter_jsonl(args.documents_jsonl, DocumentRecord)}
    index = BM25Index()
    for d in docs.values():
        index.add_document(d.doc_id, d.text)

    for q in iter_jsonl(args.queries_jsonl, QueryRecord):
        raw = {did: s for did, s in index.score(q.query_text)[: args.pool_k]}
        sem = _minmax(raw)
        rows = []
        for did, s_sem in sem.items():
            d = docs[did]
            rows.append(
                {
                    "doc_id": d.doc_id,
                    "s_sem": s_sem,
                    "pacer_norm": pacerscore_normalized(d, q, s_sem),
                    "cluster_id": d.cluster_id,
                }
            )
        rows.sort(key=lambda r: r["pacer_norm"], reverse=True)
        print(json.dumps({"query_id": q.query_id, "ranked": rows[: args.out_k]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
