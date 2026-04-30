"""
NEO-Sentinel Admin Dashboard
=============================
Streamlit admin panel for the NEO-Sentinel Autonomous Asteroid Hazard
Classification System.

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
os.environ["DAGSHUB_NON_INTERACTIVE"] = "1"
_hf_token = os.environ.get("DAGSHUB_TOKEN", "")
if _hf_token:
    os.environ["DAGSHUB_USER_TOKEN"] = _hf_token

import time
import json
import subprocess
import threading
from pathlib import Path
from typing import Optional
import streamlit.components.v1 as components

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
REGISTRY_CACHE_TTL: int = 60   # seconds
LEADERBOARD_CACHE_TTL: int = 120  # seconds — leaderboard is less time-sensitive

THRESHOLD_RECALL: float    = 0.90
THRESHOLD_PRECISION: float = 0.70
THRESHOLD_F1: float        = 0.85
THRESHOLD_ROC_AUC: float   = 0.92


# ---------------------------------------------------------------------------
# Page configuration (must be the very first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NEO-Sentinel Admin",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Sea-themed CSS design system
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global canvas ── */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(160deg, #03111f 0%, #041e33 40%, #062c4a 75%, #04223c 100%);
        font-family: 'Inter', sans-serif;
        color: #d6eaf8;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #031525; }

    /* ── Subtle animated ocean shimmer on the page ── */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse 80% 40% at 20% 80%, rgba(0,168,232,0.04) 0%, transparent 60%),
            radial-gradient(ellipse 60% 30% at 80% 20%, rgba(0,210,200,0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Hero header bar ── */
    .neo-header {
        background: linear-gradient(135deg, rgba(0,90,160,0.55) 0%, rgba(0,160,200,0.35) 100%);
        border: 1px solid rgba(0,180,220,0.25);
        border-radius: 14px;
        padding: 1.6rem 2.2rem;
        margin-bottom: 1.4rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 32px rgba(0,120,200,0.18), inset 0 1px 0 rgba(255,255,255,0.06);
    }
    .neo-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        color: #e8f4fd;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .neo-header p {
        font-size: 0.85rem;
        color: #7ec8e3;
        margin: 0;
        font-weight: 400;
    }

    /* ── Live status pill ── */
    .status-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0,210,100,0.12);
        border: 1px solid rgba(0,210,100,0.35);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #00d084;
        letter-spacing: 0.5px;
    }
    .status-dot {
        width: 7px; height: 7px;
        background: #00d084;
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
        display: inline-block;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.4; transform: scale(0.7); }
    }

    /* ── Nav button ── */
    .nav-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0,100,160,0.28);
        border: 1px solid rgba(0,160,210,0.3);
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 0.80rem;
        font-weight: 600;
        color: #7ec8e3 !important;
        text-decoration: none !important;
        transition: background 0.2s, border-color 0.2s;
        white-space: nowrap;
    }
    .nav-btn:hover {
        background: rgba(0,130,190,0.4);
        border-color: rgba(0,180,220,0.5);
        color: #b8e4f4 !important;
    }

    /* ── Section cards ── */
    .panel-card {
        background: rgba(4, 30, 54, 0.72);
        border: 1px solid rgba(0, 160, 210, 0.18);
        border-radius: 12px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 20px rgba(0,80,160,0.15);
    }

    /* ── Section titles ── */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #7ec8e3;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 1.1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(0,160,210,0.4) 0%, transparent 100%);
        margin-left: 8px;
    }

    /* ── Metric cards ── */
    .metric-grid { display: flex; gap: 1rem; margin-top: 0.8rem; }
    .metric-tile {
        flex: 1;
        background: rgba(3, 20, 40, 0.75);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        border-top: 3px solid;
        position: relative;
        overflow: hidden;
    }
    .metric-tile::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(180deg, rgba(0,160,210,0.04) 0%, transparent 60%);
        pointer-events: none;
    }
    .metric-tile.pass { border-color: #00c896; }
    .metric-tile.fail { border-color: #e05252; }
    .metric-tile.none { border-color: #4a6070; }
    .metric-label {
        font-size: 0.72rem;
        color: #7ba0b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #e8f4fd;
        line-height: 1;
        margin-bottom: 0.4rem;
    }
    .metric-value.pass { color: #00d884; }
    .metric-value.fail { color: #f07070; }
    .metric-threshold {
        font-size: 0.72rem;
        color: #4a6878;
        font-weight: 500;
    }
    .metric-badge {
        position: absolute;
        top: 0.8rem; right: 0.9rem;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.6px;
        padding: 2px 8px;
        border-radius: 10px;
    }
    .badge-pass { background: rgba(0,200,150,0.15); color: #00d884; }
    .badge-fail { background: rgba(220,80,80,0.15); color: #f07070; }

    /* ── Info row chips ── */
    .info-chip {
        display: inline-block;
        background: rgba(0,100,160,0.25);
        border: 1px solid rgba(0,160,210,0.2);
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 0.78rem;
        color: #a8d8ea;
        font-family: 'Courier New', monospace;
        margin-right: 8px;
        margin-bottom: 6px;
    }

    /* ── Divider ── */
    .sea-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(0,160,210,0.3) 30%, rgba(0,200,200,0.3) 70%, transparent 100%);
        margin: 1.6rem 0;
    }

    /* ── Log viewer ── */
    .log-container {
        background: rgba(2, 12, 24, 0.88);
        border: 1px solid rgba(0, 130, 180, 0.2);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        font-family: 'Courier New', monospace;
        font-size: 0.76rem;
        max-height: 440px;
        overflow-y: auto;
        line-height: 1.7;
        letter-spacing: 0.01em;
        scrollbar-width: thin;
        scrollbar-color: rgba(0,160,210,0.3) transparent;
    }
    .log-container::-webkit-scrollbar { width: 5px; }
    .log-container::-webkit-scrollbar-thumb { background: rgba(0,160,210,0.3); border-radius: 3px; }
    .log-line { white-space: pre-wrap; word-break: break-all; padding: 1px 0; }
    .log-error    { color: #f07070; }
    .log-critical { color: #ff4444; font-weight: 700; }
    .log-warning  { color: #f5c842; }
    .log-info     { color: #7ec8e3; }
    .log-debug    { color: #4a6878; }

    /* ── Controls strip ── */
    .stSelectbox > div > div,
    .stSlider > div { color: #a8d8ea !important; }
    button[kind="primary"] {
        background: linear-gradient(135deg, #005a9e, #007bbd) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #e8f4fd !important;
        font-weight: 600 !important;
    }
    button[kind="secondary"] {
        background: rgba(0,100,160,0.2) !important;
        border: 1px solid rgba(0,160,210,0.25) !important;
        border-radius: 8px !important;
        color: #7ec8e3 !important;
    }

    /* ── Footer ── */
    .neo-footer {
        text-align: center;
        color: #2a4a60;
        font-size: 0.73rem;
        padding: 1.2rem 0 0.4rem;
        letter-spacing: 0.3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# MLflow / DagsHub initialisation
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
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
        # Re-apply the auth override right before init, just like in main.py
        os.environ["DAGSHUB_NON_INTERACTIVE"] = "1"
        token = os.getenv("DAGSHUB_TOKEN")
        if token:
            os.environ["DAGSHUB_USER_TOKEN"] = token
            
        dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
        mlflow.set_tracking_uri(tracking_uri)
        logger.info("Dashboard: MLflow initialised.")
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
    Cached for REGISTRY_CACHE_TTL seconds.
    """
    try:
        client = MlflowClient()
        model_version = client.get_model_version_by_alias(
            name=MODEL_NAME,
            alias=CHAMPION_ALIAS,
        )
        run_id: str = model_version.run_id
        version: str = model_version.version
        logger.info(f"Dashboard: resolved @champion → version {version}, run_id {run_id}")

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
# Leaderboard data fetching (cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=LEADERBOARD_CACHE_TTL, show_spinner=False)
def fetch_leaderboard_runs(max_runs: int = 15) -> list:
    """
    Fetches the latest MLflow runs from the asteroid-hazard-classification
    experiment, extracts algorithm label and key metrics, and annotates
    the current @champion run.

    Returns a list of dicts ordered by start_time DESC.
    """
    try:
        client = MlflowClient()

        # Resolve current @champion run_id for badge annotation
        champion_run_id: str = ""
        try:
            mv = client.get_model_version_by_alias(
                name=MODEL_NAME, alias=CHAMPION_ALIAS
            )
            champion_run_id = mv.run_id
        except Exception:
            pass

        experiment = client.get_experiment_by_name("asteroid-hazard-classification")
        if not experiment:
            return []

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.run_type = 'child'",   # exclude parent Battle-Royale wrapper
            order_by=["start_time DESC"],
            max_results=max_runs,
        )

        rows = []
        for run in runs:
            m = run.data.metrics
            p = run.data.params
            recall    = m.get("test_recall",     m.get("recall"))
            precision = m.get("test_precision",  m.get("precision"))
            f1        = m.get("test_f1",         m.get("f1"))
            roc_auc   = m.get("test_roc_auc",   m.get("roc_auc"))
            display_name = run.info.run_name
            ts = run.info.start_time
            run_date = (
                __import__("datetime").datetime
                .fromtimestamp(ts / 1000.0, tz=__import__("datetime").timezone.utc)
                .strftime("%Y-%m-%d %H:%M")
                if ts else "—"
            )
            rows.append({
                "run_id":       run.info.run_id,
                "display_name": display_name,
                "recall":       recall,
                "precision":    precision,
                "f1":           f1,
                "roc_auc":      roc_auc,
                "run_date":     run_date,
                "is_champion":  run.info.run_id == champion_run_id,
            })
        return rows
    except Exception as exc:
        logger.error(f"Dashboard: leaderboard fetch failed: {exc}")
        return []


def _metric_cell(value: Optional[float], threshold: float) -> str:
    """Returns an HTML table cell coloured by pass/fail vs threshold."""
    if value is None:
        return '<td style="color:#4a6878;text-align:center;">N/A</td>'
    passes = value >= threshold
    colour = "#00d884" if passes else "#f07070"
    bg = "rgba(0,200,100,0.08)" if passes else "rgba(220,80,80,0.08)"
    return (
        f'<td style="text-align:center;color:{colour};'
        f'background:{bg};font-weight:600;">{value:.4f}</td>'
    )


def render_leaderboard_panel(mlflow_ready: bool) -> None:
    """Panel 2 — Multi-model run leaderboard from the MLflow experiment."""
    st.markdown(
        '<div class="section-title">📊 &nbsp; Model Leaderboard</div>',
        unsafe_allow_html=True,
    )

    if not mlflow_ready:
        st.info("Configure MLflow environment variables to enable the leaderboard.", icon="ℹ️")
        return

    with st.spinner("Loading leaderboard from MLflow experiment…"):
        rows = fetch_leaderboard_runs()

    if not rows:
        st.info("No runs found in the 'asteroid-hazard-classification' experiment yet.", icon="🌊")
        return

    # Build HTML table
    header = (
        '<table style="width:100%;border-collapse:collapse;'
        'font-family:Inter,sans-serif;font-size:0.80rem;">'
        "<thead><tr style='"
        "background:rgba(0,80,130,0.4);"
        "color:#7ec8e3;text-transform:uppercase;letter-spacing:0.7px;"
        "border-bottom:1px solid rgba(0,160,210,0.3);"
        "'>"
        "<th style='padding:8px 10px;text-align:left;'>Rank</th>"
        "<th style='padding:8px 10px;text-align:left;'>Algorithm</th>"
        "<th style='padding:8px 10px;text-align:center;'>Recall</th>"
        "<th style='padding:8px 10px;text-align:center;'>Precision</th>"
        "<th style='padding:8px 10px;text-align:center;'>F1 Score</th>"
        "<th style='padding:8px 10px;text-align:center;'>ROC-AUC</th>"
        "<th style='padding:8px 10px;text-align:left;'>Run Date (UTC)</th>"
        "</tr></thead><tbody>"
    )

    body_rows = []
    for i, row in enumerate(rows, start=1):
        champ_badge = (
            ' <span style="background:rgba(255,200,0,0.15);'
            'color:#ffd700;border:1px solid rgba(255,200,0,0.3);'
            'border-radius:10px;padding:1px 7px;font-size:0.68rem;""">🏆 champion</span>'
            if row["is_champion"] else ""
        )
        row_bg = "rgba(255,200,0,0.04)" if row["is_champion"] else (
            "rgba(4,30,54,0.6)" if i % 2 == 0 else "rgba(3,20,40,0.4)"
        )
        rank_cell = (
            f'<td style="padding:7px 10px;color:#7ec8e3;font-weight:600;">#{i}</td>'
        )
        name_cell = (
            f'<td style="padding:7px 10px;color:#e8f4fd;">{row["display_name"]}{champ_badge}</td>'
        )
        date_cell = (
            f'<td style="padding:7px 10px;color:#4a7080;">{row["run_date"]}</td>'
        )
        body_rows.append(
            f'<tr style="background:{row_bg};border-bottom:1px solid rgba(0,100,150,0.12);">'
            f"{rank_cell}{name_cell}"
            f"{_metric_cell(row['recall'],    THRESHOLD_RECALL)}"
            f"{_metric_cell(row['precision'], THRESHOLD_PRECISION)}"
            f"{_metric_cell(row['f1'],        THRESHOLD_F1)}"
            f"{_metric_cell(row['roc_auc'],   THRESHOLD_ROC_AUC)}"
            f"{date_cell}"
            f"</tr>"
        )

    footer = "</tbody></table>"
    st.markdown(
        f'<div style="overflow-x:auto;border-radius:10px;'
        f'border:1px solid rgba(0,160,210,0.15);'
        f'background:rgba(3,20,40,0.6);padding:0;">'
        f"{header}{''.join(body_rows)}{footer}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Latest {len(rows)} runs · thresholds: "
        f"recall≥{THRESHOLD_RECALL}, precision≥{THRESHOLD_PRECISION}, "
        f"f1≥{THRESHOLD_F1}, roc_auc≥{THRESHOLD_ROC_AUC} · "
        f"cache TTL: {LEADERBOARD_CACHE_TTL}s"
    )


# ---------------------------------------------------------------------------
# Log reader
# ---------------------------------------------------------------------------
def read_log_tail(log_path: Path, n_lines: int, level_filter: str) -> list[str]:
    """Reads the last `n_lines` from the Loguru sink, newest first, optionally filtered."""
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            all_lines = fh.readlines()
        lines = list(reversed(all_lines[-n_lines:]))
        if level_filter and level_filter != "ALL":
            lines = [ln for ln in lines if f"| {level_filter}" in ln]
        return lines
    except OSError as exc:
        logger.error(f"Dashboard: could not read log file {log_path}: {exc}")
        return []


def _colorise(line: str) -> str:
    """Wraps a log line in a coloured span."""
    s = line.replace("<", "&lt;").replace(">", "&gt;")
    if "| CRITICAL" in s:
        return f'<div class="log-line log-critical">{s}</div>'
    if "| ERROR" in s:
        return f'<div class="log-line log-error">{s}</div>'
    if "| WARNING" in s:
        return f'<div class="log-line log-warning">{s}</div>'
    if "| INFO" in s:
        return f'<div class="log-line log-info">{s}</div>'
    return f'<div class="log-line log-debug">{s}</div>'


# ---------------------------------------------------------------------------
# Metric tile builder
# ---------------------------------------------------------------------------
def _metric_tile(label: str, value: Optional[float], threshold: float) -> str:
    if value is None:
        css = "none"
        display = "N / A"
        badge = ""
    else:
        passes = value >= threshold
        css = "pass" if passes else "fail"
        display = f"{value:.4f}"
        badge_text = "PASS" if passes else "FAIL"
        badge_css = "badge-pass" if passes else "badge-fail"
        badge = f'<span class="metric-badge {badge_css}">{badge_text}</span>'

    return (
        f'<div class="metric-tile {css}">'
        f'  {badge}'
        f'  <div class="metric-label">{label}</div>'
        f'  <div class="metric-value {css}">{display}</div>'
        f'  <div class="metric-threshold">Threshold ≥ {threshold}</div>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------
def render_header() -> None:
    col_main, col_nav, col_status = st.columns([5, 1, 1])
    with col_main:
        st.markdown(
            """
            <div class="neo-header">
                <h1>☄️ NEO-Sentinel &mdash; Admin Dashboard</h1>
                <p>Autonomous Asteroid Hazard Classification System &nbsp;·&nbsp; Internal Observability Panel</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_nav:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Opens the Gradio prediction UI — same host, path /ui (served by FastAPI on port 7860)
        st.markdown(
            '<a class="nav-btn" href="http://localhost:7860/ui" target="_blank">'
            "⚡ &nbsp; Prediction Portal"
            "</a>",
            unsafe_allow_html=True,
        )
    with col_status:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            '<span class="status-live"><span class="status-dot"></span>LIVE</span>',
            unsafe_allow_html=True,
        )


def render_registry_panel(mlflow_ready: bool) -> None:
    """Panel 1 — @champion model metrics from the MLflow Registry."""
    st.markdown(
        '<div class="section-title">🏆 &nbsp; Active Champion Model</div>',
        unsafe_allow_html=True,
    )

    if not mlflow_ready:
        st.warning(
            "MLflow environment variables are not configured. "
            "Set `DAGSHUB_REPO_OWNER`, `DAGSHUB_REPO_NAME`, and `MLFLOW_TRACKING_URI` "
            "to enable registry metrics.",
            icon="⚠️",
        )
        return

    with st.spinner("Fetching @champion from DagsHub registry…"):
        data = fetch_champion_metrics()

    if data is None:
        st.error(
            "Could not retrieve @champion metrics from the MLflow Registry. "
            "Check the container logs for details.",
            icon="🔴",
        )
        return

    # Identity chips
    st.markdown(
        f'<div style="margin-bottom:1rem;">'
        f'  <span class="info-chip">Model: {data["model_name"]}</span>'
        f'  <span class="info-chip">Version: v{data["version"]}</span>'
        f'  <span class="info-chip">Run: {data["run_id"][:10]}…</span>'
        f'  <span class="info-chip">DVC: {data["dvc_hash"]}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Metric tiles
    st.markdown(
        f'<div class="metric-grid">'
        f'{_metric_tile("Recall", data["recall"], THRESHOLD_RECALL)}'
        f'{_metric_tile("F1 Score", data["f1"], THRESHOLD_F1)}'
        f'{_metric_tile("ROC-AUC", data["roc_auc"], THRESHOLD_ROC_AUC)}'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        f"Registry cache TTL: {REGISTRY_CACHE_TTL}s · "
        f"Refreshed at {time.strftime('%H:%M:%S UTC', time.gmtime())}"
    )


def render_logs_panel() -> None:
    """Panel 2 — Live tail of the Loguru file sink."""
    st.markdown(
        '<div class="section-title">📡 &nbsp; System Event Log</div>',
        unsafe_allow_html=True,
    )

    col_filter, col_lines, col_btn = st.columns([2, 3, 1])
    with col_filter:
        level_filter: str = st.selectbox(
            "Level",
            options=["ALL", "INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
            index=0,
            label_visibility="visible",
        )
    with col_lines:
        n_lines: int = st.slider(
            "Lines",
            min_value=20,
            max_value=500,
            value=LOG_TAIL_LINES,
            step=20,
            label_visibility="visible",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⟳ Refresh", use_container_width=True):
            st.cache_data.clear()

    auto_refresh: bool = st.toggle("Auto-refresh every 10 s", value=False)
    if auto_refresh:
        time.sleep(10)
        st.rerun()

    if not LOG_FILE_PATH.exists():
        st.info(
            f"Log file `{LOG_FILE_PATH}` does not exist yet — "
            "it will populate once the prediction API handles its first request.",
            icon="🌊",
        )
        return

    lines = read_log_tail(LOG_FILE_PATH, n_lines, level_filter)

    if not lines:
        st.info("No log entries match the current filter.", icon="ℹ️")
        return

    html_lines = "".join(_colorise(ln) for ln in lines)
    st.markdown(
        f'<div class="log-container">{html_lines}</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"{len(lines)} entries · `{LOG_FILE_PATH}` · newest first · filter: {level_filter}"
    )


def render_footer() -> None:
    st.markdown(
        '<div class="neo-footer">'
        "NEO-Sentinel &nbsp;·&nbsp; Autonomous Asteroid Hazard Classification System &nbsp;·&nbsp; "
        "Powered by XGBoost · MLflow · DagsHub"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_env_disclaimer() -> None:
    """Displays a subdued production-environment note below the dashboard header."""
    st.markdown(
        """
        <div style="
            background: rgba(0,80,130,0.14);
            border: 1px solid rgba(0,160,210,0.18);
            border-left: 3px solid #0096c7;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 0.78rem;
            color: #7ec8e3;
            margin-bottom: 1rem;
            font-family: 'Inter', sans-serif;
        ">
            ℹ️ &nbsp;<strong style="color:#a8d8ea;">Environment Note:</strong>
            Operating in production mode. Direct navigation to the Prediction Portal
            requires the main service port (7860) to be accessible.
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Renders the full NEO-Sentinel admin dashboard."""
    logger.info("NEO-Sentinel dashboard: render started")

    render_header()
    render_env_disclaimer()

    mlflow_ready = _init_mlflow()

    render_registry_panel(mlflow_ready)

    st.markdown('<div class="sea-divider"></div>', unsafe_allow_html=True)

    render_leaderboard_panel(mlflow_ready)

    st.markdown('<div class="sea-divider"></div>', unsafe_allow_html=True)

    render_logs_panel()

    render_footer()

    logger.info("NEO-Sentinel dashboard: render complete")


if __name__ == "__main__":
    main()
