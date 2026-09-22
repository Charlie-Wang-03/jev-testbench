"""The capability snapshot is a derived view of the log. Offline, and driven by synthetic records.

The point of these tests is that the snapshot cannot contain a number that is not in the records it
was built from. A derived artifact that drifts from its source is worse than no artifact.
"""

import json

import pytest

from jev_lab.recorder import UsageRecorder, read_records
from jev_lab.snapshot import (
    ADDRESSING,
    CONFIDENCE,
    INSTRUCTION,
    build_snapshot,
    write_snapshot,
)


def record(experiment, case_id, *, input_tokens=100, output_tokens=10, answers=None, notes=None,
           state_utf8_bytes=80, latency_ms=600.0, timestamp="2026-01-01T00:00:00Z",
           is_first=False, run_index=1):
    """A minimal record shaped like a real `usage.jsonl` line."""
    return {
        "run_id": "run000000000",
        "experiment": experiment,
        "case_id": case_id,
        "model_requested": "jev-latest",
        "question_count": len(answers or {}),
        "question_types": sorted({answer["type"] for answer in (answers or {}).values()}),
        "state_chars": state_utf8_bytes,
        "state_utf8_bytes": state_utf8_bytes,
        "timestamp_utc": timestamp,
        "model_resolved": "jev-1.13.0",
        "request_id": "req-x",
        "latency_ms": latency_ms,
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
        "schema_version": 2,
        "answers": answers or {},
        "notes": notes or {},
    }


CHOICE = lambda label, confidence: {"type": "choice", "choice": label, "confidence": confidence}
NOUL = lambda value: {"type": "noul", "noul": value}
SCORE = lambda value, confidence: {"type": "score", "score": value, "confidence": confidence}


def line_with(text, needle):
    """The one line containing `needle`. Fails loudly if the snapshot says it twice or not at all."""
    matches = [line for line in text.splitlines() if needle in line]
    assert len(matches) == 1, f"expected one line containing {needle!r}, found {len(matches)}"
    return matches[0]


def addressing_records():
    return [
        record(ADDRESSING, "structured_addressing", input_tokens=493,
               answers={"asks_for_refund": NOUL(0.81), "department": CHOICE("billing", 1.0)},
               state_utf8_bytes=193, is_first=True),
        record(ADDRESSING, "prose_addressing", input_tokens=452,
               answers={"asks_for_refund": NOUL(0.89), "department": CHOICE("billing", 1.0)},
               state_utf8_bytes=166, run_index=2),
    ]


def confidence_records():
    def derived(intent, intent_confidence, expected, matched, score, score_confidence, decision):
        return {
            "derived": {
                "intent": intent,
                "intent_confidence": intent_confidence,
                "expected": expected,
                "matches_expected": matched,
                "specificity_score": score,
                "specificity_confidence": score_confidence,
                "gate": {"decision": decision, "threshold": 0.6, "threshold_basis": "demo threshold"},
            }
        }

    return [
        record(CONFIDENCE, "specific_evidence", input_tokens=457,
               answers={"intent": CHOICE("release_transfer", 1.0), "specificity": SCORE(2.0, 1.0)},
               notes=derived("release_transfer", 1.0, "release_transfer", True, 2.0, 1.0, "accept"),
               is_first=True),
        record(CONFIDENCE, "ambiguous_evidence", input_tokens=462,
               answers={"intent": CHOICE("other", 0.61), "specificity": SCORE(0.06, 0.91)},
               notes=derived("other", 0.61, None, None, 0.06, 0.91, "accept"),
               run_index=2),
    ]


def instruction_records():
    return [
        record(INSTRUCTION, "vague_boundary", input_tokens=318,
               answers={"blocked": NOUL(0.75)}, state_utf8_bytes=82, is_first=True),
        record(INSTRUCTION, "explicit_boundary", input_tokens=358,
               answers={"blocked": NOUL(0.20)}, state_utf8_bytes=82, run_index=2),
    ]


class TestSnapshotShape:
    def test_an_empty_log_says_so_instead_of_inventing_a_table(self):
        assert "No records in the log yet" in build_snapshot([])

    def test_it_labels_itself_derived_rather_than_canonical(self):
        text = build_snapshot(addressing_records())
        assert "derived artifact, not a measurement" in text
        assert "results/usage.jsonl" in text

    def test_it_says_the_scope_is_narrow(self):
        text = build_snapshot(addressing_records())
        assert "not a benchmark" in text


class TestNumbersComeFromTheRecords:
    """Every figure is recomputed. If the records change, the text changes with them."""

    def test_totals_are_summed_from_the_records_not_written_down(self):
        records = addressing_records() + confidence_records() + instruction_records()
        text = build_snapshot(records)
        expected_input = sum(record["input_tokens"] for record in records)
        expected_output = sum(record["output_tokens"] for record in records)
        assert f"| {len(records)} | {expected_input} | {expected_output} " in text

    def test_the_total_is_not_rounded_away_to_zero(self):
        """A sub-cent total must not render as a flat zero in the table."""
        text = build_snapshot(addressing_records())
        assert "| $0.00 |" not in text
        assert "| $0.00003969 |" in text

    def test_changing_a_record_changes_the_snapshot(self):
        records = addressing_records()
        before = build_snapshot(records)
        records[0]["input_tokens"] = 999
        assert "999" in build_snapshot(records)
        assert "493" not in build_snapshot(records)
        assert before != build_snapshot(records)


class TestAddressingSection:
    def test_it_reports_both_token_counts_and_both_nouls(self):
        text = build_snapshot(addressing_records())
        assert "493" in text and "452" in text
        assert "0.81" in text and "0.89" in text

    def test_it_names_the_length_confound(self):
        text = build_snapshot(addressing_records())
        assert "confounded by length" in text

    def test_the_section_is_absent_when_its_records_are_absent(self):
        assert f"## `{ADDRESSING}`" not in build_snapshot(instruction_records())


class TestConfidenceSection:
    def test_it_reports_the_gate_decision_that_actually_happened(self):
        text = build_snapshot(confidence_records())
        assert "**accept**" in text
        assert "0.6" in text

    def test_it_states_that_a_passing_gate_is_not_correctness(self):
        text = build_snapshot(confidence_records())
        assert "not evidence that the underlying answer was right" in text

    def test_it_warns_against_reading_confidence_as_the_property_being_judged(self):
        text = build_snapshot(confidence_records())
        assert "does not measure the property being judged" in text

    def test_a_case_without_an_expected_label_is_not_given_one(self):
        text = build_snapshot(confidence_records())
        assert "no single label is correct for this case" in text


def gate_records(*, ambiguous_confidence, ambiguous_decision=None, threshold=0.6):
    """The `04_confidence` pair with the ambiguous arm placed wherever a test wants it.

    `ambiguous_decision` is overridable so a record can be built that contradicts its own numbers.
    Nothing else here does that, because the gate's whole point is that the stored decision and the
    stored numbers agree.
    """
    def one(case_id, intent, confidence, decision):
        return record(
            CONFIDENCE,
            case_id,
            answers={"intent": CHOICE(intent, confidence), "specificity": SCORE(1.0, 0.9)},
            notes={
                "derived": {
                    "intent": intent,
                    "intent_confidence": confidence,
                    "expected": None,
                    "matches_expected": None,
                    "specificity_score": 1.0,
                    "specificity_confidence": 0.9,
                    "gate": {
                        "decision": decision,
                        "threshold": threshold,
                        "threshold_basis": "demo threshold",
                    },
                }
            },
        )

    return [
        one("specific_evidence", "release_transfer", 1.0, "accept"),
        one(
            "ambiguous_evidence",
            "other",
            ambiguous_confidence,
            ambiguous_decision
            if ambiguous_decision is not None
            else ("accept" if ambiguous_confidence >= threshold else "escalate"),
        ),
    ]


GATE_READING = "**Reading the gate.**"


class TestTheGateReadingFollowsTheGateDecision:
    """The gate paragraph described one direction on every log, whatever the gate had done.

    It read "the ambiguous case lands just above the threshold, so this gate accepts it", which was
    true of the frozen log and would have stayed on the page on a log where that case was refused.
    Each test below moves the ambiguous record and holds the sentence to the move, in both
    directions, so a generator that ignored the decision would fail half of every pair.
    """

    def reading(self, rows):
        return line_with(build_snapshot(rows), GATE_READING)

    def test_an_accepted_ambiguous_case_is_reported_as_accepted(self):
        text = self.reading(gate_records(ambiguous_confidence=0.61))
        assert "ambiguous_evidence" in text
        assert "accepted" in text
        assert "ambiguous_evidence did not clear" not in text

    def test_an_escalated_ambiguous_case_is_not_reported_as_accepted(self):
        text = self.reading(gate_records(ambiguous_confidence=0.59))
        assert "ambiguous_evidence did not clear and was escalated" in text

    def test_the_confidence_equal_to_the_threshold_clears(self):
        # `04_confidence` gates on `>=`, so equality accepts. A snapshot reading the boundary the
        # other way would describe different semantics than the run applied.
        text = self.reading(gate_records(ambiguous_confidence=0.6))
        assert "accepted" in text
        assert "ambiguous_evidence did not clear" not in text

    def test_the_sentence_follows_the_records_and_not_the_other_way_round(self):
        accepted = self.reading(gate_records(ambiguous_confidence=0.61))
        escalated = self.reading(gate_records(ambiguous_confidence=0.59))
        assert accepted != escalated

    def test_changing_a_record_changes_the_snapshot(self):
        before = build_snapshot(gate_records(ambiguous_confidence=0.61))
        after = build_snapshot(gate_records(ambiguous_confidence=0.59))
        assert before != after

    def test_both_cases_refused_is_not_reported_as_any_of_them_clearing(self):
        rows = gate_records(ambiguous_confidence=0.59)
        # Move the specific arm below the threshold too, so the gate refused both.
        rows[0]["answers"]["intent"]["confidence"] = 0.5
        rows[0]["notes"]["derived"]["intent_confidence"] = 0.5
        rows[0]["notes"]["derived"]["gate"]["decision"] = "escalate"
        text = self.reading(rows)
        assert "no case cleared it (specific_evidence, ambiguous_evidence)" in text
        assert "accepted" not in text

    def test_a_record_whose_decision_contradicts_its_numbers_stops_the_build(self):
        # Fail closed: the snapshot declines to choose between the stored decision and the stored
        # numbers rather than printing one of them as if it had been checked.
        rows = gate_records(ambiguous_confidence=0.59, ambiguous_decision="accept")
        with pytest.raises(ValueError, match="recomputes to"):
            build_snapshot(rows)

    def test_a_stored_decision_with_nothing_to_check_it_against_stops_the_build(self):
        rows = gate_records(ambiguous_confidence=0.61)
        rows[1]["answers"] = {}
        with pytest.raises(ValueError, match="no Choice confidence"):
            build_snapshot(rows)

    def test_a_case_with_no_gate_at_all_is_not_an_error(self):
        rows = gate_records(ambiguous_confidence=0.61)
        for row in rows:
            row["notes"] = {}
        text = build_snapshot(rows)
        assert "gate: not recorded for this case." in text
        assert "no case carries a checkable gate" in text


class TestInstructionSection:
    def test_it_reports_the_byte_identical_state(self):
        text = build_snapshot(instruction_records())
        assert "byte-identical across the two arms: **True**" in text

    def test_it_refuses_to_grade_the_two_nouls(self):
        text = build_snapshot(instruction_records())
        assert "No correctness claim" in text
        assert "neither arm is reported as the right answer" in text

    def test_it_explains_the_token_gap_as_wording_not_state(self):
        text = build_snapshot(instruction_records())
        assert "the higher count is the wording, not a different state" in text


class TestLatencyIsNotAttributedToAnArm:
    @pytest.mark.parametrize("builder", [addressing_records, confidence_records, instruction_records])
    def test_no_ab_section_reports_a_latency(self, builder):
        text = build_snapshot(builder())
        assert " ms" not in text.split("## ")[-1]

    def test_the_ab_sections_say_why_latency_is_withheld(self):
        for builder in (confidence_records, instruction_records):
            text = build_snapshot(builder())
            assert "Arm identity is fully confounded with request position" in text


class TestSnapshotIsWritten:
    def test_it_is_written_beside_the_log_and_only_from_real_records(self, tmp_path):
        assert write_snapshot(tmp_path) is None
        recorder = UsageRecorder(tmp_path)
        with recorder.begin(
            experiment="01_primitives",
            case_id="only_case",
            model_requested="jev-latest",
            questions={"q": {"type": "noul", "instructions": "?"}},
            state="some state",
            case_sequence_index=0,
        ):
            pass
        target = write_snapshot(tmp_path)
        assert target is not None and target.is_file()
        text = target.read_text(encoding="utf-8")
        assert "only_case" in text
        assert "1 canonical record" in text

    def test_generating_it_does_not_touch_the_log(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        with recorder.begin(
            experiment="01_primitives",
            case_id="only_case",
            model_requested="jev-latest",
            questions={"q": {"type": "noul", "instructions": "?"}},
            state="some state",
        ):
            pass
        before = recorder.path.read_bytes()
        write_snapshot(tmp_path)
        assert recorder.path.read_bytes() == before

    def test_an_experiment_without_hand_written_prose_still_appears(self, tmp_path):
        """No experiment should be silently dropped from the snapshot just because it is new."""
        path = tmp_path / "usage.jsonl"
        path.write_text(
            json.dumps(record("99_brand_new", "a_case", answers={"q": NOUL(0.5)})) + "\n",
            encoding="utf-8",
        )
        text = build_snapshot(list(read_records(path)))
        assert "## `99_brand_new`" in text
        assert "a_case" in text


PARALLEL_QUESTIONS = ["charged_twice", "cannot_log_in", "wants_apple_pay", "is_frustrated", "mentions_order_id"]

# The values the real run produced, so the derived ratios land on the same figures.
BATCH_LATENCY = {1: 3204.053, 2: 611.128}
SEPARATE_LATENCY = [564.107, 589.735, 573.282, 648.729, 541.685]


def parallel_records(*, batch_noul=0.99, separate_noul=0.99, cycles=(1, 2), attempts=True,
                     batch_latency=None):
    """Twelve records shaped like a real `03_parallel_questions` run: two balanced cycles.

    Cycle 1 leads with the batched arm, cycle 2 with the separate arms, which is what the order
    balance looks like in the log.
    """
    batch_latency = batch_latency or BATCH_LATENCY
    records, index = [], 0

    def add(case_id, answers, notes, latency_ms, *, first=False):
        nonlocal index
        record_ = record("03_parallel_questions", case_id, input_tokens=0, answers=answers,
                         notes=notes, latency_ms=latency_ms, is_first=first, run_index=index + 1)
        record_["case_sequence_index"] = index
        index += 1
        if attempts:
            record_["transport_attempt_count"] = 1
            record_["transport_retry_count_observed"] = 0
            record_["attempt_count_source"] = "httpx_request_event_hook"
            record_["schema_version"] = 3
        records.append(record_)
        return record_

    for cycle in cycles:
        # Cycle 1: batched first. Cycle 2: the five separate calls first, batched last.
        batched_first = cycle % 2 == 1
        batch = {
            "case_id": f"cycle{cycle}_{1 if batched_first else 2}_batched_single_request",
            "answers": {name: NOUL(batch_noul) for name in PARALLEL_QUESTIONS},
            "notes": {"arm": "batched", "cycle": cycle,
                      "position_in_cycle": 1 if batched_first else 2},
            "latency_ms": batch_latency[cycle],
        }
        separate = [
            {
                "case_id": f"cycle{cycle}_{2 if batched_first else 1}_separate_{name}",
                "answers": {name: NOUL(separate_noul)},
                "notes": {"arm": "separate", "cycle": cycle,
                          "position_in_cycle": 2 + offset if batched_first else 1 + offset},
                "latency_ms": SEPARATE_LATENCY[offset],
            }
            for offset, name in enumerate(PARALLEL_QUESTIONS)
        ]
        ordered = [batch, *separate] if batched_first else [*separate, batch]
        for entry in ordered:
            record_ = add(entry["case_id"], entry["answers"], entry["notes"], entry["latency_ms"],
                          first=(entry is batch and cycle == 1))
            record_["input_tokens"] = 408 if entry is batch else 348
            record_["output_tokens"] = 97 if entry is batch else 22
            record_["total_tokens"] = record_["input_tokens"] + record_["output_tokens"]
            record_["estimated_cost_usd"] = record_["input_tokens"] * 0.042 / 1_000_000
            record_["state_chars"] = record_["state_utf8_bytes"] = 318
    return records


class TestParallelQuestionsSection:
    """The batching section must recompute every figure from the records, never restate one."""

    def test_pooled_input_ratio_is_derived_not_declared(self):
        text = build_snapshot(parallel_records())
        assert "**4.2647x**" in text
        assert "**76.55%**" in text

    def test_the_ratio_follows_the_records_when_they_change(self):
        records = parallel_records()
        assert "**4.2647x**" in build_snapshot(records)
        for record_ in records:
            if record_["notes"]["arm"] == "separate":
                record_["input_tokens"] = 174  # halve it: 870 vs 408 is 2.1324x
                record_["estimated_cost_usd"] = 174 * 0.042 / 1_000_000
        text = build_snapshot(records)
        assert "**4.2647x**" not in text
        assert "**2.1324x**" in text

    def test_it_reports_both_cycles_separately_as_well_as_pooled(self):
        text = build_snapshot(parallel_records())
        assert "cycle 1:" in text and "cycle 2:" in text
        assert "pooled over both arms" in text

    def test_it_states_that_output_tokens_cost_nothing_here(self):
        text = build_snapshot(parallel_records())
        assert "billed at $0" in text

    def test_it_does_not_report_a_speedup_factor(self):
        text = build_snapshot(parallel_records())
        assert "observed latency comparison, not a speedup measurement" in text
        assert "faster" not in text.lower()

    def test_high_batch_spread_is_flagged_with_the_agreed_marker(self):
        text = build_snapshot(parallel_records())
        assert "BATCH_LATENCY_HIGH_VARIANCE_OBSERVED" in text

    def test_the_marker_is_absent_when_the_batch_observations_agree(self):
        text = build_snapshot(parallel_records(batch_latency={1: 600.0, 2: 611.128}))
        assert "BATCH_LATENCY_HIGH_VARIANCE_OBSERVED" not in text


class TestParallelSemantics:
    def test_ten_pairings_are_compared_across_two_cycles(self):
        text = build_snapshot(parallel_records())
        assert "Pairings compared: **10**" in text
        assert "exactly equal: **10/10**" in text

    def test_full_agreement_uses_the_exact_agreed_wording(self):
        text = build_snapshot(parallel_records())
        assert ("Within these two cycles and this one synthetic shared-state case, **no "
                "batch-vs-separate Noul drift was observed.**") in text

    def test_it_refuses_to_generalise_the_agreement(self):
        text = build_snapshot(parallel_records())
        assert "not a general claim that batching never changes Jev's answers" in text

    def test_a_single_divergent_pair_is_reported_not_averaged(self):
        text = build_snapshot(parallel_records(separate_noul=0.95))
        assert "exactly equal: **0/10**" in text
        assert "did **not** agree on every pairing" in text
        assert "no batch-vs-separate Noul drift was observed" not in text


class TestParallelProvenance:
    def test_it_reports_the_attempt_count_as_an_observation_only(self):
        text = build_snapshot(parallel_records())
        assert "**12/12**" in text
        assert "no HTTP retry was locally observed" in text

    def test_a_legacy_row_without_attempts_is_counted_as_not_observed(self):
        records = parallel_records()
        records[3].pop("transport_attempt_count")
        records[3].pop("transport_retry_count_observed")
        text = build_snapshot(records)
        assert "**11/12**" in text

    def test_it_reports_the_shared_state_and_question_count(self):
        text = build_snapshot(parallel_records())
        assert "5 identical Noul questions" in text
        assert "318 utf8 bytes" in text


class TestRepeatabilitySection:
    """`13_repeatability` renders through the derived generator, one run at a time."""

    def _run(self, run_id="runrepeat0000", **overrides):
        return [
            {**record("13_repeatability", f"repeat_{index}", answers={
                "primary_issue": {"type": "choice", "choice": "shipping_delay", "confidence": 0.71,
                                  "probabilities": {"shipping_delay": 0.52, "billing_discrepancy": 0.28}},
                "wants_to_cancel": NOUL(0.37)}, run_index=index, **overrides),
             "run_id": run_id, "case_id": f"repeat_{index}"}
            for index in range(1, 6)
        ]

    def test_the_section_appears_with_its_three_arms(self):
        text = build_snapshot(self._run())
        assert "### Run-to-run stability" in text
        assert "**Choice — `primary_issue`.**" in text
        assert "**Noul — `wants_to_cancel`.**" in text

    def test_it_reports_the_identical_payload_and_the_call_count(self):
        text = build_snapshot(self._run())
        assert "5 call(s) of one byte-identical request" in text

    def test_only_the_latest_run_is_rendered_and_the_rest_are_counted(self):
        text = build_snapshot(self._run("runrepeat0000") + self._run("runrepeat0001"))
        assert "1 earlier run(s) of this experiment are in the log and are not shown here" in text

    def test_it_does_not_become_a_generic_per_case_dump(self):
        """The repeatability records must not also fall through to the catch-all block."""
        text = build_snapshot(self._run())
        assert "### `repeat_2`" not in text


class TestNoCredentialReachesTheSnapshot:
    def test_a_planted_environment_key_never_appears_in_the_derived_view(self, monkeypatch):
        monkeypatch.setenv("TYPESAFE_API_KEY", "planted-marker-never-render-me")
        text = build_snapshot(parallel_records() + addressing_records() + confidence_records())
        assert "planted-marker-never-render-me" not in text


class TestUnpositionedRows:
    """The seven real records were written before the position fields existed."""

    def _legacy(self):
        record_ = record("01_primitives", "old_case", answers={"q": NOUL(0.5)})
        for key in (
            "case_sequence_index",
            "logical_request_index_in_run",
            "client_session_id",
            "is_first_request_in_client_session",
        ):
            del record_[key]
        record_["schema_version"] = 1
        return record_

    def test_a_missing_position_is_stated_not_rendered_as_a_value(self):
        text = build_snapshot([self._legacy()])
        assert "run# None" not in text
        assert "position not recorded (older schema)" in text

    def test_it_declares_how_many_records_lack_a_position(self):
        text = build_snapshot([self._legacy(), self._legacy()])
        assert "2 of 2 record(s) predate the request-position and transport-attempt fields" in text

    def test_it_says_old_records_are_not_rewritten(self):
        assert "Old records are never rewritten to add it." in build_snapshot([self._legacy()])

    def test_the_note_is_absent_when_every_row_has_a_position(self):
        assert "predate the request-position" not in build_snapshot(addressing_records())
