#!/bin/bash

# Set the script to exit if any command fails
set -e

# Define the paths to your scripts
DOWNLOAD_ssh="/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-ssh/download_and_plot.sh"
DOWNLOAD_sst="/home/nc.memela/Projects/somisana.ac.za/public/products/satellite-sst/download_and_plot.sh"
PLOT_mhw="/home/nc.memela/Projects/somisana.ac.za/public/products/marine-heat-waves/generate_adt_anomaly_ssh.py"

# Execute the download script bash script sst
echo "Running download script: $DOWNLOAD_sst"
./ $DOWNLOAD_sst

# Execute the download script bash script for ssh
echo "Running download script: $DOWNLOAD_ssh"
./ $DOWNLOAD_ssh

# Execute the plot generation script
echo "Running plot generation script: $PLOT_mhw"
python $PLOT_mhw

echo "Completed bash scripts successfully."
