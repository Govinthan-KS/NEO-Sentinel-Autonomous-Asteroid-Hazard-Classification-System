#!/bin/sh
# =============================================================================
# NEO-Sentinel — Container Entrypoint
# Validates required environment variables, then starts the serving layer.
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

echo "[NEO-Sentinel] Validating required environment variables..."

for VAR in $REQUIRED_VARS; do
    # POSIX-compatible indirect variable reference
    eval VALUE=\$$VAR
    if [ -z "$VALUE" ]; then
        echo "[NEO-Sentinel][CRITICAL] Required environment variable '${VAR}' is not set or is empty."
        echo "[NEO-Sentinel][CRITICAL] Startup aborted. Set all required vars in HuggingFace Spaces → Settings → Variables."
        exit 1
    fi
done

echo "[NEO-Sentinel] All 5 required environment variables validated successfully."
echo "[NEO-Sentinel] DAGSHUB_REPO_OWNER=${DAGSHUB_REPO_OWNER}"
echo "[NEO-Sentinel] DAGSHUB_REPO_NAME=${DAGSHUB_REPO_NAME}"
echo "[NEO-Sentinel] MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}"
echo "[NEO-Sentinel] Starting prediction API on 0.0.0.0:7860 and admin dashboard on 0.0.0.0:8501..."

# ---------------------------------------------------------------------------
# Phase 6 — Streamlit Admin Observability Dashboard
# Runs in the background on port 8501 alongside Uvicorn.
# Access: http://<space-url>:8501
# Reads @champion metrics from MLflow Registry and tails /tmp/asteroid_api.log.
# ---------------------------------------------------------------------------
streamlit run /app/src/asteroid_classifier/ui/dashboard.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "[NEO-Sentinel] Streamlit Admin Dashboard started in background (PID: ${STREAMLIT_PID}, port: 8501)."
echo "[NEO-Sentinel] Note: port 8501 is not externally accessible in HuggingFace Spaces; monitor via this log."

# ---------------------------------------------------------------------------
# Primary Server — Uvicorn (ASGI)
# `exec` replaces the shell process so Uvicorn receives OS signals directly
# (SIGTERM/SIGINT for graceful shutdown — critical for HF Spaces lifecycle).
# ---------------------------------------------------------------------------
exec uvicorn asteroid_classifier.api.main:app \
    --host 0.0.0.0 \
    --port 7860 \
    --log-level info
