# backend/app/core/semantic_cache.py
"""
Semantic Cache for Quiz AI.

Caches MCQ generations based on semantic similarity of queries.
Uses SQLite for storage and FAISS for vector search.
Reduces LLM API calls by returning cached results for similar queries.

Improvements:
- Incremental FAISS index update (avoids full rebuild)
- Thread-safe SQLite operations
- Better connection management
"""

import logging
import json
import sqlite3
import numpy as np
import faiss
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from contextlib import contextmanager

from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL, DATABASE_PATH, EMBEDDING_DIM
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    total_entries: int
    total_hits: int
    total_misses: int
    hit_rate: float


class SemanticCache:
    """
    Semantic caching for MCQ generations.
    
    Stores query-MCQ pairs and uses cosine similarity to find similar queries.
    If a similar query (> threshold) is found, returns cached MCQ.
    
    Features:
    - Incremental index updates (no full rebuild on each store)
    - Thread-safe SQLite access
    - Connection pooling via context manager
    """
    
    # Thread lock for SQLite and FAISS operations
    _lock = threading.RLock()
    
    def __init__(
        self,
        db_path: str = None,
        similarity_threshold: float = 0.85,
        embedding_model: str = None
    ):
        """
        Initialize Semantic Cache.
        
        Args:
            db_path: Path to SQLite database
            similarity_threshold: Minimum similarity for cache hit (0-1)
            embedding_model: SentenceTransformer model name
        """
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.similarity_threshold = similarity_threshold
        self.model_name = embedding_model or EMBEDDING_MODEL
        self.embedding_dim = EMBEDDING_DIM
        
        # Track hits/misses
        self._hits = 0
        self._misses = 0
        
        # Use shared embedding service
        self._embedding_service = get_embedding_service()
        
        # Initialize database and cache index
        self._init_db()
        self._load_cache_index()
        
        logger.info(f"Cache initialized with {len(self.cache_ids)} entries")
    
    @contextmanager
    def _get_connection(self):
        """Thread-safe SQLite connection context manager."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize SQLite database."""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcq_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    query_embedding BLOB NOT NULL,
                    chunk_id TEXT,
                    mcq_json TEXT NOT NULL,
                    difficulty TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON mcq_cache(created_at)')
    
    def _load_cache_index(self):
        """Load FAISS index from cached embeddings."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT id, query_embedding FROM mcq_cache ORDER BY id")
                
                self.cache_ids = []
                embeddings = []
                
                for row in cursor:
                    self.cache_ids.append(row[0])
                    emb = np.frombuffer(row[1], dtype=np.float32)
                    embeddings.append(emb)
            
            # Create FAISS index
            if embeddings:
                embeddings = np.vstack(embeddings).astype('float32')
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
                faiss.normalize_L2(embeddings)
                self.index.add(embeddings)
            else:
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Empty but ready
    
    def _add_to_index(self, embedding: np.ndarray, cache_id: int):
        """Incrementally add a single embedding to the index."""
        with self._lock:
            # Normalize and add
            emb = embedding.reshape(1, -1).astype('float32')
            faiss.normalize_L2(emb)
            
            if self.index is None:
                self.index = faiss.IndexFlatIP(self.embedding_dim)
            
            self.index.add(emb)
            self.cache_ids.append(cache_id)
    
    def lookup(
        self,
        query: str,
        difficulty: str = None
    ) -> Optional[Dict]:
        """
        Look up cached MCQ for semantically similar query.
        
        Args:
            query: User's topic query
            difficulty: Optional difficulty filter
            
        Returns:
            Dict with cached MCQ if found, None otherwise
        """
        with self._lock:
            if self.index is None or self.index.ntotal == 0:
                self._misses += 1
                return None
            
            # Encode query using shared service
            q_emb = self._embedding_service.encode([query], normalize=True)
            
            # Search in cache
            scores, indices = self.index.search(q_emb, k=1)
            similarity = float(scores[0][0])
            
            if similarity >= self.similarity_threshold:
                idx = int(indices[0][0])
                if idx < 0 or idx >= len(self.cache_ids):
                    self._misses += 1
                    return None
                    
                cache_id = self.cache_ids[idx]
                
                # Fetch from database
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT query_text, mcq_json, difficulty FROM mcq_cache WHERE id = ?",
                        (cache_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        cached_query, mcq_json, cached_difficulty = row
                        
                        # Optional difficulty filter
                        if difficulty and cached_difficulty and cached_difficulty != difficulty:
                            self._misses += 1
                            return None
                        
                        # Update hit count
                        conn.execute(
                            "UPDATE mcq_cache SET hit_count = hit_count + 1, last_used = ? WHERE id = ?",
                            (datetime.now(), cache_id)
                        )
                        
                        self._hits += 1
                        
                        return {
                            "mcq": json.loads(mcq_json),
                            "cached": True,
                            "similarity": similarity,
                            "original_query": cached_query
                        }
            
            self._misses += 1
            return None
    
    def store(
        self,
        query: str,
        mcq: Dict,
        chunk_id: str = None,
        difficulty: str = None
    ):
        """
        Store MCQ in cache with incremental index update.
        
        Args:
            query: User's topic query
            mcq: Generated MCQ dictionary
            chunk_id: ID of source chunk
            difficulty: Difficulty level
        """
        # Encode query using shared service
        q_emb = self._embedding_service.encode_single(query, normalize=True)
        
        # Store in database and get the new ID
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO mcq_cache 
                   (query_text, query_embedding, chunk_id, mcq_json, difficulty, last_used)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    query,
                    q_emb.astype(np.float32).tobytes(),
                    chunk_id,
                    json.dumps(mcq, ensure_ascii=False),
                    difficulty,
                    datetime.now()
                )
            )
            new_id = cursor.lastrowid
        
        # Incremental index update (no full rebuild!)
        self._add_to_index(q_emb, new_id)
        
        logger.debug(f"Cache stored: '{query[:50]}...' (id={new_id}, total: {len(self.cache_ids)})")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(hit_count), 0) as total_hits
                FROM mcq_cache
            """)
            row = cursor.fetchone()
        
        total_entries = row[0] or 0
        db_hits = row[1] or 0
        
        total_lookups = self._hits + self._misses
        hit_rate = self._hits / total_lookups if total_lookups > 0 else 0.0
        
        return CacheStats(
            total_entries=total_entries,
            total_hits=db_hits + self._hits,
            total_misses=self._misses,
            hit_rate=hit_rate
        )
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM mcq_cache")
            
            self.cache_ids = []
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self._hits = 0
            self._misses = 0
        
        logger.info("Cache cleared")
    
    def cleanup_old(self, days: int = 30) -> int:
        """Remove cache entries older than specified days."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM mcq_cache WHERE created_at < datetime('now', ?)",
                    (f'-{days} days',)
                )
                deleted = cursor.rowcount
            
            if deleted > 0:
                # Need full rebuild after deletion
                self._load_cache_index()
                logger.info(f"Cache cleaned up {deleted} old entries")
            
            return deleted
