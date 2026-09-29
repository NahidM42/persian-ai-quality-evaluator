import json

from persian_ai_quality_evaluator.evaluator import evaluate_item
from persian_ai_quality_evaluator.models import EvaluationInput
from persian_ai_quality_evaluator.reporting import build_report, serialize_report, write_report


def make_report():  # type: ignore[no-untyped-def]
    item = EvaluationInput.from_dict({"item_id": "فارسی-۱", "original_text": "اين متن"})
    return build_report([evaluate_item(item)])


def test_report_has_stable_top_level_structure() -> None:
    report = make_report()

    assert list(report) == ["schema_version", "tool", "summary", "results"]
    assert report["schema_version"] == "1.0"
    assert report["summary"]["item_count"] == 1
    assert report["results"][0]["item_id"] == "فارسی-۱"


def test_serialization_preserves_persian_characters() -> None:
    serialized = serialize_report(make_report())

    assert "فارسی-۱" in serialized
    assert "\\u0641" not in serialized
    assert json.loads(serialized)["results"][0]["normalized_text"] == "این متن"


def test_report_is_json_safe_and_contains_required_result_fields() -> None:
    parsed = json.loads(serialize_report(make_report()))

    assert {
        "item_id",
        "metadata",
        "original_text",
        "reference_text",
        "normalized_text",
        "normalization_changes",
        "deterministic_issues",
        "human_evaluation",
        "issue_taxonomy",
        "summary",
    } == set(parsed["results"][0])


def test_write_report_uses_utf8_and_trailing_newline(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "report.json"

    write_report(make_report(), output)

    content = output.read_text(encoding="utf-8")
    assert "این متن" in content
    assert content.endswith("\n")


def test_batch_summary_aggregates_findings_and_ratings() -> None:
    items = [
        EvaluationInput.from_dict({"item_id": "a", "original_text": "اين"}),
        EvaluationInput.from_dict(
            {
                "item_id": "b",
                "original_text": "متن",
                "human_evaluation": {"register": {"score": 3}},
            }
        ),
    ]

    summary = build_report([evaluate_item(item) for item in items])["summary"]
    assert summary == {
        "item_count": 2,
        "deterministic_issue_count": 1,
        "normalization_change_count": 1,
        "human_rating_count": 1,
    }
