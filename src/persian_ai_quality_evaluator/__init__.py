"""Persian AI output quality evaluation primitives."""

from persian_ai_quality_evaluator.evaluator import evaluate_item
from persian_ai_quality_evaluator.models import EvaluationInput, ValidationError

__all__ = ["EvaluationInput", "ValidationError", "evaluate_item"]
__version__ = "0.1.0"
