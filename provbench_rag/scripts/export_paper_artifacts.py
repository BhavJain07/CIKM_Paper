"""Regenerate paper/*.tex tables and macros from results/*/metrics.json (no re-running eval)."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from provbench_rag.experiments.eval_suite import (
    write_latex_table,
    write_paper_macros,
    write_prefixed_track_macros,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper-dir", type=Path, default=Path("paper"))
    args = ap.parse_args(argv)

    pd = args.paper_dir
    tbl = pd / "tables"
    tbl.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("results/synthetic_v1/metrics.json", "generated_macros.tex", None, "synthetic_main_table.tex"),
        ("results/wiki_freshness_v1/metrics.json", "macros_wiki.tex", "Wiki", "wiki_main_table.tex"),
        ("results/combined_v1/metrics.json", "macros_combined.tex", "Combined", "combined_main_table.tex"),
    ]

    for metrics_path, macro_name, prefix, table_name in jobs:
        p = Path(metrics_path)
        if not p.exists():
            continue
        payload = json.loads(p.read_text(encoding="utf-8"))
        if prefix:
            write_prefixed_track_macros(payload, pd / macro_name, prefix)
        else:
            write_paper_macros(pd / macro_name, payload)
        write_latex_table(tbl / table_name, payload)
        src = p.parent / "main_results_table.tex"
        if src.exists():
            shutil.copy2(src, tbl / f"{Path(table_name).stem}_from_results.tex")

    print(f"Wrote macros under {pd}/ and tables under {tbl}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
