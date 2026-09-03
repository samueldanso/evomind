#!/bin/sh
set -e

# Seed DB on first run (persistent disk starts empty)
if [ ! -f /data/manifest.db ]; then
    echo "No DB found at /data/manifest.db — seeding..."
    mkdir -p /data
    uv run python scripts/seed.py
    echo "Seed complete."
fi

# Start FastAPI server
exec uv run uvicorn server:app --host 0.0.0.0 --port "${PORT:-8765}"
