# Consumption Prediction API Documentation

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-10-25

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Authentication](#authentication)
6. [Error Handling](#error-handling)
7. [Model Information](#model-information)
8. [Integration Guide](#integration-guide)

---

## Overview

The Consumption Prediction API provides ML-powered predictions for optimal meal quantities in airline catering. It uses a trained XGBoost model that explains 98.98% of consumption variance with a Mean Absolute Error of just 3.15 units.

### Key Features

- **Three ML Models**: XGBoost (recommended), Ensemble, Random Forest
- **Single & Batch Predictions**: Predict for one product or entire flight
- **Confidence Intervals**: 95% confidence bounds on all predictions
- **Business Metrics**: Waste rate, shortage probability, accuracy rates
- **Model Transparency**: Feature importance and performance metrics
- **Fast Inference**: <10ms per prediction

### Performance Summary

| Model | MAE ↓ | MAPE ↓ | R² ↑ | Waste Rate |
|-------|-------|--------|------|-----------|
| **XGBoost** | **3.15** | **3.04%** | **0.9898** | **1.18%** |
| Ensemble | 4.06 | 3.98% | 0.9839 | 1.81% |
| Random Forest | 6.92 | 7.19% | 0.9605 | 3.60% |

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install fastapi uvicorn pydantic numpy pandas scikit-learn xgboost

# Navigate to project directory
cd ConsumptionPrediction

# Run the API server
python run_api.py
```

### First Request

```bash
# Test the API with a single prediction
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_count": 180,
    "product_id": 1,
    "flight_type": "INTERNATIONAL",
    "service_type": "ECONOMY",
    "origin": "MEX",
    "unit_cost": 0.75,
    "flight_date": "2025-10-26"
  }'
```

### Interactive Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Endpoints

### Health & Info

#### `GET /health`
Check API health and model availability

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_status": "loaded",
  "models_available": ["xgboost", "ensemble", "random_forest"],
  "last_trained": "2025-10-25"
}
```

#### `GET /`
Get API information

---

## Prediction Endpoints

### `POST /api/v1/predict`

Single product prediction for a specific product on a flight.

**Request Schema**:
```json
{
  "passenger_count": 180,              // 1-500
  "product_id": 1,                     // 1-10
  "flight_type": "INTERNATIONAL",      // DOMESTIC, INTERNATIONAL, CHARTER
  "service_type": "ECONOMY",           // ECONOMY, BUSINESS
  "origin": "MEX",                     // Airport code
  "unit_cost": 0.75,                   // USD
  "flight_date": "2025-10-26"          // Optional: YYYY-MM-DD
}
```

**Response Schema**:
```json
{
  "predicted_quantity": 145.2,          // Recommended quantity to prepare
  "lower_bound": 142.1,                 // 95% CI lower bound
  "upper_bound": 148.3,                 // 95% CI upper bound
  "confidence_score": 0.989,            // Model confidence (0-1)
  "expected_waste": 0.85,               // Expected waste units
  "expected_shortage": 0.10,            // Shortage probability
  "model_used": "xgboost"               // Which model made prediction
}
```

**Status Codes**:
- `200`: Successful prediction
- `400`: Invalid input parameters
- `500`: Prediction error

---

### `POST /api/v1/predict/batch`

Batch predictions for an entire flight across all or selected products.

**Request Schema**:
```json
{
  "passenger_count": 180,               // Total passengers
  "flight_type": "INTERNATIONAL",       // Flight type
  "service_type": "ECONOMY",            // Service class
  "origin": "MEX",                      // Origin airport
  "flight_date": "2025-10-26",          // Optional: YYYY-MM-DD
  "products": [1, 2, 3, 4, 5]          // Optional: product IDs (defaults to all)
}
```

**Response Schema**:
```json
{
  "flight_id": "INTL-MEX-2025-10-26-001",
  "passenger_count": 180,
  "total_predicted_cost": 2150.50,      // USD
  "total_predicted_waste_cost": 42.30,  // Expected waste cost
  "total_predicted_quantity": 890,      // Total items across all products
  "predictions": [
    {
      "product_id": 1,
      "predicted_quantity": 145.2,
      "lower_bound": 142.1,
      "upper_bound": 148.3,
      "confidence_score": 0.989,
      "expected_waste": 0.85
    },
    // ... more products
  ],
  "model_used": "xgboost",
  "generated_at": "2025-10-26T14:30:00"
}
```

---

## Model Info Endpoints

### `GET /api/v1/model/metrics`

Get performance metrics for the current model.

**Response**:
```json
{
  "model": "xgboost",
  "training_date": "2025-10-25",
  "ml_metrics": {
    "MAE": 3.15,      // Mean Absolute Error
    "RMSE": 5.10,     // Root Mean Squared Error
    "MAPE": 3.04,     // Mean Absolute Percentage Error
    "R2": 0.9898      // R-squared (variance explained)
  },
  "business_metrics": {
    "waste_rate_%": 1.18,
    "shortage_rate_%": 58.82,
    "accuracy_rate_%": 79.83,
    "avg_waste_qty": 0.85
  }
}
```

### `GET /api/v1/model/feature-importance?top_n=10`

Get feature importance scores showing which inputs matter most.

**Query Parameters**:
- `top_n`: Number of features to return (1-32, default 10)

**Response**:
```json
{
  "model": "xgboost",
  "top_features": {
    "Passenger_Count": 0.25,
    "consumption_rate": 0.18,
    "spec_per_passenger": 0.15,
    "product_consumption_rate_mean": 0.12,
    "service_product_consumption_per_pax_mean": 0.09,
    "product_consumption_rate_std": 0.07,
    "Unit_Cost": 0.06,
    "Origin_encoded": 0.04,
    "day_of_week": 0.03,
    "is_weekend": 0.02
  },
  "total_features": 32
}
```

---

## Model Management Endpoints

### `GET /api/v1/model/list`

List all available models.

**Response**:
```json
{
  "available_models": ["xgboost", "ensemble", "random_forest"],
  "current_model": "xgboost"
}
```

### `POST /api/v1/model/switch/{model_name}`

Switch to a different trained model.

**Parameters**:
- `model_name`: One of `xgboost`, `ensemble`, `random_forest`

**Response**:
```json
{
  "success": true,
  "current_model": "ensemble",
  "available_models": ["xgboost", "ensemble", "random_forest"]
}
```

---

## Request/Response Examples

### Example 1: Single Product Prediction for Domestic Flight

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_count": 150,
    "product_id": 2,
    "flight_type": "DOMESTIC",
    "service_type": "BUSINESS",
    "origin": "DF",
    "unit_cost": 1.25,
    "flight_date": "2025-10-26"
  }'
```

**Response**:
```json
{
  "predicted_quantity": 98.5,
  "lower_bound": 95.2,
  "upper_bound": 101.8,
  "confidence_score": 0.989,
  "expected_waste": 0.45,
  "expected_shortage": 0.05,
  "model_used": "xgboost"
}
```

**Interpretation**:
- Prepare **98.5 units** (between 95-102 with 95% confidence)
- Expect only **0.45 units** of waste
- Very low shortage risk (5%)

---

### Example 2: Batch Prediction for International Flight

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_count": 200,
    "flight_type": "INTERNATIONAL",
    "service_type": "ECONOMY",
    "origin": "CUN",
    "flight_date": "2025-10-26",
    "products": [1, 2, 3, 4, 5]
  }'
```

**Response**:
```json
{
  "flight_id": "INTL-CUN-2025-10-26-142",
  "passenger_count": 200,
  "total_predicted_cost": 1245.75,
  "total_predicted_waste_cost": 18.50,
  "total_predicted_quantity": 1020,
  "predictions": [
    {
      "product_id": 1,
      "predicted_quantity": 198.2,
      "lower_bound": 194.5,
      "upper_bound": 201.9,
      "confidence_score": 0.989,
      "expected_waste": 1.2
    },
    {
      "product_id": 2,
      "predicted_quantity": 156.8,
      "lower_bound": 152.1,
      "upper_bound": 161.5,
      "confidence_score": 0.989,
      "expected_waste": 0.9
    },
    // ... more products
  ],
  "model_used": "xgboost",
  "generated_at": "2025-10-26T14:32:15"
}
```

---

### Example 3: Feature Importance Query

**Request**:
```bash
curl "http://localhost:8000/api/v1/model/feature-importance?top_n=5"
```

**Response**:
```json
{
  "model": "xgboost",
  "top_features": {
    "Passenger_Count": 0.25,
    "consumption_rate": 0.18,
    "spec_per_passenger": 0.15,
    "product_consumption_rate_mean": 0.12,
    "service_product_consumption_per_pax_mean": 0.09
  },
  "total_features": 32
}
```

---

## Authentication

Currently, the API has **no authentication requirement**. For production deployment, consider:

1. **API Key**: Add header-based API key authentication
2. **OAuth 2.0**: Integrate with airline's authentication system
3. **Rate Limiting**: Add rate limiting per client/key
4. **HTTPS**: Always use HTTPS in production

Example with API key (future implementation):
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid passenger count",
  "details": {
    "field": "passenger_count",
    "error": "Value must be between 1 and 500"
  }
}
```

### Common Error Codes

| Status | Error | Cause |
|--------|-------|-------|
| 400 | ValidationError | Invalid input parameters |
| 400 | InvalidFlightType | Unknown flight_type value |
| 400 | InvalidServiceType | Unknown service_type value |
| 404 | NotFound | Endpoint does not exist |
| 500 | PredictionError | ML model inference failed |
| 500 | ModelError | Model loading/switching failed |
| 503 | ServiceUnavailable | Models not loaded |

### Example Error Response

**Request** (invalid passenger count):
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_count": 600,
    "product_id": 1,
    ...
  }'
```

**Response** (400):
```json
{
  "error": "ValidationError",
  "message": "Input should be less than or equal to 500 [type=less_than_equal, input_value=600, input_type=int]",
  "details": null
}
```

---

## Model Information

### XGBoost (Recommended)

**Performance**:
- MAE: 3.15 units
- MAPE: 3.04%
- R²: 0.9898
- Waste Rate: 1.18%
- Inference Time: <3ms

**Characteristics**:
- Gradient boosting on 32 features
- 500 estimators, max_depth=6
- Excellent for production use
- Interpretable feature importance

**Best For**: General-purpose predictions, batch processing

### Ensemble

**Performance**:
- MAE: 4.06 units
- MAPE: 3.98%
- R²: 0.9839
- Waste Rate: 1.81%
- Inference Time: <5ms

**Characteristics**:
- Weighted average: 70% XGBoost + 30% Random Forest
- More conservative (higher waste rate)
- Reduced shortage risk (55.46% vs 58.82%)

**Best For**: Risk-averse scenarios, confidence building

### Random Forest

**Performance**:
- MAE: 6.92 units
- MAPE: 7.19%
- R²: 0.9605
- Waste Rate: 3.60%
- Inference Time: <2ms

**Characteristics**:
- 300 decision trees, max_depth=15
- Good for feature importance analysis
- Faster training/inference than XGBoost

**Best For**: Exploratory analysis, feature investigation

---

## Integration Guide

### Python Client

```python
import requests

API_URL = "http://localhost:8000/api/v1"

# Single prediction
response = requests.post(
    f"{API_URL}/predict",
    json={
        "passenger_count": 180,
        "product_id": 1,
        "flight_type": "INTERNATIONAL",
        "service_type": "ECONOMY",
        "origin": "MEX",
        "unit_cost": 0.75
    }
)

prediction = response.json()
print(f"Recommended quantity: {prediction['predicted_quantity']:.1f} units")
print(f"Confidence interval: {prediction['lower_bound']:.1f} - {prediction['upper_bound']:.1f}")
```

### JavaScript/Node.js Client

```javascript
const API_URL = 'http://localhost:8000/api/v1';

async function predictConsumption(params) {
  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      passenger_count: 180,
      product_id: 1,
      flight_type: 'INTERNATIONAL',
      service_type: 'ECONOMY',
      origin: 'MEX',
      unit_cost: 0.75
    })
  });

  const prediction = await response.json();
  console.log(`Recommended quantity: ${prediction.predicted_quantity.toFixed(1)} units`);
  return prediction;
}
```

### cURL Integration

See examples in [Request/Response Examples](#requestresponse-examples) section above.

---

## Monitoring & Logging

The API logs all predictions and errors to console and file.

**Log Levels**:
- `DEBUG`: Detailed information for debugging
- `INFO`: Confirmation that things are working
- `WARNING`: Something unexpected happened
- `ERROR`: A serious problem occurred

**Check API Health**:
```bash
curl http://localhost:8000/health
```

**View Logs**:
```bash
# Real-time logs
tail -f logs/api.log

# Search for errors
grep "ERROR" logs/api.log
```

---

## Performance Tuning

### Caching Predictions

For identical inputs, consider caching results:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_prediction(passenger_count, product_id, flight_type, origin):
    # Cache key is automatically generated from function parameters
    return predict_single(...)
```

### Batch Processing

For multiple predictions, use batch endpoint:

```python
# Instead of 100 individual requests
response = requests.post(f"{API_URL}/predict/batch", json={
    "passenger_count": 200,
    "flight_type": "INTERNATIONAL",
    "service_type": "ECONOMY",
    "origin": "MEX",
    "products": list(range(1, 11))  # All 10 products
})
# Single request, ~10ms instead of ~200ms
```

### Concurrent Requests

The API uses async/await and can handle multiple concurrent requests:

```bash
# Test concurrent requests
for i in {1..100}; do
  curl -X POST "http://localhost:8000/api/v1/predict" \
    -H "Content-Type: application/json" \
    -d '{ ... }' &
done
wait
```

---

## Deployment

### Docker

```bash
# Build image
docker build -t consumption-api .

# Run container
docker run -p 8000:8000 consumption-api
```

### Production Server (Gunicorn + Uvicorn)

```bash
pip install gunicorn

gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Cloud Deployment

**AWS Lambda**:
```bash
# Package for AWS Lambda
pip install awslambdaric
```

**Google Cloud Run**:
```bash
gcloud run deploy consumption-api \
  --source . \
  --platform managed \
  --region us-central1
```

---

## Support & Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'xgboost'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue**: `Model not found at path`
```bash
# Solution: Ensure models are trained
cd ConsumptionPrediction
python -m src.training
```

**Issue**: `Connection refused: localhost:8000`
```bash
# Solution: Start the API server
python run_api.py
```

---

## API Changelog

### Version 1.0.0 (2025-10-25)

- Initial release
- Single product prediction endpoint
- Batch flight prediction endpoint
- Model performance metrics endpoint
- Feature importance endpoint
- Model switching capability
- Three trained models (XGBoost, Ensemble, Random Forest)

---

**For detailed technical information, see**: [ARCHITECTURE.md](ARCHITECTURE.md)
**For training results, see**: [TRAINING_RESULTS.md](TRAINING_RESULTS.md)
