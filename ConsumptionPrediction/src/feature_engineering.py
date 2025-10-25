"""
Feature engineering for consumption prediction
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

from .utils import logger, load_config, get_data_path


class FeatureEngineer:
    """
    Create features for consumption prediction model
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize feature engineer

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.feature_config = self.config['features']
        self.label_encoders = {}
        self.scaler = None

    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal features from Date column

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with temporal features
        """
        logger.info("Creating temporal features...")

        df = df.copy()

        # Ensure Date is datetime
        if df['Date'].dtype != 'datetime64[ns]':
            df['Date'] = pd.to_datetime(df['Date'])

        # Day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df['Date'].dt.dayofweek

        # Is weekend
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Month
        df['month'] = df['Date'].dt.month

        # Day of month
        df['day_of_month'] = df['Date'].dt.day

        # Week of year
        df['week_of_year'] = df['Date'].dt.isocalendar().week

        logger.info(f"Created {5} temporal features")
        return df

    def create_consumption_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create consumption-related metrics

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with consumption metrics
        """
        logger.info("Creating consumption metrics...")

        df = df.copy()

        # Check if we're in training mode (has these columns) or prediction mode (doesn't have them)
        has_training_columns = 'Quantity_Returned' in df.columns and 'Quantity_Consumed' in df.columns

        if has_training_columns:
            # Training mode - use actual values
            # Waste rate
            df['waste_rate'] = df['Quantity_Returned'] / df['Standard_Specification_Qty']

            # Consumption rate
            df['consumption_rate'] = df['Quantity_Consumed'] / df['Standard_Specification_Qty']

            # Consumption per passenger
            df['consumption_per_passenger'] = df['Quantity_Consumed'] / df['Passenger_Count']

            # Overage quantity
            df['overage_qty'] = df['Standard_Specification_Qty'] - df['Quantity_Consumed']

            # Overage percentage
            df['overage_percentage'] = np.where(
                df['Quantity_Consumed'] > 0,
                df['overage_qty'] / df['Quantity_Consumed'],
                0
            )
        else:
            # Prediction mode - use historical averages or defaults
            df['waste_rate'] = 0.05  # Default 5% waste rate
            df['consumption_rate'] = 0.95  # Default 95% consumption
            df['consumption_per_passenger'] = 1.0  # Default 1 unit per passenger
            df['overage_qty'] = 0.0
            df['overage_percentage'] = 0.05

        # Specification per passenger (always available)
        df['spec_per_passenger'] = df['Standard_Specification_Qty'] / df['Passenger_Count']

        logger.info(f"Created {6} consumption metrics")
        return df

    def create_aggregation_features(self, df: pd.DataFrame,
                                   train_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Create aggregation features based on historical data

        Args:
            df: Input DataFrame
            train_df: Training DataFrame for calculating aggregations (use None for training)

        Returns:
            DataFrame with aggregation features
        """
        logger.info("Creating aggregation features...")

        df = df.copy()

        # Use train_df for aggregations, or df itself if training
        agg_df = train_df.copy() if train_df is not None else df.copy()

        # Ensure Product_ID has consistent type (string)
        for data in [df, agg_df]:
            if 'Product_ID' in data.columns:
                data['Product_ID'] = data['Product_ID'].astype(str)

        # Ensure consumption metrics exist in agg_df
        if 'consumption_rate' not in agg_df.columns:
            # Create consumption metrics for aggregation
            agg_df = self.create_consumption_metrics(agg_df)

        # By Product
        if self.feature_config['aggregations']['by_product']:
            agg_dict = {
                'consumption_rate': ['mean', 'std'],
                'waste_rate': ['mean', 'std'],
                'consumption_per_passenger': 'mean'
            }
            # Only include Quantity_Consumed if it exists (training mode)
            if 'Quantity_Consumed' in agg_df.columns:
                agg_dict['Quantity_Consumed'] = ['mean', 'std']

            product_agg = agg_df.groupby('Product_ID').agg(agg_dict).reset_index()

            # Flatten column names
            product_agg.columns = ['Product_ID'] + [
                f'product_{col[0]}_{col[1]}' if col[1] else f'product_{col[0]}'
                for col in product_agg.columns[1:]
            ]

            df = df.merge(product_agg, on='Product_ID', how='left')
            logger.info(f"  Added {len(product_agg.columns)-1} product aggregation features")

        # By Flight Type × Product
        if self.feature_config['aggregations']['by_flight_type']:
            agg_dict = {'consumption_rate': 'mean'}
            if 'Quantity_Consumed' in agg_df.columns:
                agg_dict['Quantity_Consumed'] = 'mean'

            flight_product_agg = agg_df.groupby(['Flight_Type', 'Product_ID']).agg(agg_dict).reset_index()

            # Dynamically create column names based on what was aggregated
            col_names = ['Flight_Type', 'Product_ID', 'flight_product_consumption_rate_mean']
            if 'Quantity_Consumed' in agg_dict:
                col_names.append('flight_product_qty_consumed_mean')
            flight_product_agg.columns = col_names

            df = df.merge(flight_product_agg, on=['Flight_Type', 'Product_ID'], how='left')
            logger.info(f"  Added {len(flight_product_agg.columns)-2} flight×product aggregation features")

        # By Service Type × Product
        if self.feature_config['aggregations']['by_service_type']:
            service_product_agg = agg_df.groupby(['Service_Type', 'Product_ID']).agg({
                'waste_rate': 'mean',
                'consumption_per_passenger': 'mean'
            }).reset_index()

            service_product_agg.columns = [
                'Service_Type', 'Product_ID',
                'service_product_waste_rate_mean',
                'service_product_consumption_per_pax_mean'
            ]

            df = df.merge(service_product_agg, on=['Service_Type', 'Product_ID'], how='left')
            logger.info(f"  Added {len(service_product_agg.columns)-2} service×product aggregation features")

        # By Origin × Product
        if self.feature_config['aggregations']['by_origin']:
            if 'Quantity_Consumed' in agg_df.columns:
                origin_product_agg = agg_df.groupby(['Origin', 'Product_ID']).agg({
                    'Quantity_Consumed': 'mean'
                }).reset_index()

                origin_product_agg.columns = [
                    'Origin', 'Product_ID',
                    'origin_product_qty_consumed_mean'
                ]

                df = df.merge(origin_product_agg, on=['Origin', 'Product_ID'], how='left')
                logger.info(f"  Added {len(origin_product_agg.columns)-2} origin×product aggregation features")

        # Fill NaN with 0 for aggregation features (in case of unseen combinations)
        aggregation_cols = [col for col in df.columns if any([
            '_mean' in col, '_std' in col, 'product_' in col,
            'flight_product_' in col, 'service_product_' in col,
            'origin_product_' in col
        ])]

        df[aggregation_cols] = df[aggregation_cols].fillna(0)

        return df

    def encode_categorical_features(self, df: pd.DataFrame,
                                    fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical features

        Args:
            df: Input DataFrame
            fit: Whether to fit encoders (True for training, False for inference)

        Returns:
            DataFrame with encoded features
        """
        logger.info("Encoding categorical features...")

        df = df.copy()

        # Label Encoding
        label_encode_cols = self.feature_config['encoding']['label_encode']

        for col in label_encode_cols:
            if col in df.columns:
                if fit:
                    # Fit and transform
                    le = LabelEncoder()
                    df[f'{col}_encoded'] = le.fit_transform(df[col])
                    self.label_encoders[col] = le
                    logger.info(f"  Label encoded {col}: {len(le.classes_)} classes")
                else:
                    # Transform only (use fitted encoder)
                    if col in self.label_encoders:
                        le = self.label_encoders[col]
                        # Handle unseen labels
                        df[f'{col}_encoded'] = df[col].map(
                            lambda x: le.transform([x])[0] if x in le.classes_ else -1
                        )
                    else:
                        logger.warning(f"No fitted encoder for {col}")

        # One-Hot Encoding
        one_hot_cols = self.feature_config['encoding']['one_hot_encode']

        for col in one_hot_cols:
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col.lower(), drop_first=False)
                df = pd.concat([df, dummies], axis=1)
                logger.info(f"  One-hot encoded {col}: {len(dummies.columns)} columns")

        return df

    def select_features(self, df: pd.DataFrame, target_col: str = 'Quantity_Consumed') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Select final features for modeling

        Args:
            df: Input DataFrame with all features
            target_col: Target column name

        Returns:
            Tuple of (X, y)
        """
        logger.info("Selecting features for modeling...")

        # Define feature columns (exclude non-predictive columns)
        exclude_cols = [
            'Flight_ID', 'Product_Name', 'Date', 'Crew_Feedback',
            'Standard_Specification_Qty', 'Quantity_Returned', 'Quantity_Consumed',
            'Origin', 'Product_ID', 'Flight_Type', 'Service_Type',  # Original categorical (now encoded)
            'Consumption_Qty', 'waste_qty', 'overage_qty'  # Temporary columns used in feature engineering
        ]

        # Get all columns except excluded and target
        feature_cols = [col for col in df.columns if col not in exclude_cols and col != target_col]

        X = df[feature_cols].copy()

        # If target column is missing (inference mode), return a placeholder series
        if target_col in df.columns:
            y = df[target_col].copy()
        else:
            # Create an empty/placeholder series with same index so downstream code
            # that expects a Series won't fail. Callers that are in inference mode
            # typically ignore `y`, so this is safe.
            try:
                y = pd.Series([0.0] * len(df), index=df.index)
            except Exception:
                # Fallback to an empty float series if construction fails
                y = pd.Series(dtype=float)

        logger.info(f"Selected {len(feature_cols)} features")
        logger.info(f"Feature columns: {feature_cols[:10]}... ({len(feature_cols) - 10} more)")

        return X, y

    def transform(self, df: pd.DataFrame, train_df: pd.DataFrame = None,
                 fit: bool = True) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Complete feature engineering pipeline

        Args:
            df: Input DataFrame
            train_df: Training DataFrame for aggregations (None if this IS training data)
            fit: Whether to fit encoders (True for training, False for inference)

        Returns:
            Tuple of (X, y)
        """
        logger.info("="*80)
        logger.info("FEATURE ENGINEERING PIPELINE")
        logger.info("="*80)

        # 1. Temporal features
        df = self.create_temporal_features(df)

        # 2. Consumption metrics
        df = self.create_consumption_metrics(df)

        # 3. Aggregation features
        df = self.create_aggregation_features(df, train_df=train_df)

        # 4. Encode categorical
        df = self.encode_categorical_features(df, fit=fit)

        # 5. Select features
        X, y = self.select_features(df)

        logger.info(f"Final feature matrix: {X.shape}")
        logger.info(f"Target vector: {y.shape}")
        logger.info("="*80)

        return X, y

    def save_encoders(self, path: str = "data/models/feature_encoders.pkl") -> None:
        """
        Save label encoders and scaler

        Args:
            path: Path to save encoders
        """
        encoders_path = get_data_path(path)
        encoders_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump({
            'label_encoders': self.label_encoders,
            'scaler': self.scaler
        }, encoders_path)

        logger.info(f"Saved feature encoders to {encoders_path}")

    def load_encoders(self, path: str = "data/models/feature_encoders.pkl") -> None:
        """
        Load label encoders and scaler

        Args:
            path: Path to load encoders from
        """
        encoders_path = get_data_path(path)

        encoders = joblib.load(encoders_path)
        self.label_encoders = encoders['label_encoders']
        self.scaler = encoders['scaler']

        logger.info(f"Loaded feature encoders from {encoders_path}")


if __name__ == "__main__":
    # Test feature engineering
    from .data_loader import ConsumptionDataLoader

    # Load data
    loader = ConsumptionDataLoader()
    train_df, val_df, test_df = loader.load_and_prepare(save=False)

    # Create features
    engineer = FeatureEngineer()

    # Transform training data
    X_train, y_train = engineer.transform(train_df, train_df=None, fit=True)

    # Transform validation data (using training stats)
    X_val, y_val = engineer.transform(val_df, train_df=train_df, fit=False)

    # Transform test data (using training stats)
    X_test, y_test = engineer.transform(test_df, train_df=train_df, fit=False)

    print("\n" + "="*80)
    print("FEATURE ENGINEERING TEST")
    print("="*80)
    print(f"\nX_train shape: {X_train.shape}")
    print(f"X_val shape:   {X_val.shape}")
    print(f"X_test shape:  {X_test.shape}")
    print(f"\nFeature names:")
    print(X_train.columns.tolist())
    print(f"\nX_train preview:")
    print(X_train.head())
    print(f"\ny_train preview:")
    print(y_train.head())
