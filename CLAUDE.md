# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hackahuates is a hackathon project for an airline catering meal quantity prediction system. The system uses machine learning to predict optimal meal quantities for flights, balancing service quality against operational efficiency and waste reduction.

## Repository Structure

```
Hackahuates/
├── Frontend/          # React + TypeScript + Vite web application
├── Docs/             # Project documentation and ML context
│   └── context.md    # Comprehensive ML requirements (4 integrated PDFs)
└── README.md         # Basic project description
```

## Frontend Development

### Setup and Commands

```bash
cd Frontend
npm install              # Install dependencies
npm run dev             # Start development server (Vite HMR)
npm run build           # TypeScript check + production build
npm run lint            # Run ESLint
npm run preview         # Preview production build
```

### Tech Stack

- **Framework**: React 19.1.1
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.1.7
- **Compiler**: SWC (via @vitejs/plugin-react-swc) for Fast Refresh
- **Linting**: ESLint 9.36.0 with TypeScript support

### Frontend Architecture

The frontend is currently a minimal Vite + React template. Based on the ML context in `Docs/context.md`, the application will need to:

1. Display flight prediction inputs (route, passenger counts, cabin class distribution, special meals)
2. Show ML model outputs (recommended meal quantities by type/class)
3. Visualize historical consumption patterns and waste metrics
4. Provide inventory management interface (SKU availability, expiration dates)
5. Present operational dashboards (pick & pack status, QC metrics)

## Machine Learning Context

The system predicts meal quantities for airline catering by integrating 4 operational domains (see `Docs/context.md` for full details):

### 1. Pick & Pack Process
- Manages order creation → picking → packing → QC → delivery workflow
- Key features: `flight_id`, `route`, `departure_time`, `booked_passengers`, `special_meal_counts`
- Business rules: round to packaging units, enforce minimum overage (+10%), guarantee special meals (100-105%)

### 2. Expiration Date Management
- Handles shelf-life (chilled ~3-5 days, frozen ~30-90 days), FIFO rotation, cold-chain compliance
- Key features: `available_inventory_by_sku`, `sku_shelf_life_days`, `waste_rate_due_to_expiry`
- Constraints: `departure_time - shelf_life` = production deadline

### 3. Consumption Prediction (Core ML Model)
- Predicts actual consumption accounting for no-shows, no-takes, cabin class variations
- **Input features**: flight attributes, passenger data, historical patterns, operational constraints
- **Output targets**: `total_meals_to_prepare`, breakdowns by cabin class/meal type/special diet
- **Modeling approaches**: Gradient-boosted trees (XGBoost/LightGBM), probabilistic/quantile regression

### 4. Productivity Estimation
- Ensures resource allocation feasibility for predicted quantities

### ML Data Flow

```
Bookings → [CONSUMPTION PREDICTION] → Base Quantity
           ↓
Inventory & Expiry → [EXPIRATION MANAGEMENT] → Usable Inventory + Constraints
           ↓
Rounding & Operations → [PICK & PACK PROCESS] → Operational Feasibility
           ↓
Resource Allocation → [PRODUCTIVITY ESTIMATION] → Final Order
```

### Critical Features for ML Model

**Flight attributes**: `flight_id`, `route`, `departure_time`, `flight_duration`, `day_of_week`, `is_holiday`, `season`, `aircraft_type`

**Passenger data**: `booked_passengers`, `booked_passengers_by_class`, `special_meal_counts_by_type`, `crew_meal_count`

**Historical patterns**: `avg_consumption_rate`, `consumption_rate_by_cabin_class`, `consumption_std_dev`

**Inventory & operations**: `available_inventory_by_sku`, `days_to_expiry_by_sku`, `packaging_unit_size`, `preparation_lead_time_hours`

**Business policies**: `overage_percentage_policy`, `minimum_meal_policy`, `shortage_cost`, `overage_cost`

### Post-Processing Rules

1. Round predictions to packaging unit sizes (trays/carts)
2. Apply minimum overage percentage (e.g., +10%)
3. Guarantee special meals at 100-105% of bookings
4. Enforce cold-chain compliance (no prep beyond `max_shelf_life` before departure)
5. Apply cost-optimal bias (if shortage cost > overage cost, bias predictions higher)

### Evaluation Metrics

**Accuracy**: MAE, MAPE, RMSE/quantile loss
**Business**: Cost = `(shortage_rate × shortage_cost) + (overage_rate × overage_cost)`, waste rate, on-time fulfillment

## Development Notes

- The frontend is currently a starter template and needs full implementation
- No backend/API layer exists yet - this will be needed to serve ML predictions
- ML model implementation is not present - refer to `Docs/context.md` for requirements
- Data sources (booking systems, inventory systems, galley logs, waste logs) need integration
- The project appears to be in initial hackathon setup phase
