"""P3 offline invariants: the frozen design, and the analyzer's decision rule.

No network. The only P3 entry point that would make a call is `run`, and the tests that touch it
exercise its fail-closed guard, which raises before any credential is resolved.
"""

import inspect

import pytest

from jev_lab import p3_boundary_locus as p3
from jev_lab.experiments import EXPERIMENTS, get_experiment
from jev_lab.recorder import DEFAULT_RESULTS_DIR

# The strings the 07 experiment sent, written out here so the test fails if either side of the
# comparison is edited to match the other.
STATE_07 = "The report export spun for ten minutes and never finished. I gave up and used CSV."
VAGUE_INSTRUCTION_07 = "Is this a serious issue?"
VAGUE_TRUE_07 = "Something went wrong for the user"
VAGUE_FALSE_07 = "Nothing went wrong for the user"
EXPLICIT_INSTRUCTION_07 = (
    "Does the state describe a situation where a primary requested capability could not "
    "complete, and no equivalent within-feature workaround allowed completion?"
)
EXPLICIT_TRUE_07 = (
    "A primary requested capability could not complete, and no equivalent within-feature "
    "workaround allowed completion"
)
EXPLICIT_FALSE_07 = (
    "The capability completed, or an equivalent within-feature workaround allowed completion, "
    "or no failure is described"
)


def _07_questions():
    """The live 07 question objects, so equality is checked against the registry itself."""
    vague_case, explicit_case = get_experiment("07_instruction_precision").cases()
    return vague_case.questions["blocked"], explicit_case.questions["blocked"]


def synthetic_record(arm, repeat, sequence_index, value, status="ok"):
    """One P3 log record with the shape `run` writes."""
    instruction_specificity, criteria_specificity = p3.ARM_SPECIFICITY[arm]
    answers = {} if value is None else {p3.QUESTION_NAME: {"type": "noul", "noul": value}}
    return {
        "status": status,
        "answers": answers,
        "notes": {
            "p3_question": p3.P3_QUESTION,
            "arm": arm,
            "arm_label": p3.ARM_LABELS[arm],
            "repeat": repeat,
            "instruction_specificity": instruction_specificity,
            "criteria_specificity": criteria_specificity,
            "sequence_index": sequence_index,
            "preregistration_id": p3.PREREGISTRATION_ID,
        },
    }


def synthetic_log(values_by_arm, missing=()):
    """A twelve-record log from per-arm value triples, in the frozen order.

    ``missing`` names ``(arm, repeat_index)`` positions that produced no usable value, so a test can
    build the early-stop and failure shapes the analyzer has to survive.
    """
    records = []
    for arm, repeat, sequence_index in p3.frozen_sequence():
        value = values_by_arm[arm][repeat - 1]
        if (arm, repeat) in missing:
            records.append(synthetic_record(arm, repeat, sequence_index, None, status="error"))
        else:
            records.append(synthetic_record(arm, repeat, sequence_index, value))
    return records


# Baseline that reproduces the 07 endpoints, for tests that are not about the endpoints.
ENDPOINTS = {"N": (0.75, 0.75, 0.75), "B": (0.20, 0.20, 0.20)}


class TestFrozenDesign:
    def test_exactly_four_arms(self):
        assert p3.ARMS == ("N", "I", "C", "B")
        assert set(p3.ARM_SPECIFICITY) == set(p3.ARMS)

    def test_every_arm_is_one_cell_of_a_two_by_two(self):
        assert p3.ARM_SPECIFICITY == {
            "N": (p3.VAGUE, p3.VAGUE),
            "I": (p3.EXPLICIT, p3.VAGUE),
            "C": (p3.VAGUE, p3.EXPLICIT),
            "B": (p3.EXPLICIT, p3.EXPLICIT),
        }

    def test_state_is_byte_identical_to_the_07_payload(self):
        assert p3.P3_STATE == STATE_07
        vague_case, explicit_case = get_experiment("07_instruction_precision").cases()
        assert vague_case.state == STATE_07
        assert explicit_case.state == STATE_07

    def test_every_arm_sends_the_same_state(self):
        states = {case.state for case in p3.p3_cases()}
        assert states == {STATE_07}

    def test_frozen_texts_match_the_literal_07_strings(self):
        assert p3.VAGUE_INSTRUCTIONS == VAGUE_INSTRUCTION_07
        assert p3.VAGUE_CRITERIA_TRUE == VAGUE_TRUE_07
        assert p3.VAGUE_CRITERIA_FALSE == VAGUE_FALSE_07
        assert p3.EXPLICIT_INSTRUCTIONS == EXPLICIT_INSTRUCTION_07
        assert p3.EXPLICIT_CRITERIA_TRUE == EXPLICIT_TRUE_07
        assert p3.EXPLICIT_CRITERIA_FALSE == EXPLICIT_FALSE_07

    def test_arm_n_equals_the_07_vague_question_object(self):
        vague, _ = _07_questions()
        assert p3.arm_question("N").model_dump() == vague.model_dump()

    def test_arm_b_equals_the_07_explicit_question_object(self):
        _, explicit = _07_questions()
        assert p3.arm_question("B").model_dump() == explicit.model_dump()

    def test_instruction_only_swaps_the_instruction_and_nothing_else(self):
        vague, explicit = _07_questions()
        question = p3.arm_question("I")
        assert question.instructions == explicit.instructions
        assert question.criteria == vague.criteria
        # Exactly one field moved: the criteria are still the vague ones, object for object.
        assert question.criteria != explicit.criteria

    def test_criteria_only_swaps_the_criteria_and_nothing_else(self):
        vague, explicit = _07_questions()
        question = p3.arm_question("C")
        assert question.instructions == vague.instructions
        assert question.criteria == explicit.criteria
        assert question.instructions != explicit.instructions

    def test_the_four_arms_are_four_distinct_questions(self):
        dumps = [p3.arm_question(arm).model_dump() for arm in p3.ARMS]
        assert all(dump["type"] == "noul" for dump in dumps)
        assert len({repr(dump) for dump in dumps}) == 4

    def test_exactly_twelve_logical_positions_three_per_arm(self):
        sequence = p3.frozen_sequence()
        assert len(sequence) == p3.MAX_LOGICAL_CALLS == 12
        for arm in p3.ARMS:
            repeats = sorted(repeat for existing, repeat, _ in sequence if existing == arm)
            assert repeats == [1, 2, 3]

    def test_sequence_indices_are_a_straight_zero_to_eleven(self):
        assert [index for _, _, index in p3.frozen_sequence()] == list(range(12))

    def test_running_order_is_the_frozen_counterbalanced_order(self):
        assert p3.ROUNDS == (
            ("N", "I", "C", "B"),
            ("B", "C", "I", "N"),
            ("C", "N", "B", "I"),
        )
        assert [arm for arm, _, _ in p3.frozen_sequence()] == [
            "N", "I", "C", "B",
            "B", "C", "I", "N",
            "C", "N", "B", "I",
        ]

    def test_every_arm_occupies_each_position_at_most_once_per_round(self):
        for round_cases in p3.ROUNDS:
            assert sorted(round_cases) == sorted(p3.ARMS)

    def test_cases_carry_their_arm_identity_in_notes(self):
        for case in p3.p3_cases():
            notes = case.notes
            assert notes["p3_question"] == p3.P3_QUESTION
            assert notes["arm"] in p3.ARMS
            assert notes["repeat"] in (1, 2, 3)
            assert notes["preregistration_id"] == p3.PREREGISTRATION_ID
            assert notes["instruction_specificity"] in (p3.VAGUE, p3.EXPLICIT)
            assert notes["criteria_specificity"] in (p3.VAGUE, p3.EXPLICIT)

    def test_case_notes_record_the_specificity_the_arm_actually_sends(self):
        for case in p3.p3_cases():
            arm = case.notes["arm"]
            question = case.questions[p3.QUESTION_NAME]
            expected_instruction = p3.VAGUE if question.instructions == VAGUE_INSTRUCTION_07 else p3.EXPLICIT
            assert case.notes["instruction_specificity"] == expected_instruction
            expected_criteria = p3.VAGUE if question.criteria == {"true": VAGUE_TRUE_07, "false": VAGUE_FALSE_07} else p3.EXPLICIT
            assert case.notes["criteria_specificity"] == expected_criteria
            assert case.notes["arm"] == arm

    def test_p3_is_not_registered_in_the_frozen_registry(self):
        assert p3.EXPERIMENT_NAME not in EXPERIMENTS
        assert len(EXPERIMENTS) == 15

    def test_building_cases_twice_yields_equal_but_independent_objects(self):
        first = p3.p3_cases()
        second = p3.p3_cases()
        assert [c.questions[p3.QUESTION_NAME].model_dump() for c in first] == [
            c.questions[p3.QUESTION_NAME].model_dump() for c in second
        ]
        assert first[0].questions[p3.QUESTION_NAME] is not second[0].questions[p3.QUESTION_NAME]


class TestBudget:
    def test_hard_ceiling_is_twelve(self):
        assert p3.MAX_LOGICAL_CALLS == 12
        assert p3.REPEATS_PER_ARM == 3

    def test_the_experiment_declares_exactly_the_frozen_sequence(self):
        cases = p3.experiment().cases()
        assert len(cases) == p3.MAX_LOGICAL_CALLS
        assert [case.case_id for case in cases] == [
            f"{arm}_r{repeat}" for arm, repeat, _ in p3.frozen_sequence()
        ]

    def test_run_passes_the_ceiling_to_the_shared_runner(self):
        source = inspect.getsource(p3.run)
        assert "max_requests=MAX_LOGICAL_CALLS" in source
        assert "ModelVersionMismatch" in source


class TestDedicatedLogPath:
    def test_log_is_not_the_frozen_root_log(self):
        assert p3.p3_log_path() != DEFAULT_RESULTS_DIR / "usage.jsonl"
        assert p3.p3_log_path().as_posix() == "results/p3_boundary_locus/usage.jsonl"

    def test_results_dir_is_its_own_directory(self):
        assert p3.P3_RESULTS_DIR.as_posix() == "results/p3_boundary_locus"

    def test_run_refuses_a_log_that_already_holds_records(self, tmp_path):
        log = p3.p3_log_path(tmp_path)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("{}\n", encoding="utf-8")
        with pytest.raises(p3.P3LogNotEmpty):
            p3.run(results_dir=tmp_path, echo=lambda *_: None)

    def test_an_absent_log_is_accepted_and_an_empty_one_too(self, tmp_path):
        p3.assert_log_empty(p3.p3_log_path(tmp_path))
        log = p3.p3_log_path(tmp_path)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("", encoding="utf-8")
        p3.assert_log_empty(log)


class TestStatistics:
    def test_median_of_three_is_the_middle_observation(self):
        result = p3.arm_statistics("I", [0.30, 0.10, 0.20])
        assert result.median == 0.20
        assert result.spread == 0.20
        assert result.usable == 3
        assert result.complete

    def test_median_keeps_all_three_raw_values(self):
        result = p3.arm_statistics("C", [0.30, 0.10, 0.20])
        assert set(result.values) == {0.10, 0.20, 0.30}

    def test_spread_is_max_minus_min(self):
        assert p3.arm_statistics("N", [0.74, 0.75, 0.79]).spread == 0.05

    def test_an_arm_without_three_values_has_no_statistic(self):
        result = p3.arm_statistics("B", [0.20, 0.20])
        assert result.median is None
        assert result.spread is None
        assert not result.complete

    def test_arm_statistics_carry_the_frozen_specificity(self):
        result = p3.arm_statistics("I", [0.5, 0.5, 0.5])
        assert result.instruction_specificity == p3.EXPLICIT
        assert result.criteria_specificity == p3.VAGUE


class TestValueExtraction:
    def test_a_successful_noul_answer_is_read(self):
        assert p3.noul_value(synthetic_record("N", 1, 0, 0.75)) == 0.75
        assert p3.noul_value(synthetic_record("B", 1, 0, 0.2)) == 0.2

    def test_a_failed_call_yields_no_value(self):
        assert p3.noul_value(synthetic_record("N", 1, 0, 0.75, status="error")) is None

    def test_a_missing_answer_yields_no_value(self):
        assert p3.noul_value(synthetic_record("N", 1, 0, None)) is None

    def test_a_boolean_is_not_read_as_a_number(self):
        record = synthetic_record("N", 1, 0, 0.75)
        record["answers"][p3.QUESTION_NAME]["noul"] = True
        assert p3.noul_value(record) is None

    def test_values_are_grouped_by_arm_in_run_order(self):
        records = synthetic_log({**ENDPOINTS, "I": (0.1, 0.2, 0.3), "C": (0.4, 0.5, 0.6)})
        grouped = p3.values_by_arm(records)
        assert grouped["I"] == [0.1, 0.2, 0.3]
        assert grouped["B"] == [0.2, 0.2, 0.2]

    def test_run_order_follows_sequence_index_not_file_order(self):
        records = synthetic_log(ENDPOINTS | {"I": (0.1, 0.2, 0.3), "C": (0.4, 0.5, 0.6)})
        shuffled = list(reversed(records))
        assert p3.values_by_arm(shuffled)["I"] == [0.1, 0.2, 0.3]


class TestGoVerdict:
    def test_a_clean_locus_signal_goes(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})
        )
        assert (analysis.go1, analysis.go2, analysis.go3) == (True, True, True)
        assert analysis.moved_arm == "I" and analysis.flat_arm == "C"
        assert analysis.verdict == p3.GO_LOCAL_LOCUS_SIGNAL

    def test_the_symmetric_case_moves_the_other_way(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"C": (0.22, 0.25, 0.27), "I": (0.73, 0.75, 0.77)})
        )
        assert analysis.moved_arm == "C" and analysis.flat_arm == "I"
        assert analysis.verdict == p3.GO_LOCAL_LOCUS_SIGNAL

    def test_go1_threshold_is_inclusive(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.47, 0.475, 0.48), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.arms["I"].median == p3.GO1_MEDIAN_AT_MOST == 0.475
        assert analysis.go1 is True
        assert analysis.verdict == p3.GO_LOCAL_LOCUS_SIGNAL

    def test_a_hair_above_the_go1_threshold_does_not_go(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.48, 0.48, 0.48), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.go1 is False
        assert analysis.verdict != p3.GO_LOCAL_LOCUS_SIGNAL

    def test_go2_band_edges_are_inclusive(self):
        for flat in (0.64, 0.86):
            analysis = p3.analyze(
                synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (flat - 0.01, flat, flat + 0.01)})
            )
            assert analysis.arms["C"].median == flat
            assert analysis.go2 is True

    def test_just_outside_the_go2_band_does_not_go(self):
        for flat in (0.63, 0.87):
            analysis = p3.analyze(
                synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (flat - 0.01, flat, flat + 0.01)})
            )
            assert analysis.go2 is False
            assert analysis.verdict != p3.GO_LOCAL_LOCUS_SIGNAL

    def test_go3_threshold_is_inclusive(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.20, 0.25, 0.25), "C": (0.70, 0.75, 0.75)})
        )
        assert analysis.arms["I"].spread == 0.05 == p3.GO3_SPREAD_AT_MOST
        assert analysis.go3 is True

    def test_a_wide_single_field_arm_does_not_go(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.20, 0.25, 0.26), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.arms["I"].spread == 0.06
        assert analysis.go3 is False
        assert analysis.verdict != p3.GO_LOCAL_LOCUS_SIGNAL

    def test_all_three_go_conditions_are_required(self):
        # GO-1 and GO-2 hold, GO-3 does not: the verdict must not be GO.
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.20, 0.25, 0.26), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.go1 and analysis.go2 and not analysis.go3
        assert analysis.verdict == p3.INCONCLUSIVE_AND_STOP


class TestKillVerdicts:
    def test_k1_fires_when_the_two_arms_are_too_close(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.50, 0.50, 0.50), "C": (0.55, 0.55, 0.55)})
        )
        assert analysis.separation == 0.05
        assert analysis.k1 is True
        assert analysis.verdict == p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION

    def test_k1_separation_is_inclusive_at_the_threshold(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.50, 0.50, 0.50), "C": (0.60, 0.60, 0.60)})
        )
        assert analysis.separation == p3.K1_MIN_SEPARATION
        assert analysis.k1 is False
        assert analysis.verdict != p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION

    def test_k2_fires_when_a_single_field_arm_is_noisier_than_the_gap(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.20, 0.30, 0.40), "C": (0.35, 0.40, 0.45)})
        )
        assert analysis.separation == 0.10
        assert analysis.k1 is False
        assert analysis.k2 is True
        assert analysis.k2_arms == ("I",)
        assert analysis.verdict == p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION

    def test_k2_reads_every_arm_including_the_endpoints(self):
        """`any arm` is unscoped in the preregistration, unlike GO-3's two named arms."""
        analysis = p3.analyze(
            synthetic_log({"N": (0.60, 0.75, 0.90), "B": (0.20, 0.20, 0.20)}
                          | {"I": (0.40, 0.45, 0.50), "C": (0.55, 0.60, 0.65)})
        )
        assert analysis.separation == 0.15
        assert analysis.k1 is False
        assert analysis.k2_arms == ("N",)
        assert analysis.verdict == p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION

    def test_k2_separation_is_inclusive_at_the_threshold(self):
        """A spread exactly equal to the separation does not trip K2 -- only exceeding it does.

        It also pins the rounding rule: ``0.40 - 0.20`` is not exactly ``0.2`` in binary floating
        point, and the comparison has to treat it as equal to the separation anyway.
        """
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.20, 0.30, 0.40), "C": (0.50, 0.50, 0.50)})
        )
        assert analysis.arms["I"].spread == analysis.separation == 0.20
        assert analysis.k2 is False


class TestEndpointValidityGuard:
    def test_a_locus_signal_with_reversed_endpoints_is_not_interpretable(self):
        analysis = p3.analyze(
            synthetic_log({"N": (0.50, 0.50, 0.50), "B": (0.60, 0.60, 0.60)}
                          | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.e1 is False
        assert (analysis.go1, analysis.go2, analysis.go3) == (True, True, True)
        assert analysis.verdict == p3.ATTRIBUTION_NOT_INTERPRETABLE

    def test_a_collapsed_endpoint_gap_is_not_interpretable(self):
        analysis = p3.analyze(
            synthetic_log({"N": (0.76, 0.76, 0.76), "B": (0.74, 0.74, 0.74)}
                          | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})
        )
        assert analysis.e1 is True and analysis.e2 is False
        assert analysis.verdict == p3.ATTRIBUTION_NOT_INTERPRETABLE

    def test_the_guard_cannot_promote_a_kill_to_a_go(self):
        analysis = p3.analyze(
            synthetic_log({"N": (0.50, 0.50, 0.50), "B": (0.60, 0.60, 0.60)}
                          | {"I": (0.50, 0.50, 0.50), "C": (0.55, 0.55, 0.55)})
        )
        assert analysis.k1 is True
        assert analysis.verdict != p3.GO_LOCAL_LOCUS_SIGNAL

    def test_the_guard_blocks_before_the_kill_conditions_are_read(self):
        """Endpoint failure is reported as uninterpretable, not as an attribution failure."""
        analysis = p3.analyze(
            synthetic_log({"N": (0.50, 0.50, 0.50), "B": (0.60, 0.60, 0.60)}
                          | {"I": (0.50, 0.50, 0.50), "C": (0.55, 0.55, 0.55)})
        )
        assert analysis.verdict == p3.ATTRIBUTION_NOT_INTERPRETABLE

    def test_the_frozen_endpoint_threshold_matches_the_preregistration(self):
        assert p3.E2_MIN_ENDPOINT_GAP == 0.275


class TestInconclusiveAndIncomplete:
    def test_neither_go_nor_kill_is_inconclusive_and_stops(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.73, 0.75, 0.77), "C": (0.58, 0.60, 0.62)})
        )
        assert not analysis.go and not analysis.kill
        assert analysis.verdict == p3.INCONCLUSIVE_AND_STOP

    def test_a_failed_position_makes_the_run_incomplete(self):
        analysis = p3.analyze(
            synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)},
                          missing={("I", 2)})
        )
        assert analysis.verdict == p3.EXECUTION_INCOMPLETE
        assert analysis.arms["I"].usable == 2

    def test_a_short_log_is_incomplete_even_when_every_arm_has_values(self):
        records = synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})
        analysis = p3.analyze(records[:-1])
        assert analysis.records == 11
        assert analysis.verdict == p3.EXECUTION_INCOMPLETE

    def test_an_empty_log_is_incomplete_and_claims_nothing(self):
        analysis = p3.analyze([])
        assert analysis.verdict == p3.EXECUTION_INCOMPLETE
        assert analysis.records == 0

    def test_an_early_stopped_log_never_reaches_a_go(self):
        """A model-version abort leaves a prefix of the sequence; it must not be analysed as data."""
        records = synthetic_log(ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})[:4]
        assert p3.analyze(records).verdict == p3.EXECUTION_INCOMPLETE


class TestReportRendering:
    def test_the_report_carries_every_raw_value_and_the_verdict(self):
        values = ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)}
        records = synthetic_log(values)
        text = p3.render_report(p3.analyze(records), records=records)
        for arm in p3.ARMS:
            for value in values[arm]:
                assert f"{value:g}" in text
        assert p3.GO_LOCAL_LOCUS_SIGNAL in text
        assert p3.PREREGISTRATION_ID in text
        assert p3.P3_MODEL in text

    def test_the_report_keeps_the_four_kinds_of_statement_apart(self):
        text = p3.render_report(p3.analyze(synthetic_log(ENDPOINTS | {
            "I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)})))
        for heading in ("Preregistered design", "Local measurement", "Derived calculation", "Limitation"):
            assert heading in text

    def test_the_report_states_the_alignment_caveat_whenever_it_renders(self):
        for values in (ENDPOINTS | {"I": (0.22, 0.25, 0.27), "C": (0.73, 0.75, 0.77)},
                       ENDPOINTS | {"I": (0.50, 0.50, 0.50), "C": (0.55, 0.55, 0.55)}):
            text = p3.render_report(p3.analyze(synthetic_log(values)))
            assert "FIELD_ALIGNMENT_CAVEAT" in text
            assert "one payload" in text

    def test_an_incomplete_run_renders_without_inventing_numbers(self):
        text = p3.render_report(p3.analyze([]))
        assert p3.EXECUTION_INCOMPLETE in text
        assert "n/a" in text

    def test_every_verdict_has_a_sentence_and_no_go_sentence_overclaims(self):
        assert set(p3._VERDICT_SENTENCES) == {
            p3.GO_LOCAL_LOCUS_SIGNAL,
            p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION,
            p3.ATTRIBUTION_NOT_INTERPRETABLE,
            p3.INCONCLUSIVE_AND_STOP,
            p3.EXECUTION_INCOMPLETE,
        }
        joined = " ".join(p3._VERDICT_SENTENCES.values()).lower()
        for overclaim in ("jev stores", "jev reads", "jev ignores", "primarily reads"):
            assert overclaim not in joined


class TestVerdictVocabulary:
    def test_only_the_preregistered_verdicts_exist(self):
        assert {
            p3.GO_LOCAL_LOCUS_SIGNAL,
            p3.KILL_NO_SINGLE_FIELD_ATTRIBUTION,
            p3.ATTRIBUTION_NOT_INTERPRETABLE,
            p3.INCONCLUSIVE_AND_STOP,
            p3.DESIGN_INVALIDATED_BEFORE_SPEND,
            p3.MODEL_VERSION_MISMATCH,
            p3.EXECUTION_INCOMPLETE,
        } == {
            "P3_GO_LOCAL_LOCUS_SIGNAL",
            "P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION",
            "P3_ATTRIBUTION_NOT_INTERPRETABLE",
            "P3_INCONCLUSIVE_AND_STOP",
            "P3_DESIGN_INVALIDATED_BEFORE_SPEND",
            "P3_MODEL_VERSION_MISMATCH",
            "P3_EXECUTION_INCOMPLETE",
        }
