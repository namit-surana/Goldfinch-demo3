"""
Perplexity AI service integration
"""

import os
import aiohttp
import json
import re
from typing import List, Dict, Any, Optional
from ..config import API_CONFIG
from ..models.responses import Certifications


class PerplexityService:
    """Service class for Perplexity AI API calls"""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set.")
        
        self.url = API_CONFIG["perplexity"]["url"]
        self.model = API_CONFIG["perplexity"]["model"]
        self.temperature = API_CONFIG["perplexity"]["temperature"]
    
    async def search(self, query: str, domains: Optional[List[str]] = None, 
                    prompt: Optional[str] = None, use_structured_output: bool = False) -> Dict[str, Any]:
        """Async Perplexity search using aiohttp with optional domain filtering, custom prompt, and structured output"""
        print("[PERPLEXITY SERVICE] search called with:", query, domains, prompt, use_structured_output)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use provided prompt or default to list general prompt
        from ..config import PERPLEXITY_LIST_GENERAL_PROMPT
        system_prompt = prompt or PERPLEXITY_LIST_GENERAL_PROMPT
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        # Add structured output if requested
        if use_structured_output:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"schema": Certifications.model_json_schema()}
            }
        
        # Add domain filter if domains are provided
        if domains:
            body["search_domain_filter"] = domains
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, json=body) as response:
                print("[PERPLEXITY SERVICE] HTTP response status:", response.status)
                data = await response.json()
                print("[PERPLEXITY SERVICE] response data:", data)
                
                # Extract content and citations from response
                content = data['choices'][0]['message']['content']
                citations = data.get('citations', [])
                
                # If using structured output, parse with Pydantic
                if use_structured_output:
                    parsed_data = json.loads(content)
                    certifications = Certifications(**parsed_data)
                    structured_content = json.dumps([cert.dict() for cert in certifications.certifications], indent=2)
                    print("[PERPLEXITY SERVICE] structured_content:", structured_content)
                    return {
                        "content": structured_content,
                        "citations": citations,
                        "parsed_certifications": certifications.certifications
                    }
                else:
                    return {
                        "content": content,
                        "citations": citations
                    }
    
    def extract_links_from_content(self, content: str) -> List[str]:
        """Extract URLs from content using regex"""
        url_pattern = r'https?://[^\s\]\)\,\;\"\'\<\>]+'
        links = re.findall(url_pattern, content)
        return list(set(links))  # Remove duplicates


# Lazy service instance - only created when needed
_perplexity_service = None

def get_perplexity_service() -> PerplexityService:
    """Get or create Perplexity service instance"""
    global _perplexity_service
    if _perplexity_service is None:
        _perplexity_service = PerplexityService()
    return _perplexity_service 