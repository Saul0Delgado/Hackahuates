"""
Run the Consumption Prediction API server
"""

import sys
import uvicorn
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.api import app


if __name__ == "__main__":
    print("=" * 80)
    print("CONSUMPTION PREDICTION API SERVER")
    print("=" * 80)
    print()
    print("Starting FastAPI server...")
    print()
    print("Server will be available at: http://localhost:8000")
    print("Interactive API documentation: http://localhost:8000/docs")
    print("Alternative documentation: http://localhost:8000/redoc")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
