# ProvBench-RAG

Benchmark and reference implementation for **provenance-sensitive retrieval** under near-duplicate source confusion (CIKM 2026 Full Research track).

## Overview

When many semantically similar documents differ in authority, freshness, jurisdiction, or copy type, standard retrieval metrics can hide rank-1 provenance failure. **ProvBench-RAG** provides clustered JSONL annotations (preferred sources, minimal evidence, abstention) and **PACER**, a transparent provenance-aware reranker over BM25 pools.

## Quick start

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
bash scripts/reproduce.sh          # synthetic track (~2 min)
bash scripts/reproduce_full.sh     # + Wikipedia + combined + extended
pytest -q
```

## Repository layout

| Path | Description |
|------|-------------|
| `provbench_rag/` | Schemas, retrieval, PACER, evaluation, experiment runners |
| `corpora/annotations/` | `synthetic_v1`, `wiki_freshness_v1`, `combined_v1` JSONL |
| `corpora/seeds/` | Wikipedia titles and public URL seeds |
| `results/` | `metrics.json` and LaTeX fragments consumed by the paper |
| `scripts/` | `reproduce.sh`, `reproduce_full.sh`, `package_overleaf.sh` |
| `paper/` | `main_acmart.tex` (ACM submission), `abstract_easychair.txt`, `SUBMISSION_GUIDE.pdf` |

## Reproduce paper numbers

```bash
bash scripts/reproduce_full.sh
python -m provbench_rag.scripts.export_paper_artifacts
bash scripts/package_overleaf.sh   # optional: paper/overleaf_bundle/ for ACM PDF
```

Compile the submission manuscript (Overleaf or full TeX Live):

```bash
cd paper && pdflatex main_acmart.tex && bibtex main_acmart && pdflatex main_acmart.tex && pdflatex main_acmart.tex
```

Working draft (single-column): `paper/main.tex` → `paper/main.pdf`.

## CIKM 2026 submission artifacts

| Artifact | File |
|----------|------|
| Step-by-step guide (PDF) | `paper/SUBMISSION_GUIDE.pdf` |
| Abstract text for EasyChair | `paper/abstract_easychair.txt` |
| Abstract reference PDF | `paper/abstract_submission.pdf` |
| Full paper (ACM, upload May 23) | `paper/main_acmart.pdf` (build via Overleaf bundle or local TeX) |

See `paper/SUBMISSION_GUIDE.pdf` for deadlines, desk-rejection checklist, and EasyChair steps.

## Data tracks

- **Synthetic** (1,500 queries, five provenance families A–E, lexical decoys in B–D).
- **Wikipedia revisions** (140 article clusters, programmatic gold).
- **Pooled** synthetic + Wikipedia in one BM25 index.

Wikipedia crawling uses conservative delays; set `WIKI_MAX_ARTICLES=0` for the full seed list in `corpora/seeds/wikipedia_titles.txt`.

## License

MIT — see [LICENSE](LICENSE).

## Citation

```bibtex
@inproceedings{provbench-rag2026,
  title={ProvBench-RAG: Provenance-Sensitive Retrieval Under Near-Duplicate Source Confusion},
  author={Anonymous},
  booktitle={Proceedings of CIKM},
  year={2026}
}
```

Replace `author` and venue metadata after acceptance.
