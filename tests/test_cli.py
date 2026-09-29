import json

import pytest

from persian_ai_quality_evaluator.cli import main


def write_json(path, data) -> None:  # type: ignore[no-untyped-def]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_help(capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    assert "deterministic text checks" in capsys.readouterr().out


def test_evaluate_writes_report(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "report.json"
    write_json(input_path, {"item_id": "cli-1", "original_text": "اين كتاب"})

    exit_code = main(["evaluate", str(input_path), "--output", str(output_path)])

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["results"][0]["normalized_text"] == "این کتاب"
    assert "Evaluated 1 item(s)." in capsys.readouterr().out


def test_evaluate_prints_json_without_output_path(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "input.json"
    write_json(input_path, {"item_id": "cli-1", "original_text": "متن"})

    assert main(["evaluate", str(input_path)]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["item_count"] == 1


def test_malformed_json_returns_error_without_traceback(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "bad.json"
    input_path.write_text("{not valid", encoding="utf-8")

    assert main(["evaluate", str(input_path)]) == 2

    error = capsys.readouterr().err
    assert "Error reading input" in error
    assert "Traceback" not in error


def test_invalid_schema_returns_error(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "invalid.json"
    write_json(input_path, {"item_id": "missing-text"})

    assert main(["evaluate", str(input_path)]) == 2

    assert "original_text is required" in capsys.readouterr().err


def test_missing_input_file_returns_error(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    missing = tmp_path / "missing.json"

    assert main(["evaluate", str(missing)]) == 2

    assert "Error reading input" in capsys.readouterr().err


def test_report_write_error_returns_nonzero(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "input.json"
    write_json(input_path, {"item_id": "cli-1", "original_text": "متن"})

    assert main(["evaluate", str(input_path), "-o", str(tmp_path)]) == 2

    assert "Error writing report" in capsys.readouterr().err


def test_normalize_command_preserves_persian_in_json(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["normalize", "اين كتاب"]) == 0

    output = capsys.readouterr().out
    assert "این کتاب" in output
    assert json.loads(output)["changes"][0]["code"] == "arabic_yeh_to_persian"
