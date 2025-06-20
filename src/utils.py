import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    try:
        load_dotenv()
    except ImportError:
        print("Note: python-dotenv not installed. Install with: pip install python-dotenv")
        print("Or set environment variables manually.")

def check_environment():
    """Check if all required environment variables are set"""
    openai_key = os.getenv("OPENAI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    missing_keys = []
    
    if not openai_key:
        missing_keys.append("OPENAI_API_KEY")
    if not perplexity_key:
        missing_keys.append("PERPLEXITY_API_KEY")
    
    if missing_keys:
        print("❌ Error: Missing environment variables:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease set them using one of these methods:")
        print("1. Set environment variables manually")
        print("2. Create a .env file with your API keys")
        print("3. Get API keys from:")
        print("   - OpenAI: https://platform.openai.com/api-keys")
        print("   - Perplexity: https://www.perplexity.ai/settings/api")
        return False
    
    return True

def print_separator(title=""):
    """Print a formatted separator line"""
    if title:
        print(f"\n{'='*50}")
        print(f" {title}")
        print(f"{'='*50}")
    else:
        print(f"\n{'='*50}")

def truncate_text(text, max_length=100):
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..." 