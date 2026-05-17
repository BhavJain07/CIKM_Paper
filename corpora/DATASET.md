# ProvBench-RAG v1 — Dataset card

## Motivation

Benchmark retrieval when multiple near-duplicate passages match a query but differ in provenance (authority, time, copy type, jurisdiction).

## Version

- **Release:** v1
- **Date:** 2026
- **Tracks:** `synthetic_v1`, `wiki_freshness_v1`, `combined_v1`

## Files per track

| File | Description |
|------|-------------|
| `documents.jsonl` | Clustered documents with provenance metadata |
| `clusters.jsonl` | Cluster membership and relation types |
| `queries.jsonl` | Queries, gold answers, evidence, preferred sources |
| `manifest.json` | Counts and build parameters |

## Composition

| Track | Queries | Documents | Notes |
|-------|---------|-----------|-------|
| synthetic_v1 | 1500 | 4200 | Five families A–E; lexical decoys in B–D |
| wiki_freshness_v1 | 140 | 420 | English Wikipedia revision triples |
| combined_v1 | 1640 | 4620 | Merged index, no domain router |

## Collection

- **Synthetic:** programmatic generator (`provbench_rag/synthetic/`), seed 42.
- **Wikipedia:** MediaWiki Action API, read-only, rate-limited crawl (`scripts/reproduce_public_data.sh`).
- **No PII** in synthetic text.

## License

- Code: MIT (repository root).
- Wikipedia text: subject to Wikimedia content terms; document URLs point to specific revisions.

## Reproducibility

```bash
bash scripts/reproduce_full.sh
```

## Archive

Deposit `corpora/annotations/` on Zenodo; cite DOI in the Resource paper.

## Maintenance

Issues and extensions via GitHub; schema versioned in `provbench_rag/schema.py`.
