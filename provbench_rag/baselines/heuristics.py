"""Source reranking heuristics for provenance baselines."""

from __future__ import annotations

from datetime import date

from provbench_rag.schema import DocumentRecord


def rerank_by_authority(
    doc_ids: list[str],
    documents: dict[str, DocumentRecord],
) -> list[str]:
    return sorted(doc_ids, key=lambda d: documents[d].authority_level, reverse=True)


def rerank_by_freshness(
    doc_ids: list[str],
    documents: dict[str, DocumentRecord],
    as_of: date | None,
) -> list[str]:
    def key(did: str) -> tuple[int, date | None]:
        doc = documents[did]
        pub = doc.publication_date
        if as_of is None or pub is None:
            return (0, pub)
        return (1 if pub <= as_of else 0, pub)

    return sorted(doc_ids, key=lambda did: key(did), reverse=True)
