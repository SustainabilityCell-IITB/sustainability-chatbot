"""
Configuration settings for IIT Bombay Sustainability Cell Chatbot
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Document settings
DOCUMENT_FILE = "ilovepdf_merged.txt"  # Name of the file in data folder
DOCUMENT_PATH = os.path.join(DATA_DIR, DOCUMENT_FILE)

# Model settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = "AIzaSyBzP6iPnrlVisRlOSRhXUGJYuIFIlspiiM"

# Text processing settings
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Retrieval settings
TOP_K_CHUNKS = 5
SIMILARITY_THRESHOLD = 0.45

# Server settings
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
DEBUG_MODE = True
