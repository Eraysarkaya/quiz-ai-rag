"""
Build a frozen shared RAG context set for thesis model comparison.

Methodology:
1. Load the fixed list of human-like science topics.
2. Run production retrieval exactly once per topic.
3. Save the retrieved context/chunks to a shared JSON file.
4. Reuse that same file for every generator model.

Usage:
    cd tez/evaluation
    python scripts/build_shared_contexts.py
    python scripts/build_shared_contexts.py --samples 100
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

from _bootstrap import bootstrap_paths

bootstrap_paths(include_backend=True)

from config import (
    TOPICS_FILE,
    SHARED_CONTEXTS_FILE,
    SAMPLE_SIZE,
    SHARED_RAG_TOP_K,
    SHARED_RAG_MIN_SCORE,
)

try:
    from app.core.rag_retriever import RAGRetriever
    from app.core.ood_detector import OODDetector
except ImportError as e:
    raise RuntimeError(f"Could not import production RAG components: {e}") from e


def load_topics(limit: int) -> list[str]:
    """Load the fixed thesis topic set."""
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("topics", [])[:limit]


def existing_shared_contexts_are_valid(
    output_path: Path,
    topics: list[str],
    top_k: int,
    min_score: float,
) -> bool:
    """Check whether a frozen shared-context file can be reused safely."""
    if not output_path.exists():
        return False

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    metadata = payload.get("metadata", {})
    contexts = payload.get("contexts", [])

    if metadata.get("experiment_type") != "shared_frozen_rag_contexts":
        return False
    if metadata.get("retrieval_top_k") != top_k:
        return False
    if metadata.get("retrieval_min_score") != min_score:
        return False
    if len(contexts) != len(topics):
        return False

    for topic, context in zip(topics, contexts):
        if context.get("topic") != topic:
            return False
        if not context.get("retrieved_context"):
            return False
        if not context.get("context_chunks"):
            return False

    return True


def retrieve_shared_contexts(
    topics: list[str],
    top_k: int,
    min_score: float,
) -> list[dict]:
    """Retrieve frozen contexts for every topic using production retrieval."""
    retriever = RAGRetriever(top_k=top_k)
    ood_detector = OODDetector()

    contexts = []

    for idx, topic in enumerate(topics, start=1):
        print(f"[{idx}/{len(topics)}] Retrieving shared context for: {topic}")

        retrieval_result = retriever.retrieve_with_context(
            topic,
            top_k=top_k,
            min_score=min_score
        )
        chunks = retrieval_result.get("chunks", [])

        if not chunks:
            raise RuntimeError(
                f"Shared context build failed: no retrieval chunks for topic '{topic}'."
            )

        ood_result = ood_detector.analyze(retrieval_result)
        if ood_result.is_ood:
            raise RuntimeError(
                f"Shared context build failed: topic '{topic}' flagged out-of-domain "
                f"(best_score={ood_result.best_score:.3f})."
            )

        contexts.append({
            "topic": topic,
            "retrieved_context": retrieval_result["context"],
            "context_chunks": chunks,
            "num_chunks": len(chunks),
            "best_retrieval_score": float(chunks[0]["score"]),
            "confidence_level": ood_result.confidence_level.value,
        })

    return contexts


def save_shared_contexts(
    contexts: list[dict],
    output_path: Path,
    top_k: int,
    min_score: float,
) -> None:
    """Persist shared context file."""
    payload = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "source_topics_file": str(TOPICS_FILE),
            "experiment_type": "shared_frozen_rag_contexts",
            "retrieval_top_k": top_k,
            "retrieval_min_score": min_score,
            "total_topics": len(contexts),
        },
        "contexts": contexts,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nShared contexts saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build frozen shared RAG contexts for thesis evaluation")
    parser.add_argument(
        "--samples",
        type=int,
        default=SAMPLE_SIZE,
        help=f"Number of topics to include (default: {SAMPLE_SIZE})"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=SHARED_RAG_TOP_K,
        help=f"Retrieval top-k for shared contexts (default: {SHARED_RAG_TOP_K})"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=SHARED_RAG_MIN_SCORE,
        help=f"Retrieval minimum score for shared contexts (default: {SHARED_RAG_MIN_SCORE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(SHARED_CONTEXTS_FILE),
        help="Output path for frozen shared contexts JSON"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild shared contexts even if a valid file already exists"
    )
    args = parser.parse_args()

    topics = load_topics(args.samples)
    if not topics:
        raise RuntimeError("No topics found for shared context generation.")

    output_path = Path(args.output)
    if not args.force and existing_shared_contexts_are_valid(
        output_path=output_path,
        topics=topics,
        top_k=args.top_k,
        min_score=args.min_score,
    ):
        print(f"Skipping shared-context build: valid file already exists at {output_path}")
        return

    print(f"Loaded {len(topics)} topics from {TOPICS_FILE.name}")
    contexts = retrieve_shared_contexts(
        topics=topics,
        top_k=args.top_k,
        min_score=args.min_score,
    )
    save_shared_contexts(
        contexts=contexts,
        output_path=output_path,
        top_k=args.top_k,
        min_score=args.min_score,
    )


if __name__ == "__main__":
    main()
