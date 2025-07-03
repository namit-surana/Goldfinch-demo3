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
# SESSION ENDPOINTS
# =============================================================================

# @db_router.post("/sessions/create", response_model=Dict[str, Any])
# async def create_session(
#     request: CreateSessionRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Create a new chat session"""
#     try:
#         session_data = await db_service.create_session(
#             user_id=request.user_id,
#             session_name=request.session_name
#         )
#         return {
#             "success": True,
#             "session": session_data,
#             "message": "Session created successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

# @db_router.get("/sessions/{session_id}", response_model=Dict[str, Any])
# async def get_session(
#     session_id: str,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get session by ID"""
#     try:
#         session_data = await db_service.get_session_by_id(session_id)
#         if not session_data:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         return {
#             "success": True,
#             "session": session_data
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

# @db_router.put("/sessions/{session_id}", response_model=Dict[str, Any])
# async def update_session(
#     session_id: str,
#     request: UpdateSessionRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Update session"""
#     try:
#         updates = {}
#         if request.session_name is not None:
#             updates["session_name"] = request.session_name
#         if request.is_active is not None:
#             updates["is_active"] = request.is_active
#         if request.starred is not None:
#             updates["starred"] = request.starred
        
#         if not updates:
#             raise HTTPException(status_code=400, detail="No valid updates provided")
        
#         success = await db_service.update_session(session_id, updates)
#         if not success:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         return {
#             "success": True,
#             "message": "Session updated successfully"
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

# @db_router.get("/sessions/user/{user_id}", response_model=Dict[str, Any])
# async def get_user_sessions(
#     user_id: str,
#     limit: int = 50,
#     offset: int = 0,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get sessions for a user"""
#     try:
#         sessions = await db_service.get_user_sessions(user_id, limit, offset)
#         return {
#             "success": True,
#             "sessions": sessions,
#             "count": len(sessions)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get user sessions: {str(e)}")

# # =============================================================================
# # USER ENDPOINTS
# # =============================================================================

# @db_router.post("/users/create", response_model=Dict[str, Any])
# async def create_user(
#     request: CreateUserRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Create a new user"""
#     try:
#         user_data = await db_service.create_user(
#             email=request.email,
#             first_name=request.first_name,
#             last_name=request.last_name,
#             company_name=request.company_name,
#             phone_number=request.phone_number
#         )
#         return {
#             "success": True,
#             "user": user_data,
#             "message": "User created successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

# @db_router.get("/users/email/{email}", response_model=Dict[str, Any])
# async def get_user_by_email(
#     email: str,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get user by email"""
#     try:
#         user_data = await db_service.get_user_by_email(email)
#         if not user_data:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         return {
#             "success": True,
#             "user": user_data
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

# # =============================================================================
# # DOMAIN SET ENDPOINTS
# # =============================================================================

# @db_router.post("/domain-sets/create", response_model=Dict[str, Any])
# async def create_domain_set(
#     request: CreateDomainSetRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Create a new domain set"""
#     try:
#         domain_set_data = await db_service.create_domain_set(
#             user_id=request.user_id,
#             name=request.name,
#             description=request.description,
#             domain_metadata_list=request.domain_metadata_list,
#             is_default=request.is_default
#         )
#         return {
#             "success": True,
#             "domain_set": domain_set_data,
#             "message": "Domain set created successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create domain set: {str(e)}")

# @db_router.get("/domain-sets/user/{user_id}", response_model=Dict[str, Any])
# async def get_user_domain_sets(
#     user_id: str,
#     limit: int = 50,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get domain sets for a user"""
#     try:
#         domain_sets = await db_service.get_user_domain_sets(user_id, limit)
#         return {
#             "success": True,
#             "domain_sets": domain_sets,
#             "count": len(domain_sets)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get user domain sets: {str(e)}")

# =============================================================================
# MESSAGE ENDPOINTS
# =============================================================================

# @db_router.post("/messages/store", response_model=Dict[str, Any])
# async def store_message(
#     request: StoreMessageRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Store a chat message"""
#     try:
#         message_data = await db_service.store_message(
#             session_id=request.session_id,
#             role=request.role,
#             content=request.content,
#             message_order=request.message_order,
#             reply_to=request.reply_to,
#             type=request.type
#         )
#         return {
#             "success": True,
#             "message": message_data,
#             "message_text": "Message stored successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")

# @db_router.get("/messages/{session_id}", response_model=Dict[str, Any])
# async def get_session_messages(
#     session_id: str,
#     limit: int = 50,
#     offset: int = 0,
#     include_summarized: bool = True,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get messages for a session"""
#     try:
#         messages = await db_service.get_session_messages(
#             session_id, limit, offset, include_summarized
#         )
#         return {
#             "success": True,
#             "messages": messages,
#             "count": len(messages)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get session messages: {str(e)}")

# @db_router.get("/messages/{session_id}/recent", response_model=Dict[str, Any])
# async def get_recent_messages(
#     session_id: str,
#     count: int = 10,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get recent messages for context"""
#     try:
#         messages = await db_service.get_recent_messages(session_id, count)
#         return {
#             "success": True,
#             "messages": messages,
#             "count": len(messages)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get recent messages: {str(e)}")

# =============================================================================
# RESEARCH REQUEST ENDPOINTS
# =============================================================================

# @db_router.post("/research/store", response_model=Dict[str, Any])
# async def store_research_request(
#     request: StoreResearchRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Store a research request"""
#     try:
#         request_id = await db_service.store_research_request(
#             session_id=request.session_id,
#             research_question=request.enhanced_query,
#             workflow_type=request.workflow_type,
#             message_id=request.message_id,
#             domain_metadata=request.domain_metadata
#         )
#         return {
#             "success": True,
#             "request_id": request_id,
#             "message": "Research request stored successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to store research request: {str(e)}")

# @db_router.put("/research/{request_id}", response_model=Dict[str, Any])
# async def update_research_request(
#     request_id: str,
#     request: UpdateResearchRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Update research request"""
#     try:
#         updates = {}
#         if request.status is not None:
#             updates["status"] = request.status
#         if request.processing_time is not None:
#             updates["processing_time"] = request.processing_time
        
#         if not updates:
#             raise HTTPException(status_code=400, detail="No valid updates provided")
        
#         success = await db_service.update_research_request(request_id, updates)
#         if not success:
#             raise HTTPException(status_code=404, detail="Research request not found")
        
#         return {
#             "success": True,
#             "message": "Research request updated successfully"
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to update research request: {str(e)}")

# @db_router.get("/research/{request_id}", response_model=Dict[str, Any])
# async def get_research_request(
#     request_id: str,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get research request by ID"""
#     try:
#         research_data = await db_service.get_research_request(request_id)
#         if not research_data:
#             raise HTTPException(status_code=404, detail="Research request not found")
        
#         return {
#             "success": True,
#             "research_request": research_data
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get research request: {str(e)}")

# @db_router.get("/research/history/{session_id}", response_model=Dict[str, Any])
# async def get_research_history(
#     session_id: str,
#     limit: int = 10,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get research history for a session"""
#     try:
#         history = await db_service.get_research_history(session_id, limit)
#         return {
#             "success": True,
#             "research_history": history,
#             "count": len(history)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get research history: {str(e)}")

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

# @db_router.post("/analytics/log", response_model=Dict[str, Any])
# async def log_analytics_event(
#     request: LogAnalyticsRequest,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Log an analytics event"""
#     try:
#         analytics_id = await db_service.log_analytics_event(
#             event_type=request.event_type,
#             event_data=request.event_data,
#             user_id=request.user_id,
#             session_id=request.session_id,
#             ip_address=request.ip_address,
#             user_agent=request.user_agent,
#             performance_data=request.performance_data
#         )
#         return {
#             "success": True,
#             "analytics_id": analytics_id,
#             "message": "Analytics event logged successfully"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to log analytics event: {str(e)}")

# @db_router.get("/analytics/summary", response_model=Dict[str, Any])
# async def get_analytics_summary(
#     days: int = 30,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get analytics summary"""
#     try:
#         summary = await db_service.get_analytics_summary(days)
#         return {
#             "success": True,
#             "summary": summary
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@db_router.get("/health", response_model=Dict[str, Any])
async def database_health_check(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Check database health"""
    try:
        is_healthy = await db_service.test_connection()
        return {
            "success": True,
            "database": "connected" if is_healthy else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# # @db_router.get("/context/{session_id}", response_model=Dict[str, Any])
# # async def get_research_context(
#     session_id: str,
#     message_count: int = 10,
#     db_service: DatabaseService = Depends(get_database_service)
# ):
#     """Get research context for LLM (session info + recent messages + research history)"""
#     try:
#         # Get session info
#         session_data = await db_service.get_session_by_id(session_id)
#         if not session_data:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         # Get recent messages
#         recent_messages = await db_service.get_recent_messages(session_id, message_count)
        
#         # Get research history
#         research_history = await db_service.get_research_history(session_id, 5)
        
#         return {
#             "success": True,
#             "context": {
#                 "session": session_data,
#                 "recent_messages": recent_messages,
#                 "research_history": research_history,
#                 "enhanced_history": [
#                     {"role": msg["role"], "content": msg["content"]}
#                     for msg in recent_messages
#                 ]
#             }
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get research context: {str(e)}") 