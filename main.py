"""Main application entry point for Data on Ice project."""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.api import app
from src.config import settings


def main():
    """Main application entry point."""
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )


if __name__ == "__main__":
    main()