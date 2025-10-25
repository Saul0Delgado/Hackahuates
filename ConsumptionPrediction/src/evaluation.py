"""
Model evaluation metrics and utilities
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .utils import logger


class Evaluator:
    """
    Evaluate model performance
    """

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate evaluation metrics

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Dictionary of metrics
        """
        # Handle pandas Series
        if isinstance(y_true, pd.Series):
            y_true = y_true.values
        if isinstance(y_pred, pd.Series):
            y_pred = y_pred.values

        # Ensure numpy arrays
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        # ML Metrics
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100  # Add small epsilon
        r2 = r2_score(y_true, y_pred)

        metrics = {
            'MAE': float(mae),
            'RMSE': float(rmse),
            'MAPE': float(mape),
            'R2': float(r2)
        }

        return metrics

    @staticmethod
    def calculate_business_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                                   unit_cost: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate business-oriented metrics

        Args:
            y_true: True consumption values
            y_pred: Predicted consumption values
            unit_cost: Unit cost of each product

        Returns:
            Dictionary of business metrics
        """
        # Handle pandas Series
        if isinstance(y_true, pd.Series):
            y_true = y_true.values
        if isinstance(y_pred, pd.Series):
            y_pred = y_pred.values
        if unit_cost is not None and isinstance(unit_cost, pd.Series):
            unit_cost = unit_cost.values

        # Ensure numpy arrays
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        # Waste calculation
        # y_pred represents optimal quantity, y_true is actual consumption
        # If we prepare y_pred and actual consumption is y_true:
        waste_qty = np.maximum(y_pred - y_true, 0)  # Items that weren't consumed
        waste_rate = np.mean(waste_qty / (y_pred + 1e-10)) * 100

        # Shortage calculation
        shortage_qty = np.maximum(y_true - y_pred, 0)  # Shortage if prediction too low
        shortage_rate = (shortage_qty > 0).sum() / len(y_true) * 100

        # Cost metrics
        cost_metrics = {}
        if unit_cost is not None:
            waste_cost = np.sum(waste_qty * unit_cost)
            cost_metrics['waste_cost_total'] = float(waste_cost)
            cost_metrics['waste_cost_avg'] = float(np.mean(waste_qty * unit_cost))

        # Accuracy metrics
        accuracy_rate = np.mean(np.abs(y_true - y_pred) <= 5) * 100  # Within 5 units

        metrics = {
            'waste_rate_%': float(waste_rate),
            'shortage_rate_%': float(shortage_rate),
            'accuracy_rate_%': float(accuracy_rate),
            'avg_waste_qty': float(np.mean(waste_qty)),
            'total_waste_qty': float(np.sum(waste_qty)),
            'avg_shortage_qty': float(np.mean(shortage_qty)),
            'total_shortage_qty': float(np.sum(shortage_qty))
        }

        metrics.update(cost_metrics)

        return metrics

    @staticmethod
    def compare_models(models_results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare multiple model results

        Args:
            models_results: Dictionary with model names and their results

        Returns:
            DataFrame with comparison
        """
        comparison_data = []

        for model_name, results in models_results.items():
            row = {'Model': model_name}
            row.update(results.get('metrics', {}))
            row.update(results.get('business_metrics', {}))
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)
        return df

    @staticmethod
    def print_evaluation_report(y_true: np.ndarray, y_pred: np.ndarray,
                               model_name: str = "Model",
                               unit_cost: np.ndarray = None) -> None:
        """
        Print formatted evaluation report

        Args:
            y_true: True values
            y_pred: Predicted values
            model_name: Name of the model
            unit_cost: Unit costs (optional)
        """
        metrics = Evaluator.calculate_metrics(y_true, y_pred)
        business_metrics = Evaluator.calculate_business_metrics(y_true, y_pred, unit_cost)

        print("\n" + "="*80)
        print(f"EVALUATION REPORT: {model_name}")
        print("="*80)

        print("\nML Metrics:")
        print(f"  MAE:   {metrics['MAE']:.2f} units")
        print(f"  RMSE:  {metrics['RMSE']:.2f} units")
        print(f"  MAPE:  {metrics['MAPE']:.2f}%")
        print(f"  R²:    {metrics['R2']:.4f}")

        print("\nBusiness Metrics:")
        print(f"  Waste Rate:     {business_metrics['waste_rate_%']:.2f}%")
        print(f"  Shortage Rate:  {business_metrics['shortage_rate_%']:.2f}%")
        print(f"  Accuracy Rate:  {business_metrics['accuracy_rate_%']:.2f}%")
        print(f"  Avg Waste:      {business_metrics['avg_waste_qty']:.2f} units/prediction")
        print(f"  Total Waste:    {business_metrics['total_waste_qty']:.0f} units")

        if 'waste_cost_total' in business_metrics:
            print(f"  Waste Cost:     ${business_metrics['waste_cost_total']:.2f}")

        print("="*80 + "\n")


if __name__ == "__main__":
    # Test evaluation
    y_true = np.array([50, 60, 70, 55, 65, 75, 45, 55])
    y_pred = np.array([52, 58, 72, 53, 67, 73, 47, 56])
    unit_cost = np.array([0.5, 0.75, 1.0, 0.5, 0.75, 1.0, 0.5, 0.75])

    evaluator = Evaluator()
    evaluator.print_evaluation_report(y_true, y_pred, "Test Model", unit_cost)
