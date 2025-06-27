"""
FastAPI server configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .endpoints import router
from database.api import database_endpoints

# Initialize FastAPI app
app = FastAPI(
    title="TIC Research API",
    description="An API for conducting Testing, Inspection, and Certification (TIC) research.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(database_endpoints.db_router) 