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

from jev_lab.composite import COMPOSITE, COMPOSITE_DIMENSIONS
from jev_lab.experiments import (
    CONFIDENCE_GATE_THRESHOLD,
    EXPERIMENTS,
    GATE_ACCEPT,
    GATE_ESCALATE,
    experiment_names,
)
from jev_lab.fanout import FANOUT, PARALLEL
from jev_lab.final_report import (
    ACTUAL_HANDLER_EXECUTION_REALIZED,
    ACTUAL_HANDLER_EXECUTION_UNTESTED,
    CLAIM_KINDS,
    CORE_CAPABILITY_EXPLORATION_CLOSED,
    FINAL_REPORT_NAME,
    LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK,
    LIMITATION,
    LOCAL_MEASUREMENT,
    OPTIONAL_EDGE_COVERAGE_BACKLOG,
    _difference_phrase,
    _saving_phrase,
    build_final_report,
    confidence_gate,
    measured_counts,
    measured_experiment_names,
    optional_backlog,
)
from jev_lab.recorder import DEFAULT_RESULTS_DIR, read_records
from jev_lab.report import TOTAL_LABEL, build_summary
from jev_lab.routing import (
    FAIL_CLOSED_SUPPRESSION_REALIZED,
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


# --------------------------------------------------------------------------------------
# Measurement-dependent prose follows the measurement
# --------------------------------------------------------------------------------------
#
# Every claim below was, at some point, a fixed sentence asserting an outcome the generator never
# computed -- the `04_confidence` gate being the one that was actually wrong against the frozen
# log. Each test moves the underlying record and holds the sentence to the move, in both
# directions: a generator that ignored the records would fail half of every pair here.

CONFIDENCE = "04_confidence"
INSTRUCTION = "07_instruction_precision"
GATE_LINE = "which is the gate behaving as written"


def confidence_record(case_id, ambiguity, *, confidence, threshold=CONFIDENCE_GATE_THRESHOLD,
                      decision=None):
    """One `04_confidence` record, carrying the gate the run would have stored for its confidence.

    `decision` is overridable so a record can be built that contradicts its own numbers; nothing
    else here does that, because the point of the gate is that the two agree.
    """
    return record(
        CONFIDENCE,
        case_id,
        answers={
            "intent": {
                "type": "choice",
                "choice": "other",
                "confidence": confidence,
                "probabilities": {"other": confidence},
            },
            "specificity": {
                "type": "score",
                "score": 1.0,
                "confidence": 0.9,
                "legend": {"0": "none", "1": "hinted", "2": "stated"},
                "probabilities": {"2": 1.0},
            },
        },
        notes={
            "ambiguity": ambiguity,
            "derived": {
                "intent": "other",
                "intent_confidence": confidence,
                "expected": None,
                "matches_expected": None,
                "gate": {
                    "decision": decision
                    if decision is not None
                    else (GATE_ACCEPT if confidence >= threshold else GATE_ESCALATE),
                    "threshold": threshold,
                    "threshold_basis": (
                        "demo threshold; not calibrated, not tuned on any data, not claimed optimal"
                    ),
                },
            },
        },
    )


def confidence_arms(*, ambiguous_confidence, threshold=CONFIDENCE_GATE_THRESHOLD,
                    ambiguous_decision=None):
    """The two-case A/B the chapter needs, with the ambiguous arm placed where the test wants it."""
    return [
        confidence_record("specific_evidence", "clear", confidence=1.0, threshold=threshold),
        confidence_record(
            "ambiguous_evidence",
            "ambiguous",
            confidence=ambiguous_confidence,
            threshold=threshold,
            decision=ambiguous_decision,
        ),
    ]


class TestTheStoredGateDecisionIsRecomputed:
    """The reported decision is the stored one, and it is checked against the numbers beside it."""

    def test_a_consistent_record_reports_its_stored_decision(self):
        gate = confidence_gate(confidence_record("c", "clear", confidence=0.61))
        assert gate["decision"] == GATE_ACCEPT
        assert gate["cleared"] is True
        assert gate["threshold"] == CONFIDENCE_GATE_THRESHOLD

    @pytest.mark.parametrize(
        "confidence,expected",
        [(1.0, GATE_ACCEPT), (0.61, GATE_ACCEPT), (0.6, GATE_ACCEPT), (0.59, GATE_ESCALATE)],
    )
    def test_the_boundary_is_greater_than_or_equal(self, confidence, expected):
        # Equality clears. This is the experiment's `>=`, and a report that read the boundary the
        # other way would be describing different semantics than the run applied.
        assert confidence_gate(confidence_record("c", "clear", confidence=confidence))[
            "decision"
        ] == expected

    def test_a_record_whose_decision_contradicts_its_numbers_stops_the_build(self):
        # Fail closed: the report declines to choose between the stored decision and the stored
        # numbers rather than silently printing one of them.
        rows = confidence_arms(ambiguous_confidence=0.59, ambiguous_decision=GATE_ACCEPT)
        with pytest.raises(ValueError, match="recomputes to"):
            build_final_report(rows)

    def test_a_record_with_no_gate_is_not_an_error(self):
        assert confidence_gate(record(CONFIDENCE, "c", answers={}, notes={})) is None


class TestTheConfidenceGateDirectionIsRead:
    """The chapter's gate sentence has to move with the gate, in both directions."""

    def outcome(self, rows):
        return line_with(build_final_report(rows), GATE_LINE)

    def test_an_ambiguous_case_above_the_threshold_is_reported_as_cleared(self):
        line = self.outcome(confidence_arms(ambiguous_confidence=0.61))
        assert "accepted and cleared on every one" in line
        assert "did not clear" not in line

    def test_an_ambiguous_case_below_the_threshold_is_reported_as_not_cleared(self):
        line = self.outcome(confidence_arms(ambiguous_confidence=0.59))
        assert "escalated without clearing on ambiguous" in line
        assert "accepted and cleared on every" not in line

    def test_an_ambiguous_case_on_the_threshold_is_reported_as_cleared(self):
        line = self.outcome(confidence_arms(ambiguous_confidence=CONFIDENCE_GATE_THRESHOLD))
        assert "accepted and cleared on every one" in line

    def test_both_cases_refused_is_not_reported_as_any_of_them_clearing(self):
        rows = [
            confidence_record("specific_evidence", "clear", confidence=0.5),
            confidence_record("ambiguous_evidence", "ambiguous", confidence=0.5),
        ]
        line = self.outcome(rows)
        assert "escalated on every one" in line
        assert "none cleared" in line

    def test_the_sentence_follows_the_records_and_not_the_other_way_round(self):
        # The whole point: the same input shape, one number moved, opposite conclusions.
        accepted = build_final_report(confidence_arms(ambiguous_confidence=0.61))
        refused = build_final_report(confidence_arms(ambiguous_confidence=0.59))
        assert accepted != refused
        assert "accepted and cleared on every one" in accepted
        assert "escalated without clearing on ambiguous" in refused

    def test_the_threshold_reported_is_the_one_the_records_were_gated_on(self):
        assert "`confidence >= 0.6`" in build_final_report(confidence_arms(ambiguous_confidence=0.61))


class TestTheInstructionConclusionIsRead:
    """`07_instruction_precision` said the wording "materially changed" the judgment regardless."""

    def instruction_arms(self, vague, explicit):
        return [
            record(
                INSTRUCTION,
                "vague_boundary",
                notes={"boundary": "vague"},
                answers={"blocked": {"type": "noul", "noul": vague}},
            ),
            record(
                INSTRUCTION,
                "explicit_boundary",
                notes={"boundary": "explicit"},
                answers={"blocked": {"type": "noul", "noul": explicit}},
            ),
        ]

    def test_a_moved_judgment_is_reported_as_moved(self):
        text = build_final_report(self.instruction_arms(0.75, 0.2))
        assert "materially changed the observed judgment" in text

    def test_an_unmoved_judgment_is_not_reported_as_having_moved(self):
        text = build_final_report(self.instruction_arms(0.5, 0.5))
        assert "materially changed the observed judgment" not in text
        assert "left the observed judgment unchanged" in text

    def test_the_sentence_follows_the_records_and_not_the_other_way_round(self):
        moved = build_final_report(self.instruction_arms(0.75, 0.2))
        still = build_final_report(self.instruction_arms(0.5, 0.5))
        assert "materially changed the observed judgment" in moved
        assert "materially changed the observed judgment" not in still


class TestTheBatchingSpreadIsComputed:
    """The spread-versus-difference sentence asserted a comparison the generator never made."""

    def batching_arms(self, batched_latencies, separate_latencies):
        rows = [
            record(PARALLEL, f"b{i}", notes={"arm": "batched", "cycle": i + 1}, latency_ms=value)
            for i, value in enumerate(batched_latencies)
        ]
        rows += [
            record(PARALLEL, f"s{i}", notes={"arm": "separate", "cycle": 1}, latency_ms=value)
            for i, value in enumerate(separate_latencies)
        ]
        return rows

    def spread_line(self, rows):
        return line_with(build_final_report(rows), "were spread by")

    def test_a_dominant_within_arm_spread_is_reported_as_larger(self):
        line = self.spread_line(self.batching_arms([3204.053, 611.128], [580.0, 580.0]))
        assert "**2592.925 ms**" in line
        assert "the within-arm spread is larger than" in line

    def test_a_spread_smaller_than_the_difference_is_reported_as_such(self):
        # Batched observations almost identical, arms far apart: the opposite reading.
        line = self.spread_line(self.batching_arms([600.0, 601.0], [1200.0, 1200.0]))
        assert "the within-arm spread is not larger than" in line

    def test_the_numbers_are_the_records_own(self):
        line = self.spread_line(self.batching_arms([900.0, 300.0], [100.0]))
        assert "**600 ms**" in line
        assert "**500 ms**" in line

    def test_the_latency_boundary_is_stated_even_when_nothing_can_be_compared(self):
        # One arm only: no comparison is available, and the limit is still stated rather than the
        # sentence vanishing along with the arm it needed.
        text = build_final_report([record(PARALLEL, "b", notes={"arm": "batched"})])
        assert "never as a speedup" in text
        assert "were spread by" not in text


class TestTheFanoutDirectionConsistencyIsRead:
    """The chapter said the pairs disagreed on latency direction whatever the pairs did."""

    def pair(self, name, fanout_ms, staged_ms):
        return [
            record(FANOUT, f"{name}_fanout", notes={"pair": name, "strategy": "fanout"},
                   latency_ms=fanout_ms),
            record(FANOUT, f"{name}_staged", notes={"pair": name, "strategy": "staged", "stage": 1},
                   latency_ms=staged_ms),
        ]

    def direction_line(self, rows):
        return line_with(build_final_report(rows), "latency direction per pair")

    def test_pairs_that_disagree_are_reported_as_inconsistent(self):
        rows = self.pair("A", 2400, 560) + self.pair("B", 550, 630)
        assert "inconsistent across pairs" in self.direction_line(rows)

    def test_pairs_that_agree_are_not_reported_as_inconsistent(self):
        rows = self.pair("A", 2400, 560) + self.pair("B", 2400, 560)
        line = self.direction_line(rows)
        assert "inconsistent across pairs" not in line
        assert "consistent across pairs" in line

    def test_the_sentence_follows_the_records_and_not_the_other_way_round(self):
        disagree = build_final_report(self.pair("A", 2400, 560) + self.pair("B", 550, 630))
        agree = build_final_report(self.pair("A", 2400, 560) + self.pair("B", 2400, 560))
        assert "inconsistent across pairs" in disagree
        assert "inconsistent across pairs" not in agree


class TestTheCompositeSuperlativeIsChecked:
    """`06_composite_scoring` called one dimension's confidence the run's lowest without looking."""

    LEGEND = {"0": "none", "1": "weak", "2": "adequate", "3": "strong"}

    def composite_record(self, case_id, scenario_class, scores, confidences):
        return record(
            COMPOSITE,
            case_id,
            notes={"scenario_class": scenario_class},
            answers={
                dimension: {
                    "type": "score",
                    "score": scores[dimension],
                    "confidence": confidences[dimension],
                    "legend": self.LEGEND,
                    "probabilities": {"3": 1.0},
                }
                for dimension in COMPOSITE_DIMENSIONS
            },
        )

    def scenario(self, *, lowest_elsewhere=False):
        """`low_risk`'s largest contribution is `evidence_quality`, at confidence 0.24."""
        low = self.composite_record(
            "low_risk",
            "low_risk",
            {"evidence_quality": 0.0, "numerical_stability": 3.0, "reproducibility": 3.0,
             "failure_severity": 0.0},
            {"evidence_quality": 0.24, "numerical_stability": 0.9, "reproducibility": 0.9,
             "failure_severity": 0.05 if lowest_elsewhere else 0.9},
        )
        others = [
            self.composite_record(
                case_id, scenario_class, dict.fromkeys(COMPOSITE_DIMENSIONS, 1.5),
                dict.fromkeys(COMPOSITE_DIMENSIONS, 0.9),
            )
            for case_id, scenario_class in (("mixed", "mixed"), ("high_risk", "high_risk"))
        ]
        return [low, *others]

    def contribution_line(self, rows):
        return line_with(build_final_report(rows), "largest single contribution")

    def test_it_keeps_the_superlative_when_the_run_agrees(self):
        assert "the lowest confidence recorded anywhere" in self.contribution_line(self.scenario())

    def test_it_drops_the_superlative_when_a_lower_confidence_exists_elsewhere(self):
        line = self.contribution_line(self.scenario(lowest_elsewhere=True))
        assert "the lowest confidence recorded anywhere" not in line
        assert "confidence **0.24**" in line


class TestTheRoutingMarkersAreChecked:
    """Two routing sentences asserted realised behaviour without consulting the computed markers."""

    def test_a_fail_closed_run_carries_the_marker(self):
        text = build_final_report(routing_records(suppress_everything=True))
        assert f"`{FAIL_CLOSED_SUPPRESSION_REALIZED}`" in text
        assert "were withheld and no handler ran for any of them" in text

    def test_the_marker_is_never_asserted_without_its_condition(self):
        # Nothing withheld means the marker cannot be carried, and the report must say so rather
        # than keep the sentence about suppression that did not happen.
        text = build_final_report(routing_records(suppress_everything=False))
        assert "either no route was suppressed, or a suppressed route reached a handler" in text
        assert "were withheld and no handler ran for any of them" not in text

    def test_the_sentence_follows_the_records_and_not_the_other_way_round(self):
        suppressed = build_final_report(routing_records(suppress_everything=True))
        executed = build_final_report(routing_records(suppress_everything=False))
        assert "were withheld and no handler ran for any of them" in suppressed
        assert "were withheld and no handler ran for any of them" not in executed

    def test_the_architectural_conclusion_does_not_outrun_the_match_count(self):
        # The canonical shape: every resolved case matched, so the universal is earned.
        rows = routing_records(suppress_everything=True)
        assert "produced the intended function and argument in every resolved case" in (
            build_final_report(rows)
        )

    def test_the_conclusion_reports_counts_when_a_case_did_not_match(self):
        rows = routing_records(suppress_everything=True)
        # Move one case's frozen expectation off the label the record actually answered, so the
        # case still resolves but no longer matches. The answer itself is left alone.
        rows[0]["notes"]["expected_function"] = "compare_runs"
        text = build_final_report(rows)
        assert "produced the intended function and argument in every resolved case" not in text
        assert "produced the intended function in 1 of 2 resolved case(s)" in text


# --------------------------------------------------------------------------------------
# The claim-label contract, enforced over the whole document
# --------------------------------------------------------------------------------------
#
# The header promises that every assertion below carries exactly one label. These patterns are what
# "an assertion" means here: a prose line that is not a claim bullet, not a status marker, and not
# a structural line. The framing allowlist is deliberately short and deliberately exact -- a new
# unlabelled paragraph should fail this check rather than quietly join the list, and anything added
# to it has to be a line that asserts nothing about the log, the bench, or the model.

CLAIM_BULLET = re.compile(
    r"^- \*\*(" + "|".join(re.escape(kind) for kind in CLAIM_KINDS) + r")\*\* — \S"
)
STATUS_MARKER = re.compile(r"^\*\*[A-Z][A-Z0-9_]*\*\*$")
STRUCTURAL_LINE = re.compile(r"^(#|\||>|```|---$)")

FRAMING_LINES: tuple[re.Pattern[str], ...] = (
    # The lead-in to the label table. It introduces the taxonomy; it states no result.
    re.compile(r"^\*\*Claim labels\.\*\* Every assertion below carries exactly one:$"),
    # Provenance: which log this was built from, and how many records it had.
    re.compile(r"^Generated from \d+ canonical record\(s\), \S+ to \S+\.$"),
    re.compile(r"^Derived from `results/usage\.jsonl`, which remains the canonical record\.$"),
    # The footer's marker list. The markers are the project's status vocabulary, and each one is
    # explained by a labelled claim in the chapter that raises it.
    re.compile(r"^`[A-Z][A-Z0-9_]*`(?: · `[A-Z][A-Z0-9_]*`)+$"),
)


def unlabelled_prose(text: str) -> list[str]:
    """Prose lines in a generated report that assert something without carrying a claim label."""
    found: list[str] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        if STRUCTURAL_LINE.match(stripped) or CLAIM_BULLET.match(stripped):
            continue
        if STATUS_MARKER.match(stripped) or any(p.match(stripped) for p in FRAMING_LINES):
            continue
        found.append(f"line {number}: {stripped}")
    return found


class TestTheClaimLabelContractHolds:
    """The header says every assertion carries exactly one label; this is where that is checked.

    A synthesis paragraph that is not a claim bullet is exactly how the unlabelled findings of the
    previous round were written -- `**Core local finding.**` and `**Architectural conclusion.**`
    each asserted a direction the generator had not computed, on a line that carried no label. The
    contract is therefore asserted over the generated document rather than chapter by chapter.
    """

    def assert_contract(self, text: str) -> None:
        assert unlabelled_prose(text) == []

    def test_the_check_catches_an_unlabelled_finding(self):
        # A guard on the guard: an allowlist that swallowed everything would pass every other test
        # here while enforcing nothing.
        assert unlabelled_prose("**Core local finding.** Batching reduced input usage.")
        assert unlabelled_prose(f"- **{LOCAL_MEASUREMENT}** — batching reduced input usage.") == []
        assert unlabelled_prose("**CORE_CAPABILITY_EXPLORATION_CLOSED**") == []

    def test_the_canonical_report_carries_no_unlabelled_prose(self):
        if not canonical_path().exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        self.assert_contract(build_final_report(list(read_records(canonical_path()))))

    def test_a_run_where_a_handler_executed_carries_no_unlabelled_prose(self):
        self.assert_contract(build_final_report(routing_records(suppress_everything=False)))

    def test_a_log_with_no_backlog_left_carries_no_unlabelled_prose(self):
        # The empty-backlog branch has prose of its own, and it is a claim like any other.
        self.assert_contract(
            build_final_report([record(name, "one_case") for name in experiment_names()])
        )

    def test_a_single_record_report_carries_no_unlabelled_prose(self):
        self.assert_contract(build_final_report([record("01_primitives", "a")]))

    def test_the_unlabelled_findings_are_gone(self):
        text = build_final_report(routing_records(suppress_everything=True))
        for phrase in ("**Core local finding.**", "**Architectural conclusion.**"):
            assert phrase not in text


class TestTheCredentialSourceIsNotReconstructed:
    """No record carries a credential source, so the report cannot say which one answered."""

    def report(self):
        return build_final_report([record("01_primitives", "a")])

    def test_the_source_is_stated_as_a_limitation(self):
        line = line_with(self.report(), "supplied the key for a given historical invocation")
        assert line.startswith(f"- **{LIMITATION}** —")

    def test_no_line_claims_which_source_answered_a_run(self):
        text = self.report()
        assert "resolved its credential as" not in text
        assert "source=local-secret-file" not in text
        assert "supplied the key in that invocation" not in text

    def test_the_design_facts_are_kept(self):
        # Removing an unsupported measurement must not remove the architecture around it.
        text = self.report()
        assert "the credential has exactly two sources" in text
        assert "stops the run before a request is sent" in text
        assert "TYPESAFE_API_KEY (environment)" in text
        assert ".secrets/typesafe.env" in text

    def test_no_artifact_is_pinned_to_a_revision_it_never_read(self):
        # The line here used to assert that the repository had no commit history, which the
        # generator cannot know and which stopped being true.
        text = self.report()
        assert "no commit history" not in text
        line = line_with(text, "nothing in this report is pinned to a revision")
        assert line.startswith(f"- **{LIMITATION}** —")


class TestTheRoutingDenominatorsAreCorrect:
    """The classification line printed a matched count where a denominator belonged."""

    def partial_function(self):
        rows = routing_records(suppress_everything=True)
        # Move one case's frozen expectation off the label the record actually answered, so the
        # case still resolves but no longer matches. The answer itself is left alone.
        rows[0]["notes"]["expected_function"] = "compare_runs"
        return rows

    def partial_argument(self):
        rows = routing_records(suppress_everything=True)
        rows[0]["notes"]["expected_argument"] = "seed"
        return rows

    def classifications(self, rows):
        return line_with(build_final_report(rows), "**classifications.**")

    def test_a_partial_function_match_names_both_counts(self):
        text = self.classifications(self.partial_function())
        assert "`FUNCTION_TARGET_NOT_REALIZED` — 1 of 2 case(s)" in text
        assert "`FUNCTION_TARGET_REALIZED`" not in text
        # The numerator was standing in for the denominator: "all 1 case(s)" on a run of two.
        assert "all 1 case(s)" not in text

    def test_a_partial_argument_match_names_both_counts(self):
        text = self.classifications(self.partial_argument())
        assert "`ARGUMENT_TARGET_NOT_REALIZED` — 1 of 2 resolved case(s)" in text
        assert "all 1 resolved case(s)" not in text

    def test_three_matched_of_four_resolved(self):
        # The denominator defect in miniature: four calls, one route that never resolved, and all
        # three that did resolve matching. The old line printed the numerator where the denominator
        # belonged, so a partial run read as a whole one.
        rows = [routing_record(row[0], confidence=0.9, review=0.9) for row in ROUTING_EXPECTED]
        rows[0]["answers"][ROUTING_FUNCTION_QUESTION]["choice"] = "inspect_residual"
        text = self.classifications(rows)
        assert "`FUNCTION_TARGET_NOT_REALIZED` — 3 of 4 case(s)" in text
        assert "`ARGUMENT_TARGET_REALIZED` — all 3 resolved case(s)" in text
        assert "all 3 case(s)" not in text
        assert "all 4 resolved case(s)" not in text

    def test_a_full_match_still_reads_as_realized(self):
        text = self.classifications(routing_records(suppress_everything=True))
        assert (
            "`FUNCTION_TARGET_REALIZED` — all 2 case(s) returned the pre-frozen expected function."
            in text
        )
        assert "`ARGUMENT_TARGET_REALIZED` — all 2 resolved case(s)" in text

    def test_the_line_follows_the_records_and_not_the_other_way_round(self):
        full = self.classifications(routing_records(suppress_everything=True))
        partial = self.classifications(self.partial_function())
        assert full != partial


class TestTheComparisonWordingFollowsTheNumbers:
    """Two helpers choose their direction word from the sign rather than from the sentence."""

    def test_the_difference_phrase_takes_its_direction_from_the_sign(self):
        assert "2664 fewer" in _difference_phrase(816, 3480, "input tokens")
        assert "2664 more" in _difference_phrase(3480, 816, "input tokens")
        assert "the same number of" in _difference_phrase(100, 100, "input tokens")

    def test_the_saving_phrase_does_not_call_an_increase_a_saving(self):
        assert "a saving of **76.55%**" in _saving_phrase(3480, 816, "separate arm's input")
        increased = _saving_phrase(816, 3480, "separate arm's input")
        assert "a saving" not in increased
        assert "an increase of" in increased
        assert "no change against" in _saving_phrase(500, 500, "separate arm's input")

    def batching(self, *, batched_input, separate_input):
        return [
            record(PARALLEL, "batched", input_tokens=batched_input, output_tokens=20,
                   notes={"arm": "batched", "cycle": 1},
                   answers={"q": {"type": "noul", "noul": 0.5}}),
            record(PARALLEL, "separate", input_tokens=separate_input, output_tokens=20,
                   notes={"arm": "separate", "cycle": 1},
                   answers={"q": {"type": "noul", "noul": 0.5}}),
        ]

    def finding(self, rows):
        return line_with(build_final_report(rows), "core local finding")

    def test_the_batching_finding_is_a_labelled_claim(self):
        assert CLAIM_BULLET.match(self.finding(self.batching(batched_input=100, separate_input=250)))

    def test_the_batching_finding_follows_the_arms(self):
        # The sentence named one direction on any log at all: "batching substantially reduced
        # repeated-state input usage". It is now read off the two arms.
        fewer = self.finding(self.batching(batched_input=100, separate_input=250))
        assert "150 fewer" in fewer
        more = self.finding(self.batching(batched_input=250, separate_input=100))
        assert "150 more" in more
        assert "fewer" not in more

    def fanout(self, *, fanout_input, staged_input, fanout_output=10, staged_output=10):
        return [
            record(FANOUT, "A_fanout", input_tokens=fanout_input, output_tokens=fanout_output,
                   notes={"pair": "A", "strategy": "fanout"},
                   answers={"q": {"type": "noul", "noul": 0.5}}),
            record(FANOUT, "A_staged", input_tokens=staged_input, output_tokens=staged_output,
                   notes={"pair": "A", "strategy": "staged", "stage": 1},
                   answers={"q": {"type": "noul", "noul": 0.5}}),
        ]

    def test_the_fanout_finding_follows_the_arms(self):
        fewer = self.finding(self.fanout(fanout_input=100, staged_input=250))
        assert "150 fewer" in fewer
        more = self.finding(self.fanout(fanout_input=250, staged_input=100))
        assert "150 more" in more
        assert "fewer" not in more

    def test_the_fanout_output_line_follows_the_arms(self):
        # "output tokens ran the other way" was fixed prose, and the number beside it could have
        # come out negative on a log where fan-out spent less.
        text = build_final_report(
            self.fanout(fanout_input=100, staged_input=250, fanout_output=5, staged_output=40)
        )
        line = line_with(text, "output tokens moved separately")
        assert "35 fewer" in line

    def test_the_fanout_input_saving_is_not_called_a_saving_when_it_is_an_increase(self):
        text = build_final_report(self.fanout(fanout_input=250, staged_input=100))
        line = line_with(text, "pooled input ratio")
        assert "a saving" not in line
        assert "an increase of" in line
