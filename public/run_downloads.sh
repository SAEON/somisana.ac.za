#!/bin/bash

# Ensure Conda is available in non-interactive shells
source /home/nc.memela/anaconda3/etc/profile.d/conda.sh

# Activate your Conda environment
conda activate somisana_croco

# Run the Python script
python /home/nc.memela/Projects/somisana-current_running_file/public/download_gifs.py

# Deactivate the environment (optional)
conda deactivate

