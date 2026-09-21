# CLAUDE.md — rules for coding agents working in this repository

This repo is a **measurement bench** for TypeSafe's Jev model. It is not a production app. Its
value comes entirely from the trustworthiness of `results/usage.jsonl`, so the rules below are
hard constraints, not preferences.

## Never reveal secrets

- The API key comes from `TYPESAFE_API_KEY` in the environment, or from `<repo>/.secrets/typesafe.env`
  — in that order, resolved by `jev_lab.client`. Those are the only two sources; never invent a
  third, and never add a fallback that "looks in a few likely places".
- **`.secrets/**` holds a live credential.** Never read, open, print, quote, copy, move, patch,
  rewrite, diff, hash, base64, or `cat` anything in it. Do not echo it "just to check". Do not ask
  the user to paste a key into the conversation, or into a file you write. If a task seems to need
  the file's contents, it does not: report `exists` / `missing` and stop.
- Never put a key in a tracked file — not in code, a test, a fixture, a doc, `.env`, an example, a
  commit message, or a branch name. `.secrets.example/**` is the committed template and holds a
  placeholder only.
- Never read the key from the environment either. Report credential state only through
  `jev_lab.client.api_key_status()`, which answers `missing`, `exists (source=…)`, or
  `unusable (<kind>)` and nothing else — never a value, a length, a prefix, a suffix, or a hash.
- Never include the key in an exception message, a traceback, or debug output. Route any text that
  might quote a server response through `jev_lab.client.scrub_secrets` before printing.
- Never run a test against the real `.secrets/typesafe.env`. `tests/conftest.py` redirects the
  loader and refuses to read that path; a test that needs a key writes a dummy one to a temp dir.
- Never add an experiment, script, or command that makes a real API call outside `run` / `run-all`,
  and never call the API from a test. Unit tests use `httpx2.MockTransport`; the suite blocks
  sockets outright.
- **Do not enable `TYPESAFE_LOG_LEVEL=debug`.** The SDK redacts secret headers but explicitly does
  **not** redact request/response *bodies*, so debug logging dumps full `state` and answers.

### This file is not a security boundary

Everything above is a convention that a cooperative agent follows. None of it is a mechanism, and
none of it should be described as one — not in this file, not in the README, not in a commit
message. An agent with file access can read `.secrets/typesafe.env`; saying otherwise would be a
false claim about a real credential.

The boundaries that exist are elsewhere, and they are the ones to keep working when you change
anything here:

- **`.gitignore`** — `.secrets/`, `*.env`, `*.secret`, `*.secrets`. The key cannot be committed by
  accident, and `git check-ignore` is the check that proves it, not a comment in a doc.
- **Fail closed** — an absent, empty, malformed, duplicated, or unreadable source stops the run
  before a request is sent, rather than proceeding with a guess.
- **No printing path** — the loader has no function that returns the key for display, status
  strings carry no derived identifier, and `scrub_secrets` covers error text that quotes a
  response. Code-side hygiene is what makes "never reveal" true rather than aspirational.
- **OS permissions** — the file's ACL, which this repository does not manage. Default Windows
  inheritance leaves it readable by more than the owner; the README says so.

If any of those four is weakened, the convention above stops being enough. Treat a change to any of
them as a security change.

## Official TypeSafe docs are the source of truth

- Docs index: <https://docs.typesafe.ai/llms.txt>. Append `.md` to a page path for raw Markdown.
- If a local observation seems to contradict the docs, trust the docs for *product semantics* and
  record the discrepancy as a finding. Do not silently "fix" the code to match a guess.
- Need a new capability? Read the relevant doc page before writing the integration.

## Separate official claims from local measurements

- A benchmark or performance statement from TypeSafe is an **OFFICIAL CLAIM** about *their*
  workload. It is not evidence about this machine, this account, or our inputs.
- Only a line in `results/usage.jsonl` produced by a run in this repo is a **local measurement**.
- When you write about a result, say which of the two you are reporting. Never present a vendor
  claim as something we verified, and never generalize one local run into a universal rule.

## Preserve append-only provenance

- `results/usage.jsonl` is append-only. Never rewrite, rewrite-in-place, truncate, reorder, or
  delete records — including "bad" rows. A failed call is data.
- One real API call produces exactly one record, written by `UsageRecorder`, whether it succeeds
  or raises. Do not bypass the recorder to make a call.
- Token counts are the `usage` values the API returned. **Never estimate tokens** and never store
  an estimate as a canonical number. Local derivations (latency, cost) are labelled as such.
- Always record both `model_requested` and `model_resolved`. An alias can move; only the response
  says which model actually answered.

## No unbounded API loops

- Every experiment declares a fixed case list up front. `--max-requests` is a hard ceiling and
  `run-all` refuses to start without an explicit budget that covers its tier.
- Never add a retry loop, a poll, a "keep trying until it works", or a repeat count without a
  documented constant cap. The SDK's own `RetryPolicy` stays at its default; do not disable or
  extend it without recording why.
- Remember that SDK retries make one logical request cost more wall-clock than its siblings. Use
  `transport_attempt_count` to see this; do not interpret latency without it.

## Latency is a measurement of the substrate as much as of the model

- **`retry_count` is dead.** The SDK sets `X-TypeSafe-Retry-Count` on the retried *request*, not on
  the response, so it is always `null` in the log. `null` means "not reported" and never "no
  retries happened". Do not backfill it, and do not reason from it.
- `transport_attempt_count` is the live field: outgoing HTTP attempts counted locally by
  `TransportProbe` for one logical call, with `attempt_count_source` naming the mechanism. It is a
  local observation, never a server-side statement.
- `transport_attempt_count == 1` licenses exactly one sentence: *this call was not observed to
  retry*. It does **not** license "this is pure model inference latency" — DNS, TCP, TLS,
  connection-pool state, server queueing, upstream load, and local scheduling all sit inside the
  same window. Never equate a single attempt with a clean model-latency measurement.
- A missing attempt count is not a zero. Say "not recorded".
- Never attribute a latency difference to an arm unless the comparison is order-balanced. Position
  and arm identity were perfectly confounded in the first three A/B experiments, which is why
  `case_sequence_index`, `logical_request_index_in_run`, `client_session_id`, and
  `is_first_request_in_client_session` are on every record.
- The probe's before/after delta assumes the CLI runs experiments **serially**. If concurrency is
  ever introduced, that assumption must be re-audited before any attempt count is trusted.

## Code does arithmetic; Jev does semantic judgment

- Never ask Jev to count, sum, compare numbers, interpolate between score levels, or compute a
  date difference. These are documented weaknesses, and the correct answer belongs in Python.
- Never use a `score` expectation to reconstruct an exact magnitude.
- When an experiment *does* probe a documented numeric limit, put the correct code-side answer
  next to it, and keep the probe small — the docs already state the limitation.
- Normalize score scales in code (`score / (len(criteria) - 1)`) before combining them.

## Prefer batching questions that share the same state

- Independent questions over one state belong in one request; questions are evaluated in parallel
  and cannot see each other's answers.
- Speculative questions are fine and often cheaper than a second round trip — but they still cost
  tokens, so measure rather than assume the trade is worth it.
- A second request is justified when an earlier answer is needed to fetch evidence, build new
  state, or choose the next options.

## Experiment design rules

- All state is **synthetic**. Never put real personal, customer, or proprietary data in a case.
- Keep every experiment small and its cost predictable. If an experiment would need a loop, it
  needs a documented cap instead.
- Any threshold used for gating is a **demonstration parameter**. The docs themselves use 0.5 on
  one page and 0.6 on another for the same example, and say thresholds must be tuned per domain.
  Never describe a threshold here as optimal or universal.
- Probes built from the *Jev 1.13 jaggedness* page exist to observe a known failure mode, not to
  demonstrate that the model is bad.

## Tests

- Unit tests must **never** touch the real API. Use the fake client pattern in
  `tests/test_experiments.py`.
- `uv run pytest` is the entry point. pytest is scoped to `tests/`; keep it that way, so a scratch
  script dropped at the repo root cannot be imported by the suite and reach the live API.
- When a change alters the record schema, bump `SCHEMA_VERSION` in `jev_lab/recorder.py` so old
  and new lines stay distinguishable.

## Cost

- Prices live only in `src/jev_lab/pricing.py`, keyed by the **resolved** model. Do not hardcode a
  rate anywhere else or copy a magic number into an experiment.
- An unknown resolved model yields `null` cost with an explicit `cost_basis` — never assume it
  shares another model's price.
- Cost is a local estimate. TypeSafe Console billing is authoritative; say so wherever cost is
  reported.
