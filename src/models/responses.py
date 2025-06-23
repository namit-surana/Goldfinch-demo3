"""
Response models for the TIC Research API
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class ResearchResultResponse(BaseModel):
    """Response model for the final research results"""
    request_id: str
    status: str
    message: str
    research_question: str
    workflow_type: Optional[str] = None
    execution_summary: Optional[Dict[str, Any]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    query_mappings: Optional[List[Dict[str, Any]]] = None
    timestamp: str
    processing_time: Optional[float] = None


class QueryMapping(BaseModel):
    """Model for query-to-website mapping"""
    query: str
    websites: List[str]


class ResearchQueries(BaseModel):
    """Model for generated research queries"""
    queries: List[str]


class QueryMappings(BaseModel):
    """Wrapper model for query mappings"""
    mappings: List[QueryMapping]


class Certification(BaseModel):
    """Model for certification data"""
    certificate_name: str
    certificate_description: str
    legal_regulation: str
    legal_text_excerpt: str
    legal_text_meaning: str
    registration_fee: str
    is_required: bool


class Certifications(BaseModel):
    """Wrapper model for certifications"""
    certifications: List[Certification] 