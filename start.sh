#!/usr/bin/env bash
set -e

PORT_NUM="${PORT:-8000}"

echo "Starting BioRAG Backend on port ${PORT_NUM}..."

# Detect whether we are in repository root or inside backend/
if [ -f "backend/app/main.py" ]; then
    export PYTHONPATH=.
    exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT_NUM}"
elif [ -f "app/main.py" ]; then
    export PYTHONPATH=.
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUM}"
else
    echo "ERROR: Could not locate app/main.py"
    exit 1
fi
