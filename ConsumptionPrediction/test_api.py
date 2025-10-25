"""
Test script for Consumption Prediction API

Run this after starting the API server with: python run_api.py
"""

import requests
import json
import time
from typing import Dict, Any


# API configuration
API_URL = "http://localhost:8000"
TIMEOUT = 30


class APITester:
    """Test the Consumption Prediction API"""

    def __init__(self, base_url: str = API_URL):
        """Initialize API tester"""
        self.base_url = base_url
        self.session = requests.Session()
        self.passed = 0
        self.failed = 0

    def print_header(self, text: str):
        """Print section header"""
        print("\n" + "=" * 80)
        print(f"  {text}")
        print("=" * 80)

    def print_test(self, name: str):
        """Print test name"""
        print(f"\n[TEST] {name}")

    def print_result(self, success: bool, message: str = ""):
        """Print test result"""
        status = "PASS" if success else "FAIL"
        symbol = "[OK]" if success else "[FAIL]"
        if success:
            self.passed += 1
        else:
            self.failed += 1
        print(f"  {symbol} {status}: {message}")

    def print_response(self, response: requests.Response):
        """Print response details"""
        print(f"  Status Code: {response.status_code}")
        try:
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"  Response: {response.text}")

    def test_health_check(self):
        """Test health check endpoint"""
        self.print_test("Health Check (GET /health)")

        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json()

            self.print_result(
                success and data.get('status') == 'healthy',
                f"Status: {data.get('status', 'unknown')}, Models: {data.get('models_available', [])}"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_root(self):
        """Test root endpoint"""
        self.print_test("Root Endpoint (GET /)")

        try:
            response = self.session.get(
                f"{self.base_url}/",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json()

            self.print_result(
                success,
                f"API: {data.get('name', 'unknown')}, Version: {data.get('version', 'unknown')}"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_single_prediction_basic(self):
        """Test basic single product prediction"""
        self.print_test("Single Prediction - Basic (POST /api/v1/predict)")

        request_data = {
            "passenger_count": 180,
            "product_id": 1,
            "flight_type": "INTERNATIONAL",
            "service_type": "ECONOMY",
            "origin": "MEX",
            "unit_cost": 0.75
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/predict",
                json=request_data,
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            self.print_result(
                success and 'predicted_quantity' in data,
                f"Predicted: {data.get('predicted_quantity', 'N/A'):.1f} units" if success else ""
            )

            if not success or not ('lower_bound' in data and 'upper_bound' in data):
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_single_prediction_domestic(self):
        """Test domestic flight prediction"""
        self.print_test("Single Prediction - Domestic Flight")

        request_data = {
            "passenger_count": 150,
            "product_id": 2,
            "flight_type": "DOMESTIC",
            "service_type": "BUSINESS",
            "origin": "DF",
            "unit_cost": 1.25,
            "flight_date": "2025-10-26"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/predict",
                json=request_data,
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            self.print_result(
                success and 'predicted_quantity' in data,
                f"Predicted: {data.get('predicted_quantity', 'N/A'):.1f} units"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_batch_prediction(self):
        """Test batch prediction"""
        self.print_test("Batch Prediction (POST /api/v1/predict/batch)")

        request_data = {
            "passenger_count": 200,
            "flight_type": "INTERNATIONAL",
            "service_type": "ECONOMY",
            "origin": "CUN",
            "flight_date": "2025-10-26",
            "products": [1, 2, 3, 4, 5]
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/predict/batch",
                json=request_data,
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            predictions_count = len(data.get('predictions', []))

            self.print_result(
                success and predictions_count == 5,
                f"Flight ID: {data.get('flight_id', 'N/A')}, Products: {predictions_count}/5"
            )

            if not success or predictions_count != 5:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_batch_all_products(self):
        """Test batch prediction for all products"""
        self.print_test("Batch Prediction - All Products")

        request_data = {
            "passenger_count": 180,
            "flight_type": "CHARTER",
            "service_type": "BUSINESS",
            "origin": "MEX"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/predict/batch",
                json=request_data,
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            predictions_count = len(data.get('predictions', []))

            self.print_result(
                success and predictions_count == 10,
                f"Total products predicted: {predictions_count}/10"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_feature_importance(self):
        """Test feature importance endpoint"""
        self.print_test("Feature Importance (GET /api/v1/model/feature-importance)")

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/model/feature-importance?top_n=5",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            features_count = len(data.get('top_features', {}))

            self.print_result(
                success and features_count == 5,
                f"Top features returned: {features_count}/5"
            )

            if success:
                top_feature = list(data.get('top_features', {}).items())[0]
                print(f"    Top feature: {top_feature[0]} ({top_feature[1]:.2%})")

            if not success or features_count != 5:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_model_metrics(self):
        """Test model metrics endpoint"""
        self.print_test("Model Metrics (GET /api/v1/model/metrics)")

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/model/metrics",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            ml_metrics = data.get('ml_metrics', {})

            self.print_result(
                success and 'R2' in ml_metrics,
                f"Model: {data.get('model', 'N/A')}, R²: {ml_metrics.get('R2', 'N/A')}"
            )

            if success:
                print(f"    MAE: {ml_metrics.get('MAE', 'N/A')}")
                print(f"    MAPE: {ml_metrics.get('MAPE', 'N/A')}%")

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_list_models(self):
        """Test list models endpoint"""
        self.print_test("List Models (GET /api/v1/model/list)")

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/model/list",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            models = data.get('available_models', [])

            self.print_result(
                success and len(models) > 0,
                f"Available models: {', '.join(models)}"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_switch_model(self):
        """Test model switching"""
        self.print_test("Switch Model (POST /api/v1/model/switch/ensemble)")

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/model/switch/ensemble",
                timeout=TIMEOUT
            )
            success = response.status_code == 200
            data = response.json() if success else {}

            self.print_result(
                success and data.get('success') == True,
                f"Switched to: {data.get('current_model', 'N/A')}"
            )

            if not success:
                self.print_response(response)

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def test_invalid_input(self):
        """Test invalid input handling"""
        self.print_test("Error Handling - Invalid Input")

        request_data = {
            "passenger_count": 1000,  # Invalid: > 500
            "product_id": 1,
            "flight_type": "INVALID_TYPE",
            "service_type": "ECONOMY",
            "origin": "MEX",
            "unit_cost": 0.75
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/predict",
                json=request_data,
                timeout=TIMEOUT
            )
            success = response.status_code >= 400

            self.print_result(
                success,
                f"Status: {response.status_code} (expected error)"
            )

            if success:
                print(f"    Error handled correctly")

        except Exception as e:
            self.print_result(False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests"""
        self.print_header("CONSUMPTION PREDICTION API - TEST SUITE")

        print("\n[INFO] Starting API tests...")
        print(f"[INFO] API URL: {self.base_url}")
        print(f"[INFO] Timeout: {TIMEOUT}s")

        self.print_header("BASIC HEALTH CHECKS")
        self.test_health_check()
        self.test_root()

        self.print_header("PREDICTION ENDPOINTS")
        self.test_single_prediction_basic()
        self.test_single_prediction_domestic()
        self.test_batch_prediction()
        self.test_batch_all_products()

        self.print_header("MODEL INFORMATION")
        self.test_feature_importance()
        self.test_model_metrics()

        self.print_header("MODEL MANAGEMENT")
        self.test_list_models()
        self.test_switch_model()

        self.print_header("ERROR HANDLING")
        self.test_invalid_input()

        self.print_header("TEST RESULTS")
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {percentage:.1f}%")

        if self.failed == 0:
            print("\n[OK] All tests passed!")
        else:
            print(f"\n[FAIL] {self.failed} test(s) failed")

        print("=" * 80)

        return self.failed == 0


def main():
    """Run API tests"""
    print("\n")
    print("." * 80)
    print("CONSUMPTION PREDICTION API - TEST SUITE")
    print("." * 80)
    print("\n[INFO] Make sure the API server is running:")
    print("       python run_api.py")
    print("\n[INFO] Or manually start with:")
    print("       uvicorn src.api.main:app --reload")
    print("\n")

    tester = APITester()

    try:
        # Quick connectivity test
        print("[CHECKING] Connecting to API...")
        response = requests.get(f"{API_URL}/", timeout=5)
        print("[OK] API is reachable\n")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API at", API_URL)
        print("[ERROR] Make sure the server is running with: python run_api.py")
        return False
    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        return False

    # Run all tests
    success = tester.run_all_tests()

    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
