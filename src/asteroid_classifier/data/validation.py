"""
validation.py — Great Expectations Data Validation Gate
=========================================================
Validates the ingested NASA NeoWs CSV against a defined expectation suite
before any training step is permitted to proceed.

If ANY critical expectation fails:
  - Every failed rule is logged at ERROR level.
  - DataValidationError is raised → pipeline halts.
  - The process exits with code 1 (blocks the CI/CD step).

Auto-discovery mode (used by CI/CD):
  When called as  `python -m asteroid_classifier.data.validation`  with no
  arguments, the module derives the expected CSV path from the Hydra config
  (same resolution logic as trainer.py) and validates that file.

Manual mode (local debugging):
  `python -m asteroid_classifier.data.validation /path/to/file.csv`
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import great_expectations as gx

from asteroid_classifier.core.exceptions import DataValidationError
from asteroid_classifier.core.logging import get_logger

logger = get_logger()


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------
def validate_neo_data(csv_path: str) -> bool:
    """
    Validates the ingested NEO dataset at `csv_path` using Great Expectations.

    Expectations checked:
      - Required columns exist: id, is_potentially_hazardous, absolute_magnitude_h
      - No null values in: id, absolute_magnitude_h
      - is_potentially_hazardous is strictly boolean (True / False)
      - estimated_diameter_min_km ≥ 0  (physical constraint)
      - relative_velocity_kmph ≥ 0     (physical constraint)
      - miss_distance_km ≥ 0           (physical constraint)

    Returns True on full success.
    Raises DataValidationError if any expectation fails or an execution error occurs.
    """
    resolved = Path(csv_path).resolve()
    logger.info(f"[NEO-Sentinel] Starting data validation on: {resolved}")

    if not resolved.exists():
        raise DataValidationError(
            f"[NEO-Sentinel] Validation target not found: {resolved}. "
            "Ensure the ingestion step completed successfully before validation."
        )

    if resolved.stat().st_size == 0:
        raise DataValidationError(
            f"[NEO-Sentinel] Validation target is empty (0 bytes): {resolved}. "
            "The ingestion step may have produced no records."
        )

    try:
        # ── Great Expectations ephemeral context ─────────────────────────────
        context = gx.get_context()

        data_source = context.data_sources.add_pandas("pandas_source")
        asset = data_source.add_csv_asset(
            "neo_asset", filepath_or_buffer=resolved
        )
        batch_definition = asset.add_batch_definition_whole_dataframe("daily_batch")

        suite_name = "neo_validation_suite"
        suite_config = gx.ExpectationSuite(name=suite_name)
        suite = context.suites.add_or_update(suite=suite_config)

        # ── Structural expectations ──────────────────────────────────────────
        # Critical columns must exist
        for col in ("id", "is_potentially_hazardous", "absolute_magnitude_h"):
            suite.add_expectation(
                gx.expectations.ExpectColumnToExist(column=col)
            )

        # ── Null-value expectations ──────────────────────────────────────────
        # Key identifier and primary feature must never be null
        for col in ("id", "absolute_magnitude_h"):
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
            )

        # ── Domain expectations ──────────────────────────────────────────────
        # Target label must be strictly boolean — never a stray string
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="is_potentially_hazardous",
                value_set=["True", "False", True, False],
            )
        )

        # ── Physical-constraint expectations ─────────────────────────────────
        # These columns are optional (may be NaN for NEOs with no close approach)
        # but if a value IS present it must be physically valid (>= 0).
        for col in (
            "estimated_diameter_min_km",
            "estimated_diameter_max_km",
            "relative_velocity_kmph",
            "miss_distance_km",
        ):
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToBeBetween(
                    column=col,
                    min_value=0,
                    # No max_value — unbounded upper end for physical measurements
                    mostly=0.95,  # tolerate up to 5 % NaN / missing-approach rows
                )
            )

        context.suites.add_or_update(suite=suite)

        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name="neo_daily_validation",
                data=batch_definition,
                suite=suite,
            )
        )

        results = validation_definition.run()

    except DataValidationError:
        raise  # already formatted — let it propagate
    except Exception as exc:
        logger.error(f"[NEO-Sentinel] Validation execution error: {exc}")
        raise DataValidationError(
            f"[NEO-Sentinel] Great Expectations context error: {exc}"
        ) from exc

    # ── Inspect results ──────────────────────────────────────────────────────
    if not results.success:
        logger.error(
            f"[NEO-Sentinel] Data validation FAILED for: {resolved}"
        )
        failed_count = 0
        for item in results.results:
            if not item.success:
                failed_count += 1
                expectation_type = (
                    item.expectation_config.type
                    if item.expectation_config
                    else "unknown"
                )
                logger.error(
                    f"[NEO-Sentinel]   ✗ Failed expectation [{failed_count}]: "
                    f"{expectation_type}"
                )
        raise DataValidationError(
            f"[NEO-Sentinel] Validation suite failed "
            f"({failed_count} expectation(s) violated). "
            "Training blocked — fix the data quality issue first."
        )

    logger.info(
        f"[NEO-Sentinel] Data validation PASSED ✓ — "
        f"all expectations met for: {resolved}"
    )
    return True


# ---------------------------------------------------------------------------
# Auto-discovery helper (CI/CD mode)
# ---------------------------------------------------------------------------
def _discover_latest_csv() -> str:
    """
    Derives the expected ingested CSV path from the Hydra config.

    Uses the identical resolution logic as trainer.py so both modules
    always agree on which file to operate on without any hardcoding.

    Raises FileNotFoundError with a descriptive message if the file is absent.
    """
    from asteroid_classifier.core.config import get_config  # local import — avoids Hydra side-effects at module level

    cfg = get_config()

    raw_dir_str: str = (
        cfg.get("data", {})
        .get("storage", {})
        .get("raw_data_dir", "data/raw")
    )
    lookback_days: int = int(
        cfg.get("data", {})
        .get("nasa_neows_api", {})
        .get("lookback_days", 30)
    )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"neo_rolling_{lookback_days}d_{today_str}.csv"
    project_root = Path(__file__).resolve().parents[3]
    full_path = project_root / raw_dir_str / filename

    if not full_path.exists():
        raise FileNotFoundError(
            f"[NEO-Sentinel] Auto-discovery failed: expected file not found:\n"
            f"  {full_path}\n"
            "Ensure the ingestion step ran successfully today before calling validation."
        )

    return str(full_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # ── Resolve the target CSV path ─────────────────────────────────────────
    # Mode 1: explicit path from CLI argument (manual / debugging)
    # Mode 2: auto-discover from Hydra config   (CI/CD pipeline)
    csv_path: Optional[str] = None

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        logger.info(
            f"[NEO-Sentinel] Validation running in manual mode — target: {csv_path}"
        )
    else:
        logger.info(
            "[NEO-Sentinel] No path argument supplied — "
            "auto-discovering latest ingested CSV from config."
        )
        try:
            csv_path = _discover_latest_csv()
        except FileNotFoundError as exc:
            logger.error(str(exc))
            sys.exit(1)

    # ── Run validation ───────────────────────────────────────────────────────
    try:
        validate_neo_data(csv_path)
        logger.info(
            "[NEO-Sentinel] Validation gate passed. "
            "Training is cleared to proceed."
        )
        sys.exit(0)
    except DataValidationError as exc:
        logger.error(str(exc))
        sys.exit(1)
    except Exception as exc:
        logger.error(
            f"[NEO-Sentinel] Unexpected error during validation: {exc}"
        )
        sys.exit(1)
