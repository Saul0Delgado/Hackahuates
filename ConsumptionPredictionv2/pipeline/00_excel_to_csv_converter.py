"""
Excel to CSV Converter
=====================

Converts large Excel files to CSV format for faster processing.
This speeds up data loading by 10-100x compared to reading Excel directly.

Usage:
    python 00_excel_to_csv_converter.py

Author: ML Pipeline
Date: 2025-10-25
"""

import pandas as pd
from pathlib import Path
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\Docs\Hackathon_ConsumptionandEstimationv2')
OUTPUT_DIR = Path(r'C:\Users\garza\Documents\Hackahuates\ConsumptionPredictionv2\data\raw')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONVERSION FUNCTION
# ============================================================================

def convert_excel_to_csv():
    """Convert Excel files to CSV format"""

    print("=" * 70)
    print("EXCEL TO CSV CONVERTER")
    print("=" * 70)

    # Find Excel files
    excel_files = sorted(list(DATA_DIR.glob('*.xlsx')))

    if len(excel_files) == 0:
        print(f"\n[ERROR] No Excel files found in: {DATA_DIR}")
        return

    print(f"\n[OK] Found {len(excel_files)} Excel files to convert")

    for excel_file in excel_files:
        csv_output = OUTPUT_DIR / f"{excel_file.stem}.csv"

        # Skip if already converted
        if csv_output.exists():
            print(f"\n[SKIP] Already converted: {csv_output.name}")
            continue

        print(f"\n[CONVERT] Converting: {excel_file.name}")
        print(f"           => {csv_output.name}")

        try:
            # Read Excel (this is the slow part)
            start_time = time.time()
            print("        Reading Excel file...")
            df = pd.read_excel(excel_file)
            read_time = time.time() - start_time

            print(f"        [DONE] Read complete ({read_time:.1f}s)")
            print(f"        - Rows: {len(df):,}")
            print(f"        - Columns: {len(df.columns)}")
            print(f"        - Size: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

            # Write to CSV (very fast)
            print("        Writing to CSV...")
            write_start = time.time()
            df.to_csv(csv_output, index=False)
            write_time = time.time() - write_start

            print(f"        [DONE] Write complete ({write_time:.1f}s)")
            print(f"        [SUCCESS] Conversion successful!")

        except Exception as e:
            print(f"        [ERROR] {e}")
            continue

    print("\n" + "=" * 70)
    print("[SUCCESS] CSV CONVERSION COMPLETE")
    print("=" * 70)
    print(f"\nCSV files saved to: {OUTPUT_DIR}")
    print("\nNow update EDA scripts to use CSV instead of Excel:")
    print("  Change: pd.read_excel(file)")
    print("  To:     pd.read_csv(file)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    convert_excel_to_csv()
