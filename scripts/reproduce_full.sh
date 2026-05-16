#!/usr/bin/env bash
# Full pipeline: synthetic + optional public data + merge + all experiments + LaTeX export.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
"$PY" -m pip install -q -e ".[dev]"

echo "== Synthetic track =="
bash scripts/reproduce.sh

echo "== Public tracks (set WIKI_MAX_ARTICLES=0 for full Wikipedia seeds; slow) =="
bash scripts/reproduce_public_data.sh

echo "== Merge synthetic + Wikipedia =="
"$PY" -m provbench_rag.scripts.merge_corpora \
  --out-dir corpora/annotations/combined_v1 \
  --tracks corpora/annotations/synthetic_v1 corpora/annotations/wiki_freshness_v1

echo "== Combined experiments =="
"$PY" -m provbench_rag.scripts.run_experiments \
  corpora/annotations/combined_v1/documents.jsonl \
  corpora/annotations/combined_v1/queries.jsonl \
  --out-dir results/combined_v1

echo "== Export paper tables/macros from metrics.json =="
"$PY" -m provbench_rag.scripts.export_paper_artifacts

echo "== Extended evaluation (stratified, ablations, bootstrap, RRF baseline; ~5 min) =="
"$PY" -m provbench_rag.scripts.run_extended_experiments \
  corpora/annotations/synthetic_v1/documents.jsonl \
  corpora/annotations/synthetic_v1/queries.jsonl \
  --out-dir results/synthetic_v1/extended

echo "Done. Compile paper with: cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
