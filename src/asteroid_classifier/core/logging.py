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

# Add file handler with rotation
logger.add(
    LOGS_DIR / "pipeline.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="50 MB",
    retention="10 days",
)


def get_logger():
    """Returns the configured loguru logger"""
    return logger
