"""Emit seed query JSONL lines from clusters (for human refinement)."""

from __future__ import annotations

import argparse
import uuid

from provbench_rag.io import iter_jsonl, write_jsonl
from provbench_rag.schema import ClusterRecord, QueryRecord


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("clusters_jsonl")
    ap.add_argument("out_queries_jsonl")
    args = ap.parse_args(argv)

    queries: list[QueryRecord] = []
    for cl in iter_jsonl(args.clusters_jsonl, ClusterRecord):
        if not cl.document_ids:
            continue
        qid = f"seed_{cl.cluster_id}_{uuid.uuid4().hex[:8]}"
        gold_docs = cl.document_ids[:2]
        pref = [cl.canonical_source_id] if cl.canonical_source_id else [cl.document_ids[0]]
        queries.append(
            QueryRecord(
                query_id=qid,
                query_text=f"What is the authoritative statement for cluster {cl.cluster_id}?",
                domain="documentation_policy_mvp",
                gold_answer="REQUIRES_HUMAN_ANNOTATION",
                acceptable_answers=[],
                gold_evidence_ids=gold_docs,
                minimal_evidence_ids=[gold_docs[0]],
                preferred_source_ids=pref,
                abstain_required=cl.relation_type == "conflict",
            )
        )
    write_jsonl(args.out_queries_jsonl, queries)
    print(f"Wrote {len(queries)} seed queries to {args.out_queries_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
