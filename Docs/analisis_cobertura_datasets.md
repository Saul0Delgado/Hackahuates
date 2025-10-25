# Análisis de Cobertura: Datasets vs. Requerimientos

## ✅ LO QUE SÍ SE PUEDE HACER CON LOS DATASETS ACTUALES

### 1. **Time Series Forecasting (Plant 1 & 2)** - COBERTURA COMPLETA ✅

**Dataset disponible**:
- Plant 1: 845 días (2023-2025) con `flights`, `passengers`, `max_capacity`
- Plant 2: 973 días (2023-2025) con `flights`

**Lo que se puede hacer**:
- ✅ Forecasting de vuelos diarios (ambas plantas)
- ✅ Forecasting de pasajeros diarios (Plant 1)
- ✅ Detección de patrones estacionales/semanales
- ✅ Predicción de utilización (`passengers/max_capacity`)
- ✅ Modelo auto-ajustable con objetivo ≤2% error
- ✅ Comparación de volumen entre plantas

**Técnicas aplicables**:
- ARIMA, SARIMA, Prophet
- LSTM, GRU (deep learning)
- XGBoost con features temporales
- Ensemble methods

**Limitaciones**:
- ❌ No hay información de rutas específicas (solo totales por día)
- ❌ No hay desglose por tipo de vuelo (short/medium/long-haul)
- ❌ No se puede vincular con consumo específico de productos

---

### 2. **Consumption Prediction (792 registros)** - COBERTURA PARCIAL ⚠️

**Dataset disponible**:
- 144 vuelos únicos
- 12 fechas (solo ~1 mes de datos)
- 6 orígenes
- 10 productos
- Variables: `Flight_Type`, `Service_Type`, `Passenger_Count`, `Standard_Specification_Qty`, `Quantity_Consumed`, `Quantity_Returned`

**Lo que SÍ se puede hacer**:
- ✅ **Predicción de consumo por producto** dado: flight_type, service_type, passenger_count
- ✅ **Optimización de cantidades preparadas** (`Standard_Specification_Qty`) para reducir waste
- ✅ **Cálculo de waste rate** por producto, tipo de vuelo, tipo de servicio
- ✅ **Análisis de patrones**: Retail vs Pick & Pack
- ✅ **Costo de desperdicio** por vuelo/producto
- ✅ **Consumption rate per capita** por producto/vuelo
- ✅ **Feature engineering**: waste_rate, consumption_rate, overage_percentage

**Técnicas aplicables**:
- Regression models (Linear, Ridge, Lasso)
- Gradient Boosting (XGBoost, LightGBM, CatBoost)
- Random Forest
- Neural Networks (MLP)
- Quantile regression (para intervalos de confianza)

**Limitaciones CRÍTICAS**:
- ❌ **Solo 12 fechas**: No se puede capturar estacionalidad anual
- ❌ **No hay desglose por cabin class** (Business/Economy/First) - solo total de pasajeros
- ❌ **No hay datos de special meals** (vegetarian, kosher, etc.)
- ❌ **No hay datos de crew meals**
- ❌ **No hay información de ruta específica** (solo origen, no destino)
- ❌ **No hay duración de vuelo** en horas
- ❌ **Crew_Feedback mayormente vacío** (91.3% null)
- ❌ **No se puede vincular con inventory/expiration data** (sin Product_ID común claro)

---

### 3. **Expiration Date Management (150 registros)** - COBERTURA PARCIAL ⚠️

**Dataset disponible**:
- 10 productos únicos
- 126 lotes
- 78 fechas de expiración diferentes
- Variables: `Product_ID`, `LOT_Number`, `Expiry_Date`, `Quantity`

**Lo que SÍ se puede hacer**:
- ✅ **Cálculo de days_to_expiry** para cada lote
- ✅ **Clasificación de riesgo de expiración** (Critical/Warning/Safe)
- ✅ **Priorización FIFO** para picking
- ✅ **Análisis de shelf-life** por categoría de producto
- ✅ **Inventario usable** para ventana de tiempo específica
- ✅ **Alertas de productos próximos a vencer**

**Técnicas aplicables**:
- Rule-based systems (FIFO)
- Optimization algorithms (linear programming para picking)
- Survival analysis (predecir probabilidad de expiración)
- Clustering por shelf-life patterns

**Limitaciones CRÍTICAS**:
- ❌ **NO hay datos de consumo histórico por lote** (no se puede predecir si se consumirá antes de expirar)
- ❌ **NO hay datos de waste por expiración** vs. otras causas
- ❌ **NO hay datos de recepción de lotes** (solo expiry, no fecha de llegada)
- ❌ **NO se puede vincular con vuelos específicos** (sin Flight_ID)
- ❌ **NO hay datos de proveedores** (Supplier_ID)
- ❌ **NO hay storage zone/temperature data**
- ❌ **Los Product_IDs NO coinciden** con Consumption Prediction dataset:
  - Expiration: COF006, CHS010, SNK001, etc.
  - Consumption: BRD001, CRK075, DRK023, etc.

  **ESTO ES UN PROBLEMA GRAVE** - Los datasets están desconectados

---

### 4. **Productivity Estimation (100 registros)** - COBERTURA MUY LIMITADA ⚠️

**Dataset disponible**:
- 100 drawers únicos
- 2 tipos de vuelo (Business/Economy)
- 4 categorías (Beverage, Breakfast, Snack, Meal)
- Variables: `Total_Items`, `Unique_Item_Types`, `Item_List`

**Lo que SÍ se puede hacer**:
- ✅ **Análisis de complejidad** de drawers (unique_items/total_items)
- ✅ **Clustering de configuraciones** por tipo de vuelo
- ✅ **Parsing de Item_List** para análisis granular de SKUs
- ✅ **Benchmark de configuraciones** estándar

**Técnicas aplicables**:
- Clustering (K-means, hierarchical)
- Association rules (para patterns de items)
- Text parsing/NLP (para Item_List)

**Limitaciones CRÍTICAS**:
- ❌ **NO hay datos de tiempo de preparación** (ground truth missing)
- ❌ **NO hay datos de recursos asignados** (número de empleados, tiempo real)
- ❌ **NO hay datos de eficiencia** por trabajador/estación
- ❌ **NO se puede estimar productividad** sin targets reales
- ❌ **NO se puede vincular con vuelos específicos**
- ❌ **Flight_Type aquí es cabin class**, en Consumption es haul distance (confusión de términos)
- ❌ **Sin datos de errores/re-work**

---

## ❌ GAPS CRÍTICOS EN LOS DATOS

### 1. **DESCONEXIÓN ENTRE DATASETS**

Los 4 datasets **NO están vinculados entre sí**:

| Dataset | Key IDs | Problema |
|---------|---------|----------|
| Time Series | `day` (fecha) | NO hay Flight_ID, NO hay productos |
| Consumption | `Flight_ID`, `Product_ID` (BRD001, CRK075...) | Product_IDs diferentes a Expiration |
| Expiration | `Product_ID` (COF006, CHS010...) | Product_IDs diferentes a Consumption |
| Productivity | `Drawer_ID` | NO hay Flight_ID, NO hay vinculación con otros datasets |

**No se puede hacer**:
- ❌ Vincular consumo de un vuelo con su inventario disponible
- ❌ Aplicar restricciones de expiration al predecir cantidades
- ❌ Vincular productividad con vuelos específicos
- ❌ Integrar las 4 dimensiones del problema en un solo flujo

### 2. **FEATURES CLAVE FALTANTES (según entrevistas + PDFs)**

#### Datos de Vuelo:
- ❌ **Route completa** (origen-destino)
- ❌ **Duración de vuelo en horas** (solo hay Flight_Type: short/medium/long)
- ❌ **Hora de salida** (morning/afternoon/evening/red-eye)
- ❌ **Day of week** (se puede derivar de fecha, pero no está)
- ❌ **Aircraft type** (tamaño, configuración)

#### Datos de Pasajeros:
- ❌ **Desglose por cabin class** (Business/Economy/First) - CRÍTICO según PDFs
- ❌ **No-show rate** (booked vs. boarded)
- ❌ **Special meals counts** (vegetarian, kosher, halal, medical, etc.)
- ❌ **Crew meal count**

#### Datos de Inventario:
- ❌ **Packaging unit size** (meals per tray, trays per cart)
- ❌ **Weight/volume** de productos (hay en Expiration pero NO en Consumption)
- ❌ **Storage zone/temperature** requirements
- ❌ **Supplier ID** y variabilidad por proveedor

#### Datos de Costos y Políticas:
- ❌ **Overage percentage policy** por contrato/aerolínea
- ❌ **Minimum meal policy** por clase de cabina
- ❌ **Shortage cost vs. overage cost** (para optimización cost-aware)
- ❌ **Reglas de contrato** por aerolínea (botellas medias, etc.)

#### Datos Operacionales:
- ❌ **Preparation lead time** (cuántas horas antes se prepara)
- ❌ **Tiempo real de armado** por carrito/vuelo
- ❌ **Errores de empacado** (QC failures)
- ❌ **Causas de waste** clasificadas (expiration vs. spoilage vs. QC vs. no-consumption)
- ❌ **Temperature monitoring logs**
- ❌ **Datos de retornos detallados** (por qué se regresaron productos)

#### Datos Temporales:
- ❌ **Seasonality** (solo 12 fechas en Consumption, 1 mes)
- ❌ **Holiday calendar** (is_holiday)
- ❌ **Events** (conferences, sports, disruptions)
- ❌ **Weather data** (puede afectar no-shows)

---

## 🔍 ANÁLISIS POR REQUERIMIENTO DEL PROYECTO

### Requerimiento 1: **Predicción de Consumo con ≤2% Error**

**Datasets necesarios**: Consumption Prediction, Time Series

**Estado**: ⚠️ **PARCIALMENTE POSIBLE**

✅ **Puedes hacer**:
- Modelo básico: `Quantity_Consumed ~ Flight_Type + Service_Type + Passenger_Count + Product_ID`
- Features temporales derivadas de Time Series (trends, seasonality)
- Optimización de `Standard_Specification_Qty`

❌ **NO puedes hacer bien**:
- Predicción robusta con solo 12 fechas (sin estacionalidad anual)
- Considerar cabin class distribution (dato faltante)
- Considerar special meals (dato faltante)
- Aplicar constraints de inventory/expiration (datasets desconectados)

**Precisión esperada**: Dudosa alcanzar ≤2% con datos tan limitados

---

### Requerimiento 2: **Gestión de Expiration/FIFO**

**Dataset necesario**: Expiration Date Management

**Estado**: ✅ **POSIBLE (standalone)**

✅ **Puedes hacer**:
- Sistema de priorización FIFO
- Alertas de productos próximos a expirar
- Filtrado de inventario usable por ventana de tiempo

❌ **NO puedes hacer**:
- Vincular con predicción de consumo (Product_IDs no coinciden)
- Optimizar compras basado en tasa de expiración histórica (sin histórico)
- Predecir waste por expiration vs. otras causas

---

### Requerimiento 3: **Pick & Pack Process Optimization**

**Dataset necesario**: Productivity Estimation

**Estado**: ❌ **NO POSIBLE**

❌ **Falta**:
- Ground truth de tiempo de preparación
- Datos de recursos (empleados, estaciones)
- Vinculación con vuelos reales
- Métricas de errores/re-work

**Solo puedes hacer**: Análisis descriptivo de configuraciones, NO optimización

---

### Requerimiento 4: **Reducir Tiempo de Armado (3s por bandeja)**

**Dataset necesario**: Datos operacionales de tiempo

**Estado**: ❌ **NO POSIBLE**

❌ **Falta completamente**:
- Timestamps de inicio/fin de armado
- Tiempo por paso del proceso
- Tiempo por bandeja/carrito
- Identificación de cuellos de botella

---

### Requerimiento 5: **Asistencia para Reglas de Contrato (30s → 10s)**

**Dataset necesario**: Contratos por aerolínea, reglas de negocio

**Estado**: ❌ **NO HAY DATOS**

❌ **Falta completamente**:
- Matriz de aerolíneas × reglas de contrato
- Cláusulas sobre productos reutilizables
- Vinculación Flight_ID → Contract_ID → Rules

---

### Requerimiento 6: **Optimización de Refill Dinámico**

**Datasets necesarios**: Consumption + Inventory histórico

**Estado**: ⚠️ **MUY LIMITADO**

⚠️ **Problema**:
- Consumption dataset tiene solo 12 fechas (insuficiente para patrones robustos)
- No hay datos históricos de refill actual vs. óptimo
- No hay datos de shortages/overages por vuelo

---

## 📊 RESUMEN DE COBERTURA

| Dimensión del Problema | Cobertura Dataset | Implementable | Notas |
|------------------------|-------------------|---------------|-------|
| **Time Series Forecasting** | 80% | ✅ SÍ | Pero solo agregado diario, sin granularidad por vuelo |
| **Consumption Prediction** | 40% | ⚠️ LIMITADO | Solo 12 fechas, faltan features clave (cabin class, special meals) |
| **Expiration Management** | 60% | ⚠️ STANDALONE | Funciona solo, pero NO se integra con otros datasets |
| **Productivity Estimation** | 20% | ❌ NO | Sin ground truth de tiempo/recursos |
| **Pick & Pack Optimization** | 10% | ❌ NO | Sin datos operacionales de tiempo |
| **Contract Rules Assistance** | 0% | ❌ NO | Sin datos de contratos |
| **Integración 4 Dimensiones** | 15% | ❌ NO | Datasets desconectados, Product_IDs incompatibles |

---

## 🎯 LO QUE REALISTAMENTE PUEDES ENTREGAR

### ✅ **SOLUCIONES VIABLES CON DATASETS ACTUALES**:

#### 1. **Time Series Forecasting MVP** (Plant 1 & 2)
- Modelo SARIMA/Prophet/LSTM para predecir flights y passengers diarios
- Target: ≤2% error (alcanzable con 845+ días de datos)
- Auto-ajuste con reentrenamiento periódico
- **Valor**: Forecasting de demanda agregada a nivel planta

#### 2. **Consumption Prediction Prototype**
- Modelo ML para predecir `Quantity_Consumed` dado flight_type, service_type, passenger_count, product_id
- Optimización de `Standard_Specification_Qty` para minimizar waste
- Análisis comparativo: Retail vs. Pick & Pack
- **Limitación**: Solo 12 fechas, sin estacionalidad robusta
- **Valor**: Prototipo para demostrar concepto, requiere más datos para producción

#### 3. **Expiration Management System**
- Sistema de priorización FIFO por lote
- Dashboard de alertas de productos próximos a expirar
- Cálculo de inventario usable por ventana de tiempo
- **Valor**: Herramienta standalone para reducir waste por expiración

#### 4. **Drawer Configuration Analysis**
- Clustering de configuraciones típicas por flight_type y drawer_category
- Análisis de complejidad (unique_items/total_items)
- Benchmark de configuraciones estándar
- **Limitación**: Descriptivo, NO predictivo (sin tiempo real)
- **Valor**: Insights para estandarización

---

### ⚠️ **SOLUCIONES QUE REQUIEREN DATOS ADICIONALES**:

#### 5. **Consumption Prediction Robusto** (para producción)
**Datos adicionales necesarios**:
- Más fechas (mínimo 1 año completo para capturar estacionalidad)
- Desglose por cabin class (Business/Economy/First)
- Special meals counts
- Duración de vuelo en horas
- Route completa (origen-destino)
- Day of week, holidays

#### 6. **Integrated Inventory-Consumption System**
**Datos adicionales necesarios**:
- Unificación de Product_IDs entre Consumption y Expiration
- Vinculación Flight_ID con inventory disponible pre-vuelo
- Histórico de waste clasificado por causa (expiration, spoilage, QC, no-consumption)

#### 7. **Productivity Optimization**
**Datos adicionales necesarios**:
- Timestamps de armado (inicio/fin por carrito/vuelo)
- Recursos asignados (número de empleados por estación)
- Errores/re-work rates
- Vinculación Drawer → Flight_ID

#### 8. **Contract Rules Assistant**
**Datos adicionales necesarios**:
- Matriz de aerolíneas × contratos × reglas
- Vinculación Flight_ID → Airline → Contract
- Reglas de reutilización de productos por aerolínea

---

## 💡 RECOMENDACIONES

### Corto Plazo (con datasets actuales):

1. **Implementa Time Series Forecasting** (alta viabilidad, alto valor)
   - Entrega predicciones de flights/passengers diarios con ≤2% error
   - Sistema auto-ajustable

2. **Desarrolla Consumption Prediction Prototype**
   - Demuestra concepto de optimización de cantidades
   - Identifica features más importantes
   - Calcula ROI potencial de reducción de waste

3. **Crea Expiration Management Dashboard**
   - Sistema FIFO standalone
   - Alertas automáticas
   - Fácil de implementar, valor inmediato

4. **Analiza Drawer Configurations**
   - Insights descriptivos para estandarización
   - Sin capacidad predictiva, pero útil para benchmarking

### Mediano Plazo (solicitar datos adicionales):

5. **Solicita a GateGroup**:
   - ✅ Más fechas de Consumption (mínimo 12 meses)
   - ✅ Cabin class distribution por vuelo
   - ✅ Duración de vuelo en horas
   - ✅ Unificación de Product_IDs entre datasets
   - ✅ Timestamps de armado de carritos
   - ✅ Matriz de contratos por aerolínea

6. **Con datos adicionales**:
   - Implementa modelo integrado (4 dimensiones)
   - Optimización de productividad
   - Asistente de reglas de contrato

---

## ✅ CONCLUSIÓN

**Con los datasets actuales PUEDES implementar**:
- ✅ Time Series Forecasting (alta calidad)
- ✅ Consumption Prediction (prototipo, no producción)
- ✅ Expiration Management (standalone)
- ✅ Configuration Analysis (descriptivo)

**NO PUEDES implementar (datos insuficientes)**:
- ❌ Solución integrada de 4 dimensiones
- ❌ Productivity optimization (sin ground truth)
- ❌ Contract rules assistant (sin datos de contratos)
- ❌ Reducción de tiempo de armado (sin timestamps)

**El mayor gap**: Los datasets están **desconectados** - Product_IDs diferentes, sin vinculación entre vuelos-inventory-productivity.

**Recomendación estratégica**:
1. Entregar MVPs de alta calidad con datos actuales (Time Series + Consumption Prototype + Expiration)
2. Demostrar valor y ROI potencial
3. Justificar solicitud de datos adicionales para fases posteriores
4. Diseñar arquitectura extensible para integración futura
