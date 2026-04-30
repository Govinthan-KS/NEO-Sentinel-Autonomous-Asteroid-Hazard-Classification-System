import os
import requests
from typing import Optional, Dict, Any
from asteroid_classifier.core.logging import get_logger

logger = get_logger()

def _send_discord_message(content: str, embeds: Optional[list] = None) -> bool:
    """Internal helper to push messages to Discord."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    logger.debug("[Discord] Webhook URL loaded.")
    
    if not webhook_url or webhook_url == "your_discord_webhook_url_here":
        logger.warning("[Discord] DISCORD_WEBHOOK_URL not set or is placeholder; skipping notification.")
        return False
        
    payload: Dict[str, Any] = {"content": content}
    if embeds:
        payload["embeds"] = embeds

    try:
        response = requests.post(webhook_url, json=payload, timeout=5.0)
        response.raise_for_status()
        logger.info("[Discord] Notification sent successfully.")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"[Discord] HTTP Error {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"[Discord] Failed to send notification: {e}")
        return False

def notify_high_hazard(confidence: float, features: dict) -> bool:
    """Triggered on >90% prediction confidence."""
    content = f"🚨 **HIGH HAZARD ALERT** 🚨\nAsteroid detected with {confidence*100:.2f}% confidence!"
    embeds = [{
        "title": "Asteroid Telemetry",
        "color": 16711680, # Red
        "description": "\n".join([f"**{k}**: {v}" for k, v in features.items()])
    }]
    return _send_discord_message(content, embeds)

def notify_pipeline_event(event_name: str, details: str) -> bool:
    """Triggered on retrain start/end or champion promotion."""
    content = f"🔄 **PIPELINE EVENT**: {event_name}"
    embeds = [{
        "description": details,
        "color": 3447003 # Blue
    }]
    return _send_discord_message(content, embeds)

def notify_health_issue(issue_type: str, details: str) -> bool:
    """Triggered on 500 error or similar health issues."""
    content = f"💀 **SYSTEM HEALTH ISSUE**: {issue_type}"
    embeds = [{
        "description": details,
        "color": 16711680 # Red
    }]
    return _send_discord_message(content, embeds)

def notify_drift_detected(drift_score: float, feature_name: str) -> bool:
    """Triggered when drift is detected."""
    content = f"⚠️ **DRIFT DETECTED**\nWarning: `{feature_name}` drift detected (Score: {drift_score:.4f}). Triggering automated retraining."
    embeds = [{
        "title": "Drift Metrics",
        "description": f"Feature: {feature_name}\nScore: {drift_score:.4f}",
        "color": 16766720 # Yellow
    }]
    return _send_discord_message(content, embeds)
