import copernicusmarine
from datetime import datetime
import os

# Get today's date in the required format (YYYY-MM-DD)
today = datetime.today().strftime('%Y-%m-%d')
last_year ='2024-01-01'
# Define the output directory
output_directory = "/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-sst"

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Fetch the data with a specified output directory
copernicusmarine.subset(
    dataset_id="METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
    variables=["analysed_sst", "analysis_error", "mask", "sea_ice_fraction"],
    minimum_longitude=10,
    maximum_longitude=40,
    minimum_latitude=-40,
    maximum_latitude=-20,
    start_datetime=f"{last_year}T00:00:00",
    end_datetime=f"{today}T00:00:00",
    output_directory=output_directory
)

