#!/usr/bin/env bash
# Build submission PDFs that compile on BasicTeX (guide, abstract, draft).
# ACM sigconf PDF (main_acmart.pdf): use Overleaf — see paper/overleaf_bundle/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/paper"

echo "== SUBMISSION_GUIDE.pdf =="
pdflatex -interaction=nonstopmode SUBMISSION_GUIDE.tex >/dev/null
pdflatex -interaction=nonstopmode SUBMISSION_GUIDE.tex >/dev/null

echo "== abstract_submission.pdf =="
pdflatex -interaction=nonstopmode abstract_submission.tex >/dev/null
pdflatex -interaction=nonstopmode abstract_submission.tex >/dev/null

echo "== main.pdf (internal draft; upload main_acmart.pdf to CIKM) =="
pdflatex -interaction=nonstopmode main.tex >/dev/null
bibtex main >/dev/null || true
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null

echo "== overleaf_bundle/ =="
bash "${ROOT}/scripts/package_overleaf.sh"

echo ""
echo "Done:"
ls -la SUBMISSION_GUIDE.pdf abstract_submission.pdf main.pdf 2>/dev/null
echo ""
echo "CIKM upload (May 23): compile main_acmart.tex on Overleaf from paper/overleaf_bundle/"
echo "  then save PDF as paper/main_acmart.pdf"
