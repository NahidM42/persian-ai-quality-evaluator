"""Command-line interface for Persian AI quality evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from persian_ai_quality_evaluator.evaluator import evaluate_item
from persian_ai_quality_evaluator.models import ValidationError, parse_input_document
from persian_ai_quality_evaluator.normalization import normalize_text
from persian_ai_quality_evaluator.reporting import build_report, serialize_report, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persian-ai-eval",
        description=(
            "Evaluate Persian AI output with deterministic text checks and "
            "evaluator-provided human ratings. No subjective score is generated automatically."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate a JSON item or batch and produce a structured report.",
        description=(
            "Run deterministic checks and validate supplied human ratings. "
            "Epistemic Strength assesses calibrated certainty from evaluator evidence; "
            "it is not external fact-checking."
        ),
    )
    evaluate_parser.add_argument("input", help="Path to a UTF-8 JSON input document")
    evaluate_parser.add_argument(
        "-o", "--output", help="Write the UTF-8 JSON report to this path"
    )
    evaluate_parser.set_defaults(handler=_handle_evaluate)

    normalize_parser = subparsers.add_parser(
        "normalize", help="Conservatively normalize one Persian text string."
    )
    normalize_parser.add_argument("text", help="Text to normalize")
    normalize_parser.set_defaults(handler=_handle_normalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return 0 for success or 2 for input/I/O errors."""

    args = build_parser().parse_args(argv)
    return args.handler(args)


def _handle_evaluate(args: argparse.Namespace) -> int:
    try:
        document = _read_json(args.input)
        items = parse_input_document(document)
        report = build_report([evaluate_item(item) for item in items])
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
        print(f"Error reading input '{args.input}': {error}", file=sys.stderr)
        return 2

    if args.output:
        try:
            write_report(report, args.output)
        except (OSError, UnicodeError) as error:
            print(f"Error writing report '{args.output}': {error}", file=sys.stderr)
            return 2
        print(f"Evaluated {report['summary']['item_count']} item(s).")
        print(
            "Deterministic issues: "
            f"{report['summary']['deterministic_issue_count']}"
        )
        print(f"Report: {args.output}")
    else:
        print(serialize_report(report), end="")
    return 0


def _handle_normalize(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            normalize_text(args.text).to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
    )
    return 0


def _read_json(path: str | Path) -> Any:
    content = Path(path).read_text(encoding="utf-8")
    return json.loads(content)


if __name__ == "__main__":  # pragma: no cover - exercised through the entry point
    raise SystemExit(main())
