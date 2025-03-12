#!/bin/bash

# Set the script to exit if any command fails
set -e

# Detect the environment based on hostname
HOSTNAME=$(hostname)

if [[ "$HOSTNAME" == "COMP000000183" ]]; then
    echo "Running on Local Machine: $HOSTNAME"
    BASE_DIR="/home/nc.memela/Projects/tmp/sat-sst"
    CONDA_PATH="/home/nc.memela/anaconda3/bin/activate"
else
    echo "Running on Server: $HOSTNAME"
    BASE_DIR="/home/ocean-access/tmp/sat-sst"
    CONDA_PATH="/home/ocean-access/anaconda3/bin/activate"
fi

# Ensure Conda is available in non-interactive shells
source $CONDA_PATH

# Activate the conda environment
echo "Activating conda environment: somisana_croco"
conda activate somisana_croco

# Move to the directory where this script is located
cd "$(dirname "$0")"

# Define the paths to your scripts
DOWNLOAD_SCRIPT="download_sst_cmems.py"
PLOT_SCRIPT="generate_adt_anomaly_sst.py"

# Define the download directory and file pattern dynamically
DOWNLOAD_DIRECTORY="$BASE_DIR"
FILE_PATTERN="METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2_multi-vars_*.nc"

# Check for existing files before download
echo "Checking for existing files in $DOWNLOAD_DIRECTORY"
existing_files=($DOWNLOAD_DIRECTORY/$FILE_PATTERN)

# Remove old files before downloading new ones
if [ -n "${existing_files[0]}" ]; then
    echo "Removing old files before download..."
    rm -f "${existing_files[@]}"
    echo "Old files removed successfully."
else
    echo "No old files found."
fi

# Execute the download script
echo "Running download script: $DOWNLOAD_SCRIPT"
python $DOWNLOAD_SCRIPT

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "✅ Download completed successfully."
else
    echo "❌ Download failed."
    exit 1
fi

# Execute the plot generation script
echo "Running plot generation script: $PLOT_SCRIPT"
python $PLOT_SCRIPT

echo "✅ Plot generation completed successfully."

# Deactivate Conda environment (optional)
conda deactivate
