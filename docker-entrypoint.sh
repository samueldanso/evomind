#!/bin/sh
set -e

mkdir -p /data

# Re-seed if DB is missing OR has no chunks (incomplete previous seed)
NEEDS_SEED=false
if [ ! -f /data/manifest.db ]; then
    NEEDS_SEED=true
else
    CHUNK_COUNT=$(uv run python -c "import sqlite3; c=sqlite3.connect('/data/manifest.db'); print(c.execute(\"SELECT COUNT(*) FROM chunks\").fetchone()[0])" 2>/dev/null || echo "0")
    if [ "$CHUNK_COUNT" = "0" ]; then
        NEEDS_SEED=true
    fi
fi

if [ "$NEEDS_SEED" = "true" ]; then
    echo "Seeding database at /data/manifest.db..."
    rm -f /data/manifest.db
    EVO_STORE=/data uv run python scripts/seed.py
    echo "Seed complete."
fi

# Start FastAPI server
exec uv run uvicorn server:app --host 0.0.0.0 --port "${PORT:-8765}"
