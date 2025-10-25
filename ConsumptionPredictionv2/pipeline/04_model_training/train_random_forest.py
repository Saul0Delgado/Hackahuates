"""
Random Forest Model Training
============================

Trains a Random Forest regressor for consumption prediction.
This serves as a baseline model for comparison.

Outputs:
- random_forest_model.pkl (trained model)
- random_forest_predictions.csv (predictions on test set)
- random_forest_metrics.json (performance metrics)

Author: ML Pipeline
Date: 2025-10-25
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import pickle
import warnings

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

FEATURES_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\pipeline\03_feature_engineering\outputs')
OUTPUT_DIR = Path(__file__).parent / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

# Model hyperparameters
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 15,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'max_samples': 0.8,  # Bootstrap fraction instead of subsample
    'random_state': 42,
    'n_jobs': -1
}

# ============================================================================
# LOAD DATA
# ============================================================================

def load_features():
    """Load feature matrices"""

    print("=" * 70)
    print("LOADING FEATURE DATA")
    print("=" * 70)

    train_path = FEATURES_DIR / 'features_trainA.csv'
    test_path = FEATURES_DIR / 'features_testB.csv'

    if not train_path.exists():
        raise FileNotFoundError(f"Train features not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test features not found: {test_path}")

    # Load data
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    print(f"\nTrain set: {train_df.shape}")
    print(f"Test set: {test_df.shape}")

    return train_df, test_df


# ============================================================================
# PREPARE DATA
# ============================================================================

def prepare_data(train_df, test_df):
    """Separate features and target"""

    print("\n" + "=" * 70)
    print("PREPARING DATA")
    print("=" * 70)

    # Target variable
    TARGET = 'CONSUMPTION_QTY'

    # Extract target
    y_train = train_df[TARGET].values
    y_test = test_df[TARGET].values

    # Features (all columns except target and identifiers)
    drop_cols = [TARGET, 'FLIGHT_KEY', 'FLIGHT_DATE', 'ORIGIN', 'DESTINATION', 'ROUTE']
    feature_cols = [col for col in train_df.columns if col not in drop_cols]

    X_train = train_df[feature_cols].copy()
    X_test = test_df[feature_cols].copy()

    print(f"\nFeatures used: {len(feature_cols)}")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"y_test shape: {y_test.shape}")

    # Check for missing values
    missing_train = X_train.isnull().sum().sum()
    missing_test = X_test.isnull().sum().sum()

    if missing_train > 0 or missing_test > 0:
        print(f"\n[WARNING] Missing values found:")
        print(f"  Train: {missing_train}")
        print(f"  Test: {missing_test}")
        print(f"  Filling with 0...")
        X_train = X_train.fillna(0)
        X_test = X_test.fillna(0)

    return X_train, X_test, y_train, y_test, feature_cols


# ============================================================================
# TRAIN MODEL
# ============================================================================

def train_random_forest(X_train, y_train):
    """Train Random Forest model"""

    print("\n" + "=" * 70)
    print("TRAINING RANDOM FOREST MODEL")
    print("=" * 70)

    print(f"\nHyperparameters:")
    for key, value in RF_PARAMS.items():
        print(f"  {key}: {value}")

    # Create and train model
    print(f"\nTraining Random Forest regressor...")
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X_train, y_train)

    print(f"\n[OK] Training complete!")

    return model


# ============================================================================
# EVALUATE MODEL
# ============================================================================

def evaluate_model(model, X_train, X_test, y_train, y_test):
    """Evaluate model on train and test sets"""

    print("\n" + "=" * 70)
    print("EVALUATING MODEL")
    print("=" * 70)

    # Train predictions
    y_train_pred = model.predict(X_train)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    train_mape = mean_absolute_percentage_error(y_train, y_train_pred)

    # Test predictions
    y_test_pred = model.predict(X_test)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    test_mape = mean_absolute_percentage_error(y_test, y_test_pred)

    print(f"\nTRAIN SET METRICS:")
    print(f"  MAE:  {train_mae:.4f}")
    print(f"  RMSE: {train_rmse:.4f}")
    print(f"  R²:   {train_r2:.4f}")
    print(f"  MAPE: {train_mape:.4f}")

    print(f"\nTEST SET METRICS:")
    print(f"  MAE:  {test_mae:.4f}")
    print(f"  RMSE: {test_rmse:.4f}")
    print(f"  R²:   {test_r2:.4f}")
    print(f"  MAPE: {test_mape:.4f}")

    metrics = {
        'train': {
            'mae': float(train_mae),
            'rmse': float(train_rmse),
            'r2': float(train_r2),
            'mape': float(train_mape)
        },
        'test': {
            'mae': float(test_mae),
            'rmse': float(test_rmse),
            'r2': float(test_r2),
            'mape': float(test_mape)
        }
    }

    return metrics, y_test_pred


# ============================================================================
# FEATURE IMPORTANCE
# ============================================================================

def analyze_feature_importance(model, feature_cols):
    """Analyze feature importance"""

    print("\n" + "=" * 70)
    print("FEATURE IMPORTANCE")
    print("=" * 70)

    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)

    print(f"\nTop 10 Important Features:")
    for idx, row in importance_df.head(10).iterrows():
        print(f"  {row['feature']:<30} {row['importance']:.4f}")

    return importance_df


# ============================================================================
# SAVE OUTPUTS
# ============================================================================

def save_outputs(model, metrics, y_test_pred, test_df, importance_df):
    """Save model, predictions, and metrics"""

    print("\n" + "=" * 70)
    print("SAVING OUTPUTS")
    print("=" * 70)

    # Save model
    model_path = OUTPUT_DIR / 'random_forest_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"  Model saved: {model_path}")

    # Save metrics
    metrics['timestamp'] = datetime.now().isoformat()
    metrics_path = OUTPUT_DIR / 'random_forest_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics saved: {metrics_path}")

    # Save predictions
    # Select available columns for predictions
    available_cols = ['CONSUMPTION_QTY']
    for col in ['FLIGHT_KEY', 'FLIGHT_DATE', 'PASSENGERS']:
        if col in test_df.columns:
            available_cols.insert(0, col)

    predictions_df = test_df[available_cols].copy() if available_cols else pd.DataFrame({'CONSUMPTION_QTY': test_df.get('CONSUMPTION_QTY', [])})
    predictions_df['PREDICTED_CONSUMPTION'] = y_test_pred
    predictions_df['RESIDUAL'] = predictions_df['CONSUMPTION_QTY'] - y_test_pred
    predictions_df['ABS_ERROR'] = np.abs(predictions_df['RESIDUAL'])
    predictions_df['ERROR_PCT'] = (predictions_df['ABS_ERROR'] / predictions_df['CONSUMPTION_QTY'] * 100).fillna(0)

    predictions_path = OUTPUT_DIR / 'random_forest_predictions.csv'
    predictions_df.to_csv(predictions_path, index=False)
    print(f"  Predictions saved: {predictions_path}")

    # Save feature importance
    importance_path = OUTPUT_DIR / 'random_forest_feature_importance.csv'
    importance_df.to_csv(importance_path, index=False)
    print(f"  Feature importance saved: {importance_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute complete Random Forest training pipeline"""

    print(f"\nStarting Random Forest Training at {datetime.now()}")

    # Load data
    train_df, test_df = load_features()

    # Prepare data
    X_train, X_test, y_train, y_test, feature_cols = prepare_data(train_df, test_df)

    # Train model
    model = train_random_forest(X_train, y_train)

    # Evaluate
    metrics, y_test_pred = evaluate_model(model, X_train, X_test, y_train, y_test)

    # Feature importance
    importance_df = analyze_feature_importance(model, feature_cols)

    # Save outputs
    save_outputs(model, metrics, y_test_pred, test_df, importance_df)

    print("\n" + "=" * 70)
    print(f"Random Forest Training Complete! Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
