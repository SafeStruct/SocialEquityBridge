"""
Functions to be used when calculating monitoring class for bridges.
"""

import pandas as pd
import numpy as np


def select_value(row, i, value, continents):
    """
    Select the maximum value from the row for a given value and index across all continents.

    Args:
        row (pd.Series): The row of the DataFrame.
        i (int): The index to be used in the column name.
        value (str): The value to be used in the column name.
        continents (list): The list of continents to be used in the column name.

    Returns:
        float: The maximum value found or NaN if no valid values are found.
    """
    # Extract values from the row for the given value and index across all continents
    values = [
        row[f"ps_{value}_{c}_{i}"]
        for c in continents
        if pd.notnull(row[f"ps_{value}_{c}_{i}"])
    ]

    # Return the maximum value if the list is not empty, otherwise return NaN
    return max(values) if values else np.nan


def assign_monitoring_class(bridges_gdf, snt_status="", nb_sections=5):
    """
    Assign monitoring class per segment (not corrected by Sentinel availability).

    Arguments:
        bridges_gdf (gpd.GeoDataFrame): The GeoDataFrame with the data.
        snt_status (str): The status of the Sentinel data (either "" or "_pref").
        nb_sections (int): The number of sections to be used.

    Returns:
        gpd.GeoDataFrame: The GeoDataFrame with the monitoring class assigned.
    """

    for i in range(1, nb_sections + 1):

        # Both Sentinel flight directions available
        # <= 20%
        condition = (bridges_gdf[f"ps_avail_perc_{i}"] < 0.2) & (
            bridges_gdf[f"ps_count_100m_{i}"] < 10
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.2

        condition = (bridges_gdf[f"ps_avail_perc_{i}"] < 0.2) & (
            bridges_gdf[f"ps_count_100m_{i}"] >= 10
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.4

        # 20-40%
        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.2)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.4)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 3)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.2

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.2)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.4)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 3)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.4

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.2)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.4)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.6

        # 40-60%
        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.4)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.6)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 1)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.2

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.4)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.6)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 1)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 5)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.4

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.4)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.6)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 5)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.6

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.4)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.6)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.8

        # 60-80%
        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.6)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 1)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.2

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.6)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 1)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 3)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.4

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.6)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 3)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 5)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.6

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.6)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 5)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.8

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.6)
            & (bridges_gdf[f"ps_avail_perc_{i}"] < 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 10)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 1

        # >=80%
        condition = (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.8) & (
            bridges_gdf[f"ps_count_100m_{i}"] < 1
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.4

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 1)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 3)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.6

        condition = (
            (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.8)
            & (bridges_gdf[f"ps_count_100m_{i}"] >= 3)
            & (bridges_gdf[f"ps_count_100m_{i}"] < 5)
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 0.8

        # condition = (
        #     (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.8)
        #     & (bridges_gdf[f"ps_count_100m_{i}"] >= 5)
        #     & (bridges_gdf[f"ps_count_100m_{i}"] < 10)
        # )
        # bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 1

        condition = (bridges_gdf[f"ps_avail_perc_{i}"] >= 0.8) & (
            bridges_gdf[f"ps_count_100m_{i}"] >= 5
        )
        bridges_gdf.loc[condition, f"Monitoring_{i}{snt_status}"] = 1

        # If both Sentinel flight directions available every 6 days leave the values as they are
        # Save those to a new column to avoid overwriting the original values as it's needed
        # for some plots. These will be independent of the SNT availability.
        bridges_gdf[f"Monitoring_{i}_PS_availability_only"] = bridges_gdf[
            f"Monitoring_{i}{snt_status}"
        ]

    return bridges_gdf


def monitoring_class_stats(bridges_gdf, snt_status, max_monitoring_coefficient):
    """
    Calculate the statistics for monitoring class for bridges
    based on Sentinel availability.

    Arguments:
        bridges_gdf (gpd.GeoDataFrame): The GeoDataFrame with the data.
        snt_status (str): The status of the Sentinel data (either "" or "_pref").
        max_monitoring_coefficient (float): Max value of the coefficient for scaling

    Returns:
        gpd.GeoDataFrame: The GeoDataFrame with the monitoring class assigned.
    """
    # Calculate the mean of the monitoring classes
    bridges_gdf[f"Monitoring_mean{snt_status}"] = bridges_gdf[
        [
            f"Monitoring_1{snt_status}",
            f"Monitoring_2{snt_status}",
            f"Monitoring_3{snt_status}",
            f"Monitoring_4{snt_status}",
            f"Monitoring_5{snt_status}",
        ]
    ].mean(axis=1)

    # Calculate the minimum of the monitoring classes
    bridges_gdf[f"Monitoring_min{snt_status}"] = bridges_gdf[
        [
            f"Monitoring_1{snt_status}",
            f"Monitoring_2{snt_status}",
            f"Monitoring_3{snt_status}",
            f"Monitoring_4{snt_status}",
            f"Monitoring_5{snt_status}",
        ]
    ].min(axis=1)

    # Assign final monitoring class
    weights = [0.1, 0.25, 0.3, 0.25, 0.1]
    columns = [
        f"Monitoring_1{snt_status}",
        f"Monitoring_2{snt_status}",
        f"Monitoring_3{snt_status}",
        f"Monitoring_4{snt_status}",
        f"Monitoring_5{snt_status}",
    ]

    bridges_gdf[f"Monitoring{snt_status}"] = (
        bridges_gdf[columns].multiply(weights, axis=1).sum(axis=1)
    )

    columns = [
        "Monitoring_1_PS_availability_only",
        "Monitoring_2_PS_availability_only",
        "Monitoring_3_PS_availability_only",
        "Monitoring_4_PS_availability_only",
        "Monitoring_5_PS_availability_only",
    ]

    bridges_gdf["Monitoring_PS_availability_only"] = (
        bridges_gdf[columns].multiply(weights, axis=1).sum(axis=1)
    )

    # If both Sentinel flight directions available every 12 days, correct by -.1
    bridges_gdf.loc[
        bridges_gdf[f"SNT_availability{snt_status}"] == 4,
        f"Monitoring{snt_status}",
    ] = (
        bridges_gdf.loc[
            bridges_gdf[f"SNT_availability{snt_status}"] == 4,
            f"Monitoring{snt_status}",
        ]
        - 0.1
    )

    # If only one Sentinel flight direction available every 6 days, correct by -.2
    bridges_gdf.loc[
        bridges_gdf[f"SNT_availability{snt_status}"] == 1,
        f"Monitoring{snt_status}",
    ] = (
        bridges_gdf.loc[
            bridges_gdf[f"SNT_availability{snt_status}"] == 1,
            f"Monitoring{snt_status}",
        ]
        - 0.2
    )

    # If only one Sentinel flight direction available every 12 days, correct by -.3
    bridges_gdf.loc[
        bridges_gdf[f"SNT_availability{snt_status}"] == 3,
        f"Monitoring{snt_status}",
    ] = (
        bridges_gdf.loc[
            bridges_gdf[f"SNT_availability{snt_status}"] == 3,
            f"Monitoring{snt_status}",
        ]
        - 0.3
    )

    # Sentinel not available
    bridges_gdf.loc[
        bridges_gdf[f"SNT_availability{snt_status}"] == 0,
        f"Monitoring{snt_status}",
    ] = 0

    # Convert any negative values to 0
    bridges_gdf[f"Monitoring{snt_status}"] = bridges_gdf[
        f"Monitoring{snt_status}"
    ].clip(lower=0)

    # # Scale 'Monitoring_class' values from [0, 1] to [1, 0.75]
    # bridges_gdf[f"Monitoring_scaled{snt_status}"] = 1 - (
    #     bridges_gdf[f"Monitoring_class{snt_status}"] * 0.25
    # )

    # Scale 'Monitoring' values from [0, 1] to [1, 1.35]
    bridges_gdf[f"Monitoring_scaled{snt_status}"] = 1 + (
        (1 - bridges_gdf[f"Monitoring{snt_status}"])
        * (max_monitoring_coefficient - 1.0)
    )
    return bridges_gdf


def calculate_geometric_mean(row, columns):
    """
    Calculate the geometric mean for specified columns in a row.

    Arguments:
        row (pd.Series): The row of the DataFrame.
        columns (list): The list of columns to be used in the calculation.

    Returns:
        float: The geometric mean for the specified columns in the row.
    """
    # Extract the values from the specified columns
    x = row[columns].values

    # Invert so that higher values are better
    x_inv = 1 - x

    # Rescale to [1, 10] - rescaling helps with numerical stability
    # and avoids division by zero
    # Rescaling done with linear transformation (https://en.wikipedia.org/wiki/Linear_interpolation)
    x_rescaled = 9 * x_inv + 1

    # Calculate the geometric mean
    geo_mean = x_rescaled.prod() ** (1.0 / len(x_rescaled))

    # Rescale back to [0, 1]
    geo_mean_rescaled = (geo_mean - 1) / 9

    # Invert back so that higher are worse
    geo_mean_final = 1 - geo_mean_rescaled

    return geo_mean_final


def determine_snt_availability(row, snt_status=""):
    """
    This function determines the availability of Sentinel data for a bridge
    based on the time between asc and dsc acquistions.

    Arguments:
        row (pd.Series): The row of the DataFrame.
        snt_status (str): The status of the Sentinel data (either "" or "_pref").

    Returns:
        int: The availability of Sentinel data for the bridge.
    """
    asc = row[f"asc{snt_status}_time"]
    dsc = row[f"dsc{snt_status}_time"]

    if (np.isnan(asc) and dsc == 6) or (asc == 6 and np.isnan(dsc)):
        return 1
    elif asc == 6 and dsc == 6:
        return 2
    elif (np.isnan(asc) and dsc == 12) or (asc == 12 and np.isnan(dsc)):
        return 3
    elif asc == 12 and dsc == 12:
        return 4
    elif (asc == 12 and dsc == 6) or (asc == 6 and dsc == 12):
        return 4
    elif np.isnan(asc) and np.isnan(dsc):
        return 0
    else:
        return None  # or some default value if needed


def calculate_risk(bridges_gdf, risk_type, risk_col, exposure_col, vulnerability_col):
    """
    Helper function to calculate risk and add it to the DataFrame.

    Arguments:
        bridges_gdf (pd.DataFrame): The DataFrame containing bridge data.
        risk_type (str): The type of risk (e.g., "Landslide", "Subsidence", "Multi-hazard").
        vulnerability_col (str): The column name for the vulnerability data.
    """
    bridges_gdf[f"{risk_type}_risk_{vulnerability_col[-3:]}"] = bridges_gdf.apply(
        lambda row: calculate_geometric_mean(
            row, [risk_col, exposure_col, vulnerability_col]
        ),
        axis=1,
    )
