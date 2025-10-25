/**
 * API Request/Response Types - ConsumptionPredictionv2 Product-Level
 *
 * This file defines the TypeScript interfaces that match the backend
 * Product-Level API with 6 separate models (one per category)
 */

// ============================================================================
// REQUEST TYPES
// ============================================================================

/**
 * Prediction request for product-level (category-level) forecasting
 */
export interface PredictionRequest {
  flight_key: string;
  route: string;
  passengers: number;
  flight_date: string;
  warehouse: 'Lisbon' | 'Madrid' | 'Palma de Mallorca' | 'Porto';
  num_items?: number;
  num_categories?: number;
  total_demand?: number;
  day_of_week?: number;
  month?: number;
}

/**
 * Batch prediction request (for multiple flights)
 */
export interface BatchPredictionRequest {
  flights: PredictionRequest[];
}

// ============================================================================
// RESPONSE TYPES - SINGLE PREDICTION
// ============================================================================

/**
 * Single category prediction from one of the 6 product-level models
 */
export interface CategoryPrediction {
  product: string; // e.g., "Cold Drink", "Savoury Snacks", etc.
  predicted_qty: number;
  confidence_lower: number;
  confidence_upper: number;
  recommended_qty: number;
  stockout_risk: number;
  stockout_category: 'VERY_LOW' | 'LOW' | 'MEDIUM' | 'HIGH';
  model_accuracy: number; // Accuracy ±5%
  model_r2: number; // R² score (0-1)
  model_mae: number; // Mean Absolute Error
}

/**
 * Full prediction response containing all 6 category predictions
 */
export interface PredictionResponse {
  request_id: string;
  flight_key: string;
  timestamp: string; // ISO datetime
  prediction_by_product: {
    [key: string]: CategoryPrediction;
  };
  total_summary: {
    total_recommended_qty: number;
    breakdown: string;
  };
  business_metrics: {
    expected_waste_units: number;
    expected_waste_cost: number;
    efficiency_improvement: number;
    estimated_savings: number;
  };
}

// ============================================================================
// RESPONSE TYPES - BATCH PREDICTION
// ============================================================================

/**
 * Batch prediction response for multiple flights
 */
export interface BatchPredictionResponse {
  batch_id: string;
  timestamp: string;
  total_requests: number;
  successful: number;
  failed: number;
  predictions: PredictionResponse[];
  summary: {
    total_predicted_quantity: number;
    average_accuracy: number;
  };
}

// ============================================================================
// MODEL METRICS & INFO
// ============================================================================

/**
 * Performance metrics for a single model (one category)
 */
export interface CategoryModelMetrics {
  category: string;
  r2: number; // Test R²
  mae: number; // Test MAE
  rmse: number; // Test RMSE
  accuracy_within_5pct: number; // Test accuracy
  train_samples: number;
  test_samples: number;
  target_mean: number;
  target_std: number;
  model_path: string;
  n_trees: number;
}

/**
 * Aggregated metrics for all 6 models
 */
export interface ModelMetricsMulti {
  models: {
    [category: string]: CategoryModelMetrics;
  };
  average_performance: {
    avg_r2: number;
    avg_mae: number;
    avg_rmse: number;
    avg_accuracy_within_5pct: number;
  };
  total_features: number;
  training_date: string;
}

/**
 * Model information response
 */
export interface ModelInfoResponse {
  model_information: {
    name: string;
    version: string;
    type: string;
    total_models: number;
  };
  model_performance: {
    [category: string]: {
      r2: number;
      mae: number;
      accuracy: number;
    };
  };
  api_health: {
    status: string;
    models_loaded: number;
    model_directory: string;
  };
  product_models: {
    [category: string]: {
      r2: number;
      mae: number;
      accuracy_within_5pct: number;
      model_r2: number;
    };
  };
}

/**
 * Feature importance response
 */
export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface FeatureImportanceResponse {
  model: string;
  top_features: Record<string, number>;
  total_features: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  models_available: string[];
  active_model: string;
  models_loaded?: number;
  total_models_expected?: number;
  models?: {
    [category: string]: string;
  };
  model_directory?: string;
  models_directory_exists?: boolean;
}

// ============================================================================
// PRODUCT CATEGORIES
// ============================================================================

/**
 * Available product categories in the model
 */
export const PRODUCT_CATEGORIES = [
  'Cold Drink',
  'Savoury Snacks',
  'Alcohol',
  'Hot Drink',
  'Sweet Snacks',
  'Fresh Food'
] as const;

export type ProductCategory = typeof PRODUCT_CATEGORIES[number];

/**
 * Warehouse options in the dataset
 */
export const WAREHOUSES = [
  'Lisbon',
  'Madrid',
  'Palma de Mallorca',
  'Porto'
] as const;

export type WarehouseOption = typeof WAREHOUSES[number];

// ============================================================================
// MODEL PERFORMANCE CONSTANTS
// ============================================================================

/**
 * Real model performance metrics from training
 */
export const MODEL_PERFORMANCE = {
  'Cold Drink': {
    r2: 0.9715,
    mae: 0.2566,
    accuracy: 71.52,
    rmse: 0.7877
  },
  'Savoury Snacks': {
    r2: 0.9700,
    mae: 0.2842,
    accuracy: 53.66,
    rmse: 0.8183
  },
  'Alcohol': {
    r2: 0.9162,
    mae: 0.3336,
    accuracy: 46.21,
    rmse: 1.4302
  },
  'Hot Drink': {
    r2: 0.9163,
    mae: 0.2398,
    accuracy: 55.63,
    rmse: 0.6789
  },
  'Sweet Snacks': {
    r2: 0.9440,
    mae: 0.1856,
    accuracy: 52.78,
    rmse: 0.5784
  },
  'Fresh Food': {
    r2: 0.9213,
    mae: 0.3105,
    accuracy: 35.62,
    rmse: 0.7144
  }
} as const;

/**
 * Calculate average performance across all models
 */
export function calculateAveragePerformance() {
  const categories = Object.keys(MODEL_PERFORMANCE) as ProductCategory[];
  const count = categories.length;

  const avg_r2 = categories.reduce((sum, cat) => sum + MODEL_PERFORMANCE[cat].r2, 0) / count;
  const avg_mae = categories.reduce((sum, cat) => sum + MODEL_PERFORMANCE[cat].mae, 0) / count;
  const avg_accuracy = categories.reduce((sum, cat) => sum + MODEL_PERFORMANCE[cat].accuracy, 0) / count;
  const avg_rmse = categories.reduce((sum, cat) => sum + MODEL_PERFORMANCE[cat].rmse, 0) / count;

  return {
    avg_r2,
    avg_mae,
    avg_accuracy,
    avg_rmse
  };
}
