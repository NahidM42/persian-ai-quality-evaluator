import pytest

from persian_ai_quality_evaluator.models import (
    Applicability,
    EvaluationInput,
    HumanRating,
    ValidationError,
    parse_input_document,
)
from persian_ai_quality_evaluator.taxonomy import RubricDimension


def minimal_item(**updates: object) -> dict[str, object]:
    item: dict[str, object] = {"item_id": "example-1", "original_text": "متن"}
    item.update(updates)
    return item


def test_valid_input_with_optional_fields() -> None:
    item = EvaluationInput.from_dict(
        minimal_item(reference_text="reference", metadata={"model": "demo"})
    )

    assert item.reference_text == "reference"
    assert item.metadata == {"model": "demo"}


@pytest.mark.parametrize("score", [1, 5])
def test_human_score_boundaries_are_accepted(score: int) -> None:
    rating = HumanRating.from_dict({"score": score}, path="rating")

    assert rating.score == score


@pytest.mark.parametrize("score", [0, 6, 2.5, True, "4"])
def test_invalid_human_scores_are_rejected(score: object) -> None:
    with pytest.raises(ValidationError, match="integer from 1 to 5"):
        HumanRating.from_dict({"score": score}, path="rating")


@pytest.mark.parametrize("score", [0, 6, True, False])
def test_direct_human_rating_rejects_out_of_range_and_boolean_scores(score: object) -> None:
    with pytest.raises(ValidationError, match="integer from 1 to 5"):
        HumanRating(score=score)  # type: ignore[arg-type]


def test_evaluator_evidence_and_comments_are_preserved() -> None:
    rating = HumanRating.from_dict(
        {"score": 4, "evidence": ["عبارت روان است."], "comments": "Minor edit."},
        path="rating",
    )

    assert rating.evidence == ("عبارت روان است.",)
    assert rating.comments == "Minor edit."


def test_not_applicable_cannot_have_a_score() -> None:
    with pytest.raises(ValidationError, match="must be null"):
        HumanRating.from_dict(
            {"applicability": "not_applicable", "score": 3}, path="rating"
        )


def test_missing_required_fields_are_clear() -> None:
    with pytest.raises(ValidationError, match="item_id is required"):
        EvaluationInput.from_dict({"original_text": "متن"})
    with pytest.raises(ValidationError, match="original_text is required"):
        EvaluationInput.from_dict({"item_id": "x"})


def test_reference_may_be_omitted_but_not_blank() -> None:
    assert EvaluationInput.from_dict(minimal_item()).reference_text is None
    with pytest.raises(ValidationError, match="non-empty string or null"):
        EvaluationInput.from_dict(minimal_item(reference_text="  "))


def test_direct_item_rejects_scored_semantic_fidelity_without_reference() -> None:
    with pytest.raises(ValidationError, match="must be 'not_applicable'"):
        EvaluationInput(
            item_id="direct-score",
            original_text="متن",
            human_evaluation={
                RubricDimension.SEMANTIC_FIDELITY: HumanRating(score=4)
            },
        )


def test_direct_item_rejects_applicable_unrated_semantic_fidelity_without_reference() -> None:
    with pytest.raises(ValidationError, match="must be 'not_applicable'"):
        EvaluationInput(
            item_id="direct-applicable",
            original_text="متن",
            human_evaluation={
                RubricDimension.SEMANTIC_FIDELITY: HumanRating(
                    applicability=Applicability.APPLICABLE
                )
            },
        )


def test_direct_item_accepts_not_applicable_unrated_semantic_fidelity_without_reference() -> None:
    item = EvaluationInput(
        item_id="direct-not-applicable",
        original_text="متن",
        human_evaluation={
            RubricDimension.SEMANTIC_FIDELITY: HumanRating(
                applicability=Applicability.NOT_APPLICABLE
            )
        },
    )

    rating = item.human_evaluation[RubricDimension.SEMANTIC_FIDELITY]
    assert rating.applicability is Applicability.NOT_APPLICABLE
    assert rating.score is None


def test_direct_item_accepts_scored_semantic_fidelity_with_reference() -> None:
    item = EvaluationInput(
        item_id="direct-with-reference",
        original_text="متن",
        reference_text="source",
        human_evaluation={
            RubricDimension.SEMANTIC_FIDELITY: HumanRating(score=4)
        },
    )

    rating = item.human_evaluation[RubricDimension.SEMANTIC_FIDELITY]
    assert rating.applicability is Applicability.APPLICABLE
    assert rating.score == 4


def test_semantic_fidelity_score_without_reference_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must be 'not_applicable'"):
        EvaluationInput.from_dict(
            minimal_item(
                human_evaluation={"semantic_fidelity": {"score": 4}}
            )
        )


def test_semantic_fidelity_not_applicable_without_reference_is_valid() -> None:
    item = EvaluationInput.from_dict(
        minimal_item(
            human_evaluation={
                "semantic_fidelity": {
                    "applicability": "not_applicable",
                    "score": None,
                    "comments": "No source was supplied.",
                }
            }
        )
    )

    rating = item.human_evaluation[RubricDimension.SEMANTIC_FIDELITY]
    assert rating.applicability is Applicability.NOT_APPLICABLE


def test_human_evaluation_may_be_missing() -> None:
    assert EvaluationInput.from_dict(minimal_item()).human_evaluation == {}


def test_unknown_human_dimension_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown dimension"):
        EvaluationInput.from_dict(
            minimal_item(human_evaluation={"fluency_magic": {"score": 5}})
        )


def test_metadata_must_be_json_safe() -> None:
    with pytest.raises(ValidationError, match="cannot be represented in JSON"):
        EvaluationInput.from_dict(minimal_item(metadata={"values": {1, 2}}))

    with pytest.raises(ValidationError, match="non-finite number"):
        EvaluationInput.from_dict(minimal_item(metadata={"value": float("nan")}))


def test_parse_single_item_and_batch() -> None:
    assert len(parse_input_document(minimal_item())) == 1
    assert len(parse_input_document({"items": [minimal_item(), minimal_item(item_id="b")]})) == 2


def test_batch_requires_unique_ids() -> None:
    with pytest.raises(ValidationError, match="must be unique"):
        parse_input_document({"items": [minimal_item(), minimal_item()]})


def test_batch_must_not_be_empty() -> None:
    with pytest.raises(ValidationError, match="non-empty list"):
        parse_input_document({"items": []})
