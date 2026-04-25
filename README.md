---
title: NEO-Sentinel | Autonomous Asteroid Hazard Classification System
emoji: ☄️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ☄️ NEO-Sentinel: Autonomous Asteroid Hazard Classification System

> **Production-grade MLOps pipeline for real-time asteroid threat classification using NASA open data.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.x-orange)](https://xgboost.readthedocs.io)
[![MLflow](https://img.shields.io/badge/MLflow-DagsHub-blue)](https://dagshub.com)
[![Docker](https://img.shields.io/badge/Docker-HF%20Spaces-2496ED?logo=docker)](https://huggingface.co)

---

## Project Overview

NEO-Sentinel: Autonomous Asteroid Hazard Classification System ingests Near-Earth Object (NEO) data from NASA's NeoWs API, trains a **high-recall binary classifier** to predict whether an asteroid is potentially hazardous, and serves predictions via a REST API and interactive Gradio UI — all in a single production-grade Docker container deployed to HuggingFace Spaces.

**Core ML Constraint:** The model is not promoted to production unless all three thresholds are met:

| Metric | Minimum Threshold | Rationale |
|--------|------------------|-----------|
| **Recall** | ≥ 0.90 | A missed hazardous asteroid is catastrophically worse than a false alarm |
| **F1 Score** | ≥ 0.85 | Balance precision with high recall |
| **ROC-AUC** | ≥ 0.92 | Full discriminability across classification thresholds |

The system prioritises **recall over precision** — the engineering equivalent of "never miss a real threat."

---

## Model Lineage

The serving layer **dynamically pulls the `@champion` model alias** from the DagsHub MLflow Model Registry at every container cold start. No model artifact is baked into the image.

```
DagsHub MLflow Registry
└── asteroid-hazard-classifier
    └── @champion  ←  loaded at runtime via mlflow.pyfunc.load_model()
```

This means a newly promoted champion model automatically becomes live on the next container restart — **zero redeployment required for model updates.**

Model name in registry: `asteroid-hazard-classifier`
Registry URI: `models:/asteroid-hazard-classifier@champion`

---

## Technical Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **ML Model** | XGBoost 2.x | Gradient-boosted binary classifier |
| **Preprocessing** | Scikit-Learn | ColumnTransformer pipeline, SMOTE oversampling |
| **Experiment Tracking** | MLflow on DagsHub | All runs, metrics, artifacts, and model registry |
| **Data Versioning** | DVC → DagsHub | Every dataset version is content-hashed and reproducible |
| **REST API** | FastAPI + Uvicorn | `POST /predict` with Pydantic telemetry validation |
| **Prediction UI** | Gradio 4.x | Interactive asteroid hazard query interface |
| **Config Management** | Hydra | Zero hardcoding — all values in `configs/*.yaml` |
| **Observability** | Loguru | Structured logs at every pipeline stage |
| **Container** | Docker (python:3.12-slim) | Single image, deployed to HuggingFace Spaces |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | `POST` | Submit asteroid telemetry, receive hazard prediction |
| `/ui` | `GET` | Gradio interactive prediction interface |
| `/health` | `GET` | Liveness check — returns `{"status": "ok"}` |
| `/docs` | `GET` | FastAPI auto-generated Swagger UI |
| `/redoc` | `GET` | FastAPI ReDoc documentation |

### Example: Prediction Request

```bash
curl -X POST https://<your-space>.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{
    "absolute_magnitude_h": 18.1,
    "estimated_diameter_min_km": 0.4,
    "estimated_diameter_max_km": 0.9,
    "relative_velocity_kmph": 62000.0,
    "miss_distance_km": 1800000.0,
    "orbiting_body": "Earth"
  }'
```

**Response:**
```json
{
  "is_potentially_hazardous": true,
  "confidence": 0.94,
  "model_alias": "@champion"
}
```

---

## Physical Telemetry Constraints

All inputs are validated by Pydantic before reaching the model. Out-of-range values are rejected with a `422 Unprocessable Entity` error:

| Feature | Valid Range | Unit |
|---------|------------|------|
| `absolute_magnitude_h` | 10 – 35 | H magnitude |
| `estimated_diameter_min_km` | 0.0001 – 100 | km |
| `estimated_diameter_max_km` | 0.0001 – 100 | km |
| `relative_velocity_kmph` | 0 – 300,000 | km/h |
| `miss_distance_km` | 0 – 100,000,000 | km |
| `orbiting_body` | Earth only | — |

---

## Runtime Configuration

All secrets are injected via **HuggingFace Spaces → Settings → Repository Secrets**. No credentials are baked into the image.

| Variable | Purpose |
|----------|---------|
| `NASA_API_KEY` | NASA NeoWs API access |
| `DAGSHUB_TOKEN` | DagsHub authentication for MLflow Registry |
| `MLFLOW_TRACKING_URI` | DagsHub MLflow server URL |
| `DAGSHUB_REPO_OWNER` | DagsHub repository owner |
| `DAGSHUB_REPO_NAME` | DagsHub repository name |

The container **validates all five variables at startup** and exits cleanly with a descriptive error if any are missing.

---

## Full MLOps Pipeline

```
[1] DATA INGESTION     NASA NeoWs API → Daily Airflow DAG → Raw JSON
        ↓
[2] DATA VALIDATION    Great Expectations → Schema + range checks
        ↓
[3] DATA VERSIONING    DVC → DagsHub remote (content-hashed, reproducible)
        ↓
[4] MODEL TRAINING     XGBoost + SMOTE → MLflow tracking on DagsHub
        ↓
[5] MODEL PROMOTION    Recall ≥ 0.90, F1 ≥ 0.85, ROC-AUC ≥ 0.92 → @champion
        ↓
[6] SERVING            FastAPI + Gradio → This HuggingFace Space ← YOU ARE HERE
        ↓
[7] DRIFT MONITORING   Evidently AI → Weekly drift reports → Retrain trigger
        ↓
[8] OBSERVABILITY      Loguru + Streamlit Admin Dashboard
        ↓
[9] CI/CD              GitHub Actions → Auto retrain + redeploy on promotion
```

---

## Repository Structure

```
asteroid-hazard-classifier/
├── configs/                    # Hydra YAML — zero hardcoding in source
│   └── api/default.yaml        # Model registry URI, host, port
├── src/asteroid_classifier/
│   ├── api/                    # FastAPI routes, schemas, main app
│   ├── models/predictor.py     # MLflow @champion model loader
│   ├── ui/gradio_app.py        # Gradio prediction interface
│   └── core/                   # Loguru, Hydra config, exceptions
├── docker/
│   ├── Dockerfile              # python:3.12-slim production image
│   └── entrypoint.sh           # Secret validation + Uvicorn bootstrap
└── pyproject.toml              # Poetry dependency manifest
```

---

## 🛠️ Local Development

Run the full dual-service stack locally using a `secrets.env` file so credentials never appear in your shell history.

**1. Create `secrets.env`** in the project root (this file is gitignored):

```env
NASA_API_KEY=your_nasa_api_key
DAGSHUB_TOKEN=your_dagshub_token
MLFLOW_TRACKING_URI=https://dagshub.com/your_owner/your_repo.mlflow
DAGSHUB_REPO_OWNER=your_dagshub_owner
DAGSHUB_REPO_NAME=your_dagshub_repo_name
```

**2. Build and run:**

```bash
docker build -f docker/Dockerfile -t neo-sentinel:local .

docker run --rm \
  --env-file secrets.env \
  -p 7860:7860 \
  -p 8501:8501 \
  neo-sentinel:local
```

**3. Verify both services:**

| Service | URL |
|---------|-----|
| Prediction API | `http://localhost:7860/health` |
| Gradio UI | `http://localhost:7860/ui` |
| Admin Dashboard | `http://localhost:8501` |

> **Note:** `secrets.env` is listed in `.gitignore` and must never be committed.

---

*Built with 🔭 NASA open data · MLflow on DagsHub · FastAPI · Gradio · XGBoost · DVC*
