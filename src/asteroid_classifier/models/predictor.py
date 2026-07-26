import mlflow
import pandas as pd
from typing import Tuple
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.exceptions import ModelNotLoadedError, PredictionError
import os
import dagshub

class AsteroidPredictor:
    def __init__(self, model_uri: str):
        self.logger = get_logger()
        self.model_uri = model_uri
        self.model = None
        self.explainer = None
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


    def predict(self, features_dict: dict) -> Tuple[bool, float]:
        if self.model is None:
            raise ModelNotLoadedError("Model is not initialized.")
        
        try:
            # Map Pydantic dict to explicitly named DataFrame columns precisely as MLflow model expects
            df = pd.DataFrame([features_dict])
            
            # Use pyfunc model to predict
            prediction = self.model.predict(df)
            
            # Predict Proba if available
            if hasattr(self.model, '_model_impl') and hasattr(self.model._model_impl, 'predict_proba'):
                proba = self.model._model_impl.predict_proba(df)[0]
                confidence = float(max(proba))
            else:
                confidence = 1.0 # fallback
                
            pred_val = bool(prediction[0])
            
            self.logger.info(f"Made prediction: {pred_val} with confidence: {confidence:.2f}")
            return pred_val, confidence
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
            pred_val, confidence = self.predict(features_dict)
            
            # 2. Extract pipeline and transform input data for the explainer
            pipeline = self.model._model_impl
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
