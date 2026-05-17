#!/usr/bin/env bash
# Create provbench-rag-v1-annotations.zip for Zenodo upload.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/dist"
mkdir -p "$OUT"
ZIP="${OUT}/provbench-rag-v1-annotations.zip"
rm -f "$ZIP"
(
  cd "${ROOT}/corpora"
  zip -r "$ZIP" annotations/synthetic_v1 annotations/wiki_freshness_v1 annotations/combined_v1 DATASET.md
)
echo "Created $ZIP"
echo "Upload this file to https://zenodo.org and paste the DOI into paper/main.tex"
