"use client"

import { useState, useEffect } from "react"
import { PredictionForm } from "./components/PredictionForm"
import { ModelMetricsDashboard } from "./components/ModelMetrics"
import { ProductsManager } from "./components/ProductsManager"
import { VoiceAssistant } from "./components/VoiceAssistant"
import { Button } from "./components/ui/button"
import { Badge } from "./components/ui/badge"
import { Card, CardContent } from "./components/ui/card"
import { apiService } from "./services/api"
import { Activity, BarChart3, RefreshCw, AlertCircle, Package, Mic } from "lucide-react"

type View = "prediction" | "metrics" | "products" | "voice"

export default function App() {
  const [view, setView] = useState<View>("prediction")
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking")

  useEffect(() => {
    checkAPIStatus()
  }, [])

  const checkAPIStatus = async () => {
    try {
      await apiService.checkHealth()
      setApiStatus("online")
    } catch {
      setApiStatus("offline")
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card shadow-sm" role="banner">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Activity className="h-6 w-6 text-primary" aria-hidden="true" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-foreground">SmartCart AI</h1>
                  <p className="text-sm text-muted-foreground">Sistema de Predicción Inteligente</p>
                </div>
              </div>
              <Badge
                variant={apiStatus === "online" ? "default" : "destructive"}
                className="h-6"
                aria-live="polite"
                aria-label={`Estado de la API: ${apiStatus === "checking" ? "verificando" : apiStatus === "online" ? "conectada" : "desconectada"}`}
              >
                <span
                  className={`mr-2 h-2 w-2 rounded-full ${apiStatus === "online" ? "bg-green-400" : "bg-red-400"} animate-pulse`}
                  aria-hidden="true"
                />
                {apiStatus === "checking"
                  ? "Verificando..."
                  : apiStatus === "online"
                    ? "API Conectada"
                    : "API Desconectada"}
              </Badge>
            </div>
            <nav className="flex gap-2 flex-wrap" role="navigation" aria-label="Navegación principal">
              <Button
                variant={view === "prediction" ? "default" : "outline"}
                onClick={() => setView("prediction")}
                className="gap-2"
                aria-pressed={view === "prediction"}
                aria-label="Ver predicciones"
              >
                <Activity className="h-4 w-4" aria-hidden="true" />
                <span>Predicción</span>
              </Button>
              <Button
                variant={view === "metrics" ? "default" : "outline"}
                onClick={() => setView("metrics")}
                className="gap-2"
                aria-pressed={view === "metrics"}
                aria-label="Ver métricas del modelo"
              >
                <BarChart3 className="h-4 w-4" aria-hidden="true" />
                <span>Métricas</span>
              </Button>
              <Button
                variant={view === "products" ? "default" : "outline"}
                onClick={() => setView("products")}
                className="gap-2"
                aria-pressed={view === "products"}
                aria-label="Ver gestión de productos"
              >
                <Package className="h-4 w-4" aria-hidden="true" />
                <span>Productos</span>
              </Button>
              <Button
                variant={view === "voice" ? "default" : "outline"}
                onClick={() => setView("voice")}
                className="gap-2"
                aria-pressed={view === "voice"}
                aria-label="Asistente de voz para productividad"
              >
                <Mic className="h-4 w-4" aria-hidden="true" />
                <span>Asistente de Voz</span>
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8" role="main">
        {apiStatus === "offline" && (
          <Card className="mb-6 border-destructive/50 bg-destructive/5" role="alert" aria-live="assertive">
            <CardContent className="p-6">
              <div className="flex gap-4">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1">
                  <h2 className="text-destructive font-semibold text-lg mb-2">No se puede conectar con el API</h2>
                  <p className="text-foreground/80 leading-relaxed mb-3">
                    Asegúrate de que el servidor esté corriendo en{" "}
                    <code className="bg-muted px-2 py-1 rounded text-sm font-mono">http://localhost:8000</code>
                  </p>
                  <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                    Para iniciar el servidor:{" "}
                    <code className="bg-muted px-2 py-1 rounded font-mono">
                      cd ConsumptionPrediction && python run_api.py
                    </code>
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={checkAPIStatus}
                    className="gap-2 bg-transparent"
                    aria-label="Reintentar conexión con el API"
                  >
                    <RefreshCw className="h-4 w-4" aria-hidden="true" />
                    Reintentar Conexión
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="animate-in fade-in duration-500">
          {view === "prediction" ? (
            <PredictionForm />
          ) : view === "metrics" ? (
            <ModelMetricsDashboard />
          ) : view === "products" ? (
            <ProductsManager />
          ) : (
            <VoiceAssistant />
          )}
        </div>
      </main>

      <footer className="border-t bg-card mt-auto" role="contentinfo">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" aria-hidden="true" />
              <span className="font-semibold text-foreground">SmartCart AI</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
              Sistema de Predicción de Comidas para Catering Aéreo
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="font-medium text-primary">95%</span>
                <span>Reducción de desperdicio</span>
              </div>
              <span className="text-border" aria-hidden="true">
                •
              </span>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="font-medium text-primary">98.98%</span>
                <span>Precisión del modelo</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
