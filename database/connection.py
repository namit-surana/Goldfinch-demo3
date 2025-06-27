"""
Database connection utilities for Goldfinch Research API
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Make sure environment variables are set manually.")

def get_database_url() -> str:
    """Get database URL from environment variables"""
    # For AWS RDS PostgreSQL
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "goldfinch_research")
    username = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"

def get_engine():
    """Create SQLAlchemy engine"""
    database_url = get_database_url()
    
    # For development/testing, you might want to use SQLite
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        database_url = "sqlite:///./goldfinch_research.db"
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("DB_ECHO", "false").lower() == "true"
    )

def get_session() -> Session:
    """Get database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# Global engine instance
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 