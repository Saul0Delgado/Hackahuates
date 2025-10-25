"""
API module for Consumption Prediction service
"""

from .main import app
from .prediction_service import PredictionService
from .schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    FeatureImportanceResponse,
    ModelMetricsResponse,
    HealthCheckResponse,
    ErrorResponse
)

__all__ = [
    'app',
    'PredictionService',
    'PredictionRequest',
    'PredictionResponse',
    'BatchPredictionRequest',
    'BatchPredictionResponse',
    'FeatureImportanceResponse',
    'ModelMetricsResponse',
    'HealthCheckResponse',
    'ErrorResponse'
]
