"""Generate the synthetic ProvBench-RAG release (documents, clusters, queries)."""

from __future__ import annotations

import argparse

from provbench_rag.synthetic.generator import generate_synthetic_release


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="corpora/annotations/synthetic_v1", help="Output directory")
    ap.add_argument(
        "--instances-per-family",
        type=int,
        default=300,
        help="Each of A–E produces this many clusters (default 300 → 1500 queries).",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)

    stats = generate_synthetic_release(
        args.out,
        instances_per_family=args.instances_per_family,
        seed=args.seed,
    )
    print(
        f"Wrote {stats.documents} documents, {stats.clusters} clusters, "
        f"{stats.queries} queries to {args.out}/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
