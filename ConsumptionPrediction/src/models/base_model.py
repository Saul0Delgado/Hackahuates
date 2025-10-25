"""
Base model class for consumption prediction
"""

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import joblib
from pathlib import Path

from ..utils import logger, get_data_path


class BaseConsumptionModel(ABC):
    """
    Abstract base class for consumption prediction models
    """

    def __init__(self, name: str):
        """
        Initialize base model

        Args:
            name: Model name
        """
        self.name = name
        self.model = None
        self.is_fitted = False

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Train the model

        Args:
            X: Feature matrix
            y: Target vector
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Feature matrix

        Returns:
            Predictions array
        """
        pass

    def predict_with_confidence(self, X: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Make predictions with confidence intervals

        Args:
            X: Feature matrix

        Returns:
            Tuple of (predictions, confidence)
        """
        predictions = self.predict(X)
        confidence = None  # Override in subclasses if available

        return predictions, confidence

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model on test data

        Args:
            X: Feature matrix
            y: Target vector

        Returns:
            Dictionary of metrics
        """
        from ..evaluation import Evaluator

        y_pred = self.predict(X)
        evaluator = Evaluator()
        metrics = evaluator.calculate_metrics(y, y_pred)

        return metrics

    def save(self, path: str = None) -> str:
        """
        Save model to disk

        Args:
            path: Save path (default: data/models/{model_name}.pkl)

        Returns:
            Path where model was saved
        """
        if path is None:
            path = f"data/models/{self.name}.pkl"

        save_path = get_data_path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self, save_path)
        logger.info(f"Saved {self.name} to {save_path}")

        # Also save quantile models if they exist
        if hasattr(self, 'quantile_models') and self.quantile_models:
            quantile_path = f"data/models/{self.name}_quantiles.pkl"
            quantile_save_path = get_data_path(quantile_path)
            joblib.dump(self.quantile_models, quantile_save_path)
            logger.info(f"Saved quantile models to {quantile_save_path}")

        return str(save_path)

    def load(self, path: str = None) -> None:
        """
        Load model from disk

        Args:
            path: Load path (default: data/models/{model_name}.pkl)
        """
        if path is None:
            path = f"data/models/{self.name}.pkl"

        load_path = get_data_path(path)
        self.model = joblib.load(load_path)
        self.is_fitted = True

        logger.info(f"Loaded {self.name} from {load_path}")

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance (if available)

        Returns:
            Dictionary of feature importances or None
        """
        return None

    def summary(self) -> str:
        """
        Get model summary

        Returns:
            Model summary string
        """
        status = "Fitted ✓" if self.is_fitted else "Not fitted"
        return f"{self.name} ({status})"
