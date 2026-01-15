"""
Main entry point for IIT Bombay Sustainability Cell Chatbot
"""
from flask import Flask, request, jsonify, render_template, session
import config
from document_loader import load_all_sources
from text_processor import preprocess_document
from embedder import create_embedder
from retriever import create_retriever
from llm_handler import create_llm_handler
import secrets

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# Global variables for caching
chunks = None
chunk_embeddings = None
embedder = None
retriever = None
llm_handler = None

# Store conversation histories (in production, use a database)
conversations = {}


def initialize_chatbot():
    """Initialize all chatbot components"""
    global chunks, chunk_embeddings, embedder, retriever, llm_handler
    
    print("=" * 60)
    print("Initializing IIT Bombay Sustainability Cell Chatbot")
    print("=" * 60)
    
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
    
    # Chunk text
    print(f"\n2. Chunking text (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
    try:
        chunks = preprocess_document(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        print(f"   [OK] Created {len(chunks)} chunks")
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
    
    # Create retriever
    print(f"\n5. Initializing retriever")
    try:
        retriever = create_retriever(chunks, chunk_embeddings)
        print(f"   [OK] Retriever initialized")
    except Exception as e:
        print(f"   [ERROR] Error initializing retriever: {e}")
        raise
    
    # Create LLM handler
    print(f"\n6. Initializing LLM: {config.GEMINI_MODEL}")
    try:
        llm_handler = create_llm_handler(config.GEMINI_API_KEY, config.GEMINI_MODEL)
        print(f"   [OK] LLM handler initialized")
    except Exception as e:
        print(f"   [ERROR] Error initializing LLM: {e}")
        raise
    
    print("\n" + "=" * 60)
    print("Chatbot initialized successfully!")
    print("=" * 60)
    print(f"Settings:")
    print(f"  - Top-k chunks: {config.TOP_K_CHUNKS}")
    print(f"  - Similarity threshold: {config.SIMILARITY_THRESHOLD}")
    print(f"  - Server: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
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
        # Get session ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['session_id'] = session_id
            conversations[session_id] = []

        # Get query from request
        data = request.json
        user_query = data.get('query', '').strip()

        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400

        print(f"\n[Query] {user_query}")

        # Get conversation history
        conversation_history = conversations.get(session_id, [])

        # Build contextual query for better retrieval on follow-up questions
        contextual_query = build_contextual_query(user_query, conversation_history)
        if contextual_query != user_query:
            print(f"[Context] Enhanced query: {contextual_query[:80]}...")

        # Embed the contextual query for better retrieval
        query_embedding = embedder.embed_text(contextual_query)

        # Retrieve relevant chunks
        relevant_chunks, scores = retriever.retrieve(
            query_embedding,
            top_k=config.TOP_K_CHUNKS,
            threshold=config.SIMILARITY_THRESHOLD
        )
        
        if relevant_chunks:
            print(f"[Retrieval] Found {len(relevant_chunks)} relevant chunks")
            for i, score in enumerate(scores, 1):
                print(f"  Chunk {i}: similarity = {score:.4f}")
        else:
            print(f"[Retrieval] No chunks above threshold ({config.SIMILARITY_THRESHOLD})")
        
        # Generate response using LLM with conversation history
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
        
        return jsonify({
            'response': response,
            'num_chunks_used': len(relevant_chunks),
            'max_similarity': float(scores[0]) if scores else 0.0
        })
        
    except Exception as e:
        print(f"[Error] {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in conversations:
            conversations[session_id] = []
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize chatbot on startup
    initialize_chatbot()
    
    # Run Flask app
    print(f"Starting server on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG_MODE)
