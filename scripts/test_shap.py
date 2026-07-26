import os
import sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

import mlflow
from mlflow.tracking import MlflowClient

# Add src to pythonpath so imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from asteroid_classifier.models.trainer import generate_shap_summary
from asteroid_classifier.core.config import get_config

def main():
    print("Testing SHAP extraction...")
    
    cfg = get_config()
    
    # 1. Init MLflow + DagsHub tracking (same as trainer)
    import dagshub
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER", "Govinthan-KS")
    repo_name = os.getenv("DAGSHUB_REPO_NAME", "Asteroid-Hazard-Classifier")
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    
    training_config = cfg.get("training", {})
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI") or training_config.get(
        "mlflow_tracking_uri", "http://localhost:5000"
    )
    mlflow.set_tracking_uri(mlflow_uri)
    
    # 2. Load @champion model
    client = MlflowClient()
    try:
        mv = client.get_model_version_by_alias(
            name="asteroid-hazard-classifier", alias="champion"
        )
    except Exception as e:
        print(f"Error finding champion: {e}")
        return
        
    print(f"Loading champion model from: {mv.source}")
    model = mlflow.pyfunc.load_model(mv.source)
    pipeline = model._model_impl
    if hasattr(pipeline, "sklearn_model"):
        pipeline = pipeline.sklearn_model
    
    # 3. Load local X_test data
    print("Loading local data...")
    raw_data_dir = cfg.get("data", {}).get("storage", {}).get("raw_data_dir", "data/raw")
    project_root = Path(__file__).resolve().parents[1]
    
    # Find the most recent CSV file
    csv_files = sorted((project_root / raw_data_dir).glob("*.csv"))
    if not csv_files:
        print("No CSV files found in raw data dir.")
        return
        
    latest_file = csv_files[-1]
    print(f"Using data file: {latest_file}")
    df = pd.read_csv(latest_file)
    
    target_col = "is_potentially_hazardous"
    if target_col not in df.columns and "is_potentially_hazardous_asteroid" in df.columns:
        target_col = "is_potentially_hazardous_asteroid"
        
    y = df[target_col].astype(int)
    cols_to_drop = [target_col, "id", "name"]
    X = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    test_size = training_config.get("test_size", 0.2)
    random_state = training_config.get("random_state", 42)
    
    _, X_test, _, _ = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # 4. Call SHAP helper
    print("Calling generate_shap_summary...")
    output_path = str(project_root / "shap_summary_test.png")
    top_features = generate_shap_summary(pipeline, X_test, output_path)
    
    # 5. Print results
    print("--------------------------------------------------")
    print(f"SHAP summary plot successfully saved to: {output_path}")
    print(f"Top 5 features extracted: {top_features}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
