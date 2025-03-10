import copernicusmarine
from datetime import datetime, timedelta
from datetime import datetime
import os

# Get today's date in the required format (YYYY-MM-DD)
today = datetime.today().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
#last_year ='2025-03-05'
# Define the output directory
output_directory = "/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-ssh"

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

# Fetch the data with a specified output directory
copernicusmarine.subset(
    dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    variables=["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "ugos", "ugosa", "vgos", "vgosa"],
    minimum_longitude=10,
    maximum_longitude=40,
    minimum_latitude=-40,
    maximum_latitude=-20,
    start_datetime=f"{yesterday}T00:00:00",
    end_datetime=f"{today}T00:00:00",
    output_directory=output_directory
)

