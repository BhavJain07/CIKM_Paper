"""Paired bootstrap confidence intervals for per-query scalar scores."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "scores_jsonl",
        help="Each line: {\"score\": <float>, ...} (uses `score` field)",
    )
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ci", type=float, default=0.95)
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    scores: list[float] = []
    with Path(args.scores_jsonl).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            scores.append(float(obj["score"]))
    x = np.asarray(scores, dtype=np.float64)
    n = x.shape[0]
    if n == 0:
        print(json.dumps({"error": "no scores"}))
        return 1
    means = []
    for _ in range(args.bootstrap):
        idx = [rng.randrange(0, n) for _ in range(n)]
        means.append(float(x[idx].mean()))
    means.sort()
    low_q = (1 - args.ci) / 2
    high_q = 1 - low_q
    lo = means[int(low_q * len(means))]
    hi = means[int(high_q * len(means)) - 1]
    print(json.dumps({"mean": float(x.mean()), "ci_low": lo, "ci_high": hi, "n": n}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
