"""
XGBoost model for consumption prediction with Bayesian optimization and quantile regression
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import xgboost as xgb
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from ..utils import logger, load_config
from .base_model import BaseConsumptionModel


class XGBoostConsumptionModel(BaseConsumptionModel):
    """
    XGBoost model for consumption prediction with quantile regression support
    """

    def __init__(self, config_path: str = "config/config.yaml", quantile: Optional[float] = None):
        """
        Initialize XGBoost model

        Args:
            config_path: Path to configuration file
            quantile: Optional quantile value (0.0-1.0) for quantile regression
        """
        super().__init__("xgboost")

        config = load_config(config_path)
        self.xgb_config = config['models']['xgboost']
        self.params = self.xgb_config['params'].copy()
        self.quantile = quantile

        # If quantile specified, use quantile objective
        if quantile is not None:
            self.params['objective'] = 'reg:quantileerror'
            self.params['quantile_alpha'] = quantile
            self.name = f"xgboost_q{int(quantile*100)}"

        # Initialize model
        self.model = xgb.XGBRegressor(**self.params, verbosity=0)
        self.feature_names = None
        self.feature_importance_dict = None
        self.quantile_models = {}  # Store quantile models

    def train(self, X: pd.DataFrame, y: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None,
              verbose: bool = True, early_stopping_rounds: int = 20) -> None:
        """
        Train XGBoost model with early stopping

        Args:
            X: Training features
            y: Training target
            X_val: Validation features
            y_val: Validation target
            verbose: Whether to print training progress
            early_stopping_rounds: Early stopping rounds
        """
        logger.info(f"Training {self.name}...")

        self.feature_names = X.columns.tolist()

        # Train with early stopping
        if X_val is not None and y_val is not None:
            self.model.fit(
                X, y,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X, y, verbose=False)

        self.is_fitted = True
        self._calculate_feature_importance(X.columns)

        if verbose:
            logger.info(f"{self.name} training complete")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Feature matrix

        Returns:
            Predictions array
        """
        if not self.is_fitted:
            raise ValueError(f"{self.name} is not fitted yet")

        # Ensure X has the same columns as training data
        if hasattr(self.model, 'feature_names_in_'):
            expected_features = self.model.feature_names_in_
            X = X.copy()

            # Add missing columns with 0
            for feature in expected_features:
                if feature not in X.columns:
                    X[feature] = 0

            # Remove extra columns
            X = X[expected_features]

        return self.model.predict(X)

    def predict_with_confidence(self, X: pd.DataFrame, percentile: float = 0.95) -> tuple:
        """
        Make predictions with confidence intervals

        Args:
            X: Feature matrix
            percentile: Confidence level (0.95 = 95%)

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = self.predict(X)

        # Calculate margin using 1.96 for 95% CI
        std_dev = np.std(predictions)
        margin = 1.96 * std_dev

        lower = np.maximum(predictions - margin, 0)
        upper = predictions + margin

        return predictions, lower, upper

    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series,
                                X_val: pd.DataFrame, y_val: pd.Series,
                                n_trials: int = 50, verbose: bool = True) -> Dict:
        """
        Bayesian hyperparameter optimization using Optuna

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            n_trials: Number of optimization trials
            verbose: Whether to print progress

        Returns:
            Dictionary with best parameters and score
        """
        if verbose:
            logger.info(f"Starting Bayesian hyperparameter optimization ({n_trials} trials)...")

        def objective(trial):
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

            try:
                model = xgb.XGBRegressor(**params, verbosity=0, random_state=42)
                model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

                y_pred = model.predict(X_val)
                from sklearn.metrics import mean_absolute_error
                mae = mean_absolute_error(y_val, y_pred)

                return mae
            except Exception as e:
                return float('inf')

        sampler = TPESampler(seed=42)
        pruner = MedianPruner()
        study = optuna.create_study(sampler=sampler, pruner=pruner, direction='minimize')

        study.optimize(objective, n_trials=n_trials, show_progress_bar=verbose)

        best_params = study.best_params
        best_score = study.best_value

        if verbose:
            logger.info(f"Best MAE: {best_score:.4f}")
            logger.info("Best Parameters:")
            for param, value in best_params.items():
                logger.info(f"  {param}: {value}")

        # Update model parameters
        self.params.update(best_params)
        self.model = xgb.XGBRegressor(**self.params, verbosity=0)

        return {'best_params': best_params, 'best_score': best_score}

    def _calculate_feature_importance(self, feature_names) -> None:
        """
        Calculate and store feature importance

        Args:
            feature_names: List of feature names
        """
        try:
            importances = self.model.feature_importances_
            self.feature_importance_dict = {
                name: importance
                for name, importance in zip(feature_names, importances)
            }
        except AttributeError:
            logger.warning("Could not extract feature importance from model")

    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """
        Get top feature importances

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary of feature importances
        """
        if self.feature_importance_dict is None:
            return None

        # Sort by importance and get top N
        sorted_features = sorted(
            self.feature_importance_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return dict(sorted_features[:top_n])

    def train_quantile_ensemble(self, X_train: pd.DataFrame, y_train: pd.Series,
                               X_val: pd.DataFrame, y_val: pd.Series,
                               quantiles: list = None, verbose: bool = True) -> Dict:
        """
        Train ensemble of quantile models for safety stock prediction

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            quantiles: List of quantiles to train (default: [0.50, 0.75, 0.90, 0.95])
            verbose: Whether to print progress

        Returns:
            Dictionary of trained quantile models
        """
        if quantiles is None:
            quantiles = [0.50, 0.75, 0.90, 0.95]

        if verbose:
            logger.info(f"Training quantile ensemble for shortage mitigation...")

        self.quantile_models = {}

        for quantile in quantiles:
            if verbose:
                logger.info(f"  Training Q{int(quantile*100)} model...")

            q_model = XGBoostConsumptionModel(quantile=quantile)
            q_model.train(X_train, y_train, X_val, y_val, verbose=False)
            self.quantile_models[quantile] = q_model

        if verbose:
            logger.info(f"Quantile ensemble training complete")
            logger.info(f"Available quantiles: {list(self.quantile_models.keys())}")

        return self.quantile_models

    def predict_quantiles(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Get quantile predictions for confidence intervals and safety stock

        Args:
            X: Feature matrix

        Returns:
            Dictionary with quantile predictions
        """
        if not self.quantile_models:
            raise ValueError("Quantile models not trained. Call train_quantile_ensemble first.")

        predictions = {}
        for quantile, model in self.quantile_models.items():
            predictions[f'Q{int(quantile*100)}'] = model.predict(X)

        return predictions

    def get_safety_stock_recommendation(self, X: pd.DataFrame, percentile: float = 90) -> np.ndarray:
        """
        Get safety stock recommendation using quantile prediction

        Args:
            X: Feature matrix
            percentile: Percentile to use for safety stock (default 90)

        Returns:
            Recommended quantities with safety buffer
        """
        quantile_key = percentile / 100
        if quantile_key not in self.quantile_models:
            raise ValueError(f"Quantile {percentile} not available. Train with train_quantile_ensemble first.")

        return self.quantile_models[quantile_key].predict(X)

    def summary(self) -> str:
        """
        Get model summary

        Returns:
            Model summary string
        """
        base_summary = super().summary()

        if self.is_fitted:
            n_features = len(self.feature_names) if self.feature_names else 0
            n_estimators = self.params.get('n_estimators', 'unknown')
            max_depth = self.params.get('max_depth', 'unknown')
            quantile_info = f" (Quantile: {self.quantile})" if self.quantile else ""

            info = (f"{base_summary}{quantile_info}\n"
                   f"  Features: {n_features}\n"
                   f"  Estimators: {n_estimators}\n"
                   f"  Max depth: {max_depth}")

            if self.quantile_models:
                quantiles = list(self.quantile_models.keys())
                info += f"\n  Quantile ensemble: {[f'Q{int(q*100)}' for q in quantiles]}"

            return info

        return base_summary
