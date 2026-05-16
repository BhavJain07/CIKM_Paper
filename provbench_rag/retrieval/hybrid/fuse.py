"""Fuse ranked lists from BM25 and dense retrieval."""

from __future__ import annotations

from collections import defaultdict


def weighted_sum_fusion(
    ranked_a: list[tuple[str, float]],
    ranked_b: list[tuple[str, float]],
    weight_a: float = 0.5,
    weight_b: float = 0.5,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for did, s in ranked_a:
        scores[did] += weight_a * float(s)
    for did, s in ranked_b:
        scores[did] += weight_b * float(s)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, float]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for r, (did, _) in enumerate(ranked, start=1):
            scores[did] += 1.0 / (k + r)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
