import copernicusmarine
from datetime import datetime, timedelta
import os
import glob  # ✅ Added import for 'glob'

# Detect the environment based on hostname
HOSTNAME = os.uname().nodename

if HOSTNAME == "COMP000000183":
    print("Running on Local Machine:", HOSTNAME)
    OUTPUT_DIR = "/home/nc.memela/Projects/tmp/sat-sst/"
else:
    print("Running on Server:", HOSTNAME)
    OUTPUT_DIR = os.path.expanduser("~/tmp/sat-sst/")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fetch credentials from environment variables
username = os.getenv("CMEMS_USERNAME", "nmemela1")
password = os.getenv("CMEMS_PASSWORD", "Memela161")

# Initialize the date with today and set a maximum lookback period (7 days)
current_date = datetime.today()
max_lookback_days = 7

# Initialize a flag to track successful download
data_downloaded = False

# Loop to attempt data download, going back one day if not available
for days_back in range(max_lookback_days):
    date_str = current_date.strftime('%Y-%m-%d')
    print(f"🌍 Attempting to fetch SST data for {date_str}...")
    
    # Define expected filename pattern (modify if necessary)
    expected_filename_pattern = os.path.join(OUTPUT_DIR, f"*{date_str}*.nc")

    # Check if any matching file exists in the directory
    existing_files = glob.glob(expected_filename_pattern)

    # If a file exists, delete it
    if existing_files:
        for file in existing_files:
            os.remove(file)
            print(f"🗑️ Deleted existing file: {file}")


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
            output_directory=OUTPUT_DIR,
        )
        print(f"✅ Data successfully downloaded for {date_str}.")
        data_downloaded = True
        break  # Exit loop once data is downloaded

    except Exception as e:
        print(f"❌ No data available for {date_str}. Trying the previous day...")
        # Move to the previous day
        current_date -= timedelta(days=1)

if not data_downloaded:
    print("⚠️ No recent data available in the past 7 days. Keeping the existing file.")
