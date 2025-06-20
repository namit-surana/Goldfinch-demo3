# Simplified Configuration for TIC Research

# Essential tools for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Provide_a_List",
            "description": "Break down a research question into focused search queries for comprehensive web research. Use this when you need to analyze multiple aspects of a complex research question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of focused search queries targeting different aspects of the research question"
                    }
                },
                "required": ["queries"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "TIC_Specific_Questions",
            "description": "Direct search for TIC-specific information using web search and domain-filtered search. Use this for straightforward questions that need direct answers from specific domains.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {
                        "type": "string",
                        "description": "The user's research question"
                    },
                    "target_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of specific domains to search within"
                    }
                },
                "required": ["user_question", "target_domains"],
                "additionalProperties": False
            }
        }
    }
]

# API Configuration
API_CONFIG = {
    "openai": {
        "model": "gpt-4"
    },
    "perplexity": {
        "url": "https://api.perplexity.ai/chat/completions",
        "model": "sonar-pro",
        "temperature": 0.1
    }
}

