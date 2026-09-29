"""Conservative, deterministic Persian text normalization."""

import unicodedata

from persian_ai_quality_evaluator.models import NormalizationChange, NormalizationResult


_CHARACTER_REPLACEMENTS = (
    ("ي", "ی", "arabic_yeh_to_persian", "Replace Arabic yeh with Persian yeh."),
    ("ك", "ک", "arabic_kaf_to_persian", "Replace Arabic kaf with Persian kaf."),
)


def normalize_text(text: str) -> NormalizationResult:
    """Apply NFC plus two safe Persian character substitutions.

    The function intentionally does not alter spacing, punctuation, wording, or ZWNJ.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    changes: list[NormalizationChange] = []
    normalized = unicodedata.normalize("NFC", text)
    if normalized != text:
        changes.append(
            NormalizationChange(
                code="unicode_nfc",
                description="Normalize Unicode combining sequences to NFC.",
                count=1,
            )
        )

    for source, target, code, description in _CHARACTER_REPLACEMENTS:
        count = normalized.count(source)
        if count:
            normalized = normalized.replace(source, target)
            changes.append(
                NormalizationChange(code=code, description=description, count=count)
            )

    return NormalizationResult(
        original_text=text,
        normalized_text=normalized,
        changes=tuple(changes),
    )
