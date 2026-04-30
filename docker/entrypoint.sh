#!/bin/sh
# =============================================================================
# NEO-Sentinel — Container Entrypoint
# =============================================================================
# Start order:
#   1. Validate all required environment variables (hard exit on any missing)
#   2. Streamlit admin dashboard   → background (port 8501)
#   3. Discord Orchestration Bot   → background watchdog loop (auto-restarts)
#   4. Uvicorn / FastAPI           → foreground via exec (receives SIGTERM)
#
# POSIX sh — no bash-isms; works on python:3.12-slim's /bin/sh (dash).
#
# Design decisions:
#   - `exec uvicorn` at the end: replaces the shell so HuggingFace Spaces
#     sends SIGTERM directly to Uvicorn for graceful shutdown.
#   - Bot runs inside a `while true` watchdog loop so transient Discord
#     disconnects / rate-limits auto-recover without human intervention.
#   - Bot block is wrapped in `set +e` / `set -e` guards so a bad token on
#     first launch does NOT kill the container — it logs and keeps retrying.
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# 1. Required Environment Variable Validation
# ---------------------------------------------------------------------------
# DISCORD_BOT_TOKEN is intentionally optional here — if absent the bot simply
# won't connect, but the API and dashboard still serve traffic normally.
# All five core MLflow / NASA vars are hard-required for API functionality.
REQUIRED_VARS="NASA_API_KEY DAGSHUB_TOKEN MLFLOW_TRACKING_URI DAGSHUB_REPO_OWNER DAGSHUB_REPO_NAME"

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
# 2. Streamlit Admin Observability Dashboard (background, port 8501)
# ---------------------------------------------------------------------------
streamlit run /app/src/asteroid_classifier/ui/dashboard.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "[NEO-Sentinel] Streamlit Admin Dashboard started (PID: ${STREAMLIT_PID}, port: 8501)."
echo "[NEO-Sentinel] Note: port 8501 is not externally accessible on HF Spaces free tier."

# ---------------------------------------------------------------------------
# 3. Discord Orchestration Bot (background watchdog — auto-restart on crash)
# ---------------------------------------------------------------------------
# Guard: only start if DISCORD_BOT_TOKEN is present.
# The watchdog loop runs entirely outside `set -e` so a bot crash never
# propagates to the foreground Uvicorn process.
if [ -n "$DISCORD_BOT_TOKEN" ]; then
    set +e   # disable exit-on-error for the bot block only

    # Watchdog function — restarts the bot after any non-zero exit.
    # 5-second back-off prevents a tight crash-loop hammering Discord's gateway.
    _run_bot_watchdog() {
        while true; do
            echo "[NEO-Sentinel] Discord Bot starting (module mode)..."
            python -m asteroid_classifier.bot.bot
            EXIT_CODE=$?
            echo "[NEO-Sentinel][WARNING] Discord Bot exited with code ${EXIT_CODE}. Restarting in 5 s..."
            sleep 5
        done
    }

    _run_bot_watchdog &
    BOT_WATCHDOG_PID=$!
    echo "[NEO-Sentinel] Discord Bot watchdog started (PID: ${BOT_WATCHDOG_PID})."

    set -e   # re-enable exit-on-error for the rest of the script
else
    echo "[NEO-Sentinel][WARNING] DISCORD_BOT_TOKEN not set — Discord Bot will not start."
    echo "[NEO-Sentinel][WARNING] Set DISCORD_BOT_TOKEN in HF Spaces → Settings → Repository Secrets to enable the bot."
fi

# ---------------------------------------------------------------------------
# 4. Uvicorn — Primary ASGI Server (foreground)
# ---------------------------------------------------------------------------
# `exec` replaces the shell process so Uvicorn becomes PID of this shell.
# HuggingFace Spaces sends SIGTERM to the container's main PID for graceful
# shutdown — exec ensures Uvicorn receives it directly rather than the shell.
echo "[NEO-Sentinel] Starting Uvicorn on 0.0.0.0:7860..."
exec uvicorn asteroid_classifier.api.main:app \
    --host 0.0.0.0 \
    --port 7860 \
    --log-level info
