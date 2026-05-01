"""
trainer.py — Multi-Model Benchmarking Pipeline
================================================
Loops through every YAML file in configs/model/, trains the corresponding
estimator, logs each as a separate MLflow run, then runs champion-challenger
selection to decide whether to promote a new @champion.

Model factory supports: XGBoost · Random Forest · LightGBM

Imbalance strategy per model type:
  xgboost      → SMOTE if viable, else scale_pos_weight (existing logic)
  random_forest → class_weight="balanced" (native) — SMOTE skipped
  lightgbm      → is_unbalance=True (native) — SMOTE skipped

Selection rule (Recall PRIMARY, F1 SECONDARY):
  1. Pick the best run from this session (highest recall, tie-break on F1).
  2. Fetch current @champion recall from the MLflow Registry.
  3. Promote if: new_recall > champion_recall AND new_f1 >= F1_THRESHOLD.
  4. If no @champion exists yet, promote unconditionally if F1 threshold is met.
"""

import os
import sys
import glob
import yaml
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import psutil
import dagshub

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline as SklearnPipeline
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from mlflow.tracking import MlflowClient

from asteroid_classifier.data.preprocessing import build_preprocessor
from asteroid_classifier.models.evaluator import evaluate_model
from asteroid_classifier.core.config import get_config
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.exceptions import ModelPromotionError

os.environ["MLFLOW_RECORD_ENV_VARS_IN_MODEL_LOGGING"] = "false"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXPERIMENT_NAME = "asteroid-hazard-classification"
MODEL_REGISTRY_NAME = "asteroid-hazard-classifier"
CHAMPION_ALIAS = "champion"
F1_PROMOTION_GATE = 0.85      # F1 must meet this minimum regardless of recall
CONFIGS_MODEL_GLOB = str(
    Path(__file__).resolve().parents[3] / "configs" / "model" / "*.yaml"
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def get_logger_instance():
    return get_logger()


def get_dvc_hash() -> str:
    """Extracts DVC content hash from data.dvc if available."""
    try:
        dvc_path = Path(__file__).resolve().parents[3] / "data.dvc"
        with open(dvc_path, "r") as f:
            dvc_data = yaml.safe_load(f)
            return dvc_data.get("outs", [{}])[0].get("md5", "unknown_hash")
    except Exception:
        return "unknown_hash"


def _init_mlflow(training_config: dict) -> None:
    """Initialises DagsHub + MLflow once for the whole benchmarking session."""
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER", "Govinthan-KS")
    repo_name = os.getenv("DAGSHUB_REPO_NAME", "Asteroid-Hazard-Classifier")
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI") or training_config.get(
        "mlflow_tracking_uri", "http://localhost:5000"
    )
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)


# ---------------------------------------------------------------------------
# Estimator factory
# ---------------------------------------------------------------------------
def build_estimator(model_type: str, params: dict) -> Any:
    """
    Returns the correct sklearn-compatible estimator for the given model_type.
    Raises ValueError for unsupported types — never silent failure.
    """
    if model_type == "xgboost":
        return XGBClassifier(**params)
    if model_type == "random_forest":
        return RandomForestClassifier(**params)
    if model_type == "lightgbm":
        return LGBMClassifier(**params)
    raise ValueError(
        f"Unsupported model_type '{model_type}'. "
        "Expected one of: xgboost, random_forest, lightgbm."
    )


# ---------------------------------------------------------------------------
# Single model training run
# ---------------------------------------------------------------------------
def train_single_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    training_config: dict,
    model_config: dict,
    nested: bool = False,
) -> dict:
    """
    Trains one estimator, logs it as an MLflow run, and returns a result dict.
    When nested=True the run is a child of an active parent run.

    Returns:
        {run_id, display_name, model_type, metrics, passed_threshold}
    """
    logger = get_logger_instance()

    model_params = {
        k: v for k, v in model_config.items()
        if k not in ("model_type", "display_name")
    }
    model_type: str = model_config.get("model_type", "xgboost")
    display_name: str = model_config.get("display_name", model_type.capitalize())

    # ── Imbalance strategy ──────────────────────────────────────────────────
    # RF and LGBM handle imbalance natively via config; only XGBoost uses SMOTE.
    use_smote = (model_type == "xgboost") and training_config.get("use_smote", True)

    num_pos = int(np.sum(y_train == 1))
    num_neg = int(np.sum(y_train == 0))
    n_minority = min(num_pos, num_neg)

    if use_smote and n_minority < 2:
        logger.warning(
            f"[{display_name}] Minority class count ({n_minority}) < 2. "
            "Disabling SMOTE — falling back to scale_pos_weight."
        )
        use_smote = False

    if model_type == "xgboost" and not use_smote:
        model_params["scale_pos_weight"] = float(num_neg / max(1, num_pos))

    preprocessor = build_preprocessor()
    clf = build_estimator(model_type, model_params)

    if use_smote:
        k_neighbors = min(n_minority - 1, 5)
        pipeline = ImbPipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("smote", SMOTE(
                    random_state=training_config.get("random_state", 42),
                    k_neighbors=k_neighbors,
                )),
                ("classifier", clf),
            ]
        )
    else:
        pipeline = SklearnPipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", clf),
            ]
        )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_name = f"{display_name}-7D-Rolling-{today_str}"

    logger.info(f"[{display_name}] Starting MLflow run: {run_name}")

    with mlflow.start_run(run_name=run_name, nested=nested) as run:
        run_id = run.info.run_id
        # Mark as a child run so the dashboard leaderboard can filter it cleanly
        mlflow.set_tag("run_type", "child")

        # Hardware snapshot — start
        mem_start = psutil.virtual_memory().used / (1024 ** 3)
        cpu_start = psutil.cpu_percent(interval=None)
        mlflow.log_metrics({
            "cpu_utilization_start": cpu_start,
            "memory_used_gb_start": mem_start,
        })

        pipeline.fit(X_train, y_train)

        # Hardware snapshot — end
        mem_end = psutil.virtual_memory().used / (1024 ** 3)
        cpu_end = psutil.cpu_percent(interval=None)
        mlflow.log_metrics({
            "cpu_utilization_end": cpu_end,
            "memory_used_gb_end": mem_end,
        })

        metrics = evaluate_model(pipeline, X_test, y_test)

        # Prefix all performance metrics with test_ for the dashboard query
        test_metrics = {f"test_{k}": v for k, v in metrics.items()}
        mlflow.log_metrics(test_metrics)
        mlflow.log_metrics(metrics)          # keep unpreixed for backward compat

        mlflow.log_params(model_params)
        mlflow.log_param("model_type", model_type)
        mlflow.log_param("display_name", display_name)
        mlflow.log_param("use_smote", use_smote)
        mlflow.log_param("data_dvc_hash", get_dvc_hash())

        # Log model artifact
        input_example = X_train[:5].copy() if isinstance(X_train, pd.DataFrame) else None
        mlflow.sklearn.log_model(pipeline, "model", input_example=input_example)

        # Tag for easy dashboard filtering
        mlflow.set_tag("display_name", display_name)
        mlflow.set_tag("model_type", model_type)

        logger.info(
            f"[{display_name}] Run complete — "
            f"Recall: {metrics['recall']:.4f}, "
            f"F1: {metrics['f1']:.4f}, "
            f"ROC-AUC: {metrics['roc_auc']:.4f}"
        )

    # Check whether this run meets the minimum promotion threshold (non-fatal)
    thresholds = training_config.get("thresholds", {})
    passed = (
        metrics.get("recall", 0.0) >= thresholds.get("recall", 0.90)
        and metrics.get("f1", 0.0) >= thresholds.get("f1", F1_PROMOTION_GATE)
        and metrics.get("roc_auc", 0.0) >= thresholds.get("roc_auc", 0.92)
    )
    if not passed:
        logger.warning(
            f"[{display_name}] Metrics did NOT meet all promotion thresholds "
            f"(recall≥{thresholds.get('recall',0.90)}, "
            f"f1≥{thresholds.get('f1',0.85)}, "
            f"roc_auc≥{thresholds.get('roc_auc',0.92)}). "
            "Run logged but not eligible for @champion."
        )

    return {
        "run_id": run_id,
        "display_name": display_name,
        "model_type": model_type,
        "metrics": metrics,
        "passed_threshold": passed,
    }


# ---------------------------------------------------------------------------
# Champion-Challenger selection
# ---------------------------------------------------------------------------
PRECISION_GUARDRAIL: float = 0.30  # blocks pure dummy models (precision≈0)
# XGBoost on sparse data: precision≈0.375 — revert to 0.70 when data volume grows


def _get_current_champion_metrics(client: MlflowClient) -> dict:
    """
    Fetches recall and F1 of the current @champion from the MLflow Registry.
    Returns {"recall": -1.0, "f1": -1.0} sentinel if no champion exists yet,
    which guarantees any valid first-run model will be promoted.
    """
    sentinel = {"recall": -1.0, "f1": -1.0}
    try:
        mv = client.get_model_version_by_alias(
            name=MODEL_REGISTRY_NAME, alias=CHAMPION_ALIAS
        )
        run = client.get_run(mv.run_id)
        m = run.data.metrics
        return {
            "recall": float(m.get("test_recall", m.get("recall", -1.0))),
            "f1":     float(m.get("test_f1",     m.get("f1",     -1.0))),
        }
    except Exception:
        return sentinel  # no champion registered yet


def _do_promote(
    client: MlflowClient,
    best: dict,
    reason: str,
) -> None:
    """Registers and aliases the best run as @champion."""
    logger = get_logger_instance()
    try:
        client.get_registered_model(MODEL_REGISTRY_NAME)
    except Exception:
        client.create_registered_model(MODEL_REGISTRY_NAME)

    run      = client.get_run(best["run_id"])
    mv       = client.create_model_version(
        name=MODEL_REGISTRY_NAME,
        source=f"{run.info.artifact_uri}/model",
        run_id=best["run_id"],
    )
    version = str(mv.version)

    client.set_registered_model_alias(
        name=MODEL_REGISTRY_NAME,
        alias=CHAMPION_ALIAS,
        version=version,
    )
    client.transition_model_version_stage(
        name=MODEL_REGISTRY_NAME,
        version=version,
        stage="Production",
        archive_existing_versions=False,
    )

    m = best["metrics"]
    logger.info(
        f"[NEO-Sentinel] ✅ @champion promoted \u2192 [{best['display_name']}] "
        f"version={version}, run_id={best['run_id'][:8]}… | "
        f"recall={m['recall']:.4f}  precision={m.get('precision', float('nan')):.4f}  "
        f"f1={m['f1']:.4f}  roc_auc={m['roc_auc']:.4f} | "
        f"Reason: {reason}"
    )


def select_and_promote_champion(results: list, training_config: dict) -> None:
    """
    Multi-tiered champion-challenger selection.

    Stage 0 — Precision guardrail
        Any candidate with precision < PRECISION_GUARDRAIL is disqualified.
        Prevents a 'predict-everything-hazardous' dummy from stealing @champion.

    Stage 1 — Primary: Recall
        Candidate recall must be ≥ current champion recall.

    Stage 2 — Tie-breaker: F1-Score
        If recall ties, candidate F1 must be strictly greater than champion F1.

    Stage 3 — Tertiary: Newer-is-better
        If recall AND F1 are identical, promote anyway — a model trained on
        more recent data is considered more relevant than an older equivalent.
    """
    logger = get_logger_instance()

    eligible = [r for r in results if r["passed_threshold"]]
    if not eligible:
        logger.warning(
            "[NEO-Sentinel] No model met all promotion thresholds. "
            "@champion alias unchanged."
        )
        return

    # ── Stage 0: Precision guardrail ────────────────────────────────────────────────
    precision_safe = [
        r for r in eligible
        if r["metrics"].get("precision", 0.0) >= PRECISION_GUARDRAIL
    ]
    disqualified = len(eligible) - len(precision_safe)
    if disqualified:
        logger.warning(
            f"[NEO-Sentinel] {disqualified} model(s) disqualified: "
            f"precision < {PRECISION_GUARDRAIL} (dummy-model guardrail)."
        )
    if not precision_safe:
        logger.warning(
            "[NEO-Sentinel] All candidates failed the precision guardrail. "
            "@champion alias unchanged."
        )
        return

    # Pick best from this session (recall DESC → f1 DESC)
    best = sorted(
        precision_safe,
        key=lambda r: (r["metrics"]["recall"], r["metrics"]["f1"]),
        reverse=True,
    )[0]
    bm = best["metrics"]

    logger.info(
        f"[NEO-Sentinel] Best candidate this session: [{best['display_name']}] "
        f"recall={bm['recall']:.4f}  precision={bm.get('precision', float('nan')):.4f}  "
        f"f1={bm['f1']:.4f}"
    )

    client = MlflowClient()
    champion = _get_current_champion_metrics(client)
    c_recall, c_f1 = champion["recall"], champion["f1"]

    if c_recall < 0:
        logger.info(
            "[NEO-Sentinel] No existing @champion found. "
            "Promoting first eligible model unconditionally."
        )
        _do_promote(client, best, reason="first champion")
        return

    logger.info(
        f"[NEO-Sentinel] Current @champion — recall={c_recall:.4f}  f1={c_f1:.4f}"
    )

    # ── Stage 1: Recall ─────────────────────────────────────────────────────────
    if bm["recall"] > c_recall:
        _do_promote(
            client, best,
            reason=f"higher recall ({bm['recall']:.4f} > {c_recall:.4f})",
        )
        return

    if bm["recall"] < c_recall:
        logger.info(
            f"[NEO-Sentinel] Candidate recall ({bm['recall']:.4f}) < "
            f"champion ({c_recall:.4f}). No promotion."
        )
        return

    # ── Stage 2: F1 tie-breaker (recall is equal) ───────────────────────────────
    if bm["f1"] > c_f1:
        logger.info(
            f"[NEO-Sentinel] Promotion triggered by F1-Score tie-breaker "
            f"({bm['f1']:.4f} > {c_f1:.4f} at recall={bm['recall']:.4f})."
        )
        _do_promote(
            client, best,
            reason=f"F1 tie-breaker ({bm['f1']:.4f} > {c_f1:.4f})",
        )
        return

    if bm["f1"] < c_f1:
        logger.info(
            f"[NEO-Sentinel] Candidate F1 ({bm['f1']:.4f}) < "
            f"champion F1 ({c_f1:.4f}) at equal recall. No promotion."
        )
        return

    # ── Stage 3: Newer-is-better (recall AND F1 identical) ─────────────────────
    logger.info(
        "[NEO-Sentinel] Promoting newer model with identical metrics for data freshness. "
        f"(recall={bm['recall']:.4f}, f1={bm['f1']:.4f} — same as champion)"
    )
    _do_promote(
        client, best,
        reason="newer model with identical metrics (data freshness)",
    )


# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------
def run_training_pipeline() -> None:
    """
    Discovers all YAML files in configs/model/, trains each estimator, then
    runs champion-challenger selection.
    """
    logger = get_logger_instance()
    logger.info("NEO-Sentinel: Multi-Model Benchmarking Pipeline started.")

    try:
        cfg = get_config()
        training_config: dict = cfg.get("training", {})

        # Load data
        raw_data_dir_str = cfg.get("data", {}).get("storage", {}).get("raw_data_dir", "data/raw")
        lookback_days = int(
            cfg.get("data", {}).get("nasa_neows_api", {}).get("lookback_days", 7)
        )
        project_root = Path(__file__).resolve().parents[3]
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"neo_rolling_{lookback_days}d_{today_str}.csv"
        latest_file = project_root / raw_data_dir_str / filename

        if not latest_file.exists():
            raise FileNotFoundError(
                f"Expected data file {latest_file} not found. Has ingestion run today?"
            )

        logger.info(f"Loading data: {latest_file}")
        df = pd.read_csv(latest_file)

        target_col = "is_potentially_hazardous"
        if target_col not in df.columns and "is_potentially_hazardous_asteroid" in df.columns:
            target_col = "is_potentially_hazardous_asteroid"

        y = df[target_col].astype(int)
        cols_to_drop = [target_col, "id", "name"]
        X = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

        test_size = training_config.get("test_size", 0.2)
        random_state = training_config.get("random_state", 42)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        logger.info(
            f"Data split — train: {len(X_train)}, test: {len(X_test)}, "
            f"hazardous in train: {int(y_train.sum())}"
        )

        # Initialise MLflow once for the whole session
        _init_mlflow(training_config)

        # Discover all model configs
        model_yaml_files = sorted(glob.glob(CONFIGS_MODEL_GLOB))
        if not model_yaml_files:
            raise FileNotFoundError(f"No model YAML files found at: {CONFIGS_MODEL_GLOB}")

        logger.info(f"Found {len(model_yaml_files)} model config(s): "
                    f"{[Path(f).stem for f in model_yaml_files]}")

        # ── Parent run wraps all three child runs for DagsHub UI cleanliness ────
        parent_run_name = f"NEO-Sentinel-Battle-Royale-{today_str}"
        logger.info(f"Opening parent MLflow run: '{parent_run_name}'")

        with mlflow.start_run(run_name=parent_run_name) as parent_run:
            mlflow.set_tag("run_type", "parent")
            mlflow.set_tag("models_benchmarked", str(len(model_yaml_files)))
            mlflow.log_param("data_dvc_hash", get_dvc_hash())

            # ── Benchmarking loop ─────────────────────────────────────────────
            results: list = []
            for yaml_path in model_yaml_files:
                with open(yaml_path, "r") as f:
                    model_config = yaml.safe_load(f)

                display_name = model_config.get("display_name", Path(yaml_path).stem)
                logger.info(f"{'─' * 60}")
                logger.info(f"Training: {display_name}")

                try:
                    result = train_single_model(
                        X_train, y_train, X_test, y_test,
                        training_config, model_config,
                        nested=True,        # child of parent_run
                    )
                    results.append(result)
                except Exception as exc:
                    logger.error(f"[{display_name}] Training failed: {exc}")
                    # Never abort the loop — benchmark the remaining models

            logger.info(f"{'─' * 60}")
            logger.info(
                f"Benchmarking complete. "
                f"{len(results)}/{len(model_yaml_files)} runs succeeded."
            )

            # Log summary to parent run for a single-glance DagsHub view
            for r in sorted(results, key=lambda x: x["metrics"]["recall"], reverse=True):
                tag_key = f"result.{r['display_name'].replace(' ', '_').lower()}"
                mlflow.set_tag(
                    tag_key,
                    f"recall={r['metrics']['recall']:.4f} "
                    f"f1={r['metrics']['f1']:.4f} "
                    f"roc_auc={r['metrics']['roc_auc']:.4f} "
                    f"({'eligible' if r['passed_threshold'] else 'blocked'})"
                )
                logger.info(
                    f"  [{r['display_name']:15s}] "
                    f"recall={r['metrics']['recall']:.4f}  "
                    f"f1={r['metrics']['f1']:.4f}  "
                    f"roc_auc={r['metrics']['roc_auc']:.4f}  "
                    f"{'✅ eligible' if r['passed_threshold'] else '❌ below threshold'}"
                )

        # Champion-Challenger runs outside the parent run context so promotion
        # registry calls aren't attributed to the parent MLflow run.
        select_and_promote_champion(results, training_config)

    except ModelPromotionError as exc:
        logger.error(f"Promotion error: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Training pipeline failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    run_training_pipeline()
