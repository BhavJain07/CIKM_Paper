"""Paired significance tests for query-level binary / score differences."""

from __future__ import annotations

import math
from collections.abc import Sequence


def mcnemar_exact_two_sided(model_a_correct: Sequence[bool], model_b_correct: Sequence[bool]) -> float:
    """
    Exact two-sided McNemar p-value for correlated binary outcomes (mid-p not applied).
    Contingency: n01 = A wrong & B right; n10 = A right & B wrong; ignore concordant pairs.
    """
    if len(model_a_correct) != len(model_b_correct):
        raise ValueError("length mismatch")
    n01 = n10 = 0
    for a, b in zip(model_a_correct, model_b_correct, strict=True):
        if a and not b:
            n10 += 1
        elif b and not a:
            n01 += 1
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)

    def binom_cdf(t: int) -> float:
        s = 0.0
        for i in range(0, t + 1):
            s += math.comb(n, i) * (0.5**n)
        return s

    tail = binom_cdf(k)
    return min(1.0, 2 * tail)


def wilcoxon_signed_rank_normal_approx(
    diffs: Sequence[float],
) -> tuple[float, float]:
    """
    Wilcoxon signed-rank test using normal approximation (no ties correction).
    Returns (z_statistic, two_sided_p_approx).
    """
    vals = [float(d) for d in diffs if d != 0.0]
    if not vals:
        return 0.0, 1.0
    ranks = _average_ranks([abs(v) for v in vals])
    wplus = sum(r for r, v in zip(ranks, vals, strict=True) if v > 0)
    n = len(vals)
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24
    if var <= 0:
        return 0.0, 1.0
    z = (wplus - mean) / math.sqrt(var)
    # Two-sided normal approximation: p = 2(1 - Phi(|z|)) = 1 - erf(|z|/sqrt(2))
    p = max(0.0, min(1.0, 1.0 - math.erf(abs(z) / math.sqrt(2))))
    return z, p


def _average_ranks(abs_vals: list[float]) -> list[float]:
    indexed = sorted(enumerate(abs_vals), key=lambda x: x[1])
    ranks = [0.0] * len(abs_vals)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg
        i = j + 1
    return ranks
