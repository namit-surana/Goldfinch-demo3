"""
API endpoints for the TIC Research API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import asyncio
import aiohttp
from ..models import ResearchRequest, ResearchResultResponse, ResearchSummaryResponse, DomainMetadata
from ..core import DynamicTICResearchWorkflow
from ..services.openai_service import OpenAIService
from database.services import get_llm_db_service, get_database_service
import time

router = APIRouter()




async def call_rag_api(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Call external RAG API with conversation history"""
    try:
        # Prepare conversation history as text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        # Prepare request payload for the new FastGPT endpoint
        payload = {
            "stream": False,
            "details": False,
            "chatId": "test",
            "variables": {
                "query": conversation_text
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer fastgpt-gfpB42VPJmmJVR4QENoVR7kg3vnyKZV1OavJSNobw86ncLmUSRVoGv"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://fastgpt.mangrovesai.com/api/v1/chat/completions?appId=6862aa378829be5788710a6a",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"RAG API error: {response.status}")
                data = await response.json()
                
                # Extract domain_metadata from responseData[3].pluginOutput.domain_metadata
                try:
                    response_data = data.get("responseData", [])
                    if len(response_data) > 3:
                        plugin_output = response_data[3].get("pluginOutput", {})
                        domain_metadata = plugin_output.get("domain_metadata", [])
                        print(f"[API] Extracted {len(domain_metadata)} domain metadata items from RAG API")
                        return domain_metadata
                    else:
                        print("[API] Warning: responseData array too short, using fallback")
                        return []
                except Exception as e:
                    print(f"[API] Error extracting domain_metadata: {str(e)}")
                    return []
        
    except Exception as e:
        print(f"❌ Error calling RAG API: {str(e)}")
        raise


# @router.get("/sessions/{session_id}/messages")
# async def get_chat_messages(session_id: str, limit: int = 50):
#     """Get chat messages for a session"""
#     try:
#         # Placeholder response - no database connection
#         return {
#             "messages": [
#                 {
#                     "message_id": "placeholder",
#                     "role": "system",
#                     "content": "Database connection not available",
#                     "timestamp": datetime.now().isoformat(),
#                     "message_order": 0,
#                     "reply_to": None,
#                     "is_summarized": False
#                 }
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")


# @router.get("/sessions/{session_id}/research-history")
# async def get_research_history(session_id: str, limit: int = 10):
#     """Get research history for a session"""
#     try:
#         # Placeholder response - no database connection
#         return {
#             "research_history": [
#                 {
#                     "request_id": "placeholder",
#                     "enhanced_query": "Database connection not available",
#                     "workflow_type": "placeholder",
#                     "status": "placeholder",
#                     "timestamp": datetime.now().isoformat(),
#                     "processing_time": 0.0
#                 }
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving research history: {str(e)}")


# @router.post("/sessions")
# async def create_session(
#     user_email: str = "default@example.com",
#     user_name: str = "Default User",
#     session_name: Optional[str] = None
# ):
#     """Create a new chat session"""
#     try:
#         # Placeholder response - no database connection
#         return {
#             "session_id": "placeholder_session_id",
#             "user_id": "placeholder_user_id",
#             "session_name": session_name or "New Session",
#             "created_at": datetime.now().isoformat()
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


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


def get_latest_user_message(messages: list) -> Optional[str]:
    """Return the content of the most recent user message from a list of messages."""
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content")
    return None






@router.post("/chat/stream_summary")
async def chat_stream_summary(request: dict):
    """
    Streaming chat endpoint: stores user message, triggers research, and streams the entire process including summary generation.
    """
    session_id = request.get("session_id")
    content = request.get("content")
    if not session_id or not content:
        raise HTTPException(status_code=400, detail="session_id and content are required")

    async def generate_stream():
        """Generator function for streaming the complete workflow"""
        try:
            db_service = get_database_service()
            openai_service = OpenAIService()

            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your request...'})}\n\n"

            # Store user message
            user_message = await db_service.store_message(
                session_id=session_id,
                role="user",
                content=content,
                type="text"
            )
            
            yield f"data: {json.dumps({'type': 'user_message', 'data': user_message})}\n\n"

            # Get recent messages and latest user message
            recent_messages = await db_service.get_recent_messages(session_id, 7)
            recent_messages_simple = [{"role": m["role"], "content": m["content"]} for m in recent_messages]
            latest_user_message = get_latest_user_message(recent_messages_simple)
            
            if not latest_user_message:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No user message found in recent messages.'})}\n\n"
                return

            # Stream progress: Getting domain metadata
            yield f"data: {json.dumps({'type': 'status', 'message': 'Fetching domain metadata...'})}\n\n"
            
            domain_metadata = await call_rag_api(recent_messages_simple)
            from ..models.domain import DomainMetadata
            domain_metadata_objects = [DomainMetadata(**d) for d in domain_metadata]
            domain_metadata_dicts = [d.dict() for d in domain_metadata_objects]

            # Stream progress: Router decision
            yield f"data: {json.dumps({'type': 'status', 'message': 'Determining research workflow...'})}\n\n"
            
            router_start = time.time()
            router_answer = await openai_service.get_router_decision(recent_messages_simple)
            router_elapsed = time.time() - router_start
            
            if not router_answer:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Router decision failed'})}\n\n"
                return
                
            router_decision = router_answer["type"]
            enhanced_query = router_answer["content"]
            
            yield f"data: {json.dumps({'type': 'router_decision', 'workflow_type': router_decision, 'enhanced_query': enhanced_query})}\n\n"

            # Store research request
            request_id = await db_service.store_research_request(
                message_id=user_message["message_id"],
                session_id=session_id,
                research_question=enhanced_query,
                workflow_type=router_decision,
                domain_metadata=domain_metadata_dicts
            )

            if router_decision == "direct_response":
                # Stream the direct response
                yield f"data: {json.dumps({'type': 'summary_chunk', 'content': enhanced_query})}\n\n"
                
                assistant_message = await db_service.store_message(
                    session_id=session_id,
                    role="assistant",
                    content=enhanced_query,
                    reply_to=user_message["message_id"]
                )
                
                await db_service.update_research_request(
                    request_id=request_id,
                    updates={"status": "completed", "processing_time": router_elapsed}
                )
                
                yield f"data: {json.dumps({'type': 'completed', 'assistant_message': assistant_message, 'request_id': request_id})}\n\n"
                return

            # Stream progress: Research workflow
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating research queries...'})}\n\n"
            
            parallel_queries = await openai_service.generate_and_map_research_queries(router_decision, enhanced_query, domain_metadata)
            
            # Show the generated queries to the user
            generated_queries = list(set([q["query"] for q in parallel_queries]))  # Remove duplicates
            yield f"data: {json.dumps({'type': 'research_queries', 'queries': generated_queries})}\n\n"
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Executing {len(parallel_queries)} research queries...'})}\n\n"
            
            query_log_ids = [
                await db_service.store_query_log(
                    request_id=request_id,
                    query_text=query["query"],
                    query_type=query["type"],
                    websites=query["websites"]
                )
                for query in parallel_queries
            ]

            # Execute research workflow with progress updates
            from ..core import DynamicTICResearchWorkflow
            workflow = DynamicTICResearchWorkflow(domain_metadata_objects)
            
            # Add progress callback for individual search updates
            async def search_progress_callback(search_type, message):
                yield f"data: {json.dumps({'type': 'search_progress', 'search_type': search_type, 'message': message})}\n\n"
            
            result = await workflow.execute_workflow(router_decision, latest_user_message, parallel_queries)
            search_results = result.get("search_results", [])

            # Update query logs
            for i, search_result in enumerate(search_results):
                if i < len(query_log_ids):
                    await db_service.update_query_log(
                        query_id=query_log_ids[i],
                        results=search_result.get("result", ""),
                        citations=search_result.get("citations", []),
                        status=search_result.get("status", [])
                    )

            await db_service.update_research_request(
                request_id=request_id,
                updates={
                    "status": result.get("status"),
                    "processing_time": result.get("processing_time")
                }
            )

            # Stream progress: Generating summary
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating AI summary...'})}\n\n"

            # **HERE'S THE KEY: Stream the summary generation using OpenAI's streaming**
            summary_generator = openai_service.generate_research_summary_streaming(recent_messages_simple, search_results)
            
            full_summary = ""
            for chunk in summary_generator:
                if chunk:
                    full_summary += chunk
                    yield f"data: {json.dumps({'type': 'summary_chunk', 'content': chunk})}\n\n"
            
            # Store the complete assistant message
            assistant_message = await db_service.store_message(
                session_id=session_id,
                role="assistant",
                content=full_summary,
                reply_to=user_message["message_id"],
                type="text"
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'completed', 'assistant_message': assistant_message, 'research_summary': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/plain")



@router.post("/chat/send")
async def chat_send(request: dict):

    """
    Unified chat endpoint: stores user message, triggers research, stores assistant reply, returns both messages and research summary.
    """
    session_id = request.get("session_id")
    content = request.get("content")
    if not session_id or not content:
        raise HTTPException(status_code=400, detail="session_id and content are required")

    db_service = get_database_service()
    openai_service = OpenAIService()

    # Store user message
    user_message = await db_service.store_message(
        session_id=session_id,
        role="user",
        content=content,
        type="text"
    )

    # Get recent messages and latest user message
    recent_messages = await db_service.get_recent_messages(session_id, 7)
    recent_messages_simple = [{"role": m["role"], "content": m["content"]} for m in recent_messages]
    latest_user_message = get_latest_user_message(recent_messages_simple)
    if not latest_user_message:
        raise HTTPException(status_code=400, detail="No user message found in recent messages.")

    # Get domain metadata from RAG API and convert to dicts
    domain_metadata = await call_rag_api(recent_messages_simple)
    from ..models.domain import DomainMetadata
    domain_metadata_objects = [DomainMetadata(**d) for d in domain_metadata]
    domain_metadata_dicts = [d.dict() for d in domain_metadata_objects]

    # Get router decision
    router_start = time.time()
    router_answer = await openai_service.get_router_decision(recent_messages_simple)
    router_elapsed = time.time() - router_start
    if not router_answer:
        raise HTTPException(status_code=500, detail="Router decision failed")
    router_decision = router_answer["type"]
    enhanced_query = router_answer["content"]

    # Store research request
    request_id = await db_service.store_research_request(
        message_id=user_message["message_id"],
        session_id=session_id,
        research_question=enhanced_query,
        workflow_type=router_decision,
        domain_metadata=domain_metadata_dicts
    )

    if router_decision == "direct_response":
        summary = enhanced_query
        assistant_message = await db_service.store_message(
            session_id=session_id,
            role="assistant",
            content=summary,
            reply_to=user_message["message_id"]
        )
        await db_service.update_research_request(
            request_id=request_id,
            updates={"status": "completed", "processing_time": router_elapsed}
        )
        return {
            "success": True,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "research_summary": {
                "request_id": request_id,
                "status": "completed",
                "message": "Direct LLM response provided.",
                "research_question": latest_user_message,
                "workflow_type": "direct_response",
                "execution_summary": {},
                "search_results": [],
                "timestamp": datetime.now().isoformat(),
                "processing_time": router_elapsed
            },
            "summary": summary
        }

    # Otherwise, run the research workflow
    parallel_queries = await openai_service.generate_and_map_research_queries(router_decision, enhanced_query, domain_metadata)
    query_log_ids = [
        await db_service.store_query_log(
            request_id=request_id,
            query_text=query["query"],
            query_type=query["type"],
            websites=query["websites"]
        )
        for query in parallel_queries
    ]

    from ..core import DynamicTICResearchWorkflow
    workflow = DynamicTICResearchWorkflow(domain_metadata_objects)
    result = await workflow.execute_workflow(router_decision, latest_user_message, parallel_queries)
    search_results = result.get("search_results", [])

    for i, search_result in enumerate(search_results):
        if i < len(query_log_ids):
            await db_service.update_query_log(
                query_id=query_log_ids[i],
                results=search_result.get("result", ""),
                citations=search_result.get("citations", []),
                status=search_result.get("status", [])
            )

    await db_service.update_research_request(
        request_id=request_id,
        updates={
            "status": result.get("status"),
            "processing_time": result.get("processing_time")
        }
    )

    summary = await openai_service.generate_research_summary(recent_messages_simple, search_results)
    assistant_message = await db_service.store_message(
        session_id=session_id,
        role="assistant",
        content=summary,
        reply_to=user_message["message_id"],
        type="text"
    )

    return {
        "success": True,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "research_summary": result,
        "summary": summary
    } 