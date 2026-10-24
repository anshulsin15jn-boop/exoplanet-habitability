# Exoplanet Habitability Project

## Goal
Use real data from the NASA Exoplanet Archive (Planetary Systems Composite Parameters
table, `pscomppars`) to find exoplanets that could potentially have liquid water on their
surface: rocky planets inside the habitable zone. Then check the results against NASA-linked
research:
- the Kopparapu et al. (2014) habitable zone model (temperature-dependent boundaries),
- the NASA Habitable Worlds Observatory (HWO) ExEP Precursor Science Stars list,
- Bohl et al. (2026), "Probing the Limits of Habitability: A Catalogue of Rocky Exoplanets
  in the Habitable Zone" (arXiv 2501.14054).

## About the user
College student learning data science. Comfortable with pandas, basic Python, Calculus I & II,
and intro statistics. Has **not** taken linear algebra.
- Before any code that uses a new concept, explain the concept in 2-3 plain sentences.
- Prefer clear, readable code over clever code.

## Folder layout
```
data/raw/          untouched archive downloads, dated filenames, COMMITTED for reproducibility
data/large/        files over 50 MB (git-ignored; none expected)
data/processed/    cleaned tables and candidate lists
notebooks/         exoplanet_habitability.ipynb (main work; must also open in Google Colab)
src/physics.py     reusable physics functions (insolation, luminosity, T_eq), tested
tests/             pytest tests for src/
figures/           every plot saved as PNG
outputs/           final CSV deliverables (candidate table, Phase 6 comparison table)
```

## Working rules
1. Start each phase in plan mode; show the plan and wait for approval before writing files.
2. Work one phase at a time. At the end of each phase: show key outputs, summarize what we
   learned in 3-5 bullets, make a git commit, then wait for the user to say "next".
3. After every filter, print how many planets remain so the funnel is visible.
4. When a scientific threshold is a judgment call, state the value chosen, its source, and
   one alternative.
5. Never invent column names, table names, or scientific constants. Check the archive's
   documentation or the source paper, and say so when unsure.
6. Before deleting or overwriting any existing file, show what will change and wait for
   confirmation.

## Data rules
- Download from the archive's TAP API once; save the raw CSV in `data/raw/` with the download
  date in the filename. Afterward, load from that file instead of calling the API again.
- Commit every raw snapshot (the archive updates over time). Never overwrite an existing
  snapshot; a new download gets a new date. Files over 50 MB go in `data/large/` instead.
- Downloads are written to a `*.part` file and renamed when complete (`*.part` is git-ignored).
- Code creates the folders it needs (`mkdir(parents=True, exist_ok=True)`).
- Drop rows only for the columns a given step actually needs (never a blanket `dropna()`).
- The pscomppars snapshot has the user's 16 columns plus 3 source columns (user approved):
  `pl_rade_reflink` and `pl_insol_reflink` contain "Calculated Value" when the archive computed
  the number (radius from mass via Chen & Kipping 2017; insolation from L/a^2), and
  `pl_bmassprov` is one of Mass / Msini / Msin(i)/sin(i) / M-R relationship.
- `src/archive.py` has `download_tap_csv` and `latest_snapshot`; reuse them for any archive table.

## Rocky classification rules (Phase 2, user approved; code in `src/rocky.py`)
- Impossible values (<= 0 for sizes/masses/orbits/temps/distance/insolation; eccentricity outside
  [0, 1)) become NaN; rows are never dropped for them.
- `rocky_path`: microlensing -> `excluded` (user decision); measured radius (reflink not
  "Calculated Value") -> `measured radius`; else measured mass (Msini, Mass, Msin(i)/sin(i)) ->
  `minimum mass` (estimated radius ignored; `mass_type` = minimum/true); else `excluded`.
- `rocky_label`: radius path R <= 1.6 rocky (Rogers 2015), 1.6 < R <= 2.0 possibly rocky,
  > 2.0 not rocky (2.0 from Bohl et al. 2026 Sec. 1 and 3); mass path M <= 5 possibly rocky,
  > 5 not rocky (Bohl et al. Sec. 1 and 3). Mass-path planets are never "rocky".
- **Circularity rule:** a mass with `pl_bmassprov == "M-R relationship"` is never used to support,
  confirm, or change a rocky label (it equals the Chen & Kipping formula applied to the radius).
- Bohl et al. used NEA default values (2025-12-20) with Gaia DR3 stellar updates, not pscomppars.
- Figures use `src/plot_style.py` (`apply_style()`, fixed series color order).

## Code rules
- Keep notebook code compatible with Google Colab's Python (about 3.11-3.12): no 3.13+ only syntax.
- Code must run on pandas 2.x (Colab) and 3.x (local). Assign with `df.loc[mask, "col"] = ...`
  (never chained assignment), use `.copy()` for subsets we modify later, and never select text
  columns with `select_dtypes(include="object")`. When output differs between versions, add a
  one-line note pointing to the notebook's "pandas 2 vs pandas 3" cell.
- At the end of each phase, run the notebook in both `.venv` (pandas 3) and `.venv-pandas2`.
- The notebook adds the project root to `sys.path` so `from src import physics` works.

## How to run (Windows)
```
.venv\Scripts\activate
python -m pytest
jupyter nbconvert --to notebook --execute notebooks/exoplanet_habitability.ipynb --output-dir outputs/_run
```
Set up from scratch: `py -3.14 -m venv .venv` then `pip install -r requirements.txt`
(`requirements-lock.txt` holds the exact tested versions).

pandas 2 check environment:
```
py -3.14 -m venv .venv-pandas2
.venv-pandas2\Scripts\python -m pip install -r requirements.txt "pandas>=2.0,<3"
.venv-pandas2\Scripts\jupyter nbconvert --to notebook --execute notebooks/exoplanet_habitability.ipynb --output-dir outputs/_run/pandas2
```

## Roadmap
- Phase 0: project setup
- Phase 1: load the data (pscomppars via TAP)
- Phase 2: clean and filter, rocky labels, radius valley
- Phase 3: stellar energy (src/physics.py + tests), habitable zone flags, candidate table
- Phase 4: visualize
- Phase 5: KMeans clustering, PCA, similarity to Earth
- Phase 6: compare with NASA research (Kopparapu, HWO stars, Bohl et al.)
- Final: notebook runs top to bottom, tests pass, CSVs in outputs/, figures/, README.md

**Current phase:** Phase 2 complete (`data/processed/planets_classified.csv`; 1,808 rocky or possibly rocky). Next: Phase 3.
