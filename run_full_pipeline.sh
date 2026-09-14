#!/usr/bin/env bash
#
# Run the full California BVI pipeline (local / non-HPC path).
#
# Excludes optional HPC steps (osm_extract_mpi, osm_combine_lines, divide_into_segments).
# Those OSM shapefiles must already be on disk — see "Required inputs" below.
#
# Prerequisites:
#   1. poetry install
#   2. cp config/paths.example.yaml config/paths.yaml  (set data_root)
#   3. All required input files present under data_root (checked below)
#
# =============================================================================
# REQUIRED INPUTS (paths relative to data_root in config/paths.yaml)
# =============================================================================
#
# External — download or obtain before running:
#
#   California_brdgs/NBI/2024del/CA24.txt
#       Raw California NBI inventory (step 1)
#
#   California_county_codes/county_codes.csv
#       County FIPS codes and names (step 6)
#
#   California_county_GDP_2023/California_GDP_manually_extracted.xlsx
#       County GDP (steps 6 and 11)
#
#   California_borders/ca_counties/CA_Counties.shp  (+ .shx, .dbf, .prj, …)
#       County boundaries for maps (steps 8–9)
#
#   CDC_Social_Vulnerability_2022/California_county_2022.csv
#       CDC Social Vulnerability Index (step 8)
#
#   California_subsidence/vertical_displacement_Govorcin_paper/CA_VLM.tif
#       Govorcin vertical displacement raster (step 4)
#
#   ps_density/merged_california.tif
#       Merged California PS-density GeoTIFF (step 5; from GlobalRiskBridge / data bundle)
#
# Bundled intermediate — not produced by this script; must exist before step 5:
#
#   HPC_output/combined_nbi_lines.shp  (+ sidecar files)
#   HPC_output/nbi_segments_segment_1.shp … nbi_segments_segment_5.shp
#       Pre-generated OSM bridge shapefiles (skip HPC steps 2–3b)
#
# Displacement susceptibility — one of:
#
#   California_subsidence/vertical_displacement_Govorcin_paper/CA_VLM_fixed_filled2px.tif
#       Preferred: included in the published data bundle
#   OR run step 4 below, then apply 2-pixel QGIS interpolation manually and save
#       as CA_VLM_fixed_filled2px.tif before continuing to step 5
#
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

run() {
  echo ""
  echo ">>> $*"
  "$@"
}

echo "Checking required inputs..."
poetry run python <<'PY'
from pathlib import Path

from bridge_vulnerability.config.paths import paths

missing: list[str] = []


def require(label: str, path: Path) -> None:
    if not path.exists():
        missing.append(f"  - {label}\n    {path}")


# External inputs
nbi_raw = paths.external.nbi.raw_dir / paths.external.nbi.raw_file
require("NBI raw file", nbi_raw)
require("County codes CSV", paths.external.auxiliary.county_codes_csv)
require("County GDP workbook", paths.external.auxiliary.county_gdp_xlsx)
require("County boundaries shapefile", paths.external.auxiliary.counties_shp)
require("CDC SVI CSV", paths.external.auxiliary.cdc_svi_csv)
require("Displacement VLM raster", paths.external.displacement.vlm_raster)
require("PS density raster", paths.external.ps_density.raster)

# Pre-generated OSM line files (HPC output bundle)
require("OSM combined bridge lines", paths.intermediate.osm.combined_lines)
for segment in range(1, 6):
    require(
        f"OSM bridge segment {segment}",
        Path(str(paths.intermediate.osm.segments_pattern).format(segment)),
    )

# Displacement susceptibility (manual QGIS step if missing)
susceptibility = paths.intermediate.displacement.susceptibility_raster
if not susceptibility.exists():
    missing.append(
        "  - Displacement susceptibility raster (missing — see run_full_pipeline.sh header)\n"
        f"    {susceptibility}"
    )

if missing:
    print("Missing required inputs:\n")
    print("\n".join(missing))
    print(
        "\nConfigure paths in config/paths.yaml (or set BVI_DATA_ROOT) and "
        "place the files listed above before re-running."
    )
    raise SystemExit(1)

print("All required inputs found.")
PY

# --- Step 1: NBI inventory ---
run poetry run python -m bridge_vulnerability.data_prep.nbi_read

# --- Step 4: Fix displacement nodata (step 4; parallel with skipped HPC steps) ---
run poetry run python -m bridge_vulnerability.data_prep.displacement_fix_nodata

poetry run python <<'PY'
from bridge_vulnerability.config.paths import paths

susceptibility = paths.intermediate.displacement.susceptibility_raster
if not susceptibility.exists():
    fixed = paths.intermediate.displacement.fixed_raster
    print(
        "\nDisplacement susceptibility raster not found:\n"
        f"  {susceptibility}\n\n"
        "Step 4 produced the fixed raster at:\n"
        f"  {fixed}\n\n"
        "Apply 2-pixel interpolation in QGIS, save as the susceptibility path above,\n"
        "then re-run this script (steps 1 and 4 will run again; that is safe).\n"
    )
    raise SystemExit(1)
PY

# --- Step 5: Bridge-level raster extraction ---
run poetry run python -m bridge_vulnerability.data_prep.extract_bridge_raster_stats

# --- Step 6: NBI enrichment ---
run poetry run python -m bridge_vulnerability.data_prep.nbi_enrich

# --- Step 7: Build BVI index ---
run poetry run python -m bridge_vulnerability.index.build_bvi

# --- Step 8: Vulnerability maps (also writes weighted_subindicators.csv for step 10) ---
run poetry run python -m bridge_vulnerability.plotting.vulnerability_maps

# --- Step 9: Bridge count maps ---
run poetry run python -m bridge_vulnerability.plotting.bridge_count_maps

# --- Step 10: Monte Carlo sensitivity (threshold, then PCA) ---
run env BVI_ANALYSIS_TYPE=threshold poetry run python -m bridge_vulnerability.sensitivity.monte_carlo
run env BVI_ANALYSIS_TYPE=pca poetry run python -m bridge_vulnerability.sensitivity.monte_carlo

# --- Step 11: Validation benchmark ---
run poetry run python -m bridge_vulnerability.validation.benchmark_poor_bridges

echo ""
echo "Full pipeline completed successfully."
