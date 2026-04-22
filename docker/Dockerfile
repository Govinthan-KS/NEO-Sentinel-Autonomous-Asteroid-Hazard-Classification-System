# =============================================================================
# Asteroid Hazard Classifier — Production Dockerfile
# Base: python:3.12-slim (minimal, secure)
# Port: 7860 (HuggingFace Spaces default)
# =============================================================================

FROM python:3.12-slim

# ---------------------------------------------------------------------------
# Environment
# PYTHONPATH    — enables `import asteroid_classifier.*` without pip install -e
# POETRY_*      — install deps directly into system Python (no virtualenv in container)
# PYTHONUNBUFFERED — real-time Loguru log streaming in Docker logs
# ---------------------------------------------------------------------------
ENV PYTHONPATH=/app/src \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---------------------------------------------------------------------------
# System dependencies (minimal — only what slim removes that we need)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Layer 1: Install Poetry
# Pinned via pip to avoid upstream version drift
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir "poetry>=1.8.0,<3.0.0"

# ---------------------------------------------------------------------------
# Layer 2: Install Python dependencies
# Copy ONLY pyproject.toml + poetry.lock first — this layer is cached
# unless dependencies actually change. Source code changes don't bust it.
# ---------------------------------------------------------------------------
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main

# ---------------------------------------------------------------------------
# Layer 3: Application source (Layered Architecture compliance)
# src/   — all Python modules
# configs/ — Hydra YAML configs (no hardcoding in source)
# ---------------------------------------------------------------------------
COPY src/ ./src/
COPY configs/ ./configs/

# ---------------------------------------------------------------------------
# Layer 4: Entrypoint script
# Performs secret validation before handing off to Uvicorn
# ---------------------------------------------------------------------------
COPY docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
EXPOSE 7860

ENTRYPOINT ["./entrypoint.sh"]
