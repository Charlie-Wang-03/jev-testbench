"""The closing evaluation report is a derived view, and these tests hold it to that.

Three things are being defended here, in order of how expensive they would be to get wrong:

* **It cannot drift.** Every number is recomputed from the records, and the file on disk is
  compared against a fresh build. A hand-edited report fails.
* **It cannot overclaim.** A run where nothing executed must not read as a run where something
  did; a pre-registered expectation the answers contradicted must stay contradicted; and no line
  may assert a performance property the records do not carry.
* **It cannot leak.** No credential material, in any form, on any line.

Everything here is offline: the records are synthetic, or read from a local log, and nothing
touches the network.
"""

import json
import pathlib
import re

import pytest

from jev_lab.experiments import EXPERIMENTS, experiment_names
from jev_lab.final_report import (
    ACTUAL_HANDLER_EXECUTION_REALIZED,
    ACTUAL_HANDLER_EXECUTION_UNTESTED,
    CLAIM_KINDS,
    CORE_CAPABILITY_EXPLORATION_CLOSED,
    FINAL_REPORT_NAME,
    LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK,
    OPTIONAL_EDGE_COVERAGE_BACKLOG,
    build_final_report,
    measured_counts,
    measured_experiment_names,
    optional_backlog,
)
from jev_lab.recorder import DEFAULT_RESULTS_DIR, read_records
from jev_lab.report import TOTAL_LABEL, build_summary
from jev_lab.routing import (
    ROUTING,
    ROUTING_ARGUMENT_QUESTION,
    ROUTING_EXPECTED,
    ROUTING_FUNCTION_QUESTION,
    ROUTING_HUMAN_REVIEW_THRESHOLD,
    ROUTING_REVIEW_QUESTION,
    ROUTING_SUPPRESSION_EXPECTATION_MET,
    ROUTING_SUPPRESSION_EXPECTATION_MISSED,
)


def record(experiment, case_id, *, input_tokens=100, output_tokens=10, answers=None, notes=None,
           run_id="run000000000", latency_ms=600.0, timestamp="2026-01-01T00:00:00Z",
           is_first=False, run_index=1):
    """A minimal record shaped like a real `usage.jsonl` line."""
    return {
        "run_id": run_id,
        "experiment": experiment,
        "case_id": case_id,
        "model_requested": "jev-latest",
        "model_resolved": "jev-1.13.0",
        "request_id": f"req-{case_id}",
        "latency_ms": latency_ms,
        "question_count": len(answers or {}),
        "question_types": sorted({answer["type"] for answer in (answers or {}).values()}),
        "state_chars": 80,
        "state_utf8_bytes": 80,
        "timestamp_utc": timestamp,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": input_tokens * 0.042 / 1_000_000,
        "cost_basis": "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
        "status": "ok",
        "error_type": None,
        "retry_count": None,
        "case_sequence_index": run_index - 1,
        "logical_request_index_in_run": run_index,
        "client_session_id": "session00000",
        "is_first_request_in_client_session": is_first,
        "transport_attempt_count": 1,
        "transport_retry_count_observed": 0,
        "attempt_count_source": "httpx_request_event_hook",
        "schema_version": 3,
        "answers": answers or {},
        "notes": notes or {},
    }


# A case written as routine, and a case written to be withheld. Both names and both argument
# labels come from the frozen registry, so this fixture cannot drift from the sets the router
# actually closes over.
ROUTINE_CASE, WITHHELD_CASE = "oscillating_error", "out_of_range_values"


def routing_record(case_id, *, confidence, review):
    """One routing record whose dispatch is resolved entirely from its own answers.

    The function, the argument, and the pre-registered suppression expectation are read from
    `ROUTING_EXPECTED` rather than restated here: a fixture that hardcoded its own labels would
    keep passing after the registry moved, which is exactly the drift it exists to catch.
    """
    _, expected_function, expected_argument, expects_suppression = next(
        row for row in ROUTING_EXPECTED if row[0] == case_id
    )
    return record(
        ROUTING,
        case_id,
        answers={
            ROUTING_FUNCTION_QUESTION: {
                "type": "choice",
                "choice": expected_function,
                "confidence": confidence,
                "probabilities": {
                    expected_function: confidence,
                    "escalate_for_review": round(1 - confidence, 4),
                },
            },
            ROUTING_ARGUMENT_QUESTION[expected_function]: {
                "type": "choice",
                "choice": expected_argument,
                "confidence": confidence,
                "probabilities": {expected_argument: confidence},
            },
            ROUTING_REVIEW_QUESTION: {"type": "noul", "noul": review},
        },
        notes={
            "expected_function": expected_function,
            "expected_argument": expected_argument,
            "expects_suppression": expects_suppression,
        },
    )


def routing_records(*, suppress_everything):
    """The routing experiment as a run that either executed something or executed nothing."""
    # Above the review threshold either way: withheld whatever the confidence floor would say.
    review = ROUTING_HUMAN_REVIEW_THRESHOLD + 0.4 if suppress_everything else 0.1
    confidence = 0.9
    return [
        routing_record(case_id, confidence=confidence, review=review)
        for case_id in (ROUTINE_CASE, WITHHELD_CASE)
    ]


def line_with(text, needle):
    """The one line containing `needle`. Fails loudly if the report says it twice or not at all."""
    matches = [line for line in text.splitlines() if needle in line]
    assert len(matches) == 1, f"expected one line containing {needle!r}, found {len(matches)}"
    return matches[0]


def total_row(text):
    """The ledger's TOTAL row, split into cells."""
    line = line_with(text, f"| **{TOTAL_LABEL}** |")
    return [cell.strip().strip("*") for cell in line.strip("|").split("|")]


def assert_no_credentials(text):
    """Fail on anything shaped like a credential. A mention of a pattern is not a credential."""
    for pattern in TestSecretHygiene.FORBIDDEN_PATTERNS:
        match = re.search(pattern, text)
        assert match is None, f"{match.group(0)!r} must never reach a derived artifact"


# --------------------------------------------------------------------------------------
# Derived, not authored
# --------------------------------------------------------------------------------------


class TestTotalsDeriveFromTheCanonicalRecords:
    def test_the_ledger_total_equals_the_summary_of_the_records(self):
        records = [
            record("01_primitives", "a", input_tokens=500, output_tokens=40),
            record("04_confidence", "b", input_tokens=300, output_tokens=20),
        ]
        cells = total_row(build_final_report(records))
        # cells: label, requests, input, output, total, cost
        assert cells[1] == "2"
        assert cells[2] == f"{800:,}"
        assert cells[3] == f"{60:,}"
        assert cells[4] == f"{860:,}"

    def test_the_headline_counts_match_the_records(self):
        records = [record("01_primitives", "a", input_tokens=500, output_tokens=40)]
        text = build_final_report(records)
        assert "**500 input**" in text
        assert "**40 output**" in text

    def test_the_cost_is_the_local_estimate_not_a_stored_number(self):
        records = [record("01_primitives", "a", input_tokens=1_000_000, output_tokens=0)]
        text = build_final_report(records)
        summary = build_summary(records)[TOTAL_LABEL]
        assert summary["estimated_cost_usd"] == pytest.approx(0.042)
        assert "$0.042" in total_row(text)[5]

    def test_the_cost_basis_is_quoted_from_the_records(self):
        text = build_final_report([record("01_primitives", "a")])
        assert "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens" in text


class TestWhatIsReportedAsRun:
    def test_only_experiments_with_records_are_listed_as_run(self):
        records = [record("01_primitives", "a"), record("01_primitives", "b")]
        text = build_final_report(records)
        run_line = line_with(text, "experiments actually run:")
        assert "`01_primitives`" in run_line
        assert "`03_parallel_questions`" not in run_line
        assert "`12_function_routing`" not in run_line

    def test_the_run_count_is_the_number_of_distinct_experiments_with_records(self):
        records = [record("01_primitives", "a"), record("04_confidence", "b")]
        run_line = line_with(build_final_report(records), "experiments actually run:")
        assert "actually run: 2 —" in run_line

    def test_an_experiment_with_no_records_is_never_described_as_measured(self):
        text = build_final_report([record("01_primitives", "a")])
        measured = measured_experiment_names([record("01_primitives", "a")])
        assert measured == ["01_primitives"]
        for name in experiment_names():
            if name in measured or name not in text:
                continue
            # Any experiment the report names without records must be named as unrun, which here
            # means the backlog table, whose heading says exactly that.
            assert OPTIONAL_EDGE_COVERAGE_BACKLOG in text

    def test_a_record_for_an_experiment_the_registry_does_not_know_is_still_counted(self):
        # The report describes the log; it does not filter it against the registry. Dropping an
        # unknown experiment would hide a record rather than surface it.
        records = [record("99_not_registered", "a")]
        assert "`99_not_registered`" in line_with(
            build_final_report(records), "experiments actually run:"
        )


class TestTheOptionalBacklog:
    def test_it_is_the_registry_minus_what_has_records(self):
        records = [record("01_primitives", "a")]
        backlog = optional_backlog(records)
        assert [entry["name"] for entry in backlog] == [
            name for name in experiment_names() if name != "01_primitives"
        ]

    def test_an_experiment_leaves_the_backlog_once_it_has_a_record(self):
        assert "04_confidence" in [e["name"] for e in optional_backlog([])]
        assert "04_confidence" not in [e["name"] for e in optional_backlog([record("04_confidence", "a")])]

    def test_it_is_empty_when_every_registered_experiment_has_run(self):
        records = [record(name, f"case-{name}") for name in experiment_names()]
        assert optional_backlog(records) == []
        assert "nothing is outstanding" in build_final_report(records)

    def test_every_entry_carries_its_tier_and_its_declared_ceiling(self):
        from jev_lab.experiments import experiment_call_ceiling

        for entry in optional_backlog([]):
            experiment = EXPERIMENTS[entry["name"]]
            assert entry["tier"] == experiment.tier
            assert entry["calls"] == experiment_call_ceiling(experiment)
            assert entry["intent"]

    def test_the_backlog_is_marked_optional(self):
        text = build_final_report([record("01_primitives", "a")])
        assert OPTIONAL_EDGE_COVERAGE_BACKLOG in text
        assert "not** blockers for the freeze" in text


# --------------------------------------------------------------------------------------
# Honesty about what happened
# --------------------------------------------------------------------------------------


class TestHandlerExecutionIsNotUpgraded:
    """`ACTUAL_HANDLER_EXECUTION_UNTESTED` must survive any regeneration, and must be the only
    thing claimed when nothing ran."""

    def test_a_run_that_executed_nothing_says_the_branch_is_untested(self):
        text = build_final_report(routing_records(suppress_everything=True))
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED in text
        assert ACTUAL_HANDLER_EXECUTION_REALIZED not in text

    def test_it_says_why_the_branch_was_not_entered(self):
        text = build_final_report(routing_records(suppress_everything=True))
        assert "no handler was called" in text
        assert "was never entered under a live answer" in text

    def test_it_does_not_claim_a_full_execution_chain(self):
        text = build_final_report(routing_records(suppress_everything=True))
        assert "does not claim a full execution chain succeeded" in text

    def test_a_run_that_did_execute_says_so_instead(self):
        # The gate that opens: both thresholds cleared, so the inert handler is reached. The other
        # direction of the same rule -- the marker follows the records, not a fixed string.
        text = build_final_report(routing_records(suppress_everything=False))
        assert ACTUAL_HANDLER_EXECUTION_REALIZED in text
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED not in text

    def test_the_marker_follows_the_records_and_not_the_other_way_round(self):
        for suppress in (True, False):
            analysis_text = build_final_report(routing_records(suppress_everything=suppress))
            realized = ACTUAL_HANDLER_EXECUTION_REALIZED in analysis_text
            assert realized is not suppress


class TestSuppressionExpectationsArePreserved:
    def withheld(self):
        """Both cases withheld: one was written as routine, so the expectation is contradicted."""
        return routing_records(suppress_everything=True)

    def test_a_missed_expectation_is_reported_as_missed(self):
        text = build_final_report(self.withheld())
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED in text
        assert ROUTING_SUPPRESSION_EXPECTATION_MET not in text

    def test_the_mismatch_is_not_smoothed_into_agreement(self):
        text = build_final_report(self.withheld())
        assert "the disagreement is left standing" in text
        assert "no threshold was moved after seeing it" in text

    def test_an_unexpected_suppression_keeps_its_count(self):
        rows = [routing_record(ROUTINE_CASE, confidence=0.9, review=0.9)]
        text = build_final_report(rows)
        assert "1 case(s) the design wrote as routine were withheld" in text

    def test_a_met_expectation_is_reported_as_met(self):
        rows = [routing_record(WITHHELD_CASE, confidence=0.9, review=0.9)]
        text = build_final_report(rows)
        assert ROUTING_SUPPRESSION_EXPECTATION_MET in text
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED not in text


class TestNoUnsupportedClaimWording:
    """Words that would turn an observation into a guarantee, checked where they appear.

    A risky word is allowed only on a line that also carries a negation -- the report says "no
    speedup is claimed", which is the opposite of claiming one. What is banned outright is the set
    of phrases that have no honest use here at all.
    """

    BANNED = (
        "we have proven",
        "proves that",
        "is proven",
        "guarantees",
        "guaranteed",
        "is calibrated",
        "calibrated to",
        "production-ready",
        "outperforms",
        "superior to",
        "best-in-class",
        "always returns",
        "never fails",
        "is accurate",
        "accuracy of 1",
    )

    # Patterns, not bare words. `deterministic arithmetic` is a true statement about the code and
    # is a designed part of the architecture; a deterministic *model* is the claim that is banned,
    # so the pattern names the noun it has to be attached to.
    RISKY = (
        r"\bfaster\b",
        r"\bspeedup\b",
        r"\baccuracy\b",
        r"\bcalibrat\w*",
        r"\bproven\b",
        r"\bguarantee\w*",
        r"\bdeterministic (?:model|behaviou?r|output|response)\b",
        r"\bis deterministic\b",
        r"\bsuperior\b",
        r"\boutperform\w*",
        r"\bcertif\w*",
        r"\breliab\w*",
        r"\boptimal\b",
    )

    NEGATIONS = ("no ", "not ", "never", "neither", "without", "nothing", "cannot")

    def report(self):
        # One record per chapter that makes a claim, so the wording rules are checked against the
        # whole document rather than against the chapters that happen to be populated.
        return build_final_report(
            routing_records(suppress_everything=True)
            + [
                record("01_primitives", "a"),
                record("03_parallel_questions", "b"),
                # Both confidence arms, because the chapter is an A/B and is omitted with only one.
                record("04_confidence", "clear", notes={"ambiguity": "clear"}),
                record("04_confidence", "ambiguous", notes={"ambiguity": "ambiguous"}),
                record("06_composite_scoring", "d"),
            ]
        )

    def test_no_banned_phrase_appears(self):
        text = self.report().lower()
        for phrase in self.BANNED:
            assert phrase not in text, f"{phrase!r} is not a claim this bench can make"

    def test_every_risky_word_sits_on_a_line_that_denies_it(self):
        for line in self.report().splitlines():
            lowered = line.lower()
            for pattern in self.RISKY:
                if re.search(pattern, lowered):
                    assert any(
                        negation in lowered for negation in self.NEGATIONS
                    ), f"{pattern!r} asserted without a denial: {line}"

    def test_no_threshold_is_described_as_optimal_or_tuned(self):
        text = self.report()
        assert "not calibrated" in text
        assert "not claimed to be optimal" in text

    def test_latency_is_not_established_as_a_benchmark(self):
        assert LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK in self.report()

    def test_the_not_established_chapter_names_its_boundaries(self):
        text = self.report()
        for boundary in (
            "no general accuracy estimate",
            "no calibration claim",
            "no deterministic-model claim",
            "no universal repeatability bound",
            "no stable latency or speedup claim",
            "no general superiority over any other approach",
            "no universal batching ratio",
            "no proof that the composite dimensions are independent",
            "no real external side effect",
            "no production-safety certification",
        ):
            assert boundary in text, f"the report dropped {boundary!r}"

    def test_the_composite_dimensions_are_never_called_independent(self):
        text = self.report()
        for line in text.splitlines():
            if "dimension" in line.lower() and "independent" in line.lower():
                # "not shown to be empirically independent" is the only permitted reading.
                assert "not shown" in line or "no proof" in line, line

    def test_official_claims_are_attributed_to_typesafe(self):
        for line in self.report().splitlines():
            if line.startswith(f"- **{CLAIM_KINDS[0]}**"):
                assert "TypeSafe documents" in line or "published price" in line, line


class TestClaimLabels:
    def test_every_claim_is_one_of_the_five_kinds(self):
        pattern = re.compile(r"^- \*\*(.+?)\*\* — ")
        seen = set()
        for line in build_final_report(routing_records(suppress_everything=True)).splitlines():
            match = pattern.match(line)
            if match:
                assert match.group(1) in CLAIM_KINDS, match.group(1)
                seen.add(match.group(1))
        assert seen == set(CLAIM_KINDS)

    def test_the_labels_are_explained_in_the_header(self):
        text = build_final_report([record("01_primitives", "a")])
        for kind in CLAIM_KINDS:
            assert f"**{kind}**" in text


# --------------------------------------------------------------------------------------
# Hygiene
# --------------------------------------------------------------------------------------


class TestSecretHygiene:
    # Value-shaped patterns, not words. The bare word "authorization" is deliberately absent: the
    # report's own architectural conclusion is about *execution authorization*, and banning the word
    # would ban the finding. The literal strings `sk-` and `TYPESAFE_API_KEY` are absent for the same
    # reason -- chapter 16 names both as the patterns the log is scanned for, so what is banned is a
    # string that *has a value after it*, not the mention of a pattern.
    FORBIDDEN_PATTERNS = (
        r"Bearer\s+[A-Za-z0-9._~+/=-]{8,}",
        r"(?i)\bauthorization\b\s*:\s*\S",
        r"(?i)\bx-api-key\b\s*:\s*\S",
        r"sk-[A-Za-z0-9_-]{8,}",
        r"TYPESAFE_API_KEY\s*=\s*\S",
        r"(?i)\bapi[_-]?key\b\s*=\s*\S",
    )

    def test_no_credential_material_in_a_derived_report(self):
        assert_no_credentials(build_final_report(routing_records(suppress_everything=True)))

    def test_the_environment_variable_is_named_but_never_assigned(self):
        text = build_final_report([record("01_primitives", "a")])
        assert "TYPESAFE_API_KEY (environment)" in text
        assert "TYPESAFE_API_KEY=" not in text

    def test_the_secret_file_is_described_without_a_path_to_a_value(self):
        text = build_final_report([record("01_primitives", "a")])
        assert ".secrets/typesafe.env" in text
        assert "=" not in line_with(text, ".secrets/typesafe.env  (repo root")


class TestDegenerateInputs:
    def test_an_empty_log_produces_no_report(self):
        assert "No records" in build_final_report([])

    def test_an_error_record_is_still_counted(self):
        failed = record("01_primitives", "a") | {"status": "error", "error_type": "RuntimeError"}
        text = build_final_report([failed])
        assert "status error=1" in text

    def test_a_record_with_no_answers_does_not_crash_a_chapter(self):
        text = build_final_report([record("01_primitives", "a")])
        assert "## 2. Primitive behaviour" in text

    def test_a_chapter_is_omitted_rather_than_faked_when_its_experiment_is_absent(self):
        text = build_final_report([record("01_primitives", "a")])
        assert "## 10. Function routing" not in text
        assert "## 6. Batching" not in text


# --------------------------------------------------------------------------------------
# The canonical log
# --------------------------------------------------------------------------------------


def canonical_path():
    return pathlib.Path(DEFAULT_RESULTS_DIR) / "usage.jsonl"


class TestTheCanonicalLog:
    """The real log is not versioned, so these skip where it is absent. Where it is present, the
    report has to agree with it -- including about the things that went wrong."""

    def records(self):
        path = canonical_path()
        if not path.exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        records = list(read_records(path))
        assert records
        return records

    def test_the_freeze_marker_is_present(self):
        assert CORE_CAPABILITY_EXPLORATION_CLOSED in build_final_report(self.records())

    def test_the_canonical_run_still_reports_the_execution_branch_as_untested(self):
        # If a later edit made the report say a handler ran, this is where it shows up: the same
        # records cannot support both readings, and the log is the one that decides.
        text = build_final_report(self.records())
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED in text
        assert ACTUAL_HANDLER_EXECUTION_REALIZED not in text

    def test_the_canonical_run_still_reports_the_missed_suppression_expectation(self):
        text = build_final_report(self.records())
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED in text
        assert ROUTING_SUPPRESSION_EXPECTATION_MET not in text

    def test_the_canonical_totals_match_the_canonical_log(self):
        records = self.records()
        summary = build_summary(records)[TOTAL_LABEL]
        cells = total_row(build_final_report(records))
        assert cells[1] == str(summary["requests"])
        assert cells[2] == f"{summary['input_tokens']:,}"
        assert cells[3] == f"{summary['output_tokens']:,}"
        assert cells[4] == f"{summary['total_tokens']:,}"

    def test_the_canonical_backlog_is_the_registry_minus_the_log(self):
        records = self.records()
        backlog = [entry["name"] for entry in optional_backlog(records)]
        assert backlog == [name for name in experiment_names() if not measured_counts(records).get(name)]

    def test_the_file_on_disk_is_a_fresh_build_of_the_log(self):
        if not canonical_path().exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        target = pathlib.Path(DEFAULT_RESULTS_DIR) / FINAL_REPORT_NAME
        if not target.exists():
            pytest.skip(f"{FINAL_REPORT_NAME} has not been generated here yet")
        assert target.read_text(encoding="utf-8") == build_final_report(self.records())

    def test_the_canonical_report_carries_no_credential_material(self):
        assert_no_credentials(build_final_report(self.records()))


class TestWriteFinalReport:
    def test_writes_where_the_log_is_and_reads_it_back(self, tmp_path):
        from jev_lab.final_report import write_final_report

        results = tmp_path / "results"
        results.mkdir()
        log = results / "usage.jsonl"
        log.write_text("".join(json.dumps(record("01_primitives", f"c{i}")) + "\n" for i in range(3)),
                       encoding="utf-8")
        target = write_final_report(results)
        assert target is not None
        assert target.name == FINAL_REPORT_NAME
        assert "01_primitives" in target.read_text(encoding="utf-8")

    def test_no_log_means_no_file_is_written(self, tmp_path):
        from jev_lab.final_report import write_final_report

        results = tmp_path / "results"
        results.mkdir()
        assert write_final_report(results) is None
        assert not (results / FINAL_REPORT_NAME).exists()

    def test_writing_the_report_leaves_the_log_byte_identical(self, tmp_path):
        from jev_lab.final_report import write_final_report

        results = tmp_path / "results"
        results.mkdir()
        log = results / "usage.jsonl"
        log.write_text(json.dumps(record("01_primitives", "a")) + "\n", encoding="utf-8")
        before = log.read_bytes()
        write_final_report(results)
        assert log.read_bytes() == before
