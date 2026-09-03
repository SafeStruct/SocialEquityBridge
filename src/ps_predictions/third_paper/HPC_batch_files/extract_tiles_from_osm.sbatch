#!/bin/bash
#SBATCH --job-name="osmium_extract_california"	
#SBATCH --partition=compute-p2
#SBATCH --time=01:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=20G
#SBATCH --account=research-ceg-gse



# Load modules:
module load 2024r1
module load miniconda3
module load openmpi

# Set conda env:
unset CONDA_SHLVL
source "$(conda info --base)/etc/profile.d/conda.sh"


# Define the continent name as a variable
CONTINENT="california"

# Define input and output directories based on the continent
INPUT_DIR="/scratch/dmalinowska/SOCIAL_PAPER/ml_model_data_california/json_files_${CONTINENT}"
OUTPUT_DIR="/scratch/dmalinowska/SOCIAL_PAPER"

continental_file="/scratch/dmalinowska/SOCIAL_PAPER/${CONTINENT}_filt.pbf"


# Iterate over all polygon JSON files in the input directory
for polygon_file in "${INPUT_DIR}"/polygons_"${CONTINENT}"_*.json; do

    conda activate /scratch/dmalinowska/.conda/envs/cpu_env_for_3rd_paper

    echo "Processing ${polygon_file} -> ${continental_file}"
    echo "osmium extract -c "${polygon_file}" "${continental_file}" --overwrite"
    
    # Run the osmium extract command with the current polygon file
    time /home/dmalinowska/.local/bin/osmium extract -c "${polygon_file}" "${continental_file}" --overwrite
    
    conda deactivate

done

