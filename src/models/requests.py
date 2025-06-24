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