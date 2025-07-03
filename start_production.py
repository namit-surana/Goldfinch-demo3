#!/usr/bin/env python3
"""
TIC Research API - Production Entry Point for Render
"""

import os
import sys
import uvicorn
from src.api.server import app

def main():
    """Main entry point for production deployment"""
    
    # Get port from environment (Render sets this automatically)
    port = int(os.environ.get("PORT", 8000))
    
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY", "PERPLEXITY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Optional database variables (warn if missing but don't fail)
    db_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_db_vars = [var for var in db_vars if not os.environ.get(var)]
    
    if missing_db_vars:
        print(f"⚠️  Missing database environment variables: {', '.join(missing_db_vars)}")
        print("⚠️  Database features will be limited")
    
    print(f"🚀 Starting TIC Research API on port {port}")
    print(f"📊 Database configured: {'Yes' if not missing_db_vars else 'No'}")
    
    # Configure uvicorn for production
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        # Production settings
        workers=1,  # Render free tier works best with 1 worker
        loop="asyncio",
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30
    )

if __name__ == "__main__":
    main() 