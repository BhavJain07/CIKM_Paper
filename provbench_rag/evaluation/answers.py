"""Answer extraction from synthetic / templated evidence text."""

from __future__ import annotations

import re

_ANSWER_RE = re.compile(r"Answer:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL)


def extract_answer_line(text: str) -> str | None:
    m = _ANSWER_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def answers_conflict(doc_a: str, doc_b: str) -> bool:
    a = extract_answer_line(doc_a)
    b = extract_answer_line(doc_b)
    if a is None or b is None:
        return False
    return a.lower() != b.lower()
