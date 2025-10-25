"""
Neural Network Model Training
=============================

Trains a deep neural network for consumption prediction.
Uses TensorFlow/Keras for flexible deep learning architecture.

Outputs:
- neural_network_model.h5 (trained model)
- neural_network_predictions.csv (predictions on test set)
- neural_network_metrics.json (performance metrics)

Author: ML Pipeline
Date: 2025-10-25
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

FEATURES_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\pipeline\03_feature_engineering\outputs')
OUTPUT_DIR = Path(__file__).parent / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

# Neural Network hyperparameters
NN_PARAMS = {
    'hidden_layers': [128, 64, 32],
    'activation': 'relu',
    'dropout': 0.2,
    'learning_rate': 0.001,
    'batch_size': 32,
    'epochs': 100,
    'validation_split': 0.2
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
    """Separate features and target, and normalize"""

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

    # Check for missing values and fill
    missing_train = X_train.isnull().sum().sum()
    missing_test = X_test.isnull().sum().sum()

    if missing_train > 0 or missing_test > 0:
        print(f"\n[WARNING] Missing values found:")
        print(f"  Train: {missing_train}")
        print(f"  Test: {missing_test}")
        print(f"  Filling with 0...")
        X_train = X_train.fillna(0)
        X_test = X_test.fillna(0)

    # Normalize features
    print(f"\nNormalizing features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"  Feature scaling complete")

    return X_train_scaled, X_test_scaled, y_train, y_test, feature_cols, scaler


# ============================================================================
# BUILD MODEL
# ============================================================================

def build_model(input_dim):
    """Build neural network architecture"""

    print("\n" + "=" * 70)
    print("BUILDING NEURAL NETWORK")
    print("=" * 70)

    print(f"\nArchitecture:")
    print(f"  Input dimension: {input_dim}")
    print(f"  Hidden layers: {NN_PARAMS['hidden_layers']}")
    print(f"  Dropout: {NN_PARAMS['dropout']}")
    print(f"  Learning rate: {NN_PARAMS['learning_rate']}")

    # Build sequential model
    model = models.Sequential()

    # Input layer
    model.add(layers.Input(shape=(input_dim,)))

    # Hidden layers
    for hidden_dim in NN_PARAMS['hidden_layers']:
        model.add(layers.Dense(hidden_dim, activation=NN_PARAMS['activation']))
        model.add(layers.Dropout(NN_PARAMS['dropout']))

    # Output layer
    model.add(layers.Dense(1, activation='linear'))  # Linear for regression

    # Compile
    optimizer = keras.optimizers.Adam(learning_rate=NN_PARAMS['learning_rate'])
    model.compile(
        optimizer=optimizer,
        loss='mse',
        metrics=['mae', 'mape']
    )

    print(f"\n[OK] Model built and compiled")

    return model


# ============================================================================
# TRAIN MODEL
# ============================================================================

def train_neural_network(model, X_train, y_train, X_val, y_val):
    """Train neural network"""

    print("\n" + "=" * 70)
    print("TRAINING NEURAL NETWORK")
    print("=" * 70)

    # Early stopping callback
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )

    print(f"\nTraining with:")
    print(f"  Batch size: {NN_PARAMS['batch_size']}")
    print(f"  Epochs: {NN_PARAMS['epochs']}")
    print(f"  Validation split: {NN_PARAMS['validation_split']}")

    # Train
    history = model.fit(
        X_train, y_train,
        batch_size=NN_PARAMS['batch_size'],
        epochs=NN_PARAMS['epochs'],
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        verbose=1
    )

    print(f"\n[OK] Training complete!")

    return model, history


# ============================================================================
# EVALUATE MODEL
# ============================================================================

def evaluate_model(model, X_train, X_test, y_train, y_test):
    """Evaluate model on train and test sets"""

    print("\n" + "=" * 70)
    print("EVALUATING MODEL")
    print("=" * 70)

    # Train predictions
    y_train_pred = model.predict(X_train, verbose=0).flatten()
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    train_mape = mean_absolute_percentage_error(y_train, y_train_pred)

    # Test predictions
    y_test_pred = model.predict(X_test, verbose=0).flatten()
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
# SAVE OUTPUTS
# ============================================================================

def save_outputs(model, metrics, y_test_pred, test_df):
    """Save model, predictions, and metrics"""

    print("\n" + "=" * 70)
    print("SAVING OUTPUTS")
    print("=" * 70)

    # Save model
    model_path = OUTPUT_DIR / 'neural_network_model.h5'
    model.save(model_path)
    print(f"  Model saved: {model_path}")

    # Save metrics
    metrics['timestamp'] = datetime.now().isoformat()
    metrics_path = OUTPUT_DIR / 'neural_network_metrics.json'
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

    predictions_path = OUTPUT_DIR / 'neural_network_predictions.csv'
    predictions_df.to_csv(predictions_path, index=False)
    print(f"  Predictions saved: {predictions_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute complete Neural Network training pipeline"""

    print(f"\nStarting Neural Network Training at {datetime.now()}")

    # Load data
    train_df, test_df = load_features()

    # Prepare data
    X_train_scaled, X_test_scaled, y_train, y_test, feature_cols, scaler = prepare_data(train_df, test_df)

    # Build model
    model = build_model(input_dim=X_train_scaled.shape[1])

    # Create validation set
    n_val = int(0.2 * len(X_train_scaled))
    X_train_nn = X_train_scaled[:-n_val]
    y_train_nn = y_train[:-n_val]
    X_val = X_train_scaled[-n_val:]
    y_val = y_train[-n_val:]

    # Train model
    model, history = train_neural_network(model, X_train_nn, y_train_nn, X_val, y_val)

    # Evaluate
    metrics, y_test_pred = evaluate_model(model, X_train_scaled, X_test_scaled, y_train, y_test)

    # Save outputs
    save_outputs(model, metrics, y_test_pred, test_df)

    print("\n" + "=" * 70)
    print(f"Neural Network Training Complete! Outputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
