"""Run retrieval baselines + PACER on a JSONL dataset and write results."""

from __future__ import annotations

import argparse
from pathlib import Path

from provbench_rag.experiments.eval_suite import (
    evaluate_methods,
    write_latex_table,
    write_paper_macros,
    write_results_json,
)
from provbench_rag.methods.retrieve import RetrievalMethod
from provbench_rag.provenance.scoring import PACERWeights


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("documents_jsonl")
    ap.add_argument("queries_jsonl")
    ap.add_argument("--out-dir", default="results", help="Directory for metrics.json and table.tex")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--pool-k", type=int, default=80)
    ap.add_argument(
        "--pacer-alpha",
        type=float,
        default=1.0,
        help="PACER weight on min-max BM25 semantic term.",
    )
    ap.add_argument("--pacer-beta", type=float, default=1.0)
    ap.add_argument("--pacer-gamma", type=float, default=1.0)
    ap.add_argument("--pacer-delta", type=float, default=1.0)
    ap.add_argument("--pacer-eta", type=float, default=1.0)
    ap.add_argument(
        "--paper-macros",
        default=None,
        help="If set, write paper/generated_macros.tex to this path (e.g. paper/generated_macros.tex).",
    )
    args = ap.parse_args(argv)

    methods: list[RetrievalMethod] = [
        "bm25",
        "authority_first",
        "recent_first",
        "pacer",
        "cluster_pacer",
    ]
    pacer_w = PACERWeights(
        alpha=args.pacer_alpha,
        beta=args.pacer_beta,
        gamma=args.pacer_gamma,
        delta=args.pacer_delta,
        eta=args.pacer_eta,
    )
    payload = evaluate_methods(
        args.documents_jsonl,
        args.queries_jsonl,
        methods,
        k=args.k,
        pool_k=args.pool_k,
        pacer_weights=pacer_w,
    )
    payload["pacer_weights"] = {
        "alpha": pacer_w.alpha,
        "beta": pacer_w.beta,
        "gamma": pacer_w.gamma,
        "delta": pacer_w.delta,
        "eta": pacer_w.eta,
    }

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_results_json(out / "metrics.json", payload)
    write_latex_table(out / "main_results_table.tex", payload)
    extra = []
    if args.paper_macros:
        mp = Path(args.paper_macros)
        mp.parent.mkdir(parents=True, exist_ok=True)
        write_paper_macros(mp, payload)
        extra.append(str(mp))
    print(f"Wrote {out / 'metrics.json'}, {out / 'main_results_table.tex'}" + (f", {', '.join(extra)}" if extra else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
