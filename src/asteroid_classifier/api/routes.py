from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
import os
import datetime
from asteroid_classifier.api.schemas import AsteroidFeatures, PredictionResponse, ExplainResponse, ContactRequest
from asteroid_classifier.core.logging import get_logger

from asteroid_classifier.data.prediction_logger import log_prediction
from asteroid_classifier.api.auth import get_current_user, rate_limit_predict, rate_limit_contact

import resend
resend.api_key = os.getenv("RESEND_API_KEY", "")

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
async def predict(
    request: Request, 
    features: AsteroidFeatures, 
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(rate_limit_predict)
):
    logger.info(f"Received prediction request shape: {features.model_dump()} from user {current_user.get('user_id')}")
    predictor = request.app.state.predictor
    
    res = predictor.predict(features.model_dump())
    
    response = PredictionResponse(
        is_hazardous=res.is_hazardous,
        confidence=res.confidence,
        is_anomaly=res.is_anomaly,
        anomaly_score=res.anomaly_score,
        model_alias="champion"
    )
    logger.info(f"Returning prediction: is_hazardous={res.is_hazardous}, confidence={res.confidence:.4f}")



    timestamp = datetime.datetime.utcnow().isoformat()
    model_version = getattr(predictor, "model_uri", "unknown")
    background_tasks.add_task(_append_to_parquet, features.model_dump(), model_version, res.confidence, timestamp)
    
    # ── Database Logging ──
    db_run_id = getattr(predictor, "run_id", "unknown")
    background_tasks.add_task(log_prediction, features.model_dump(), res, db_run_id)

    return response

@router.post("/explain", response_model=ExplainResponse)
async def explain(
    request: Request, 
    features: AsteroidFeatures,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(rate_limit_predict)
):
    logger.info(f"Received explanation request shape: {features.model_dump()} from user {current_user.get('user_id')}")
    predictor = request.app.state.predictor

    try:
        is_hazardous, confidence, contributions = predictor.explain(features.model_dump())
        response = ExplainResponse(
            is_hazardous=is_hazardous, 
            confidence=confidence, 
            explanations=contributions
        )
        logger.info(f"Returning explanation: is_hazardous={is_hazardous}, confidence={confidence:.4f}")
        return response
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contact", response_model=dict)
async def contact(
    request: Request,
    payload: ContactRequest,
    current_user: dict | None = Depends(rate_limit_contact)
):
    if payload.honeypot:
        logger.info("Bot detected via honeypot. Ignoring contact request.")
        return {"status": "ok"}
    
    dest_email = os.getenv("CONTACT_DESTINATION_EMAIL")
    if not dest_email or not resend.api_key:
        logger.error("Resend API key or destination email not configured.")
        raise HTTPException(status_code=500, detail="Email configuration error.")
        
    user_id = current_user.get("user_id") if current_user else "Guest"
    
    html_content = f"""
    <div style="font-family: monospace; background-color: #05070d; color: #c7d3ee; padding: 20px;">
        <h2 style="color: #a3e635; border-bottom: 1px solid #1a2333; padding-bottom: 10px;">NEO-Sentinel Support Request</h2>
        <p><strong>From:</strong> {payload.name} &lt;{payload.email}&gt;</p>
        <p><strong>User ID:</strong> {user_id}</p>
        <p><strong>Subject:</strong> {payload.subject}</p>
        <div style="background-color: #0a0d16; padding: 15px; border: 1px solid #1a2333; border-radius: 5px; margin-top: 20px;">
            {payload.message}
        </div>
    </div>
    """
    
    try:
        resend.Emails.send({
            "from": "NEO-Sentinel <onboarding@resend.dev>",
            "to": dest_email,
            "subject": f"Support Request: {payload.subject}",
            "html": html_content,
            "reply_to": payload.email
        })
        logger.info(f"Contact email sent successfully from {payload.email}")
        return {"status": "ok", "message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email via Resend: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email.")
