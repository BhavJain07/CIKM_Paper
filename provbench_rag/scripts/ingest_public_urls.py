"""
Download public seed URLs (docs, standards excerpts) with robots-aware fetching.

Produces single-document clusters suitable for corpus expansion or BM25 indexing.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from provbench_rag.crawl.client import PoliteHttpClient
from provbench_rag.crawl.html_text import html_to_text
from provbench_rag.io import write_jsonl
from provbench_rag.schema import ClusterRecord, DocumentRecord


def _read_urls(path: Path) -> list[str]:
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        out.append(ln)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls-file", type=Path, default=Path("corpora/seeds/public_doc_urls.txt"))
    ap.add_argument("--out-dir", type=Path, default=Path("corpora/annotations/public_urls_v1"))
    args = ap.parse_args(argv)

    client = PoliteHttpClient()
    urls = _read_urls(args.urls_file)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out_dir / "raw_html"
    raw_dir.mkdir(exist_ok=True)

    documents: list[DocumentRecord] = []
    clusters: list[ClusterRecord] = []

    for url in urls:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        cid = f"url_{h}"
        did = f"doc_{h}"
        try:
            raw, ctype = client.get_bytes(url)
        except (OSError, PermissionError, ValueError) as e:
            print(f"SKIP {url}: {e}")
            continue
        (raw_dir / f"{h}.bin").write_bytes(raw)
        if "html" in (ctype or "").lower() or raw.lstrip()[:1] in (b"<", b"\xef"):
            text = html_to_text(raw.decode("utf-8", errors="replace"))
        else:
            text = raw.decode("utf-8", errors="replace")

        documents.append(
            DocumentRecord(
                doc_id=did,
                cluster_id=cid,
                source_url=url,
                source_type="public_http",
                authority_level=4,
                publication_date=None,
                validity_start=None,
                validity_end=None,
                jurisdiction=None,
                original_or_copy_label="original",
                text=text,
                paragraph_spans=[],
            )
        )
        clusters.append(
            ClusterRecord(
                cluster_id=cid,
                relation_type="authority_split",
                document_ids=[did],
                canonical_source_id=did,
            )
        )
        print(f"OK {url}")

    write_jsonl(args.out_dir / "documents.jsonl", documents)
    write_jsonl(args.out_dir / "clusters.jsonl", clusters)
    print(f"Wrote {len(documents)} documents to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
