import pytest

from persian_ai_quality_evaluator.normalization import normalize_text


def test_replaces_arabic_yeh() -> None:
    result = normalize_text("اين")

    assert result.normalized_text == "این"
    assert result.changes[0].code == "arabic_yeh_to_persian"
    assert result.changes[0].count == 1


def test_replaces_arabic_kaf() -> None:
    result = normalize_text("كتاب كوتاه")

    assert result.normalized_text == "کتاب کوتاه"
    assert result.changes[0].count == 2


def test_already_normalized_persian_is_unchanged() -> None:
    result = normalize_text("این کتاب مفید است.")

    assert result.normalized_text == result.original_text
    assert result.changes == ()


def test_empty_text_is_supported() -> None:
    assert normalize_text("").to_dict() == {
        "original_text": "",
        "normalized_text": "",
        "changes": [],
    }


def test_unicode_combining_sequence_is_normalized_to_nfc() -> None:
    result = normalize_text("ا\u0654")

    assert result.normalized_text == "أ"
    assert result.changes[0].code == "unicode_nfc"


def test_normalization_is_idempotent() -> None:
    first = normalize_text("اين كتاب")
    second = normalize_text(first.normalized_text)

    assert second.normalized_text == first.normalized_text
    assert second.changes == ()


def test_normalization_preserves_spacing_and_punctuation() -> None:
    result = normalize_text("اين  متن ،كوتاه است...")

    assert result.normalized_text == "این  متن ،کوتاه است..."


def test_normalization_rejects_non_string() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        normalize_text(42)  # type: ignore[arg-type]
