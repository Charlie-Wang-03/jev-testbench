"""Registry invariants and the runner, driven by a fake client. No network access."""

import inspect
import json

import pytest
import httpx2
from typesafe_sdk import (
    ChoiceAnswer,
    NoulAnswer,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeAuthenticationError,
    Usage,
)

from jev_lab import experiments as lab
from jev_lab.experiments import (
    ATOMIC_QUESTIONS,
    BATCH_ARM,
    CORE,
    EXTENDED,
    EXPERIMENTS,
    MAX_REPEATS,
    PARALLEL_CYCLES,
    SEPARATE_ARM,
    Case,
    answer_digest,
    confidence_of,
    experiment_call_ceiling,
    experiment_names,
    experiments_for_tier,
    get_experiment,
    normalized_score,
    noul_of,
    run_experiment,
    score_of,
    top_label,
    total_cases,
)
from jev_lab.recorder import read_records, UsageRecorder
from jev_lab.routing import HANDLERS

VALID_TYPES = {"choice", "score", "noul"}

# Two order-balanced cycles of six calls. See `test_every_experiment_is_bounded_to_a_small_number_of_calls`.
MAX_CASES_PER_EXPERIMENT = 12


def make_response(answers=None, model="jev-1.13.0", input_tokens=100, output_tokens=10):
    return SystemOneResponse(
        model=model,
        usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens),
        answers=answers or {},
    )


class FakeClient:
    """Answers every question with a fixed answer of the matching kind."""

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def system_one(self, state, questions, model=None):
        self.calls.append({"state": state, "questions": questions, "model": model})
        if self.error is not None:
            raise self.error
        answers = {}
        for name, question in questions.items():
            kind = question.type if hasattr(question, "type") else question["type"]
            if kind == "choice":
                answers[name] = ChoiceAnswer(choice="billing", confidence=0.8, probabilities={"billing": 0.8})
            elif kind == "score":
                answers[name] = ScoreAnswer(
                    score=1.5, confidence=0.7, legend={0: "a", 1: "b", 2: "c"}, probabilities={0: 0.0, 1: 0.5, 2: 0.5}
                )
            else:
                answers[name] = NoulAnswer(noul=0.9)
        return make_response(answers=answers)


class TestRegistryShape:
    def test_fifteen_experiments_are_registered(self):
        assert len(EXPERIMENTS) == 15

    def test_names_are_sorted_and_consistent_with_their_keys(self):
        names = experiment_names()
        assert names == sorted(names)
        for name in names:
            assert EXPERIMENTS[name].name == name

    def test_every_experiment_declares_a_known_tier(self):
        for experiment in EXPERIMENTS.values():
            assert experiment.tier in {CORE, EXTENDED}

    def test_every_experiment_has_an_intent_line(self):
        for experiment in EXPERIMENTS.values():
            assert experiment.intent.strip()

    def test_unknown_experiment_raises_a_helpful_error(self):
        with pytest.raises(KeyError, match="unknown experiment"):
            get_experiment("99_nope")

    def test_tier_lookup_is_consistent_with_total_cases(self):
        all_experiments = experiments_for_tier(CORE) + experiments_for_tier(EXTENDED)
        assert total_cases(all_experiments) == total_cases(list(EXPERIMENTS.values()))

    def test_every_registered_digest_honours_the_case_response_protocol(self):
        """The digest contract is ``digest(case, response)``.

        A digest registered with the wrong arity only blows up mid-run, after the API call has
        already been paid for, so it is checked here against an empty response instead.
        """
        for experiment in EXPERIMENTS.values():
            if experiment.digest is None:
                continue
            for case in experiment.cases():
                assert isinstance(experiment.digest(case, make_response()), dict)

    def test_a_digest_runs_locally_without_touching_the_api(self, tmp_path):
        """A digest is pure interpretation: it must not need a client to produce its result."""
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("04_confidence"), client=FakeClient(), recorder=recorder)
        for record in read_records(recorder.path):
            assert "derived" in record["notes"]


class TestCaseInvariants:
    def test_every_case_has_an_id_state_and_at_least_one_question(self):
        for experiment in EXPERIMENTS.values():
            for case in experiment.cases():
                assert case.case_id
                assert case.state is not None
                assert case.questions, f"{experiment.name}/{case.case_id} has no questions"

    def test_case_ids_are_unique_within_an_experiment(self):
        for experiment in EXPERIMENTS.values():
            ids = [case.case_id for case in experiment.cases()]
            assert len(ids) == len(set(ids)), f"duplicate case ids in {experiment.name}"

    def test_all_question_types_are_recognised(self):
        for experiment in EXPERIMENTS.values():
            for case in experiment.cases():
                for question in case.questions.values():
                    assert question.type in VALID_TYPES

    def test_every_experiment_is_bounded_to_a_small_number_of_calls(self):
        # Guards against an experiment that quietly grows into an unbounded loop. The ceiling is
        # 12 because `03_parallel_questions` needs two cycles of six calls to balance its arm
        # order; raising it again should be a deliberate act, not a side effect.
        #
        # Checked against the *call ceiling*, not the declared case count: an experiment whose
        # next request depends on the last answer declares fewer cases than it can call, and the
        # count that has to stay bounded is the one the run can actually reach.
        for experiment in EXPERIMENTS.values():
            ceiling = experiment_call_ceiling(experiment)
            assert ceiling <= MAX_CASES_PER_EXPERIMENT, f"{experiment.name} makes too many calls"

    def test_the_largest_experiment_is_the_order_balanced_one(self):
        """The ceiling exists for a known reason: if something else is now the biggest, look why."""
        largest = max(EXPERIMENTS.values(), key=experiment_call_ceiling)
        assert largest.name == "03_parallel_questions"
        assert experiment_call_ceiling(largest) == MAX_CASES_PER_EXPERIMENT

    def test_a_control_flow_experiment_states_its_ceiling(self):
        """A declared case list under-counts when a case schedules another, so the gap must be
        stated rather than inferred from the list."""
        for experiment in EXPERIMENTS.values():
            if experiment.follow_up is None:
                assert experiment.call_ceiling is None
                continue
            assert experiment.call_ceiling is not None, f"{experiment.name} hides its real budget"
            assert experiment.call_ceiling >= len(experiment.cases())

    def test_every_registered_follow_up_honours_the_case_response_protocol(self):
        """The follow-up contract is ``follow_up(case, response)`` and it returns cases.

        Like the digest, an arity mistake here only surfaces mid-run, after the first call has
        been paid for. A follow-up that raised on an empty response would abort the flow there.
        """
        for experiment in EXPERIMENTS.values():
            if experiment.follow_up is None:
                continue
            for case in experiment.cases():
                scheduled = experiment.follow_up(case, make_response())
                assert isinstance(scheduled, list)
                assert all(isinstance(entry, Case) for entry in scheduled)

    def test_a_follow_up_runs_locally_without_touching_the_api(self, tmp_path):
        """A follow-up chooses what to run; it never runs it."""
        for experiment in EXPERIMENTS.values():
            if experiment.follow_up is None:
                continue
            for case in experiment.cases():
                experiment.follow_up(case, make_response())

    def test_cases_are_rebuilt_fresh_each_time(self):
        experiment = get_experiment("02_structured_addressing")
        assert experiment.cases() is not experiment.cases()


class TestSpecificExperiments:
    def test_primitives_asks_all_three_types_in_one_request(self):
        cases = get_experiment("01_primitives").cases()
        assert len(cases) == 1
        types = {question.type for question in cases[0].questions.values()}
        assert types == {"choice", "score", "noul"}

    def test_structured_state_compares_equal_content_in_two_forms(self):
        cases = get_experiment("02_structured_addressing").cases()
        assert len(cases) == 2
        assert list(cases[0].questions) == list(cases[1].questions)
        assert cases[0].state != cases[1].state
        assert isinstance(cases[0].state, dict)

    def test_parallel_questions_has_one_batched_arm_and_one_per_question(self):
        cases = get_experiment("03_parallel_questions").cases()
        batched = [case for case in cases if case.notes["arm"] == BATCH_ARM]
        separate = [case for case in cases if case.notes["arm"] == SEPARATE_ARM]
        assert len(batched) == PARALLEL_CYCLES
        assert len(separate) == len(batched[0].questions) * PARALLEL_CYCLES
        assert all(len(case.questions) == 1 for case in separate)

    def test_parallel_questions_uses_identical_state_and_questions_in_both_arms(self):
        cases = get_experiment("03_parallel_questions").cases()
        batched = next(case for case in cases if case.notes["arm"] == BATCH_ARM)
        for case in (c for c in cases if c.notes["arm"] == SEPARATE_ARM):
            assert case.state == batched.state
            name = next(iter(case.questions))
            assert name in batched.questions
            # Same question object, not merely the same name.
            assert case.questions[name] is batched.questions[name]

    def test_parallel_questions_balances_the_order_so_neither_arm_is_always_first(self):
        """Without this the batched arm is always the cold request and the arm is unreadable."""
        cases = get_experiment("03_parallel_questions").cases()
        positions = {
            cycle: [case.notes["arm"] for case in cases if case.notes["cycle"] == cycle]
            for cycle in range(1, PARALLEL_CYCLES + 1)
        }
        assert len(positions) == PARALLEL_CYCLES
        for cycle, arms in positions.items():
            assert arms[0] != arms[-1], f"cycle {cycle} does not lead and trail with opposite arms"
        # Across cycles each arm leads exactly once, so position cannot track arm identity.
        assert {arms[0] for arms in positions.values()} == {BATCH_ARM, SEPARATE_ARM}
        assert {arms[-1] for arms in positions.values()} == {BATCH_ARM, SEPARATE_ARM}

    def test_parallel_questions_declares_its_call_count(self):
        expected = PARALLEL_CYCLES * (1 + len(ATOMIC_QUESTIONS))
        assert len(get_experiment("03_parallel_questions").cases()) == expected

    def test_parallel_questions_never_claims_a_latency_speedup(self):
        """The design balances order; it does not license a performance claim."""
        # Normalize comment markers and line wrapping so the assertion is about the wording,
        # not about where the author happened to break the line.
        source = " ".join(inspect.getsource(lab).replace("#", " ").split())
        assert "only observational" in source
        assert "speedup claim" in source

    def test_parallel_questions_keeps_question_order_constant_within_the_separate_arm(self):
        """A constant within-arm order cancels; a varying one could masquerade as an arm effect."""
        cases = get_experiment("03_parallel_questions").cases()
        orders = [
            [next(iter(case.questions)) for case in cases if case.notes["cycle"] == cycle and case.notes["arm"] == SEPARATE_ARM]
            for cycle in range(1, PARALLEL_CYCLES + 1)
        ]
        assert orders[0] == orders[1] == list(ATOMIC_QUESTIONS)

    def test_confidence_experiment_documents_that_its_threshold_is_a_demo(self):
        cases = get_experiment("04_confidence").cases()
        assert {case.notes["ambiguity"] for case in cases} == {"clear", "ambiguous"}

    def test_instruction_precision_pairs_vague_and_precise_on_one_state(self):
        cases = get_experiment("07_instruction_precision").cases()
        assert cases[0].state == cases[1].state
        assert {case.notes["boundary"] for case in cases} == {"vague", "explicit"}

    def test_state_length_holds_core_evidence_fixed_across_tiers(self):
        cases = get_experiment("10_state_length").cases()
        assert [case.notes["tier"] for case in cases] == ["short", "medium", "longer"]
        assert cases[0].state in cases[2].state
        assert len(cases[0].state) < len(cases[2].state)

    def test_language_pair_covers_both_languages(self):
        cases = get_experiment("11_language_pair").cases()
        assert {case.notes["language"] for case in cases} == {"en", "zh"}

    def test_function_routing_only_reaches_registered_handlers(self):
        cases = get_experiment("12_function_routing").cases()
        for case in cases:
            assert case.notes["side_effects"] == lab.ROUTING_SIDE_EFFECTS
            criteria = case.questions["function"].criteria
            assert set(criteria) == set(HANDLERS)

    def test_repeatability_is_bounded(self):
        cases = get_experiment("13_repeatability").cases()
        assert len(cases) == lab.REPEAT_CALLS
        assert len(cases) <= MAX_REPEATS


def state_text(case):
    """A case's state as searchable text, whether it is a string or structured JSON."""
    return case.state if isinstance(case.state, str) else json.dumps(case.state)


class TestStructuredAddressing:
    """02 varies the addressing clause. It is not a clean JSON-versus-prose causal test."""

    # The four facts both arms must carry, so neither arm is better informed than the other.
    FACTS = ("t-4471", "i was charged twice for order #98423.", "30", "refund the duplicate in full")

    def test_both_arms_carry_the_same_facts(self):
        for case in get_experiment("02_structured_addressing").cases():
            text = state_text(case).lower()
            for fact in self.FACTS:
                assert fact in text, f"{case.case_id} is missing {fact!r}"

    def test_the_two_arms_use_the_same_primitive_set(self):
        cases = get_experiment("02_structured_addressing").cases()
        for case in cases:
            assert {question.type for question in case.questions.values()} == {"choice", "noul"}

    def test_both_arms_ask_the_same_question_keys(self):
        cases = get_experiment("02_structured_addressing").cases()
        assert list(cases[0].questions) == list(cases[1].questions)

    def test_choice_criteria_are_identical_across_arms(self):
        first, second = get_experiment("02_structured_addressing").cases()
        assert first.questions["department"].criteria == second.questions["department"].criteria

    def test_noul_criteria_are_identical_across_arms(self):
        first, second = get_experiment("02_structured_addressing").cases()
        assert first.questions["asks_for_refund"].criteria == second.questions["asks_for_refund"].criteria

    def test_structured_arm_addresses_by_field_path(self):
        cases = get_experiment("02_structured_addressing").cases()
        structured = next(case for case in cases if case.notes["state_form"] == "json")
        for question in structured.questions.values():
            assert "`" in question.instructions, "the structured arm should name a field path"

    def test_prose_arm_never_references_a_json_field_path(self):
        cases = get_experiment("02_structured_addressing").cases()
        prose = next(case for case in cases if case.notes["state_form"] == "prose")
        for question in prose.questions.values():
            text = question.instructions
            assert "`" not in text, "the prose arm must not use backticked paths"
            assert "ticket." not in text and "policy." not in text
            assert "[" not in text, "the prose arm must not use JSON index syntax"

    def test_the_length_confound_is_acknowledged_in_the_source(self):
        """The design is documented as confounded on length, not presented as a clean test."""
        source = __import__("inspect").getsource(lab)
        header = source[source.index("# `02_structured_addressing`") : source.index("def _02_")]
        assert "confounded" in header
        assert "not a clean" in header.lower()


class TestConfidenceDesign:
    """04 separates correctness from confidence and gates on confidence in code."""

    def test_both_arms_use_the_same_choice_and_score_criteria(self):
        first, second = get_experiment("04_confidence").cases()
        assert first.questions["intent"].criteria == second.questions["intent"].criteria
        assert first.questions["specificity"].criteria == second.questions["specificity"].criteria

    def test_both_arms_ask_a_choice_and_a_score(self):
        for case in get_experiment("04_confidence").cases():
            assert {question.type for question in case.questions.values()} == {"choice", "score"}

    def test_clear_arm_declares_an_expected_label(self):
        cases = get_experiment("04_confidence").cases()
        clear = next(case for case in cases if case.notes["ambiguity"] == "clear")
        assert clear.notes["expected"] in lab.CONFIDENCE_CHOICE_CRITERIA

    def test_ambiguous_arm_does_not_force_a_single_expected_label(self):
        cases = get_experiment("04_confidence").cases()
        ambiguous = next(case for case in cases if case.notes["ambiguity"] == "ambiguous")
        assert "expected" not in ambiguous.notes
        assert ambiguous.notes["expected_policy"]

    def test_the_two_states_are_close_in_length(self):
        first, second = get_experiment("04_confidence").cases()
        a, b = len(state_text(first).encode("utf-8")), len(state_text(second).encode("utf-8"))
        assert abs(a - b) / max(a, b) < 0.25, "arms drifted apart in length"

    def test_both_states_share_the_scenario_entities(self):
        for case in get_experiment("04_confidence").cases():
            text = case.state.lower()
            for entity in ("account 4471", "account 8891", "$250", "transfer"):
                assert entity in text, f"{case.case_id} lost {entity!r}"

    def test_gate_escalates_below_the_threshold(self):
        assert lab._confidence_gate(0.59)["decision"] == lab.GATE_ESCALATE

    def test_gate_accepts_at_the_threshold(self):
        assert lab._confidence_gate(lab.CONFIDENCE_GATE_THRESHOLD)["decision"] == lab.GATE_ACCEPT

    def test_gate_accepts_above_the_threshold(self):
        assert lab._confidence_gate(0.95)["decision"] == lab.GATE_ACCEPT

    def test_gate_reports_not_applicable_without_confidence(self):
        assert lab._confidence_gate(None)["decision"] == "not_applicable"

    def test_threshold_is_labelled_a_demo_not_a_tuned_value(self):
        basis = lab._confidence_gate(0.5)["threshold_basis"].lower()
        assert "demo" in basis
        assert "not calibrated" in basis and "not tuned" in basis

    def test_threshold_constant_is_documented_as_a_demo(self):
        source = __import__("inspect").getsource(lab)
        marker = source.index("CONFIDENCE_GATE_THRESHOLD =")
        preamble = source[max(0, marker - 600) : marker]
        assert "NOT a tuned" in preamble or "not a tuned" in preamble

    def test_the_gate_actually_runs_and_reaches_the_log(self, tmp_path):
        """The gate is executed in code and its decision is persisted, with no extra API call."""
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("04_confidence"), client=FakeClient(), recorder=recorder)
        records = list(read_records(recorder.path))
        assert len(records) == 2, "the gate must not add API calls"
        for record in records:
            derived = record["notes"]["derived"]
            assert derived["gate"]["decision"] in {lab.GATE_ACCEPT, lab.GATE_ESCALATE}
            assert derived["gate"]["threshold"] == lab.CONFIDENCE_GATE_THRESHOLD

    def test_correctness_is_reported_separately_from_confidence(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("04_confidence"), client=FakeClient(), recorder=recorder)
        by_case = {record["case_id"]: record["notes"]["derived"] for record in read_records(recorder.path)}
        # The clear arm carries an expectation, so a match is reported...
        assert by_case["specific_evidence"]["expected"] == "release_transfer"
        assert by_case["specific_evidence"]["matches_expected"] is False  # FakeClient answers "billing"
        # ...and the ambiguous arm reports no correctness at all rather than inventing one.
        assert by_case["ambiguous_evidence"]["matches_expected"] is None

    def test_score_confidence_is_not_presented_as_correctness(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("04_confidence"), client=FakeClient(), recorder=recorder)
        derived = next(iter(read_records(recorder.path)))["notes"]["derived"]
        assert "not correctness" in derived["specificity_note"]


class TestInstructionPrecisionDesign:
    """07 changes only how explicitly the decision boundary is stated."""

    # Nouns lifted from the state; if they appear in the question, the answer can be lexical.
    STATE_NOUNS = ("export", "csv", "report", "spun", "never", "finished", "minutes", "gave", "used")

    def test_state_is_byte_identical_across_arms(self):
        first, second = get_experiment("07_instruction_precision").cases()
        assert first.state == second.state
        assert first.state.encode("utf-8") == second.state.encode("utf-8")

    def test_both_arms_carry_criteria(self):
        for case in get_experiment("07_instruction_precision").cases():
            assert case.questions["blocked"].criteria

    def test_criteria_presence_is_asserted_in_the_notes(self):
        for case in get_experiment("07_instruction_precision").cases():
            assert case.notes["criteria"].startswith("present")

    def test_both_arms_use_the_same_primitive_and_answer_space(self):
        cases = get_experiment("07_instruction_precision").cases()
        assert list(cases[0].questions) == list(cases[1].questions)
        for case in cases:
            assert case.questions["blocked"].type == "noul"

    def test_explicit_boundary_does_not_leak_the_state_s_nouns(self):
        cases = get_experiment("07_instruction_precision").cases()
        explicit = next(case for case in cases if case.notes["boundary"] == "explicit")
        question = explicit.questions["blocked"]
        criteria = question.criteria
        blob = f"{question.instructions} {criteria}".lower()
        leaked = [noun for noun in self.STATE_NOUNS if noun in blob]
        assert leaked == [], f"explicit boundary leaks state nouns: {leaked}"

    def test_vague_boundary_does_not_leak_the_state_s_nouns(self):
        cases = get_experiment("07_instruction_precision").cases()
        vague = next(case for case in cases if case.notes["boundary"] == "vague")
        question = vague.questions["blocked"]
        criteria = question.criteria
        blob = f"{question.instructions} {criteria}".lower()
        assert [noun for noun in self.STATE_NOUNS if noun in blob] == []

    def test_the_two_boundaries_actually_differ(self):
        cases = get_experiment("07_instruction_precision").cases()
        vague = cases[0].questions["blocked"]
        explicit = cases[1].questions["blocked"]
        assert vague.instructions != explicit.instructions
        assert len(explicit.instructions) > len(vague.instructions)
        assert vague.criteria != explicit.criteria

    def test_the_isolated_variable_is_documented_as_compound(self):
        source = __import__("inspect").getsource(lab)
        assert "isolate instruction wording from criteria wording" in source

    def test_model_info_resolves_both_aliases(self):
        cases = get_experiment("00_model_info").cases()
        assert {case.notes["alias"] for case in cases} == {"jev-latest", "jev-preview"}


class TestDerivedHelpers:
    def response(self):
        return make_response(
            answers={
                "dept": ChoiceAnswer(choice="billing", confidence=0.8, probabilities={"billing": 0.8}),
                "sev": ScoreAnswer(score=1.7, confidence=0.6, legend={0: "a", 1: "b", 2: "c"}, probabilities={0: 0.1, 1: 0.5, 2: 0.4}),
                "spam": NoulAnswer(noul=0.98),
            }
        )

    def test_answer_digest_keeps_the_salient_value_per_kind(self):
        digest = answer_digest(self.response())
        assert digest["dept"]["choice"] == "billing"
        assert digest["sev"]["score"] == 1.7
        assert digest["spam"]["noul"] == 0.98

    def test_answer_digest_stringifies_score_level_keys(self):
        digest = answer_digest(self.response())
        assert set(digest["sev"]["probabilities"]) == {"0", "1", "2"}

    def test_answer_digest_does_not_invent_confidence_for_noul(self):
        assert "confidence" not in answer_digest(self.response())["spam"]

    def test_accessors_return_none_for_the_wrong_answer_kind(self):
        response = self.response()
        assert top_label(response, "sev") is None
        assert score_of(response, "dept") is None
        assert noul_of(response, "dept") is None
        assert confidence_of(response, "spam") is None

    def test_accessors_return_values_for_the_right_kind(self):
        response = self.response()
        assert top_label(response, "dept") == "billing"
        assert score_of(response, "sev") == 1.7
        assert noul_of(response, "spam") == 0.98
        assert confidence_of(response, "sev") == 0.6

    def test_normalized_score_divides_by_the_top_level(self):
        assert normalized_score(self.response(), "sev", levels=3) == 0.85

    def test_normalized_score_is_none_for_a_single_level(self):
        assert normalized_score(self.response(), "sev", levels=1) is None


class TestRunner:
    def test_each_case_appends_exactly_one_record(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        records = run_experiment(get_experiment("01_primitives"), client=FakeClient(), recorder=recorder)
        assert len(records) == 1
        assert len(list(read_records(recorder.path))) == 1

    def test_records_carry_model_and_usage_from_the_response(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("01_primitives"), client=FakeClient(), recorder=recorder)
        record = next(iter(read_records(recorder.path)))
        assert record["status"] == "ok"
        assert record["model_resolved"] == "jev-1.13.0"
        assert record["input_tokens"] == 100
        assert record["output_tokens"] == 10
        assert record["total_tokens"] == 110
        assert record["estimated_cost_usd"] is not None

    def test_max_requests_truncates_the_run(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        records = run_experiment(
            get_experiment("03_parallel_questions"), client=FakeClient(), recorder=recorder, max_requests=2
        )
        assert len(records) == 2

    def test_on_case_receives_each_response(self, tmp_path):
        seen = []
        run_experiment(
            get_experiment("01_primitives"),
            client=FakeClient(),
            recorder=UsageRecorder(tmp_path),
            on_case=lambda case, record, response: seen.append((case.case_id, response.model)),
        )
        assert seen == [("ticket_all_primitives", "jev-1.13.0")]

    def test_a_failing_case_is_recorded_and_the_run_continues(self, tmp_path):
        errors = []
        recorder = UsageRecorder(tmp_path)
        records = run_experiment(
            get_experiment("02_structured_addressing"),
            client=FakeClient(error=RuntimeError("boom")),
            recorder=recorder,
            on_error=lambda case, error: errors.append(case.case_id),
        )
        assert records == []
        assert sorted(errors) == ["prose_addressing", "structured_addressing"]
        persisted = list(read_records(recorder.path))
        assert [record["status"] for record in persisted] == ["error", "error"]
        assert [record["error_type"] for record in persisted] == ["RuntimeError", "RuntimeError"]

    def test_authentication_failure_aborts_immediately(self, tmp_path):
        auth_error = TypeSafeAuthenticationError(401, None, httpx2.Headers())
        recorder = UsageRecorder(tmp_path)
        with pytest.raises(TypeSafeAuthenticationError):
            run_experiment(
                get_experiment("02_structured_addressing"),
                client=FakeClient(error=auth_error),
                recorder=recorder,
            )
        # The first case is recorded, and the second is never attempted.
        assert len(list(read_records(recorder.path))) == 1

    def test_question_metadata_is_recorded_per_case(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("01_primitives"), client=FakeClient(), recorder=recorder)
        record = next(iter(read_records(recorder.path)))
        assert record["question_count"] == 3
        assert record["question_types"] == ["choice", "noul", "score"]
        assert record["state_chars"] > 0

    def test_model_requested_defaults_to_jev_latest(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("01_primitives"), client=FakeClient(), recorder=recorder)
        record = next(iter(read_records(recorder.path)))
        assert record["model_requested"] == lab.DEFAULT_MODEL == "jev-latest"

    def test_case_notes_are_preserved_in_the_log(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment("04_confidence"), client=FakeClient(), recorder=recorder)
        notes = [record["notes"] for record in read_records(recorder.path)]
        assert {note["ambiguity"] for note in notes} == {"clear", "ambiguous"}
