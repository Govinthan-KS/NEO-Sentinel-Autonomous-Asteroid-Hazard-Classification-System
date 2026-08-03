from pydantic import BaseModel, Field, model_validator

from typing import Literal

class AsteroidFeatures(BaseModel):
    absolute_magnitude_h: float = Field(..., gt=0, lt=50, description="Absolute magnitude H (brightness proxy)")
    estimated_diameter_min_km: float = Field(..., gt=0, le=1000, description="Minimum estimated diameter in km")
    estimated_diameter_max_km: float = Field(..., gt=0, le=1000, description="Maximum estimated diameter in km")
    relative_velocity_kmph: float = Field(..., ge=0, le=300000, description="Speed relative to Earth in km/h")
    miss_distance_km: float = Field(..., ge=0, description="Closest approach distance in km")
    orbiting_body: Literal["Earth"] = Field(default="Earth", description="Body it orbits (must be Earth)")

    @model_validator(mode='after')
    def check_diameters(self):
        if self.estimated_diameter_max_km < self.estimated_diameter_min_km:
            raise ValueError('estimated_diameter_max_km must be greater than or equal to estimated_diameter_min_km')
        return self

class PredictionResponse(BaseModel):
    is_hazardous: bool = Field(..., description="Hazardous classification")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    is_anomaly: bool | None = Field(default=None, description="Flagged as statistical anomaly")
    anomaly_score: float | None = Field(default=None, description="Anomaly isolation score (lower is more anomalous)")

class FeatureContribution(BaseModel):
    feature_name: str = Field(..., description="Name of the feature")
    feature_value: float = Field(..., description="Input value of the feature")
    shap_contribution: float = Field(..., description="SHAP value contribution of the feature")

class ExplainResponse(PredictionResponse):
    explanations: list[FeatureContribution] = Field(..., description="List of feature contributions via SHAP")

class ErrorResponse(BaseModel):
    error: str
    message: str

class ChampionMetricsResponse(BaseModel):
    version: str | None = None
    run_id: str | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    dvc_hash: str | None = None
    model_name: str | None = None
    run_name: str | None = None
    trained_date: str | None = None
    days_since_trained: int | None = None
    last_challenged_date: str | None = None
    days_since_last_challenge: int | None = None

class LeaderboardRun(BaseModel):
    run_id: str
    display_name: str
    recall: float | None
    precision: float | None
    f1: float | None
    roc_auc: float | None
    run_date: str
    is_champion: bool

class DashboardSummaryResponse(BaseModel):
    total_predictions: int
    hazard_rate: float
    anomaly_rate: float
    current_model_run_id: str | None

class RecentPrediction(BaseModel):
    timestamp: str
    absolute_magnitude_h: float | None
    estimated_diameter_min_km: float | None
    estimated_diameter_max_km: float | None
    relative_velocity_kmph: float | None
    miss_distance_km: float | None
    orbiting_body: str | None
    is_hazardous: bool | None
    confidence: float | None
    is_anomaly: bool | None
    anomaly_score: float | None
    model_run_id: str | None

class TrendPoint(BaseModel):
    date: str
    total: int
    hazardous: int
    anomalies: int

class ContactRequest(BaseModel):
    name: str = Field(..., description="Name of sender")
    email: str = Field(..., description="Email of sender")
    subject: str = Field(..., description="Subject of message")
    message: str = Field(..., description="Body of message")
    honeypot: str | None = Field(default=None, description="Honeypot field for bots")
