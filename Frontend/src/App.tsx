import { useState, useEffect } from 'react';
import { PredictionForm } from './components/PredictionForm';
import { ModelMetricsDashboard } from './components/ModelMetrics';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Card, CardContent } from './components/ui/card';
import { apiService } from './services/api';

type View = 'prediction' | 'metrics';

function App() {
  const [view, setView] = useState<View>('prediction');
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    checkAPIStatus();
  }, []);

  const checkAPIStatus = async () => {
    try {
      await apiService.checkHealth();
      setApiStatus('online');
    } catch {
      setApiStatus('offline');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">SmartCart AI</h1>
              <Badge variant={apiStatus === 'online' ? 'default' : 'destructive'}>
                {apiStatus === 'checking' ? 'Verificando...' : apiStatus === 'online' ? '🟢 API Conectada' : '🔴 API Desconectada'}
              </Badge>
            </div>
            <nav className="flex gap-2">
              <Button
                variant={view === 'prediction' ? 'default' : 'outline'}
                onClick={() => setView('prediction')}
              >
                📊 Predicción
              </Button>
              <Button
                variant={view === 'metrics' ? 'default' : 'outline'}
                onClick={() => setView('metrics')}
              >
                📈 Métricas
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {apiStatus === 'offline' && (
          <Card className="mb-6 bg-destructive/10 border-destructive">
            <CardContent className="p-4">
              <p className="text-destructive font-medium">
                ⚠️ No se puede conectar con el API. Asegúrate de que el servidor esté corriendo en http://localhost:8000
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Para iniciar el servidor: <code className="bg-muted px-2 py-1 rounded">cd ConsumptionPrediction && python run_api.py</code>
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={checkAPIStatus}
                className="mt-3"
              >
                Reintentar Conexión
              </Button>
            </CardContent>
          </Card>
        )}

        {view === 'prediction' ? <PredictionForm /> : <ModelMetricsDashboard />}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>SmartCart AI - Sistema de Predicción de Comidas para Catering Aéreo</p>
          <p className="mt-1">Reducción de desperdicio del 95% | Precisión 98.98%</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
