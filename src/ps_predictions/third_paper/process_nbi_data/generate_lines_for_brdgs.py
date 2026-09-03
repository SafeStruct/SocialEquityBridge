# In this script, we generate the lines for the bridges from the NBI database,
# by finding the appropriate lines from OSM using bridge's coordinates.

import os
import numpy as np
import geopandas as gpd
from mpi4py import MPI
import time
import warnings
import argparse

from ps_predictions.second_paper.bridges_db.retrieve_osm_lines_for_brdgs import (
    find_OSM_lines_and_polygons,
)

with warnings.catch_warnings():
    # filter sklearn\externals\joblib\parallel.py:268:
    # DeprecationWarning: check_pickle is deprecated
    warnings.simplefilter("ignore", category=DeprecationWarning)
    import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def find_OSM_lines_and_polygons_parallel(nbi_gdf):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Split the DataFrame into chunks for each process
    chunks = np.array_split(nbi_gdf, size)

    # Each process works on its own chunk
    local_chunk = chunks[rank]

    # Process the local chunk
    local_lines, local_polygons = find_OSM_lines_and_polygons(
        local_chunk,
        dist_min=10,
        dist_max=40,
        dist_interval=5,
        primary_buffer_distance=0.00013,  # in degrees
        length_percentage=0.15,  # 15% of line length
    )

    # Gather the results from all processes
    all_lines = comm.gather(local_lines, root=0)
    all_polygons = comm.gather(local_polygons, root=0)

    if rank == 0:
        # Combine the results from all processes
        gdf_lines = gpd.GeoDataFrame(pd.concat(all_lines, ignore_index=True))
        gdf_polygons = gpd.GeoDataFrame(pd.concat(all_polygons, ignore_index=True))
        return gdf_lines, gdf_polygons
    else:
        return None, None


time_start = time.time()

# Define general folder
# folder_path = "/mnt/g/SOCIAL_PAPER"
folder_path = "/scratch/dmalinowska/SOCIAL_PAPER"

# Import NBI data
nbi_csv_path = os.path.join(
    folder_path, "California_brdgs/NBI", "nbi_bridges_geo_county.csv"
)
nbi_gdf = gpd.read_file(nbi_csv_path)
nbi_gdf.crs = "EPSG:4326"

# Set up argument parser
parser = argparse.ArgumentParser(description="Process bridges to get lines.")
parser.add_argument(
    "--min_range",
    type=int,
    required=True,
    help="Min value of the range",
)

# Parse arguments
args = parser.parse_args()
min_range = args.min_range
# min_range = 1024
max_range = min_range + 1024

# Check validity of min and max range
if min_range < 0:
    raise ValueError("Min range must be greater than 0")

elif min_range > len(nbi_gdf):
    raise ValueError("Min range must be less than the number of bridges")

elif max_range > len(nbi_gdf):
    max_range = len(nbi_gdf)

# Add columns Foot/Cycle, Road, Rail, Road should be equal to 1 and other two to 0
nbi_gdf["Foot/Cycle"] = 0
nbi_gdf["Road"] = 1
nbi_gdf["Rail"] = 0

# Create ID column from index
nbi_gdf["ID"] = nbi_gdf.index

# Rename STRUCTURE_LEN_MT_049 to Total Length and change type from string to float
nbi_gdf.rename(columns={"STRUCTURE_LEN_MT_049": "Total Length"}, inplace=True)
nbi_gdf["Total Length"] = nbi_gdf["Total Length"].astype(float)

nbi_gdf = nbi_gdf.iloc[min_range:max_range]

# # Find the OSM lines and polygons for the bridges
# gdf_lines, gdf_polygons = find_OSM_lines_and_polygons(nbi_gdf)


# # Print the number of processed bridges and check if all bridges have been processed
# print(len(gdf_lines), len(nbi_gdf))
# if len(gdf_lines) == len(nbi_gdf):
#     print("All bridges have been processed")
# else:
#     print("Some bridges have not been processed")

# Find the OSM lines and polygons for the bridges using parallel processing
gdf_lines, gdf_polygons = find_OSM_lines_and_polygons_parallel(nbi_gdf)


# Only the root process will print the results
if MPI.COMM_WORLD.Get_rank() == 0:
    # Print the number of processed bridges and check if all bridges have been processed
    print(len(gdf_lines), len(nbi_gdf))
    if len(gdf_lines) == len(nbi_gdf):
        print("All bridges have been processed")
    else:
        print("Some bridges have not been processed")

    print(nbi_gdf.columns)

    # Truncate column names to 10 characters and ensure uniqueness
    def make_unique_columns(columns):
        # First truncate all columns to 10 characters
        truncated = columns.str[:10]
        # Create a dictionary to track counts of each name
        name_counts = {}
        # Create new column names with counters for duplicates
        new_columns = []
        for col in truncated:
            if col in name_counts:
                name_counts[col] += 1
                new_columns.append(f"{col}_{name_counts[col]}")
            else:
                name_counts[col] = 0
                new_columns.append(col)
        return new_columns

    gdf_lines.columns = make_unique_columns(gdf_lines.columns)
    gdf_polygons.columns = make_unique_columns(gdf_polygons.columns)

    # Save to file
    gdf_lines.to_file(
        os.path.join(
            folder_path,
            "California_brdgs/NBI",
            f"nbi_lines_{min_range}_{max_range}.shp",
        )
    )
    gdf_polygons.to_file(
        os.path.join(
            folder_path,
            "California_brdgs/NBI",
            f"nbi_polygons_{min_range}_{max_range}.shp",
        )
    )

    time_end = time.time()
    print(f"Time elapsed: {time_end - time_start}")
    # print(nbi_gdf.columns)
