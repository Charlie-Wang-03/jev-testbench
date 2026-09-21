"""`13_repeatability` and its derived analysis. Offline, and driven by synthetic records.

The experiment exists to hold one invariant: the payload is identical on every call, so anything
that moves is a measurement rather than a prompt effect. These tests pin that invariant down at the
only place it really counts -- the bytes the SDK would put on the wire -- and then pin down how the
derived report talks about what it found.
"""

import hashlib
import json

import httpx2
import pytest
from typesafe_sdk import TypeSafeClient

from jev_lab.experiments import get_experiment, run_experiment
from jev_lab.recorder import UsageRecorder
from jev_lab.repeatability import (
    CONCENTRATED_TOP_PROBABILITY,
    SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED,
    TOKEN_ACCOUNTING_VARIATION_OBSERVED,
    analyze,
    build_repeatability_block,
)

BLOCKED_BY_DESIGN = ("deterministic", "non-deterministic", "temperature", "sampling", "seed",
                     "random")

# Wording that would turn an observation into a claim about mechanism.
FORBIDDEN_CLAIMS = ("proves", "always answers", "is random")

DUMMY_KEY = "not-a-real-key"
REPLY = {
    "model": "jev-1.13.0",
    "answers": {
        "primary_issue": {
            "type": "choice", "choice": "shipping_delay", "confidence": 0.71,
            "probabilities": {"shipping_delay": 0.52, "billing_discrepancy": 0.28,
                              "cancellation_request": 0.11, "product_question": 0.09},
        },
        "urgency": {
            "type": "score", "score": 1.44, "confidence": 0.63,
            "legend": {"0": "none", "1": "some", "2": "critical"},
            "probabilities": {"0": 0.13, "1": 0.48, "2": 0.39},
        },
        "wants_to_cancel": {"type": "noul", "noul": 0.37},
    },
    "usage": {"input_tokens": 312, "output_tokens": 41},
}


def record(index, *, choice="shipping_delay", confidence=0.71, score=1.44, noul=0.37,
           input_tokens=312, output_tokens=41, status="ok", attempts=1, latency=612.5,
           first=False, schema_version=3):
    """A record shaped like one call of `13_repeatability`."""
    answers = {} if status != "ok" else {
        "primary_issue": {"type": "choice", "choice": choice, "confidence": confidence,
                          "probabilities": {"shipping_delay": 0.52, "billing_discrepancy": 0.28,
                                            "cancellation_request": 0.11, "product_question": 0.09}},
        "urgency": {"type": "score", "score": score, "confidence": 0.63,
                    "legend": {"0": "none", "1": "some", "2": "critical"},
                    "probabilities": {"0": 0.13, "1": 0.48, "2": 0.39}},
        "wants_to_cancel": {"type": "noul", "noul": noul},
    }
    entry = {
        "run_id": "runrepeat0000", "experiment": "13_repeatability", "case_id": f"repeat_{index}",
        "model_requested": "jev-latest", "model_resolved": "jev-1.13.0",
        "timestamp_utc": f"2026-01-01T00:00:{index:02d}Z", "latency_ms": latency,
        "input_tokens": input_tokens if status == "ok" else 0,
        "output_tokens": output_tokens if status == "ok" else 0,
        "total_tokens": (input_tokens + output_tokens) if status == "ok" else 0,
        "estimated_cost_usd": input_tokens * 0.042 / 1_000_000 if status == "ok" else None,
        "cost_basis": "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
        "status": status, "error_type": None if status == "ok" else "TypeSafeError",
        "case_sequence_index": index - 1, "logical_request_index_in_run": index - 1,
        "client_session_id": "session00000", "is_first_request_in_client_session": first,
        "transport_attempt_count": attempts, "transport_retry_count_observed": max(attempts - 1, 0),
        "attempt_count_source": "httpx_request_event_hook",
        "schema_version": schema_version, "answers": answers,
        "notes": {"repeat": index, "of": 5},
    }
    if schema_version < 3:
        for key in ("transport_attempt_count", "transport_retry_count_observed",
                    "attempt_count_source"):
            entry.pop(key)
    if schema_version < 2:
        for key in ("case_sequence_index", "logical_request_index_in_run",
                    "client_session_id", "is_first_request_in_client_session"):
            entry.pop(key)
    return entry


def identical_run(count=5, **overrides):
    """`count` records that differ only in their local provenance, exactly as a real run would."""
    return [record(index, first=(index == 1), **overrides) for index in range(1, count + 1)]


class TestTheDesignSendsOneIdenticalRequest:
    """Section C: the invariant is about objects and bytes, not about intentions."""

    def test_it_makes_exactly_five_calls(self):
        cases = get_experiment("13_repeatability").cases()
        assert len(cases) == 5

    def test_every_call_asks_all_three_primitive_types(self):
        for case in get_experiment("13_repeatability").cases():
            assert {question.type for question in case.questions.values()} == {
                "choice", "score", "noul"}

    def test_every_call_shares_one_state_object(self):
        cases = get_experiment("13_repeatability").cases()
        assert len({id(case.state) for case in cases}) == 1

    def test_every_call_shares_the_same_question_objects(self):
        cases = get_experiment("13_repeatability").cases()
        for name in cases[0].questions:
            assert len({id(case.questions[name]) for case in cases}) == 1

    def test_question_order_is_identical_across_calls(self):
        cases = get_experiment("13_repeatability").cases()
        assert len({tuple(case.questions) for case in cases}) == 1

    def test_the_state_carries_no_per_call_metadata(self):
        """No timestamp, id, or repeat index may be smuggled into the payload."""
        state = get_experiment("13_repeatability").cases()[0].state
        for marker in ("repeat_", "run_id", "session", "2026-", "T00:"):
            assert marker not in state

    def test_the_requested_model_is_the_same_for_every_call(self):
        assert len({case.notes["of"] for case in get_experiment("13_repeatability").cases()}) == 1


class TestPayloadIdentityThroughTheRealSdk:
    """The strongest available proof: hash the bytes the SDK would actually send."""

    @staticmethod
    def _capture():
        bodies = []

        def handler(request):
            bodies.append(request.content)
            return httpx2.Response(200, json=REPLY, headers={"x-typesafe-request-id": "req-x"})

        client = TypeSafeClient(api_key=DUMMY_KEY, transport=httpx2.MockTransport(handler))
        return client, bodies

    def test_the_serialized_bodies_are_byte_identical(self, tmp_path):
        client, bodies = self._capture()
        with client:
            run_experiment(get_experiment("13_repeatability"), client=client,
                           recorder=UsageRecorder(tmp_path))
        assert len(bodies) == 5
        assert len({hashlib.sha256(body).hexdigest() for body in bodies}) == 1

    def test_no_local_provenance_reaches_the_wire(self, tmp_path):
        """case_id and notes are provenance for the log, never part of the request."""
        client, bodies = self._capture()
        with client:
            run_experiment(get_experiment("13_repeatability"), client=client,
                           recorder=UsageRecorder(tmp_path))
        blob = bodies[0].decode("utf-8")
        for leaked in ("repeat_1", "case_id", "notes", '"of"'):
            assert leaked not in blob
        assert sorted(json.loads(blob)) == ["model", "questions", "state"]

    def test_the_wire_body_carries_no_credential(self, tmp_path):
        client, bodies = self._capture()
        with client:
            run_experiment(get_experiment("13_repeatability"), client=client,
                           recorder=UsageRecorder(tmp_path))
        assert DUMMY_KEY not in bodies[0].decode("utf-8")


class TestDerivedMetrics:
    def test_choice_reports_labels_agreement_and_per_option_spread(self):
        analysis = analyze(identical_run())
        choice = analysis["choice"]
        assert choice["labels"]["labels"] == ["shipping_delay"] * 5
        assert choice["labels"]["agreeing_count"] == 5
        assert set(choice["probabilities"]) == {
            "shipping_delay", "billing_discrepancy", "cancellation_request", "product_question"}
        assert choice["probabilities"]["shipping_delay"] == {"min": 0.52, "max": 0.52,
                                                             "mean": 0.52, "range": 0.0}
        assert choice["max_probability_spread"] == 0.0
        assert choice["confidence"]["range"] == 0.0

    def test_choice_agreement_counts_a_split_field(self):
        records = identical_run()
        for entry in records[3:]:
            entry["answers"]["primary_issue"]["choice"] = "billing_discrepancy"
        labels = analyze(records)["choice"]["labels"]
        assert labels["agreeing_count"] == 3
        assert labels["distinct"] == 2

    def test_score_reports_min_max_mean_range_and_levels(self):
        records = identical_run()
        for entry, value in zip(records, (1.0, 1.2, 1.4, 1.6, 1.8)):
            entry["answers"]["urgency"]["score"] = value
        score = analyze(records)["score"]
        assert score["values"] == [1.0, 1.2, 1.4, 1.6, 1.8]
        assert score["summary"]["min"] == 1.0 and score["summary"]["max"] == 1.8
        assert score["summary"]["mean"] == pytest.approx(1.4)
        assert score["summary"]["range"] == pytest.approx(0.8)
        assert set(score["probabilities"]) == {"0", "1", "2"}

    def test_noul_reports_deviation_from_the_first_call_not_from_the_mean(self):
        records = identical_run()
        for entry, value in zip(records, (0.30, 0.32, 0.35, 0.40, 0.44)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        noul = analyze(records)["noul"]
        assert noul["values"][0] == 0.30
        assert noul["max_deviation_from_first"] == pytest.approx(0.14)
        assert noul["summary"]["range"] == pytest.approx(0.14)

    def test_a_failed_call_is_counted_rather_than_read_as_agreement(self):
        records = identical_run()
        records[2] = record(3, status="error")
        analysis = analyze(records)
        assert analysis["calls"] == 5
        assert analysis["ok_calls"] == 4
        assert analysis["failed_calls"] == 1
        assert analysis["choice"]["observed"] == 4
        assert analysis["choice"]["labels"]["agreeing_count"] == 4

    def test_transport_counts_split_single_multiple_and_unrecorded(self):
        records = identical_run()
        records[1]["transport_attempt_count"] = 3
        records[1]["transport_retry_count_observed"] = 2
        records[2] = record(3, schema_version=1)
        transport = analyze(records)["transport"]
        assert transport["single_attempt"] == 3
        assert transport["multiple_attempts"] == 1
        assert transport["not_recorded"] == 1

    def test_model_resolution_is_reported_per_call(self):
        model = analyze(identical_run())["model"]
        assert model["consistent"] is True
        assert model["resolved"] == ["jev-1.13.0"] * 5

    def test_a_moved_alias_is_visible_rather_than_averaged(self):
        records = identical_run()
        records[4]["model_resolved"] = "jev-1.14.0"
        analysis = analyze(records)
        assert analysis["model"]["consistent"] is False
        assert "not all from one model" in "\n".join(build_repeatability_block(records))


class TestTokenRepeatability:
    def test_equal_tokens_are_reported_as_exact_equality(self):
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "**exactly equal**" in text
        assert TOKEN_ACCOUNTING_VARIATION_OBSERVED not in text

    def test_varying_tokens_raise_the_marker(self):
        records = identical_run()
        for entry, value in zip(records, (312, 312, 313, 312, 314)):
            entry["input_tokens"] = value
            entry["total_tokens"] = value + entry["output_tokens"]
            entry["estimated_cost_usd"] = value * 0.042 / 1_000_000
        analysis = analyze(records)
        assert analysis["tokens"]["varies"] is True
        assert analysis["tokens"]["unique"]["input"] == [312, 313, 314]
        text = "\n".join(build_repeatability_block(records))
        assert TOKEN_ACCOUNTING_VARIATION_OBSERVED in text

    def test_varying_output_tokens_also_raise_the_marker(self):
        """Output is free at the published rate, so it is analysed on its own footing."""
        records = identical_run()
        for entry, value in zip(records, (41, 41, 42, 41, 41)):
            entry["output_tokens"] = value
            entry["total_tokens"] = entry["input_tokens"] + value
        assert TOKEN_ACCOUNTING_VARIATION_OBSERVED in "\n".join(build_repeatability_block(records))

    def test_variation_is_never_averaged_away(self):
        records = identical_run()
        records[4]["input_tokens"] = 999
        records[4]["total_tokens"] = 999 + records[4]["output_tokens"]
        entries = analyze(records)["tokens"]["unique"]
        assert entries["input"] == [312, 999]  # both survive; neither becomes "the" cost


class TestExactEqualityWording:
    def test_no_drift_is_stated_plainly(self):
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "no drift observed, and nothing more" in text

    def test_it_does_not_claim_a_sixth_call_would_agree(self):
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "does not establish that a sixth call would agree" in text

    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_it_uses_none_of_the_unsupported_mechanism_words(self, word):
        text = "\n".join(build_repeatability_block(identical_run())).lower()
        assert word not in text

    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_the_drift_path_also_avoids_them(self, word):
        records = identical_run(noul=0.3)
        for entry, value in zip(records, (0.3, 0.5, 0.9, 0.4, 0.8)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        assert word not in "\n".join(build_repeatability_block(records)).lower()

    @pytest.mark.parametrize("claim", FORBIDDEN_CLAIMS)
    def test_it_makes_no_claim_about_mechanism(self, claim):
        assert claim not in "\n".join(build_repeatability_block(identical_run())).lower()

    def test_the_report_says_what_the_experiment_is_not(self):
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "not a prompt sensitivity test" in text
        assert "not a correctness test" in text


class TestDriftPath:
    def test_a_label_change_is_reported_with_its_count(self):
        records = identical_run()
        records[4]["answers"]["primary_issue"]["choice"] = "billing_discrepancy"
        text = "\n".join(build_repeatability_block(records))
        assert "**4 of 5**" in text
        assert "2 distinct label(s) appeared" in text

    def test_probability_movement_is_reported_as_a_spread(self):
        records = identical_run()
        for entry, value in zip(records, (0.52, 0.55, 0.60, 0.57, 0.50)):
            entry["answers"]["primary_issue"]["probabilities"]["shipping_delay"] = value
        analysis = analyze(records)
        assert analysis["choice"]["probabilities"]["shipping_delay"]["range"] == pytest.approx(0.10)
        assert "Largest probability spread" in "\n".join(build_repeatability_block(records))

    def test_the_first_noul_is_the_reference_point(self):
        records = identical_run()
        for entry, value in zip(records, (0.9, 0.9, 0.9, 0.9, 0.1)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        assert analyze(records)["noul"]["max_deviation_from_first"] == pytest.approx(0.8)


class TestNoulVariationMarker:
    """A field that moved is reported as having moved, and the disclosure travels with it."""

    def test_a_small_nonzero_range_raises_the_marker(self):
        records = identical_run()
        for entry, value in zip(records, (0.11, 0.11, 0.10, 0.11, 0.11)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        analysis = analyze(records)
        assert SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED in analysis["markers"]
        assert SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED in "\n".join(
            build_repeatability_block(records))

    def test_an_identical_noul_raises_nothing(self):
        analysis = analyze(identical_run())
        assert SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED not in analysis["markers"]

    def test_a_large_range_raises_no_marker_but_is_still_reported(self):
        """The parameter bounds the adjective, never the number."""
        records = identical_run()
        for entry, value in zip(records, (0.3, 0.5, 0.9, 0.4, 0.8)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        analysis = analyze(records)
        assert SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED not in analysis["markers"]
        assert analysis["noul"]["summary"]["range"] == pytest.approx(0.6)
        assert "**0.6**" in "\n".join(build_repeatability_block(records))

    def test_the_marker_names_the_parameter_that_qualified_it(self):
        records = identical_run()
        for entry, value in zip(records, (0.37, 0.37, 0.36, 0.37, 0.37)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        text = "\n".join(build_repeatability_block(records))
        assert "smallness parameter" in text
        assert "not a significance test" in text

    @pytest.mark.parametrize("word", BLOCKED_BY_DESIGN)
    def test_it_does_not_name_a_mechanism_as_the_cause(self, word):
        records = identical_run()
        for entry, value in zip(records, (0.37, 0.37, 0.36, 0.37, 0.37)):
            entry["answers"]["wants_to_cancel"]["noul"] = value
        assert word not in "\n".join(build_repeatability_block(records)).lower()


class TestDistributionShape:
    """A clean result at a corner of a scale is reported as a corner, not as the whole scale."""

    @staticmethod
    def _saturate(records):
        for entry in records:
            entry["answers"]["primary_issue"]["probabilities"] = {
                "shipping_delay": 1.0, "billing_discrepancy": 0.0,
                "cancellation_request": 0.0, "product_question": 0.0}
            entry["answers"]["primary_issue"]["confidence"] = 1.0
        return records

    def test_a_saturated_choice_is_flagged_and_the_limit_is_stated(self):
        records = self._saturate(identical_run())
        analysis = analyze(records)
        assert analysis["shape"]["choice_saturated"] is True
        text = "\n".join(build_repeatability_block(records))
        assert "**Choice is saturated.**" in text
        assert "not evidence about repeatability where two options are close" in text

    def test_a_choice_with_spread_across_it_is_not_flagged(self):
        analysis = analyze(identical_run())
        assert analysis["shape"]["choice_saturated"] is False
        assert "Choice is saturated" not in "\n".join(build_repeatability_block(identical_run()))

    def test_a_concentrated_score_is_flagged_with_its_leading_probability(self):
        records = identical_run()
        for entry in records:
            entry["answers"]["urgency"]["probabilities"] = {"0": 0.01, "1": 0.98, "2": 0.01}
        analysis = analyze(records)
        assert analysis["shape"]["score_concentrated"] is True
        assert analysis["shape"]["score_top_probability"] == pytest.approx(0.98)
        text = "\n".join(build_repeatability_block(records))
        assert "**Score is concentrated.**" in text
        assert "0.98" in text

    def test_an_even_score_is_not_flagged_and_the_count_is_derived(self):
        """`identical_run` spreads mass 0.13/0.48/0.39, so neither field is at a corner."""
        analysis = analyze(identical_run())
        assert analysis["shape"]["score_concentrated"] is False
        assert analysis["shape"]["score_top_probability"] == pytest.approx(0.48)
        assert "What the shapes of these distributions limit" not in "\n".join(
            build_repeatability_block(identical_run()))

    def test_the_count_of_cornered_fields_follows_the_data(self):
        from_saturated_only = self._saturate(identical_run())
        assert "end of one of them" in "\n".join(build_repeatability_block(from_saturated_only))
        for entry in from_saturated_only:
            entry["answers"]["urgency"]["probabilities"] = {"0": 0.01, "1": 0.98, "2": 0.01}
        assert "end of two of them" in "\n".join(build_repeatability_block(from_saturated_only))

    def test_the_parameter_is_named_rather_than_implied(self):
        assert CONCENTRATED_TOP_PROBABILITY == 0.9  # a reporting convention, not a finding


class TestLatencyStaysSeparate:
    def test_latency_is_reported_descriptively_and_marked_apart(self):
        records = identical_run()
        for entry, value in zip(records, (900.0, 610.0, 605.0, 612.0, 608.0)):
            entry["latency_ms"] = value
        text = "\n".join(build_repeatability_block(records))
        assert "descriptive only" in text
        assert "different measurements and are not combined" in text
        assert "900" in text  # the first request is shown, not dropped

    def test_the_first_request_is_named_as_such(self):
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "First request of the session (marked, not dropped)" in text

    def test_latency_is_printed_at_the_precision_the_log_stores(self):
        """Three decimals in, three decimals out -- the report must not drop a recorded digit."""
        records = identical_run()
        records[0]["latency_ms"] = 2449.657
        text = "\n".join(build_repeatability_block(records))
        assert "2449.657" in text


class TestOldRecordsStayReadable:
    def test_a_schema_two_record_contributes_no_transport_count(self):
        records = [record(index, schema_version=2) for index in range(1, 6)]
        transport = analyze(records)["transport"]
        assert transport["not_recorded"] == 5
        assert transport["single_attempt"] == 0
        text = "\n".join(build_repeatability_block(records))
        assert "retry behaviour is simply unknown" in text

    def test_a_schema_one_record_still_yields_its_semantic_metrics(self):
        records = [record(index, schema_version=1) for index in range(1, 6)]
        analysis = analyze(records)
        assert analysis["choice"]["observed"] == 5
        assert analysis["noul"]["summary"]["range"] == 0.0
        assert analysis["latency"]["first"] is None

    def test_an_empty_run_says_so_rather_than_printing_zeroes(self):
        text = "\n".join(build_repeatability_block([]))
        assert "No successful call" in text


class TestSecretHygiene:
    def test_no_credential_reaches_the_rendered_block(self, monkeypatch):
        monkeypatch.setenv("TYPESAFE_API_KEY", "planted-marker-render-me-never")
        text = "\n".join(build_repeatability_block(identical_run()))
        assert "planted-marker-render-me-never" not in text

    def test_the_analysis_reads_only_measurement_fields(self):
        """An unexpected extra field on a record must not be copied into the report."""
        records = identical_run()
        records[0]["secret_extra"] = "should-not-appear"
        assert "should-not-appear" not in "\n".join(build_repeatability_block(records))
