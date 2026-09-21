"""End-to-end plumbing check through the real SDK, with no network access.

These tests build a genuine `TypeSafeClient` on an `httpx2.MockTransport`, so the SDK's own request
encoding and response decoding run for real: the same path a live call takes, minus the socket.
The API key is a dummy string; nothing here reaches TypeSafe.
"""

import contextlib
import inspect
import json

import httpx2
import pytest
from typesafe_sdk import RetryPolicy, TypeSafeAuthenticationError, TypeSafeClient

from jev_lab import __main__ as cli
from jev_lab import experiments as lab
from jev_lab.client import TransportProbe
from jev_lab.experiments import get_experiment, run_experiment
from jev_lab.recorder import UsageRecorder, read_records
from jev_lab.report import generate_report

DUMMY_KEY = "not-a-real-key"
REQUEST_ID = "req-test-0001"

# Shapes mirror the documented API response for a Choice + Score + Noul request.
ANSWERS = {
    "department": {
        "type": "choice",
        "choice": "billing",
        "confidence": 0.81,
        "probabilities": {"billing": 0.88, "account": 0.12, "feature_request": 0.0, "other": 0.0},
    },
    "severity": {
        "type": "score",
        "score": 1.43,
        "confidence": 0.35,
        "legend": {"0": "Cosmetic", "1": "Degraded", "2": "Blocking"},
        "probabilities": {"0": 0.0, "1": 0.57, "2": 0.43},
    },
    "repeat_contact": {"type": "noul", "noul": 0.93},
}

BODY = {"model": "jev-1.13.0", "answers": ANSWERS, "usage": {"input_tokens": 328, "output_tokens": 34}}


def make_client(handler, body=None, status=200, headers=None):
    """A real TypeSafeClient wired to a mock transport instead of the network."""

    def default_handler(request):
        return httpx2.Response(
            status,
            json=body if body is not None else BODY,
            headers=headers if headers is not None else {"x-typesafe-request-id": REQUEST_ID},
        )

    return TypeSafeClient(
        api_key=DUMMY_KEY,
        transport=httpx2.MockTransport(handler or default_handler),
    )


class TestRealSdkRoundTrip:
    def test_response_decodes_into_typed_answers(self, tmp_path):
        captured = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx2.Response(200, json=BODY, headers={"x-typesafe-request-id": REQUEST_ID})

        with make_client(handler) as client:
            records = run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )

        assert len(records) == 1
        assert captured["body"]["state"] == get_experiment("01_primitives").cases()[0].state
        assert set(captured["body"]["questions"]) == {"department", "severity", "repeat_contact"}

    def test_usage_and_request_id_come_from_the_api_response(self, tmp_path):
        with make_client(None) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["model_resolved"] == "jev-1.13.0"
        assert record["request_id"] == REQUEST_ID
        assert (record["input_tokens"], record["output_tokens"], record["total_tokens"]) == (328, 34, 362)

    def test_cost_matches_the_published_rate_for_the_resolved_model(self, tmp_path):
        with make_client(None) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        # 328 input tokens x $0.042 / 1e6, output free.
        assert record["estimated_cost_usd"] == 328 * 0.042 / 1_000_000
        assert "jev-1.13.0" in record["cost_basis"]

    def test_answers_are_persisted_in_full(self, tmp_path):
        with make_client(None) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        answers = next(iter(read_records(tmp_path / "usage.jsonl")))["answers"]
        assert answers["department"]["choice"] == "billing"
        assert answers["severity"]["score"] == 1.43
        assert answers["repeat_contact"]["noul"] == 0.93

    def test_sdk_coerces_score_level_keys_to_integers(self, tmp_path):
        """The wire format keys levels by string; the SDK's answer maps are int-keyed."""
        with make_client(None) as client:
            response = client.system_one(
                state="x",
                questions=get_experiment("01_primitives").cases()[0].questions,
            )
        score = response.scores["severity"]
        assert set(score.probabilities) == {0, 1, 2}
        assert set(score.legend) == {0, 1, 2}

    def test_noul_answer_carries_no_confidence(self, tmp_path):
        with make_client(None) as client:
            response = client.system_one(
                state="x",
                questions=get_experiment("01_primitives").cases()[0].questions,
            )
        assert not hasattr(response.nouls["repeat_contact"], "confidence")

    def test_an_unknown_resolved_model_records_no_cost(self, tmp_path):
        body = {**BODY, "model": "jev-9.9.9"}
        with make_client(None, body=body) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["model_resolved"] == "jev-9.9.9"
        assert record["estimated_cost_usd"] is None
        assert record["cost_basis"].startswith("unknown")


class TestCliPlumbingAgainstTheLog:
    def test_run_then_report_produces_a_populated_summary(self, tmp_path):
        with make_client(None) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        summary = generate_report(tmp_path)
        assert summary["01_primitives"]["requests"] == 1
        assert summary["01_primitives"]["input_tokens"] == 328
        assert summary["TOTAL"]["total_tokens"] == 362
        csv_text = (tmp_path / "summary.csv").read_text(encoding="utf-8")
        assert "01_primitives" in csv_text
        assert "TOTAL" in csv_text

    def test_the_log_is_append_only_across_runs(self, tmp_path):
        for _ in range(2):
            with make_client(None) as client:
                run_experiment(
                    get_experiment("01_primitives"),
                    client=client,
                    recorder=UsageRecorder(tmp_path),
                )
        records = list(read_records(tmp_path / "usage.jsonl"))
        assert len(records) == 2
        assert records[0]["timestamp_utc"] <= records[1]["timestamp_utc"]

    def test_a_401_is_recorded_and_aborts_the_run(self, tmp_path):
        from typesafe_sdk import TypeSafeAuthenticationError

        def handler(request):
            return httpx2.Response(401, json={"error": "invalid api key"})

        recorder = UsageRecorder(tmp_path)
        try:
            with make_client(handler) as client:
                run_experiment(get_experiment("02_structured_addressing"), client=client, recorder=recorder)
        except TypeSafeAuthenticationError:
            pass
        else:
            raise AssertionError("a 401 should raise TypeSafeAuthenticationError")

        records = list(read_records(recorder.path))
        assert len(records) == 1
        assert records[0]["status"] == "error"
        assert records[0]["error_type"] == "TypeSafeAuthenticationError"

    def test_a_500_is_retried_by_the_sdk_and_still_records_once(self, tmp_path):
        attempts = {"n": 0}

        def handler(request):
            attempts["n"] += 1
            if attempts["n"] == 1:
                return httpx2.Response(500, json={"error": "boom"})
            return httpx2.Response(200, json=BODY, headers={"x-typesafe-request-id": REQUEST_ID})

        with make_client(handler) as client:
            records = run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        # One logical request in the log, two HTTP attempts on the wire.
        assert len(records) == 1
        assert attempts["n"] == 2
        assert len(list(read_records(tmp_path / "usage.jsonl"))) == 1


@pytest.fixture
def cli_offline(monkeypatch, tmp_path):
    """Point the CLI's client seam at a mock transport so `main(...)` runs with no key and no network."""
    monkeypatch.setattr(cli, "require_api_key", lambda: None)
    monkeypatch.setattr(cli, "open_client", lambda **kwargs: contextlib.nullcontext(make_client(None)))
    return tmp_path


class TestCliCommandSurface:
    """The literal Section G commands, driven through argv with the transport mocked out."""

    def test_run_01_primitives_then_report(self, cli_offline, capsys):
        exit_code = cli.main(["--results-dir", str(cli_offline), "run", "01_primitives"])
        assert exit_code == 0

        printed = capsys.readouterr().out
        assert "running 1 experiment(s), 1 API call(s)" in printed
        assert "jev-1.13.0" in printed  # the resolved model is surfaced to the operator
        assert "wrote 1 record(s)" in printed

        assert cli.main(["--results-dir", str(cli_offline), "report"]) == 0
        assert (cli_offline / "usage.jsonl").is_file()
        assert (cli_offline / "summary.csv").is_file()
        assert (cli_offline / "summary.md").is_file()

    def test_run_refuses_a_budget_it_cannot_cover(self, cli_offline, capsys):
        exit_code = cli.main(
            ["--results-dir", str(cli_offline), "run", "03_parallel_questions", "--max-requests", "2"]
        )
        assert exit_code == 1
        assert "refusing to run" in capsys.readouterr().out
        assert not (cli_offline / "usage.jsonl").exists()

    def test_run_all_refuses_without_an_explicit_budget(self, cli_offline, capsys):
        expected = lab.total_cases(lab.experiments_for_tier(lab.CORE))
        assert cli.main(["--results-dir", str(cli_offline), "run-all", "--tier", "core"]) == 1
        assert f"needs {expected} API calls" in capsys.readouterr().out

    def test_report_without_records_writes_nothing(self, tmp_path, capsys):
        assert cli.main(["--results-dir", str(tmp_path), "report"]) == 0
        assert not (tmp_path / "summary.csv").exists()
        assert not (tmp_path / "summary.md").exists()

    def test_list_needs_no_credential(self, capsys):
        assert cli.main(["list"]) == 0
        assert "TYPESAFE_API_KEY: missing" in capsys.readouterr().out


class TestTransportAttemptInstrumentation:
    """The transport probe counts real wire attempts, through the real SDK, with no network.

    Retry behaviour is the SDK's own: `RetryPolicy()` defaults to two retries over 408/429/5xx.
    Backoff is zeroed here so the tests exercise the retry *count* without sleeping through it.
    """

    def _probe_and_client(self, handler, *, max_retries=2):
        probe = TransportProbe()
        http_client = probe.instrument(
            timeout=5.0,
            transport=httpx2.MockTransport(handler),
        )
        client = TypeSafeClient(
            api_key=DUMMY_KEY,
            http_client=http_client,
            retry=RetryPolicy(max_retries=max_retries, backoff_initial=0, backoff_max=0),
        )
        return probe, client

    @staticmethod
    def _ok():
        return httpx2.Response(200, json=BODY, headers={"x-typesafe-request-id": REQUEST_ID})

    def _run(self, tmp_path, handler, **kwargs):
        probe, client = self._probe_and_client(handler, **kwargs)
        with client:
            records = run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
                probe=probe,
            )
        return probe, records, next(iter(read_records(tmp_path / "usage.jsonl")))

    def test_success_on_the_first_attempt(self, tmp_path):
        _, _, record = self._run(tmp_path, lambda request: self._ok())
        assert record["transport_attempt_count"] == 1
        assert record["transport_retry_count_observed"] == 0
        assert record["attempt_count_source"] == "httpx_request_event_hook"

    @pytest.mark.parametrize("status", [500, 529])
    def test_a_retryable_failure_then_success(self, tmp_path, status):
        """529 Overloaded is inside the SDK's default retry set, same as 5xx."""
        attempts = {"n": 0}

        def handler(request):
            attempts["n"] += 1
            return self._ok() if attempts["n"] > 1 else httpx2.Response(status, json={"error": "boom"})

        _, _, record = self._run(tmp_path, handler)
        assert record["status"] == "ok"
        assert record["transport_attempt_count"] == attempts["n"] > 1
        assert record["transport_retry_count_observed"] == record["transport_attempt_count"] - 1

    def test_a_non_retryable_401_is_one_attempt(self, tmp_path):
        def handler(request):
            return httpx2.Response(401, json={"error": "invalid api key"})

        probe, client = self._probe_and_client(handler)
        try:
            with client:
                run_experiment(
                    get_experiment("01_primitives"),
                    client=client,
                    recorder=UsageRecorder(tmp_path),
                    probe=probe,
                )
        except TypeSafeAuthenticationError:
            pass
        else:
            raise AssertionError("a 401 should raise TypeSafeAuthenticationError")

        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["status"] == "error"
        assert record["transport_attempt_count"] == 1
        assert record["transport_retry_count_observed"] == 0

    def test_retry_exhaustion_still_records_the_attempt_count(self, tmp_path):
        """The record must carry the count even when the logical call ultimately fails.

        `run_experiment` records a failed case and moves on rather than raising, so the attempt
        count is the only place the exhaustion is visible.
        """
        def handler(request):
            return httpx2.Response(500, json={"error": "always down"})

        probe, client = self._probe_and_client(handler, max_retries=2)
        with client:
            assert run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
                probe=probe,
            ) == []
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["status"] == "error"
        assert record["transport_attempt_count"] == 3  # initial + max_retries
        assert record["transport_retry_count_observed"] == 2

    def test_the_probe_retains_nothing_from_the_request(self, tmp_path):
        """The hook is a counter. It must not hold, copy, or inspect any part of a request."""
        probe, _, _ = self._run(tmp_path, lambda request: self._ok())
        assert set(vars(probe)) == {"_attempts", "_attached"}
        assert all(isinstance(value, (int, bool)) for value in vars(probe).values())

    def test_the_hook_never_touches_headers_or_credentials(self):
        """The hook is the only code that ever receives a request, so it is the surface to check."""
        hook = inspect.getsource(TransportProbe._on_request).lower()
        for forbidden in ("headers", "authorization", "api_key", "content", "body", "url", "request."):
            assert forbidden not in hook

    def test_no_credential_reaches_the_record(self, tmp_path):
        _, _, record = self._run(tmp_path, lambda request: self._ok())
        assert DUMMY_KEY not in json.dumps(record)

    def test_two_logical_calls_in_one_session_have_independent_counts(self, tmp_path):
        """The counter is cumulative; each record must report its own delta, not a running total."""
        probe, client = self._probe_and_client(lambda request: self._ok())
        recorder = UsageRecorder(tmp_path)
        with client:
            run_experiment(
                get_experiment("02_structured_addressing"),
                client=client,
                recorder=recorder,
                probe=probe,
            )
        records = list(read_records(recorder.path))
        assert len(records) == 2
        assert [record["transport_attempt_count"] for record in records] == [1, 1]
        assert probe.attempts == 2  # the counter itself did accumulate across the session

    def test_a_probe_that_was_never_instrumented_records_nothing(self, tmp_path):
        """A fabricated count is worse than a missing one, so an unwired probe writes no number."""
        probe, client = self._probe_and_client(lambda request: self._ok())
        unwired = TransportProbe()
        with client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
                probe=unwired,
            )
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert unwired.attached is False
        assert record["transport_attempt_count"] is None
        assert record["transport_retry_count_observed"] is None
        assert record["attempt_count_source"] is None

    def test_running_without_a_probe_records_nothing_rather_than_zero(self, tmp_path):
        with make_client(None) as client:
            run_experiment(
                get_experiment("01_primitives"),
                client=client,
                recorder=UsageRecorder(tmp_path),
            )
        assert next(iter(read_records(tmp_path / "usage.jsonl")))["transport_attempt_count"] is None
