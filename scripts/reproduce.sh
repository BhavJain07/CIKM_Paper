#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Create .venv first: python3.12 -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'"
  exit 1
fi
"$PY" -m provbench_rag.scripts.build_dataset --out corpora/annotations/synthetic_v1 --instances-per-family 300
"$PY" -m provbench_rag.scripts.run_experiments \
  corpora/annotations/synthetic_v1/documents.jsonl \
  corpora/annotations/synthetic_v1/queries.jsonl \
  --out-dir results/synthetic_v1 \
  --paper-macros paper/generated_macros.tex
echo "Done. Metrics: results/synthetic_v1/metrics.json"
