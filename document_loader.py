"""
Document loader module for loading text and PDF files
"""
import os
from typing import Optional


def load_text_file(file_path: str) -> str:
    """
    Load text content from a text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Text content as a string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            raise ValueError(f"File is empty: {file_path}")
        
        return text
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {str(e)}")


def load_pdf_file(file_path: str) -> str:
    """
    Load text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content as a string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required to load PDF files. Install with: pip install pypdf")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        if not text.strip():
            raise ValueError(f"No text extracted from PDF: {file_path}")
        
        return text
    except Exception as e:
        raise IOError(f"Error reading PDF {file_path}: {str(e)}")


def load_document(file_path: str) -> str:
    """
    Load document content. Auto-detects file type (txt or pdf).
    
    Args:
        file_path: Path to the document
        
    Returns:
        Document text content
        
    Raises:
        ValueError: If file type is not supported
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.txt':
        return load_text_file(file_path)
    elif ext == '.pdf':
        return load_pdf_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .txt, .pdf")
