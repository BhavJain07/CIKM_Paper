"""Retrieval and reranking methods for experiments."""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from typing import Callable, Literal

from provbench_rag.provenance.scoring import PACERWeights, pacerscore_normalized
from provbench_rag.retrieval.bm25.index import BM25Index
from provbench_rag.retrieval.hybrid.fuse import reciprocal_rank_fusion
from provbench_rag.schema import DocumentRecord, QueryRecord

RetrievalMethod = Literal[
    "control_random_pool",
    "control_semantic_only",
    "control_oracle_pool",
    "bm25",
    "authority_first",
    "recent_first",
    "rrf_bm25_authority",
    "pacer",
    "cluster_pacer",
]

# PACER with only the lexical (min--max BM25) term: β=γ=δ=η=0 in scoring.py.
_CONTROL_SEMANTIC_ONLY_WEIGHTS = PACERWeights(alpha=1.0, beta=0.0, gamma=0.0, delta=0.0, eta=0.0)


def _minmax(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    lo = min(scores.values())
    hi = max(scores.values())
    span = max(hi - lo, 1e-12)
    return {k: (v - lo) / span for k, v in scores.items()}


def _bm25_pool(index: BM25Index, query_text: str, pool_k: int) -> dict[str, float]:
    raw = {did: s for did, s in index.score(query_text)[:pool_k]}
    return _minmax(raw)


def _query_deterministic_rng(query_id: str) -> random.Random:
    h = hashlib.sha256(query_id.encode("utf-8")).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def rank_control_random_pool(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
) -> list[str]:
    """Random permutation of the BM25 pool (deterministic per query_id); lower-bound control."""
    del docs
    sem = _bm25_pool(index, query.query_text, pool_k)
    pool_ids = list(sem.keys())
    rng = _query_deterministic_rng(query.query_id)
    rng.shuffle(pool_ids)
    return pool_ids[:k]


def rank_control_oracle_pool(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
) -> list[str]:
    """If a preferred source appears in the pool, promote it to rank 1; then BM25 order (upper-bound control)."""
    del docs
    sem = _bm25_pool(index, query.query_text, pool_k)
    pool_set = set(sem.keys())
    bm25_order = [d for d, _ in index.score(query.query_text) if d in pool_set]
    prefer_in_pool = next((p for p in query.preferred_source_ids if p in pool_set), None)
    out: list[str] = []
    if prefer_in_pool is not None:
        out.append(prefer_in_pool)
    for did in bm25_order:
        if did not in out:
            out.append(did)
        if len(out) >= k:
            return out[:k]
    return out[:k]


def rank_control_semantic_only(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
) -> list[str]:
    """Same pool path as PACER but provenance weights zeroed—lexical term only (treatment isolating fusion head)."""
    return rank_pacer(index, docs, query, pool_k, k, _CONTROL_SEMANTIC_ONLY_WEIGHTS)


def rank_bm25(index: BM25Index, query: QueryRecord, pool_k: int, k: int) -> list[str]:
    raw = index.score(query.query_text)
    return [did for did, _ in raw[:k]]


def rank_authority_first(index: BM25Index, docs: dict[str, DocumentRecord], query: QueryRecord, k: int) -> list[str]:
    pool = rank_bm25(index, query, pool_k=max(k * 5, 50), k=max(k * 5, 50))
    return sorted(pool, key=lambda did: docs[did].authority_level, reverse=True)[:k]


def rank_rrf_bm25_authority(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
    weights: PACERWeights | None = None,
) -> list[str]:
    """RRF fusion of BM25 ordering vs authority ordering restricted to the BM25 pool."""
    del weights
    pool = _bm25_pool(index, query.query_text, pool_k)
    pool_set = set(pool.keys())
    bm25_order = [d for d, _ in index.score(query.query_text) if d in pool_set][:pool_k]
    auth_order = sorted(pool_set, key=lambda x: docs[x].authority_level, reverse=True)
    fused = reciprocal_rank_fusion(
        [[(did, 0.0) for did in bm25_order], [(did, 0.0) for did in auth_order]],
        k=60,
    )
    return [d for d, _ in fused[:k]]


def rank_recent_first(index: BM25Index, docs: dict[str, DocumentRecord], query: QueryRecord, k: int) -> list[str]:
    pool = rank_bm25(index, query, pool_k=max(k * 5, 50), k=max(k * 5, 50))

    def pub_key(did: str) -> tuple[int, str]:
        d = docs[did]
        if d.publication_date is None:
            return (0, "")
        return (1, d.publication_date.isoformat())

    return sorted(pool, key=pub_key, reverse=True)[:k]


def rank_pacer(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
    weights: PACERWeights | None = None,
) -> list[str]:
    sem = _bm25_pool(index, query.query_text, pool_k)
    scored: list[tuple[str, float]] = []
    for did, s_sem in sem.items():
        d = docs[did]
        scored.append((did, pacerscore_normalized(d, query, s_sem, weights)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [did for did, _ in scored[:k]]


def rank_cluster_pacer(
    index: BM25Index,
    docs: dict[str, DocumentRecord],
    query: QueryRecord,
    pool_k: int,
    k: int,
    weights: PACERWeights | None = None,
) -> list[str]:
    """Stage 1: rank clusters by max PACER; stage 2: emit best doc per cluster then fill."""
    sem = _bm25_pool(index, query.query_text, pool_k)
    by_cluster: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for did, s_sem in sem.items():
        d = docs[did]
        sc = pacerscore_normalized(d, query, s_sem, weights)
        by_cluster[d.cluster_id].append((did, sc))
    cluster_order: list[tuple[str, float]] = []
    for cid, lst in by_cluster.items():
        best = max(lst, key=lambda x: x[1])
        cluster_order.append((cid, best[1]))
    cluster_order.sort(key=lambda x: x[1], reverse=True)

    out: list[str] = []
    seen: set[str] = set()
    for cid, _ in cluster_order:
        lst = by_cluster[cid]
        lst.sort(key=lambda x: x[1], reverse=True)
        for did, _ in lst:
            if did not in seen:
                out.append(did)
                seen.add(did)
                break
        if len(out) >= k:
            break
    if len(out) < k:
        for did in rank_pacer(index, docs, query, pool_k, k * 3, weights):
            if did not in seen:
                out.append(did)
                seen.add(did)
            if len(out) >= k:
                break
    return out[:k]


def get_ranker(name: RetrievalMethod) -> Callable[..., list[str]]:
    if name == "control_random_pool":
        return lambda index, docs, q, pool_k, k, w=None: rank_control_random_pool(index, docs, q, pool_k, k)
    if name == "control_oracle_pool":
        return lambda index, docs, q, pool_k, k, w=None: rank_control_oracle_pool(index, docs, q, pool_k, k)
    if name == "control_semantic_only":
        return lambda index, docs, q, pool_k, k, w=None: rank_control_semantic_only(index, docs, q, pool_k, k)
    if name == "bm25":
        return lambda index, docs, q, pool_k, k, w=None: rank_bm25(index, q, pool_k, k)
    if name == "authority_first":
        return lambda index, docs, q, pool_k, k, w=None: rank_authority_first(index, docs, q, k)
    if name == "recent_first":
        return lambda index, docs, q, pool_k, k, w=None: rank_recent_first(index, docs, q, k)
    if name == "rrf_bm25_authority":
        return rank_rrf_bm25_authority
    if name == "pacer":
        return rank_pacer
    if name == "cluster_pacer":
        return rank_cluster_pacer
    raise ValueError(name)
