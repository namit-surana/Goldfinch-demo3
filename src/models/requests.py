"""
Request models for the TIC Research API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from .domain import DomainMetadata


class ResearchRequest(BaseModel):
    """Main research request model"""
    research_question: str = Field(
        ..., 
        description="The research question to investigate"
    )
    domain_list_metadata: List[DomainMetadata] = Field(
        ..., 
        description="List of domain metadata for TIC websites"
    )
    chat_history: List[Dict[str, str]] = Field(
        default=[], description="Previous chat messages for context")


class ChatStreamRequest(BaseModel):
    """Request model for streaming chat endpoint"""
    session_id: str = Field(..., description="Unique session identifier")
    content: str = Field(..., description="User message content")


class CancelRequest(BaseModel):
    """Request model for cancelling requests"""
    message_id: Optional[str] = Field(None, description="Specific message ID to cancel")
    session_id: Optional[str] = Field(None, description="Session ID to cancel all messages")
    reason: str = Field(default="User requested cancellation", description="Reason for cancellation")


class ChatSendRequest(BaseModel):
    """Request model for non-streaming chat endpoint"""
    session_id: str = Field(..., description="Unique session identifier")
    content: str = Field(..., description="User message content")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")


class RootResponse(BaseModel):
    """Response model for root endpoint"""
    message: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    docs: str = Field(..., description="Documentation URL")
    database: str = Field(..., description="Database connection status")


class CancelResponse(BaseModel):
    """Response model for cancellation endpoint"""
    status: str = Field(..., description="Cancellation status")
    cancelled_count: int = Field(..., description="Number of requests cancelled")
    message: str = Field(..., description="Cancellation message")


class StreamEvent(BaseModel):
    """Model for streaming events"""
    type: str = Field(..., description="Event type")
    message: Optional[str] = Field(None, description="Event message")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    assistant_message: Optional[Dict[str, Any]] = Field(None, description="Assistant message data")


class ChatMessage(BaseModel):
    """Model for chat messages"""
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session identifier")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    type: Optional[str] = Field(None, description="Message type")
    reply_to: Optional[str] = Field(None, description="ID of message this replies to")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ResearchSummary(BaseModel):
    """Model for research summary"""
    request_id: str = Field(..., description="Research request ID")
    status: str = Field(..., description="Research status")
    message: Optional[str] = Field(None, description="Status message")
    research_question: str = Field(..., description="Research question")
    workflow_type: str = Field(..., description="Workflow type used")
    execution_summary: Dict[str, Any] = Field(default_factory=dict, description="Execution details")
    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    timestamp: str = Field(..., description="Timestamp")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ChatSendResponse(BaseModel):
    """Response model for non-streaming chat endpoint"""
    success: bool = Field(..., description="Success status")
    user_message: ChatMessage = Field(..., description="Stored user message")
    assistant_message: ChatMessage = Field(..., description="Stored assistant message")
    research_summary: ResearchSummary = Field(..., description="Research summary")
    summary: str = Field(..., description="Generated summary text")