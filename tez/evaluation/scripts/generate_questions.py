"""
Generate MCQs for thesis model comparison from frozen shared RAG contexts.

Methodology:
1. Shared contexts are produced once with build_shared_contexts.py.
2. Every model receives the same context set.
3. Only the generator model changes between conditions.

Usage:
    cd tez/evaluation
    python scripts/generate_questions.py --condition all --samples 100
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime

from _bootstrap import bootstrap_paths

bootstrap_paths(include_backend=True)

from config import (
    ALL_MODELS,
    SAMPLE_SIZE,
    RATE_LIMIT_DELAY,
    GENERATED_PATH,
    SHARED_CONTEXTS_FILE,
)

try:
    from app.core.mcq_generator import MCQGenerator
except ImportError as e:
    raise RuntimeError(f"Could not import production MCQ generator: {e}") from e


def get_output_file(model: str) -> Path:
    """Return the generated output path for a model."""
    safe_name = model.replace("/", "-")
    return GENERATED_PATH / f"{safe_name}.json"


def load_shared_contexts(path: Path, limit: int) -> dict:
    """Load the frozen shared RAG contexts file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Shared context file not found at {path}. "
            f"Run build_shared_contexts.py first."
        )

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    contexts = payload.get("contexts", [])
    if not contexts:
        raise RuntimeError("Shared context file is empty.")

    payload["contexts"] = contexts[:limit]
    return payload


def existing_output_is_valid(
    model: str,
    shared_context_payload: dict,
    contexts_path: Path,
) -> bool:
    """Check whether an existing generation file can be safely reused."""
    output_file = get_output_file(model)
    if not output_file.exists():
        return False

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    contexts = shared_context_payload["contexts"]
    questions = payload.get("questions", [])

    if payload.get("model") != model:
        return False
    if payload.get("generation_path") != "shared_contexts+production_mcq_generator":
        return False
    if payload.get("shared_context_file") != str(contexts_path):
        return False
    if payload.get("expected_samples") != len(contexts):
        return False
    if len(questions) != len(contexts):
        return False

    for expected, produced in zip(contexts, questions):
        if produced.get("topic") != expected.get("topic"):
            return False
        if produced.get("retrieved_context") != expected.get("retrieved_context"):
            return False
        if produced.get("context_chunks") != expected.get("context_chunks"):
            return False
        if not produced.get("question"):
            return False
        if len(produced.get("distractors", [])) != 3:
            return False

    return True


def generate_for_model(
    model: str,
    shared_context_payload: dict,
    contexts_path: Path,
    delay: float,
) -> dict:
    """Generate questions for one model using the same frozen contexts."""
    contexts = shared_context_payload["contexts"]
    generator = MCQGenerator(model_name=model)

    print("=" * 70)
    print(f"GENERATING QUESTIONS FOR: {model}")
    print(f"Shared contexts: {len(contexts)}")
    print("=" * 70)

    results = {
        "model": model,
        "samples": len(contexts),
        "expected_samples": len(contexts),
        "generation_path": "shared_contexts+production_mcq_generator",
        "shared_context_file": str(contexts_path),
        "shared_context_metadata": shared_context_payload.get("metadata", {}),
        "questions": [],
        "timestamp": datetime.now().isoformat(),
    }

    success_count = 0
    for idx, entry in enumerate(contexts, start=1):
        topic = entry["topic"]
        context_text = entry["retrieved_context"]

        print(f"\n[{idx}/{len(contexts)}] Processing: {topic}")

        start_time = time.time()
        mcq = generator.generate_mcq(context_text=context_text, difficulty="medium")
        elapsed = time.time() - start_time

        if mcq and mcq.get("question"):
            correct_text = mcq["options"][mcq["correct"]]
            distractors = [
                text for label, text in mcq["options"].items()
                if label != mcq["correct"]
            ]

            results["questions"].append({
                "topic": topic,
                "question": mcq.get("question", ""),
                "correct_answer": correct_text,
                "distractors": distractors,
                "explanation": mcq.get("explanation", ""),
                "retrieved_context": context_text,
                "context_chunks": entry.get("context_chunks", []),
                "num_chunks": entry.get("num_chunks"),
                "best_retrieval_score": entry.get("best_retrieval_score"),
                "retrieval_confidence_level": entry.get("confidence_level"),
                "model": model,
                "generation_time": elapsed,
                "timestamp": datetime.now().isoformat(),
            })
            success_count += 1
            print(f"  Generated in {elapsed:.2f}s")
        else:
            raise RuntimeError(
                f"Generation failed for model '{model}' on topic '{topic}'. "
                "Partial output was not saved so the comparison set stays aligned."
            )

        time.sleep(delay)

    if success_count != len(contexts):
        raise RuntimeError(
            f"Generation count mismatch for model '{model}': "
            f"{success_count}/{len(contexts)} questions."
        )

    GENERATED_PATH.mkdir(parents=True, exist_ok=True)
    safe_name = model.replace("/", "-")
    output_file = GENERATED_PATH / f"{safe_name}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved: {output_file}")
    print(f"Questions generated: {success_count}/{len(contexts)}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate thesis comparison MCQs from frozen shared RAG contexts")
    parser.add_argument(
        "--condition",
        type=str,
        default="all",
        choices=["all"] + ALL_MODELS,
        help="Which model(s) to generate questions for"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=SAMPLE_SIZE,
        help=f"Number of shared contexts to use (default: {SAMPLE_SIZE})"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=RATE_LIMIT_DELAY,
        help=f"Delay between generations in seconds (default: {RATE_LIMIT_DELAY})"
    )
    parser.add_argument(
        "--contexts",
        type=str,
        default=str(SHARED_CONTEXTS_FILE),
        help="Path to the frozen shared contexts JSON"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if a valid output file already exists"
    )
    args = parser.parse_args()

    shared_context_payload = load_shared_contexts(Path(args.contexts), args.samples)
    print(
        f"Loaded {len(shared_context_payload['contexts'])} frozen shared contexts "
        f"from {Path(args.contexts).name}"
    )

    models = ALL_MODELS if args.condition == "all" else [args.condition]
    for model in models:
        if not args.force and existing_output_is_valid(
            model=model,
            shared_context_payload=shared_context_payload,
            contexts_path=Path(args.contexts),
        ):
            print(f"Skipping {model}: valid generated file already exists.")
            continue

        generate_for_model(
            model=model,
            shared_context_payload=shared_context_payload,
            contexts_path=Path(args.contexts),
            delay=args.delay,
        )


if __name__ == "__main__":
    main()
