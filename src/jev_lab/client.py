"""TypeSafe client construction with credential hygiene.

The key is read in one order and only this order:

1. ``os.environ["TYPESAFE_API_KEY"]``, when it holds a non-blank value;
2. ``<repository root>/.secrets/typesafe.env``, a local file that is git-ignored;
3. nothing -- and every command that needs the API fails closed.

The environment wins so a rotated or one-off key can be set for a single shell without rewriting
the file on disk. When the environment holds a value, the file is **not read at all**: a broken
file cannot take down a session that was configured explicitly.

This module never writes the key, prints it, logs it, or echoes it in an error message. Callers can
ask *whether* a key is present and *which source* answered (``api_key_status``), and that is all the
CLI ever reports -- no value, length, prefix, suffix, hash, or fingerprint of the key is produced
anywhere.

The file format is deliberately not `.env` syntax. See ``read_secret_file``.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx2
from typesafe_sdk import ModelMetadata, TypeSafeClient
from typesafe_sdk.constants import DEFAULT_TIMEOUT

API_KEY_ENV = "TYPESAFE_API_KEY"

# Where a local key lives, relative to the repository root. One directory, one file, no search path.
SECRET_DIR_NAME = ".secrets"
SECRET_FILE_NAME = "typesafe.env"

# What the CLI is allowed to say about the credential.
EXISTS = "exists"
MISSING = "missing"
# A file that exists but cannot be used is neither of the above, and saying "missing" for a file
# with a duplicate key in it would send someone hunting for the wrong problem. The word carries the
# kind of problem and nothing about the contents.
UNUSABLE = "unusable"

# Which source answered. Named so a report can say where a key came from; neither name says
# anything about the key itself.
SOURCE_ENVIRONMENT = "environment"
SOURCE_LOCAL_SECRET_FILE = "local-secret-file"

REDACTED = "***"


def repo_root() -> Path:
    """The repository root, resolved from this file rather than from the working directory.

    ``src/jev_lab/client.py`` -> ``src/jev_lab`` -> ``src`` -> the root. A command started from any
    subdirectory of the repository finds the same file.

    Nothing is searched: this is the only path considered, and no directory outside the repository
    is ever looked in. An installed (non-editable) copy resolves inside ``site-packages``, where no
    ``.secrets/`` exists, so the failure mode there is *missing* rather than a key read from
    somewhere unexpected.
    """
    return Path(__file__).resolve().parents[2]


def secret_file_path() -> Path:
    """The single file this loader reads. Overridden in tests; never a search path."""
    return repo_root() / SECRET_DIR_NAME / SECRET_FILE_NAME


class MissingApiKeyError(RuntimeError):
    """Raised when a command that needs the API cannot find a key in either source."""

    def __init__(self) -> None:
        super().__init__(
            f"{API_KEY_ENV} is not set (status: {MISSING}). "
            f"Set {API_KEY_ENV} in the current environment, or create "
            f"{SECRET_DIR_NAME}/{SECRET_FILE_NAME} in the repository root. "
            "That file is git-ignored and must never be committed."
        )


class SecretFileError(RuntimeError):
    """Raised when a local secret file exists but cannot be used.

    The message names the file and the kind of problem, and nothing else: never a line from the
    file, never a value, never part of one. An unusable file is a hard error rather than a quiet
    fall back to *missing*, because a key that was meant to load and did not is a different
    situation from no key at all.
    """

    def __init__(self, kind: str, detail: str = "") -> None:
        self.kind = kind
        self.path = secret_file_path()
        message = f"{self.path.as_posix()} exists but could not be used ({kind})"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


def read_secret_file(path: Path | None = None) -> str | None:
    """The key in the local secret file, or ``None`` when the file is absent, empty, or blank.

    A deliberately narrow reader, not a `.env` implementation and not a shell:

    * the only name it accepts is ``TYPESAFE_API_KEY``, on a line of the form ``NAME=value`` with no
      space around the ``=``; a line naming anything else is an error, not a line to ignore, because
      a file that looks like configuration but is not would let someone believe a setting took
      effect that never did;
    * blank lines and lines whose first non-blank character is ``#`` are ignored;
    * the value is the rest of the line, with surrounding whitespace removed; there is no inline
      comment syntax, so a ``#`` inside the value is part of the value;
    * an empty value means *missing*, not "the empty key";
    * a second ``TYPESAFE_API_KEY`` line fails closed rather than letting the last one win;
    * nothing is expanded, substituted, sourced, executed, or interpreted. ``$(...)``, backticks,
      ``${VAR}``, ``export``, and quotes are ordinary characters here, and a line that is not a
      comment, a blank line, or an assignment is an error.

    Lines are split on newline only, so the exotic separators `str.splitlines` recognises cannot
    turn one line into two.
    """
    target = path or secret_file_path()
    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as error:
        raise SecretFileError("unreadable", error.strerror or type(error).__name__) from None

    value: str | None = None
    for number, raw in enumerate(text.split("\n"), start=1):
        line = raw[:-1] if raw.endswith("\r") else raw
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise SecretFileError(
                "malformed",
                f"line {number} is not a comment, a blank line, or a NAME=value assignment",
            )
        name, _, raw_value = line.partition("=")
        if name != API_KEY_ENV:
            raise SecretFileError("malformed", f"line {number} sets an unexpected name")
        if value is not None:
            raise SecretFileError("duplicate-key", f"line {number} repeats {API_KEY_ENV}")
        value = raw_value.strip()
    return value or None


def credential() -> tuple[str, str] | None:
    """The key and its source, or ``None`` when there is none.

    The environment is checked first and, when it holds a non-blank value, the file is not opened.
    The tuple's first element is a live credential: it goes to the SDK and nowhere else. Nothing in
    this project prints it, logs it, or stores it.

    Raises `SecretFileError` when the file exists and cannot be used -- but only on the path where
    the file was the source under consideration.
    """
    from_environment = os.environ.get(API_KEY_ENV, "").strip()
    if from_environment:
        return from_environment, SOURCE_ENVIRONMENT
    value = read_secret_file()
    return (value, SOURCE_LOCAL_SECRET_FILE) if value else None


def api_key() -> str | None:
    """The configured key, or ``None`` when there is none. The return value is a credential."""
    found = credential()
    return found[0] if found else None


def api_key_status() -> str:
    """Presence and, when present, which source answered.

    One of ``"missing"``, ``"exists (source=environment)"``,
    ``"exists (source=local-secret-file)"``, or ``"unusable (<kind>)"``. Deliberately not the key,
    not its length, not a prefix or a suffix, not a hash: nothing in this project needs a derived
    identifier for the credential, so none is produced.
    """
    try:
        found = credential()
    except SecretFileError as error:
        return f"{UNUSABLE} ({error.kind})"
    if found is None:
        return MISSING
    return f"{EXISTS} (source={found[1]})"


def require_api_key() -> None:
    """Raise `MissingApiKeyError` unless a key is configured.

    `SecretFileError` is deliberately not caught here: a key that failed to load is a different
    failure from no key at all, and reporting it is the point of failing closed.
    """
    if credential() is None:
        raise MissingApiKeyError


def scrub_secrets(text: str) -> str:
    """Replace any occurrence of the configured API key in ``text`` with ``***``.

    Defence in depth for the case where a server error body or a traceback quotes a credential back
    at us. With no key configured this is a no-op safe to call on any string.

    This runs on error paths, so it does not raise: when the secret file is unusable, no key from it
    was ever handed to the SDK and there is nothing from that source to scrub, so the fall back is
    the environment -- the only other source a credential could have come from.
    """
    try:
        key = api_key()
    except SecretFileError:
        key = os.environ.get(API_KEY_ENV, "").strip() or None
    return text.replace(key, REDACTED) if key else text


@contextmanager
def open_client(
    model: str | None = None,
    timeout: float | None = None,
    probe: "TransportProbe | None" = None,
) -> Iterator[TypeSafeClient]:
    """Yield a `TypeSafeClient`, closing it afterwards.

    `model` is the *requested* model; the model that actually answered is reported per response.
    Pass a `TransportProbe` to have outgoing HTTP attempts counted; without one, the client is
    built exactly as the SDK builds it and no instrumentation is installed.

    The key this module resolved is passed to the SDK explicitly, so both sources behave
    identically: left to itself the SDK reads only the environment and would not see a key that
    lives in the local file. The credential is read here and handed over; it is not logged or
    stored anywhere else.
    """
    found = credential()
    if found is None:
        raise MissingApiKeyError
    key, _source = found
    http_client = None if probe is None else probe.instrument(timeout=timeout or DEFAULT_TIMEOUT)
    client = TypeSafeClient(api_key=key, model=model, timeout=timeout, http_client=http_client)
    try:
        yield client
    finally:
        client.close()


def available_models(client: TypeSafeClient) -> list[ModelMetadata]:
    """List the models this account can access, in the order the API returns them."""
    return list(client.models.list().models)


# What the record says when the attempt count came from this instrumentation.
ATTEMPT_COUNT_SOURCE = "httpx_request_event_hook"


class TransportProbe:
    """Counts outgoing HTTP request attempts. It holds an integer and nothing else.

    The SDK sets ``X-TypeSafe-Retry-Count`` on the *retried request*, not the response, so a retry
    count cannot be read back off a response -- which is why the historical ``retry_count`` field is
    always null. This counts attempts where they actually happen instead: an `httpx2` request event
    hook fires once per wire attempt (`_send_handling_redirects`), so a logical call's attempts are
    the difference between two reads of the counter.

    The hook is deliberately the smallest thing that can work. It increments an integer and inspects
    nothing: it does not read a header, look at the URL, serialize, retain, or write the request.
    No credential, body, or header content can reach a log through it, because none of it is ever
    looked at. A probe that is never instrumented reports ``attached = False`` and produces no
    number at all, rather than a fabricated one.

    Scope: this counts *wire attempts*, so it includes a redirect hop if one ever occurred, not only
    SDK retries. It is a local observation of this process's traffic, never a server-side statement.
    """

    def __init__(self) -> None:
        self._attempts = 0
        self._attached = False

    def _on_request(self, _request: object) -> None:
        """The hook. It counts; the argument is intentionally never touched."""
        self._attempts += 1

    def instrument(self, *, timeout: float, transport: httpx2.BaseTransport | None = None) -> httpx2.Client:
        """Build the HTTP client the SDK will use, with this probe's counter wired to it.

        `timeout` must be the SDK's own default when the caller has no override: the SDK inherits
        its timeout from a supplied client, so an uninstrumented default here would silently change
        the timeout the bench runs under.
        """
        http_client = httpx2.Client(timeout=timeout, transport=transport, event_hooks={"request": [self._on_request]})
        self._attached = True
        return http_client

    @property
    def attempts(self) -> int:
        """Outgoing HTTP attempts observed so far in this client session."""
        return self._attempts

    @property
    def attached(self) -> bool:
        """Whether a client was actually built around this probe."""
        return self._attached
