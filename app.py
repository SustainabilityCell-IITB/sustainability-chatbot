from flask import Flask, render_template, request, jsonify
import os
from utils import load_pdf_text, chunk_text, embed_chunks, find_most_relevant_chunks
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import numpy as np

app = Flask(__name__)

# configuration
# prefer a TXT file if present (faster), otherwise fall back to PDF
ROOT_TXT = os.path.join(os.path.dirname(__file__), "ilovepdf_merged.txt")
ROOT_PDF = os.path.join(os.path.dirname(__file__), "ilovepdf_merged.pdf")
FALLBACK_PDF = os.path.join(os.path.dirname(__file__), "data", "document.pdf")

# Check for text file first, then PDF
if os.path.exists(ROOT_TXT):
    DATA_FILE = ROOT_TXT
    IS_PDF = False
elif os.path.exists(ROOT_PDF):
    DATA_FILE = ROOT_PDF
    IS_PDF = True
else:
    DATA_FILE = FALLBACK_PDF
    IS_PDF = True

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_API_KEY = "AIzaSyBzP6iPnrlVisRlOSRhXUGJYuIFIlspiiM"
GEMINI_MODEL = "gemini-2.5-flash"  # most capable Gemini model
SIMILARITY_THRESHOLD = 0.45  # lowered for more permissive matching

# configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# load models once
print("[1/4] Loading sentence embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
print("[2/4] Gemini API configured.")

# load and prepare document
if os.path.exists(DATA_FILE):
    if IS_PDF:
        print(f"[3/4] Loading PDF: {DATA_FILE}")
        full_text = load_pdf_text(DATA_FILE)
    else:
        print(f"[3/4] Loading text file: {DATA_FILE}")
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            full_text = f.read()
    
    print(f"[4/4] Chunking text (extracted {len(full_text)} characters)...")
    chunks = chunk_text(full_text, chunk_size=400, overlap=50)
    print(f"[4/4] Embedding {len(chunks)} chunks (this may take a minute)...")
    chunk_embeddings = embed_chunks(chunks, embedder)
    print(f"✓ Ready! Serving {len(chunks)} chunks from document.")
else:
    print(f"[!] Document not found at {DATA_FILE}. Starting without document context.")
    full_text = ""
    chunks = []
    chunk_embeddings = np.array([])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    data = request.json or {}
    q = data.get('query', '').strip()
    if not q:
        return jsonify({'error': 'empty query'}), 400

    # find relevant chunks - using top 5 for more context
    top_chunks, top_scores = find_most_relevant_chunks(q, chunks, chunk_embeddings, embedder, top_k=5)
    # if top score below threshold -> out of context
    if len(top_scores) == 0 or top_scores[0] < SIMILARITY_THRESHOLD:
        return jsonify({'answer': 'Out of context question'})

    # craft prompt: provide context + user question
    context_text = "\n\n".join(top_chunks)
    prompt = f"""Context from PDF:
{context_text}

Question: {q}

Answer the question concisely based only on the context provided above. If the context doesn't contain relevant information, say "Out of context question"."""

    try:
        response = model.generate_content(prompt)
        answer = response.text if response and response.text else "Unable to generate answer."
    except Exception as e:
        answer = f"Error calling Gemini API: {str(e)}"

    return jsonify({'answer': answer, 'scores': [float(s) for s in top_scores]})


if __name__ == '__main__':
    app.run(debug=True)
