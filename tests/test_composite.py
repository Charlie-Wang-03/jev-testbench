"""`06_composite_scoring`. Offline, driven by the real SDK encoder and synthetic records.

The two load-bearing checks here are the ones the design calls hard rules:

* **Confidence never enters the arithmetic.** Changing every confidence in a record must leave
  every derived value bit-identical. That is checked by mutation, not by reading the source.
* **A malformed dimension fails closed.** Nothing defaults to zero, nothing is dropped, no weight
  is rescaled, and confidence is never substituted for a score.

Everything runs against `httpx2.MockTransport` under the real SDK client, with the same
`TransportProbe` the CLI installs, so the payloads and the attempt counts are the ones a real run
would produce. No test touches the network.
"""

import json
import math
import pathlib
import tempfile

import httpx2
import pytest
from typesafe_sdk import SystemOneResponse, TypeSafeClient
from typesafe_sdk.constants import DEFAULT_TIMEOUT

from jev_lab.client import TransportProbe
from jev_lab.composite import (
    COMPOSITE,
    COMPOSITE_ADVERSE,
    COMPOSITE_BENEFICIAL,
    COMPOSITE_DIMENSIONS,
    COMPOSITE_EXPECTED_ORDER,
    COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED,
    COMPOSITE_EXPECTED_ORDER_OBSERVED,
    COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED,
    COMPOSITE_SCALE_LEVELS,
    COMPOSITE_SCORE_UNAVAILABLE,
    COMPOSITE_TOP_LEVEL,
    COMPOSITE_WEIGHTS,
    analyze_composite,
    build_composite_block,
    case_composite,
    composite_digest,
    composite_of,
    confidence_diagnostics,
    contribution_shares,
    dimension_row,
    normalize,
    probability_diagnostics,
    risk_align,
    weighted_contribution,
    weights_sum,
)
from jev_lab.experiments import (
    COMPOSITE_STATES,
    experiment_call_ceiling,
    experiment_names,
    get_experiment,
    run_experiment,
)
from jev_lab.recorder import UsageRecorder, read_records
from jev_lab.snapshot import build_snapshot

DUMMY_KEY = "not-a-real-key"
REQUEST_ID = "req-composite-0001"

# The scores the mock returns per state, chosen so the scenario's frozen order comes out right for
# a default run: LOW < MIXED < HIGH, with the two ends landing on the formula's endpoints.
DEFAULT_SCORES = {
    "low_risk": {
        "evidence_quality": 3,
        "numerical_stability": 3,
        "reproducibility": 3,
        "failure_severity": 0,
    },
    "mixed": {
        "evidence_quality": 2,
        "numerical_stability": 1,
        "reproducibility": 2,
        "failure_severity": 2,
    },
    "high_risk": {
        "evidence_quality": 0,
        "numerical_stability": 0,
        "reproducibility": 0,
        "failure_severity": 3,
    },
}

# Grading vocabulary. The report is not permitted to grade the scenario against anything, so these
# words may appear only inside the sentence that refuses to use them -- which is why the test below
# checks the surrounding line rather than the whole document.
FORBIDDEN_GRADING = ("accuracy", "calibrat", "ground-truth score", "ground truth score")

# Words that name a mechanism this experiment never varied. None of them may appear in the report.
BLOCKED_BY_DESIGN = (
    "deterministic",
    "non-deterministic",
    "temperature",
    "sampling",
    "seed",
    "random",
)


def _legend():
    return {str(level): f"level {level}" for level in range(COMPOSITE_SCALE_LEVELS)}


def _score_answer(level):
    """A well-formed Score answer whose distribution peaks on ``level``."""
    probabilities = {str(i): 0.0 for i in range(COMPOSITE_SCALE_LEVELS)}
    probabilities[str(level)] = 0.7
    remainder = 0.3 / (COMPOSITE_SCALE_LEVELS - 1)
    for i in range(COMPOSITE_SCALE_LEVELS):
        if i != level:
            probabilities[str(i)] = remainder
    return {
        "type": "score",
        "score": level,
        "confidence": 0.8,
        "legend": _legend(),
        "probabilities": probabilities,
    }


def state_of(parsed):
    """Which state a request carried. Takes the *parsed* body, not the raw bytes."""
    for name, state in COMPOSITE_STATES.items():
        if parsed["state"] == state:
            return name
    raise AssertionError("a request carried a state no case declares")


def reply_for(raw, scores=None, answers=None):
    """A response covering every question in the request that produced it."""
    body = json.loads(raw)
    questions = body["questions"]
    if answers is not None:
        return {
            "model": "jev-1.13.0",
            "answers": answers,
            "usage": {"input_tokens": 512, "output_tokens": 48},
        }
    chosen = (scores or DEFAULT_SCORES)[state_of(body)]
    assert set(chosen) == set(questions)
    return {
        "model": "jev-1.13.0",
        "answers": {name: _score_answer(chosen[name]) for name in questions},
        "usage": {"input_tokens": 512, "output_tokens": 48},
    }


def run_offline(scores=None, answers=None, max_requests=None, latencies=None):
    """Run `06` through the real SDK against a mock transport. Returns ``(bodies, records)``.

    ``latencies`` overrides the recorded wall-clock per case, in call order. The mock's own timings
    are real but meaningless (sub-millisecond, in-process), so an assertion about a *ratio* between
    calls has to set the three windows explicitly rather than read whatever the mock happened to
    take.
    """
    bodies = []

    def handler(request):
        bodies.append(request.content)
        return httpx2.Response(
            200,
            json=reply_for(request.content, scores=scores, answers=answers),
            headers={"x-typesafe-request-id": REQUEST_ID},
        )

    probe = TransportProbe()
    http_client = probe.instrument(timeout=DEFAULT_TIMEOUT, transport=httpx2.MockTransport(handler))
    client = TypeSafeClient(api_key=DUMMY_KEY, http_client=http_client)
    with tempfile.TemporaryDirectory() as directory:
        recorder = UsageRecorder(pathlib.Path(directory))
        with client:
            run_experiment(
                get_experiment(COMPOSITE),
                client=client,
                recorder=recorder,
                model="jev-latest",
                probe=probe,
                **({"max_requests": max_requests} if max_requests is not None else {}),
            )
        records = list(read_records(recorder.path))
    if latencies is not None:
        records = _with_latency(records, latencies)
    return [json.loads(body) for body in bodies], records


def _with_latency(records, values):
    """A copy of the records with the three latency windows set explicitly, in call order."""
    out = _copy(records)
    assert len(values) == len(out)
    for record, value in zip(out, values):
        record["latency_ms"] = value
    return out


def _copy(records):
    return [json.loads(json.dumps(record)) for record in records]


def _with_answer(records, case_id, dimension, answer):
    """A copy of the records with one dimension's answer replaced (or removed when ``None``)."""
    out = _copy(records)
    for record in out:
        if record["case_id"] == case_id:
            if answer is None:
                record["answers"].pop(dimension, None)
            else:
                record["answers"][dimension] = answer
    return out


def _by_case(records, case_id):
    return next(record for record in records if record["case_id"] == case_id)


def _response_without(dimension, record):
    """A real SDK response object with one dimension's answer removed, for the digest path.

    A recorded answer is JSON, so its rubric levels are object keys and therefore strings; the SDK's
    own model wants integers. The conversion is exact here because every key is a level number.
    """
    answers = {}
    for name, answer in record["answers"].items():
        if name == dimension:
            continue
        answer = dict(answer)
        for field in ("legend", "probabilities"):
            if isinstance(answer.get(field), dict):
                answer[field] = {int(level): value for level, value in answer[field].items()}
        answers[name] = answer
    return SystemOneResponse.model_validate(
        {
            "model": "jev-1.13.0",
            "answers": answers,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
    )


class TestTheDeclaredShape:
    """Sections F and Q: three states, four Score questions each, one question set."""

    def test_the_experiment_declares_three_cases(self):
        assert [case.case_id for case in get_experiment(COMPOSITE).cases()] == list(
            COMPOSITE_EXPECTED_ORDER
        )

    def test_the_call_count_is_exactly_three(self):
        assert experiment_call_ceiling(get_experiment(COMPOSITE)) == 3
        bodies, records = run_offline()
        assert len(bodies) == 3
        assert len(records) == 3

    def test_every_request_carries_four_score_questions(self):
        bodies, _ = run_offline()
        for body in bodies:
            questions = body["questions"]
            assert len(questions) == len(COMPOSITE_DIMENSIONS) == 4
            assert all(spec["type"] == "score" for spec in questions.values())
            assert tuple(questions) == COMPOSITE_DIMENSIONS

    def test_the_three_states_share_one_question_set(self):
        cases = get_experiment(COMPOSITE).cases()
        first = cases[0].questions
        for case in cases[1:]:
            assert case.questions is first
        for dimension in COMPOSITE_DIMENSIONS:
            assert cases[0].questions[dimension] is cases[2].questions[dimension]

    def test_only_the_state_differs_between_cases(self):
        cases = get_experiment(COMPOSITE).cases()
        assert len({case.state for case in cases}) == 3
        assert len({case.notes["scenario_class"] for case in cases}) == 3

    def test_each_rubric_has_exactly_four_levels(self):
        for dimension, question in get_experiment(COMPOSITE).cases()[0].questions.items():
            assert len(question.criteria) == COMPOSITE_SCALE_LEVELS == 4, dimension

    def test_every_request_reports_a_legend_of_zero_through_three(self):
        _, records = run_offline()
        for record in records:
            for dimension in COMPOSITE_DIMENSIONS:
                legend = record["answers"][dimension]["legend"]
                assert sorted(int(level) for level in legend) == [0, 1, 2, 3]


class TestTheFrozenWeights:
    """Sections D and E: weights frozen, summing to one, and not from the model."""

    def test_the_weights_sum_to_one(self):
        assert weights_sum() == 1.0

    def test_every_dimension_has_exactly_one_weight(self):
        assert set(COMPOSITE_WEIGHTS) == set(COMPOSITE_DIMENSIONS)

    def test_the_two_direction_groups_are_disjoint_and_complete(self):
        assert set(COMPOSITE_BENEFICIAL) | set(COMPOSITE_ADVERSE) == set(COMPOSITE_DIMENSIONS)
        assert not set(COMPOSITE_BENEFICIAL) & set(COMPOSITE_ADVERSE)

    def test_the_weights_are_a_source_constant_not_a_measured_quantity(self):
        assert COMPOSITE_WEIGHTS == {
            "evidence_quality": 0.30,
            "numerical_stability": 0.30,
            "reproducibility": 0.20,
            "failure_severity": 0.20,
        }


class TestTheArithmetic:
    """Sections D and J: normalization, direction, and the sum."""

    def test_normalization_maps_the_rubric_onto_zero_to_one(self):
        assert normalize(0) == 0.0
        assert normalize(COMPOSITE_TOP_LEVEL) == 1.0
        assert normalize(1) == pytest.approx(1 / 3)

    def test_the_beneficial_dimensions_are_inverted(self):
        for dimension in COMPOSITE_BENEFICIAL:
            assert risk_align(dimension, 3) == 0.0
            assert risk_align(dimension, 0) == 1.0
            assert risk_align(dimension, 1) > risk_align(dimension, 2)

    def test_failure_severity_is_not_inverted(self):
        dimension = "failure_severity"
        assert dimension in COMPOSITE_ADVERSE
        assert risk_align(dimension, 0) == 0.0
        assert risk_align(dimension, 3) == 1.0
        assert risk_align(dimension, 1) < risk_align(dimension, 2)

    def test_an_unknown_dimension_has_no_direction(self):
        # Raising is the point: a dimension with no declared direction must not silently take one of
        # the two, which would quietly invert a whole score.
        with pytest.raises(KeyError):
            risk_align("not_a_dimension", 1)

    def test_the_composite_is_the_sum_of_its_contributions(self):
        _, records = run_offline()
        for record in records:
            case = case_composite(record)
            contributions = [row["weighted_contribution"] for row in case["rows"]]
            assert case["composite_risk"] == composite_of(contributions)
            assert case["composite_risk"] == sum(
                row["weighted_contribution"] for row in case["rows"]
            )

    def test_the_stored_contributions_sum_to_the_stored_composite(self):
        # Section I: the aggregate must be recomputable from the parts, so both go in the record.
        _, records = run_offline()
        for record in records:
            derived = record["notes"]["derived"]
            contributions = [
                derived["dimensions"][dimension]["weighted_contribution"]
                for dimension in COMPOSITE_DIMENSIONS
            ]
            assert derived["composite_risk"] == sum(contributions)

    def test_the_composite_stays_inside_zero_and_one(self):
        _, records = run_offline()
        for record in records:
            assert 0.0 <= case_composite(record)["composite_risk"] <= 1.0

    def test_the_extremes_land_on_zero_and_one(self):
        _, records = run_offline()
        assert case_composite(_by_case(records, "low_risk"))["composite_risk"] == 0.0
        assert case_composite(_by_case(records, "high_risk"))["composite_risk"] == pytest.approx(1.0)

    def test_every_risk_aligned_value_is_inside_zero_and_one(self):
        _, records = run_offline()
        for record in records:
            for row in case_composite(record)["rows"]:
                assert 0.0 <= row["normalized_score"] <= 1.0
                assert 0.0 <= row["risk_aligned_value"] <= 1.0

    def test_the_composite_is_bounded_for_every_rubric_combination(self):
        # The bound is a property of the formula, not of the three states that happened to run.
        for combination in range(COMPOSITE_SCALE_LEVELS ** len(COMPOSITE_DIMENSIONS)):
            levels, remainder = [], combination
            for _ in COMPOSITE_DIMENSIONS:
                levels.append(remainder % COMPOSITE_SCALE_LEVELS)
                remainder //= COMPOSITE_SCALE_LEVELS
            contributions = [
                weighted_contribution(dimension, risk_align(dimension, level))
                for dimension, level in zip(COMPOSITE_DIMENSIONS, levels)
            ]
            assert 0.0 <= composite_of(contributions) <= 1.0


class TestConfidenceNeverEnters:
    """Section E: the hard rule, checked by mutation rather than by reading the source."""

    def test_changing_every_confidence_leaves_every_derived_value_identical(self):
        _, records = run_offline()
        baseline = [case_composite(record) for record in records]
        mutated = _copy(records)
        for record in mutated:
            for answer in record["answers"].values():
                answer["confidence"] = 0.01 if answer["confidence"] != 0.01 else 0.99
        after = [case_composite(record) for record in mutated]
        for before, later in zip(baseline, after):
            assert before["composite_risk"] == later["composite_risk"]
            assert [row.get("weighted_contribution") for row in before["rows"]] == [
                row.get("weighted_contribution") for row in later["rows"]
            ]

    def test_confidence_alone_never_changes_the_ordering(self):
        _, records = run_offline()
        mutated = _copy(records)
        for index, record in enumerate(mutated):
            for answer in record["answers"].values():
                answer["confidence"] = [0.99, 0.5, 0.0][index]
        assert (
            analyze_composite(mutated)["observed_order"]
            == analyze_composite(records)["observed_order"]
        )

    def test_the_phrase_only_ever_appears_being_denied(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        # The report says there is no such quantity. That sentence is the only place the phrase may
        # appear, so every occurrence has to sit inside a denial.
        for line in text.splitlines():
            if "composite confidence" in line.lower():
                assert "no such quantity" in line.lower()
        for phrase in ("confidence-weighted", "confidence-discounted", "confidence-adjusted"):
            assert phrase not in text.lower()

    def test_the_confidence_diagnostic_is_named_a_diagnostic(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "**Dimension confidences** (diagnostic only)" in text
        assert "enter no arithmetic" in text

    def test_the_diagnostic_reports_min_max_and_mean_of_the_four(self):
        _, records = run_offline()
        diagnostic = confidence_diagnostics(case_composite(_by_case(records, "low_risk"))["rows"])
        assert (diagnostic["min"], diagnostic["max"], diagnostic["mean"]) == (0.8, 0.8, 0.8)

    def test_the_diagnostic_is_absent_without_a_usable_confidence(self):
        _, records = run_offline()
        rows = [
            dict(row, confidence="not a number") if row.get("available") else row
            for row in case_composite(_by_case(records, "low_risk"))["rows"]
        ]
        assert confidence_diagnostics(rows)["available"] is False


class TestProbabilitiesNeverEnter:
    """Section L: the distribution is a diagnostic, not an input."""

    def test_the_full_distribution_is_preserved(self):
        _, records = run_offline()
        for record in records:
            for dimension in COMPOSITE_DIMENSIONS:
                probabilities = record["answers"][dimension]["probabilities"]
                assert sorted(int(level) for level in probabilities) == [0, 1, 2, 3]

    def test_rewriting_the_distribution_leaves_every_derived_value_identical(self):
        _, records = run_offline()
        mutated = _copy(records)
        for record in mutated:
            for answer in record["answers"].values():
                answer["probabilities"] = {"0": 1.0, "1": 0.0, "2": 0.0, "3": 0.0}
        assert (
            analyze_composite(mutated)["observed_order"]
            == analyze_composite(records)["observed_order"]
        )
        for original, changed in zip(records, mutated):
            assert (
                case_composite(original)["composite_risk"]
                == case_composite(changed)["composite_risk"]
            )

    def test_the_dominant_level_and_margin_are_derived_but_unused(self):
        _, records = run_offline()
        row = dimension_row(_by_case(records, "low_risk"), "evidence_quality")
        diagnostic = probability_diagnostics(row)
        assert diagnostic["dominant_level"] == "3"
        assert diagnostic["margin"] == pytest.approx(0.7 - 0.1)
        assert "weighted_contribution" not in diagnostic


class TestFailClosed:
    """Section O: a malformed dimension stops the composite; nothing is repaired."""

    def test_a_missing_dimension_makes_the_composite_unavailable(self):
        _, records = run_offline()
        case = case_composite(_with_answer(records, "low_risk", "reproducibility", None)[0])
        assert case["available"] is False
        assert case["unavailable"] == ["reproducibility"]
        assert COMPOSITE_SCORE_UNAVAILABLE in case["markers"]
        assert "composite_risk" not in case

    def test_a_wrong_primitive_makes_the_composite_unavailable(self):
        _, records = run_offline()
        mutated = _with_answer(
            records, "low_risk", "reproducibility", {"type": "noul", "noul": 0.4}
        )
        case = case_composite(mutated[0])
        assert case["available"] is False
        assert "not a `score`" in case["rows"][2]["reason"]

    def test_a_score_outside_the_rubric_makes_the_composite_unavailable(self):
        _, records = run_offline()
        for bad in (-1, 4, 99):
            answer = _score_answer(1)
            answer["score"] = bad
            mutated = _with_answer(records, "low_risk", "evidence_quality", answer)
            assert case_composite(mutated[0])["available"] is False, bad

    def test_a_legend_of_the_wrong_cardinality_makes_the_composite_unavailable(self):
        _, records = run_offline()
        answer = _score_answer(2)
        answer["legend"] = {"0": "a", "1": "b", "2": "c"}
        case = case_composite(_with_answer(records, "low_risk", "evidence_quality", answer)[0])
        assert case["available"] is False
        assert "legend carries 3 level(s)" in case["rows"][0]["reason"]

    def test_a_non_finite_score_makes_the_composite_unavailable(self):
        _, records = run_offline()
        for bad in (math.nan, math.inf, -math.inf, "3", None, True):
            answer = _score_answer(1)
            answer["score"] = bad
            mutated = _with_answer(records, "low_risk", "evidence_quality", answer)
            case = case_composite(mutated[0])
            assert case["available"] is False, bad
            assert "composite_risk" not in case

    def test_nothing_defaults_to_zero_or_gets_dropped(self):
        _, records = run_offline()
        case = case_composite(_with_answer(records, "low_risk", "failure_severity", None)[0])
        assert len(case["rows"]) == len(COMPOSITE_DIMENSIONS)
        # The three usable dimensions keep their contributions; the unusable one carries a reason
        # instead of a number, so there is no zero sitting where a measurement should be.
        assert [
            row["dimension"] for row in case["rows"] if "weighted_contribution" not in row
        ] == ["failure_severity"]
        assert [row["dimension"] for row in case["rows"] if row["available"]] == [
            dimension for dimension in COMPOSITE_DIMENSIONS if dimension != "failure_severity"
        ]
        assert "composite_risk" not in case

    def test_the_remaining_weights_are_not_rescaled(self):
        _, records = run_offline()
        rows = case_composite(_with_answer(records, "low_risk", "failure_severity", None)[0])["rows"]
        assert [row["weight"] for row in rows] == [0.30, 0.30, 0.20, 0.20]
        assert sum(row["weight"] for row in rows) == 1.0

    def test_confidence_is_never_substituted_for_a_score(self):
        _, records = run_offline()
        answer = _score_answer(1)
        answer["score"] = None
        answer["confidence"] = 0.99
        mutated = _with_answer(records, "low_risk", "evidence_quality", answer)
        assert case_composite(mutated[0])["available"] is False

    def test_an_unavailable_case_stops_the_order_being_reported(self):
        _, records = run_offline()
        analysis = analyze_composite(_with_answer(records, "mixed", "numerical_stability", None))
        assert COMPOSITE_SCORE_UNAVAILABLE in analysis["markers"]
        assert COMPOSITE_EXPECTED_ORDER_OBSERVED not in analysis["markers"]
        assert COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED not in analysis["markers"]
        assert len(analysis["observed_order"]) == len(COMPOSITE_EXPECTED_ORDER) - 1

    def test_the_raw_measurement_survives_an_unavailable_composite(self):
        _, records = run_offline()
        mutated = _with_answer(records, "low_risk", "reproducibility", None)
        assert mutated[0]["answers"]["evidence_quality"]["score"] == 3
        assert mutated[0]["input_tokens"] == records[0]["input_tokens"]
        assert mutated[0]["latency_ms"] == records[0]["latency_ms"]

    def test_the_report_says_what_was_not_done(self):
        _, records = run_offline()
        text = "\n".join(
            build_composite_block(_with_answer(records, "low_risk", "reproducibility", None))
        )
        assert f"**`{COMPOSITE_SCORE_UNAVAILABLE}`**" in text
        assert "Nothing defaulted to zero" in text
        assert "no confidence was substituted for a score" in text


class TestScenarioOrder:
    """Sections H and P: the frozen ordinal expectation, and no grading language."""

    def test_the_expected_order_marker_is_raised_on_a_matching_run(self):
        _, records = run_offline()
        analysis = analyze_composite(records)
        assert analysis["observed_order"] == list(COMPOSITE_EXPECTED_ORDER)
        assert COMPOSITE_EXPECTED_ORDER_OBSERVED in analysis["markers"]
        assert COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED not in analysis["markers"]

    def test_a_violated_order_raises_its_own_marker(self):
        flipped = {
            "low_risk": DEFAULT_SCORES["high_risk"],
            "mixed": DEFAULT_SCORES["mixed"],
            "high_risk": DEFAULT_SCORES["low_risk"],
        }
        _, records = run_offline(scores=flipped)
        analysis = analyze_composite(records)
        assert analysis["observed_order"] == ["high_risk", "mixed", "low_risk"]
        assert COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED in analysis["markers"]
        assert COMPOSITE_EXPECTED_ORDER_OBSERVED not in analysis["markers"]

    def test_a_violated_order_is_reported_rather_than_repaired(self):
        flipped = {
            "low_risk": DEFAULT_SCORES["high_risk"],
            "mixed": DEFAULT_SCORES["mixed"],
            "high_risk": DEFAULT_SCORES["low_risk"],
        }
        _, records = run_offline(scores=flipped)
        text = "\n".join(build_composite_block(records))
        assert "the observed order differs from the frozen one" in text
        assert "not edited to make the order come out differently" in text
        # The weights are untouched by the violation.
        assert COMPOSITE_WEIGHTS["evidence_quality"] == 0.30

    def test_no_exact_numeric_target_is_asserted(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "Expected (frozen before the run)" in text
        assert "is not a benchmark" in text

    @pytest.mark.parametrize("word", FORBIDDEN_GRADING)
    def test_no_grading_language_is_ever_affirmative(self, word):
        # The words may appear only inside a denial; an affirmative use would be a claim about the
        # model's correctness against a truth this experiment does not have.
        _, records = run_offline()
        lines = [line for line in build_composite_block(records) if word in line.lower()]
        for line in lines:
            assert "not " in line.lower(), line

    def test_the_dimension_table_shows_the_whole_arithmetic(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        header = (
            "| dimension | raw score | normalized | risk-aligned | weight | contribution "
            "| confidence |"
        )
        assert header in text
        assert "**composite_risk = " in text

    def test_the_frozen_weights_are_stated_before_any_result(self):
        _, records = run_offline()
        lines = build_composite_block(records)
        weights_at = lines.index("### Frozen weights")
        table_at = next(i for i, line in enumerate(lines) if line.startswith("### `low_risk`"))
        assert weights_at < table_at
        assert "a design choice, not a measurement" in "\n".join(lines)


class TestUsageAndLatency:
    """Sections M and N: usage recorded, latency described, nothing compared."""

    def test_usage_is_recorded_per_call(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "3 request(s): 1536 input" in text
        assert "local estimate" in text
        assert "Console billing is authoritative" in text

    def test_no_tokenizer_decomposition_is_attempted(self):
        _, records = run_offline()
        assert "No attempt is made to decompose it" in "\n".join(build_composite_block(records))

    def test_attempt_counts_are_reported_per_call(self):
        _, records = run_offline()
        assert [record["transport_attempt_count"] for record in records] == [1, 1, 1]
        assert [record["attempt_count_source"] for record in records] == [
            "httpx_request_event_hook"
        ] * 3
        text = "\n".join(build_composite_block(records))
        assert "`transport_attempt_count` per call, in order: 1, 1, 1" in text
        assert "not evidence of pure model latency" in text

    def test_the_latency_section_states_the_fixed_order_and_the_confound(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "The order is fixed and it confounds" in text
        assert "nothing here says which state was faster" in text

    def test_the_first_request_is_marked_and_not_used(self):
        _, records = run_offline()
        assert records[0]["is_first_request_in_client_session"] is True
        assert "the first request of the client session" in "\n".join(
            build_composite_block(records)
        )

    def test_no_latency_comparison_between_states_is_drawn(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records)).lower()
        for phrase in ("slower than", "faster than", "latency saving"):
            assert phrase not in text


class TestFirstRequestLatencyOutlier:
    """Section K: the session opener's latency, described and never explained."""

    SLOW_OPENER = (2374.121, 625.546, 565.525)
    EVEN = (600.0, 620.0, 630.0)

    def test_the_marker_is_raised_when_the_session_opener_is_much_the_slowest(self):
        _, records = run_offline(latencies=self.SLOW_OPENER)
        analysis = analyze_composite(records)
        assert COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED in analysis["markers"]
        observation = analysis["first_request_latency"]
        assert observation["available"] is True
        assert observation["is_outlier"] is True
        assert observation["ratio"] == pytest.approx(2374.121 / 625.546)

    def test_the_marker_is_not_raised_when_the_calls_are_comparable(self):
        _, records = run_offline(latencies=self.EVEN)
        analysis = analyze_composite(records)
        assert COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED not in analysis["markers"]
        assert analysis["first_request_latency"]["is_outlier"] is False

    def test_no_ratio_is_invented_from_a_missing_latency(self):
        _, records = run_offline()
        stripped = _copy(records)
        stripped[0]["latency_ms"] = None
        analysis = analyze_composite(stripped)
        assert analysis["first_request_latency"]["available"] is False
        assert COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED not in analysis["markers"]

    def test_the_marker_names_the_confound_rather_than_a_cause(self):
        _, records = run_offline(latencies=self.SLOW_OPENER)
        text = "\n".join(build_composite_block(records))
        assert f"**`{COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED}`**" in text
        assert "confounded here and cannot be separated" in text
        assert "not a speed claim" in text
        # It must not read as a statement about the states themselves.
        for phrase in ("slower than", "faster than", "because of the state", "state-dependent"):
            assert phrase not in text.lower()

    def test_the_latency_section_still_states_the_fixed_order(self):
        _, records = run_offline(latencies=self.SLOW_OPENER)
        text = "\n".join(build_composite_block(records))
        assert "The order is fixed and it confounds" in text
        assert "nothing here says which state was faster" in text

    def test_the_ratio_is_not_called_a_speedup(self):
        _, records = run_offline(latencies=self.SLOW_OPENER)
        text = "\n".join(build_composite_block(records))
        assert "speedup" not in text.lower()
        assert "overhead" not in text.lower()


class TestContributionDecomposition:
    """Section E: where each composite came from, as a decomposition and nothing more."""

    def test_the_shares_of_a_case_sum_to_one(self):
        _, records = run_offline()
        for record in records:
            case = case_composite(record)
            if not case["available"] or not case["composite_risk"]:
                continue
            assert sum(entry["share"] for entry in contribution_shares(case)) == pytest.approx(1.0)

    def test_the_largest_contributor_is_the_largest_contribution(self):
        _, records = run_offline()
        for record in records:
            case = case_composite(record)
            shares = contribution_shares(case)
            top = max(shares, key=lambda entry: entry["weighted_contribution"])
            assert top["weighted_contribution"] == max(
                row["weighted_contribution"] for row in case["rows"]
            )
            assert f"`{top['dimension']}`" in "\n".join(build_composite_block([record]))

    def test_a_dimension_can_dominate_without_having_the_largest_weight(self):
        # A share is the product of a weight and a score, so a 0.20-weight dimension can outweigh a
        # 0.30-weight one. This is the reason the decomposition is reported at all.
        _, records = run_offline()
        case = case_composite(_by_case(records, "low_risk"))
        shares = {entry["dimension"]: entry for entry in contribution_shares(case)}
        assert shares["evidence_quality"]["weight"] == 0.20 or (
            shares["evidence_quality"]["weight"] == 0.30
        )
        top = max(shares.values(), key=lambda entry: entry["weighted_contribution"])
        assert top["dimension"] == "evidence_quality"

    def test_a_zero_composite_yields_no_share_rather_than_a_division(self):
        zero = {
            "case_id": "all_best",
            "answers": {
                "evidence_quality": _score_answer(3),
                "numerical_stability": _score_answer(3),
                "reproducibility": _score_answer(3),
                "failure_severity": _score_answer(0),
            },
        }
        case = case_composite(zero)
        assert case["composite_risk"] == 0.0
        assert all(entry["share"] is None for entry in contribution_shares(case))
        # Every contribution ties at zero, so no dimension is the largest contributor and none is
        # named -- naming one would just be the row order showing through.
        assert "| `all_best` | — | — | — |" in "\n".join(build_composite_block([zero]))

    def test_no_share_is_reported_for_an_unusable_dimension(self):
        _, records = run_offline()
        case = case_composite(_with_answer(records, "low_risk", "reproducibility", None)[0])
        assert "reproducibility" not in {
            entry["dimension"] for entry in contribution_shares(case)
        }

    def test_the_decomposition_disclaims_its_own_influence_claim(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "### Contribution decomposition" in text
        assert "not how much a dimension ought to matter" in text
        assert "no share here is evidence about these dimensions in" in text


class TestDoubleCountingLimit:
    def test_the_double_counting_limit_is_stated(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "Double counting is possible and is not estimated" in text
        assert "no independence is claimed" in text

    def test_no_covariance_is_estimated(self):
        _, records = run_offline()
        analysis = analyze_composite(records)
        assert "covariance" not in {
            key for case in analysis["cases"] for key in case
        }
        assert "covariance between dimensions" in "\n".join(build_composite_block(records))


class TestTheRecordAndItsDerived:
    """Section I: raw and derived provenance, both in the canonical record."""

    def test_the_raw_score_and_distribution_are_stored(self):
        _, records = run_offline()
        answer = records[0]["answers"]["evidence_quality"]
        assert set(answer) >= {"type", "score", "confidence", "legend", "probabilities"}

    def test_the_per_dimension_derivation_is_stored(self):
        _, records = run_offline()
        dimensions = records[0]["notes"]["derived"]["dimensions"]
        assert set(dimensions) == set(COMPOSITE_DIMENSIONS)
        for values in dimensions.values():
            assert set(values) == {
                "raw_score",
                "normalized_score",
                "risk_aligned_value",
                "weight",
                "weighted_contribution",
            }

    def test_the_digest_makes_no_api_call_of_its_own(self):
        # The digest runs inside the recorded call's window; if it called out, the mock would see a
        # fourth body and this would fail.
        bodies, _ = run_offline()
        assert len(bodies) == 3

    def test_an_unavailable_case_stores_the_reason_instead_of_a_number(self):
        _, records = run_offline()
        response = _response_without("reproducibility", records[0])
        derived = composite_digest(get_experiment(COMPOSITE).cases()[0], response)
        assert derived["composite_available"] is False
        assert "composite_risk" not in derived
        assert "reason" in derived["dimensions"]["reproducibility"]

    def test_a_complete_case_stores_the_composite_beside_its_parts(self):
        _, records = run_offline()
        derived = records[0]["notes"]["derived"]
        assert derived["composite_available"] is True
        assert derived["composite_risk"] == case_composite(records[0])["composite_risk"]

    def test_records_without_notes_still_render(self):
        _, records = run_offline()
        stripped = []
        for record in _copy(records):
            record.pop("notes", None)
            stripped.append(record)
        lines = build_composite_block(stripped)
        assert sum(line.startswith("### `") for line in lines) == 3

    def test_a_case_with_no_answers_renders_as_unavailable(self):
        text = "\n".join(build_composite_block([{"case_id": "empty", "answers": {}}]))
        assert COMPOSITE_SCORE_UNAVAILABLE in text

    def test_an_empty_record_list_renders_nothing(self):
        assert build_composite_block([]) == []

    def test_the_snapshot_includes_the_section(self):
        _, records = run_offline()
        text = build_snapshot(list(records))
        assert f"## `{COMPOSITE}`" in text
        assert "### Frozen weights" in text

    def test_the_experiment_is_registered(self):
        assert COMPOSITE in experiment_names()


class TestSecretHygiene:
    def test_no_credential_reaches_the_rendered_block(self):
        _, records = run_offline()
        text = "\n".join(build_composite_block(records)).lower()
        assert DUMMY_KEY not in text
        assert "api_key" not in text
        assert "authorization" not in text

    def test_an_unexpected_answer_field_is_not_copied_into_the_report(self):
        _, records = run_offline()
        mutated = _copy(records)
        mutated[0]["answers"]["evidence_quality"]["internal_note"] = "should not surface"
        assert "should not surface" not in "\n".join(build_composite_block(mutated))

    def test_no_record_is_rewritten_by_reading_it(self):
        _, records = run_offline()
        before = json.dumps(records, sort_keys=True)
        build_composite_block(records)
        analyze_composite(records)
        assert json.dumps(records, sort_keys=True) == before


class TestWording:
    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_no_unsupported_mechanism_words(self, word):
        _, records = run_offline()
        assert word not in "\n".join(build_composite_block(records)).lower()

    def test_it_says_the_dimensions_are_designed_not_proven_orthogonal(self):
        _, records = run_offline()
        assert "designed to be orthogonal, not shown to be" in "\n".join(
            build_composite_block(records)
        )

    def test_the_four_questions_are_called_separate_never_independent(self):
        # The report denies that these dimensions were shown independent, so it must not describe
        # them that way anywhere else: "separate" is what the design and the rubrics support.
        _, records = run_offline()
        text = "\n".join(build_composite_block(records))
        assert "Four separate atomic `Score` questions" in text
        for phrase in (
            "independent Score",
            "independent judgment",
            "independent question",
            "four independent",
            "mutually independent",
        ):
            assert phrase not in text, phrase

    def test_it_says_the_composite_is_validated_against_nothing(self):
        _, records = run_offline()
        assert "not validated against anything" in "\n".join(build_composite_block(records))

    def test_it_says_nothing_downstream_acts_on_the_result(self):
        _, records = run_offline()
        assert "Nothing downstream acts on it" in "\n".join(build_composite_block(records))


class TestSyntheticStateOnly:
    """Sections G and Q: the states are synthetic and state no verdict."""

    def test_the_three_states_are_distinct_and_share_a_domain(self):
        states = list(COMPOSITE_STATES.values())
        assert len(set(states)) == 3
        for state in states:
            assert "advection-diffusion" in state
            assert state.startswith("Validation record")

    def test_no_state_states_the_verdict(self):
        for name, state in COMPOSITE_STATES.items():
            lowered = state.lower()
            for phrase in (
                "low risk",
                "high risk",
                "should be rejected",
                "should be accepted",
                "is safe",
                "is unsafe",
                "trustworthy",
            ):
                assert phrase not in lowered, f"{name} states a verdict: {phrase!r}"

    def test_no_state_reuses_the_rubric_vocabulary(self):
        # A state echoing the rubric's own words would let a correct answer come from matching
        # rather than from the judgment being asked for.
        for name, state in COMPOSITE_STATES.items():
            lowered = state.lower()
            for word in ("independent check", "sensitive", "reproduce", "interpretation"):
                assert word not in lowered, f"{name} leaks rubric wording: {word!r}"

    def test_no_case_id_names_a_verdict_in_the_block(self):
        _, records = run_offline()
        assert "should be" not in "\n".join(build_composite_block(records)).lower()

    def test_the_mock_is_the_only_network_path(self):
        # Three requests and no more means nothing else in the process was reached.
        bodies, _ = run_offline()
        assert len(bodies) == 3
