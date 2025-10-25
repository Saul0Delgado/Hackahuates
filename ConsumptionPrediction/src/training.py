"""
Training pipeline for consumption prediction models
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from pathlib import Path
import xgboost as xgb

from .utils import logger, load_config
from .data_loader import ConsumptionDataLoader
from .feature_engineering import FeatureEngineer
from .models import XGBoostConsumptionModel, RandomForestConsumptionModel, EnsembleConsumptionModel
from .evaluation import Evaluator


class TrainingPipeline:
    """
    Complete training pipeline for consumption prediction
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize training pipeline

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.data_loader = ConsumptionDataLoader(config_path)
        self.feature_engineer = FeatureEngineer(config_path)
        self.evaluator = Evaluator()

        self.models = {}
        self.results = {}

    def load_data(self, reload: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load and prepare data

        Args:
            reload: Whether to reload from raw data

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        logger.info("Loading data...")

        if reload:
            # Load, validate, clean, and split from raw
            train_df, val_df, test_df = self.data_loader.load_and_prepare(save=True)
        else:
            # Try to load processed data
            try:
                train_df, val_df, test_df = self.data_loader.load_processed_data()
            except FileNotFoundError:
                logger.warning("Processed data not found, loading from raw...")
                train_df, val_df, test_df = self.data_loader.load_and_prepare(save=True)

        return train_df, val_df, test_df

    def prepare_features(self, train_df: pd.DataFrame, val_df: pd.DataFrame,
                        test_df: pd.DataFrame) -> Tuple[Dict, Dict, Dict]:
        """
        Prepare features for modeling

        Args:
            train_df: Training data
            val_df: Validation data
            test_df: Test data

        Returns:
            Tuple of dicts with X and y for each set
        """
        logger.info("Preparing features...")

        # Transform training data (fit encoders)
        X_train, y_train = self.feature_engineer.transform(
            train_df, train_df=None, fit=True
        )

        # Transform validation data (use training stats)
        X_val, y_val = self.feature_engineer.transform(
            val_df, train_df=train_df, fit=False
        )

        # Transform test data (use training stats)
        X_test, y_test = self.feature_engineer.transform(
            test_df, train_df=train_df, fit=False
        )

        # Save encoders
        self.feature_engineer.save_encoders()

        train_data = {'X': X_train, 'y': y_train}
        val_data = {'X': X_val, 'y': y_val}
        test_data = {'X': X_test, 'y': y_test}

        return train_data, val_data, test_data

    def train_models(self, train_data: Dict, val_data: Dict, best_xgb_params: Dict = None) -> None:
        """
        Train all configured models

        Args:
            train_data: Training data with X and y
            val_data: Validation data with X and y
            best_xgb_params: Optional best XGBoost parameters from optimization
        """
        logger.info("Training models...")

        X_train, y_train = train_data['X'], train_data['y']
        X_val, y_val = val_data['X'], val_data['y']

        # Train XGBoost
        if self.config['models']['xgboost']['enabled']:
            logger.info("\n" + "="*80)
            logger.info("Training XGBoost")
            logger.info("="*80)

            xgb_model = XGBoostConsumptionModel()

            # Use optimized parameters if available
            if best_xgb_params:
                logger.info("Using optimized hyperparameters from Bayesian search")
                xgb_model.params.update(best_xgb_params)
                xgb_model.model = xgb.XGBRegressor(**xgb_model.params, verbosity=0)

            xgb_model.train(X_train, y_train, X_val, y_val, verbose=True)
            self.models['xgboost'] = xgb_model
            xgb_model.save()

        # Train Random Forest
        if self.config['models']['random_forest']['enabled']:
            logger.info("\n" + "="*80)
            logger.info("Training Random Forest")
            logger.info("="*80)

            rf_model = RandomForestConsumptionModel()
            rf_model.train(X_train, y_train, verbose=True)
            self.models['random_forest'] = rf_model
            rf_model.save()

        # Train Ensemble
        if self.config['models']['ensemble']['enabled']:
            logger.info("\n" + "="*80)
            logger.info("Training Ensemble")
            logger.info("="*80)

            ensemble_model = EnsembleConsumptionModel()
            ensemble_model.train(X_train, y_train, X_val, y_val, verbose=True)
            self.models['ensemble'] = ensemble_model
            ensemble_model.save()

    def evaluate_models(self, test_data: Dict) -> Dict:
        """
        Evaluate all trained models

        Args:
            test_data: Test data with X and y

        Returns:
            Dictionary of evaluation results
        """
        logger.info("\n" + "="*80)
        logger.info("EVALUATING MODELS")
        logger.info("="*80)

        X_test, y_test = test_data['X'], test_data['y']
        y_test_array = y_test.values if isinstance(y_test, pd.Series) else y_test

        for model_name, model in self.models.items():
            logger.info(f"\nEvaluating {model_name}...")

            # Make predictions
            y_pred = model.predict(X_test)

            # Calculate metrics
            metrics = model.evaluate(X_test, y_test)

            # Calculate business metrics
            business_metrics = self.evaluator.calculate_business_metrics(
                y_test_array, y_pred
            )

            # Store results
            self.results[model_name] = {
                'model': model,
                'metrics': metrics,
                'business_metrics': business_metrics,
                'predictions': y_pred
            }

            # Print report
            self.evaluator.print_evaluation_report(
                y_test_array, y_pred, model_name
            )

        return self.results

    def get_best_model(self, metric: str = 'MAE') -> Tuple[str, Dict]:
        """
        Get best model based on metric

        Args:
            metric: Metric to use for comparison (MAE, RMSE, MAPE, R2)

        Returns:
            Tuple of (model_name, model_object)
        """
        best_model_name = None
        best_value = float('inf') if metric in ['MAE', 'RMSE', 'MAPE'] else float('-inf')

        for model_name, results in self.results.items():
            value = results['metrics'][metric]

            if metric in ['MAE', 'RMSE', 'MAPE']:
                # Lower is better
                if value < best_value:
                    best_value = value
                    best_model_name = model_name
            else:
                # Higher is better (R2)
                if value > best_value:
                    best_value = value
                    best_model_name = model_name

        logger.info(f"\nBest model: {best_model_name} ({metric}: {best_value:.4f})")

        return best_model_name, self.models[best_model_name]

    def print_summary(self) -> None:
        """
        Print training summary
        """
        logger.info("\n" + "="*80)
        logger.info("TRAINING SUMMARY")
        logger.info("="*80)

        for model_name, results in self.results.items():
            logger.info(f"\n{model_name.upper()}:")
            logger.info("  Metrics:")
            for metric_name, value in results['metrics'].items():
                logger.info(f"    {metric_name}: {value:.4f}")
            logger.info("  Business Metrics:")
            for metric_name, value in results['business_metrics'].items():
                logger.info(f"    {metric_name}: {value:.2f}")

    def optimize_xgboost(self, train_data: Dict, val_data: Dict, n_trials: int = 150) -> None:
        """
        Optimize XGBoost hyperparameters using Bayesian optimization

        Args:
            train_data: Training data with X and y
            val_data: Validation data with X and y
            n_trials: Number of optimization trials
        """
        logger.info("\n" + "="*80)
        logger.info("BAYESIAN HYPERPARAMETER OPTIMIZATION")
        logger.info("="*80)

        X_train, y_train = train_data['X'], train_data['y']
        X_val, y_val = val_data['X'], val_data['y']

        xgb_model = XGBoostConsumptionModel()
        opt_results = xgb_model.optimize_hyperparameters(
            X_train, y_train, X_val, y_val,
            n_trials=n_trials, verbose=True
        )

        logger.info(f"\nOptimization Results:")
        logger.info(f"  Best MAE: {opt_results['best_score']:.4f}")

    def train_quantile_ensemble(self, train_data: Dict, val_data: Dict, test_data: Dict = None) -> None:
        """
        Train Q90 safety stock model

        Args:
            train_data: Training data with X and y
            val_data: Validation data with X and y
            test_data: Optional test data for evaluation
        """
        logger.info("\n" + "="*80)
        logger.info("TRAINING Q90 SAFETY STOCK MODEL")
        logger.info("="*80)

        X_train, y_train = train_data['X'], train_data['y']
        X_val, y_val = val_data['X'], val_data['y']

        xgb_model = self.models.get('xgboost')
        if xgb_model is None:
            logger.warning("XGBoost model not trained. Skipping Q90 model.")
            return

        xgb_model.train_quantile_ensemble(X_train, y_train, X_val, y_val, verbose=True)
        logger.info("Q90 safety stock model training complete")

        # Evaluate on test set if provided
        if test_data is not None:
            X_test, y_test = test_data['X'], test_data['y']
            y_test_array = y_test.values if isinstance(y_test, pd.Series) else y_test

            logger.info("\n" + "="*80)
            logger.info("Q90 SAFETY STOCK EVALUATION")
            logger.info("="*80)

            # Get predictions
            base_pred = xgb_model.predict(X_test)
            q90_pred = xgb_model.predict_quantiles(X_test)

            # Calculate metrics
            base_shortages = np.sum(y_test_array > base_pred)
            q90_shortages = np.sum(y_test_array > q90_pred)
            shortage_reduction = ((base_shortages - q90_shortages) / base_shortages * 100) if base_shortages > 0 else 0

            base_waste = np.mean(np.maximum(base_pred - y_test_array, 0))
            q90_waste = np.mean(np.maximum(q90_pred - y_test_array, 0))

            logger.info(f"\nBase Model (Mean):")
            logger.info(f"  Shortages: {base_shortages}/{len(y_test_array)} ({base_shortages/len(y_test_array)*100:.1f}%)")
            logger.info(f"  Avg Waste: {base_waste:.2f} units")

            logger.info(f"\nQ90 Safety Stock:")
            logger.info(f"  Shortages: {q90_shortages}/{len(y_test_array)} ({q90_shortages/len(y_test_array)*100:.1f}%)")
            logger.info(f"  Avg Surplus: {q90_waste:.2f} units")

            logger.info(f"\nImprovement:")
            logger.info(f"  Shortage reduction: {shortage_reduction:.1f}%")
            logger.info(f"  Additional surplus: {q90_waste - base_waste:.2f} units")
            logger.info("="*80)

    def run(self, reload_data: bool = False, optimize_hyperparams: bool = False,
            train_quantiles: bool = False) -> Tuple[str, Dict]:
        """
        Run complete training pipeline

        Args:
            reload_data: Whether to reload data from raw
            optimize_hyperparams: Whether to run Bayesian optimization
            train_quantiles: Whether to train quantile ensemble

        Returns:
            Tuple of (best_model_name, best_model)
        """
        logger.info("\n" + "="*80)
        logger.info("CONSUMPTION PREDICTION TRAINING PIPELINE")
        logger.info("="*80)

        # 1. Load data
        train_df, val_df, test_df = self.load_data(reload=reload_data)

        # 2. Prepare features
        train_data, val_data, test_data = self.prepare_features(
            train_df, val_df, test_df
        )

        # 3. Optimize hyperparameters (optional)
        best_xgb_params = None
        if optimize_hyperparams:
            logger.info("\n" + "="*80)
            logger.info("BAYESIAN HYPERPARAMETER OPTIMIZATION")
            logger.info("="*80)

            X_train, y_train = train_data['X'], train_data['y']
            X_val, y_val = val_data['X'], val_data['y']

            xgb_model = XGBoostConsumptionModel()
            opt_results = xgb_model.optimize_hyperparameters(
                X_train, y_train, X_val, y_val,
                n_trials=300, verbose=True  # Bayesian optimization with 300 trials
            )
            best_xgb_params = opt_results['best_params']
            logger.info(f"\nBest MAE from optimization: {opt_results['best_score']:.4f}")

        # 4. Train models (with optimized params if available)
        self.train_models(train_data, val_data, best_xgb_params)

        # 5. Train quantile ensemble (optional)
        if train_quantiles:
            self.train_quantile_ensemble(train_data, val_data, test_data)

        # 6. Evaluate models
        self.evaluate_models(test_data)

        # 7. Print summary
        self.print_summary()

        # 8. Get best model
        best_model_name, best_model = self.get_best_model(metric='MAE')

        logger.info("\n" + "="*80)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*80)

        return best_model_name, best_model


if __name__ == "__main__":
    # Run training pipeline
    pipeline = TrainingPipeline()
    best_model_name, best_model = pipeline.run()

    print(f"\n✅ Training complete!")
    print(f"   Best model: {best_model_name}")
    print(f"   Saved to: data/models/{best_model_name}.pkl")
