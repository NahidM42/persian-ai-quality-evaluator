import pytest

from persian_ai_quality_evaluator.checks import run_deterministic_checks


def codes(text: str) -> list[str]:
    return [issue.code for issue in run_deterministic_checks(text)]


def test_finds_arabic_form_characters_with_locations() -> None:
    issues = run_deterministic_checks("اين كتاب")

    assert codes("اين كتاب") == ["arabic_yeh", "arabic_kaf"]
    assert issues[0].location is not None
    assert issues[0].location.start == 1


def test_finds_repeated_whitespace() -> None:
    assert codes("این  متن") == ["repeated_whitespace"]


def test_finds_space_before_punctuation() -> None:
    assert codes("درست است ، بعد") == ["space_before_punctuation"]


def test_finds_missing_space_after_persian_punctuation() -> None:
    assert codes("اول،بعد") == ["missing_space_after_punctuation"]


def test_does_not_flag_decimal_or_newline_indentation() -> None:
    assert codes("نسخه 3.12\n  خط دوم") == []
    assert "missing_space_after_punctuation" not in codes("نسخه 3.12")


def test_finds_selected_mi_prefix_spacing() -> None:
    assert codes("کار می کند") == ["space_in_mi_prefix"]
    assert codes("کار می‌کند") == []


def test_finds_selected_plural_suffix_spacing() -> None:
    assert codes("کتاب ها مفیدند") == ["space_before_ha_suffix"]
    assert codes("کتاب‌ها مفیدند") == []


def test_finds_persian_text_in_ascii_quotes() -> None:
    assert codes('واژه "خوب" است') == ["ascii_quotes_for_persian"]
    assert codes("واژه «خوب» است") == []


def test_finds_repeated_punctuation_and_three_dot_ellipsis() -> None:
    found = codes("واقعا؟؟...")

    assert found == ["repeated_punctuation", "three_dots_instead_of_ellipsis"]


def test_reports_non_nfc_unicode() -> None:
    assert codes("ا\u0654") == ["non_nfc_unicode"]


def test_clean_text_has_no_deterministic_findings() -> None:
    assert codes("این کتاب‌ها مفید هستند.") == []


def test_checks_reject_non_string() -> None:
    with pytest.raises(TypeError, match="text must be a string"):
        run_deterministic_checks(None)  # type: ignore[arg-type]
