"""Concatenate compatible ProvBench JSONL corpora (documents, clusters, queries)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _merge_jsonl(paths: list[Path], out: Path) -> int:
    n = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as wf:
        for p in paths:
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                wf.write(line + "\n")
                n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--tracks",
        nargs="+",
        required=True,
        help="Directories each containing documents.jsonl, clusters.jsonl, queries.jsonl",
    )
    args = ap.parse_args(argv)

    docs_in: list[Path] = []
    cl_in: list[Path] = []
    q_in: list[Path] = []
    for d in args.tracks:
        root = Path(d)
        docs_in.append(root / "documents.jsonl")
        cl_in.append(root / "clusters.jsonl")
        q_in.append(root / "queries.jsonl")

    od = args.out_dir
    nd = _merge_jsonl(docs_in, od / "documents.jsonl")
    nc = _merge_jsonl(cl_in, od / "clusters.jsonl")
    nq = _merge_jsonl(q_in, od / "queries.jsonl")
    man = {
        "merged_from": [str(p) for p in args.tracks],
        "documents": nd,
        "clusters": nc,
        "queries": nq,
    }
    (od / "manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(f"Wrote {od} ({man})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
