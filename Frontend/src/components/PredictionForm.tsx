import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import type { BatchPredictionRequest, BatchPredictionResponse } from '../types/api';

export function PredictionForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);

  const [formData, setFormData] = useState<BatchPredictionRequest>({
    passenger_count: 180,
    flight_type: 'INTERNATIONAL',
    service_type: 'ECONOMY',
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
                  <option value="INTERNATIONAL">Internacional</option>
                  <option value="DOMESTIC">Doméstico</option>
                  <option value="SHORT_HAUL">Corto Alcance</option>
                  <option value="MEDIUM_HAUL">Mediano Alcance</option>
                  <option value="LONG_HAUL">Largo Alcance</option>
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
                  <option value="ECONOMY">Economy</option>
                  <option value="BUSINESS">Business</option>
                  <option value="FIRST_CLASS">Primera Clase</option>
                  <option value="PREMIUM_ECONOMY">Premium Economy</option>
                </Select>
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

              <div className="space-y-2">
                <Label htmlFor="products">Productos (IDs separados por coma)</Label>
                <Input
                  id="products"
                  type="text"
                  placeholder="1,2,3,4,5"
                  value={formData.products.join(',')}
                  onChange={(e) =>
                    handleInputChange(
                      'products',
                      e.target.value.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n))
                    )
                  }
                  required
                />
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

      {result && <PredictionResults result={result} />}
    </div>
  );
}

interface PredictionResultsProps {
  result: BatchPredictionResponse;
}

function PredictionResults({ result }: PredictionResultsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Resultados de la Predicción</CardTitle>
        <CardDescription>
          Vuelo ID: {result.flight_id} | Modelo: {result.model_used}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-primary/10 rounded-lg">
            <p className="text-sm text-muted-foreground">Total de Comidas</p>
            <p className="text-2xl font-bold">{result.total_predicted_quantity}</p>
          </div>
          <div className="p-4 bg-green-500/10 rounded-lg">
            <p className="text-sm text-muted-foreground">Costo Total</p>
            <p className="text-2xl font-bold">${result.total_predicted_cost.toFixed(2)}</p>
          </div>
          <div className="p-4 bg-orange-500/10 rounded-lg">
            <p className="text-sm text-muted-foreground">Desperdicio Estimado</p>
            <p className="text-2xl font-bold">${result.total_predicted_waste_cost.toFixed(2)}</p>
          </div>
          <div className="p-4 bg-blue-500/10 rounded-lg">
            <p className="text-sm text-muted-foreground">Pasajeros</p>
            <p className="text-2xl font-bold">{result.passenger_count}</p>
          </div>
        </div>

        {/* Products Table */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Predicciones por Producto</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Producto</th>
                  <th className="text-right p-2">Cantidad</th>
                  <th className="text-right p-2">Rango Min-Max</th>
                  <th className="text-right p-2">Confianza</th>
                  <th className="text-right p-2">Desperdicio</th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((pred) => (
                  <tr key={pred.product_id} className="border-b hover:bg-muted/50">
                    <td className="p-2 font-medium">Producto {pred.product_id}</td>
                    <td className="p-2 text-right font-semibold">
                      {Math.round(pred.predicted_quantity)}
                    </td>
                    <td className="p-2 text-right text-sm text-muted-foreground">
                      {Math.round(pred.lower_bound)} - {Math.round(pred.upper_bound)}
                    </td>
                    <td className="p-2 text-right">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                        pred.confidence_score > 0.95
                          ? 'bg-green-500/20 text-green-700 dark:text-green-400'
                          : pred.confidence_score > 0.90
                          ? 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400'
                          : 'bg-red-500/20 text-red-700 dark:text-red-400'
                      }`}>
                        {(pred.confidence_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-2 text-right text-sm">
                      {pred.expected_waste.toFixed(2)} unidades
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Generado: {new Date(result.generated_at).toLocaleString('es-MX')}
        </p>
      </CardContent>
    </Card>
  );
}
