"""
Embedder module for generating text embeddings
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Handles text embedding generation using SentenceTransformer"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
        """
        self.model_name = model_name
        self.model = None
        
    def load_model(self):
        """Load the embedding model"""
        if self.model is None:
            print(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print("Embedding model loaded successfully!")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings, shape (n_texts, embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
        """
        if not texts:
            raise ValueError("Cannot embed empty list of texts")
        
        # Ensure model is loaded
        if self.model is None:
            self.load_model()
        
        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=4,
            convert_to_numpy=True,
            show_progress_bar=True
        )    
        return embeddings
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array embedding, shape (embedding_dim,)
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        embeddings = self.embed_texts([text])
        return embeddings[0]


def create_embedder(model_name: str) -> Embedder:
    """
    Factory function to create and initialize an Embedder.
    
    Args:
        model_name: Name of the embedding model
        
    Returns:
        Initialized Embedder instance
    """
    embedder = Embedder(model_name)
    embedder.load_model()
    return embedder
