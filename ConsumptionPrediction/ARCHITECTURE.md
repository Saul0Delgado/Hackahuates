# Consumption Prediction Module - Architecture Plan

## 🎯 Objetivo

Predecir la cantidad óptima de productos a preparar por vuelo para:
- ✅ Reducir waste (11% → 7% = -36%)
- ✅ Evitar shortages (mantener >95% satisfacción)
- ✅ Optimizar fuel consumption (menos peso innecesario)
- ✅ Cumplir meta de ≤2% error (alcanzable con más datos)   

---

## 📊 Dataset Disponible

**Archivo**: `Docs/HackMTY2025_ChallengeDimensions/02_ConsumptionPrediction/[HackMTY2025]_ConsumptionPrediction_Dataset_v1_csvs/Sheet1.csv`

**Registros**: 792 rows × 13 columns

**Columnas**:
```
Flight_ID                   object   (144 únicos)
Origin                      object   (6 únicos: DOH, etc.)
Date                        object   (12 fechas: 2025-09-26 a 2025-10-07)
Flight_Type                 object   (3: short-haul, medium-haul, long-haul)
Service_Type                object   (2: Retail, Pick & Pack)
Passenger_Count             int64    (96 valores únicos)
Product_ID                  object   (10 productos)
Product_Name                object   (10 nombres)
Standard_Specification_Qty  int64    (cantidad preparada)
Quantity_Returned           int64    (no consumido = waste)
Quantity_Consumed           int64    (consumo real)
Unit_Cost                   float64  (10 costos únicos)
Crew_Feedback               object   (91.3% null, 3 valores cuando existe)
```

**Ejemplos de productos**:
- BRD001: Bread Roll Pack
- CRK075: Butter Cookies 75g
- DRK023: Sparkling Water 330ml
- DRK024: Still Water 500ml
- CHO050: Chocolate Bar 50g

---

## 🏗️ Arquitectura del Módulo

```
ConsumptionPrediction/
│
├── data/                           # Datos y artifacts
│   ├── raw/                        # Datos originales
│   │   └── consumption_dataset.csv
│   ├── processed/                  # Datos procesados
│   │   ├── train.csv
│   │   ├── test.csv
│   │   └── validation.csv
│   └── models/                     # Modelos entrenados
│       ├── xgboost_model.pkl
│       ├── random_forest_model.pkl
│       ├── ensemble_model.pkl
│       └── scaler.pkl
│
├── src/                            # Código fuente
│   ├── __init__.py
│   ├── data_loader.py              # Carga de datos
│   ├── feature_engineering.py     # Ingeniería de features
│   ├── models/                     # Modelos ML
│   │   ├── __init__.py
│   │   ├── xgboost_model.py
│   │   ├── random_forest_model.py
│   │   ├── ensemble_model.py
│   │   └── base_model.py
│   ├── training.py                 # Pipeline de entrenamiento
│   ├── prediction.py               # Pipeline de predicción
│   ├── evaluation.py               # Métricas y evaluación
│   └── utils.py                    # Utilidades
│
├── api/                            # API REST
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── schemas.py                  # Pydantic models
│   ├── endpoints.py                # Endpoints
│   └── dependencies.py             # Dependencias
│
├── notebooks/                      # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
│
├── tests/                          # Tests unitarios
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_feature_engineering.py
│   ├── test_models.py
│   └── test_api.py
│
├── scripts/                        # Scripts ejecutables
│   ├── train_model.py              # Entrenar modelos
│   ├── evaluate_model.py           # Evaluar modelos
│   └── predict.py                  # Hacer predicciones
│
├── config/                         # Configuración
│   ├── config.yaml                 # Config general
│   └── model_config.yaml           # Config de modelos
│
├── requirements.txt                # Dependencias Python
├── Dockerfile                      # Docker para deployment
├── docker-compose.yml              # Orquestación
├── README.md                       # Documentación
└── ARCHITECTURE.md                 # Este archivo
```

---

## 🔬 Pipeline de ML

### 1. Data Loading & Preprocessing

**Input**: CSV crudo del dataset
**Output**: DataFrame limpio y validado

**Pasos**:
```python
def load_and_preprocess():
    # 1. Cargar CSV
    df = pd.read_csv('data/raw/consumption_dataset.csv')

    # 2. Validación básica
    assert df.shape[0] == 792
    assert df.isnull().sum()['Flight_ID'] == 0

    # 3. Conversión de tipos
    df['Date'] = pd.to_datetime(df['Date'])

    # 4. Limpieza
    df['Crew_Feedback'] = df['Crew_Feedback'].fillna('none')

    # 5. Validación de integridad
    assert (df['Standard_Specification_Qty'] >=
            df['Quantity_Consumed'] + df['Quantity_Returned']).all()

    return df
```

---

### 2. Feature Engineering

**Features básicos** (ya disponibles):
- `Flight_Type`: categorical (short/medium/long-haul)
- `Service_Type`: categorical (Retail / Pick & Pack)
- `Passenger_Count`: numeric
- `Product_ID`: categorical (10 productos)
- `Origin`: categorical (6 orígenes)

**Features derivados** (a crear):

#### Temporales
```python
df['day_of_week'] = df['Date'].dt.dayofweek  # 0=Monday, 6=Sunday
df['is_weekend'] = df['day_of_week'].isin([5, 6])
df['month'] = df['Date'].dt.month
df['day_of_month'] = df['Date'].dt.day
```

#### Métricas de consumo
```python
df['waste_rate'] = df['Quantity_Returned'] / df['Standard_Specification_Qty']
df['consumption_rate'] = df['Quantity_Consumed'] / df['Standard_Specification_Qty']
df['consumption_per_passenger'] = df['Quantity_Consumed'] / df['Passenger_Count']
df['overage_qty'] = df['Standard_Specification_Qty'] - df['Quantity_Consumed']
df['overage_percentage'] = df['overage_qty'] / df['Quantity_Consumed']
```

#### Agregaciones históricas (por producto)
```python
# Por Product_ID
product_stats = df.groupby('Product_ID').agg({
    'consumption_rate': ['mean', 'std'],
    'waste_rate': ['mean', 'std'],
    'Quantity_Consumed': ['mean', 'std']
}).reset_index()

df = df.merge(product_stats, on='Product_ID', suffixes=('', '_product_avg'))
```

#### Agregaciones por Flight_Type
```python
# Por Flight_Type × Product_ID
flight_product_stats = df.groupby(['Flight_Type', 'Product_ID']).agg({
    'consumption_rate': 'mean',
    'Quantity_Consumed': 'mean'
}).reset_index()

df = df.merge(flight_product_stats, on=['Flight_Type', 'Product_ID'],
              suffixes=('', '_flight_product_avg'))
```

#### Agregaciones por Service_Type
```python
# Retail vs Pick & Pack tienen patrones muy diferentes
service_stats = df.groupby(['Service_Type', 'Product_ID']).agg({
    'waste_rate': 'mean',
    'consumption_per_passenger': 'mean'
}).reset_index()

df = df.merge(service_stats, on=['Service_Type', 'Product_ID'],
              suffixes=('', '_service_avg'))
```

#### Encoding de categóricas
```python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

# Label Encoding para tree-based models
le_product = LabelEncoder()
df['product_id_encoded'] = le_product.fit_transform(df['Product_ID'])

le_origin = LabelEncoder()
df['origin_encoded'] = le_origin.fit_transform(df['Origin'])

# One-Hot Encoding para Flight_Type y Service_Type
df = pd.get_dummies(df, columns=['Flight_Type', 'Service_Type'],
                    prefix=['flight', 'service'])
```

**Features finales** (30-40 features):
```
Originales:         5-7 features
Derivados simples:  5-10 features
Agregaciones:       15-20 features
Encoded:            5-8 features
TOTAL:             ~30-40 features
```

---

### 3. Train/Test Split

**Estrategia**: Time-based split (NO random)

```python
# Ordenar por fecha
df = df.sort_values('Date')

# Fechas disponibles: 2025-09-26 a 2025-10-07 (12 días)
# Split: 70% train, 15% validation, 15% test

train_cutoff = df['Date'].quantile(0.70)  # ~8 días
val_cutoff = df['Date'].quantile(0.85)    # ~2 días

train_df = df[df['Date'] <= train_cutoff]        # ~554 rows
val_df = df[(df['Date'] > train_cutoff) &
            (df['Date'] <= val_cutoff)]           # ~119 rows
test_df = df[df['Date'] > val_cutoff]             # ~119 rows
```

**Rationale**: Time-based split simula producción (predecir futuro basado en pasado)

---

### 4. Model Training

#### Modelo 1: XGBoost (Principal)

**Ventajas**:
- ✅ Excelente con datos tabulares
- ✅ Maneja missing values automáticamente
- ✅ Feature importance interpretable
- ✅ Rápido de entrenar e inferir

**Configuración**:
```python
from xgboost import XGBRegressor

xgb_model = XGBRegressor(
    n_estimators=500,           # Muchos árboles (early stopping evita overfit)
    max_depth=6,                # Profundidad moderada
    learning_rate=0.05,         # Learning rate bajo (más estable)
    subsample=0.8,              # 80% muestras por árbol
    colsample_bytree=0.8,       # 80% features por árbol
    gamma=1,                    # Mínima reducción de loss para split
    reg_alpha=0.1,              # L1 regularization
    reg_lambda=1,               # L2 regularization
    random_state=42,
    n_jobs=-1,                  # Usar todos los cores
    early_stopping_rounds=50    # Parar si no mejora en 50 rounds
)

# Entrenamiento
xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=100
)
```

**Target**: `Quantity_Consumed` (consumo real)

---

#### Modelo 2: Random Forest (Baseline robusto)

**Ventajas**:
- ✅ Robusto a outliers
- ✅ Menos propenso a overfit
- ✅ Funciona bien sin mucho tuning

**Configuración**:
```python
from sklearn.ensemble import RandomForestRegressor

rf_model = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)
```

---

#### Modelo 3: Ensemble (Weighted Average)

**Estrategia**: Combinar XGBoost + Random Forest

```python
class EnsembleModel:
    def __init__(self, xgb_model, rf_model, weights=[0.7, 0.3]):
        self.xgb_model = xgb_model
        self.rf_model = rf_model
        self.weights = weights

    def predict(self, X):
        xgb_pred = self.xgb_model.predict(X)
        rf_pred = self.rf_model.predict(X)

        ensemble_pred = (
            self.weights[0] * xgb_pred +
            self.weights[1] * rf_pred
        )

        return ensemble_pred
```

**Weights optimizados** basado en validation performance

---

### 5. Post-Processing & Business Rules

**Problema**: Predicciones pueden ser decimales o fuera de límites

**Solución**: Aplicar reglas de negocio

```python
def apply_business_rules(prediction, passenger_count, product_id):
    # 1. Redondear a entero
    quantity = int(np.round(prediction))

    # 2. Mínimo buffer de seguridad (5%)
    min_buffer = 1.05
    quantity = int(quantity * min_buffer)

    # 3. Mínimo absoluto por producto (no menos de 10% de pasajeros)
    min_qty = max(10, int(passenger_count * 0.1))
    quantity = max(quantity, min_qty)

    # 4. Máximo razonable (no más de 150% de pasajeros)
    max_qty = int(passenger_count * 1.5)
    quantity = min(quantity, max_qty)

    # 5. Redondear a packaging unit (ejemplo: cajas de 6)
    packaging_units = {
        'BRD001': 6,
        'CRK075': 12,
        'DRK023': 6,
        # ... otros productos
    }

    unit_size = packaging_units.get(product_id, 1)
    quantity = int(np.ceil(quantity / unit_size) * unit_size)

    return quantity
```

---

### 6. Evaluation Metrics

#### Métricas de precisión
```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)

    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
        'R2': r2
    }
```

#### Métricas de negocio
```python
def evaluate_business_impact(y_true, y_pred_optimized, standard_qty, unit_cost):
    # Waste reduction
    actual_waste = standard_qty - y_true
    predicted_waste = y_pred_optimized - y_true
    waste_reduction = (actual_waste - predicted_waste) / actual_waste * 100

    # Cost savings
    waste_cost_actual = actual_waste.sum() * unit_cost
    waste_cost_predicted = predicted_waste.sum() * unit_cost
    cost_savings = waste_cost_actual - waste_cost_predicted

    # Shortage risk
    shortage_actual = (y_true > standard_qty).sum() / len(y_true) * 100
    shortage_predicted = (y_true > y_pred_optimized).sum() / len(y_true) * 100

    return {
        'waste_reduction_%': waste_reduction,
        'cost_savings_$': cost_savings,
        'shortage_risk_actual_%': shortage_actual,
        'shortage_risk_predicted_%': shortage_predicted
    }
```

---

## 🚀 API REST (FastAPI)

### Endpoints

#### 1. Predicción simple
```python
POST /api/v1/predict

Request:
{
    "flight_type": "medium-haul",
    "service_type": "Pick & Pack",
    "passenger_count": 272,
    "product_id": "CRK075",
    "origin": "DOH",
    "date": "2025-10-26"
}

Response:
{
    "product_id": "CRK075",
    "product_name": "Butter Cookies 75g",
    "standard_qty": 74,
    "predicted_consumption": 63,
    "recommended_qty": 68,
    "confidence_interval_95%": [60, 71],
    "waste_reduction": "8.1%",
    "cost_savings_per_flight": 4.50,
    "model_confidence": 0.94
}
```

#### 2. Predicción batch (vuelo completo)
```python
POST /api/v1/predict/batch

Request:
{
    "flight_id": "AM109",
    "flight_type": "medium-haul",
    "service_type": "Retail",
    "passenger_count": 272,
    "origin": "DOH",
    "date": "2025-10-26",
    "products": ["BRD001", "CRK075", "DRK023", "DRK024"]
}

Response:
{
    "flight_id": "AM109",
    "total_items": 4,
    "predictions": [
        {
            "product_id": "BRD001",
            "recommended_qty": 58,
            "waste_reduction": "6.5%"
        },
        {
            "product_id": "CRK075",
            "recommended_qty": 68,
            "waste_reduction": "8.1%"
        },
        // ...
    ],
    "total_waste_reduction": "7.2%",
    "total_cost_savings": 18.30
}
```

#### 3. Feature importance
```python
GET /api/v1/model/feature-importance

Response:
{
    "features": [
        {
            "feature": "passenger_count",
            "importance": 0.35,
            "rank": 1
        },
        {
            "feature": "product_id_encoded",
            "importance": 0.22,
            "rank": 2
        },
        {
            "feature": "flight_type_medium-haul",
            "importance": 0.15,
            "rank": 3
        }
        // ...
    ]
}
```

#### 4. Model performance
```python
GET /api/v1/model/metrics

Response:
{
    "model_type": "XGBoost Ensemble",
    "training_date": "2025-10-25T14:30:00Z",
    "metrics": {
        "MAE": 4.2,
        "RMSE": 6.1,
        "MAPE": 6.8,
        "R2": 0.89
    },
    "business_metrics": {
        "waste_reduction": "36%",
        "avg_cost_savings_per_flight": 12.50
    }
}
```

---

## 🐳 Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose API port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  consumption-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - MODEL_PATH=/app/models/xgboost_model.pkl
      - LOG_LEVEL=INFO
```

---

## 📊 Expected Performance

Basado en research y datos disponibles:

| Métrica | Target | Alcanzable con 792 rows |
|---------|--------|-------------------------|
| **MAE** | <5 units | ✅ Sí (4-6 units) |
| **MAPE** | <10% | ✅ Sí (6-12%) |
| **R²** | >0.85 | ⚠️ Probablemente 0.75-0.85 |
| **Waste reduction** | 30%+ | ✅ Sí (25-40%) |
| **≤2% error** | Ideal | ❌ Difícil con solo 12 fechas |

**Limitaciones actuales**:
- Solo 12 fechas (insuficiente para estacionalidad robusta)
- No hay desglose por cabin class
- Falta información de special meals

**Con más datos** (12 meses):
- ✅ Alcanzar ≤2% error
- ✅ Capturar estacionalidad
- ✅ R² >0.90

---

## 🔄 Continuous Improvement

### Auto-retraining pipeline
```python
# Scheduled job (diario)
def auto_retrain():
    # 1. Fetch nuevos datos de ERP
    new_data = fetch_from_erp(yesterday)

    # 2. Append a dataset histórico
    append_to_dataset(new_data)

    # 3. Evaluar performance actual
    current_mae = evaluate_current_model(new_data)

    # 4. Si performance degrada, re-entrenar
    if current_mae > threshold:
        train_new_model()
        deploy_if_better()

    # 5. Log metrics
    log_to_dashboard()
```

---

## 📚 Referencias de Research

1. **KLM TRAYS**: ML forecasting → 63% waste reduction
2. **Rodrigues et al. (2024)**: Random Forest + LSTM → 14-52% waste reduction
3. **van der Walt & Bean (2022)**: XGBoost → 92% satisfaction, -2.2 meals/flight
4. **Malefors et al. (2021)**: Random Forest → MAE <0.15

---

## ✅ Success Criteria

**MVP (2 días)**:
- ✅ XGBoost model entrenado
- ✅ API REST funcional
- ✅ Predicciones con <10% MAPE
- ✅ Demostración con datos reales

**Producción (futuro)**:
- ✅ Ensemble model optimizado
- ✅ Auto-retraining pipeline
- ✅ Integración con ERP
- ✅ Dashboard de monitoring

---

## 🎯 Next Steps

1. **Implementar data_loader.py**
2. **Implementar feature_engineering.py**
3. **Entrenar modelos**
4. **Crear API FastAPI**
5. **Crear demo Jupyter notebook**
6. **Testing y evaluación**

---

¿Listo para empezar la implementación? 🚀
