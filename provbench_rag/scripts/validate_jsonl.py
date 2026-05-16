"""Validate JSONL annotation files against the ProvBench schema."""

from __future__ import annotations

import argparse
import sys

from provbench_rag.io import iter_jsonl
from provbench_rag.schema import ClusterRecord, DocumentRecord, QueryRecord


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="Path to .jsonl file")
    p.add_argument("kind", choices=["document", "query", "cluster"])
    args = p.parse_args(argv)

    model = {
        "document": DocumentRecord,
        "query": QueryRecord,
        "cluster": ClusterRecord,
    }[args.kind]

    n = 0
    for rec in iter_jsonl(args.path, model):
        _ = rec
        n += 1
    print(f"OK: validated {n} {args.kind} records from {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
