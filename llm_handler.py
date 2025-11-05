"""
LLM handler module for interacting with Google Gemini API
"""
from typing import List, Optional
import google.generativeai as genai


class LLMHandler:
    """Handles interactions with Google Gemini LLM"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the LLM handler.
        
        Args:
            api_key: Google Gemini API key
            model_name: Name of the Gemini model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        
        # Configure API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, query: str, context_chunks: List[str], 
                         max_length: int = 500) -> str:
        """
        Generate a response using the LLM with provided context.
        
        Args:
            query: User's question
            context_chunks: Relevant text chunks to use as context
            max_length: Maximum length of the response
            
        Returns:
            Generated response text
        """
        # Build the prompt with context
        if context_chunks:
            context = "\n\n".join(context_chunks)
            prompt = f"""You are a helpful assistant for IIT Bombay's Sustainability Cell. 
Answer the user's question based on the following context from official documents.
If the question is a greeting or general query, respond naturally and helpfully.
Be conversational and friendly while staying professional.

Context:
{context}

Question: {query}

Answer (maximum {max_length} words):"""
        else:
            # Handle queries without relevant context (greetings, general questions)
            prompt = f"""You are a helpful assistant for IIT Bombay's Sustainability Cell.
The user's question may not be directly related to specific documents.
Respond naturally and helpfully. Be conversational and friendly while staying professional.

Question: {query}

Answer (maximum {max_length} words):"""
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_simple_response(self, query: str, context: Optional[str] = None) -> str:
        """
        Generate a simple response with optional context.
        
        Args:
            query: User's question
            context: Optional context string
            
        Returns:
            Generated response text
        """
        if context:
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        else:
            prompt = query
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"


def create_llm_handler(api_key: str, model_name: str) -> LLMHandler:
    """
    Factory function to create an LLM handler.
    
    Args:
        api_key: Google Gemini API key
        model_name: Name of the Gemini model
        
    Returns:
        Initialized LLMHandler instance
    """
    return LLMHandler(api_key, model_name)
