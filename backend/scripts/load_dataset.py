# backend/scripts/load_dataset.py
"""
Load and extract SciQ dataset for Quiz AI corpus.
Extracts support passages to build the RAG knowledge base.

Usage: python -m backend.scripts.load_dataset
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from datasets import load_dataset as hf_load_dataset

from backend.app.core.config import PROCESSED_DIR, CORPUS_PATH


def load_and_extract_sciq():
    """Load SciQ dataset and extract usable support passages."""
    print("📥 Loading SciQ dataset from HuggingFace...")
    ds = hf_load_dataset("allenai/sciq")

    records = []
    record_id = 0

    for split in ["train", "validation", "test"]:
        for item in ds[split]:
            support = item.get("support", None)

            if support is None or support.strip() == "":
                continue

            record = {
                "id": record_id,
                "context": support.strip(),
                "original_question": item.get("question", ""),
                "original_answer": item.get("correct_answer", "")
            }
            records.append(record)
            record_id += 1

    print(f"✅ Extracted {len(records)} usable context passages.")
    return records


def save_corpus(records):
    """Save corpus to JSONL file."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"💾 Saved corpus to {CORPUS_PATH}")


if __name__ == "__main__":
    print("🚀 Starting dataset extraction...")
    records = load_and_extract_sciq()
    save_corpus(records)
    
    if records:
        print("\n📋 Sample record:")
        sample = records[0]
        print(f"   ID: {sample['id']}")
        print(f"   Context: {sample['context'][:150]}...")
    
    print("\n🎉 Dataset extraction completed successfully.")
