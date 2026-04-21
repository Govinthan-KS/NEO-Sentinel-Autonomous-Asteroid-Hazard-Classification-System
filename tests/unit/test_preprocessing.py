import pytest
import pandas as pd
import numpy as np
from asteroid_classifier.data.preprocessing import build_preprocessor

def test_preprocessor_handles_unseen_categories():
    """
    Test that the OneHotEncoder handles unknown categories elegantly
    using handle_unknown='ignore' so the pipeline doesn't crash on drift.
    """
    # Create mock training data
    train_data = pd.DataFrame({
        'absolute_magnitude_h': [20.0, 22.1],
        'estimated_diameter_min_km': [0.1, 0.3],
        'estimated_diameter_max_km': [0.2, 0.5],
        'relative_velocity_kmph': [15000, 20000],
        'miss_distance_km': [1000000, 2000000],
        'orbiting_body': ['Earth', 'Earth']
    })
    
    preprocessor = build_preprocessor()
    preprocessor.fit(train_data)
    
    # Create test data with unseen category "Mars"
    test_data = pd.DataFrame({
        'absolute_magnitude_h': [21.0],
        'estimated_diameter_min_km': [0.2],
        'estimated_diameter_max_km': [0.4],
        'relative_velocity_kmph': [18000],
        'miss_distance_km': [1500000],
        'orbiting_body': ['Mars']
    })
    
    # Should transform without throwing an error
    try:
        transformed = preprocessor.transform(test_data)
        assert transformed is not None
        assert transformed.shape[0] == 1
    except Exception as e:
        pytest.fail(f"Preprocessor threw an error on unseen category: {e}")

def test_preprocessing_aligns_features():
    train_data = pd.DataFrame({
        'absolute_magnitude_h': [20.0, 22.1],
        'estimated_diameter_min_km': [0.1, 0.3],
        'estimated_diameter_max_km': [0.2, 0.5],
        'relative_velocity_kmph': [15000, 20000],
        'miss_distance_km': [1000000, 2000000],
        'orbiting_body': ['Earth', 'Earth']
    })
    preprocessor = build_preprocessor()
    res = preprocessor.fit_transform(train_data)
    # 5 numeric numeric + 1 OHE for Earth
    assert res.shape[1] == 6
