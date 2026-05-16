"""Okapi BM25 retrieval over tokenized documents (inverted-index scoring)."""

from __future__ import annotations

import math
import re
import string
from collections import defaultdict


def _tokenize(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(rf"[{re.escape(string.punctuation)}]", " ", t)
    return [x for x in t.split() if x]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._doc_ids: list[str] = []
        self._doc_lens: list[int] = []
        self._doc_freqs: list[dict[str, int]] = []
        self._df: dict[str, int] = defaultdict(int)
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._N = 0
        self._avgdl = 0.0

    def add_document(self, doc_id: str, text: str) -> None:
        toks = _tokenize(text)
        tf: dict[str, int] = defaultdict(int)
        for w in toks:
            tf[w] += 1
        for w in tf:
            self._df[w] += 1
        doc_i = self._N
        self._doc_ids.append(doc_id)
        self._doc_lens.append(len(toks))
        self._doc_freqs.append(dict(tf))
        for w, f in tf.items():
            self._postings[w].append((doc_i, f))
        self._N += 1
        total = sum(self._doc_lens)
        self._avgdl = total / self._N if self._N else 0.0

    def score(self, query: str) -> list[tuple[str, float]]:
        qtoks = _tokenize(query)
        if self._N == 0:
            return []
        scores: dict[str, float] = defaultdict(float)
        for q in set(qtoks):
            df = self._df.get(q, 0)
            if df == 0:
                continue
            idf = math.log(1.0 + (self._N - df + 0.5) / (df + 0.5))
            for i, f in self._postings.get(q, ()):
                dl = self._doc_lens[i]
                denom = f + self.k1 * (1 - self.b + self.b * dl / max(self._avgdl, 1e-6))
                doc_id = self._doc_ids[i]
                scores[doc_id] += idf * (f * (self.k1 + 1)) / denom
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
