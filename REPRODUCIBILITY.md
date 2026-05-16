# Reproducibility

## Requirements

- Python 3.10+
- `pip install -e ".[dev]"`

## Full pipeline

```bash
bash scripts/reproduce_full.sh
python -m provbench_rag.scripts.export_paper_artifacts
bash scripts/build_submission_pdfs.sh
```

## Outputs

| Path | Description |
|------|-------------|
| `results/synthetic_v1/metrics.json` | Primary synthetic metrics |
| `results/synthetic_v1/extended/metrics_extended.json` | Stratified, ablations, bootstrap |
| `results/wiki_freshness_v1/metrics.json` | Wikipedia revision track |
| `results/combined_v1/metrics.json` | Pooled corpus |
| `paper/generated_macros.tex` | LaTeX numeric macros |

## Wikipedia crawl

Respect Wikimedia rate limits. Default `reproduce_public_data.sh` uses `WIKI_MAX_ARTICLES=15`; set `WIKI_MAX_ARTICLES=0` for the full seed list (slow).

## Tests

```bash
pytest -q
```
