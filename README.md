# IIT Bombay Sustainability Cell Chatbot

A modular RAG (Retrieval-Augmented Generation) chatbot powered by Google Gemini API for answering questions about IIT Bombay's sustainability initiatives.

## Architecture

The chatbot is built with a modular architecture where each processing step is handled by a separate module:

### Core Modules

1. **config.py** - Configuration management
   - API keys and model settings
   - File paths and data locations
   - Processing parameters (chunk size, similarity threshold, etc.)

2. **document_loader.py** - Document loading
   - Load text files (.txt)
   - Load PDF files (.pdf)
   - Auto-detect file types

3. **text_processor.py** - Text processing
   - Chunk documents with configurable size and overlap
   - Clean and normalize text
   - Prevent infinite loops in chunking

4. **embedder.py** - Embedding generation
   - Generate embeddings using SentenceTransformer
   - Cache model for efficiency
   - Support batch and single text embedding

5. **retriever.py** - Similarity search
   - Find relevant chunks using cosine similarity
   - Top-k retrieval with threshold filtering
   - Return chunks with similarity scores

6. **llm_handler.py** - LLM interaction
   - Generate responses using Google Gemini API
   - Build context-aware prompts
   - Handle both contextual and conversational queries

7. **main.py** - Application entry point
   - Initialize all modules
   - Flask web server
   - API endpoints for querying

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Your Document

Place your document (text or PDF) in the `data/` folder. Update `config.py` if needed:

```python
DOCUMENT_FILE = "your_document.txt"  # or .pdf
```

### 3. Configure API Key

Update your Gemini API key in `config.py`:

```python
GEMINI_API_KEY = "your-api-key-here"
```

## Usage

### Run the Chatbot

Simply run the main script:

```bash
python main.py
```

This will:
1. Load the document from `data/` folder
2. Process and chunk the text
3. Generate embeddings
4. Initialize the retriever and LLM
5. Start the Flask server at http://127.0.0.1:5000

### Access the Web Interface

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### API Usage

You can also query the chatbot via API:

```bash
curl -X POST http://127.0.0.1:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the sustainability initiatives?"}'
```

## Configuration

Edit `config.py` to customize:

- **CHUNK_SIZE**: Size of text chunks (default: 400)
- **CHUNK_OVERLAP**: Overlap between chunks (default: 50)
- **TOP_K_CHUNKS**: Number of chunks to retrieve (default: 5)
- **SIMILARITY_THRESHOLD**: Minimum similarity score (default: 0.45)
- **EMBEDDING_MODEL**: SentenceTransformer model name
- **GEMINI_MODEL**: Gemini model version

## Project Structure

```
Kg_chatbot/
├── main.py                 # Entry point - run this!
├── config.py              # Configuration settings
├── document_loader.py     # Load documents
├── text_processor.py      # Chunk and process text
├── embedder.py           # Generate embeddings
├── retriever.py          # Similarity search
├── llm_handler.py        # Gemini API interaction
├── requirements.txt      # Python dependencies
├── data/                 # Document storage
│   └── ilovepdf_merged.txt
└── templates/
    └── index.html        # Web UI

# Legacy files (deprecated):
# - app.py (replaced by main.py)
# - utils.py (split into modular files)
```

## How It Works

1. **Document Loading**: Loads text from `data/` folder
2. **Text Processing**: Splits document into overlapping chunks
3. **Embedding**: Converts chunks to vector embeddings
4. **Query Processing**: User query is also embedded
5. **Retrieval**: Finds top-k most similar chunks via cosine similarity
6. **Generation**: Gemini LLM generates natural response using retrieved context

## Features

- ✅ Modular architecture - easy to maintain and extend
- ✅ Supports both text and PDF documents
- ✅ Smart chunking with overlap to preserve context
- ✅ Semantic similarity search using embeddings
- ✅ Context-aware responses from Gemini LLM
- ✅ Handles both factual and conversational queries
- ✅ Web interface for easy interaction
- ✅ RESTful API for integration

## Customization for IIT Bombay

The chatbot is specifically tuned for IIT Bombay's Sustainability Cell:
- Uses official sustainability documents as knowledge base
- Professional and friendly tone
- Contextual awareness of IIT Bombay initiatives

## Troubleshooting

**No relevant chunks found**: Lower `SIMILARITY_THRESHOLD` in `config.py`

**Out of memory**: Reduce `CHUNK_SIZE` or document size

**Slow loading**: Text files load faster than PDFs - prefer .txt format

**API errors**: Check your `GEMINI_API_KEY` in `config.py`

## License

This project is for IIT Bombay Sustainability Cell.

