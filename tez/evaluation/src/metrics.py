"""
Core Metrics Calculator for Quiz AI Evaluation

Model Comparison Experiment - 4 Metrics (Fluency removed)
Based on: RAGAS (2023), QGEval (2024), EQGBench (2025), MMLU

BLIND JUDGING: Model names are NEVER included in judge prompts
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time


def _trim(text: str, max_chars: int = 400) -> str:
    """Trim long fields to keep judge prompts compact and stable."""
    if text is None:
        return ""
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


@dataclass
class EvaluationResult:
    """Result for a single question evaluation."""
    question_id: int
    topic: str

    # 4 metrics for model comparison (fluency removed)
    question_quality: Optional[float] = None
    answer_correctness: Optional[float] = None
    distractor_quality: Optional[float] = None
    answer_relevancy: Optional[float] = None


class MetricsCalculator:
    """
    Calculate evaluation metrics using LLM-as-Judge.

    BLIND JUDGING: Prompts do NOT include model names or identifiers.
    Judge evaluates purely based on question/answer content.
    """

    # ============================================================
    # PROMPT TEMPLATES (Blind - No model names)
    # ============================================================

    PROMPT_QUESTION_QUALITY = """Metric: question_quality
Judge whether the item is clear, unambiguous, science-topic aligned, and has one best answer.
Rubric: 0.0 invalid or confusing, 0.5 answerable but weak, 1.0 clear and educationally strong.
Question: {question}
Topic: {topic}"""

    PROMPT_ANSWER_CORRECTNESS = """Metric: answer_correctness
Judge whether the proposed correct answer is factually correct for the question and topic.
Rubric: 0.0 incorrect, 0.5 partly correct, 1.0 fully correct.
Question: {question}
Answer: {answer}
Topic: {topic}"""

    PROMPT_DISTRACTOR_QUALITY = """Metric: distractor_quality
Judge whether all distractors are plausible within the same domain yet still incorrect and non-duplicative.
Rubric: 0.0 obviously bad, 0.5 mixed quality, 1.0 all distractors are strong.
Question: {question}
Correct Answer: {correct}
Distractors: {distractors}"""

    PROMPT_ANSWER_RELEVANCY = """Metric: answer_relevancy
Judge how directly the answer responds to the exact question being asked.
Rubric: 0.0 irrelevant, 0.5 partly relevant, 1.0 directly relevant.
Question: {question}
Answer: {answer}"""

    def __init__(self, llm_judge=None):
        self.llm_judge = llm_judge

    # ============================================================
    # METRIC CALCULATION METHODS (Blind - no model info passed)
    # ============================================================

    def calc_question_quality(self, question: str, topic: str) -> Tuple[Optional[float], Dict]:
        if not self.llm_judge:
            return None, {"error": "No judge"}
        prompt = self.PROMPT_QUESTION_QUALITY.format(
            question=_trim(question, 350),
            topic=_trim(topic, 120),
        )
        result = self.llm_judge.evaluate(prompt)
        score = result.get("score")
        if score is None:
            print(f"  Warning: Failed to get question_quality score")
        return score, result

    def calc_answer_correctness(self, question: str, answer: str, topic: str) -> Tuple[Optional[float], Dict]:
        if not self.llm_judge:
            return None, {"error": "No judge"}
        prompt = self.PROMPT_ANSWER_CORRECTNESS.format(
            question=_trim(question, 300),
            answer=_trim(answer, 220),
            topic=_trim(topic, 120),
        )
        result = self.llm_judge.evaluate(prompt)
        score = result.get("score")
        if score is None:
            print(f"  Warning: Failed to get answer_correctness score")
        return score, result

    def calc_distractor_quality(self, question: str, correct: str, distractors: List[str]) -> Tuple[Optional[float], Dict]:
        if not self.llm_judge or not distractors:
            return None, {"error": "No judge or distractors"}
        prompt = self.PROMPT_DISTRACTOR_QUALITY.format(
            question=_trim(question, 220),
            correct=_trim(correct, 120),
            distractors=" | ".join(_trim(d, 80) for d in distractors[:3]),
        )
        result = self.llm_judge.evaluate(prompt)
        score = result.get("score")
        if score is None:
            print(f"  Warning: Failed to get distractor_quality score")
        return score, result

    def calc_answer_relevancy(self, question: str, answer: str) -> Tuple[Optional[float], Dict]:
        """Rate how relevant the answer is to the question (RAGAS-based)."""
        if not self.llm_judge:
            return None, {"error": "No judge"}
        prompt = self.PROMPT_ANSWER_RELEVANCY.format(
            question=_trim(question, 300),
            answer=_trim(answer, 220),
        )
        result = self.llm_judge.evaluate(prompt)
        score = result.get("score")
        if score is None:
            print(f"  Warning: Failed to get answer_relevancy score")
        return score, result


# ============================================================
# BATCH EVALUATION
# ============================================================

def evaluate_generated_questions(
    questions_data: Dict,
    llm_judge=None,
    include_llm_metrics: bool = True,
) -> Dict:
    """
    Evaluate questions with 4 metrics for model comparison.

    BLIND JUDGING: Model names are NOT passed to judge prompts.
    """

    calculator = MetricsCalculator(llm_judge=llm_judge)
    questions = questions_data.get("questions", [])
    results = []
    model_name = questions_data.get("model", "unknown")

    print(f"\n{'='*60}")
    print(f"EVALUATING: {len(questions)} questions")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    print("Metrics: Question Quality, Answer Correctness, Distractor Quality, Answer Relevancy")
    print("BLIND JUDGING: Model names hidden from judge")

    if not llm_judge:
        print("WARNING: No LLM judge - metrics will be None")
        include_llm_metrics = False

    for i, q in enumerate(questions):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  Progress: {i + 1}/{len(questions)}")

        question = q.get("question", "")
        answer = q.get("correct_answer", "")
        distractors = q.get("distractors", [])
        topic = q.get("topic", "")

        result = EvaluationResult(question_id=i, topic=topic)

        if include_llm_metrics and llm_judge:
            # 4 metrics for model comparison (no fluency)
            result.question_quality, _ = calculator.calc_question_quality(question, topic)
            result.answer_correctness, _ = calculator.calc_answer_correctness(question, answer, topic)
            result.distractor_quality, _ = calculator.calc_distractor_quality(question, answer, distractors)
            result.answer_relevancy, _ = calculator.calc_answer_relevancy(question, answer)

            time.sleep(0.5)  # Rate limit delay

        results.append(result)

    return aggregate_results(results, questions_data)


def aggregate_results(results: List[EvaluationResult], metadata: Dict) -> Dict:
    """Aggregate results for model comparison (4 metrics)."""

    def stats(values):
        valid = [v for v in values if v is not None]
        if not valid:
            return {
                "mean": None,
                "std": None,
                "count": 0,
                "median": None,
                "min": None,
                "max": None,
                "stderr": None,
                "ci95_low": None,
                "ci95_high": None,
            }

        mean_value = statistics.fmean(valid)
        std_value = statistics.pstdev(valid) if len(valid) > 1 else 0.0
        stderr = std_value / math.sqrt(len(valid)) if len(valid) > 0 else None
        ci_margin = 1.96 * stderr if stderr is not None else None

        return {
            "mean": float(mean_value),
            "std": float(std_value),
            "count": len(valid),
            "median": float(statistics.median(valid)),
            "min": float(min(valid)),
            "max": float(max(valid)),
            "stderr": float(stderr) if stderr is not None else None,
            "ci95_low": float(max(0.0, mean_value - ci_margin)) if ci_margin is not None else None,
            "ci95_high": float(min(1.0, mean_value + ci_margin)) if ci_margin is not None else None,
        }

    return {
        "metadata": {
            "generator_model": metadata.get("model", "unknown"),
            "total_questions": len(results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "model_comparison": {
            "question_quality": stats([r.question_quality for r in results]),
            "answer_correctness": stats([r.answer_correctness for r in results]),
            "distractor_quality": stats([r.distractor_quality for r in results]),
            "answer_relevancy": stats([r.answer_relevancy for r in results])
        }
    }
