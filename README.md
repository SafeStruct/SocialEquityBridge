# California Bridge Vulnerability Index (BVI)

PCA/PFA-based Bridge Vulnerability Index for California bridges, integrating NBI inventory data, displacement susceptibility, and spaceborne monitoring availability.

## How to cite

This repository contains code required to reproduce results for the paper entitled "Integrating structural and social vulnerability for equitable bridge maintenance prioritisation" published in International Journal of Disaster Risk Reduction (DOI [https://doi.org/10.1016/j.ijdrr.2026.106115](https://doi.org/10.1016/j.ijdrr.2026.106115)).

See also [`CITATION.cff`](CITATION.cff).

## Data availability

Input data, intermediate files, and pipeline outputs that reproduce the paper are published on Zenodo (external, intermediate, and outputs). Source URLs and licenses for third-party inputs are described in that dataset.

**DOI:** TODO — add Zenodo DOI after dataset publication

Until the DOI is available, configure `data_root` as described below and place the files listed under [Required inputs](#required-inputs).

## Installation

Requires Python 3.10.

**Poetry** (local pipeline — sufficient for most users):

```bash
poetry install
```

**Conda** (same default dependencies, Python 3.10):

```bash
conda env create -f environment.yml
conda activate bridge-vulnerability-california
```

**Optional HPC extras** — only needed to regenerate OSM bridge line shapefiles on a cluster with MPI. With Poetry:

```bash
poetry install --with hpc
```

With conda, additionally install `mpi4py`, `osmnx`, and `utm` (for example from conda-forge). Most users should skip this and use pre-generated OSM line files configured in `config/paths.yaml`.

Optional formatting hooks for contributors:

```bash
poetry install --with dev
pre-commit install
```

## Configuration

File paths are defined in `config/paths.yaml`. Analysis defaults (thresholds, PCA settings, Monte Carlo sample size, plot DPI, and related constants) are defined in `config/params.yaml`. Change values there rather than in scripts.

**Setup (first time):**

```bash
cp config/paths.example.yaml config/paths.yaml
# Edit config/paths.yaml and set data_root to your SOCIAL_PAPER directory
```

**Quick override** (without editing the file):

```bash
export BVI_DATA_ROOT=/mnt/e/SOCIAL_PAPER
```

Dated output folders (`PFA_results_{run_date}`, `plots_{run_date}`, `plots_maps_{run_date}`) use today's date (`DD_MM_YYYY`) automatically. To pin a specific run date:

```bash
export BVI_RUN_DATE=08_01_2026
```

**HPC override** (set in your Slurm script):

```bash
export BVI_DATA_ROOT=/path/to/data_root
```

**Custom config files:**

```bash
export BVI_PATHS_FILE=/path/to/my_paths.yaml
export BVI_PARAMS_FILE=/path/to/my_params.yaml
```

Pipeline scripts also accept the same settings as flags (no file edit needed):

```bash
poetry run python -m bridge_vulnerability.index.build_bvi \
  --data-root /path/to/data_root \
  --run-date 08_01_2026 \
  --log-level INFO
```

Common flags on every step: `--data-root`, `--run-date`, `--paths-file`, `--params-file`, `--log-level`, `--dry-run` (print resolved paths and exit). Monte Carlo additionally accepts `--analysis-type`, `--n-samples`, `--batch-size`, and `--plot-only` (replot Figs 8–9 from intermediate CSVs without re-running sampling). OSM MPI extraction accepts `--min_range` and `--chunk-size`.

**In Python scripts or notebooks:**

```python
from bridge_vulnerability.config.paths import paths, p

nbi_csv = paths.intermediate.nbi.bridges_enriched_csv
index_dir = paths.intermediate.index.dir
figures_dir = paths.outputs.figures.dir
tables_dir = paths.outputs.tables.dir
county_shp = p("external", "auxiliary", "counties_shp")
```

Paths are grouped by role in `config/paths.yaml`:

| Section | Meaning |
|---|---|
| `external` | Third-party or manual data — must exist before running the pipeline |
| `intermediate` | Files produced by one step and consumed by later steps (including glue CSVs under `intermediate/pfa_{run_date}/` and Monte Carlo dumps under `intermediate/sensitivity_{run_date}/`) |
| `outputs` | Paper artifacts only: `outputs/figures_{run_date}/` (`fig*.png` + paired `fig*.csv`) and `outputs/tables_{run_date}/` (`table*.csv`) |

## Required inputs

Before running the pipeline, set `data_root` in `config/paths.yaml` (or `BVI_DATA_ROOT`) and place the following files under that directory. Paths match `config/paths.example.yaml`.

### External data (download or obtain)

| Path under `data_root` | Used in |
|---|---|
| `California_brdgs/NBI/2024del/CA24.txt` | Step 1 — raw NBI inventory |
| `California_county_codes/county_codes.csv` | Step 6 — county FIPS / names |
| `California_county_GDP_2023/California_GDP_manually_extracted.xlsx` | Steps 6, 11 — county GDP |
| `California_borders/ca_counties/CA_Counties.shp` (+ sidecars) | Steps 8–9 — county boundaries |
| `CDC_Social_Vulnerability_2022/California_county_2022.csv` | Step 8 — CDC SVI |
| `California_subsidence/vertical_displacement_Govorcin_paper/CA_VLM.tif` | Step 4 — displacement raster |
| `ps_density/merged_california.tif` | Step 5 — PS density (see [External dependencies](#external-dependencies)) |

### Bundled intermediate (skip HPC steps 2–3b)

These are **not** produced by the local pipeline. Use the published data bundle or regenerate on HPC:

| Path under `data_root` | Used in |
|---|---|
| `HPC_output/combined_nbi_lines.shp` (+ sidecars) | Step 5 — displacement zonal stats |
| `HPC_output/nbi_segments_segment_1.shp` … `nbi_segments_segment_5.shp` | Step 5 — PS density zonal stats |

### Displacement susceptibility (manual if not bundled)

Step 5 reads `California_subsidence/vertical_displacement_Govorcin_paper/CA_VLM_fixed_filled2px.tif`. The data bundle includes this file. To recreate: run step 4, apply 2-pixel QGIS interpolation on `CA_VLM_fixed.tif`, and save as `CA_VLM_fixed_filled2px.tif`.

## Run the full pipeline (local)

For a single end-to-end run of all **non-HPC** steps (1, 4–11, including both Monte Carlo analyses), use:

```bash
poetry install
cp config/paths.example.yaml config/paths.yaml   # edit data_root
./run_full_pipeline.sh
```

The script checks required inputs, runs each step in order, and stops with QGIS instructions if the susceptibility raster is missing. Steps 2–3b (MPI OSM extraction and segment division) are skipped — pre-generated OSM shapefiles must already be present.

See the header of [`run_full_pipeline.sh`](run_full_pipeline.sh) for the same input checklist in plain text.

## Running the pipeline

Run every script from the repository root with Poetry:

```bash
poetry run python -m bridge_vulnerability.<package>.<module>
```

After step 1, steps 2–3 and step 4 (displacement) can run in parallel. Step 3b requires step 3. Step 5 requires step 3b outputs (or bundled shapefiles) and the displacement susceptibility raster. Steps 6–11 depend on earlier outputs as noted below.

### NBI inventory

**Step 1. `data_prep.nbi_read`** — Loads raw California NBI text data, filters tunnels and culverts, converts coordinates, and writes bridge tables with geometry.

**Input:** `external.nbi.raw_dir` / `external.nbi.raw_file` (raw NBI text file, e.g. `CA24.txt`). **Output:** `intermediate.nbi.bridges_csv`, `bridges_geo_csv`, and `bridges_shp`.

```bash
poetry run python -m bridge_vulnerability.data_prep.nbi_read
```

### OSM bridge lines — optional (HPC only; can run in parallel with step 4)

Most users should **skip steps 2–3b**. The published data bundle includes OSM bridge shapefiles in `{data_root}/HPC_output/` (paths relative to `data_root` in `config/paths.yaml`). Step 5 reads these files directly:

| File in `HPC_output/` | `paths.yaml` key | Used in |
|---|---|---|
| `combined_nbi_lines.shp` | `intermediate.osm.combined_lines` | Step 5 — displacement zonal stats |
| `nbi_segments_segment_1.shp` … `nbi_segments_segment_5.shp` | `intermediate.osm.segments_pattern` | Step 5 — PS density zonal stats |

**If you are regenerating lines on HPC** (`poetry install --with hpc`), run steps 2–3b below. They write chunked shapefiles, combined layers, and five segment shapefiles under `intermediate.osm.hpc_output_dir`. If your output folder or filenames differ from the defaults above, update the `intermediate.osm.*` keys in `config/paths.yaml`.

**Step 2. `data_prep.osm_extract_mpi`** — Extracts OpenStreetMap road lines for each bridge using MPI on an HPC cluster (submit `hpc/run_osm_line_extraction.sbatch`).

**Input:** `intermediate.nbi.bridges_geo_csv`. **Output:** chunked shapefiles in `intermediate.osm.hpc_output_dir` (`nbi_lines_<start>_<end>.shp`, `nbi_polygons_<start>_<end>.shp`).

```bash
srun python -m bridge_vulnerability.data_prep.osm_extract_mpi --min_range 0
```

**Step 3. `data_prep.osm_combine_lines`** — Merges chunked OSM line and polygon shapefiles from the HPC output folder into combined layers.

**Input:** `intermediate.osm.hpc_output_dir` (`nbi_lines_*.shp`, `nbi_polygons_*.shp` from step 2). **Output:** `intermediate.osm.combined_lines` and `intermediate.osm.combined_polygons`.

```bash
poetry run python -m bridge_vulnerability.data_prep.osm_combine_lines
```

**Step 3b. `data_prep.divide_into_segments`** — Divides each bridge centerline into five along-length segments for PS density zonal statistics.

**Input:** `intermediate.osm.combined_lines`, `intermediate.osm.combined_polygons`. **Output:** `intermediate.osm.centerlines` (`nbi_segments.shp`) and `intermediate.osm.segments_pattern` (`nbi_segments_segment_1.shp` … `_5.shp`).

```bash
poetry run python -m bridge_vulnerability.data_prep.divide_into_segments
```

### Displacement rasters (can run in parallel with steps 2–3)

**Step 4. `data_prep.displacement_fix_nodata`** — Replaces NaN nodata values in the Govorcin VLM displacement raster with a fixed placeholder value (999) for downstream zonal statistics.

**Input:** `external.displacement.vlm_raster` (e.g. `CA_VLM.tif`). **Output:** `intermediate.displacement.fixed_raster` (e.g. `CA_VLM_fixed.tif`).

```bash
poetry run python -m bridge_vulnerability.data_prep.displacement_fix_nodata
```

#### Displacement susceptibility raster (required for step 5)

Step 5 reads **`intermediate.displacement.susceptibility_raster`** (default: `CA_VLM_fixed_filled2px.tif`).

**Provided in the data bundle:** This file is included under `{data_root}/intermediate/...` so most users do not need to recreate it.

**How it was produced:** Step 4 converts missing VLM pixels (NaN) to a fixed nodata value of 999 (`CA_VLM_fixed.tif`). The susceptibility raster adds **2-pixel interpolation in QGIS** to fill remaining gaps so displacement values exist over all bridge locations — including areas where the original VLM data had no coverage due to loss of coherence over water or vegetated areas.

> *From the paper:* “For this work, interpolation was applied to the VLM dataset to fill missing data pixels and ensure coverage over all bridges not covered by the original data due to loss of coherence over water or vegetated areas.”

**To recreate from scratch:** Run step 4, open `CA_VLM_fixed.tif` in QGIS, apply 2-pixel interpolation to fill nodata pixels, and save the result as `CA_VLM_fixed_filled2px.tif` (or update `intermediate.displacement.susceptibility_raster` in `config/paths.yaml`).

### Bridge-level raster extraction

**Step 5. `data_prep.extract_bridge_raster_stats`** — Computes zonal statistics of displacement susceptibility and PS density along bridge lines and writes per-bridge CSV/shapefile outputs.

**Input:** `intermediate.osm.combined_lines`, `intermediate.osm.segments_pattern` (segments 1–5), `intermediate.displacement.susceptibility_raster`, `external.ps_density.raster`. **Output:** `intermediate.bridge_lines.displacement_csv`, `monitoring_csv`, and `combined_csv`.

```bash
poetry run python -m bridge_vulnerability.data_prep.extract_bridge_raster_stats
```

### NBI enrichment

**Step 6. `data_prep.nbi_enrich`** — Joins bridge inventory with county names, county GDP, and keeps only bridges that have OSM line statistics from step 5.

**Input:** `intermediate.nbi.bridges_geo_csv`, `intermediate.bridge_lines.displacement_csv`, `external.auxiliary.county_codes_csv`, `external.auxiliary.county_gdp_xlsx`. **Output:** `intermediate.nbi.bridges_enriched_csv` (e.g. `nbi_bridges_geo_county.csv`).

```bash
poetry run python -m bridge_vulnerability.data_prep.nbi_enrich
```

**Required for steps 7–10:** downstream scripts (`build_bvi`, `bridge_count_maps`, `monte_carlo`) read `intermediate.nbi.bridges_enriched_csv`, which only this step produces.

### Build BVI (PCA/PFA)

**Step 7. `index.build_bvi`** — Merges enriched NBI data with displacement/monitoring stats, aggregates to county level, and runs PCA/PFA to produce vulnerability weights and scaled indicators.

**Input:** `intermediate.nbi.bridges_enriched_csv`, `intermediate.bridge_lines.combined_csv`. **Output:** glue CSVs in `intermediate.index` (`county_level_df.csv`, `final_weights.csv`, `full_county_scaled.csv`); paper tables 7–9 in `outputs.tables.dir`; Figs 4–5 (`fig4_*.png` / `fig5_*.png` plus matching `.csv`) in `outputs.figures.dir`.

```bash
poetry run python -m bridge_vulnerability.index.build_bvi
```

### Result maps

**Step 8. `plotting.vulnerability_maps`** — Produces county-level vulnerability maps, bivariate plots, and indicator contribution figures from BVI outputs.

**Input:** `intermediate.index` (`county_level_df.csv`, `full_county_scaled.csv`, `final_weights.csv`), `external.auxiliary.counties_shp`, `external.auxiliary.cdc_svi_csv`. **Output:** paper maps as PNG in `outputs.figures.dir` (each with a same-name `.csv`); `intermediate.index.weighted_subindicators_csv` and `bivariate_bins_csv` for later steps.

```bash
poetry run python -m bridge_vulnerability.plotting.vulnerability_maps
```

**Step 9. `plotting.bridge_count_maps`** — Maps the number of bridges per county (only needs enriched NBI from step 6; can run before step 7).

**Input:** `intermediate.nbi.bridges_enriched_csv`, `external.auxiliary.counties_shp`. **Output:** `outputs.figures.dir/fig2_Number of Bridges_map.png` and matching `.csv`.

```bash
poetry run python -m bridge_vulnerability.plotting.bridge_count_maps
```

### Sensitivity analysis

**Step 10. `sensitivity.monte_carlo`** — Runs Monte Carlo / Sobol sensitivity analysis (slow; re-runs the index many times). Each analysis can take up to a few hours. The script supports **two separate analyses**; each run executes only one of them:

| `analysis_type` | What varies | What stays fixed |
|---|---|---|
| `"threshold"` (default) | Bridge-indicator thresholds (`ADT_THRESHOLD`, detour miles, waterway/scour ratings, displacement) | Base PCA settings in `base_pca_params` |
| `"pca"` | PCA/index settings (capping, skew/variance thresholds, aggregation method, Mahalanobis cutoff, dropped indicator) | Default thresholds in `default_thresholds` |

**Run both analyses** to get the full sensitivity picture. Either set `BVI_ANALYSIS_TYPE` or pass `--analysis-type` (no file edit needed):

```bash
# 1) Threshold sensitivity
poetry run python -m bridge_vulnerability.sensitivity.monte_carlo
# or: BVI_ANALYSIS_TYPE=threshold poetry run python -m bridge_vulnerability.sensitivity.monte_carlo

# 2) PCA / index sensitivity
poetry run python -m bridge_vulnerability.sensitivity.monte_carlo --analysis-type pca

# Replot Figs 8–9 from saved intermediate CSVs (no resampling)
poetry run python -m bridge_vulnerability.sensitivity.monte_carlo --analysis-type threshold --plot-only
poetry run python -m bridge_vulnerability.sensitivity.monte_carlo --analysis-type pca --plot-only
```

`run_full_pipeline.sh` runs both automatically.

**Input:** `intermediate.nbi.bridges_enriched_csv` (re-loaded internally for a full run), `intermediate.index.weighted_subindicators_csv` from step 8 (reference ranks for plots).

**Output:** ranking dumps in `intermediate.sensitivity.dir` (for replotting), tagged by `analysis_type`:
- `sensitivity_results_threshold_rankings.csv` / `sensitivity_results_pca_rankings.csv`
- `sobol_indices_threshold_rankings_wide.csv` / `sobol_indices_pca_rankings_wide.csv`

Paper Figs 8–9 (`fig8a`–`fig8c` for threshold, `fig9a`–`fig9c` for PCA, each with a paired `.csv`) are written to `outputs.figures.dir`. Use `--plot-only` to regenerate those figures from the intermediate CSVs without re-running Monte Carlo.

### Validation

**Step 11. `validation.benchmark_poor_bridges`** — Compares county BVI rank with poor-bridge replacement-cost rank (requires step 8 for `bivariate_bins.csv`).

**Input:** `intermediate.index.bivariate_bins_csv`, `external.auxiliary.county_gdp_xlsx`. **Output:** `outputs.tables.table10_csv` (`table10_bvi_poorbrdgs_benchmarking.csv`: BVI vs traditional replacement-cost rank, with BVI/SVI categories).

```bash
poetry run python -m bridge_vulnerability.validation.benchmark_poor_bridges
```

## Pipeline overview

```mermaid
flowchart TD
    A[NBI raw data] --> B[nbi_read]
    B --> E[osm_extract_mpi]
    E --> F[osm_combine_lines]
    G[VLM raster] --> H[displacement_fix_nodata]
    H --> H2[QGIS 2px interpolation]
    I[PS density raster] --> J[extract_bridge_raster_stats]
    F --> J
    H2 --> J
    J --> C[nbi_enrich]
    J --> K[build_bvi]
    J --> N[monte_carlo]
    C --> K
    K --> L[vulnerability_maps]
    C --> M[bridge_count_maps]
    C --> N
    L --> N
    L --> P[benchmark_poor_bridges]
```

## Repository structure

```
src/bridge_vulnerability/
├── config/                    # Path configuration loader
├── data_prep/                 # Steps 1–6: ingest and spatial extraction
├── index/                     # Step 7: PCA/PFA index construction
├── plotting/                  # Steps 8–9: result maps
├── sensitivity/               # Step 10: Monte Carlo / Sobol analysis
│   └── helpers/               # Plotting functions used by monte_carlo (not run directly)
├── validation/                # Step 11: poor-bridges benchmark
└── utils/                     # Shared helpers (OSM, monitoring class, PCA, plotting)

config/paths.example.yaml      # Path template (committed)
config/paths.yaml              # Your local paths (gitignored)
config/params.yaml             # Analysis defaults (thresholds, PCA, Monte Carlo)
run_full_pipeline.sh           # End-to-end local pipeline (steps 1, 4–11)
hpc/                           # Slurm batch scripts for MPI OSM extraction
environment.yml                # Conda environment (Python 3.10)
```

### Modules that are not run directly

These are imported by pipeline scripts; do not invoke them with `poetry run python -m ...`:

| Location | Purpose |
|---|---|
| `sensitivity/helpers/monte_carlo_plots.py` | Visualization helpers for `monte_carlo` |
| `data_prep/bridge_divisions.py` | Geometry helpers for `divide_into_segments` |
| `utils/osm_bridge_lines.py` | OSM line/polygon extraction logic for `osm_extract_mpi` (requires `--with hpc`) |
| `utils/monitoring_class.py` | Spaceborne monitoring classification for `extract_bridge_raster_stats` |
| `utils/pca.py` | PCA/PFA utilities for `build_bvi` and `monte_carlo` |
| `utils/plotting.py` | Map styling helpers for `vulnerability_maps` and `bridge_count_maps` |
| `config/paths.py` | Loads `config/paths.yaml` |
| `config/params.py` | Loads `config/params.yaml` |
| `config/cli.py` | Shared command-line flags for pipeline scripts |

## Pipeline I/O reference

| Step | Script | Reads | Writes |
|---|---|---|---|
| 1 | `nbi_read` | `external.nbi.*` | `intermediate.nbi.bridges_csv`, `bridges_geo_csv`, `bridges_shp` |
| 2–3 | `osm_extract_mpi` / `osm_combine_lines` | `intermediate.nbi.bridges_geo_csv`, `intermediate.osm.hpc_output_dir/nbi_lines_*.shp` (step 3) | `intermediate.osm.hpc_output_dir/nbi_lines_*.shp`, `nbi_polygons_*.shp`, `combined_nbi_lines.shp`, `combined_nbi_polygons.shp` |
| 3b | `divide_into_segments` | `intermediate.osm.combined_lines`, `combined_nbi_polygons` | `nbi_segments.shp`, `nbi_segments_segment_*.shp` |
| 4 | `displacement_fix_nodata` | `external.displacement.vlm_raster` | `intermediate.displacement.fixed_raster` |
| — | QGIS 2px interpolation (manual) | `intermediate.displacement.fixed_raster` | `intermediate.displacement.susceptibility_raster` |
| 5 | `extract_bridge_raster_stats` | `external.ps_density.*`, `intermediate.displacement.susceptibility_raster`, `intermediate.osm.*` | `intermediate.bridge_lines.*` |
| 6 | `nbi_enrich` | `external.auxiliary.*`, `intermediate.nbi.bridges_geo_csv`, `intermediate.bridge_lines.displacement_csv` | `intermediate.nbi.bridges_enriched_csv` |
| 7 | `build_bvi` | `intermediate.nbi.bridges_enriched_csv`, `intermediate.bridge_lines.combined_csv` | `intermediate.index/*`, `outputs.tables/table7–9`, `outputs.figures/fig4–5` |
| 8 | `vulnerability_maps` | `intermediate.index/*`, `external.auxiliary.*` | `outputs.figures/fig3, fig6–7, fig10–14`; `intermediate.index/weighted_subindicators.csv`, `bivariate_bins.csv` |
| 9 | `bridge_count_maps` | `intermediate.nbi.bridges_enriched_csv`, `external.auxiliary.counties_shp` | `outputs.figures/fig2_*` |
| 10 | `monte_carlo` (run twice: `analysis_type` `"threshold"` then `"pca"`; `--plot-only` to skip sampling) | enriched NBI + `intermediate.index.weighted_subindicators_csv` (from step 8) | `intermediate.sensitivity/*_rankings*.csv`; `outputs.figures/fig8–9` |
| 11 | `benchmark_poor_bridges` | `intermediate.index.bivariate_bins_csv`, `external.auxiliary.county_gdp_xlsx` | `outputs.tables.table10_csv` |

## Paper figures

Dated folders use `BVI_RUN_DATE` (default: today as `DD_MM_YYYY`). Paper figures live in `outputs/figures_{run_date}/`; tables in `outputs/tables_{run_date}/`. Each figure is a PNG with a sibling CSV of the plotted values. Minimum paper-only sequence: steps 7 → 8 → 9 → 10 → 11 (step 9 does not need step 7).

| Paper figure / table | Output file | Folder | Step | Script |
|---|---|---|---|---|
| Fig. 2 | `fig2_Number of Bridges_map.png` | `outputs.figures.dir` | 9 | `bridge_count_maps` |
| Fig. 3a–i | `fig3a_Traffic load.png` … `fig3i_Lack of monitoring.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 4 | `fig4_correlation_matrix_scaled.png` | `outputs.figures.dir` | 7 | `build_bvi` |
| Fig. 5 | `fig5_residual_correlations.png` | `outputs.figures.dir` | 7 | `build_bvi` |
| Fig. 6 | `fig6_infrastructure_vulnerability.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 7 | `fig7_dominant_sub_indicator_group.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 8a–c | `fig8a_rankings_uncertainty_threshold.png`, `fig8b_sobol_absolute_variance_decomposition_threshold.png`, `fig8c_sobol_total_effects_threshold.png` | `outputs.figures.dir` | 10 | `monte_carlo --analysis-type threshold` |
| Fig. 9a–c | `fig9a_rankings_uncertainty_pca.png`, `fig9b_sobol_absolute_variance_decomposition_pca.png`, `fig9c_sobol_total_effects_pca.png` | `outputs.figures.dir` | 10 | `monte_carlo --analysis-type pca` |
| Fig. 10a–d | `fig10a_social_vulnerability_Socioeconomic status.png` … `fig10d_social_vulnerability_Housing type & transportation.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 11 | `fig11_social_vulnerability_Social Vulnerability Index (SVI).png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 12 | `fig12_scatter_social_vs_bridge_vulnerability_subplots.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 13 | `fig13_scatter_matrix_bridge_vs_social.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Fig. 14 | `fig14_bivariate.png` | `outputs.figures.dir` | 8 | `vulnerability_maps` |
| Table 7 | `table7_pca_features_components.csv` | `outputs.tables.dir` | 7 | `build_bvi` |
| Table 8 | `table8_pcfa_eigenvalues.csv` | `outputs.tables.dir` | 7 | `build_bvi` |
| Table 9 | `table9_pcfa_factor_loadings_rotated.csv` | `outputs.tables.dir` | 7 | `build_bvi` |
| Table 10 | `table10_bvi_poorbrdgs_benchmarking.csv` | `outputs.tables.dir` | 11 | `benchmark_poor_bridges` |

### CSV columns

Each `fig*.png` has a sibling `fig*.csv` of the plotted values (not the full pipeline dumps). Values are rounded in tables 7–9 to two decimals.

| Files | Columns |
|---|---|
| Figs 2, 3a–i, 6, 10a–d, 11 | `County Name` / `County` (Fig. 2), `County_Code`, mapped value, `bin` (colour interval). Fig. 2 also has `over_water_count`. |
| Fig. 4 | `indicator_row`, `indicator_col`, `correlation`, `p_value`, `significant_p05` |
| Fig. 5 | `indicator_row`, `indicator_col`, `residual_correlation` |
| Fig. 7 | County, three group contributions, `dominant_sub_indicator_group` (code), `dominant_group` (label) |
| Figs 8a / 9a | Per-county rank summary: `original_rank`, `min`, `p05`, `p25`, `median`, `p75`, `p95`, `max`, `mean` |
| Figs 8b / 9b | Per-county `total_variance`, `unexplained_variance`, plus one column per sampled parameter |
| Figs 8c / 9c | Per-county Sobol total-effect (`ST`) values by parameter |
| Figs 12–13 | Long form: county, `social_value`, BVI or `bridge_value`, panel `pearson_r` / `p_value` |
| Fig. 14 | Raw BVI and SVI, `final_scores_bin` / `SVI_bin`, `combined`, `BVI Category`, `Social Vulnerability` (High/Medium/Low) |
| Table 7 | Indicator rows × unrotated `PC1`… columns |
| Table 8 | Eigenvalues before extraction and after rotation (blank cells are unretained components) |
| Table 9 | Rotated factor loadings, unity-sum squared loadings, `Communality`; footer rows `Explained variance` and `Explained/total` |
| Table 10 | BVI rank vs poor-bridge replacement-cost rank, `Priority Shift` (Traditional − BVI), `BVI Category`, `Social Vulnerability` |

Full Monte Carlo sample dumps (`sensitivity_results_*_rankings.csv`, `sobol_indices_*_rankings_wide.csv`) stay under `intermediate.sensitivity.dir` for `--plot-only`; they are not the figure CSVs.

## External dependencies

PS density maps for California were generated with the PS prediction workflow in [SafeStruct/GlobalRiskBridge](https://github.com/SafeStruct/GlobalRiskBridge) (`src/ps_predictions/predict_PS_dens.ipynb`). That notebook currently supports regions within a single 1×1° tile. To recreate the statewide PS prediction raster, generate all tiles separately and merge them (for example in QGIS). The published data bundle includes the merged California PS-density GeoTIFF required as input to step 5 (`ps_density/merged_california.tif`, `external.ps_density.raster`), so regenerating the PS density map is optional.

## License

MIT
