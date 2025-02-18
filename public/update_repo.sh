#!/bin/bash
REPO_DIR="/home/nkululeko/somisana.ac.za"

# Navigate to your repository
cd "$REPO_DIR" || exit

# Update your local repository
git pull origin main

# Add any changes
git add .

# Only commit if there are changes
if ! git diff-index --quiet HEAD --; then
    git commit -m "Automated update commit on $(date)"
    git push origin main
fi

