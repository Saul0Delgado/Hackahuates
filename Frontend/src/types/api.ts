// API Response Types
export interface PredictionRequest {
  passenger_count: number;
  product_id: number;
  flight_type: string;
  service_type: string;
  origin: string;
  unit_cost?: number;
  flight_date?: string;
}

export interface PredictionResponse {
  predicted_quantity: number;
  lower_bound: number;
  upper_bound: number;
  confidence_score: number;
  expected_waste: number;
  expected_shortage: number;
  model_used: string;
}

export interface BatchPredictionRequest {
  passenger_count: number;
  flight_type: string;
  service_type: string;
  origin: string;
  flight_date?: string;
  products: number[];
}

export interface ProductPrediction {
  product_id: number;
  predicted_quantity: number;
  lower_bound: number;
  upper_bound: number;
  confidence_score: number;
  expected_waste: number;
  expected_shortage: number;
}

export interface BatchPredictionResponse {
  flight_id: string;
  passenger_count: number;
  total_predicted_cost: number;
  total_predicted_waste_cost: number;
  total_predicted_quantity: number;
  predictions: ProductPrediction[];
  model_used: string;
  generated_at: string;
}

export interface ModelMetrics {
  model: string;
  training_date: string;
  ml_metrics: {
    MAE: number;
    RMSE: number;
    MAPE: number;
    R2: number;
  };
  business_metrics: {
    waste_rate_percent: number;
    shortage_rate_percent: number;
    accuracy_rate_percent: number;
    avg_waste_qty: number;
  };
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface HealthResponse {
  status: string;
  models_available: string[];
  active_model: string;
}
