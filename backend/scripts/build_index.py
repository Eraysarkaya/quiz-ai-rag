# backend/scripts/build_index.py
"""
Build FAISS index from chunked corpus.
Uses SentenceTransformer embeddings with normalization for cosine similarity.

Usage: python -m backend.scripts.build_index
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from backend.app.core.config import (
    CHUNKS_PATH,
    VECTORSTORE_DIR,
    INDEX_PATH,
    META_PATH,
    EMBEDDING_MODEL
)


def load_chunks():
    """Load chunks from JSONL file."""
    print(f"📥 Loading chunks from: {CHUNKS_PATH}")
    
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"Chunks file not found at {CHUNKS_PATH}. Run chunking.py first."
        )

    texts = []
    metas = []

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj["text"])
            metas.append({
                "chunk_id": obj["chunk_id"],
                "text": obj["text"],
                "source_id": obj.get("source_id"),
                "chunk_index": obj.get("chunk_index"),
                "total_chunks": obj.get("total_chunks")
            })

    print(f"📚 Total chunks loaded: {len(texts)}")
    return texts, metas


def build_embeddings(texts: list, batch_size: int = 64) -> np.ndarray:
    """Build embeddings for all texts using SentenceTransformer."""
    print(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    all_embeddings = []
    print("🔢 Computing embeddings...")
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i + batch_size]
        emb = model.encode(
            batch_texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        all_embeddings.append(emb)

    embeddings = np.vstack(all_embeddings).astype("float32")
    print(f"✅ Embeddings shape: {embeddings.shape}")
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """Build FAISS index using IndexFlatIP for cosine similarity."""
    dim = embeddings.shape[1]
    print(f"📐 Building FAISS index (dim={dim}) using IndexFlatIP...")

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    print(f"✅ Index populated with {index.ntotal} vectors.")
    return index


def save_index_and_meta(index: faiss.Index, metas: list):
    """Save FAISS index and metadata to disk."""
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"💾 Saving FAISS index to: {INDEX_PATH}")
    # Python handles Unicode paths correctly on Windows, while FAISS' native
    # file writer may not. Serialize first and let pathlib write the bytes.
    INDEX_PATH.write_bytes(faiss.serialize_index(index).tobytes())

    print(f"💾 Saving metadata to: {META_PATH}")
    with open(META_PATH, "w", encoding="utf-8") as f:
        for m in metas:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    print("🎉 Index and metadata saved successfully.")


if __name__ == "__main__":
    print("🚀 Starting index building...")
    
    texts, metas = load_chunks()
    embeddings = build_embeddings(texts)
    index = build_faiss_index(embeddings)
    save_index_and_meta(index, metas)
    
    print("\n✅ Index building completed!")
    print(f"   📊 Total vectors: {index.ntotal}")
    print(f"   📁 Index file: {INDEX_PATH}")
    print(f"   📁 Metadata file: {META_PATH}")
