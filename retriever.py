"""
Retriever module for finding relevant text chunks using similarity search
"""
from typing import List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    """Handles similarity-based retrieval of relevant text chunks"""
    
    def __init__(self, chunks: List[str], chunk_embeddings: np.ndarray):
        """
        Initialize the retriever.
        
        Args:
            chunks: List of text chunks
            chunk_embeddings: Embeddings for each chunk, shape (n_chunks, embedding_dim)
        """
        if len(chunks) != len(chunk_embeddings):
            raise ValueError(f"Number of chunks ({len(chunks)}) must match number of embeddings ({len(chunk_embeddings)})")
        
        self.chunks = chunks
        self.chunk_embeddings = chunk_embeddings
    
    def retrieve(self, query_embedding: np.ndarray, top_k: int = 5, 
                 threshold: float = 0.45) -> Tuple[List[str], List[float]]:
        """
        Retrieve most relevant chunks for a query.
        
        Args:
            query_embedding: Embedding of the query, shape (embedding_dim,)
            top_k: Number of top chunks to retrieve
            threshold: Minimum similarity score threshold
            
        Returns:
            Tuple of (relevant_chunks, similarity_scores)
            Returns empty lists if no chunks meet the threshold
        """
        # Ensure query_embedding is 2D for cosine_similarity
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
        
        # Get indices sorted by similarity (highest first)
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Get top-k results above threshold
        relevant_chunks = []
        scores = []
        
        for idx in sorted_indices[:top_k]:
            score = float(similarities[idx])
            if score >= threshold:
                relevant_chunks.append(self.chunks[idx])
                scores.append(score)
        
        return relevant_chunks, scores
    
    def retrieve_with_details(self, query_embedding: np.ndarray, top_k: int = 5,
                             threshold: float = 0.45) -> List[dict]:
        """
        Retrieve most relevant chunks with detailed information.
        
        Args:
            query_embedding: Embedding of the query
            top_k: Number of top chunks to retrieve
            threshold: Minimum similarity score threshold
            
        Returns:
            List of dicts with keys: 'text', 'score', 'index'
        """
        chunks, scores = self.retrieve(query_embedding, top_k, threshold)
        
        results = []
        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            results.append({
                'text': chunk,
                'score': score,
                'rank': i + 1
            })
        
        return results


def create_retriever(chunks: List[str], chunk_embeddings: np.ndarray) -> Retriever:
    """
    Factory function to create a Retriever.
    
    Args:
        chunks: List of text chunks
        chunk_embeddings: Embeddings for the chunks
        
    Returns:
        Initialized Retriever instance
    """
    return Retriever(chunks, chunk_embeddings)
