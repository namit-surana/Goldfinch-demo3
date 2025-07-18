#!/usr/bin/env python3
"""
TIC Research API - Main Entry Point
"""
from src.api import app
from dotenv import load_dotenv
load_dotenv()

import uvicorn


if __name__ == "__main__":
    # Use the import string format for uvicorn
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["src"]) 