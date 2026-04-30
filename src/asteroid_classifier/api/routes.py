from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import os
import datetime
from asteroid_classifier.api.schemas import AsteroidFeatures, PredictionResponse
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.utils.notifications import notify_high_hazard

router = APIRouter()
logger = get_logger()

LOG_FLAG_FILE = "data/logging_enabled.flag"
PARQUET_FILE = "data/production_logs.parquet"

def _append_to_parquet(features_dict: dict, model_version: str, confidence: float, timestamp: str):
    try:
        if not os.path.exists(LOG_FLAG_FILE):
            return
            
        record = {
            "timestamp": timestamp,
            "model_version": model_version,
            "confidence": confidence,
            **features_dict
        }
        df = pd.DataFrame([record])
        
        if os.path.exists(PARQUET_FILE):
            existing_df = pd.read_parquet(PARQUET_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
            
        df.to_parquet(PARQUET_FILE, index=False)
        logger.info(f"{timestamp} | INFO | api | predict | Parquet appended.")
    except Exception as e:
        logger.error(f"Failed to append to parquet: {e}")


@router.get("/health", response_class=JSONResponse)
async def health() -> dict:
    """Liveness probe — returns 200 {"status": "ok"} when the API is running."""
    logger.info("Health check requested")
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, features: AsteroidFeatures, background_tasks: BackgroundTasks):
    logger.info(f"Received prediction request shape: {features.model_dump()}")
    predictor = request.app.state.predictor

    is_hazardous, confidence = predictor.predict(features.model_dump())

    response = PredictionResponse(is_hazardous=is_hazardous, confidence=confidence)
    logger.info(f"Returning prediction: is_hazardous={is_hazardous}, confidence={confidence:.4f}")

    if confidence > 0.90:
        try:
            notify_high_hazard(confidence, features.model_dump())
        except Exception as e:
            logger.error(f"Failed to send Discord alert synchronously: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    timestamp = datetime.datetime.utcnow().isoformat()
    model_version = getattr(predictor, "model_uri", "unknown")
    background_tasks.add_task(_append_to_parquet, features.model_dump(), model_version, confidence, timestamp)

    return response
