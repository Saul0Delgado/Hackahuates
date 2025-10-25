# SmartCart AI - HackMTY 2025

**Team Hackahuates**

Sistema de Machine Learning para optimizar cantidades de comidas en vuelos comerciales, reduciendo desperdicio y costos operacionales.

---

## Resultados

**Modelo XGBoost (producción)**
- R²: 0.9898 (98.98% precisión)
- MAE: 3.15 unidades
- MAPE: 3.04%
- Tasa de desperdicio: 1.18% (baseline 24%)
- Reducción de desperdicio: 95%

**Impacto económico proyectado**
- Ahorro por vuelo: $107.25
- Ahorro anual (500 vuelos, 10 productos): $536,250

---

## Inicio Rápido

### Prerequisitos
- Python 3.9+
- Node.js 16+
- Git

### Backend (Terminal 1)

```bash
cd ConsumptionPrediction
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python run_api.py
```

API disponible en: http://localhost:8000
Documentación: http://localhost:8000/docs

### Frontend (Terminal 2)

```bash
cd Frontend
npm install
npm run dev
```

Interfaz disponible en: http://localhost:5173

---

## Módulos del Proyecto

### 1. ConsumptionPrediction (Backend ML)

**Stack tecnológico**
- Python 3.9, FastAPI, Uvicorn
- XGBoost, scikit-learn, pandas
- Optuna (optimización hiperparámetros)

**Funcionalidad**
- API REST para predicciones individuales y batch
- Intervalos de confianza (95%)
- Métricas de negocio en tiempo real
- Feature importance y explicabilidad

**Endpoints principales**
- `POST /api/v1/predict` - Predicción individual
- `POST /api/v1/predict/batch` - Predicción múltiple
- `GET /api/v1/metrics` - Métricas del modelo
- `GET /health` - Estado del servicio

### 2. Frontend (React + TypeScript)

**Stack tecnológico**
- React 19, TypeScript, Vite
- Tailwind CSS, Shadcn/ui
- Lucide Icons

**Funcionalidad**
- Formulario de predicción con validación
- Visualización de métricas del modelo
- Indicador de estado de conexión API
- Diseño responsive

### 3. ExpiringDate (OCR para fechas)

**Stack tecnológico**
- Flask, Tesseract OCR
- OpenCV, PIL, dateparser

**Funcionalidad**
- Extracción de fechas de caducidad desde imágenes
- Procesamiento de imágenes base64
- API REST para integración

```bash
cd ExpiringDate
pip install -r requirements.txt
python app.py
```

API disponible en: http://localhost:5001

---

## Entrenamiento del Modelo

### Entrenar desde cero

```bash
cd ConsumptionPrediction
python scripts/train_optimized.py
```

Genera:
- Modelos entrenados en `data/models/`
- Métricas en `TRAINING_RESULTS.md`
- Gráficas de evaluación

### Optimización de hiperparámetros

```bash
python scripts/optimize_hyperparameters.py
```

Usa Optuna para encontrar mejores configuraciones (100 trials por defecto).

---

## Estructura del Proyecto

```
Hackahuates/
├── ConsumptionPrediction/    # Backend ML + API
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── models/           # Modelos ML
│   │   └── data_loader.py    # Procesamiento datos
│   ├── data/
│   │   ├── models/           # Modelos entrenados (.pkl)
│   │   ├── processed/        # train/val/test splits
│   │   └── raw/              # Dataset original
│   ├── scripts/              # Training scripts
│   └── requirements.txt
│
├── Frontend/                 # React UI
│   ├── src/
│   │   ├── components/       # Componentes React
│   │   ├── services/         # API client
│   │   └── types/            # TypeScript types
│   └── package.json
│
├── ExpiringDate/             # OCR module
│   ├── app.py               # Flask API
│   ├── extract_date.py      # Lógica OCR
│   └── requirements.txt
│
└── Docs/                     # Documentación hackathon
    ├── context.md
    └── HackMTY2025_ChallengeDimensions/
```

---