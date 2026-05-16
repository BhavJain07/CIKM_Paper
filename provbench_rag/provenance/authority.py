"""Authority compatibility s_auth(d, q): higher when document authority matches query needs."""

from __future__ import annotations

from provbench_rag.schema import DocumentRecord, QueryRecord


def authority_score(document: DocumentRecord, _query: QueryRecord) -> float:
    """Map authority_level (1..5) to [0,1]. Extend with query-side authority hints when annotated."""
    return (document.authority_level - 1) / 4.0


def authority_score_normalized_vs_cluster(
    document: DocumentRecord,
    cluster_max_authority: int,
    cluster_min_authority: int,
) -> float:
    """Relative authority within cluster: 1.0 at max, 0.0 at min."""
    span = max(cluster_max_authority - cluster_min_authority, 1)
    return (document.authority_level - cluster_min_authority) / span
