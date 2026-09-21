"""Turn the append-only usage log into per-experiment summaries.

``results/usage.jsonl`` stays the canonical record; the CSV and Markdown files are derived views
that can be regenerated at any time and are never committed.
"""

import csv
from collections import defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from .recorder import DEFAULT_RESULTS_DIR, read_records, summarize
from .pricing import UNKNOWN_COST_BASIS

SUMMARY_CSV_NAME = "summary.csv"
SUMMARY_MD_NAME = "summary.md"

# Column order is shared by the CSV, the Markdown table, and the TOTAL row.
COLUMNS: tuple[str, ...] = (
    "requests",
    "errors",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "mean_input_tokens",
    "mean_output_tokens",
    "mean_latency_ms",
    "p50_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "estimated_cost_usd",
)

TOTAL_LABEL = "TOTAL"
HEADER_LABEL = "experiment"
COST_COLUMN = "estimated_cost_usd"

# Significant digits kept when a float is written in plain decimal notation. Jev calls cost far
# less than a cent, so the CSV must not round a real cost down to a flat 0.
CSV_SIGNIFICANT_DIGITS = 12
HUMAN_SIGNIFICANT_DIGITS = 4


def _plain_decimal(value: float, significant: int) -> str:
    """Render a float as plain decimal text, never in exponent form, trimmed of float noise.

    ``repr``-level tails are dropped: a computed ``2.1504e-05`` prints as ``0.0000215``, not
    ``0.000021504000000000003``. The raw value stays exact in ``usage.jsonl``; this is a view.
    """
    text = f"{value:.{significant}g}"
    if "e" in text or "E" in text:
        text = format(Decimal(text), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _format_cell(value: Any) -> str:
    """Render one machine-readable cell: ``None`` becomes ``n/a``, floats keep usable precision.

    Lossless enough to stay non-zero and parse back to the measured value. Rounding for human
    readability belongs in the Markdown view, not here.
    """
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return _plain_decimal(value, CSV_SIGNIFICANT_DIGITS) if value else "0"
    return str(value)


def _format_human(value: Any, *, column: str) -> str:
    """Render one cell for the Markdown table, where readability beats round-trip fidelity."""
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value == 0:
            return "0"
        if column == COST_COLUMN:
            return f"${_plain_decimal(value, HUMAN_SIGNIFICANT_DIGITS)}"
        return f"{value:.4f}" if abs(value) < 1 else f"{value:.1f}"
    return str(value)


def group_by_experiment(records: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Bucket records by experiment name, preserving first-seen order for stable output."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get("experiment", "unknown"))].append(dict(record))
    return dict(grouped)


def build_summary(records: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize every experiment plus a `TOTAL` row over all records.

    An empty log produces an empty summary rather than a row of zeroes, so an untouched repo
    does not look like a run that measured nothing.
    """
    materialized = [dict(record) for record in records]
    if not materialized:
        return {}
    grouped = group_by_experiment(materialized)
    summary = {experiment: summarize(rows) for experiment, rows in grouped.items()}
    summary[TOTAL_LABEL] = summarize(materialized)
    return summary


def write_csv(summary: Mapping[str, Mapping[str, Any]], path: Path) -> None:
    """Write the summary table as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow((HEADER_LABEL, *COLUMNS))
        for experiment, metrics in summary.items():
            writer.writerow((experiment, *(_format_cell(metrics.get(column)) for column in COLUMNS)))


def write_markdown(
    summary: Mapping[str, Mapping[str, Any]],
    path: Path,
    *,
    log_path: Path,
    record_count: int,
    run_ids: Iterable[str] = (),
) -> None:
    """Write the summary table as Markdown, with provenance and cost caveats stated up front."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Jev lab summary",
        "",
        f"- Source: `{log_path.as_posix()}` (append-only, {record_count} records)",
        f"- Runs included: {', '.join(sorted(set(run_ids))) or 'n/a'}",
        "- Token counts are the `usage` values the API returned, not local estimates.",
        "- Latency is local wall-clock around the call and includes any SDK network retries.",
        "- `estimated_cost_usd` is a local estimate from published prices; Console billing is authoritative.",
        "- This table rounds for readability. `summary.csv` carries the same numbers unrounded.",
        "",
        "| " + " | ".join((HEADER_LABEL, *COLUMNS)) + " |",
        "| " + " | ".join("---" for _ in range(len(COLUMNS) + 1)) + " |",
    ]
    for experiment, metrics in summary.items():
        cells = [_format_human(metrics.get(column), column=column) for column in COLUMNS]
        lines.append("| " + " | ".join((f"`{experiment}`", *cells)) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_report(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> dict[str, dict[str, Any]]:
    """Read the usage log and (re)write ``summary.csv`` and ``summary.md``.

    With no records there is nothing to summarize, so no files are written and ``{}`` is returned.
    """
    results_dir = Path(results_dir)
    log_path = results_dir / "usage.jsonl"
    records = list(read_records(log_path))
    summary = build_summary(records)
    if not summary:
        return {}
    write_csv(summary, results_dir / SUMMARY_CSV_NAME)
    write_markdown(
        summary,
        results_dir / SUMMARY_MD_NAME,
        log_path=log_path,
        record_count=len(records),
        run_ids=[str(record.get("run_id", "")) for record in records],
    )
    return summary


def cost_basis_note() -> str:
    """The caveat printed alongside any cost figure."""
    return f"Estimated cost is a local estimate; Console billing is authoritative. ({UNKNOWN_COST_BASIS})"
