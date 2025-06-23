"""
Domain metadata models for TIC websites
"""

from pydantic import BaseModel
from typing import List


class DomainMetadata(BaseModel):
    """Model for TIC website metadata"""
    name: str
    homepage: str
    domain: str
    region: str
    org_type: str
    aliases: List[str] = []
    industry_tags: List[str] = []
    semantic_profile: str
    boost_keywords: List[str] = [] 