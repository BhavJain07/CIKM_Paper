"""Original-vs-copy preference s_orig(d, q)."""

from __future__ import annotations

from provbench_rag.schema import DocumentRecord, QueryRecord

_LABEL_WEIGHT: dict[str, float] = {
    "original": 1.0,
    "summary": 0.55,
    "mirror": 0.35,
    "copy": 0.25,
    "unknown": 0.5,
}


def originality_score(document: DocumentRecord, _query: QueryRecord) -> float:
    return _LABEL_WEIGHT.get(document.original_or_copy_label, 0.5)
