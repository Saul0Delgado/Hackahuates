# SmartCart AI - Sistema de Predicción de Comidas para Catering Aéreo

**Hackathon MTY 2025 - Team Hackahuates**

Sistema de Machine Learning para optimizar cantidades de comidas en vuelos, reduciendo desperdicio del 95% y ahorrando costos operacionales.

---

## 🚀 **EMPIEZA AQUÍ**

### 👉 **[LEE LA GUÍA DE INICIO COMPLETA](START_HERE.md)** 👈

**Resumen rápido:**

Necesitas **DOS terminales abiertas** simultáneamente:

**Terminal 1 - Backend:**
```bash
cd ConsumptionPrediction
python -m venv venv
venv\Scripts\activate  # Windows | source venv/bin/activate en Mac/Linux
pip install -r requirements.txt
python run_api.py
```
✅ Backend en: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd Frontend
npm install
npm run dev
```
✅ Frontend en: http://localhost:5173

---

## ⚠️ Errores Comunes

| Error | Solución |
|-------|----------|
| "Failed to fetch" | El backend no está corriendo → Inicia el backend en Terminal 1 |
| Badge rojo "🔴 API Desconectada" | Verifica que http://localhost:8000 esté activo |
| Estilos no se ven | Reinicia el frontend (Ctrl+C y `npm run dev`) |

**[Ver guía completa de solución de problemas](START_HERE.md#-solución-de-problemas)**

---

## 📊 Resultados

- **Precisión**: 98.98% (R²)
- **Error**: 3.04% (MAPE)
- **Reducción de Desperdicio**: 95% vs baseline
- **Ahorro Anual**: $536,250 (10 productos)

## 📁 Estructura

```
Hackahuates/
├── ConsumptionPrediction/   # Backend ML + API
├── Frontend/                # React + TypeScript UI
├── Docs/                    # Documentación
└── INTEGRATION_SUMMARY.md   # Guía completa
```

## 📚 Documentación

- [Resumen de Integración](INTEGRATION_SUMMARY.md)
- [Backend README](ConsumptionPrediction/README.md)
- [Frontend Instructions](Frontend/INSTRUCTIONS.md)
- [API Documentation](ConsumptionPrediction/API_DOCUMENTATION.md)
