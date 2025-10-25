import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import type { BatchPredictionRequest, BatchPredictionResponse } from '../types/api';

// Product catalog matching dataset
const PRODUCTS = [
  { id: 1, name: 'Bread (Pan)', code: 'BRD001' },
  { id: 2, name: 'Chocolate (Chocolate)', code: 'CHO050' },
  { id: 3, name: 'Coffee (Café)', code: 'COF200' },
  { id: 4, name: 'Crackers (Galletas)', code: 'CRK075' },
  { id: 5, name: 'Drink #1 (Bebida 1)', code: 'DRK023' },
  { id: 6, name: 'Drink #2 (Bebida 2)', code: 'DRK024' },
  { id: 7, name: 'Hot Beverage (Bebida Caliente)', code: 'HTB110' },
  { id: 8, name: 'Juice (Jugo)', code: 'JCE200' },
  { id: 9, name: 'Nuts (Nueces)', code: 'NUT030' },
  { id: 10, name: 'Snack (Snack)', code: 'SNK001' },
];

export function PredictionForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);

  const [formData, setFormData] = useState<BatchPredictionRequest>({
    passenger_count: 180,
    flight_type: 'long-haul',
    service_type: 'Retail',
    origin: 'MEX',
    flight_date: new Date().toISOString().split('T')[0],
    products: [1, 2, 3, 4, 5],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const prediction = await apiService.predictBatch(formData);
      setResult(prediction);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al hacer la predicción');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof BatchPredictionRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Predicción de Comidas por Vuelo</CardTitle>
          <CardDescription>
            Ingresa los datos del vuelo para predecir las cantidades óptimas de comidas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="passenger_count">Número de Pasajeros</Label>
                <Input
                  id="passenger_count"
                  type="number"
                  min="1"
                  value={formData.passenger_count}
                  onChange={(e) => handleInputChange('passenger_count', parseInt(e.target.value))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="flight_type">Tipo de Vuelo</Label>
                <Select
                  id="flight_type"
                  value={formData.flight_type}
                  onChange={(e) => handleInputChange('flight_type', e.target.value)}
                  required
                >
                  <option value="short-haul">Short-Haul (Corto Alcance)</option>
                  <option value="medium-haul">Medium-Haul (Mediano Alcance)</option>
                  <option value="long-haul">Long-Haul (Largo Alcance)</option>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="service_type">Tipo de Servicio</Label>
                <Select
                  id="service_type"
                  value={formData.service_type}
                  onChange={(e) => handleInputChange('service_type', e.target.value)}
                  required
                >
                  <option value="Retail">
                    Retail - Servicio Estándar (Consumo bajo, ~67 unidades promedio)
                  </option>
                  <option value="Pick & Pack">
                    Pick & Pack - Servicio Empaquetado (Consumo alto, ~107 unidades promedio)
                  </option>
                </Select>
                <p className="text-xs text-muted-foreground mt-1">
                  💡 Estos son los tipos de servicio en el dataset. Pick & Pack requiere mayor preparación.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="origin">Origen</Label>
                <Select
                  id="origin"
                  value={formData.origin}
                  onChange={(e) => handleInputChange('origin', e.target.value)}
                  required
                >
                  <option value="MEX">Ciudad de México (MEX)</option>
                  <option value="DOH">Doha (DOH)</option>
                  <option value="JFK">Nueva York (JFK)</option>
                  <option value="LAX">Los Ángeles (LAX)</option>
                  <option value="LHR">Londres (LHR)</option>
                  <option value="CDG">París (CDG)</option>
                </Select>
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

              <div className="col-span-1 md:col-span-2 space-y-2">
                <Label>Productos a Predecir</Label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-3 border rounded-md bg-muted/30">
                  {PRODUCTS.map(product => (
                    <label key={product.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.products.includes(product.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            handleInputChange(
                              'products',
                              [...formData.products, product.id].sort((a, b) => a - b)
                            );
                          } else {
                            handleInputChange(
                              'products',
                              formData.products.filter(id => id !== product.id)
                            );
                          }
                        }}
                        className="cursor-pointer"
                      />
                      <span className="text-sm font-medium">{product.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive rounded-md text-destructive text-sm">
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Calculando...' : 'Calcular Predicción'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <PredictionResults result={result} products={PRODUCTS} />
      )}
    </div>
  );
}

interface PredictionResultsProps {
  result: BatchPredictionResponse;
  products: typeof PRODUCTS;
}

function PredictionResults({ result, products }: PredictionResultsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Resultados de la Predicción</CardTitle>
        <CardDescription>
          Vuelo: {result.flight_id} | Modelo: {result.model_used} |
          Generado: {new Date(result.generated_at).toLocaleString('es-MX')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Cards - Only showing what is ACTUALLY calculated */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Total Quantity */}
          <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-200">
            <p className="text-sm text-muted-foreground font-semibold">Total de Comidas</p>
            <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">
              {Math.round(result.total_predicted_quantity)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">unidades a preparar</p>
          </div>

          {/* Total Cost */}
          <div className="p-4 bg-green-500/10 rounded-lg border border-green-200">
            <p className="text-sm text-muted-foreground font-semibold">Costo Total</p>
            <p className="text-3xl font-bold text-green-700 dark:text-green-300">
              ${result.total_predicted_cost.toFixed(2)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">costo de producción</p>
          </div>

          {/* Passengers */}
          <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-200">
            <p className="text-sm text-muted-foreground font-semibold">Pasajeros</p>
            <p className="text-3xl font-bold text-purple-700 dark:text-purple-300">
              {result.passenger_count}
            </p>
            <p className="text-xs text-muted-foreground mt-1">en el vuelo</p>
          </div>
        </div>

        {/* Info Note */}
        <div className="p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 rounded-lg">
          <p className="text-sm font-semibold text-amber-900 dark:text-amber-200 mb-2">
            ℹ️ Sobre estos resultados:
          </p>
          <ul className="text-xs text-amber-800 dark:text-amber-300 space-y-1 list-disc list-inside">
            <li>
              <strong>Cantidad (Q50):</strong> Recomendación central del modelo (mediana)
            </li>
            <li>
              <strong>Rango Min-Max:</strong> Intervalo de confianza del 90% (Q5-Q95)
            </li>
            <li>
              <strong>Precisión del Modelo (R²):</strong> Capacidad del modelo para explicar varianza histórica (98.98%)
            </li>
            <li>
              <strong>Devoluciones Esperadas:</strong> Basado en tasa histórica de devolución por producto
            </li>
          </ul>
        </div>

        {/* Products Table */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Predicciones por Producto</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3 font-semibold">Producto</th>
                  <th className="text-center p-3 font-semibold">Cantidad</th>
                  <th className="text-center p-3 font-semibold">Rango (Q5-Q95)</th>
                  <th className="text-center p-3 font-semibold">Riesgo Escasez</th>
                  <th className="text-center p-3 font-semibold">
                    Devoluciones
                    <span className="text-xs font-normal block text-muted-foreground">
                      Esperadas
                    </span>
                  </th>
                  <th className="text-right p-3 font-semibold">Costo Unitario</th>
                  <th className="text-right p-3 font-semibold">Costo Total</th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((pred) => {
                  const product = products.find(p => p.id === pred.product_id);
                  const productName = product?.name || `Producto ${pred.product_id}`;
                  const unitCost = (result.total_predicted_cost / result.total_predicted_quantity) *
                                  (pred.predicted_quantity / result.total_predicted_quantity);
                  const productCost = pred.predicted_quantity * unitCost;

                  return (
                    <tr key={pred.product_id} className="border-b hover:bg-muted/30 transition-colors">
                      <td className="p-3 font-medium">{productName}</td>

                      {/* Predicted Quantity */}
                      <td className="p-3 text-center font-bold text-lg">
                        {Math.round(pred.predicted_quantity)}
                      </td>

                      {/* Confidence Interval */}
                      <td className="p-3 text-center text-sm text-muted-foreground">
                        {Math.round(pred.lower_bound)} – {Math.round(pred.upper_bound)}
                      </td>

                      {/* Shortage Risk Indicator */}
                      <td className="p-3 text-center">
                        {pred.expected_shortage > 0 ? (
                          <span className="inline-block bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 px-2 py-1 rounded text-xs font-semibold">
                            ⚠️ Riesgo ({(pred.expected_shortage * 100).toFixed(0)}%)
                          </span>
                        ) : (
                          <span className="inline-block bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-2 py-1 rounded text-xs font-semibold">
                            ✓ Sin riesgo
                          </span>
                        )}
                      </td>

                      {/* Expected Waste/Returns */}
                      <td className="p-3 text-center">
                        <span className="inline-block bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 px-2 py-1 rounded text-xs font-medium">
                          {pred.expected_waste.toFixed(1)} unidades
                        </span>
                        <p className="text-xs text-muted-foreground mt-1">
                          ({((pred.expected_waste / pred.predicted_quantity) * 100).toFixed(1)}%)
                        </p>
                      </td>

                      {/* Unit Cost */}
                      <td className="p-3 text-right text-sm">
                        ${(unitCost || 0).toFixed(2)}
                      </td>

                      {/* Product Total Cost */}
                      <td className="p-3 text-right font-semibold">
                        ${(productCost || 0).toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer with model info */}
        <div className="pt-4 border-t text-xs text-muted-foreground space-y-1">
          <p>
            <strong>Modelo utilizado:</strong> {result.model_used}
            (R² = 0.9898 en test set)
          </p>
          <p>
            <strong>Intervalo de confianza:</strong> 90% (Q5-Q95 percentiles)
          </p>
          <p>
            <strong>Nota:</strong> Las predicciones están basadas en patrones históricos.
            Los valores reales pueden variar según factores operacionales no contemplados en el modelo.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
