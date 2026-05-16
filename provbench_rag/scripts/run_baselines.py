"""Run BM25 baseline retrieval and report retrieval + provenance metrics."""

from __future__ import annotations

import argparse

from provbench_rag.baselines.naive_rag import retrieve_bm25_topk
from provbench_rag.evaluation.provenance_metrics import preferred_source_accuracy, provenance_f1
from provbench_rag.evaluation.retrieval_metrics import ndcg_at_k, recall_at_k
from provbench_rag.evaluation.support_metrics import sufficiency_score
from provbench_rag.io import iter_jsonl
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.schema import DocumentRecord, QueryRecord


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("documents_jsonl")
    ap.add_argument("queries_jsonl")
    ap.add_argument("--k", type=int, default=10)
    args = ap.parse_args(argv)

    docs = {d.doc_id: d for d in iter_jsonl(args.documents_jsonl, DocumentRecord)}
    index = BM25Index()
    for d in docs.values():
        index.add_document(d.doc_id, d.text)

    psa: list[float] = []
    suff: list[float] = []
    ndcgs: list[float] = []
    recalls: list[float] = []
    prov_f1: list[float] = []
    for q in iter_jsonl(args.queries_jsonl, QueryRecord):
        ranked = retrieve_bm25_topk(index, q.query_text, args.k)
        rel = set(q.gold_evidence_ids)
        recalls.append(recall_at_k(ranked, rel, args.k))
        ndcgs.append(ndcg_at_k(ranked, rel, args.k))
        suff.append(sufficiency_score(ranked, q.gold_evidence_ids))
        psa.append(preferred_source_accuracy(ranked[:1], q.preferred_source_ids))
        prov_f1.append(provenance_f1(ranked[:3], q.preferred_source_ids)[2])
    n = max(len(psa), 1)
    print(
        {
            "queries": n,
            "recall_at_k_mean": sum(recalls) / n,
            "ndcg_at_k_mean": sum(ndcgs) / n,
            "psa_at_1_mean": sum(psa) / n,
            "sufficiency_mean": sum(suff) / n,
            "provenance_f1_at_3_mean": sum(prov_f1) / n,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
