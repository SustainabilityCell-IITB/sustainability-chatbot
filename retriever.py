"""
Retriever module for finding relevant text chunks using hybrid search and reranking
"""
from typing import List, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re


class Retriever:
    """Handles hybrid retrieval (semantic + BM25) with optional cross-encoder reranking"""

    def __init__(self, chunks: List[str], chunk_embeddings: np.ndarray,
                 use_hybrid: bool = True, use_reranker: bool = True,
                 chunk_sources: Optional[List[str]] = None):
        """
        Initialize the retriever.

        Args:
            chunks: List of text chunks
            chunk_embeddings: Embeddings for each chunk, shape (n_chunks, embedding_dim)
            use_hybrid: Whether to use hybrid search (semantic + BM25)
            use_reranker: Whether to use cross-encoder reranking
            chunk_sources: Optional list of source names for each chunk
        """
        if len(chunks) != len(chunk_embeddings):
            raise ValueError(f"Number of chunks ({len(chunks)}) must match number of embeddings ({len(chunk_embeddings)})")

        self.chunks = chunks
        self.chunk_embeddings = chunk_embeddings
        self.use_hybrid = use_hybrid
        self.use_reranker = use_reranker
        self.chunk_sources = chunk_sources if chunk_sources else ['Unknown'] * len(chunks)

        # Initialize BM25 for keyword search
        if use_hybrid:
            tokenized_chunks = [self._tokenize(chunk) for chunk in chunks]
            self.bm25 = BM25Okapi(tokenized_chunks)
            print("   [OK] BM25 index initialized for hybrid search")

        # Initialize cross-encoder for reranking
        self.cross_encoder = None
        if use_reranker:
            try:
                from sentence_transformers import CrossEncoder
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                print("   [OK] Cross-encoder reranker initialized")
            except Exception as e:
                print(f"   [WARN] Could not load cross-encoder: {e}")
                self.use_reranker = False

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Lowercase and split on non-alphanumeric characters
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def _get_semantic_scores(self, query_embedding: np.ndarray) -> np.ndarray:
        """Get semantic similarity scores for all chunks"""
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
        return similarities

    def _get_bm25_scores(self, query: str) -> np.ndarray:
        """Get BM25 scores for all chunks"""
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        # Normalize BM25 scores to 0-1 range
        if scores.max() > 0:
            scores = scores / scores.max()
        return scores

    def _rerank_with_cross_encoder(self, query: str, chunks: List[str],
                                    initial_scores: List[float]) -> Tuple[List[str], List[float]]:
        """Rerank chunks using cross-encoder"""
        if not self.cross_encoder or len(chunks) == 0:
            return chunks, initial_scores

        # Create query-chunk pairs
        pairs = [[query, chunk] for chunk in chunks]

        # Get cross-encoder scores
        ce_scores = self.cross_encoder.predict(pairs)

        # Combine indices with scores and sort
        indexed_scores = list(enumerate(ce_scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # Reorder chunks and scores
        reranked_chunks = [chunks[idx] for idx, _ in indexed_scores]
        reranked_scores = [float(score) for _, score in indexed_scores]

        return reranked_chunks, reranked_scores

    def _rerank_with_cross_encoder_and_sources(self, query: str, chunks: List[str],
                                                initial_scores: List[float],
                                                sources: List[str]) -> Tuple[List[str], List[float], List[str]]:
        """Rerank chunks using cross-encoder while preserving source information"""
        if not self.cross_encoder or len(chunks) == 0:
            return chunks, initial_scores, sources

        # Create query-chunk pairs
        pairs = [[query, chunk] for chunk in chunks]

        # Get cross-encoder scores
        ce_scores = self.cross_encoder.predict(pairs)

        # Combine indices with scores and sort
        indexed_scores = list(enumerate(ce_scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # Reorder chunks, scores, and sources
        reranked_chunks = [chunks[idx] for idx, _ in indexed_scores]
        reranked_scores = [float(score) for _, score in indexed_scores]
        reranked_sources = [sources[idx] for idx, _ in indexed_scores]

        return reranked_chunks, reranked_scores, reranked_sources

    def retrieve(self, query_embedding: np.ndarray, top_k: int = 5,
                 threshold: float = 0.45, query_text: Optional[str] = None,
                 semantic_weight: float = 0.7) -> Tuple[List[str], List[float], List[str]]:
        """
        Retrieve most relevant chunks for a query using hybrid search.

        Args:
            query_embedding: Embedding of the query, shape (embedding_dim,)
            top_k: Number of top chunks to retrieve
            threshold: Minimum similarity score threshold
            query_text: Original query text (needed for BM25 and reranking)
            semantic_weight: Weight for semantic scores (1-weight for BM25)

        Returns:
            Tuple of (relevant_chunks, similarity_scores, source_names)
        """
        # Get semantic similarity scores
        semantic_scores = self._get_semantic_scores(query_embedding)

        # Combine with BM25 if hybrid search is enabled
        if self.use_hybrid and query_text:
            bm25_scores = self._get_bm25_scores(query_text)
            # Weighted combination of semantic and BM25 scores
            combined_scores = (semantic_weight * semantic_scores +
                             (1 - semantic_weight) * bm25_scores)
        else:
            combined_scores = semantic_scores

        # Get indices sorted by combined score (highest first)
        sorted_indices = np.argsort(combined_scores)[::-1]

        # Get more candidates for reranking (2x top_k)
        candidate_k = top_k * 2 if self.use_reranker else top_k

        # Get candidates above threshold
        candidate_chunks = []
        candidate_scores = []
        candidate_sources = []
        candidate_indices = []

        for idx in sorted_indices[:candidate_k]:
            score = float(combined_scores[idx])
            if score >= threshold or len(candidate_chunks) < top_k:
                candidate_chunks.append(self.chunks[idx])
                candidate_scores.append(score)
                candidate_sources.append(self.chunk_sources[idx])
                candidate_indices.append(idx)

        # Rerank with cross-encoder if enabled
        if self.use_reranker and query_text and len(candidate_chunks) > 0:
            reranked_chunks, reranked_scores, reranked_sources = self._rerank_with_cross_encoder_and_sources(
                query_text, candidate_chunks, candidate_scores, candidate_sources
            )
            # Return top_k after reranking
            return reranked_chunks[:top_k], reranked_scores[:top_k], reranked_sources[:top_k]

        return candidate_chunks[:top_k], candidate_scores[:top_k], candidate_sources[:top_k]

    def retrieve_with_details(self, query_embedding: np.ndarray, top_k: int = 5,
                             threshold: float = 0.45, query_text: Optional[str] = None) -> List[dict]:
        """
        Retrieve most relevant chunks with detailed information.

        Args:
            query_embedding: Embedding of the query
            top_k: Number of top chunks to retrieve
            threshold: Minimum similarity score threshold
            query_text: Original query text for hybrid search

        Returns:
            List of dicts with keys: 'text', 'score', 'rank'
        """
        chunks, scores = self.retrieve(query_embedding, top_k, threshold, query_text)

        results = []
        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            results.append({
                'text': chunk,
                'score': score,
                'rank': i + 1
            })

        return results


def create_retriever(chunks: List[str], chunk_embeddings: np.ndarray,
                    use_hybrid: bool = True, use_reranker: bool = True,
                    chunk_sources: Optional[List[str]] = None) -> Retriever:
    """
    Factory function to create a Retriever.

    Args:
        chunks: List of text chunks
        chunk_embeddings: Embeddings for the chunks
        use_hybrid: Whether to use hybrid search (semantic + BM25)
        use_reranker: Whether to use cross-encoder reranking
        chunk_sources: Optional list of source names for each chunk

    Returns:
        Initialized Retriever instance
    """
    return Retriever(chunks, chunk_embeddings, use_hybrid, use_reranker, chunk_sources)
