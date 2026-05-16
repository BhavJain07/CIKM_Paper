"""PACER-style linear combination of provenance signals."""

from __future__ import annotations

from dataclasses import dataclass

from provbench_rag.provenance import authority, freshness, jurisdiction, originality
from provbench_rag.schema import DocumentRecord, QueryRecord


@dataclass(frozen=True)
class PACERWeights:
    alpha: float = 1.0  # semantic (caller supplies)
    beta: float = 1.0
    gamma: float = 1.0
    delta: float = 1.0
    eta: float = 1.0


def pacerscore_components(
    document: DocumentRecord,
    query: QueryRecord,
    semantic_relevance: float,
) -> dict[str, float]:
    """Return named components in [0,1] before weighting."""
    return {
        "s_sem": max(0.0, min(1.0, semantic_relevance)),
        "s_auth": authority.authority_score(document, query),
        "s_fresh": freshness.freshness_score(document, query),
        "s_orig": originality.originality_score(document, query),
        "s_jur": jurisdiction.jurisdiction_score(document, query),
    }


def pacerscore_document(
    document: DocumentRecord,
    query: QueryRecord,
    semantic_relevance: float,
    weights: PACERWeights | None = None,
) -> float:
    """
    s(d|q) = α s_sem + β s_auth + γ s_fresh + δ s_orig + η s_jur (unnormalized sum).
    Caller can softmax or divide by (α+β+γ+δ+η) for a probability-like score.
    """
    w = weights or PACERWeights()
    c = pacerscore_components(document, query, semantic_relevance)
    return (
        w.alpha * c["s_sem"]
        + w.beta * c["s_auth"]
        + w.gamma * c["s_fresh"]
        + w.delta * c["s_orig"]
        + w.eta * c["s_jur"]
    )


def pacerscore_normalized(
    document: DocumentRecord,
    query: QueryRecord,
    semantic_relevance: float,
    weights: PACERWeights | None = None,
) -> float:
    w = weights or PACERWeights()
    denom = w.alpha + w.beta + w.gamma + w.delta + w.eta
    return pacerscore_document(document, query, semantic_relevance, weights) / denom
