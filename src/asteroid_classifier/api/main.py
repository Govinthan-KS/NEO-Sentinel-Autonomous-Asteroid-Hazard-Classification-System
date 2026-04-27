import os
import time
import dagshub
import mlflow
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import gradio as gr

from asteroid_classifier.api.routes import router
from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.config import get_config
from asteroid_classifier.models.predictor import AsteroidPredictor
from asteroid_classifier.core.exceptions import AsteroidPipelineError
from asteroid_classifier.ui.gradio_app import build_ui

logger = get_logger()


def _bootstrap_dagshub() -> None:
    """
    Forces headless DagsHub/MLflow authentication from environment variables.
    Must be called before any other MLflow or DagsHub operation.

    DAGSHUB_NON_INTERACTIVE=1  — SDK-level kill-switch for OAuth flows.
    DAGSHUB_USER_TOKEN         — primary bypass key read by the DagsHub SDK.
    Both are set before dagshub.init() is called so no prompt is possible.

    Raises RuntimeError immediately if any required secret is absent.
    """
    # Kill-switch must be set FIRST — before any SDK import side-effects fire
    os.environ["DAGSHUB_NON_INTERACTIVE"] = "1"

    token      = os.getenv("DAGSHUB_TOKEN")
    repo_owner = os.getenv("DAGSHUB_REPO_OWNER")
    repo_name  = os.getenv("DAGSHUB_REPO_NAME")

    missing = [
        name for name, val in {
            "DAGSHUB_TOKEN":      token,
            "DAGSHUB_REPO_OWNER": repo_owner,
            "DAGSHUB_REPO_NAME":  repo_name,
        }.items() if not val
    ]
    if missing:
        raise RuntimeError(
            f"[NEO-Sentinel] Missing required environment variables for headless auth: "
            f"{', '.join(missing)}. "
            "Set these in HuggingFace Spaces → Settings → Repository Secrets."
        )

    # Map to the env var the DagsHub SDK reads for non-interactive login
    os.environ["DAGSHUB_USER_TOKEN"] = token

    # Explicit strings — never rely on SDK auto-discovery in a headless env
    dagshub.init(
        repo_owner=str(repo_owner),
        repo_name=str(repo_name),
        mlflow=True,
    )
    logger.info("[NEO-Sentinel] DagsHub headless auth initialised successfully.")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"[NEO-Sentinel] MLflow tracking URI: {tracking_uri}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[NEO-Sentinel] Initializing API Lifespan...")

    # ── Step 1: headless auth — must run before any MLflow/DagsHub call ──
    _bootstrap_dagshub()

    # ── Step 2: load champion model from registry ─────────────────────────
    cfg = get_config()
    model_uri = cfg.get("api", {}).get("model", {}).get(
        "registry_uri", "models:/asteroid-hazard-classifier@champion"
    )
    logger.info(f"[NEO-Sentinel] Loading model from registry: {model_uri}")
    app.state.predictor = AsteroidPredictor(model_uri=model_uri)
    logger.info("[NEO-Sentinel] API is ready to accept traffic.")
    yield
    # Shutdown
    logger.info("[NEO-Sentinel] Shutting down API...")

app = FastAPI(title="Asteroid Hazard Classifier", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # Suppress Gradio's internal polling/queue paths to keep logs clean
    _noisy = ("/queue", "/run", "/info", "/heartbeat", "/upload", "/theme.css")
    if not any(request.url.path.startswith(p) for p in _noisy):
        logger.info(
            f"Request {request.method} {request.url.path} "
            f"completed in {process_time:.4f}s → {response.status_code}"
        )
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    status_code = 500
    if isinstance(exc, AsteroidPipelineError):
        status_code = 400
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "message": str(exc)}
    )

app.include_router(router)


@app.get("/health", tags=["ops"])
async def health_check():
    """Liveness probe for the HuggingFace Spaces load balancer."""
    return {"status": "ok", "service": "NEO-Sentinel"}

class PredictorWrapper:
    """Wrapper to dynamically access the loaded predictor from app state within Gradio."""
    def predict(self, features):
        return app.state.predictor.predict(features)

wrapper = PredictorWrapper()
demo = build_ui(wrapper)

# Mount Gradio at root / so HF Spaces load balancer finds the UI on port 7860.
# FastAPI's own routes (/health, /predict, etc.) are matched first;
# unmatched paths fall through to Gradio.
app = gr.mount_gradio_app(app, demo, path="/")

