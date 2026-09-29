"""Evaluation orchestration with a strict automated/human boundary."""

from persian_ai_quality_evaluator.checks import run_deterministic_checks
from persian_ai_quality_evaluator.models import (
    Applicability,
    EvaluationInput,
    EvaluationResult,
    HumanRating,
    RubricResult,
)
from persian_ai_quality_evaluator.normalization import normalize_text
from persian_ai_quality_evaluator.taxonomy import RubricDimension, taxonomy_values


def evaluate_item(item: EvaluationInput) -> EvaluationResult:
    """Evaluate one item without inventing any subjective rubric score."""

    item.validate()
    normalization = normalize_text(item.original_text)
    ratings: list[RubricResult] = []

    for dimension in RubricDimension:
        rating = item.human_evaluation.get(dimension)
        if rating is None:
            if (
                dimension is RubricDimension.SEMANTIC_FIDELITY
                and item.reference_text is None
            ):
                rating = HumanRating(applicability=Applicability.NOT_APPLICABLE)
            else:
                rating = HumanRating()
        ratings.append(RubricResult.from_rating(dimension, rating))

    return EvaluationResult(
        item_id=item.item_id,
        metadata=dict(item.metadata),
        original_text=item.original_text,
        reference_text=item.reference_text,
        normalized_text=normalization.normalized_text,
        normalization_changes=normalization.changes,
        deterministic_issues=run_deterministic_checks(item.original_text),
        human_evaluation=tuple(ratings),
        issue_taxonomy=tuple(taxonomy_values()),
    )
