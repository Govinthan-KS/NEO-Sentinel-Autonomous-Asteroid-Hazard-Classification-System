import pytest
from asteroid_classifier.models.evaluator import check_promotion_thresholds
from asteroid_classifier.core.exceptions import ModelPromotionError

def test_check_promotion_thresholds_pass():
    metrics = {"recall": 0.95, "f1": 0.88, "roc_auc": 0.94}
    thresholds = {"recall": 0.90, "f1": 0.85, "roc_auc": 0.92}
    
    # Should simply return True without exception
    result = check_promotion_thresholds(metrics, thresholds)
    assert result is True

def test_check_promotion_thresholds_fail_recall():
    metrics = {"recall": 0.88, "f1": 0.90, "roc_auc": 0.95} # fail recall
    thresholds = {"recall": 0.90, "f1": 0.85, "roc_auc": 0.92}
    
    with pytest.raises(ModelPromotionError) as exc_info:
        check_promotion_thresholds(metrics, thresholds)
        
    assert "recall" in str(exc_info.value)

def test_check_promotion_thresholds_fail_multiple():
    metrics = {"recall": 0.80, "f1": 0.80, "roc_auc": 0.90}
    thresholds = {"recall": 0.90, "f1": 0.85, "roc_auc": 0.92}
    
    with pytest.raises(ModelPromotionError) as exc_info:
        check_promotion_thresholds(metrics, thresholds)
        
    err_str = str(exc_info.value)
    assert "recall" in err_str
    assert "f1" in err_str
    assert "roc_auc" in err_str
