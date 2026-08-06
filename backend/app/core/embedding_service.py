# backend/app/core/embedding_service.py
"""
Shared Embedding Service for Quiz AI.

Provides a singleton embedding model instance to avoid loading the model
multiple times across different modules (RAGRetriever, SemanticCache).

Memory-efficient: Uses a single SentenceTransformer instance.
Thread-safe: Lock-protected model access.
"""

import logging
import threading
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Singleton Embedding Service.
    
    Provides shared access to the SentenceTransformer model across the application.
    Avoids loading multiple model instances (saves ~500MB+ memory).
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingService._initialized:
            return
            
        with EmbeddingService._lock:
            if EmbeddingService._initialized:
                return
                
            self.model_name = EMBEDDING_MODEL
            self.embedding_dim = EMBEDDING_DIM
            self._model = None
            EmbeddingService._initialized = True
            logger.info(f"EmbeddingService initialized (model: {self.model_name})")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            with EmbeddingService._lock:
                if self._model is None:
                    logger.info(f"Loading embedding model: {self.model_name}")
                    self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        convert_to_numpy: bool = True
    ) -> np.ndarray:
        """
        Encode text(s) to embeddings.
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to L2-normalize embeddings (for cosine similarity)
            convert_to_numpy: Whether to return numpy array
            
        Returns:
            Embeddings as numpy array of shape (n, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=convert_to_numpy
        )
        
        return embeddings.astype('float32')
    
    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """Encode a single text and return 1D vector."""
        return self.encode([text], normalize=normalize)[0]


# Global singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
