"""
API endpoints for the TIC Research API
"""

from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict, Any
from ..models import ResearchRequest, ResearchResultResponse
from ..core import DynamicTICResearchWorkflow
from .server import app


@app.post("/research", response_model=ResearchResultResponse)
async def start_research(request: ResearchRequest):
    """
    Start a new research request and get the results directly.
    This is a synchronous endpoint and may take a while to respond.
    """
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
        
        return ResearchResultResponse(**result)

    except Exception as e:
        print(f"❌ Unhandled error in /research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint to confirm the API is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "TIC Research API",
        "version": "1.0.0",
        "docs": "/docs"
    } 