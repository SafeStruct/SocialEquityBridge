# This code access California txt file and read the data in them to create a pandas dataframe
# It uses pandas and dask if needed

import pandas as pd
import os
import geopandas as gpd

# import dask.dataframe as dd
# import numpy as np

if __name__ == "__main__":
    folder_path = "/mnt/g/SOCIAL_PAPER/California_brdgs/NBI/2024del"

    file = "CA24.txt"

    data = pd.read_csv(
        os.path.join(folder_path, file),
        sep=",",
        low_memory=False,
        on_bad_lines="warn",
    )
    print(data.head())
    print(data.shape)
    print(data.columns)

    # Save the data to a csv file

    data.to_csv("/mnt/g/SOCIAL_PAPER/California_brdgs/NBI/nbi_bridges.csv", index=False)

    print(f"Total number of bridges:{len(data)}")

    # Remove all tunnels and culverts
    data = data[
        (data["STRUCTURE_TYPE_043B"] != 18) & (data["STRUCTURE_TYPE_043B"] != 19)
    ]

    print(f"Total number of bridges after tunnels and culvert removed:{len(data)}")

    # Leave only the following columns
    # columns_to_keep = [
    #     "STRUCTURE_NUMBER_008",
    #     "LAT_016",
    #     "LONG_017",
    #     # exposure
    #     "DETOUR_KILOS_019",
    #     "ROUTE_PREFIX_005B",
    #     "ADT_029",
    #     "HISTORY_037",
    #     "PERCENT_ADT_TRUCK_109",
    #     "MIN_VERT_CLR_010",
    #     # sensitivity
    #     "YEAR_BUILT_027",
    #     "INVENTORY_RATING_066",
    #     "DATE_OF_INSPECT_090",
    #     "INSPECT_FREQ_MONTHS_091",
    #     "YEAR_RECONSTRUCTED_106",
    #     "LOWEST_RATING",
    #     "STRUCTURE_LEN_MT_049",
    #     "MAIN_UNIT_SPANS_045",
    #     "APPR_SPANS_046",
    #     "MAX_SPAN_LEN_MT_048",
    #     # adaptive capabilities
    #     "HIGHWAY_SYSTEM_104",
    #     "TOTAL_IMP_COST_096",
    #     "DECK_AREA",
    #     "COUNTY_CODE_003",
    #     # just for plotting/comparison
    #     "BRIDGE_CONDITION",
    # ]

    # # Leave only the following columns
    # columns_to_keep = [
    #     # Bridge identification
    #     "STRUCTURE_NUMBER_008",
    #     "LAT_016",
    #     "LONG_017",
    #     # Traffic load
    #     "ADT_029",
    #     "PERCENT_ADT_TRUCK_109",
    #     # Structural adequacy and safety
    #     "SUPERSTRUCTURE_COND_059",
    #     "SUBSTRUCTURE_COND_060",
    #     "INVENTORY_RATING_066",
    #     # Serviceability and functional obsolescence
    #     "TRAFFIC_LANES_ON_028A",
    #     "ADT_029",
    #     "APPR_WIDTH_MT_032",
    #     "ROADWAY_WIDTH_MT_051",
    #     "VERT_CLR_OVER_MT_053",
    #     "DECK_COND_058",
    #     "STRUCTURAL_EVAL_067",
    #     "DECK_GEOMETRY_EVAL_068",
    #     "UNDCLRENCE_EVAL_069",
    #     "WATERWAY_EVAL_071",
    #     "APPR_ROAD_EVAL_072",
    #     "STRAHNET_HIGHWAY_100",
    #     # Essentiality for public use (ADT and STRAHNET already included)
    #     "DETOUR_KILOS_019",
    #     # exposure,
    #     "ROUTE_PREFIX_005B",
    #     "HISTORY_037",
    #     # sensitivity
    #     "YEAR_BUILT_027",
    #     "DATE_OF_INSPECT_090",
    #     "INSPECT_FREQ_MONTHS_091",
    #     "YEAR_RECONSTRUCTED_106",
    #     "STRUCTURE_LEN_MT_049",
    #     "MAIN_UNIT_SPANS_045",
    #     "APPR_SPANS_046",
    #     "MAX_SPAN_LEN_MT_048",
    #     # adaptive capabilities
    #     "HIGHWAY_SYSTEM_104",
    #     "DECK_AREA",
    #     "COUNTY_CODE_003",
    # ]

    # Save the data to a shp, using LAT and LON columns to generate point geometries
    # data = data[columns_to_keep]

    # Print all rows in which LAT or LON are null
    print(data[data["LAT_016"].isnull() | data["LONG_017"].isnull()])

    data = data.dropna(subset=["LAT_016", "LONG_017"])

    # Latitude is encoded as XX deg XX min XXXX sec
    # Longitude is encoded as XXX deg XX min XXXX sec
    # We need to convert them to decimal degrees

    data["LAT_016"] = data["LAT_016"].astype(str)
    data["LONG_017"] = data["LONG_017"].astype(str)

    data["LAT_016"] = data["LAT_016"].apply(
        lambda x: float(x[:2]) + float(x[2:4]) / 60 + float(x[4:]) / 100 / (60 * 60)
    )

    data["LONG_017"] = data["LONG_017"].apply(
        lambda x: (float(x[:3]) + float(x[3:5]) / 60 + float(x[5:]) / 100 / (60 * 60))
        * -1
    )

    data = gpd.GeoDataFrame(
        data, geometry=gpd.points_from_xy(data.LONG_017, data.LAT_016)
    )
    data.crs = "EPSG:4326"
    data.to_file("/mnt/g/SOCIAL_PAPER/California_brdgs/NBI/nbi_bridges.shp")

    data = data.rename_geometry("WKT")
    data.to_csv(
        "/mnt/g/SOCIAL_PAPER/California_brdgs/NBI/nbi_bridges_geo.csv", index=False
    )
