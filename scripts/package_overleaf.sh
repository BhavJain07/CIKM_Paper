#!/usr/bin/env bash
# Package a minimal Overleaf-upload bundle for CIKM ACM submission.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/paper/overleaf_bundle"
rm -rf "$OUT"
mkdir -p "$OUT/tables" "$OUT/results/synthetic_v1/extended"

cp "${ROOT}/paper/main_acmart.tex" "$OUT/"
cp "${ROOT}/paper/acmart.cls" "$OUT/"
cp "${ROOT}/paper/ACM-Reference-Format.bst" "$OUT/"
cp "${ROOT}/paper/references.bib" "$OUT/"
cp "${ROOT}/paper/generated_macros.tex" "$OUT/"
cp "${ROOT}/paper/macros_wiki.tex" "$OUT/"
cp "${ROOT}/paper/macros_combined.tex" "$OUT/"
cp -r "${ROOT}/paper/tables/"* "$OUT/tables/"
mkdir -p "$OUT/results/synthetic_v1/extended"
cp "${ROOT}/results/synthetic_v1/extended/"*.tex "$OUT/results/synthetic_v1/extended/"

cat > "$OUT/README.txt" <<'EOF'
Upload all files in this folder to Overleaf.
Use compiler: pdfLaTeX.
Main file: main_acmart.tex
Template: ACM acmart sigconf (already included via acmart.cls).
After compile, download main_acmart.pdf for EasyChair (May 23).
EOF

echo "Wrote ${OUT}/ ($(du -sh "$OUT" | awk '{print $1}'))"
