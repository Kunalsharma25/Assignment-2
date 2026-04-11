import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from environment variables."""
    # Ensure .env is loaded
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        # In a real app, we'd raise an error.
        # For the demo, we might want to allow it to run up to the scraping part.
        logger.warning("OPENAI_API_KEY is missing or using placeholder in .env.")
    
    config = {
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "max_tokens_per_chunk": int(os.getenv("MAX_TOKENS_PER_CHUNK", 1000)),
        "request_delay": float(os.getenv("REQUEST_DELAY_SECONDS", 2.0)),
        "max_retries": int(os.getenv("MAX_RETRIES", 3))
    }
    
    return config
