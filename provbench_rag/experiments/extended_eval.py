"""Stratified metrics, PACER ablations, bootstrap CIs, and Wilcoxon paired tests."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from provbench_rag.evaluation.answer_metrics import exact_match, token_f1
from provbench_rag.evaluation.predictions import predict_abstain, predicted_answer
from provbench_rag.evaluation.provenance_metrics import preferred_source_accuracy, provenance_f1
from provbench_rag.evaluation.retrieval_metrics import ndcg_at_k, recall_at_k
from provbench_rag.evaluation.significance import mcnemar_exact_two_sided, wilcoxon_signed_rank_normal_approx
from provbench_rag.evaluation.support_metrics import minimality_penalty, prov_score, sufficiency_score
from provbench_rag.experiments.bootstrap_ci import bootstrap_mean_ci
from provbench_rag.experiments.per_query_scores import infer_stratum, per_query_metrics
from provbench_rag.io import iter_jsonl
from provbench_rag.methods.retrieve import RetrievalMethod, get_ranker
from provbench_rag.provenance.scoring import PACERWeights
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.schema import DocumentRecord, QueryRecord

PACER_ABLATIONS: dict[str, PACERWeights] = {
    "drop_authority": PACERWeights(alpha=1.0, beta=0.0, gamma=1.0, delta=1.0, eta=1.0),
    "drop_freshness": PACERWeights(alpha=1.0, beta=1.0, gamma=0.0, delta=1.0, eta=1.0),
    "drop_originality": PACERWeights(alpha=1.0, beta=1.0, gamma=1.0, delta=0.0, eta=1.0),
    "drop_jurisdiction": PACERWeights(alpha=1.0, beta=1.0, gamma=1.0, delta=1.0, eta=0.0),
}

FULL_METHODS: list[RetrievalMethod] = [
    "control_random_pool",
    "control_semantic_only",
    "bm25",
    "authority_first",
    "recent_first",
    "rrf_bm25_authority",
    "pacer",
    "cluster_pacer",
    "control_oracle_pool",
]


def _answer_acc(pred: str, gold: str, acceptable: list[str]) -> float:
    if exact_match(pred, gold):
        return 1.0
    for a in acceptable:
        if exact_match(pred, a):
            return 1.0
    return token_f1(pred, gold)


def _abstain_correct(pred_abstain: bool, query: QueryRecord) -> float:
    if not query.abstain_required:
        return 1.0 if not pred_abstain else 0.0
    return 1.0 if pred_abstain else 0.0


def _aggregate_rankings(
    rankings: list[list[str]],
    queries: list[QueryRecord],
    docs: dict[str, DocumentRecord],
    k: int,
) -> dict[str, float]:
    psa_na: list[float] = []
    recall_list: list[float] = []
    ndcg_list: list[float] = []
    suff_list: list[float] = []
    min_list: list[float] = []
    ans_list: list[float] = []
    abst_list: list[float] = []
    pf_list: list[float] = []

    for q, ranked in zip(queries, rankings, strict=True):
        rel = set(q.gold_evidence_ids)
        recall_list.append(recall_at_k(ranked, rel, k))
        ndcg_list.append(ndcg_at_k(ranked, rel, k))
        suff_list.append(sufficiency_score(ranked, q.gold_evidence_ids))
        min_list.append(minimality_penalty(ranked, q.minimal_evidence_ids))
        pred_ab = predict_abstain(ranked, docs, q)
        pred_ans = predicted_answer(ranked, docs, q)
        ans_list.append(_answer_acc(pred_ans, q.gold_answer, q.acceptable_answers))
        abst_list.append(_abstain_correct(pred_ab, q))
        psa_v = None if q.abstain_required else preferred_source_accuracy(ranked[:1], q.preferred_source_ids)
        if psa_v is not None:
            psa_na.append(psa_v)
        if not q.abstain_required and q.preferred_source_ids:
            pf_list.append(provenance_f1(ranked[:3], q.preferred_source_ids)[2])

    n = max(len(queries), 1)
    n_psa = max(len(psa_na), 1)
    n_pf = max(len(pf_list), 1)
    agg = {
        "recall_at_k": sum(recall_list) / n,
        "ndcg_at_k": sum(ndcg_list) / n,
        "psa_at_1_non_abstain": sum(psa_na) / n_psa,
        "provenance_f1_at_3_non_abstain": sum(pf_list) / n_pf,
        "sufficiency": sum(suff_list) / n,
        "minimality": sum(min_list) / n,
        "answer_accuracy": sum(ans_list) / n,
        "abstention_accuracy": sum(abst_list) / n,
    }
    agg["prov_score"] = prov_score(
        agg["answer_accuracy"],
        agg["psa_at_1_non_abstain"],
        agg["sufficiency"],
        agg["minimality"],
        agg["abstention_accuracy"],
    )
    return agg


def run_extended_evaluation(
    documents_path: str | Path,
    queries_path: str | Path,
    methods: Sequence[RetrievalMethod] | None = None,
    k: int = 10,
    pool_k: int = 80,
    base_weights: PACERWeights | None = None,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 42,
) -> dict[str, Any]:
    methods = list(methods or FULL_METHODS)
    base_weights = base_weights or PACERWeights()

    docs = {d.doc_id: d for d in iter_jsonl(documents_path, DocumentRecord)}
    queries = list(iter_jsonl(queries_path, QueryRecord))

    index = BM25Index()
    for d in docs.values():
        index.add_document(d.doc_id, d.text)

    rankings: dict[str, list[list[str]]] = {m: [] for m in methods}
    ablation_rankings: dict[str, list[list[str]]] = {a: [] for a in PACER_ABLATIONS}

    for q in queries:
        for m in methods:
            ranker = get_ranker(m)
            rankings[m].append(ranker(index, docs, q, pool_k, k, base_weights))
        for aname, w in PACER_ABLATIONS.items():
            ablation_rankings[aname].append(
                get_ranker("pacer")(index, docs, q, pool_k, k, w),
            )

    results: dict[str, Any] = {
        "queries": len(queries),
        "k": k,
        "pool_k": pool_k,
        "methods": {m: _aggregate_rankings(rankings[m], queries, docs, k) for m in methods},
        "pacer_ablations": {
            aname: _aggregate_rankings(lst, queries, docs, k) for aname, lst in ablation_rankings.items()
        },
    }

    if "bm25" in rankings and "pacer" in rankings:
        a_bits: list[bool] = []
        b_bits: list[bool] = []
        for q, rb, rp in zip(queries, rankings["bm25"], rankings["pacer"], strict=True):
            if q.abstain_required:
                continue
            psa_b = None if q.abstain_required else preferred_source_accuracy(rb[:1], q.preferred_source_ids)
            psa_p = None if q.abstain_required else preferred_source_accuracy(rp[:1], q.preferred_source_ids)
            if psa_b is None or psa_p is None:
                continue
            a_bits.append(psa_b >= 0.5)
            b_bits.append(psa_p >= 0.5)
        if a_bits and len(a_bits) == len(b_bits):
            results["mcnemar_psa_preferred_bm25_vs_pacer"] = mcnemar_exact_two_sided(a_bits, b_bits)
            results["mcnemar_n_queries"] = len(a_bits)

    stratified: dict[str, dict[str, dict[str, float]]] = {}
    family_counts: dict[str, int] = defaultdict(int)
    for q in queries:
        family_counts[infer_stratum(q, docs)] += 1

    for fam in sorted(family_counts.keys()):
        idxs = [i for i, q in enumerate(queries) if infer_stratum(q, docs) == fam]
        if not idxs:
            continue
        q_sub = [queries[i] for i in idxs]
        stratified[fam] = {}
        for m in ("bm25", "pacer"):
            if m not in rankings:
                continue
            r_sub = [rankings[m][i] for i in idxs]
            stratified[fam][m] = _aggregate_rankings(r_sub, q_sub, docs, k)
    results["stratified_by_family"] = stratified
    results["stratified_counts"] = dict(family_counts)

    micro_bm25: list[float] = []
    micro_pacer: list[float] = []
    deltas: list[float] = []
    for q, rb, rp in zip(queries, rankings["bm25"], rankings["pacer"], strict=True):
        vb = per_query_metrics(q, rb, docs, k)["prov_score"]
        vp = per_query_metrics(q, rp, docs, k)["prov_score"]
        micro_bm25.append(vb)
        micro_pacer.append(vp)
        deltas.append(vp - vb)

    b_bm25 = bootstrap_mean_ci(micro_bm25, n_bootstrap=bootstrap_samples, seed=bootstrap_seed)
    b_pacer = bootstrap_mean_ci(micro_pacer, n_bootstrap=bootstrap_samples, seed=bootstrap_seed + 1)
    b_delta = bootstrap_mean_ci(deltas, n_bootstrap=bootstrap_samples, seed=bootstrap_seed + 2)

    wz, wp = wilcoxon_signed_rank_normal_approx(deltas)

    results["bootstrap_micro_provscore"] = {
        "bm25": {"mean": b_bm25[0], "ci_low": b_bm25[1], "ci_high": b_bm25[2]},
        "pacer": {"mean": b_pacer[0], "ci_low": b_pacer[1], "ci_high": b_pacer[2]},
        "paired_delta_pacer_minus_bm25": {
            "mean": b_delta[0],
            "ci_low": b_delta[1],
            "ci_high": b_delta[2],
        },
    }
    results["wilcoxon_micro_provscore_delta"] = {"z_statistic": wz, "p_value_two_sided_approx": wp}
    results["bootstrap_samples"] = bootstrap_samples
    results["ablation_weights"] = {k: vars(v) for k, v in PACER_ABLATIONS.items()}
    results["pacer_weights"] = vars(base_weights)
    return results


def write_extended_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")


def write_stratified_latex(path: str | Path, payload: dict[str, Any]) -> None:
    s = payload.get("stratified_by_family", {})
    counts = payload.get("stratified_counts", {})
    lines = [
        "% Stratified ProvScore (BM25 vs PACER)",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Stratum & $n$ & BM25 & PACER & $\\Delta$ \\\\",
        "\\hline",
    ]
    for fam in sorted(s.keys()):
        row = s[fam]
        if "bm25" not in row or "pacer" not in row:
            continue
        n = counts.get(fam, 0)
        b = row["bm25"]["prov_score"]
        p = row["pacer"]["prov_score"]
        lines.append(f"{fam} & {n} & {b:.3f} & {p:.3f} & {p - b:+.3f} \\\\")
    lines.extend(["\\hline", "\\end{tabular}", ""])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_ablation_latex(path: str | Path, payload: dict[str, Any]) -> None:
    base = payload["methods"]["pacer"]["prov_score"]
    lines = [
        "% PACER ablations (single-term removal)",
        "\\begin{tabular}{lr}",
        "\\hline",
        "Variant & ProvScore \\\\",
        "\\hline",
        f"Full PACER & {base:.3f} \\\\",
    ]
    for name in sorted(payload.get("pacer_ablations", {}).keys()):
        sc = payload["pacer_ablations"][name]["prov_score"]
        safe = name.replace("_", r"\_")
        lines.append(f"{safe} & {sc:.3f} \\\\")
    lines.extend(["\\hline", "\\end{tabular}", ""])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_extended_main_table(path: str | Path, payload: dict[str, Any]) -> None:
    """Wider table including Prov.F1 column."""
    lines = [
        "% Extended main results table",
        "\\begin{tabular}{lrrrrrr}",
        "\\hline",
        "Method & PSA@1 & R@$k$ & nDCG & Prov.F1 & Ans & ProvScore \\\\",
        "\\hline",
    ]
    for name, m in payload["methods"].items():
        psa = m.get("psa_at_1_non_abstain", 0.0)
        safe = name.replace("_", r"\_")
        lines.append(
            f"\\texttt{{{safe}}} & {psa:.3f} & {m['recall_at_k']:.3f} & {m['ndcg_at_k']:.3f} & "
            f"{m['provenance_f1_at_3_non_abstain']:.3f} & {m['answer_accuracy']:.3f} & {m['prov_score']:.3f} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", ""])
    if "mcnemar_psa_preferred_bm25_vs_pacer" in payload:
        lines.append(
            f"% McNemar PSA@1 BM25 vs PACER: $n$={payload.get('mcnemar_n_queries', '?')}, "
            f"$p$={payload['mcnemar_psa_preferred_bm25_vs_pacer']:.6g}"
        )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_bootstrap_latex(path: str | Path, payload: dict[str, Any]) -> None:
    b = payload["bootstrap_micro_provscore"]
    w = payload["wilcoxon_micro_provscore_delta"]
    lines = [
        "% Bootstrap 95\\% CI on micro-averaged ProvScore",
        "\\begin{tabular}{lrr}",
        "\\hline",
        "Estimator & Mean & 95\\% CI \\\\",
        "\\hline",
        f"BM25 micro-Prov & {b['bm25']['mean']:.3f} & [{b['bm25']['ci_low']:.3f}, {b['bm25']['ci_high']:.3f}] \\\\",
        f"PACER micro-Prov & {b['pacer']['mean']:.3f} & [{b['pacer']['ci_low']:.3f}, {b['pacer']['ci_high']:.3f}] \\\\",
        f"$\\Delta$ (paired) & {b['paired_delta_pacer_minus_bm25']['mean']:.3f} & "
        f"[{b['paired_delta_pacer_minus_bm25']['ci_low']:.3f}, {b['paired_delta_pacer_minus_bm25']['ci_high']:.3f}] \\\\",
        "\\hline",
        "\\end{tabular}",
        "",
        f"% Wilcoxon signed-rank on paired $\\Delta$: $z$={w['z_statistic']:.3f}, "
        f"$p\\approx${w['p_value_two_sided_approx']:.4f}",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
