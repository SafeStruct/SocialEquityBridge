# ============================================================================
# IMPORTS
# ============================================================================
import os
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt
from adjustText import adjust_text
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import matplotlib.colors as mcolors

from ps_predictions.third_paper.plotting_helper import (
    # add_labels_to_map,
    colormap,
    county_codes,
    add_histogram_legend,
)

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Paths
folder_path = "/mnt/e/SOCIAL_PAPER"
plots_path = os.path.join(folder_path, "plots_maps_08_01_2026")
nbi_csv_path = os.path.join(
    folder_path, "California_brdgs/NBI", "nbi_bridges_geo_county.csv"
)
path_counties_shp = os.path.join(
    folder_path, "California_borders", "ca_counties", "CA_Counties.shp"
)

# Output files
output_map_path = os.path.join(plots_path, "Number of Bridges_map.png")

# Plot configuration
bins = list(range(0, 3750, 250))
vmax = bins[-1]
figsize = (10, 10)
dpi = 600

# ============================================================================
# DATA LOADING
# ============================================================================

# Import NBI data
nbi_df = pd.read_csv(nbi_csv_path, low_memory=False)

# Count bridges per county
bridge_counts = nbi_df["County"].value_counts().reset_index()
bridge_counts.columns = ["County", "bridge_count"]

# Make the bridge count an int
bridge_counts["bridge_count"] = bridge_counts["bridge_count"].astype(int)

# Count number of bridges that could be affected by scour
# (i.e. they are over water)
# those have scour criticality SCOUR_CRITICAL_113 set to anything but not N
bridge_over_water_count = (
    nbi_df[~nbi_df["SCOUR_CRITICAL_113"].isin(["N"])]
    .groupby("County")
    .size()
    .reset_index(name="over_water_count")
)
bridge_counts = bridge_counts.merge(bridge_over_water_count, on="County", how="left")

# Read shp file with the counties
counties_geometries = gpd.read_file(path_counties_shp)

# Merge bridge counts with counties geometries
counties_geometries = counties_geometries.merge(
    bridge_counts, left_on="NAME", right_on="County", how="left"
)
counties_geometries["County_Code"] = counties_geometries["NAME"].map(county_codes)

# Rename bridge_count to Number of Bridges
counties_geometries.rename(columns={"bridge_count": "Number of Bridges"}, inplace=True)

# ============================================================================
# PLOTTING
# ============================================================================

# Create a figure and an axes
fig = plt.figure(figsize=figsize)
ax = plt.axes(projection=ccrs.epsg(3857))

ax.add_feature(cfeature.LAND, alpha=0.5)
ax.add_feature(cfeature.OCEAN, alpha=0.5)
ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.3)
ax.add_feature(cfeature.LAKES, alpha=0.5)
ax.add_feature(cfeature.RIVERS, alpha=0.5)


# Determine number of bins
if isinstance(bins, list):
    n_bins = len(bins) - 1
else:
    n_bins = bins

# Create discrete colormap with exact number of colors
colors = [colormap(i / (n_bins - 1)) for i in range(n_bins)]
discrete_cmap = mcolors.ListedColormap(colors)
# print("Using discrete colormap with colors:", colors)

# Create a discrete colormap with an extra color at the beginning
colors_with_padding = [colormap(0)] + [
    colormap(i / (n_bins - 1)) for i in range(n_bins)
]
discrete_cmap_padded = mcolors.ListedColormap(colors_with_padding)
# print("Using discrete colormap with colors:", discrete_cmap_padded)

# Create consistent normalisation
if isinstance(bins, list):
    vmin, vmax = min(bins), max(bins)
else:
    vmin, vmax = (
        counties_geometries["Number of Bridges"].min(),
        counties_geometries["Number of Bridges"].max(),
    )

norm = plt.Normalize(vmin=vmin, vmax=vmax)

# Plot counties with bridge counts using colormap and user-defined bins
counties_geometries.plot(
    ax=ax,
    column="Number of Bridges",
    cmap=discrete_cmap_padded,
    scheme="User_Defined",
    classification_kwds=dict(bins=bins),
    legend=False,
    edgecolor="black",
    linewidth=0.25,
)

# Collect text objects for adjustText
texts = []

for idx, row in counties_geometries.iterrows():
    if not row.geometry.is_empty:
        county = row["County"]
        col = "Number of Bridges"
        label = f"{county}\n{row[col]}"

        centroid = row.geometry.centroid

        # Create text object
        text = ax.text(
            centroid.x,
            centroid.y,
            label,
            transform=ccrs.epsg(3857),
            ha="center",
            va="center",
            fontsize=9,
            bbox=dict(
                facecolor="white", alpha=0.9, edgecolor="none", linewidth=0.5, pad=0.5
            ),
            zorder=5,
        )
        texts.append(text)

# Automatically adjust text positions
adjust_text(
    texts,
    arrowprops=dict(
        arrowstyle="-|>",
        color="black",
        alpha=0.7,
        lw=0.8,
        # shrinkA=10, shrinkB=10
    ),
    expand_text=(1.2, 1.4),
    expand_points=(1.5, 1.5),
    force_text=0.5,
    force_points=0.1,
    force_explode=(0.4, 0.4),  # This forces all labels to move away initially
    explode_radius=150,
    ax=ax,
    min_arrow_len=0,
)

# # Create colorbar
# if isinstance(bins, list):
#     norm = plt.Normalize(vmin=min(bins), vmax=max(bins))
# else:
#     norm = plt.Normalize(vmin=0, vmax=vmax)


# Add histogram legend (bins must match)
add_histogram_legend(
    ax=ax,
    data=counties_geometries,
    column="Number of Bridges",
    colormap=discrete_cmap,
    norm=norm,
    position=[0.68, 0.65, 0.3, 0.3],
    bins=bins,
    title="Value Distribution",
    bar_edgecolor="black",
    bar_linewidth=0.5,
    fontsize_title=12,
    fontsize_labels=12,
    fontsize_ticks=10,
)

# Turn off axis
ax.axis("off")

# Remove edges of the plot
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

plt.savefig(
    output_map_path,
    dpi=dpi,
    bbox_inches="tight",
)

plt.close()
