"""
Cache manager for storing and loading embeddings to/from disk.
Dramatically speeds up startup time by avoiding re-computation.
"""
import os
import hashlib
import numpy as np
from typing import Tuple, List, Optional
import json


class CacheManager:
    """Manages caching of embeddings and chunks to disk"""

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.embeddings_file = os.path.join(cache_dir, "embeddings.npy")
        self.chunks_file = os.path.join(cache_dir, "chunks.json")
        self.metadata_file = os.path.join(cache_dir, "metadata.json")

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of content to detect changes"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _compute_config_hash(self, chunk_size: int, overlap: int, model_name: str) -> str:
        """Compute hash of configuration to detect config changes"""
        config_str = f"{chunk_size}_{overlap}_{model_name}"
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()

    def is_cache_valid(self, content: str, chunk_size: int, overlap: int, model_name: str) -> bool:
        """
        Check if cached embeddings are valid for the current content and config.

        Args:
            content: Current document content
            chunk_size: Chunk size setting
            overlap: Overlap setting
            model_name: Embedding model name

        Returns:
            True if cache is valid and can be used
        """
        if not os.path.exists(self.metadata_file):
            return False

        if not os.path.exists(self.embeddings_file):
            return False

        if not os.path.exists(self.chunks_file):
            return False

        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)

            content_hash = self._compute_content_hash(content)
            config_hash = self._compute_config_hash(chunk_size, overlap, model_name)

            return (metadata.get('content_hash') == content_hash and
                    metadata.get('config_hash') == config_hash)
        except Exception:
            return False

    def save_cache(self, chunks: List[str], chunk_sources: List[str],
                   embeddings: np.ndarray, content: str,
                   chunk_size: int, overlap: int, model_name: str) -> None:
        """
        Save chunks and embeddings to cache.

        Args:
            chunks: List of text chunks
            chunk_sources: List of source names for each chunk
            embeddings: Numpy array of embeddings
            content: Original document content (for hash)
            chunk_size: Chunk size setting
            overlap: Overlap setting
            model_name: Embedding model name
        """
        try:
            # Save embeddings as numpy file
            np.save(self.embeddings_file, embeddings)

            # Save chunks and sources as JSON
            with open(self.chunks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'chunks': chunks,
                    'sources': chunk_sources
                }, f, ensure_ascii=False)

            # Save metadata
            metadata = {
                'content_hash': self._compute_content_hash(content),
                'config_hash': self._compute_config_hash(chunk_size, overlap, model_name),
                'num_chunks': len(chunks),
                'embedding_shape': list(embeddings.shape),
                'model_name': model_name
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"   [OK] Cache saved ({len(chunks)} chunks, {embeddings.shape})")

        except Exception as e:
            print(f"   [WARN] Failed to save cache: {e}")

    def load_cache(self) -> Optional[Tuple[List[str], List[str], np.ndarray]]:
        """
        Load chunks and embeddings from cache.

        Returns:
            Tuple of (chunks, chunk_sources, embeddings) or None if load fails
        """
        try:
            # Load embeddings
            embeddings = np.load(self.embeddings_file)

            # Load chunks and sources
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chunks = data['chunks']
                chunk_sources = data.get('sources', ['Unknown'] * len(chunks))

            return chunks, chunk_sources, embeddings

        except Exception as e:
            print(f"   [WARN] Failed to load cache: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached files"""
        for filepath in [self.embeddings_file, self.chunks_file, self.metadata_file]:
            if os.path.exists(filepath):
                os.remove(filepath)
        print("   [OK] Cache cleared")


def create_cache_manager(cache_dir: str = "cache") -> CacheManager:
    """Factory function to create a CacheManager"""
    return CacheManager(cache_dir)
