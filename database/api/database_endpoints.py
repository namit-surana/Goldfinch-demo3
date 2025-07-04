"""
Independent database endpoints for LLM communication
These endpoints allow the LLM to interact directly with the database
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.database_service import get_database_service, DatabaseService

# Create router for database endpoints
db_router = APIRouter(prefix="/db", tags=["database"])

# =============================================================================
# REQUEST MODELS
# =============================================================================

class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    session_name: Optional[str] = Field(None, description="Session name")

class UpdateSessionRequest(BaseModel):
    session_name: Optional[str] = None
    is_active: Optional[bool] = None
    starred: Optional[bool] = None

class StoreMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    message_order: Optional[int] = Field(None, description="Message order")
    reply_to: Optional[str] = Field(None, description="Message ID this message replies to")
    type: Optional[str] = Field(None, description="Message type")

class StoreResearchRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    enhanced_query: str = Field(..., description="Enhanced research query")
    workflow_type: str = Field(..., description="Workflow type")
    message_id: Optional[str] = Field(None, description="Triggering message ID")
    domain_metadata: Optional[Dict[str, Any]] = Field(default={}, description="Domain metadata used")

class UpdateResearchRequest(BaseModel):
    status: Optional[str] = None
    processing_time: Optional[float] = None

class LogAnalyticsRequest(BaseModel):
    event_type: str = Field(..., description="Event type")
    event_data: Dict[str, Any] = Field(default={}, description="Event data")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    performance_data: Optional[Dict[str, Any]] = Field(default={}, description="Performance data")

class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    company_name: Optional[str] = Field(None, description="Company name")
    phone_number: Optional[str] = Field(None, description="Phone number")

class CreateDomainSetRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    name: str = Field(..., description="Domain set name")
    description: Optional[str] = Field(None, description="Domain set description")
    domain_metadata_list: Optional[List[Dict[str, Any]]] = Field(default=[], description="Domain metadata list")
    is_default: Optional[bool] = Field(False, description="Whether this is the default domain set")

# =============================================================================
# ACTIVE ENDPOINTS
# =============================================================================

@db_router.get("/health", response_model=Dict[str, Any])
async def database_health_check(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Check database connectivity"""
    try:
        # Test basic database connection
        result = await db_service.test_connection()
        return {
            "success": True,
            "status": "healthy" if result else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "message": "Database connection test successful" if result else "Database connection failed"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Database health check failed: {str(e)}"
        }
