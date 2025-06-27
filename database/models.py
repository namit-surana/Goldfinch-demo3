"""
Database models for Goldfinch Research API
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())

class User(Base):
    """User table"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())
    preferences = Column(JSON, default={})
    default_domain_set_id = Column(String, ForeignKey("domain_sets.domain_set_id"), nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    domain_sets = relationship("DomainSet", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")

class Session(Base):
    """Session table"""
    __tablename__ = "sessions"
    
    session_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    current_memory_id = Column(String, ForeignKey("conversation_memory.memory_id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    chat_messages = relationship("ChatMessage", back_populates="session")
    research_requests = relationship("ResearchRequest", back_populates="session")
    conversation_memories = relationship("ConversationMemory", back_populates="session")
    analytics = relationship("Analytics", back_populates="session")

class ChatMessage(Base):
    """Chat message table"""
    __tablename__ = "chat_messages"
    
    message_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=True)
    reply_to = Column(String, nullable=True)
    is_summarized = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("Session", back_populates="chat_messages")
    research_requests = relationship("ResearchRequest", back_populates="triggering_message")

class ConversationMemory(Base):
    """Conversation memory table"""
    __tablename__ = "conversation_memory"
    
    memory_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    summary = Column(Text, nullable=True)
    up_to_message_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    summarization_strategy = Column(String, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="conversation_memories")

class ResearchRequest(Base):
    """Research request table"""
    __tablename__ = "research_requests"
    
    request_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    message_id = Column(String, ForeignKey("chat_messages.message_id"), nullable=True)
    enhanced_query = Column(Text, nullable=False)
    workflow_type = Column(String, nullable=False)
    domain_metadata_used = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")
    
    # Relationships
    session = relationship("Session", back_populates="research_requests")
    triggering_message = relationship("ChatMessage", back_populates="research_requests")
    query_logs = relationship("QueryLog", back_populates="research_request")

class QueryLog(Base):
    """Query log table"""
    __tablename__ = "query_logs"
    
    query_id = Column(String, primary_key=True, default=generate_uuid)
    request_id = Column(String, ForeignKey("research_requests.request_id"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_type = Column(String, nullable=False)
    websites = Column(JSON, default=[])
    time_taken = Column(Float, nullable=True)
    results = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, default="pending")
    
    # Relationships
    research_request = relationship("ResearchRequest", back_populates="query_logs")

class DomainSet(Base):
    """Domain set table"""
    __tablename__ = "domain_sets"
    
    domain_set_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    domain_metadata_list = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_default = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="domain_sets")

class Analytics(Base):
    """Analytics table"""
    __tablename__ = "analytics"
    
    analytics_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    performance_data = Column(JSON, default={})
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    session = relationship("Session", back_populates="analytics") 