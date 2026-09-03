"""
This module contains functions to find OSM lines for bridges
and converts them into polygons.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import Polygon, MultiLineString, LineString, Point
from shapely.ops import linemerge, unary_union
import osmnx as ox
import utm
from pyproj import CRS


def utm_crs_from_latlon(lat, lon):
    """
    This function determines the appropriate UTM (Universal Transverse Mercator) CRS (Coordinate Reference System)
    for a given latitude and longitude. This is useful for accurate length calculations in spatial analysis.

    The function uses the `utm` library's `latlon_to_zone_number` function to determine the correct UTM zone.
    If the latitude is less than 0, the location is in the southern hemisphere, so the 'south' parameter is set to True.

    Parameters:
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.

    Returns:
        CRS: The appropriate UTM CRS for the location.

    Source: https://gis.stackexchange.com/questions/436938/calculate-length-using-geopandas
    """

    # Define the parameters for the UTM CRS
    crs_params = dict(
        proj="utm",  # The projection is UTM
        zone=utm.latlon_to_zone_number(
            lat, lon
        ),  # The UTM zone is determined based on the latitude and longitude
        south=lat
        < 0,  # If the latitude is less than 0, the location is in the southern hemisphere
    )

    # Return the UTM CRS created from the parameters
    return CRS.from_dict(crs_params)


def get_features(center_point, tags, dist):
    """
    This function retrieves all features within a certain distance of a given point.

    Parameters:
        center_point (tuple): The coordinates of the center point as a tuple (latitude, longitude).
        tags (dict): The tags of the features to retrieve.
        dist (float): The distance around the center point within which to retrieve features.

    Returns:
        GeoDataFrame: A GeoDataFrame containing the features within the specified distance of the center point.
    """
    try:
        # Use the OSMnx library's features_from_point function to retrieve the features
        return ox.features.features_from_point(
            (center_point[1], center_point[0]), tags, dist=dist
        )
    except Exception:
        # No features found within the specified distance
        # print(f"During the search for features, the following error occurred: {e}")
        # print(f"No features found within {dist} meters of the center point.")
        return None


def check_for_roads(center_point, tags_roads, dist):
    """
    This function checks for roads within a certain distance of a given point and prints a message if any are found.

    Parameters:
        center_point (tuple): The coordinates of the center point as a tuple (latitude, longitude).
        tags_roads (dict): The tags of the roads to check for.
        dist (float): The distance around the center point within which to check for roads.

    Returns:
        GeoDataFrame or None: A GeoDataFrame containing the roads within the specified distance of the center point,
        or None if no roads are found.
    """
    # Use the get_features function to retrieve the roads
    gdf_OSM_all = get_features(center_point, tags_roads, dist)

    # Check if any roads were found
    # if len(gdf_OSM_all) != 0:
    if gdf_OSM_all is not None:
        return gdf_OSM_all

    # If no roads were found, return None
    return None


def max_length_of_polygon(polygon):
    """
    This function calculates the maximum length of a polygon, defined as the maximum distance between any two points.
    The function uses the minimum rotated rectangle (MBR) that encloses the polygon to calculate this length.
    The length of the diagonal of the MBR is used as an approximation of the maximum length of the polygon.

    Parameters:
        polygon (Polygon): The polygon to measure.

    Returns:
        float or None: The maximum length of the polygon, or None if the input is not a Polygon.
    """

    # Check if the input is a Polygon
    if isinstance(polygon, Polygon):
        # Get the minimum rotated rectangle (MBR) that encloses the polygon
        mbr = polygon.minimum_rotated_rectangle

        # Extract the x and y coordinates of the MBR's exterior
        x, y = mbr.exterior.coords.xy

        # Calculate the length of the diagonal of the MBR
        # This is done using the Pythagorean theorem: sqrt((x2-x1)^2 + (y2-y1)^2)
        max_length = ((x[2] - x[0]) ** 2 + (y[2] - y[0]) ** 2) ** 0.5

        # Return the calculated length
        return max_length

    # If the input is not a Polygon, return None
    return None


def return_length_of_polygon(gdf_OSM_bridge, utm_crs):
    """
    This function takes all elements from the GeoDataFrame, converts them to a polygon and measures its length.

    Parameters:
        gdf_OSM_bridge (GeoDataFrame): The GeoDataFrame containing the bridge data.
        utm_crs (CRS): The Coordinate Reference System to use for the calculations.

    Returns:
        float: The maximum length of the polygon, or 0 if the GeoDataFrame is empty.
    """

    # Check if the GeoDataFrame is not empty
    if len(gdf_OSM_bridge) != 0:
        # Create a copy of the GeoDataFrame
        gdf_OSM_bridge_temp = gdf_OSM_bridge.copy()

        # Convert any Polygon geometries in the GeoDataFrame to LineString
        gdf_OSM_bridge_temp["geometry"] = gdf_OSM_bridge_temp["geometry"].apply(
            lambda x: x.boundary if x.geom_type == "Polygon" else x
        )

        # Convert all LineString geometries in the GeoDataFrame to a MultiLineString
        multi_line = MultiLineString(
            gdf_OSM_bridge_temp[
                gdf_OSM_bridge_temp["geometry"].geom_type == "LineString"
            ].geometry.tolist()
        )
        del gdf_OSM_bridge_temp

        # Get the convex hull of the MultiLineString
        convex_hull_polygon = multi_line.convex_hull

        # If the convex hull is a LineString, buffer it by a small amount to make it a Polygon
        if isinstance(multi_line.convex_hull, LineString):
            buffer_distance = 0.0000001  # Adjust this value as needed
            convex_hull_polygon = convex_hull_polygon.buffer(buffer_distance)

        # Convert the polygon to a GeoDataFrame and set the CRS
        convex_hull_series = GeoSeries([convex_hull_polygon])
        convex_hull_gdf = gpd.GeoDataFrame(convex_hull_series, columns=["geometry"])
        convex_hull_gdf.set_crs(utm_crs, inplace=True)

        # Measure the length of the polygon as the maximum distance between any two points
        convex_hull_gdf["max_length"] = convex_hull_gdf.geometry.apply(
            max_length_of_polygon
        )

        # Return the maximum length
        return convex_hull_gdf["max_length"].max()

    # If the GeoDataFrame is empty, return 0
    else:
        return 0


def check_bridge_length(
    gdf_OSM_bridge,
    bridge,
    dist,
    center_point,
    utm_crs,
    dist_min=100,
):
    """
    Process the bridge data by converting the CRS, adding a length column,
    filtering out too long and too small bridges, and checking the length difference.

    Parameters:
        gdf_OSM_bridge (GeoDataFrame): The GeoDataFrame containing the bridge data.
        bridge (dict): The bridge data.
        dist (float): The distance around the center point within which to check for bridges.
        center_point (tuple): The coordinates of the center point as a tuple (latitude, longitude).
        utm_crs (CRS): The UTM CRS to use for the calculations.
        dist_min (int): The minimum distance to check for bridges (default: 100).
    Returns:
        tuple: A tuple containing the processed GeoDataFrame and the percentage difference in length.
    """

    # Add a new column 'length' to gdf_OSM_bridge
    gdf_OSM_bridge["length"] = gdf_OSM_bridge["geometry"].length

    # Drop all the rows where the 'length' is more than 3 times length of the bridge
    # (to filter out anything that is incorrectly long)
    gdf_OSM_bridge = gdf_OSM_bridge[
        gdf_OSM_bridge["length"] < (3 * bridge["Total Length"])
    ]

    # Drop all the rows where the 'length' is less than 25% of bridge length
    # (to filter out small bridges incorrectly included)
    if dist == dist_min:
        gdf_OSM_bridge = gdf_OSM_bridge
    # elif dist==200:
    #     # if dist is 200, then drop all the rows where the 'length' is less than 10% of bridge length
    #     min_length = .1*bridge["Total Length"]
    #     gdf_OSM_bridge = gdf_OSM_bridge[gdf_OSM_bridge['length'] > min_length]
    else:
        # if dist is more than 100, then drop all the rows where the 'length' is less than 10% of bridge length
        min_length = 0.1 * bridge["Total Length"]
        gdf_OSM_bridge = gdf_OSM_bridge[gdf_OSM_bridge["length"] > min_length]

        # Add all bridges from within 100 m (assumption: anything with tag bridge within 100 m
        # is correct, even if it is small)
        try:
            gdf_OSM_bridge_100 = get_features(center_point, {"bridge": True}, dist_min)
            # Filter out only the bridges that are motorway, trunk, primary, secondary (so that no links are included)
            if gdf_OSM_bridge_100 is not None:
                gdf_OSM_bridge_100 = gdf_OSM_bridge_100[
                    gdf_OSM_bridge_100["highway"].isin(
                        ["motorway", "trunk", "primary", "secondary"]
                    )
                ]
                gdf_OSM_bridge_100 = gdf_OSM_bridge_100.to_crs(utm_crs)

                # # To avoid the error of concatenating two empty GeoDataFrames, check if the GeoDataFrame is empty
                # # Drop columns in gdf_OSM_bridge where all values are NA
                # gdf_OSM_bridge = gdf_OSM_bridge.dropna(axis=1, how='all')
                # # Drop columns in gdf_OSM_bridge_100 where all values are NA
                # gdf_OSM_bridge_100 = gdf_OSM_bridge_100.dropna(axis=1, how='all')

                # gdf_OSM_bridge = pd.concat([gdf_OSM_bridge, gdf_OSM_bridge_100])

                df_list = [gdf_OSM_bridge, gdf_OSM_bridge_100]
                gdf_OSM_bridge = pd.concat([df for df in df_list if not df.empty])

        except Exception:
            # Uncomment the following line to print a message if an error occurs
            # print(f"Error at distance 100 meters: {e}")
            pass

    # Check if length of the lines is similar to the recorded length of the bridge
    OSM_elements_length = return_length_of_polygon(gdf_OSM_bridge, utm_crs)
    length_difference = OSM_elements_length - bridge["Total Length"]
    length_percent = (length_difference / bridge["Total Length"]) * 100

    # Return the processed GeoDataFrame and the percentage difference in length
    return gdf_OSM_bridge, length_percent


def get_longest_side(polygon):
    """
    This function takes a polygon and returns the longest side of the polygon as a LineString.

    Arguments:
        polygon (Polygon): The input polygon.

    Returns:
        LineString: The longest side of the polygon.
    """
    # Get the coordinates of the polygon's exterior
    coords = list(polygon.exterior.coords)

    # Create a LineString for each pair of consecutive points
    lines = [LineString([coords[i], coords[i + 1]]) for i in range(len(coords) - 1)]

    # Find the longest LineString
    longest_side = max(lines, key=lambda line: line.length)

    # x,y = polygon.minimum_rotated_rectangle.exterior.coords.xy
    # # get length of bounding box edges and get width of polygon as the shortest edge of the bounding box
    # longest_side = max(Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

    return longest_side


def calculate_angle(line1, line2):
    """
    This function calculates the angle between two lines.

    Arguments:
        line1 (LineString): The first line.
        line2 (LineString): The second line.

    Returns:
        float: The angle between the two lines in degrees.
    """
    # If line is a mulitpolygon, conver it to polygon but only considering the first one
    if line1.geom_type == "MultiPolygon":
        line1 = line1.geoms[0]
    if line2.geom_type == "MultiPolygon":
        line2 = line2.geoms[0]

    # If any of the lines is a polygon, convert it to a linestring
    if line1.geom_type == "Polygon":
        line1 = get_longest_side(line1)
    if line2.geom_type == "Polygon":
        line2 = get_longest_side(line2)

    # Calculate the direction of the lines
    direction1 = np.array(line1.coords[-1]) - np.array(line1.coords[0])
    direction2 = np.array(line2.coords[-1]) - np.array(line2.coords[0])

    # Normalize the directions
    norm1 = np.linalg.norm(direction1)
    norm2 = np.linalg.norm(direction2)
    # print(norm1, norm2)
    if norm1 != 0:
        direction1 /= norm1
    else:
        # print("Warning: division by zero encountered. Setting direction1 to zero.")
        direction1 = np.zeros_like(direction1)

    if norm2 != 0:
        direction2 /= norm2
    else:
        # print("Warning: division by zero encountered. Setting direction2 to zero.")
        direction2 = np.zeros_like(direction2)

    # Calculate the angle between the lines
    angle = np.arccos(np.clip(np.dot(direction1, direction2), -1.0, 1.0))

    # Convert the angle to degrees
    angle = np.degrees(angle)

    return angle


def calculate_width(initial_line, line2, buffer_distance):
    """
    This function calculates the width between two lines.

    Arguments:
        initial_line (LineString): The initial line.
        line2 (LineString): The second line.
        buffer_distance (float): The buffer distance to use for the width calculation.

    Returns:
        float: The width between the two lines.
    """
    # Make unirary union of the geometry of the row and the initial_line_polygon
    try:
        combined_lines = linemerge(unary_union([line2, initial_line]))
    except Exception:
        combined_lines = unary_union([line2, initial_line])

    polygon = combined_lines.buffer(buffer_distance, cap_style="flat")

    # Get a width of the updated polygon
    x, y = polygon.minimum_rotated_rectangle.exterior.coords.xy
    # get length of bounding box edges and get width of polygon as the shortest edge of the bounding box
    width = min(
        Point(x[0], y[0]).distance(Point(x[1], y[1])),
        Point(x[1], y[1]).distance(Point(x[2], y[2])),
    )

    return width


def filter_parallel_lines(gdf_OSM_bridge, initial_line, filter_buffer_distance=0.00045):
    """
    This function filters out lines that are not parallel to the initial line.

    Arguments:
        gdf_OSM_bridge (GeoDataFrame): The GeoDataFrame containing the bridge data.
        initial_line (LineString): The initial line to which the other lines should be parallel.
        filter_buffer_distance (float): Buffer distance used for filtering parallel lines (default: 0.00045).

    Returns:
        GeoDataFrame: The filtered GeoDataFrame containing only lines that are parallel to the initial line.
    """
    # Handle the case where the GeoDataFrame is empty
    if gdf_OSM_bridge is None:
        return gdf_OSM_bridge, initial_line

    if gdf_OSM_bridge.empty:
        return gdf_OSM_bridge, initial_line
    # Remove lines that are not parallel to the initial line
    else:
        # gdf_OSM_bridge = gdf_OSM_bridge.to_crs(utm_crs)
        # print(gdf_OSM_bridge['geometry'], initial_line)

        # Calculate the angle between the initial line and the current line
        gdf_OSM_bridge = gdf_OSM_bridge.copy()
        gdf_OSM_bridge.loc[:, "angle"] = gdf_OSM_bridge["geometry"].apply(
            lambda row: calculate_angle(initial_line, row)
        )
        # print(gdf_OSM_bridge['angle'])

        # Drop those rows that have an angle between 60 and 120 degrees (approx perpendicular)
        gdf_OSM_bridge = gdf_OSM_bridge[
            (gdf_OSM_bridge["angle"] < 60) | (gdf_OSM_bridge["angle"] > 120)
        ]
        gdf_OSM_bridge = gdf_OSM_bridge.drop(columns=["angle"])

        # Create a polygon from the initial line by buffering
        initial_line_polygon = initial_line.buffer(filter_buffer_distance, cap_style="flat")

        # Get a width of the initial_line_polygon
        # Source: https://gis.stackexchange.com/questions/295874/getting-polygon-breadth-in-shapely
        x, y = initial_line_polygon.minimum_rotated_rectangle.exterior.coords.xy
        # get length of bounding box edges and get width of polygon as the shortest edge of the bounding box
        width_init_line = min(
            Point(x[0], y[0]).distance(Point(x[1], y[1])),
            Point(x[1], y[1]).distance(Point(x[2], y[2])),
        )

        # print(width_init_line)
        if len(gdf_OSM_bridge) != 0:
            # Calculate the width between the initial line and the current line
            gdf_OSM_bridge = gdf_OSM_bridge.copy()
            gdf_OSM_bridge.loc[:, "width"] = gdf_OSM_bridge["geometry"].apply(
                lambda row: calculate_width(initial_line, row, filter_buffer_distance)
            )
            # print(gdf_OSM_bridge['width'])

            # for index, row in gdf_OSM_bridge.iterrows():
            #     # Make unirary union of the geometry of the row and the initial_line_polygon
            #     # union = row['geometry'].union(initial_line)
            #     combined_lines = linemerge(unary_union([row['geometry'],initial_line]))

            #     polygon = combined_lines.buffer(buffer_distance, cap_style= 'flat')

            #     # Get a width of the updated polygon
            #     x,y = polygon.minimum_rotated_rectangle.exterior.coords.xy
            #     # get length of bounding box edges and get width of polygon as the shortest edge of the bounding box
            #     width = min(Point(x[0], y[0]).distance(Point(x[1], y[1])),
            # Point(x[1], y[1]).distance(Point(x[2], y[2])))

            #     print(width)

            #     gdf_OSM_bridge.at[index, 'width'] = width

            # Drop those rows that have an angle between 60 and 120 degrees (approx perpendicular)
            max_width = max(width_init_line * 1.2, 200)
            gdf_OSM_bridge = gdf_OSM_bridge[gdf_OSM_bridge["width"] < max_width]
            gdf_OSM_bridge = gdf_OSM_bridge.drop(columns=["width"])

        return gdf_OSM_bridge, initial_line


def get_bridge_lines(
    gdf_lsb,
    dist_min=100,
    dist_max=2000,
    dist_interval=100,
    filter_buffer_distance=0.00045,
):
    """
    This function retrieves the OSM lines for the bridges in the LSB database.

    Arguments:
        gdf_lsb (GeoDataFrame): The GeoDataFrame containing the LSB database.
        dist_min (int): The minimum distance to check for bridges (default: 100).
        dist_max (int): The maximum distance to check for bridges (default: 2000).
        dist_interval (int): The interval between distance checks (default: 100).
        filter_buffer_distance (float): Buffer distance used for filtering parallel lines (default: 0.00045).

    Returns:
        gdf_lsb (GeoDataFrame): The GeoDataFrame with the OSM lines for the bridges added.
    """
    # Iterate over the bridges
    for index, bridge in gdf_lsb.iterrows():
        # str_id = bridge["STRUCTURE_NUMBER_008"]

        # print(
        #     f"Currently processed bridge with index {index} and number {str_id}",
        #     flush=True,
        # )

        # Initialise/define the tags to look for in the OSM data
        tags = {}
        tags_roads = {}
        tags_bridge = {"bridge": True}

        # Assign tags based on information about bridge typology from the db
        # Tags for highways
        if bridge["Foot/Cycle"] == 1 and bridge["Road"] == 1:
            tags["highway"] = [
                "footway",
                "pedestrian",
                "motorway",
                "trunk",
                "primary",
                "secondary",
            ]
            tags_roads["highway"] = [
                "footway",
                "pedestrian",
                "motorway",
                "trunk",
                "primary",
            ]
        elif bridge["Foot/Cycle"] == 1 and bridge["Road"] == 0:
            tags["highway"] = ["footway", "pedestrian"]
            tags_roads["highway"] = ["footway", "pedestrian"]
        elif bridge["Foot/Cycle"] == 0 and bridge["Road"] == 1:
            tags["highway"] = ["motorway", "trunk", "primary", "secondary"]
            tags_roads["highway"] = ["motorway", "trunk", "primary"]

        # Tags for railways
        if bridge["Rail"] == 1:
            tags["railway"] = ["rail", "subway"]
            tags_roads["railway"] = "rail"

        # If typology not assigned in the db, then use the following tags
        if bridge["Road"] == 0 and bridge["Foot/Cycle"] == 0 and bridge["Rail"] == 0:
            tags = {
                "highway": ["motorway", "trunk", "primary", "secondary"],
                "railway": "rail",
            }
            tags_roads = {
                "highway": ["motorway", "trunk", "primary", "secondary"],
                "railway": "rail",
            }

        # Retrieve the bridge ID and its center point
        brdg_id = bridge["ID"]
        center_point = tuple(bridge.geometry.coords)[0]

        # Determine the appropriate UTM CRS for the bridge
        utm_crs = utm_crs_from_latlon(lat=center_point[1], lon=center_point[0])

        # Initialize variables for length comparison
        length_percent_prev_dist = 100000000000000
        length_percent = 100000000000000

        # Initialize variable for storing the intial line
        initial_line = None

        # Initialize variable for storing the GeoDataFrame for the bridge
        gdf_OSM_bridge = None
        # print("bridge_lines", dist_min, dist_max, dist_interval)

        # Iterate over distances in increments of 100m, starting from 100m to 2000m
        # Look for lines within each distance range until appropriate lines are found,
        # or the maximum distance is reached
        for dist in range(dist_min, dist_max, dist_interval):
            # Store the previous distance's length percentage for comparison in the next iteration
            length_percent_prev_dist = length_percent
            try:
                # Try to create a copy of the current GeoDataFrame for the bridge
                # This is done to have a backup of the current state of the GeoDataFrame
                # in case the next iteration fails to find a better solution
                gdf_OSM_bridge_prev_dist = gdf_OSM_bridge.copy()
            except Exception:
                # If no lines found in previous iteration or it is the first iteration,
                # the gdf_OSM_bridge is empty, so the copy operation fails
                # ignore the error and move to the next line of code
                pass

            try:
                # If distance is less than 200m, look for bridge polygons
                if dist < (2 * dist_min):
                    # Look for all entries with bridge tag
                    gdf_OSM_bridge = get_features(center_point, tags_bridge, dist)

                    # If bridges are found, assummed these are the correct lines and move to the next one
                    if gdf_OSM_bridge is not None:
                        gdf_OSM_bridge = gdf_OSM_bridge.to_crs(utm_crs)

                        # Remove lines that have word "link" in the column highway
                        # As they are usually not relevant and only mess up the results
                        if "highway" in gdf_OSM_bridge.columns:
                            gdf_OSM_bridge = gdf_OSM_bridge[
                                ~gdf_OSM_bridge["highway"].str.contains(
                                    "link", na=False
                                )
                            ]

                        # Save a backup of the current GeoDataFrame
                        # in case further processing dosen't find a better solution
                        gdf_OSM_bridge_100_backup = gdf_OSM_bridge.copy()

                        # Check length of the lines
                        gdf_OSM_bridge, length_percent = check_bridge_length(
                            gdf_OSM_bridge,
                            bridge,
                            dist,
                            center_point,
                            utm_crs,
                            dist_min,
                        )
                        # print(brdg_id, length_percent)

                        # If the length difference is less than 15%, stop the search
                        if abs(length_percent) < 15:
                            break
                        # If the length difference is big, continue,
                        else:
                            continue

                # If distance 200 or more, look for road and railway lines
                else:
                    # Find all features within the specified distance of the center point
                    gdf_OSM_bridge = get_features(center_point, tags, dist)
                    # gdf_OSM_bridge = gdf_OSM_all[gdf_OSM_all['bridge'].notna()]

                if gdf_OSM_bridge is not None:
                    gdf_OSM_bridge = gdf_OSM_bridge.to_crs(utm_crs)
                    # Convert all polygons in gdf into lines by taking the longest side of the polygon as the line
                    # Create a boolean mask for rows where the geometry is a Polygon
                    mask = gdf_OSM_bridge["geometry"].apply(
                        lambda geom: isinstance(geom, Polygon)
                    )
                    # Apply the function to only those rows
                    gdf_OSM_bridge.loc[mask, "geometry"] = gdf_OSM_bridge.loc[
                        mask, "geometry"
                    ].apply(get_longest_side)

                    # Once a geometry is found, store the longest as the initial line
                    if initial_line is None:
                        # Get the longest line by comparing lengths directly
                        lengths = gdf_OSM_bridge.geometry.apply(lambda x: x.length)
                        initial_line = gdf_OSM_bridge.geometry[lengths.idxmax()]

                    # Remove all lines that are not parallel to the main one
                    if initial_line is not None:
                        gdf_OSM_bridge, initial_line = filter_parallel_lines(
                            gdf_OSM_bridge, initial_line, filter_buffer_distance
                        )

                    # Check length of the lines
                    gdf_OSM_bridge, length_percent = check_bridge_length(
                        gdf_OSM_bridge, bridge, dist, center_point, utm_crs, dist_min
                    )

                    # If the length difference is less than 15%, stop the search
                    if abs(length_percent) < 15:
                        break  # breaks the loop iterating through distances and go to the next brdg

                    # If the length difference is greater than the previous difference,
                    # revert to the previous distance and stop the search
                    elif abs(length_percent) > abs(length_percent_prev_dist):
                        gdf_OSM_bridge = gdf_OSM_bridge_prev_dist.copy()
                        break  # breaks the loop iterating through distances and go to the next brdg

                    # If the length difference is more than 15% but less than in the previous iteration and
                    # the distance is less than or equal to 500m, look for roads
                    # (looking for roads at distances greater than 500m might result in including
                    # inrrelevant roads far away from the bridge)
                    elif dist <= (5 * dist_min):
                        # Check if the GeoDataFrame for the bridge is not empty
                        if len(gdf_OSM_bridge) != 0:
                            # If it's not empty, check for roads around the bridge
                            gdf_roads = check_for_roads(center_point, tags_roads, dist)

                            if gdf_roads is not None:
                                gdf_roads = gdf_roads.to_crs(utm_crs)

                                # Concatenate the GeoDataFrames for the bridge and the roads,
                                gdf_OSM_bridge_with_roads = pd.concat(
                                    [gdf_OSM_bridge, gdf_roads]
                                )

                        else:
                            # If the GeoDataFrame for the bridge is empty, just check for roads around the bridge
                            gdf_OSM_bridge_with_roads = check_for_roads(
                                center_point, tags_roads, dist
                            )
                            if gdf_OSM_bridge_with_roads is not None:
                                gdf_OSM_bridge_with_roads = (
                                    gdf_OSM_bridge_with_roads.to_crs(utm_crs)
                                )

                        # Once a geometry is found, store the longest as the initial line
                        # and then remove all not parallel lines
                        if initial_line is None:
                            # Get the longest line by comparing lengths directly
                            lengths = gdf_OSM_bridge_with_roads.geometry.apply(lambda x: x.length)
                            initial_line = gdf_OSM_bridge_with_roads.geometry[lengths.idxmax()]
                        else:
                            gdf_OSM_bridge_with_roads, initial_line = (
                                filter_parallel_lines(gdf_OSM_bridge, initial_line, filter_buffer_distance)
                            )

                        # If roads found, then check its length
                        if gdf_OSM_bridge_with_roads is not None:
                            # Check the length of the bridge and road data,
                            # and get the percentage difference in length
                            gdf_OSM_bridge_with_roads, length_percent_road = (
                                check_bridge_length(
                                    gdf_OSM_bridge_with_roads,
                                    bridge,
                                    dist,
                                    center_point,
                                    utm_crs,
                                    dist_min,
                                )
                            )

                            # If the absolute percentage difference in length is less than 15%, consider it a match
                            if abs(length_percent_road) < 15:
                                # Copy the GeoDataFrame with both bridge and road data to the main GeoDataFrame
                                gdf_OSM_bridge = gdf_OSM_bridge_with_roads.copy()
                                # Update the length percentage
                                length_percent = length_percent_road
                                # Break the loop as we have found a match
                                break

                            # If the absolute percentage difference in length is greater than
                            # the current length percentage, ignore this iteration
                            elif abs(length_percent_road) > abs(length_percent):
                                break

                            # If the absolute percentage difference in length is greater than
                            # the previous length percentage, revert to the previous GeoDataFrame
                            elif abs(length_percent_road) > abs(
                                length_percent_prev_dist
                            ):
                                gdf_OSM_bridge = gdf_OSM_bridge_prev_dist.copy()
                                # Break the loop as we have found a match
                                break

                            else:
                                # If none of the above conditions are met, continue with the next iteration
                                continue

            except Exception as e:
                print(
                    "There is an issue with the bridge nb",
                    brdg_id,
                    "at distance",
                    dist,
                    "\n",
                    e,
                    "\n",
                )

        # If no lines are found, try using the backup
        if gdf_OSM_bridge is None:
            if "gdf_OSM_bridge_100_backup" in locals():
                if not gdf_OSM_bridge_100_backup.empty:
                    gdf_OSM_bridge = gdf_OSM_bridge_100_backup.copy()

        # If geometry is empty, check if backup is available and use
        elif len(gdf_OSM_bridge) == 0:
            if "gdf_OSM_bridge_100_backup" in locals():
                if not gdf_OSM_bridge_100_backup.empty:
                    gdf_OSM_bridge = gdf_OSM_bridge_100_backup.copy()

        # Once a geometry is found, store the longest as the initial line and then remove all not parallel lines
        if (
            initial_line is None
            and "gdf_OSM_bridge" in locals()
            and gdf_OSM_bridge is not None
            and not gdf_OSM_bridge.empty
        ):
            # Get the longest line by comparing lengths directly
            lengths = gdf_OSM_bridge.geometry.apply(lambda x: x.length)
            initial_line = gdf_OSM_bridge.geometry[lengths.idxmax()]
        elif "gdf_OSM_bridge" in locals() and gdf_OSM_bridge is not None:
            gdf_OSM_bridge, initial_line = filter_parallel_lines(
                gdf_OSM_bridge, initial_line, filter_buffer_distance
            )

            # If gdf_OSM_bridge is empty, then use the backup
            if len(gdf_OSM_bridge) == 0:
                if "gdf_OSM_bridge_100_backup" in locals():
                    if not gdf_OSM_bridge_100_backup.empty:
                        gdf_OSM_bridge = gdf_OSM_bridge_100_backup.copy()

        # Convert the GeoDataFrame to a common CRS
        if (
            ("gdf_OSM_bridge" in locals())
            and (gdf_OSM_bridge is not None)
            and (len(gdf_OSM_bridge) != 0)
        ):
            gdf_OSM_bridge = gdf_OSM_bridge.to_crs("EPSG:4326")
        else:
            # If no lines are found, create an empty GeoDataFrame
            # gdf_OSM_bridge = gpd.GeoDataFrame(
            #     {col: [] for col in gpd.GeoDataFrame([bridge]).columns}
            # )
            # gdf_OSM_bridge.crs = "EPSG:4326"

            # if no lines found, create a GeoDataFrame with a point-like line at the center of the bridge
            gdf_OSM_bridge = gpd.GeoDataFrame(bridge).T
            gdf_OSM_bridge = gdf_OSM_bridge.set_geometry("geometry")
            gdf_OSM_bridge.crs = "EPSG:4326"
            # Convert point to line
            gdf_OSM_bridge["geometry"] = gdf_OSM_bridge["geometry"].apply(
                lambda x: LineString([x, Point(x.x + 0.000001, x.y + 0.000001)])
            )

        # Convert all geometries into linestrings
        gdf_OSM_bridge["geometry"] = gdf_OSM_bridge["geometry"].apply(
            lambda x: x.boundary if x.geom_type == "Polygon" else x
        )

        # Combine all geometries together
        combined_geometry = gdf_OSM_bridge["geometry"].unary_union

        # Append the combined_geometry to the gdf_OSM at the appropriate bridge ID
        gdf_lsb.at[index, "combined_geometry"] = combined_geometry

        # Add railway, bridge, highway columns to the gdf_lsb
        if "railway" in gdf_OSM_bridge.columns:
            list_types = list(set(gdf_OSM_bridge["railway"]))
            gdf_lsb.at[index, "railway"] = list_types

        if "bridge" in gdf_OSM_bridge.columns:
            list_types = list(set(gdf_OSM_bridge["bridge"]))
            gdf_lsb.at[index, "bridge"] = list_types

        if "highway" in gdf_OSM_bridge.columns:
            list_types = list(set(gdf_OSM_bridge["highway"]))
            gdf_lsb.at[index, "highway"] = list_types

        # Append the GeoDataFrame to the list
        if len(gdf_OSM_bridge) == 0:
            print("No OSM lines found for bridge nb", brdg_id)

        # clean up
        try:
            del gdf_OSM_bridge
        except Exception:
            pass

        try:
            del gdf_OSM_bridge_prev_dist
        except Exception:
            pass

        try:
            del length_percent_prev_dist
        except Exception:
            pass

        try:
            del gdf_OSM_bridge_100_backup
        except Exception:
            pass

    return gdf_lsb


def find_OSM_lines_and_polygons(
    gdf_lsb,
    dist_min=100,
    dist_max=2000,
    dist_interval=100,
    primary_buffer_distance=0.00045,  # Added parameter for primary buffer
    secondary_buffer_distance=0.00003,  # Added parameter for secondary buffer
    filter_buffer_distance=0.00045,  # Added parameter for filtering parallel lines
    length_percentage=None,  # New parameter for dynamic buffer based on line length
):
    """
    This function retrieves the OSM lines for the bridges in the LSB database and converts them to polygons.

    Arguments:
        gdf_lsb (GeoDataFrame): The GeoDataFrame containing the LSB database.
        dist_min (int): The minimum distance to check for bridges (default: 100).
        dist_max (int): The maximum distance to check for bridges (default: 2000).
        dist_interval (int): The interval between distance checks (default: 100).
        primary_buffer_distance (float): Main buffer distance for creating polygons (default: 0.00045).
        secondary_buffer_distance (float): Additional buffer to close gaps (default: 0.00003).
        filter_buffer_distance (float): Buffer distance used for filtering parallel lines (default: 0.00045).
        length_percentage (float, optional): If provided, buffer will be the smaller of primary_buffer_distance 
            or length_percentage * line_length (default: None).

    Returns:
        tuple: A tuple containing the GeoDataFrame with the OSM lines
        for the bridges added and the GeoDataFrame with the polygons.
    """
    # print("findOSMlines", dist_min)
    # Set-up columns for output
    gdf_lsb["highway"] = np.nan
    gdf_lsb["railway"] = np.nan
    gdf_lsb["bridge"] = np.nan

    gdf_lsb["highway"] = gdf_lsb["highway"].astype(object)
    gdf_lsb["railway"] = gdf_lsb["railway"].astype(object)
    gdf_lsb["bridge"] = gdf_lsb["bridge"].astype(object)

    # Iterate over bridges and find OSM lines
    gdf_lsb = get_bridge_lines(gdf_lsb, dist_min, dist_max, dist_interval, filter_buffer_distance)

    # Drop the original 'geometry' column
    gdf_lsb = gdf_lsb.drop(columns=["geometry"])

    # Convert columns to strings
    gdf_lsb["highway"] = gdf_lsb["highway"].astype(str)
    gdf_lsb["railway"] = gdf_lsb["railway"].astype(str)
    gdf_lsb["bridge"] = gdf_lsb["bridge"].astype(str)

    # Rename the 'combined_geometry' column to 'geometry'
    # Set 'combined_geometry' as the active geometry column
    gdf_lsb = gdf_lsb.rename(columns={"combined_geometry": "geometry"})
    gdf_lsb = gdf_lsb.set_geometry("geometry")

    # Filter out GEOMETRYCOLLECTION geometries
    gdf_lsb = gdf_lsb[
        gdf_lsb.geometry.geom_type.isin(
            ["Point", "LineString", "Polygon", "MultiLineString"]
        )
    ]

    # Initialize a gdf to store the polygons
    gdf_lsb_polygons = gdf_lsb.copy()

    # Loop over each row in the GeoDataFrame to get polygons
    for index, row in gdf_lsb.iterrows():
        # If the geometry is a LineString, convert it to a MultiLineString
        if isinstance(row["geometry"], LineString):
            multi_line = MultiLineString([row["geometry"]])

        # If the geometry is already a MultiLineString, use it directly
        elif isinstance(row["geometry"], MultiLineString):
            multi_line = row["geometry"]

        # Skip this row if the geometry is not a LineString or MultiLineString
        else:
            continue

        # Get the convex hull of the MultiLineString
        # convex_hull_polygon = multi_line.convex_hull

        # Make unirary union of the geometry of the row and the initial_line_polygon
        try:
            multi_line = linemerge(unary_union(multi_line))
        except Exception:
            multi_line = unary_union(multi_line)

        # Calculate the dynamic buffer distance if length_percentage is provided
        if length_percentage is not None:
            # Calculate the total length of the line
            line_length = multi_line.length
            # Calculate the dynamic buffer as a percentage of line length
            dynamic_buffer = line_length * length_percentage
            # Use the smaller of the dynamic buffer or primary buffer
            actual_primary_buffer = min(dynamic_buffer, primary_buffer_distance)
        else:
            actual_primary_buffer = primary_buffer_distance

        # Buffer the lines into a polygon using the calculated buffer distance
        convex_hull_polygon = multi_line.buffer(actual_primary_buffer, cap_style="flat")

        # Add an additional small buffer to the polygon to close gaps that could appear
        # if the lines were following a curve, using the secondary buffer distance
        convex_hull_polygon = convex_hull_polygon.buffer(secondary_buffer_distance, cap_style="square", join_style="mitre", mitre_limit=10)

        # Save polygon to gdf
        gdf_lsb_polygons.at[index, "geometry_poly"] = convex_hull_polygon

    # Drop the original 'geometry' column
    gdf_lsb_polygons = gdf_lsb_polygons.drop(columns=["geometry"])

    # Rename the 'combined_geometry' column to 'geometry'
    # Set 'combined_geometry' as the active geometry column
    gdf_lsb_polygons = gdf_lsb_polygons.rename(columns={"geometry_poly": "geometry"})
    gdf_lsb_polygons = gdf_lsb_polygons.set_geometry("geometry")

    return gdf_lsb, gdf_lsb_polygons
