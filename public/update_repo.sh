#!/bin/bash

LOCKFILE=/tmp/git_push.lock
REPO_DIR="/home/nkululeko/somisana.ac.za"

# Check if lock file exists (prevent two scripts at the same time)
if [ -e "$LOCKFILE" ]; then
    echo "🔒 Script already running. Exiting."
    exit 1
fi

# Create lock file
touch "$LOCKFILE"

# Navigate to your repository
cd "$REPO_DIR" || exit

# Remove Git lock if it exists
if [ -f .git/index.lock ]; then
    echo "⚠️  Removing stale index.lock file..."
    rm -f .git/index.lock
fi

# Update your local repository (optional — you can comment this if unnecessary)
git pull origin main

# Add any changes
git add .

# Only commit if there are changes
if ! git diff-index --quiet HEAD --; then
    git commit -m "Automated update commit on $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
else
    echo "✅ No changes to commit."
fi

# Remove lock file
rm -f "$LOCKFILE"


