# backend/scripts/chunking.py
"""
Semantic-aware text chunking for Quiz AI.
Uses sentence tokenization to avoid mid-sentence splits.

Usage: python -m backend.scripts.chunking
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import re
from typing import List, Dict

from backend.app.core.config import (
    CORPUS_PATH,
    CHUNKS_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CHUNK_CHARS
)
from backend.app.core.utils import estimate_tokens


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= 1 and len(text) > 200:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_text_semantic(
    text: str,
    max_tokens: int = CHUNK_SIZE,
    overlap_tokens: int = CHUNK_OVERLAP,
    min_chars: int = MIN_CHUNK_CHARS
) -> List[str]:
    """Semantic chunking that respects sentence boundaries."""
    if not text or not text.strip():
        return []
    
    sentences = split_into_sentences(text)
    
    if not sentences:
        return [text.strip()] if len(text.strip()) >= min_chars else []
    
    chunks = []
    current_chunk_sentences = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)
        
        if current_tokens + sentence_tokens > max_tokens and current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            if len(chunk_text) >= min_chars:
                chunks.append(chunk_text)
            
            overlap_sentences = []
            overlap_count = 0
            for s in reversed(current_chunk_sentences):
                s_tokens = estimate_tokens(s)
                if overlap_count + s_tokens <= overlap_tokens:
                    overlap_sentences.insert(0, s)
                    overlap_count += s_tokens
                else:
                    break
            
            current_chunk_sentences = overlap_sentences
            current_tokens = overlap_count
        
        current_chunk_sentences.append(sentence)
        current_tokens += sentence_tokens
    
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        if len(chunk_text) >= min_chars:
            chunks.append(chunk_text)
    
    return chunks


def read_corpus() -> List[Dict]:
    """Load corpus from JSONL file."""
    print(f"📥 Loading corpus from: {CORPUS_PATH}")
    
    records = []
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if obj.get("context"):
                records.append(obj)
    
    print(f"📚 Loaded {len(records)} context passages.")
    return records


def build_chunks() -> List[Dict]:
    """Build chunks from corpus using semantic chunking."""
    records = read_corpus()
    
    all_chunks = []
    chunk_id = 0
    
    for record in records:
        context = record.get("context", "").strip()
        source_id = record.get("id")
        
        chunks = chunk_text_semantic(context)
        
        for idx, chunk_text in enumerate(chunks):
            chunk_record = {
                "chunk_id": chunk_id,
                "text": chunk_text,
                "source_id": source_id,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }
            all_chunks.append(chunk_record)
            chunk_id += 1
    
    print(f"✂️ Total chunks created: {len(all_chunks)}")
    
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for item in all_chunks:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"💾 Chunks saved to: {CHUNKS_PATH}")
    return all_chunks


if __name__ == "__main__":
    print("🚀 Starting semantic chunking...")
    chunks = build_chunks()
    print(f"\n🎉 Chunking completed! Total: {len(chunks)} chunks")
