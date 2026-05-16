"""Retrieval-only and naive top-k baselines."""

from __future__ import annotations

from provbench_rag.retrieval.bm25.index import BM25Index


def retrieve_bm25_topk(index: BM25Index, query: str, k: int) -> list[str]:
    return [doc_id for doc_id, _ in index.score(query)[:k]]
