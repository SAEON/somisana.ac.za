import copernicusmarine
from datetime import datetime, timedelta
import os

# Detect the environment based on hostname
HOSTNAME = os.uname().nodename

if HOSTNAME == "COMP000000183":
    print("Running on Local Machine:", HOSTNAME)
    output_directory = "/home/nc.memela/Projects/tmp/sat-sst/"
else:
    print("Running on Server:", HOSTNAME)
    output_directory = "/home/nkululeko/tmp/sat-sst/long-record/"  # Updated path with "/ocean-access" removed

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Set credentials directly to avoid manual login prompts
os.environ['CMEMS_USERNAME'] = 'nmemela1'  # Replace with your actual username
os.environ['CMEMS_PASSWORD'] = 'Memela161'  # Replace with your actual password

# Define the date range: start of last year to the most recent available day
start_date = datetime(datetime.today().year - 1, 1, 1)
current_date = datetime.today()
max_lookback_days = 30  # Check up to 30 days back if today's data is not available

# Attempt to fetch data from the start of last year to the most recent day available
data_downloaded = False

for days_back in range(max_lookback_days):
    end_date_str = current_date.strftime('%Y-%m-%d')
    start_date = datetime(2007, 2, 1).strftime('%Y-%m-%d')
    print(f"Attempting to fetch data from {start_date} to {end_date_str}...")

    try:
        # Attempt to fetch the data
        copernicusmarine.subset(
            dataset_id="METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
            variables=["analysed_sst", "analysis_error", "mask", "sea_ice_fraction"],
            minimum_longitude=10,
            maximum_longitude=40,
            minimum_latitude=-40,
            maximum_latitude=-20,
            start_datetime=f"{start_date.strftime('%Y-%m-%d')}T00:00:00",
            end_datetime=f"{end_date_str}T00:00:00",
            output_directory=output_directory,
            username=os.getenv('CMEMS_USERNAME'),
            password=os.getenv('CMEMS_PASSWORD')
        )
        print(f"Data successfully downloaded from {start_date.strftime('%Y-%m-%d')} to {end_date_str}.")
        data_downloaded = True
        break  # Exit loop if data is downloaded successfully

    except Exception as e:
        print(f"No data available up to {end_date_str}. Trying the previous day...")
        current_date -= timedelta(days=1)

if not data_downloaded:
    print("No recent data available in the past 30 days. Keeping the existing file.")
