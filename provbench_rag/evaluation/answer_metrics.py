"""Answer-level metrics: exact match and token F1."""

from __future__ import annotations

import re
import string


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(rf"[{re.escape(string.punctuation)}]", " ", s)
    return " ".join(s.split())


def exact_match(prediction: str, gold: str) -> bool:
    return _norm(prediction) == _norm(gold)


def token_f1(prediction: str, gold: str) -> float:
    pred_toks = _norm(prediction).split()
    gold_toks = _norm(gold).split()
    if not pred_toks and not gold_toks:
        return 1.0
    if not pred_toks or not gold_toks:
        return 0.0
    pred_set = {}
    for t in pred_toks:
        pred_set[t] = pred_set.get(t, 0) + 1
    gold_counts = {}
    for t in gold_toks:
        gold_counts[t] = gold_counts.get(t, 0) + 1
    overlap = 0
    for t, c in pred_set.items():
        overlap += min(c, gold_counts.get(t, 0))
    prec = overlap / len(pred_toks)
    rec = overlap / len(gold_toks)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)
