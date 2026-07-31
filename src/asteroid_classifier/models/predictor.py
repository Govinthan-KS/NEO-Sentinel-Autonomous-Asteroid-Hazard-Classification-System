import mlflow
import pandas as pd
from typing import Tuple, Optional
from dataclasses import dataclass
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.exceptions import ModelNotLoadedError, PredictionError
import os
import dagshub

@dataclass
class PredictionResult:
    is_hazardous: bool
    confidence: float
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None

class AsteroidPredictor:
    def __init__(self, model_uri: str):
        self.logger = get_logger()
        self.model_uri = model_uri
        self.model = None
        self.explainer = None
        self.anomaly_detector = None
        self._load_model()

    def _load_model(self):
        try:
            # DagsHub auth is bootstrapped in main.py before this is called.
            # Calling dagshub.init() again here would reset state and risk
            # triggering an interactive OAuth prompt in headless environments.
            self.logger.info(f"[NEO-Sentinel] Loading MLflow model from: {self.model_uri}")
            self.model = mlflow.pyfunc.load_model(self.model_uri)
            self.logger.info("[NEO-Sentinel] Model loaded successfully.")
            
            try:
                champion_run_id = getattr(self.model.metadata, "run_id", None)
                self.run_id = champion_run_id
            except Exception as e:
                self.run_id = None
                self.logger.warning(f"[NEO-Sentinel] Could not extract run_id from champion model: {e}")
                
            try:
                if self.run_id:
                    client = mlflow.MlflowClient()
                    artifacts = [a.path for a in client.list_artifacts(self.run_id)]
                    if "anomaly_detector" in artifacts:
                        anomaly_uri = f"runs:/{self.run_id}/anomaly_detector"
                        self.logger.info(f"[NEO-Sentinel] Attempting to load anomaly detector from {anomaly_uri}")
                        self.anomaly_detector = mlflow.sklearn.load_model(anomaly_uri)
                    else:
                        self.logger.info(f"[NEO-Sentinel] No 'anomaly_detector' artifact found in run {self.run_id}. Skipping load.")
            except Exception as e:
                self.logger.warning(f"[NEO-Sentinel] Could not load anomaly detector: {e}")
            
            try:
                import shap
                pipeline = getattr(self.model, '_model_impl', None)
                if hasattr(pipeline, "sklearn_model"):
                    pipeline = pipeline.sklearn_model
                    
                if pipeline is not None and hasattr(pipeline, "named_steps"):
                    classifier = pipeline.named_steps.get("classifier")
                    if classifier is not None:
                        self.logger.info("[NEO-Sentinel] Caching SHAP TreeExplainer for the loaded champion model.")
                        self.explainer = shap.TreeExplainer(classifier)
            except ImportError:
                self.logger.warning("[NEO-Sentinel] SHAP is not installed, explain endpoint will fail.")
            except Exception as e:
                self.logger.error(f"[NEO-Sentinel] Failed to cache SHAP explainer: {e}")

        except Exception as e:
            self.logger.error(f"[NEO-Sentinel] Failed to load model from {self.model_uri}: {e}")
            raise ModelNotLoadedError(str(e))


    def predict(self, features_dict: dict) -> PredictionResult:
        if self.model is None:
            raise ModelNotLoadedError("Model is not initialized.")
        
        try:
            # Map Pydantic dict to explicitly named DataFrame columns precisely as MLflow model expects
            df = pd.DataFrame([features_dict])
            
            # Use pyfunc model to predict
            prediction = self.model.predict(df)
            
            # Unwrap pyfunc
            pipeline = getattr(self.model, '_model_impl', None)
            if hasattr(pipeline, "sklearn_model"):
                pipeline = pipeline.sklearn_model
            
            # Predict Proba if available
            if pipeline is not None and hasattr(pipeline, 'predict_proba'):
                proba = pipeline.predict_proba(df)[0]
                confidence = float(max(proba))
            else:
                confidence = 1.0 # fallback
                
            pred_val = bool(prediction[0])
            
            is_anomaly = None
            anomaly_score = None
            
            if self.anomaly_detector is not None and pipeline is not None:
                preprocessor = pipeline.named_steps.get("preprocessor")
                if preprocessor:
                    transformed_features = preprocessor.transform(df)
                    iso_pred = self.anomaly_detector.predict(transformed_features)[0]
                    is_anomaly = bool(iso_pred == -1)
                    anomaly_score = float(self.anomaly_detector.decision_function(transformed_features)[0])
            
            self.logger.info(f"Made prediction: {pred_val} with confidence: {confidence:.2f}, anomaly: {is_anomaly}")
            return PredictionResult(
                is_hazardous=pred_val, 
                confidence=confidence, 
                is_anomaly=is_anomaly, 
                anomaly_score=anomaly_score
            )
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            raise PredictionError(str(e))

    def explain(self, features_dict: dict) -> Tuple[bool, float, list]:
        """Runs prediction and computes SHAP explanations using the cached explainer."""
        if self.model is None:
            raise ModelNotLoadedError("Model is not initialized.")
        if self.explainer is None:
            raise PredictionError("SHAP Explainer was not successfully cached during model load.")
            
        try:
            # 1. Get standard prediction first
            res = self.predict(features_dict)
            pred_val = res.is_hazardous
            confidence = res.confidence
            
            # 2. Extract pipeline and transform input data for the explainer
            pipeline = getattr(self.model, '_model_impl', None)
            if hasattr(pipeline, "sklearn_model"):
                pipeline = pipeline.sklearn_model
                
            preprocessor = pipeline.named_steps.get("preprocessor")
            
            df = pd.DataFrame([features_dict])
            transformed_features = preprocessor.transform(df)
            
            # Get feature names if possible
            if hasattr(preprocessor, "get_feature_names_out"):
                feature_names = preprocessor.get_feature_names_out()
            else:
                feature_names = [f"feature_{i}" for i in range(transformed_features.shape[1])]
                
            # 3. Compute SHAP values
            shap_vals = self.explainer.shap_values(transformed_features)
            
            # Explicit check for SHAP value format based on model type
            if isinstance(shap_vals, list):
                self.logger.info("SHAP values returned as a list (likely Random Forest). Extracting index 1 for hazardous class.")
                shap_vals = shap_vals[1]
            else:
                self.logger.info("SHAP values returned as a single array (likely XGBoost/LightGBM).")
                
            if shap_vals.ndim == 2:
                shap_vals = shap_vals[0]
                
            # Flatten transformed features if needed (e.g. if it's a sparse matrix)
            try:
                feat_values = transformed_features.toarray()[0]
            except AttributeError:
                feat_values = transformed_features[0]
                
            # 4. Map contributions
            contributions = []
            for name, val, shap_val in zip(feature_names, feat_values, shap_vals):
                contributions.append({
                    "feature_name": name,
                    "feature_value": float(val),
                    "shap_contribution": float(shap_val)
                })
                
            # Sort by absolute contribution descending
            contributions = sorted(contributions, key=lambda x: abs(x["shap_contribution"]), reverse=True)
            
            return pred_val, confidence, contributions
            
        except Exception as e:
            self.logger.error(f"Explanation failed: {e}")
            raise PredictionError(f"Failed to generate SHAP explanation: {e}")
