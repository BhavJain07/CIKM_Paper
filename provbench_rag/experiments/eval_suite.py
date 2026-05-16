"""Full benchmark evaluation across retrieval methods."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from provbench_rag.evaluation.answer_metrics import exact_match, token_f1
from provbench_rag.evaluation.predictions import predict_abstain, predicted_answer
from provbench_rag.evaluation.provenance_metrics import preferred_source_accuracy, provenance_f1
from provbench_rag.evaluation.retrieval_metrics import ndcg_at_k, recall_at_k
from provbench_rag.evaluation.significance import mcnemar_exact_two_sided
from provbench_rag.evaluation.support_metrics import minimality_penalty, prov_score, sufficiency_score
from provbench_rag.io import iter_jsonl
from provbench_rag.methods.retrieve import RetrievalMethod, get_ranker
from provbench_rag.provenance.scoring import PACERWeights
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.schema import DocumentRecord, QueryRecord


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


def _psa_at_1(ranked: list[str], query: QueryRecord) -> float | None:
    if query.abstain_required:
        return None
    return preferred_source_accuracy(ranked[:1], query.preferred_source_ids)


def evaluate_methods(
    documents_path: str | Path,
    queries_path: str | Path,
    methods: Sequence[RetrievalMethod],
    k: int = 10,
    pool_k: int = 80,
    pacer_weights: PACERWeights | None = None,
) -> dict[str, Any]:
    docs = {d.doc_id: d for d in iter_jsonl(documents_path, DocumentRecord)}
    queries = list(iter_jsonl(queries_path, QueryRecord))

    index = BM25Index()
    for d in docs.values():
        index.add_document(d.doc_id, d.text)

    rankings: dict[str, list[list[str]]] = {m: [] for m in methods}
    for method in methods:
        ranker = get_ranker(method)
        for q in queries:
            rankings[method].append(ranker(index, docs, q, pool_k, k, pacer_weights))

    results: dict[str, Any] = {"queries": len(queries), "k": k, "pool_k": pool_k, "methods": {}}

    for method in methods:
        psa_non_abstain: list[float] = []
        recall_list: list[float] = []
        ndcg_list: list[float] = []
        suff_list: list[float] = []
        min_list: list[float] = []
        ans_acc_list: list[float] = []
        abst_list: list[float] = []
        prov_f1_non_abstain: list[float] = []

        for q, ranked in zip(queries, rankings[method], strict=True):
            rel = set(q.gold_evidence_ids)
            recall_list.append(recall_at_k(ranked, rel, k))
            ndcg_list.append(ndcg_at_k(ranked, rel, k))
            suff_list.append(sufficiency_score(ranked, q.gold_evidence_ids))
            min_list.append(minimality_penalty(ranked, q.minimal_evidence_ids))
            pred_ab = predict_abstain(ranked, docs, q)
            pred_ans = predicted_answer(ranked, docs, q)
            ans_acc_list.append(_answer_acc(pred_ans, q.gold_answer, q.acceptable_answers))
            abst_list.append(_abstain_correct(pred_ab, q))
            psa = _psa_at_1(ranked, q)
            if psa is not None:
                psa_non_abstain.append(psa)
            if not q.abstain_required and q.preferred_source_ids:
                prov_f1_non_abstain.append(provenance_f1(ranked[:3], q.preferred_source_ids)[2])

        n = max(len(queries), 1)
        n_psa = max(len(psa_non_abstain), 1)
        n_pf = max(len(prov_f1_non_abstain), 1)
        agg = {
            "recall_at_k": sum(recall_list) / n,
            "ndcg_at_k": sum(ndcg_list) / n,
            "psa_at_1_non_abstain": sum(psa_non_abstain) / n_psa,
            "provenance_f1_at_3_non_abstain": sum(prov_f1_non_abstain) / n_pf,
            "sufficiency": sum(suff_list) / n,
            "minimality": sum(min_list) / n,
            "answer_accuracy": sum(ans_acc_list) / n,
            "abstention_accuracy": sum(abst_list) / n,
        }
        agg["prov_score"] = prov_score(
            agg["answer_accuracy"],
            agg["psa_at_1_non_abstain"],
            agg["sufficiency"],
            agg["minimality"],
            agg["abstention_accuracy"],
        )
        results["methods"][method] = agg

    if "bm25" in rankings and "pacer" in rankings:
        a_bits: list[bool] = []
        b_bits: list[bool] = []
        for q, rb, rp in zip(queries, rankings["bm25"], rankings["pacer"], strict=True):
            if q.abstain_required:
                continue
            psa_b = _psa_at_1(rb, q)
            psa_p = _psa_at_1(rp, q)
            if psa_b is None or psa_p is None:
                continue
            a_bits.append(psa_b >= 0.5)
            b_bits.append(psa_p >= 0.5)
        if a_bits and len(a_bits) == len(b_bits):
            results["mcnemar_psa_preferred_bm25_vs_pacer"] = mcnemar_exact_two_sided(a_bits, b_bits)
            results["mcnemar_n_queries"] = len(a_bits)

    return results


def write_results_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_paper_macros(path: str | Path, payload: dict[str, Any]) -> None:
    """LaTeX \\newcommand definitions for numeric results (primary synthetic track)."""

    def f3(x: float) -> str:
        return f"{x:.3f}"

    m = payload["methods"]
    lines = [
        "% Experiment metrics (synthetic track)",
        f"\\newcommand{{\\ProvBenchNumQueries}}{{{payload['queries']}}}",
        f"\\newcommand{{\\ProvBenchK}}{{{payload['k']}}}",
        f"\\newcommand{{\\ProvBmRecall}}{{{f3(m['bm25']['recall_at_k'])}}}",
        f"\\newcommand{{\\ProvBmNDCG}}{{{f3(m['bm25']['ndcg_at_k'])}}}",
        f"\\newcommand{{\\ProvBmPSA}}{{{f3(m['bm25']['psa_at_1_non_abstain'])}}}",
        f"\\newcommand{{\\ProvBmProvF}}{{{f3(m['bm25']['provenance_f1_at_3_non_abstain'])}}}",
        f"\\newcommand{{\\ProvBmAns}}{{{f3(m['bm25']['answer_accuracy'])}}}",
        f"\\newcommand{{\\ProvBmProvScore}}{{{f3(m['bm25']['prov_score'])}}}",
        f"\\newcommand{{\\ProvPacerRecall}}{{{f3(m['pacer']['recall_at_k'])}}}",
        f"\\newcommand{{\\ProvPacerNDCG}}{{{f3(m['pacer']['ndcg_at_k'])}}}",
        f"\\newcommand{{\\ProvPacerPSA}}{{{f3(m['pacer']['psa_at_1_non_abstain'])}}}",
        f"\\newcommand{{\\ProvPacerProvF}}{{{f3(m['pacer']['provenance_f1_at_3_non_abstain'])}}}",
        f"\\newcommand{{\\ProvPacerAns}}{{{f3(m['pacer']['answer_accuracy'])}}}",
        f"\\newcommand{{\\ProvPacerProvScore}}{{{f3(m['pacer']['prov_score'])}}}",
    ]
    if "mcnemar_psa_preferred_bm25_vs_pacer" in payload:
        p = payload["mcnemar_psa_preferred_bm25_vs_pacer"]
        lines.append(f"\\newcommand{{\\McNemarPSA}}{{{p:.6g}}}")
        lines.append(f"\\newcommand{{\\McNemarN}}{{{payload.get('mcnemar_n_queries', 0)}}}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_table(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "% Results table (provbench_rag.experiments.eval_suite)",
        "\\begin{tabular}{lrrrrr}",
        "\\hline",
        "Method & PSA@1 & Recall@k & nDCG@k & Ans.Acc. & ProvScore \\\\",
        "\\hline",
    ]
    for name, m in payload["methods"].items():
        psa = m.get("psa_at_1_non_abstain", 0.0)
        safe = name.replace("_", r"\_")
        lines.append(
            f"\\texttt{{{safe}}} & {psa:.3f} & {m['recall_at_k']:.3f} & {m['ndcg_at_k']:.3f} & "
            f"{m['answer_accuracy']:.3f} & {m['prov_score']:.3f} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", ""])
    if "mcnemar_psa_preferred_bm25_vs_pacer" in payload:
        lines.append(
            f"% McNemar PSA@1 (bm25 vs pacer), n={payload.get('mcnemar_n_queries', '?')}: "
            f"p={payload['mcnemar_psa_preferred_bm25_vs_pacer']:.4f}"
        )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_prefixed_track_macros(payload: dict[str, Any], path: str | Path, prefix: str) -> None:
    """Emit \\WikiBmNDCG-style commands for secondary tracks."""

    def f3(x: float) -> str:
        return f"{x:.3f}"

    m = payload["methods"]
    lines = [
        f"% Experiment metrics ({prefix} track)",
        f"\\newcommand{{\\{prefix}NumQueries}}{{{payload['queries']}}}",
        f"\\newcommand{{\\{prefix}K}}{{{payload['k']}}}",
        f"\\newcommand{{\\{prefix}BmRecall}}{{{f3(m['bm25']['recall_at_k'])}}}",
        f"\\newcommand{{\\{prefix}BmNDCG}}{{{f3(m['bm25']['ndcg_at_k'])}}}",
        f"\\newcommand{{\\{prefix}BmPSA}}{{{f3(m['bm25']['psa_at_1_non_abstain'])}}}",
        f"\\newcommand{{\\{prefix}BmProvF}}{{{f3(m['bm25']['provenance_f1_at_3_non_abstain'])}}}",
        f"\\newcommand{{\\{prefix}BmAns}}{{{f3(m['bm25']['answer_accuracy'])}}}",
        f"\\newcommand{{\\{prefix}BmProvScore}}{{{f3(m['bm25']['prov_score'])}}}",
        f"\\newcommand{{\\{prefix}PacerRecall}}{{{f3(m['pacer']['recall_at_k'])}}}",
        f"\\newcommand{{\\{prefix}PacerNDCG}}{{{f3(m['pacer']['ndcg_at_k'])}}}",
        f"\\newcommand{{\\{prefix}PacerPSA}}{{{f3(m['pacer']['psa_at_1_non_abstain'])}}}",
        f"\\newcommand{{\\{prefix}PacerProvF}}{{{f3(m['pacer']['provenance_f1_at_3_non_abstain'])}}}",
        f"\\newcommand{{\\{prefix}PacerAns}}{{{f3(m['pacer']['answer_accuracy'])}}}",
        f"\\newcommand{{\\{prefix}PacerProvScore}}{{{f3(m['pacer']['prov_score'])}}}",
        f"\\newcommand{{\\{prefix}ClusterPacerProvScore}}{{{f3(m['cluster_pacer']['prov_score'])}}}",
    ]
    if "mcnemar_psa_preferred_bm25_vs_pacer" in payload:
        p = payload["mcnemar_psa_preferred_bm25_vs_pacer"]
        lines.append(f"\\newcommand{{\\{prefix}McNemarPSA}}{{{p:.6g}}}")
        lines.append(f"\\newcommand{{\\{prefix}McNemarN}}{{{payload.get('mcnemar_n_queries', 0)}}}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
