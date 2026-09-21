"""Append-only JSONL provenance for every real API call.

``results/usage.jsonl`` is the canonical local measurement log. The token counts in it are the
ones the API reported in ``usage`` -- this project never estimates tokens. Wall-clock latency and
``estimated_cost_usd`` are measured/derived locally and labelled as such.
"""

import json
import statistics
import uuid
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from typesafe_sdk import SystemOneResponse

from .pricing import estimate_cost, token_counts

DEFAULT_RESULTS_DIR = Path("results")
USAGE_LOG_NAME = "usage.jsonl"

# The SDK sets this header on a *retry attempt's request* (`RequestState.attempt`), not on the
# response. This recorder reads it off the response, so it is only populated if the server echoes
# it back, which in practice it does not. ``retry_count is None`` therefore means "not reported"
# and must never be read as "no retries happened" -- which matters, because a retried call's
# latency includes backoff.
RETRY_COUNT_HEADER = "x-typesafe-retry-count"

# Bumped when the record shape changes, so old and new lines stay distinguishable.
# 2 added the request-position fields below; schema-1 rows simply lack them.
# 3 added the locally observed transport attempt counts; schema-1 and -2 rows lack those.
SCHEMA_VERSION = 3


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string with a ``Z`` suffix and second precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_run_id() -> str:
    """A short unique identifier grouping the records of one `run` invocation."""
    return uuid.uuid4().hex[:12]


def new_client_session_id() -> str:
    """A short random identifier for one client session.

    Randomness only: it is not derived from the credential, the machine, or the account, so it
    carries no secret and is safe to log. Its purpose is to group the calls that shared one
    ``TypeSafeClient`` -- and therefore one connection pool.
    """
    return uuid.uuid4().hex[:12]


def state_size(state: Any) -> tuple[int, int]:
    """Return ``(chars, utf8_bytes)`` for a state payload, measured as it is sent.

    Text is measured verbatim; structured state is measured as the SDK serializes it (compact
    JSON, non-ASCII characters kept literal rather than ``\\u``-escaped).
    """
    if isinstance(state, str):
        text = state
    else:
        text = json.dumps(state, ensure_ascii=False, separators=(",", ":"), default=str)
    return len(text), len(text.encode("utf-8"))


def serialize_answers(response: SystemOneResponse | None) -> dict[str, Any]:
    """Flatten a response's answers into JSON-safe dictionaries keyed by question name."""
    if response is None:
        return {}
    return {name: answer.model_dump(mode="json") for name, answer in response.answers.items()}


def question_types(questions: Mapping[str, Any]) -> list[str]:
    """Sorted, de-duplicated question type names, derived from SDK objects or raw dictionaries."""
    types = {
        question.type if hasattr(question, "type") else str(question.get("type", "unknown"))
        for question in questions.values()
    }
    return sorted(types)


@dataclass
class CallRecord:
    """One row of ``results/usage.jsonl``: everything measured about a single API call."""

    run_id: str
    experiment: str
    case_id: str
    model_requested: str
    question_count: int
    question_types: list[str]
    state_chars: int
    state_utf8_bytes: int
    timestamp_utc: str = field(default_factory=utc_now_iso)
    model_resolved: str | None = None
    request_id: str | None = None
    latency_ms: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    cost_basis: str = ""
    status: str = "pending"
    error_type: str | None = None
    retry_count: int | None = None
    # Request position. Latency is confounded by where a call sat in the session -- the first
    # request of a fresh client pays connection setup that its siblings do not -- so the position
    # is recorded rather than reconstructed after the fact. `None` means "not recorded", which is
    # the normal state for every schema-1 row; it never means zero.
    case_sequence_index: int | None = None
    logical_request_index_in_run: int | None = None
    client_session_id: str | None = None
    is_first_request_in_client_session: bool | None = None
    # Locally observed transport attempts for this logical call. `retry_count` above is the SDK's
    # own field, set on the request rather than the response, so it stays null forever; these are
    # counted in this process instead. All three are `None` when nothing was recorded -- which is
    # the normal state for every schema-1 and schema-2 row, and never means one attempt or zero
    # retries.
    transport_attempt_count: int | None = None
    transport_retry_count_observed: int | None = None
    attempt_count_source: str | None = None
    schema_version: int = SCHEMA_VERSION
    answers: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to a single JSONL line."""
        return json.dumps(self.__dict__, ensure_ascii=False, default=str)


class UsageRecorder:
    """Times API calls and appends one provenance line per call.

    The recorder is deliberately dumb about what it records: it takes the *response object* the
    API returned and copies the fields out of it, so a call that fails still produces a line.
    """

    def __init__(
        self,
        results_dir: Path | str = DEFAULT_RESULTS_DIR,
        run_id: str | None = None,
        client_session_id: str | None = None,
    ) -> None:
        self.results_dir = Path(results_dir)
        self.run_id = run_id or new_run_id()
        self._client_session_id = client_session_id or new_client_session_id()
        self._requests_in_run = 0
        self._requests_in_session = 0

    @property
    def client_session_id(self) -> str:
        """Identifier shared by the records produced through one client session."""
        return self._client_session_id

    def bind_client_session(self, client_session_id: str) -> None:
        """Point the recorder at a client session, resetting the session-relative counter.

        The CLI opens exactly one client per invocation, so this normally never fires. It exists so
        a caller that reuses a recorder across two sessions cannot mislabel the first request of
        the second session as a continuation of the first.
        """
        if client_session_id != self._client_session_id:
            self._client_session_id = client_session_id
            self._requests_in_session = 0

    @property
    def path(self) -> Path:
        """Path to the append-only JSONL log."""
        return self.results_dir / USAGE_LOG_NAME

    def append(self, record: CallRecord) -> None:
        """Append one record as a JSONL line, creating the results directory if needed."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(record.to_json())
            handle.write("\n")

    def begin(
        self,
        *,
        experiment: str,
        case_id: str,
        model_requested: str,
        questions: Mapping[str, Any],
        state: Any,
        notes: Mapping[str, Any] | None = None,
        case_sequence_index: int | None = None,
    ) -> "_PendingCall":
        """Start measuring a call; use the result as a context manager around ``client.system_one``."""
        chars, utf8_bytes = state_size(state)
        index_in_run = self._requests_in_run
        self._requests_in_run += 1
        first_in_session = self._requests_in_session == 0
        self._requests_in_session += 1
        return _PendingCall(
            recorder=self,
            record=CallRecord(
                run_id=self.run_id,
                experiment=experiment,
                case_id=case_id,
                model_requested=model_requested,
                question_count=len(questions),
                question_types=question_types(questions),
                state_chars=chars,
                state_utf8_bytes=utf8_bytes,
                case_sequence_index=case_sequence_index,
                logical_request_index_in_run=index_in_run,
                client_session_id=self._client_session_id,
                is_first_request_in_client_session=first_in_session,
                notes=dict(notes or {}),
            ),
        )


class _PendingCall:
    """Measures wall-clock latency around one API call and records the outcome either way."""

    def __init__(self, recorder: UsageRecorder, record: CallRecord) -> None:
        self._recorder = recorder
        self._record = record
        self._started = 0.0

    @property
    def record(self) -> CallRecord:
        """The record being built; experiments may copy it to annotate outputs."""
        return self._record

    def __enter__(self) -> "_PendingCall":
        self._started = perf_counter()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self._record.latency_ms = round((perf_counter() - self._started) * 1000, 3)
        if exc is not None:
            # Record the exception *class* only: messages can echo request content.
            self._record.status = "error"
            self._record.error_type = type(exc).__name__
        else:
            self._record.status = "ok"
        self._recorder.append(self._record)
        return False

    def succeeded(self, response: SystemOneResponse) -> SystemOneResponse:
        """Copy API-reported usage and derived cost out of a successful response."""
        self._record.model_resolved = response.model
        self._record.request_id = _safe_request_id(response)
        self._record.retry_count = _safe_retry_count(response)
        self._record.input_tokens, self._record.output_tokens, self._record.total_tokens = token_counts(response.usage)
        self._record.estimated_cost_usd, self._record.cost_basis = estimate_cost(response)
        self._record.answers = serialize_answers(response)
        return response


def _safe_request_id(response: SystemOneResponse) -> str | None:
    """Read the request ID, tolerating a response that did not carry the header."""
    try:
        return response.request_id
    except Exception:  # noqa: BLE001 - the SDK raises a plain TypeSafeError when the header is absent.
        return None


def _safe_retry_count(response: SystemOneResponse) -> int | None:
    """Read the SDK's retry count header, or ``None`` when it is absent or unparseable.

    A retried call still yields one response, so without this the logical request count and the
    wall-clock latency would not line up.
    """
    try:
        raw = response.raw_http_response.headers.get(RETRY_COUNT_HEADER)
    except Exception:  # noqa: BLE001 - response may not be backed by a raw HTTP response.
        return None
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def read_records(path: Path | str) -> Iterator[dict[str, Any]]:
    """Yield records from a JSONL log, skipping blank lines.

    A malformed line raises: silently dropping measurement rows would quietly corrupt a summary.
    """
    log = Path(path)
    if not log.exists():
        return
    with log.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{log}:{number}: malformed JSONL record") from error


def percentile(values: list[float], fraction: float) -> float | None:
    """Linear-interpolated percentile of ``values``, or ``None`` for an empty list."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate records into the summary metrics reported per experiment.

    Only ``status == "ok"`` rows contribute tokens and cost; failed calls still count toward
    ``requests`` so a summary can never look healthier than the log.
    """
    ok = [record for record in records if record.get("status") == "ok"]
    latencies = [float(record["latency_ms"]) for record in ok if record.get("latency_ms") is not None]
    costs = [float(record["estimated_cost_usd"]) for record in ok if record.get("estimated_cost_usd") is not None]
    input_tokens = sum(int(record.get("input_tokens") or 0) for record in ok)
    output_tokens = sum(int(record.get("output_tokens") or 0) for record in ok)
    unknown_cost = sum(1 for record in ok if record.get("estimated_cost_usd") is None)
    return {
        "requests": len(records),
        "errors": len(records) - len(ok),
        # Retry observation. `None` means "not recorded", which is every row written before the
        # transport probe existed -- it is counted separately and never read as zero retries.
        "attempts_not_recorded": sum(1 for record in records if record.get("transport_attempt_count") is None),
        "observed_retried_requests": sum(
            1 for record in records if (record.get("transport_retry_count_observed") or 0) >= 1
        ),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "mean_input_tokens": statistics.fmean([int(r.get("input_tokens") or 0) for r in ok]) if ok else None,
        "mean_output_tokens": statistics.fmean([int(r.get("output_tokens") or 0) for r in ok]) if ok else None,
        "mean_latency_ms": statistics.fmean(latencies) if latencies else None,
        "p50_latency_ms": percentile(latencies, 0.5),
        "min_latency_ms": min(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None,
        "estimated_cost_usd": sum(costs) if costs else (0.0 if not unknown_cost else None),
        "unknown_cost_requests": unknown_cost,
    }
