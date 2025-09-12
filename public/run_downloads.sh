#!/bin/bash

# Detect the environment based on hostname
HOSTNAME=$(hostname)

if [[ "$HOSTNAME" == "COMP000000183" ]]; then
    echo "Running on Local Machine: $HOSTNAME"
    
    # Ensure Conda is available in non-interactive shells
    source /home/nc.memela/anaconda3/etc/profile.d/conda.sh

    # Activate Conda environment
    conda activate somisana_croco

    # Run the Python script
    python /home/nc.memela/Projects/somisana.ac.za/public/download_gifs.py

    # Deactivate the environment (optional)
    conda deactivate

#else
#    echo "Running on Server: $HOSTNAME"
    
#    # Ensure Virtual Environment is available in non-interactive shells
#    source /home/ocean-access/python_venv/bin/activate

#    # Run the Python script
#    python /home/nkululeko/somisana.ac.za/public/download_gifs.py

#    # Deactivate the environment (optional)
#    deactivate
#fi

else
    echo "Running on Server: $HOSTNAME"

    # Ensure Conda is available in non-interactive shells
    source /home/nkululeko/miniforge3/etc/profile.d/conda.sh

    # Activate Conda environment
    conda activate somisana_croco

    # Run the Python script
    python /home/nkululeko/somisana.ac.za/public/download_gifs.py

    # Deactivate the environment (optional)
    conda deactivate
fi

