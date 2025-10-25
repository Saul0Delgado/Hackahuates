"""
Script to train XGBoost with Bayesian optimization and quantile regression
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from src.training import TrainingPipeline
from src.utils import logger


def main():
    """Run optimized training pipeline"""

    print("\n" + "=" * 80)
    print("ADVANCED XGBOOST TRAINING: BAYESIAN OPTIMIZATION + QUANTILES")
    print("=" * 80)
    print()

    pipeline = TrainingPipeline()

    # Run with both optimizations
    print("This will:")
    print("  1. Run Bayesian hyperparameter optimization (50 trials, ~15 minutes)")
    print("  2. Train optimized XGBoost model")
    print("  3. Train quantile ensemble (Q50, Q75, Q90, Q95) for safety stock")
    print()

    try:
        # Run with 100 trials for Bayesian optimization (increased from 50)
        best_model_name, best_model = pipeline.run(
            reload_data=False,
            optimize_hyperparams=True,  # Enable Bayesian optimization (100 trials)
            train_quantiles=True        # Enable quantile ensemble
        )

        print()
        print("=" * 80)
        print("TRAINING COMPLETE")
        print("=" * 80)
        print()
        print(f"Best Model: {best_model_name}")
        print()
        print("Model saved to: data/models/xgboost.pkl")
        print()
        print("New Features:")
        print("  - Optimized hyperparameters (via Bayesian search)")
        print("  - Quantile predictions (Q50, Q75, Q90, Q95)")
        print("  - Safety stock recommendations (Q90)")
        print()
        print("Expected Improvements:")
        print("  - MAE reduction: ~9% (3.15 → 2.87)")
        print("  - Shortage rate reduction: ~50% (58.82% → ~10-20%)")
        print()

    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
