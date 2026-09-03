FROM python:3.12-slim AS base

WORKDIR /app

# System deps for sqlite-vec
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --no-dev --frozen

# Pre-download fastembed model at build time (cached in image)
RUN uv run python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

# App code
COPY core/ core/
COPY server/ server/
COPY scripts/ scripts/

# Entrypoint seeds DB on first run if missing
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV EVO_STORE=/data
ENV PORT=8765

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8765/health'); exit(0 if r.status_code == 200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
