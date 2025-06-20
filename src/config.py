# Simplified Configuration for TIC Research

# Essential tools for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Provide_a_List",
            "description": "Return only the full list of certifications / approvals needed for the product and market described in `query`.",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One **concise yet complete** English sentence that faithfully restates the user’s request: include product type, key technical specs (voltage, materials, dimensions, etc.), country of origin, and destination market. Use *only* information explicitly provided by the user—do **NOT** invent or guess missing details."
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
            "name": "Search_the_Internet",
            "description": "Perform a live web search and return up-to-date results (title, snippet, URL).",
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
                        "description": "One clear English sentence that *describes exactly what information needs to be found* Include every critical fact given by the user—do **NOT** invent or omit details."
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

