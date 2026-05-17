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
Required files in project root: main.tex, references.bib, acmart.cls, ACM-Reference-Format.bst
Compiler menu: pdfLaTeX -> BibTeX -> pdfLaTeX -> pdfLaTeX
If citations show "?", references.bib is missing or BibTeX did not run.
Limit: 4 pages content (incl. appendix) + references
EOF

ZIP="${ROOT}/paper/provbench-rag-overleaf.zip"
rm -f "$ZIP"
# Zip contents at archive root (main.tex at top level) for Overleaf Upload Project.
(cd "$OUT" && zip -r -q "$ZIP" .)

echo "Wrote ${OUT}/"
echo "Wrote ${ZIP}"
