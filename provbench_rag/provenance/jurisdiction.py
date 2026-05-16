"""Jurisdiction compatibility s_jur(d, q)."""

from __future__ import annotations

from provbench_rag.schema import DocumentRecord, QueryRecord


def jurisdiction_score(document: DocumentRecord, query: QueryRecord) -> float:
    qj = (query.query_jurisdiction or "").strip().lower()
    dj = (document.jurisdiction or "").strip().lower()
    if not qj or not dj:
        return 0.5
    return 1.0 if qj == dj else 0.0
