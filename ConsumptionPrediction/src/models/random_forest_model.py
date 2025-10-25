"""
Random Forest model for consumption prediction
"""

import pandas as pd
import numpy as np
from typing import Dict
from sklearn.ensemble import RandomForestRegressor

from ..utils import logger, load_config
from .base_model import BaseConsumptionModel


class RandomForestConsumptionModel(BaseConsumptionModel):
    """
    Random Forest model for consumption prediction
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize Random Forest model

        Args:
            config_path: Path to configuration file
        """
        super().__init__("random_forest")

        config = load_config(config_path)
        self.rf_config = config['models']['random_forest']
        self.params = self.rf_config['params'].copy()

        # Initialize model
        self.model = RandomForestRegressor(**self.params)
        self.feature_names = None
        self.feature_importance_dict = None

    def train(self, X: pd.DataFrame, y: pd.Series, verbose: bool = True) -> None:
        """
        Train Random Forest model

        Args:
            X: Training features
            y: Training target
            verbose: Whether to print training progress
        """
        logger.info(f"Training {self.name}...")

        self.feature_names = X.columns.tolist()

        # Train model
        self.model.fit(X, y)

        self.is_fitted = True

        # Calculate feature importance
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

        return self.model.predict(X)

    def predict_with_confidence(self, X: pd.DataFrame) -> tuple:
        """
        Make predictions with confidence intervals

        Args:
            X: Feature matrix

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = self.predict(X)

        # Get per-tree predictions for confidence intervals
        tree_predictions = np.array([tree.predict(X) for tree in self.model.estimators_])

        # Calculate standard deviation across trees
        std_dev = np.std(tree_predictions, axis=0)

        # 95% confidence interval
        margin = 1.96 * std_dev

        lower = predictions - margin
        upper = predictions + margin

        return predictions, lower, upper

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

            return (f"{base_summary}\n"
                   f"  Features: {n_features}\n"
                   f"  Estimators: {n_estimators}\n"
                   f"  Max depth: {max_depth}")

        return base_summary
