from typing import Dict, Any
import numpy as np
from sklearn.metrics import recall_score, f1_score, roc_auc_score, precision_score
from asteroid_classifier.core.exceptions import ModelPromotionError

def evaluate_model(model: Any, X_test: Any, y_test: Any) -> Dict[str, float]:
    """
    Evaluates the model on test data and returns key metrics.
    Precision is included so the promotion logic can apply its guardrail.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    metrics = {
        "recall":    float(recall_score(y_test, y_pred, zero_division=0)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "f1":        float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc":   float(roc_auc_score(y_test, y_proba)),
    }
    return metrics

def check_promotion_thresholds(metrics: Dict[str, float], thresholds: Dict[str, float]) -> bool:
    """
    Validates if metrics meet the minimum requirements for production promotion.
    Raises ModelPromotionError if they do not meet the limits, specifically prioritizing Recall.
    """
    failed_metrics = {}
    
    for metric_name, required_val in thresholds.items():
        actual_val = metrics.get(metric_name, 0.0)
        if actual_val < required_val:
            failed_metrics[metric_name] = {"actual": actual_val, "required": required_val}
            
    if failed_metrics:
        error_msg = f"Model blocked from promotion! Failed metrics: {failed_metrics}"
        raise ModelPromotionError(error_msg)
        
    return True
