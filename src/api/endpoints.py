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

router = APIRouter()

@router.post("/research", response_model=ResearchSummaryResponse)
async def start_research(request: dict):
    """
    Start a new research request and get the results with AI-generated summary.
    This endpoint expects the user message to already be stored by the frontend.
    """
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    print(f"[API] /research called with session_id: {session_id}")
    
    try:
        # Step 1: Get the last 10 messages from the database
        print("[API] Step 1: Getting last 10 messages...")
        db_service = get_database_service()
        recent_messages = await db_service.get_recent_messages(session_id, 10)
        print(f"[API] Retrieved {len(recent_messages)} recent messages")
        
        if not recent_messages:
            raise HTTPException(
                status_code=400,
                detail="No messages found in session. Please ensure the user message is stored first."
            )
        
        # Step 2: Get the latest user message (the most recent message from the user)
        latest_user_message = None
        for message in reversed(recent_messages):  # Start from the most recent
            if message.get("role") == "user":
                latest_user_message = message.get("content")
                break
        
        if not latest_user_message:
            raise HTTPException(
                status_code=400,
                detail="No user message found in recent messages. Please ensure a user message is stored first."
            )
        
        print(f"[API] Latest user message: {latest_user_message}")
        
        # Step 3: Call external RAG API with conversation history
        print("[API] Step 3: Calling external RAG API...")
        domain_metadata = await call_rag_api(recent_messages)
        print(f"[API] RAG API returned {len(domain_metadata)} domain metadata items")
        
        # Step 4: Convert domain metadata and get router decision
        print("[API] Step 4: Getting router decision...")
        
        # Convert domain metadata dictionaries to DomainMetadata objects
        domain_metadata_objects = []
        for domain_dict in domain_metadata:
            try:
                domain_obj = DomainMetadata(**domain_dict)
                domain_metadata_objects.append(domain_obj)
            except Exception as e:
                print(f"[API] Warning: Could not convert domain metadata {domain_dict.get('name', 'unknown')}: {str(e)}")
        
        # print(f"[API] Converted {len(domain_metadata_objects)} domain metadata objects")
        
        # Get router decision and enhanced query
        openai_service = OpenAIService()
        router_answer = await openai_service.get_router_decision(latest_user_message, recent_messages)
        
        if not router_answer:
            raise HTTPException(status_code=500, detail="Router decision failed")
            
        router_decision = router_answer["type"]
        enhanced_query = router_answer["content"]
        
        print(f"[API] Router decision: {router_decision}")
        print(f"[API] Enhanced query: {enhanced_query}")
        
        # Step 5: Store research request with enhanced query
        print("[API] Step 5: Storing research request...")
        request_id = await db_service.store_research_request(
            session_id=session_id,
            research_question=enhanced_query,
            workflow_type=router_decision
        )
        print(f"[API] Research request stored. Request ID: {request_id}")
        
        # Step 6: Generate parallel queries and store in query_logs
        print("[API] Step 6: Generating parallel queries...")
        parallel_queries = await openai_service.generate_research_queries(router_decision, enhanced_query)
        print(f"[API] Generated {len(parallel_queries)} parallel queries")
        
        # Store each parallel query in query_logs table with status="pending"
        query_log_ids = []
        for i, query in enumerate(parallel_queries):
            query_log = await db_service.store_query_log(
                request_id=request_id,
                query_text=query,
                query_type="parallel_search"
            )
            query_log_ids.append(query_log["query_id"])
            print(f"[API] Stored parallel query {i+1}: {query[:50]}...")
        
        # Step 7: Execute research workflow
        print("[API] Step 7: Executing research workflow...")
        workflow = DynamicTICResearchWorkflow(domain_metadata_objects)
        result = await workflow.route_research_request(latest_user_message, recent_messages)
        
        # Print the workflow output as requested
        print("="*80)
        print("RESEARCH WORKFLOW OUTPUT:")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))
        print("="*80)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Research failed - router timeout, no tool selected, or unknown tool"
            )
        
        # Step 8: Update query_logs with search results
        print("[API] Step 8: Updating query logs with search results...")
        search_results = result.get("search_results", [])
        for i, search_result in enumerate(search_results):
            if i < len(query_log_ids):
                await db_service.update_query_log(
                    query_id=query_log_ids[i],
                    results=search_result.get("result", ""),
                    citations=search_result.get("citations", []),
                    status="completed"
                )
                print(f"[API] Updated query log {i+1} with search results")
        
        # Step 9: Store assistant message with research results
        print("[API] Step 9: Storing assistant message...")
        assistant_content = result.get("summary", f"Research completed for: {latest_user_message}")
        await db_service.store_message(
            session_id=session_id,
            role="assistant",
            content=assistant_content
        )
        print("[API] Assistant message stored")
        
        # Step 10: Generate AI summary and return results
        print("[API] Step 10: Generating AI summary...")
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
        
        # TODO: Uncomment when ready to make actual API call
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         "https://fastgpt.mangrovesai.com/api/v1/chat/completions?appId=6862aa378829be5788710a6a",
        #         json=payload,
        #         headers=headers
        #     ) as response:
        #         if response.status != 200:
        #             raise Exception(f"RAG API error: {response.status}")
        #         data = await response.json()
        #         
        #         # Extract domain_metadata from responseData[3].pluginOutput.domain_metadata
        #         try:
        #             response_data = data.get("responseData", [])
        #             if len(response_data) > 3:
        #                 plugin_output = response_data[3].get("pluginOutput", {})
        #                 domain_metadata = plugin_output.get("domain_metadata", [])
        #                 print(f"[API] Extracted {len(domain_metadata)} domain metadata items from RAG API")
        #                 return domain_metadata
        #             else:
        #                 print("[API] Warning: responseData array too short, using fallback")
        #                 return []
        #         except Exception as e:
        #             print(f"[API] Error extracting domain_metadata: {str(e)}")
        #             return []
        
        # Placeholder response with the domain metadata you provided
        print("[API] Using placeholder domain metadata (RAG API call commented out)")
        return [
            {
                "name": "Responsible Sport Initiative",
                "homepage": "https://wfsgi.org/",
                "domain": "wfsgi.org",
                "region": "Global",
                "org_type": "Inter-Governmental",
                "aliases": ["RSI"],
                "industry_tags": ["ConsumerGoods"],
                "semantic_profile": "The Responsible Sport Initiative (RSI), part of the World Federation of the Sporting Goods Industry, aims to elevate corporate social responsibility within the sporting goods sector...",
                "boost_keywords": ["sporting goods sustainability", "Responsible Sport Initiative standards", "ethical compliance in sports supply"]
            },
            {
                "name": "Responsible Business Alliance (RBA)",
                "homepage": "https://www.responsiblebusiness.org",
                "domain": "responsiblebusiness.org",
                "region": "Global",
                "org_type": "NGO",
                "aliases": ["RBA", "Electronic Industry Citizenship Coalition"],
                "industry_tags": ["Electronics", "ConsumerGoods"],
                "semantic_profile": "The Responsible Business Alliance (RBA), originally founded as the Electronic Industry Citizenship Coalition, is the world's largest industry coalition dedicated to corporate social responsibility in global supply chains...",
                "boost_keywords": ["RBA Code of Conduct", "global supply chain ethics", "electronics industry responsibility"]
            }
        ]
    except Exception as e:
        print(f"❌ Error calling RAG API: {str(e)}")
        raise


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