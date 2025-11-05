"""
Main entry point for IIT Bombay Sustainability Cell Chatbot
"""
from flask import Flask, request, jsonify, render_template
import config
from document_loader import load_document
from text_processor import preprocess_document
from embedder import create_embedder
from retriever import create_retriever
from llm_handler import create_llm_handler

# Initialize Flask app
app = Flask(__name__)

# Global variables for caching
chunks = None
chunk_embeddings = None
embedder = None
retriever = None
llm_handler = None


def initialize_chatbot():
    """Initialize all chatbot components"""
    global chunks, chunk_embeddings, embedder, retriever, llm_handler
    
    print("=" * 60)
    print("Initializing IIT Bombay Sustainability Cell Chatbot")
    print("=" * 60)
    
    # Load document
    print(f"\n1. Loading document from: {config.DOCUMENT_PATH}")
    try:
        text = load_document(config.DOCUMENT_PATH)
        print(f"   ✓ Document loaded successfully ({len(text)} characters)")
    except Exception as e:
        print(f"   ✗ Error loading document: {e}")
        raise
    
    # Chunk text
    print(f"\n2. Chunking text (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
    try:
        chunks = preprocess_document(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        print(f"   ✓ Created {len(chunks)} chunks")
    except Exception as e:
        print(f"   ✗ Error chunking text: {e}")
        raise
    
    # Create embedder
    print(f"\n3. Initializing embedding model: {config.EMBEDDING_MODEL}")
    try:
        embedder = create_embedder(config.EMBEDDING_MODEL)
        print(f"   ✓ Embedder initialized")
    except Exception as e:
        print(f"   ✗ Error initializing embedder: {e}")
        raise
    
    # Generate embeddings
    print(f"\n4. Generating embeddings for {len(chunks)} chunks")
    try:
        chunk_embeddings = embedder.embed_texts(chunks)
        print(f"   ✓ Embeddings generated (shape: {chunk_embeddings.shape})")
    except Exception as e:
        print(f"   ✗ Error generating embeddings: {e}")
        raise
    
    # Create retriever
    print(f"\n5. Initializing retriever")
    try:
        retriever = create_retriever(chunks, chunk_embeddings)
        print(f"   ✓ Retriever initialized")
    except Exception as e:
        print(f"   ✗ Error initializing retriever: {e}")
        raise
    
    # Create LLM handler
    print(f"\n6. Initializing LLM: {config.GEMINI_MODEL}")
    try:
        llm_handler = create_llm_handler(config.GEMINI_API_KEY, config.GEMINI_MODEL)
        print(f"   ✓ LLM handler initialized")
    except Exception as e:
        print(f"   ✗ Error initializing LLM: {e}")
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
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """Handle chatbot queries"""
    try:
        # Get query from request
        data = request.json
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        print(f"\n[Query] {user_query}")
        
        # Embed the query
        query_embedding = embedder.embed_text(user_query)
        
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
        
        # Generate response using LLM
        response = llm_handler.generate_response(user_query, relevant_chunks)
        
        print(f"[Response] {response[:100]}..." if len(response) > 100 else f"[Response] {response}")
        
        return jsonify({
            'response': response,
            'num_chunks_used': len(relevant_chunks),
            'max_similarity': float(scores[0]) if scores else 0.0
        })
        
    except Exception as e:
        print(f"[Error] {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize chatbot on startup
    initialize_chatbot()
    
    # Run Flask app
    print(f"Starting server on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG_MODE)
