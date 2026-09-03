# This code converts all displacement csvs found in a folder into shp files

# import pandas as pd
import os

# import geopandas as gpd

import dask.dataframe as dd
import dask_geopandas as dgpd

# import dask.dataframe as dd
# import numpy as np

if __name__ == "__main__":
    folder_path = (
        "/mnt/g/SOCIAL_PAPER/California_subsidence/verticaldisplacementpointdata"
    )
    file = "CALIFORNIA_DWR_VERT_01.csv"
    # Read a csv file and save as shp
    # data = pd.read_csv(
    #     os.path.join(folder_path, file),
    #     low_memory=True,
    #     on_bad_lines="warn",
    #     nrows=100,
    #     usecols=["OID_", "CODE", "LAT", "LON", "HEIGHT", "VEL_V"],
    # )

    data = dd.read_csv(
        os.path.join(folder_path, file),
        # usecols=["OID_", "CODE", "LAT", "LON", "HEIGHT", "VEL_V", "D20240701"],
        # usecols=["LAT", "LON", "D20240701"],
        assume_missing=True,  # Assume missing values for better performance
    )

    # Drop if nan in D20240701
    # data = data.dropna(subset=["D20240701"])

    # data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.LON, data.LAT))
    # data.crs = "EPSG:4326"

    # Convert the Dask DataFrame to a Dask GeoDataFrame
    data = dgpd.from_dask_dataframe(
        data, geometry=dgpd.points_from_xy(data, "LON", "LAT")
    )

    # Set the coordinate reference system (CRS)
    data = data.set_crs("EPSG:4326")

    # Convert the Dask GeoDataFrame to a GeoPandas GeoDataFrame
    data = data.compute()

    data.to_file(os.path.join(folder_path, file[:-3] + "shp"))
