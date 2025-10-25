"""
Simple test to debug prediction issues
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.prediction_service import PredictionService

def test_prediction():
    print("="*60)
    print("Testing Prediction Service")
    print("="*60)

    try:
        # Initialize service
        print("\n[1/3] Loading prediction service...")
        service = PredictionService(model_name="xgboost")
        print("[OK] Service loaded successfully")

        # Test single prediction
        print("\n[2/3] Testing single prediction...")
        result = service.predict_single(
            passenger_count=180,
            product_id=1,
            flight_type="INTERNATIONAL",
            service_type="ECONOMY",
            origin="MEX",
            unit_cost=0.75,
            flight_date="2025-10-26"
        )
        print("[OK] Prediction successful!")
        print(f"   Predicted quantity: {result['predicted_quantity']:.2f}")
        print(f"   Confidence: {result['confidence_score']:.2%}")

        # Test batch prediction
        print("\n[3/3] Testing batch prediction...")
        batch_result = service.predict_batch(
            passenger_count=180,
            flight_type="INTERNATIONAL",
            service_type="ECONOMY",
            origin="MEX",
            flight_date="2025-10-26",
            products=[1, 2, 3]
        )
        print("[OK] Batch prediction successful!")
        print(f"   Total quantity: {batch_result['total_predicted_quantity']:.0f}")
        print(f"   Total cost: ${batch_result['total_predicted_cost']:.2f}")
        print(f"   Products predicted: {len(batch_result['predictions'])}")

        print("\n" + "="*60)
        print("ALL TESTS PASSED [OK]")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_prediction()
    sys.exit(0 if success else 1)
