"""
Build a real Wikipedia revision track: three time-staggered snapshots per article.

Uses only the public MediaWiki API and index.php (no API key).
Gold labels are programmatic: preferred source = newest revision; answer = first sentence
of the newest revision text (freshness stress-test for retrieval).
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from provbench_rag.crawl.wikipedia import RevisionMeta, list_revisions, parse_revision_html
from provbench_rag.evaluation.text_extract import first_sentence
from provbench_rag.io import write_jsonl
from provbench_rag.schema import ClusterRecord, DocumentRecord, QueryRecord

USER_AGENT = (
    "ProvBench-RAG/0.1 (public dataset builder for academic research; "
    "contact: local-lab) Python-urllib"
)


def _read_titles(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        out.append(ln)
    return out


def _pick_three(revs: list[RevisionMeta]) -> tuple[RevisionMeta, RevisionMeta, RevisionMeta] | None:
    if len(revs) < 3:
        return None
    chrono = sorted(revs, key=lambda r: r.timestamp)
    # Oldest, median, newest among fetched window
    i0, i1, i2 = 0, len(chrono) // 2, len(chrono) - 1
    return chrono[i0], chrono[i1], chrono[i2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--titles-file",
        type=Path,
        default=Path("corpora/seeds/wikipedia_titles.txt"),
    )
    ap.add_argument("--out-dir", type=Path, default=Path("corpora/annotations/wiki_freshness_v1"))
    ap.add_argument("--revision-limit", type=int, default=30, help="Revisions to list per page")
    ap.add_argument("--max-articles", type=int, default=0, help="0 = all titles")
    args = ap.parse_args(argv)

    titles = _read_titles(args.titles_file)
    if args.max_articles:
        titles = titles[: args.max_articles]

    args.out_dir.mkdir(parents=True, exist_ok=True)

    documents: list[DocumentRecord] = []
    clusters: list[ClusterRecord] = []
    queries: list[QueryRecord] = []

    for title in titles:
        try:
            page_id, revs = list_revisions(title, args.revision_limit, USER_AGENT)
        except (KeyError, ValueError, OSError) as e:
            print(f"SKIP {title}: {e}")
            continue
        triple = _pick_three(revs)
        if triple is None:
            print(f"SKIP {title}: not enough revisions ({len(revs)})")
            continue
        old_r, mid_r, new_r = triple
        cid = f"wiki_page_{page_id}"

        texts: dict[int, str] = {}
        for r in (old_r, mid_r, new_r):
            try:
                texts[r.rev_id] = parse_revision_html(r.rev_id, USER_AGENT)
            except OSError as e:
                print(f"SKIP rev {r.rev_id} for {title}: {e}")
                texts[r.rev_id] = ""

        gold_sentence = first_sentence(texts.get(new_r.rev_id, ""))
        if not gold_sentence:
            print(f"SKIP {title}: empty gold sentence")
            continue

        # Validity windows: only newest applies at query_time (after newest revision).
        q_time_date = max(date.today(), new_r.timestamp.date())

        def doc_for(r: RevisionMeta) -> DocumentRecord:
            rid = f"wiki_{page_id}_{r.rev_id}"
            vs = r.timestamp.date()
            if r.rev_id == new_r.rev_id:
                ve: date | None = None
                auth = 5
                orig: str = "original"
            elif r.rev_id == mid_r.rev_id:
                ve = new_r.timestamp.date() - timedelta(days=1)
                auth = 5
                orig = "original"
            else:
                ve = mid_r.timestamp.date() - timedelta(days=1)
                auth = 5
                orig = "original"
            return DocumentRecord(
                doc_id=rid,
                cluster_id=cid,
                source_url=f"https://en.wikipedia.org/w/index.php?oldid={r.rev_id}",
                source_type="wikipedia_revision",
                authority_level=auth,
                publication_date=vs,
                validity_start=vs,
                validity_end=ve,
                jurisdiction=None,
                original_or_copy_label=orig,
                text=texts.get(r.rev_id, ""),
                paragraph_spans=[],
            )

        d_old = doc_for(old_r)
        d_mid = doc_for(mid_r)
        d_new = doc_for(new_r)
        documents.extend([d_old, d_mid, d_new])

        clusters.append(
            ClusterRecord(
                cluster_id=cid,
                relation_type="fresh_vs_stale",
                document_ids=[d_old.doc_id, d_mid.doc_id, d_new.doc_id],
                canonical_source_id=d_new.doc_id,
            )
        )

        qid = f"q_{cid}"
        queries.append(
            QueryRecord(
                query_id=qid,
                query_text=(
                    f'What is the first sentence of the English Wikipedia article "{title.replace("_", " ")}"? '
                    f"Answer with that sentence verbatim as it appears in the article."
                ),
                domain="wikipedia_revision_freshness",
                query_time=datetime(q_time_date.year, q_time_date.month, q_time_date.day, tzinfo=timezone.utc),
                query_jurisdiction=None,
                gold_answer=gold_sentence,
                acceptable_answers=[],
                gold_evidence_ids=[d_new.doc_id],
                minimal_evidence_ids=[d_new.doc_id],
                preferred_source_ids=[d_new.doc_id],
                abstain_required=False,
            )
        )
        print(f"OK {title} -> cluster {cid}", flush=True)

    write_jsonl(args.out_dir / "documents.jsonl", documents)
    write_jsonl(args.out_dir / "clusters.jsonl", clusters)
    write_jsonl(args.out_dir / "queries.jsonl", queries)

    manifest = {
        "track": "wikipedia_freshness_v1",
        "articles_ok": len(clusters),
        "documents": len(documents),
        "queries": len(queries),
        "titles_file": str(args.titles_file),
    }
    (args.out_dir / "manifest.json").write_text(
        __import__("json").dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {args.out_dir} ({manifest})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
