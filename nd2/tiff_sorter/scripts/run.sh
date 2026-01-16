#!/bin/bash
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPTS_DIR/.."
PYTHON3="$PROJECT_DIR/venv/bin/python3"
"$PYTHON3" "$PROJECT_DIR/split_channels.py"