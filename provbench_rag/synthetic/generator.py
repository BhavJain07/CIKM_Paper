"""Generate documents, clusters, and queries with controlled provenance near-duplicates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from provbench_rag.io import write_jsonl
from provbench_rag.schema import ClusterRecord, DocumentRecord, QueryRecord


@dataclass(frozen=True)
class GeneratorStats:
    clusters: int
    documents: int
    queries: int
    seed: int


def _make_cluster(
    family: str,
    idx: int,
) -> tuple[list[DocumentRecord], ClusterRecord, QueryRecord]:
    cid = f"syn_{family}_{idx:05d}"
    qid = f"q_{cid}"
    ref = f"REF-{cid}"
    base = (
        f"Administrative guidance bundle {ref}. "
        f"Subject: Form X-12 submission window after posted notice. "
        f"Cluster identifier {cid} for audit trail."
    )

    q_time = date(2024, 9, 15)
    q_jur = "US"

    if family == "A":
        correct = "30 days"
        wrong = "14 days"
        d_off = DocumentRecord(
            doc_id=f"{cid}_official",
            cluster_id=cid,
            source_url=f"https://gov.example/policy/{cid}",
            source_type="official_html",
            authority_level=5,
            publication_date=date(2024, 6, 1),
            validity_start=date(2024, 6, 1),
            validity_end=date(2026, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=(
                base
                + " Official directive text. Answer: "
                + correct
                + " Filing must use authenticated channels."
            ),
            paragraph_spans=[],
        )
        d_blog = DocumentRecord(
            doc_id=f"{cid}_blog",
            cluster_id=cid,
            source_url=f"https://blog.example/posts/{cid}",
            source_type="blog",
            authority_level=2,
            publication_date=date(2024, 7, 2),
            validity_start=date(2024, 7, 1),
            validity_end=date(2026, 12, 31),
            jurisdiction="US",
            original_or_copy_label="summary",
            text=(
                base
                + " Informal explainer for practitioners. Answer: "
                + wrong
                + " This is not legal advice."
            ),
            paragraph_spans=[],
        )
        d_seo = DocumentRecord(
            doc_id=f"{cid}_seo",
            cluster_id=cid,
            source_url=f"https://answers.example/{cid}",
            source_type="ugc",
            authority_level=1,
            publication_date=date(2024, 8, 1),
            validity_start=date(2024, 8, 1),
            validity_end=date(2026, 12, 31),
            jurisdiction="US",
            original_or_copy_label="copy",
            text=(
                base
                + " Community rewrite for SEO. Answer: "
                + wrong
                + " Upvotes appreciated."
            ),
            paragraph_spans=[],
        )
        docs = [d_off, d_blog, d_seo]
        cluster = ClusterRecord(
            cluster_id=cid,
            relation_type="original_vs_copy",
            document_ids=[d.doc_id for d in docs],
            canonical_source_id=d_off.doc_id,
        )
        q = QueryRecord(
            query_id=qid,
            query_text=(
                f"For cluster {cid}, how long after posted notice may an eligible applicant file Form X-12?"
            ),
            domain="synthetic_documentation_policy",
            query_time=q_time,
            query_jurisdiction=q_jur,
            gold_answer=correct,
            acceptable_answers=["within 30 days", "thirty days"],
            gold_evidence_ids=[d_off.doc_id],
            minimal_evidence_ids=[d_off.doc_id],
            preferred_source_ids=[d_off.doc_id],
            abstain_required=False,
        )

    elif family == "B":
        correct = "30 days"
        wrong = "14 days"
        d_stale = DocumentRecord(
            doc_id=f"{cid}_stale",
            cluster_id=cid,
            source_url=f"https://docs.example/archive/{cid}",
            source_type="docs_snapshot",
            authority_level=4,
            publication_date=date(2021, 1, 1),
            validity_start=date(2021, 1, 1),
            validity_end=date(2023, 6, 30),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " Archived manual page. Answer: " + wrong + " Legacy wording prior to reform.",
            paragraph_spans=[],
        )
        d_fresh = DocumentRecord(
            doc_id=f"{cid}_current",
            cluster_id=cid,
            source_url=f"https://docs.example/current/{cid}",
            source_type="docs_snapshot",
            authority_level=4,
            publication_date=date(2024, 5, 1),
            validity_start=date(2024, 5, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " Current manual page. Answer: " + correct + " Applies to notices dated 2024-05-01 onward.",
            paragraph_spans=[],
        )
        d_mirror = DocumentRecord(
            doc_id=f"{cid}_mirror",
            cluster_id=cid,
            source_url=f"https://mirror.example/docs/{cid}",
            source_type="mirror",
            authority_level=2,
            publication_date=date(2024, 6, 1),
            validity_start=date(2024, 6, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="mirror",
            # Lexical decoy: mirror repeats query-time phrasing but is stale/incorrect.
            text=(
                base
                + " Mirrored documentation snapshot. As of 2024-09-15, this page claims the window is Answer: "
                + wrong
                + " (may lag behind the current manual)."
            ),
            paragraph_spans=[],
        )
        docs = [d_stale, d_fresh, d_mirror]
        cluster = ClusterRecord(
            cluster_id=cid,
            relation_type="fresh_vs_stale",
            document_ids=[d.doc_id for d in docs],
            canonical_source_id=d_fresh.doc_id,
        )
        q = QueryRecord(
            query_id=qid,
            query_text=(
                f"For cluster {cid}, as of 2024-09-15, how long after posted notice to file Form X-12?"
            ),
            domain="synthetic_documentation_policy",
            query_time=q_time,
            query_jurisdiction=q_jur,
            gold_answer=correct,
            acceptable_answers=[],
            gold_evidence_ids=[d_fresh.doc_id],
            minimal_evidence_ids=[d_fresh.doc_id],
            preferred_source_ids=[d_fresh.doc_id],
            abstain_required=False,
        )

    elif family == "C":
        correct = "30 days"
        wrong = "21 days"
        d_farm = DocumentRecord(
            doc_id=f"{cid}_farm",
            cluster_id=cid,
            source_url=f"https://contentfarm.example/a/{cid}",
            source_type="scrape",
            authority_level=1,
            publication_date=date(2024, 7, 1),
            validity_start=date(2024, 7, 1),
            validity_end=date(2026, 12, 31),
            jurisdiction="US",
            original_or_copy_label="copy",
            # Lexical decoy: content farm over-optimizes for the exact query wording but is wrong.
            text=(
                base
                + " Explainer article: filing window for Form X-12 after notice (definitive guide). Answer: "
                + wrong
                + " Sponsored content."
            ),
            paragraph_spans=[],
        )
        d_off = DocumentRecord(
            doc_id=f"{cid}_agency",
            cluster_id=cid,
            source_url=f"https://agency.example/rules/{cid}",
            source_type="official_pdf",
            authority_level=5,
            publication_date=date(2024, 6, 10),
            validity_start=date(2024, 6, 10),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " Agency rulebook excerpt. Answer: " + correct + " Binding interpretation.",
            paragraph_spans=[],
        )
        d_tert = DocumentRecord(
            doc_id=f"{cid}_textbook",
            cluster_id=cid,
            source_url=f"https://edu.example/notes/{cid}",
            source_type="tertiary",
            authority_level=3,
            publication_date=date(2024, 8, 1),
            validity_start=date(2024, 8, 1),
            validity_end=date(2026, 12, 31),
            jurisdiction="US",
            original_or_copy_label="summary",
            text=base + " Student notes summary. Answer: " + wrong + " Check primary sources.",
            paragraph_spans=[],
        )
        docs = [d_farm, d_off, d_tert]
        cluster = ClusterRecord(
            cluster_id=cid,
            relation_type="authority_split",
            document_ids=[d.doc_id for d in docs],
            canonical_source_id=d_off.doc_id,
        )
        q = QueryRecord(
            query_id=qid,
            query_text=f"For cluster {cid}, what is the filing window for Form X-12 after notice?",
            domain="synthetic_documentation_policy",
            query_time=q_time,
            query_jurisdiction=q_jur,
            gold_answer=correct,
            acceptable_answers=[],
            gold_evidence_ids=[d_off.doc_id],
            minimal_evidence_ids=[d_off.doc_id],
            preferred_source_ids=[d_off.doc_id],
            abstain_required=False,
        )

    elif family == "D":
        correct = "30 days"
        wrong_eu = "45 days"
        d_us = DocumentRecord(
            doc_id=f"{cid}_us",
            cluster_id=cid,
            source_url=f"https://reg.us.example/{cid}",
            source_type="regulation",
            authority_level=5,
            publication_date=date(2024, 5, 1),
            validity_start=date(2024, 5, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " United States regulatory excerpt. Answer: " + correct + " Applies to US notices.",
            paragraph_spans=[],
        )
        d_eu = DocumentRecord(
            doc_id=f"{cid}_eu",
            cluster_id=cid,
            source_url=f"https://reg.eu.example/{cid}",
            source_type="regulation",
            authority_level=5,
            publication_date=date(2024, 5, 1),
            validity_start=date(2024, 5, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction="EU",
            original_or_copy_label="original",
            text=base + " European regulatory excerpt. Answer: " + wrong_eu + " Applies to EU notices.",
            paragraph_spans=[],
        )
        d_blog = DocumentRecord(
            doc_id=f"{cid}_intl_blog",
            cluster_id=cid,
            source_url=f"https://blog.example/intl/{cid}",
            source_type="blog",
            authority_level=2,
            publication_date=date(2024, 6, 1),
            validity_start=date(2024, 6, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction=None,
            original_or_copy_label="summary",
            # Lexical decoy: repeats "under US rules" but accidentally cites the EU window.
            text=(
                base
                + " International comparison blog. Under US rules, the window is Answer: "
                + wrong_eu
                + " (note: this post sometimes conflates jurisdictions)."
            ),
            paragraph_spans=[],
        )
        docs = [d_us, d_eu, d_blog]
        cluster = ClusterRecord(
            cluster_id=cid,
            relation_type="jurisdiction_mismatch",
            document_ids=[d.doc_id for d in docs],
            canonical_source_id=d_us.doc_id,
        )
        q = QueryRecord(
            query_id=qid,
            query_text=f"For cluster {cid}, under US rules, how long after notice to file Form X-12?",
            domain="synthetic_documentation_policy",
            query_time=q_time,
            query_jurisdiction="US",
            gold_answer=correct,
            acceptable_answers=[],
            gold_evidence_ids=[d_us.doc_id],
            minimal_evidence_ids=[d_us.doc_id],
            preferred_source_ids=[d_us.doc_id],
            abstain_required=False,
        )

    elif family == "E":
        a1 = "30 days"
        a2 = "45 days"
        d_a = DocumentRecord(
            doc_id=f"{cid}_a",
            cluster_id=cid,
            source_url=f"https://authority-a.example/{cid}",
            source_type="official_html",
            authority_level=5,
            publication_date=date(2024, 6, 1),
            validity_start=date(2024, 6, 1),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " Source A interpretation. Answer: " + a1 + " Cites directive A-12.",
            paragraph_spans=[],
        )
        d_b = DocumentRecord(
            doc_id=f"{cid}_b",
            cluster_id=cid,
            source_url=f"https://authority-b.example/{cid}",
            source_type="official_html",
            authority_level=5,
            publication_date=date(2024, 6, 2),
            validity_start=date(2024, 6, 2),
            validity_end=date(2027, 12, 31),
            jurisdiction="US",
            original_or_copy_label="original",
            text=base + " Source B interpretation. Answer: " + a2 + " Cites directive B-9.",
            paragraph_spans=[],
        )
        docs = [d_a, d_b]
        cluster = ClusterRecord(
            cluster_id=cid,
            relation_type="conflict",
            document_ids=[d.doc_id for d in docs],
            canonical_source_id=None,
        )
        q = QueryRecord(
            query_id=qid,
            query_text=(
                f"For cluster {cid}, what is the definitive filing window for Form X-12 after notice "
                f"when authoritative sources disagree?"
            ),
            domain="synthetic_documentation_policy",
            query_time=q_time,
            query_jurisdiction="US",
            gold_answer="ABSTAIN",
            acceptable_answers=["INSUFFICIENT_EVIDENCE", "cannot determine"],
            gold_evidence_ids=[d_a.doc_id, d_b.doc_id],
            minimal_evidence_ids=[d_a.doc_id, d_b.doc_id],
            preferred_source_ids=[],
            abstain_required=True,
        )
    else:
        raise ValueError(family)

    return docs, cluster, q


def generate_synthetic_release(
    out_dir: str | Path,
    instances_per_family: int = 240,
    seed: int = 42,
) -> GeneratorStats:
    """
    Emit `documents.jsonl`, `clusters.jsonl`, `queries.jsonl`, and `manifest.json`.
    Five families (A–E) × `instances_per_family` clusters by default → 1200 queries.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    families = ["A", "B", "C", "D", "E"]
    all_docs: list[DocumentRecord] = []
    all_clusters: list[ClusterRecord] = []
    all_queries: list[QueryRecord] = []

    for fam in families:
        for i in range(instances_per_family):
            docs, cl, q = _make_cluster(fam, i)
            all_docs.extend(docs)
            all_clusters.append(cl)
            all_queries.append(q)

    write_jsonl(out / "documents.jsonl", all_docs)
    write_jsonl(out / "clusters.jsonl", all_clusters)
    write_jsonl(out / "queries.jsonl", all_queries)

    stats = GeneratorStats(
        clusters=len(all_clusters),
        documents=len(all_docs),
        queries=len(all_queries),
        seed=seed,
    )
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "clusters": stats.clusters,
                "documents": stats.documents,
                "queries": stats.queries,
                "seed": stats.seed,
                "instances_per_family": instances_per_family,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return stats
