import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { apiService } from '../services/api';
import { PRODUCT_CATEGORIES, WAREHOUSES, MODEL_PERFORMANCE, type PredictionRequest, type PredictionResponse, type WarehouseOption, type ProductCategory } from '../types/api';

export function PredictionForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  // Generate flight key automatically
  const generateFlightKey = () => {
    return `FL${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  };

  const [formData, setFormData] = useState<PredictionRequest>({
    flight_key: generateFlightKey(),
    route: 'LIS-MAD',
    passengers: 180,
    flight_date: new Date().toISOString().split('T')[0],
    warehouse: 'Lisbon',
    num_items: 15,
    num_categories: 6,
    total_demand: 25.5,
    day_of_week: new Date().getDay(),
    month: new Date().getMonth() + 1,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const prediction = await apiService.predict(formData);
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al hacer la predicción")
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof PredictionRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Predicción de Comidas por Categoría</CardTitle>
          <CardDescription>
            Ingresa los datos del vuelo para obtener predicciones detalladas por categoría de producto
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Flight Identifier Section */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Identificación del Vuelo</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="flight_key">Clave del Vuelo</Label>
                  <div className="flex gap-2">
                    <Input
                      id="flight_key"
                      value={formData.flight_key}
                      onChange={(e) => handleInputChange('flight_key', e.target.value)}
                      placeholder="ej: AA1234"
                      required
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleInputChange('flight_key', generateFlightKey())}
                    >
                      Generar
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="route">Ruta (Origen-Destino)</Label>
                  <Input
                    id="route"
                    value={formData.route}
                    onChange={(e) => handleInputChange('route', e.target.value)}
                    placeholder="ej: LIS-MAD"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Flight Details Section */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Detalles del Vuelo</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="passengers">Número de Pasajeros</Label>
                  <Input
                    id="passengers"
                    type="number"
                    min="1"
                    max="500"
                    value={formData.passengers}
                    onChange={(e) => handleInputChange('passengers', parseInt(e.target.value))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="flight_date">Fecha del Vuelo</Label>
                  <Input
                    id="flight_date"
                    type="date"
                    value={formData.flight_date}
                    onChange={(e) => handleInputChange('flight_date', e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="warehouse">Almacén</Label>
                  <Select
                    id="warehouse"
                    value={formData.warehouse}
                    onChange={(e) => handleInputChange('warehouse', e.target.value as WarehouseOption)}
                    required
                  >
                    {WAREHOUSES.map(wh => (
                      <option key={wh} value={wh}>{wh}</option>
                    ))}
                  </Select>
                </div>
              </div>
            </div>

            {/* Optional Details Section */}
            <div className="space-y-4 pt-4 border-t">
              <h3 className="text-sm font-semibold text-muted-foreground">Detalles Adicionales (Opcional)</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="num_items">Número de Items</Label>
                  <Input
                    id="num_items"
                    type="number"
                    min="1"
                    value={formData.num_items || 15}
                    onChange={(e) => handleInputChange('num_items', parseInt(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground">Default: 15</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="total_demand">Demanda Total Estimada</Label>
                  <Input
                    id="total_demand"
                    type="number"
                    min="0"
                    step="0.5"
                    value={formData.total_demand || 25.5}
                    onChange={(e) => handleInputChange('total_demand', parseFloat(e.target.value))}
                  />
                  <p className="text-xs text-muted-foreground">Default: 25.5</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="day_of_week">Día de la Semana</Label>
                  <Select
                    id="day_of_week"
                    value={String(formData.day_of_week || 2)}
                    onChange={(e) => handleInputChange('day_of_week', parseInt(e.target.value))}
                  >
                    <option value="0">Lunes</option>
                    <option value="1">Martes</option>
                    <option value="2">Miércoles</option>
                    <option value="3">Jueves</option>
                    <option value="4">Viernes</option>
                    <option value="5">Sábado</option>
                    <option value="6">Domingo</option>
                  </Select>
                </div>
              </div>
            </div>

            {error && (
              <div
                className="p-4 bg-destructive/10 border border-destructive/50 rounded-lg text-destructive text-sm flex items-start gap-2"
                role="alert"
                aria-live="polite"
              >
                <AlertTriangle className="size-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" disabled={loading} className="w-full" size="lg">
              {loading ? '⏳ Calculando predicciones...' : '🚀 Predecir por Categoría'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && <PredictionResults result={result} />}
    </div>
  )
}

interface PredictionResultsProps {
  result: PredictionResponse;
}

function PredictionResults({ result }: PredictionResultsProps) {
  // Calculate total recommended qty
  const totalRecommended = Object.values(result.prediction_by_product)
    .reduce((sum, pred) => sum + (pred.recommended_qty || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Resultados de Predicción</CardTitle>
              <CardDescription className="mt-2">
                Vuelo: <span className="font-mono font-semibold">{result.flight_key}</span>
                {' '} | Generado: {new Date(result.timestamp).toLocaleString('es-MX')}
              </CardDescription>
            </div>
            <Badge className="bg-green-500 hover:bg-green-600 text-white text-base px-4 py-2">
              ✓ Completado
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300 font-semibold">Total Recomendado</p>
          <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 mt-2">
            {totalRecommended}
          </p>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">unidades a preparar</p>
        </div>

        <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
          <p className="text-sm text-green-700 dark:text-green-300 font-semibold">Precisión Promedio</p>
          <p className="text-3xl font-bold text-green-900 dark:text-green-100 mt-2">
            {(Object.values(result.prediction_by_product)
              .reduce((sum, pred) => sum + (pred.model_accuracy || 0), 0) / Object.keys(result.prediction_by_product).length).toFixed(1)}%
          </p>
          <p className="text-xs text-green-600 dark:text-green-400 mt-1">accuracy promedio</p>
        </div>

        <div className="p-4 bg-purple-50 dark:bg-purple-900/30 rounded-lg border border-purple-200 dark:border-purple-800">
          <p className="text-sm text-purple-700 dark:text-purple-300 font-semibold">R² Promedio</p>
          <p className="text-3xl font-bold text-purple-900 dark:text-purple-100 mt-2">
            {(Object.values(result.prediction_by_product)
              .reduce((sum, pred) => sum + (pred.model_r2 || 0), 0) / Object.keys(result.prediction_by_product).length * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">varianza explicada</p>
        </div>
      </div>

      {/* Category Predictions Grid */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Predicciones por Categoría</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(result.prediction_by_product).map(([key, pred]) => {
            const categoryName = pred.product as ProductCategory;
            const performance = MODEL_PERFORMANCE[categoryName as ProductCategory];

            // Determine color based on risk
            const riskColors = {
              'VERY_LOW': 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800',
              'LOW': 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800',
              'MEDIUM': 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800',
              'HIGH': 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800',
            };

            const riskBadgeColors = {
              'VERY_LOW': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
              'LOW': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
              'MEDIUM': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
              'HIGH': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
            };

            return (
              <Card key={key} className={`${riskColors[pred.stockout_category]} border`}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Category Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-base">{categoryName}</h4>
                        <p className="text-2xl font-bold mt-2">
                          {pred.recommended_qty} unidades
                        </p>
                      </div>
                      <Badge className={`${riskBadgeColors[pred.stockout_category]}`}>
                        {pred.stockout_category}
                      </Badge>
                    </div>

                    {/* Confidence Interval */}
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground font-semibold">Rango de Confianza (90%)</p>
                      <div className="bg-background/50 rounded px-3 py-2 border">
                        <p className="font-mono text-sm">
                          {Math.round(pred.confidence_lower)} – {Math.round(pred.confidence_upper)} unidades
                        </p>
                      </div>
                    </div>

                    {/* Model Metrics */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground">R²</p>
                        <p className="font-bold text-sm">{(pred.model_r2 * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Accuracy</p>
                        <p className="font-bold text-sm">{pred.model_accuracy.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">MAE</p>
                        <p className="font-bold text-sm">±{pred.model_mae.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Riesgo</p>
                        <p className="font-bold text-sm">{(pred.stockout_risk * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Business Metrics */}
      {result.business_metrics && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Métricas de Negocio</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground font-semibold">Unidades Esperadas de Desperdicio</p>
                <p className="text-2xl font-bold mt-2">{result.business_metrics.expected_waste_units?.toFixed(1) || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold">Costo de Desperdicio Estimado</p>
                <p className="text-2xl font-bold mt-2">${result.business_metrics.expected_waste_cost?.toFixed(2) || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold">Mejora Eficiencia vs Total</p>
                <p className="text-2xl font-bold mt-2 text-green-600">{result.business_metrics.efficiency_improvement?.toFixed(1) || 'N/A'}%</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-semibold">Ahorros Estimados</p>
                <p className="text-2xl font-bold mt-2 text-green-600">${result.business_metrics.estimated_savings?.toFixed(2) || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Note */}
      <Card className="border-amber-200 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
        <CardContent className="pt-6">
          <p className="text-sm font-semibold text-amber-900 dark:text-amber-200 mb-3">
            ℹ️ Cómo Usar Estos Resultados:
          </p>
          <ul className="text-xs text-amber-800 dark:text-amber-300 space-y-2 list-disc list-inside">
            <li><strong>Cantidad Recomendada:</strong> Número exacto a preparar por categoría</li>
            <li><strong>Rango de Confianza:</strong> En el 90% de casos, la demanda caerá en este rango</li>
            <li><strong>R²:</strong> Porcentaje de varianza explicada por el modelo (mayor = mejor)</li>
            <li><strong>Accuracy (±5%):</strong> % de predicciones dentro del 5% de error</li>
            <li><strong>Riesgo Stockout:</strong> Probabilidad de quedarse sin inventario</li>
            <li><strong>MAE:</strong> Error absoluto medio (desviación esperada)</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
