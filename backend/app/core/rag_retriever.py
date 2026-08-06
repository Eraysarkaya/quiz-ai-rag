# backend/app/core/rag_retriever.py
"""
FAISS + SentenceTransformer RAG Retriever.
Production-ready retrieval using Cosine Similarity.

Uses shared EmbeddingService for memory efficiency.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np

from .config import (
    VECTORSTORE_DIR,
    INDEX_PATH,
    META_PATH,
    DEFAULT_TOP_K,
    SIMILARITY_THRESHOLD
)
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


def _compute_cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Compute Cosine Similarity: (A · B) / (||A|| * ||B||)"""
    norm_q = np.linalg.norm(query_vec)
    if norm_q > 0:
        query_vec = query_vec / norm_q
    
    norm_docs = np.linalg.norm(doc_vecs, axis=1, keepdims=True)
    norm_docs = np.where(norm_docs == 0, 1e-10, norm_docs)
    doc_vecs_norm = doc_vecs / norm_docs
    
    return np.dot(doc_vecs_norm, query_vec.T).flatten()


class RAGRetriever:
    """FAISS + SentenceTransformer based RAG Retriever."""
    
    # Singleton for index caching
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, top_k: int = None):
        if RAGRetriever._initialized:
            return
            
        self.top_k = top_k or DEFAULT_TOP_K
        # Use shared embedding service instead of loading our own model
        self._embedding_service = get_embedding_service()
        self._load_index_and_meta()
        RAGRetriever._initialized = True
        logger.info("RAGRetriever initialized (using shared EmbeddingService)")

    def _load_index_and_meta(self):
        """Load FAISS index and metadata."""
        logger.info(f"Loading FAISS index from: {INDEX_PATH}")
        
        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {INDEX_PATH}. Run build_index.py first."
            )

        # FAISS' Windows file reader cannot reliably open paths containing
        # non-ASCII characters (for example the "Ş" in this workspace path).
        # Reading the bytes in Python first keeps the project portable.
        serialized_index = np.frombuffer(INDEX_PATH.read_bytes(), dtype=np.uint8)
        self.index = faiss.deserialize_index(serialized_index)
        
        n_total = self.index.ntotal
        logger.debug(f"Reconstructing {n_total} vectors from FAISS index")
        
        try:
            self.doc_vectors = self.index.reconstruct_n(0, n_total)
        except RuntimeError:
            logger.warning("Could not reconstruct vectors")
            self.doc_vectors = None
            
        logger.info(f"Loading metadata from: {META_PATH}")
        if not META_PATH.exists():
            raise FileNotFoundError(f"Metadata file not found at {META_PATH}")

        self.meta = []
        with open(META_PATH, "r", encoding="utf-8") as f:
            for line in f:
                self.meta.append(json.loads(line))

        if self.index.ntotal != len(self.meta):
            logger.warning(f"Index size ({self.index.ntotal}) != Metadata count ({len(self.meta)})")
        else:
            logger.info(f"Loaded {self.index.ntotal} vectors and metadata entries")

    def _encode_query(self, query: str) -> np.ndarray:
        """Encode query string to embedding vector using shared service."""
        return self._embedding_service.encode([query], normalize=True)

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        min_score: float = None
    ) -> List[Dict]:
        """Retrieve the most relevant chunks using Cosine Similarity."""
        if top_k is None:
            top_k = self.top_k
        if min_score is None:
            min_score = SIMILARITY_THRESHOLD

        query_vec = self._encode_query(query)[0]

        if self.doc_vectors is None:
            raise RuntimeError("Document vectors not available")
        
        scores = _compute_cosine_similarity(query_vec, self.doc_vectors)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for rank, idx in enumerate(top_indices):
            if idx < 0 or idx >= len(self.meta):
                continue
                
            score = float(scores[idx])
            if score < min_score:
                continue
            
            meta = self.meta[idx]
            results.append({
                "chunk_id": meta["chunk_id"],
                "text": meta["text"],
                "score": score,
                "rank": rank + 1,
                "source_id": meta.get("source_id"),
                "chunk_index": meta.get("chunk_index"),
                "total_chunks": meta.get("total_chunks")
            })

        return results

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = None,
        min_score: float = None
    ) -> Dict:
        """Retrieve relevant chunks and return with combined context."""
        chunks = self.retrieve(query, top_k, min_score)
        context = "\n\n".join([c["text"] for c in chunks])
        
        return {
            "context": context,
            "chunks": chunks,
            "query": query,
            "num_chunks": len(chunks)
        }
