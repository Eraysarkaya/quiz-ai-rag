"""
Run the complete thesis evaluation pipeline in the intended order.

Steps:
1. Build frozen shared RAG contexts once.
2. Generate questions for all models from the same contexts.
3. Run blind judge evaluation for all models.
4. Generate thesis-ready reports (.md + Excel).

Usage:
    cd tez/evaluation
    python scripts/run_full_experiment.py
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

from _bootstrap import bootstrap_paths

bootstrap_paths()

from config import ALL_MODELS, JUDGE_MODEL


SCRIPT_DIR = Path(__file__).resolve().parent
EVALUATION_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = EVALUATION_ROOT.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"


def validate_prerequisites() -> None:
    """Fail fast on missing files before starting the experiment."""
    required_files = [
        EVALUATION_ROOT / "data" / "topics.json",
        BACKEND_ROOT / "data" / "vectorstore" / "faiss_index.bin",
        BACKEND_ROOT / "data" / "vectorstore" / "chunk_meta.jsonl",
        PROJECT_ROOT / ".env",
    ]

    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        joined = "\n".join(missing)
        raise SystemExit(f"Missing prerequisite files:\n{joined}")

    print(f"Python executable: {sys.executable}")
    print(f"Evaluation root: {EVALUATION_ROOT}")
    print(f"Backend root: {BACKEND_ROOT}")


def load_groq_api_key() -> str:
    """Read Groq API key from environment or project .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        return api_key

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise SystemExit("GROQ_API_KEY not found in environment or project .env")


def validate_model_registry() -> None:
    """Fail fast if configured generator or judge models are not active on Groq."""
    try:
        from groq import Groq
    except ImportError as exc:
        raise SystemExit(
            "groq package is not installed in the active Python environment."
        ) from exc

    if JUDGE_MODEL["id"] in ALL_MODELS:
        raise SystemExit("Judge model must not also appear in generator models.")

    client = Groq(api_key=load_groq_api_key())
    try:
        response = client.models.list()
    except Exception as exc:
        raise SystemExit(f"Could not query Groq model registry: {exc}") from exc

    active_models = {model.id for model in response.data}
    required_models = set(ALL_MODELS) | {JUDGE_MODEL["id"]}
    missing = sorted(required_models - active_models)

    if missing:
        visible_active = ", ".join(sorted(active_models))
        joined_missing = ", ".join(missing)
        raise SystemExit(
            "Configured models are not active on Groq.\n"
            f"Missing: {joined_missing}\n"
            f"Active models returned by API: {visible_active}"
        )

    print("Groq model registry check passed.")


def clean_previous_outputs() -> None:
    """Remove previous experiment artifacts to avoid mixed-result folders."""
    targets = [
        EVALUATION_ROOT / "data" / "shared_rag_contexts.json",
        *list((EVALUATION_ROOT / "generated").glob("*.json")),
        *list((EVALUATION_ROOT / "results").glob("eval_*.json")),
        EVALUATION_ROOT / "results" / "reports" / "model_comparison.xlsx",
        EVALUATION_ROOT / "results" / "reports" / "model_comparison.txt",
        EVALUATION_ROOT / "results" / "reports" / "SONUCLAR.md",
        EVALUATION_ROOT / "results" / "reports" / "METODOLOJI.md",
    ]

    for path in targets:
        if path.exists():
            path.unlink()
            print(f"Removed old artifact: {path}")


def run_step(script: str, args: list[str] | None = None) -> None:
    args = args or []
    cmd = [sys.executable, str(SCRIPT_DIR / script), *args]
    print("\n" + "=" * 80)
    print("RUNNING:", " ".join(cmd))
    print("=" * 80)
    completed = subprocess.run(cmd, check=False, cwd=EVALUATION_ROOT)
    if completed.returncode != 0:
        raise SystemExit(f"Step failed: {script} (exit code {completed.returncode})")


def main():
    parser = argparse.ArgumentParser(description="Run the full thesis evaluation pipeline")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete previous artifacts and rebuild everything from scratch"
    )
    parser.add_argument(
        "--force-generation",
        action="store_true",
        help="Regenerate model outputs even if valid generation files already exist"
    )
    parser.add_argument(
        "--force-evaluation",
        action="store_true",
        help="Re-run judge evaluation even if valid result files already exist"
    )
    parser.add_argument(
        "--force-contexts",
        action="store_true",
        help="Rebuild frozen shared contexts even if a valid context file already exists"
    )
    args = parser.parse_args()

    validate_prerequisites()
    validate_model_registry()

    if args.fresh:
        clean_previous_outputs()

    build_args: list[str] = []
    generate_args: list[str] = ["--condition", "all"]
    evaluation_args: list[str] = ["--condition", "all"]

    if args.force_contexts or args.fresh:
        build_args.append("--force")
    if args.force_generation or args.fresh:
        generate_args.append("--force")
    if args.force_evaluation or args.fresh:
        evaluation_args.append("--force")

    run_step("build_shared_contexts.py", build_args)
    run_step("generate_questions.py", generate_args)
    run_step("run_evaluation.py", evaluation_args)
    run_step("generate_reports.py")


if __name__ == "__main__":
    main()
