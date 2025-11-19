# auth.py
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env in project root

def get_api_key():
    """
    Returns the GENAI API key (from .env or environment).
    Also ensures the environment variable is set for ADK to pick up.
    """
    key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GENAI_API_KEY (or GOOGLE_API_KEY) not set. Create a .env with GENAI_API_KEY=your_key")
    # ensure ADK / genai libs can find it via env
    os.environ["GENAI_API_KEY"] = key
    os.environ["GOOGLE_API_KEY"] = key
    return key
