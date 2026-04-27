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
        self._load_model()

    def _load_model(self):
        try:
            # DagsHub auth is bootstrapped in main.py before this is called.
            # Calling dagshub.init() again here would reset state and risk
            # triggering an interactive OAuth prompt in headless environments.
            self.logger.info(f"[NEO-Sentinel] Loading MLflow model from: {self.model_uri}")
            self.model = mlflow.pyfunc.load_model(self.model_uri)
            self.logger.info("[NEO-Sentinel] Model loaded successfully.")
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
