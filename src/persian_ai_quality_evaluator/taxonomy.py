"""Stable issue and rubric taxonomy used in reports."""

from enum import StrEnum


class IssueCategory(StrEnum):
    """Categories shared by deterministic issues and human rubric dimensions."""

    CHARACTERS = "characters"
    UNICODE = "unicode"
    SPACING = "spacing"
    ZWNJ = "zwnj"
    PUNCTUATION = "punctuation"
    TYPOGRAPHY = "typography"
    NATURALNESS = "naturalness"
    TERMINOLOGY = "terminology"
    REGISTER = "register"
    SEMANTIC_FIDELITY = "semantic_fidelity"
    EPISTEMIC_STRENGTH = "epistemic_strength"


class Severity(StrEnum):
    """Confidence-oriented severity for deterministic findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RubricDimension(StrEnum):
    """Dimensions that require evaluator judgement rather than automation."""

    LINGUISTIC_NATURALNESS = "linguistic_naturalness"
    TERMINOLOGY = "terminology"
    REGISTER = "register"
    SEMANTIC_FIDELITY = "semantic_fidelity"
    EPISTEMIC_STRENGTH = "epistemic_strength"


RUBRIC_CATEGORY: dict[RubricDimension, IssueCategory] = {
    RubricDimension.LINGUISTIC_NATURALNESS: IssueCategory.NATURALNESS,
    RubricDimension.TERMINOLOGY: IssueCategory.TERMINOLOGY,
    RubricDimension.REGISTER: IssueCategory.REGISTER,
    RubricDimension.SEMANTIC_FIDELITY: IssueCategory.SEMANTIC_FIDELITY,
    RubricDimension.EPISTEMIC_STRENGTH: IssueCategory.EPISTEMIC_STRENGTH,
}


def taxonomy_values() -> list[str]:
    """Return the complete stable taxonomy in declaration order."""

    return [category.value for category in IssueCategory]
