"""
Main Evaluation Script for Quiz AI

Model Comparison Experiment - 4 Generator Models, 4 Metrics (Blind Judging)

Usage:
    cd tez/evaluation
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --condition llama-3.3-70b-versatile --samples 10
    python scripts/run_evaluation.py --condition all
"""

import json
import argparse
from pathlib import Path

from _bootstrap import bootstrap_paths

bootstrap_paths()

from config import (
    GENERATED_FILES,
    GENERATED_PATH,
    JUDGE_MODEL,
    RESULTS_PATH,
    ALL_MODELS,
    METRICS
)
from metrics import evaluate_generated_questions
from judge import LLMJudge


def get_result_file(condition: str) -> Path:
    """Return the evaluation result path for a model."""
    safe_name = condition.replace("/", "-")
    return RESULTS_PATH / f"eval_{safe_name}.json"


def load_generated_questions(condition: str) -> dict:
    """Load generated questions from JSON file."""
    # Try GENERATED_FILES mapping first
    file_path = GENERATED_FILES.get(condition)

    # Fallback to GENERATED_PATH with sanitized name
    if not file_path or not file_path.exists():
        safe_name = condition.replace("/", "-")
        file_path = GENERATED_PATH / f"{safe_name}.json"

    if not file_path.exists():
        print(f"Error: File not found for condition '{condition}'")
        print(f"Searched: {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data.get('questions', []))} questions from {file_path.name}")
    return data


def existing_result_is_valid(condition: str, questions_data: dict) -> bool:
    """Check whether an existing evaluation result can be safely reused."""
    result_file = get_result_file(condition)
    if not result_file.exists():
        return False

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    metadata = payload.get("metadata", {})
    model_comparison = payload.get("model_comparison", {})

    if metadata.get("generator_model") != condition:
        return False
    if metadata.get("judge_model") != JUDGE_MODEL["id"]:
        return False
    if metadata.get("generation_path") != questions_data.get("generation_path"):
        return False
    if metadata.get("shared_context_file") != questions_data.get("shared_context_file"):
        return False
    if metadata.get("total_questions") != len(questions_data.get("questions", [])):
        return False

    for metric in METRICS:
        metric_data = model_comparison.get(metric)
        if not metric_data:
            return False
        if metric_data.get("count") != len(questions_data.get("questions", [])):
            return False
        if metric_data.get("mean") is None:
            return False

    return True


def validate_generated_questions(questions_data: dict) -> None:
    """Reject invalid generation files before running judge evaluation."""
    questions = questions_data.get("questions", [])
    expected_samples = questions_data.get("expected_samples", len(questions))
    invalid = []

    if len(questions) != expected_samples:
        invalid.append(
            f"question count mismatch ({len(questions)} != expected {expected_samples})"
        )

    for idx, question in enumerate(questions):
        if not question.get("context_chunks"):
            invalid.append(f"question[{idx}] has empty context_chunks")
        if str(question.get("retrieved_context", "")).startswith("Topic:"):
            invalid.append(f"question[{idx}] uses topic-only retrieved_context")

    if invalid:
        preview = "; ".join(invalid[:5])
        raise RuntimeError(
            "Evaluation aborted: generated questions do not satisfy the shared-context "
            f"validity checks. Examples: {preview}"
        )


def validate_reportable_results(results: dict) -> None:
    """Reject partial or judge-less outputs before they can be reported."""
    metadata = results.get("metadata", {})
    total_questions = metadata.get("total_questions", 0)
    comparison = results.get("model_comparison", {})

    invalid_metrics = []
    for metric in METRICS:
        metric_data = comparison.get(metric, {})
        if metric_data.get("mean") is None:
            invalid_metrics.append(f"{metric}: missing mean score")
        if metric_data.get("count") != total_questions:
            invalid_metrics.append(
                f"{metric}: count {metric_data.get('count')} != total_questions {total_questions}"
            )

    if invalid_metrics:
        preview = "; ".join(invalid_metrics[:6])
        raise RuntimeError(
            "Evaluation aborted: result set is incomplete and cannot be used for thesis "
            f"comparison. Details: {preview}"
        )


def run_evaluation(
    condition: str,
    sample_size: int = None,
    allow_missing_judge: bool = False,
) -> dict:
    """
    Run evaluation for a specific model.

    Args:
        condition: Model ID (e.g., "llama-3.3-70b-versatile")
        sample_size: Limit number of questions (for testing)

    Returns:
        Evaluation results dict
    """
    print(f"\n{'='*60}")
    print(f"EVALUATING: {condition}")
    print(f"{'='*60}")

    # Load generated questions
    questions_data = load_generated_questions(condition)

    if not questions_data or not questions_data.get('questions'):
        print(f"No questions found for model '{condition}'")
        return {}

    print(f"Generator: {questions_data.get('model', 'unknown')}")
    print(f"Generation path: {questions_data.get('generation_path', 'unknown')}")

    if questions_data.get("generation_path") != "shared_contexts+production_mcq_generator":
        raise RuntimeError(
            "Evaluation aborted: generated questions were not produced from the "
            "clean shared-context thesis pipeline."
        )

    validate_generated_questions(questions_data)

    # Limit sample size if specified
    if sample_size and sample_size < len(questions_data.get("questions", [])):
        import random
        random.seed(42)
        questions_data["questions"] = random.sample(
            questions_data["questions"], sample_size
        )
        print(f"Limited to {sample_size} samples for testing")

    # Initialize LLM judge
    try:
        llm_judge = LLMJudge(model=JUDGE_MODEL["id"])
        print(f"LLM Judge initialized: {JUDGE_MODEL['name']}")
    except Exception as e:
        if allow_missing_judge:
            llm_judge = None
            print(f"Warning: Could not initialize LLM judge: {e}")
            print("Judge-less dry run enabled; metrics will be None and results will not be reportable.")
        else:
            raise RuntimeError(
                "Could not initialize the independent LLM judge. "
                "Thesis comparison requires a working judge because partial/null scores "
                f"would invalidate the model comparison. Original error: {e}"
            ) from e

    # Run evaluation
    results = evaluate_generated_questions(
        questions_data=questions_data,
        llm_judge=llm_judge,
        include_llm_metrics=True
    )
    results.setdefault("metadata", {}).update({
        "judge_model": JUDGE_MODEL["id"],
        "judge_name": JUDGE_MODEL["name"],
        "generation_path": questions_data.get("generation_path"),
        "shared_context_file": questions_data.get("shared_context_file"),
        "shared_context_metadata": questions_data.get("shared_context_metadata", {}),
    })
    if not allow_missing_judge:
        validate_reportable_results(results)

    return results


def save_results(results: dict, condition: str):
    """Save evaluation results to JSON."""
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    # Sanitize filename (/ → -)
    output_file = get_result_file(condition)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nResults saved: {output_file}")


def print_summary(results: dict):
    """Print evaluation summary."""
    if not results:
        print("No results to summarize")
        return

    print(f"\n{'='*70}")
    print("EVALUATION SUMMARY")
    print(f"{'='*70}")

    meta = results.get("metadata", {})
    print(f"Generator: {meta.get('generator_model', 'unknown')}")
    print(f"Total Questions: {meta.get('total_questions', 0)}")

    # Model comparison metrics
    mc = results.get("model_comparison", {})
    if mc:
        print(f"\n--- MODEL COMPARISON METRICS ---")
        print(f"{'Metric':<25} {'Mean':>8} {'Std':>8} {'Status':>10}")
        print("-" * 55)

        # Get thresholds from config
        thresholds = {name: data.get("good_threshold", 0.70) for name, data in METRICS.items()}

        for metric_name, metric_data in mc.items():
            mean = metric_data.get("mean")
            std = metric_data.get("std")

            if mean is not None:
                threshold = thresholds.get(metric_name, 0.70)
                if mean >= threshold:
                    status = "GOOD"
                elif mean >= 0.60:
                    status = "FAIR"
                else:
                    status = "POOR"

                print(f"{metric_name:<25} {mean:>8.3f} {std:>8.3f} {status:>10}")
            else:
                print(f"{metric_name:<25} {'N/A':>8} {'N/A':>8} {'N/A':>10}")

    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Quiz AI Evaluation - Model Comparison")
    parser.add_argument(
        "--condition",
        type=str,
        default="all",
        choices=["all"] + ALL_MODELS,
        help="Which model to evaluate (default: all)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Limit number of samples (for testing)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run evaluation even if a valid result file already exists"
    )
    parser.add_argument(
        "--allow-missing-judge",
        action="store_true",
        help="Allow dry-run evaluation without a working judge (not suitable for thesis reports)"
    )

    args = parser.parse_args()

    # Determine models to evaluate
    if args.condition == "all":
        conditions = ALL_MODELS
    else:
        conditions = [args.condition]

    # Run evaluations
    all_results = {}

    for condition in conditions:
        questions_data = load_generated_questions(condition)
        if not questions_data or not questions_data.get("questions"):
            print(f"No questions found for model '{condition}'")
            continue

        if not args.force and existing_result_is_valid(condition, questions_data):
            print(f"Skipping {condition}: valid evaluation result already exists.")
            with open(get_result_file(condition), "r", encoding="utf-8") as f:
                results = json.load(f)
            print_summary(results)
            all_results[condition] = results
            continue

        results = run_evaluation(
            condition=condition,
            sample_size=args.samples,
            allow_missing_judge=args.allow_missing_judge,
        )

        if results:
            save_results(results, condition)
            print_summary(results)
            all_results[condition] = results

    # Print comparison if multiple models evaluated
    if len(all_results) > 1:
        print("\n" + "=" * 100)
        print("MODEL COMPARISON SUMMARY")
        print("=" * 100)

        # 4 metrics comparison (fluency removed)
        metrics = ["question_quality", "answer_correctness", "distractor_quality", "answer_relevancy"]

        # Header
        print(f"\n{'Model':<35} ", end="")
        for m in metrics:
            short = m.replace("_", "\n")[:12]
            print(f"{short:>12}", end="")
        print()
        print("-" * 85)

        # Rows
        for condition, results in all_results.items():
            # Sanitize for display
            display_name = condition.replace("/", "/\n")[:33]
            print(f"{display_name:<35} ", end="")

            mc = results.get("model_comparison", {})
            for m in metrics:
                v = mc.get(m, {}).get("mean", 0) or 0
                print(f"{v:>12.3f}", end="")
            print()

        print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
