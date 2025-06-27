"""
Database API Package
Contains all database-related API endpoints and routers
"""

from .database_endpoints import db_router

__all__ = [
    'db_router'
] 