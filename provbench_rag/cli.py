"""Thin CLI entry for `provbench` console script."""

from __future__ import annotations

import sys


def main() -> None:
    print("Use module invocations, e.g.:")
    print("  python -m provbench_rag.scripts.validate_jsonl <path> document")
    print("  python -m provbench_rag.scripts.run_baselines <documents.jsonl> <queries.jsonl>")
    sys.exit(0)


if __name__ == "__main__":
    main()
