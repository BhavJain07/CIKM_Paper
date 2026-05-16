"""Plain-text heuristics shared by crawled tracks and evaluation."""

from __future__ import annotations

import re


def first_sentence(text: str, max_words: int = 80) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    for sep in [". ", "? ", "! "]:
        if sep in text[:1200]:
            idx = text.index(sep)
            frag = text[: idx + 1].strip()
            if len(frag.split()) <= max_words:
                return frag
    words = text.split()[:max_words]
    return " ".join(words)
