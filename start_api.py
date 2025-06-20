#!/usr/bin/env python3
"""
Startup script for TIC Research API Server
"""

import uvicorn
import sys
from pathlib import Path

# Add the 'src' directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

if __name__ == "__main__":
    print("🚀 Starting TIC Research API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("============================================================")
    
    # Use the import string format for uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["src"]) 