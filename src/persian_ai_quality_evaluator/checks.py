"""High-confidence deterministic checks for Persian output text."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from persian_ai_quality_evaluator.models import Issue, TextLocation
from persian_ai_quality_evaluator.taxonomy import IssueCategory, Severity


_PERSIAN_LETTER = "\u0621-\u063A\u0641-\u064A\u066E-\u06D3\u06FA-\u06FF"
_SPACING_BEFORE_PUNCTUATION = re.compile(r"[ \t]+(?=[،؛؟,.!?:])")
_MISSING_SPACE_AFTER_PUNCTUATION = re.compile(
    rf"[،؛؟!?](?=[{_PERSIAN_LETTER}A-Za-z])"
)
_REPEATED_HORIZONTAL_WHITESPACE = re.compile(r"(?<=[^\s])[ \t]{2,}")
_SEPARATED_MI_PREFIX = re.compile(rf"(?<![{_PERSIAN_LETTER}])(ن?می)[ \t]+(?=[{_PERSIAN_LETTER}])")
_SEPARATED_HA_SUFFIX = re.compile(rf"(?<=[{_PERSIAN_LETTER}])[ \t]+(های?)(?![{_PERSIAN_LETTER}])")
_STRAIGHT_QUOTES_AROUND_PERSIAN = re.compile(rf'"[^"\n]*[{_PERSIAN_LETTER}][^"\n]*"')
_REPEATED_PUNCTUATION = re.compile(r"([!?؟،؛])\1+")
_THREE_DOTS = re.compile(r"(?<!\.)\.{3}(?!\.)")


def run_deterministic_checks(text: str) -> tuple[Issue, ...]:
    """Return reproducible findings without making linguistic judgements."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    issues: list[Issue] = []
    issues.extend(_character_issues(text))
    issues.extend(_unicode_issues(text))
    issues.extend(_regex_issues(text))
    return tuple(sorted(issues, key=_issue_sort_key))


def _character_issues(text: str) -> Iterable[Issue]:
    mappings = (
        ("ي", "arabic_yeh", "Arabic yeh (ي) is used instead of Persian yeh (ی).", "ی"),
        ("ك", "arabic_kaf", "Arabic kaf (ك) is used instead of Persian kaf (ک).", "ک"),
    )
    for character, code, message, suggestion in mappings:
        for match in re.finditer(re.escape(character), text):
            yield _issue(
                text,
                match.start(),
                match.end(),
                code=code,
                category=IssueCategory.CHARACTERS,
                severity=Severity.WARNING,
                message=message,
                suggestion=f"Replace with {suggestion}.",
            )


def _unicode_issues(text: str) -> Iterable[Issue]:
    if unicodedata.normalize("NFC", text) != text:
        yield Issue(
            code="non_nfc_unicode",
            category=IssueCategory.UNICODE,
            severity=Severity.INFO,
            message="Text contains Unicode sequences that are not NFC-normalized.",
            suggestion="Normalize the text to Unicode NFC.",
        )


def _regex_issues(text: str) -> Iterable[Issue]:
    definitions = (
        (
            _REPEATED_HORIZONTAL_WHITESPACE,
            "repeated_whitespace",
            IssueCategory.SPACING,
            Severity.WARNING,
            "Repeated horizontal whitespace was found.",
            "Use a single space.",
        ),
        (
            _SPACING_BEFORE_PUNCTUATION,
            "space_before_punctuation",
            IssueCategory.PUNCTUATION,
            Severity.WARNING,
            "Whitespace appears immediately before punctuation.",
            "Remove the whitespace before the punctuation mark.",
        ),
        (
            _MISSING_SPACE_AFTER_PUNCTUATION,
            "missing_space_after_punctuation",
            IssueCategory.PUNCTUATION,
            Severity.WARNING,
            "A letter follows punctuation without a space.",
            "Add a space after the punctuation mark.",
        ),
        (
            _SEPARATED_MI_PREFIX,
            "space_in_mi_prefix",
            IssueCategory.ZWNJ,
            Severity.WARNING,
            "The verbal prefix «می» or «نمی» is separated with a regular space.",
            "Use a zero-width non-joiner (نیم‌فاصله) after the prefix.",
        ),
        (
            _SEPARATED_HA_SUFFIX,
            "space_before_ha_suffix",
            IssueCategory.ZWNJ,
            Severity.WARNING,
            "The plural suffix «ها» or «های» is separated with a regular space.",
            "Use a zero-width non-joiner (نیم‌فاصله) before the suffix.",
        ),
        (
            _STRAIGHT_QUOTES_AROUND_PERSIAN,
            "ascii_quotes_for_persian",
            IssueCategory.TYPOGRAPHY,
            Severity.INFO,
            "Straight ASCII quotation marks surround Persian text.",
            "Prefer Persian guillemets «…» for Persian prose.",
        ),
        (
            _REPEATED_PUNCTUATION,
            "repeated_punctuation",
            IssueCategory.TYPOGRAPHY,
            Severity.INFO,
            "A punctuation mark is repeated.",
            "Use one punctuation mark unless repetition is intentional.",
        ),
        (
            _THREE_DOTS,
            "three_dots_instead_of_ellipsis",
            IssueCategory.TYPOGRAPHY,
            Severity.INFO,
            "Three full stops are used instead of the ellipsis character.",
            "Use the single ellipsis character (…).",
        ),
    )

    for pattern, code, category, severity, message, suggestion in definitions:
        for match in pattern.finditer(text):
            yield _issue(
                text,
                match.start(),
                match.end(),
                code=code,
                category=category,
                severity=severity,
                message=message,
                suggestion=suggestion,
            )


def _issue(
    text: str,
    start: int,
    end: int,
    *,
    code: str,
    category: IssueCategory,
    severity: Severity,
    message: str,
    suggestion: str,
) -> Issue:
    context_start = max(0, start - 12)
    context_end = min(len(text), end + 12)
    return Issue(
        code=code,
        category=category,
        severity=severity,
        message=message,
        location=TextLocation(start=start, end=end, context=text[context_start:context_end]),
        suggestion=suggestion,
    )


def _issue_sort_key(issue: Issue) -> tuple[int, str]:
    start = issue.location.start if issue.location else -1
    return (start, issue.code)
