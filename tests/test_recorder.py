"""JSONL append/read, answer serialization, aggregation, and the missing-key path. All offline."""

import json

import pytest
from typesafe_sdk import Choice, ChoiceAnswer, Noul, NoulAnswer, ScoreAnswer

from jev_lab import client as client_module
from jev_lab.client import (
    EXISTS,
    MISSING,
    SOURCE_ENVIRONMENT,
    MissingApiKeyError,
    api_key_status,
    open_client,
    require_api_key,
    scrub_secrets,
)
from jev_lab.recorder import (
    SCHEMA_VERSION,
    CallRecord,
    UsageRecorder,
    new_run_id,
    percentile,
    read_records,
    serialize_answers,
    state_size,
    summarize,
)


class FakeResponse:
    """Stands in for a `SystemOneResponse` without touching the network."""

    def __init__(self, answers=None, request_id="req-123"):
        self.answers = answers or {}
        self.request_id = request_id


class TestMissingApiKeyPath:
    """The CLI must never proceed without a key, and must never reveal one."""

    def test_status_reports_missing_when_unset(self, monkeypatch):
        monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)
        assert api_key_status() == MISSING

    def test_status_reports_exists_when_set(self, monkeypatch):
        monkeypatch.setenv(client_module.API_KEY_ENV, "sk-not-a-real-key")
        assert api_key_status() == f"{EXISTS} (source={SOURCE_ENVIRONMENT})"

    def test_status_reports_missing_for_blank_value(self, monkeypatch):
        monkeypatch.setenv(client_module.API_KEY_ENV, "   ")
        assert api_key_status() == MISSING

    def test_status_never_contains_the_key(self, monkeypatch):
        secret = "sk-super-secret-value"
        monkeypatch.setenv(client_module.API_KEY_ENV, secret)
        assert secret not in api_key_status()
        assert api_key_status() == f"{EXISTS} (source={SOURCE_ENVIRONMENT})"

    def test_require_raises_when_unset(self, monkeypatch):
        monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)
        with pytest.raises(MissingApiKeyError):
            require_api_key()

    def test_open_client_raises_before_constructing_a_client(self, monkeypatch):
        monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)
        with pytest.raises(MissingApiKeyError):
            with open_client():
                pytest.fail("the client must not be yielded without a key")

    def test_missing_key_error_message_does_not_leak_a_value(self, monkeypatch):
        monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)
        with pytest.raises(MissingApiKeyError) as caught:
            require_api_key()
        assert client_module.API_KEY_ENV in str(caught.value)
        assert MISSING in str(caught.value)


class TestScrubSecrets:
    def test_replaces_the_configured_key(self, monkeypatch):
        monkeypatch.setenv(client_module.API_KEY_ENV, "sk-abc123")
        assert scrub_secrets("failed with key sk-abc123") == "failed with key ***"

    def test_is_a_noop_without_a_key(self, monkeypatch):
        monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)
        assert scrub_secrets("nothing to hide") == "nothing to hide"

    def test_leaves_other_text_untouched(self, monkeypatch):
        monkeypatch.setenv(client_module.API_KEY_ENV, "sk-abc123")
        assert scrub_secrets("request_id=req-9 status=200") == "request_id=req-9 status=200"


class TestStateSize:
    def test_text_state_is_measured_in_chars(self):
        assert state_size("hello") == (5, 5)

    def test_non_ascii_counts_bytes_not_chars(self):
        chars, utf8_bytes = state_size("你好")
        assert (chars, utf8_bytes) == (2, 6)

    def test_structured_state_is_measured_as_compact_json(self):
        chars, utf8_bytes = state_size({"a": 1})
        assert chars == len('{"a":1}')
        assert utf8_bytes == chars

    def test_structured_state_keeps_non_ascii_literal(self):
        chars, utf8_bytes = state_size({"k": "你"})
        assert chars == len('{"k":"你"}')
        assert utf8_bytes == chars + 2


class TestAnswerSerialization:
    def test_choice_answer_fields_survive_serialization(self):
        answer = ChoiceAnswer(choice="billing", confidence=0.82, probabilities={"billing": 0.82, "tech": 0.18})
        dumped = serialize_answers(FakeResponse({"intent": answer}))["intent"]
        assert dumped["type"] == "choice"
        assert dumped["choice"] == "billing"
        assert dumped["confidence"] == 0.82
        assert dumped["probabilities"] == {"billing": 0.82, "tech": 0.18}

    def test_score_answer_serializes_legend_and_probabilities(self):
        answer = ScoreAnswer(
            score=1.7,
            confidence=0.6,
            legend={0: "low", 1: "mid", 2: "high"},
            probabilities={0: 0.1, 1: 0.2, 2: 0.7},
        )
        dumped = serialize_answers(FakeResponse({"urgency": answer}))["urgency"]
        assert dumped["type"] == "score"
        assert dumped["score"] == 1.7
        assert dumped["legend"] == {"0": "low", "1": "mid", "2": "high"}
        assert dumped["probabilities"] == {"0": 0.1, "1": 0.2, "2": 0.7}

    def test_noul_answer_has_no_confidence_field(self):
        dumped = serialize_answers(FakeResponse({"spam": NoulAnswer(noul=0.98)}))["spam"]
        assert dumped == {"type": "noul", "noul": 0.98}
        assert "confidence" not in dumped

    def test_missing_response_serializes_to_empty(self):
        assert serialize_answers(None) == {}


class TestAppendAndRead:
    def make_record(self, **overrides) -> CallRecord:
        defaults = {
            "run_id": "run-1",
            "experiment": "01_primitives",
            "case_id": "case-a",
            "model_requested": "jev-latest",
            "question_count": 3,
            "question_types": ["choice", "noul", "score"],
            "state_chars": 10,
            "state_utf8_bytes": 10,
        }
        return CallRecord(**{**defaults, **overrides})

    def test_append_creates_the_file_and_one_line_per_record(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        recorder.append(self.make_record(case_id="case-a"))
        recorder.append(self.make_record(case_id="case-b"))
        assert len(recorder.path.read_text(encoding="utf-8").strip().splitlines()) == 2

    def test_append_is_additive_across_recorder_instances(self, tmp_path):
        UsageRecorder(tmp_path).append(self.make_record(case_id="case-a"))
        UsageRecorder(tmp_path).append(self.make_record(case_id="case-b"))
        records = list(read_records(tmp_path / "usage.jsonl"))
        assert [record["case_id"] for record in records] == ["case-a", "case-b"]

    def test_round_trip_preserves_core_fields(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        recorder.append(
            self.make_record(
                model_resolved="jev-1.13.0",
                request_id="req-1",
                latency_ms=812.5,
                input_tokens=120,
                output_tokens=12,
                total_tokens=132,
                estimated_cost_usd=0.00000504,
                cost_basis="jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
                status="ok",
                answers={"urgency": {"type": "score", "score": 1.7}},
            )
        )
        record = next(iter(read_records(recorder.path)))
        assert record["model_resolved"] == "jev-1.13.0"
        assert record["request_id"] == "req-1"
        assert record["latency_ms"] == 812.5
        assert (record["input_tokens"], record["output_tokens"], record["total_tokens"]) == (120, 12, 132)
        assert record["answers"]["urgency"]["score"] == 1.7

    def test_non_ascii_answers_are_written_literally(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        recorder.append(self.make_record(answers={"tone": {"type": "choice", "choice": "投诉"}}))
        assert "投诉" in recorder.path.read_text(encoding="utf-8")

    def test_read_missing_file_yields_nothing(self, tmp_path):
        assert list(read_records(tmp_path / "absent.jsonl")) == []

    def test_read_skips_blank_lines(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        path.write_text('{"experiment": "a"}\n\n{"experiment": "b"}\n', encoding="utf-8")
        assert len(list(read_records(path))) == 2

    def test_malformed_line_raises_rather_than_being_dropped(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        path.write_text('{"experiment": "a"}\nnot json\n', encoding="utf-8")
        with pytest.raises(ValueError):
            list(read_records(path))

    def test_run_id_is_stable_within_a_recorder_and_unique_across_them(self, tmp_path):
        first, second = UsageRecorder(tmp_path), UsageRecorder(tmp_path)
        assert first.run_id == first.run_id
        assert first.run_id != second.run_id

    def test_generated_run_ids_are_unique(self):
        assert len({new_run_id() for _ in range(50)}) == 50


class TestPendingCall:
    """The context manager must record a line whether the call succeeds or fails."""

    def make_pending(self, tmp_path, **overrides):
        recorder = UsageRecorder(tmp_path)
        return recorder.begin(
            experiment="01_primitives",
            case_id="case-a",
            model_requested="jev-latest",
            questions={"a": Noul(instructions="x")},
            state="state text",
            **overrides,
        )

    def test_successful_call_records_ok_status_and_latency(self, tmp_path):
        with self.make_pending(tmp_path) as pending:
            pending.record.model_resolved = "jev-1.13.0"
            pending.record.input_tokens = 10
            pending.record.status_note = None
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["status"] == "ok"
        assert record["latency_ms"] is not None and record["latency_ms"] >= 0

    def test_failed_call_still_appends_a_row(self, tmp_path):
        with pytest.raises(RuntimeError):
            with self.make_pending(tmp_path):
                raise RuntimeError("boom: secret-ish detail")
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["status"] == "error"
        assert record["error_type"] == "RuntimeError"

    def test_error_rows_record_only_the_exception_class(self, tmp_path):
        with pytest.raises(ValueError):
            with self.make_pending(tmp_path):
                raise ValueError("state content that should not be persisted")
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert "state content that should not be persisted" not in json.dumps(record)

    def test_question_metadata_is_captured_from_question_objects(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        with recorder.begin(
            experiment="01_primitives",
            case_id="case-mixed",
            model_requested="jev-latest",
            questions={
                "tone": Choice(instructions="What is the tone?", criteria={"calm": None, "angry": None}),
                "spam": Noul(instructions="is it spam?"),
            },
            state={"a": 1},
        ):
            pass
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["question_count"] == 2
        assert record["question_types"] == ["choice", "noul"]

    def test_raw_dict_questions_are_accepted(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        with recorder.begin(
            experiment="01_primitives",
            case_id="case-dict",
            model_requested="jev-latest",
            questions={"q": {"type": "score", "criteria": ["a", "b"]}},
            state="x",
        ):
            pass
        record = next(iter(read_records(tmp_path / "usage.jsonl")))
        assert record["question_types"] == ["score"]


class TestPercentile:
    def test_empty_returns_none(self):
        assert percentile([], 0.5) is None

    def test_single_value(self):
        assert percentile([7.0], 0.5) == 7.0

    def test_median_of_even_count_interpolates(self):
        assert percentile([10.0, 20.0], 0.5) == 15.0

    def test_median_of_odd_count_is_the_middle_value(self):
        assert percentile([30.0, 10.0, 20.0], 0.5) == 20.0

    def test_zero_and_one_are_min_and_max(self):
        values = [5.0, 1.0, 9.0]
        assert percentile(values, 0.0) == 1.0
        assert percentile(values, 1.0) == 9.0


class TestSummarize:
    def make_records(self):
        return [
            {
                "experiment": "01_primitives",
                "status": "ok",
                "latency_ms": 100.0,
                "input_tokens": 100,
                "output_tokens": 10,
                "estimated_cost_usd": 0.0000042,
            },
            {
                "experiment": "01_primitives",
                "status": "ok",
                "latency_ms": 300.0,
                "input_tokens": 200,
                "output_tokens": 20,
                "estimated_cost_usd": 0.0000084,
            },
        ]

    def test_totals_and_means(self):
        metrics = summarize(self.make_records())
        assert metrics["requests"] == 2
        assert metrics["input_tokens"] == 300
        assert metrics["output_tokens"] == 30
        assert metrics["total_tokens"] == 330
        assert metrics["mean_input_tokens"] == 150
        assert metrics["mean_output_tokens"] == 15
        assert metrics["mean_latency_ms"] == 200.0
        assert metrics["p50_latency_ms"] == 200.0
        assert metrics["min_latency_ms"] == 100.0
        assert metrics["max_latency_ms"] == 300.0

    def test_cost_is_summed(self):
        assert round(summarize(self.make_records())["estimated_cost_usd"], 12) == round(0.0000042 * 3, 12)

    def test_error_rows_count_but_do_not_contribute_tokens_or_latency(self):
        # Latency and tokens summarize successful calls; failures are visible via `errors`.
        records = [*self.make_records(), {"experiment": "01_primitives", "status": "error", "latency_ms": 50.0}]
        metrics = summarize(records)
        assert metrics["requests"] == 3
        assert metrics["errors"] == 1
        assert metrics["input_tokens"] == 300
        assert metrics["mean_latency_ms"] == 200.0

    def test_unknown_cost_rows_are_flagged(self):
        records = [
            {
                "status": "ok",
                "latency_ms": 10.0,
                "input_tokens": 5,
                "output_tokens": 1,
                "estimated_cost_usd": None,
            }
        ]
        metrics = summarize(records)
        assert metrics["unknown_cost_requests"] == 1
        assert metrics["estimated_cost_usd"] is None

    def test_empty_input_is_all_none_or_zero(self):
        metrics = summarize([])
        assert metrics["requests"] == 0
        assert metrics["input_tokens"] == 0
        assert metrics["mean_latency_ms"] is None


class TestRequestPositionProvenance:
    """Latency is confounded by where a call sat in the session, so position is recorded, not inferred."""

    def _begin(self, recorder, case_id="case", index=None):
        return recorder.begin(
            experiment="exp",
            case_id=case_id,
            model_requested="jev-latest",
            questions={"q": Noul(instructions="?")},
            state="state",
            case_sequence_index=index,
        )

    def test_a_record_carries_its_position_and_session(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        with self._begin(recorder, index=0):
            pass
        record = next(iter(read_records(recorder.path)))
        assert record["case_sequence_index"] == 0
        assert record["logical_request_index_in_run"] == 0
        assert record["client_session_id"] == recorder.client_session_id
        assert record["is_first_request_in_client_session"] is True

    def test_only_the_first_call_of_a_session_is_flagged_first(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        for index, case_id in enumerate(["a", "b", "c"]):
            with self._begin(recorder, case_id=case_id, index=index):
                pass
        records = list(read_records(recorder.path))
        assert [record["logical_request_index_in_run"] for record in records] == [0, 1, 2]
        assert [record["case_sequence_index"] for record in records] == [0, 1, 2]
        assert [record["is_first_request_in_client_session"] for record in records] == [True, False, False]

    def test_every_record_in_one_run_shares_a_session_id(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        for _ in range(3):
            with self._begin(recorder):
                pass
        sessions = {record["client_session_id"] for record in read_records(recorder.path)}
        assert sessions == {recorder.client_session_id}

    def test_a_rebound_session_restarts_its_counter(self, tmp_path):
        """Reusing a recorder across sessions must not mislabel the new session's first call."""
        recorder = UsageRecorder(tmp_path)
        with self._begin(recorder):
            pass
        recorder.bind_client_session("second-session")
        with self._begin(recorder):
            pass
        records = list(read_records(recorder.path))
        assert records[0]["is_first_request_in_client_session"] is True
        assert records[1]["is_first_request_in_client_session"] is True
        assert records[1]["client_session_id"] == "second-session"
        # The run-wide index keeps counting: the run did not restart.
        assert records[1]["logical_request_index_in_run"] == 1

    def test_binding_the_same_session_again_changes_nothing(self, tmp_path):
        recorder = UsageRecorder(tmp_path)
        recorder.bind_client_session(recorder.client_session_id)
        with self._begin(recorder):
            pass
        assert next(iter(read_records(recorder.path)))["is_first_request_in_client_session"] is True

    def test_a_session_id_is_random_and_not_derived_from_anything_secret(self):
        first, second = UsageRecorder("unused-a"), UsageRecorder("unused-b")
        assert first.client_session_id != second.client_session_id
        assert len(first.client_session_id) == 12
        assert all(character in "0123456789abcdef" for character in first.client_session_id)

    def test_a_failed_call_still_records_its_position(self, tmp_path):
        """Position is set before the call, so an error row carries it too."""
        recorder = UsageRecorder(tmp_path)
        with pytest.raises(RuntimeError):
            with self._begin(recorder, index=0):
                raise RuntimeError("boom")
        record = next(iter(read_records(recorder.path)))
        assert record["status"] == "error"
        assert record["logical_request_index_in_run"] == 0
        assert record["is_first_request_in_client_session"] is True


class TestSchemaOneRowsStayReadable:
    """Fields added in schema 2 must never break a log that predates them."""

    LEGACY = {
        "run_id": "aaaaaaaaaaaa",
        "experiment": "01_primitives",
        "case_id": "legacy_case",
        "model_requested": "jev-latest",
        "question_count": 1,
        "question_types": ["noul"],
        "state_chars": 10,
        "state_utf8_bytes": 10,
        "latency_ms": 500.0,
        "input_tokens": 100,
        "output_tokens": 10,
        "total_tokens": 110,
        "estimated_cost_usd": 100 * 0.042 / 1_000_000,
        "cost_basis": "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
        "status": "ok",
        "error_type": None,
        "retry_count": None,
        "schema_version": 1,
        "answers": {},
        "notes": {},
    }

    def _write(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        path.write_text(json.dumps(self.LEGACY) + "\n", encoding="utf-8")
        return path

    def test_a_schema_one_row_reads_back_without_the_new_keys(self, tmp_path):
        record = next(iter(read_records(self._write(tmp_path))))
        assert record["schema_version"] == 1  # the legacy literal, not the current constant
        for key in (
            "case_sequence_index",
            "logical_request_index_in_run",
            "client_session_id",
            "is_first_request_in_client_session",
        ):
            assert key not in record

    def test_a_schema_one_row_still_summarizes(self, tmp_path):
        summary = summarize(list(read_records(self._write(tmp_path))))
        assert summary["requests"] == 1
        assert summary["input_tokens"] == 100
        assert summary["errors"] == 0

    def test_old_and_new_rows_coexist_in_one_log(self, tmp_path):
        path = self._write(tmp_path)
        recorder = UsageRecorder(tmp_path)
        with recorder.begin(
            experiment="01_primitives",
            case_id="new_case",
            model_requested="jev-latest",
            questions={"q": Noul(instructions="?")},
            state="state",
        ):
            pass
        records = list(read_records(path))
        assert len(records) == 2
        assert records[0]["schema_version"] == 1
        assert records[1]["schema_version"] == SCHEMA_VERSION
        assert summarize(records)["requests"] == 2


class TestSchemaTwoRowsStayReadable:
    """Schema 2 added position; schema 3 added attempt counts. Neither may break the other."""

    SCHEMA_TWO = {
        "run_id": "bbbbbbbbbbbb",
        "experiment": "01_primitives",
        "case_id": "schema_two_case",
        "model_requested": "jev-latest",
        "question_count": 1,
        "question_types": ["noul"],
        "state_chars": 10,
        "state_utf8_bytes": 10,
        "latency_ms": 500.0,
        "input_tokens": 100,
        "output_tokens": 10,
        "total_tokens": 110,
        "estimated_cost_usd": 100 * 0.042 / 1_000_000,
        "cost_basis": "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
        "status": "ok",
        "error_type": None,
        "retry_count": None,
        "case_sequence_index": 0,
        "logical_request_index_in_run": 0,
        "client_session_id": "aaaa",
        "is_first_request_in_client_session": True,
        "schema_version": 2,
        "answers": {},
        "notes": {},
    }

    def _write(self, tmp_path):
        path = tmp_path / "usage.jsonl"
        path.write_text(json.dumps(self.SCHEMA_TWO) + "\n", encoding="utf-8")
        return path

    def test_a_schema_two_row_reads_back_with_its_position_intact(self, tmp_path):
        record = next(iter(read_records(self._write(tmp_path))))
        assert record["logical_request_index_in_run"] == 0
        assert record["is_first_request_in_client_session"] is True

    def test_a_schema_two_row_has_no_attempt_count_and_is_not_given_one(self, tmp_path):
        record = next(iter(read_records(self._write(tmp_path))))
        for key in ("transport_attempt_count", "transport_retry_count_observed", "attempt_count_source"):
            assert key not in record

    def test_summarize_counts_unrecorded_attempts_separately_from_retries(self, tmp_path):
        """The two must never collapse: 'unknown' is not 'no retries happened'."""
        summary = summarize(list(read_records(self._write(tmp_path))))
        assert summary["attempts_not_recorded"] == 1
        assert summary["observed_retried_requests"] == 0

    def test_a_recorded_single_attempt_is_not_counted_as_unrecorded(self, tmp_path):
        record = dict(self.SCHEMA_TWO, schema_version=SCHEMA_VERSION, transport_attempt_count=1,
                      transport_retry_count_observed=0, attempt_count_source="httpx_request_event_hook")
        summary = summarize([record])
        assert summary["attempts_not_recorded"] == 0
        assert summary["observed_retried_requests"] == 0

    def test_a_recorded_retry_is_counted(self, tmp_path):
        record = dict(self.SCHEMA_TWO, schema_version=SCHEMA_VERSION, transport_attempt_count=3,
                      transport_retry_count_observed=2, attempt_count_source="httpx_request_event_hook")
        summary = summarize([record])
        assert summary["attempts_not_recorded"] == 0
        assert summary["observed_retried_requests"] == 1
