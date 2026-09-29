"""Stable UTF-8 JSON reporting helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persian_ai_quality_evaluator import __version__
from persian_ai_quality_evaluator.models import EvaluationResult


def build_report(results: list[EvaluationResult]) -> dict[str, Any]:
    """Build a deterministic JSON-safe report for one or more results."""

    result_dicts = [result.to_dict() for result in results]
    return {
        "schema_version": "1.0",
        "tool": {
            "name": "persian-ai-quality-evaluator",
            "version": __version__,
        },
        "summary": {
            "item_count": len(results),
            "deterministic_issue_count": sum(
                len(result.deterministic_issues) for result in results
            ),
            "normalization_change_count": sum(
                sum(change.count for change in result.normalization_changes)
                for result in results
            ),
            "human_rating_count": sum(
                rating.score is not None
                for result in results
                for rating in result.human_evaluation
            ),
        },
        "results": result_dicts,
    }


def serialize_report(report: dict[str, Any]) -> str:
    """Serialize a report with readable Persian text and strict JSON numbers."""

    return json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def write_report(report: dict[str, Any], path: str | Path) -> None:
    """Write a report as UTF-8 JSON."""

    Path(path).write_text(serialize_report(report), encoding="utf-8")
