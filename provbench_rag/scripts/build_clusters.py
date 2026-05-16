"""Build clusters.jsonl from documents.jsonl (one cluster row per distinct cluster_id)."""

from __future__ import annotations

import argparse
from collections import defaultdict

from provbench_rag.io import iter_jsonl, write_jsonl
from provbench_rag.schema import ClusterRecord, DocumentRecord


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("documents_jsonl", help="documents.jsonl path")
    ap.add_argument("out_clusters_jsonl", help="output clusters.jsonl path")
    ap.add_argument(
        "--relation-type",
        default="original_vs_copy",
        choices=[
            "original_vs_copy",
            "fresh_vs_stale",
            "authority_split",
            "jurisdiction_mismatch",
            "conflict",
        ],
    )
    args = ap.parse_args(argv)

    by_cluster: dict[str, list[str]] = defaultdict(list)
    canonical: dict[str, str] = {}
    for doc in iter_jsonl(args.documents_jsonl, DocumentRecord):
        by_cluster[doc.cluster_id].append(doc.doc_id)
        if doc.original_or_copy_label == "original":
            canonical[doc.cluster_id] = doc.doc_id

    clusters: list[ClusterRecord] = []
    for cid, doc_ids in sorted(by_cluster.items()):
        clusters.append(
            ClusterRecord(
                cluster_id=cid,
                relation_type=args.relation_type,
                document_ids=sorted(doc_ids),
                canonical_source_id=canonical.get(cid),
            )
        )
    write_jsonl(args.out_clusters_jsonl, clusters)
    print(f"Wrote {len(clusters)} clusters to {args.out_clusters_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
