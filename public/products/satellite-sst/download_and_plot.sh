#!/bin/bash

# Set the script to exit if any command fails
set -e

# Activate the conda environment
echo "Activating conda environment: somisana_croco"
source ~/anaconda3/bin/activate somisana_croco

# Define the paths to your scripts
DOWNLOAD_SCRIPT="download_sst_cmems.py"
PLOT_SCRIPT="generate_adt_anomaly_ssh.py"

# Define the download directory and file pattern
DOWNLOAD_DIRECTORY="/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-sst"
FILE_PATTERN="METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_multi-vars_10.02E-39.97E_39.97S-20.02S_20*.nc"

# Check for existing files before download
echo "Checking for existing files in $DOWNLOAD_DIRECTORY"
existing_files=($DOWNLOAD_DIRECTORY/$FILE_PATTERN)

# Execute the download script
echo "Running download script: $DOWNLOAD_SCRIPT"
python $DOWNLOAD_SCRIPT

# If download is successful, remove old files
if [ $? -eq 0 ]; then
    echo "Download completed successfully."
    
    # Remove old files if new files exist
    if [ -n "${existing_files[0]}" ]; then
        echo "Removing old files..."
        rm -f "${existing_files[@]}"
        echo "Old files removed successfully."
    else
        echo "No old files found to remove."
    fi
else
    echo "Download failed. Old files will not be deleted."
    exit 1
fi

# Execute the plot generation script
echo "Running plot generation script: $PLOT_SCRIPT"
python $PLOT_SCRIPT

echo "Plot generation completed successfully."
