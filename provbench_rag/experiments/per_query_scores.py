"""Per-query scalar metrics for bootstrap and stratified analysis."""

from __future__ import annotations

from provbench_rag.evaluation.predictions import predict_abstain, predicted_answer
from provbench_rag.evaluation.provenance_metrics import preferred_source_accuracy, provenance_f1
from provbench_rag.evaluation.retrieval_metrics import ndcg_at_k, recall_at_k
from provbench_rag.evaluation.support_metrics import minimality_penalty, prov_score, sufficiency_score
from provbench_rag.evaluation.answer_metrics import exact_match, token_f1
from provbench_rag.schema import DocumentRecord, QueryRecord


def _answer_acc(pred: str, gold: str, acceptable: list[str]) -> float:
    if exact_match(pred, gold):
        return 1.0
    for a in acceptable:
        if exact_match(pred, a):
            return 1.0
    return token_f1(pred, gold)


def _psa(q: QueryRecord, ranked: list[str]) -> float | None:
    if q.abstain_required:
        return None
    return preferred_source_accuracy(ranked[:1], q.preferred_source_ids)


def infer_stratum(q: QueryRecord, docs: dict[str, DocumentRecord]) -> str:
    """Synthetic families A–E from cluster_id; Wikipedia revision; else other."""
    if not q.gold_evidence_ids:
        return "unknown"
    cid = docs[q.gold_evidence_ids[0]].cluster_id
    if cid.startswith("syn_"):
        parts = cid.split("_")
        if len(parts) >= 2 and parts[1] in {"A", "B", "C", "D", "E"}:
            return parts[1]
    if cid.startswith("wiki_page_"):
        return "wiki_rev"
    return "other"


def _abstain_correct(pred_abstain: bool, query: QueryRecord) -> float:
    if not query.abstain_required:
        return 1.0 if not pred_abstain else 0.0
    return 1.0 if pred_abstain else 0.0


def per_query_metrics(
    q: QueryRecord,
    ranked: list[str],
    docs: dict[str, DocumentRecord],
    k: int,
) -> dict[str, float]:
    rel = set(q.gold_evidence_ids)
    psa_v = _psa(q, ranked)
    pf_v = (
        provenance_f1(ranked[:3], q.preferred_source_ids)[2]
        if not q.abstain_required and q.preferred_source_ids
        else 1.0
    )
    suff = sufficiency_score(ranked, q.gold_evidence_ids)
    minim = minimality_penalty(ranked, q.minimal_evidence_ids)
    pred_ab = predict_abstain(ranked, docs, q)
    pred_ans = predicted_answer(ranked, docs, q)
    ans = _answer_acc(pred_ans, q.gold_answer, q.acceptable_answers)
    abst = _abstain_correct(pred_ab, q)
    # PSA slot for micro ProvScore: neutral 0.5 when undefined (abstention-only gold)
    psa_slot = float(psa_v) if psa_v is not None else 0.5
    pv = prov_score(ans, psa_slot, suff, minim, abst)
    return {
        "prov_score": pv,
        "answer_accuracy": ans,
        "psa": float(psa_v) if psa_v is not None else 0.0,
        "psa_defined": 1.0 if psa_v is not None else 0.0,
        "recall_at_k": recall_at_k(ranked, rel, k),
        "ndcg_at_k": ndcg_at_k(ranked, rel, k),
        "provenance_f1_at_3": pf_v,
        "sufficiency": suff,
        "minimality": minim,
        "abstention_correct": abst,
    }
