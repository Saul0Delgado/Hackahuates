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
    print("  1. Run Bayesian hyperparameter optimization (300 trials, ~90 minutes)")
    print("  2. Train optimized XGBoost model with best hyperparameters")
    print("  3. Train Q90 safety stock model")
    print()

    try:
        best_model_name, best_model = pipeline.run(
            reload_data=False,
            optimize_hyperparams=True,  # Enable Bayesian optimization (300 trials)
            train_quantiles=True        # Train Q90 safety stock model
        )

        print()
        print("=" * 80)
        print("TRAINING COMPLETE")
        print("=" * 80)
        print()
        print(f"Best Model: {best_model_name}")
        print()
        print("Model saved to: data/models/xgboost.pkl")
        print("Q90 safety stock model saved to: data/models/xgboost_quantiles.pkl")
        print()
        print("Features:")
        print("  - Optimized hyperparameters (300-trial Bayesian optimization)")
        print("  - Q90 quantile model for safety stock recommendations")
        print()

    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
