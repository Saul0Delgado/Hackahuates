"""
Exploratory Data Analysis (EDA) for Consumption Prediction Dataset
================================================================

Analyzes 1.3M transactions from Q1-Q3 2025 airline catering data to:
- Understand data structure and quality
- Identify key patterns and relationships
- Guide feature engineering strategy
- Detect anomalies and data issues

Author: ML Pipeline
Date: 2025-10-25
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Use absolute path to CSV data directory (much faster than Excel!)
DATA_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\data\raw')
OUTPUT_DIR = Path(__file__).parent / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"Data directory: {DATA_DIR}")
print(f"Data directory exists: {DATA_DIR.exists()}")

# Plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# DATA LOADING
# ============================================================================

def load_datasets():
    """Load both Excel files (Q1 2025 and Q2-Q3 2025)"""

    print("=" * 70)
    print("LOADING DATASETS")
    print("=" * 70)

    # Find CSV files (much faster than Excel!)
    files = sorted(list(DATA_DIR.glob('*.csv')))
    print(f"\nFound {len(files)} CSV files:")
    for f in files:
        print(f"  - {f.name}")

    if len(files) == 0:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    datasets = {}
    for file_path in files:
        print(f"\nLoading: {file_path.name}")

        df = pd.read_csv(file_path)
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        datasets[file_path.stem] = df

    print(f"\nTotal datasets loaded: {len(datasets)}")
    return datasets


# ============================================================================
# INITIAL EXPLORATION
# ============================================================================

def explore_schema(datasets):
    """Analyze dataset schema and data types"""

    print("\n" + "=" * 70)
    print("SCHEMA ANALYSIS")
    print("=" * 70)

    for name, df in datasets.items():
        print(f"\n{name}:")
        print(f"{'Column':<20} {'Type':<15} {'Missing':<10} {'Unique':<10}")
        print("-" * 55)

        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = df[col].isna().sum()
            unique = df[col].nunique()
            print(f"{col:<20} {dtype:<15} {missing:<10} {unique:<10}")


def explore_target_variable(datasets):
    """Analyze SALES (consumption) as target variable"""

    print("\n" + "=" * 70)
    print("TARGET VARIABLE ANALYSIS: SALES (CONSUMPTION)")
    print("=" * 70)

    combined_sales = pd.concat([df['SALES'] for df in datasets.values()])

    print(f"\nStatistics:")
    print(f"  Mean: {combined_sales.mean():.4f}")
    print(f"  Median: {combined_sales.median():.4f}")
    print(f"  Std Dev: {combined_sales.std():.4f}")
    print(f"  Min: {combined_sales.min():.4f}")
    print(f"  Max: {combined_sales.max():.4f}")
    print(f"  Q1: {combined_sales.quantile(0.25):.4f}")
    print(f"  Q3: {combined_sales.quantile(0.75):.4f}")

    print(f"\nZero sales: {(combined_sales == 0).sum():,} ({(combined_sales == 0).sum()/len(combined_sales)*100:.2f}%)")
    print(f"Negative sales: {(combined_sales < 0).sum():,} ({(combined_sales < 0).sum()/len(combined_sales)*100:.2f}%)")

    # Distribution visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(combined_sales, bins=50, edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Sales Quantity')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Distribution of Sales (All Data)')
    axes[0].grid(True, alpha=0.3)

    # Filtered view (exclude zero sales)
    non_zero_sales = combined_sales[combined_sales > 0]
    axes[1].hist(non_zero_sales, bins=50, edgecolor='black', alpha=0.7, color='green')
    axes[1].set_xlabel('Sales Quantity')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title(f'Distribution of Sales (Non-Zero Only, n={len(non_zero_sales):,})')
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '01_sales_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()


def analyze_lost_sales(datasets):
    """Analyze stockout/lost sales problem"""

    print("\n" + "=" * 70)
    print("CRITICAL PROBLEM: LOST SALES (STOCKOUTS)")
    print("=" * 70)

    for name, df in datasets.items():
        lost_sales = df['LOST SALES'].fillna(0)
        total_demand = df['SALES'] + lost_sales

        total_sales = df['SALES'].sum()
        total_lost = lost_sales.sum()
        stockout_rate = (total_lost / (total_sales + total_lost)) * 100 if (total_sales + total_lost) > 0 else 0

        print(f"\n{name}:")
        print(f"  Total Sales: {total_sales:,.0f}")
        print(f"  Total Lost Sales: {total_lost:,.0f}")
        print(f"  Stockout Rate: {stockout_rate:.2f}%")
        print(f"  Transactions with stockouts: {(lost_sales > 0).sum():,}")


# ============================================================================
# CATEGORICAL ANALYSIS
# ============================================================================

def analyze_categories(datasets):
    """Analyze product categories"""

    print("\n" + "=" * 70)
    print("CATEGORY ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    category_stats = combined_df.groupby('CATEGORY').agg({
        'SALES': ['sum', 'mean', 'count'],
        'LOST SALES': lambda x: x.fillna(0).sum()
    }).round(2)

    category_stats.columns = ['Total Sales', 'Avg Sales', 'Count', 'Total Lost']
    category_stats['Stockout Rate %'] = (category_stats['Total Lost'] / (category_stats['Total Sales'] + category_stats['Total Lost']) * 100).round(2)
    category_stats = category_stats.sort_values('Total Sales', ascending=False)

    print("\nCategory Performance:")
    print(category_stats)

    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Sales by category
    category_sales = combined_df.groupby('CATEGORY')['SALES'].sum().sort_values(ascending=False)
    axes[0, 0].barh(category_sales.index, category_sales.values, color='steelblue')
    axes[0, 0].set_xlabel('Total Sales')
    axes[0, 0].set_title('Sales by Category')
    axes[0, 0].grid(True, alpha=0.3, axis='x')

    # Stockout rate by category
    category_stockout = (combined_df.groupby('CATEGORY')['LOST SALES'].fillna(0).sum() /
                         (combined_df.groupby('CATEGORY')['SALES'].sum() +
                          combined_df.groupby('CATEGORY')['LOST SALES'].fillna(0).sum()) * 100).sort_values(ascending=False)
    axes[0, 1].barh(category_stockout.index, category_stockout.values, color='coral')
    axes[0, 1].set_xlabel('Stockout Rate (%)')
    axes[0, 1].set_title('Stockout Rate by Category')
    axes[0, 1].grid(True, alpha=0.3, axis='x')

    # Count by category
    category_count = combined_df['CATEGORY'].value_counts().sort_values(ascending=False)
    axes[1, 0].barh(category_count.index, category_count.values, color='green')
    axes[1, 0].set_xlabel('Number of Transactions')
    axes[1, 0].set_title('Transaction Count by Category')
    axes[1, 0].grid(True, alpha=0.3, axis='x')

    # Average sales by category
    category_avg = combined_df.groupby('CATEGORY')['SALES'].mean().sort_values(ascending=False)
    axes[1, 1].barh(category_avg.index, category_avg.values, color='purple')
    axes[1, 1].set_xlabel('Average Sales per Transaction')
    axes[1, 1].set_title('Avg Sales by Category')
    axes[1, 1].grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '02_category_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# ROUTE ANALYSIS
# ============================================================================

def analyze_routes(datasets):
    """Analyze routes and origins/destinations"""

    print("\n" + "=" * 70)
    print("ROUTE ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    # Create route pair
    combined_df['ROUTE'] = combined_df['ORIGEN'] + '-' + combined_df['DESTINO']

    route_stats = combined_df.groupby('ROUTE').agg({
        'SALES': ['sum', 'mean', 'count'],
        'LOST SALES': lambda x: x.fillna(0).sum(),
        'PASSENGERS': ['mean', 'min', 'max']
    }).round(2)

    route_stats.columns = ['Total Sales', 'Avg Sales', 'Count', 'Lost Sales', 'Avg Passengers', 'Min Pass', 'Max Pass']
    route_stats = route_stats.sort_values('Count', ascending=False)

    print(f"\nUnique routes: {combined_df['ROUTE'].nunique()}")
    print(f"\nTop 15 routes by transaction count:")
    print(route_stats.head(15))

    # Top origins
    origin_stats = combined_df.groupby('ORIGEN').agg({
        'SALES': ['sum', 'mean', 'count'],
        'PASSENGERS': 'mean'
    }).round(2)

    origin_stats.columns = ['Total Sales', 'Avg Sales', 'Count', 'Avg Passengers']
    origin_stats = origin_stats.sort_values('Count', ascending=False)

    print(f"\nOrigins (top 10):")
    print(origin_stats.head(10))

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Top 15 routes
    top_routes = combined_df['ROUTE'].value_counts().head(15)
    axes[0].barh(top_routes.index, top_routes.values, color='teal')
    axes[0].set_xlabel('Number of Transactions')
    axes[0].set_title('Top 15 Routes by Transaction Volume')
    axes[0].grid(True, alpha=0.3, axis='x')

    # Top 10 origins
    top_origins = combined_df['ORIGEN'].value_counts().head(10)
    axes[1].bar(top_origins.index, top_origins.values, color='darkgreen')
    axes[1].set_ylabel('Number of Transactions')
    axes[1].set_title('Top 10 Origins by Transaction Volume')
    axes[1].grid(True, alpha=0.3, axis='y')
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '03_route_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# WAREHOUSE ANALYSIS
# ============================================================================

def analyze_warehouses(datasets):
    """Analyze warehouse distribution and performance"""

    print("\n" + "=" * 70)
    print("WAREHOUSE ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    warehouse_stats = combined_df.groupby('WAREHOUSE').agg({
        'SALES': ['sum', 'mean', 'count'],
        'LOST SALES': lambda x: x.fillna(0).sum(),
        'PASSENGERS': 'mean'
    }).round(2)

    warehouse_stats.columns = ['Total Sales', 'Avg Sales', 'Count', 'Lost Sales', 'Avg Passengers']
    warehouse_stats['% of Total'] = (warehouse_stats['Count'] / warehouse_stats['Count'].sum() * 100).round(2)

    print("\nWarehouse Performance:")
    print(warehouse_stats)

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Warehouse distribution
    warehouse_count = combined_df['WAREHOUSE'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(warehouse_count)))
    axes[0].pie(warehouse_count.values, labels=warehouse_count.index, autopct='%1.1f%%', colors=colors)
    axes[0].set_title('Distribution of Transactions by Warehouse')

    # Average sales by warehouse
    warehouse_avg = combined_df.groupby('WAREHOUSE')['SALES'].mean().sort_values(ascending=False)
    axes[1].bar(warehouse_avg.index, warehouse_avg.values, color='orange')
    axes[1].set_ylabel('Average Sales per Transaction')
    axes[1].set_title('Average Sales by Warehouse')
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '04_warehouse_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# TEMPORAL ANALYSIS
# ============================================================================

def analyze_temporal(datasets):
    """Analyze temporal patterns"""

    print("\n" + "=" * 70)
    print("TEMPORAL ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)
    combined_df['FECHA'] = pd.to_datetime(combined_df['FECHA'])
    combined_df['DATE_ONLY'] = combined_df['FECHA'].dt.date

    # Daily aggregation
    daily_sales = combined_df.groupby('DATE_ONLY')['SALES'].agg(['sum', 'mean', 'count']).reset_index()
    daily_sales.columns = ['Date', 'Total Sales', 'Avg Sales', 'Transactions']

    print(f"\nDaily Statistics:")
    print(f"  Avg daily sales: {daily_sales['Total Sales'].mean():.2f}")
    print(f"  Avg transactions per day: {daily_sales['Transactions'].mean():.0f}")
    print(f"  Date range: {daily_sales['Date'].min()} to {daily_sales['Date'].max()}")

    # Temporal visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Daily trend
    axes[0, 0].plot(daily_sales['Date'], daily_sales['Total Sales'], marker='o', linestyle='-', alpha=0.7)
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Total Sales')
    axes[0, 0].set_title('Daily Sales Trend')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].tick_params(axis='x', rotation=45)

    # Passenger count trend
    daily_passengers = combined_df.groupby('DATE_ONLY')['PASSENGERS'].mean()
    axes[0, 1].plot(daily_passengers.index, daily_passengers.values, marker='s', linestyle='-', color='green', alpha=0.7)
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Average Passengers')
    axes[0, 1].set_title('Daily Average Passenger Count')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)

    # Monthly aggregation
    combined_df['MONTH'] = combined_df['FECHA'].dt.to_period('M')
    monthly_stats = combined_df.groupby('MONTH').agg({
        'SALES': ['sum', 'mean'],
        'PASSENGERS': 'mean',
        'LOST SALES': lambda x: x.fillna(0).sum()
    }).round(2)

    monthly_sales = monthly_stats['SALES']['sum']
    axes[1, 0].bar(monthly_sales.index.astype(str), monthly_sales.values, color='steelblue')
    axes[1, 0].set_xlabel('Month')
    axes[1, 0].set_ylabel('Total Sales')
    axes[1, 0].set_title('Monthly Total Sales')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    plt.setp(axes[1, 0].xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Day of week effect
    combined_df['DAY_OF_WEEK'] = combined_df['FECHA'].dt.day_name()
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_sales = combined_df.groupby('DAY_OF_WEEK')['SALES'].mean().reindex(dow_order)
    axes[1, 1].bar(range(len(dow_sales)), dow_sales.values, color='purple', alpha=0.7)
    axes[1, 1].set_xticks(range(len(dow_sales)))
    axes[1, 1].set_xticklabels([day[:3] for day in dow_sales.index], rotation=45)
    axes[1, 1].set_ylabel('Average Sales')
    axes[1, 1].set_title('Day of Week Effect on Sales')
    axes[1, 1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '05_temporal_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# PASSENGER ANALYSIS
# ============================================================================

def analyze_passengers(datasets):
    """Analyze relationship between passengers and sales"""

    print("\n" + "=" * 70)
    print("PASSENGER & CONSUMPTION ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    # Sales per passenger ratio
    combined_df['SALES_PER_PASSENGER'] = combined_df['SALES'] / combined_df['PASSENGERS']
    combined_df['SALES_PER_PASSENGER'] = combined_df['SALES_PER_PASSENGER'].replace([np.inf, -np.inf], 0)

    print(f"\nSales per Passenger Analysis:")
    print(f"  Mean: {combined_df['SALES_PER_PASSENGER'].mean():.4f}")
    print(f"  Std Dev: {combined_df['SALES_PER_PASSENGER'].std():.4f}")
    print(f"  Min: {combined_df['SALES_PER_PASSENGER'].min():.4f}")
    print(f"  Max: {combined_df['SALES_PER_PASSENGER'].max():.4f}")

    print(f"\nPassenger Count Distribution:")
    print(f"  Mean: {combined_df['PASSENGERS'].mean():.2f}")
    print(f"  Median: {combined_df['PASSENGERS'].median():.2f}")
    print(f"  Std Dev: {combined_df['PASSENGERS'].std():.2f}")
    print(f"  Min: {combined_df['PASSENGERS'].min()}")
    print(f"  Max: {combined_df['PASSENGERS'].max()}")

    # Correlation
    correlation = combined_df[['PASSENGERS', 'SALES', 'SALES_PER_PASSENGER']].corr()
    print(f"\nCorrelation Matrix:")
    print(correlation)

    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Scatter: Passengers vs Sales
    axes[0, 0].scatter(combined_df['PASSENGERS'], combined_df['SALES'], alpha=0.3, s=20)
    axes[0, 0].set_xlabel('Passenger Count')
    axes[0, 0].set_ylabel('Sales')
    axes[0, 0].set_title(f'Passengers vs Sales (r={combined_df["PASSENGERS"].corr(combined_df["SALES"]):.3f})')
    axes[0, 0].grid(True, alpha=0.3)

    # Distribution of sales per passenger
    axes[0, 1].hist(combined_df['SALES_PER_PASSENGER'][combined_df['SALES_PER_PASSENGER'] < 1],
                    bins=50, edgecolor='black', alpha=0.7, color='green')
    axes[0, 1].set_xlabel('Sales per Passenger')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Distribution of Sales per Passenger (< 1.0)')
    axes[0, 1].grid(True, alpha=0.3)

    # Passenger distribution
    axes[1, 0].hist(combined_df['PASSENGERS'], bins=30, edgecolor='black', alpha=0.7, color='blue')
    axes[1, 0].set_xlabel('Passenger Count')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Distribution of Passenger Counts')
    axes[1, 0].grid(True, alpha=0.3)

    # Sales distribution
    axes[1, 1].hist(combined_df['SALES'][combined_df['SALES'] > 0], bins=50, edgecolor='black', alpha=0.7, color='orange')
    axes[1, 1].set_xlabel('Sales Quantity')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Distribution of Sales (Non-Zero)')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '06_passenger_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# ITEM CODE ANALYSIS
# ============================================================================

def analyze_items(datasets):
    """Analyze individual items/SKUs"""

    print("\n" + "=" * 70)
    print("ITEM/SKU ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    item_stats = combined_df.groupby('ITEM CODE').agg({
        'SALES': ['sum', 'mean', 'count'],
        'LOST SALES': lambda x: x.fillna(0).sum(),
        'CATEGORY': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'
    }).round(2)

    item_stats.columns = ['Total Sales', 'Avg Sales', 'Count', 'Lost Sales', 'Primary Category']
    item_stats = item_stats.sort_values('Count', ascending=False)

    print(f"\nUnique items: {combined_df['ITEM CODE'].nunique()}")
    print(f"\nTop 20 items by transaction count:")
    print(item_stats.head(20))


# ============================================================================
# CORRELATION ANALYSIS
# ============================================================================

def analyze_correlations(datasets):
    """Analyze correlations between numeric variables"""

    print("\n" + "=" * 70)
    print("CORRELATION ANALYSIS")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    # Numeric columns
    numeric_df = combined_df[['SALES', 'LOST SALES', 'PASSENGERS']].fillna(0)
    correlation_matrix = numeric_df.corr()

    print("\nCorrelation Matrix:")
    print(correlation_matrix)

    # Visualization
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Correlation Matrix: Key Variables')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / '07_correlation_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()


# ============================================================================
# DATA QUALITY REPORT
# ============================================================================

def data_quality_report(datasets):
    """Generate comprehensive data quality report"""

    print("\n" + "=" * 70)
    print("DATA QUALITY REPORT")
    print("=" * 70)

    quality_report = {}

    for name, df in datasets.items():
        quality_report[name] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }

        print(f"\n{name}:")
        print(f"  Total rows: {len(df):,}")
        print(f"  Duplicate rows: {df.duplicated().sum():,}")
        print(f"  Missing values: {df.isnull().sum().sum():,}")

    # Save quality report
    with open(OUTPUT_DIR / 'data_quality_report.json', 'w') as f:
        json.dump(quality_report, f, indent=2, default=str)

    return quality_report


# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================

def generate_summary(datasets):
    """Generate summary of findings and recommendations"""

    print("\n" + "=" * 70)
    print("SUMMARY & RECOMMENDATIONS FOR FEATURE ENGINEERING")
    print("=" * 70)

    combined_df = pd.concat(datasets.values(), ignore_index=True)

    summary = {
        'total_transactions': len(combined_df),
        'total_unique_flights': combined_df['FLIGHT KEY'].nunique(),
        'unique_items': combined_df['ITEM CODE'].nunique(),
        'unique_categories': combined_df['CATEGORY'].nunique(),
        'unique_routes': (combined_df['ORIGEN'] + '-' + combined_df['DESTINO']).nunique(),
        'unique_warehouses': combined_df['WAREHOUSE'].nunique(),
        'avg_transactions_per_flight': len(combined_df) / combined_df['FLIGHT KEY'].nunique(),
        'avg_passenger_count': combined_df['PASSENGERS'].mean(),
        'stockout_rate_percent': ((combined_df['LOST SALES'].fillna(0).sum() /
                                   (combined_df['SALES'].sum() + combined_df['LOST SALES'].fillna(0).sum())) * 100),
        'date_range': f"{combined_df['FECHA'].min()} to {combined_df['FECHA'].max()}"
    }

    print("\nDataset Summary:")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")

    recommendations = """
RECOMMENDED FEATURES FOR ENGINEERING (Updated from EDA):

1. TEMPORAL FEATURES (7):
   - day_of_week: Strong weekly patterns observed
   - month, quarter, season: Seasonal consumption variations
   - is_weekend: Different patterns on weekends
   - is_holiday: Holiday effects
   - days_since_year_start

2. ROUTE FEATURES (6):
   - origin, destination: Geographic patterns
   - route_pair: Origin-destination interaction
   - route_distance: Can estimate from IATA codes
   - is_international: Short-haul vs international
   - is_hub_route: High-traffic routes show patterns

3. FLIGHT/PASSENGER FEATURES (5):
   - passenger_count: Strong correlation with sales
   - passenger_count_normalized: Per-aircraft-capacity
   - booked_utilization_ratio: Demand signal
   - flight_duration_category: Long-haul vs short-haul
   - departure_time_category: Morning, afternoon, evening

4. HISTORICAL AGGREGATIONS (20):
   - Rolling averages (7-day, 30-day, 90-day) by route
   - Rolling averages by warehouse
   - Historical consumption by category
   - Historical stockout rates
   - Seasonal indices (normalized by month/week)
   - Trend indicators (is consumption increasing/decreasing?)

5. WAREHOUSE FEATURES (4):
   - warehouse_location: Encoding warehouse patterns
   - warehouse_avg_sales: Warehouse capacity/efficiency
   - warehouse_stockout_history: Warehouse reliability
   - inventory_level_category: Estimated stock levels

6. PRODUCT/CATEGORY FEATURES (8):
   - top_category_proportion: What dominates this flight?
   - category_diversity_index: Variety of products
   - category_historical_rate: Category consumption rates
   - category_seasonality: Category x season effects
   - category_warehouse_affinity: Which categories in which warehouses

7. INTERACTION FEATURES (8):
   - route x season: Route-specific seasonality
   - warehouse x category: Warehouse expertise in categories
   - passenger_count x category: Passenger type effects
   - day_of_week x route: Route-specific weekly effects

IMMEDIATE ACTIONS:

1. [OK] COMPLETE: Dataset structure and quality verified
2. NEXT: Aggregate transaction-level > flight-level data
   - Sum SALES and LOST SALES per FLIGHT KEY
   - Create binary targets: shortage_occurred (0/1)
3. NEXT: Implement feature engineering pipeline
   - All 58+ features listed above
4. NEXT: Train XGBoost, Random Forest, Neural Network
5. NEXT: Evaluate and compare models

KEY METRIC TO TRACK:
>> Can we reduce stockout rate from {summary['stockout_rate_percent']:.1f}% to <5%?
"""

    print(recommendations)

    # Save summary
    with open(OUTPUT_DIR / 'eda_summary.txt', 'w') as f:
        f.write(f"EDA SUMMARY - {datetime.now()}\n")
        f.write("=" * 70 + "\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
        f.write("\n" + recommendations)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute complete EDA pipeline"""

    print(f"\nStarting EDA Pipeline at {datetime.now()}")
    print("=" * 70)

    # Load data
    datasets = load_datasets()

    # Exploratory analyses
    explore_schema(datasets)
    explore_target_variable(datasets)
    analyze_lost_sales(datasets)
    analyze_categories(datasets)
    analyze_routes(datasets)
    analyze_warehouses(datasets)
    analyze_temporal(datasets)
    analyze_passengers(datasets)
    analyze_items(datasets)
    analyze_correlations(datasets)

    # Quality and summary
    data_quality_report(datasets)
    generate_summary(datasets)

    print("\n" + "=" * 70)
    print(f"EDA Complete! Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
