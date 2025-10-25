"""
Bayesian hyperparameter optimization for XGBoost using Optuna
"""

import pandas as pd
import numpy as np
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from typing import Dict, Tuple, Callable
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .utils import logger, load_config


class HyperparameterOptimizer:
    """
    Bayesian hyperparameter optimization for XGBoost models
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize optimizer

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.xgb_config = self.config['models']['xgboost']
        self.study = None
        self.best_params = None
        self.best_score = None

    def objective(self, trial: optuna.Trial, X_train: pd.DataFrame,
                  y_train: pd.Series, X_val: pd.DataFrame,
                  y_val: pd.Series) -> float:
        """
        Objective function for Optuna to minimize

        Args:
            trial: Optuna trial object
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target

        Returns:
            Validation MAE (to minimize)
        """
        # Suggest hyperparameters
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=50),
            'max_depth': trial.suggest_int('max_depth', 3, 15),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_weight': trial.suggest_float('min_child_weight', 0.5, 10.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 5.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 5.0),
            'gamma': trial.suggest_float('gamma', 0.0, 5.0),
        }

        # Train model with suggested parameters
        try:
            model = xgb.XGBRegressor(
                **params,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )

            # Train with early stopping
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=20,
                verbose=False
            )

            # Predict on validation set
            y_pred = model.predict(X_val)

            # Calculate validation MAE
            mae = mean_absolute_error(y_val, y_pred)

            return mae

        except Exception as e:
            logger.warning(f"Trial failed: {e}")
            return float('inf')

    def optimize(self, X_train: pd.DataFrame, y_train: pd.Series,
                 X_val: pd.DataFrame, y_val: pd.Series,
                 n_trials: int = 150, timeout: int = 3600) -> Dict:
        """
        Run Bayesian optimization

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            n_trials: Number of trials to run
            timeout: Timeout in seconds

        Returns:
            Dictionary with best parameters and score
        """
        logger.info("=" * 80)
        logger.info("BAYESIAN HYPERPARAMETER OPTIMIZATION")
        logger.info("=" * 80)
        logger.info(f"Running {n_trials} optimization trials...")
        logger.info(f"Objective: Minimize Validation MAE")

        # Create study with Bayesian sampler (TPE)
        sampler = TPESampler(seed=42)
        pruner = MedianPruner()

        self.study = optuna.create_study(
            sampler=sampler,
            pruner=pruner,
            direction='minimize'
        )

        # Optimize
        self.study.optimize(
            lambda trial: self.objective(trial, X_train, y_train, X_val, y_val),
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True
        )

        # Get best parameters
        self.best_params = self.study.best_params
        self.best_score = self.study.best_value

        logger.info("\n" + "=" * 80)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Best MAE: {self.best_score:.4f}")
        logger.info("\nBest Hyperparameters:")
        for param, value in self.best_params.items():
            if isinstance(value, float):
                logger.info(f"  {param}: {value:.6f}")
            else:
                logger.info(f"  {param}: {value}")

        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'num_trials': len(self.study.trials),
            'trials': self.study.trials
        }

    def get_optimization_history(self) -> pd.DataFrame:
        """
        Get optimization history as DataFrame

        Returns:
            DataFrame with trial history
        """
        if self.study is None:
            return None

        trials_data = []
        for trial in self.study.trials:
            trials_data.append({
                'Trial': trial.number,
                'Value': trial.value,
                'State': trial.state.name,
                **trial.params
            })

        return pd.DataFrame(trials_data)

    def plot_optimization_history(self, save_path: str = None):
        """
        Plot optimization history

        Args:
            save_path: Path to save the plot (optional)
        """
        if self.study is None:
            logger.warning("No optimization study to plot")
            return

        try:
            import matplotlib.pyplot as plt

            trials = self.study.trials
            trial_numbers = [t.number for t in trials if t.value is not None]
            trial_values = [t.value for t in trials if t.value is not None]

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))

            # Plot 1: Optimization progress
            axes[0].plot(trial_numbers, trial_values, 'b-', alpha=0.6, marker='o')
            axes[0].set_xlabel('Trial Number')
            axes[0].set_ylabel('Validation MAE')
            axes[0].set_title('Optimization Progress')
            axes[0].grid(True, alpha=0.3)

            # Plot 2: Best value over time
            best_values = []
            best_so_far = float('inf')
            for val in trial_values:
                best_so_far = min(best_so_far, val)
                best_values.append(best_so_far)

            axes[1].plot(trial_numbers, best_values, 'g-', linewidth=2)
            axes[1].set_xlabel('Trial Number')
            axes[1].set_ylabel('Best Validation MAE')
            axes[1].set_title('Best Score Over Time')
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Optimization plot saved to {save_path}")

            plt.show()

        except Exception as e:
            logger.error(f"Failed to plot optimization history: {e}")


class QuantileXGBoostModel:
    """
    XGBoost model for quantile regression to predict confidence bounds
    """

    def __init__(self, quantile: float = 0.90, random_state: int = 42):
        """
        Initialize quantile model

        Args:
            quantile: Quantile to predict (0.0-1.0)
            random_state: Random seed
        """
        self.quantile = quantile
        self.random_state = random_state
        self.model = None
        self.is_fitted = False

    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None,
              verbose: bool = True) -> None:
        """
        Train quantile regression model

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            verbose: Whether to print progress
        """
        if verbose:
            logger.info(f"Training Quantile XGBoost (Q={self.quantile})...")

        params = {
            'objective': 'reg:quantilehubererror',
            'quantile_alpha': self.quantile,
            'n_estimators': 500,
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': self.random_state,
            'n_jobs': -1,
            'verbosity': 0
        }

        self.model = xgb.XGBRegressor(**params)

        # Train with early stopping if validation data provided
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=20,
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)

        self.is_fitted = True

        if verbose:
            logger.info(f"Quantile XGBoost training complete")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make quantile predictions

        Args:
            X: Features to predict on

        Returns:
            Predicted quantile values
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")

        return self.model.predict(X)

    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """
        Get feature importance

        Args:
            top_n: Number of top features

        Returns:
            Dictionary of feature importances
        """
        if not self.is_fitted:
            return None

        importances = self.model.feature_importances_
        feature_names = self.model.get_booster().feature_names

        importance_dict = {
            name: importance
            for name, importance in zip(feature_names, importances)
        }

        sorted_features = sorted(
            importance_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return dict(sorted_features[:top_n])


class SafetyStockOptimizer:
    """
    Optimize safety stock levels using multiple quantile models
    """

    def __init__(self):
        """Initialize optimizer"""
        self.models = {}
        self.quantiles = [0.50, 0.75, 0.90, 0.95]

    def train_quantile_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                               X_val: pd.DataFrame = None, y_val: pd.Series = None,
                               verbose: bool = True) -> Dict:
        """
        Train ensemble of quantile models

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            verbose: Whether to print progress

        Returns:
            Dictionary of trained models
        """
        if verbose:
            logger.info("=" * 80)
            logger.info("TRAINING QUANTILE ENSEMBLE FOR SAFETY STOCK")
            logger.info("=" * 80)

        for quantile in self.quantiles:
            if verbose:
                logger.info(f"\nTraining Q{int(quantile*100)} model...")

            model = QuantileXGBoostModel(quantile=quantile)
            model.train(X_train, y_train, X_val, y_val, verbose=False)
            self.models[quantile] = model

            if verbose:
                logger.info(f"Q{int(quantile*100)} model trained")

        if verbose:
            logger.info("\n" + "=" * 80)
            logger.info("QUANTILE ENSEMBLE TRAINING COMPLETE")
            logger.info("=" * 80)

        return self.models

    def predict_with_quantiles(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Make predictions with multiple quantiles

        Args:
            X: Features to predict on

        Returns:
            Dictionary with predictions for each quantile
        """
        predictions = {}
        for quantile, model in self.models.items():
            predictions[f'Q{int(quantile*100)}'] = model.predict(X)

        return predictions

    def get_recommended_quantity(self, X: pd.DataFrame, percentile: float = 90) -> np.ndarray:
        """
        Get recommended quantity based on quantile

        Args:
            X: Features
            percentile: Percentile to use (e.g., 90)

        Returns:
            Recommended quantities
        """
        quantile_key = f'Q{int(percentile)}'

        if percentile not in self.models:
            raise ValueError(f"Quantile {percentile} not available. "
                           f"Available: {list(self.models.keys())}")

        return self.models[percentile / 100].predict(X)
