"""Bootstrap confidence intervals for mean query-level scores."""

from __future__ import annotations

import random

import numpy as np


def bootstrap_mean_ci(
    values: list[float],
    n_bootstrap: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) for the sample mean under bootstrap resampling."""
    arr = np.asarray(values, dtype=np.float64)
    n = arr.shape[0]
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        means[i] = float(arr[idx].mean())
    means.sort()
    alpha = (1 - ci) / 2
    lo = float(means[int(alpha * n_bootstrap)])
    hi = float(means[min(int((1 - alpha) * n_bootstrap) - 1, n_bootstrap - 1)])
    return float(arr.mean()), lo, hi
