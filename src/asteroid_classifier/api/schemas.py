from pydantic import BaseModel, Field, model_validator

class AsteroidFeatures(BaseModel):
    absolute_magnitude_h: float = Field(..., gt=0, lt=50, description="Absolute magnitude H (brightness proxy)")
    estimated_diameter_min_km: float = Field(..., gt=0, le=1000, description="Minimum estimated diameter in km")
    estimated_diameter_max_km: float = Field(..., gt=0, le=1000, description="Maximum estimated diameter in km")
    relative_velocity_kmph: float = Field(..., ge=0, le=300000, description="Speed relative to Earth in km/h")
    miss_distance_km: float = Field(..., ge=0, description="Closest approach distance in km")
    orbiting_body: str = Field(default="Earth", description="Body it orbits")

    @model_validator(mode='after')
    def check_diameters(self):
        if self.estimated_diameter_max_km < self.estimated_diameter_min_km:
            raise ValueError('estimated_diameter_max_km must be greater than or equal to estimated_diameter_min_km')
        return self

class PredictionResponse(BaseModel):
    is_hazardous: bool = Field(..., description="Hazardous classification")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")

class ErrorResponse(BaseModel):
    error: str
    message: str
