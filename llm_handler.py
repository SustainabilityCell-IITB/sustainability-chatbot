"""
LLM handler module for interacting with Groq or Google Gemini API
"""
from typing import List, Optional
from groq import Groq


class LLMHandler:
    """Handles interactions with LLM (Groq or Gemini)"""

    def __init__(self, api_key: str, model_name: str, provider: str = "groq"):
        """
        Initialize the LLM handler.

        Args:
            api_key: API key for the LLM provider
            model_name: Name of the model to use
            provider: LLM provider ("groq" or "gemini")
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self.client = None

        if provider == "groq":
            self.client = Groq(api_key=api_key)
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name)

    def _generate_groq(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using Groq API"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for IIT Bombay's Sustainability Cell. Be conversational and friendly while staying professional."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def _generate_gemini(self, prompt: str) -> str:
        """Generate response using Gemini API"""
        response = self.client.generate_content(prompt)
        return response.text.strip()

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
            prompt = f"""Answer the user's question based on the following context from official documents.
If the question is a greeting or general query, respond naturally and helpfully.

Context:
{context}

Question: {query}

Answer (maximum {max_length} words):"""
        else:
            # Handle queries without relevant context (greetings, general questions)
            prompt = f"""The user's question may not be directly related to specific documents.
Respond naturally and helpfully.

Question: {query}

Answer (maximum {max_length} words):"""

        try:
            if self.provider == "groq":
                return self._generate_groq(prompt)
            else:
                return self._generate_gemini(prompt)
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def generate_response_with_history(self, query: str, context_chunks: List[str],
                                      conversation_history: List[dict],
                                      max_length: int = 500) -> str:
        """
        Generate a response using the LLM with context and conversation history.

        Args:
            query: User's current question
            context_chunks: Relevant text chunks to use as context
            conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
            max_length: Maximum length of the response

        Returns:
            Generated response text
        """
        # Build conversation history string
        history_str = ""
        if conversation_history:
            # Only include last 6 messages (3 exchanges) to avoid token limits
            recent_history = conversation_history[-6:]
            for msg in recent_history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                history_str += f"{role}: {msg['content']}\n"

        # Build the prompt with context and history
        if context_chunks:
            context = "\n\n".join(context_chunks)
            prompt = f"""Answer the user's question based on the following context from official documents and the conversation history.
If the question is a greeting or general query, respond naturally and helpfully.
Use the conversation history to understand context and provide coherent responses.

Context from documents:
{context}

Conversation History:
{history_str}

Current Question: {query}

Answer (maximum {max_length} words):"""
        else:
            # Handle queries without relevant context (greetings, general questions)
            prompt = f"""The user's question may not be directly related to specific documents.
Respond naturally and helpfully.
Use the conversation history to maintain context.

Conversation History:
{history_str}

Current Question: {query}

Answer (maximum {max_length} words):"""

        try:
            if self.provider == "groq":
                return self._generate_groq(prompt)
            else:
                return self._generate_gemini(prompt)
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
            if self.provider == "groq":
                return self._generate_groq(prompt)
            else:
                return self._generate_gemini(prompt)
        except Exception as e:
            return f"Error: {str(e)}"


def create_llm_handler(api_key: str, model_name: str, provider: str = "groq") -> LLMHandler:
    """
    Factory function to create an LLM handler.

    Args:
        api_key: API key for the LLM provider
        model_name: Name of the model
        provider: LLM provider ("groq" or "gemini")

    Returns:
        Initialized LLMHandler instance
    """
    return LLMHandler(api_key, model_name, provider)
