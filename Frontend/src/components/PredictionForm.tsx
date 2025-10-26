import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { apiService } from '../services/api';
import { WAREHOUSES, AIRPORTS, type PredictionRequest, type PredictionResponse, type WarehouseOption, type ProductCategory } from '../types/api';
import { AlertTriangle, TrendingUp, RefreshCw } from 'lucide-react';

export function PredictionForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [origin, setOrigin] = useState('LIS');
  const [destination, setDestination] = useState('MAD');

  // Generate flight key automatically
  const generateFlightKey = () => {
    return `FL${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  };

  const [formData, setFormData] = useState<PredictionRequest>({
    flight_key: generateFlightKey(),
    route: `${origin}-${destination}`,
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

  const handleAirportChange = (newOrigin?: string, newDestination?: string) => {
    const updatedOrigin = newOrigin ?? origin;
    const updatedDestination = newDestination ?? destination;

    if (newOrigin !== undefined) setOrigin(newOrigin);
    if (newDestination !== undefined) setDestination(newDestination);

    setFormData(prev => ({
      ...prev,
      route: `${updatedOrigin}-${updatedDestination}`
    }));
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line react/jsx-key */}
          <h1 className="text-3xl font-bold" style={{ color: '#010165' }}>
            Predicción Inteligente
          </h1>
        </div>
        <p className="text-slate-600 max-w-2xl">
          Obtén predicciones precisas de consumo por categoría de producto para optimizar tu inventario
        </p>
      </div>

      {/* Main Form Card */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="pt-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Step 1: Essential Flight Information */}
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-1" style={{ color: '#010165' }}>Información del Vuelo</h2>
                <p className="text-sm text-slate-600">Datos esenciales para la predicción</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="flight_key" className="text-sm font-medium">
                    Clave del Vuelo
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="flight_key"
                      value={formData.flight_key}
                      onChange={(e) => handleInputChange('flight_key', e.target.value)}
                      placeholder="ej: AA1234"
                      className="h-11 rounded-lg"
                      required
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleInputChange('flight_key', generateFlightKey())}
                      className="rounded-lg"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="origin" className="text-sm font-medium">
                    Origen
                  </Label>
                  <Select
                    id="origin"
                    value={origin}
                    onChange={(e) => handleAirportChange(e.target.value, undefined)}
                    className="h-11 rounded-lg"
                    required
                  >
                    {AIRPORTS.map(airport => (
                      <option key={airport.code} value={airport.code}>
                        {airport.code} - {airport.name}, {airport.country}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="destination" className="text-sm font-medium">
                    Destino
                  </Label>
                  <Select
                    id="destination"
                    value={destination}
                    onChange={(e) => handleAirportChange(undefined, e.target.value)}
                    className="h-11 rounded-lg"
                    required
                  >
                    {AIRPORTS.map(airport => (
                      <option key={airport.code} value={airport.code}>
                        {airport.code} - {airport.name}, {airport.country}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="passengers" className="text-sm font-medium">
                    Número de Pasajeros
                  </Label>
                  <Input
                    id="passengers"
                    type="number"
                    min="1"
                    max="500"
                    value={formData.passengers}
                    onChange={(e) => handleInputChange('passengers', parseInt(e.target.value))}
                    className="h-11 rounded-lg"
                    required
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="flight_date" className="text-sm font-medium">
                    Fecha del Vuelo
                  </Label>
                  <Input
                    id="flight_date"
                    type="date"
                    value={formData.flight_date}
                    onChange={(e) => handleInputChange('flight_date', e.target.value)}
                    className="h-11 rounded-lg"
                    required
                  />
                </div>

                <div className="space-y-3">
                  <Label htmlFor="warehouse" className="text-sm font-medium">
                    Almacén
                  </Label>
                  <Select
                    id="warehouse"
                    value={formData.warehouse}
                    onChange={(e) => handleInputChange('warehouse', e.target.value as WarehouseOption)}
                    className="h-11 rounded-lg"
                    required
                  >
                    {WAREHOUSES.map(wh => (
                      <option key={wh} value={wh}>{wh}</option>
                    ))}
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="day_of_week" className="text-sm font-medium">
                    Día de la Semana
                  </Label>
                  <Select
                    id="day_of_week"
                    value={String(formData.day_of_week || 2)}
                    onChange={(e) => handleInputChange('day_of_week', parseInt(e.target.value))}
                    className="h-11 rounded-lg"
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

            {/* Divider */}
            <div className="border-t border-slate-200" />

            {/* Step 2: Advanced Options */}
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-1" style={{ color: '#010165' }}>Parámetros Avanzados</h2>
                <p className="text-sm text-slate-600">Opcional: Ajusta parámetros adicionales</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-3">
                  <Label htmlFor="num_items" className="text-sm font-medium">
                    Número de Items
                  </Label>
                  <Input
                    id="num_items"
                    type="number"
                    min="1"
                    value={formData.num_items || 15}
                    onChange={(e) => handleInputChange('num_items', parseInt(e.target.value))}
                    className="h-11 rounded-lg"
                  />
                  <p className="text-xs text-slate-500">Predeterminado: 15</p>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="total_demand" className="text-sm font-medium">
                    Demanda Total Estimada
                  </Label>
                  <Input
                    id="total_demand"
                    type="number"
                    min="0"
                    step="0.5"
                    value={formData.total_demand || 25.5}
                    onChange={(e) => handleInputChange('total_demand', parseFloat(e.target.value))}
                    className="h-11 rounded-lg"
                  />
                  <p className="text-xs text-slate-500">Predeterminado: 25.5</p>
                </div>

                <div className="space-y-3">
                  <Label htmlFor="num_categories" className="text-sm font-medium">
                    Número de Categorías
                  </Label>
                  <Input
                    id="num_categories"
                    type="number"
                    min="1"
                    value={formData.num_categories || 6}
                    onChange={(e) => handleInputChange('num_categories', parseInt(e.target.value))}
                    className="h-11 rounded-lg"
                  />
                  <p className="text-xs text-slate-500">Predeterminado: 6</p>
                </div>
              </div>
            </div>

            {/* Error Alert */}
            {error && (
              <div
                className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start gap-3"
                role="alert"
                aria-live="polite"
              >
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">Error en la predicción</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 rounded-lg font-semibold text-base transition-all"
              style={{
                backgroundColor: loading ? '#010165cc' : '#010165',
                color: 'white'
              }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Calculando predicciones...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Generar Predicción
                </span>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results Section */}
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

  const avgAccuracy = (Object.values(result.prediction_by_product)
    .reduce((sum, pred) => sum + (pred.model_accuracy || 0), 0) / Object.keys(result.prediction_by_product).length).toFixed(1);

  const avgR2 = (Object.values(result.prediction_by_product)
    .reduce((sum, pred) => sum + (pred.model_r2 || 0), 0) / Object.keys(result.prediction_by_product).length * 100).toFixed(1);

  return (
    <div className="space-y-8">
      {/* Success Header */}
      <div className="flex items-start gap-4">
        {/* eslint-disable-next-line react/jsx-key */}
        <div>
          <h2 className="text-2xl font-bold" style={{ color: '#010165' }}>Predicción Completada</h2>
          <p className="text-slate-600 mt-1">
            Vuelo <span className="font-semibold">{result.flight_key}</span> • {new Date(result.timestamp).toLocaleDateString('es-MX')}
          </p>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-600 font-medium mb-2">Total a Preparar</p>
            <p className="text-4xl font-bold" style={{ color: '#010165' }}>
              {totalRecommended}
            </p>
            <p className="text-xs text-slate-500 mt-2">unidades recomendadas</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-600 font-medium mb-2">Precisión Promedio</p>
            <p className="text-4xl font-bold" style={{ color: '#010165' }}>
              {avgAccuracy}%
            </p>
            <p className="text-xs text-slate-500 mt-2">dentro del 5% de error</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-600 font-medium mb-2">Varianza Explicada</p>
            <p className="text-4xl font-bold" style={{ color: '#010165' }}>
              {avgR2}%
            </p>
            <p className="text-xs text-slate-500 mt-2">calidad del modelo (R²)</p>
          </CardContent>
        </Card>
      </div>

      {/* Category Predictions Grid */}
      <div className="space-y-5">
        <h3 className="text-lg font-semibold" style={{ color: '#010165' }}>Predicciones por Categoría</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Object.entries(result.prediction_by_product).map(([key, pred]) => {
            const categoryName = pred.product as ProductCategory;

            // Risk level styling - clean solid colors for SaaS aesthetic
            const riskConfig = {
              'VERY_LOW': { borderColor: 'border-emerald-200', textColor: 'text-emerald-700', dotColor: 'bg-emerald-500', label: 'Bajo' },
              'LOW': { borderColor: 'border-blue-200', textColor: 'text-blue-700', dotColor: 'bg-blue-500', label: 'Bajo' },
              'MEDIUM': { borderColor: 'border-amber-200', textColor: 'text-amber-700', dotColor: 'bg-amber-500', label: 'Medio' },
              'HIGH': { borderColor: 'border-red-200', textColor: 'text-red-700', dotColor: 'bg-red-500', label: 'Alto' },
            };

            const config = riskConfig[pred.stockout_category];

            return (
              <Card key={key} className={`bg-white ${config.borderColor} border-2 transition-all hover:shadow-md`}>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Category Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-base">{categoryName}</h4>
                        <p className="text-3xl font-bold mt-1" style={{ color: '#010165' }}>
                          {pred.recommended_qty}
                        </p>
                        <p className="text-xs text-slate-600 mt-1">unidades</p>
                      </div>
                      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border ${config.borderColor}`}>
                        <div className={`w-2.5 h-2.5 rounded-full ${config.dotColor}`} />
                        <span className={`text-xs font-semibold ${config.textColor}`}>
                          {config.label}
                        </span>
                      </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-slate-200" />

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-slate-600 font-medium">Rango 90%</p>
                        <p className="text-sm font-mono font-semibold mt-1">
                          {Math.round(pred.confidence_lower)}–{Math.round(pred.confidence_upper)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 font-medium">Accuracy</p>
                        <p className="text-sm font-semibold mt-1" style={{ color: '#010165' }}>{pred.model_accuracy.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 font-medium">R²</p>
                        <p className="text-sm font-semibold mt-1" style={{ color: '#010165' }}>{(pred.model_r2 * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-600 font-medium">MAE</p>
                        <p className="text-sm font-semibold mt-1" style={{ color: '#010165' }}>±{pred.model_mae.toFixed(2)}</p>
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
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg" style={{ color: '#010165' }}>Impacto Económico</CardTitle>
            <CardDescription>Análisis de desperdicio y ahorro potencial</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-600 font-medium mb-2">Desperdicio Esperado</p>
                <p className="text-2xl font-bold">{result.business_metrics.expected_waste_units?.toFixed(1) || '—'}</p>
                <p className="text-xs text-slate-500 mt-1">unidades</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-600 font-medium mb-2">Costo de Desperdicio</p>
                <p className="text-2xl font-bold">${result.business_metrics.expected_waste_cost?.toFixed(0) || '—'}</p>
                <p className="text-xs text-slate-500 mt-1">estimado</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-600 font-medium mb-2">Mejora de Eficiencia</p>
                <p className="text-2xl font-bold" style={{ color: '#010165' }}>{result.business_metrics.efficiency_improvement?.toFixed(1) || '—'}%</p>
                <p className="text-xs text-slate-500 mt-1">vs método total</p>
              </div>
              <div className="p-4 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-600 font-medium mb-2">Ahorros Estimados</p>
                <p className="text-2xl font-bold" style={{ color: '#010165' }}>${result.business_metrics.estimated_savings?.toFixed(0) || '—'}</p>
                <p className="text-xs text-slate-500 mt-1">potenciales</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
