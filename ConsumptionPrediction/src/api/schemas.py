"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class PredictionRequest(BaseModel):
    """Single product prediction request"""

    passenger_count: int = Field(..., ge=1, le=500, description="Number of passengers")
    product_id: int = Field(..., ge=1, le=10, description="Product ID (1-10)")
    flight_type: str = Field(..., description="Flight type: DOMESTIC, INTERNATIONAL, or CHARTER")
    service_type: str = Field(..., description="Service type: ECONOMY or BUSINESS")
    origin: str = Field(..., description="Origin city/code")
    unit_cost: float = Field(..., gt=0, description="Unit cost in USD")
    flight_date: Optional[str] = Field(default=None, description="Flight date (YYYY-MM-DD)")

    class Config:
        schema_extra = {
            "example": {
                "passenger_count": 180,
                "product_id": 1,
                "flight_type": "INTERNATIONAL",
                "service_type": "ECONOMY",
                "origin": "MEX",
                "unit_cost": 0.75,
                "flight_date": "2025-10-26"
            }
        }


class PredictionResponse(BaseModel):
    """Single product prediction response"""

    predicted_quantity: float = Field(..., description="Predicted quantity in units")
    lower_bound: float = Field(..., description="95% confidence interval lower bound")
    upper_bound: float = Field(..., description="95% confidence interval upper bound")
    confidence_score: float = Field(..., ge=0, le=1, description="Model confidence score")
    expected_waste: float = Field(..., ge=0, description="Expected waste quantity")
    expected_shortage: float = Field(..., ge=0, description="Expected shortage probability")
    model_used: str = Field(..., description="Model used for prediction (xgboost, ensemble, random_forest)")

    class Config:
        schema_extra = {
            "example": {
                "predicted_quantity": 145.2,
                "lower_bound": 142.1,
                "upper_bound": 148.3,
                "confidence_score": 0.989,
                "expected_waste": 0.85,
                "expected_shortage": 0.10,
                "model_used": "xgboost"
            }
        }


class BatchPredictionRequest(BaseModel):
    """Batch prediction request for entire flight"""

    passenger_count: int = Field(..., ge=1, le=500, description="Total number of passengers")
    flight_type: str = Field(..., description="Flight type: DOMESTIC, INTERNATIONAL, or CHARTER")
    service_type: str = Field(..., description="Service type: ECONOMY or BUSINESS")
    origin: str = Field(..., description="Origin city/code")
    flight_date: Optional[str] = Field(default=None, description="Flight date (YYYY-MM-DD)")
    products: Optional[List[int]] = Field(default=None, description="Product IDs to predict (if None, predicts all)")

    class Config:
        schema_extra = {
            "example": {
                "passenger_count": 180,
                "flight_type": "INTERNATIONAL",
                "service_type": "ECONOMY",
                "origin": "MEX",
                "flight_date": "2025-10-26",
                "products": [1, 2, 3, 4, 5]
            }
        }


class ProductPrediction(BaseModel):
    """Single product prediction within batch"""

    product_id: int
    predicted_quantity: float
    lower_bound: float
    upper_bound: float
    confidence_score: float
    expected_waste: float
    expected_shortage: float = Field(..., ge=0, le=1, description="Probability of shortage (0.0 or 0.1)")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""

    flight_id: str = Field(..., description="Unique flight identifier")
    passenger_count: int
    total_predicted_cost: float = Field(..., description="Total predicted cost of all items")
    total_predicted_waste_cost: float = Field(..., description="Expected total waste cost")
    total_predicted_quantity: float = Field(..., description="Total predicted items")
    predictions: List[ProductPrediction] = Field(..., description="Per-product predictions")
    model_used: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "flight_id": "INTL-MEX-2025-10-26-001",
                "passenger_count": 180,
                "total_predicted_cost": 2150.50,
                "total_predicted_waste_cost": 42.30,
                "total_predicted_quantity": 890,
                "predictions": [
                    {
                        "product_id": 1,
                        "predicted_quantity": 145.2,
                        "lower_bound": 142.1,
                        "upper_bound": 148.3,
                        "confidence_score": 0.989,
                        "expected_waste": 0.85
                    }
                ],
                "model_used": "xgboost",
                "generated_at": "2025-10-26T14:30:00"
            }
        }


class FeatureImportanceResponse(BaseModel):
    """Feature importance response"""

    model: str = Field(..., description="Model name")
    top_features: Dict[str, float] = Field(..., description="Top 10 features and their importance scores")
    total_features: int = Field(..., description="Total number of features in model")

    class Config:
        schema_extra = {
            "example": {
                "model": "xgboost",
                "top_features": {
                    "Passenger_Count": 0.25,
                    "consumption_rate": 0.18,
                    "spec_per_passenger": 0.15,
                    "product_consumption_rate_mean": 0.12
                },
                "total_features": 32
            }
        }


class ModelMetricsResponse(BaseModel):
    """Model performance metrics response"""

    model: str = Field(..., description="Model name")
    training_date: str = Field(..., description="Date model was trained")
    ml_metrics: Dict[str, float] = Field(..., description="ML metrics (MAE, RMSE, MAPE, R2)")
    business_metrics: Dict[str, float] = Field(..., description="Business metrics (waste_rate, shortage_rate, etc)")

    class Config:
        schema_extra = {
            "example": {
                "model": "xgboost",
                "training_date": "2025-10-25",
                "ml_metrics": {
                    "MAE": 3.15,
                    "RMSE": 5.10,
                    "MAPE": 3.04,
                    "R2": 0.9898
                },
                "business_metrics": {
                    "waste_rate_%": 1.18,
                    "shortage_rate_%": 58.82,
                    "accuracy_rate_%": 79.83,
                    "avg_waste_qty": 0.85
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    model_status: str = Field(..., description="Model availability status")
    models_available: List[str] = Field(..., description="List of available models")
    last_trained: str = Field(..., description="Date models were last trained")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "model_status": "loaded",
                "models_available": ["xgboost", "random_forest", "ensemble"],
                "last_trained": "2025-10-25"
            }
        }


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(default=None, description="Additional error details")
