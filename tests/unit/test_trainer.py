import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from asteroid_classifier.models.trainer import train_model
from asteroid_classifier.core.exceptions import ModelPromotionError

@patch("asteroid_classifier.models.trainer.mlflow")
def test_train_model_hybrid_smote(mock_mlflow):
    """
    Test the hybrid trainer fallback for calculate_pos_weight when use_smote is False.
    """
    # Dummy data
    X_train = pd.DataFrame({
        'absolute_magnitude_h': [20.0, 22.1, 21.0, 19.5],
        'estimated_diameter_min_km': [0.1, 0.3, 0.2, 0.4],
        'estimated_diameter_max_km': [0.2, 0.5, 0.3, 0.6],
        'relative_velocity_kmph': [15000, 20000, 18000, 16000],
        'miss_distance_km': [1e6, 2e6, 1.5e6, 1.2e6],
        'orbiting_body': ['Earth', 'Earth', 'Earth', 'Earth']
    })
    y_train = np.array([0, 0, 0, 1]) # Highly imbalanced

    X_test = X_train.copy()
    y_test = y_train.copy()
    
    training_config = {
        "use_smote": False,
        "mlflow_tracking_uri": "sqlite:///mlruns.db",
        "thresholds": {"recall": 0.0} # Set to basically 0 to bypass promotion failure in test
    }
    
    model_config = {
        "model_type": "xgboost",
        "n_estimators": 5,
        "scale_pos_weight": 1 # Should dynamically be overwritten to 3
    }
    
    with patch("asteroid_classifier.models.trainer.XGBClassifier") as mock_xgb:
        # Mocking its internal sklearn-like methods to avoid running actual fitting errors
        mock_pipeline_inst = MagicMock()
        mock_xgb.return_value = mock_pipeline_inst
        
        # Override evaluate_model to return dummy passing metrics
        with patch("asteroid_classifier.models.trainer.evaluate_model", return_value={"recall": 1.0}):
            pipeline, metrics = train_model(X_train, y_train, X_test, y_test, training_config, model_config)
            
            # Assert that scale_pos_weight was specifically set to num_neg (3) / num_pos (1) = 3.0
            mock_xgb.assert_called_once_with(n_estimators=5, scale_pos_weight=3.0)
            mock_mlflow.start_run.assert_called_once()
            mock_mlflow.log_params.assert_called()
            mock_mlflow.sklearn.log_model.assert_called() # Should log preprocessor and model
