#!/bin/sh
# =============================================================================
# Asteroid Hazard Classifier — Container Entrypoint
# Validates required environment variables, then starts the Uvicorn server.
# POSIX sh (not bash) for maximum compatibility across slim base images.
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Required Environment Variable Validation
# All five vars must be present and non-empty before startup proceeds.
# Missing any one of them will cause a hard exit(1) with a clear message —
# never a silent failure buried in an MLflow or DagsHub traceback.
# ---------------------------------------------------------------------------
REQUIRED_VARS="NASA_API_KEY DAGSHUB_TOKEN MLFLOW_TRACKING_URI DAGSHUB_REPO_OWNER DAGSHUB_REPO_NAME"

echo "[INFO] Validating required environment variables..."

for VAR in $REQUIRED_VARS; do
    # POSIX-compatible indirect variable reference
    eval VALUE=\$$VAR
    if [ -z "$VALUE" ]; then
        echo "[CRITICAL] Required environment variable '${VAR}' is not set or is empty."
        echo "[CRITICAL] Startup aborted. Set all required vars in HuggingFace Spaces → Settings → Variables."
        exit 1
    fi
done

echo "[INFO] All 5 required environment variables validated successfully."
echo "[INFO] DAGSHUB_REPO_OWNER=${DAGSHUB_REPO_OWNER}"
echo "[INFO] DAGSHUB_REPO_NAME=${DAGSHUB_REPO_NAME}"
echo "[INFO] MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}"
echo "[INFO] Starting Uvicorn server on 0.0.0.0:7860..."

# ---------------------------------------------------------------------------
# Stage 8 (Future) — Streamlit Admin Observability Dashboard
# Uncomment once src/asteroid_classifier/ui/dashboard.py is production-ready.
# The dashboard will be accessible on port 8501 within the same container.
# ---------------------------------------------------------------------------
# streamlit run /app/src/asteroid_classifier/ui/dashboard.py \
#     --server.port 8501 \
#     --server.headless true \
#     --server.address 0.0.0.0 &

# ---------------------------------------------------------------------------
# Primary Server — Uvicorn (ASGI)
# `exec` replaces the shell process so Uvicorn receives OS signals directly
# (SIGTERM/SIGINT for graceful shutdown — critical for HF Spaces lifecycle).
# ---------------------------------------------------------------------------
exec uvicorn asteroid_classifier.api.main:app \
    --host 0.0.0.0 \
    --port 7860 \
    --log-level info
