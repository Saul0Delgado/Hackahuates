"""
Script to run Bayesian hyperparameter optimization for XGBoost
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.data_loader import ConsumptionDataLoader
from src.feature_engineering import FeatureEngineer
from src.hyperparameter_optimization import HyperparameterOptimizer, SafetyStockOptimizer
from src.utils import logger


def main():
    """Run hyperparameter optimization"""

    logger.info("\n" + "=" * 80)
    logger.info("HYPERPARAMETER OPTIMIZATION FOR XGBOOST")
    logger.info("=" * 80)

    # 1. Load data
    logger.info("\n[STEP 1] Loading data...")
    data_loader = ConsumptionDataLoader()
    train_df, val_df, test_df = data_loader.load_and_prepare(save=False)
    logger.info(f"  Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # 2. Engineer features
    logger.info("\n[STEP 2] Engineering features...")
    feature_engineer = FeatureEngineer()
    X_train, y_train = feature_engineer.transform(train_df, fit=True)
    X_val, y_val = feature_engineer.transform(val_df, fit=False)
    X_test, y_test = feature_engineer.transform(test_df, fit=False)
    logger.info(f"  Features: {X_train.shape[1]}")

    # 3. Run Bayesian optimization
    logger.info("\n[STEP 2] Running Bayesian Optimization...")
    optimizer = HyperparameterOptimizer()

    optimization_results = optimizer.optimize(
        X_train, y_train, X_val, y_val,
        n_trials=100,
        timeout=3600  # 1 hour timeout
    )

    # 4. Display results
    logger.info("\n" + "=" * 80)
    logger.info("OPTIMIZATION RESULTS")
    logger.info("=" * 80)

    logger.info(f"\nBest MAE: {optimization_results['best_score']:.4f}")
    logger.info(f"Number of trials: {optimization_results['num_trials']}")
    logger.info("\nBest Hyperparameters:")
    for param, value in optimization_results['best_params'].items():
        if isinstance(value, float):
            logger.info(f"  {param}: {value:.6f}")
        else:
            logger.info(f"  {param}: {value}")

    # 5. Save optimization results
    results_file = Path(__file__).parent.parent / "optimization_results.json"
    with open(results_file, 'w') as f:
        # Convert best_params to JSON-serializable format
        best_params_json = {}
        for k, v in optimization_results['best_params'].items():
            if isinstance(v, np.integer):
                best_params_json[k] = int(v)
            elif isinstance(v, np.floating):
                best_params_json[k] = float(v)
            else:
                best_params_json[k] = v

        json.dump({
            'best_score': float(optimization_results['best_score']),
            'best_params': best_params_json,
            'num_trials': optimization_results['num_trials']
        }, f, indent=2)

    logger.info(f"\nResults saved to: {results_file}")

    # 6. Train quantile models for safety stock
    logger.info("\n[STEP 3] Training Quantile Ensemble...")
    safety_optimizer = SafetyStockOptimizer()
    safety_optimizer.train_quantile_ensemble(X_train, y_train, X_val, y_val)

    logger.info("\n" + "=" * 80)
    logger.info("OPTIMIZATION COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Review optimization_results.json")
    logger.info("2. Update config.yaml with best hyperparameters")
    logger.info("3. Retrain XGBoost with optimized parameters")
    logger.info("4. Evaluate on test set")


if __name__ == "__main__":
    main()
