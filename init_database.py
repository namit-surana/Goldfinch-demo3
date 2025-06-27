#!/usr/bin/env python3
"""
Database initialization script for Goldfinch Research API
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.connection import engine
from database.models import Base
from sqlalchemy import text

def init_database():
    """Initialize the database with all tables"""
    print("🚀 Initializing Goldfinch Research Database...")
    
    try:
        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Test database connection
        print("🔍 Testing database connection...")
        with engine.connect() as connection:
            if os.getenv("USE_SQLITE", "false").lower() == "true":
                # SQLite doesn't have version() function, use a simple query instead
                result = connection.execute(text("SELECT 1;"))
                print("✅ Database connected successfully! SQLite database ready.")
            else:
                result = connection.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                print(f"✅ Database connected successfully! PostgreSQL version: {version}")
        
        print("🎉 Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your database credentials in environment variables")
        print("2. Ensure your RDS instance is running and accessible")
        print("3. Verify security group allows connections from your EC2 instance")
        print("4. For local development, set USE_SQLITE=true")
        sys.exit(1)

def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    try:
        from database.connection import get_session
        from database.models import User, DomainSet
        from database.services.database_service import get_database_service
        
        db = get_session()
        database_service = get_database_service()
        
        # Create a sample user
        user = database_service.get_or_create_user(
            db, 
            email="test@example.com", 
            name="Test User"
        )
        
        # Create a sample domain set
        sample_domains = [
            {
                "name": "GlobalGAP",
                "domain": "globalgap.org",
                "region": "Global",
                "org_type": "Certification Body",
                "aliases": ["GLOBALGAP", "Global GAP"],
                "industry_tags": ["Agriculture", "Food Safety"],
                "semantic_profile": "International food safety certification standards",
                "boost_keywords": ["certification", "food safety", "agriculture"]
            },
            {
                "name": "UL Solutions",
                "domain": "ul.com",
                "region": "Global",
                "org_type": "Testing & Certification",
                "aliases": ["Underwriters Laboratories", "UL"],
                "industry_tags": ["Safety", "Testing", "Certification"],
                "semantic_profile": "Safety science and testing certification",
                "boost_keywords": ["safety", "testing", "certification", "standards"]
            }
        ]
        
        domain_set = DomainSet(
            user_id=user.user_id,
            name="Sample TIC Domains",
            description="Sample domain set for testing",
            domain_metadata_list=sample_domains,
            is_default=True
        )
        
        db.add(domain_set)
        db.commit()
        
        print("✅ Sample data created successfully!")
        print(f"   - User: {user.email}")
        print(f"   - Domain Set: {domain_set.name}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()

if __name__ == "__main__":
    print("=" * 50)
    print("Goldfinch Research Database Initialization")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars and os.getenv("USE_SQLITE", "false").lower() != "true":
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables or use USE_SQLITE=true for local development")
        sys.exit(1)
    
    # Initialize database
    init_database()
    
    # Ask if user wants sample data
    if input("\n🤔 Create sample data for testing? (y/N): ").lower().startswith('y'):
        create_sample_data()
    
    print("\n🎯 Next steps:")
    print("1. Update your .env file with the correct database credentials")
    print("2. Run your API server: python start_api.py")
    print("3. Test the database integration with a research request") 