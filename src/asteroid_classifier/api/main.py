import time
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing API Lifespan...")
    cfg = get_config()
    model_uri = cfg.get("api", {}).get("model", {}).get("registry_uri", "models:/asteroid-hazard-classifier@champion")
    
    logger.info(f"Connecting to MLflow Registry model: {model_uri}")
    app.state.predictor = AsteroidPredictor(model_uri=model_uri)
    logger.info("API is ready to accept traffic.")
    yield
    # Shutdown
    logger.info("Shutting down API...")

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
