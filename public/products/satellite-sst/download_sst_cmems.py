import copernicusmarine
from datetime import datetime, timedelta
import os

# Define the output directory
output_directory = "/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-sst"
os.makedirs(output_directory, exist_ok=True)

# Fetch credentials from environment variables
username = 'nmemela1'
password = 'Memela161'

# Initialize the date with today and set a maximum lookback period (7 days)
current_date = datetime.today()
max_lookback_days = 7

# Initialize a flag to track successful download
data_downloaded = False

# Loop to attempt data download, going back one day if not available
for days_back in range(max_lookback_days):
    date_str = current_date.strftime('%Y-%m-%d')
    print(f"Attempting to fetch data for {date_str}...")

    try:
        # Attempt to fetch the data
        copernicusmarine.subset(
            dataset_id="METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
            variables=["analysed_sst", "analysis_error", "mask", "sea_ice_fraction"],
            minimum_longitude=10,
            maximum_longitude=40,
            minimum_latitude=-40,
            maximum_latitude=-20,
            start_datetime=f"{date_str}T00:00:00",
            end_datetime=f"{date_str}T00:00:00",
            username=username,
            password=password,
            output_directory=output_directory
        )
        print(f"Data successfully downloaded for {date_str}.")
        data_downloaded = True
        break  # Exit loop once data is downloaded

    except Exception as e:
        print(f"No data available for {date_str}. Trying the previous day...")
        # Move to the previous day
        current_date -= timedelta(days=1)

if not data_downloaded:
    print("No recent data available in the past 7 days. Keeping the existing file.")
