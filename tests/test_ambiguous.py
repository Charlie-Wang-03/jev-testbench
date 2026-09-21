"""`13b_ambiguous_repeatability`. Offline, and driven by synthetic records.

Two things are pinned down here. The first is that `13b` really does send `01_primitives`' own
request -- verified at the only place it counts, the bytes the SDK would put on the wire, rather
than by comparing two hand-written definitions that happen to look alike. The second is that the
historical `01_primitives` call stays a reference and never becomes a sixth sample.
"""

import hashlib
import json

import httpx2
import pytest
from typesafe_sdk import TypeSafeClient

from jev_lab.ambiguous import (
    AMBIGUOUS,
    AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED,
    REFERENCE,
    build_ambiguous_block,
)
from jev_lab.experiments import (
    AMBIGUOUS_CALLS,
    DEFAULT_MAX_REQUESTS,
    get_experiment,
    run_experiment,
)
from jev_lab.recorder import UsageRecorder
from jev_lab.repeatability import analyze, build_repeatability_block

BLOCKED_BY_DESIGN = ("deterministic", "non-deterministic", "temperature", "sampling", "seed",
                     "random")
FORBIDDEN_CLAIMS = ("proves", "always answers", "is random")

DUMMY_KEY = "not-a-real-key"
REPLY = {"model": "jev-1.13.0", "answers": {},
         "usage": {"input_tokens": 512, "output_tokens": 77}}

# A Choice with two live options and a Score with two live levels: the shape this experiment exists
# to observe, and the shape `13_repeatability` never produced.
NEAR_TIE = {
    "choice": "other",
    "confidence": 0.26,
    "probabilities": {"other": 0.45, "billing": 0.44, "account": 0.11, "feature_request": 0.0},
}
NEAR_TIE_SCORE = {"score": 1.59, "confidence": 0.39, "legend": {},
                  "probabilities": {"0": 0.0, "1": 0.41, "2": 0.59}}


def record(index, *, choice="other", probabilities=None, confidence=0.26, score=1.59,
           score_probabilities=None, noul=0.12, input_tokens=512, output_tokens=77, status="ok",
           attempts=1, latency=600.0, first=False):
    """A record shaped like one call of `13b_ambiguous_repeatability`."""
    answers = {} if status != "ok" else {
        "department": {"type": "choice", "choice": choice, "confidence": confidence,
                       "probabilities": dict(probabilities or NEAR_TIE["probabilities"])},
        "severity": {"type": "score", "score": score, "confidence": 0.39, "legend": {},
                     "probabilities": dict(score_probabilities or NEAR_TIE_SCORE["probabilities"])},
        "repeat_contact": {"type": "noul", "noul": noul},
    }
    return {
        "run_id": "runambig0000", "experiment": AMBIGUOUS, "case_id": f"ambiguous_{index}",
        "model_requested": "jev-latest", "model_resolved": "jev-1.13.0",
        "timestamp_utc": f"2026-01-01T00:00:{index:02d}Z", "latency_ms": latency,
        "input_tokens": input_tokens if status == "ok" else 0,
        "output_tokens": output_tokens if status == "ok" else 0,
        "total_tokens": (input_tokens + output_tokens) if status == "ok" else 0,
        "estimated_cost_usd": input_tokens * 0.042 / 1_000_000 if status == "ok" else None,
        "status": status, "error_type": None if status == "ok" else "TypeSafeError",
        "case_sequence_index": index - 1, "logical_request_index_in_run": index - 1,
        "client_session_id": "session00000", "is_first_request_in_client_session": first,
        "transport_attempt_count": attempts, "transport_retry_count_observed": max(attempts - 1, 0),
        "attempt_count_source": "httpx_request_event_hook", "schema_version": 3,
        "answers": answers, "notes": {"repeat": index, "of": AMBIGUOUS_CALLS},
    }


def a_run(count=5, **overrides):
    return [record(index, first=(index == 1), **overrides) for index in range(1, count + 1)]


def reference_record():
    """The historical `01_primitives` call, as it is actually stored in the log."""
    return {
        "run_id": "c716ef341576", "experiment": REFERENCE, "case_id": "ticket_all_primitives",
        "model_requested": "jev-latest", "model_resolved": "jev-1.13.0",
        "timestamp_utc": "2026-09-20T15:29:51Z", "status": "ok",
        "answers": {
            "department": {"type": "choice", "choice": "other", "confidence": 0.26,
                           "probabilities": {"other": 0.45, "billing": 0.44, "account": 0.11,
                                             "feature_request": 0.0}},
            "severity": {"type": "score", "score": 1.59, "confidence": 0.39,
                         "probabilities": {"0": 0.0, "1": 0.41, "2": 0.59}},
            "repeat_contact": {"type": "noul", "noul": 0.12},
        },
    }


def captured_bodies(experiment_name):
    """Every request body the real SDK would send for one experiment, offline."""
    bodies = []

    def handler(request):
        bodies.append(request.content)
        return httpx2.Response(200, json=REPLY, headers={"x-typesafe-request-id": "req-x"})

    client = TypeSafeClient(api_key=DUMMY_KEY, transport=httpx2.MockTransport(handler))
    import tempfile
    import pathlib

    with tempfile.TemporaryDirectory() as directory:
        with client:
            run_experiment(get_experiment(experiment_name), client=client,
                           recorder=UsageRecorder(pathlib.Path(directory)), model="jev-latest")
    return bodies


class TestItRepeatsZeroOnePrimitives:
    """Section B: reuse, not a lookalike copy. Identity is checked on objects, not on appearances."""

    def test_the_two_experiments_share_one_state_object(self):
        one = get_experiment("01_primitives").cases()[0]
        five = get_experiment(AMBIGUOUS).cases()
        assert all(case.state is one.state for case in five)

    def test_the_two_experiments_share_the_question_objects(self):
        one = get_experiment("01_primitives").cases()[0]
        five = get_experiment(AMBIGUOUS).cases()
        for name in one.questions:
            assert all(case.questions[name] is one.questions[name] for case in five)

    def test_question_names_and_order_are_01_s_own(self):
        one = get_experiment("01_primitives").cases()[0]
        five = get_experiment(AMBIGUOUS).cases()
        assert len({tuple(case.questions) for case in five}) == 1
        assert tuple(five[0].questions) == tuple(one.questions)

    def test_the_case_id_of_01_is_untouched(self):
        cases = get_experiment("01_primitives").cases()
        assert len(cases) == 1
        assert cases[0].case_id == "ticket_all_primitives"

    def test_01_and_13b_send_byte_identical_requests(self):
        bodies = captured_bodies("01_primitives") + captured_bodies(AMBIGUOUS)
        assert len(bodies) == 6
        assert len({hashlib.sha256(body).hexdigest() for body in bodies}) == 1

    def test_the_13b_calls_are_identical_to_each_other(self):
        bodies = captured_bodies(AMBIGUOUS)
        assert len(bodies) == AMBIGUOUS_CALLS
        assert len({body for body in bodies}) == 1

    def test_no_local_provenance_reaches_the_wire(self):
        body = captured_bodies(AMBIGUOUS)[0]
        blob = body.decode("utf-8")
        for leaked in ("ambiguous_", "ticket_all_primitives", "case_id", "notes", '"of"'):
            assert leaked not in blob
        assert sorted(json.loads(blob)) == ["model", "questions", "state"]

    def test_the_wire_body_carries_no_credential(self):
        assert DUMMY_KEY not in captured_bodies(AMBIGUOUS)[0].decode("utf-8")


class TestTheFiveCallDesign:
    def test_it_makes_exactly_five_calls(self):
        assert len(get_experiment(AMBIGUOUS).cases()) == 5

    def test_the_count_matches_the_other_repeat_experiment(self):
        from jev_lab.experiments import REPEAT_CALLS
        assert AMBIGUOUS_CALLS == REPEAT_CALLS

    def test_it_fits_inside_the_default_budget(self):
        assert len(get_experiment(AMBIGUOUS).cases()) <= DEFAULT_MAX_REQUESTS

    def test_every_call_asks_all_three_primitive_types(self):
        for case in get_experiment(AMBIGUOUS).cases():
            assert {question.type for question in case.questions.values()} == {
                "choice", "score", "noul"}

    def test_no_call_adds_a_nonce_or_an_uncertainty_hint(self):
        """Nothing may be smuggled into the payload to manufacture ambiguity."""
        case = get_experiment(AMBIGUOUS).cases()[0]
        for marker in ("uncertain", "unsure", "ambiguous_", "nonce", "T00:", "2026-"):
            assert marker not in case.state
            for question in case.questions.values():
                assert marker not in json.dumps(question.__dict__, default=str)

    def test_the_notes_record_the_repeat_but_stay_local(self):
        cases = get_experiment(AMBIGUOUS).cases()
        assert [case.notes["repeat"] for case in cases] == [1, 2, 3, 4, 5]
        assert {case.notes["repeats"] for case in cases} == {REFERENCE}


class TestNearTieMetrics:
    def test_the_margin_is_the_gap_between_the_top_two(self):
        block = analyze(a_run())["choice"]
        assert block["margins"] == [pytest.approx(0.01)] * 5
        assert block["margin_summary"]["min"] == pytest.approx(0.01)
        assert block["margin_summary"]["range"] == pytest.approx(0.0)

    def test_a_moved_second_option_moves_the_margin(self):
        records = a_run()
        records[2]["answers"]["department"]["probabilities"] = {
            "other": 0.50, "billing": 0.40, "account": 0.10, "feature_request": 0.0}
        block = analyze(records)["choice"]
        assert block["margins"][2] == pytest.approx(0.10)
        assert block["margin_summary"]["range"] == pytest.approx(0.09)

    def test_a_flip_is_counted(self):
        records = a_run()
        records[1]["answers"]["department"]["choice"] = "billing"
        records[1]["answers"]["department"]["probabilities"] = {
            "other": 0.44, "billing": 0.45, "account": 0.11, "feature_request": 0.0}
        block = analyze(records)["choice"]
        assert block["leaders"] == ["other", "billing", "other", "other", "other"]
        assert block["leader_switches"] == 2
        assert "**The leading option changed between calls 2 time(s)**" in "\n".join(
            build_repeatability_block(records))

    def test_a_stable_leader_reports_no_change(self):
        block = analyze(a_run())["choice"]
        assert block["leader_switches"] == 0

    def test_an_exact_tie_follows_the_label_the_answer_named(self):
        """A tie has no first place; the ranking must not contradict the returned label."""
        records = a_run()
        records[0]["answers"]["department"]["choice"] = "other"
        records[0]["answers"]["department"]["probabilities"] = {
            "other": 0.45, "billing": 0.45, "account": 0.10, "feature_request": 0.0}
        row = analyze(records)["choice"]["ranking"][0]
        assert row["tied"] is True
        assert row["leader"] == "other"
        assert row["margin"] == 0.0

    def test_an_exact_tie_without_a_label_orders_alphabetically(self):
        records = a_run()
        records[0]["answers"]["severity"]["probabilities"] = {"0": 0.0, "1": 0.5, "2": 0.5}
        row = analyze(records)["score"]["ranking"][0]
        assert row["tied"] is True
        assert row["leader"] == "1"

    def test_the_report_says_when_the_top_two_tied(self):
        records = a_run()
        for entry in records:
            entry["answers"]["severity"]["probabilities"] = {"0": 0.0, "1": 0.5, "2": 0.5}
        text = "\n".join(build_repeatability_block(records))
        assert "EXACT_TOP_PROBABILITY_TIE_OBSERVED" in text
        assert "on 5 of 5 call(s)" in text
        assert "not a quantity this call measured" in text

    def test_a_tie_raises_its_marker_and_a_clean_run_does_not(self):
        tied = a_run()
        tied[4]["answers"]["department"]["probabilities"] = {
            "other": 0.45, "billing": 0.45, "account": 0.10, "feature_request": 0.0}
        assert "EXACT_TOP_PROBABILITY_TIE_OBSERVED" in analyze(tied)["markers"]
        assert "EXACT_TOP_PROBABILITY_TIE_OBSERVED" not in analyze(a_run())["markers"]

    def test_the_tie_note_does_not_explain_how_the_label_was_chosen(self):
        """The record shows a tie and a label; it does not show how one became the other."""
        tied = a_run()
        tied[4]["answers"]["department"]["probabilities"] = {
            "other": 0.45, "billing": 0.45, "account": 0.10, "feature_request": 0.0}
        text = "\n".join(build_repeatability_block(tied))
        assert "do not address it" in text

    def test_the_choice_spread_is_reported(self):
        records = a_run()
        for entry, value in zip(records, (0.45, 0.46, 0.44, 0.47, 0.43)):
            entry["answers"]["department"]["probabilities"]["other"] = value
        block = analyze(records)["choice"]
        assert block["probabilities"]["other"]["range"] == pytest.approx(0.04)
        assert block["max_probability_spread"] == pytest.approx(0.04)

    def test_the_score_spread_is_reported(self):
        records = a_run()
        for entry, value in zip(records, (0.59, 0.56, 0.60, 0.58, 0.55)):
            entry["answers"]["severity"]["probabilities"]["2"] = value
        block = analyze(records)["score"]
        assert block["probabilities"]["2"]["range"] == pytest.approx(0.05)

    def test_a_changed_dominant_score_level_is_counted(self):
        records = a_run()
        records[3]["answers"]["severity"]["probabilities"] = {"0": 0.0, "1": 0.61, "2": 0.39}
        block = analyze(records)["score"]
        assert block["dominant_levels"] == ["2", "2", "2", "1", "2"]
        assert block["dominant_level_switches"] == 2

    def test_a_failed_call_is_counted_rather_than_read_as_agreement(self):
        records = a_run()
        records[2] = record(3, status="error")
        analysis = analyze(records)
        assert analysis["calls"] == 5
        assert analysis["ok_calls"] == 4
        assert analysis["choice"]["observed"] == 4


class TestTargetRealized:
    """Section H: whether the run is ambiguous is a result, and a negative one is recorded."""

    def test_a_near_tie_run_does_not_raise_the_marker(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED not in text
        assert "do carry information about a field whose top options are close together" in text

    def test_a_saturated_choice_raises_the_marker(self):
        records = a_run(choice="billing")
        for entry in records:
            entry["answers"]["department"]["probabilities"] = {
                "other": 0.0, "billing": 1.0, "account": 0.0, "feature_request": 0.0}
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED in text
        assert "the Choice came back saturated" in text

    def test_a_concentrated_score_raises_the_marker(self):
        records = a_run()
        for entry in records:
            entry["answers"]["severity"]["probabilities"] = {"0": 0.0, "1": 0.01, "2": 0.99}
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED in text
        assert "of the mass" in text

    def test_it_says_the_records_are_not_adjusted_or_rerun(self):
        records = a_run()
        for entry in records:
            entry["answers"]["department"]["probabilities"] = {
                "other": 0.0, "billing": 1.0, "account": 0.0, "feature_request": 0.0}
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "not adjusted" in text
        assert "not rerun over until it agrees" in text

    def test_the_history_is_called_prior_evidence_and_not_a_guarantee(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "prior evidence" in text
        assert "not a guarantee" in text


class TestHistoricalReferenceStaysSeparate:
    """Section F: the earlier call is an outside marker, never a sixth sample."""

    def test_the_five_call_statistics_are_not_computed_over_six(self):
        records = a_run()
        reference = reference_record()
        assert analyze(records)["calls"] == 5
        assert analyze(records + [reference])["calls"] == 6  # only if the caller pools them
        assert "5 call(s)" in "\n".join(build_ambiguous_block(records, [reference]))

    def test_the_reference_appears_under_its_own_heading(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert f"### Historical reference: `{REFERENCE}`" in text
        assert "**not** pooled with the calls above" in text

    def test_the_reference_is_reported_with_its_provenance(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "c716ef341576" in text
        assert "2026-09-20T15:29:51Z" in text

    def test_a_missing_reference_is_stated_rather_than_invented(self):
        text = "\n".join(build_ambiguous_block(a_run(), []))
        assert f"No `{REFERENCE}` record is present" in text

    def test_the_reference_values_are_compared_to_the_observed_range(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "inside the observed range" in text
        assert "the historical winner `other`" in text

    def test_a_reference_outside_the_range_is_reported_as_outside(self):
        records = a_run()
        for entry in records:
            entry["answers"]["severity"]["score"] = 2.5
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "below the observed range" in text

    def test_a_reference_winner_that_never_leads_is_reported(self):
        records = a_run(choice="billing")
        for entry in records:
            entry["answers"]["department"]["probabilities"] = {
                "other": 0.10, "billing": 0.80, "account": 0.10, "feature_request": 0.0}
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "never led here" in text

    def test_one_historical_point_is_not_turned_into_a_stability_claim(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "cannot show that a value is stable" in text


class TestExactEqualityAndDriftPaths:
    def test_an_unchanging_run_says_no_drift_and_no_more(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "no drift observed, and nothing more" in text

    def test_an_unchanging_noul_is_reported_as_exactly_equal(self):
        text = "\n".join(build_ambiguous_block(a_run(noul=0.12), [reference_record()]))
        assert "**exactly equal**" in text

    def test_a_moved_noul_is_reported_as_a_small_variation(self):
        records = a_run()
        for entry, value in zip(records, (0.12, 0.12, 0.13, 0.12, 0.12)):
            entry["answers"]["repeat_contact"]["noul"] = value
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED" in text

    def test_token_variation_raises_its_own_marker(self):
        records = a_run()
        records[4]["input_tokens"] = 513
        records[4]["total_tokens"] = 513 + records[4]["output_tokens"]
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "TOKEN_ACCOUNTING_VARIATION_OBSERVED" in text

    def test_transport_attempts_are_counted_not_assumed(self):
        records = a_run()
        records[1]["transport_attempt_count"] = 3
        text = "\n".join(build_ambiguous_block(records, [reference_record()]))
        assert "with more than one: **1**" in text
        assert "No HTTP retry was locally observed" not in text

    def test_latency_is_kept_separate_from_the_semantics(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "descriptive only" in text
        assert "are not combined" in text
        assert "First request of the session (marked, not dropped)" in text


class TestWording:
    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_no_unsupported_mechanism_words(self, word):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()])).lower()
        assert word not in text

    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_the_saturated_path_also_avoids_them(self, word):
        records = a_run()
        for entry in records:
            entry["answers"]["department"]["probabilities"] = {
                "other": 0.0, "billing": 1.0, "account": 0.0, "feature_request": 0.0}
        assert word not in "\n".join(build_ambiguous_block(records, [reference_record()])).lower()

    @pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
    def test_no_claims_about_mechanism(self, claim):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()])).lower()
        assert claim not in text

    def test_it_says_what_the_experiment_is_not(self):
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "not a prompt sensitivity test" in text
        assert "not a correctness test" in text


class TestSecretHygiene:
    def test_no_credential_reaches_the_rendered_block(self, monkeypatch):
        monkeypatch.setenv("TYPESAFE_API_KEY", "planted-marker-render-me-never")
        text = "\n".join(build_ambiguous_block(a_run(), [reference_record()]))
        assert "planted-marker-render-me-never" not in text

    def test_an_unexpected_field_is_not_copied_into_the_report(self):
        records = a_run()
        records[0]["secret_extra"] = "should-not-appear"
        reference = reference_record()
        reference["secret_extra"] = "should-not-appear-either"
        text = "\n".join(build_ambiguous_block(records, [reference]))
        assert "should-not-appear" not in text
