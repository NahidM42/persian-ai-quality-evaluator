# Persian AI Quality Evaluator

Persian AI Quality Evaluator is a small, local Python framework for reviewing Persian-language AI output. It combines reproducible text checks with a validated structure for human linguistic judgement, producing UTF-8 JSON reports that preserve Persian text.

The project is deliberately narrow: software detects a conservative set of character, Unicode, spacing, ZWNJ, punctuation, and typography patterns; people rate naturalness, terminology, register, semantic fidelity, and epistemic strength. It does not present subjective language quality as an automatically measured fact.

## Problem and approach

Persian AI responses can contain mechanically detectable problems such as Arabic `ي`/`ك`, spacing before `،`, or a regular space in `می کند`. Other questions—whether a translation is faithful, a term is appropriate, or a claim sounds more certain than the available support—require context and human judgement.

This package keeps those two layers explicit:

```text
UTF-8 JSON input
├── original Persian output ──→ conservative normalization ──→ recorded changes
├── original Persian output ──→ deterministic checks ───────→ structured issues
└── evaluator ratings ────────→ schema validation ──────────→ rubric results
                                                              ↓
                                                     UTF-8 JSON report
```

No model, external API, network service, or paid dependency is required.

## Features

- Deterministic NFC normalization and Arabic `ي` → Persian `ی`, Arabic `ك` → Persian `ک` substitutions.
- Every normalization operation is recorded; spacing, punctuation, and wording are not silently rewritten.
- Structured deterministic findings with code, category, severity, message, code-point location/context, and a conservative suggestion.
- Checks for selected character forms, non-NFC text, repeated horizontal whitespace, punctuation spacing, obvious `می`/`نمی` and `ها`/`های` نیم‌فاصله patterns, ASCII quotes around Persian, repeated punctuation, and three-dot ellipses.
- A validated 1–5 human rubric with applicability, evidence, and comments.
- Explicit null scores for dimensions an evaluator has not rated.
- Reference-aware Semantic Fidelity validation.
- Stable single-item or batch JSON input and UTF-8 JSON reports.
- An `argparse` CLI, automated tests, generated examples, and GitHub Actions CI.

## What it intentionally does not do

The tool does not generate human rubric scores, prove that prose is natural, perform complete Persian spell/grammar checking, rewrite style, or verify real-world claims. Its deterministic rules are a high-confidence MVP subset, not full orthographic coverage.

Epistemic Strength is specifically **not fact-checking**. A human evaluator uses it to judge whether certainty language such as `ممکن است`, `شواهد نشان می‌دهد`, or `قطعا` is proportionate to the support available to that evaluator. The tool stores and validates that judgement; it does not establish whether a claim is true.

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use Python 3.12 or later:

```bash
git clone git@github.com:NahidM42/persian-ai-quality-evaluator.git
cd persian-ai-quality-evaluator
uv sync
```

The package has no runtime dependencies. `uv sync` installs pytest from the development dependency group and exposes the `persian-ai-eval` command.

## CLI usage

Evaluate the three-item sample and write a report:

```bash
uv run persian-ai-eval evaluate \
  examples/sample_input.json \
  --output examples/sample_report.json
```

Without `--output`, the complete JSON report is written to stdout. Input/schema and file errors return exit code `2` without a routine traceback; successful evaluation returns `0`. Deterministic findings are report data, not an operational CLI failure.

Normalize a short value directly:

```bash
uv run persian-ai-eval normalize "اين كتاب"
```

Use `uv run persian-ai-eval --help` or `uv run persian-ai-eval evaluate --help` for command help.

## Input schema

The CLI accepts either one item object or a non-empty batch object with an `items` list. Batch `item_id` values must be unique. This is a minimal single-item example:

```json
{
  "item_id": "response-001",
  "original_text": "شواهد نشان می‌دهد این روش ممکن است مفید باشد.",
  "reference_text": "Evidence suggests this method may be useful.",
  "metadata": {
    "model": "local-demo"
  },
  "human_evaluation": {
    "semantic_fidelity": {
      "applicability": "applicable",
      "score": 4,
      "evidence": ["The possibility and certainty level are retained."],
      "comments": "Meaning is preserved with a minor lexical difference."
    },
    "epistemic_strength": {
      "score": 5,
      "evidence": ["«شواهد نشان می‌دهد» و «ممکن است» ادعا را محدود می‌کنند."]
    }
  }
}
```

`metadata` must contain JSON-safe values. A human dimension may omit `score` or set it to `null`; that means not rated and is not converted into a score. `applicability` defaults to `applicable` and may instead be `not_applicable`, in which case `score` must be null.

See [examples/sample_input.json](examples/sample_input.json) for deterministic cleanup, a reference-aware review, and a no-reference review in one batch.

## Output

Reports contain a schema/tool header, aggregate summary, and one structured result per item. Each result retains the original and reference text, normalized text, normalization changes, deterministic issues, all five human dimensions, the stable taxonomy, and a derived summary. The arithmetic mean includes only supplied scores; a report never fills missing scores.

An abbreviated result looks like this:

```json
{
  "item_id": "deterministic-cleanup",
  "original_text": "اين  يك نمونه است ،اما كوتاه است... و \"مفيد\" است.",
  "normalized_text": "این  یک نمونه است ،اما کوتاه است... و \"مفید\" است.",
  "normalization_changes": [
    {
      "code": "arabic_yeh_to_persian",
      "description": "Replace Arabic yeh with Persian yeh.",
      "count": 3
    }
  ],
  "deterministic_issues": [
    {
      "code": "arabic_yeh",
      "category": "characters",
      "severity": "warning",
      "message": "Arabic yeh (ي) is used instead of Persian yeh (ی).",
      "location": {"start": 1, "end": 2, "context": "اين  يك نمونه "},
      "suggestion": "Replace with ی."
    }
  ]
}
```

The included [examples/sample_report.json](examples/sample_report.json) is generated by the real CLI. It is intentionally verbose so every automated finding and human-rubric state remains inspectable.

## Issue taxonomy

### Deterministic issue categories

| Category | Used for |
| --- | --- |
| `characters` | Arabic-form character substitutions |
| `unicode` | Unicode normalization state |
| `spacing` | Repeated whitespace |
| `zwnj` | Selected obvious نیم‌فاصله patterns |
| `punctuation` | Selected spacing around punctuation |
| `typography` | Quotes, ellipses, and repeated punctuation |

### Human evaluation dimensions

| Dimension | Used for |
| --- | --- |
| `naturalness` | Human Linguistic Naturalness dimension |
| `terminology` | Human Terminology dimension |
| `register` | Human Register dimension |
| `semantic_fidelity` | Human Semantic Fidelity dimension |
| `epistemic_strength` | Human Epistemic Strength dimension |

Issue locations are zero-based Python Unicode code-point offsets into `original_text`, with an end-exclusive `end` value. Deterministic checks deliberately run on the submitted text so a normalized character remains visible as a finding as well as a recorded correction.

## Human rubric

All five dimensions use the same documented scale:

| Score | Meaning |
| --- | --- |
| `1` | Major problems prevent the output from meeting the dimension. |
| `2` | Substantial problems require significant revision. |
| `3` | Acceptable overall, with clear issues to revise. |
| `4` | Good, with only minor issues. |
| `5` | Strong performance with no material issue identified. |

- **Linguistic Naturalness:** fluency and idiomatic quality as judged by a Persian-language evaluator.
- **Terminology:** appropriateness and consistency of terms for the context.
- **Register:** suitability and consistency of tone, formality, and audience fit.
- **Semantic Fidelity:** preservation of meaning relative to a supplied source/reference.
- **Epistemic Strength:** calibration of expressed certainty relative to support available to the evaluator—not external truth verification.

Evidence and comments are evaluator-authored context, never generated by the pipeline.

### Semantic Fidelity rule

Semantic Fidelity can only be rated when `reference_text` exists. Without a reference, the result always contains:

```json
{
  "dimension": "semantic_fidelity",
  "applicability": "not_applicable",
  "score": null
}
```

An input that assigns Semantic Fidelity a score—or marks it applicable—without a reference is rejected. When a reference exists but the evaluator supplies no rating, the dimension is `applicable` with a null score.

## Project structure

```text
persian-ai-quality-evaluator/
├── .github/workflows/tests.yml
├── examples/
│   ├── sample_input.json
│   └── sample_report.json
├── src/persian_ai_quality_evaluator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── checks.py
│   ├── cli.py
│   ├── evaluator.py
│   ├── models.py
│   ├── normalization.py
│   ├── reporting.py
│   └── taxonomy.py
├── tests/
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

The modules separate data validation, normalization, deterministic detection, orchestration, and serialization. Dataclasses and enums keep the report schema explicit without adding a validation framework.

## Testing

Run the complete suite:

```bash
uv run pytest -q
```

Tests cover normalization and idempotence, positive and negative deterministic cases, score and applicability validation, the no-reference Semantic Fidelity rule, missing human ratings, JSON structure and Unicode, CLI help/error paths, and end-to-end report generation. GitHub Actions runs the same locked test command on Python 3.12.

## Limitations

- The fixed patterns cover a defensible subset of Persian typography; they are not a dictionary, morphological analyzer, spell checker, or grammar checker.
- ZWNJ detection is limited to selected separated `می`/`نمی` prefixes and `ها`/`های` suffixes; context-dependent exceptions may require human review.
- Punctuation rules intentionally avoid ambiguous period/colon cases such as decimals and URLs, trading coverage for fewer false positives.
- Normalization does not repair reported spacing or typography findings.
- Reports use character offsets, not grapheme-cluster or rendered-screen coordinates.
- Human scores are only as reliable as the rubric application and evidence supplied by evaluators; inter-rater calibration is outside this MVP.
- There is no external claim verification, model inference, web UI, database, or workflow service.

## Possible extensions

Future work could add a published JSON Schema, configurable deterministic rule selection, calibrated multi-rater agreement summaries, dataset-level CSV/JSONL ingestion, and additional conservative Persian orthography rules. Any automatic language-quality model would need separate validation and must preserve the current distinction between measured patterns and human judgement.
