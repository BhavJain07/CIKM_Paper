#!/usr/bin/env bash
# Fetch real public data (no API keys): Wikipedia revisions + public HTTP seeds.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
"$PY" -m pip install -q -e ".[dev]"

echo "== Wikipedia freshness track (revision triples, programmatic gold) =="
# Omit --max-articles for the full seed list (slow; respect Wikimedia rate limits).
WIKI_MAX="${WIKI_MAX_ARTICLES:-15}"
"$PY" -m provbench_rag.scripts.build_wikipedia_freshness_track \
  --out-dir corpora/annotations/wiki_freshness_v1 \
  --revision-limit 35 \
  --max-articles "${WIKI_MAX}"

echo "== Public URL pack (single-doc clusters for corpus richness) =="
"$PY" -m provbench_rag.scripts.ingest_public_urls \
  --out-dir corpora/annotations/public_urls_v1

echo "== Evaluate Wikipedia track (writes results only to results/wiki_freshness_v1) =="
"$PY" -m provbench_rag.scripts.run_experiments \
  corpora/annotations/wiki_freshness_v1/documents.jsonl \
  corpora/annotations/wiki_freshness_v1/queries.jsonl \
  --out-dir results/wiki_freshness_v1

echo "Done."
