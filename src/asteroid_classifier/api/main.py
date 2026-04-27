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

    The DagsHub SDK reads DAGSHUB_USER_TOKEN for non-interactive auth.
    We map DAGSHUB_TOKEN (the name used in HF Spaces secrets) to that var
    before calling dagshub.init() so it never falls back to OAuth.

    Raises RuntimeError immediately if any required secret is absent,
    causing the container to fail fast with a clear message instead of
    hanging indefinitely on an interactive prompt.
    """
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

    # Map to the env var name the DagsHub SDK reads for non-interactive login
    os.environ["DAGSHUB_USER_TOKEN"] = token
    dagshub.init(repo_owner=repo_owner, repo_name=repo_name, mlflow=True)
    logger.info("[NEO-Sentinel] DagsHub headless auth initialised successfully.")


    # Confirm the tracking URI is set
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
    # Exclude internal gradio polling routes from cluttering INFO logs
    if not request.url.path.startswith("/ui/") and not request.url.path.startswith("/info"):
        logger.info(f"Request {request.method} {request.url.path} completed in {process_time:.4f}s with status {response.status_code}")
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

class PredictorWrapper:
    """Wrapper to dynamically access the loaded predictor from app state within Gradio."""
    def predict(self, features):
        return app.state.predictor.predict(features)

wrapper = PredictorWrapper()
demo = build_ui(wrapper)

# Mount Gradio app at the /ui path natively
app = gr.mount_gradio_app(app, demo, path="/ui")
