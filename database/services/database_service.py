"""
Database service layer for TIC Research API
Handles all database operations with AWS RDS PostgreSQL
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging
import json  # Ensure json is imported
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        try:
            # Get database configuration from environment
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "tic_research")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            
            # Build connection string
            connection_string = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Create async engine
            self.engine = create_async_engine(
                connection_string,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # =============================================================================
    # SESSION OPERATIONS
    # =============================================================================
    
    async def create_session(self, user_id: str, title: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            async with self.get_session() as session:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"
                
                query = text("""
                    INSERT INTO sessions (session_id, user_id, title, created_at, updated_at)
                    VALUES (:session_id, :user_id, :title, NOW(), NOW())
                    RETURNING session_id, user_id, title, created_at
                """)
                
                result = await session.execute(query, {
                    "session_id": session_id,
                    "user_id": user_id,
                    "title": title or "New Session"
                })
                
                row = result.fetchone()
                return {
                    "session_id": row.session_id,
                    "user_id": row.user_id,
                    "title": row.title,
                    "created_at": row.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT session_id, user_id, title, created_at, updated_at, 
                           is_active, message_count
                    FROM sessions 
                    WHERE session_id = :session_id
                """)
                
                result = await session.execute(query, {"session_id": session_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "session_id": row.session_id,
                        "user_id": row.user_id,
                        "title": row.title,
                        "created_at": row.created_at.isoformat(),
                        "updated_at": row.updated_at.isoformat(),
                        "is_active": row.is_active,
                        "message_count": row.message_count
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            raise
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session"""
        try:
            async with self.get_session() as session:
                # Build dynamic update query
                set_clauses = []
                params = {"session_id": session_id}
                
                for key, value in updates.items():
                    if key in ["title", "is_active"]:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return False
                
                set_clauses.append("updated_at = NOW()")
                
                query = text(f"""
                    UPDATE sessions 
                    SET {', '.join(set_clauses)}
                    WHERE session_id = :session_id
                """)
                
                result = await session.execute(query, params)
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get sessions for a user"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT session_id, title, created_at, updated_at, 
                           is_active, message_count
                    FROM sessions 
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, {
                    "user_id": user_id,
                    "limit": limit,
                    "offset": offset
                })
                
                return [
                    {
                        "session_id": row.session_id,
                        "title": row.title,
                        "created_at": row.created_at.isoformat(),
                        "updated_at": row.updated_at.isoformat(),
                        "is_active": row.is_active,
                        "message_count": row.message_count
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            raise
    
    # =============================================================================
    # MESSAGE OPERATIONS
    # =============================================================================
    
    async def store_message(self, session_id: str, role: str, content: str, 
                          message_order: int = None, metadata: Dict = None) -> Dict[str, Any]:
        """Store a chat message"""
        try:
            async with self.get_session() as session:
                # Get next message order if not provided
                if message_order is None:
                    order_query = text("""
                        SELECT COALESCE(MAX(message_order), 0) + 1
                        FROM chat_messages 
                        WHERE session_id = :session_id
                    """)
                    result = await session.execute(order_query, {"session_id": session_id})
                    message_order = result.scalar()
                
                message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
                
                query = text("""
                    INSERT INTO chat_messages (message_id, session_id, role, content, 
                                             message_order, timestamp)
                    VALUES (:message_id, :session_id, :role, :content, 
                           :message_order, NOW())
                    RETURNING message_id, session_id, role, content, message_order, timestamp
                """)
                
                result = await session.execute(query, {
                    "message_id": message_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "message_order": message_order
                })
                
                row = result.fetchone()
                
                # Update session message count
                await session.execute(text("""
                    UPDATE sessions 
                    SET message_count = message_count + 1, updated_at = NOW()
                    WHERE session_id = :session_id
                """), {"session_id": session_id})
                
                return {
                    "message_id": row.message_id,
                    "session_id": row.session_id,
                    "role": row.role,
                    "content": row.content,
                    "message_order": row.message_order,
                    "timestamp": row.timestamp.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            raise
    
    async def get_session_messages(self, session_id: str, limit: int = 50, 
                                 offset: int = 0, include_summarized: bool = True) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        try:
            async with self.get_session() as session:
                where_clause = "WHERE session_id = :session_id"
                if not include_summarized:
                    where_clause += " AND is_summarized = false"
                
                query = text(f"""
                    SELECT message_id, role, content, message_order, timestamp, 
                           is_summarized
                    FROM chat_messages 
                    {where_clause}
                    ORDER BY message_order ASC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, {
                    "session_id": session_id,
                    "limit": limit,
                    "offset": offset
                })
                
                return [
                    {
                        "message_id": row.message_id,
                        "role": row.role,
                        "content": row.content,
                        "message_order": row.message_order,
                        "timestamp": row.timestamp.isoformat(),
                        "is_summarized": row.is_summarized
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            raise
    
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for context"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT message_id, role, content, message_order, timestamp
                    FROM chat_messages 
                    WHERE session_id = :session_id AND is_summarized = false
                    ORDER BY message_order DESC
                    LIMIT :count
                """)
                
                result = await session.execute(query, {
                    "session_id": session_id,
                    "count": count
                })
                
                # Return in chronological order
                messages = [
                    {
                        "message_id": row.message_id,
                        "role": row.role,
                        "content": row.content,
                        "message_order": row.message_order,
                        "timestamp": row.timestamp.isoformat()
                    }
                    for row in result.fetchall()
                ]
                
                return list(reversed(messages))  # Reverse to get chronological order
                
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            raise
    
    # =============================================================================
    # RESEARCH REQUEST OPERATIONS
    # =============================================================================
    
    async def store_research_request(self, session_id: str, research_question: str, 
                                   workflow_type: str, message_id: str = None,
                                   domain_metadata: Dict = None) -> str:
        """Store a research request"""
        try:
            async with self.get_session() as session:
                request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
                
                # Serialize domain_metadata to JSON string for Postgres jsonb
                domain_metadata_json = json.dumps(domain_metadata) if domain_metadata is not None else '{}'
                
                query = text("""
                    INSERT INTO research_requests (request_id, session_id, message_id,
                                                 enhanced_query, workflow_type, 
                                                 domain_metadata_used, timestamp, status)
                    VALUES (:request_id, :session_id, :message_id, :research_question,
                           :workflow_type, :domain_metadata, NOW(), 'pending')
                    RETURNING request_id
                """)
                
                result = await session.execute(query, {
                    "request_id": request_id,
                    "session_id": session_id,
                    "message_id": message_id,
                    "research_question": research_question,
                    "workflow_type": workflow_type,
                    "domain_metadata": domain_metadata_json  # Pass as JSON string
                })
                
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Failed to store research request: {e}")
            raise
    
    async def update_research_request(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update research request status and results"""
        try:
            async with self.get_session() as session:
                set_clauses = []
                params = {"request_id": request_id}
                
                for key, value in updates.items():
                    if key in ["status", "processing_time"]:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return False
                
                query = text(f"""
                    UPDATE research_requests 
                    SET {', '.join(set_clauses)}
                    WHERE request_id = :request_id
                """)
                
                result = await session.execute(query, params)
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update research request: {e}")
            raise
    
    async def get_research_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get research request by ID"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT request_id, session_id, message_id, enhanced_query,
                           workflow_type, domain_metadata_used, timestamp, 
                           processing_time, status
                    FROM research_requests 
                    WHERE request_id = :request_id
                """)
                
                result = await session.execute(query, {"request_id": request_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "request_id": row.request_id,
                        "session_id": row.session_id,
                        "message_id": row.message_id,
                        "research_question": row.enhanced_query,
                        "workflow_type": row.workflow_type,
                        "domain_metadata_used": row.domain_metadata_used,
                        "timestamp": row.timestamp.isoformat(),
                        "processing_time": row.processing_time,
                        "status": row.status
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get research request: {e}")
            raise
    
    async def get_research_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get research history for a session"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT request_id, enhanced_query, workflow_type,
                           status, timestamp, processing_time
                    FROM research_requests 
                    WHERE session_id = :session_id
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(query, {
                    "session_id": session_id,
                    "limit": limit
                })
                
                return [
                    {
                        "request_id": row.request_id,
                        "research_question": row.enhanced_query,
                        "workflow_type": row.workflow_type,
                        "status": row.status,
                        "timestamp": row.timestamp.isoformat(),
                        "processing_time": row.processing_time
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get research history: {e}")
            raise
    
    # =============================================================================
    # QUERY LOGS OPERATIONS
    # =============================================================================
    
    async def store_query_log(self, request_id: str, query_text: str, query_type: str, websites: List[str] = None) -> Dict[str, Any]:
        """Store a query log entry"""
        try:
            async with self.get_session() as session:
                query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id[:8]}_{uuid.uuid4().hex[:6]}"
                
                # Serialize websites to JSON string
                websites_json = json.dumps(websites or [])
                
                query = text("""
                    INSERT INTO query_logs (query_id, request_id, query_text, query_type,
                                          websites, timestamp, status)
                    VALUES (:query_id, :request_id, :query_text, :query_type,
                           :websites, NOW(), 'pending')
                    RETURNING query_id, request_id, query_text, query_type, timestamp
                """)
                
                result = await session.execute(query, {
                    "query_id": query_id,
                    "request_id": request_id,
                    "query_text": query_text,
                    "query_type": query_type,
                    "websites": websites_json
                })
                
                row = result.fetchone()
                return {
                    "query_id": row.query_id,
                    "request_id": row.request_id,
                    "query_text": row.query_text,
                    "query_type": row.query_type,
                    "timestamp": row.timestamp.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to store query log: {e}")
            raise
    
    async def update_query_log(self, query_id: str, results: str = None, 
                             citations: List[Dict] = None, status: str = "completed",
                             time_taken: float = None) -> bool:
        """Update query log with results"""
        try:
            async with self.get_session() as session:
                # Serialize citations to JSON string
                citations_json = json.dumps(citations or [])
                
                query = text("""
                    UPDATE query_logs 
                    SET results = :results, citations = :citations, status = :status,
                        time_taken = :time_taken
                    WHERE query_id = :query_id
                """)
                
                result = await session.execute(query, {
                    "query_id": query_id,
                    "results": results,
                    "citations": citations_json,
                    "status": status,
                    "time_taken": time_taken
                })
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update query log: {e}")
            raise
    
    async def get_query_logs(self, request_id: str) -> List[Dict[str, Any]]:
        """Get all query logs for a research request"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT query_id, query_text, query_type, query_order,
                           results, citations, time_taken, status, timestamp
                    FROM query_logs 
                    WHERE request_id = :request_id
                    ORDER BY query_order ASC
                """)
                
                result = await session.execute(query, {"request_id": request_id})
                
                return [
                    {
                        "query_id": row.query_id,
                        "query_text": row.query_text,
                        "query_type": row.query_type,
                        "query_order": row.query_order,
                        "results": row.results,
                        "citations": row.citations,
                        "time_taken": row.time_taken,
                        "status": row.status,
                        "timestamp": row.timestamp.isoformat()
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Failed to get query logs: {e}")
            raise
    
    # =============================================================================
    # ANALYTICS OPERATIONS
    # =============================================================================
    
    async def log_analytics_event(self, event_type: str, event_data: Dict[str, Any],
                                user_id: str = None, session_id: str = None,
                                ip_address: str = None, user_agent: str = None,
                                performance_data: Dict[str, Any] = None) -> str:
        """Log an analytics event"""
        try:
            async with self.get_session() as session:
                analytics_id = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                query = text("""
                    INSERT INTO analytics (analytics_id, user_id, session_id, event_type,
                                         event_data, timestamp, ip_address, user_agent, performance_data)
                    VALUES (:analytics_id, :user_id, :session_id, :event_type,
                           :event_data, NOW(), :ip_address, :user_agent, :performance_data)
                    RETURNING analytics_id
                """)
                
                result = await session.execute(query, {
                    "analytics_id": analytics_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "event_data": event_data or {},
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "performance_data": performance_data or {}
                })
                
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            raise
    
    async def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics summary for the last N days"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT 
                        event_type,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY event_type ORDER BY timestamp)))) as avg_interval
                    FROM analytics 
                    WHERE timestamp >= NOW() - INTERVAL ':days days'
                    GROUP BY event_type
                """)
                
                result = await session.execute(query, {"days": days})
                
                summary = {
                    "period_days": days,
                    "total_events": 0,
                    "events_by_type": {},
                    "performance_metrics": {}
                }
                
                for row in result.fetchall():
                    summary["events_by_type"][row.event_type] = {
                        "count": row.count,
                        "avg_interval_seconds": row.avg_interval
                    }
                    summary["total_events"] += row.count
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            raise


# Global database service instance
_db_service = None

def get_database_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service 