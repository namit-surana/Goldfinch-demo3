"""
LLM Database Integration Service
Provides seamless integration between LLM workflows and database operations
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database_service import get_database_service, DatabaseService


class LLMDatabaseService:
    """Service for LLM-database integration"""
    
    def __init__(self):
        self.db_service = get_database_service()
    
    # =============================================================================
    # CONTEXT MANAGEMENT
    # =============================================================================
    
    async def get_research_context(self, session_id: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Get comprehensive research context for LLM"""
        try:
            # Get session info
            session_data = await self.db_service.get_session_by_id(session_id)
            if not session_data:
                return {"enhanced_history": chat_history or []}
            
            # Get recent messages from database
            recent_messages = await self.db_service.get_recent_messages(session_id, 10)
            print(recent_messages)
            # Get research history
            research_history = await self.db_service.get_research_history(session_id, 5)
            
            # Combine chat history with database messages
            enhanced_history = []
            
            # Add database messages first (they're more recent)
            for msg in recent_messages:
                enhanced_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add provided chat history if available
            if chat_history:
                enhanced_history.extend(chat_history)
            
            # Remove duplicates (keep most recent)
            seen = set()
            unique_history = []
            for msg in reversed(enhanced_history):
                content_hash = f"{msg['role']}:{msg['content'][:50]}"
                if content_hash not in seen:
                    seen.add(content_hash)
                    unique_history.append(msg)
            
            return {
                "session": session_data,
                "recent_messages": recent_messages,
                "research_history": research_history,
                "enhanced_history": list(reversed(unique_history)),
                "context_summary": {
                    "total_messages": len(recent_messages),
                    "total_research_requests": len(research_history),
                    "session_age_hours": self._calculate_session_age(session_data["created_at"])
                }
            }
            
        except Exception as e:
            print(f"Error getting research context: {e}")
            return {"enhanced_history": chat_history or []}
    
    def _calculate_session_age(self, created_at: str) -> float:
        """Calculate session age in hours"""
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(created.tzinfo)
            return (now - created).total_seconds() / 3600
        except:
            return 0.0
    
    # =============================================================================
    # RESEARCH WORKFLOW INTEGRATION
    # =============================================================================
    
    async def start_research_workflow(self, session_id: str, research_question: str, 
                                    workflow_type: str, message_id: str = None,
                                    domain_metadata: Dict = None) -> str:
        """Start a research workflow and store initial request"""
        try:
            # Store research request
            request_id = await self.db_service.store_research_request(
                session_id=session_id,
                research_question=research_question,
                workflow_type=workflow_type,
                message_id=message_id,
                domain_metadata=domain_metadata
            )
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="research_started",
                event_data={
                    "request_id": request_id,
                    "workflow_type": workflow_type,
                    "question_length": len(research_question)
                },
                session_id=session_id
            )
            
            return request_id
            
        except Exception as e:
            print(f"Error starting research workflow: {e}")
            raise
    
    async def complete_research_workflow(self, request_id: str, result: Dict[str, Any]) -> bool:
        """Complete a research workflow and store results"""
        try:
            # Update research request with completion data
            processing_time = result.get("processing_time", 0.0)
            await self.db_service.update_research_request(
                request_id=request_id,
                updates={
                    "status": "completed",
                    "processing_time": processing_time,
                    "query_strategy": {
                        "workflow_type": result.get("workflow_type"),
                        "total_searches": len(result.get("search_results", [])),
                        "query_mappings_count": len(result.get("query_mappings", []))
                    }
                }
            )
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="research_completed",
                event_data={
                    "request_id": request_id,
                    "processing_time": processing_time,
                    "result_status": result.get("status"),
                    "search_results_count": len(result.get("search_results", [])),
                    "workflow_type": result.get("workflow_type")
                },
                session_id=result.get("session_id")
            )
            
            return True
            
        except Exception as e:
            print(f"Error completing research workflow: {e}")
            return False
    
    async def log_research_error(self, request_id: str, error_message: str, 
                               session_id: str = None) -> bool:
        """Log research error"""
        try:
            # Update research request with error status
            await self.db_service.update_research_request(
                request_id=request_id,
                updates={
                    "status": "failed",
                    "query_strategy": {"error": error_message}
                }
            )
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="research_error",
                event_data={
                    "request_id": request_id,
                    "error_message": error_message
                },
                session_id=session_id
            )
            
            return True
            
        except Exception as e:
            print(f"Error logging research error: {e}")
            return False
    
    # =============================================================================
    # MESSAGE MANAGEMENT
    # =============================================================================
    
    async def store_user_message(self, session_id: str, content: str, 
                               metadata: Dict = None) -> Dict[str, Any]:
        """Store a user message"""
        try:
            message_data = await self.db_service.store_message(
                session_id=session_id,
                role="user",
                content=content,
                metadata=metadata
            )
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="user_message",
                event_data={
                    "message_id": message_data["message_id"],
                    "content_length": len(content)
                },
                session_id=session_id
            )
            
            return message_data
            
        except Exception as e:
            print(f"Error storing user message: {e}")
            raise
    
    async def store_assistant_message(self, session_id: str, content: str, 
                                    metadata: Dict = None) -> Dict[str, Any]:
        """Store an assistant message"""
        try:
            message_data = await self.db_service.store_message(
                session_id=session_id,
                role="assistant",
                content=content,
                metadata=metadata
            )
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="assistant_message",
                event_data={
                    "message_id": message_data["message_id"],
                    "content_length": len(content)
                },
                session_id=session_id
            )
            
            return message_data
            
        except Exception as e:
            print(f"Error storing assistant message: {e}")
            raise
    
    # =============================================================================
    # PERFORMANCE MONITORING
    # =============================================================================
    
    async def log_llm_performance(self, event_type: str, performance_data: Dict[str, Any],
                                session_id: str = None, user_id: str = None) -> str:
        """Log LLM performance metrics"""
        try:
            analytics_id = await self.db_service.log_analytics_event(
                event_type=f"llm_{event_type}",
                event_data=performance_data,
                session_id=session_id,
                user_id=user_id,
                performance_data=performance_data
            )
            
            return analytics_id
            
        except Exception as e:
            print(f"Error logging LLM performance: {e}")
            return None
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a specific session"""
        try:
            # Get session info
            session_data = await self.db_service.get_session_by_id(session_id)
            if not session_data:
                return {"error": "Session not found"}
            
            # Get research history
            research_history = await self.db_service.get_research_history(session_id, 50)
            
            # Calculate metrics
            total_research_requests = len(research_history)
            completed_requests = len([r for r in research_history if r["status"] == "completed"])
            failed_requests = len([r for r in research_history if r["status"] == "failed"])
            
            avg_processing_time = 0.0
            if completed_requests > 0:
                processing_times = [r["processing_time"] for r in research_history if r["processing_time"]]
                if processing_times:
                    avg_processing_time = sum(processing_times) / len(processing_times)
            
            return {
                "session_id": session_id,
                "total_research_requests": total_research_requests,
                "completed_requests": completed_requests,
                "failed_requests": failed_requests,
                "success_rate": (completed_requests / total_research_requests * 100) if total_research_requests > 0 else 0,
                "avg_processing_time": avg_processing_time,
                "session_age_hours": self._calculate_session_age(session_data["created_at"]),
                "message_count": session_data["message_count"]
            }
            
        except Exception as e:
            print(f"Error getting session analytics: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # CACHE MANAGEMENT
    # =============================================================================
    
    async def check_result_cache(self, research_question: str, domain_metadata: Dict) -> Optional[Dict[str, Any]]:
        """Check if a similar research result exists in cache"""
        try:
            # This would integrate with a caching service (Redis, etc.)
            # For now, return None to indicate no cache hit
            return None
            
        except Exception as e:
            print(f"Error checking result cache: {e}")
            return None
    
    async def store_result_cache(self, research_question: str, domain_metadata: Dict, 
                               result: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """Store research result in cache"""
        try:
            # This would integrate with a caching service (Redis, etc.)
            # For now, return True to indicate success
            return True
            
        except Exception as e:
            print(f"Error storing result cache: {e}")
            return False
    
    # =============================================================================
    # MEMORY MANAGEMENT
    # =============================================================================
    
    async def create_conversation_memory(self, session_id: str, summary: str, 
                                       up_to_message_order: int) -> str:
        """Create a conversation memory snapshot"""
        try:
            # This would integrate with the conversation_memory table
            # For now, return a placeholder ID
            memory_id = f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
            
            # Log analytics event
            await self.db_service.log_analytics_event(
                event_type="memory_created",
                event_data={
                    "memory_id": memory_id,
                    "summary_length": len(summary),
                    "up_to_message_order": up_to_message_order
                },
                session_id=session_id
            )
            
            return memory_id
            
        except Exception as e:
            print(f"Error creating conversation memory: {e}")
            return None
    
    async def get_conversation_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation memory for a session"""
        try:
            # This would integrate with the conversation_memory table
            # For now, return None to indicate no memory
            return None
            
        except Exception as e:
            print(f"Error getting conversation memory: {e}")
            return None


# Global LLM database service instance
_llm_db_service = None

def get_llm_db_service() -> LLMDatabaseService:
    """Get or create LLM database service instance"""
    global _llm_db_service
    if _llm_db_service is None:
        _llm_db_service = LLMDatabaseService()
    return _llm_db_service 