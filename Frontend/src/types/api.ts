/**
 * API Request/Response Types
 *
 * This file defines the TypeScript interfaces that match the backend
 * Consumption Prediction API (FastAPI with Pydantic models)
 */

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface PredictionRequest {
  passenger_count: number;
  product_id: number;
  flight_type: string;
  service_type: string;
  origin: string;
  unit_cost?: number;
  flight_date?: string;
}

export interface BatchPredictionRequest {
  passenger_count: number;
  flight_type: string;
  /**
   * Service type: Must be one of:
   * - "Retail" (standard service, ~67 units avg consumption)
   * - "Pick & Pack" (packaged service, ~107 units avg consumption)
   */
  service_type: string;
  origin: string;
  flight_date?: string;
  products: number[];
}

// ============================================================================
// RESPONSE TYPES - SINGLE PREDICTION
// ============================================================================

/**
 * Single product prediction response from ML model
 *
 * @field predicted_quantity - Recommended quantity to prepare (Q50 median from model)
 * @field lower_bound - Conservative estimate (Q5 = 5th percentile, 95% CI lower)
 * @field upper_bound - Optimistic estimate (Q95 = 95th percentile, 95% CI upper)
 * @field confidence_score - Model R² score (0.9898 for XGBoost = 98.98% variance explained)
 *                          NOTE: This is NOT the confidence in the prediction interval,
 *                          but rather the model's overall ability to explain data variance
 * @field expected_waste - Expected quantity that will be returned/not consumed
 *                        Calculated as: predicted_quantity × historical_return_rate
 *                        Based on dataset's Quantity_Returned / Standard_Specification_Qty ratio
 * @field expected_shortage - Probability of running out (0.10 if predicted < passengers, else 0.0)
 * @field model_used - Name of the model used ("xgboost", "ensemble", "random_forest")
 */
export interface PredictionResponse {
  predicted_quantity: number;
  lower_bound: number;
  upper_bound: number;
  confidence_score: number; // This is Model R², not interval confidence
  expected_waste: number; // Calculated from historical return rates
  expected_shortage: number;
  model_used: string;
}

// ============================================================================
// RESPONSE TYPES - BATCH PREDICTION
// ============================================================================

/**
 * Per-product prediction within batch response
 *
 * Contains all fields from PredictionResponse but at product level
 *
 * @field expected_shortage - Probability of shortage (0.0 = no risk, 0.1 = 10% risk if predicted < passengers)
 */
export interface ProductPrediction {
  product_id: number;
  predicted_quantity: number;
  lower_bound: number;
  upper_bound: number;
  confidence_score: number; // Model R² (XGBoost: 0.9898)
  expected_waste: number; // Quantity × historical_return_rate
  expected_shortage: number; // 0.0 or 0.1 (probability of shortage)
}

/**
 * Batch prediction response for entire flight
 *
 * Aggregates predictions for multiple products on a single flight
 *
 * @field flight_id - Generated unique flight identifier (format: "INT-MEX-2025-10-26-001")
 * @field passenger_count - Total passengers on flight (from input)
 * @field total_predicted_quantity - Sum of all predicted_quantity values
 * @field total_predicted_cost - Sum of (predicted_quantity × unit_cost) for all products
 * @field total_predicted_waste_cost - Sum of (expected_waste × unit_cost) for all products
 *                                     Based on historical return rates
 * @field predictions - Array of per-product predictions
 * @field model_used - Active model name ("xgboost" recommended)
 * @field generated_at - ISO timestamp when prediction was made
 */
export interface BatchPredictionResponse {
  flight_id: string;
  passenger_count: number;
  total_predicted_quantity: number; // Sum of all product predictions
  total_predicted_cost: number; // Sum of all product costs
  total_predicted_waste_cost: number; // Sum of (waste × unit_cost)
  predictions: ProductPrediction[];
  model_used: string;
  generated_at: string; // ISO datetime
}

// ============================================================================
// MODEL INFO TYPES
// ============================================================================

/**
 * Model performance metrics
 *
 * @field ml_metrics - Machine learning metrics from test set
 * @field business_metrics - Operationally relevant metrics
 */
export interface ModelMetrics {
  model: string;
  training_date: string;
  ml_metrics: {
    MAE: number; // Mean Absolute Error
    RMSE: number; // Root Mean Squared Error
    MAPE: number; // Mean Absolute Percentage Error
    R2: number; // R² = variance explained (0.9898 for XGBoost)
  };
  business_metrics: {
    waste_rate_percent: number; // % of prepared items that are returned
    shortage_rate_percent: number; // % of cases with insufficient quantity
    accuracy_rate_percent: number; // Overall prediction accuracy
    avg_waste_qty: number; // Average units wasted per product
  };
}

/**
 * Feature importance for model interpretation
 *
 * @field feature - Feature/variable name
 * @field importance - Importance score (0-1, where 1 = most important)
 */
export interface FeatureImportance {
  feature: string;
  importance: number;
}

/**
 * Feature importance response from backend
 *
 * @field model - Model name (xgboost, ensemble, random_forest)
 * @field top_features - Dictionary of top features and their importance scores
 * @field total_features - Total number of features in the model
 */
export interface FeatureImportanceResponse {
  model: string;
  top_features: Record<string, number>; // Dict of feature_name: importance_score
  total_features: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  models_available: string[];
  active_model: string;
}

// ============================================================================
// FIELD INTERPRETATION GUIDE
// ============================================================================

/**
 * IMPORTANT: How to interpret prediction results
 *
 * PREDICTED QUANTITY:
 *   - This is the Q50 (median) prediction from the model
 *   - Interpretation: "Prepare this many units"
 *   - Example: predicted_quantity = 145 → "Prepare 145 units of this product"
 *
 * CONFIDENCE INTERVAL (lower_bound to upper_bound):
 *   - lower_bound = Q5 (5th percentile)
 *   - upper_bound = Q95 (95th percentile)
 *   - Interpretation: "In 90% of cases, actual need will fall within this range"
 *   - Example: 142-148 → "90% confident need will be between 142 and 148"
 *
 * CONFIDENCE SCORE:
 *   - This is the Model's R² score, NOT the interval confidence
 *   - R² = how much variance the model explains
 *   - Example: 0.9898 → "Model explains 98.98% of the variance in historical data"
 *   - Does NOT mean: "98% chance this prediction is within ±10 units"
 *
 * EXPECTED WASTE:
 *   - Quantity of items that will likely be returned/not consumed
 *   - Calculated as: predicted_quantity × historical_return_rate
 *   - historical_return_rate = (Quantity_Returned / Standard_Specification_Qty) from training data
 *   - Example: predicted = 145, return_rate = 12% → waste = 17.4 units
 *
 * EXPECTED SHORTAGE:
 *   - Probability of running out (if prediction < passenger_count)
 *   - Values: 0.10 (10% chance) if prediction < passengers, else 0.0
 *
 * TOTAL PREDICTED COST:
 *   - Sum of all products: predicted_quantity × unit_cost
 *   - Example: Product1 (100 × $0.75) + Product2 (200 × $1.50) = $375
 *
 * TOTAL PREDICTED WASTE COST:
 *   - Sum of all products: expected_waste × unit_cost
 *   - Note: This is cost of expected returns, not full waste
 */
