"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { apiService } from "../services/api"
import type { ModelMetrics, FeatureImportance } from "../types/api"
import { Target, TrendingUp, AlertCircle, Loader2 } from "lucide-react"

export function ModelMetricsDashboard() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [features, setFeatures] = useState<FeatureImportance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMetrics()
  }, [])

  const loadMetrics = async () => {
  try {
    setLoading(true)
    const [metricsData, featuresData] = await Promise.all([
      apiService.getModelMetrics(),
      apiService.getFeatureImportance(10),
    ])
    setMetrics(metricsData)
    
    // --- PASO CLAVE DE DEPURACIÓN ---
    // ...
    console.log("Datos recibidos para features:", featuresData) 

    // Guardamos directamente el array de features en el estado
    setFeatures(featuresData);

    setError(null)
    // ...
  } catch (err) {
    setError(err instanceof Error ? err.message : "Error al cargar métricas")
  } finally {
    setLoading(false)
  }
}

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground" aria-live="polite">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" aria-hidden="true" />
          <p>Cargando métricas del modelo...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-destructive" role="alert" aria-live="assertive">
          <AlertCircle className="w-8 h-8 mx-auto mb-2" aria-hidden="true" />
          <p>Error: {error}</p>
        </CardContent>
      </Card>
    )
  }

  if (!metrics) return null

  // Safe access with default values
  const mlMetrics = metrics.ml_metrics || {}
  const businessMetrics = metrics.business_metrics || {}

  return (
    <div className="space-y-6" role="region" aria-label="Panel de métricas del modelo">
      {/* Model Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Métricas del Modelo</CardTitle>
              <CardDescription>
                Modelo: {metrics.model || "N/A"} | Entrenado: {metrics.training_date || "N/A"}
              </CardDescription>
            </div>
            <Badge variant="default" className="text-lg px-4 py-2" aria-label="Estado del modelo: Activo">
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4" role="list" aria-label="Métricas de machine learning">
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
              value={((mlMetrics.R2 || 0) * 100).toFixed(2) + "%"}
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4" role="list" aria-label="Métricas de negocio">
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
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" aria-hidden="true" />
            <CardTitle>Importancia de Features</CardTitle>
          </div>
          <CardDescription>Top 10 características más influyentes en las predicciones</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3" role="list" aria-label="Lista de importancia de características">
            {features.map((feature, index) => (
              <div key={feature.feature} className="space-y-1" role="listitem">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">
                    {index + 1}. {feature.feature}
                  </span>
                  <span className="text-muted-foreground">{(feature.importance * 100).toFixed(1)}%</span>
                </div>
                <div
                  className="h-2 bg-muted rounded-full overflow-hidden"
                  role="progressbar"
                  aria-valuenow={feature.importance * 100}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`Importancia de ${feature.feature}: ${(feature.importance * 100).toFixed(1)}%`}
                >
                  <div className="h-full bg-primary transition-all" style={{ width: `${feature.importance * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Highlights */}
      <Card className="border-primary/20 bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" aria-hidden="true" />
            Resumen de Desempeño
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center"
            role="list"
            aria-label="Resumen de desempeño"
          >
            <div role="listitem">
              <p className="text-3xl font-bold text-primary">95%</p>
              <p className="text-sm text-muted-foreground">Reducción de Desperdicio vs Baseline</p>
            </div>
            <div role="listitem">
              <p className="text-3xl font-bold text-primary">98.98%</p>
              <p className="text-sm text-muted-foreground">Varianza Explicada (R²)</p>
            </div>
            <div role="listitem">
              <p className="text-3xl font-bold text-primary">&lt;10ms</p>
              <p className="text-sm text-muted-foreground">Tiempo de Inferencia</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string
  description: string
  color: "blue" | "purple" | "orange" | "green" | "red" | "yellow"
  highlight?: boolean
}

function MetricCard({ title, value, description, color, highlight }: MetricCardProps) {
  const colorClasses = {
    blue: "bg-primary/10 border-primary/20",
    purple: "bg-primary/10 border-primary/20",
    orange: "bg-accent/10 border-accent/20",
    green: "bg-primary/10 border-primary/20",
    red: "bg-destructive/10 border-destructive/20",
    yellow: "bg-accent/10 border-accent/20",
  }

  return (
    <div
      className={`p-4 rounded-lg border-2 transition-all ${colorClasses[color]} ${
        highlight ? "ring-2 ring-primary/50" : ""
      }`}
      role="listitem"
      aria-label={`${title}: ${value} - ${description}`}
    >
      <p className="text-sm text-muted-foreground mb-1">{title}</p>
      <p className="text-2xl font-bold mb-1">{value}</p>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  )
}
