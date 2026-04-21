import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from typing import List

NUMERIC_FEATURES = [
    'absolute_magnitude_h',
    'estimated_diameter_min_km',
    'estimated_diameter_max_km',
    'relative_velocity_kmph',
    'miss_distance_km'
]

CATEGORICAL_FEATURES = [
    'orbiting_body'
]

def build_preprocessor() -> ColumnTransformer:
    """
    Builds the Scikit-Learn ColumnTransformer for the data pipeline.
    
    Numeric features are scaled using StandardScaler.
    Categorical features are encoded using OneHotEncoder with handle_unknown='ignore'
    to prevent crashes if unseen categories (e.g., orbiting Mars) appear in production data.
    """
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERIC_FEATURES),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ],
        remainder='drop'  # Drop any un-specified features
    )
    
    return preprocessor
