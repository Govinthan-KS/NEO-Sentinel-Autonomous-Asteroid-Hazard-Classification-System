import os
import pandas as pd
from pathlib import Path
from asteroid_classifier.core.logging import get_logger

logger = get_logger()

PARQUET_FILE = "data/production_logs.parquet"

def initialize_parquet_schema():
    """Initializes the Parquet file with the correct schema if it doesn't exist."""
    if not os.path.exists(PARQUET_FILE):
        try:
            # We import here to avoid circular imports if needed
            from asteroid_classifier.api.schemas import AsteroidFeatures
            
            # Get the features defined in the Pydantic schema
            feature_columns = list(AsteroidFeatures.model_fields.keys())
            columns = ["timestamp", "model_version", "confidence"] + feature_columns
            
            df = pd.DataFrame(columns=columns)
            
            Path(PARQUET_FILE).parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(PARQUET_FILE, index=False)
            logger.info(f"Initialized Parquet schema at {PARQUET_FILE} with columns: {columns}")
        except Exception as e:
            logger.error(f"Failed to initialize Parquet schema: {e}")
