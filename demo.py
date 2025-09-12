"""Demo application entry point for Data on Ice project."""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.api.demo_app import app


def main():
    """Main demo application entry point."""
    import uvicorn
    
    print("🏒 Starting Data on Ice Demo Application")
    print("📊 ISU Archive Transformation Platform")
    print("🤖 Powered by Alibaba Cloud AI Technologies")
    print()
    print("🌐 Access the web interface at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()