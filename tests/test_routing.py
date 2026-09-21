"""`12_function_routing`. Offline, driven by the real SDK encoder and synthetic records.

The load-bearing checks here are the ones the design calls hard rules:

* **The registry is closed.** A label the registry does not carry, and an argument outside the
  selected function's frozen set, both stop before execution -- no fallback, no nearest name, no
  argument defaulted or dropped.
* **Nothing the model returns is ever executed.** No answer is evaluated, imported, or turned into
  a callable; the only call Python makes is `HANDLERS[name](value)`, and only after the frozen
  policy permits it.
* **The expected labels never steer a decision.** They live in local notes, they are absent from
  the payload, and they are read only to fill in a comparison after the fact.

Everything runs against `httpx2.MockTransport` under the real SDK client, with the same
`TransportProbe` the CLI installs, so the payloads and the attempt counts are the ones a real run
would produce. No test touches the network.
"""

import hashlib
import json
import pathlib
import re
import tempfile

import httpx2
import pytest
from typesafe_sdk import SystemOneResponse, TypeSafeClient
from typesafe_sdk.constants import DEFAULT_TIMEOUT

from jev_lab.client import TransportProbe
from jev_lab.experiments import (
    ROUTING_ARGUMENT_CRITERIA,
    ROUTING_ARGUMENT_INSTRUCTIONS,
    ROUTING_SIDE_EFFECTS,
    ROUTING_STATES,
    experiment_call_ceiling,
    experiment_names,
    get_experiment,
    run_experiment,
)
from jev_lab.recorder import DEFAULT_RESULTS_DIR, UsageRecorder, read_records
from jev_lab.routing import (
    ACTUAL_HANDLER_EXECUTION_REALIZED,
    ACTUAL_HANDLER_EXECUTION_UNTESTED,
    FAIL_CLOSED_SUPPRESSION_REALIZED,
    FUNCTION_EXECUTION_SUPPRESSED,
    FUNCTION_ROUTE_UNAVAILABLE,
    HANDLERS,
    OUTCOME_EXECUTED,
    OUTCOME_HUMAN_REVIEW,
    OUTCOME_ROUTE_UNAVAILABLE,
    ROUTING,
    ROUTING_ARGUMENT_NAME,
    ROUTING_ARGUMENT_QUESTION,
    ROUTING_ARGUMENT_QUESTIONS,
    ROUTING_ARGUMENTS,
    ROUTING_CASE_ORDER,
    ROUTING_CONFIDENCE_FLOOR,
    ROUTING_EXPECTED,
    ROUTING_EXPECTED_FUNCTIONS_OBSERVED,
    ROUTING_FUNCTION_MISMATCH_OBSERVED,
    ROUTING_FUNCTION_QUESTION,
    ROUTING_FUNCTIONS,
    ROUTING_HUMAN_REVIEW_THRESHOLD,
    ROUTING_REVIEW_QUESTION,
    ROUTING_SUPPRESSION_EXPECTATION_MET,
    ROUTING_SUPPRESSION_EXPECTATION_MISSED,
    analyze_routing,
    argument_allowed,
    arguments_for,
    build_routing_block,
    route_decision,
    routing_digest,
)

DUMMY_KEY = "not-a-real-key"
REQUEST_ID = "req-routing-0001"

# sha256 of the first 38 lines of `results/usage.jsonl` -- every record that existed before this
# experiment's real run. Appending leaves those bytes untouched, so matching this proves the run
# added a line rather than rewriting one. It is a local, unversioned artifact: the guard skips where
# the log is absent instead of pretending to have checked it.
PRE_RUN_PREFIX_SHA256 = "c45a14103b9551e584fb891b522110d133137f42146c7942f4fbee982b3282fd"

# The label each state is expected to route to, keyed by case id, and the label the mock returns for
# it by default. The review signal is above the frozen threshold for exactly the one case written to
# need a person, so the default run is the scenario's intention.
EXPECTED = {case_id: (function, argument) for case_id, function, argument, _ in ROUTING_EXPECTED}
THRESHOLD_EXPECTED = {
    case_id: expects for case_id, _, _, expects in ROUTING_EXPECTED
}
DEFAULT_REVIEW = {
    case_id: (0.9 if THRESHOLD_EXPECTED[case_id] else 0.05) for case_id in EXPECTED
}
DEFAULT_CONFIDENCE = 0.9

# Every function name a request could carry, in registry order.
ALL_FUNCTIONS = list(ROUTING_FUNCTIONS)

# Directive vocabulary no state may carry: a state that named its own answer would measure string
# matching rather than routing. Matched on word boundaries, so "call." and "calls" are caught too.
DIRECTIVE_WORDS = (
    "call",
    "invoke",
    "handler",
    "function",
    "route",
    "escalate",
    "tool",
    "next step",
)

BY_STATE = {state: case_id for case_id, state in ROUTING_STATES.items()}


def state_of(parsed):
    """Which state a request carried. Takes the *parsed* body, not the raw bytes."""
    return BY_STATE[parsed["state"]]


def _choice(label, labels, probability=0.9, confidence=0.9):
    """A well-formed Choice answer over ``labels`` whose distribution peaks on ``label``."""
    rest = (1.0 - probability) / (len(labels) - 1)
    return {
        "type": "choice",
        "choice": label,
        "confidence": confidence,
        "probabilities": {name: (probability if name == label else rest) for name in labels},
    }


def reply_for(raw, routes=None, confidences=None, reviews=None):
    """A response covering every question in the request that produced it.

    Each override is merged over the default per case, so a caller can move one case's route,
    confidence, or review signal without restating the other three. A partial mapping that fell
    through to a lookup would raise inside the mock and turn the other cases into transport
    errors -- which would read as a fail-closed result rather than as a broken fixture.
    """
    body = json.loads(raw)
    name = state_of(body)
    function, argument = (routes or {}).get(name, EXPECTED[name])
    answers = {}
    for question in body["questions"]:
        if question == ROUTING_FUNCTION_QUESTION:
            answers[question] = _choice(
                function,
                ALL_FUNCTIONS,
                confidence=(confidences or {}).get(name, DEFAULT_CONFIDENCE),
            )
        elif question == ROUTING_REVIEW_QUESTION:
            answers[question] = {
                "type": "noul",
                "noul": (reviews or {}).get(name, DEFAULT_REVIEW[name]),
            }
        else:
            owner = next(f for f, q in ROUTING_ARGUMENT_QUESTION.items() if q == question)
            labels = list(ROUTING_ARGUMENTS[owner])
            # Only the selected function's argument carries the intended label. The other three
            # questions are answered too -- the request asked them -- but with a label Python
            # never reads.
            answers[question] = _choice(argument if owner == function else labels[0], labels)
    return {
        "model": "jev-1.13.0",
        "answers": answers,
        "usage": {"input_tokens": 700, "output_tokens": 70},
    }


def run_offline(routes=None, confidences=None, reviews=None, latencies=None):
    """Run `12` through the real SDK against a mock transport. Returns ``(bodies, records)``.

    ``latencies`` overrides the recorded wall-clock per case, in call order: the mock's own timings
    are real but meaningless (sub-millisecond, in-process).
    """
    bodies = []

    def handler(request):
        bodies.append(request.content)
        return httpx2.Response(
            200,
            json=reply_for(request.content, routes=routes, confidences=confidences, reviews=reviews),
            headers={"x-typesafe-request-id": REQUEST_ID},
        )

    probe = TransportProbe()
    http_client = probe.instrument(timeout=DEFAULT_TIMEOUT, transport=httpx2.MockTransport(handler))
    client = TypeSafeClient(api_key=DUMMY_KEY, http_client=http_client)
    with tempfile.TemporaryDirectory() as directory:
        recorder = UsageRecorder(pathlib.Path(directory))
        with client:
            run_experiment(
                get_experiment(ROUTING),
                client=client,
                recorder=recorder,
                model="jev-latest",
                probe=probe,
            )
        records = list(read_records(recorder.path))
    if latencies is not None:
        records = _with_latency(records, latencies)
    return [json.loads(body) for body in bodies], records


def _copy(records):
    return [json.loads(json.dumps(record)) for record in records]


def _with_latency(records, values):
    """A copy of the records with the four latency windows set explicitly, in call order."""
    out = _copy(records)
    assert len(values) == len(out)
    for record, value in zip(out, values):
        record["latency_ms"] = value
    return out


def _with_answer(records, case_id, question, answer):
    """A copy of the records with one answer replaced (or removed when ``None``)."""
    out = _copy(records)
    for record in out:
        if record["case_id"] == case_id:
            if answer is None:
                record["answers"].pop(question, None)
            else:
                record["answers"][question] = answer
    return out


def _with_field(records, case_id, question, field, value):
    """A copy with one field of one answer replaced (or removed when ``None``)."""
    out = _copy(records)
    for record in out:
        if record["case_id"] == case_id:
            if value is None:
                record["answers"][question].pop(field, None)
            else:
                record["answers"][question][field] = value
    return out


def _by_case(records, case_id):
    return next(record for record in records if record["case_id"] == case_id)


def _decision(records, case_id):
    return route_decision(_by_case(records, case_id))


def _response_for(record):
    """A real SDK response object built from a recorded one, for the digest path.

    Routing answers are Choice and Noul, whose distributions are keyed by *label*, so unlike `06`'s
    Score answers no key has to be coerced back to an integer.
    """
    return SystemOneResponse.model_validate(
        {
            "model": "jev-1.13.0",
            "answers": json.loads(json.dumps(record["answers"])),
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
    )


class TestTheDeclaredShape:
    """Sections D, L and Q: four states, one question set, exactly four calls."""

    def test_the_experiment_declares_four_cases(self):
        assert [case.case_id for case in get_experiment(ROUTING).cases()] == list(ROUTING_CASE_ORDER)

    def test_the_call_count_is_exactly_four(self):
        assert experiment_call_ceiling(get_experiment(ROUTING)) == 4
        bodies, records = run_offline()
        assert len(bodies) == 4
        assert len(records) == 4

    def test_every_request_carries_one_choice_per_function_plus_the_noul(self):
        bodies, _ = run_offline()
        for body in bodies:
            kinds = [question["type"] for question in body["questions"].values()]
            assert kinds.count("choice") == len(ROUTING_FUNCTIONS) + 1
            assert kinds.count("noul") == 1

    def test_every_case_shares_one_question_mapping(self):
        cases = get_experiment(ROUTING).cases()
        assert all(case.questions is cases[0].questions for case in cases)

    def test_the_question_names_are_the_frozen_ones(self):
        _, records = run_offline()
        wanted = set(ROUTING_ARGUMENT_QUESTIONS) | {
            ROUTING_FUNCTION_QUESTION,
            ROUTING_REVIEW_QUESTION,
        }
        for record in records:
            assert set(record["answers"]) == wanted
            assert record["question_types"] == ["choice", "noul"]

    def test_the_routing_choice_offers_exactly_the_registry(self):
        _, records = run_offline()
        criteria = get_experiment(ROUTING).cases()[0].questions[ROUTING_FUNCTION_QUESTION].criteria
        assert set(criteria) == set(HANDLERS) == set(ROUTING_FUNCTIONS)

    def test_each_argument_choice_offers_exactly_its_functions_set(self):
        questions = get_experiment(ROUTING).cases()[0].questions
        for function in ROUTING_FUNCTIONS:
            question = questions[ROUTING_ARGUMENT_QUESTION[function]]
            assert set(question.criteria) == set(ROUTING_ARGUMENTS[function])

    def test_every_argument_label_has_a_description(self):
        # The keys and the schema are two separate literals; nothing but this test holds them
        # together, so a label added to one and forgotten in the other would reach the wire with no
        # description.
        labels = {label for values in ROUTING_ARGUMENTS.values() for label in values}
        assert set(ROUTING_ARGUMENT_CRITERIA) == labels
        assert set(ROUTING_ARGUMENT_INSTRUCTIONS) == set(ROUTING_FUNCTIONS)

    def test_the_experiment_is_registered_with_its_digest(self):
        assert ROUTING in experiment_names()
        assert get_experiment(ROUTING).digest is routing_digest

    def test_the_ceiling_matches_the_tier_it_declares(self):
        experiment = get_experiment(ROUTING)
        assert experiment.tier == "extended"
        assert experiment_call_ceiling(experiment) == len(experiment.cases())


class TestTheFrozenRegistry:
    """Section B: four names, closed, no fallback, no run-time construction."""

    def test_the_registry_holds_the_four_declared_functions(self):
        assert list(ROUTING_FUNCTIONS) == [
            "inspect_residuals",
            "compare_runs",
            "request_more_evidence",
            "escalate_for_review",
        ]
        assert set(HANDLERS) == set(ROUTING_FUNCTIONS)
        assert set(ROUTING_ARGUMENTS) == set(ROUTING_FUNCTIONS)
        assert set(ROUTING_ARGUMENT_NAME) == set(ROUTING_FUNCTIONS)
        assert set(ROUTING_ARGUMENT_QUESTION) == set(ROUTING_FUNCTIONS)

    def test_each_registry_entry_is_the_module_function_of_that_name(self):
        for name, handler in HANDLERS.items():
            assert handler.__name__ == name
            assert handler.__module__.endswith("routing")

    def test_every_function_has_a_closed_set_of_at_least_two_arguments(self):
        for function, labels in ROUTING_ARGUMENTS.items():
            assert len(labels) >= 2, function
            assert len(set(labels)) == len(labels), function

    def test_argument_labels_are_unique_across_functions(self):
        # A label that belonged to two functions would make a per-function mismatch ambiguous: the
        # same string would be legal for one route and illegal for another.
        labels = [label for values in ROUTING_ARGUMENTS.values() for label in values]
        assert len(labels) == len(set(labels))

    def test_the_argument_schema_is_not_a_single_flat_set(self):
        # If every function accepted every label, the second layer would carry no information and
        # the routing decision would be one enumerated Choice wearing two questions.
        sets = [set(values) for values in ROUTING_ARGUMENTS.values()]
        assert all(len(values) < len({label for s in sets for label in s}) for values in sets)

    def test_an_unknown_function_has_no_arguments(self):
        assert not argument_allowed("no_such_function", "global")
        try:
            arguments_for("no_such_function")
        except KeyError:
            return
        raise AssertionError("an unknown function must not have an argument set")

    def test_argument_matching_is_exact(self):
        # No case folding, no prefix, no nearest neighbour: a label is in the set or the case stops.
        allowed = ROUTING_ARGUMENTS["inspect_residuals"]
        assert argument_allowed("inspect_residuals", "global")
        for near in ("Global", "global ", " glob", "globals", "global_region", ""):
            assert not argument_allowed("inspect_residuals", near), near

    def test_a_label_from_another_functions_set_is_not_accepted(self):
        assert not argument_allowed("compare_runs", "global")
        assert not argument_allowed("escalate_for_review", "diagnostic_plot")

    def test_non_string_labels_are_not_accepted(self):
        for value in (None, 3, 0.5, True, ["global"], {"region": "global"}):
            assert not argument_allowed("inspect_residuals", value), value

    def test_a_run_does_not_mutate_the_registry(self):
        before = dict(HANDLERS)
        run_offline()
        assert HANDLERS == before
        assert set(HANDLERS) == set(ROUTING_FUNCTIONS)


class TestThePayload:
    """Section P: what actually goes on the wire, checked through the real SDK encoder."""

    def test_the_four_requests_differ_only_in_the_state(self):
        bodies, _ = run_offline()
        assert len(bodies) == 4
        assert {json.dumps(body["questions"], sort_keys=True) for body in bodies} == {
            json.dumps(bodies[0]["questions"], sort_keys=True)
        }
        assert len({json.dumps(body["state"]) for body in bodies}) == 4

    def test_the_request_carries_nothing_but_state_and_questions(self):
        bodies, _ = run_offline()
        for body in bodies:
            assert sorted(body) == ["model", "questions", "state"]

    def test_the_registry_is_present_only_as_the_routing_choices_labels(self):
        bodies, _ = run_offline()
        body = bodies[0]
        assert set(body["questions"][ROUTING_FUNCTION_QUESTION]["criteria"]) == set(HANDLERS)
        # Nowhere else: the criteria *values* are descriptions, and no name appears in the state.
        blob = json.dumps(body["state"])
        for name in ROUTING_FUNCTIONS:
            assert name not in blob, name

    def test_the_expected_label_is_not_in_the_payload(self):
        bodies, _ = run_offline()
        for body in bodies:
            case_id = state_of(body)
            function, argument = EXPECTED[case_id]
            blob = json.dumps(body["state"])
            assert function not in blob
            assert argument not in blob
            assert case_id not in json.dumps(body)
            assert "expected" not in json.dumps(body)

    def test_no_local_provenance_reaches_the_wire(self):
        bodies, _ = run_offline()
        blob = json.dumps(bodies[0])
        for leaked in ("case_id", "notes", "run_id", "timestamp", "expected_", "suppress"):
            assert leaked not in blob, leaked

    def test_the_wire_body_carries_no_credential(self):
        bodies, _ = run_offline()
        assert DUMMY_KEY not in json.dumps(bodies[0])
        assert "api_key" not in json.dumps(bodies[0]).lower()

    def test_the_same_question_objects_produce_the_same_questions_every_time(self):
        first, _ = run_offline()
        second, _ = run_offline()
        assert json.dumps(first[0]["questions"], sort_keys=True) == json.dumps(
            second[0]["questions"], sort_keys=True
        )


class TestSelection:
    """Sections A, I and M: the default run routes where the scenario intends."""

    def test_every_case_selects_its_expected_function_and_argument(self):
        _, records = run_offline()
        analysis = analyze_routing(records)
        assert analysis["matched_count"] == 4
        assert analysis["argument_matched_count"] == 4
        for case in analysis["cases"]:
            assert case["selected_function"] == EXPECTED[case["case_id"]][0]

    def test_the_selected_argument_carries_the_functions_own_keyword(self):
        _, records = run_offline()
        for case_id, (function, argument) in EXPECTED.items():
            decision = _decision(records, case_id)
            assert decision["selected_arguments"] == {
                ROUTING_ARGUMENT_NAME[function]: argument
            }

    def test_the_handler_result_comes_from_python(self):
        _, records = run_offline()
        for case_id, (function, _) in EXPECTED.items():
            decision = _decision(records, case_id)
            if not decision["handler_called"]:
                continue
            expected = HANDLERS[function](EXPECTED[case_id][1])
            assert decision["handler_result"] == expected
            assert decision["handler_result"]["side_effect"] is False
            assert decision["handler_result"]["executed"] is True

    def test_the_stored_result_equals_the_handlers_own_return_value(self):
        _, records = run_offline()
        for record in records:
            derived = record["notes"]["derived"]
            if derived["handler_called"]:
                assert derived["handler_result"] == HANDLERS[derived["selected_function"]](
                    next(iter(derived["selected_arguments"].values()))
                )

    def test_the_outcome_names_what_python_did(self):
        _, records = run_offline()
        outcomes = [case["outcome"] for case in analyze_routing(records)["cases"]]
        assert set(outcomes) <= {OUTCOME_EXECUTED, OUTCOME_HUMAN_REVIEW, OUTCOME_ROUTE_UNAVAILABLE}
        assert outcomes.count(OUTCOME_EXECUTED) == 3
        assert outcomes.count(OUTCOME_HUMAN_REVIEW) == 1


class TestFailClosed:
    """Section J: no route, no argument, or an unusable label stops the case."""

    @staticmethod
    def _unavailable(records, case_id):
        return route_decision(_by_case(records, case_id))

    def test_a_missing_routing_answer_stops_the_case(self):
        records = _with_answer(_copy(run_offline()[1]), "oscillating_error",
                               ROUTING_FUNCTION_QUESTION, None)
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert decision["handler_called"] is False
        assert decision["selected_function"] is None
        assert "missing" in decision["unavailable_reason"]

    def test_a_routing_answer_of_the_wrong_primitive_stops_the_case(self):
        records = _with_answer(
            _copy(run_offline()[1]),
            "oscillating_error",
            ROUTING_FUNCTION_QUESTION,
            {"type": "noul", "noul": 0.9},
        )
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert "not a `choice`" in decision["unavailable_reason"]

    def test_an_unknown_function_label_stops_the_case(self):
        records = _with_field(
            _copy(run_offline()[1]), "oscillating_error", ROUTING_FUNCTION_QUESTION,
            "choice", "inspect_residual",
        )
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert "not a name in the frozen registry" in decision["unavailable_reason"]
        assert decision["handler_called"] is False

    def test_a_label_that_looks_like_a_call_is_not_routed(self):
        # The nearest name is not taken, and neither is anything that could be a call site.
        for label in (
            "inspect_residuals()",
            "routing.inspect_residuals",
            "__import__('os').system('echo hi')",
            "inspect_residuals; import os",
        ):
            records = _with_field(
                _copy(run_offline()[1]), "oscillating_error",
                ROUTING_FUNCTION_QUESTION, "choice", label,
            )
            decision = self._unavailable(records, "oscillating_error")
            assert decision["available"] is False, label
            assert decision["handler_called"] is False, label

    def test_a_non_string_function_label_stops_the_case(self):
        for value in (None, 7, ["inspect_residuals"], {"name": "inspect_residuals"}):
            records = _with_field(
                _copy(run_offline()[1]), "oscillating_error",
                ROUTING_FUNCTION_QUESTION, "choice", value,
            )
            assert self._unavailable(records, "oscillating_error")["available"] is False, value

    def test_a_missing_argument_answer_stops_the_case(self):
        question = ROUTING_ARGUMENT_QUESTION["inspect_residuals"]
        records = _with_answer(_copy(run_offline()[1]), "oscillating_error", question, None)
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert "argument answer" in decision["unavailable_reason"]
        assert question in decision["unavailable_reason"]

    def test_an_argument_answer_of_the_wrong_primitive_stops_the_case(self):
        question = ROUTING_ARGUMENT_QUESTION["inspect_residuals"]
        records = _with_answer(
            _copy(run_offline()[1]), "oscillating_error", question, {"type": "score", "score": 1.5}
        )
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert "not a `choice`" in decision["unavailable_reason"]

    def test_an_argument_outside_the_functions_set_stops_the_case(self):
        question = ROUTING_ARGUMENT_QUESTION["inspect_residuals"]
        records = _with_field(
            _copy(run_offline()[1]), "oscillating_error", question, "choice", "boundary_of_domain"
        )
        decision = self._unavailable(records, "oscillating_error")
        assert decision["available"] is False
        assert "not in the frozen set" in decision["unavailable_reason"]
        assert decision["handler_called"] is False

    def test_an_argument_belonging_to_another_function_stops_the_case(self):
        # `resolution` is a legal label for `compare_runs` and not for `inspect_residuals`. Passing
        # it through would mean the per-function sets were decoration.
        question = ROUTING_ARGUMENT_QUESTION["inspect_residuals"]
        records = _with_field(
            _copy(run_offline()[1]), "oscillating_error", question, "choice", "resolution"
        )
        assert self._unavailable(records, "oscillating_error")["available"] is False

    def test_an_unavailable_case_leaves_nothing_behind(self):
        records = _with_answer(
            _copy(run_offline()[1]), "refinement_difference", ROUTING_FUNCTION_QUESTION, None
        )
        decision = self._unavailable(records, "refinement_difference")
        assert decision["handler_result"] is None
        assert decision["execution_suppressed"] is False
        assert decision["selected_arguments"] == {}
        assert decision["argument_answers_consumed"] == []
        assert decision["argument_answers_unused"] == list(ROUTING_ARGUMENT_QUESTIONS)
        assert decision["markers"] == [FUNCTION_ROUTE_UNAVAILABLE]

    def test_one_unavailable_case_does_not_stop_the_others(self):
        records = _with_answer(
            _copy(run_offline()[1]), "refinement_difference", ROUTING_FUNCTION_QUESTION, None
        )
        analysis = analyze_routing(records)
        assert analysis["unavailable_count"] == 1
        assert analysis["resolved_count"] == 3
        assert analysis["executed_count"] == 2
        assert FUNCTION_ROUTE_UNAVAILABLE in analysis["markers"]

    def test_no_mismatch_marker_is_claimed_while_a_case_is_unavailable(self):
        # "Three of three matched" is not "four of four matched", and an unrouted case is not a
        # disagreement with the expectation either.
        records = _with_answer(
            _copy(run_offline()[1]), "refinement_difference", ROUTING_FUNCTION_QUESTION, None
        )
        markers = analyze_routing(records)["markers"]
        assert FUNCTION_ROUTE_UNAVAILABLE in markers
        assert ROUTING_EXPECTED_FUNCTIONS_OBSERVED not in markers
        assert ROUTING_FUNCTION_MISMATCH_OBSERVED not in markers

    def test_an_unavailable_record_stores_the_reason(self):
        _, records = run_offline()
        mutated = _with_answer(records, "oscillating_error", ROUTING_FUNCTION_QUESTION, None)
        case = get_experiment(ROUTING).cases()[0]
        derived = routing_digest(case, _response_for(_by_case(mutated, "oscillating_error")))
        assert derived["outcome"] == OUTCOME_ROUTE_UNAVAILABLE
        assert derived["handler_called"] is False
        assert "route_unavailable_reason" in derived
        assert "selected_function" not in derived

    def test_an_empty_record_renders_as_unavailable(self):
        text = "\n".join(build_routing_block([{"case_id": "empty", "answers": {}}]))
        assert FUNCTION_ROUTE_UNAVAILABLE in text
        assert "no handler called" in text

    def test_no_record_means_no_block(self):
        assert build_routing_block([]) == []


class TestTheHumanReviewPolicy:
    """Section H: the frozen policy, and the fact that it can only withhold."""

    def test_the_default_run_suppresses_the_case_written_for_review(self):
        _, records = run_offline()
        decision = _decision(records, "out_of_range_values")
        assert decision["execution_suppressed"] is True
        assert decision["handler_called"] is False
        assert decision["outcome"] == OUTCOME_HUMAN_REVIEW
        assert "threshold" in decision["suppression_reason"]

    def test_the_case_written_for_review_is_the_one_suppressed(self):
        _, records = run_offline()
        analysis = analyze_routing(records)
        assert analysis["suppression_expected_count"] == 1
        assert analysis["suppression_expected_hit"] == 1
        assert analysis["unexpected_suppression_count"] == 0
        assert analysis["unrealized_suppression_count"] == 0
        assert ROUTING_SUPPRESSION_EXPECTATION_MET in analysis["markers"]
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED not in analysis["markers"]

    def test_an_expectation_that_did_not_happen_is_reported_as_missed(self):
        # The case written to need review runs: the expectation was missed in the other direction.
        _, records = run_offline(reviews={name: 0.05 for name in EXPECTED})
        analysis = analyze_routing(records)
        assert analysis["suppressed_count"] == 0
        assert analysis["unrealized_suppression_count"] == 1
        assert analysis["unrealized_suppression_cases"] == ["out_of_range_values"]
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED in analysis["markers"]
        assert ROUTING_SUPPRESSION_EXPECTATION_MET not in analysis["markers"]

    def test_a_case_suppressed_though_it_was_not_expected_to_be_is_missed(self):
        # The direction the old marker pair could not see: a routine scenario withheld anyway.
        _, records = run_offline(reviews={"oscillating_error": 0.9})
        analysis = analyze_routing(records)
        assert analysis["unexpected_suppression_count"] == 1
        assert analysis["unexpected_suppression_cases"] == ["oscillating_error"]
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED in analysis["markers"]

    def test_a_confidence_below_the_floor_suppresses(self):
        _, records = run_offline(
            confidences={"oscillating_error": ROUTING_CONFIDENCE_FLOOR - 0.01}
        )
        decision = _decision(records, "oscillating_error")
        assert decision["execution_suppressed"] is True
        assert decision["handler_called"] is False
        assert "confidence" in decision["suppression_reason"]
        assert decision["selected_function"] == "inspect_residuals"

    def test_a_confidence_exactly_at_the_floor_executes(self):
        # The floor is inclusive: the boundary is `>=`, and a test that did not pin it would let an
        # off-by-one at the edge through.
        _, records = run_offline(
            confidences={"oscillating_error": ROUTING_CONFIDENCE_FLOOR}
        )
        assert _decision(records, "oscillating_error")["handler_called"] is True

    def test_a_review_probability_at_the_threshold_suppresses(self):
        _, records = run_offline(
            reviews={**DEFAULT_REVIEW, "oscillating_error": ROUTING_HUMAN_REVIEW_THRESHOLD}
        )
        assert _decision(records, "oscillating_error")["execution_suppressed"] is True

    def test_a_review_probability_just_below_the_threshold_executes(self):
        _, records = run_offline(
            reviews={**DEFAULT_REVIEW, "oscillating_error": ROUTING_HUMAN_REVIEW_THRESHOLD - 0.01}
        )
        assert _decision(records, "oscillating_error")["handler_called"] is True

    def test_a_missing_confidence_suppresses_rather_than_passing(self):
        records = _with_field(
            _copy(run_offline()[1]), "oscillating_error",
            ROUTING_FUNCTION_QUESTION, "confidence", None,
        )
        decision = _decision(records, "oscillating_error")
        assert decision["available"] is True
        assert decision["execution_suppressed"] is True
        assert "confidence was not recorded" in decision["suppression_reason"]

    def test_a_missing_review_answer_suppresses_rather_than_passing(self):
        records = _with_answer(
            _copy(run_offline()[1]), "oscillating_error", ROUTING_REVIEW_QUESTION, None
        )
        decision = _decision(records, "oscillating_error")
        assert decision["execution_suppressed"] is True
        assert "needs_human_review` was not recorded" in decision["suppression_reason"]

    def test_a_review_answer_of_the_wrong_primitive_suppresses(self):
        records = _with_answer(
            _copy(run_offline()[1]),
            "oscillating_error",
            ROUTING_REVIEW_QUESTION,
            {"type": "choice", "choice": "no", "confidence": 0.9, "probabilities": {"no": 0.9}},
        )
        assert _decision(records, "oscillating_error")["execution_suppressed"] is True

    def test_a_non_numeric_review_probability_suppresses(self):
        for value in (None, "0.1", True, float("nan")):
            records = _with_answer(
                _copy(run_offline()[1]),
                "oscillating_error",
                ROUTING_REVIEW_QUESTION,
                {"type": "noul", "noul": value},
            )
            assert _decision(records, "oscillating_error")["execution_suppressed"] is True, value

    def test_suppression_still_reports_the_route_it_declined(self):
        _, records = run_offline()
        decision = _decision(records, "out_of_range_values")
        assert decision["selected_function"] == "escalate_for_review"
        assert decision["selected_arguments"] == {"reason": "unphysical_values"}
        assert decision["matches_expected_function"] is True

    def test_the_policy_never_selects_a_function_of_its_own(self):
        _, records = run_offline()
        analysis = analyze_routing(records)
        selected = {
            case["case_id"]: case["selected_function"]
            for case in analysis["cases"]
            if case["available"]
        }
        assert selected == {case_id: fn for case_id, (fn, _) in EXPECTED.items()}
        # And in the suppressed case the handler is simply not called: nothing takes its place.
        assert analysis["cases"][3]["handler_result"] is None


class TestTheHandlersAreInert:
    """Sections I and Q: the handlers do nothing, and nothing else can be reached."""

    def test_every_handler_returns_a_fixed_dict(self):
        for function, handler in HANDLERS.items():
            label = ROUTING_ARGUMENTS[function][0]
            result = handler(label)
            assert set(result) == {"handler", ROUTING_ARGUMENT_NAME[function], "executed",
                                   "side_effect"}
            assert result["handler"] == function
            assert result["executed"] is True
            assert result["side_effect"] is False

    def test_a_handler_is_pure(self):
        for function, handler in HANDLERS.items():
            label = ROUTING_ARGUMENTS[function][0]
            assert handler(label) == handler(label)

    def test_the_handler_result_keys_are_the_functions_own(self):
        _, records = run_offline()
        for record in records:
            result = record["notes"]["derived"].get("handler_result")
            if result is None:
                continue
            assert set(result) == {
                "handler",
                ROUTING_ARGUMENT_NAME[result["handler"]],
                "executed",
                "side_effect",
            }

    def test_a_run_writes_no_file_but_the_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)

            def handler(request):
                return httpx2.Response(
                    200, json=reply_for(request.content),
                    headers={"x-typesafe-request-id": REQUEST_ID},
                )

            client = TypeSafeClient(api_key=DUMMY_KEY, transport=httpx2.MockTransport(handler))
            with client:
                run_experiment(
                    get_experiment(ROUTING),
                    client=client,
                    recorder=UsageRecorder(root),
                    model="jev-latest",
                )
            assert sorted(entry.name for entry in root.iterdir()) == ["usage.jsonl"]

    def test_the_mock_is_the_only_network_path(self):
        # Four bodies for four calls: the four handlers ran without a fifth request.
        bodies, records = run_offline()
        assert len(bodies) == 4
        assert len(records) == 4

    def test_the_module_cannot_reach_outside_itself(self):
        """The dispatch path is read as a syntax tree, not as text.

        A substring scan would be answered by the module's own prose, which discusses subprocesses
        precisely in order to say it has none. The tree says what the code can actually do: no call
        to `eval`, `exec`, `compile`, `__import__`, or `open`, and no import of anything that can
        open a socket, a pipe, or a file.
        """
        import ast

        import jev_lab.routing as module

        tree = ast.parse(pathlib.Path(module.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                    "open",
                }, node.func.id
            if isinstance(node, ast.Attribute):
                assert node.attr not in {"system", "popen", "spawn", "run"}, node.attr
            if isinstance(node, ast.Name):
                assert node.id not in {"eval", "exec", "compile", "__import__"}, node.id
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        assert imported <= {
            "collections",  # collections.abc, for the type annotations
            "typing",  # TYPE_CHECKING and Any
            "repeatability",  # the relative `.repeatability`
            "recorder",  # the relative `.recorder`, imported lazily inside the digest
            "typesafe_sdk",  # a type-checking import only
        }, sorted(imported)


class TestNothingTheModelReturnsIsExecuted:
    """Section A: the answer is a key or it is a reason, and never code."""

    def test_the_selected_function_is_always_a_registry_key(self):
        _, records = run_offline()
        for case in analyze_routing(records)["cases"]:
            if case["available"]:
                assert case["selected_function"] in HANDLERS

    def test_a_label_the_registry_lacks_is_never_created(self):
        records = _with_field(
            _copy(run_offline()[1]), "oscillating_error",
            ROUTING_FUNCTION_QUESTION, "choice", "delete_everything",
        )
        decision = _decision(records, "oscillating_error")
        assert decision["available"] is False
        assert "delete_everything" not in HANDLERS
        assert decision["handler_result"] is None

    def test_the_argument_value_reaches_the_handler_as_a_string(self):
        _, records = run_offline()
        for case in analyze_routing(records)["cases"]:
            if case["handler_called"]:
                value = next(iter(case["selected_arguments"].values()))
                assert isinstance(value, str)

    def test_the_handler_is_called_with_the_label_not_the_answer_object(self):
        seen = []
        for function, handler in HANDLERS.items():
            label = ROUTING_ARGUMENTS[function][1]
            assert handler(label) == {
                "handler": function,
                ROUTING_ARGUMENT_NAME[function]: label,
                "executed": True,
                "side_effect": False,
            }
            seen.append(function)
        assert len(seen) == len(ROUTING_FUNCTIONS)


class TestConfidenceIsNotCorrectness:
    """Sections F, G and N: the two are reported side by side, never combined."""

    def test_a_confident_wrong_route_is_recorded_as_wrong(self):
        _, records = run_offline(
            routes={**EXPECTED, "refinement_difference": ("escalate_for_review", "resource_limit")},
            confidences={"refinement_difference": 0.99},
        )
        decision = _decision(records, "refinement_difference")
        assert decision["matches_expected_function"] is False
        assert decision["confidence"] == 0.99
        assert decision["handler_called"] is True

    def test_a_low_confidence_correct_route_is_recorded_as_correct(self):
        _, records = run_offline(confidences={"oscillating_error": 0.55})
        decision = _decision(records, "oscillating_error")
        assert decision["matches_expected_function"] is True
        assert decision["confidence"] == 0.55

    def test_changing_every_confidence_changes_no_expected_label(self):
        _, records = run_offline()
        before = [
            (case["expected_function"], case["expected_argument"])
            for case in analyze_routing(records)["cases"]
        ]
        mutated = records
        for case_id in EXPECTED:
            mutated = _with_field(
                mutated, case_id, ROUTING_FUNCTION_QUESTION, "confidence", 0.01
            )
        after = [
            (case["expected_function"], case["expected_argument"])
            for case in analyze_routing(mutated)["cases"]
        ]
        assert before == after

    def test_a_wrong_route_is_reported_not_retried(self):
        _, records = run_offline(
            routes={**EXPECTED, "oscillating_error": ("compare_runs", "seed")}
        )
        analysis = analyze_routing(records)
        assert analysis["matched_count"] == 3
        assert analysis["argument_matched_count"] == 3
        assert ROUTING_FUNCTION_MISMATCH_OBSERVED in analysis["markers"]
        assert ROUTING_EXPECTED_FUNCTIONS_OBSERVED not in analysis["markers"]
        # Four calls in, four calls out: a disagreement does not buy a second attempt.
        assert analysis["calls"] == 4

    def test_the_margin_is_the_gap_between_the_top_two(self):
        bodies, records = run_offline()
        decision = _decision(records, "oscillating_error")
        probabilities = decision["probabilities"]
        ranked = sorted(probabilities.values(), reverse=True)
        assert decision["margin"] == ranked[0] - ranked[1]
        assert decision["dominant_probability"] == ranked[0]

    def test_a_tie_produces_a_zero_margin_rather_than_a_coin_flip(self):
        tied = {name: 0.25 for name in ALL_FUNCTIONS}
        records = _with_answer(
            _copy(run_offline()[1]),
            "oscillating_error",
            ROUTING_FUNCTION_QUESTION,
            {"type": "choice", "choice": "inspect_residuals", "confidence": 0.9,
             "probabilities": tied},
        )
        decision = _decision(records, "oscillating_error")
        assert decision["margin"] == 0.0
        assert decision["selected_function"] == "inspect_residuals"

    def test_a_single_entry_distribution_has_no_margin(self):
        records = _with_answer(
            _copy(run_offline()[1]),
            "oscillating_error",
            ROUTING_FUNCTION_QUESTION,
            {"type": "choice", "choice": "inspect_residuals", "confidence": 0.9,
             "probabilities": {"inspect_residuals": 1.0}},
        )
        assert _decision(records, "oscillating_error")["margin"] is None

    def test_the_report_keeps_the_full_distribution(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "### Routing distributions" in text
        for name in ALL_FUNCTIONS:
            assert f"`{name}`" in text


class TestTheSpeculativeArguments:
    """Section K: what was asked, what was consumed, what was not."""

    def test_every_case_asks_every_argument_question(self):
        _, records = run_offline()
        for record in records:
            derived = record["notes"]["derived"]
            assert derived["argument_questions_asked"] == list(ROUTING_ARGUMENT_QUESTIONS)

    def test_only_the_selected_functions_argument_is_consumed(self):
        _, records = run_offline()
        for case_id, (function, _) in EXPECTED.items():
            decision = _decision(records, case_id)
            assert decision["argument_answers_consumed"] == [
                ROUTING_ARGUMENT_QUESTION[function]
            ]
            assert len(decision["argument_answers_unused"]) == len(ROUTING_FUNCTIONS) - 1

    def test_an_unused_answer_cannot_reach_the_dispatch(self):
        # The other three questions are answered with a legal label for *their* function. None of
        # them may appear in the argument the handler is called with.
        _, records = run_offline()
        for case_id, (function, argument) in EXPECTED.items():
            decision = _decision(records, case_id)
            name, value = next(iter(decision["selected_arguments"].items()))
            assert name == ROUTING_ARGUMENT_NAME[function]
            assert value == argument

    def test_the_unused_answers_are_counted_not_costed(self):
        _, records = run_offline()
        decision = _decision(records, "oscillating_error")
        assert len(decision["argument_answers_unused"]) == 3
        text = "\n".join(build_routing_block(records))
        assert "cost of the unused answers is not decomposed" in text
        assert "not separable" in text


class TestTheDerivedAnalysis:
    """The post-run derivation: both gates separately, the expectation compared both ways, and
    which part of the chain the run actually reached.

    These are report-time computations over the records, not stored fields. The stored
    `suppression_reason` names the first gate that failed, so a report that read only that would
    describe a case withheld by two gates as though one threshold were all that stood in its way.
    """

    def test_both_gates_are_evaluated_independently(self):
        _, records = run_offline(confidences={"oscillating_error": 0.1})
        decision = _decision(records, "oscillating_error")
        assert decision["confidence_gate_pass"] is False
        # The review signal for this case is below the threshold, so that gate passes on its own.
        assert decision["review_gate_pass"] is True
        assert decision["execution_allowed"] is False

    def test_a_case_can_fail_the_review_gate_while_passing_the_floor(self):
        _, records = run_offline(reviews={"oscillating_error": 0.99})
        decision = _decision(records, "oscillating_error")
        assert decision["confidence_gate_pass"] is True
        assert decision["review_gate_pass"] is False
        assert decision["execution_allowed"] is False
        # The stored field names the one condition it stopped at -- here the review threshold,
        # since the floor passed. It never names both.
        assert "threshold" in decision["suppression_reason"]

    def test_execution_is_allowed_only_when_both_gates_pass(self):
        _, records = run_offline()
        allowed = [case for case in analyze_routing(records)["cases"] if case["execution_allowed"]]
        assert [case["case_id"] for case in allowed] == ["oscillating_error", "refinement_difference", "unchecked_result"]

    def test_the_gate_counts_separate_the_two_failure_modes(self):
        # One case fails only the floor, one fails only the review gate, one fails both, and the
        # fourth passes both and runs. The two gates are moved independently, which is the whole
        # point: a single stored reason can only ever name one of the three suppressed cases.
        _, records = run_offline(
            confidences={"oscillating_error": 0.1, "out_of_range_values": 0.1},
            reviews={"refinement_difference": 0.99},
        )
        analysis = analyze_routing(records)
        assert analysis["withheld_by_confidence_alone_count"] == 1  # oscillating_error
        assert analysis["withheld_by_review_alone_count"] == 1  # refinement_difference
        assert analysis["withheld_by_both_gates_count"] == 1  # out_of_range_values
        assert analysis["executed_count"] == 1  # unchecked_result

    def test_a_missing_input_is_not_a_failed_gate(self):
        # Not recorded and failed are different, and the policy suppresses either way.
        records = _with_answer(run_offline()[1], "oscillating_error", ROUTING_FUNCTION_QUESTION, None)
        decision = _decision(records, "oscillating_error")
        assert decision["available"] is False
        assert decision["confidence_gate_pass"] is None
        assert decision["review_gate_pass"] is None
        assert decision["execution_allowed"] is None

    def test_a_missing_confidence_suppresses_without_claiming_a_gate_failed(self):
        records = _with_field(
            run_offline()[1], "oscillating_error", ROUTING_FUNCTION_QUESTION, "confidence", None
        )
        decision = _decision(records, "oscillating_error")
        assert decision["confidence_gate_pass"] is None
        assert decision["review_gate_pass"] is True
        assert decision["execution_allowed"] is False
        assert decision["execution_suppressed"] is True

    def test_the_run_that_executes_nothing_says_the_branch_is_untested(self):
        _, records = run_offline(reviews={name: 0.9 for name in EXPECTED})
        analysis = analyze_routing(records)
        assert analysis["executed_count"] == 0
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED in analysis["markers"]
        assert ACTUAL_HANDLER_EXECUTION_REALIZED not in analysis["markers"]
        text = "\n".join(build_routing_block(records))
        assert "not a full execution-chain result" in text.lower()
        assert "never entered" in text

    def test_a_run_that_executes_something_says_the_branch_was_reached(self):
        _, records = run_offline()
        analysis = analyze_routing(records)
        assert analysis["executed_count"] == 3
        assert ACTUAL_HANDLER_EXECUTION_REALIZED in analysis["markers"]
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED not in analysis["markers"]

    def test_fail_closed_is_reported_when_nothing_ran_for_a_withheld_route(self):
        _, records = run_offline(reviews={name: 0.9 for name in EXPECTED})
        analysis = analyze_routing(records)
        assert analysis["suppressed_count"] == 4
        assert FAIL_CLOSED_SUPPRESSION_REALIZED in analysis["markers"]

    def test_fail_closed_is_not_claimed_when_nothing_was_withheld(self):
        _, records = run_offline(reviews={name: 0.05 for name in EXPECTED})
        assert FAIL_CLOSED_SUPPRESSION_REALIZED not in analyze_routing(records)["markers"]

    def test_the_classifications_follow_the_records(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "**FUNCTION_TARGET_REALIZED**" in text
        assert "**ARGUMENT_TARGET_REALIZED**" in text
        assert "FUNCTION_TARGET_NOT_REALIZED" not in text
        assert f"**{ROUTING_SUPPRESSION_EXPECTATION_MET}**" in text
        assert f"**{ACTUAL_HANDLER_EXECUTION_REALIZED}**" in text

    def test_a_target_that_was_not_realized_is_named_as_such(self):
        _, records = run_offline(routes={"oscillating_error": ("compare_runs", "resolution")})
        text = "\n".join(build_routing_block(records))
        assert "**FUNCTION_TARGET_NOT_REALIZED**" in text
        assert "**FUNCTION_TARGET_REALIZED**" not in text
        assert f"**{ROUTING_SUPPRESSION_EXPECTATION_MET}**" in text  # suppression still as designed

    def test_the_gate_table_renders_a_row_per_case(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "### Gate decomposition" in text
        assert "### Expected suppression versus observed" in text
        assert "### Handler execution" in text
        assert "### Classifications" in text
        for case_id in ROUTING_CASE_ORDER:
            assert f"| `{case_id}` |" in text

    def test_the_canonical_run_withheld_every_route_and_no_case_on_the_floor_alone(self):
        # The measurement, re-derived from the log rather than read off the stored reason. If a
        # later edit changed a threshold or a state, this is where it would show up as a different
        # answer to a question the run already settled.
        #
        # The load-bearing count is the zero: `withheld_by_confidence_alone_count == 0` means moving
        # the 0.8 floor would not have executed any of the four routes, because each one either
        # failed the floor *and* the review threshold, or passed the floor and failed the review
        # threshold. The stored reason names one condition per record and cannot show that.
        path = pathlib.Path(DEFAULT_RESULTS_DIR) / "usage.jsonl"
        if not path.exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        records = [
            record for record in read_records(path) if record.get("experiment") == ROUTING
        ]
        assert records
        analysis = analyze_routing(records)
        assert analysis["calls"] == 4
        assert analysis["executed_count"] == 0
        assert analysis["suppressed_count"] == 4
        assert analysis["withheld_by_both_gates_count"] == 3
        assert analysis["withheld_by_review_alone_count"] == 1
        assert analysis["withheld_by_confidence_alone_count"] == 0
        assert [
            case["case_id"]
            for case in analysis["cases"]
            if case["review_gate_pass"] is False and case["confidence_gate_pass"] is True
        ] == ["out_of_range_values"]
        assert analysis["unexpected_suppression_count"] == 3
        assert analysis["unrealized_suppression_count"] == 0
        assert ACTUAL_HANDLER_EXECUTION_UNTESTED in analysis["markers"]
        assert ROUTING_SUPPRESSION_EXPECTATION_MISSED in analysis["markers"]


class TestTheRecordAndItsDerived:
    """Sections I and M: raw and derived provenance, both in the canonical record."""

    def test_the_raw_answers_are_stored(self):
        _, records = run_offline()
        assert set(records[0]["answers"][ROUTING_FUNCTION_QUESTION]) >= {
            "type", "choice", "confidence", "probabilities",
        }
        assert records[0]["answers"][ROUTING_REVIEW_QUESTION]["type"] == "noul"

    def test_the_decision_is_stored_beside_the_answers(self):
        _, records = run_offline()
        derived = records[0]["notes"]["derived"]
        assert set(derived) >= {
            "expected_function",
            "expected_argument",
            "expects_suppression",
            "registry",
            "argument_schema",
            "argument_questions_asked",
            "outcome",
            "handler_called",
            "execution_suppressed",
            "suppression_reason",
            "selected_function",
            "selected_arguments",
            "route_confidence",
            "needs_human_review",
            "matches_expected_function",
            "matches_expected_argument",
            "handler_result",
        }

    def test_the_record_carries_the_registry_that_was_in_force(self):
        _, records = run_offline()
        derived = records[0]["notes"]["derived"]
        assert derived["registry"] == list(ROUTING_FUNCTIONS)
        assert derived["argument_schema"] == {
            name: list(values) for name, values in ROUTING_ARGUMENTS.items()
        }

    def test_the_side_effect_note_is_carried(self):
        _, records = run_offline()
        assert records[0]["notes"]["side_effects"] == ROUTING_SIDE_EFFECTS

    def test_the_digest_makes_no_api_call_of_its_own(self):
        # The digest runs inside the recorded call's window, and it calls the handler there. If
        # either called out, the mock would see more than four bodies.
        bodies, _ = run_offline()
        assert len(bodies) == 4

    def test_a_complete_case_stores_the_decision_beside_its_answers(self):
        _, records = run_offline()
        derived = records[0]["notes"]["derived"]
        assert derived["outcome"] == OUTCOME_EXECUTED
        assert derived["matches_expected_function"] is True
        assert derived["selected_function"] == "inspect_residuals"

    def test_records_without_notes_still_render(self):
        _, records = run_offline()
        stripped = []
        for record in _copy(records):
            record.pop("notes", None)
            stripped.append(record)
        text = "\n".join(build_routing_block(stripped))
        assert text.count("### Routes") == 1

    def test_the_snapshot_includes_the_section(self):
        from jev_lab.snapshot import build_snapshot

        _, records = run_offline()
        text = build_snapshot(list(records))
        assert f"## `{ROUTING}`" in text
        assert "### Frozen registry" in text
        assert "### Frozen human-review policy" in text

    def test_the_canonical_log_holds_this_experiment_s_run(self):
        # A guard on the append-only log, now that the run has happened. The 38 lines that existed
        # before it are pinned by hash: an *append* leaves them alone, so if this fails, something
        # rewrote history rather than added to it. The hash is of the exact bytes on this machine,
        # and the log is deliberately not versioned, hence the skip.
        path = pathlib.Path(DEFAULT_RESULTS_DIR) / "usage.jsonl"
        if not path.exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) >= 38 + len(ROUTING_CASE_ORDER)
        prefix = hashlib.sha256(("\n".join(lines[:38]) + "\n").encode("utf-8")).hexdigest()
        assert prefix == PRE_RUN_PREFIX_SHA256

        routing = [json.loads(line) for line in lines if json.loads(line).get("experiment") == ROUTING]
        assert len(routing) >= len(ROUTING_CASE_ORDER)
        runs: dict[str, list[str]] = {}
        for record in routing:
            runs.setdefault(record["run_id"], []).append(record["case_id"])
        assert list(ROUTING_CASE_ORDER) in runs.values()
        assert all(record["status"] == "ok" for record in routing)
        assert all(record["transport_attempt_count"] == 1 for record in routing)
        assert all(record["transport_retry_count_observed"] == 0 for record in routing)

    def test_the_canonical_log_carries_no_credential(self):
        # The log records what the API returned. Nothing in the request path can put a credential in
        # it, and this checks the shapes that would show up if something did -- without ever reading
        # the key, which cannot be compared against here.
        path = pathlib.Path(DEFAULT_RESULTS_DIR) / "usage.jsonl"
        if not path.exists():
            pytest.skip("no local log on this machine; results/usage.jsonl is not versioned")
        text = path.read_text(encoding="utf-8")
        for shape in ("Bearer", "Authorization", "TYPESAFE_API_KEY", "api_key", "sk-"):
            assert shape not in text

    def test_the_older_records_still_parse(self):
        # The log is append-only across schema bumps, so a reader has to keep reading the versions
        # written before the current one rather than assuming every line shares its shape.
        path = pathlib.Path(DEFAULT_RESULTS_DIR) / "usage.jsonl"
        records = list(read_records(path))
        versions = {record.get("schema_version") for record in records}
        assert versions <= {1, 2, 3}
        assert 3 in versions
        assert all(record.get("experiment") for record in records)
        assert all(record.get("case_id") for record in records)


class TestTheReportSaysWhatItIsNot:
    """Sections F, M and S: counts, never a rate; no verdict about the model."""

    def test_it_reports_counts_on_four_synthetic_cases(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "Functions matched:** 4 of 4 cases" in text
        assert "Arguments matched:** 4 of 4 resolved cases" in text

    def test_it_never_turns_the_counts_into_a_rate(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "not an accuracy" in text
        for forbidden in ("accuracy:", "accuracy rate", "% accuracy", "correct 4/4"):
            assert forbidden not in text.lower()

    def test_it_says_the_expected_routes_are_the_scenarios_own(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "the scenario's intention" in text
        assert "frozen with the states" in text

    def test_it_says_a_route_is_not_a_correctness_result(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "Nothing downstream in this repository acts on a route" in text

    def test_it_says_confidence_is_not_correctness(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "Confidence is not correctness" in text
        assert "never combined" in text

    def test_it_labels_both_thresholds_as_demonstration_parameters(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "are demonstration parameters" in text
        assert "uncalibrated" in text

    def test_it_says_the_handlers_are_inert(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "Every handler is inert" in text
        assert "no change to this project" in text

    def test_it_says_a_stable_label_is_not_a_stable_distribution(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "A stable label is not a stable distribution" in text

    def test_it_makes_no_latency_claim_about_a_route(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records))
        assert "descriptive only" in text
        assert "no such comparison is made" in text
        for forbidden in ("faster than", "slower than", "fastest", "slowest route"):
            assert forbidden not in text.lower()

    def test_it_does_not_retry_or_repair_anything(self):
        _, records = run_offline(
            routes={**EXPECTED, "unchecked_result": ("inspect_residuals", "global")}
        )
        analysis = analyze_routing(records)
        text = "\n".join(build_routing_block(records))
        assert analysis["calls"] == 4
        assert "is not retried" not in text  # the report does not narrate a mechanism it has none of


class TestSecretHygiene:
    def test_no_credential_reaches_the_rendered_block(self):
        _, records = run_offline()
        text = "\n".join(build_routing_block(records)).lower()
        assert DUMMY_KEY.lower() not in text
        assert "api_key" not in text
        assert "authorization" not in text

    def test_an_unexpected_answer_field_is_not_copied_into_the_report(self):
        _, records = run_offline()
        mutated = _copy(records)
        mutated[0]["answers"][ROUTING_FUNCTION_QUESTION]["internal_note"] = "should not surface"
        assert "should not surface" not in "\n".join(build_routing_block(mutated))

    def test_no_record_is_rewritten_by_reading_it(self):
        _, records = run_offline()
        before = json.dumps(records, sort_keys=True)
        build_routing_block(records)
        analyze_routing(records)
        assert json.dumps(records, sort_keys=True) == before


class TestSyntheticStates:
    """Sections E and Q: synthetic, distinct, and stating no answer."""

    def test_the_four_states_are_distinct_and_share_a_domain(self):
        states = list(ROUTING_STATES.values())
        assert len(set(states)) == 4
        for state in states:
            assert state.startswith("Validation record")
            assert "advection-diffusion" in state

    def test_no_state_names_a_function_in_the_registry(self):
        for case_id, state in ROUTING_STATES.items():
            for name in ROUTING_FUNCTIONS:
                assert name not in state, f"{case_id} names {name}"

    def test_no_state_names_an_argument_label(self):
        for case_id, state in ROUTING_STATES.items():
            for values in ROUTING_ARGUMENTS.values():
                for label in values:
                    assert label not in state, f"{case_id} names {label}"

    def test_no_state_tells_the_reader_what_to_do(self):
        for case_id, state in ROUTING_STATES.items():
            lowered = state.lower()
            for word in DIRECTIVE_WORDS:
                assert not re.search(rf"\b{re.escape(word)}", lowered), (
                    f"{case_id} is directive: {word!r}"
                )

    def test_no_state_states_a_verdict_about_the_run(self):
        for case_id, state in ROUTING_STATES.items():
            lowered = state.lower()
            for phrase in ("should be rejected", "must be rejected", "is invalid", "safe to use"):
                assert phrase not in lowered, f"{case_id} states a verdict: {phrase!r}"

    def test_the_states_are_the_only_thing_that_differs(self):
        bodies, _ = run_offline()
        payloads = [json.dumps(body["questions"], sort_keys=True) for body in bodies]
        assert len(set(payloads)) == 1
        assert len({body["state"] for body in bodies}) == 4

    def test_each_expected_route_is_an_element_of_its_frozen_set(self):
        for case_id, function, argument, _ in ROUTING_EXPECTED:
            assert function in ROUTING_FUNCTIONS
            assert argument in ROUTING_ARGUMENTS[function]
            assert case_id in ROUTING_STATES


class TestFirstRequestLatencyOutlier:
    """Section O: latency described, and the opener's position named as the confound."""

    # The four recorded windows, with the opener far the slowest.
    SLOW_OPENER = (1600.0, 400.0, 420.0, 380.0)
    EVEN = (500.0, 520.0, 480.0, 540.0)

    def test_an_outlier_opener_is_reported_with_its_ratio(self):
        records = _with_latency(run_offline()[1], self.SLOW_OPENER)
        analysis = analyze_routing(records)
        assert analysis["first_request_latency"]["is_outlier"] is True
        assert "LATENCY_OUTLIER_OBSERVED" in " ".join(analysis["markers"])
        assert "longest of the four" in "\n".join(build_routing_block(records))

    def test_an_even_session_raises_no_marker(self):
        records = _with_latency(run_offline()[1], self.EVEN)
        analysis = analyze_routing(records)
        assert analysis["first_request_latency"]["is_outlier"] is False
        assert not [m for m in analysis["markers"] if "LATENCY" in m]

    def test_a_missing_latency_makes_the_observation_unavailable(self):
        records = _copy(run_offline()[1])
        records[2]["latency_ms"] = None
        assert analyze_routing(records)["first_request_latency"] == {"available": False}

    def test_the_block_reports_every_latency_including_a_missing_one(self):
        records = _copy(run_offline()[1])
        records[2]["latency_ms"] = None
        text = "\n".join(build_routing_block(records))
        assert "not recorded" in text
