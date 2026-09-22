"""`05_speculative_fanout`. Offline, driven by the real SDK encoder and synthetic records.

The load-bearing check in this file is the payload audit. Section E of the design requires that
the two arms ask *the same question objects*, and "the same" is verified in two places at once:
on the objects themselves (`is`, not `==`), and on the bytes the real SDK would put on the wire.
A definition that reads alike is not evidence of either.
"""

import json
import pathlib
import tempfile

import httpx2
import pytest
from typesafe_sdk import TypeSafeClient

from jev_lab.experiments import (
    FANOUT_ARM,
    FANOUT_BRANCH_QUESTIONS,
    FANOUT_BRANCH_SPECIFIC,
    FANOUT_CALL_CEILING,
    FANOUT_DECLARED_ORDER,
    FANOUT_EXPECTED_BRANCH,
    FANOUT_PRIMARY_QUESTIONS,
    FANOUT_QUESTIONS,
    FANOUT_STATES,
    STAGED_ARM,
    Case,
    experiment_call_ceiling,
    get_experiment,
    run_experiment,
)
from jev_lab.fanout import (
    CONSUMED_ANSWER_MISMATCH_OBSERVED,
    FANOUT,
    FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS,
    PRIMARY_BRANCH_DISAGREEMENT_OBSERVED,
    PRIMARY_BRANCH_UNEXPECTED,
    SPECULATIVE_QUESTIONS_UNUSED,
    STAGED_SECOND_REQUEST_SKIPPED,
    analyze_fanout,
    build_fanout_block,
    unused_answers,
)
from jev_lab.recorder import UsageRecorder, read_records
from jev_lab.repeatability import format_ms
from jev_lab.snapshot import build_snapshot

DUMMY_KEY = "not-a-real-key"
REQUEST_ID = "req-fanout-0001"

BLOCKED_BY_DESIGN = ("deterministic", "non-deterministic", "temperature", "sampling", "seed",
                     "random")
# Comparative phrases that only appear inside a directional claim. Bare adjectives are absent on
# purpose: this report has to be able to say "which arm is cheaper is not assumed" and "not a
# speedup", and banning the words would ban the disclaimers along with the claims.
FORBIDDEN_CLAIMS = ("faster than", "cheaper than", "proves", "demonstrates that")

MORE_DETAIL = "request_more_detail"
ESCALATE = "escalate_to_specialist"


def _answer_for(name, spec, primary):
    """One canned answer, shaped by the question the request actually carried."""
    if name == "next_action":
        second = "escalate_to_specialist" if primary == MORE_DETAIL else "request_more_detail"
        return {"type": "choice", "choice": primary, "confidence": 0.71,
                "probabilities": {primary: 0.71, second: 0.29}}
    kind = spec["type"]
    if kind == "choice":
        return {"type": "choice", "choice": "reproduction_context", "confidence": 0.66,
                "probabilities": {"reproduction_context": 0.66, "account_or_plan_identifier": 0.34}}
    if kind == "score":
        return {"type": "score", "score": 1.0, "confidence": 0.62,
                "legend": {"0": "none", "1": "stated", "2": "imminent"},
                "probabilities": {"0": 0.0, "1": 1.0, "2": 0.0}}
    return {"type": "noul", "noul": 0.5}


def reply_for(body, primary):
    """A response covering every question in the request that produced it.

    Output tokens scale with the number of answers, which is the property the real API has and the
    one the output-token section of the report is about: a request that answers six questions
    writes more than one that answers three. Input tokens are held flat so a test can assert the
    request count from the token count alone.
    """
    questions = json.loads(body)["questions"]
    return {
        "model": "jev-1.13.0",
        "answers": {name: _answer_for(name, spec, primary) for name, spec in questions.items()},
        "usage": {"input_tokens": 640, "output_tokens": 12 * len(questions)},
    }


def pair_of(body):
    """Which pair a request belongs to, read off its state."""
    for pair, state in FANOUT_STATES.items():
        if body["state"] == state:
            return pair
    raise AssertionError("a request carried a state no pair declares")


def run_offline(primary=None, max_requests=FANOUT_CALL_CEILING):
    """Run `05` through the real SDK against a mock transport. Returns ``(bodies, records)``.

    ``primary`` is either one label forced on every pair, or ``None`` to let each pair answer with
    the branch its state is expected to select. The ``None`` default matters: forcing one label on
    both pairs would make the second pair fail its expectation by construction, and a test that
    reports a routing miss the harness invented is worse than no test.
    """
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        answer = FANOUT_EXPECTED_BRANCH[pair_of(body)] if primary is None else primary
        bodies.append(request.content)
        return httpx2.Response(200, json=reply_for(request.content, answer),
                               headers={"x-typesafe-request-id": REQUEST_ID})

    client = TypeSafeClient(api_key=DUMMY_KEY, transport=httpx2.MockTransport(handler))
    with tempfile.TemporaryDirectory() as directory:
        recorder = UsageRecorder(pathlib.Path(directory))
        with client:
            run_experiment(
                get_experiment(FANOUT),
                client=client,
                recorder=recorder,
                model="jev-latest",
                max_requests=max_requests,
            )
        records = list(read_records(recorder.path))
    return [json.loads(body) for body in bodies], records


def _is_fanout(record):
    return (record.get("notes") or {}).get("strategy") == "fanout"


def _with_output_tokens(record, value):
    """The same record with its output side moved. Nothing else about it is touched."""
    return {**record, "output_tokens": value}


def split_bodies(bodies):
    """The captured requests, separated into the three shapes this design can send.

    A fanout request carries every question, a staged first stage carries the primary alone, and a
    staged second stage carries a branch set. Counting questions is not enough to tell them apart
    -- a branch set and the primary are both smaller than the fanout request -- so the primary is
    matched by name.
    """
    fanout, stage_one, stage_two = [], [], []
    for body in bodies:
        names = tuple(body["questions"])
        if len(names) == len(FANOUT_QUESTIONS):
            fanout.append(body)
        elif names == tuple(FANOUT_PRIMARY_QUESTIONS):
            stage_one.append(body)
        else:
            stage_two.append(body)
    return fanout, stage_one, stage_two


def case_named(case_id):
    for case in get_experiment(FANOUT).cases():
        if case.case_id == case_id:
            return case
    raise AssertionError(f"no declared case {case_id!r}")


class TestTheTwoArmsAskTheSameQuestions:
    """Section E: identity at the object, checked before identity at the encoder."""

    def test_the_primary_question_is_one_object(self):
        fanout = case_named("pairA_fanout")
        staged = case_named("pairA_staged_1")
        assert fanout.questions["next_action"] is staged.questions["next_action"]

    def test_the_staged_first_stage_carries_the_primary_alone(self):
        assert tuple(case_named("pairA_staged_1").questions) == ("next_action",)

    def test_each_branch_follow_up_is_one_object(self):
        for branch, questions in FANOUT_BRANCH_QUESTIONS.items():
            for name, question in questions.items():
                assert question is FANOUT_QUESTIONS[name], f"{branch}/{name} is not the same object"

    def test_the_fanout_request_carries_every_branch_question(self):
        expected = set(FANOUT_PRIMARY_QUESTIONS)
        for questions in FANOUT_BRANCH_QUESTIONS.values():
            expected |= set(questions)
        assert set(FANOUT_QUESTIONS) == expected
        assert len(FANOUT_QUESTIONS) == 6

    def test_both_pairs_send_one_set_of_questions(self):
        first, second = case_named("pairA_fanout"), case_named("pairB_fanout")
        assert first.questions is second.questions

    def test_each_pair_sends_one_state_object_in_both_arms(self):
        for pair in FANOUT_STATES:
            assert case_named(f"pair{pair}_fanout").state is case_named(f"pair{pair}_staged_1").state


class TestTheEncodedPayloadsMatch:
    """Section E, at the only place it counts: the bytes the SDK would put on the wire."""

    def test_the_run_makes_the_declared_calls(self):
        bodies, records = run_offline()
        assert len(bodies) == FANOUT_CALL_CEILING
        assert len(records) == FANOUT_CALL_CEILING

    def test_the_staged_first_stage_is_a_subset_of_the_fanout_request(self):
        bodies, _ = run_offline()
        fanout, stage_one, _ = split_bodies(bodies)
        assert fanout and stage_one
        for name, spec in stage_one[0]["questions"].items():
            assert fanout[0]["questions"][name] == spec, f"{name} was reworded between the arms"

    def test_the_staged_second_stage_is_a_subset_of_the_fanout_request(self):
        bodies, _ = run_offline()
        fanout, _, stage_two = split_bodies(bodies)
        assert len(stage_two) == 2
        for body in stage_two:
            for name, spec in body["questions"].items():
                assert fanout[0]["questions"][name] == spec, f"{name} was reworded between the arms"

    def test_each_second_stage_carries_exactly_its_branch_set(self):
        bodies, _ = run_offline()
        _, _, stage_two = split_bodies(bodies)
        assert [set(body["questions"]) for body in stage_two] == [
            set(FANOUT_BRANCH_QUESTIONS[branch]) for branch in (MORE_DETAIL, ESCALATE)
        ]

    def test_a_forced_branch_sends_that_branch_to_both_pairs(self):
        bodies, _ = run_offline(primary=ESCALATE)
        _, _, stage_two = split_bodies(bodies)
        assert {frozenset(body["questions"]) for body in stage_two} == {
            frozenset(FANOUT_BRANCH_QUESTIONS[ESCALATE])
        }

    def test_every_stage_sends_a_state_the_pair_declares(self):
        bodies, _ = run_offline()
        assert all(pair_of(body) in FANOUT_STATES for body in bodies)

    def test_the_two_pairs_differ_only_in_their_state(self):
        bodies, _ = run_offline()
        fanout, _, _ = split_bodies(bodies)
        assert len(fanout) == 2
        assert fanout[0]["questions"] == fanout[1]["questions"]
        assert fanout[0]["state"] != fanout[1]["state"]

    def test_no_local_provenance_reaches_the_wire(self):
        bodies, _ = run_offline()
        for body in bodies:
            blob = json.dumps(body)
            for leaked in ("pairA", "pairB", "staged", "fanout", "case_id", "branch_expected",
                           "speculative"):
                assert leaked not in blob, f"{leaked!r} leaked into the request"

    def test_the_wire_carries_only_the_documented_keys(self):
        bodies, _ = run_offline()
        for body in bodies:
            assert sorted(body) == ["model", "questions", "state"]

    def test_the_wire_body_carries_no_credential(self):
        bodies, _ = run_offline()
        assert all(DUMMY_KEY not in json.dumps(body) for body in bodies)


class TestTheBranchIsChosenInPython:
    """Section B: the routing is a code-side lookup, and its frozen rules hold."""

    def test_a_fanout_case_schedules_nothing(self):
        from jev_lab.experiments import _05_follow_up

        case = case_named("pairA_fanout")
        assert _05_follow_up(case, _response(ESCALATE)) == []

    def test_a_second_stage_schedules_nothing(self):
        from jev_lab.experiments import _05_follow_up

        case = Case(
            case_id="pairA_staged_2",
            state=FANOUT_STATES["A"],
            questions=FANOUT_BRANCH_QUESTIONS[MORE_DETAIL],
            notes={"strategy": STAGED_ARM, "stage": 2, "pair": "A"},
        )
        # Without this the flow would recurse: stage 2 carries no primary question to route on.
        assert _05_follow_up(case, _response(MORE_DETAIL)) == []

    @pytest.mark.parametrize("branch", sorted(FANOUT_BRANCH_SPECIFIC))
    def test_the_second_stage_is_the_branch_the_answer_chose(self, branch):
        from jev_lab.experiments import _05_follow_up

        scheduled = _05_follow_up(case_named("pairA_staged_1"), _response(branch))
        assert len(scheduled) == 1
        assert scheduled[0].questions is FANOUT_BRANCH_QUESTIONS[branch]

    def test_the_second_stage_reuses_the_first_stage_state_object(self):
        from jev_lab.experiments import _05_follow_up

        first = case_named("pairA_staged_1")
        scheduled = _05_follow_up(first, _response(ESCALATE))
        assert scheduled[0].state is first.state

    def test_an_unknown_label_sends_no_second_request(self):
        """The frozen rule: no audited question set exists for a branch the map does not hold."""
        from jev_lab.experiments import _05_follow_up

        assert _05_follow_up(case_named("pairA_staged_1"), _response("something_else")) == []

    def test_an_unknown_label_still_gets_its_second_call_cap(self):
        bodies, records = run_offline(primary="something_else")
        assert len(bodies) == 4  # the two fanout calls and the two staged first stages
        assert all(record["status"] == "ok" for record in records)

    def test_the_expected_branch_is_frozen_for_every_pair(self):
        assert set(FANOUT_EXPECTED_BRANCH) == set(FANOUT_STATES)
        for pair, branch in FANOUT_EXPECTED_BRANCH.items():
            assert branch in FANOUT_BRANCH_QUESTIONS
            assert case_named(f"pair{pair}_staged_1").notes["branch_expected"] == branch

    def test_the_expected_branch_is_local_bookkeeping_only(self):
        """The branch names are the primary's own criteria keys, so they are on the wire by design.

        What must not reach it is the *expectation* — which branch this pair is supposed to select.
        That lives in the case notes, and the payload audit checks separately that notes never
        serialize.
        """
        for case in get_experiment(FANOUT).cases():
            assert "branch_expected" in case.notes
        bodies, _ = run_offline()
        assert all("branch_expected" not in json.dumps(body) for body in bodies)


def _response(primary):
    """A decoded response whose primary answer names ``primary``."""
    from typesafe_sdk import ChoiceAnswer, SystemOneResponse, Usage

    return SystemOneResponse(
        model="jev-1.13.0",
        usage=Usage(input_tokens=1, output_tokens=1),
        answers={"next_action": ChoiceAnswer(choice=primary, confidence=0.7,
                                             probabilities={primary: 0.7, "other": 0.3})},
    )


class TestTheDeclaredSkeleton:
    """Section D: a fixed, budgeted case list, with the ceiling stated rather than implied."""

    def test_four_cases_are_declared(self):
        assert len(get_experiment(FANOUT).cases()) == 4

    def test_the_ceiling_covers_the_declared_flows(self):
        assert experiment_call_ceiling(get_experiment(FANOUT)) == FANOUT_CALL_CEILING == 6

    def test_every_other_experiment_has_no_gap_between_cases_and_calls(self):
        for name, experiment in get_experiment(FANOUT).__class__ and _all_experiments().items():
            if name == FANOUT:
                continue
            assert experiment.follow_up is None
            assert experiment_call_ceiling(experiment) == len(experiment.cases())

    def test_the_declared_order_balances_the_arms(self):
        """Pair A leads with fanout, pair B with staged, so arm is not perfectly confounded."""
        first: dict[str, str] = {}
        for pair, strategy in FANOUT_DECLARED_ORDER:
            first.setdefault(pair, strategy)
        assert set(first.values()) == {FANOUT_ARM, STAGED_ARM}

    def test_the_declared_order_matches_the_cases(self):
        declared = [(case.notes["pair"], case.notes["strategy"]) for case in get_experiment(FANOUT).cases()]
        assert declared == list(FANOUT_DECLARED_ORDER)

    def test_a_staged_first_stage_actually_runs_second(self):
        _, records = run_offline()
        order = [record["case_id"] for record in records]
        for pair in FANOUT_STATES:
            assert order.index(f"pair{pair}_staged_1") < order.index(f"pair{pair}_staged_2")
        assert order.index("pairA_fanout") < order.index("pairA_staged_1")
        assert order.index("pairB_staged_1") < order.index("pairB_fanout")


def _all_experiments():
    from jev_lab.experiments import EXPERIMENTS

    return EXPERIMENTS


class TestFollowUpBudgetAndFailure:
    def test_the_budget_caps_the_flow(self):
        _, records = run_offline(max_requests=3)
        assert len(records) == 3

    def test_a_failed_first_stage_sends_no_second_request(self, tmp_path):
        class Failing:
            def __init__(self):
                self.calls = 0

            def system_one(self, state, questions, model=None):
                self.calls += 1
                raise RuntimeError("boom")

        client = Failing()
        recorder = UsageRecorder(tmp_path)
        run_experiment(get_experiment(FANOUT), client=client, recorder=recorder)
        # Four declared cases, four attempts: nothing was routed, so nothing was scheduled after.
        assert client.calls == 4
        assert [record["status"] for record in read_records(recorder.path)] == ["error"] * 4

    def test_a_follow_up_runs_immediately_after_its_parent(self):
        _, records = run_offline()
        order = [record["case_id"] for record in records]
        assert order == [
            "pairA_fanout",
            "pairA_staged_1",
            "pairA_staged_2",
            "pairB_staged_1",
            "pairB_staged_2",
            "pairB_fanout",
        ]


class TestUnusedQuestionAccounting:
    """Section F: asked against consumed, and the honest limit on the unit."""

    def test_a_fanout_call_records_the_split(self):
        _, records = run_offline()
        derived = _derived_of(records, "pairA_fanout")
        assert derived["questions_asked"] == list(FANOUT_QUESTIONS)
        assert derived["questions_consumed"] == ["next_action", "followup_urgency", "missing_detail",
                                                 "detail_is_blocking"]
        assert derived["questions_unused"] == ["specialist_team", "is_unauthorised_change"]
        assert derived["unused_question_count"] == 2

    def test_the_other_branch_is_what_goes_unused(self):
        _, records = run_offline(primary=ESCALATE)
        derived = _derived_of(records, "pairA_fanout")
        assert derived["questions_unused"] == ["missing_detail", "detail_is_blocking"]

    def test_a_staged_second_stage_records_its_branch(self):
        _, records = run_offline()
        assert _derived_of(records, "pairA_staged_2")["branch_served"] == MORE_DETAIL

    def test_unused_answers_are_counted_from_the_answers_that_came_back(self):
        record = {"notes": {"derived": {"questions_unused": ["a", "b", "c"]}},
                  "answers": {"a": {"type": "noul", "noul": 0.5}, "b": None}}
        # Only two of the three unused questions were answered at all, so only two were discarded.
        assert unused_answers(record) == ["a"]

    def test_the_fanout_arm_pays_for_questions_it_does_not_read(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        assert analysis["fanout_questions_asked"] == 12
        assert analysis["fanout_questions_consumed"] == 8
        assert analysis["fanout_questions_unused"] == 4
        assert analysis["fanout_unused_answers"] == 4

    def test_the_report_refuses_a_per_question_token_cost(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "cannot be separated from the tokens spent on the request" in text
        assert "No per-question token cost is claimed here" in text


def _derived_of(records, case_id):
    for record in records:
        if record["case_id"] == case_id:
            return record["notes"]["derived"]
    raise AssertionError(f"no record for {case_id!r}")


class TestGroupingAndAggregation:
    def test_the_two_arms_are_grouped_per_pair(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        assert [entry["pair"] for entry in analysis["pairs"]] == ["A", "B"]
        for entry in analysis["pairs"]:
            assert len(entry["fanout"]) == 1
            assert len(entry["staged"]) == 2

    def test_the_two_stages_are_told_apart(self):
        _, records = run_offline()
        entry = analyze_fanout(records)["pairs"][0]
        assert len(entry["staged_stage_1"]) == 1
        assert len(entry["staged_stage_2"]) == 1

    def test_pooled_totals_are_the_sum_of_the_pairs(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        assert analysis["calls"] == 6
        assert analysis["fanout_calls"] == 2
        assert analysis["staged_calls"] == 4
        assert analysis["fanout_input_tokens"] == 2 * 640
        assert analysis["staged_input_tokens"] == 4 * 640

    def test_the_cost_ratio_is_derived_not_assumed(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "| **pooled** | 2 | 4 | 1280 | 2560 | 0.5000x |" in text

    def test_the_round_trip_counts_are_stated(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "fanout **2** logical request(s) against staged **4**" in text


class TestSemanticComparison:
    """Section H: only consumed follow-ups take part, and a difference is reported as one."""

    def test_identical_answers_are_reported_as_identical(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        comparisons = analysis["pairs"][0]["comparisons"]
        assert [c["question"] for c in comparisons] == ["next_action", "followup_urgency",
                                                       "missing_detail", "detail_is_blocking"]
        assert all(c["differences"] == [] for c in comparisons)

    def test_an_unused_question_never_enters_the_comparison(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        compared = {c["question"] for c in analysis["pairs"][0]["comparisons"]}
        assert compared.isdisjoint({"specialist_team", "is_unauthorised_change"})

    def test_the_primary_is_paired_with_the_first_stage_and_the_follow_ups_with_the_second(self):
        """The staged arm asks the primary all along, in its first request.

        Pairing every consumed question against the second stage would report the primary as
        absent from the staged arm when it was asked there — a comparison that silently stopped
        happening rather than one that failed.
        """
        _, records = run_offline()
        comparisons = {c["question"]: c for c in analyze_fanout(records)["pairs"][0]["comparisons"]}
        assert comparisons["next_action"]["comparable"] is True
        assert comparisons["next_action"]["stage"] == 1
        assert comparisons["missing_detail"]["stage"] == 2
        assert "carried by no staged request" not in "\n".join(build_fanout_block(records))

    def test_the_two_comparisons_are_reported_under_separate_headings(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "**The primary question, asked in two contexts.**" in text
        assert "**Follow-ups both arms consumed.**" in text

    def test_a_moved_noul_is_reported_as_a_difference(self):
        # Pair A consumes branch A, so the follow-up it has to move is branch A's.
        records = _synthetic_pair(noul=0.9)
        moved = [
            c for c in analyze_fanout(records)["pairs"][0]["comparisons"]
            if c["question"] == "detail_is_blocking"
        ]
        # Fanout first, staged second: the order the comparison is written in.
        assert moved and moved[0]["differences"] == ["`noul` 0.5 vs 0.9"]

    def test_a_moved_probability_names_the_option_that_moved(self):
        records = _synthetic_pair(option="account_or_plan_identifier")
        comparison = [
            c for c in analyze_fanout(records)["pairs"][0]["comparisons"]
            if c["question"] == "missing_detail"
        ][0]
        # `format_number` renders 0.0 as "0"; the option that moved is named, which is the point.
        assert "P(`account_or_plan_identifier`) 0.34 vs 0" in comparison["differences"]

    def test_a_difference_raises_its_marker(self):
        records = _synthetic_pair(noul=0.9)
        assert CONSUMED_ANSWER_MISMATCH_OBSERVED in analyze_fanout(records)["markers"]
        _, clean = run_offline()
        assert CONSUMED_ANSWER_MISMATCH_OBSERVED not in analyze_fanout(clean)["markers"]

    def test_a_noul_is_not_compared_on_a_confidence_it_does_not_have(self):
        """Comparing ``None`` to ``None`` would report agreement nobody measured."""
        records = _synthetic_pair()
        comparison = [
            c for c in analyze_fanout(records)["pairs"][0]["comparisons"]
            if c["question"] == "detail_is_blocking"
        ][0]
        assert comparison["differences"] == []
        assert comparison["kind"] == "noul"


def _synthetic_pair(noul=0.5, option=None):
    """A hand-built pair where the staged answer moves, to exercise the difference path."""
    _, records = run_offline()
    records = [dict(record) for record in records]
    for record in records:
        if record["case_id"] == "pairA_staged_2":
            answers = {name: dict(answer) for name, answer in record["answers"].items()}
            if "detail_is_blocking" in answers:
                answers["detail_is_blocking"] = {"type": "noul", "noul": noul}
            if option and "missing_detail" in answers:
                answers["missing_detail"] = {
                    "type": "choice", "choice": "nothing_specific", "confidence": 0.5,
                    "probabilities": {option: 0.0, "reproduction_context": 1.0},
                }
            record["answers"] = answers
    return records


class TestRoutingAndAgreement:
    """Section J: routing correctness is reported, and it is not confidence."""

    def test_the_expected_branch_is_reported_against_the_actual_one(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert f"`{MORE_DETAIL}`" in text
        assert f"(`{MORE_DETAIL}`)" in text
        assert "**Routing correctness is not confidence.**" in text

    def test_a_wrong_branch_is_reported_rather_than_hidden(self):
        # Forcing escalation makes pair A wrong and pair B right, so the miss is one-sided.
        _, records = run_offline(primary=ESCALATE)
        assert _derived_of(records, "pairA_fanout")["branch_matches_expected"] is False
        assert _derived_of(records, "pairB_fanout")["branch_matches_expected"] is True
        assert PRIMARY_BRANCH_UNEXPECTED in analyze_fanout(records)["markers"]
        assert "| A |" in "\n".join(build_fanout_block(records))
        assert "| no (`request_more_detail`) |" in "\n".join(build_fanout_block(records))

    def test_an_unroutable_label_raises_its_marker(self):
        bodies, records = run_offline(primary="something_else")
        markers = analyze_fanout(records)["markers"]
        assert PRIMARY_BRANCH_UNEXPECTED in markers
        assert STAGED_SECOND_REQUEST_SKIPPED in markers

    def test_a_disagreement_between_the_arms_raises_its_marker(self):
        records = [dict(record) for record in run_offline()[1]]
        for record in records:
            if record["case_id"] == "pairA_fanout":
                answers = {name: dict(answer) for name, answer in record["answers"].items()}
                answers["next_action"] = {"type": "choice", "choice": ESCALATE, "confidence": 0.6,
                                          "probabilities": {ESCALATE: 0.6, MORE_DETAIL: 0.4}}
                record["answers"] = answers
                record["notes"] = {**record["notes"],
                                   "derived": {**record["notes"]["derived"],
                                               "branch_taken": ESCALATE,
                                               "branch_matches_expected": False}}
        assert PRIMARY_BRANCH_DISAGREEMENT_OBSERVED in analyze_fanout(records)["markers"]

    def test_a_clean_run_raises_only_the_overhead_marker(self):
        # One marker is excluded from the exact comparison, and the exclusion is checked rather
        # than trusted. This harness times a mock transport with a real clock, so whether the two
        # pairs' latency directions disagree is an artifact of how long each simulated round trip
        # happened to take -- asserting it either way makes the test a coin flip. Everything the
        # run does control is still asserted exactly, and the excluded marker is asserted to match
        # the directions actually recorded, so a genuine regression in either still fails here.
        _, records = run_offline()
        analysis = analyze_fanout(records)
        timing_dependent = FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS
        assert [m for m in analysis["markers"] if m != timing_dependent] == [
            SPECULATIVE_QUESTIONS_UNUSED
        ]
        directions = {pair["latency_direction"] for pair in analysis["pairs"]} - {None}
        assert (timing_dependent in analysis["markers"]) is (len(directions) > 1)


class TestLatencyIsObservational:
    """Section I: sequential time as observed, with no speedup claimed."""

    def test_the_staged_total_is_the_sum_of_its_two_windows(self):
        _, records = run_offline()
        staged = [r for r in records if r["case_id"].startswith("pairA_staged")]
        text = "\n".join(build_fanout_block(records))
        total = format_ms(sum(float(r["latency_ms"]) for r in staged))
        assert f"**{total} ms** sequential" in text
        # Both measured windows are shown beside the sum, so the addition is checkable by eye.
        assert " + ".join(format_ms(r["latency_ms"]) for r in staged) in text

    def test_it_says_the_python_step_between_the_stages_is_not_timed(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "the Python routing" in text
        assert "is not separately timed" in text

    def test_the_first_request_of_the_session_is_marked(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "opened the client session" in text

    @pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
    def test_no_directional_claim_is_made(self, claim):
        _, records = run_offline()
        assert claim not in "\n".join(build_fanout_block(records)).lower()

    def test_the_design_does_not_pick_a_winner_in_advance(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "is not assumed, and not decided by the design" in text
        assert "No latency factor is claimed" in text


def _latency(records, pair, fanout, staged):
    """A copy of the records with one pair's three windows set, for the direction tests.

    A mock transport answers at whatever speed the machine happens to run at, so a direction
    assertion that read the observed latencies would be a coin toss. Every window the comparison
    touches is set here, including both staged stages, so the direction is arithmetic.
    """
    wanted = {
        f"pair{pair}_fanout": fanout,
        f"pair{pair}_staged_1": staged,
        f"pair{pair}_staged_2": staged,
    }
    out = []
    for record in records:
        record = dict(record)
        if record["case_id"] in wanted:
            record["latency_ms"] = wanted[record["case_id"]]
        out.append(record)
    return out


class TestLatencyDirectionIsReported:
    """Section I: when the two pairs point opposite ways, that is the finding, not the average."""

    def test_opposite_directions_raise_the_marker(self):
        _, records = run_offline()
        # Pair A's fanout is the slow arm (9000 against 500 + 500) and pair B's the fast one
        # (100 against 500 + 500).
        records = _latency(records, "A", fanout=9000.0, staged=500.0)
        records = _latency(records, "B", fanout=100.0, staged=500.0)
        assert FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS in analyze_fanout(records)["markers"]

    def test_a_consistent_direction_does_not_raise_it(self):
        _, records = run_offline()
        records = _latency(records, "A", fanout=100.0, staged=500.0)
        records = _latency(records, "B", fanout=100.0, staged=500.0)
        directions = {pair["latency_direction"] for pair in analyze_fanout(records)["pairs"]}
        assert directions == {"fanout_faster"}
        assert FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS not in analyze_fanout(records)[
            "markers"
        ]

    def test_the_disagreement_names_no_cause(self):
        # Position is offered as a plausible confound, never as the identified cause: the six calls
        # cannot separate connection setup from arm identity, and the wording must not imply they
        # did.
        _, records = run_offline()
        records = _latency(records, "A", fanout=9000.0, staged=500.0)
        records = _latency(records, "B", fanout=100.0, staged=500.0)
        text = "\n".join(build_fanout_block(records))
        assert "the records do not identify the cause" in text
        assert "is the explanation" not in text
        assert "proves" not in text.lower()

    def test_each_pair_states_its_own_direction(self):
        _, records = run_offline()
        records = _latency(records, "A", fanout=9000.0, staged=500.0)
        records = _latency(records, "B", fanout=100.0, staged=500.0)
        text = "\n".join(build_fanout_block(records))
        assert "**A direction**: fanout was the slower arm" in text
        assert "**B direction**: fanout was the faster arm" in text
        assert "The pairs disagree on direction" in text

    def test_a_missing_latency_yields_no_direction(self):
        _, records = run_offline()
        records = _latency(records, "A", fanout=None, staged=500.0)
        directions = {
            pair["pair"]: pair["latency_direction"] for pair in analyze_fanout(records)["pairs"]
        }
        assert directions["A"] is None
        assert "A direction" not in "\n".join(build_fanout_block(records))


class TestOutputTokenTradeoff:
    """Section E: the output side of the trade, and the price caveat that belongs with it."""

    def test_the_difference_and_ratio_come_from_the_records(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        text = "\n".join(build_fanout_block(records))
        fanout = analysis["fanout_output_tokens"]
        staged = analysis["staged_output_tokens"]
        assert f"fanout **{fanout:.0f}**, staged **{staged:.0f}**" in text
        assert f"**{fanout - staged:+.0f}** tokens" in text

    def test_it_says_the_fanout_arm_produced_more_output_tokens(self):
        _, records = run_offline()
        assert analyze_fanout(records)["fanout_output_tokens"] > analyze_fanout(records)[
            "staged_output_tokens"
        ]
        assert "materially more output tokens" in "\n".join(build_fanout_block(records))

    def test_the_output_direction_follows_the_records(self):
        # The sentence named one direction on any log at all. Swap which arm spends the output
        # tokens and the reading has to swap with it.
        _, records = run_offline()
        analysis = analyze_fanout(records)
        assert analysis["fanout_output_tokens"] > analysis["staged_output_tokens"]
        swapped = [_with_output_tokens(record, 1 if _is_fanout(record) else 100) for record in records]
        swapped_analysis = analyze_fanout(swapped)
        assert swapped_analysis["fanout_output_tokens"] < swapped_analysis["staged_output_tokens"]
        text = "\n".join(build_fanout_block(swapped))
        assert "materially fewer output tokens" in text
        assert "materially more output tokens" not in text
        assert "the same number of output tokens" not in text

    def test_a_tie_is_not_reported_as_a_direction(self):
        _, records = run_offline()
        tied = [_with_output_tokens(record, 0) for record in records]
        text = "\n".join(build_fanout_block(tied))
        assert "the same number of output tokens" in text
        assert "materially more output tokens" not in text
        assert "materially fewer output tokens" not in text

    def test_output_is_not_called_free_in_general(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "**Output tokens are not free in general.**" in text
        assert "not a statement about TypeSafe's pricing" in text

    def test_the_price_is_read_from_the_table_not_asserted(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        # The resolved model and its published output rate, not a hardcoded sentence.
        assert "`jev-1.13.0`" in text
        assert "$0/M tokens for `jev-1.13.0`" in text

    def test_an_unknown_model_makes_no_cost_claim(self):
        records = [dict(record, model_resolved="jev-unlisted") for record in run_offline()[1]]
        text = "\n".join(build_fanout_block(records))
        assert "No price is available for the resolved model" in text
        assert "/M tokens for" not in text


class TestRelationToParallelQuestions:
    """Section J: the two designs side by side, and the ranking explicitly refused."""

    def test_the_parallel_saving_is_recomputed_from_its_records(self):
        _, records = run_offline()
        batched = [dict(r, notes={**r["notes"], "arm": "batched"}, input_tokens=400) for r in records]
        separate = [
            dict(r, notes={**r["notes"], "arm": "separate"}, input_tokens=1000) for r in records
        ]
        text = "\n".join(build_fanout_block(records, batched + separate))
        assert "a saving of **60.00%** of the input tokens" in text

    def test_the_two_percentages_are_not_ranked(self):
        _, records = run_offline()
        parallel = [dict(r, notes={**r["notes"], "arm": "batched"}) for r in records]
        parallel += [dict(r, notes={**r["notes"], "arm": "separate"}) for r in records]
        text = "\n".join(build_fanout_block(records, parallel))
        assert "the larger one is not the better architecture" in text
        assert "not evidence about the other" in text

    def test_without_the_other_experiment_the_section_is_absent(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "Relation to `03_parallel_questions`" not in text


class TestPooledDerivedMetrics:
    """Section C/K: the pooled counts, and the unit they are counted in."""

    def test_the_unused_fraction_is_a_count_over_a_count(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        assert analysis["fanout_questions_asked"] == 12
        assert analysis["fanout_questions_unused"] == 4
        text = "\n".join(build_fanout_block(records))
        assert "an unused fraction of **33.33%**" in text
        assert "It is not a fraction of the tokens, the cost, or the latency" in text

    def test_the_pooled_totals_are_sums_of_the_arm_records(self):
        _, records = run_offline()
        analysis = analyze_fanout(records)
        fanout = [r for r in records if r["notes"]["strategy"] == FANOUT_ARM]
        staged = [r for r in records if r["notes"]["strategy"] == STAGED_ARM]
        assert analysis["fanout_input_tokens"] == sum(r["input_tokens"] for r in fanout)
        assert analysis["staged_input_tokens"] == sum(r["input_tokens"] for r in staged)
        assert analysis["fanout_calls"] == len(fanout)
        assert analysis["staged_calls"] == len(staged)


class TestWording:
    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_no_unsupported_mechanism_words(self, word):
        _, records = run_offline()
        assert word not in "\n".join(build_fanout_block(records)).lower()

    def test_it_says_what_the_experiment_does_not_show(self):
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "The crossover" in text
        assert "No handler runs" in text
        assert "TypeSafe Console billing is authoritative" in text

    def test_cost_is_labelled_a_local_estimate(self):
        _, records = run_offline()
        assert "**local estimate**" in "\n".join(build_fanout_block(records))


class TestOlderAndUnexpectedRecords:
    def test_a_record_without_notes_does_not_crash_the_block(self):
        text = "\n".join(build_fanout_block([{"experiment": FANOUT, "case_id": "x", "status": "ok"}]))
        assert f"## `{FANOUT}`" in text

    def test_a_schema_one_record_is_not_read_as_a_measurement(self):
        old = {"experiment": FANOUT, "case_id": "pairA_fanout", "status": "ok", "schema_version": 1}
        analysis = analyze_fanout([old])
        assert analysis["pairs"] == []
        assert analysis["fanout_questions_unused"] == 0

    def test_an_empty_record_list_renders_nothing(self):
        assert build_fanout_block([]) == []

    def test_the_snapshot_includes_the_section(self):
        _, records = run_offline()
        text = build_snapshot(records)
        assert f"## `{FANOUT}`" in text
        assert "### Speculative overhead" in text


class TestSecretHygiene:
    def test_no_credential_reaches_the_rendered_block(self, monkeypatch):
        monkeypatch.setenv("TYPESAFE_API_KEY", "planted-marker-render-me-never")
        _, records = run_offline()
        text = "\n".join(build_fanout_block(records))
        assert "planted-marker-render-me-never" not in text

    def test_an_unexpected_field_is_not_copied_into_the_report(self):
        _, records = run_offline()
        records[0] = {**records[0], "secret_extra": "should-not-appear",
                      "notes": {**records[0]["notes"], "secret": "should-not-appear"}}
        assert "should-not-appear" not in "\n".join(build_fanout_block(records))

    def test_no_record_is_rewritten_by_reading_it(self, tmp_path):
        _, records = run_offline()
        before = json.dumps(records, sort_keys=True)
        build_fanout_block(records)
        assert json.dumps(records, sort_keys=True) == before
