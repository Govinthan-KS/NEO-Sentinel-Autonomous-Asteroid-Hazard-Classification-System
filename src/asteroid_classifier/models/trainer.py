import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
import glob
from sklearn.model_selection import train_test_split
from datetime import datetime, timezone
import os
import sys
import psutil
import dagshub
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.pipeline import Pipeline as SklearnPipeline
from asteroid_classifier.data.preprocessing import build_preprocessor
from asteroid_classifier.models.evaluator import evaluate_model, check_promotion_thresholds
from asteroid_classifier.core.config import get_config
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.exceptions import ModelPromotionError

from pathlib import Path

os.environ["MLFLOW_RECORD_ENV_VARS_IN_MODEL_LOGGING"] = "false"

def get_dvc_hash() -> str:
    """Extracts DVC hash from data.dvc file if available."""
    try:
        dvc_path = Path(__file__).resolve().parents[3] / "data.dvc"
        with open(dvc_path, 'r') as f:
            dvc_data = yaml.safe_load(f)
            return dvc_data.get('outs', [{}])[0].get('md5', 'unknown_hash')
    except Exception:
        return 'unknown_hash'

def train_model(X_train: np.ndarray, y_train: np.ndarray, 
                X_test: np.ndarray, y_test: np.ndarray,
                training_config: dict, model_config: dict):
    """
    Core function for training the model using the hybrid imbalance-handling strategy.
    Tracks everything using MLflow for DagsHub.
    """
    use_smote = training_config.get('use_smote', True)
    
    # Configure MLflow using DagsHub explicit initialization
    repo_owner = os.getenv('DAGSHUB_REPO_OWNER', 'Govinthan-KS')
    repo_name = os.getenv('DAGSHUB_REPO_NAME', 'Asteroid-Hazard-Classifier')
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI') or training_config.get('mlflow_tracking_uri', 'http://localhost:5000')
    
    # Configure MLflow explicitly following dagshub init
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("asteroid-hazard-classification")
    
    preprocessor = build_preprocessor()
    
    # Prepare model
    model_params = model_config.copy()
    model_type = model_params.pop('model_type', 'xgboost')
    
    if model_type != 'xgboost':
        raise ValueError(f"Unsupported model type: {model_type}")

    # Hybrid imbalance handling
    num_pos = np.sum(y_train == 1)
    num_neg = np.sum(y_train == 0)
    n_minority = min(num_pos, num_neg)

    if use_smote and n_minority < 2:
        logger = get_logger()
        logger.warning(f"Minority class count ({n_minority}) < 2. Disabling SMOTE fallback to scale_pos_weight.")
        use_smote = False

    if not use_smote:
        # Calculate scale_pos_weight
        scale_pos_weight = num_neg / max(1, num_pos)
        model_params['scale_pos_weight'] = float(scale_pos_weight)
        
    clf = XGBClassifier(**model_params)
    
    if use_smote:
        k_neighbors = min(n_minority - 1, 5)
        pipeline = ImbPipeline(steps=[
            ('preprocessor', preprocessor),
            ('smote', SMOTE(random_state=training_config.get('random_state', 42), k_neighbors=k_neighbors)),
            ('classifier', clf)
        ])
    else:
        pipeline = SklearnPipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', clf)
        ])

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    model_name_display = "XGBoost" if model_type.lower() == 'xgboost' else model_type.capitalize()
    run_name = f"{model_name_display}-7D-Rolling-{today_str}"
    
    with mlflow.start_run(run_name=run_name):
        mem_start = psutil.virtual_memory().used / (1024**3)
        cpu_start = psutil.cpu_percent(interval=None)
        mlflow.log_metrics({"cpu_utilization_start": cpu_start, "memory_used_gb_start": mem_start})

        # Fit logic
        pipeline.fit(X_train, y_train)
        
        mem_end = psutil.virtual_memory().used / (1024**3)
        cpu_end = psutil.cpu_percent(interval=None)
        mlflow.log_metrics({"cpu_utilization_end": cpu_end, "memory_used_gb_end": mem_end})
        
        # Calculate metrics
        metrics = evaluate_model(pipeline, X_test, y_test)
        
        # Log to MLflow
        mlflow.log_params(model_params)
        mlflow.log_param("use_smote", use_smote)
        mlflow.log_param("data_dvc_hash", get_dvc_hash())
        mlflow.log_metrics(metrics)
        
        # Log artifacts: Preprocessor specifically logic, plus the full pipeline model
        mlflow.sklearn.log_model(preprocessor, "preprocessor")
        
        input_example = X_train[:5].copy() if isinstance(X_train, (pd.DataFrame, np.ndarray)) else None
        if isinstance(input_example, pd.DataFrame):
            num_cols = input_example.select_dtypes(include=['number']).columns
            input_example[num_cols] = input_example[num_cols].astype('float64')
            
        mlflow.sklearn.log_model(pipeline, "model", input_example=input_example)
        
        # Finally, evaluate for promotion checking
        check_promotion_thresholds(metrics, training_config.get('thresholds', {}))
        
        return pipeline, metrics

def run_training_pipeline():
    logger = get_logger()
    logger.info("Initializing Model Training Pipeline...")
    try:
        cfg = get_config()
        logger.info(f"Loaded config properly. Target model type: {cfg.get('model', {}).get('model_type', 'xgboost')}")
        
        # Load Real Data
        raw_data_dir_str = cfg.get('data', {}).get('storage', {}).get('raw_data_dir', 'data/raw')
        project_root = Path(__file__).resolve().parents[3]
        
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"neo_rolling_7d_{today_str}.csv"
        latest_file = project_root / raw_data_dir_str / filename
        
        if not latest_file.exists():
            raise FileNotFoundError(f"Expected data file {latest_file} not found. Has ingestion run today?")
            
        logger.info(f"Loading data file: {latest_file}")
        
        df = pd.read_csv(latest_file)
        
        # Determine target column name based on raw data structure
        target_col = 'is_potentially_hazardous'
        if target_col not in df.columns and 'is_potentially_hazardous_asteroid' in df.columns:
            target_col = 'is_potentially_hazardous_asteroid'
            
        # Pre-process for Training
        y = df[target_col].astype(int)
        
        # Drop non-feature columns
        cols_to_drop = [target_col, 'id', 'name']
        X = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # Train/Test Split
        test_size = cfg.get('training', {}).get('test_size', 0.2)
        random_state = cfg.get('training', {}).get('random_state', 42)
        
        logger.info(f"Splitting data with test_size={test_size}, random_state={random_state}")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        # Connect the Dots
        logger.info("Starting model training pipeline...")
        pipeline, metrics = train_model(X_train, y_train, X_test, y_test, cfg.get('training', {}), cfg.get('model', {}))
        
        logger.info(f"Training pipeline successfully executed. Metrics: {metrics}")
        
    except ModelPromotionError as e:
        logger.error(f"Promotion thresholds not met: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_training_pipeline()
