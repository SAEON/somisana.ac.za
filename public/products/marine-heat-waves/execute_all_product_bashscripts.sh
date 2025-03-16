#!/bin/bash

# Exit the script if any command fails
set -e

# Detect the environment based on hostname
HOSTNAME=$(hostname)

if [[ "$HOSTNAME" == "COMP000000183" ]]; then
    echo "📌 Running on Local Machine ($HOSTNAME)"
    BASE_DIR="/home/nc.memela/Projects/somisana.ac.za/public/products"
    ENV_ACTIVATION="source ~/anaconda3/bin/activate somisana_croco"
elif [[ "$HOSTNAME" == "ocimsvaps.ocean.gov.za" ]]; then
    echo "📌 Running on Server ($HOSTNAME)"
    BASE_DIR="/home/nkululeko/somisana.ac.za/public/products"
    ENV_ACTIVATION="source /home/ocean-access/python_venv/bin/activate"
else
    echo "🚨 Unknown environment: $HOSTNAME"
    exit 1
fi

# Define script paths dynamically
DOWNLOAD_SSH="$BASE_DIR/satellite-ssh/download_and_plot.sh"
DOWNLOAD_SST="$BASE_DIR/satellite-sst/download_and_plot.sh"
PLOT_MHW="$BASE_DIR/marine-heat-waves/generate_heatwaves.py"

# Function to execute a script and handle errors
run_script() {
    local script_path="$1"
    local script_type="$2"  # "bash" or "python"

    echo "🚀 Running $script_type script: $script_path"
    
    if [[ "$script_type" == "bash" ]]; then
        bash "$script_path"
    elif [[ "$script_type" == "python" ]]; then
        python "$script_path"
    else
        echo "❌ Unsupported script type: $script_type"
        exit 1
    fi

    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully executed: $script_path"
    else
        echo "❌ Failed to execute: $script_path"
        exit 1
    fi
}

# Activate the appropriate environment
echo "🔄 Activating environment..."
source /home/ocean-access/python_venv/bin/activate

# Execute the scripts
run_script "$DOWNLOAD_SST" "bash"
run_script "$DOWNLOAD_SSH" "bash"
run_script "$PLOT_MHW" "python"

echo "🎉 All scripts executed successfully!"
