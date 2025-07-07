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


# Configure CORS with extended settings
origins = [
    "http://localhost:3000",
    "http://localhost:5175",
    "http://73.226.206.254:5175",
    "https://project.mangrovesai.com",
    "https://www.mangrovesai.com",
    "https://mangrovesai.com"
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "If-None-Match",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(router)
app.include_router(database_endpoints.db_router) 