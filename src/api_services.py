import os
from config import API_CONFIG

class PerplexityService:
    """Service class for Perplexity AI API calls"""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set.")
        
        self.url = API_CONFIG["perplexity"]["url"]
        self.model = API_CONFIG["perplexity"]["model"]
        self.temperature = API_CONFIG["perplexity"]["temperature"]

# Lazy service instance - only created when needed
_perplexity_service = None

def get_perplexity_service():
    """Get or create Perplexity service instance"""
    global _perplexity_service
    if _perplexity_service is None:
        _perplexity_service = PerplexityService()
    return _perplexity_service

 