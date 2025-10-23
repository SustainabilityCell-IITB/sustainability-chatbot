import pypdf
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def load_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file using pypdf (faster than PyPDF2)."""
    text_parts = []
    print(f"   Opening PDF with {pypdf.PdfReader.__name__}...")
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            num_pages = len(reader.pages)
            print(f"   Found {num_pages} pages. Extracting text...")
            for i, page in enumerate(reader.pages):
                if i % 10 == 0:
                    print(f"   Processing page {i+1}/{num_pages}...")
                try:
                    text = page.extract_text() or ""
                    text_parts.append(text)
                except Exception as e:
                    print(f"   Warning: Could not extract text from page {i+1}: {e}")
                    continue
        print(f"   Extraction complete!")
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"   Error loading PDF: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks (approx by characters)."""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    # ensure overlap is smaller than chunk_size to avoid infinite loops
    overlap = min(overlap, chunk_size - 1)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # always advance by at least 1 character to prevent infinite loop
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks


def embed_chunks(chunks: List[str], embedder: SentenceTransformer) -> np.ndarray:
    if not chunks:
        return np.array([])
    embs = embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    return embs


def find_most_relevant_chunks(query: str, chunks: List[str], chunk_embeddings: np.ndarray, embedder: SentenceTransformer, top_k: int = 3) -> Tuple[List[str], List[float]]:
    """Return top_k chunks and their similarity scores for a query."""
    if not chunks or chunk_embeddings.size == 0:
        return [], []
    q_emb = embedder.encode([query], convert_to_numpy=True)[0]
    sims = cosine_similarity([q_emb], chunk_embeddings)[0]
    idx = np.argsort(-sims)[:top_k]
    top_chunks = [chunks[i] for i in idx]
    top_scores = [float(sims[i]) for i in idx]
    return top_chunks, top_scores
