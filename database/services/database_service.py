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
    # MESSAGE OPERATIONS
    # =============================================================================
    
    async def store_message(self, session_id: str, role: str, content: str, 
                          message_order: int = None, reply_to: str = None, type: str = "text") -> Dict[str, Any]:
        """Store a chat message"""
        try:
            async with self.get_session() as session:
                if message_order is None:
                    order_query = text("""
                        SELECT COALESCE(MAX(message_order), 0) + 1
                        FROM chat_messages 
                        WHERE session_id = :session_id
                    """)
                    result = await session.execute(order_query, {"session_id": session_id})
                    message_order = result.scalar()
                message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id}"
                query = text("""
                    INSERT INTO chat_messages (message_id, session_id, role, content, 
                                             message_order, timestamp, reply_to, type)
                    VALUES (:message_id, :session_id, :role, :content, 
                           :message_order, NOW(), :reply_to, :type)
                    RETURNING message_id, session_id, role, content, message_order, timestamp, reply_to, type
                """)
                result = await session.execute(query, {
                    "message_id": message_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "message_order": message_order,
                    "reply_to": reply_to,
                    "type": type
                })
                row = result.fetchone()
                await session.execute(text("""
                    UPDATE chat_sessions 
                    SET message_count = message_count + 1, updated_at = NOW()
                    WHERE session_id = :session_id
                """), {"session_id": session_id})
                return {
                    "message_id": row.message_id,
                    "session_id": row.session_id,
                    "role": row.role,
                    "content": row.content,
                    "message_order": row.message_order,
                    "timestamp": row.timestamp.isoformat(),
                    "reply_to": row.reply_to,
                    "type": row.type
                }
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            raise
 
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for context"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT message_id, role, content, message_order, timestamp, reply_to, type
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
                        "timestamp": row.timestamp.isoformat(),
                        "reply_to": row.reply_to,
                        "type": row.type
                    }
                    for row in result.fetchall()
                ]

                if len(messages) < count:
                    query = text("""
                        SELECT session_type, session_message_metadata
                        FROM chat_sessions
                        WHERE session_id = :session_id
                        LIMIT :1
                    """)
                    
                    current_session = await session.execute(query, {
                        "session_id": session_id,
                    })
                    if current_session.fetchone().session_type == "follow_up":
                        query = text("""
                            SELECT session_id, message_order
                            FROM chat_messages
                            WHERE message_id = :message_id
                            LIMIT :1
                        """)
                        source_session = await session.execute(query, {
                            "message_id": current_session.fetchone().session_message_metadata["source_message_id"],
                        })
                        session_id = result.fetchone().session_id

                        query = text("""
                            SELECT message_id, role, content, message_order, timestamp, reply_to, type
                            FROM chat_messages
                            WHERE session_id = :session_id AND message_order <= :message_order
                            ORDER BY message_order DESC
                            LIMIT :count
                        """)
                        
                        source_session_message = await session.execute(query, {
                            "session_id": source_session.fetchone().session_id,
                            "message_order": source_session.fetchone().message_order,
                            "count": count - len(messages)
                        })
                        messages = [
                            {
                                "message_id": row.message_id,
                                "role": row.role,
                                "content": row.content,
                                "message_order": row.message_order,
                                "timestamp": row.timestamp.isoformat(),
                                "reply_to": row.reply_to,
                                "type": row.type
                            }
                            for row in result.fetchall()
                        ] + messages
                    else: pass
                else: pass
 
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
                request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id}"
                
                # Serialize domain_metadata to JSON string for Postgres jsonb
                domain_metadata_json = json.dumps(domain_metadata) if domain_metadata is not None else '{}'
                
                query = text("""
                    INSERT INTO research_requests (request_id, session_id, message_id,
                                                 enhanced_query, workflow_type, 
                                                 domain_metadata_used, timestamp, status)
                    VALUES (:request_id, :session_id, :message_id, :enhanced_query,
                           :workflow_type, :domain_metadata, NOW(), 'pending')
                    RETURNING request_id
                """)
                
                result = await session.execute(query, {
                    "request_id": request_id,
                    "session_id": session_id,
                    "message_id": message_id,
                    "enhanced_query": research_question,
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
    
    async def store_query_log(self, request_id: str, query_text: str, query_type: str, websites: List[Dict] = None) -> Dict[str, Any]:
        """Store a query log entry"""
        try:
            async with self.get_session() as session:
                query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id}_{uuid.uuid4().hex[:6]}"
                
                # Serialize websites to JSON string
                websites_json = json.dumps(websites or [])
                
                query = text("""
                    INSERT INTO query_logs (query_id, request_id, query_text, query_type,
                                          websites, timestamp, status)
                    VALUES (:query_id, :request_id, :query_text, :query_type,
                           :websites, NOW(), 'pending')
                    RETURNING query_id
                """)
                
                result = await session.execute(query, {
                    "query_id": query_id,
                    "request_id": request_id,
                    "query_text": query_text,
                    "query_type": query_type,
                    "websites": websites_json
                })

                return result.scalar()
                
        except Exception as e:
            logger.error(f"Failed to store query log: {e}")
            raise
    
    async def update_query_log(self, query_id: str, results: str = None, 
                             citations: List[Dict] = None, status: str = "completed") -> bool:
        """Update query log with results"""
        try:
            async with self.get_session() as session:
                # Serialize citations to JSON string
                citations_json = json.dumps(citations or [])
                
                query = text("""
                    UPDATE query_logs 
                    SET results = :results, citations = :citations, status = :status
                    WHERE query_id = :query_id
                """)
                
                result = await session.execute(query, {
                    "query_id": query_id,
                    "results": results,
                    "citations": citations_json,
                    "status": status
                })
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update query log: {e}")
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

    # =============================================================================
    # USER DOMAIN SETS
    # =============================================================================
    
    async def create_domain_set(self, user_id: str, name: str, description: str = None,
                              domain_metadata_list: List[Dict] = None, is_default: bool = False) -> Dict[str, Any]:
        """Create a new domain set for a user"""
        try:
            async with self.get_session() as session:
                domain_set_id = f"domain_set_{user_id}_{int(datetime.now().timestamp())}"
                query = text("""
                    INSERT INTO domain_sets (domain_set_id, user_id, name, description, 
                                           domain_metadata_list, is_default, created_at, updated_at)
                    VALUES (:domain_set_id, :user_id, :name, :description, :domain_metadata_list, :is_default, NOW(), NOW())
                    RETURNING domain_set_id, name, description, is_default, created_at
                """)
                result = await session.execute(query, {
                    "domain_set_id": domain_set_id,
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                    "domain_metadata_list": json.dumps(domain_metadata_list or []),
                    "is_default": is_default
                })
                row = result.fetchone()
                return {
                    "domain_set_id": row.domain_set_id,
                    "name": row.name,
                    "description": row.description,
                    "is_default": row.is_default,
                    "created_at": row.created_at.isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to create domain set: {e}")
            raise
    
    async def get_user_domain_sets(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get domain sets for a user"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT domain_set_id, name, description, domain_metadata_list, 
                           is_default, is_shared, usage_count, created_at, updated_at
                    FROM domain_sets 
                    WHERE user_id = :user_id
                    ORDER BY is_default DESC, created_at DESC
                    LIMIT :limit
                """)
                result = await session.execute(query, {"user_id": user_id, "limit": limit})
                return [
                    {
                        "domain_set_id": row.domain_set_id,
                        "name": row.name,
                        "description": row.description,
                        "domain_metadata_list": row.domain_metadata_list,
                        "is_default": row.is_default,
                        "is_shared": row.is_shared,
                        "usage_count": row.usage_count,
                        "created_at": row.created_at.isoformat(),
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in result.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get user domain sets: {e}")
            raise

    # =============================================================================
    # MESSAGE CANCELLATION OPERATIONS
    # =============================================================================
    
    async def cancel_message(self, message_id: str, reason: str) -> bool:
        """Cancel a specific message"""
        try:
            async with self.get_session() as session:
                query = text("""
                    UPDATE chat_messages 
                    SET is_cancelled = TRUE,
                        cancellation_timestamp = NOW(),
                        cancellation_reason = :reason
                    WHERE message_id = :message_id AND role = 'user'
                """)
                result = await session.execute(query, {"reason": reason, "message_id": message_id})
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to cancel message: {e}")
            raise
    
    async def cancel_session_messages(self, session_id: str, reason: str) -> int:
        """Cancel all pending user messages in a session"""
        try:
            async with self.get_session() as session:
                query = text("""
                    UPDATE chat_messages 
                    SET is_cancelled = TRUE,
                        cancellation_timestamp = NOW(),
                        cancellation_reason = :reason
                    WHERE session_id = :session_id AND role = 'user' AND is_cancelled = FALSE
                """)
                result = await session.execute(query, {"reason": reason, "session_id": session_id})
                return result.rowcount
        except Exception as e:
            logger.error(f"Failed to cancel session messages: {e}")
            raise
    
    async def is_message_cancelled(self, message_id: str, session_id: str = None, skip_cancellation_message: bool = False) -> bool:
        """Check if a message has been cancelled and optionally store cancellation message"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT is_cancelled, session_id FROM chat_messages 
                    WHERE message_id = :message_id
                """)
                result = await session.execute(query, {"message_id": message_id})
                row = result.fetchone()
                
                if not row:
                    return False
                
                is_cancelled = row.is_cancelled
                
                # If cancelled and session_id provided, store cancellation message (unless skipped)
                if is_cancelled and session_id and not skip_cancellation_message:
                    # Check if cancellation message already exists
                    check_query = text("""
                        SELECT message_id FROM chat_messages 
                        WHERE reply_to = :message_id AND type = 'cancelled'
                    """)
                    check_result = await session.execute(check_query, {"message_id": message_id})
                    
                    if not check_result.fetchone():
                        # Store cancellation message
                        cancellation_message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id}"
                        order_query = text("""
                            SELECT COALESCE(MAX(message_order), 0) + 1
                            FROM chat_messages 
                            WHERE session_id = :session_id
                        """)
                        order_result = await session.execute(order_query, {"session_id": session_id})
                        message_order = order_result.scalar()
                        
                        insert_query = text("""
                            INSERT INTO chat_messages (message_id, session_id, role, content, 
                                                     message_order, timestamp, reply_to, type)
                            VALUES (:message_id, :session_id, :role, :content, 
                                   :message_order, NOW(), :reply_to, :type)
                        """)
                        await session.execute(insert_query, {
                            "message_id": cancellation_message_id,
                            "session_id": session_id,
                            "role": "assistant",
                            "content": "Response generation stopped by user.",
                            "message_order": message_order,
                            "reply_to": message_id,
                            "type": "cancelled"
                        })
                        
                        # Update session message count
                        await session.execute(text("""
                            UPDATE chat_sessions 
                            SET message_count = message_count + 1, updated_at = NOW()
                            WHERE session_id = :session_id
                        """), {"session_id": session_id})
                
                return is_cancelled
        except Exception as e:
            logger.error(f"Failed to check message cancellation: {e}")
            return False
    
    async def get_cancellation_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get the cancellation message for a given user message"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT message_id, session_id, role, content, message_order, timestamp, reply_to, type
                    FROM chat_messages 
                    WHERE reply_to = :message_id AND type = 'cancelled'
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                result = await session.execute(query, {"message_id": message_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "message_id": row.message_id,
                        "session_id": row.session_id,
                        "role": row.role,
                        "content": row.content,
                        "message_order": row.message_order,
                        "timestamp": row.timestamp.isoformat(),
                        "reply_to": row.reply_to,
                        "type": row.type
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get cancellation message: {e}")
            return None

# Global database service instance
_db_service = None

def get_database_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service 