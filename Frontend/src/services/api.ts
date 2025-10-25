import type {
  PredictionRequest,
  PredictionResponse,
  BatchPredictionRequest,
  BatchPredictionResponse,
  ModelInfoResponse,
  FeatureImportance,
  FeatureImportanceResponse,
  HealthResponse,
} from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

class APIService {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check
  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Single prediction (product-level - 6 categories)
  async predict(data: PredictionRequest): Promise<PredictionResponse> {
    return this.request<PredictionResponse>('/api/v1/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Batch prediction (multiple flights)
  async predictBatch(
    data: BatchPredictionRequest
  ): Promise<BatchPredictionResponse> {
    return this.request<BatchPredictionResponse>('/api/v1/predict-batch', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Get model info (all 6 models)
  async getModelInfo(): Promise<ModelInfoResponse> {
    return this.request<ModelInfoResponse>('/api/v1/model-info');
  }

  // Get model metrics (compatibility - calls model-info)
  async getModelMetrics(): Promise<any> {
    return this.getModelInfo();
  }

  // Get feature importance (if available)
  async getFeatureImportance(topN: number = 10): Promise<FeatureImportanceResponse> {
    return this.request<FeatureImportanceResponse>(
      `/api/v1/model/feature-importance?top_n=${topN}`
    ).catch(() => ({
      model: 'product-level',
      top_features: {},
      total_features: 81
    }));
  }

  // Helper to convert feature importance response to array format
  featureImportanceToArray(response: FeatureImportanceResponse): FeatureImportance[] {
    return Object.entries(response.top_features).map(([feature, importance]) => ({
      feature,
      importance,
    }));
  }

  // List available models
  async listModels(): Promise<{ models: string[]; active_model: string }> {
    return this.request<{ models: string[]; active_model: string }>(
      '/api/v1/model/list'
    );
  }

  // Switch model
  async switchModel(modelName: string): Promise<{ message: string; active_model: string }> {
    return this.request<{ message: string; active_model: string }>(
      '/api/v1/model/switch',
      {
        method: 'POST',
        body: JSON.stringify({ model_name: modelName }),
      }
    );
  }
}

// Export singleton instance
export const apiService = new APIService();
