# CIKM 2026 Resource — everything to do (in order)

## What you are submitting

- **Track:** CIKM 2026 **Resource** (in EasyChair)
- **Paper type:** Benchmark / dataset / software resource (not a “new SOTA model” paper)
- **Page limit:** 4 pages of content (including appendix if any) + **unlimited references**
- **Review:** **Single-blind** — put **real names** on the PDF

---

## Why your `main.pdf` still looks like 7 pages

The file **`paper/main.pdf` on disk is the OLD Full Research draft** (not recompiled since the Resource rewrite).

The **current** paper is **`paper/main.tex`** (~4 pages when compiled in ACM format on Overleaf).

**You must compile again** (Overleaf) and use the **new** PDF for CIKM. Ignore the old `main.pdf` until you replace it.

---

## Is the abstract ready?

**Yes**, for EasyChair **after you**:

1. Use track **CIKM 2026 Resource**
2. Paste text from **`paper/abstract_easychair.txt`** (paragraph only, not the TITLE/KEYWORDS lines)
3. Enter **real co-authors** and affiliations
4. **Nominate ≥1 author as reviewer**

Title for EasyChair:

`ProvBench-RAG: A Benchmark Resource for Provenance-Sensitive Retrieval Under Near-Duplicate Source Confusion`

**Experiments:** not re-run. Numbers in the paper match existing `results/*/metrics.json` and `paper/tables/resource_summary_table.tex`.

---

## What is a Zenodo DOI? (plain English)

- **GitHub** = where code and files live; URLs can change if you rename/move the repo.
- **Zenodo** = free academic archive (like a permanent library deposit).
- **DOI** = a permanent ID (e.g. `10.5281/zenodo.1234567`) that always points to that deposit.

Resource reviewers expect: “this dataset will still exist in 5 years.” GitHub + **Zenodo DOI** is the standard combo.

**For June 6:** GitHub URL in the paper is **required** for you. Zenodo can be:
- **Best:** upload before June 6 and put the real DOI in `paper/main.tex`, or  
- **OK for review:** write “Zenodo deposit in progress” and upload before **camera-ready (Aug 20)**.

Create the zip: `bash scripts/prepare_zenodo_zip.sh` → upload `dist/provbench-rag-v1-annotations.zip` at [zenodo.org](https://zenodo.org).

---

## Deadlines (11:59pm Anywhere on Earth)

| When | What |
|------|------|
| **May 30, 2026** | Abstract + authors in EasyChair |
| **June 6, 2026** | Upload paper PDF |
| **Aug 7, 2026** | Accept/reject notification |
| **Aug 20, 2026** | Camera-ready (+ final DOI in paper) |

---

## Step-by-step (do in this order)

### A. GitHub (you said you will add URL)

1. Push this repo to GitHub (public).
2. Confirm GitHub URL in **`paper/main.tex`**: `https://github.com/BhavJain07/CIKM_Paper`.
3. **`README.md`** and **`CITATION.cff`** already point to the same repo.
4. Quick check: clone in a fresh folder and run `bash scripts/reproduce.sh` (optional but good).

### B. Paper PDF (Overleaf — replaces old 7-page `main.pdf`)

1. On your Mac: `bash scripts/package_overleaf.sh`
2. Go to [overleaf.com](https://www.overleaf.com) → New Project → Upload Project.
3. Upload **`paper/provbench-rag-overleaf.zip`** (main.tex is at the zip root).
4. Set main document: **`main.tex`**.
5. Compile (pdfLaTeX + BibTeX). Fix only if Overleaf shows errors.
6. Check page count: **≤4 pages** of body before references.
7. In **`main.tex`** on Overleaf: set **real author names** (single-blind).
8. Download PDF → save as `paper/main.pdf` (overwrites old file).

### C. Zenodo (before or shortly after June 6)

1. `bash scripts/prepare_zenodo_zip.sh`
2. [zenodo.org](https://zenodo.org) → Upload → publish.
3. Copy DOI → paste into `paper/main.tex` (Availability section) → recompile PDF if you already submitted, update for camera-ready at latest.

### D. EasyChair abstract (by May 30)

1. [easychair.org/my/conference?conf=cikm26](https://easychair.org/my/conference?conf=cikm26)
2. New submission → **CIKM 2026 Resource**
3. Title + abstract from **`abstract_easychair.txt`**
4. Authors + keywords + **reviewer nomination**
5. Submit abstract registration

### E. EasyChair paper PDF (by June 6)

1. Same submission → upload the **new** Overleaf PDF (not the old 7-page one).
2. Final submit.

---

## Files cheat sheet

| File | Use |
|------|-----|
| `paper/abstract_easychair.txt` | Paste into EasyChair |
| `paper/main.tex` | Source; compile on Overleaf |
| `paper/overleaf_bundle/` | Upload folder for Overleaf |
| `paper/SUBMISSION_GUIDE.pdf` | Printable instructions |
| `corpora/DATASET.md` | Dataset documentation |
| `ZENODO.md` | Zenodo how-to |
| `TRACK.md` | Why Resource track |

---

## What was already done in the repo

- Paper rewritten for **Resource** (benchmark focus, 4-page structure)
- Abstract rewritten for **Resource**
- Summary results table (no new experiments)
- Dataset card, Zenodo script, Overleaf bundle, submission guides
- Old Full Research `main_acmart.tex` marked deprecated

---

## What only you can do

- Real author names in `main.tex` and EasyChair
- GitHub URL
- Overleaf compile → new PDF
- EasyChair clicks (Resource track, reviewer nom)
- Zenodo upload + DOI (strongly recommended by Aug 20; ideal by June 6)
