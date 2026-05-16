"""Predict abstention and answers from ranked evidence using rule-based extractors."""

from __future__ import annotations

from provbench_rag.evaluation.answers import answers_conflict, extract_answer_line
from provbench_rag.evaluation.text_extract import first_sentence
from provbench_rag.schema import DocumentRecord, QueryRecord


def predict_abstain(ranked_ids: list[str], docs: dict[str, DocumentRecord], query: QueryRecord) -> bool:
    if not query.abstain_required:
        return False
    tops = [did for did in ranked_ids if did in docs][:2]
    if len(tops) < 2:
        return True
    d0, d1 = docs[tops[0]], docs[tops[1]]
    if d0.cluster_id != d1.cluster_id:
        return True
    return answers_conflict(d0.text, d1.text)


def predicted_answer(ranked_ids: list[str], docs: dict[str, DocumentRecord], query: QueryRecord) -> str:
    if predict_abstain(ranked_ids, docs, query):
        return "ABSTAIN"
    if not ranked_ids:
        return ""
    top_text = docs[ranked_ids[0]].text
    if query.domain == "wikipedia_revision_freshness":
        return first_sentence(top_text) or ""
    return extract_answer_line(top_text) or ""
