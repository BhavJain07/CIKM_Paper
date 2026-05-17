# Zenodo deposit (Resource track requirement)

CIKM Resource papers expect a **persistent archive with DOI** for the dataset/software resource.

## What to upload

Create a zip containing:

- `corpora/annotations/synthetic_v1/` (all JSONL + manifest)
- `corpora/annotations/wiki_freshness_v1/`
- `corpora/annotations/combined_v1/`
- `corpora/DATASET.md`
- `results/` (optional: metrics JSON for frozen leaderboard numbers)

## Steps

1. Go to [https://zenodo.org](https://zenodo.org) and sign in.
2. **New upload** → drag the zip.
3. Title: `ProvBench-RAG v1 benchmark annotations`
4. Authors: match the paper author list.
5. License: CC BY 4.0 (or MIT if you prefer code-style; be consistent with paper).
6. Publish → copy the **DOI** (e.g. `10.5281/zenodo.1234567`).
7. Replace the placeholder in `paper/main.tex` (`10.5281/zenodo.XXXXXXX`).
8. Add the DOI to `README.md` and `CITATION.cff`.

Do this **before camera-ready** (August 20, 2026); you can note “DOI pending” in the June 6 submission if the upload is in progress.
