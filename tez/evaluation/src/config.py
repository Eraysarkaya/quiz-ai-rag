"""
Evaluation configuration for Quiz AI thesis experiments.

Clean experiment design:
1. Human-like topic list is fixed.
2. RAG retrieval is executed ONCE and frozen to a shared contexts file.
3. Every generator model receives the SAME frozen contexts.
4. Blind LLM-as-a-judge scoring is used for model comparison.
"""

# ============================================================
# GENERATOR MODELS (Active comparison set)
# ============================================================

GENERATOR_MODELS = {
    "llama-3.3-70b-versatile": {
        "id": "llama-3.3-70b-versatile",
        "name": "LLaMA 3.3 70B",
        "params": "70B",
        "family": "llama-3"
    },
    "llama-3.1-8b-instant": {
        "id": "llama-3.1-8b-instant",
        "name": "LLaMA 3.1 8B",
        "params": "8B",
        "family": "llama-3"
    },
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "name": "LLaMA 4 Scout",
        "params": "17B MoE",
        "family": "llama-4"
    },
    "qwen/qwen3-32b": {
        "id": "qwen/qwen3-32b",
        "name": "Qwen 3 32B",
        "params": "32B",
        "family": "qwen"
    }
}

# ============================================================
# JUDGE MODEL (Independent from generators)
# ============================================================

JUDGE_MODEL = {
    "id": "openai/gpt-oss-120b",
    "name": "GPT-OSS 120B",
    "params": "120B"
}

# NOTE: Judge is from a DIFFERENT model family (OpenAI/GPT) than
# generators - this eliminates self-evaluation bias

# ============================================================
# EVALUATION SETTINGS
# ============================================================

SAMPLE_SIZE = 100
RATE_LIMIT_DELAY = 0.5

# Shared RAG retrieval settings used once for all models
SHARED_RAG_TOP_K = 5
SHARED_RAG_MIN_SCORE = 0.25

# ============================================================
# PATHS
# ============================================================

from pathlib import Path

BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / "data"
GENERATED_PATH = BASE_PATH / "generated"
RESULTS_PATH = BASE_PATH / "results"
REPORTS_PATH = RESULTS_PATH / "reports"

TOPICS_FILE = DATA_PATH / "topics.json"
SHARED_CONTEXTS_FILE = DATA_PATH / "shared_rag_contexts.json"

# Generated files - using official model IDs (/ replaced with - in filename)
GENERATED_FILES = {
    "llama-3.3-70b-versatile": GENERATED_PATH / "llama-3.3-70b-versatile.json",
    "llama-3.1-8b-instant": GENERATED_PATH / "llama-3.1-8b-instant.json",
    "meta-llama/llama-4-scout-17b-16e-instruct": GENERATED_PATH / "meta-llama-llama-4-scout-17b-16e-instruct.json",
    "qwen/qwen3-32b": GENERATED_PATH / "qwen-qwen3-32b.json",
}

# ============================================================
# METRICS (4 Total - Fluency removed as too subjective)
# ============================================================

METRICS = {
    "question_quality": {
        "description": "Is the question well-formed and answerable?",
        "good_threshold": 0.75
    },
    "answer_correctness": {
        "description": "Is the answer factually correct?",
        "good_threshold": 0.75
    },
    "distractor_quality": {
        "description": "Are distractors plausible but clearly wrong?",
        "good_threshold": 0.70
    },
    "answer_relevancy": {
        "description": "How relevant is the answer to the question?",
        "good_threshold": 0.75
    }
}

# ============================================================
# ALL MODELS LIST (for --condition all)
# ============================================================

ALL_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
]
