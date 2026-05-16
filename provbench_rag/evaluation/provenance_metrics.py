"""Provenance-aware retrieval and citation metrics."""

from __future__ import annotations

from collections.abc import Iterable


def preferred_source_accuracy(
    cited_doc_ids: Iterable[str],
    preferred_source_ids: list[str],
) -> float:
    """
    1.0 if any cited doc is in preferred set; else 0.0.
    For ranked lists, call with top-1 slice or use MRR variant separately.
    """
    cited = set(cited_doc_ids)
    pref = set(preferred_source_ids)
    return 1.0 if cited & pref else 0.0


def provenance_f1(
    cited_doc_ids: Iterable[str],
    preferred_source_ids: list[str],
) -> tuple[float, float, float]:
    """
    Treat preferred sources as positive labels for citation set (micro-F1 components).
    Precision = |cited ∩ pref| / |cited|; recall = |cited ∩ pref| / |pref|.
    """
    cited = list(cited_doc_ids)
    cited_set = set(cited)
    pref_set = set(preferred_source_ids)
    if not cited_set and not pref_set:
        return 1.0, 1.0, 1.0
    inter = len(cited_set & pref_set)
    prec = inter / len(cited_set) if cited_set else 0.0
    rec = inter / len(pref_set) if pref_set else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    return prec, rec, f1


def cluster_confusion_rate(
    cited_cluster_ids: list[str],
    gold_cluster_id: str,
) -> float:
    """Fraction of cited items whose cluster differs from gold (0.0 if empty citations)."""
    if not cited_cluster_ids:
        return 0.0
    wrong = sum(1 for c in cited_cluster_ids if c != gold_cluster_id)
    return wrong / len(cited_cluster_ids)


def citation_policy_violation_rates(
    cited_docs: list[dict],
) -> dict[str, float]:
    """
    cited_docs entries may include keys: is_stale, is_unofficial, jurisdiction_mismatch (bool).
    Returns rates in [0,1] over cited_docs.
    """
    n = len(cited_docs)
    if n == 0:
        return {"stale": 0.0, "unofficial": 0.0, "jurisdiction_mismatch": 0.0}

    def rate(key: str) -> float:
        return sum(1 for d in cited_docs if d.get(key)) / n

    return {
        "stale": rate("is_stale"),
        "unofficial": rate("is_unofficial"),
        "jurisdiction_mismatch": rate("jurisdiction_mismatch"),
    }
