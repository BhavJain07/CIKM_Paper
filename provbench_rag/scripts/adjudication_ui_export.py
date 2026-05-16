"""Export queries + documents to TSV for spreadsheet or lightweight review UIs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from provbench_rag.io import iter_jsonl
from provbench_rag.schema import DocumentRecord, QueryRecord


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("queries_jsonl")
    ap.add_argument("documents_jsonl")
    ap.add_argument("out_tsv")
    args = ap.parse_args(argv)

    docs = {d.doc_id: d for d in iter_jsonl(args.documents_jsonl, DocumentRecord)}
    outp = Path(args.out_tsv)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "query_id",
                "query_text",
                "gold_answer",
                "preferred_source_ids",
                "gold_evidence_ids",
                "abstain_required",
                "evidence_preview",
            ]
        )
        for q in iter_jsonl(args.queries_jsonl, QueryRecord):
            previews = []
            for eid in q.gold_evidence_ids[:3]:
                d = docs.get(eid)
                previews.append((d.text[:200] + "…") if d and len(d.text) > 200 else (d.text if d else ""))
            w.writerow(
                [
                    q.query_id,
                    q.query_text,
                    q.gold_answer,
                    ",".join(q.preferred_source_ids),
                    ",".join(q.gold_evidence_ids),
                    str(q.abstain_required),
                    " | ".join(previews),
                ]
            )
    print(f"Wrote {args.out_tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
