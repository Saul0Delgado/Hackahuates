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

## ⚙️ Configuración de Variables de Entorno

Crear archivo `.env` **en la raíz del proyecto** con:

```env
GEMINI_API_KEY=tu_api_key_aqui
ELEVEN_LABS_API_KEY=tu_api_key_aqui
```

**Obtener API Keys:**
- **Gemini**: https://makersuite.google.com/app/apikey
- **ElevenLabs**: https://elevenlabs.io/app/settings/api-keys

---

## 🚀 Inicio Rápido (3 Servicios)

### Prerequisitos
- Python 3.9+
- Node.js 16+
- Git
- **Tesseract OCR** (para ExpiringDate)
  - Windows: https://github.com/tesseract-ocr/tesseract/wiki/Downloads
  - Mac: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

### 1️⃣ Backend - Modelo Predictivo + Asistente de Voz (Terminal 1)

```bash
cd ConsumptionPredictionv2
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
pip install google-generativeai elevenlabs python-dotenv

# Ejecutar API
uvicorn API_PRODUCTO_LEVEL_TEMPLATE:app --reload --host 0.0.0.0 --port 8000
```

✅ API disponible en: http://localhost:8000
✅ Documentación: http://localhost:8000/docs
✅ Voice Assistant: `POST /api/v1/productivity/voice-assistant`

### 2️⃣ ExpiringDate - OCR para Fechas de Caducidad (Terminal 2)

```bash
cd ExpiringDate
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```

✅ API disponible en: http://localhost:5000
✅ Endpoints: `/api/extraction/extract_date` (base64 image)

### 3️⃣ Frontend - Interfaz Web (Terminal 3)

```bash
cd Frontend
npm install
npm run dev
```

✅ Interfaz disponible en: http://localhost:5173
✅ Acceso desde navegador: http://localhost:5173

**Pantallas principales:**
- 📊 Predicción: Modelo ML para cantidad óptima de comidas
- 🎤 Asistente de Voz: Preguntas operacionales en tiempo real
- 📸 Gestión de Fechas: Detectar caducidades con cámara
- 📈 Métricas: Performance del modelo

---

## 🏗️ Módulos del Proyecto

### 1. ConsumptionPredictionv2 (Backend ML + Asistente de Voz)

**Stack tecnológico**
- Python 3.9, FastAPI, Uvicorn
- XGBoost, scikit-learn, pandas, NumPy
- **Google Gemini 2.0 Flash** (conversación IA)
- **ElevenLabs Multilingual v2** (síntesis voz natural)
- python-dotenv (gestión de variables de entorno)

**Funcionalidad**
- API REST predicciones por categoría de producto (6 modelos)
- Intervalos de confianza (95%) y recomendaciones accionables
- **Asistente conversacional**: Responde preguntas operacionales en tiempo real
- **Voz natural en español**: Paula voice desde ElevenLabs
- Métricas de negocio (waste reduction, ahorro, accuracy)

**Endpoints principales**
- `POST /api/v1/predict` - Predicción por producto/categoría
- `POST /api/v1/predict/batch` - Predicciones múltiples
- `GET /api/v1/metrics` - Métricas y performance
- **`POST /api/v1/productivity/voice-assistant`** - Asistente de voz conversacional
- `GET /health` - Estado del servicio

### 2. Frontend (React + TypeScript + IA Conversacional)

**Stack tecnológico**
- React 19, TypeScript, Vite
- Tailwind CSS, Shadcn/ui, Framer Motion
- Lucide Icons, Web Speech API
- ElevenLabs (reproducción audio natural)

**Funcionalidad**
- 📊 **Predicción**: Formulario con validación, selección origen/destino
- 🎤 **Asistente de Voz**: Interfaz moderna con reconocimiento y síntesis voz
- 📸 **Gestión de Fechas**: Webcam + upload de imágenes para OCR
- 📈 **Métricas**: Dashboard con performance y ROI
- 💾 **Historial**: Conversaciones guardadas con operarios
- 🎨 **Diseño**: SaaS 2025 style, branding #010165, responsive

**Componentes principales**
- `PredictionForm.tsx` - Predicción cantidad óptima
- `VoiceAssistantModern.tsx` - Conversación IA con voz natural
- `ProductsManager.tsx` - Detección fechas con cámara/upload
- `ModelMetricsDashboard.tsx` - Visualización métricas

### 3. ExpiringDate (OCR + Computer Vision para Fechas)

**Stack tecnológico**
- Flask, Flask-RESTX, Flask-CORS
- **Tesseract OCR** (detección texto en imágenes)
- OpenCV, PIL, NumPy, dateparser
- Gunicorn (production server)

**Funcionalidad**
- 📸 Extracción automática fechas de caducidad desde imágenes
- 🎯 Detección ángulos variables, etiquetas borrosas, múltiples formatos
- 📝 Procesamiento base64 (cámara) y multipart (upload)
- 🔄 Integración con Frontend (ProductsManager component)
- 📊 Inventario FIFO automático
- ⚠️ Alertas expiraciones próximas

**Endpoints principales**
- `POST /api/extraction/extract_date` - Base64 image input
- `POST /api/extraction/extract_date_from_image` - File upload input
- `GET /health` - Status del servicio

**Modelos OCR**
- Preprocessing: contraste, rotación automática, denoising
- Tesseract + pattern matching para formatos fecha
- Confidence thresholding para precision

---

## 🎙️ Asistente de Voz Conversacional (Feature Principal)

**Tecnología integrada:**
- **Google Gemini 2.0 Flash** - Comprensión conversacional con contexto operacional
- **ElevenLabs Multilingual v2** - Síntesis voz natural en español
- **Web Speech API** - Reconocimiento voz navegador (fallback automático)

**Capabilities:**
- ✅ Responde preguntas operacionales en tiempo real (30s → 10s)
- ✅ Entiende reglas por aerolínea (Aeromexico, Delta, United, etc)
- ✅ Consultas sobre reuso de productos, expiración, contrato específico
- ✅ Voz 100% natural (Paula voice), manos libres, español nativo
- ✅ Contexto drawer (ID, tipo vuelo, categoría, inventario)
- ✅ Graceful degradation: funciona sin ElevenLabs (fallback Web Speech API)

**Ejemplos de uso:**
```
Operario: "¿Puedo reusar esta botella de Sprite a la mitad para Aeromexico?"
Assistant: "Sí, para Aeromexico puedes reusar botellas si están más del 50% llenas,
siempre que el volumen total cumpla con el mínimo requerido."

Operario: "¿Este producto vence en 3 días, lo agrego al carrito?"
Assistant: "No, descártalo. La regla es mantener mínimo 5 a 7 días antes de vencer
para cumplir cold-chain compliance."
```

**Impacto operacional:**
- 🎯 Reduce sobrecarga cognitiva (memorizando contratos)
- 🎯 Minimiza errores por distracción (trabajo repetitivo)
- 🎯 Elimina fricción por consulta de documentación manual
- 🎯 Mejora productividad: 3.5 min → 2.5 min por carrito

---

## 📚 Entrenamiento del Modelo

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

## 📁 Estructura del Proyecto

```
Hackahuates/
├── .env                      # 🔐 Variables de entorno (GEMINI_API_KEY, ELEVEN_LABS_API_KEY)
│
├── ConsumptionPredictionv2/  # 🧠 Backend ML + Asistente de Voz
│   ├── API_PRODUCTO_LEVEL_TEMPLATE.py  # FastAPI principal
│   ├── voice_assistant_service.py      # 🎤 Gemini + ElevenLabs
│   ├── pipeline/             # 🔧 Training pipeline
│   │   ├── 00_excel_to_csv_converter.py
│   │   ├── 01_data_exploration/
│   │   ├── 02_data_preparation/
│   │   ├── 03_feature_engineering/
│   │   ├── 04_model_training/         # XGBoost, Random Forest, Neural Networks
│   │   └── 05_evaluation/
│   ├── data/
│   │   ├── models/           # Modelos entrenados por categoría (.pkl)
│   │   ├── processed/        # train/val/test splits
│   │   └── raw/              # Dataset original
│   ├── requirements.txt      # Dependencies (FastAPI, Uvicorn, XGBoost, google-generativeai, elevenlabs)
│   └── .env (heredado)
│
├── Frontend/                 # 🎨 React UI + Speech Input/Output
│   ├── src/
│   │   ├── components/
│   │   │   ├── PredictionForm.tsx          # 📊 Predicción ML
│   │   │   ├── VoiceAssistantModern.tsx    # 🎤 Asistente conversacional
│   │   │   ├── ProductsManager.tsx         # 📸 OCR detector fechas
│   │   │   ├── ModelMetrics.tsx            # 📈 Dashboard métricas
│   │   │   ├── VoiceOrb.tsx                # 🔘 Control de voz
│   │   │   └── WebcamModal.tsx             # 📷 Captura cámara
│   │   ├── services/api.ts   # Cliente API (predict, voice-assistant, extraction)
│   │   ├── types/api.ts      # TypeScript types
│   │   ├── App.tsx           # Layout principal
│   │   └── main.tsx
│   ├── package.json          # React 19, Framer Motion, Tailwind, etc.
│   └── vite.config.ts
│
├── ExpiringDate/             # 🔍 OCR + Computer Vision
│   ├── app.py                # Flask-RESTX API
│   ├── extract_date.py       # Tesseract OCR + pattern matching
│   ├── utils.py              # Preprocessing (contraste, rotación, denoising)
│   ├── requirements.txt       # Flask, pytesseract, OpenCV, PIL, dateparser
│   └── logs/                 # Logging detallado
│
├── Docs/                     # 📚 Documentación
│   ├── context.md            # 4 PDFs integrados (Pick&Pack, Expiration, Consumption, Productivity)
│   └── HackMTY2025_ChallengeDimensions/
│
└── README.md                 # Este archivo
```

---

## 🔧 Solución de Problemas

### Backend (ConsumptionPredictionv2) no inicia

**Error: `Port 8000 already in use`**
```bash
# Windows: Encontrar proceso en puerto 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>
```

**Error: `GEMINI_API_KEY not found`**
- ✅ Verificar que `.env` existe en raíz del proyecto
- ✅ Validar formato: `GEMINI_API_KEY=<tu_key_sin_espacios>`
- ✅ Reiniciar terminal/IDE para recargar variables
- ✅ En Windows, verificar encoding UTF-8 del archivo .env

**Error: `ModuleNotFoundError: No module named 'google.generativeai'`**
```bash
pip install google-generativeai elevenlabs python-dotenv
```

### Voice Assistant sin audio (Asistente de Voz)

**Escucho voz robotizada en lugar de natural (Paula voice)**
- ✅ Verificar `ELEVEN_LABS_API_KEY` válida en `.env`
- ✅ Revisar logs backend: `[ELEVENLABS SUCCESS]` debe aparecer
- ✅ Si falla: sistema fallback automático a Web Speech API
- ✅ Intentar actualizar el navegador (borrar caché)

**"ELEVENLABS ERROR" en logs pero no hay audio**
- ✅ Verificar quota ElevenLabs (10k chars gratis/mes)
- ✅ Revisar respuesta del backend: error 402 = sin créditos
- ✅ Aumentar plan ElevenLabs o usar Web Speech API

**Micrófono no funciona al hacer preguntas**
- ✅ Conceder permisos de micrófono al navegador
- ✅ Verificar que navegador soporta Web Speech API (Chrome, Edge, Safari)
- ✅ Firefox requiere complementos adicionales
- ✅ Ver logs: `[VOICE ASSISTANT] New query received`

### ExpiringDate (OCR) no detecta fechas

**Tesseract no está instalado**
- Windows: Descargar desde https://github.com/tesseract-ocr/tesseract/wiki/Downloads
- Mac: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: Agregar a PATH o configurar en código: `pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

**Detección de fechas incorrecta/vacía**
- ✅ Revisar que imagen tiene buena calidad (fecha clara, legible)
- ✅ Aumentar contraste y reducir ruido (preprocessing automático intenta)
- ✅ Formatos soportados: DD/MM/YYYY, DD-MM-YYYY, JJ.MM.AA, etc
- ✅ Ver logs: `[EXTRACTION] Detected date: ...`

**Error 500 en endpoint `/api/extraction/extract_date`**
- ✅ Revisar que imagen base64 es válida
- ✅ Tamaño máximo: 5MB
- ✅ Formato: JPEG, PNG, BMP (no WebP)
- ✅ Ver logs Flask: python app.py produce output detallado

### Frontend (React) problemas

**"Cannot GET /api/..." o 404 errors**
- ✅ Verificar que Backend está corriendo en `http://localhost:8000`
- ✅ Revisar CORS habilitado (backend incluye `CORSMiddleware`)
- ✅ En navegador, F12 → Network → ver requests fallidas

**Voice Assistant tab en blanco / no carga**
- ✅ Verificar backend respondiendo: curl http://localhost:8000/docs
- ✅ Revisar logs frontend (F12 → Console)
- ✅ Recargar página (Ctrl+Shift+R hard refresh)

**Componente ProductsManager no se conecta a ExpiringDate**
- ✅ Verificar ExpiringDate corriendo en `http://localhost:5000`
- ✅ Revisar CORS en ExpiringDate: `CORS(app)` debe estar activo
- ✅ Endpoint esperado: `http://localhost:5000/api/extraction/extract_date`

### GPU / Performance

**Modelo ML muy lento para predecir**
- ✅ Modelos XGBoost típicamente rápidos (<100ms)
- ✅ Si lento: revisar que no hay otras tareas pesadas
- ✅ Considerar quantization para producción

**Asistente de Voz tarda mucho en responder**
- ✅ Gemini 2.0 Flash es rápido (~1-2s)
- ✅ Si >5s: revisar latencia red, tamaño prompt
- ✅ ElevenLabs TTS: ~500-800ms por respuesta

---

## 📞 Soporte y Contribuciones

**Reportar bugs:**
- Crear issue en GitHub con logs backend + frontend
- Incluir versión Python, Node.js, sistema operativo

**Mejoras sugeridas:**
- Integrar datos reales GateGroup (consumo, inventario, waste logs)
- Entrenar modelos con históricos específicos por ruta/aerolínea
- Agregar dashboard gerencial (analytics, ROI)
- Expandir a más idiomas ElevenLabs
- Implementar versión mobile (iOS/Android)

---

**SmartCart AI** - Hackathon HackMTY 2025 | Team Hackahuates
Reduciendo desperdicio de comidas aéreas con ML + IA Conversacional en voz natural 🎤✈️