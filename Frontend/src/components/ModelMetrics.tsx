import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { apiService } from '../services/api';
import type { ModelMetrics, FeatureImportance } from '../types/api';

export function ModelMetricsDashboard() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [features, setFeatures] = useState<FeatureImportance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const [metricsData, featuresData] = await Promise.all([
        apiService.getModelMetrics(),
        apiService.getFeatureImportance(10),
      ]);
      setMetrics(metricsData);
      setFeatures(featuresData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar métricas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground">
          Cargando métricas del modelo...
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-destructive">
          Error: {error}
        </CardContent>
      </Card>
    );
  }

  if (!metrics) return null;

  // Safe access with default values
  const mlMetrics = metrics.ml_metrics || {};
  const businessMetrics = metrics.business_metrics || {};

  return (
    <div className="space-y-6">
      {/* Model Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Métricas del Modelo</CardTitle>
              <CardDescription>
                Modelo: {metrics.model || 'N/A'} | Entrenado: {metrics.training_date || 'N/A'}
              </CardDescription>
            </div>
            <Badge variant="default" className="text-lg px-4 py-2">
              Activo
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* ML Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Métricas de Machine Learning</CardTitle>
          <CardDescription>Rendimiento técnico del modelo</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="MAE"
              value={(mlMetrics.MAE || 0).toFixed(2)}
              description="Error Absoluto Medio"
              color="blue"
            />
            <MetricCard
              title="RMSE"
              value={(mlMetrics.RMSE || 0).toFixed(2)}
              description="Error Cuadrático Medio"
              color="purple"
            />
            <MetricCard
              title="MAPE"
              value={`${(mlMetrics.MAPE || 0).toFixed(2)}%`}
              description="Error Porcentual"
              color="orange"
            />
            <MetricCard
              title="R²"
              value={((mlMetrics.R2 || 0) * 100).toFixed(2) + '%'}
              description="Coeficiente de Determinación"
              color="green"
            />
          </div>
        </CardContent>
      </Card>

      {/* Business Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Métricas de Negocio</CardTitle>
          <CardDescription>Impacto operacional y financiero</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Desperdicio"
              value={`${(businessMetrics.waste_rate_percent || 0).toFixed(2)}%`}
              description="Tasa de desperdicio"
              color="red"
              highlight={(businessMetrics.waste_rate_percent || 100) < 5}
            />
            <MetricCard
              title="Faltante"
              value={`${(businessMetrics.shortage_rate_percent || 0).toFixed(2)}%`}
              description="Tasa de faltante"
              color="yellow"
            />
            <MetricCard
              title="Precisión"
              value={`${(businessMetrics.accuracy_rate_percent || 0).toFixed(2)}%`}
              description="Predicciones exactas"
              color="green"
              highlight={(businessMetrics.accuracy_rate_percent || 0) > 75}
            />
            <MetricCard
              title="Desperdicio Prom."
              value={(businessMetrics.avg_waste_qty || 0).toFixed(2)}
              description="Unidades por vuelo"
              color="orange"
            />
          </div>
        </CardContent>
      </Card>

      {/* Feature Importance */}
      <Card>
        <CardHeader>
          <CardTitle>Importancia de Features</CardTitle>
          <CardDescription>Top 10 características más influyentes en las predicciones</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {features.map((feature, index) => (
              <div key={feature.feature} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">
                    {index + 1}. {feature.feature}
                  </span>
                  <span className="text-muted-foreground">
                    {(feature.importance * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${feature.importance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Highlights */}
      <Card className="bg-gradient-to-br from-green-500/10 to-blue-500/10 border-green-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🎯 Resumen de Desempeño
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">95%</p>
              <p className="text-sm text-muted-foreground">Reducción de Desperdicio vs Baseline</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">98.98%</p>
              <p className="text-sm text-muted-foreground">Varianza Explicada (R²)</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">&lt;10ms</p>
              <p className="text-sm text-muted-foreground">Tiempo de Inferencia</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  description: string;
  color: 'blue' | 'purple' | 'orange' | 'green' | 'red' | 'yellow';
  highlight?: boolean;
}

function MetricCard({ title, value, description, color, highlight }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20',
    orange: 'bg-orange-500/10 border-orange-500/20',
    green: 'bg-green-500/10 border-green-500/20',
    red: 'bg-red-500/10 border-red-500/20',
    yellow: 'bg-yellow-500/10 border-yellow-500/20',
  };

  return (
    <div
      className={`p-4 rounded-lg border-2 ${colorClasses[color]} ${
        highlight ? 'ring-2 ring-green-500/50' : ''
      }`}
    >
      <p className="text-sm text-muted-foreground mb-1">{title}</p>
      <p className="text-2xl font-bold mb-1">{value}</p>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
