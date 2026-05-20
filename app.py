"""
Hugging Face Spaces entry point for IIT Bombay Sustainability Cell Chatbot
This file is used by Hugging Face Spaces to run the Flask app
"""
from main import app, initialize_chatbot

# Initialize on import (Hugging Face runs this file directly)
initialize_chatbot()

# For Hugging Face Spaces
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
