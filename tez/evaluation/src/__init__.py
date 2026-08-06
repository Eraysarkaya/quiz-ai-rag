"""
Quiz AI Evaluation Package

Model Comparison Experiment - 4 Models, 5 Metrics
"""

from .config import (
    GENERATOR_MODELS,
    JUDGE_MODEL,
    METRICS,
    SAMPLE_SIZE,
    GENERATED_FILES,
    ALL_MODELS
)

__version__ = "3.0.0"
__all__ = [
    "GENERATOR_MODELS",
    "JUDGE_MODEL",
    "METRICS",
    "SAMPLE_SIZE",
    "GENERATED_FILES",
    "ALL_MODELS"
]
