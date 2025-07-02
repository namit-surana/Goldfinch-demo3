"""
Database models for Goldfinch Research API (updated to match latest schema)
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

# =====================
# USERS
# =====================
class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    preferences = Column(JSON, default={})
    hashed_password = Column(String, nullable=True)
    id_token = Column(String, nullable=True)
    token_version = Column(Integer, nullable=True)
    last_name = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    geographic_location = Column(String, nullable=True)
    email_verified = Column(Boolean, nullable=True)
    reset_code = Column(String, nullable=True)
    reset_code_expiry = Column(DateTime, nullable=True)
    industry_field = Column(String, nullable=True)
    last_modified_at = Column(DateTime(timezone=True), nullable=True)
    # Relationships
    sessions = relationship("Session", back_populates="user")
    domain_sets = relationship("DomainSet", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")

# =====================
# DOMAIN SETS
# =====================
class DomainSet(Base):
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

# =====================
# SESSIONS
# =====================
class Session(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    session_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    current_memory_id = Column(String, ForeignKey("conversation_memory.memory_id"), nullable=True)
    message_count = Column(Integer, default=0)
    starred = Column(Boolean, default=False)
    # Relationships
    user = relationship("User", back_populates="sessions")
    chat_messages = relationship("ChatMessage", back_populates="session")
    research_requests = relationship("ResearchRequest", back_populates="session")
    conversation_memories = relationship("ConversationMemory", back_populates="session")
    analytics = relationship("Analytics", back_populates="session")

# =====================
# CHAT MESSAGES
# =====================
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    message_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=True)
    is_summarized = Column(Boolean, default=False)
    reply_to = Column(String, ForeignKey("chat_messages.message_id"), nullable=True)
    type = Column(String, nullable=True)
    # Relationships
    session = relationship("Session", back_populates="chat_messages")
    research_requests = relationship("ResearchRequest", back_populates="triggering_message", foreign_keys='ResearchRequest.message_id')

# =====================
# CONVERSATION MEMORY
# =====================
class ConversationMemory(Base):
    __tablename__ = "conversation_memory"
    memory_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), nullable=False)
    summary = Column(Text, nullable=True)
    up_to_message_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    summarization_strategy = Column(String, nullable=True)
    # Relationships
    session = relationship("Session", back_populates="conversation_memories")

# =====================
# RESEARCH REQUESTS
# =====================
class ResearchRequest(Base):
    __tablename__ = "research_requests"
    request_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), nullable=False)
    message_id = Column(String, ForeignKey("chat_messages.message_id"), nullable=True)
    enhanced_query = Column(Text, nullable=False)
    workflow_type = Column(String, nullable=False)
    domain_metadata_used = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # Relationships
    session = relationship("Session", back_populates="research_requests")
    triggering_message = relationship("ChatMessage", back_populates="research_requests", foreign_keys=[message_id])
    query_logs = relationship("QueryLog", back_populates="research_request")

# =====================
# QUERY LOGS
# =====================
class QueryLog(Base):
    __tablename__ = "query_logs"
    query_id = Column(String, primary_key=True, default=generate_uuid)
    request_id = Column(String, ForeignKey("research_requests.request_id"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_type = Column(String, nullable=False)
    websites = Column(JSON, default=[])
    results = Column(Text, nullable=True)
    citations = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, default="pending")
    # Relationships
    research_request = relationship("ResearchRequest", back_populates="query_logs")

# =====================
# ANALYTICS
# =====================
class Analytics(Base):
    __tablename__ = "analytics"
    analytics_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), nullable=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    performance_data = Column(JSON, default={})
    # Relationships
    user = relationship("User", back_populates="analytics")
    session = relationship("Session", back_populates="analytics")

# =====================
# ANNOTATIONS
# =====================
class Annotation(Base):
    __tablename__ = "annotations"
    annotation_id = Column(String, primary_key=True, default=generate_uuid)
    image_id = Column(String, nullable=True)
    type = Column(String, nullable=True)
    attributes = Column(JSON, nullable=True)
    color = Column(String, nullable=True)
    label = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())
    label_id = Column(String, nullable=True)

# =====================
# CHAT ATTACHMENTS
# =====================
class ChatAttachment(Base):
    __tablename__ = "chat_attachments"
    attachment_id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    file_url = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# =====================
# CHAT FEEDBACKS
# =====================
class ChatFeedback(Base):
    __tablename__ = "chat_feedbacks"
    chat_feedback_id = Column(String, primary_key=True, default=generate_uuid)
    message_id = Column(String, nullable=True)
    is_positive = Column(Boolean, nullable=True)
    negative_reason = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# =====================
# DAILY REPORTS
# =====================
class DailyReport(Base):
    __tablename__ = "daily_reports"
    daily_report_id = Column(String, primary_key=True, default=generate_uuid)
    creator_id = Column(String, nullable=True)
    report_metadata = Column(JSON, nullable=True)
    overview_data = Column(JSON, nullable=True)
    defect_data = Column(JSON, nullable=True)
    order_info_data = Column(JSON, nullable=True)
    summary_data = Column(Text, nullable=True)
    pdf_file_path = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================
# IMAGES
# =====================
class Image(Base):
    __tablename__ = "images"
    image_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    predicted_image_id = Column(String, nullable=True)
    s3_url = Column(String, nullable=True)
    labeled = Column(Boolean, nullable=True)
    tags = Column(JSON, nullable=True)
    image_name = Column(String, nullable=True)
    image_category = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    attributes = Column(JSON, nullable=True)
    combined_image = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================
# PREDICTIONS
# =====================
class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id = Column(String, primary_key=True, default=generate_uuid)
    image_id = Column(String, nullable=True)
    defect_type = Column(String, nullable=True)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    w = Column(Float, nullable=True)
    h = Column(Float, nullable=True)

# =====================
# PROJECTS
# =====================
class Project(Base):
    __tablename__ = "projects"
    project_id = Column(String, primary_key=True, default=generate_uuid)
    creator_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    order_number = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    style_number = Column(String, nullable=True)
    production_line = Column(String, nullable=True)
    image_category = Column(String, nullable=True)
    attributes = Column(JSON, nullable=True)
    total_num_of_inspections = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================
# REFER CODES
# =====================
class ReferCode(Base):
    __tablename__ = "refer_codes"
    refer_code_id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, nullable=True)
    used = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_modified_at = Column(DateTime(timezone=True), onupdate=func.now())

# =====================
# SESSION FEEDBACKS
# =====================
class SessionFeedback(Base):
    __tablename__ = "session_feedbacks"
    session_feedback_id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, nullable=True)
    feedback_body = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) 