from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from asteroid_classifier.api.schemas import AsteroidFeatures, PredictionResponse
from asteroid_classifier.core.logging import get_logger

router = APIRouter()
logger = get_logger()


@router.get("/health", response_class=JSONResponse)
async def health() -> dict:
    """Liveness probe — returns 200 {"status": "ok"} when the API is running."""
    logger.info("Health check requested")
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, features: AsteroidFeatures):
    logger.info(f"Received prediction request shape: {features.model_dump()}")
    predictor = request.app.state.predictor

    is_hazardous, confidence = predictor.predict(features.model_dump())

    response = PredictionResponse(is_hazardous=is_hazardous, confidence=confidence)
    logger.info(f"Returning prediction: is_hazardous={is_hazardous}, confidence={confidence:.4f}")

    return response
