"""
Prediction service - handles model loading and inference
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List
from datetime import datetime

from ..utils import logger, load_config, get_project_root, get_data_path
from ..feature_engineering import FeatureEngineer
from ..models import XGBoostConsumptionModel, RandomForestConsumptionModel, EnsembleConsumptionModel


class PredictionService:
    """
    Service for making predictions using trained models
    """

    # Product ID mapping (numeric ID to actual Product_ID)
    PRODUCT_ID_MAP = {
        1: 'BRD001',
        2: 'CHO050',
        3: 'COF200',
        4: 'CRK075',
        5: 'DRK023',
        6: 'DRK024',
        7: 'HTB110',
        8: 'JCE200',
        9: 'NUT030',
        10: 'SNK001'
    }

    # Flight type mapping (frontend values to training values)
    FLIGHT_TYPE_MAP = {
        'INTERNATIONAL': 'long-haul',
        'DOMESTIC': 'short-haul',
        'SHORT_HAUL': 'short-haul',
        'MEDIUM_HAUL': 'medium-haul',
        'LONG_HAUL': 'long-haul',
        # Already correct values
        'long-haul': 'long-haul',
        'medium-haul': 'medium-haul',
        'short-haul': 'short-haul'
    }

    # Service type mapping (frontend values to training values)
    SERVICE_TYPE_MAP = {
        'ECONOMY': 'Retail',
        'BUSINESS': 'Retail',
        'FIRST_CLASS': 'Retail',
        'PREMIUM_ECONOMY': 'Retail',
        'PICK_AND_PACK': 'Pick & Pack',
        # Already correct values
        'Retail': 'Retail',
        'Pick & Pack': 'Pick & Pack'
    }

    def __init__(self, model_name: str = "xgboost"):
        """
        Initialize prediction service

        Args:
            model_name: Name of model to use (xgboost, ensemble, random_forest)
        """
        self.config = load_config()
        self.model_name = model_name
        self.model = None
        self.feature_engineer = None
        self.all_models = {}
        self.train_df = None  # Reference training data for aggregations

        # Load models
        self._load_models()

    def _load_models(self) -> None:
        """Load all trained models"""
        try:
            logger.info(f"Loading models...")

            # Load XGBoost
            try:
                self.all_models['xgboost'] = XGBoostConsumptionModel()
                self.all_models['xgboost'].load()
                logger.info("XGBoost model loaded")
            except Exception as e:
                logger.error(f"Failed to load XGBoost: {e}")

            # Load Random Forest
            try:
                self.all_models['random_forest'] = RandomForestConsumptionModel()
                self.all_models['random_forest'].load()
                logger.info("Random Forest model loaded")
            except Exception as e:
                logger.error(f"Failed to load Random Forest: {e}")

            # Load Ensemble
            try:
                self.all_models['ensemble'] = EnsembleConsumptionModel()
                self.all_models['ensemble'].load()
                logger.info("Ensemble model loaded")
            except Exception as e:
                logger.error(f"Failed to load Ensemble: {e}")

            # Set primary model
            if self.model_name in self.all_models:
                self.model = self.all_models[self.model_name]
            else:
                # Fallback to XGBoost if available
                if 'xgboost' in self.all_models:
                    self.model = self.all_models['xgboost']
                    self.model_name = 'xgboost'
                    logger.warning(f"Model {self.model_name} not found, using xgboost")
                else:
                    raise RuntimeError("No models could be loaded")

            # Load feature engineer
            self.feature_engineer = FeatureEngineer()
            self.feature_engineer.load_encoders()

            # Load reference training data for aggregations
            try:
                train_path = get_data_path("data/processed/train.csv")
                if train_path.exists():
                    self.train_df = pd.read_csv(train_path)
                    logger.info(f"Loaded reference training data: {len(self.train_df)} rows")
                else:
                    logger.warning("Training data not found, predictions may have feature mismatches")
            except Exception as e:
                logger.warning(f"Could not load training data: {e}")

            logger.info(f"Using {self.model_name} for predictions")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def predict_single(self, passenger_count: int, product_id: int,
                       flight_type: str, service_type: str, origin: str,
                       unit_cost: float, flight_date: Optional[str] = None) -> Dict:
        """
        Make a single product prediction

        Args:
            passenger_count: Number of passengers
            product_id: Product ID (numeric 1-10 or string like 'BRD001')
            flight_type: Flight type (DOMESTIC, INTERNATIONAL, CHARTER)
            service_type: Service type (ECONOMY, BUSINESS)
            origin: Origin city/code
            unit_cost: Unit cost in USD
            flight_date: Flight date (YYYY-MM-DD)

        Returns:
            Dictionary with prediction and confidence intervals
        """
        try:
            # Convert numeric product_id to actual Product_ID if needed
            if isinstance(product_id, int) and product_id in self.PRODUCT_ID_MAP:
                actual_product_id = self.PRODUCT_ID_MAP[product_id]
            else:
                actual_product_id = product_id  # Already a string or use as-is

            # Map flight_type and service_type to training values
            actual_flight_type = self.FLIGHT_TYPE_MAP.get(flight_type.upper(), flight_type)
            actual_service_type = self.SERVICE_TYPE_MAP.get(service_type.upper(), service_type)

            # Create input dataframe
            input_data = pd.DataFrame({
                'Passenger_Count': [passenger_count],
                'Product_ID': [actual_product_id],
                'Flight_Type': [actual_flight_type],
                'Service_Type': [actual_service_type],
                'Origin': [origin],
                'Unit_Cost': [unit_cost],
                'Consumption_Qty': [passenger_count],  # Placeholder for feature engineering
                'Standard_Specification_Qty': [passenger_count],  # Required for feature engineering
                'Date': [flight_date if flight_date else datetime.now().strftime('%Y-%m-%d')],
                'waste_qty': [0],  # Placeholder
                'overage_qty': [0],  # Placeholder
            })

            # Transform features using training data for aggregations
            X, _ = self.feature_engineer.transform(input_data, train_df=self.train_df, fit=False)

            # Get predictions with confidence intervals
            prediction, lower, upper = self.model.predict_with_confidence(X)

            # Calculate business metrics
            predicted_qty = float(prediction[0])
            waste_expected = max(0, predicted_qty - passenger_count)
            shortage_prob = 0.0 if predicted_qty >= passenger_count else 0.10

            result = {
                'predicted_quantity': predicted_qty,
                'lower_bound': float(lower[0]),
                'upper_bound': float(upper[0]),
                'confidence_score': 0.9898,  # From XGBoost R² on test set
                'expected_waste': waste_expected,
                'expected_shortage': shortage_prob,
                'model_used': self.model_name
            }

            return result

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise

    def predict_batch(self, passenger_count: int, flight_type: str,
                      service_type: str, origin: str, flight_date: Optional[str] = None,
                      products: Optional[List[int]] = None) -> Dict:
        """
        Make batch predictions for an entire flight

        Args:
            passenger_count: Total passenger count
            flight_type: Flight type
            service_type: Service type
            origin: Origin city/code
            flight_date: Flight date
            products: List of product IDs to predict (if None, predicts all)

        Returns:
            Dictionary with batch predictions
        """
        try:
            if products is None:
                products = list(range(1, 11))  # All 10 products

            predictions = []
            total_quantity = 0
            total_cost = 0
            total_waste_cost = 0

            flight_id = self._generate_flight_id(origin, flight_type, flight_date)

            for product_id in products:
                # Get unit cost for this product (from config or default)
                unit_cost = self.config['business_rules'].get('unit_costs', {}).get(
                    f'product_{product_id}', 0.75
                )

                # Make prediction
                pred_result = self.predict_single(
                    passenger_count, product_id, flight_type,
                    service_type, origin, unit_cost, flight_date
                )

                predictions.append({
                    'product_id': product_id,
                    'predicted_quantity': pred_result['predicted_quantity'],
                    'lower_bound': pred_result['lower_bound'],
                    'upper_bound': pred_result['upper_bound'],
                    'confidence_score': pred_result['confidence_score'],
                    'expected_waste': pred_result['expected_waste']
                })

                # Accumulate totals
                total_quantity += pred_result['predicted_quantity']
                total_cost += pred_result['predicted_quantity'] * unit_cost
                total_waste_cost += pred_result['expected_waste'] * unit_cost

            result = {
                'flight_id': flight_id,
                'passenger_count': passenger_count,
                'total_predicted_cost': total_cost,
                'total_predicted_waste_cost': total_waste_cost,
                'total_predicted_quantity': total_quantity,
                'predictions': predictions,
                'model_used': self.model_name,
                'generated_at': datetime.utcnow().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error making batch prediction: {e}")
            raise

    def get_feature_importance(self, top_n: int = 10) -> Dict:
        """
        Get feature importance for the current model

        Args:
            top_n: Number of top features to return

        Returns:
            Dictionary with feature importances
        """
        try:
            importance = self.model.get_feature_importance(top_n=top_n)

            result = {
                'model': self.model_name,
                'top_features': importance if importance else {},
                'total_features': 32  # Total features in the model
            }

            return result

        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            raise

    def get_model_metrics(self) -> Dict:
        """
        Get model performance metrics

        Returns:
            Dictionary with model metrics
        """
        # Hardcoded from training results
        metrics_store = {
            'xgboost': {
                'ml_metrics': {
                    'MAE': 3.15,
                    'RMSE': 5.10,
                    'MAPE': 3.04,
                    'R2': 0.9898
                },
                'business_metrics': {
                    'waste_rate_%': 1.18,
                    'shortage_rate_%': 58.82,
                    'accuracy_rate_%': 79.83,
                    'avg_waste_qty': 0.85
                }
            },
            'ensemble': {
                'ml_metrics': {
                    'MAE': 4.06,
                    'RMSE': 6.43,
                    'MAPE': 3.98,
                    'R2': 0.9839
                },
                'business_metrics': {
                    'waste_rate_%': 1.81,
                    'shortage_rate_%': 55.46,
                    'accuracy_rate_%': 71.43,
                    'avg_waste_qty': 1.26
                }
            },
            'random_forest': {
                'ml_metrics': {
                    'MAE': 6.92,
                    'RMSE': 10.06,
                    'MAPE': 7.19,
                    'R2': 0.9605
                },
                'business_metrics': {
                    'waste_rate_%': 3.60,
                    'shortage_rate_%': 48.74,
                    'accuracy_rate_%': 55.46,
                    'avg_waste_qty': 2.58
                }
            }
        }

        metrics = metrics_store.get(self.model_name, metrics_store['xgboost'])

        result = {
            'model': self.model_name,
            'training_date': '2025-10-25',
            'ml_metrics': metrics['ml_metrics'],
            'business_metrics': metrics['business_metrics']
        }

        return result

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.all_models.keys())

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model

        Args:
            model_name: Name of model to switch to

        Returns:
            True if successful, False otherwise
        """
        if model_name in self.all_models:
            self.model = self.all_models[model_name]
            self.model_name = model_name
            logger.info(f"Switched to {model_name} model")
            return True
        else:
            logger.error(f"Model {model_name} not available")
            return False

    @staticmethod
    def _generate_flight_id(origin: str, flight_type: str, flight_date: Optional[str] = None) -> str:
        """
        Generate a unique flight ID

        Args:
            origin: Origin city/code
            flight_type: Flight type
            flight_date: Flight date

        Returns:
            Generated flight ID
        """
        if flight_date is None:
            flight_date = datetime.now().strftime('%Y-%m-%d')

        flight_type_abbr = flight_type[0:3].upper()
        import random
        seq = random.randint(1, 999)

        return f"{flight_type_abbr}-{origin}-{flight_date}-{seq:03d}"
