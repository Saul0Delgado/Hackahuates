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
    q90_preds = base_model.predict_quantiles(X_test[:10])
    actual = y_test.iloc[:10].values

    # Display results
    print("\n" + "=" * 80)
    print("Q90 SAFETY STOCK PREDICTION (First 10 test samples)")
    print("=" * 80)
    print()

    results_df = pd.DataFrame({
        'Actual': actual,
        'Base_Pred': np.round(base_preds, 2),
        'Q90_SafetyStock': np.round(q90_preds, 2),
        'Safety_Margin': np.round(q90_preds - base_preds, 2),
        'Shortage': [
            'YES' if actual[i] > q90_preds[i] else 'NO'
            for i in range(len(actual))
        ]
    })

    print(results_df.to_string(index=False))
    print()

    # Analysis
    print("=" * 80)
    print("Q90 SAFETY STOCK ANALYSIS")
    print("=" * 80)
    print()

    # Compare shortage scenarios
    base_shortages = np.sum(actual > base_preds)
    q90_shortages = np.sum(actual > q90_preds)

    print(f"Base Model (Mean) Prediction:")
    print(f"  Shortages: {base_shortages}/10 ({base_shortages*10}%)")
    print(f"  Waste (avg): {np.mean(np.maximum(base_preds - actual, 0)):.2f} units")
    print()

    print(f"Q90 Safety Stock:")
    print(f"  Shortages: {q90_shortages}/10 ({q90_shortages*10}%)")
    print(f"  Surplus (avg): {np.mean(np.maximum(q90_preds - actual, 0)):.2f} units")
    print()

    # Business impact
    shortage_reduction = ((base_shortages - q90_shortages) / base_shortages * 100) if base_shortages > 0 else 0
    print("Impact:")
    print(f"  - Shortage reduction: {shortage_reduction:.0f}%")
    print(f"  - Using Q90 for safety stock ensures ~90% demand fulfillment")
    print()


if __name__ == "__main__":
    main()
