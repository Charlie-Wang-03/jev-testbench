# Contributing

## Before anything else: there is no license yet

This repository has **no license**. Choosing one is a human decision that has not been made —
see [docs/OPEN_SOURCE_LICENSE_DECISION.md](docs/OPEN_SOURCE_LICENSE_DECISION.md). Until it is,
outside contributions cannot be merged under clear terms, so please open an issue rather than a
pull request. This section will be replaced when the decision lands.

## What this repository is

A measurement bench, not a product. Its value is the trustworthiness of `results/usage.jsonl`, and
everything below exists to protect that. The rules in [CLAUDE.md](CLAUDE.md) are the long version;
this page is the short one.

Good contributions here look like: a new experiment with a fixed case list and a stated budget; a
sharper analysis of records already in the log; a correction to something this repository claims
that the records do not support; a bug in a derived view; a better translation.

Contributions that will be rejected regardless of quality: a claim that generalizes one local run;
a vendor number restated as something we measured; a "fix" to a negative result; a rewritten log.

## Getting set up

Needs [uv](https://docs.astral.sh/uv/) and Python 3.13 (pinned in `.python-version`; uv will fetch
it). No API key, no account, no network:

```console
uv sync --locked
uv run pytest                     # the whole suite, sockets blocked
uv run ruff check .               # the lint gate CI runs
uv build                          # the distribution must build
```

The first command installs exactly the locked versions. If you change dependencies, run `uv lock`
and commit the updated `uv.lock` — CI runs `uv sync --locked` and fails on a stale lock.

## The non-negotiables

Each of these is a rule someone broke once and the failure mode is why it is written down.

- **Never a real API call from a test, and never a key in a tracked file.** Not in code, a test, a
  fixture, a doc, an example, a commit message, or a branch name. The suite blocks sockets and
  redirects the secret-file loader; use `httpx2.MockTransport` behind the real SDK instead, as
  [tests/test_experiments.py](tests/test_experiments.py) does. See [SECURITY.md](SECURITY.md).
- **`results/usage.jsonl` is append-only.** Never rewrite, reorder, truncate, or delete records —
  including rows for failed calls. A failed call is data. Its SHA-256 is published and cited, so
  appending to it invalidates a reference; new work gets its own directory and its own log.
- **Never estimate a token count.** The numbers are the `usage` values the API returned. Local
  derivations such as latency and cost are labelled as such.
- **Record both `model_requested` and `model_resolved`.** An alias can move; only the response says
  which model answered.
- **All state is synthetic.** No real personal, customer, or proprietary data, ever.
- **No unbounded loops.** Every experiment declares a fixed case list up front and a documented
  call ceiling. `run-all` refuses to start without a budget that covers its tier.
- **Code does arithmetic; Jev does semantic judgment.** Never ask the model to count, sum, compare
  numbers, interpolate between score levels, or compute a date difference. Normalize score scales
  in code.
- **Say which kind of claim you are making.** Official vendor claim, design assumption, local
  measurement, derived calculation, or limitation. Never present one as another.
- **Do not enable `TYPESAFE_LOG_LEVEL=debug`.** The SDK does not redact request or response bodies,
  so it prints full state and answers.

## Changing the record schema

If a change alters the record schema, bump `SCHEMA_VERSION` in
[src/jev_lab/recorder.py](src/jev_lab/recorder.py) so old and new lines stay distinguishable.
Downstream code must tolerate older rows: **a missing field means "not recorded," and `null` means
"not reported" — neither means zero.**

## Adding an experiment

1. Give it a **fixed case list** and a `call_ceiling`. Cost must be knowable before it runs.
2. Register it in `EXPERIMENTS` with a tier, so `list` and `run-all` see it.
3. If it changes only one thing between arms, check that nothing else moved with it. The first
   A/B experiments here confounded arm identity with request position, which is why
   `case_sequence_index`, `logical_request_index_in_run`, `client_session_id`, and
   `is_first_request_in_client_session` are on every record. Order-balance your arms.
4. State the limits of what the design can conclude, next to the numbers, not in a closing
   disclaimer.

If you are proposing a **claim** rather than a measurement, write the design and the thresholds
down and freeze them before the first request — [docs/experiments/](docs/experiments/) has the
pattern, and P3 is what it looks like when the frozen rule then kills the finding.

## Translations

The public documents come in English/Simplified Chinese pairs. A translation is a claim that both
halves say the same thing, so the pair is checked mechanically, not trusted:
[tests/test_docs_consistency.py](tests/test_docs_consistency.py) asserts that each half links to the
other, that every hash, verdict string, count, filename, and headline figure appears on both sides,
and that the canonical digests appear as contiguous 64-character runs.

The evidence artifacts — audits, preregistration, result, source registry — are canonical in
English and are deliberately **not** translated, so that the evidence layer has one textual source
rather than two that can drift. A test asserts that asymmetry too.

Write prose natively in each language rather than translating literally. What must match is what a
reader copies out.

## What CI runs

[.github/workflows/ci.yml](.github/workflows/ci.yml), offline and with no repository secret:
`uv sync --locked`, `uv run ruff check .`, `uv run pytest`, `uv build`, regeneration of the derived
reports, and a check that the committed `results/JEV_LOCAL_EVALUATION_FINAL.md` matches a fresh
regeneration. Run the same commands locally before opening a pull request.

Formatting is not enforced: `ruff format` is deliberately not adopted here, for the reasons
recorded in [pyproject.toml](pyproject.toml). Match the surrounding style instead.
