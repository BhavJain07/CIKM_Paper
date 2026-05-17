# Reproducibility (ProvBench-RAG Resource)

```bash
pip install -e ".[dev]"
bash scripts/reproduce_full.sh
python -m provbench_rag.scripts.export_paper_artifacts
```

Frozen outputs: `results/*/metrics.json`, `paper/generated_macros.tex`, `paper/tables/resource_summary_table.tex` (hand-synced summary).

Paper table numbers for Resource track: `paper/tables/resource_summary_table.tex` (from last `metrics.json` run).

Zenodo: see [ZENODO.md](ZENODO.md).
