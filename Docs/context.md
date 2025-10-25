# 🍽️ Sistema de Predicción de Cantidades para Catering Aéreo
**Contexto LLM-Friendly: 4 Documentos PDF Integrados**

---

## 📋 DOCUMENTO 1: PICK & PACK PROCESS OVERVIEW

**Propósito**: Flujo completo de selección y empaque: orden → picking → packing → QC → entrega.

### Etapas del Proceso
1. Creación de orden/manifesto (vuelo, menú, cantidades, comidas especiales)
2. Inventario & reabastecimiento (recepción, almacenamiento, gestión de SKUs)
3. Picking (selección según orden, batching)
4. Packing/Kitting (ensamble de bandejas/carritos, etiquetado)
5. Control de calidad (conteos, temperatura, verificaciones)
6. Staging & transporte (rampa, carga)
7. Retornos & disposición (sobrantes, spoilage)

### Datos Disponibles para el Modelo
- **Órdenes de vuelo**: Cantidades, tipos de comida, horarios de servicio
- **Conteos**: Pasajeros totales, desglose por clase (economía/ejecutiva/primera)
- **Comidas especiales**: Vegetariana, religiosa, médica (conteos separados)
- **Horarios**: Cutoffs de orden, lead times de pick/pack
- **Restricciones**: Tamaño de bandejas/carritos, lotes mínimos/máximos
- **KPIs**: Precisión de orden, cumplimiento de horarios, tasas de desperdicio

### Features (Características)
- `flight_id`, `route`, `departure_time`, `flight_duration`
- `day_of_week`, `is_holiday`, `season`
- `booked_passengers`, `booked_passengers_by_class`
- `special_meal_counts_by_type`
- `available_skus`, `packaging_unit_size`
- `recent_waste_rate`, `historical_accuracy_rate`

### Reglas de Negocio (Post-processing)
- Redondear a tamaño de lote/bandeja más próximo (ej: si tamaño=50 y predicción=145 → 150)
- Sobrecarga mínima garantizada (ej: +10%)
- Garantía de comidas especiales: preparación 100-105% de conteos
- No permitir cambios después del cutoff de orden

### Datos de Entrenamiento/Validación
- Pick & pack confirmations (qué se preparó realmente)
- Returns/waste logs (cantidad, razón: expiración, QC, spoilage, no-consumo)
- Meal served counts (logs de cabina cuando sea posible)
- Temperature & safety check logs

---

## 🗓️ DOCUMENTO 2: EXPIRATION DATE MANAGEMENT

**Propósito**: Gestión de shelf-life, fechas de vencimiento, rotación FIFO y minimización de desperdicio por expiración.

### Conceptos Clave
- **Shelf-life**: Chilled (~3-5 días), Frozen (~30-90 días), Ambient (variable)
- **Rotación FIFO**: Items más viejos primero para reducir expiración
- **Cold-chain**: Zonas de temperatura específicas, impacto en viabilidad de producto
- **Waste tracking**: Registros separados por razón (expiración, spoilage, QC, returns)

### Impacto en Predicción
- **Inventario usable**: No todo el inventory disponible se puede usar (filtrar por días a expiración)
- **Production deadline**: `departure_time - shelf_life` = límite máximo para preparar
- **Expiry-driven waste**: Tasas históricas de desperdicio por expiración deben separarse de otras causas
- **Storage constraints**: Volumen total preparado debe caber en almacenamiento frío

### Features para el Modelo
- `available_inventory_by_sku` (filtrado por fecha de expiración)
- `sku_shelf_life_days`
- `storage_temperature_zone`
- `waste_rate_due_to_expiry_by_sku`
- `supplier_id`, `season` (variabilidad de expiración)
- `lead_time_hours` (presión por cambios de último momento)
- `days_to_expiry_for_available_inventory`

### Reglas Operacionales
- **Expiry-Safe Overage**: +X% adicional como buffer contra expiración (ej: +5%)
- **FIFO Priority**: Picking preferencial de items cercanos a expiración
- **Last-Minute Cutoff**: `No meal prep after (departure_time - max_shelf_life)`
- **Cold-Chain Compliance**: Total preparado debe caber en espacio refrigerado para ventana de shelf-life

### Datos a Integrar
- Fecha de recepción y expiración por lote/SKU
- Waste logs clasificados por razón (expiración, spoilage, QC, customer return)
- Expiry rates históricas por SKU, proveedor, zona de almacenamiento, estación
- Shelf-life & storage zone mapping
- Pick logs (para verificar adherencia FIFO)
- Temperature monitoring logs

---

## 📊 DOCUMENTO 3: CONSUMPTION PREDICTION

**Propósito**: Predicción de consumo óptimo de comida por vuelo balanceando calidad vs. eficiencia operacional.

### Conceptos Fundamentales
- **Consumo real vs. preparado**: No todo lo preparado se consume (leftovers, no-takes, spoilage)
- **Variabilidad**: Tasas de consumo varían por ruta, horario, estación, clase de cabina
- **No-show rates**: Pasajeros reservados ≠ pasajeros abordados
- **No-take rates**: Pasajeros abordados ≠ pasajeros que consumen comida

### Factores por Pasajero
- Total booked vs. actual boarding (no-show rates por ruta/estación)
- Desglose por clase de cabina (consumo diferente: economía vs. ejecutiva vs. primera)
- Comidas especiales garantizadas vs. probabilísticas (variación por tipo)
- Comidas de crew (separadas de pasajeros)

### Características del Vuelo
- Ruta, duración, horario de salida (short-haul vs. long-haul)
- Horario del día (breakfast, lunch, dinner, red-eye)
- Día de semana, vacaciones, estación (peak vs. off-peak)
- Eventos especiales que afecten demanda

### Features para el Modelo
**Atributos de vuelo**:
- `flight_id`, `route`, `scheduled_departure_time`, `flight_duration`
- `day_of_week`, `is_holiday`, `season`, `time_of_day`
- `aircraft_type`

**Datos de pasajeros**:
- `total_booked_passengers`
- `booked_passengers_by_class` (economy/business/first)
- `special_meal_counts_by_type` (vegetarian, vegan, kosher, halal, medical, etc.)
- `no_show_rate_historical`
- `crew_meal_count`

**Patrones históricos**:
- `average_consumption_rate` (% de pasajeros que consumen)
- `consumption_rate_by_cabin_class` (distintos por clase)
- `consumption_rate_by_meal_type` (breakfast/lunch/dinner)
- `std_deviation_in_consumption` (volatilidad)

**Restricciones operacionales**:
- `available_inventory_by_sku`
- `packaging_unit_size` (meals per tray, trays per cart)
- `preparation_lead_time_hours`
- `shelf_life_days`

**Políticas de negocio**:
- `overage_percentage_policy` (ej: +10%)
- `minimum_meal_quantity` por clase
- `special_meal_guarantee_policy` (ej: 100% o 105%)
- `cost_of_shortage` vs. `cost_of_overage`

### Targets (Qué Predecir)
- `total_meals_to_prepare` (objetivo principal)
- `meals_by_cabin_class` (economía, ejecutiva, primera)
- `meals_by_meal_type` (breakfast, lunch, dinner, snacks)
- `meals_by_special_diet`
- `recommended_overage_count` o `percentage`

### Consideraciones de Exactitud
- **Multi-stage attrition**: Booked → Boarded → Consuming (cada etapa reduce cantidad)
- **Comidas especiales**: Generalmente garantizadas pero pueden cancelarse last-minute (tasa de no-consumo baja)
- **Waste calibration**: Historical logs ayudan a calibrar tasa de consumo "realizada"
- **Lead-time pressure**: Vuelos con lead times cortos tienen menos flexibilidad (recomendaciones conservadoras)
- **Route-time-season interactions**: Mismo vuelo en diferente día/estación tiene perfiles distintos

### Reglas de Negocio (Post-processing)
1. **Redondeo a lotes**: Redondear a tamaño de tray/case más próximo
2. **Sobrecarga mínima**: +X% o +Y comidas después de predicción base
3. **Garantía de especiales**: 100-105% de conteos de comidas especiales
4. **Cold-chain compliance**: No preparar más de `max_shelf_life` horas antes de salida
5. **Cost-optimal rule**: Si shortage > overage, bias a predicciones más altas (seguro); si overage > shortage, bias a predicciones bajas (eficiente)

### Datos de Entrenamiento
- `flight_id`, `date`, `booked_passengers`, `boarded_passengers`, `meals_prepared`, `meals_served`, `meals_returned`
- Desglose por clase de cabina y tipo de comida
- Waste logs: cantidad, razón (expiración, spoilage, QC, no consumo)
- Special meal bookings: tipo, booked, cancelled
- Availability del inventory en el momento de la orden
- External signals: weather, disruptions, events

---

## ⚙️ DOCUMENTO 4: PRODUCTIVITY ESTIMATION

**Propósito**: Metodologías de estimación de recursos basadas en parámetros operacionales.

### Conceptos Aplicables
- **Problem structure**: Múltiples variables contribuyen a estimaciones finales
- **Data-driven approach**: Usar métricas medibles y patrones históricos
- **Historical patterns**: Base para crear predictores confiables
- **Model development principles**: Entrenar iterativamente para mejorar exactitud

### Aplicación a Predicción de Cantidades
- Usar datos históricos de vuelo y consumo
- Integrar múltiples parámetros de entrada (detalles de vuelo, demográficas)
- Entrenar modelos para capturar relaciones complejas
- Validar predicciones contra outcomes reales

### Variables Clave
- Passenger count, flight duration, route type (drivers principales)
- Meal preferences, special requests (variabilidad de consumo)
- Seasonal factors, peak vs. off-peak (cyclical patterns)
- Operational constraints (inventory, shelf-life, lead times)

---

## 🎯 TARGETS Y FEATURES CONSOLIDADOS

### Features (Entrada del Modelo)

| Categoría | Variables |
|-----------|-----------|
| **Flight** | flight_id, route, departure_time, duration, day_of_week, hour_of_day, is_holiday, season, aircraft_type |
| **Passengers** | booked_passengers, boarded_passengers_historical_rate, cabin_class_distribution, crew_count |
| **Special Meals** | vegetarian_count, vegan_count, kosher_count, halal_count, medical_count, religious_count |
| **Historical** | avg_consumption_rate, consumption_rate_by_class, consumption_rate_by_meal_type, consumption_std_dev |
| **Inventory** | available_inventory_by_sku, days_to_expiry_by_sku, sku_shelf_life_days |
| **Operational** | packaging_unit_size, preparation_lead_time_hours, lead_time_hours_before_departure, recent_waste_rate |
| **Policy** | overage_percentage_policy, minimum_meal_policy, shortage_cost, overage_cost |

### Targets (Salida del Modelo)

| Target | Descripción |
|--------|------------|
| `total_meals_to_prepare` | Cantidad total de comidas a preparar (objetivo principal) |
| `meals_by_cabin_class` | Desglose por economía, ejecutiva, primera |
| `meals_by_meal_type` | Desglose por breakfast, lunch, dinner, snacks |
| `meals_by_special_diet` | Desglose por tipo de comida especial |
| `recommended_overage_percentage` | % de sobrecarga recomendada para la predicción |

---

## 📈 ENFOQUES DE MODELADO SUGERIDOS

### Tipo 1: Demand Forecasting + Features
- **Base**: Historical average para vuelos similares (ruta, horario, día)
- **Enhanced**: Agregar features de passenger count, mix de cabina, especiales, estación
- **Methods**: Exponential smoothing, ARIMA, Prophet, Hierarchical time-series

### Tipo 2: Gradient-Boosted Trees
- **Ventajas**: Capturan no-linealities (ej: consumo varía por ruta × estación × horario)
- **Models**: XGBoost, LightGBM con feature engineering
- **Output**: Fast, interpretable, operacionalmente viable

### Tipo 3: Probabilistic / Quantile Regression
- **Output**: Media + intervalos de confianza (50th, 90th percentiles)
- **Uso**: Upper quantile (90th) como cantidad recomendada para balancear riesgo de shortage vs. waste

### Tipo 4: Multi-Output Hierarchical
- **Output**: Total + desglose por clase/tipo/dieta
- **Constraint**: Sum(segments) = Total

---

## 📊 MÉTRICAS DE EVALUACIÓN

### Accuracy Metrics
- MAE (Mean Absolute Error) en conteos de comidas
- MAPE (Mean Absolute Percentage Error) en % sobre/bajo demanda real
- RMSE o quantile loss para modelos probabilísticos

### Business Metrics
- `Cost = (shortage_rate × shortage_cost_per_meal) + (overage_rate × overage_cost_per_meal)`
- Waste rate: % de comidas preparadas no servidas
- On-time fulfillment: % de vuelos que cumplieron deadline

### Validation
- Backtest con vuelos históricos: predecir → aplicar reglas → comparar vs. actual
- Evaluar por combinaciones route-time-season
- A/B test: predicción del modelo vs. planificación manual actual

---

## 🔗 INTEGRACIÓN DE LOS 4 DOCUMENTOS

```
FLOW GENERAL:
  
  Bookings (Consumo Esperado)
         ↓
    [CONSUMPTION PREDICTION]
    ↓ (Cantidad Base)
         ↓
  Inventory & Expiry (Restricciones)
         ↓
    [EXPIRATION MANAGEMENT]
    ↓ (Inventario Usable, Shelf-life Constraints)
         ↓
  Rounding & Operations (Reglas)
         ↓
    [PICK & PACK PROCESS]
    ↓ (Validar factibilidad operacional)
         ↓
  Resource Allocation (Productividad)
         ↓
    [PRODUCTIVITY ESTIMATION]
    ↓ (Confirmar viabilidad de recursos)
         ↓
  Final Order → Picking → Packing → QC → Delivery
```

### Relaciones Clave
1. **CONSUMPTION PREDICTION** genera demanda base
2. **EXPIRATION MANAGEMENT** filtra inventario usable y define deadlines
3. **PICK & PACK PROCESS** valida que predicción sea operacionalmente factible
4. **PRODUCTIVITY ESTIMATION** asegura que recursos estén disponibles

---

## 💾 DATOS CRÍTICOS A CAPTURAR

### De Sistemas Existentes
- **Booking System**: Manifiestos con cambios timestamped, conteos finales por clase
- **Inventory System**: Availability en tiempo real, expiry dates, ubicaciones de almacenamiento
- **Galley/Service Logs**: Comidas servidas reales (best label para entrenar)
- **Pick & Pack Logs**: Qué se preparó realmente vs. predicción
- **Waste Logs**: Cantidad, razón detallada (expiración, spoilage, QC, no-consumo)
- **QC Logs**: Rechazos, razones, impacto en cantidad servida
- **Temperature Monitoring**: Registros de cold-chain

### Mapping Necesario
- SKU ID ↔ Meal type, Cabin class, Shelf-life, Storage zone, Packaging unit
- Flight ↔ Route, Typical passenger mix, Historical consumption
- Route ↔ Typical meal types, Seasonal variations

### External Signals
- Holiday calendar
- Events calendar (conferences, sports, holidays)
- Weather alerts
- Disruption alerts

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA

1. **Fase 1**: Recolectar y limpiar datos históricos de los 4 documentos
2. **Fase 2**: Feature engineering (variables derivadas de datos crudos)
3. **Fase 3**: Entrenar modelo demand forecasting base (XGBoost con features)
4. **Fase 4**: Agregar probabilistic output para quantiles
5. **Fase 5**: Implementar post-processing rules (redondeo, overage, especiales)
6. **Fase 6**: Validar contra operational constraints (expiry, inventory, capacity)
7. **Fase 7**: A/B test vs. planeamiento actual
8. **Fase 8**: Monitor & iterate (reentrenar con nuevos datos)

---

## 📁 DATASETS DISPONIBLES

### Dataset 1: Time Series Consumption & Estimation (Gategroup)

**Archivo**: `Hackatlon Consumption and Estimation - Gategroup Dataset 1 de 2.xlsx`

**Objetivo**: Crear modelo que alcance ≤2% de error en predicción de series temporales. Plant 1 debe predecir flights y passengers; Plant 2 solo flights. El sistema debe auto-ajustarse.

#### Plant 1 (845 registros)
**Periodo**: 2023-01-02 a 2025-04-26 (845 días)

| Columna | Tipo | Descripción | Rango/Valores |
|---------|------|-------------|---------------|
| `day` | int64 | Fecha en formato YYYYMMDD | 20230102 - 20250426 |
| `flights` | int64 | Número de vuelos procesados por día | 140 valores únicos |
| `passengers` | int64 | Total de pasajeros por día | 833 valores únicos |
| `max capacity` | int64 | Capacidad máxima de pasajeros por día | 828 valores únicos |

**Sample**:
```
day      flights  passengers  max_capacity
20230102    352     94434        99351
20230103    356     92710        99616
20230104    358     88888        99437
```

**Casos de uso**:
- Forecasting de demanda diaria (flights + passengers)
- Detección de patrones estacionales/semanales
- Estimación de utilización (passengers / max_capacity)
- Predicción de capacidad requerida

#### Plant 2 (973 registros)
**Periodo**: 2023-01-02 a 2025-08-29 (973 días)

| Columna | Tipo | Descripción | Rango/Valores |
|---------|------|-------------|---------------|
| `day` | datetime64 | Fecha | 2023-01-02 a 2025-08-29 |
| `flights` | int64 | Número de vuelos por día | 23 valores únicos (rango menor que Plant 1) |

**Sample**:
```
day         flights
2023-01-02     19
2023-01-03     23
2023-01-04     20
```

**Casos de uso**:
- Forecasting de vuelos diarios (más simple que Plant 1)
- Detección de patrones de operación
- Comparación de volumen operacional entre plantas

---

### Dataset 2: Expiration Date Management (150 registros)

**Archivo**: `[HackMTY2025]_ExpirationDateManagement_Dataset_v1.xlsx`

**Propósito**: Gestión de inventario con fechas de expiración y lotes para minimizar desperdicio por vencimiento.

| Columna | Tipo | Descripción | Valores únicos | Notas |
|---------|------|-------------|----------------|-------|
| `Product_ID` | object | ID del producto | 10 | COF006, CHS010, SNK001, etc. |
| `Product_Name` | object | Nombre del producto | 10 | Instant Coffee Stick, Cheese Portion Pack, Snack Box Economy, etc. |
| `Weight_or_Volume` | object | Peso/volumen del producto | 6 | 200ml, 150g, 100g, 50g, etc. |
| `LOT_Number` | object | Número de lote | 126 | LOT-E19, LOT-E99, LOT-A68, etc. |
| `Expiry_Date` | object | Fecha de vencimiento | 78 | Formato: YYYY-MM-DD |
| `Quantity` | int64 | Cantidad en inventario | 131 valores únicos | Rango variable por producto |

**Sample**:
```
Product_ID  Product_Name            Weight  LOT_Number  Expiry_Date  Quantity
COF006      Instant Coffee Stick    200ml   LOT-E19     2025-12-10   231
CHS010      Cheese Portion Pack     150g    LOT-E99     2025-10-29   484
SNK001      Snack Box Economy       150g    LOT-A68     2025-12-05   357
```

**Casos de uso**:
- Cálculo de días hasta expiración (`days_to_expiry`)
- Priorización FIFO para picking
- Predicción de desperdicio por expiración
- Alertas de inventario cercano a vencer
- Cálculo de inventario usable para ventana de tiempo específica
- Análisis de shelf-life por categoría de producto

**Features derivadas sugeridas**:
- `days_to_expiry = expiry_date - today`
- `shelf_life_category`: Chilled (<7 days), Medium (7-30 days), Long (>30 days)
- `expiry_risk_level`: Critical (<3 days), Warning (3-7 days), Safe (>7 days)
- `lot_age`: Antigüedad del lote basada en patrón de número de lote

---

### Dataset 3: Consumption Prediction (792 registros)

**Archivo**: `[HackMTY2025]_ConsumptionPrediction_Dataset_v1.xlsx`

**Propósito**: Predicción de consumo real vs. estándar, optimización de cantidades preparadas, reducción de waste.

| Columna | Tipo | Descripción | Valores únicos | % Null |
|---------|------|-------------|----------------|--------|
| `Flight_ID` | object | Identificador de vuelo | 144 | 0% |
| `Origin` | object | Aeropuerto de origen | 6 (DOH, etc.) | 0% |
| `Date` | object | Fecha del vuelo | 12 | 0% |
| `Flight_Type` | object | Tipo de vuelo | 3 (medium-haul, short-haul, long-haul) | 0% |
| `Service_Type` | object | Tipo de servicio | 2 (Retail, Pick & Pack) | 0% |
| `Passenger_Count` | int64 | Conteo de pasajeros | 96 valores únicos | 0% |
| `Product_ID` | object | ID del producto | 10 | 0% |
| `Product_Name` | object | Nombre del producto | 10 | 0% |
| `Standard_Specification_Qty` | int64 | Cantidad estándar preparada | 223 valores únicos | 0% |
| `Quantity_Returned` | int64 | Cantidad devuelta (no consumida) | 103 valores únicos | 0% |
| `Quantity_Consumed` | int64 | Cantidad consumida real | 175 valores únicos | 0% |
| `Unit_Cost` | float64 | Costo unitario | 10 valores únicos | 0% |
| `Crew_Feedback` | object | Retroalimentación de tripulación | 3 (69 registros con feedback, 91.3% null) | 91.3% |

**Sample**:
```
Flight_ID  Origin  Date        Flight_Type  Service_Type  Passenger_Count  Product_ID  Product_Name           Std_Qty  Returned  Consumed  Unit_Cost  Crew_Feedback
AM109      DOH     2025-09-26  medium-haul  Retail        272             BRD001      Bread Roll Pack        62       7         55        0.35       NaN
AM109      DOH     2025-09-26  medium-haul  Retail        272             CRK075      Butter Cookies 75g     74       14        60        0.75       NaN
LX110      DOH     2025-09-26  medium-haul  Pick & Pack   272             CRK075      Butter Cookies 75g     131      36        95        0.75       drawer incomplete
```

**Valores observados**:
- **Origins**: 6 aeropuertos diferentes
- **Flight_Type**: short-haul, medium-haul, long-haul
- **Service_Type**: Retail vs. Pick & Pack (afecta cantidades y patrones de consumo)
- **Crew_Feedback**: "drawer incomplete" y otros mensajes (campo mayormente vacío)

**Casos de uso**:
- **Predicción de consumo**: `Quantity_Consumed` basado en `Flight_Type`, `Service_Type`, `Passenger_Count`, `Product_ID`
- **Optimización de cantidades**: Reducir `Standard_Specification_Qty` sin afectar servicio
- **Cálculo de waste rate**: `(Quantity_Returned / Standard_Specification_Qty) * 100`
- **Costo de desperdicio**: `Quantity_Returned * Unit_Cost`
- **Tasa de consumo**: `(Quantity_Consumed / Passenger_Count) * 100` (consumo per cápita)
- **Análisis por tipo de servicio**: Comparar Retail vs. Pick & Pack

**Features derivadas sugeridas**:
- `waste_rate = (returned / standard_qty) * 100`
- `consumption_rate = (consumed / passenger_count) * 100`
- `waste_cost = returned * unit_cost`
- `overage_qty = standard_qty - consumed`
- `overage_percentage = (overage_qty / consumed) * 100`
- `consumption_per_passenger = consumed / passenger_count`
- `specification_accuracy = (consumed / standard_qty) * 100`

**Target sugerido**: `Standard_Specification_Qty` (predecir cantidad óptima a preparar dado flight_type, service_type, passenger_count, product_id)

**Validación**: Evaluar predicción contra `Quantity_Consumed` real y calcular waste vs. shortage rates.

---

### Dataset 4: Productivity Estimation (100 registros)

**Archivo**: `[HackMTY2025]_ProductivityEstimation_Dataset_v1.xlsx`

**Propósito**: Estimación de recursos/productividad basada en configuración de drawers (cajones/gavetas) para diferentes tipos de vuelo.

| Columna | Tipo | Descripción | Valores únicos | Notas |
|---------|------|-------------|----------------|-------|
| `Drawer_ID` | object | ID único del drawer | 100 (todos únicos) | DRW_001, DRW_002, etc. |
| `Flight_Type` | object | Tipo de vuelo | 2 (Business, Economy) | Clase de cabina |
| `Drawer_Category` | object | Categoría del drawer | 4 (Beverage, Breakfast, Snack, Meal) | Tipo de servicio |
| `Total_Items` | int64 | Total de items en el drawer | 33 valores únicos | Rango de items por drawer |
| `Unique_Item_Types` | int64 | Tipos únicos de items | 12 valores únicos | Diversidad de productos |
| `Item_List` | object | Lista de items (SKUs) | 100 (todos únicos) | Formato: CUTL01, CUP01, SNK01, etc. |

**Sample**:
```
Drawer_ID  Flight_Type  Drawer_Category  Total_Items  Unique_Item_Types  Item_List
DRW_001    Business     Beverage         12           4                  CUTL01, CUTL02, CUP01, SNK01
DRW_002    Economy      Breakfast        11           5                  CUP01, BUT02, SNK02, CUTL02, SNK01
DRW_003    Business     Snack            15           7                  SNK02, BUT02, DRK05, SNK03, STR01, JAM02, CUTL01
```

**Valores observados**:
- **Flight_Type**: Business, Economy (no incluye First Class en este dataset)
- **Drawer_Category**: Beverage, Breakfast, Snack, Meal
- **Item codes**: CUTL (cutlery), CUP (cups), SNK (snacks), BUT (butter), DRK (drinks), STR (stirrers), JAM (jam), etc.

**Casos de uso**:
- **Estimación de tiempo de preparación**: Basado en `Total_Items` y `Unique_Item_Types`
- **Asignación de recursos**: Número de empleados/tiempo requerido por drawer category
- **Complejidad de preparación**: Drawers con más `Unique_Item_Types` son más complejos
- **Estandarización de configuraciones**: Patrones comunes por `Flight_Type` × `Drawer_Category`
- **Productividad por categoría**: Items/hora por tipo de drawer

**Features derivadas sugeridas**:
- `complexity_score = (unique_item_types / total_items) * 100` (diversidad/complejidad)
- `avg_items_per_type = total_items / unique_item_types` (repetición promedio)
- `item_count_per_category`: Distribución de items por SKU prefix (CUTL, CUP, SNK, etc.)
- `preparation_time_estimate`: Basado en total_items y unique_item_types

**Target sugerido**: Tiempo de preparación o número de empleados requeridos (si se tiene ground truth)

**Análisis adicional**: Parsear `Item_List` para extraer SKU counts y crear features más granulares.

---

## 🔗 INTEGRACIÓN DE DATASETS CON DOCUMENTOS CONCEPTUALES

### Mapeo de Datasets a Dimensiones del Problema

| Dataset | Documento relacionado | Uso en el flujo |
|---------|----------------------|-----------------|
| **Time Series (Plant 1 & 2)** | Consumption Prediction | Input histórico para forecasting de demanda base |
| **Expiration Date Management** | Expiration Date Management | Filtrado de inventario usable, cálculo de shelf-life constraints |
| **Consumption Prediction** | Consumption Prediction + Pick & Pack | Training data para modelo de predicción de cantidades + validación de waste rates |
| **Productivity Estimation** | Productivity Estimation + Pick & Pack | Validación de factibilidad operacional (recursos disponibles) |

### Flujo Integrado con Datasets Reales

```
[Plant 1 & 2 Time Series]
         ↓ (Historical patterns)
    [CONSUMPTION PREDICTION MODEL]
    ← Entrenado con [Consumption Prediction Dataset]
         ↓ (Base Quantity Prediction)

[Expiration Dataset]
         ↓ (Filtrar inventario usable)
    [EXPIRATION CONSTRAINTS]
         ↓ (Available inventory + days to expiry)

    [FINAL QUANTITY CALCULATION]
    - Redondeo a packaging units
    - Aplicar overage policies
    - Validar contra shelf-life
         ↓

[Productivity Dataset]
         ↓ (Validar factibilidad)
    [RESOURCE ALLOCATION CHECK]
         ↓
    Final Order → Pick → Pack → QC → Delivery
```

---

## 📊 FEATURES UNIFICADAS DE TODOS LOS DATASETS

### Features Temporales
- `day`, `date`: Timestamp del evento
- `day_of_week`: Derivado de date
- `is_weekend`: Boolean
- `is_holiday`: Requiere calendario externo
- `season`: Derivado de month
- `days_to_expiry`: Calculado de expiry_date

### Features de Vuelo/Demanda
- `flight_id`, `flights`: Identificador y conteos
- `origin`: Aeropuerto
- `flight_type`: short/medium/long-haul, o Business/Economy
- `passenger_count`, `passengers`, `max_capacity`: Demanda de pasajeros
- `utilization_rate = passengers / max_capacity`

### Features de Producto
- `product_id`, `product_name`: Identificación
- `weight_or_volume`: Especificación física
- `unit_cost`: Costo unitario
- `lot_number`: Trazabilidad

### Features de Consumo/Inventario
- `standard_specification_qty`: Cantidad estándar preparada
- `quantity_consumed`: Consumo real
- `quantity_returned`: Desperdicio
- `quantity`: Inventario disponible
- `waste_rate`, `consumption_rate`: Derivados

### Features de Operaciones
- `service_type`: Retail vs. Pick & Pack
- `drawer_category`: Beverage, Breakfast, Snack, Meal
- `total_items`, `unique_item_types`: Complejidad de preparación
- `crew_feedback`: Retroalimentación cualitativa

### Targets Principales
1. **Time series forecasting**: `flights`, `passengers` (Plant 1 & 2)
2. **Consumption prediction**: `quantity_consumed` o `standard_specification_qty` optimizado
3. **Waste minimization**: Minimizar `quantity_returned` mientras se garantiza disponibilidad
4. **Productivity estimation**: Tiempo/recursos requeridos (si se tiene ground truth)

---

## 🎤 INFORMACIÓN OPERACIONAL DE ENTREVISTAS CON GATEGROUP

**Fuentes**: Transcripts de entrevistas con funcionarios de GateGroup (ResumenTranscriptCitado.md, PreguntasGateGroup.md)

### Alcance del Reto

**Productos en scope**:
- Snacks y bebidas **NO preparadas** (productos empaquetados listos para servir)
- NO incluye comida caliente ni preparaciones (make and pack) - eso es otro proceso
- Productos reales disponibles para pruebas y medición de tiempos

**Objetivo principal**:
> "Me da igual el algoritmo, me da igual la solución que me des, siempre y cuando cumpla con el propósito de mejorar el proceso." (19:06)

**Meta de precisión**:
- Error máximo ≤2% en predicciones de series temporales
- Actualmente no han tenido faltantes porque aerolíneas mandan con buffer, pero se busca optimizar

**Objetivo de eficiencia**:
> "Si me reduces 3 segundos por bandeja por vuelo, al final del año puedes estar hablando de días." (18:30)
- Reducir tiempo de armado sin afectar calidad
- Vuelo completo (~7 carritos): **~4 horas** de armado actualmente

---

### Proceso Operacional Real

#### 1. Ciclo de Vida de un Vuelo

**Pre-vuelo (armado)**:
1. Cliente (aerolínea) hace pedido basado en manifiesto de pasajeros
2. Proveedor suministra productos (ej: Aeromexico vía Mester)
3. GateGroup arma carritos en planta (10 minutos del aeropuerto)
4. Productos se organizan en trolleys/carritos (largos y medios)
5. Tiempo de preparación: **~4 horas** para vuelo completo
6. Transporte y carga al avión: **~3 horas** antes de salida

**Post-vuelo (recepción y reuso)**:
1. Vuelo aterriza, carritos regresan a planta
2. **Conteo manual** de inventario restante
3. Check de caducidades por lote
4. Match con venta a bordo (si aplica) y distribución realizada
5. **Productos cerrados/buenos** → se reutilizan en siguiente vuelo
6. **Productos abiertos/medios** → depende de contrato con aerolínea:
   - Algunas aerolíneas aceptan botellas a la mitad si suman el volumen requerido
   - Otras exigen solo botellas cerradas (botellas abiertas se desechan)
   - Ejemplos: vino tinto con corcho aunque no esté bebido → se desecha
7. Refill hasta alcanzar **mínimos establecidos** por SKU
8. Vuelo listo para siguiente ciclo

#### 2. Gestión de Inventarios

**Control de stock**:
- Cada producto tiene un **mínimo establecido** por carrito/vuelo
- Ejemplo: "Tengo que tener 3 Coca-Cola zero, 3 Coca-Cola normal, 2 Sprites..."
- Refill basado en: `cantidad_faltante = mínimo - cantidad_actual`
- Stock general basado en **históricos de consumo** e inventarios

**Sistema de lotes (FIFO)**:
> "Lo vamos poniendo por lotes, cuando se acabe el lote ponemos el siguiente." (07:20)
- No se mezclan lotes de fechas muy diferentes (máximo 2-3 lotes volando)
- Control de caducidad **por lote** (no producto a producto)
- Cada lote tiene fecha de caducidad uniforme
- Sugerencia del cliente: automatizar lectura de fechas con IA/OCR

**Caducidades**:
- Check **5-7 días antes** de expiración
- Productos próximos a vencer se desechan antes de ese límite
- Post-vuelo se revisan caducidades en el reconteo

**Tecnología actual**:
- **Tablets (iPad/Android)** con app desarrollada in-house (80% de casos)
- App conectada a **ERP desarrollado internamente**
- Almacenamiento en **la nube** (data centers propios)
- En algunos casos de venta a bordo: duplicación de registro en sistema de aerolínea + sistema propio (consume tiempo extra)

---

### Variables Clave de Negocio

**Drivers de consumo** (según experiencia operacional):
> "En su experiencia cuáles son las variables que impactan en el consumo... cantidad de personas y las horas de vuelo que tienen." (14:30)

1. **Cantidad de pasajeros**: Driver principal
2. **Horas de vuelo**:
   - Vuelos cortos (~2 horas): mayoría de vuelos
   - Vuelos largos: dobles servicios (4-12 carritos dependiendo de duración)
3. **Tipo de vuelo**: Determinado por contrato con aerolínea
4. **Históricos**: Datos de pasajeros históricos (de aerolíneas o empresas terceras como OAG)

**Fuentes de datos de pasajeros**:
> "Nos dan las aerolíneas o nos las dan empresas terceros como OAC, pero nos dan datos de cuántos pasajeros hubo en históricos." (09:49)
- Aerolíneas proveen manifiestos y datos históricos
- Empresas terceras (OAG, etc.)
- Histórico propio de GateGroup

---

### Configuración de Carritos (Trolleys)

**Tipos de carritos**:
- **Largos** (full size)
- **Medios** (half size - mitad de un largo)
- Total para un vuelo típico: **~7 carritos** (pueden ser ~12 en vuelos grandes)

**Capacidad y organización**:
- Productos pequeños (latas, snacks): caben en bandejas múltiples
- Productos grandes (tetrabrix de jugo): ocupan más espacio, menos unidades por bandeja
- Configuración varía según tipo de producto (bebidas vs. snacks vs. suministros)

**Contenidos**:
- Bebidas (refrescos, agua, jugos)
- Snacks (galletas, botanas, chips)
- Suministros: cubrebocas, guantes, bolsas de basura
- Documentación del vuelo
- Cubiertos, vasos, servilletas

**Estaciones de armado**:
- Personas dedicadas a **líquidos**
- Personas dedicadas a **botanas y galletas**
- Personas dedicadas a **misceláneos**
- Aproximadamente **3 estaciones** de armado simultáneas

---

### Restricciones y Reglas por Contrato

**Variabilidad por aerolínea**:
> "Son un montón de variables que se tiene que saber de memoria el empacador y que lo suyo es que haya una ayuda." (16:50)

Cada contrato tiene **cláusulas específicas**:

1. **Botellas abiertas**:
   - Aerolínea A: Acepta medias botellas si suman volumen total (ej: 2 medias = 1 litro)
   - Aerolínea B: Solo acepta botellas cerradas nuevas, abiertas se desechan
   - Criterios de aceptación: si está >50% llena vs. <50%

2. **Productos abiertos**:
   - Algunos productos abiertos → desechar independientemente (ej: vino con corcho)
   - Refrescos/bebidas: depende del contrato

3. **Volúmenes mínimos**:
   - Contratos especifican volumen total requerido por tipo de bebida/producto
   - GateGroup debe cumplir sin importar cómo se distribuya (botellas completas vs. medias)

**Problema operacional**:
- Empacadores deben **memorizar** reglas de cada contrato/aerolínea
- Proceso de verificación toma **~30 segundos** actualmente
- Oportunidad: Reducir a **~10 segundos** con asistencia digital (vinculación automática vuelo → contrato → reglas)

---

### Desafíos de Productividad

**Factor humano**:
> "Por eso es que se aburren o se pueden distraer porque tú piensas que si estás haciendo ocho horas esto..." (12:25)

- Trabajo repetitivo de **8 horas** armando carritos
- Riesgo de distracción y error por monotonía
- Necesidad de mantener atención en múltiples variables

**KPIs existentes (confidenciales)**:
> "Tenemos ya ciertos KPIs para hacer eso. Esos no se los vamos a pasar." (13:00)
- Existen **promedios de tiempo** por paso del proceso (inicio a fin)
- Métrica interna: "puntos de historia" por vuelo
- Objetivo: "Hacer la misma historia con menos puntos" (reducir tiempo)

**Oportunidades de mejora**:
1. Reducir tiempo de armado por bandeja/carrito
2. Minimizar errores de empacado
3. Ayudar a verificar reglas de contrato más rápido
4. Optimizar decisiones de reuso de productos (botellas medias, etc.)
5. Automatizar chequeo de caducidades

---

### Predicción y Optimización de Compras

**Caso de uso: Venta a bordo**:
> "Me interesa saber cómo comprar mejor porque a lo mejor no tengo que comprar y poner siempre tres Coca-Colas, si ya sé que no se van a consumir." (09:13)

**Escenario**:
- Stock pertenece a GateGroup (no siempre es de la aerolínea)
- Optimizar compras basado en consumo real histórico
- Ejemplo: Si siempre sobran Coca-Colas normales y faltan Coca-Cola Zero:
  - Cambiar configuración de 3-2 a 2-4
  - Coordinar con cliente o ajustar plan propio
  - Evitar compras innecesarias hasta agotar stock

**Limitación actual**:
- En muchos casos, productos ya están pagados por aerolínea
- Enfoque en **tiempo/eficiencia** más que en reducción de desperdicio económico
- Pero en venta a bordo, optimización de compras sí impacta margen de GateGroup

---

### Contexto Técnico y de Implementación

**Preferencias de solución**:
1. **Foco en proceso, no en tecnología**:
   > "Céntrate más en mejorar el proceso independientemente del fondo." (20:18)

2. **Costo razonable**:
   - No se esperan inversiones millonarias por carrito
   - Pero costo no es el factor principal si hay mejora significativa

3. **Digitalización pragmática**:
   > "No todos los procesos los tendremos que digitalizar al 100, siempre y cuando seamos eficientes." (21:04)
   - Bienvenida combinación de soluciones tecnológicas + no tecnológicas
   - Flexibilidad para soluciones híbridas

4. **Implementación por GateGroup**:
   - Aerolínea NO está involucrada en implementación
   - GateGroup ejecuta la solución internamente
   - Aerolínea solo paga por el servicio

**Infraestructura existente**:
- App in-house ya desarrollada (tablets)
- ERP in-house
- Conectividad en tierra (NO hay conectividad arriba del avión durante vuelo)
- Almacenamiento en nube
- Posibilidad de integración con sistemas existentes

---

### Datos Disponibles para Modelado

**Datos históricos confirmados**:
1. **Manifiestos de pasajeros** por vuelo (de aerolíneas)
2. **Consumos históricos** (registrados en app/ERP propio)
3. **Inventarios pre y post vuelo** (conteos manuales)
4. **Venta a bordo** cuando aplique (match entre inventario y ventas)
5. **Datos de terceros**: OAG u otras empresas proveen históricos de pasajeros
6. **Históricos de merma/desperdicio** por producto y razón

**Granularidad**:
- Por vuelo (Flight_ID)
- Por SKU (producto específico)
- Por lote (fecha de caducidad)
- Por ruta (histórico por aeropuerto origen/destino)
- Por temporada/época del año

---

### Oportunidades de ML/IA Identificadas en Entrevistas

1. **Predicción de consumo optimizada**:
   - Basado en pasajeros + horas de vuelo + históricos
   - Reducir sobrecarga innecesaria
   - Objetivo: ≤2% error

2. **Automatización de lectura de caducidades**:
   > "Te puedes poner a hacer que una IA te ponga a revisar lata a lata todos los dígitos de la fecha de caducidad." (11:04)
   - OCR/Computer Vision para leer fechas en lotes
   - Evitar revisión manual lata por lata

3. **Asistencia inteligente para reglas de contrato**:
   - Vincular vuelo → contrato → cláusulas automáticamente
   - Mostrar al empacador qué productos se pueden reusar
   - Reducir tiempo de verificación de 30s a 10s

4. **Optimización de refill**:
   - Basado en consumo real histórico por ruta/vuelo
   - Ajustar mínimos dinámicamente

5. **Sincronización de sistemas**:
   - Evitar doble registro (sistema propio + sistema aerolínea)
   - Transferencia automática de datos entre sistemas

6. **Identificación/marcado de productos**:
   - Posibilidad de agregar marcas/tags a productos para mejor identificación
   - Computer vision para tracking de lotes

---

### Métricas de Éxito del Proyecto

**Cuantitativas**:
1. **Reducción de tiempo**: Segundos ahorrados por bandeja × bandejas por vuelo × vuelos por año = días ahorrados
2. **Precisión de predicción**: Error ≤2% en forecasting de consumo
3. **Reducción de errores**: Menos productos incorrectos o faltantes
4. **Optimización de compras**: Reducción de stock innecesario (cuando aplique)

**Cualitativas**:
1. **Mejora en proceso**: Simplificación, menos pasos manuales
2. **Reducción de carga cognitiva**: Menos reglas que memorizar
3. **Satisfacción del trabajador**: Menos monotonía/distracción
4. **Aplicabilidad**: Que la solución sea práctica de implementar

**Prioridad**:
> "Si me reduces 3 segundos por bandeja por vuelo, al final del año puedes estar hablando de días."
- **Tiempo es el KPI principal** (más que costo de desperdicio en este caso)
- Impacto acumulativo a lo largo del año es significativo

---

*Documento preparado para alimentar modelos de ML con contexto operacional integrado.*
