"""Run stratified evaluation, ablations, bootstrap CIs, and export LaTeX fragments."""

from __future__ import annotations

import argparse
from pathlib import Path

from provbench_rag.experiments.extended_eval import (
    run_extended_evaluation,
    write_ablation_latex,
    write_bootstrap_latex,
    write_extended_json,
    write_extended_main_table,
    write_stratified_latex,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("documents_jsonl")
    ap.add_argument("queries_jsonl")
    ap.add_argument("--out-dir", type=Path, default=Path("results/synthetic_v1/extended"))
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--pool-k", type=int, default=80)
    ap.add_argument("--bootstrap-samples", type=int, default=2000)
    args = ap.parse_args(argv)

    payload = run_extended_evaluation(
        args.documents_jsonl,
        args.queries_jsonl,
        k=args.k,
        pool_k=args.pool_k,
        bootstrap_samples=args.bootstrap_samples,
    )

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    write_extended_json(out / "metrics_extended.json", payload)
    write_extended_main_table(out / "main_results_extended.tex", payload)
    write_stratified_latex(out / "stratified_table.tex", payload)
    write_ablation_latex(out / "ablation_table.tex", payload)
    write_bootstrap_latex(out / "bootstrap_table.tex", payload)
    print(f"Wrote extended metrics to {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
