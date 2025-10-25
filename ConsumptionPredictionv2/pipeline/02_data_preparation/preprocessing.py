"""
Data Preparation & Preprocessing Pipeline
==========================================

Converts transaction-level data → flight-level aggregations
Handles data cleaning, validation, and train/test splitting

Outputs:
- flights_processed_trainA.csv (46,654 flights from Q1 2025)
- flights_processed_testB.csv (53,203 flights from Q2-Q3 2025)

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

# Use absolute path to CSV data directory (much faster than Excel!)
DATA_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\data\raw')
OUTPUT_DIR = Path(__file__).parent / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# LOAD DATA
# ============================================================================

def load_raw_datasets():
    """Load both CSV files"""

    print("=" * 70)
    print("LOADING RAW DATA (from CSV files)")
    print("=" * 70)

    files = sorted(list(DATA_DIR.glob('*.csv')))

    if len(files) == 0:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}. Run 00_excel_to_csv_converter.py first!")

    datasets = {}
    for file_path in files:
        print(f"Loading: {file_path.name}")
        df = pd.read_csv(file_path)
        datasets[file_path.stem] = df
        print(f"  Rows: {len(df):,}, Columns: {len(df.columns)}")

    return datasets


# ============================================================================
# DATA CLEANING
# ============================================================================

def clean_data(df):
    """Clean transaction-level data"""

    print("\nCleaning data...")
    print(f"  Initial rows: {len(df):,}")

    # Convert FECHA to datetime
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')

    # Handle missing values
    df['LOST SALES'] = df['LOST SALES'].fillna(0)

    # Remove invalid records
    # Keep only positive or zero sales
    df = df[df['SALES'] >= 0].copy()
    print(f"  After removing negative sales: {len(df):,}")

    # Remove rows with missing key fields
    key_fields = ['FLIGHT KEY', 'PASSENGERS', 'SALES', 'FECHA']
    df = df.dropna(subset=key_fields)
    print(f"  After removing missing key fields: {len(df):,}")

    # Remove duplicates (keep first occurrence)
    initial_rows = len(df)
    df = df.drop_duplicates()
    print(f"  After removing duplicates: {len(df):,}")

    return df


# ============================================================================
# FLIGHT-LEVEL AGGREGATION
# ============================================================================

def aggregate_to_flight_level(df):
    """
    Aggregate transaction-level data to flight-level

    Each transaction represents one item on one flight.
    We need to aggregate to get total consumption per flight.

    ENHANCED: Also creates product-level (category-level) targets
    """

    print("\nAggregating to flight-level...")

    # Group by FLIGHT KEY and aggregate
    flight_data = df.groupby('FLIGHT KEY').agg({
        # Target variables
        'SALES': 'sum',  # Total consumption
        'LOST SALES': 'sum',  # Total stockouts

        # Flight attributes
        'PASSENGERS': 'first',  # Should be same for all rows of same flight
        'ORIGEN': 'first',
        'DESTINO': 'first',
        'FECHA': 'first',
        'WAREHOUSE': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],

        # Transaction counts
        'ITEM CODE': 'count',  # Number of items/products on this flight
        'CATEGORY': lambda x: x.nunique()  # Number of different categories

    }).reset_index()

    # Rename columns for clarity
    flight_data.columns = [
        'FLIGHT_KEY', 'CONSUMPTION_QTY', 'STOCKOUT_QTY',
        'PASSENGERS', 'ORIGIN', 'DESTINATION', 'FLIGHT_DATE',
        'WAREHOUSE', 'NUM_ITEMS', 'NUM_CATEGORIES'
    ]

    # Create derived features
    flight_data['TOTAL_DEMAND'] = flight_data['CONSUMPTION_QTY'] + flight_data['STOCKOUT_QTY']
    flight_data['STOCKOUT_OCCURRED'] = (flight_data['STOCKOUT_QTY'] > 0).astype(int)
    flight_data['STOCKOUT_RATE'] = (
        flight_data['STOCKOUT_QTY'] / flight_data['TOTAL_DEMAND']
    ).fillna(0)
    flight_data['CONSUMPTION_PER_PASSENGER'] = (
        flight_data['CONSUMPTION_QTY'] / flight_data['PASSENGERS']
    ).fillna(0)

    # Create route feature
    flight_data['ROUTE'] = flight_data['ORIGIN'] + '-' + flight_data['DESTINATION']

    print(f"  Aggregated to {len(flight_data):,} flights")
    print(f"  Avg items per flight: {flight_data['NUM_ITEMS'].mean():.1f}")
    print(f"  Avg categories per flight: {flight_data['NUM_CATEGORIES'].mean():.1f}")

    # ========================================================================
    # PRODUCT-LEVEL AGGREGATION (by CATEGORY)
    # ========================================================================
    print("\n  Creating product-level (category-level) targets...")

    # Aggregate consumption by category
    category_data = df.groupby(['FLIGHT KEY', 'CATEGORY']).agg({
        'SALES': 'sum',  # Consumption by category
        'LOST SALES': 'sum'  # Stockouts by category
    }).reset_index()

    # Pivot to get one column per category
    category_consumption = category_data.pivot_table(
        index='FLIGHT KEY',
        columns='CATEGORY',
        values='SALES',
        fill_value=0,
        aggfunc='sum'
    ).reset_index()

    category_stockouts = category_data.pivot_table(
        index='FLIGHT KEY',
        columns='CATEGORY',
        values='LOST SALES',
        fill_value=0,
        aggfunc='sum'
    ).reset_index()

    # Rename columns to indicate they are consumption quantities
    # Get all columns except 'FLIGHT KEY' and rename them
    consumption_col_names = {col: f'{col}_QTY' for col in category_consumption.columns if col != 'FLIGHT KEY'}
    category_consumption = category_consumption.rename(columns=consumption_col_names)

    stockout_col_names = {col: f'{col}_STOCKOUT' for col in category_stockouts.columns if col != 'FLIGHT KEY'}
    category_stockouts = category_stockouts.rename(columns=stockout_col_names)

    # Merge back into flight_data
    # First, rename 'FLIGHT KEY' in category dataframes to match flight_data's 'FLIGHT_KEY'
    category_consumption = category_consumption.rename(columns={'FLIGHT KEY': 'FLIGHT_KEY'})
    category_stockouts = category_stockouts.rename(columns={'FLIGHT KEY': 'FLIGHT_KEY'})

    flight_data = flight_data.merge(category_consumption, on='FLIGHT_KEY', how='left')
    flight_data = flight_data.merge(category_stockouts, on='FLIGHT_KEY', how='left')

    # Fill missing category values with 0
    category_cols = [col for col in flight_data.columns if '_QTY' in col or '_STOCKOUT' in col]
    flight_data[category_cols] = flight_data[category_cols].fillna(0)

    qty_cols = [col for col in category_cols if '_QTY' in col]
    print(f"    Found {len(qty_cols)} product categories")
    if qty_cols:
        print(f"    Categories: {', '.join([col.replace('_QTY', '') for col in qty_cols])}")

    return flight_data


# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

def extract_temporal_features(flight_data):
    """Extract temporal features from FLIGHT_DATE"""

    print("\nExtracting temporal features...")

    flight_data['FLIGHT_DATE'] = pd.to_datetime(flight_data['FLIGHT_DATE'])

    flight_data['YEAR'] = flight_data['FLIGHT_DATE'].dt.year
    flight_data['MONTH'] = flight_data['FLIGHT_DATE'].dt.month
    flight_data['QUARTER'] = flight_data['FLIGHT_DATE'].dt.quarter
    flight_data['DAY_OF_MONTH'] = flight_data['FLIGHT_DATE'].dt.day
    flight_data['DAY_OF_WEEK'] = flight_data['FLIGHT_DATE'].dt.dayofweek  # 0=Monday, 6=Sunday
    flight_data['WEEK_OF_YEAR'] = flight_data['FLIGHT_DATE'].dt.isocalendar().week
    flight_data['IS_WEEKEND'] = (flight_data['DAY_OF_WEEK'] >= 5).astype(int)

    # Season mapping
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    flight_data['SEASON'] = flight_data['MONTH'].map(season_map)

    # Date-based split indicator
    flight_data['DATA_PARTITION'] = 'A'  # Will update for B
    flight_data.loc[flight_data['FLIGHT_DATE'] >= pd.Timestamp('2025-05-01'), 'DATA_PARTITION'] = 'B'

    return flight_data


# ============================================================================
# DATA QUALITY CORRECTION
# ============================================================================

def correct_data_quality(flight_data):
    """Handle data quality issues discovered in EDA"""

    print("\nCorrecting data quality issues...")
    initial_flights = len(flight_data)

    # Fill missing ORIGIN/DESTINATION with 'UNKNOWN'
    missing_origin = flight_data['ORIGIN'].isnull().sum()
    missing_dest = flight_data['DESTINATION'].isnull().sum()
    if missing_origin > 0 or missing_dest > 0:
        print(f"  Filling {missing_origin} missing ORIGIN values with 'UNKNOWN'")
        print(f"  Filling {missing_dest} missing DESTINATION values with 'UNKNOWN'")
        flight_data['ORIGIN'] = flight_data['ORIGIN'].fillna('UNKNOWN')
        flight_data['DESTINATION'] = flight_data['DESTINATION'].fillna('UNKNOWN')

    # Fill missing WAREHOUSE with most common warehouse
    missing_warehouse = flight_data['WAREHOUSE'].isnull().sum()
    if missing_warehouse > 0:
        print(f"  Filling {missing_warehouse} missing WAREHOUSE values with mode")
        most_common_warehouse = flight_data['WAREHOUSE'].mode()[0]
        flight_data['WAREHOUSE'] = flight_data['WAREHOUSE'].fillna(most_common_warehouse)

    # Handle invalid passenger counts (null or <= 0)
    invalid_passengers = (flight_data['PASSENGERS'].isnull()) | (flight_data['PASSENGERS'] <= 0)
    invalid_count = invalid_passengers.sum()
    if invalid_count > 0:
        print(f"  [WARNING] Found {invalid_count} flights with invalid passenger counts (null or <=0)")
        print(f"  Removing these {invalid_count} flights from dataset")
        flight_data = flight_data[~invalid_passengers].copy()

    # Update ROUTE after filling missing values
    flight_data['ROUTE'] = flight_data['ORIGIN'] + '-' + flight_data['DESTINATION']

    removed_flights = initial_flights - len(flight_data)
    if removed_flights > 0:
        print(f"  Total flights removed due to data quality: {removed_flights} ({removed_flights/initial_flights*100:.2f}%)")

    return flight_data


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_flight_data(flight_data):
    """Validate aggregated flight data"""

    print("\nValidating flight-level data...")

    # Check for remaining missing values
    missing = flight_data.isnull().sum()
    if missing.sum() > 0:
        print("  Warning: Missing values found:")
        print(missing[missing > 0])
    else:
        print("  [OK] No missing values")

    # Check data ranges
    assert (flight_data['CONSUMPTION_QTY'] >= 0).all(), "Negative consumption found!"
    assert (flight_data['STOCKOUT_QTY'] >= 0).all(), "Negative stockout found!"
    assert (flight_data['PASSENGERS'] > 0).all(), "Non-positive passenger count found!"
    assert (flight_data['STOCKOUT_RATE'] >= 0).all() and (flight_data['STOCKOUT_RATE'] <= 1).all(), \
        "Stockout rate out of range!"
    assert (flight_data['FLIGHT_DATE'].notna()).all(), "Missing flight dates!"

    # Check temporal consistency
    assert flight_data['FLIGHT_DATE'].min() >= pd.Timestamp('2025-01-01'), "Date before 2025-01-01"
    assert flight_data['FLIGHT_DATE'].max() <= pd.Timestamp('2025-12-31'), "Date after 2025-12-31"

    print(f"  [OK] All validation checks passed!")

    # Summary statistics
    print(f"\n  Consumption Statistics:")
    print(f"    Mean: {flight_data['CONSUMPTION_QTY'].mean():.2f}")
    print(f"    Std: {flight_data['CONSUMPTION_QTY'].std():.2f}")
    print(f"    Min: {flight_data['CONSUMPTION_QTY'].min():.2f}")
    print(f"    Max: {flight_data['CONSUMPTION_QTY'].max():.2f}")

    print(f"\n  Passenger Statistics:")
    print(f"    Mean: {flight_data['PASSENGERS'].mean():.2f}")
    print(f"    Std: {flight_data['PASSENGERS'].std():.2f}")
    print(f"    Min: {flight_data['PASSENGERS'].min()}")
    print(f"    Max: {flight_data['PASSENGERS'].max()}")

    print(f"\n  Stockout Statistics:")
    stockout_flights = (flight_data['STOCKOUT_OCCURRED'] == 1).sum()
    print(f"    Flights with stockouts: {stockout_flights:,} ({stockout_flights/len(flight_data)*100:.2f}%)")
    print(f"    Avg stockout rate: {flight_data['STOCKOUT_RATE'].mean():.4f}")

    return flight_data


# ============================================================================
# TRAIN/TEST SPLIT
# ============================================================================

def split_train_test(flight_data):
    """Split into train (Q1 2025) and test (Q2-Q3 2025)"""

    print("\nSplitting into train and test sets...")

    train_data = flight_data[flight_data['DATA_PARTITION'] == 'A'].copy()
    test_data = flight_data[flight_data['DATA_PARTITION'] == 'B'].copy()

    print(f"  Train set (Q1 2025): {len(train_data):,} flights")
    print(f"    Date range: {train_data['FLIGHT_DATE'].min().date()} to {train_data['FLIGHT_DATE'].max().date()}")

    print(f"  Test set (Q2-Q3 2025): {len(test_data):,} flights")
    print(f"    Date range: {test_data['FLIGHT_DATE'].min().date()} to {test_data['FLIGHT_DATE'].max().date()}")

    return train_data, test_data


# ============================================================================
# EXPORT DATA
# ============================================================================

def export_processed_data(train_data, test_data):
    """Export to CSV for next pipeline stages"""

    print("\nExporting processed data...")

    # Select final columns - include category columns
    base_columns = [
        'FLIGHT_KEY', 'FLIGHT_DATE', 'ORIGIN', 'DESTINATION', 'ROUTE',
        'PASSENGERS', 'WAREHOUSE', 'NUM_ITEMS', 'NUM_CATEGORIES',
        'CONSUMPTION_QTY', 'STOCKOUT_QTY', 'TOTAL_DEMAND',
        'STOCKOUT_OCCURRED', 'STOCKOUT_RATE', 'CONSUMPTION_PER_PASSENGER',
        'YEAR', 'MONTH', 'QUARTER', 'DAY_OF_WEEK', 'IS_WEEKEND', 'SEASON'
    ]

    # Add category columns (product-level targets)
    category_columns = [col for col in train_data.columns if '_QTY' in col or '_STOCKOUT' in col]
    final_columns = base_columns + category_columns

    # Keep only columns that exist
    final_columns = [col for col in final_columns if col in train_data.columns]

    train_data = train_data[final_columns]
    test_data = test_data[final_columns]

    # Export train
    train_path = OUTPUT_DIR / 'flights_processed_trainA.csv'
    train_data.to_csv(train_path, index=False)
    print(f"  Exported: {train_path}")
    print(f"    Columns: {len(train_data.columns)}")
    print(f"    Size: {train_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # Export test
    test_path = OUTPUT_DIR / 'flights_processed_testB.csv'
    test_data.to_csv(test_path, index=False)
    print(f"  Exported: {test_path}")
    print(f"    Columns: {len(test_data.columns)}")
    print(f"    Size: {test_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # Print category columns info
    print(f"\n  Product-level targets (categories): {len(category_columns)}")
    qty_cols = [col for col in category_columns if '_QTY' in col]
    if qty_cols:
        print(f"    {', '.join([col.replace('_QTY', '') for col in qty_cols])}")

    return train_data, test_data


# ============================================================================
# DATA QUALITY REPORT
# ============================================================================

def generate_quality_report(original_data, processed_data):
    """Generate data quality metrics"""

    print("\nGenerating quality report...")

    report = {
        'timestamp': datetime.now().isoformat(),
        'original_rows': len(original_data),
        'processed_flights': len(processed_data),
        'data_retention_pct': len(processed_data) / len(original_data) * 100,
        'processed_stats': {
            'consumption': {
                'mean': float(processed_data['CONSUMPTION_QTY'].mean()),
                'std': float(processed_data['CONSUMPTION_QTY'].std()),
                'min': float(processed_data['CONSUMPTION_QTY'].min()),
                'max': float(processed_data['CONSUMPTION_QTY'].max()),
            },
            'passengers': {
                'mean': float(processed_data['PASSENGERS'].mean()),
                'std': float(processed_data['PASSENGERS'].std()),
                'min': int(processed_data['PASSENGERS'].min()),
                'max': int(processed_data['PASSENGERS'].max()),
            },
            'stockout_rate': {
                'mean': float(processed_data['STOCKOUT_RATE'].mean()),
                'flights_with_stockouts': int((processed_data['STOCKOUT_OCCURRED'] == 1).sum()),
                'pct_with_stockouts': float((processed_data['STOCKOUT_OCCURRED'] == 1).sum() / len(processed_data) * 100),
            }
        }
    }

    # Save report
    report_path = OUTPUT_DIR / 'preprocessing_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"  Quality report saved to: {report_path}")

    return report


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute complete preprocessing pipeline"""

    print(f"\nStarting Data Preparation at {datetime.now()}")
    print("=" * 70)

    # Load raw data
    datasets = load_raw_datasets()

    # Combine datasets
    combined_df = pd.concat(list(datasets.values()), ignore_index=True)
    print(f"\nCombined dataset: {len(combined_df):,} transactions")

    # Clean data
    combined_df = clean_data(combined_df)

    # Aggregate to flight level
    flight_data = aggregate_to_flight_level(combined_df)

    # Extract temporal features
    flight_data = extract_temporal_features(flight_data)

    # Correct data quality issues discovered in EDA
    flight_data = correct_data_quality(flight_data)

    # Validate
    flight_data = validate_flight_data(flight_data)

    # Split train/test
    train_data, test_data = split_train_test(flight_data)

    # Export
    train_data, test_data = export_processed_data(train_data, test_data)

    # Quality report
    generate_quality_report(combined_df, flight_data)

    print("\n" + "=" * 70)
    print(f"Data Preparation Complete! Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
