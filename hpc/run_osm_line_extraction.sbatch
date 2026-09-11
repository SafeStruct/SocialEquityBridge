#!/bin/bash
#SBATCH --job-name="osm_extract"
#SBATCH --time=03:00:00
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --partition=YOUR_PARTITION
#SBATCH --mem-per-cpu=2GB
#SBATCH --account=YOUR_ACCOUNT

# Optional cluster module loads (Delft example; adapt or remove):
# module load 2024r1
# module load miniconda3
# module load openmpi/4.1.6
# module load py-mpi4py/3.1.4

unset CONDA_SHLVL
source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate /path/to/your/conda/env

# Point pipeline scripts at the cluster data directory
export BVI_DATA_ROOT=/path/to/data_root

# Process NBI rows in chunks. Adjust START/END to your inventory size
# (END should be >= number of bridges after step 1). CHUNK defaults to 1024.
START=0
END=23000
CHUNK=1024

for i in $(seq "${START}" "${CHUNK}" "${END}")
do
    srun python3 -m bridge_vulnerability.data_prep.osm_extract_mpi --min_range "$i" --chunk-size "${CHUNK}"
done

conda deactivate
