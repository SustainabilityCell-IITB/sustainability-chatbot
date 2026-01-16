"""
Text processing module for chunking documents with source tracking
"""
from typing import List, Tuple
import re


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


def extract_source_from_text(text: str) -> str:
    """
    Extract the source name from text content markers.
    Looks for patterns like '--- Content from: filename ---'

    Args:
        text: Text that may contain source markers

    Returns:
        Source name or 'Unknown' if not found
    """
    # Look for the source marker pattern
    pattern = r'---\s*Content from:\s*([^-]+)\s*---'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return "Unknown"


def chunk_text_with_sources(text: str, chunk_size: int = 400, overlap: int = 50) -> Tuple[List[str], List[str]]:
    """
    Split text into overlapping chunks while tracking source files.

    Args:
        text: Input text to chunk (with source markers)
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        Tuple of (list of chunks, list of source names for each chunk)
    """
    # First, split by source markers to track which source each section belongs to
    source_pattern = r'---\s*Content from:\s*([^-]+)\s*---'

    # Find all source markers and their positions
    markers = list(re.finditer(source_pattern, text))

    if not markers:
        # No source markers, return regular chunks with 'Unknown' source
        chunks = chunk_text(text, chunk_size, overlap)
        sources = ['Unknown'] * len(chunks)
        return chunks, sources

    # Build a list of (start_pos, end_pos, source_name) for each section
    sections = []
    for i, match in enumerate(markers):
        source_name = match.group(1).strip()
        start_pos = match.end()

        # End position is the start of the next marker, or end of text
        if i + 1 < len(markers):
            end_pos = markers[i + 1].start()
        else:
            end_pos = len(text)

        sections.append((start_pos, end_pos, source_name))

    # Now chunk the entire text and assign sources based on position
    chunks = []
    sources = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        # Clean out source markers from the chunk
        chunk = re.sub(source_pattern, '', chunk).strip()

        if chunk:
            # Determine which source this chunk belongs to
            chunk_mid = (start + end) // 2
            source = 'Unknown'
            for sec_start, sec_end, sec_source in sections:
                if sec_start <= chunk_mid < sec_end:
                    source = sec_source
                    break

            chunks.append(chunk)
            sources.append(source)

        step = chunk_size - overlap
        if step <= 0:
            step = 1
        start += step

    return chunks, sources


def preprocess_document_with_sources(text: str, chunk_size: int = 400, overlap: int = 50) -> Tuple[List[str], List[str]]:
    """
    Preprocess document: clean and chunk while tracking sources.

    Args:
        text: Input document text with source markers
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks

    Returns:
        Tuple of (list of chunks, list of source names)
    """
    # Don't clean text first as it removes source markers
    chunks, sources = chunk_text_with_sources(text, chunk_size, overlap)

    # Clean each chunk individually
    cleaned_chunks = [clean_text(chunk) for chunk in chunks]

    # Filter out empty chunks
    result_chunks = []
    result_sources = []
    for chunk, source in zip(cleaned_chunks, sources):
        if chunk:
            result_chunks.append(chunk)
            result_sources.append(source)

    return result_chunks, result_sources
