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
from ..models import DomainMetadata
from ..core import DynamicTICResearchWorkflow
from ..services.openai_service import OpenAIService
from database.services import get_database_service
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


@router.post("/chat/cancel")
async def cancel_request(request: dict):
    """Cancel a user message or all messages in a session"""
    try:
        message_id = request.get("message_id")
        session_id = request.get("session_id")
        reason = request.get("reason", "User requested cancellation")
        
        if not message_id and not session_id:
            raise HTTPException(
                status_code=400, 
                detail="Either message_id or session_id is required"
            )
        
        db_service = get_database_service()
        cancelled_count = 0
        if message_id:
            success = await db_service.cancel_message(message_id, reason)
            cancelled_count = 1 if success else 0
        elif session_id:
            cancelled_count = await db_service.cancel_session_messages(session_id, reason)
        return {
            "status": "success" if cancelled_count > 0 else "no_active_requests",
            "cancelled_count": cancelled_count,
            "message": f"Cancelled {cancelled_count} request(s)"
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error cancelling request: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel request")


@router.post("/chat/stream_summary")
async def chat_stream_summary(request: dict):
    session_id = request.get("session_id")
    content = request.get("content")
    if not session_id or not content:
        raise HTTPException(status_code=400, detail="session_id and content are required")

    async def generate_stream():
        db_service = get_database_service()
        openai_service = OpenAIService()
        message_id = None
        try:
            # Store user message
            user_message = await db_service.store_message(
                session_id=session_id,
                role="user",
                content=content,
                type="text"
            )
            message_id = user_message["message_id"]
            yield f"data: {json.dumps({'type': 'user_message', 'data': user_message})}\n\n"

            # Check cancellation before any processing
            if await db_service.is_message_cancelled(message_id, session_id):
                # Get the cancellation message that was stored
                cancellation_message = await db_service.get_cancellation_message(message_id)
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled before processing', 'assistant_message': cancellation_message})}\n\n"
                return

            # Get recent messages
            recent_messages = await db_service.get_recent_messages(session_id, 7)
            recent_messages_simple = [{"role": m["role"], "content": m["content"]} for m in recent_messages]
            latest_user_message = get_latest_user_message(recent_messages_simple)
            if not latest_user_message:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No user message found in recent messages.'})}\n\n"
                return

            # Check cancellation before RAG call
            if await db_service.is_message_cancelled(message_id, session_id):
                # Get the cancellation message that was stored
                cancellation_message = await db_service.get_cancellation_message(message_id)
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled before RAG call', 'assistant_message': cancellation_message})}\n\n"
                return

            # Stream progress: Getting domain metadata
            yield f"data: {json.dumps({'type': 'status', 'message': 'Fetching domain metadata...'})}\n\n"
            domain_metadata = await call_rag_api(recent_messages_simple)

            # Check cancellation after RAG call
            if await db_service.is_message_cancelled(message_id, session_id):
                # Get the cancellation message that was stored
                cancellation_message = await db_service.get_cancellation_message(message_id)
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled after RAG call', 'assistant_message': cancellation_message})}\n\n"
                return

            from ..models.domain import DomainMetadata
            domain_metadata_objects = [DomainMetadata(**d) for d in domain_metadata]
            domain_metadata_dicts = [d.dict() for d in domain_metadata_objects]

            # Stream progress: Router decision
            yield f"data: {json.dumps({'type': 'status', 'message': 'Determining research workflow...'})}\n\n"
            router_start = time.time()
            router_answer = await openai_service.get_router_decision(recent_messages_simple)
            router_elapsed = time.time() - router_start

            # Check cancellation after router decision
            if await db_service.is_message_cancelled(message_id, session_id):
                # Get the cancellation message that was stored
                cancellation_message = await db_service.get_cancellation_message(message_id)
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled after router decision', 'assistant_message': cancellation_message})}\n\n"
                return

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
            
            # Store query logs for tracking individual queries
            query_log_ids = []

            if router_decision == "direct_response":
                # Check for cancellation before direct response
                if await db_service.is_message_cancelled(message_id, session_id):
                    # Get the cancellation message that was stored
                    cancellation_message = await db_service.get_cancellation_message(message_id)
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user', 'assistant_message': cancellation_message})}\n\n"
                    return
                
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
            
            # Check for cancellation before starting research
            if await db_service.is_message_cancelled(message_id, session_id):
                # Get the cancellation message that was stored
                cancellation_message = await db_service.get_cancellation_message(message_id)
                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user', 'assistant_message': cancellation_message})}\n\n"
                return
            
            # Execute research workflow with cancellation support
            workflow = DynamicTICResearchWorkflow(domain_metadata_objects)
            
            async def search_progress_callback(search_type, message):
                """Callback for search progress updates"""
                # Check for cancellation in callback
                if await db_service.is_message_cancelled(message_id, session_id):
                    raise Exception("Request cancelled during search")
                
                # Note: We can't yield here since this is called from the workflow
                # The workflow will handle progress updates internally
            
            try:
                # Execute workflow with cancellation support
                research_result = await workflow.route_research_request_with_progress(
                    enhanced_query, 
                    recent_messages_simple, 
                    search_progress_callback
                )
                
                # Check for cancellation after research
                if await db_service.is_message_cancelled(message_id, session_id):
                    # Get the cancellation message that was stored
                    cancellation_message = await db_service.get_cancellation_message(message_id)
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled by user', 'assistant_message': cancellation_message})}\n\n"
                    return
                
                if research_result:
                    # Store query logs from workflow result
                    if research_result.get("search_tasks"):
                        query_log_ids = [
                            await db_service.store_query_log(
                                request_id=request_id,
                                query_text=task["query"],
                                query_type=task["type"],
                                websites=task["websites"]
                            )
                            for task in research_result["search_tasks"]
                        ]
                    
                    # Stream progress: Generating summary
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Generating summary...'})}\n\n"
                    
                    # Generate summary with streaming
                    summary_stream = openai_service.generate_research_summary_streaming(
                        recent_messages_simple, research_result
                    )
                    
                    full_summary = ""
                    async for chunk in summary_stream:
                        # Check for cancellation during summary generation
                        if await db_service.is_message_cancelled(message_id, session_id, skip_cancellation_message=True):
                            # Store partial summary if we have any content
                            if full_summary.strip():
                                # Store the partial summary as assistant message
                                partial_message = await db_service.store_message(
                                    session_id=session_id,
                                    role="assistant",
                                    content=full_summary + "\n\n[Generation stopped by user]",
                                    reply_to=user_message["message_id"],
                                    type="partial"
                                )
                                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled during summary generation', 'assistant_message': partial_message})}\n\n"
                            else:
                                # No partial content, get the cancellation message
                                cancellation_message = await db_service.get_cancellation_message(message_id)
                                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Request cancelled during summary generation', 'assistant_message': cancellation_message})}\n\n"
                            return
                            
                        full_summary += chunk
                        yield f"data: {json.dumps({'type': 'summary_chunk', 'content': chunk})}\n\n"
                    
                    # Store assistant message
                    assistant_message = await db_service.store_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_summary,
                        reply_to=user_message["message_id"]
                    )
                    
                    # Update query logs with results
                    if query_log_ids and research_result.get("search_results"):
                        for i, search_result in enumerate(research_result["search_results"]):
                            if i < len(query_log_ids):
                                await db_service.update_query_log(
                                    query_id=query_log_ids[i],
                                    results=search_result.get("result", ""),
                                    citations=search_result.get("citations", []),
                                    status=search_result.get("status", "completed")
                                )
                    
                    # Update research request as completed
                    await db_service.update_research_request(
                        request_id=request_id,
                        updates={"status": "completed", "processing_time": time.time() - router_start}
                    )
                    
                    yield f"data: {json.dumps({'type': 'completed', 'assistant_message': assistant_message, 'request_id': request_id})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Research workflow failed'})}\n\n"
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred during processing'})}\n\n"

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