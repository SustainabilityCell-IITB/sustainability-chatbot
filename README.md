PDF/Text Chatbot with Gemini AI
=================================

A Flask web app that answers questions about documents using Google's Gemini AI. Supports both text files and PDFs.

Features
--------

- 📄 **Document support**: Text files (.txt) or PDF files
- 🤖 **Gemini 1.5 Pro**: Powered by Google's most advanced AI model
- 🔍 **Smart retrieval**: Uses semantic search to find relevant content
- 🎯 **Context awareness**: Returns "Out of context question" for unrelated queries
- ⚡ **Fast**: Prefers text files for instant loading

Setup
------

1. **Install dependencies** (use a virtual environment):

   ```bash
   pip install -r requirements.txt
   ```

2. **Add your document** (place in project root):
   - Text file (recommended): `ilovepdf_merged.txt`
   - OR PDF file: `ilovepdf_merged.pdf`
   - OR fallback: `data/document.pdf`

3. **Set your Gemini API key** in `app.py`:
   ```python
   GEMINI_API_KEY = "your-api-key-here"
   ```
   Get your key at: https://makersuite.google.com/app/apikey

Run
----

```bash
python app.py
```

Open http://127.0.0.1:5000/ and start asking questions!

How it Works
------------

1. **Document Loading**: Loads text file (instant) or extracts from PDF
2. **Chunking**: Splits text into overlapping 400-character chunks
3. **Embedding**: Converts chunks to vector embeddings using sentence-transformers
4. **Query Processing**: 
   - Finds top 3 most relevant chunks using cosine similarity
   - Checks if similarity score meets threshold (0.65)
   - Sends context + question to Gemini 1.5 Pro
   - Returns AI-generated answer or "Out of context question"

Configuration
-------------

Edit `app.py` to customize:

- `SIMILARITY_THRESHOLD`: Adjust how strict context matching is (default: 0.65)
- `GEMINI_MODEL`: Change AI model (default: "gemini-1.5-pro")
- Chunk size/overlap in `chunk_text()` call

Tech Stack
----------

- **Backend**: Flask
- **AI**: Google Gemini 1.5 Pro API
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF Parsing**: pypdf
- **Vector Search**: scikit-learn (cosine similarity)

Notes
-----

- First run downloads the embedding model (~80MB)
- Text files load instantly; PDFs take a few seconds
- Models require internet connection on first use
- Adjust `SIMILARITY_THRESHOLD` for more/less strict matching
