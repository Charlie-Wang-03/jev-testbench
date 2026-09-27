# Reproducibility

**English** | [简体中文](reproducibility.zh-CN.md)

Two paths through this repository. The first needs nothing but a clone. The second spends money.

---

## Requirements

| | |
|---|---|
| OS | Any (developed on Windows 11) |
| Python | 3.13 (pinned in `.python-version`) |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| SDK | `typesafe-sdk`, pinned in `pyproject.toml` and `uv.lock` |

---

## 1. Fully offline — no API key, no network

This is the path you want. It reproduces the *analysis*, which is the part that can be reproduced
exactly.

```console
git clone https://github.com/Charlie-Wang-03/jev-testbench.git
cd jev-testbench

uv sync --locked
uv run pytest
```

**The full offline suite passes and no socket is opened.** The suite blocks sockets outright, so an accidental API
call fails loudly rather than quietly spending your money. The tests use `httpx2.MockTransport`
against the real SDK where they need to exercise the client.

### Rebuild the derived artifacts

```console
uv run python -m jev_lab report         # results/summary.csv, results/summary.md
uv run python -m jev_lab snapshot       # results/capability_snapshot.md
uv run python -m jev_lab final-report   # results/JEV_LOCAL_EVALUATION_FINAL.md
```

None of these calls the API, needs a key, or writes to the log. Every number is recomputed from the
committed canonical logs on the way out, so a regenerated file either matches the log or is
detectably stale — a derived file can never become a second source of truth.

### Inspect the evidence directly

```console
uv run python -m jev_lab list           # experiments, tiers, call ceilings, credential status
```

Then read a log. They are JSONL — one self-describing object per line:

```console
head -1 results/usage.jsonl
head -1 results/p3_boundary_locus/usage.jsonl
```

### Verify the hashes

```console
sha256sum results/usage.jsonl                # 38e67630a7c345...8dc40b1b   (42 records)
sha256sum results/p3_boundary_locus/usage.jsonl  # 17f36f7551d598...f34c5d78e   (12 records)
```

These must match the values in [FREEZE.md](../../FREEZE.md) and the
[provenance record](../EVIDENCE_PROVENANCE.md). `.gitattributes` pins `eol=lf` precisely so a
Windows checkout cannot rewrite line endings and silently change the bytes these hashes cover.

### The identifiers in each record

Every record carries `request_id` (per call), `run_id` (per CLI invocation) and
`client_session_id` (per connection pool). Opening the log, these are the first fields that look
like they might be sensitive, so here is what they are:

- **They are not credentials**, and they are not derived from the API key.
- **They stay in the logs by owner decision** — `OWNER_DECISION_PUBLIC_OK`. No identifier was
  hashed, redacted, or removed, and the two hashes above cover the logs exactly as published.
- **They are opaque, not anonymous.** A `request_id` is a handle into TypeSafe's own request
  history; it is kept because it is what lets a published record be checked against the service
  that produced it. The owner reviewed that tradeoff and accepted it.

The full account, including what a scan of both logs did and did not find, is in
[SECURITY.md § Opaque identifiers in the canonical logs](../../SECURITY.md#opaque-identifiers-in-the-canonical-logs).

### What you can check without a key

- The P3 analyzer's post-run correction did not move the verdict —
  `tests/test_p3_boundary_locus.py` asserts this against the real log.
- The core log never changed after the freeze —
  `git diff e20fad5 bdcb637 --stat -- results/usage.jsonl` is empty.

---

## 2. Live — needs a TypeSafe account, and spends real money

> **Cost warning.** These commands make real API calls against a real account. Read
> [Credentials](credentials.md) first, and see [Budgets](#budgets) below.

```console
uv run python -m jev_lab list                    # see what exists, and its call ceiling
uv run python -m jev_lab run 01_primitives       # one experiment; ceiling of 8 calls by default
uv run python -m jev_lab run-all --tier core     # a whole tier; refuses without an explicit budget
```

`list`, `report`, `snapshot` and `final-report` never call the API. **`run` and `run-all` are the
only commands that spend money**, and their `--help` text says so.

### Budgets

- `run` defaults to a hard ceiling of **8** API calls. Override with `--max-requests N`.
- `run-all` **refuses to start** unless `--max-requests` is at least the tier's case count. A bulk
  run must be an explicit human decision.
- `05_speculative_fanout` has control flow, so its four declared cases can become six calls. Its
  budget check uses the stated `call_ceiling`, never the case count.
- There are **no unbounded loops** anywhere. The repeating experiments are capped at 5 repeats.
- An authentication failure aborts immediately rather than spending the rest of the budget.

### Writing your results somewhere else

Every command takes `--results-dir`. Point it at a scratch directory to avoid appending to the
canonical logs, which are frozen evidence and must not be added to:

```console
uv run python -m jev_lab run 01_primitives --results-dir /tmp/jev-scratch
```

---

## 3. What "reproduce" can and cannot mean here

> **Frozen measurements are historical measurements, not golden outputs that every future run must
> reproduce exactly.**

Reproducing the **method** is the goal. Reproducing the **digits** is not something this design can
promise, for four separate reasons:

1. **The alias can move.** `jev-latest` is what gets requested by default; only the response says
   which model answered. The frozen records resolved to `jev-1.13.0`. A future run may resolve
   elsewhere. Both `model_requested` and `model_resolved` are recorded for exactly this reason.
2. **It is a probabilistic model.** Byte-identical requests returned differently-shaped
   distributions here — the winning label held, the distribution underneath it moved. See
   [Findings §1](../findings/findings.md).
3. **The substrate differs.** Latency is wall-clock around one SDK call, and it contains DNS, TCP,
   TLS, connection-pool state, server queueing, upstream load and local scheduling. A different
   machine or a different day is a different measurement.
4. **The account and session differ.** Cost is a local estimate from one published price table;
   TypeSafe Console billing is authoritative.

So: a live run that produces different numbers has **not** falsified the frozen ones, and a live run
that matches them has not validated them. It has produced a second measurement.

### Why the core log is frozen and not extended

`results/usage.jsonl` holds 42 records with a published SHA-256. Appending to it would invalidate
that hash and destroy the citation. New work gets its own log in its own directory — which is
exactly what P3 did. If you want to add measurements, use `--results-dir`.

### Re-running P3

P3 is not in the `EXPERIMENTS` registry, precisely so it cannot be run by `run-all`. Its design is
frozen in the [preregistration](../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md), and it made
exactly twelve calls. Running it again would produce a *new* measurement under the same design —
which is a legitimate thing to do, but it is a new experiment, not a reproduction of the frozen
one, and it belongs in a new log.

---

## 4. Troubleshooting

| Symptom | Cause |
|---|---|
| `TYPESAFE_API_KEY: missing` | No key in the environment and no readable `.secrets/typesafe.env`. See [Credentials](credentials.md). |
| `TYPESAFE_API_KEY: unusable (malformed \| duplicate-key \| unreadable)` | The file exists but cannot be used. The loader fails closed rather than guessing. |
| `refusing to run: N cases planned but --max-requests is M` | The budget is smaller than the case list. Pass a larger `--max-requests` if that spend is intended. |
| pytest cannot create its temp directory | pytest uses a project-local basetemp (`--basetemp=.pytest-tmp`) because the system `%TEMP%` is not writable in every environment this runs in. `.pytest-tmp/` is gitignored. |
| Answers look empty or odd after setting `TYPESAFE_LOG_LEVEL` | Do not set it to `debug`. The SDK redacts secret *headers* but explicitly does **not** redact request/response *bodies*, so debug logging dumps your full state and every answer. |
