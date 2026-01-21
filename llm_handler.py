"""
LLM handler module for interacting with Groq or Google Gemini API
"""
from typing import List, Optional
import requests
import time


def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = initial_delay * (2 ** attempt)
            print(f"[Retry] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)


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
            # Use requests directly instead of Groq SDK for better compatibility
            self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
            self.groq_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model_name)

    def _get_system_prompt(self) -> str:
        """Get the enhanced system prompt for better response quality"""
        return """You are the official AI assistant for IIT Bombay's Sustainability Cell. Your role is to help students, faculty, and visitors learn about sustainability initiatives on campus.

CRITICAL RULES - NEVER VIOLATE THESE:
1. ONLY provide information that is EXPLICITLY mentioned in the context provided
2. NEVER make up, guess, or hallucinate information like email addresses, phone numbers, URLs, or contact details
3. If information is NOT in the context, say "I don't have that specific information" - DO NOT guess
4. NEVER invent statistics, numbers, or counts that aren't in the context
5. If asked for contact info and it's not in the context, say "Please check our official website or social media for contact details"

PERSONALITY & TONE:
- Be friendly, approachable, and enthusiastic about sustainability
- Keep responses concise and well-structured (use bullet points for lists)
- Be professional but not overly formal

RESPONSE GUIDELINES:
- Answer ONLY based on the provided context
- Use bullet points or numbered lists for multiple items
- Keep responses under 200 words unless more detail is specifically requested
- If information is missing, clearly state that you don't have it

FORMATTING:
- Use **bold** for important names, dates, or key terms
- Use bullet points for lists of 3+ items

ABOUT SUSTAINABILITY CELL:
- Part of IIT Bombay's student body (Gymkhana)
- Focuses on campus sustainability, environmental awareness, and green initiatives"""

    def _generate_groq(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using Groq API with requests library"""
        def make_request():
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3  # Lower temperature to reduce hallucination
            }
            response = requests.post(
                self.groq_url,
                headers=self.groq_headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        return retry_with_backoff(make_request, max_retries=3, initial_delay=2)

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
            prompt = f"""Answer the user's question using ONLY the information from the context below.

IMPORTANT:
- ONLY use facts explicitly stated in the context
- If information is not in the context, say "I don't have that specific information"
- NEVER make up email addresses, phone numbers, URLs, statistics, or any other details
- If asked for contact info not in context, say "Please check our official website or social media"

Context:
{context}

Question: {query}

Answer (maximum {max_length} words, use ONLY information from context):"""
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
            prompt = f"""Answer the user's question using ONLY the information from the context below.

IMPORTANT:
- ONLY use facts explicitly stated in the context
- If information is not in the context, say "I don't have that specific information"
- NEVER make up email addresses, phone numbers, URLs, statistics, or any other details
- If asked for contact info not in context, say "Please check our official website or social media"

Context from documents:
{context}

Conversation History:
{history_str}

Current Question: {query}

Answer (maximum {max_length} words, use ONLY information from context):"""
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


    def generate_fallback_response(self, query: str, conversation_history: List[dict] = None) -> str:
        """
        Generate a helpful fallback response when no relevant context is found.
        Suggests related topics the user might want to ask about.

        Args:
            query: User's question
            conversation_history: Previous conversation messages

        Returns:
            Helpful fallback response with suggestions
        """
        # Build history string if available
        history_str = ""
        if conversation_history:
            recent_history = conversation_history[-4:]
            for msg in recent_history:
                role = "User" if msg['role'] == 'user' else "Assistant"
                history_str += f"{role}: {msg['content']}\n"

        prompt = f"""The user asked a question but I couldn't find specific information about it in our knowledge base.

User's Question: {query}

{f"Conversation History:{chr(10)}{history_str}" if history_str else ""}

Please provide a helpful response that:
1. Acknowledges you don't have specific information about their query
2. Briefly explains what Sustainability Cell does (if relevant)
3. Suggests 2-3 related topics they CAN ask about, such as:
   - Team members and structure
   - Events (Green Cup, workshops, competitions)
   - GESH Fellowship program
   - Campus sustainability projects
   - How to join or contact Sustainability Cell

Keep the response friendly and under 100 words."""

        try:
            if self.provider == "groq":
                return self._generate_groq(prompt, max_tokens=512)
            else:
                return self._generate_gemini(prompt)
        except Exception as e:
            return "I don't have specific information about that. You can ask me about Sustainability Cell's team, events like Green Cup, the GESH Fellowship, or how to get involved!"


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
