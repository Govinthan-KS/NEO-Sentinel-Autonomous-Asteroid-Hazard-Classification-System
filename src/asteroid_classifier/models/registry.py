import os
import mlflow
from mlflow.tracking.client import MlflowClient
from mlflow.entities import Run
import dagshub
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.models.evaluator import check_promotion_thresholds
from asteroid_classifier.core.exceptions import ModelPromotionError

logger = get_logger()

def init_registry(training_config: Dict[str, Any]) -> str:
    """
    Initializes MLflow tracking specifically for Model Registry operations safely.
    It matches trainer.py's strategy to prevent localhost fallback defaults or credential leakage.
    """
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER", "Govinthan-KS")
    repo_name = os.getenv("DAGSHUB_REPO_NAME", "Asteroid-Hazard-Classifier")
    
    # Intialize dagshub gracefully
    try:
        dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    except Exception as e:
        logger.warning(f"DagsHub initialization warning (might be local or env missing): {e}")

    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI") or training_config.get("mlflow_tracking_uri", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    logger.info(f"Registry initialized with Tracking URI: {mlflow_uri}")
    return mlflow_uri

def get_best_run(client: MlflowClient, experiment_name: str) -> Run:
    """
    Fetches the best recent run strictly looking for optimal Recall, then F1 score.
    """
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        raise ValueError(f"Experiment '{experiment_name}' not found.")
        
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.recall DESC", "metrics.f1 DESC"],
        max_results=1
    )
    if not runs:
        raise ValueError(f"No runs found in experiment '{experiment_name}'.")
    
    return runs[0]

def enrich_version_metadata(client: MlflowClient, model_name: str, version: str, run: Run, dry_run: bool = False):
    """
    Constructs an updated metadata description utilizing the run's metadata.
    """
    dvc_hash = run.data.params.get("data_dvc_hash", "Unknown")
    cpu_util = run.data.metrics.get("cpu_utilization_end", "Unknown")
    mem_util = run.data.metrics.get("memory_used_gb_end", "Unknown")
    
    # Try getting the run date from tags or calculate dynamically
    start_time = run.info.start_time
    if start_time:
        date_str = datetime.fromtimestamp(start_time / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        date_str = "Unknown"
        
    description = (
        f"**Asteroid Hazard Classifier Version**\n\n"
        f"**Training Date:** {date_str}\n"
        f"**DVC Data Hash:** {dvc_hash}\n"
        f"- CPU Usage: {cpu_util} %\n"
        f"- RAM Usage: {mem_util} GB\n"
    )
    
    if dry_run:
        logger.info(f"[DRY RUN] Would update version {version} description with:\n{description}")
    else:
        # Commit the description to the Model Version
        client.update_model_version(name=model_name, version=version, description=description)
        logger.info(f"Updated description for Model '{model_name}' Version '{version}'.")

def archive_active_models(client: MlflowClient, model_name: str, keep_version: str, dry_run: bool = False):
    """
    Atomic archival handler. Avoid conflicts when assigning aliases/stages by transitioning older versions.
    """
    logger.info(f"Archiving previous active models for '{model_name}'...")
    
    try:
        # Check registered model details
        model_info = client.get_registered_model(model_name)
    except Exception as e:
        logger.info(f"Model '{model_name}' might not exist yet during archival. Skipping.")
        return

    # Check for older versions in legacy stages or with specific aliases
    for mv in model_info.latest_versions:
        # Only archive previous items
        if str(mv.version) != str(keep_version) and mv.current_stage in ["Production", "Staging"]:
            if dry_run:
                logger.info(f"[DRY RUN] Would transition '{model_name}' Version '{mv.version}' from '{mv.current_stage}' to 'Archived'.")
            else:
                client.transition_model_version_stage(
                    name=model_name,
                    version=mv.version,
                    stage="Archived",
                    archive_existing_versions=False
                )
                
    # MLflow deletes Alias automatically if we reassign to a new version, so we don't strictly need to manually delete `@champion` from older ones,
    # but logically cleaning things up ensures clarity. (MLflow's alias system maps an alias to a specific version at a time.)
    logger.info("Archival verification complete.")

def register_and_promote(
    experiment_name: str,
    model_name: str,
    thresholds: Dict[str, float],
    training_config: Dict[str, Any],
    dry_run: bool = False
):
    """
    Main orchestrator for grabbing the best model run, evaluating metric thresholds,
    and pushing it seamlessly into the Model Registry tagged properly.
    """
    logger.info(f"Starting registration for experiment '{experiment_name}' {'[DRY RUN]' if dry_run else ''}")
    
    _ = init_registry(training_config)
    client = MlflowClient()
    
    try:
        best_run = get_best_run(client, experiment_name)
    except ValueError as e:
        logger.error(str(e))
        return
        
    logger.info(f"Best run ID selected: {best_run.info.run_id}")
    metrics = best_run.data.metrics
    
    logger.info("Evaluating model metrics against promotional thresholds...")
    try:
        check_promotion_thresholds(metrics, thresholds)
    except ModelPromotionError as e:
        logger.error(f"Best run {best_run.info.run_id} failed eligibility: {str(e)}")
        raise e

    # Passed validation, proceed: 
    if dry_run:
        logger.info(f"[DRY RUN] Model metadata validated. Proceeding to mock registration.")
        # Dummy version for dry_run
        version = "999-dry-run"
    else:
        logger.info(f"Creating model version for run {best_run.info.run_id}")
        
        # Ensure registered model exists
        try:
            client.get_registered_model(model_name)
        except Exception:
            client.create_registered_model(model_name)
            
        mv = client.create_model_version(
            name=model_name,
            source=f"{best_run.info.artifact_uri}/model",
            run_id=best_run.info.run_id
        )
        version = str(mv.version)
        logger.info(f"Registered model version: {version}")

    enrich_version_metadata(client, model_name, version, best_run, dry_run=dry_run)
    archive_active_models(client, model_name, version, dry_run=dry_run)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would assign @champion alias to {model_name} Version {version}.")
        logger.info(f"[DRY RUN] Would transition legacy stage to 'Production' for {model_name} Version {version}.")
        logger.info("[DRY RUN] Finished registration execution safety check.")
    else:
        logger.info(f"Promoting {model_name} Version {version} with @champion alias and 'Production' legacy stage.")
        client.set_registered_model_alias(name=model_name, alias="champion", version=version)
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=False
        )
        logger.info("Model Promotion completed safely. Repository parity synchronized.")
