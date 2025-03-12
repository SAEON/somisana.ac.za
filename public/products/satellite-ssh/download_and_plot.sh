#!/bin/bash

# Set the script to exit if any command fails
set -e

# Detect the environment based on hostname
HOSTNAME=$(hostname)

if [[ "$HOSTNAME" == "COMP000000183" ]]; then
    echo "📌 Running on Local Machine: $HOSTNAME"

    # Ensure Conda is available in non-interactive shells
    source /home/nc.memela/anaconda3/etc/profile.d/conda.sh

    # Activate Conda environment
    conda activate somisana_croco

    # Set base directory
    BASE_DIR="/home/nc.memela/Projects/tmp/sat-ssh"

elif [[ "$HOSTNAME" == *"ocean-access"* ]]; then
    echo "📌 Running on Server: $HOSTNAME"

    # Ensure Virtual Environment is available in non-interactive shells
    source /home/ocean-access/python_venv/bin/activate

    # Set base directory
    BASE_DIR="/home/ocean-access/tmp/sat-ssh"

else
    echo "🚨 Unknown environment: $HOSTNAME. Exiting."
    exit 1
fi

# Move to the directory where this script is located
cd "$(dirname "$0")"

# Define the paths to your scripts
DOWNLOAD_SCRIPT="download_ssh_cmems.py"
PLOT_SCRIPT="generate_adt_anomaly_ssh.py"

# Define the download directory and file pattern
FILE_PATTERN="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D_multi-vars_*.nc"

# Check for existing files before download
echo "📂 Checking for existing files in $BASE_DIR"
existing_files=($BASE_DIR/$FILE_PATTERN)

# Remove old files before downloading new ones
if [ -n "${existing_files[0]}" ]; then
    echo "🗑️ Removing old files before download..."
    rm -f "${existing_files[@]}"
    echo "✅ Old files removed successfully."
else
    echo "⚠️ No old files found."
fi

# Execute the download script
echo "📥 Running download script: $DOWNLOAD_SCRIPT"
python $DOWNLOAD_SCRIPT

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "✅ Download completed successfully."
else
    echo "❌ Download failed."
    exit 1
fi

# Execute the plot generation script
echo "📊 Running plot generation script: $PLOT_SCRIPT"
python $PLOT_SCRIPT

echo "🎉 Plot generation completed successfully."

# Deactivate the environment (optional)
if [[ "$HOSTNAME" == "COMP000000183" ]]; then
    conda deactivate
elif [[ "$HOSTNAME" == *"ocean-access"* ]]; then
    deactivate
fi
