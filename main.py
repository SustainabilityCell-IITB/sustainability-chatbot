"""
Main entry point for IIT Bombay Sustainability Cell Chatbot
"""
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import config
from document_loader import load_all_sources
from text_processor import preprocess_document_with_sources
from embedder import create_embedder
from retriever import create_retriever
from llm_handler import create_llm_handler
from cache_manager import create_cache_manager
import secrets
import time
import re

# Input validation constants
MAX_QUERY_LENGTH = 1000  # Maximum characters allowed
MIN_QUERY_LENGTH = 2     # Minimum characters required


def sanitize_query(query: str) -> tuple:
    """
    Sanitize and validate user input.

    Args:
        query: Raw user input

    Returns:
        Tuple of (sanitized_query, error_message)
        If error_message is not None, the query is invalid
    """
    if not query:
        return None, "Query cannot be empty"

    # Remove null bytes and other control characters
    query = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', query)

    # Strip whitespace and normalize spaces
    query = ' '.join(query.split())

    # Check length constraints
    if len(query) < MIN_QUERY_LENGTH:
        return None, "Query is too short. Please ask a complete question."

    if len(query) > MAX_QUERY_LENGTH:
        return None, f"Query is too long. Please keep it under {MAX_QUERY_LENGTH} characters."

    # Remove potential prompt injection patterns (basic protection)
    # This catches attempts to override system prompts
    injection_patterns = [
        r'ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)',
        r'disregard\s+(all\s+)?(previous|above|prior)',
        r'you\s+are\s+now\s+in\s+',
        r'new\s+instructions?:',
        r'system\s*:\s*',
    ]

    query_lower = query.lower()
    for pattern in injection_patterns:
        if re.search(pattern, query_lower):
            return None, "Invalid query format. Please ask a genuine question."

    return query, None

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# Enable CORS for cross-origin requests (needed when frontend is on different domain)
CORS(app, origins=config.ALLOWED_ORIGINS, supports_credentials=True)

# Global variables for caching
chunks = None
chunk_sources = None
chunk_embeddings = None
embedder = None
retriever = None
llm_handler = None

# Store conversation histories (in production, use a database)
conversations = {}


def initialize_chatbot():
    """Initialize all chatbot components"""
    global chunks, chunk_sources, chunk_embeddings, embedder, retriever, llm_handler

    start_time = time.time()

    print("=" * 60)
    print("Initializing IIT Bombay Sustainability Cell Chatbot")
    print("=" * 60)

    # Initialize cache manager
    cache_manager = create_cache_manager()

    # Load documents from data folder and URLs
    print(f"\n1. Loading documents from: {config.DATA_DIR}")
    if config.WEBSITE_URLS:
        print(f"   Also loading from {len(config.WEBSITE_URLS)} URL(s)")
    try:
        text, sources = load_all_sources(config.DATA_DIR, config.WEBSITE_URLS)
        print(f"   [OK] Loaded {len(sources['files'])} file(s): {', '.join(sources['files'])}")
        if sources['urls']:
            print(f"   [OK] Loaded {len(sources['urls'])} URL(s)")
        print(f"   [OK] Total content: {len(text)} characters")
    except Exception as e:
        print(f"   [ERROR] Error loading documents: {e}")
        raise

    # Check if we can use cached embeddings
    print(f"\n2. Checking embedding cache...")
    cache_valid = cache_manager.is_cache_valid(
        text, config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.EMBEDDING_MODEL
    )

    if cache_valid:
        print("   [OK] Valid cache found! Loading from cache...")
        cached_data = cache_manager.load_cache()
        if cached_data:
            chunks, chunk_sources, chunk_embeddings = cached_data
            print(f"   [OK] Loaded {len(chunks)} chunks from cache")
            print(f"   [OK] Loaded embeddings (shape: {chunk_embeddings.shape})")

            # Still need to initialize embedder for query embedding
            print(f"\n3. Initializing embedding model: {config.EMBEDDING_MODEL}")
            embedder = create_embedder(config.EMBEDDING_MODEL)
            print(f"   [OK] Embedder initialized")
        else:
            cache_valid = False  # Cache load failed, regenerate

    if not cache_valid:
        # Chunk text with source tracking
        print(f"\n2. Chunking text (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
        try:
            chunks, chunk_sources = preprocess_document_with_sources(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            print(f"   [OK] Created {len(chunks)} chunks with source tracking")
        except Exception as e:
            print(f"   [ERROR] Error chunking text: {e}")
            raise

        # Create embedder
        print(f"\n3. Initializing embedding model: {config.EMBEDDING_MODEL}")
        try:
            embedder = create_embedder(config.EMBEDDING_MODEL)
            print(f"   [OK] Embedder initialized")
        except Exception as e:
            print(f"   [ERROR] Error initializing embedder: {e}")
            raise

        # Generate embeddings
        print(f"\n4. Generating embeddings for {len(chunks)} chunks")
        try:
            chunk_embeddings = embedder.embed_texts(chunks)
            print(f"   [OK] Embeddings generated (shape: {chunk_embeddings.shape})")
        except Exception as e:
            print(f"   [ERROR] Error generating embeddings: {e}")
            raise

        # Save to cache for next startup
        print(f"\n5. Saving to cache...")
        cache_manager.save_cache(
            chunks, chunk_sources, chunk_embeddings,
            text, config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.EMBEDDING_MODEL
        )
    
    # Create retriever with source tracking
    step = 6 if not cache_valid else 4
    print(f"\n{step}. Initializing retriever")
    print(f"   Hybrid search: {config.USE_HYBRID_SEARCH}, Reranking: {config.USE_RERANKER}")
    try:
        retriever = create_retriever(
            chunks, chunk_embeddings,
            use_hybrid=config.USE_HYBRID_SEARCH,
            use_reranker=config.USE_RERANKER,
            chunk_sources=chunk_sources
        )
        print(f"   [OK] Retriever initialized")
    except Exception as e:
        print(f"   [ERROR] Error initializing retriever: {e}")
        raise

    # Create LLM handler based on provider
    if config.LLM_PROVIDER == "groq":
        model_name = config.GROQ_MODEL
        api_key = config.GROQ_API_KEY
    else:
        model_name = config.GEMINI_MODEL
        api_key = config.GEMINI_API_KEY

    step += 1
    print(f"\n{step}. Initializing LLM: {model_name} ({config.LLM_PROVIDER})")
    try:
        llm_handler = create_llm_handler(api_key, model_name, config.LLM_PROVIDER)
        print(f"   [OK] LLM handler initialized")
    except Exception as e:
        print(f"   [ERROR] Error initializing LLM: {e}")
        raise

    # Calculate startup time
    startup_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("Chatbot initialized successfully!")
    print("=" * 60)
    print(f"Settings:")
    print(f"  - Top-k chunks: {config.TOP_K_CHUNKS}")
    print(f"  - Similarity threshold: {config.SIMILARITY_THRESHOLD}")
    print(f"  - Server: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"  - Startup time: {startup_time:.2f} seconds" + (" (cached)" if cache_valid else ""))
    print("=" * 60 + "\n")


@app.route('/')
def home():
    """Serve the chatbot UI"""
    # Create a new session ID for each visitor
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
        conversations[session['session_id']] = []
    return render_template('index.html')


def build_contextual_query(user_query: str, conversation_history: list, max_context_turns: int = 2) -> str:
    """
    Build an enhanced query by including recent conversation context.
    This helps with vague follow-up questions like "Tell me their names".
    """
    if not conversation_history:
        return user_query

    # Get the last few exchanges for context
    recent_context = []
    turn_count = 0

    # Go through history in reverse to get most recent exchanges
    for i in range(len(conversation_history) - 1, -1, -2):
        if turn_count >= max_context_turns:
            break
        if i >= 1:
            # Get user message (should be at even indices: 0, 2, 4...)
            user_msg = conversation_history[i-1].get('content', '') if conversation_history[i-1].get('role') == 'user' else ''
            if user_msg:
                recent_context.insert(0, user_msg)
                turn_count += 1

    if recent_context:
        # Combine recent context with current query for better retrieval
        context_str = " ".join(recent_context)
        enhanced_query = f"{context_str} {user_query}"
        return enhanced_query

    return user_query


@app.route('/api/query', methods=['POST'])
def query():
    """Handle chatbot queries with conversation history"""
    try:
        # Get query from request
        data = request.json
        raw_query = data.get('query', '')

        # Get session ID - support both Flask session and request body (for CORS)
        session_id = data.get('session_id') or session.get('session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['session_id'] = session_id

        if session_id not in conversations:
            conversations[session_id] = []

        # Sanitize and validate input
        user_query, error = sanitize_query(raw_query)
        if error:
            print(f"\n[Rejected] {error} | Input: {raw_query[:50]}...")
            return jsonify({'error': error}), 400

        print(f"\n[Query] {user_query}")

        # Get conversation history
        conversation_history = conversations.get(session_id, [])

        # Build contextual query for better retrieval on follow-up questions
        contextual_query = build_contextual_query(user_query, conversation_history)
        if contextual_query != user_query:
            print(f"[Context] Enhanced query: {contextual_query[:80]}...")

        # Embed the contextual query for better retrieval
        query_embedding = embedder.embed_text(contextual_query)

        # Retrieve relevant chunks using hybrid search (semantic + BM25)
        relevant_chunks, scores, sources = retriever.retrieve(
            query_embedding,
            top_k=config.TOP_K_CHUNKS,
            threshold=config.SIMILARITY_THRESHOLD,
            query_text=contextual_query
        )

        # Check if we found relevant context
        max_score = scores[0] if scores else 0.0
        use_fallback = False

        if relevant_chunks:
            print(f"[Retrieval] Found {len(relevant_chunks)} relevant chunks")
            for i, (score, source) in enumerate(zip(scores, sources), 1):
                print(f"  Chunk {i}: similarity = {score:.4f} | Source: {source}")

            # Use fallback if best score is very low (poor relevance)
            if max_score < 0.35:
                use_fallback = True
                print(f"[Fallback] Low relevance score ({max_score:.4f}), using fallback response")
        else:
            print(f"[Retrieval] No chunks above threshold ({config.SIMILARITY_THRESHOLD})")
            use_fallback = True

        # Generate response - use fallback for low relevance queries
        if use_fallback:
            response = llm_handler.generate_fallback_response(
                user_query,
                conversation_history
            )
        else:
            response = llm_handler.generate_response_with_history(
                user_query,
                relevant_chunks,
                conversation_history
            )
        
        print(f"[Response] {response[:100]}..." if len(response) > 100 else f"[Response] {response}")
        
        # Store in conversation history
        conversation_history.append({
            'role': 'user',
            'content': user_query
        })
        conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        conversations[session_id] = conversation_history
        
        # Get unique sources for citation
        unique_sources = list(dict.fromkeys(sources)) if sources else []

        return jsonify({
            'response': response,
            'num_chunks_used': len(relevant_chunks),
            'max_similarity': float(scores[0]) if scores else 0.0,
            'sources': unique_sources
        })
        
    except Exception as e:
        print(f"[Error] {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        # Support both Flask session and request body (for CORS)
        data = request.json or {}
        session_id = data.get('session_id') or session.get('session_id')
        if session_id and session_id in conversations:
            conversations[session_id] = []
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    return jsonify({
        'status': 'healthy',
        'service': 'sustainability-chatbot-api'
    })


if __name__ == '__main__':
    # Initialize chatbot on startup
    initialize_chatbot()
    
    # Run Flask app
    print(f"Starting server on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG_MODE)
