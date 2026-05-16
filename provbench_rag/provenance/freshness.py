"""Time-validity compatibility s_fresh(d, q) against query_time and doc validity window."""

from __future__ import annotations

from datetime import date, datetime

from provbench_rag.schema import DocumentRecord, QueryRecord


def _as_date(t: date | datetime | None) -> date | None:
    if t is None:
        return None
    if isinstance(t, datetime):
        return t.date()
    return t


def freshness_score(document: DocumentRecord, query: QueryRecord) -> float:
    """
    1.0 if query_time falls in [validity_start, validity_end] when both set;
    partial credit if only one bound; 0.5 if no temporal metadata on doc or query.
    """
    qd = _as_date(query.query_time)
    vs = document.validity_start
    ve = document.validity_end

    if qd is None or (vs is None and ve is None):
        return 0.5

    if vs is not None and ve is not None:
        if vs <= qd <= ve:
            return 1.0
        if qd < vs:
            return max(0.0, 1.0 - (vs - qd).days / 365.0)
        return max(0.0, 1.0 - (qd - ve).days / 365.0)

    if vs is not None and qd >= vs:
        return 1.0
    if ve is not None and qd <= ve:
        return 1.0
    return 0.25
