"""
Admin Observability Dashboard — Phase 6
========================================
Streamlit app serving the internal Admin panel for the Asteroid Hazard Classifier.

Panels:
  1. Registry Metrics  — @champion model recall, F1, ROC-AUC from MLflow
  2. Live Logs         — tail of /tmp/asteroid_api.log with level filtering

Run standalone (local):
    streamlit run src/asteroid_classifier/ui/dashboard.py

In-container:
    Launched in the background by entrypoint.sh on port 8501.
    Access via: http://<space-url>:8501

Standards:
    - No secrets hardcoded — reads from environment variables only
    - get_logger() from core/logging.py for all internal logging
    - MlflowClient for registry queries; never loads the model artifact itself
    - Uses st.cache_data for registry calls (60-second TTL) to avoid hammering DagsHub
"""

import os
import time
from pathlib import Path
from typing import Optional

import dagshub
import mlflow
import streamlit as st
from mlflow.tracking import MlflowClient

from asteroid_classifier.core.logging import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_NAME: str = "asteroid-hazard-classifier"
CHAMPION_ALIAS: str = "champion"
LOG_FILE_PATH: Path = Path("/tmp/asteroid_api.log")
LOG_TAIL_LINES: int = 200
REGISTRY_CACHE_TTL: int = 60  # seconds

# Promotion thresholds (mirror of evaluator.py — display-only, no logic)
THRESHOLD_RECALL: float = 0.90
THRESHOLD_F1: float = 0.85
THRESHOLD_ROC_AUC: float = 0.92


# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Asteroid Classifier — Admin Dashboard",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Custom CSS — minimal, functional dark styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; }
    .metric-card {
        background: #1c2333;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        border-left: 4px solid;
    }
    .metric-pass  { border-color: #00d084; }
    .metric-fail  { border-color: #ff4b4b; }
    .metric-label { font-size: 0.82rem; color: #9aa0ad; margin-bottom: 4px; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #f0f0f0; }
    .metric-threshold { font-size: 0.75rem; color: #6b7280; margin-top: 4px; }
    .log-area {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.78rem;
        max-height: 480px;
        overflow-y: auto;
        white-space: pre-wrap;
        color: #cdd5df;
    }
    .log-error   { color: #ff6b6b; }
    .log-warning { color: #ffd93d; }
    .log-info    { color: #6bcfff; }
    .log-debug   { color: #9aa0ad; }
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-running { background: #1a4731; color: #00d084; }
    .badge-error   { background: #4a1c1c; color: #ff4b4b; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# MLflow / DagsHub initialisation
# ---------------------------------------------------------------------------
def _init_mlflow() -> bool:
    """
    Initialise DagsHub + MLflow from environment variables.
    Returns True on success, False if any required env var is missing.
    """
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER")
    repo_name = os.getenv("DAGSHUB_REPO_NAME")
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    if not all([repo_owner, repo_name, tracking_uri]):
        logger.warning(
            "Dashboard: one or more MLflow env vars missing "
            "(DAGSHUB_REPO_OWNER / DAGSHUB_REPO_NAME / MLFLOW_TRACKING_URI)"
        )
        return False

    try:
        dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"Dashboard: MLflow initialised — tracking URI: {tracking_uri}")
        return True
    except Exception as exc:
        logger.error(f"Dashboard: DagsHub/MLflow init failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Registry data fetching (cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=REGISTRY_CACHE_TTL, show_spinner=False)
def fetch_champion_metrics() -> Optional[dict]:
    """
    Pulls test_recall, test_f1, and test_roc_auc for the @champion model
    from the MLflow Model Registry via MlflowClient.

    Returns a dict of metric values, or None on failure.
    Cached for REGISTRY_CACHE_TTL seconds to avoid hammering DagsHub.
    """
    try:
        client = MlflowClient()

        # Resolve @champion alias → model version
        model_version = client.get_model_version_by_alias(
            name=MODEL_NAME,
            alias=CHAMPION_ALIAS,
        )
        run_id: str = model_version.run_id
        version: str = model_version.version
        logger.info(
            f"Dashboard: fetched @champion → version {version}, run_id {run_id}"
        )

        # Pull the full run to get metrics
        run = client.get_run(run_id)
        metrics = run.data.metrics
        params = run.data.params

        return {
            "version": version,
            "run_id": run_id,
            "recall": metrics.get("test_recall", metrics.get("recall")),
            "f1": metrics.get("test_f1", metrics.get("f1")),
            "roc_auc": metrics.get("test_roc_auc", metrics.get("roc_auc")),
            "dvc_hash": params.get("data_dvc_hash", "—"),
            "model_name": MODEL_NAME,
        }
    except Exception as exc:
        logger.error(f"Dashboard: failed to fetch @champion metrics: {exc}")
        return None


# ---------------------------------------------------------------------------
# Log reader
# ---------------------------------------------------------------------------
def read_log_tail(
    log_path: Path, n_lines: int, level_filter: str
) -> list[str]:
    """
    Reads the last `n_lines` entries from the Loguru log sink file.
    Filters by log level keyword if a filter is specified.

    Returns an empty list if the file does not exist yet.
    """
    if not log_path.exists():
        return []

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            all_lines = fh.readlines()

        # Most recent lines first
        lines = list(reversed(all_lines[-n_lines:]))

        if level_filter and level_filter != "ALL":
            lines = [ln for ln in lines if f"| {level_filter}" in ln]

        return lines
    except OSError as exc:
        logger.error(f"Dashboard: could not read log file {log_path}: {exc}")
        return []


def _colorise_log_line(line: str) -> str:
    """Wraps a log line in an HTML span with colour based on level."""
    if "| ERROR" in line or "| CRITICAL" in line:
        return f'<span class="log-error">{line}</span>'
    if "| WARNING" in line:
        return f'<span class="log-warning">{line}</span>'
    if "| INFO" in line:
        return f'<span class="log-info">{line}</span>'
    return f'<span class="log-debug">{line}</span>'


# ---------------------------------------------------------------------------
# Metric card helper
# ---------------------------------------------------------------------------
def _metric_card(
    label: str,
    value: Optional[float],
    threshold: float,
    fmt: str = ".4f",
) -> str:
    """Returns an HTML metric card string. Pass/fail colouring vs threshold."""
    if value is None:
        css_class = "metric-fail"
        display = "N/A"
    else:
        passes = value >= threshold
        css_class = "metric-pass" if passes else "metric-fail"
        display = f"{value:{fmt}}"

    return (
        f'<div class="metric-card {css_class}">'
        f'  <div class="metric-label">{label}</div>'
        f'  <div class="metric-value">{display}</div>'
        f'  <div class="metric-threshold">Threshold ≥ {threshold}</div>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Dashboard layout
# ---------------------------------------------------------------------------
def render_header() -> None:
    col_title, col_badge = st.columns([5, 1])
    with col_title:
        st.markdown("## ☄️ Asteroid Hazard Classifier — Admin Dashboard")
        st.markdown(
            "<span style='color:#6b7280;font-size:0.85rem;'>"
            "Internal observability panel · Phase 6"
            "</span>",
            unsafe_allow_html=True,
        )
    with col_badge:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<span class="status-badge badge-running">● LIVE</span>',
            unsafe_allow_html=True,
        )
    st.divider()


def render_registry_panel(mlflow_ready: bool) -> None:
    """Panel 1 — @champion model metrics from the MLflow Registry."""
    st.markdown("### 🏆 Model Registry — @champion")

    if not mlflow_ready:
        st.warning(
            "MLflow environment variables not configured. "
            "Set `DAGSHUB_REPO_OWNER`, `DAGSHUB_REPO_NAME`, and "
            "`MLFLOW_TRACKING_URI` to enable registry metrics.",
            icon="⚠️",
        )
        return

    with st.spinner("Fetching @champion metrics from DagsHub..."):
        data = fetch_champion_metrics()

    if data is None:
        st.error(
            "Could not fetch @champion model data from the MLflow Registry. "
            "Check the container logs for details.",
            icon="🔴",
        )
        return

    # Model version badge
    col_ver, col_run = st.columns(2)
    with col_ver:
        st.info(
            f"**Model version:** `{data['version']}`  \n"
            f"**Registered name:** `{data['model_name']}`",
            icon="📌",
        )
    with col_run:
        st.info(
            f"**MLflow run:** `{data['run_id'][:12]}…`  \n"
            f"**DVC data hash:** `{data['dvc_hash']}`",
            icon="🔗",
        )

    # Metric cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            _metric_card("Recall (test)", data["recall"], THRESHOLD_RECALL),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _metric_card("F1 Score (test)", data["f1"], THRESHOLD_F1),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _metric_card("ROC-AUC (test)", data["roc_auc"], THRESHOLD_ROC_AUC),
            unsafe_allow_html=True,
        )

    st.caption(
        f"Metrics cached for {REGISTRY_CACHE_TTL}s · "
        f"Last refreshed: {time.strftime('%H:%M:%S UTC', time.gmtime())}"
    )


def render_logs_panel() -> None:
    """Panel 2 — Live tail of the Loguru file sink."""
    st.markdown("### 📋 Live Logs")

    col_filter, col_lines, col_refresh = st.columns([2, 2, 1])
    with col_filter:
        level_filter: str = st.selectbox(
            "Filter by level",
            options=["ALL", "INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
            index=0,
            label_visibility="collapsed",
        )
    with col_lines:
        n_lines: int = st.slider(
            "Lines to display",
            min_value=20,
            max_value=500,
            value=LOG_TAIL_LINES,
            step=20,
            label_visibility="collapsed",
        )
    with col_refresh:
        do_refresh = st.button("🔄 Refresh", use_container_width=True)

    # Auto-refresh every 10 seconds when the user toggles it
    auto_refresh: bool = st.toggle("Auto-refresh (10 s)", value=False)
    if auto_refresh:
        time.sleep(10)
        st.rerun()

    if do_refresh:
        st.cache_data.clear()

    if not LOG_FILE_PATH.exists():
        st.info(
            f"Log file `{LOG_FILE_PATH}` does not exist yet. "
            "It will appear once the API has processed at least one request.",
            icon="ℹ️",
        )
        return

    lines = read_log_tail(LOG_FILE_PATH, n_lines, level_filter)

    if not lines:
        st.info("No log entries match the current filter.", icon="ℹ️")
        return

    colourised = "".join(_colorise_log_line(ln) for ln in lines)
    st.markdown(
        f'<div class="log-area">{colourised}</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Showing last {len(lines)} entries from `{LOG_FILE_PATH}` "
        f"(newest first) · Filter: {level_filter}"
    )


def main() -> None:
    """Entry point — renders all dashboard panels in sequence."""
    logger.info("Streamlit admin dashboard: page render started")

    render_header()

    mlflow_ready = _init_mlflow()

    render_registry_panel(mlflow_ready)

    st.divider()

    render_logs_panel()

    logger.info("Streamlit admin dashboard: page render complete")


if __name__ == "__main__":
    main()
