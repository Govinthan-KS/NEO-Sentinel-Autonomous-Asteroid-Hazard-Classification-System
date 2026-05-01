"""
versioning.py — DVC Data Versioning Gate
==========================================
Versions the ingested data/ directory with DVC and pushes the snapshot
to the DagsHub remote, so every MLflow training run carries a traceable
data lineage hash.

Design contract (critical for pipeline safety):
  - DVC push failure is NON-BLOCKING.
    A WARNING is logged and the function returns the best available hash.
    Training always proceeds — data upload is a lineage feature, not a
    correctness requirement.
  - No exception propagates out of version_and_push_data().
    The caller can rely on always receiving a string hash back.
  - All credentials sourced exclusively from os.getenv().
  - Subprocess calls have explicit timeouts — never hangs the runner.

Remote configuration (read from .dvc/config):
  remote = origin
  url    = https://dagshub.com/Govinthan-KS/asteroid-hazard-classifier.dvc
  auth   = basic (user=DAGSHUB_REPO_OWNER, password=DAGSHUB_TOKEN)
"""

from __future__ import annotations

import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Optional

from asteroid_classifier.core.logging import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
DATA_DVC_PATH: Path = PROJECT_ROOT / "data.dvc"
DVC_REMOTE_NAME: str = "origin"      # matches .dvc/config [core] remote
DVC_ADD_TIMEOUT: int = 60            # seconds — local cache op, should be fast
DVC_PUSH_TIMEOUT: int = 300          # seconds — network upload, allow generous window


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _run_dvc(args: list[str], timeout: int) -> tuple[bool, str]:
    """
    Runs a DVC CLI command as a child process from the project root.

    Returns (success: bool, message: str).
    Never raises — all failure modes are captured and returned as (False, msg).
    """
    cmd = ["dvc"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=timeout,
        )
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0:
            return True, output
        return False, output or f"DVC exited with code {result.returncode}"

    except subprocess.TimeoutExpired:
        return False, (
            f"DVC command timed out after {timeout}s: dvc {' '.join(args)}"
        )
    except FileNotFoundError:
        return False, (
            "DVC executable not found. "
            "Ensure dvc is installed: it is listed in pyproject.toml dependencies."
        )
    except Exception as exc:
        return False, f"Unexpected subprocess error: {exc}"


def _read_dvc_hash() -> str:
    """
    Reads the current md5 content hash from data.dvc.
    Returns 'unknown_hash' on any failure — never raises.
    """
    try:
        with open(DATA_DVC_PATH, "r") as fh:
            dvc_data = yaml.safe_load(fh)
        return dvc_data.get("outs", [{}])[0].get("md5", "unknown_hash")
    except Exception as exc:
        logger.warning(f"[NEO-Sentinel] Could not read DVC hash from data.dvc: {exc}")
        return "unknown_hash"


def _configure_remote_auth() -> bool:
    """
    Injects DagsHub credentials into the DVC remote's LOCAL config
    (.dvc/config.local — gitignored, never committed).

    Returns True if credentials are available and were applied.
    Returns False if any required env-var is missing — caller will skip push.
    """
    token = os.getenv("DAGSHUB_TOKEN")
    owner = os.getenv("DAGSHUB_REPO_OWNER")

    if not token or not owner:
        logger.warning(
            "[NEO-Sentinel] DVC auth skipped — DAGSHUB_TOKEN or "
            "DAGSHUB_REPO_OWNER not set. DVC push will be skipped."
        )
        return False

    # These write to .dvc/config.local (local-only, gitignored)
    auth_commands = [
        ["remote", "modify", "--local", DVC_REMOTE_NAME, "auth", "basic"],
        ["remote", "modify", "--local", DVC_REMOTE_NAME, "user", owner],
        ["remote", "modify", "--local", DVC_REMOTE_NAME, "password", token],
    ]

    all_ok = True
    for cmd_args in auth_commands:
        ok, msg = _run_dvc(cmd_args, timeout=10)
        if not ok:
            logger.warning(
                f"[NEO-Sentinel] DVC auth config warning: {msg} "
                "(will attempt push anyway with existing config)"
            )
            all_ok = False

    if all_ok:
        logger.info("[NEO-Sentinel] DVC remote authentication configured.")
    return True  # return True even on partial failure — push might still work


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def version_and_push_data() -> str:
    """
    Versions the data/ directory and pushes it to DagsHub DVC remote.

    Pipeline:
      1. dvc add data/     — updates data.dvc with the new content hash
      2. Configure auth    — injects DAGSHUB_TOKEN into .dvc/config.local
      3. dvc push          — uploads new data files to DagsHub remote

    Returns:
        The DVC content hash (md5) string for MLflow lineage tagging.
        Always returns a string — 'unknown_hash' on unrecoverable failure.

    This function NEVER raises. All failures are logged as WARNING and the
    function returns gracefully so training always proceeds.
    """
    logger.info("[NEO-Sentinel] Starting DVC data versioning...")

    # ── Step 1: dvc add ──────────────────────────────────────────────────────
    logger.info("[NEO-Sentinel] Running: dvc add data/")
    ok, msg = _run_dvc(["add", "data/"], timeout=DVC_ADD_TIMEOUT)

    if ok:
        logger.info("[NEO-Sentinel] dvc add succeeded.")
    else:
        logger.warning(
            f"[NEO-Sentinel] dvc add failed (non-blocking): {msg}\n"
            "The data.dvc hash may be stale this run. Training will proceed."
        )
        # Return whatever hash is already in data.dvc — better than nothing
        return _read_dvc_hash()

    # Read the fresh hash written by dvc add
    fresh_hash = _read_dvc_hash()
    logger.info(f"[NEO-Sentinel] Dataset content hash: {fresh_hash}")

    # ── Step 2: Configure DagsHub auth ───────────────────────────────────────
    _configure_remote_auth()  # best-effort — push continues even if this warns

    # ── Step 3: dvc push ─────────────────────────────────────────────────────
    logger.info(
        f"[NEO-Sentinel] Pushing dataset to DagsHub DVC remote '{DVC_REMOTE_NAME}'..."
    )
    ok, msg = _run_dvc(["push"], timeout=DVC_PUSH_TIMEOUT)

    if ok:
        logger.info(
            f"[NEO-Sentinel] DVC push succeeded — "
            f"dataset version {fresh_hash[:12]}… is now on DagsHub remote."
        )
    else:
        logger.warning(
            f"[NEO-Sentinel] DVC push failed (non-blocking): {msg}\n"
            "Data was NOT uploaded to DagsHub this run. "
            "The MLflow run will still be tagged with the local hash for partial lineage. "
            "Training will proceed."
        )

    # Return hash regardless of push success — MLflow gets the correct hash
    return fresh_hash


# ---------------------------------------------------------------------------
# Entry point (CI/CD and local use)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    hash_value = version_and_push_data()
    logger.info(f"[NEO-Sentinel] Versioning step complete. Hash: {hash_value}")
    # Always exit 0 — DVC push failure is a WARNING, not a pipeline error.
    # The CI step uses continue-on-error: true as an additional safeguard.
    sys.exit(0)
