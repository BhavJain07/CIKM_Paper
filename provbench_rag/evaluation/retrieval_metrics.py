"""Standard IR metrics at cutoff k."""

from __future__ import annotations

import math


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    top = set(retrieved[:k])
    return len(top & relevant) / len(relevant)


def dcg_at_k(relevance_scores: list[float], k: int) -> float:
    scores = relevance_scores[:k]
    return sum((2**rel - 1) / math.log2(i + 2) for i, rel in enumerate(scores))


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    rel_vec = [1.0 if doc in relevant else 0.0 for doc in retrieved[:k]]
    ideal = sorted(rel_vec, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(rel_vec, k) / idcg


def mean_reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for i, doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1.0 / i
    return 0.0
