# California bridge vulnerability

Analysis code for the third paper (PCA/PFA-based Bridge Vulnerability Index for California).

## Pipeline

1. NBI: `process_nbi_data/read_nbi_data.py` then `match_county_code_with_name.py`
2. OSM bridge lines: HPC `HPC_batch_files/test_mpi_loop.sbatch`, then `process_nbi_data/process_birdge_lines.py`
3. Displacement / monitoring: `process_displacement_data/`, then `get_monit_displ_values_for_bridges.py`
4. Index and maps: `data_analysis_PCA_share_variables.py`, `plot_maps.py`, `plot_bridge_stats.py`
5. Sensitivity: `monte_carlo_sensitivity.py`
6. SR comparison: `process_nbi_data/sufficiency_rating.py`, `benchmark_agains_nbi.py`, `benchmark_against_poor_bridge.ipynb`

PS density maps for California were generated with the separate `PS_predictions` repository (`predict_PS_dens_for_region_osmnx.py`).

Scripts currently use absolute paths under `/mnt/e/SOCIAL_PAPER` or `/mnt/g/SOCIAL_PAPER`.
