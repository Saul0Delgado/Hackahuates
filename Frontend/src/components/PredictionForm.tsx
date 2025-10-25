"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Select } from "./ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { apiService } from "../services/api"
import type { BatchPredictionRequest, BatchPredictionResponse } from "../types/api"
import {
  Plane,
  Calendar,
  Users,
  Package,
  MapPin,
  TrendingUp,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  Info,
  BarChart3,
  CheckSquare,
  Square,
} from "lucide-react"

// Product catalog matching dataset
const PRODUCTS = [
  { id: 1, name: "Bread (Pan)", code: "BRD001" },
  { id: 2, name: "Chocolate (Chocolate)", code: "CHO050" },
  { id: 3, name: "Coffee (Café)", code: "COF200" },
  { id: 4, name: "Crackers (Galletas)", code: "CRK075" },
  { id: 5, name: "Drink #1 (Bebida 1)", code: "DRK023" },
  { id: 6, name: "Drink #2 (Bebida 2)", code: "DRK024" },
  { id: 7, name: "Hot Beverage (Bebida Caliente)", code: "HTB110" },
  { id: 8, name: "Juice (Jugo)", code: "JCE200" },
  { id: 9, name: "Nuts (Nueces)", code: "NUT030" },
  { id: 10, name: "Snack (Snack)", code: "SNK001" },
]

export function PredictionForm() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<BatchPredictionResponse | null>(null)

  const [formData, setFormData] = useState<BatchPredictionRequest>({
    passenger_count: 180,
    flight_type: "long-haul",
    service_type: "Retail",
    origin: "MEX",
    flight_date: new Date().toISOString().split("T")[0],
    products: [1, 2, 3, 4, 5],
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const prediction = await apiService.predictBatch(formData)
      setResult(prediction)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al hacer la predicción")
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof BatchPredictionRequest, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSelectAll = () => {
    handleInputChange(
      "products",
      PRODUCTS.map((p) => p.id),
    )
  }

  const handleDeselectAll = () => {
    handleInputChange("products", [])
  }

  return (
    <div className="space-y-6">
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="size-5 text-primary" />
            Predicción de Comidas por Vuelo
          </CardTitle>
          <CardDescription className="leading-relaxed">
            Ingresa los datos del vuelo para predecir las cantidades óptimas de comidas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Passenger Count */}
              <div className="space-y-2">
                <Label htmlFor="passenger_count" className="flex items-center gap-2">
                  <Users className="size-4 text-muted-foreground" />
                  Número de Pasajeros
                </Label>
                <Input
                  id="passenger_count"
                  type="number"
                  min="1"
                  value={formData.passenger_count}
                  onChange={(e) => handleInputChange("passenger_count", Number.parseInt(e.target.value))}
                  required
                  aria-label="Número de pasajeros en el vuelo"
                />
              </div>

              {/* Flight Type */}
              <div className="space-y-2">
                <Label htmlFor="flight_type" className="flex items-center gap-2">
                  <Plane className="size-4 text-muted-foreground" />
                  Tipo de Vuelo
                </Label>
                <Select
                  id="flight_type"
                  value={formData.flight_type}
                  onChange={(e) => handleInputChange("flight_type", e.target.value)}
                  aria-label="Seleccionar tipo de vuelo"
                >
                  <option value="short-haul">Short-Haul (Corto Alcance)</option>
                  <option value="medium-haul">Medium-Haul (Mediano Alcance)</option>
                  <option value="long-haul">Long-Haul (Largo Alcance)</option>
                </Select>
              </div>

              {/* Service Type */}
              <div className="space-y-2">
                <Label htmlFor="service_type" className="flex items-center gap-2">
                  <Package className="size-4 text-muted-foreground" />
                  Tipo de Servicio
                </Label>
                <Select
                  id="service_type"
                  value={formData.service_type}
                  onChange={(e) => handleInputChange("service_type", e.target.value)}
                  aria-label="Seleccionar tipo de servicio"
                >
                  <option value="Retail">Retail - Servicio Estándar (~67 unidades promedio)</option>
                  <option value="Pick & Pack">Pick & Pack - Servicio Empaquetado (~107 unidades promedio)</option>
                </Select>
                <p className="text-xs text-muted-foreground mt-1 flex items-start gap-1.5 leading-relaxed">
                  <Info className="size-3.5 mt-0.5 shrink-0" />
                  <span>Pick & Pack requiere mayor preparación y tiene consumo más alto</span>
                </p>
              </div>

              {/* Origin */}
              <div className="space-y-2">
                <Label htmlFor="origin" className="flex items-center gap-2">
                  <MapPin className="size-4 text-muted-foreground" />
                  Origen
                </Label>
                <Select
                  id="origin"
                  value={formData.origin}
                  onChange={(e) => handleInputChange("origin", e.target.value)}
                  aria-label="Seleccionar ciudad de origen"
                >
                  <option value="MEX">Ciudad de México (MEX)</option>
                  <option value="DOH">Doha (DOH)</option>
                  <option value="JFK">Nueva York (JFK)</option>
                  <option value="LAX">Los Ángeles (LAX)</option>
                  <option value="LHR">Londres (LHR)</option>
                  <option value="CDG">París (CDG)</option>
                </Select>
              </div>

              {/* Flight Date */}
              <div className="space-y-2">
                <Label htmlFor="flight_date" className="flex items-center gap-2">
                  <Calendar className="size-4 text-muted-foreground" />
                  Fecha del Vuelo
                </Label>
                <Input
                  id="flight_date"
                  type="date"
                  value={formData.flight_date}
                  onChange={(e) => handleInputChange("flight_date", e.target.value)}
                  required
                  aria-label="Fecha del vuelo"
                />
              </div>

              {/* Products Selection */}
              <div className="col-span-1 md:col-span-2 space-y-3">
                <Label className="flex items-center gap-2">
                  <Package className="size-4 text-muted-foreground" />
                  Productos a Predecir
                </Label>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAll}
                    className="text-xs bg-transparent"
                    aria-label="Seleccionar todos los productos"
                  >
                    <CheckSquare className="size-3.5 mr-1.5" />
                    Seleccionar todos
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleDeselectAll}
                    className="text-xs bg-transparent"
                    aria-label="Deseleccionar todos los productos"
                  >
                    <Square className="size-3.5 mr-1.5" />
                    Deseleccionar todos
                  </Button>
                </div>

                <div
                  className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 border border-border/50 rounded-lg bg-muted/30"
                  role="group"
                  aria-label="Selección de productos para predicción"
                >
                  {PRODUCTS.map((product) => (
                    <label
                      key={product.id}
                      className="flex items-center gap-2 cursor-pointer hover:text-foreground transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={formData.products.includes(product.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            handleInputChange(
                              "products",
                              [...formData.products, product.id].sort((a, b) => a - b),
                            )
                          } else {
                            handleInputChange(
                              "products",
                              formData.products.filter((id) => id !== product.id),
                            )
                          }
                        }}
                        className="cursor-pointer accent-primary"
                        aria-label={`Incluir ${product.name} en la predicción`}
                      />
                      <span className="text-sm font-medium">{product.name}</span>
                    </label>
                  ))}
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

            <Button
              type="submit"
              disabled={loading || formData.products.length === 0}
              className="w-full"
              aria-label={loading ? "Calculando predicción" : "Calcular predicción de comidas"}
            >
              {loading ? "Calculando..." : "Calcular Predicción"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && <PredictionResults result={result} products={PRODUCTS} />}
    </div>
  )
}

interface PredictionResultsProps {
  result: BatchPredictionResponse
  products: typeof PRODUCTS
}

function PredictionResults({ result, products }: PredictionResultsProps) {
  return (
    <Card className="border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="size-5 text-primary" />
          Resultados de la Predicción
        </CardTitle>
        <CardDescription className="leading-relaxed">
          Vuelo: {result.flight_id} | Modelo: {result.model_used} | Generado:{" "}
          {new Date(result.generated_at).toLocaleString("es-MX")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Total Quantity */}
          <div className="p-4 bg-primary/10 rounded-lg border border-primary/20">
            <p className="text-sm text-muted-foreground font-semibold flex items-center gap-2">
              <Package className="size-4" />
              Total de Comidas
            </p>
            <p className="text-3xl font-bold text-primary mt-2">{Math.round(result.total_predicted_quantity)}</p>
            <p className="text-xs text-muted-foreground mt-1">unidades a preparar</p>
          </div>

          {/* Total Cost */}
          <div className="p-4 bg-accent/50 rounded-lg border border-accent">
            <p className="text-sm text-muted-foreground font-semibold flex items-center gap-2">
              <DollarSign className="size-4" />
              Costo Total
            </p>
            <p className="text-3xl font-bold text-foreground mt-2">${result.total_predicted_cost.toFixed(2)}</p>
            <p className="text-xs text-muted-foreground mt-1">costo de producción</p>
          </div>

          {/* Passengers */}
          <div className="p-4 bg-muted rounded-lg border border-border">
            <p className="text-sm text-muted-foreground font-semibold flex items-center gap-2">
              <Users className="size-4" />
              Pasajeros
            </p>
            <p className="text-3xl font-bold text-foreground mt-2">{result.passenger_count}</p>
            <p className="text-xs text-muted-foreground mt-1">en el vuelo</p>
          </div>
        </div>

        {/* Info Note */}
        <div className="p-4 bg-accent/30 border border-accent rounded-lg">
          <p className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
            <Info className="size-4" />
            Sobre estos resultados:
          </p>
          <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside leading-relaxed">
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
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="size-5" />
            Predicciones por Producto
          </h3>
          <div className="overflow-x-auto rounded-lg border border-border/50">
            <table className="w-full border-collapse text-sm" role="table">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3 font-semibold" scope="col">
                    Producto
                  </th>
                  <th className="text-center p-3 font-semibold" scope="col">
                    Cantidad
                  </th>
                  <th className="text-center p-3 font-semibold" scope="col">
                    Rango (Q5-Q95)
                  </th>
                  <th className="text-center p-3 font-semibold" scope="col">
                    Riesgo Escasez
                  </th>
                  <th className="text-center p-3 font-semibold" scope="col">
                    Devoluciones
                    <span className="text-xs font-normal block text-muted-foreground">Esperadas</span>
                  </th>
                  <th className="text-right p-3 font-semibold" scope="col">
                    Costo Unitario
                  </th>
                  <th className="text-right p-3 font-semibold" scope="col">
                    Costo Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.predictions.map((pred) => {
                  const product = products.find((p) => p.id === pred.product_id)
                  const productName = product?.name || `Producto ${pred.product_id}`
                  const unitCost =
                    (result.total_predicted_cost / result.total_predicted_quantity) *
                    (pred.predicted_quantity / result.total_predicted_quantity)
                  const productCost = pred.predicted_quantity * unitCost

                  return (
                    <tr key={pred.product_id} className="border-b hover:bg-muted/30 transition-colors">
                      <td className="p-3 font-medium">{productName}</td>

                      {/* Predicted Quantity */}
                      <td className="p-3 text-center font-bold text-lg">{Math.round(pred.predicted_quantity)}</td>

                      {/* Confidence Interval */}
                      <td className="p-3 text-center text-sm text-muted-foreground">
                        {Math.round(pred.lower_bound)} – {Math.round(pred.upper_bound)}
                      </td>

                      {/* Shortage Risk Indicator */}
                      <td className="p-3 text-center">
                        {pred.expected_shortage > 0 ? (
                          <span className="inline-flex items-center gap-1.5 bg-destructive/10 text-destructive px-2 py-1 rounded text-xs font-semibold">
                            <AlertTriangle className="size-3" />
                            Riesgo ({(pred.expected_shortage * 100).toFixed(0)}%)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 bg-accent/50 text-foreground px-2 py-1 rounded text-xs font-semibold">
                            <CheckCircle2 className="size-3" />
                            Sin riesgo
                          </span>
                        )}
                      </td>

                      {/* Expected Waste/Returns */}
                      <td className="p-3 text-center">
                        <span className="inline-block bg-muted text-foreground px-2 py-1 rounded text-xs font-medium">
                          {pred.expected_waste.toFixed(1)} unidades
                        </span>
                        <p className="text-xs text-muted-foreground mt-1">
                          ({((pred.expected_waste / pred.predicted_quantity) * 100).toFixed(1)}%)
                        </p>
                      </td>

                      {/* Unit Cost */}
                      <td className="p-3 text-right text-sm">${(unitCost || 0).toFixed(2)}</td>

                      {/* Product Total Cost */}
                      <td className="p-3 text-right font-semibold">${(productCost || 0).toFixed(2)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer with model info */}
        <div className="pt-4 border-t text-xs text-muted-foreground space-y-1.5 leading-relaxed">
          <p>
            <strong>Modelo utilizado:</strong> {result.model_used}
            (R² = 0.9898 en test set)
          </p>
          <p>
            <strong>Intervalo de confianza:</strong> 90% (Q5-Q95 percentiles)
          </p>
          <p>
            <strong>Nota:</strong> Las predicciones están basadas en patrones históricos. Los valores reales pueden
            variar según factores operacionales no contemplados en el modelo.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
