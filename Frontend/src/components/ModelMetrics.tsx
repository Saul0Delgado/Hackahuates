import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { apiService } from '../services/api';
import type { ModelMetrics, FeatureImportance, FeatureImportanceResponse } from '../types/api';

export function ModelMetricsDashboard() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [featureResponse, setFeatureResponse] = useState<FeatureImportanceResponse | null>(null);
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
      setFeatureResponse(featuresData);
      // Convert feature importance dict to array
      const featuresArray = apiService.featureImportanceToArray(featuresData);
      setFeatures(featuresArray);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar métricas');
      setFeatures([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-2 border-midnight_blue-200">
        <CardContent className="p-8 text-center text-muted-foreground">
          Cargando métricas del modelo...
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-2 border-red-200">
        <CardContent className="p-8 text-center text-red-700">
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
      {/* Model Info Header */}
      <Card className="border-2 border-midnight_blue-200">
        <CardHeader className="bg-gradient-to-r from-navy_blue-500 to-midnight_blue-600 text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Métricas del Modelo</CardTitle>
              <CardDescription className="text-midnight_blue-200">
                Modelo: {metrics.model || 'N/A'} | Entrenado: {metrics.training_date || 'N/A'}
              </CardDescription>
            </div>
            <Badge className="bg-green-500 hover:bg-green-600 text-white text-lg px-4 py-2">
              ✓ Activo
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* ML Metrics */}
      <Card className="border-2 border-midnight_blue-200">
        <CardHeader className="bg-gradient-to-r from-midnight_blue-100 to-midnight_blue-50 border-b-2 border-midnight_blue-200">
          <CardTitle className="text-navy_blue-900">Métricas de Machine Learning</CardTitle>
          <CardDescription className="text-navy_blue-700">
            Rendimiento técnico del modelo en test set (792 muestras)
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="MAE"
              value={(mlMetrics.MAE || 0).toFixed(2)}
              description="Error Absoluto Medio"
              unit="unidades"
              color="navy_blue"
              interpretation="Error promedio en predicciones"
            />
            <MetricCard
              title="RMSE"
              value={(mlMetrics.RMSE || 0).toFixed(2)}
              description="Error Cuadrático Medio"
              unit="unidades"
              color="midnight_blue"
              interpretation="Penaliza errores grandes"
            />
            <MetricCard
              title="MAPE"
              value={`${(mlMetrics.MAPE || 0).toFixed(2)}%`}
              description="Error Porcentual"
              unit="porcentaje"
              color="marian_blue"
              interpretation="Error relativo promedio"
            />
            <MetricCard
              title="R²"
              value={((mlMetrics.R2 || 0) * 100).toFixed(2) + '%'}
              description="Coeficiente de Determinación"
              unit="varianza"
              color="green"
              interpretation="Varianza explicada por modelo"
            />
          </div>
        </CardContent>
      </Card>

      {/* Business Metrics */}
      <Card className="border-2 border-midnight_blue-200">
        <CardHeader className="bg-gradient-to-r from-marian_blue-100 to-marian_blue-50 border-b-2 border-midnight_blue-200">
          <CardTitle className="text-navy_blue-900">Métricas de Negocio</CardTitle>
          <CardDescription className="text-navy_blue-700">
            Impacto operacional basado en predicciones vs consumo real
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Tasa Devolución"
              value={`${(businessMetrics.waste_rate_percent || 0).toFixed(2)}%`}
              description="Items devueltos no consumidos"
              unit="porcentaje"
              color="orange"
              interpretation="% de items preparados no consumidos"
              benchmark="Dataset: ~18% (Retail), ~45% (Pick & Pack)"
            />
            <MetricCard
              title="Tasa Escasez"
              value={`${(businessMetrics.shortage_rate_percent || 0).toFixed(2)}%`}
              description="Casos con insuficiente cantidad"
              unit="porcentaje"
              color="red"
              interpretation="% de predicciones que no alcanzan"
            />
            <MetricCard
              title="Precisión"
              value={`${(businessMetrics.accuracy_rate_percent || 0).toFixed(2)}%`}
              description="Predicciones exactas o cercanas"
              unit="porcentaje"
              color="green"
              interpretation="% de predicciones dentro del rango aceptable"
              highlight={(businessMetrics.accuracy_rate_percent || 0) > 75}
            />
            <MetricCard
              title="Prom. Devoluciones"
              value={(businessMetrics.avg_waste_qty || 0).toFixed(2)}
              description="Promedio de items por vuelo"
              unit="unidades"
              color="marian_blue"
              interpretation="Unidades promedio devueltas por vuelo"
            />
          </div>
        </CardContent>
      </Card>

      {/* Feature Importance */}
      <Card className="border-2 border-midnight_blue-200">
        <CardHeader className="bg-gradient-to-r from-navy_blue-100 to-navy_blue-50 border-b-2 border-midnight_blue-200">
          <CardTitle className="text-navy_blue-900">
            Importancia de Features (Top {featureResponse?.total_features || 10})
          </CardTitle>
          <CardDescription className="text-navy_blue-700">
            Features más influyentes en predicciones ({featureResponse?.total_features || 'N/A'} features totales en el modelo)
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {features.length > 0 ? (
            <div className="space-y-4">
              {features.map((feature, index) => (
                <div key={feature.feature} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-navy_blue-900">
                      {index + 1}. {formatFeatureName(feature.feature)}
                    </span>
                    <span className="inline-block px-3 py-1 rounded-full bg-midnight_blue-100 text-midnight_blue-800 font-bold text-xs">
                      {(feature.importance * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-midnight_blue-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-navy_blue-500 to-midnight_blue-600 transition-all"
                      style={{ width: `${feature.importance * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-marian_blue-700">
                    {getFeatureDescription(feature.feature)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">
              No hay datos de importancia de features disponibles
            </p>
          )}
        </CardContent>
      </Card>

      {/* Dataset Validation */}
      <Card className="border-2 border-marian_blue-200">
        <CardHeader className="bg-gradient-to-r from-marian_blue-100 to-marian_blue-50 border-b-2 border-midnight_blue-200">
          <CardTitle className="text-navy_blue-900">Información del Dataset de Entrenamiento</CardTitle>
          <CardDescription className="text-navy_blue-700">
            Características del dataset utilizado para entrenar el modelo
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-midnight_blue-50 rounded-lg border border-midnight_blue-200">
              <p className="text-xs font-semibold text-midnight_blue-700">Muestras Totales</p>
              <p className="text-2xl font-bold text-navy_blue-900 mt-1">792</p>
              <p className="text-xs text-muted-foreground mt-1">En dataset de consumo</p>
            </div>
            <div className="p-4 bg-navy_blue-50 rounded-lg border border-navy_blue-200">
              <p className="text-xs font-semibold text-navy_blue-700">Features Engineered</p>
              <p className="text-2xl font-bold text-navy_blue-900 mt-1">{featureResponse?.total_features || 32}</p>
              <p className="text-xs text-muted-foreground mt-1">Características del modelo</p>
            </div>
            <div className="p-4 bg-marian_blue-50 rounded-lg border border-marian_blue-200">
              <p className="text-xs font-semibold text-marian_blue-700">Productos</p>
              <p className="text-2xl font-bold text-navy_blue-900 mt-1">10</p>
              <p className="text-xs text-muted-foreground mt-1">BRD, CHO, COF, etc.</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-xs font-semibold text-green-700">Service Types</p>
              <p className="text-2xl font-bold text-navy_blue-900 mt-1">2</p>
              <p className="text-xs text-muted-foreground mt-1">Retail + Pick & Pack</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Quantiles Explanation */}
      <Card className="border-2 border-green-200">
        <CardHeader className="bg-gradient-to-r from-green-100 to-green-50 border-b-2 border-green-200">
          <CardTitle className="text-green-900">Entendiendo las Predicciones Cuantílicas</CardTitle>
          <CardDescription className="text-green-700">
            Cómo interpretar los intervalos de confianza (Q5, Q50, Q95)
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">Q5 (Límite Inferior)</p>
              <p className="text-xs text-muted-foreground">
                Estimación conservadora. En el 5% de casos, el consumo será menor a este valor. Útil para planificación pesimista.
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">Q50 (Mediana)</p>
              <p className="text-xs text-muted-foreground">
                Predicción central del modelo. En el 50% de casos estará por encima, 50% por debajo. Recomendado para producción.
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">Q95 (Límite Superior)</p>
              <p className="text-xs text-muted-foreground">
                Estimación optimista. En el 95% de casos, el consumo no excederá este valor. Útil para evitar escasez.
              </p>
            </div>
          </div>
          <div className="mt-4 p-4 bg-green-100 rounded-lg border-l-4 border-green-700">
            <p className="text-xs text-green-800">
              💡 <strong>Intervalo de confianza 90%:</strong> Entre Q5 y Q95 se encuentra el 90% de los casos esperados. Si el consumo real cae fuera, es un evento raro pero posible.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Service Type Guidance */}
      <Card className="border-2 border-marian_blue-200">
        <CardHeader className="bg-gradient-to-r from-marian_blue-100 to-marian_blue-50 border-b-2 border-marian_blue-200">
          <CardTitle className="text-marian_blue-900">Recomendaciones por Tipo de Servicio</CardTitle>
          <CardDescription className="text-marian_blue-700">
            Guía operacional según servicio
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-marian_blue-50 rounded-lg border border-marian_blue-200">
              <p className="text-sm font-semibold text-marian_blue-700 mb-2">🛍️ Retail (Servicio Estándar)</p>
              <ul className="text-xs text-marian_blue-600 space-y-1">
                <li>• Consumo promedio: ~67 unidades</li>
                <li>• Tasa de devolución: ~18%</li>
                <li>• Usar Q50 con buffer de 5-10%</li>
                <li>• Mejor para vuelos cortos</li>
              </ul>
            </div>
            <div className="p-4 bg-marian_blue-50 rounded-lg border border-marian_blue-200">
              <p className="text-sm font-semibold text-marian_blue-700 mb-2">📦 Pick & Pack (Empaquetado)</p>
              <ul className="text-xs text-marian_blue-600 space-y-1">
                <li>• Consumo promedio: ~107 unidades</li>
                <li>• Tasa de devolución: ~45%</li>
                <li>• Usar Q50 con buffer de 10-15%</li>
                <li>• Mejor para vuelos largos</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Summary */}
      <Card className="bg-gradient-to-br from-navy_blue-100 to-midnight_blue-100 border-2 border-navy_blue-300">
        <CardHeader>
          <CardTitle className="text-navy_blue-900 flex items-center gap-2">
            📊 Resumen de Desempeño
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-white rounded-lg border-2 border-navy_blue-200">
              <p className="text-sm font-semibold text-navy_blue-700 mb-2">Varianza Explicada (R²)</p>
              <p className="text-4xl font-bold text-navy_blue-900">
                {((mlMetrics.R2 || 0) * 100).toFixed(2)}%
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                El modelo explica {((mlMetrics.R2 || 0) * 100).toFixed(2)}% de la varianza en consumo histórico
              </p>
            </div>

            <div className="p-4 bg-white rounded-lg border-2 border-marian_blue-200">
              <p className="text-sm font-semibold text-marian_blue-700 mb-2">Error Promedio</p>
              <p className="text-4xl font-bold text-navy_blue-900">
                ±{(mlMetrics.MAE || 0).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Desviación promedio de {(mlMetrics.MAE || 0).toFixed(1)} unidades en predicciones
              </p>
            </div>

            <div className="p-4 bg-white rounded-lg border-2 border-midnight_blue-200">
              <p className="text-sm font-semibold text-midnight_blue-700 mb-2">Precisión Operativa</p>
              <p className="text-4xl font-bold text-navy_blue-900">
                {(businessMetrics.accuracy_rate_percent || 0).toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {(businessMetrics.accuracy_rate_percent || 0) > 75
                  ? '✓ Excelente precisión en predicciones'
                  : 'Precisión dentro de margen operacional'}
              </p>
            </div>
          </div>

          {/* Key Findings */}
          <div className="mt-6 p-4 bg-midnight_blue-50 rounded-lg border-l-4 border-navy_blue-600">
            <p className="text-sm font-semibold text-navy_blue-900 mb-3">Hallazgos Clave:</p>
            <ul className="text-sm text-navy_blue-700 space-y-2 list-disc list-inside">
              <li>
                <strong>Feature más importante:</strong> {features[0]?.feature && formatFeatureName(features[0].feature)}
                ({((features[0]?.importance || 0) * 100).toFixed(1)}%)
              </li>
              <li>
                <strong>Tasa de devolución modelo:</strong> {(businessMetrics.waste_rate_percent || 0).toFixed(2)}%
                (dataset promedio: Retail ~18%, Pick & Pack ~45%)
              </li>
              <li>
                <strong>Intervalo de confianza:</strong> 90% (Q5-Q95 percentiles en predicciones)
              </li>
              <li>
                <strong>Validación:</strong> Todas las métricas basadas en datos reales del dataset de entrenamiento
              </li>
            </ul>
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
  unit?: string;
  color: 'navy_blue' | 'midnight_blue' | 'marian_blue' | 'green' | 'red' | 'orange';
  interpretation?: string;
  benchmark?: string;
  highlight?: boolean;
}

function MetricCard({
  title,
  value,
  description,
  unit,
  color,
  interpretation,
  benchmark,
  highlight,
}: MetricCardProps) {
  const colorConfig = {
    navy_blue: {
      bg: 'bg-navy_blue-50',
      border: 'border-navy_blue-300',
      title: 'text-navy_blue-700',
      value: 'text-navy_blue-900',
      ring: 'ring-navy_blue-500/50',
    },
    midnight_blue: {
      bg: 'bg-midnight_blue-50',
      border: 'border-midnight_blue-300',
      title: 'text-midnight_blue-700',
      value: 'text-navy_blue-900',
      ring: 'ring-midnight_blue-500/50',
    },
    marian_blue: {
      bg: 'bg-marian_blue-50',
      border: 'border-marian_blue-300',
      title: 'text-marian_blue-700',
      value: 'text-navy_blue-900',
      ring: 'ring-marian_blue-500/50',
    },
    green: {
      bg: 'bg-green-50',
      border: 'border-green-300',
      title: 'text-green-700',
      value: 'text-green-900',
      ring: 'ring-green-500/50',
    },
    red: {
      bg: 'bg-red-50',
      border: 'border-red-300',
      title: 'text-red-700',
      value: 'text-red-900',
      ring: 'ring-red-500/50',
    },
    orange: {
      bg: 'bg-orange-50',
      border: 'border-orange-300',
      title: 'text-orange-700',
      value: 'text-orange-900',
      ring: 'ring-orange-500/50',
    },
  };

  const config = colorConfig[color];

  return (
    <div
      className={`p-4 rounded-lg border-2 ${config.bg} ${config.border} ${
        highlight ? `ring-2 ${config.ring}` : ''
      }`}
    >
      <p className={`text-xs font-semibold ${config.title} mb-1`}>{title}</p>
      <p className={`text-2xl font-bold ${config.value} mb-2`}>{value}</p>
      <p className="text-xs text-muted-foreground mb-2">{description}</p>
      {unit && <p className="text-xs text-muted-foreground">({unit})</p>}
      {interpretation && <p className="text-xs text-marian_blue-700 mt-2 italic">{interpretation}</p>}
      {benchmark && <p className="text-xs text-navy_blue-600 mt-2">📊 {benchmark}</p>}
    </div>
  );
}

/**
 * Format feature names from model output
 * Converts snake_case to readable format
 */
function formatFeatureName(feature: string): string {
  return feature
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Get human-readable description of features
 */
function getFeatureDescription(feature: string): string {
  const descriptions: Record<string, string> = {
    Passenger_Count: '📊 Número de pasajeros - Factor principal de demanda',
    consumption_rate: '📈 Tasa de consumo histórica - Patrón de uso',
    spec_per_passenger: '👥 Especificación por pasajero - Estándar operacional',
    product_consumption_rate_mean: '📉 Consumo promedio por producto - Tendencia histórica',
    day_of_week: '📅 Día de la semana - Efecto temporal',
    'Flight_Type-long-haul': '✈️ Tipo de vuelo (largo alcance) - Duración del vuelo',
    'Service_Type-Pick & Pack': '📦 Tipo de servicio (Pick & Pack) - Modelo operacional',
    waste_qty: '🔄 Cantidad devuelta - Tasa histórica de no consumo',
    overage_qty: '➕ Excedente - Buffer de seguridad histórico',
    'Origin-MEX': '🌍 Origen (México) - Localización geográfica',
  };

  return descriptions[feature] || 'Feature del modelo de predicción';
}
