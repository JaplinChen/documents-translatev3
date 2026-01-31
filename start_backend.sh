#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

# Activate venv
source .venv/bin/activate

# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Starting backend in venv..."
# Run uvicorn
python -m uvicorn backend.main:app --reload --port 5002 --host 0.0.0.0
