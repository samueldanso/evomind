#!/bin/sh
set -e

mkdir -p /data

# Seed version — bump this to force re-seed on next deploy
SEED_VERSION="2"

NEEDS_SEED=false
if [ ! -f /data/manifest.db ]; then
    NEEDS_SEED=true
elif [ ! -f /data/.seed-version ] || [ "$(cat /data/.seed-version)" != "$SEED_VERSION" ]; then
    NEEDS_SEED=true
fi

if [ "$NEEDS_SEED" = "true" ]; then
    echo "Seeding database (version $SEED_VERSION)..."
    rm -f /data/manifest.db
    EVO_STORE=/data uv run python scripts/seed.py
    echo "$SEED_VERSION" > /data/.seed-version
    echo "Seed complete."
fi

# Start FastAPI server
exec uv run uvicorn server:app --host 0.0.0.0 --port "${PORT:-8765}"
