# In this script, an RGB raster image is converted into a raster with one value per pixel.
import os
import numpy as np
import rasterio


def create_rgb_to_ordinal_map():
    """Create a dictionary mapping RGB values to ordinal susceptibility values

    Ordinal Value Ranges:
    12: < -5.5 mm displacement
    11: -5.5 to -5.0 mm
    10: -5.0 to -4.5 mm
    9:  -4.5 to -4.0 mm
    8:  -4.0 to -3.5 mm
    7:  -3.5 to -3.0 mm
    6:  -3.0 to -2.5 mm
    5:  -2.5 to -2.0 mm
    4:  -2.0 to -1.5 mm
    3:  -1.5 to -1.0 mm
    2:  -1.0 to -0.5 mm
    1:  -0.5 to 0 mm
    0:  No data
    1:  0 to 0.5 mm (positive displacement)
    2:  0.5 to 2.0 mm (positive displacement)
    """
    return {
        (194, 82, 60): 12,  # < -5.5 mm
        (209, 104, 48): 11,  # -5.5 to -5.0 mm
        (227, 136, 32): 10,  # -5.0 to -4.5 mm
        (240, 173, 17): 9,  # -4.5 to -4.0 mm
        (245, 206, 10): 8,  # -4.0 to -3.5 mm
        (252, 244, 3): 7,  # -3.5 to -3.0 mm
        (170, 242, 0): 6,  # -3.0 to -2.5 mm
        (73, 230, 0): 5,  # -2.5 to -2.0 mm
        (4, 214, 15): 4,  # -2.0 to -1.5 mm
        (19, 189, 87): 3,  # -1.5 to -1.0 mm
        (29, 163, 132): 2,  # -1.0 to -0.5 mm
        (28, 136, 145): 1,  # -0.5 to 0 mm
        (0, 0, 0): 0,  # No data
        (19, 89, 133): 1,  # 0 to 0.5 mm (positive displacement)
        (11, 44, 122): 2,  # 0.5 to 2.0 mm (positive displacement)
    }


def rgb_to_ordinal(input_raster_path, output_raster_path):
    """
    Convert RGB raster to ordinal susceptibility values.

    Parameters:
    input_raster_path: Path to input RGB raster
    output_raster_path: Path to save output ordinal raster
    """

    # Pre-compute RGB arrays once
    rgb_map = create_rgb_to_ordinal_map()
    rgb_values = np.array(list(rgb_map.keys()), dtype=np.int16)
    ordinal_values = np.array(list(rgb_map.values()), dtype=np.int16)

    with rasterio.open(input_raster_path) as src:
        # Ensure we have an RGB raster
        profile = src.profile.copy()

        if src.count != 3:
            raise ValueError("Input raster must have exactly 3 bands (RGB)")

        # Update profile for output
        profile.update(dtype=rasterio.int16, count=1, nodata=0)

        # Process in chunks
        with rasterio.open(output_raster_path, "w", **profile) as dst:
            for ji, window in src.block_windows():
                # Read and process chunk
                rgb_chunk = src.read(window=window).astype(np.int16)

                # Swap bands 1 and 3 in the chunk
                rgb_chunk = np.stack([rgb_chunk[2], rgb_chunk[1], rgb_chunk[0]])

                # DEBUGGING
                # if rgb_chunk[1].max() > 170:
                #     rgb_chunk = rgb_chunk[:, :, 2464:2467]
                #     print(rgb_chunk.max())

                rgb_pixels = rgb_chunk.transpose(1, 2, 0)

                # First handle no data (0,0,0) exactly
                no_data_mask = np.all(rgb_pixels == [0, 0, 0], axis=2)

                # Then handle other colors with tolerance
                # Vectorized matching
                # differences = np.abs(rgb_pixels[:, :, np.newaxis, :] - rgb_values)
                # matches = np.all(differences <= tolerance, axis=-1)
                # match_indices = np.argmax(matches, axis=-1)

                # Calculate absolute differences and their means
                differences = np.abs(
                    rgb_pixels[:, :, np.newaxis, :]
                    - rgb_values[np.newaxis, np.newaxis, :, :]
                )

                # differences = np.abs(rgb_pixels[:, :, np.newaxis, :] - rgb_values)
                mean_differences = np.mean(
                    differences, axis=-1
                )  # Average across RGB channels

                # # Find matches where mean difference is within tolerance
                # matches = mean_differences <= tolerance
                # match_indices = np.argmax(matches, axis=-1)

                # Find indices of smallest mean differences
                match_indices = np.argmin(mean_differences, axis=-1)

                # Create output chunk
                output = np.zeros(rgb_pixels.shape[:2], dtype=np.int16)
                # has_match = np.any(matches, axis=-1)
                # output[has_match] = ordinal_values[match_indices[has_match]]
                output[:] = ordinal_values[match_indices]

                # Override with no data values
                output[no_data_mask] = 0

                # Write chunk
                dst.write(output[np.newaxis, :, :], window=window)


if __name__ == "__main__":

    folder_path = (
        "/mnt/g/SOCIAL_PAPER/California_subsidence/vertical_displacement_rasters"
    )

    input_path = os.path.join(
        folder_path,
        "Vertical_Displacement_TRE_ALTAMIRA_Total_Since_20150613_20240701_merged_filled.tif",
    )
    output_path = os.path.join(
        folder_path, "subsidence_susceptibility_ordinal_filled.tif"
    )
    rgb_to_ordinal(input_path, output_path)
