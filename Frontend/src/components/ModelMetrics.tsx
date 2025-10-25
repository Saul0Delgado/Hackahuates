import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { apiService } from '../services/api';
import { MODEL_PERFORMANCE, calculateAveragePerformance, PRODUCT_CATEGORIES, type ProductCategory } from '../types/api';

export function ModelMetricsDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      // Verify API is reachable
      await apiService.checkHealth();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar métricas');
    } finally {
      setLoading(false);
    }
  };

  const avgPerformance = calculateAveragePerformance();

  if (loading) {
    return (
      <Card className="border-2 border-blue-200">
        <CardContent className="p-8 text-center text-muted-foreground">
          ⏳ Cargando métricas de los modelos...
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-2 border-red-200">
        <CardContent className="p-8 text-center">
          <p className="text-red-700 font-semibold mb-3">⚠️ Error al conectar con API</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <p className="text-xs text-muted-foreground mt-3">
            Asegúrate de que el API esté corriendo en http://localhost:8000
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-2 border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-3xl">📊 Métricas de los Modelos Product-Level</CardTitle>
              <CardDescription className="mt-2">
                6 modelos XGBoost independientes (uno por categoría de producto)
              </CardDescription>
            </div>
            <Badge className="bg-green-500 hover:bg-green-600 text-white text-lg px-4 py-2">
              ✓ Listos para Producción
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Average Performance Summary */}
      <Card className="border-2 border-green-300">
        <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950">
          <CardTitle className="text-green-900 dark:text-green-100">Rendimiento Promedio (6 Modelos)</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricSummaryCard
              title="R² Promedio"
              value={`${(avgPerformance.avg_r2 * 100).toFixed(2)}%`}
              description="Varianza explicada"
              color="green"
            />
            <MetricSummaryCard
              title="MAE Promedio"
              value={avgPerformance.avg_mae.toFixed(4)}
              description="Error Absoluto Medio"
              color="blue"
            />
            <MetricSummaryCard
              title="RMSE Promedio"
              value={avgPerformance.avg_rmse.toFixed(4)}
              description="Error Cuadrático Medio"
              color="purple"
            />
            <MetricSummaryCard
              title="Accuracy Promedio"
              value={`${avgPerformance.avg_accuracy.toFixed(2)}%`}
              description="Precisión ±5%"
              color="orange"
            />
          </div>

          {/* Key Insights */}
          <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2">🎯 Resumen Ejecutivo:</p>
            <ul className="text-sm text-green-800 dark:text-green-200 space-y-1 list-disc list-inside">
              <li>Todos los modelos tienen <strong>R² &gt; 91.6%</strong> - Excelente capacidad explicativa</li>
              <li>Error promedio <strong>MAE = 0.268 unidades</strong> - Muy preciso para predicciones de inventario</li>
              <li><strong>Cold Drink y Savoury Snacks</strong> son los modelos más precisos (R² 97%+)</li>
              <li>Modelos listos para <strong>PRODUCCIÓN INMEDIATA</strong></li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Individual Model Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Rendimiento por Modelo (Test Set)</CardTitle>
          <CardDescription>
            Métricas detalladas de cada uno de los 6 modelos producto-level
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3 font-semibold">Categoría</th>
                  <th className="text-center p-3 font-semibold">R²</th>
                  <th className="text-center p-3 font-semibold">MAE</th>
                  <th className="text-center p-3 font-semibold">RMSE</th>
                  <th className="text-center p-3 font-semibold">Accuracy</th>
                  <th className="text-center p-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody>
                {PRODUCT_CATEGORIES.map((category) => {
                  const perf = MODEL_PERFORMANCE[category as ProductCategory];
                  const isTopPerformer = perf.r2 > 0.97;

                  return (
                    <tr
                      key={category}
                      className={`border-b transition-colors ${
                        isTopPerformer
                          ? 'bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/40'
                          : 'hover:bg-muted/50'
                      }`}
                    >
                      <td className="p-3 font-semibold">{category}</td>
                      <td className="p-3 text-center">
                        <Badge className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                          {(perf.r2 * 100).toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="p-3 text-center font-mono text-sm">
                        {perf.mae.toFixed(4)}
                      </td>
                      <td className="p-3 text-center font-mono text-sm">
                        {perf.rmse.toFixed(4)}
                      </td>
                      <td className="p-3 text-center">
                        <Badge
                          className={
                            perf.accuracy > 60
                              ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                              : 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200'
                          }
                        >
                          {perf.accuracy.toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="p-3 text-center">
                        {isTopPerformer ? (
                          <Badge className="bg-green-500 text-white">⭐ Top Performer</Badge>
                        ) : (
                          <Badge className="bg-blue-500 text-white">✓ Producción</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Model Comparison Visualization */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* R² Scores */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Comparación de R² (Varianza Explicada)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {PRODUCT_CATEGORIES.map((category) => {
                const perf = MODEL_PERFORMANCE[category as ProductCategory];
                const percentage = perf.r2 * 100;

                return (
                  <div key={category}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-semibold">{category}</span>
                      <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                        {percentage.toFixed(2)}%
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-400 to-blue-600"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Accuracy Scores */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Comparación de Accuracy (±5%)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {PRODUCT_CATEGORIES.map((category) => {
                const perf = MODEL_PERFORMANCE[category as ProductCategory];
                const percentage = perf.accuracy;

                return (
                  <div key={category}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-semibold">{category}</span>
                      <span className="text-sm font-bold text-green-600 dark:text-green-400">
                        {percentage.toFixed(2)}%
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-400 to-green-600"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Details Cards */}
      <div>
        <h2 className="text-xl font-bold mb-4">Detalles de Cada Modelo</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PRODUCT_CATEGORIES.map((category) => {
            const perf = MODEL_PERFORMANCE[category as ProductCategory];

            return (
              <Card key={category} className="border-2">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{category}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <MetricRow
                    label="R² Score"
                    value={`${(perf.r2 * 100).toFixed(2)}%`}
                    color="blue"
                  />
                  <MetricRow
                    label="MAE"
                    value={perf.mae.toFixed(4)}
                    color="green"
                  />
                  <MetricRow
                    label="RMSE"
                    value={perf.rmse.toFixed(4)}
                    color="purple"
                  />
                  <MetricRow
                    label="Accuracy ±5%"
                    value={`${perf.accuracy.toFixed(2)}%`}
                    color="orange"
                  />

                  {/* Interpretation */}
                  <div className="pt-3 border-t">
                    <p className="text-xs font-semibold text-muted-foreground mb-2">Interpretación:</p>
                    <p className="text-xs text-muted-foreground">
                      {perf.r2 > 0.97
                        ? '⭐ Modelo excepcional - Explica >97% de la varianza'
                        : perf.r2 > 0.90
                        ? '✓ Modelo excelente - Explica >90% de la varianza'
                        : '✓ Modelo bueno - Explica >85% de la varianza'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Dataset Information */}
      <Card className="border-2 border-purple-200">
        <CardHeader>
          <CardTitle>Información de Entrenamiento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-purple-50 dark:bg-purple-900/30 rounded-lg border border-purple-200 dark:border-purple-800">
              <p className="text-xs font-semibold text-purple-700 dark:text-purple-300">Total de Modelos</p>
              <p className="text-2xl font-bold text-purple-900 dark:text-purple-100 mt-2">6</p>
              <p className="text-xs text-muted-foreground mt-1">XGBoost (1 por categoría)</p>
            </div>
            <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs font-semibold text-blue-700 dark:text-blue-300">Features Totales</p>
              <p className="text-2xl font-bold text-blue-900 dark:text-blue-100 mt-2">81</p>
              <p className="text-xs text-muted-foreground mt-1">Features engineered</p>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
              <p className="text-xs font-semibold text-green-700 dark:text-green-300">Muestras de Entrenamiento</p>
              <p className="text-2xl font-bold text-green-900 dark:text-green-100 mt-2">37,472</p>
              <p className="text-xs text-muted-foreground mt-1">Vuelos únicos</p>
            </div>
            <div className="p-4 bg-orange-50 dark:bg-orange-900/30 rounded-lg border border-orange-200 dark:border-orange-800">
              <p className="text-xs font-semibold text-orange-700 dark:text-orange-300">Muestras de Test</p>
              <p className="text-2xl font-bold text-orange-900 dark:text-orange-100 mt-2">43,978</p>
              <p className="text-xs text-muted-foreground mt-1">Vuelos únicos</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card className="border-2 border-green-300 bg-green-50 dark:bg-green-950">
        <CardHeader>
          <CardTitle className="text-green-900 dark:text-green-100">✅ Recomendaciones para Producción</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-green-800 dark:text-green-200 list-disc list-inside">
            <li><strong>Todos los modelos están listos:</strong> R² promedio de 93.88% es excelente para predicción de inventario</li>
            <li><strong>Usa Cold Drink como benchmark:</strong> R² 97.15% es el mejor performer del portafolio</li>
            <li><strong>Error de predicción promedio:</strong> ±0.268 unidades (MAE) - muy preciso</li>
            <li><strong>Accuracy promedio:</strong> 52.5% dentro de ±5% - considera usar ±10-15% para mejores resultados operacionales</li>
            <li><strong>Deployment recomendado:</strong> API FastAPI con carga de 6 modelos en paralelo</li>
            <li><strong>Monitoreo sugerido:</strong> Trackear MAE y RMSE mensuales para detectar data drift</li>
          </ul>
        </CardContent>
      </Card>

      {/* Technical Stack */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Stack Técnico Utilizado</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">Modelo ML</p>
              <p className="text-sm">XGBoost v2.1.1</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">API Framework</p>
              <p className="text-sm">FastAPI</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">Validación</p>
              <p className="text-sm">Pydantic v2</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">Serialización</p>
              <p className="text-sm">Pickle</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">Métrica Principal</p>
              <p className="text-sm">R² Score</p>
            </div>
            <div className="p-3 bg-muted rounded">
              <p className="text-xs font-semibold mb-1">Data Processing</p>
              <p className="text-sm">Pandas + NumPy</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface MetricSummaryCardProps {
  title: string;
  value: string;
  description: string;
  color: 'green' | 'blue' | 'purple' | 'orange';
}

function MetricSummaryCard({
  title,
  value,
  description,
  color,
}: MetricSummaryCardProps) {
  const colorStyles = {
    green: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300',
    blue: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300',
    purple: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300',
    orange: 'bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800 text-orange-700 dark:text-orange-300',
  };

  return (
    <div className={`p-4 rounded-lg border-2 ${colorStyles[color]}`}>
      <p className="text-xs font-semibold">{title}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
      <p className="text-xs mt-1 opacity-75">{description}</p>
    </div>
  );
}

interface MetricRowProps {
  label: string;
  value: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

function MetricRow({ label, value, color }: MetricRowProps) {
  const colorMap = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    purple: 'text-purple-600 dark:text-purple-400',
    orange: 'text-orange-600 dark:text-orange-400',
  };

  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-bold ${colorMap[color]}`}>{value}</span>
    </div>
  );
}
