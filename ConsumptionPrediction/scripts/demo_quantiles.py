"""
Demo script showing quantile predictions and safety stock recommendations
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.data_loader import ConsumptionDataLoader
from src.feature_engineering import FeatureEngineer
from src.models import XGBoostConsumptionModel
from src.utils import logger


def main():
    """Demonstrate quantile predictions and safety stock"""

    print("\n" + "=" * 80)
    print("QUANTILE REGRESSION DEMO: SAFETY STOCK RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Load data
    logger.info("Loading data...")
    data_loader = ConsumptionDataLoader()
    train_df, val_df, test_df = data_loader.load_and_prepare()

    # Engineer features
    logger.info("Engineering features...")
    fe = FeatureEngineer()
    X_train, y_train = fe.transform(train_df, fit=True)
    X_val, y_val = fe.transform(val_df, fit=False)
    X_test, y_test = fe.transform(test_df, fit=False)

    # Train base model
    logger.info("Training base XGBoost model...")
    base_model = XGBoostConsumptionModel()
    base_model.train(X_train, y_train, X_val, y_val, verbose=False)

    # Train quantile ensemble
    logger.info("Training quantile ensemble...")
    base_model.train_quantile_ensemble(X_train, y_train, X_val, y_val, verbose=False)

    # Make predictions
    logger.info("Making predictions...")
    base_preds = base_model.predict(X_test[:10])  # First 10 test samples
    quantile_preds = base_model.predict_quantiles(X_test[:10])
    safety_stock = base_model.get_safety_stock_recommendation(X_test[:10], percentile=90)
    actual = y_test.iloc[:10].values

    # Display results
    print("\n" + "=" * 80)
    print("PREDICTION COMPARISON (First 10 test samples)")
    print("=" * 80)
    print()

    results_df = pd.DataFrame({
        'Actual': actual,
        'Base_Pred': np.round(base_preds, 2),
        'Q50': np.round(quantile_preds['Q50'], 2),
        'Q75': np.round(quantile_preds['Q75'], 2),
        'Q90_SafetyStock': np.round(quantile_preds['Q90'], 2),
        'Q95': np.round(quantile_preds['Q95'], 2),
        'Error': np.round(actual - base_preds, 2),
        'Shortage_Risk': [
            'HIGH' if actual[i] > quantile_preds['Q90'][i] else 'LOW'
            for i in range(len(actual))
        ]
    })

    print(results_df.to_string(index=False))
    print()

    # Analysis
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    # Compare shortage scenarios
    base_shortages = np.sum(actual > base_preds)
    q90_shortages = np.sum(actual > quantile_preds['Q90'])

    print(f"Base Model (Mean) Prediction:")
    print(f"  Shortages: {base_shortages}/10 ({base_shortages*10}%)")
    print(f"  Waste (avg): {np.mean(np.maximum(base_preds - actual, 0)):.2f} units")
    print()

    print(f"Q90 Safety Stock Recommendation:")
    print(f"  Shortages: {q90_shortages}/10 ({q90_shortages*10}%)")
    print(f"  Surplus (avg): {np.mean(np.maximum(quantile_preds['Q90'] - actual, 0)):.2f} units")
    print()

    print("Interpretation:")
    print(f"  - By using Q90 instead of mean: {base_shortages - q90_shortages} fewer shortages")
    print(f"  - Trade-off: Additional ~{np.mean(np.maximum(quantile_preds['Q90'] - actual, 0)):.1f} units surplus")
    print()

    # Business impact
    shortage_reduction = ((base_shortages - q90_shortages) / base_shortages * 100) if base_shortages > 0 else 0
    print("Business Impact:")
    print(f"  - Shortage rate reduction: {shortage_reduction:.0f}%")
    print(f"  - Recommended strategy: Use Q90 for safe stock, Q50 for base planning")
    print()


if __name__ == "__main__":
    main()
