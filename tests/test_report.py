"""Summary generation: aggregation, CSV/Markdown output, and empty-log behaviour. All offline."""

import csv
import json
import math

from jev_lab.report import (
    COLUMNS,
    HEADER_LABEL,
    SUMMARY_CSV_NAME,
    SUMMARY_MD_NAME,
    TOTAL_LABEL,
    build_summary,
    generate_report,
    group_by_experiment,
)


def write_log(results_dir, records):
    """Write records as a JSONL log, the way the recorder would."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "usage.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    return path


def record(experiment="01_primitives", **overrides):
    base = {
        "experiment": experiment,
        "run_id": "run-a",
        "case_id": "case-a",
        "status": "ok",
        "latency_ms": 100.0,
        "input_tokens": 100,
        "output_tokens": 10,
        "estimated_cost_usd": 0.0000042,
    }
    return {**base, **overrides}


class TestGrouping:
    def test_buckets_by_experiment(self):
        grouped = group_by_experiment([record("a"), record("b"), record("a")])
        assert sorted(grouped) == ["a", "b"]
        assert len(grouped["a"]) == 2

    def test_missing_experiment_name_falls_back(self):
        grouped = group_by_experiment([{"status": "ok"}])
        assert list(grouped) == ["unknown"]


class TestBuildSummary:
    def test_has_a_total_row_over_every_record(self):
        summary = build_summary([record("a"), record("b")])
        assert summary[TOTAL_LABEL]["requests"] == 2
        assert summary[TOTAL_LABEL]["input_tokens"] == 200

    def test_totals_sum_across_experiments(self):
        summary = build_summary([record("a"), record("b")])
        assert summary["a"]["input_tokens"] + summary["b"]["input_tokens"] == summary[TOTAL_LABEL]["input_tokens"]

    def test_empty_log_yields_empty_summary(self):
        assert build_summary([]) == {}

    def test_cost_is_summed_per_experiment(self):
        summary = build_summary([record("a"), record("a")])
        assert round(summary["a"]["estimated_cost_usd"], 12) == round(0.0000042 * 2, 12)

    def test_all_columns_are_present_for_every_row(self):
        summary = build_summary([record("a")])
        for metrics in summary.values():
            assert set(COLUMNS) <= set(metrics)


class TestGenerateReport:
    def test_writes_csv_and_markdown(self, tmp_path):
        write_log(tmp_path, [record("01_primitives")])
        generate_report(tmp_path)
        assert (tmp_path / SUMMARY_CSV_NAME).exists()
        assert (tmp_path / SUMMARY_MD_NAME).exists()

    def test_csv_has_header_and_one_row_per_experiment_plus_total(self, tmp_path):
        write_log(tmp_path, [record("a"), record("b")])
        generate_report(tmp_path)
        rows = list(csv.reader((tmp_path / SUMMARY_CSV_NAME).read_text(encoding="utf-8").splitlines()))
        assert rows[0] == [HEADER_LABEL, *COLUMNS]
        assert [row[0] for row in rows[1:]] == ["a", "b", TOTAL_LABEL]

    def test_markdown_states_that_tokens_come_from_the_api(self, tmp_path):
        write_log(tmp_path, [record("a")])
        generate_report(tmp_path)
        text = (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")
        assert "usage" in text
        assert "Console billing is authoritative" in text

    def test_markdown_records_which_runs_are_included(self, tmp_path):
        write_log(tmp_path, [record("a", run_id="run-xyz")])
        generate_report(tmp_path)
        assert "run-xyz" in (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")

    def test_empty_log_writes_no_files(self, tmp_path):
        assert generate_report(tmp_path) == {}
        assert not (tmp_path / SUMMARY_CSV_NAME).exists()
        assert not (tmp_path / SUMMARY_MD_NAME).exists()

    def test_error_rows_are_counted_in_the_summary(self, tmp_path):
        write_log(tmp_path, [record("a"), record("a", status="error", error_type="TypeSafeError")])
        summary = generate_report(tmp_path)
        assert summary["a"]["requests"] == 2
        assert summary["a"]["errors"] == 1

    def test_unknown_cost_is_rendered_as_not_available(self, tmp_path):
        write_log(tmp_path, [record("a", estimated_cost_usd=None)])
        generate_report(tmp_path)
        assert "n/a" in (tmp_path / SUMMARY_CSV_NAME).read_text(encoding="utf-8")

    def test_malformed_log_line_is_not_silently_dropped(self, tmp_path):
        path = write_log(tmp_path, [record("a")])
        with path.open("a", encoding="utf-8") as handle:
            handle.write("this is not json\n")
        try:
            generate_report(tmp_path)
        except ValueError:
            return
        raise AssertionError("a malformed record should not be silently ignored")


# The cost actually measured by the real `01_primitives` run: 512 input tokens at $0.042/M.
MEASURED_COST = 512 * 0.042 / 1_000_000
COST_INDEX = COLUMNS.index("estimated_cost_usd")


def cost_cell(tmp_path, experiment):
    """Pull the cost cell for one experiment out of the generated CSV."""
    rows = list(csv.reader((tmp_path / SUMMARY_CSV_NAME).read_text(encoding="utf-8").splitlines()))
    header, *body = rows
    index = header.index("estimated_cost_usd")
    return next(row[index] for row in body if row[0] == experiment)


class TestSmallCostStaysVisible:
    """A real Jev call costs a fraction of a cent; the summary must not round it to nothing."""

    def test_measured_cost_does_not_render_as_zero(self, tmp_path):
        write_log(tmp_path, [record("01_primitives", estimated_cost_usd=MEASURED_COST)])
        generate_report(tmp_path)
        cell = cost_cell(tmp_path, "01_primitives")
        assert float(cell) != 0.0
        assert cell != "0.0000"

    def test_measured_cost_is_written_as_plain_decimal(self, tmp_path):
        write_log(tmp_path, [record("01_primitives", estimated_cost_usd=MEASURED_COST)])
        generate_report(tmp_path)
        cell = cost_cell(tmp_path, "01_primitives")
        assert cell == "0.000021504"
        assert "e" not in cell.lower()  # a CSV consumer should not have to parse exponents

    def test_csv_cost_agrees_with_the_logged_value_to_full_significant_precision(self, tmp_path):
        """The CSV is a numeric view accurate to ~1 ULP; `usage.jsonl` stays bit-exact."""
        write_log(tmp_path, [record("01_primitives", estimated_cost_usd=MEASURED_COST)])
        generate_report(tmp_path)
        assert math.isclose(float(cost_cell(tmp_path, "01_primitives")), MEASURED_COST, rel_tol=1e-12)

    def test_a_single_token_call_is_still_non_zero(self, tmp_path):
        """The smallest conceivable billable call: one input token."""
        write_log(tmp_path, [record("a", estimated_cost_usd=0.042 / 1_000_000)])
        generate_report(tmp_path)
        parsed = float(cost_cell(tmp_path, "a"))
        assert parsed > 0
        assert math.isclose(parsed, 0.042 / 1_000_000, rel_tol=1e-12)

    def test_markdown_shows_a_readable_dollar_amount(self, tmp_path):
        write_log(tmp_path, [record("01_primitives", estimated_cost_usd=MEASURED_COST)])
        generate_report(tmp_path)
        text = (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")
        assert "$0.0000215" in text
        # The cost cell specifically must not read as a flat zero; other columns may legitimately be 0.
        cost_cells = [line.split("|")[-2].strip() for line in text.splitlines() if line.startswith("| `")]
        assert cost_cells and all(cell.startswith("$") and cell != "$0" for cell in cost_cells)

    def test_zero_cost_is_still_rendered_as_zero(self, tmp_path):
        write_log(tmp_path, [record("a", estimated_cost_usd=0.0)])
        generate_report(tmp_path)
        assert cost_cell(tmp_path, "a") == "0"
        assert "| 0 |" in (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")

    def test_unknown_cost_stays_not_available_in_both_views(self, tmp_path):
        write_log(tmp_path, [record("a", estimated_cost_usd=None)])
        generate_report(tmp_path)
        assert cost_cell(tmp_path, "a") == "n/a"
        assert "n/a" in (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")

    def test_csv_carries_latency_without_rounding_it_away(self, tmp_path):
        write_log(tmp_path, [record("a", latency_ms=679.102)])
        generate_report(tmp_path)
        rows = list(csv.reader((tmp_path / SUMMARY_CSV_NAME).read_text(encoding="utf-8").splitlines()))
        header, *body = rows
        index = header.index("mean_latency_ms")
        assert float(body[0][index]) == 679.102

    def test_markdown_latency_is_rounded_for_readability(self, tmp_path):
        write_log(tmp_path, [record("a", latency_ms=679.102)])
        generate_report(tmp_path)
        assert "679.1" in (tmp_path / SUMMARY_MD_NAME).read_text(encoding="utf-8")

    def test_a_large_cost_keeps_normal_decimal_form(self, tmp_path):
        write_log(tmp_path, [record("a", estimated_cost_usd=1234.5)])
        generate_report(tmp_path)
        cell = cost_cell(tmp_path, "a")
        assert float(cell) == 1234.5
        assert "e" not in cell.lower()
