import sys
from pathlib import Path
from loguru import logger

# Remove default logger
logger.remove()

# Centralized format defined in Engineering Standards
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module} | {function} | {line} | {message}"

# Define log paths
LOGS_DIR = Path(__file__).resolve().parents[3] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Add stdout handler
logger.add(sys.stdout, format=LOG_FORMAT, level="INFO")

# Add file handler with rotation — primary structured log for the pipeline
logger.add(
    LOGS_DIR / "pipeline.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="50 MB",
    retention="10 days",
    enqueue=True,
)

# ---------------------------------------------------------------------------
# Phase 6 — Admin Dashboard Sink
# Writes INFO+ logs to /tmp/asteroid_api.log so the Streamlit admin dashboard
# can tail a single, stable path without needing access to the project LOGS_DIR.
# Rotated at 10 MB to prevent unbounded growth inside the container's tmpfs.
# ---------------------------------------------------------------------------
logger.add(
    "/tmp/asteroid_api.log",
    format=LOG_FORMAT,
    level="INFO",
    rotation="10 MB",
    retention="3 days",
    enqueue=True,
)


def get_logger():
    """Returns the configured loguru logger."""
    return logger
