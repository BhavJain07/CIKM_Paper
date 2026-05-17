# ProvBench-RAG

**CIKM 2026 Resource Track** — open benchmark for provenance-sensitive retrieval under near-duplicate source confusion.

## What this repository is

A **benchmark resource** (dataset + evaluation toolkit + reference baselines), not a single novel model paper:

- **JSONL corpora** with clustered near-duplicates and gold preferred sources
- **Metrics:** PSA@1, ProvScore, recall@k, nDCG@k
- **Three tracks:** synthetic (1,500 queries), Wikipedia revisions (140), pooled (1,640)
- **Reference rankings:** BM25, heuristics, RRF, PACER (diagnostic reranker)

## Why Resource track

| Factor | Resource vs Full Research |
|--------|---------------------------|
| Fit | Benchmark + GitHub artifact is the core contribution |
| Length | 4 pages (fits a focused release paper) |
| Review | Single-blind (names on PDF) |
| Deadlines | Abstract **May 30**, paper **June 6** (more time) |
| Desk-reject risk | Applied track rejects synthetic-only; Resource expects datasets |

## Quick start

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
bash scripts/reproduce_full.sh
```

## Submission artifacts

| File | Purpose |
|------|---------|
| `paper/main.tex` | **Resource track paper** (ACM `acmart` sigconf, 4 pages) |
| `paper/abstract_easychair.txt` | EasyChair abstract (**Resource** track) |
| `paper/SUBMISSION_GUIDE.pdf` | Step-by-step submission |
| `corpora/DATASET.md` | Dataset card (FAIR-style) |
| `ZENODO.md` | How to mint the required DOI |

**Before submit:** compile `paper/main.tex` on Overleaf (see `paper/provbench-rag-overleaf.zip`); Zenodo DOI can be added at camera-ready.

## Build paper PDF (Overleaf)

```bash
bash scripts/package_overleaf.sh
```

Upload `paper/overleaf_bundle/` to Overleaf → main file `main.tex` → pdfLaTeX + BibTeX → download PDF for EasyChair (**June 6**).

## Repository layout

| Path | Role |
|------|------|
| `provbench_rag/` | Schemas, BM25, PACER, metrics, experiment runners |
| `corpora/annotations/` | Frozen JSONL tracks |
| `results/` | `metrics.json` and LaTeX fragments |
| `scripts/reproduce_full.sh` | End-to-end rebuild |

## Citation

See `CITATION.cff`. Update DOI after Zenodo upload.

## License

MIT — see [LICENSE](LICENSE).
