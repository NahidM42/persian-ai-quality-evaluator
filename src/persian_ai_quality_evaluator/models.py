"""Validated input and JSON-safe result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import math
from typing import Any

from persian_ai_quality_evaluator.taxonomy import (
    IssueCategory,
    RUBRIC_CATEGORY,
    RubricDimension,
    Severity,
)


class ValidationError(ValueError):
    """Raised when an evaluation document violates the public input schema."""


class Applicability(StrEnum):
    """Whether a human rubric dimension can be judged for this item."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class HumanRating:
    """An evaluator-provided rating; a null score honestly means not rated."""

    applicability: Applicability = Applicability.APPLICABLE
    score: int | None = None
    evidence: tuple[str, ...] = ()
    comments: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.applicability, Applicability):
            raise ValidationError(
                "rating.applicability must be 'applicable' or 'not_applicable'."
            )
        if self.score is not None and (
            isinstance(self.score, bool)
            or not isinstance(self.score, int)
            or not 1 <= self.score <= 5
        ):
            raise ValidationError("rating.score must be an integer from 1 to 5 or null.")
        if self.applicability is Applicability.NOT_APPLICABLE and self.score is not None:
            raise ValidationError(
                "rating.score must be null when applicability is 'not_applicable'."
            )
        if not isinstance(self.evidence, tuple) or any(
            not isinstance(value, str) or not value.strip() for value in self.evidence
        ):
            raise ValidationError("rating.evidence must be a tuple of non-empty strings.")
        if self.comments is not None and not isinstance(self.comments, str):
            raise ValidationError("rating.comments must be a string or null.")

    @classmethod
    def from_dict(cls, data: Any, *, path: str) -> HumanRating:
        if not isinstance(data, dict):
            raise ValidationError(f"{path} must be an object.")

        allowed = {"applicability", "score", "evidence", "comments"}
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ValidationError(f"{path} contains unknown field(s): {', '.join(unknown)}.")

        raw_applicability = data.get("applicability", Applicability.APPLICABLE.value)
        try:
            applicability = Applicability(raw_applicability)
        except (TypeError, ValueError) as error:
            raise ValidationError(
                f"{path}.applicability must be 'applicable' or 'not_applicable'."
            ) from error

        score = data.get("score")

        raw_evidence = data.get("evidence", [])
        if not isinstance(raw_evidence, list) or any(
            not isinstance(value, str) or not value.strip() for value in raw_evidence
        ):
            raise ValidationError(f"{path}.evidence must be a list of non-empty strings.")

        comments = data.get("comments")
        if comments is not None and not isinstance(comments, str):
            raise ValidationError(f"{path}.comments must be a string or null.")

        return cls(
            applicability=applicability,
            score=score,
            evidence=tuple(raw_evidence),
            comments=comments,
        )


@dataclass(frozen=True, slots=True)
class EvaluationInput:
    """A Persian AI output and optional reference and human judgement."""

    item_id: str
    original_text: str
    reference_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    human_evaluation: dict[RubricDimension, HumanRating] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate this instance, including its mutable rubric mapping."""

        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValidationError("item.item_id must be a non-empty string.")
        if not isinstance(self.original_text, str):
            raise ValidationError("item.original_text must be a string.")
        if self.reference_text is not None and (
            not isinstance(self.reference_text, str) or not self.reference_text.strip()
        ):
            raise ValidationError("item.reference_text must be a non-empty string or null.")
        if not isinstance(self.metadata, dict):
            raise ValidationError("item.metadata must be an object.")
        _validate_json_value(self.metadata, path="item.metadata")
        if not isinstance(self.human_evaluation, dict):
            raise ValidationError("item.human_evaluation must be an object.")
        for dimension, rating in self.human_evaluation.items():
            if not isinstance(dimension, RubricDimension):
                raise ValidationError("item.human_evaluation contains an unknown dimension.")
            if not isinstance(rating, HumanRating):
                raise ValidationError(
                    f"item.human_evaluation.{dimension.value} must be a HumanRating."
                )

        semantic = self.human_evaluation.get(RubricDimension.SEMANTIC_FIDELITY)
        if self.reference_text is None and semantic is not None:
            if semantic.applicability is not Applicability.NOT_APPLICABLE:
                raise ValidationError(
                    "item.human_evaluation.semantic_fidelity must be "
                    "'not_applicable' when reference_text is absent."
                )

    def __post_init__(self) -> None:
        self.validate()
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "human_evaluation", dict(self.human_evaluation))

    @classmethod
    def from_dict(cls, data: Any, *, path: str = "item") -> EvaluationInput:
        if not isinstance(data, dict):
            raise ValidationError(f"{path} must be an object.")

        allowed = {
            "item_id",
            "original_text",
            "reference_text",
            "metadata",
            "human_evaluation",
        }
        unknown = sorted(set(data) - allowed)
        if unknown:
            raise ValidationError(f"{path} contains unknown field(s): {', '.join(unknown)}.")

        if "item_id" not in data:
            raise ValidationError(f"{path}.item_id is required.")
        item_id = data["item_id"]

        if "original_text" not in data:
            raise ValidationError(f"{path}.original_text is required.")
        original_text = data["original_text"]

        reference_text = data.get("reference_text")
        metadata = data.get("metadata", {})

        raw_human = data.get("human_evaluation", {})
        if not isinstance(raw_human, dict):
            raise ValidationError(f"{path}.human_evaluation must be an object.")

        human_evaluation: dict[RubricDimension, HumanRating] = {}
        for raw_dimension, raw_rating in raw_human.items():
            try:
                dimension = RubricDimension(raw_dimension)
            except (TypeError, ValueError) as error:
                valid = ", ".join(dimension.value for dimension in RubricDimension)
                raise ValidationError(
                    f"{path}.human_evaluation has unknown dimension {raw_dimension!r}; "
                    f"expected one of: {valid}."
                ) from error
            human_evaluation[dimension] = HumanRating.from_dict(
                raw_rating, path=f"{path}.human_evaluation.{dimension.value}"
            )

        return cls(
            item_id=item_id,
            original_text=original_text,
            reference_text=reference_text,
            metadata=metadata,
            human_evaluation=human_evaluation,
        )


@dataclass(frozen=True, slots=True)
class NormalizationChange:
    code: str
    description: str
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "description": self.description, "count": self.count}


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    original_text: str
    normalized_text: str
    changes: tuple[NormalizationChange, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "changes": [change.to_dict() for change in self.changes],
        }


@dataclass(frozen=True, slots=True)
class TextLocation:
    start: int
    end: int
    context: str

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "context": self.context}


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    category: IssueCategory
    severity: Severity
    message: str
    location: TextLocation | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location.to_dict() if self.location else None,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True, slots=True)
class RubricResult:
    dimension: RubricDimension
    category: IssueCategory
    applicability: Applicability
    score: int | None
    evidence: tuple[str, ...]
    comments: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "category": self.category.value,
            "applicability": self.applicability.value,
            "score": self.score,
            "evidence": list(self.evidence),
            "comments": self.comments,
        }

    @classmethod
    def from_rating(
        cls, dimension: RubricDimension, rating: HumanRating
    ) -> RubricResult:
        return cls(
            dimension=dimension,
            category=RUBRIC_CATEGORY[dimension],
            applicability=rating.applicability,
            score=rating.score,
            evidence=rating.evidence,
            comments=rating.comments,
        )


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    item_id: str
    metadata: dict[str, Any]
    original_text: str
    reference_text: str | None
    normalized_text: str
    normalization_changes: tuple[NormalizationChange, ...]
    deterministic_issues: tuple[Issue, ...]
    human_evaluation: tuple[RubricResult, ...]
    issue_taxonomy: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        rated = [rating.score for rating in self.human_evaluation if rating.score is not None]
        not_applicable = sum(
            rating.applicability is Applicability.NOT_APPLICABLE
            for rating in self.human_evaluation
        )
        return {
            "item_id": self.item_id,
            "metadata": self.metadata,
            "original_text": self.original_text,
            "reference_text": self.reference_text,
            "normalized_text": self.normalized_text,
            "normalization_changes": [
                change.to_dict() for change in self.normalization_changes
            ],
            "deterministic_issues": [issue.to_dict() for issue in self.deterministic_issues],
            "human_evaluation": [rating.to_dict() for rating in self.human_evaluation],
            "issue_taxonomy": list(self.issue_taxonomy),
            "summary": {
                "normalization_change_count": sum(
                    change.count for change in self.normalization_changes
                ),
                "deterministic_issue_count": len(self.deterministic_issues),
                "rated_dimension_count": len(rated),
                "not_rated_dimension_count": len(self.human_evaluation)
                - len(rated)
                - not_applicable,
                "not_applicable_dimension_count": not_applicable,
                "mean_human_score": round(sum(rated) / len(rated), 2) if rated else None,
            },
        }


def parse_input_document(data: Any) -> list[EvaluationInput]:
    """Parse either one item or an ``{"items": [...]}`` batch document."""

    if not isinstance(data, dict):
        raise ValidationError("The JSON root must be an object.")

    if "items" not in data:
        return [EvaluationInput.from_dict(data)]

    if set(data) != {"items"}:
        unknown = sorted(set(data) - {"items"})
        raise ValidationError(
            f"A batch document may only contain 'items'; unknown field(s): {', '.join(unknown)}."
        )
    raw_items = data["items"]
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("items must be a non-empty list.")

    items = [
        EvaluationInput.from_dict(raw_item, path=f"items[{index}]")
        for index, raw_item in enumerate(raw_items)
    ]
    identifiers = [item.item_id for item in items]
    duplicates = sorted({item_id for item_id in identifiers if identifiers.count(item_id) > 1})
    if duplicates:
        raise ValidationError(f"item_id values must be unique; duplicate(s): {', '.join(duplicates)}.")
    return items


def _validate_json_value(value: Any, *, path: str) -> None:
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError(f"{path} contains a non-finite number.")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path} keys must be strings.")
            _validate_json_value(item, path=f"{path}.{key}")
        return
    raise ValidationError(f"{path} contains a value that cannot be represented in JSON.")
