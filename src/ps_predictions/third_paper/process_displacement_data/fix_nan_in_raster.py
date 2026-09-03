import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize
import warnings
import rasterio

# Suppress warnings
warnings.filterwarnings("ignore")

# Change these parameters:
main_folder = "/mnt/g/SOCIAL_PAPER/California_subsidence/vertical_displacement_Govorcin_paper"
input_raster_path = os.path.join(main_folder, 'CA_VLM.tif')  # Full path to your input raster
output_raster_path = os.path.join(main_folder, 'CA_VLM_fixed.tif')  # Full path for the output raster
nodata_value = 999  # The value you want to replace NaN with

try:
    print(f"Reading raster from {input_raster_path}")
    
    # Use rasterio for geospatial processing
    with rasterio.open(input_raster_path) as src:
        # Read the data
        data = src.read(1)
        profile = src.profile
        
        # Convert NaN values to the specified nodata value
        print(f"Before conversion: Found {np.sum(np.isnan(data))} NaN values")
        data = np.nan_to_num(data, nan=nodata_value)
        print(f"After conversion: All NaN values have been replaced with {nodata_value}")
        
        # Update the profile to include the nodata value
        profile.update(nodata=nodata_value)
        
        # Write the output raster
        with rasterio.open(output_raster_path, 'w', **profile) as dst:
            dst.write(data, 1)
            
    print(f"Process completed. Output saved to: {output_raster_path}")
    
except Exception as e:
    print(f"Error processing the raster: {e}")