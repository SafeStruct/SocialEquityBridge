#!/bin/bash
#SBATCH --job-name="mpi_test"
#SBATCH --time=03:00:00
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --partition=compute-p1
#SBATCH --mem-per-cpu=2GB
#SBATCH --account=research-ceg-gse

# Load modules:
module load 2024r1
module load miniconda3
module load openmpi/4.1.6
module load py-mpi4py/3.1.4


# Set conda env:
unset CONDA_SHLVL
source "$(conda info --base)/etc/profile.d/conda.sh"


# Activate conda, run job, deactivate conda
conda activate /scratch/dmalinowska/.conda/envs/cpu_env_for_3rd_paper

# Point pipeline scripts at cluster data directory
export BVI_DATA_ROOT=/scratch/dmalinowska/SOCIAL_PAPER

# Run the python script in a loop, changing the range with each iteration, so that each iteration only
# processes 1024 bridges at a time
for i in {15360..23000..1024}
do
    srun python3 -m bridge_vulnerability.data_prep.osm_extract_mpi --min_range $i
done

conda deactivate