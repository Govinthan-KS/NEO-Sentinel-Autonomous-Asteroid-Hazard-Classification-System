#!/bin/sh
# =============================================================================
# NEO-Sentinel — Container Entrypoint
# =============================================================================
# Start order:
#   1. Validate all required environment variables (hard exit on any missing)
#   2. Streamlit admin dashboard   → background (port 8501)
#   3. Uvicorn / FastAPI           → foreground via exec (receives SIGTERM)
#
# Pipeline triggering is handled via GitHub Actions workflow_dispatch —
# no in-container bot process required.
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# 1. Required Environment Variable Validation
# ---------------------------------------------------------------------------
REQUIRED_VARS="NASA_API_KEY DAGSHUB_TOKEN MLFLOW_TRACKING_URI DAGSHUB_REPO_OWNER DAGSHUB_REPO_NAME DATABASE_URL"

echo "[NEO-Sentinel] Validating required environment variables..."

for VAR in $REQUIRED_VARS; do
    eval VALUE=\$$VAR
    if [ -z "$VALUE" ]; then
        echo "[NEO-Sentinel][CRITICAL] Required environment variable '${VAR}' is not set or is empty."
        echo "[NEO-Sentinel][CRITICAL] Startup aborted. Set all required vars in HuggingFace Spaces → Settings → Repository Secrets."
        exit 1
    fi
done

echo "[NEO-Sentinel] All required environment variables validated successfully."
echo "[NEO-Sentinel] DAGSHUB_REPO_OWNER=${DAGSHUB_REPO_OWNER}"
echo "[NEO-Sentinel] DAGSHUB_REPO_NAME=${DAGSHUB_REPO_NAME}"
echo "[NEO-Sentinel] MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}"

# ---------------------------------------------------------------------------
# 2. [REMOVED] Streamlit Admin Observability Dashboard
# ---------------------------------------------------------------------------
# Streamlit has been removed. Uvicorn handles all traffic on port 7860.


# ---------------------------------------------------------------------------
# 3. Uvicorn — Primary ASGI Server (foreground)
# ---------------------------------------------------------------------------
echo "[NEO-Sentinel] Starting Uvicorn on 0.0.0.0:7860..."
exec uvicorn asteroid_classifier.api.main:app \
    --host 0.0.0.0 \
    --port 7860 \
    --log-level info
