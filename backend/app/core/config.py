# backend/app/core/config.py
"""
Centralized configuration for Quiz AI backend.
All tunable parameters are defined here for easy experimentation.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Get the backend root directory
BACKEND_ROOT = Path(__file__).parent.parent.parent

# Load environment variables from project root
load_dotenv(BACKEND_ROOT.parent / ".env")

# ============================================================
# API KEYS
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY is None:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")

# ============================================================
# LLM MODEL SETTINGS
# ============================================================
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq's best free model

# ============================================================
# EMBEDDING SETTINGS
# ============================================================
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 768  # Dimension of mpnet-base-v2 embeddings

# ============================================================
# CHUNKING SETTINGS (Semantic-aware)
# ============================================================
CHUNK_SIZE = 512          # Approximate tokens per chunk
CHUNK_OVERLAP = 64        # Token overlap between chunks
MIN_CHUNK_CHARS = 100     # Minimum characters to keep a chunk

# ============================================================
# RETRIEVAL SETTINGS
# ============================================================
DEFAULT_TOP_K = 5                          # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.40                # Minimum score to include result (raised from 0.25 for better quality)

# ============================================================
# MCQ GENERATION SETTINGS
# ============================================================
MCQ_TEMPERATURE = 0.3          # Slightly higher for distractor diversity
MCQ_MAX_TOKENS = 1500          # Allow longer responses for explanations
MCQ_MAX_RETRIES = 3            # Retry attempts on failure

# ============================================================
# EVALUATION SETTINGS
# ============================================================
EVAL_TEMPERATURE = 0.0         # Deterministic for evaluation consistency
EVAL_MAX_TOKENS = 500          # Sufficient for evaluation responses

# ============================================================
# FILE PATHS - Relative to backend directory
# ============================================================
DATA_DIR = BACKEND_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
OUTPUT_DIR = DATA_DIR / "outputs"

# Unified SQLite database path
DATABASE_PATH = DATA_DIR / "quiz_ai.db"

# FAISS index and metadata paths
INDEX_PATH = VECTORSTORE_DIR / "faiss_index.bin"
META_PATH = VECTORSTORE_DIR / "chunk_meta.jsonl"

# Corpus and chunks paths
CORPUS_PATH = PROCESSED_DIR / "corpus.jsonl"
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"

# ============================================================
# AUTO-CREATE DIRECTORIES
# ============================================================
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
