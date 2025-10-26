

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from sklearn.model_selection import train_test_split

from .utils import logger, load_config, get_data_path


class ConsumptionDataLoader:
    """
    Load and preprocess consumption prediction dataset
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize data loader

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.data_config = self.config['data']
        self.split_config = self.config['split']
        self.df = None
        self.df_train = None
        self.df_val = None
        self.df_test = None

    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw dataset from CSV

        Returns:
            Raw DataFrame
        """
        data_path = get_data_path(self.data_config['raw_path'])

        logger.info(f"Loading data from {data_path}")

        try:
            df = pd.read_csv(data_path)
            logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

            # Validate expected shape
            assert len(df) == 792, f"Expected 792 rows, got {len(df)}"
            assert len(df.columns) == 13, f"Expected 13 columns, got {len(df.columns)}"

            self.df = df
            return df

        except FileNotFoundError:
            logger.error(f"Data file not found: {data_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data integrity

        Args:
            df: Input DataFrame

        Returns:
            Validated DataFrame
        """
        logger.info("Validating data...")

        # Check for required columns
        required_cols = [
            'Flight_ID', 'Origin', 'Date', 'Flight_Type', 'Service_Type',
            'Passenger_Count', 'Product_ID', 'Product_Name',
            'Standard_Specification_Qty', 'Quantity_Returned',
            'Quantity_Consumed', 'Unit_Cost', 'Crew_Feedback'
        ]

        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Check for nulls in critical columns
        critical_cols = ['Flight_ID', 'Product_ID', 'Passenger_Count',
                        'Standard_Specification_Qty', 'Quantity_Consumed']

        for col in critical_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                raise ValueError(f"Column {col} has {null_count} null values")

        # Validate data integrity
        # Standard Qty should be >= Consumed + Returned
        integrity_check = (
            df['Standard_Specification_Qty'] >=
            df['Quantity_Consumed'] + df['Quantity_Returned']
        )

        violations = (~integrity_check).sum()
        if violations > 0:
            logger.warning(f"Found {violations} rows where Standard_Qty < Consumed + Returned")

        # Check for negative values
        numeric_cols = ['Passenger_Count', 'Standard_Specification_Qty',
                       'Quantity_Returned', 'Quantity_Consumed', 'Unit_Cost']

        for col in numeric_cols:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                raise ValueError(f"Column {col} has {negative_count} negative values")

        logger.info("Data validation passed ✓")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data

        Args:
            df: Input DataFrame

        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning data...")

        df = df.copy()

        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'])

        # Fill NaN in Crew_Feedback with 'none'
        df['Crew_Feedback'] = df['Crew_Feedback'].fillna('none')

        # Remove any duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            logger.warning(f"Removing {duplicates} duplicate rows")
            df = df.drop_duplicates()

        # Sort by date for time-based split
        df = df.sort_values('Date').reset_index(drop=True)

        logger.info(f"Cleaned data: {len(df)} rows remaining")
        return df

    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics of the dataset

        Args:
            df: DataFrame to summarize

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'date_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d'),
                'days': (df['Date'].max() - df['Date'].min()).days + 1
            },
            'unique_flights': df['Flight_ID'].nunique(),
            'unique_products': df['Product_ID'].nunique(),
            'unique_origins': df['Origin'].nunique(),
            'flight_types': df['Flight_Type'].value_counts().to_dict(),
            'service_types': df['Service_Type'].value_counts().to_dict(),
            'products': df['Product_ID'].unique().tolist(),
            'avg_passengers': df['Passenger_Count'].mean(),
            'avg_waste_rate': (df['Quantity_Returned'] / df['Standard_Specification_Qty']).mean(),
            'avg_consumption_rate': (df['Quantity_Consumed'] / df['Standard_Specification_Qty']).mean()
        }

        return summary

    def split_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        logger.info("Splitting data...")

        if self.split_config['time_based']:
            # Time-based split (recommended for time series)
            df = df.sort_values('Date')

            train_ratio = self.split_config['train_ratio']
            val_ratio = self.split_config['val_ratio']

            n = len(df)
            train_end = int(n * train_ratio)
            val_end = int(n * (train_ratio + val_ratio))

            train_df = df.iloc[:train_end].copy()
            val_df = df.iloc[train_end:val_end].copy()
            test_df = df.iloc[val_end:].copy()

            logger.info(f"Time-based split:")
            logger.info(f"  Train: {len(train_df)} rows ({train_df['Date'].min()} to {train_df['Date'].max()})")
            logger.info(f"  Val:   {len(val_df)} rows ({val_df['Date'].min()} to {val_df['Date'].max()})")
            logger.info(f"  Test:  {len(test_df)} rows ({test_df['Date'].min()} to {test_df['Date'].max()})")

        else:
            # Random split
            train_val_df, test_df = train_test_split(
                df,
                test_size=self.split_config['test_ratio'],
                random_state=self.split_config['random_state']
            )

            val_size = self.split_config['val_ratio'] / (1 - self.split_config['test_ratio'])
            train_df, val_df = train_test_split(
                train_val_df,
                test_size=val_size,
                random_state=self.split_config['random_state']
            )

            logger.info(f"Random split:")
            logger.info(f"  Train: {len(train_df)} rows")
            logger.info(f"  Val:   {len(val_df)} rows")
            logger.info(f"  Test:  {len(test_df)} rows")

        self.df_train = train_df
        self.df_val = val_df
        self.df_test = test_df

        return train_df, val_df, test_df

    def save_processed_data(self, train_df: pd.DataFrame, val_df: pd.DataFrame,
                           test_df: pd.DataFrame) -> None:
        """
        Save processed datasets to CSV

        Args:
            train_df: Training DataFrame
            val_df: Validation DataFrame
            test_df: Test DataFrame
        """
        processed_path = get_data_path(self.data_config['processed_path'])
        processed_path.mkdir(parents=True, exist_ok=True)

        train_path = processed_path / "train.csv"
        val_path = processed_path / "val.csv"
        test_path = processed_path / "test.csv"

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        logger.info(f"Saved processed data:")
        logger.info(f"  Train: {train_path}")
        logger.info(f"  Val:   {val_path}")
        logger.info(f"  Test:  {test_path}")

    def load_processed_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load previously processed data splits

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        processed_path = get_data_path(self.data_config['processed_path'])

        train_path = processed_path / "train.csv"
        val_path = processed_path / "val.csv"
        test_path = processed_path / "test.csv"

        logger.info("Loading processed data...")

        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)

        # Convert Date back to datetime
        for df in [train_df, val_df, test_df]:
            df['Date'] = pd.to_datetime(df['Date'])

        logger.info(f"Loaded: {len(train_df)} train, {len(val_df)} val, {len(test_df)} test")

        self.df_train = train_df
        self.df_val = val_df
        self.df_test = test_df

        return train_df, val_df, test_df

    def load_and_prepare(self, save: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Complete pipeline: load, validate, clean, and split data

        Args:
            save: Whether to save processed data to disk

        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        # Load raw data
        df = self.load_raw_data()

        # Validate
        df = self.validate_data(df)

        # Clean
        df = self.clean_data(df)

        # Print summary
        summary = self.get_data_summary(df)
        logger.info(f"Data Summary:")
        logger.info(f"  Rows: {summary['total_rows']}")
        logger.info(f"  Date range: {summary['date_range']['start']} to {summary['date_range']['end']} ({summary['date_range']['days']} days)")
        logger.info(f"  Unique flights: {summary['unique_flights']}")
        logger.info(f"  Unique products: {summary['unique_products']}")
        logger.info(f"  Avg passengers: {summary['avg_passengers']:.0f}")
        logger.info(f"  Avg waste rate: {summary['avg_waste_rate']:.2%}")

        # Split
        train_df, val_df, test_df = self.split_data(df)

        # Save if requested
        if save:
            self.save_processed_data(train_df, val_df, test_df)

        return train_df, val_df, test_df


if __name__ == "__main__":
    # Test data loader
    loader = ConsumptionDataLoader()
    train_df, val_df, test_df = loader.load_and_prepare()

    print("\n" + "="*80)
    print("DATA LOADER TEST")
    print("="*80)
    print(f"\nTrain shape: {train_df.shape}")
    print(f"Val shape:   {val_df.shape}")
    print(f"Test shape:  {test_df.shape}")
    print(f"\nTrain data preview:")
    print(train_df.head())
