"""
Ensemble model combining XGBoost and Random Forest
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from ..utils import logger, load_config
from .base_model import BaseConsumptionModel
from .xgboost_model import XGBoostConsumptionModel
from .random_forest_model import RandomForestConsumptionModel


class EnsembleConsumptionModel(BaseConsumptionModel):
    """
    Ensemble model combining multiple models with weighted averaging
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize Ensemble model

        Args:
            config_path: Path to configuration file
        """
        super().__init__("ensemble")

        config = load_config(config_path)
        self.ensemble_config = config['models']['ensemble']
        self.weights = self.ensemble_config['weights']

        # Initialize component models
        self.xgb_model = XGBoostConsumptionModel(config_path)
        self.rf_model = RandomForestConsumptionModel(config_path)

        self.feature_names = None

    def train(self, X: pd.DataFrame, y: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None,
              verbose: bool = True) -> None:
        """
        Train ensemble model

        Args:
            X: Training features
            y: Training target
            X_val: Validation features
            y_val: Validation target
            verbose: Whether to print training progress
        """
        logger.info("Training Ensemble model...")

        self.feature_names = X.columns.tolist()

        # Train XGBoost
        logger.info("Training XGBoost component...")
        self.xgb_model.train(X, y, X_val, y_val, verbose=False)

        # Train Random Forest
        logger.info("Training Random Forest component...")
        self.rf_model.train(X, y, verbose=False)

        self.is_fitted = True

        if verbose:
            logger.info("Ensemble training complete")
            logger.info(f"  XGBoost weight: {self.weights['xgboost']}")
            logger.info(f"  Random Forest weight: {self.weights['random_forest']}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using weighted ensemble

        Args:
            X: Feature matrix

        Returns:
            Predictions array
        """
        if not self.is_fitted:
            raise ValueError("Ensemble model is not fitted yet")

        # Get predictions from each model
        xgb_pred = self.xgb_model.predict(X)
        rf_pred = self.rf_model.predict(X)

        # Weighted average
        ensemble_pred = (
            self.weights['xgboost'] * xgb_pred +
            self.weights['random_forest'] * rf_pred
        )

        return ensemble_pred

    def predict_with_confidence(self, X: pd.DataFrame) -> tuple:
        """
        Make predictions with confidence intervals

        Args:
            X: Feature matrix

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        # Get predictions and confidence from both models
        xgb_pred, xgb_lower, xgb_upper = self.xgb_model.predict_with_confidence(X)
        rf_pred, rf_lower, rf_upper = self.rf_model.predict_with_confidence(X)

        # Ensemble predictions
        predictions = self.predict(X)

        # Ensemble confidence intervals
        lower = (
            self.weights['xgboost'] * xgb_lower +
            self.weights['random_forest'] * rf_lower
        )

        upper = (
            self.weights['xgboost'] * xgb_upper +
            self.weights['random_forest'] * rf_upper
        )

        return predictions, lower, upper

    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """
        Get ensemble feature importance (weighted average)

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary of feature importances
        """
        xgb_importance = self.xgb_model.get_feature_importance(top_n=None)
        rf_importance = self.rf_model.get_feature_importance(top_n=None)

        if xgb_importance is None or rf_importance is None:
            return None

        # Normalize importances
        xgb_sum = sum(xgb_importance.values())
        rf_sum = sum(rf_importance.values())

        xgb_norm = {k: v / xgb_sum for k, v in xgb_importance.items()}
        rf_norm = {k: v / rf_sum for k, v in rf_importance.items()}

        # Weighted ensemble importance
        ensemble_importance = {}
        all_features = set(xgb_norm.keys()) | set(rf_norm.keys())

        for feature in all_features:
            importance = (
                self.weights['xgboost'] * xgb_norm.get(feature, 0) +
                self.weights['random_forest'] * rf_norm.get(feature, 0)
            )
            ensemble_importance[feature] = importance

        # Sort and get top N
        sorted_features = sorted(
            ensemble_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return dict(sorted_features[:top_n])

    def summary(self) -> str:
        """
        Get model summary

        Returns:
            Model summary string
        """
        base_summary = super().summary()

        if self.is_fitted:
            n_features = len(self.feature_names) if self.feature_names else 0

            return (f"{base_summary}\n"
                   f"  Features: {n_features}\n"
                   f"  Component models: XGBoost (70%), Random Forest (30%)")

        return base_summary
