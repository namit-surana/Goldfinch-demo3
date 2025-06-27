"""
API endpoints for the TIC Research API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import asyncio
from ..models import ResearchRequest, ResearchResultResponse, ResearchSummaryResponse
from ..core import DynamicTICResearchWorkflow
from ..services.openai_service import OpenAIService

router = APIRouter()

@router.post("/research", response_model=ResearchSummaryResponse)
async def start_research(request: ResearchRequest):
    """
    Start a new research request and get the results with AI-generated summary.
    This is a synchronous endpoint and may take a while to respond.
    """
    print("[API] /research called with request:", request)
    
    try:
        # Initialize dynamic workflow with provided domain metadata
        workflow = DynamicTICResearchWorkflow(request.domain_list_metadata)
        
        # Process the research request and wait for the result
        result = await workflow.route_research_request(request.research_question, request.chat_history)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Research failed - router timeout, no tool selected, or unknown tool"
            )
        
        print("[API] /research result:", result)
        
        # Generate AI summary of the research results
        openai_service = OpenAIService()
        summary = await openai_service.generate_research_summary(result)
        
        # Create summary response
        summary_response = ResearchSummaryResponse(
            request_id=result.get('request_id'),
            status=result.get('status'),
            message=result.get('message'),
            research_question=result.get('research_question'),
            workflow_type=result.get('workflow_type'),
            execution_summary=result.get('execution_summary'),
            summary=summary,
            timestamp=result.get('timestamp'),
            processing_time=result.get('processing_time')
        )
        
        print("[API] /research summary response:", summary_response)
        return summary_response

    except Exception as e:
        print(f"❌ Unhandled error in /research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/research/stream")
async def start_research_stream(request: ResearchRequest):
    """
    Start a new research request with Server-Sent Events streaming.
    Streams progress updates and final summary.
    """
    print("[API] /research/stream called with request:", request)
    
    async def generate_stream():
        try:
            # Send initial event
            yield f"data: {json.dumps({'event': 'research_started', 'data': {'request_id': 'pending', 'message': f'Research started for: {request.research_question}', 'timestamp': datetime.now().isoformat()}})}\n\n"
            
            # Initialize workflow
            workflow = DynamicTICResearchWorkflow(request.domain_list_metadata)
            
            # Create a queue for progress events
            progress_queue = asyncio.Queue()
            
            async def progress_callback(event: str, data: Dict[str, Any]):
                """Callback to send progress events"""
                await progress_queue.put({
                    'event': event,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Process research with progress callbacks
            result = await workflow.route_research_request_with_progress(
                request.research_question, 
                request.chat_history,
                progress_callback=progress_callback
            )
            
            if result is None:
                yield f"data: {json.dumps({'event': 'research_failed', 'data': {'message': 'Research failed - router timeout or unknown error', 'timestamp': datetime.now().isoformat()}})}\n\n"
                return
            
            # Send summary generation event
            yield f"data: {json.dumps({'event': 'summary_generation', 'data': {'message': 'Generating AI summary...', 'timestamp': datetime.now().isoformat()}})}\n\n"
            
            # Generate AI summary
            openai_service = OpenAIService()
            summary = await openai_service.generate_research_summary(result)
            
            # Send final result
            final_data = {
                'request_id': result.get('request_id'),
                'status': result.get('status'),
                'message': result.get('message'),
                'research_question': result.get('research_question'),
                'workflow_type': result.get('workflow_type'),
                'execution_summary': result.get('execution_summary'),
                'summary': summary,
                'timestamp': result.get('timestamp'),
                'processing_time': result.get('processing_time')
            }
            
            yield f"data: {json.dumps({'event': 'research_completed', 'data': final_data})}\n\n"
            
        except Exception as e:
            print(f"❌ Error in research stream: {str(e)}")
            yield f"data: {json.dumps({'event': 'research_error', 'data': {'message': f'An error occurred: {str(e)}', 'timestamp': datetime.now().isoformat()}})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(session_id: str, limit: int = 50):
    """Get chat messages for a session"""
    try:
        # Placeholder response - no database connection
        return {
            "messages": [
                {
                    "message_id": "placeholder",
                    "role": "system",
                    "content": "Database connection not available",
                    "timestamp": datetime.now().isoformat(),
                    "message_order": 0,
                    "reply_to": None,
                    "is_summarized": False
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")


@router.get("/sessions/{session_id}/research-history")
async def get_research_history(session_id: str, limit: int = 10):
    """Get research history for a session"""
    try:
        # Placeholder response - no database connection
        return {
            "research_history": [
                {
                    "request_id": "placeholder",
                    "enhanced_query": "Database connection not available",
                    "workflow_type": "placeholder",
                    "status": "placeholder",
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": 0.0
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving research history: {str(e)}")


@router.post("/sessions")
async def create_session(
    user_email: str = "default@example.com",
    user_name: str = "Default User",
    title: Optional[str] = None
):
    """Create a new chat session"""
    try:
        # Placeholder response - no database connection
        return {
            "session_id": "placeholder_session_id",
            "user_id": "placeholder_user_id",
            "title": title or "New Session",
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint to confirm the API is running"""
    print("[API] /health called")
    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "disconnected"
    }
    print("[API] /health result:", result)
    return result


@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TIC Research API",
        "version": "1.0.0",
        "docs": "/docs",
        "database": "disconnected"
    } 