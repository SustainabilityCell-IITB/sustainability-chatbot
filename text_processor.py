"""
Text processing module for chunking documents
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
        
    Raises:
        ValueError: If chunk_size <= overlap or if parameters are invalid
    """
    if chunk_size <= overlap:
        raise ValueError(f"chunk_size ({chunk_size}) must be greater than overlap ({overlap})")
    
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Get chunk from start to start + chunk_size
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move start forward, accounting for overlap
        # Ensure we always move forward to prevent infinite loops
        step = chunk_size - overlap
        if step <= 0:
            step = 1  # Safety fallback
        
        start += step
    
    return chunks


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    return text.strip()


def preprocess_document(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Preprocess document: clean and chunk.
    
    Args:
        text: Input document text
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of processed text chunks
    """
    cleaned_text = clean_text(text)
    chunks = chunk_text(cleaned_text, chunk_size, overlap)
    return chunks
