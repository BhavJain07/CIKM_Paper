#!/usr/bin/env bash
# Package Overleaf bundle for CIKM 2026 Resource track (main.tex).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/paper/overleaf_bundle"
rm -rf "$OUT"
mkdir -p "$OUT/tables"

cp "${ROOT}/paper/main.tex" "$OUT/"
cp "${ROOT}/paper/acmart.cls" "$OUT/"
cp "${ROOT}/paper/ACM-Reference-Format.bst" "$OUT/"
cp "${ROOT}/paper/references.bib" "$OUT/"
cp "${ROOT}/paper/generated_macros.tex" "$OUT/"
cp -r "${ROOT}/paper/tables/"* "$OUT/tables/"

cat > "$OUT/README.txt" <<'EOF'
CIKM 2026 Resource Track — Overleaf upload
Main file: main.tex
Compiler: pdfLaTeX + BibTeX
Limit: 4 pages content (incl. appendix) + references
Single-blind: put real author names in main.tex before upload
EOF

echo "Wrote ${OUT}/"
