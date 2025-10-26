"use client"

import { useState, useEffect } from "react"
import { PredictionForm } from "./components/PredictionForm"
import { ModelMetricsDashboard } from "./components/ModelMetrics"
import { ProductsManager } from "./components/ProductsManager"
import { VoiceAssistantModern } from "./components/VoiceAssistantModern"
import { Button } from "./components/ui/button"
import { Card, CardContent } from "./components/ui/card"
import { apiService } from "./services/api"
import { Zap, BarChart3, RefreshCw, AlertCircle, Package, Mic } from "lucide-react"

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
      <header className="border-b border-slate-200 bg-white" role="banner">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg" style={{ backgroundColor: '#010165' }}>
                <Zap className="h-6 w-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight" style={{ color: '#010165' }}>SmartCart AI</h1>
                <p className="text-sm text-slate-600">Sistema de Predicción Inteligente</p>
              </div>
            </div>
            <nav className="flex gap-2 flex-wrap" role="navigation" aria-label="Navegación principal">
              <Button
                onClick={() => setView("prediction")}
                className="gap-2 rounded-lg h-10"
                style={{
                  backgroundColor: view === "prediction" ? "#010165" : "transparent",
                  color: view === "prediction" ? "white" : "#010165",
                  border: view === "prediction" ? "none" : "1px solid #e2e8f0"
                }}
                aria-pressed={view === "prediction"}
                aria-label="Ver predicciones"
              >
                <Zap className="h-4 w-4" aria-hidden="true" />
                <span>Predicción</span>
              </Button>
              <Button
                onClick={() => setView("metrics")}
                className="gap-2 rounded-lg h-10"
                style={{
                  backgroundColor: view === "metrics" ? "#010165" : "transparent",
                  color: view === "metrics" ? "white" : "#010165",
                  border: view === "metrics" ? "none" : "1px solid #e2e8f0"
                }}
                aria-pressed={view === "metrics"}
                aria-label="Ver métricas del modelo"
              >
                <BarChart3 className="h-4 w-4" aria-hidden="true" />
                <span>Métricas</span>
              </Button>
              <Button
                onClick={() => setView("products")}
                className="gap-2 rounded-lg h-10"
                style={{
                  backgroundColor: view === "products" ? "#010165" : "transparent",
                  color: view === "products" ? "white" : "#010165",
                  border: view === "products" ? "none" : "1px solid #e2e8f0"
                }}
                aria-pressed={view === "products"}
                aria-label="Ver gestión de productos"
              >
                <Package className="h-4 w-4" aria-hidden="true" />
                <span>Productos</span>
              </Button>
              <Button
                onClick={() => setView("voice")}
                className="gap-2 rounded-lg h-10"
                style={{
                  backgroundColor: view === "voice" ? "#010165" : "transparent",
                  color: view === "voice" ? "white" : "#010165",
                  border: view === "voice" ? "none" : "1px solid #e2e8f0"
                }}
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
          <Card className="mb-6 border-red-200 bg-red-50 rounded-lg" role="alert" aria-live="assertive">
            <CardContent className="p-6">
              <div className="flex gap-4">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1">
                  <h2 className="text-red-600 font-semibold text-lg mb-2">No se puede conectar con el API</h2>
                  <p className="text-slate-700 leading-relaxed mb-3">
                    Asegúrate de que el servidor esté corriendo en{" "}
                    <code className="bg-red-100 px-2 py-1 rounded text-sm font-mono text-red-800">http://localhost:8000</code>
                  </p>
                  <p className="text-sm text-slate-600 mb-4 leading-relaxed">
                    Para iniciar el servidor:{" "}
                    <code className="bg-red-100 px-2 py-1 rounded font-mono text-red-800">
                      cd ConsumptionPrediction && python run_api.py
                    </code>
                  </p>
                  <Button
                    size="sm"
                    onClick={checkAPIStatus}
                    className="gap-2 rounded-lg"
                    style={{ backgroundColor: '#010165', color: 'white' }}
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
            <VoiceAssistantModern />
          )}
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white mt-auto" role="contentinfo">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5" style={{ color: '#010165' }} aria-hidden="true" />
              <span className="font-semibold" style={{ color: '#010165' }}>SmartCart AI</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
              Sistema de Predicción de Comidas para Catering Aéreo
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <span className="font-semibold" style={{ color: '#010165' }}>95%</span>
                <span>Reducción de desperdicio</span>
              </div>
              <span className="text-slate-300" aria-hidden="true">
                •
              </span>
              <div className="flex items-center gap-2 text-slate-600">
                <span className="font-semibold" style={{ color: '#010165' }}>98.98%</span>
                <span>Precisión del modelo</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
