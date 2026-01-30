#!/bin/bash

# Get the directory where this script is located
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPTS_DIR/.."
PIP3="$PROJECT_DIR/venv/bin/pip3"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Pull latest changes from GitHub
echo "Pulling latest changes from GitHub..."
if ! git pull origin main; then
    echo "Git pull failed!"
    exit 1
fi

# Install/update packages
echo "Updating packages..."
"$PIP3" install -q -r "$SCRIPTS_DIR/requirements.txt"

echo "Update complete!"