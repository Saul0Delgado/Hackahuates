"""
ML Models for Consumption Prediction
"""

from .xgboost_model import XGBoostConsumptionModel
from .random_forest_model import RandomForestConsumptionModel
from .ensemble_model import EnsembleConsumptionModel

__all__ = [
    'XGBoostConsumptionModel',
    'RandomForestConsumptionModel',
    'EnsembleConsumptionModel'
]
