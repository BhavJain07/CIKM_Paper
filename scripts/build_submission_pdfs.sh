#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/paper"

echo "== SUBMISSION_GUIDE.pdf =="
pdflatex -interaction=nonstopmode SUBMISSION_GUIDE.tex >/dev/null
pdflatex -interaction=nonstopmode SUBMISSION_GUIDE.tex >/dev/null

echo "== abstract_submission.pdf =="
pdflatex -interaction=nonstopmode abstract_submission.tex >/dev/null
pdflatex -interaction=nonstopmode abstract_submission.tex >/dev/null

echo "== overleaf_bundle (Resource main.tex) =="
bash "${ROOT}/scripts/package_overleaf.sh"

echo ""
echo "Resource track: compile main.tex on Overleaf -> upload PDF by June 6, 2026"
ls -la SUBMISSION_GUIDE.pdf abstract_submission.pdf 2>/dev/null || true
