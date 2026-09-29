from persian_ai_quality_evaluator.evaluator import evaluate_item
import pytest

from persian_ai_quality_evaluator.models import (
    Applicability,
    EvaluationInput,
    HumanRating,
    ValidationError,
)
from persian_ai_quality_evaluator.taxonomy import IssueCategory, RubricDimension


def get_dimension(result, dimension: RubricDimension):  # type: ignore[no-untyped-def]
    return next(rating for rating in result.human_evaluation if rating.dimension is dimension)


def test_no_reference_makes_semantic_fidelity_not_applicable() -> None:
    result = evaluate_item(EvaluationInput.from_dict({"item_id": "x", "original_text": "متن"}))

    semantic = get_dimension(result, RubricDimension.SEMANTIC_FIDELITY)
    assert semantic.applicability is Applicability.NOT_APPLICABLE
    assert semantic.score is None


def test_evaluator_revalidates_mutated_human_evaluation_mapping() -> None:
    item = EvaluationInput(item_id="mutable-map", original_text="متن")
    item.human_evaluation[RubricDimension.SEMANTIC_FIDELITY] = HumanRating(score=5)

    with pytest.raises(ValidationError, match="must be 'not_applicable'"):
        evaluate_item(item)


def test_reference_makes_unrated_semantic_fidelity_applicable() -> None:
    item = EvaluationInput.from_dict(
        {"item_id": "x", "original_text": "متن", "reference_text": "source"}
    )

    semantic = get_dimension(evaluate_item(item), RubricDimension.SEMANTIC_FIDELITY)
    assert semantic.applicability is Applicability.APPLICABLE
    assert semantic.score is None


def test_supplied_human_rating_is_preserved() -> None:
    item = EvaluationInput.from_dict(
        {
            "item_id": "x",
            "original_text": "متن روان است.",
            "human_evaluation": {
                "linguistic_naturalness": {
                    "score": 5,
                    "evidence": ["ساختار جمله طبیعی است."],
                    "comments": "No edits needed.",
                }
            },
        }
    )

    rating = get_dimension(evaluate_item(item), RubricDimension.LINGUISTIC_NATURALNESS)
    assert rating.score == 5
    assert rating.evidence == ("ساختار جمله طبیعی است.",)
    assert rating.comments == "No edits needed."


def test_missing_human_scores_remain_null() -> None:
    result_dict = evaluate_item(
        EvaluationInput.from_dict({"item_id": "x", "original_text": "متن"})
    ).to_dict()

    assert all(rating["score"] is None for rating in result_dict["human_evaluation"])
    assert result_dict["summary"]["mean_human_score"] is None


def test_checks_original_while_returning_normalized_text() -> None:
    result = evaluate_item(
        EvaluationInput.from_dict({"item_id": "x", "original_text": "اين كتاب"})
    )

    assert result.normalized_text == "این کتاب"
    assert [issue.code for issue in result.deterministic_issues] == [
        "arabic_yeh",
        "arabic_kaf",
    ]


def test_result_includes_complete_taxonomy() -> None:
    result = evaluate_item(
        EvaluationInput.from_dict({"item_id": "x", "original_text": "متن"})
    )

    assert result.issue_taxonomy == tuple(category.value for category in IssueCategory)


def test_summary_counts_rated_missing_and_not_applicable_dimensions() -> None:
    item = EvaluationInput.from_dict(
        {
            "item_id": "x",
            "original_text": "متن",
            "human_evaluation": {"register": {"score": 4}},
        }
    )

    summary = evaluate_item(item).to_dict()["summary"]
    assert summary["rated_dimension_count"] == 1
    assert summary["not_rated_dimension_count"] == 3
    assert summary["not_applicable_dimension_count"] == 1
    assert summary["mean_human_score"] == 4.0
