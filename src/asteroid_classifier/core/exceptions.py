class AsteroidPipelineError(Exception):
    """Base exception for all pipeline errors."""

    pass


class DataIngestionError(AsteroidPipelineError):
    """Raised when data ingestion from the NASA API fails."""

    pass


class DataValidationError(AsteroidPipelineError):
    """Raised when data validation against expectations fails."""

    pass


class ModelTrainingError(AsteroidPipelineError):
    """Raised when model training fails."""

    pass


class ModelPromotionError(AsteroidPipelineError):
    """Raised when model promotion thresholds are not met."""

    pass


class DriftMonitorError(AsteroidPipelineError):
    """Raised when drift monitor fails."""

    pass


class ModelNotLoadedError(AsteroidPipelineError):
    """Raised when the MLflow model fails to load at API startup."""

    pass


class PredictionError(AsteroidPipelineError):
    """Raised when a prediction fails during API request."""

    pass
