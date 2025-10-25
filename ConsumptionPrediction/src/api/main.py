"""
FastAPI application for Consumption Prediction service
"""

import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from ..utils import logger
from .schemas import (
    PredictionRequest, PredictionResponse,
    BatchPredictionRequest, BatchPredictionResponse,
    FeatureImportanceResponse, ModelMetricsResponse,
    HealthCheckResponse, ErrorResponse
)
from .prediction_service import PredictionService


# Global prediction service
prediction_service: PredictionService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown
    """
    global prediction_service

    # Startup
    logger.info("Initializing Consumption Prediction API...")
    try:
        prediction_service = PredictionService()
        logger.info("API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Consumption Prediction API...")


# Create FastAPI app
app = FastAPI(
    title="Consumption Prediction API",
    description="ML-powered predictions for airline catering consumption",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse,
         tags=["Health"])
async def health_check():
    """
    Check API health and model status
    """
    try:
        models = prediction_service.get_available_models()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "model_status": "loaded" if prediction_service.model else "error",
            "models_available": models,
            "last_trained": "2025-10-25"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/", tags=["Info"])
async def root():
    """API root endpoint with information"""
    return {
        "name": "Consumption Prediction API",
        "version": "1.0.0",
        "description": "ML-powered predictions for airline catering consumption",
        "documentation": "/docs",
        "current_model": prediction_service.model_name if prediction_service else "not_initialized"
    }


# ============================================================================
# Prediction Endpoints
# ============================================================================

@app.post("/api/v1/predict", response_model=PredictionResponse,
          tags=["Predictions"],
          summary="Single Product Prediction",
          responses={
              200: {"description": "Successful prediction"},
              400: {"description": "Invalid input"},
              500: {"description": "Prediction error"}
          })
async def predict_single(request: PredictionRequest):
    """
    Make a prediction for a single product

    Predicts optimal quantity for a specific product given flight parameters.

    **Parameters:**
    - `passenger_count`: Number of passengers on flight (1-500)
    - `product_id`: Product ID (1-10)
    - `flight_type`: Type of flight (DOMESTIC, INTERNATIONAL, CHARTER)
    - `service_type`: Service class (ECONOMY, BUSINESS)
    - `origin`: Origin airport code
    - `unit_cost`: Cost per unit in USD
    - `flight_date`: Flight date in YYYY-MM-DD format (optional)

    **Returns:**
    - `predicted_quantity`: Recommended quantity to prepare
    - `lower_bound`: 95% confidence lower bound
    - `upper_bound`: 95% confidence upper bound
    - `confidence_score`: Model confidence (0-1)
    - `expected_waste`: Expected waste quantity
    - `expected_shortage`: Probability of shortage
    - `model_used`: Which model made the prediction
    """
    try:
        result = prediction_service.predict_single(
            passenger_count=request.passenger_count,
            product_id=request.product_id,
            flight_type=request.flight_type,
            service_type=request.service_type,
            origin=request.origin,
            unit_cost=request.unit_cost,
            flight_date=request.flight_date
        )
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/api/v1/predict/batch", response_model=BatchPredictionResponse,
          tags=["Predictions"],
          summary="Batch Flight Predictions",
          responses={
              200: {"description": "Successful batch predictions"},
              400: {"description": "Invalid input"},
              500: {"description": "Prediction error"}
          })
async def predict_batch(request: BatchPredictionRequest):
    """
    Make predictions for an entire flight

    Predicts optimal quantities for all products on a flight.

    **Parameters:**
    - `passenger_count`: Total passengers on flight
    - `flight_type`: Type of flight (DOMESTIC, INTERNATIONAL, CHARTER)
    - `service_type`: Service class (ECONOMY, BUSINESS)
    - `origin`: Origin airport code
    - `flight_date`: Flight date in YYYY-MM-DD format (optional)
    - `products`: List of product IDs to predict (optional, defaults to all)

    **Returns:**
    - `flight_id`: Generated unique flight identifier
    - `passenger_count`: Total passengers
    - `total_predicted_cost`: Total predicted cost of items
    - `total_predicted_waste_cost`: Expected total waste cost
    - `total_predicted_quantity`: Sum of all product predictions
    - `predictions`: List of per-product predictions
    - `model_used`: Which model made predictions
    - `generated_at`: Timestamp of prediction
    """
    try:
        result = prediction_service.predict_batch(
            passenger_count=request.passenger_count,
            flight_type=request.flight_type,
            service_type=request.service_type,
            origin=request.origin,
            flight_date=request.flight_date,
            products=request.products
        )
        return result
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


# ============================================================================
# Model Info Endpoints
# ============================================================================

@app.get("/api/v1/model/feature-importance", response_model=FeatureImportanceResponse,
         tags=["Model Info"],
         summary="Get Feature Importance")
async def get_feature_importance(top_n: int = Query(10, ge=1, le=32, description="Number of top features")):
    """
    Get feature importance scores for the current model

    Shows which input features have the most impact on predictions.

    **Parameters:**
    - `top_n`: Number of top features to return (1-32, default 10)

    **Returns:**
    - `model`: Current model name
    - `top_features`: Dict of feature names and importance scores
    - `total_features`: Total number of features in the model
    """
    try:
        # Adjust the request to feature engineer
        result = prediction_service.get_feature_importance(top_n=top_n)
        return result
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feature importance")


@app.get("/api/v1/model/metrics", response_model=ModelMetricsResponse,
         tags=["Model Info"],
         summary="Get Model Performance Metrics")
async def get_model_metrics():
    """
    Get performance metrics for the current model

    Returns ML metrics (MAE, RMSE, MAPE, R²) and business metrics (waste rate, accuracy, etc).

    **Returns:**
    - `model`: Current model name
    - `training_date`: Date when model was trained
    - `ml_metrics`: Machine learning metrics
    - `business_metrics`: Business-oriented metrics
    """
    try:
        result = prediction_service.get_model_metrics()
        return result
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


# ============================================================================
# Model Management Endpoints
# ============================================================================

@app.post("/api/v1/model/switch/{model_name}",
          tags=["Model Management"],
          summary="Switch Active Model")
async def switch_model(model_name: str):
    """
    Switch to a different trained model

    Available models: xgboost, ensemble, random_forest

    **Parameters:**
    - `model_name`: Name of model to switch to

    **Returns:**
    - `success`: Whether the switch was successful
    - `current_model`: New active model name
    - `available_models`: List of available models
    """
    try:
        success = prediction_service.switch_model(model_name)
        if success:
            return {
                "success": True,
                "current_model": prediction_service.model_name,
                "available_models": prediction_service.get_available_models()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_name} not available")
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch model")


@app.get("/api/v1/model/list",
         tags=["Model Management"],
         summary="List Available Models")
async def list_models():
    """
    Get list of available models

    **Returns:**
    - `available_models`: List of model names
    - `current_model`: Currently active model
    """
    try:
        return {
            "available_models": prediction_service.get_available_models(),
            "current_model": prediction_service.model_name
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": "HTTPException",
        "message": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "InternalServerError",
        "message": "An unexpected error occurred",
        "details": str(exc)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
