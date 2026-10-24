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
7. Commit messages: a specific summary line (e.g. "Phase 3: compute stellar flux, habitable zones,
   and candidate table") plus a short body listing the main changes. Every phase summary shows the
   commit hash next to the full commit message. History was never pushed; reword only unpushed commits,
   and only after showing the plan.

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
- `src/archive.py` has `download_tap_csv`, `download_file` (non-TAP files, writes a `.source.txt`
  citation/licence note) and `latest_snapshot`; reuse them for every download.

## Rocky classification rules (Phase 2, user approved; code in `src/rocky.py`)
- Impossible values (<= 0 for sizes/masses/orbits/temps/distance/insolation; eccentricity outside
  [0, 1)) become NaN; rows are never dropped for them.
- `rocky_path`: microlensing -> `excluded` (user decision); measured radius (reflink not
  "Calculated Value") -> `measured radius`; else measured mass (Msini, Mass, Msin(i)/sin(i)) ->
  `mass only` (renamed from "minimum mass"; estimated radius ignored; `mass_type` = minimum/true); else `excluded`.
- `rocky_label`: radius path R <= 1.6 rocky (Rogers 2015), 1.6 < R <= 2.0 possibly rocky,
  > 2.0 not rocky (2.0 from Bohl et al. 2026 Sec. 1 and 3); mass path M <= 5 possibly rocky,
  > 5 not rocky (Bohl et al. Sec. 1 and 3). Mass-path planets are never "rocky".
- **Circularity rule:** a mass with `pl_bmassprov == "M-R relationship"` is never used to support,
  confirm, or change a rocky label (it equals the Chen & Kipping formula applied to the radius).
- Bohl et al. used NEA default values (2025-12-20) with Gaia DR3 stellar updates, not pscomppars.
- Figures use `src/plot_style.py` (`apply_style()`, fixed series color order, `teff_colormap()` diverging
  red-neutral-blue centered on 5772 K). Label points with `src/plot_labels.annotate_without_overlap` and
  assert `not text_boxes_overlap(...)` (it redraws first; Annotation extents include leader lines, so it
  measures text only).
- Figures so far: `radius_histogram.png`, `insolation_comparison.png`, `radius_vs_insolation.png`,
  `teff_vs_insolation_hz.png`. Mass-only candidates are drawn hollow at the archive's estimated radius.

## Energy and habitable zone rules (Phase 3, user approved; code in `src/physics.py`, `src/habitable_zone.py`)
- L = 10**st_lum, else R^2 (Teff/5772)^4. S = L/a^2; final `insol` = archive `pl_insol`, gaps filled by ours.
- T_eq uses T0 = (1361 / 4 sigma)^0.25 = 278.3 K (IAU 2015 B3 + CODATA), not the brief's 278.6 K (S0 = 1367).
- `flux_orbit_avg` = S / sqrt(1 - e^2) only when e is measured (`pl_orbeccenlim == 0`, has uncertainty,
  0 <= e < 1). `hz_flux` = orbit-averaged where available, else S (Bohl Sec. 2 treats upper limits as e = 0).
- HZ zones: simple windows (K14 solar values, ignore Teff); K14 conservative (Runaway Greenhouse 1 Me /
  Max Greenhouse) and optimistic (Recent Venus / Early Mars), K14 Table 1; Bohl empirical = Kopparapu 2013
  Table 3 RV/EM (reproduces Bohl Table 1); Bohl 3D = Ramirez & Kaltenegger 2018 Table 2 "Leconte" inner edge
  + K13 Early Mars (known: ~0.08-0.12 higher than Bohl's printed 3D values for M dwarfs).
- Strict Teff range 2600-7200 K (user decision): outside -> "outside model range", never extrapolated.
- Candidates (`data/processed/hz_candidates.csv`, 49): rocky or possibly rocky AND (`hz_k14_optimistic ==
  "inside"` OR star outside 2600-7200 K but inside K14 optimistic limits evaluated at the nearest valid Teff,
  `clamp_teff`). The clamped extras (TRAPPIST-1 d/e/f/g) are kept with a `model_range_caveat` (user decision).
- Second 3D zone `hz_bohl_3d_interp`: linear interpolation of Bohl's printed `3DinnerFluxLimit` and
  `outerFluxLimit` vs stellar Teff from their Zenodo Table 1 (`data/raw/bohl2026_table1_*.csv`, CC-BY-4.0);
  outside 2566-5599 K -> "outside model range". Recovers their 24 planets from their own fluxes.
  Their CSV cites the 3D limit as Leconte 2013 + Ramirez & Kaltenegger **2014** (not 2018).
- Candidate selection uses `hz_flux`; switching to circular flux changes 0 planets in every zone.
- Post-Bohl flags from `ps` table snapshot (`data/raw/ps_dates_*.csv`): `new_since_bohl` (earliest
  releasedate > 2025-12-20), `updated_since_bohl` (latest rowupdate > 2025-12-20), `after_bohl_cutoff` (either).
- **Phase 6 rule (user decision):** set aside ONLY `new_since_bohl` planets (157). Planets that were only
  `updated_since_bohl` stay in the comparison and are flagged as a possible reason for disagreement.
- Match planet names with Bohl et al. by lowercase + collapsed spaces (`normalize_name`).
- **Phase 6 to-do (user request):** compare the `pscomppars` values with the archive's default solution
  (`ps` table, `default_flag = 1`) for GJ 682 b, Kepler-1649 c and Kepler-441 b, to explain their flux gaps
  (up to 4x) with Bohl et al. (Bohl used NEA default values + Gaia DR3 stellar updates).

## Clustering rules (Phase 5, user approved; code in `src/clustering.py`)
- Cluster only measured-radius planets with all four features (4,622): log10 radius, log10 `hz_flux`,
  log10 period, raw Teff (brief); StandardScaler; KMeans `n_init=10`, `random_state=0`; stability checked
  with adjusted Rand index over seeds 0-4. Clusters renumbered by median flux (hottest = 0).
- Main `cluster` uses k = 4 (best silhouette tie, stable); `cluster_k6` kept for comparison. k >= 5 always
  isolates KOI-55 b/c (27,730 K star).
- Similarity to Earth = 1 / (1 + distance) in scaled space: `similarity_4feat` and `similarity_radius_flux`
  (unweighted ESI-style analogue; PHL's exact ESI equation was not verifiable, so not reproduced).
  Output: `data/processed/planets_clustered.csv`.
- Cluster plots: 3 hues + dark neutral for the giants, plus marker shapes (4 hues fail the all-pairs check).

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

**Current phase:** Phase 5 complete (k = 4 clusters, Earth similarity scores). Next: Phase 6.
