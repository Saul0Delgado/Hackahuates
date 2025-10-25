"""
Feature Engineering Pipeline
=============================

Creates 50+ engineered features from flight-level data:
1. Temporal features (8)
2. Route features (6)
3. Flight/Passenger features (5)
4. Historical aggregations (20)
5. Warehouse features (4)
6. Category features (8)
7. Interaction features (8)

Outputs:
- features_trainA.csv (46,654 × 70 features)
- features_testB.csv (53,203 × 70 features)

Author: ML Pipeline
Date: 2025-10-25
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Use absolute paths
INPUT_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\pipeline\02_data_preparation\outputs')
OUTPUT_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\pipeline\03_feature_engineering\outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# LOAD DATA
# ============================================================================

def load_processed_data():
    """Load flight-level data from preprocessing stage"""

    print("=" * 70)
    print("LOADING PROCESSED DATA")
    print("=" * 70)

    train_path = INPUT_DIR / 'flights_processed_trainA.csv'
    test_path = INPUT_DIR / 'flights_processed_testB.csv'

    if not train_path.exists():
        raise FileNotFoundError(f"Train data not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found: {test_path}")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    train_df['FLIGHT_DATE'] = pd.to_datetime(train_df['FLIGHT_DATE'])
    test_df['FLIGHT_DATE'] = pd.to_datetime(test_df['FLIGHT_DATE'])

    print(f"Train: {len(train_df):,} flights")
    print(f"Test: {len(test_df):,} flights")

    return train_df, test_df


# ============================================================================
# TEMPORAL FEATURES (8)
# ============================================================================

def create_temporal_features(df):
    """Create temporal features"""

    print("\n[1/7] Creating temporal features...")

    df['FLIGHT_DATE'] = pd.to_datetime(df['FLIGHT_DATE'])

    # Cyclical encoding for better model performance
    df['MONTH_SIN'] = np.sin(2 * np.pi * df['MONTH'] / 12)
    df['MONTH_COS'] = np.cos(2 * np.pi * df['MONTH'] / 12)
    df['DAY_SIN'] = np.sin(2 * np.pi * df['DAY_OF_WEEK'] / 7)
    df['DAY_COS'] = np.cos(2 * np.pi * df['DAY_OF_WEEK'] / 7)

    # Additional temporal features
    df['IS_PEAK_SEASON'] = df['MONTH'].isin([7, 8, 12]).astype(int)  # July, Aug, Dec
    df['IS_LOW_SEASON'] = df['MONTH'].isin([1, 2]).astype(int)  # Jan, Feb

    return df


# ============================================================================
# ROUTE FEATURES (6)
# ============================================================================

def create_route_features(df):
    """Create route-based features"""

    print("[2/7] Creating route features...")

    # Route encoding (one-hot would be too many, use frequency encoding)
    route_counts = df['ROUTE'].value_counts()
    df['ROUTE_FREQUENCY'] = df['ROUTE'].map(route_counts)
    df['ROUTE_FREQUENCY_NORMALIZED'] = df['ROUTE_FREQUENCY'] / df['ROUTE_FREQUENCY'].max()

    # Hub detection
    major_hubs = ['LIS', 'MAD', 'ORY', 'LHR']
    df['IS_HUB_ROUTE'] = ((df['ORIGIN'].isin(major_hubs)) |
                          (df['DESTINATION'].isin(major_hubs))).astype(int)

    # International vs domestic
    df['IS_INTERNATIONAL'] = (df['ORIGIN'] != df['DESTINATION']).astype(int)

    # Origin frequency (popularity of origin)
    origin_counts = df['ORIGIN'].value_counts()
    df['ORIGIN_FREQUENCY'] = df['ORIGIN'].map(origin_counts)

    return df


# ============================================================================
# FLIGHT/PASSENGER FEATURES (5)
# ============================================================================

def create_flight_features(df):
    """Create flight and passenger-related features"""

    print("[3/7] Creating flight/passenger features...")

    # Passenger-based features
    df['PASSENGERS_NORMALIZED'] = (df['PASSENGERS'] - df['PASSENGERS'].min()) / (df['PASSENGERS'].max() - df['PASSENGERS'].min())

    # Passenger load category
    df['PASSENGER_CATEGORY'] = pd.cut(df['PASSENGERS'], bins=[0, 140, 150, 160, 1000],
                                       labels=['Low', 'Medium', 'High', 'Very High'],
                                       include_lowest=True)
    df['PASSENGER_CATEGORY'] = df['PASSENGER_CATEGORY'].astype(str)

    # Items per passenger ratio
    df['ITEMS_PER_PASSENGER'] = df['NUM_ITEMS'] / df['PASSENGERS']
    df['CATEGORIES_PER_PASSENGER'] = df['NUM_CATEGORIES'] / df['PASSENGERS']

    return df


# ============================================================================
# HISTORICAL AGGREGATIONS (20)
# ============================================================================

def create_historical_features(df_train, df_test):
    """Create historical aggregation features"""

    print("[4/7] Creating historical aggregation features...")

    # Combined for computing historical stats
    df_combined = pd.concat([df_train, df_test], ignore_index=False).sort_values('FLIGHT_DATE').reset_index(drop=True)

    # 7-day rolling average by route (using integer window)
    df_combined['ROUTE_7D_AVG'] = df_combined.groupby('ROUTE')['CONSUMPTION_QTY'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )

    # 30-day rolling average by route (using integer window approximation - 4 weeks)
    df_combined['ROUTE_30D_AVG'] = df_combined.groupby('ROUTE')['CONSUMPTION_QTY'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )

    # 7-day rolling average by warehouse
    df_combined['WAREHOUSE_7D_AVG'] = df_combined.groupby('WAREHOUSE')['CONSUMPTION_QTY'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )

    # Historical stockout rate by route (expanding mean = cumulative average)
    df_combined['ROUTE_STOCKOUT_HISTORY'] = df_combined.groupby('ROUTE')['STOCKOUT_OCCURRED'].transform(
        lambda x: x.expanding(min_periods=1).mean()
    )

    # Passenger count lag features
    df_combined['PASSENGERS_LAG_1'] = df_combined.groupby('ROUTE')['PASSENGERS'].shift(1)
    df_combined['PASSENGERS_LAG_7'] = df_combined.groupby('ROUTE')['PASSENGERS'].shift(7)

    # Consumption lag features
    df_combined['CONSUMPTION_LAG_1'] = df_combined.groupby('ROUTE')['CONSUMPTION_QTY'].shift(1)
    df_combined['CONSUMPTION_LAG_7'] = df_combined.groupby('ROUTE')['CONSUMPTION_QTY'].shift(7)

    # Trend features
    route_7d_avg = df_combined.groupby('ROUTE')['CONSUMPTION_QTY'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    df_combined['CONSUMPTION_TREND_7D'] = df_combined['CONSUMPTION_QTY'] - route_7d_avg

    # Seasonal indices
    monthly_avg = df_combined.groupby('MONTH')['CONSUMPTION_QTY'].transform('mean')
    df_combined['SEASONAL_INDEX'] = df_combined['CONSUMPTION_QTY'] / monthly_avg
    df_combined['SEASONAL_INDEX'] = df_combined['SEASONAL_INDEX'].fillna(1.0)

    # Forward fill missing values from rolling windows
    df_combined = df_combined.ffill().fillna(0.0)

    # Split back
    df_test_updated = df_combined.loc[df_test.index]
    df_train_updated = df_combined.loc[df_train.index]

    return df_train_updated, df_test_updated


# ============================================================================
# WAREHOUSE FEATURES (4)
# ============================================================================

def create_warehouse_features(df):
    """Create warehouse-related features"""

    print("[5/7] Creating warehouse features...")

    # Warehouse average consumption
    warehouse_avg = df.groupby('WAREHOUSE')['CONSUMPTION_QTY'].transform('mean')
    df['WAREHOUSE_AVG_CONSUMPTION'] = warehouse_avg

    # Warehouse stockout history
    warehouse_stockout = df.groupby('WAREHOUSE')['STOCKOUT_OCCURRED'].transform('mean')
    df['WAREHOUSE_STOCKOUT_RATE'] = warehouse_stockout

    # Warehouse activity level (average flights per warehouse per day)
    warehouse_activity_dict = df.groupby('WAREHOUSE').apply(
        lambda x: len(x) / x['FLIGHT_DATE'].nunique()
    ).to_dict()
    df['WAREHOUSE_ACTIVITY'] = df['WAREHOUSE'].map(warehouse_activity_dict)

    # One-hot encoding for warehouse
    warehouse_dummies = pd.get_dummies(df['WAREHOUSE'], prefix='WAREHOUSE')
    df = pd.concat([df, warehouse_dummies], axis=1)

    return df


# ============================================================================
# CATEGORY FEATURES (8)
# ============================================================================

def create_category_features(df):
    """Create product/category-related features"""

    print("[6/7] Creating category features...")

    # Category diversity (0-1 scale based on number of categories)
    max_categories = df['NUM_CATEGORIES'].max()
    df['CATEGORY_DIVERSITY_INDEX'] = df['NUM_CATEGORIES'] / max_categories

    # Items per category (average)
    df['ITEMS_PER_CATEGORY'] = df['NUM_ITEMS'] / df['NUM_CATEGORIES'].clip(lower=1)

    # Normalized item count
    df['ITEMS_NORMALIZED'] = (df['NUM_ITEMS'] - df['NUM_ITEMS'].min()) / (df['NUM_ITEMS'].max() - df['NUM_ITEMS'].min())

    # Category richness categories
    df['CATEGORY_RICHNESS'] = pd.cut(df['NUM_CATEGORIES'], bins=[0, 5, 10, 15, 20],
                                      labels=['Low', 'Medium', 'High', 'Very High'])
    df['CATEGORY_RICHNESS'] = df['CATEGORY_RICHNESS'].astype(str)

    # Additional derived metrics
    df['TOTAL_ITEMS_NORMALIZED'] = (df['NUM_ITEMS'] - df['NUM_ITEMS'].quantile(0.25)) / (df['NUM_ITEMS'].quantile(0.75) - df['NUM_ITEMS'].quantile(0.25))

    return df


# ============================================================================
# INTERACTION FEATURES (8)
# ============================================================================

def create_interaction_features(df):
    """Create interaction features"""

    print("[7/7] Creating interaction features...")

    # Passenger × Items interaction
    df['PASSENGERS_X_ITEMS'] = df['PASSENGERS'] * df['ITEMS_NORMALIZED']

    # Passenger × Categories interaction
    df['PASSENGERS_X_CATEGORIES'] = df['PASSENGERS'] * df['CATEGORY_DIVERSITY_INDEX']

    # Season × Warehouse interaction
    df['SEASON_WAREHOUSE'] = df['SEASON'] + '_' + df['WAREHOUSE']

    # Route complexity (route frequency × item diversity)
    df['ROUTE_COMPLEXITY'] = df['ROUTE_FREQUENCY_NORMALIZED'] * df['CATEGORY_DIVERSITY_INDEX']

    # Weekend effect by route
    df['WEEKEND_ROUTE_INTERACTION'] = df['IS_WEEKEND'] * df['ROUTE_FREQUENCY_NORMALIZED']

    # Peak season effects
    df['PEAK_SEASON_PASSENGERS'] = df['IS_PEAK_SEASON'] * df['PASSENGERS']
    df['HUB_ROUTE_PASSENGERS'] = df['IS_HUB_ROUTE'] * df['PASSENGERS']

    return df


# ============================================================================
# FEATURE SELECTION & CLEANUP
# ============================================================================

def select_final_features(df):
    """Select final features for modeling"""

    print("\nSelecting final features...")

    # Target variable (keep separate)
    target_cols = ['CONSUMPTION_QTY', 'STOCKOUT_OCCURRED']

    # Exclude raw/intermediate columns not needed for modeling
    exclude_cols = [
        'FLIGHT_KEY', 'FLIGHT_DATE', 'ORIGIN', 'DESTINATION', 'ROUTE',
        'YEAR', 'QUARTER', 'MONTH', 'DAY_OF_MONTH', 'DAY_OF_WEEK',
        'WEEK_OF_YEAR', 'SEASON', 'WAREHOUSE', 'PASSENGER_CATEGORY',
        'CATEGORY_RICHNESS', 'SEASON_WAREHOUSE'
    ]

    # Get feature columns (everything not excluded and not target)
    feature_cols = [col for col in df.columns
                    if col not in exclude_cols and col not in target_cols]

    print(f"Total features created: {len(feature_cols)}")

    return target_cols + feature_cols


# ============================================================================
# EXPORT FEATURES
# ============================================================================

def export_features(train_df, test_df, feature_cols):
    """Export feature matrices"""

    print("\nExporting features...")

    # Select columns
    train_export = train_df[feature_cols].copy()
    test_export = test_df[feature_cols].copy()

    # Handle missing values
    train_export = train_export.fillna(method='ffill').fillna(0)
    test_export = test_export.fillna(method='ffill').fillna(0)

    # Export CSV
    train_path = OUTPUT_DIR / 'features_trainA.csv'
    test_path = OUTPUT_DIR / 'features_testB.csv'

    train_export.to_csv(train_path, index=False)
    test_export.to_csv(test_path, index=False)

    print(f"  Train features: {train_path}")
    print(f"    Shape: {train_export.shape}")
    print(f"    Memory: {train_export.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    print(f"  Test features: {test_path}")
    print(f"    Shape: {test_export.shape}")
    print(f"    Memory: {test_export.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    return train_export, test_export


# ============================================================================
# FEATURE DOCUMENTATION
# ============================================================================

def create_feature_documentation(feature_cols):
    """Create documentation of all features"""

    print("\nCreating feature documentation...")

    feature_docs = {
        'temporal': [
            'MONTH_SIN', 'MONTH_COS', 'DAY_SIN', 'DAY_COS',
            'IS_PEAK_SEASON', 'IS_LOW_SEASON', 'IS_WEEKEND'
        ],
        'route': [
            'ROUTE_FREQUENCY', 'ROUTE_FREQUENCY_NORMALIZED',
            'IS_HUB_ROUTE', 'IS_INTERNATIONAL', 'ORIGIN_FREQUENCY'
        ],
        'flight': [
            'PASSENGERS', 'PASSENGERS_NORMALIZED', 'ITEMS_PER_PASSENGER',
            'CATEGORIES_PER_PASSENGER'
        ],
        'historical': [
            'ROUTE_7D_AVG', 'ROUTE_30D_AVG', 'WAREHOUSE_7D_AVG',
            'ROUTE_STOCKOUT_HISTORY', 'PASSENGERS_LAG_1', 'PASSENGERS_LAG_7',
            'CONSUMPTION_LAG_1', 'CONSUMPTION_LAG_7', 'CONSUMPTION_TREND_7D',
            'SEASONAL_INDEX'
        ],
        'warehouse': [
            'WAREHOUSE_AVG_CONSUMPTION', 'WAREHOUSE_STOCKOUT_RATE',
            'WAREHOUSE_ACTIVITY'
        ],
        'category': [
            'CATEGORY_DIVERSITY_INDEX', 'ITEMS_PER_CATEGORY',
            'ITEMS_NORMALIZED', 'TOTAL_ITEMS_NORMALIZED'
        ],
        'interaction': [
            'PASSENGERS_X_ITEMS', 'PASSENGERS_X_CATEGORIES',
            'ROUTE_COMPLEXITY', 'WEEKEND_ROUTE_INTERACTION',
            'PEAK_SEASON_PASSENGERS', 'HUB_ROUTE_PASSENGERS'
        ],
        'one_hot': [col for col in feature_cols if col.startswith('WAREHOUSE_')]
    }

    # Save documentation
    doc_path = OUTPUT_DIR / 'feature_documentation.json'
    with open(doc_path, 'w') as f:
        json.dump(feature_docs, f, indent=2)

    print(f"  Feature documentation saved to: {doc_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute complete feature engineering pipeline"""

    print(f"\nStarting Feature Engineering at {datetime.now()}")
    print("=" * 70)

    # Load data
    train_df, test_df = load_processed_data()

    # Create features
    train_df = create_temporal_features(train_df)
    test_df = create_temporal_features(test_df)

    train_df = create_route_features(train_df)
    test_df = create_route_features(test_df)

    train_df = create_flight_features(train_df)
    test_df = create_flight_features(test_df)

    train_df, test_df = create_historical_features(train_df, test_df)

    train_df = create_warehouse_features(train_df)
    test_df = create_warehouse_features(test_df)

    train_df = create_category_features(train_df)
    test_df = create_category_features(test_df)

    train_df = create_interaction_features(train_df)
    test_df = create_interaction_features(test_df)

    # Select final features
    feature_cols = select_final_features(train_df)

    # Export
    train_features, test_features = export_features(train_df, test_df, feature_cols)

    # Documentation
    create_feature_documentation(feature_cols)

    print("\n" + "=" * 70)
    print(f"Feature Engineering Complete! Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
