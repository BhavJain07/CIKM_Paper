"""Sufficiency and minimality of retrieved evidence sets."""

from __future__ import annotations

from collections.abc import Iterable


def sufficiency_score(retrieved_ids: Iterable[str], gold_evidence_ids: list[str]) -> float:
    """Fraction of gold evidence IDs covered by retrieval (recall of gold support)."""
    gold = set(gold_evidence_ids)
    if not gold:
        return 1.0
    ret = set(retrieved_ids)
    return len(ret & gold) / len(gold)


def minimality_penalty(retrieved_ids: Iterable[str], minimal_evidence_ids: list[str]) -> float:
    """
    Minimality score (higher is better): 1.0 when retrieval is no larger than necessary
    and covers the minimal set; decays as redundant documents are added beyond |M|.
    """
    ret = list(retrieved_ids)
    minimal = set(minimal_evidence_ids)
    if not minimal:
        return 1.0 / (1.0 + max(0, len(ret) - 1))
    covered = len(minimal & set(ret))
    if covered < len(minimal):
        return 0.0
    extra = max(0, len(ret) - len(minimal))
    return 1.0 / (1.0 + extra)


def citation_redundancy_ratio(retrieved_ids: list[str], cluster_id_by_doc: dict[str, str]) -> float:
    """Average number of citations per distinct cluster in retrieved set (1.0 is no redundancy)."""
    if not retrieved_ids:
        return 1.0
    clusters: dict[str, int] = {}
    for did in retrieved_ids:
        cid = cluster_id_by_doc.get(did, "singleton")
        clusters[cid] = clusters.get(cid, 0) + 1
    return len(retrieved_ids) / max(len(clusters), 1)


def prov_score(
    answer_acc: float,
    psa: float,
    suff: float,
    minimality: float,
    abstain: float,
) -> float:
    """Primary combined metric from the paper outline."""
    return 0.25 * answer_acc + 0.25 * psa + 0.20 * suff + 0.15 * minimality + 0.15 * abstain
