"""
Configuration settings for IIT Bombay Sustainability Cell Chatbot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Website URLs to scrape (add your URLs here)
# Example: WEBSITE_URLS = ["https://www.iitb.ac.in/sustainability", "https://example.com/page"]
WEBSITE_URLS = [
    # Add URLs here, e.g.:
    # "https://www.iitb.ac.in/en/about-iit-bombay/sustainability",
    "https://gesh.iitb.ac.in/",
    "https://gymkhana.iitb.ac.in/~sustainabilitycell/"
]

# Model settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# LLM Provider: "groq" or "gemini"
LLM_PROVIDER = "groq"

# Groq settings (recommended - fast and free)
GROQ_MODEL = "llama-3.3-70b-versatile"  # Best quality model on Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Gemini settings (backup)
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Text processing settings
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Retrieval settings
TOP_K_CHUNKS = 7
SIMILARITY_THRESHOLD = 0.30  # Lower threshold for better recall

# Feature flags for memory optimization (disable for low-memory deployments)
USE_RERANKER = os.getenv("USE_RERANKER", "false").lower() == "true"  # Disabled by default for production
USE_HYBRID_SEARCH = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"

# Server settings
FLASK_HOST = os.getenv("HOST", "0.0.0.0")  # 0.0.0.0 for production
FLASK_PORT = int(os.getenv("PORT", 5000))  # Render uses PORT env var
DEBUG_MODE = os.getenv("FLASK_ENV", "development") == "development"

# CORS settings - allowed origins for cross-origin requests
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")  # Comma-separated list or "*" for all
