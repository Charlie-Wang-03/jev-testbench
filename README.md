# jev-test — a TypeSafe Jev local bench

A minimal, auditable bench for measuring what TypeSafe's **Jev** model actually does on this
machine: what it can decide, where it breaks, and what each call costs in tokens, latency, and
dollars.

This is an **experiment bench, not a production application**. It has no database, no Docker, no
web UI, and no dependencies beyond the TypeSafe SDK. Its output is a JSONL log of real
measurements you can read line by line.

---

## 1. What this is for

Three questions, answered with local evidence rather than vendor claims:

1. **Capability** — which kinds of judgment does Jev handle well?
2. **Boundaries** — how do the failure modes the docs already admit to behave on our own inputs?
3. **Cost** — what do those calls cost in tokens, wall-clock latency, and US dollars?

Each experiment is a small fixed set of cases: one synthetic state plus typed questions. Every
real API call appends exactly one line to `results/usage.jsonl`.

**Official claims and local measurements are kept separate.** The TypeSafe docs make performance
claims (for example, that batching questions is "12.2x cheaper and 10.0x faster" on their GDPR
cookbook workload). Those are recorded in this project as *claims*. Anything labelled a
*measurement* was produced by a run in this repository and is in the JSONL.

---

## 2. Environment

| | |
|---|---|
| OS | Windows 11 |
| Python | 3.13 (`.python-version`: `3.13`) |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| SDK | `typesafe-sdk` (pinned in `pyproject.toml`; 0.7.0 at the time of writing) |
| Tests | `pytest` (dev dependency) |

Set up:

```powershell
uv sync
uv run pytest
```

**Platform note:** pytest is configured with a project-local basetemp (`--basetemp=.pytest-tmp`),
because the system `%TEMP%` directory is not writable in every environment this project runs in.
`.pytest-tmp/` is gitignored.

The initial `uv init` scaffolding (`src/jev_test/`, a root `test_jev.py` that called the live API
on import, and the matching `[project.scripts]` entry) has been removed. The bench is
`src/jev_lab/`, it is used as `uv run python -m jev_lab ...`, and there is no console script.

---

## 3. Setting the API key

The key is read from exactly two places, in this order:

1. the environment variable `TYPESAFE_API_KEY`, when it holds a non-blank value;
2. `<repo>/.secrets/typesafe.env`, a local file that is git-ignored;
3. neither — and every command that needs the API stops before spending anything.

The environment wins, so a rotated or one-off key can be set for one terminal without touching the
file. When it is set, the file is not opened at all.

No command ever prints the key, its length, a prefix, a suffix, or a hash of it. Every command that
touches credentials reports one of:

```text
TYPESAFE_API_KEY: missing
TYPESAFE_API_KEY: exists (source=environment)
TYPESAFE_API_KEY: exists (source=local-secret-file)
TYPESAFE_API_KEY: unusable (malformed | duplicate-key | unreadable)
```

For a single session, without leaving the key in your shell history:

```powershell
$secureKey = Read-Host "Paste TypeSafe API key" -AsSecureString
$env:TYPESAFE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
```

### Persistent local API key

A session variable is gone when the terminal closes. If you would rather not re-paste a key every
time, put it in `.secrets/typesafe.env` — inside the working directory, and outside version control.

The format is one line, no quoting, no shell syntax:

```text
# Local credentials for this machine. Never commit this file.

TYPESAFE_API_KEY=<your-key>
```

Create the file if it is not there yet. Blank lines and `#` comments
are ignored; the value is everything after the `=` with surrounding whitespace removed. Nothing in
the file is expanded, substituted, or executed — `$(...)`, `${VAR}`, backticks, and quotes are
ordinary characters, and there is no inline-comment syntax (a trailing `# comment` becomes part of
the value). Two `TYPESAFE_API_KEY` lines, an unexpected name, or a line that is not an assignment
is an error rather than a silent choice, and the loader stops. An empty value means *missing*.

`.secrets.example/typesafe.env` is the committed template. `.secrets/` is not:

```console
$ git check-ignore -v .secrets/typesafe.env
.gitignore:28:.secrets/    .secrets/typesafe.env
```

`git add --dry-run .secrets/typesafe.env` is refused for the same reason, and
`git add --dry-run .secrets.example/typesafe.env` succeeds — the template is meant to be committed.

**What this scheme does and does not buy you.** It keeps the key out of Git, out of the diff, and
out of the chat transcript. It is still a plaintext file on disk. Be clear-eyed about that:

- it is only appropriate for a personal experiment repository on a machine you control;
- it is readable by anything running as you, and by backup, indexing, and cloud-sync tools that
  watch the directory — OneDrive, Dropbox, and Windows Search included, if the repo is inside a
  synced folder;
- the default Windows ACL on the file inherits from its parent: `Administrators`, `SYSTEM`,
  `Authenticated Users`, and `BUILTIN\Users` (read). On a single-user machine that is roughly "you
  and anything running as an administrator", but it is not a per-user lock, and a second local
  account can read the file. Tightening it is optional, and if you do it, do it on the file — not
  on the repository directory, and not in a way that drops `SYSTEM` or your own account;
- an agent with file access can read it. `CLAUDE.md` asks agents not to, and that instruction is a
  convention, not a mechanism.

**If you suspect the key was exposed** — committed, pasted, synced, screenshotted — revoke it in
the TypeSafe Console and issue a new one. Do it first; rewriting history afterwards does not undo
the exposure. Then update `.secrets/typesafe.env` (or the session variable).

Committing the file is the failure this scheme is built to prevent, but the ignore rule is not the
only line: the loader fails closed, the tests never read the real file (see `tests/conftest.py`),
and no code path prints a value.

---

## 4. Commands

```powershell
uv run python -m jev_lab list                     # experiments, tiers, case counts, key status
uv run python -m jev_lab run 01_primitives        # run one experiment
uv run python -m jev_lab run-all --tier core      # run a whole tier (needs an explicit budget)
uv run python -m jev_lab report                   # rebuild summary.csv and summary.md
uv run python -m jev_lab snapshot                 # rebuild the derived capability_snapshot.md
uv run python -m jev_lab final-report             # rebuild the derived JEV_LOCAL_EVALUATION_FINAL.md
```

`list`, `report`, `snapshot`, and `final-report` never call the API and work without a key. All
four read the log and never write to it.

### Budgets and safety

- `run` defaults to a ceiling of **8** API calls. Override with `--max-requests N`.
- `run-all` **refuses to start** unless `--max-requests` is at least the tier's case count. This is
  deliberate: a bulk run must be an explicit human decision, never an accident.
- Every experiment declares its cases up front, so the cost of a run is knowable before it starts.
- One experiment has a real **control flow**: in `05_speculative_fanout` the next request depends on
  the previous answer, so its declared four cases can become six calls. It states that ceiling
  explicitly (`call_ceiling`) and the budget check uses the ceiling, never the case count. Its
  branch rule is frozen before the run: a primary answer naming no known branch sends **no** second
  request, because no offline-audited payload exists for a branch chosen at run time.
- One experiment **executes** something: `12_function_routing` calls a handler after a route is
  selected. Every handler is registered in `jev_lab/routing.py` before the run and is inert — no
  file, network, subprocess, shell, or change to this project — and the model can only select a name
  from that registry, never supply code. A label outside it, a missing argument, or an argument
  outside the selected function's frozen set all **fail closed**: the case reports
  `FUNCTION_ROUTE_UNAVAILABLE` and nothing is called. Its four cases carry no control flow, so it
  spends exactly four calls.
- There are **no unbounded loops**. The two repeating experiments (`13_repeatability` and
  `13b_ambiguous_repeatability`) are each capped at 5 repeats; any loop that would call the API is
  bounded by the case list and by `--max-requests`.
- An authentication failure aborts a run immediately rather than spending the rest of the budget.
- A failed case records its error and the run continues, so a partial result still has provenance.

### Model selection

`--model` overrides the model for a run. The default is the SDK's own default, `jev-latest`.
Every record stores both the model **requested** and the model **resolved** by the API, because an
alias can move underneath you.

Current target: `jev-1.13.0`, which is what both `jev-latest` and `jev-preview` resolve to today.
The ability to ask for a model is not evidence about which one answered — the response's `model`
field is.

---

## 5. `results/usage.jsonl` is the canonical local record

Every call appends one JSON object per line:

```json
{
  "timestamp_utc": "2026-09-20T15:04:05Z",
  "run_id": "a1b2c3d4e5f6",
  "experiment": "01_primitives",
  "case_id": "ticket_all_primitives",
  "model_requested": "jev-latest",
  "model_resolved": "jev-1.13.0",
  "request_id": "…",
  "latency_ms": 812.5,
  "question_count": 3,
  "question_types": ["choice", "noul", "score"],
  "state_chars": 187,
  "state_utf8_bytes": 187,
  "input_tokens": 328,
  "output_tokens": 34,
  "total_tokens": 362,
  "estimated_cost_usd": 0.00001378,
  "cost_basis": "jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens",
  "status": "ok",
  "error_type": null,
  "retry_count": null,
  "case_sequence_index": 0,
  "logical_request_index_in_run": 0,
  "client_session_id": "…",
  "is_first_request_in_client_session": true,
  "transport_attempt_count": 1,
  "transport_retry_count_observed": 0,
  "attempt_count_source": "httpx_request_event_hook",
  "schema_version": 3,
  "answers": { "…": "…" },
  "notes": { "…": "…" }
}
```

- **Token counts are the ones the API returned** in `usage`. This project never estimates tokens;
  `usage` is the canonical measurement.
- **The position fields exist because latency is confounded by position.** `client_session_id`
  groups the calls that shared one `TypeSafeClient` (and therefore one connection pool);
  `is_first_request_in_client_session` marks the call that opened it;
  `logical_request_index_in_run` counts 0-based across the whole invocation, and
  `case_sequence_index` counts 0-based within the experiment. All four are recorded before the
  request is sent, so a failed call carries them too. Schema-1 rows simply lack them — a missing
  field means "not recorded" and never means zero. `run` prints all of this per run so the
  confound is visible while the run is happening rather than discovered later.
- **`retry_count` is vestigial.** It is still written so old lines stay readable, but it is always
  `null` — see the retries subsection below. The live attempt fields are `transport_attempt_count`
  and `transport_retry_count_observed`, and a missing value in any of them means *not recorded*,
  never `1` and never `0 retries`.
- **`latency_ms` is local wall-clock** around the call. It is measured by this tool, not by the
  API.
- **`notes` carries the case's design metadata** (which arm it belongs to, an expected label where
  one exists) plus `notes.derived`: values computed locally from the answer, such as the
  confidence gate's routing decision. Derived values cost no extra API call.
- `results/` is **append-only**. Nothing rewrites or deletes prior records.
- `results/capability_snapshot.md` and `results/JEV_LOCAL_EVALUATION_FINAL.md` are **derived**
  views, regenerated by `snapshot` and `final-report`. Neither is a measurement and neither is a
  source of truth; every number in them is recomputed from the log on the way out, so they cannot
  drift from the records they describe.
- `results/` is **committed selectively**: the canonical log and the final report are tracked, and
  every other derived file is ignored. A clone gets the measurements, which is what makes an
  evaluation citable; it rebuilds the views. See the comment on the `results/*` rule in
  `.gitignore` — the pattern is `results/*` with a negation per tracked file, because a negation
  cannot resurrect a file whose parent directory is ignored.

### Retries distort latency, and are now counted locally

The SDK retries by default (`RetryPolicy(max_retries=2)`, retrying 408/429/5xx with backoff and a
30s budget). A retried call is still **one** logical request in the log, but its `latency_ms`
includes every attempt and the backoff between them.

`retry_count` — the SDK's own field — **is dead and stays dead.** The SDK sets
`X-TypeSafe-Retry-Count` on the retried *request*; this recorder reads that header off the
*response*, where the server does not echo it. It is therefore always `null`. It is kept only so
old lines stay readable, is never backfilled, and `null` in it never means "no retries happened".
Do not reason from it.

The live fields are counted in this process instead. `TransportProbe` attaches an `httpx2` request
event hook — which fires once per wire attempt — to the client the SDK uses, and each logical call
records the difference between two reads of that counter:

- `transport_attempt_count` — outgoing HTTP attempts inside this call's timing window.
- `transport_retry_count_observed` — `max(transport_attempt_count - 1, 0)`.
- `attempt_count_source` — how it was measured, `"httpx_request_event_hook"`.

The hook increments an integer and inspects nothing: it never reads a header, a URL, or a body,
never retains the request, and never writes anything. It cannot leak a credential because it never
looks at one. The count is a **local observation of this process's traffic**, not a server-side
statement; it counts wire attempts, so a redirect hop would be included if one ever happened.

A failed call still records its count — the second read happens in a `finally`, so a call that
exhausts its retries and raises reports all of them. When no probe is attached the fields stay
`null`, which means **not recorded** and is deliberately distinct from `1`. The before/after delta
assumes experiments run **serially**, which the CLI does; introducing concurrency would require
re-auditing it.

### Latency measurement policy

Latency here is **wall-clock around one SDK call**, and it inherits a substrate: a fresh client pays
DNS, TCP, and TLS that its siblings do not. A timing difference between two arms is therefore not
evidence about the model until the order is controlled. The policy for any experiment that wants to
say something about latency:

1. **Balance the order, always.** Neither arm may sit in the same position in every run. This is the
   one non-negotiable item, and it is what the four position fields exist to verify after the fact.
2. **Report the first request separately; do not silently drop it.** The canonical log keeps every
   call. Any derived view that excludes warm-up observations says so explicitly and shows what it
   excluded, so the exclusion is auditable rather than invisible.
3. **Do not treat repetition as optional to save a couple of calls.** Two extra calls cost a
   fraction of a cent; an unbalanced comparison is worth nothing. `03_parallel_questions` runs two
   order-balanced cycles for exactly this reason.
4. **Check the attempt count before reading any latency.** This is what `transport_attempt_count`
   is for, and it licenses exactly one sentence: *this call was not observed to make more than one
   HTTP attempt*. It licenses nothing more.
5. **Never equate `attempts == 1` with pure model inference latency.** A single attempt still sits
   inside a window that contains DNS, TCP, and TLS setup, connection-pool state, the server's own
   queueing, upstream model time, and local scheduling. The count rules out *observed* HTTP retries
   and nothing else. A call with no attempt count rules out even that.
6. **A dedicated latency benchmark is the eventual home for this.** Capability experiments should
   not have to carry timing controls they were not designed around.

Even when the order is balanced, the result is an **observed latency comparison** and is named that
way. Two cycles is a small sample: it is not enough to claim a stable speedup factor, and no
experiment here claims one.

A warm-up is tempting and only partly available. `client.models.list()` is a `GET /v1/models` on the
same client, so it shares the connection pool — that part is verified in the SDK, which constructs
the `Models` resource with the same `httpx2.Client` that `system_one` uses. Its response schema
carries no `usage` field at all, so it cannot be a token-accounted Jev inference call. But this
project has not confirmed with TypeSafe that the endpoint is unbilled, and a warm-up cannot remove a
position effect that also varies with server-side conditions. So a warm-up is a *possible future
refinement*, not a substitute for balancing, and nothing here depends on it yet.

### Logging

Do **not** set `TYPESAFE_LOG_LEVEL=debug` while running experiments. The SDK redacts secret
*headers*, but it explicitly does **not** redact request or response *bodies* — debug logging will
dump your full `state` and every answer to the console. Nothing in this project enables it.

---

## 6. Cost is a local estimate

`estimated_cost_usd` is computed locally from the published price:

```text
estimated_cost_usd = input_tokens × 0.042 / 1_000_000
```

Output tokens are free at the published rate, so they contribute nothing. Prices live in one
place, `src/jev_lab/pricing.py`, keyed by the **resolved** model — never the requested one.

If a response's resolved model is not in that table, the cost is recorded as `null` with
`cost_basis: "unknown: resolved model is not in this project's price table"` rather than being
assumed to share `jev-1.13.0`'s rate. A future model must be added to the table deliberately.

> **This is an estimate.** TypeSafe's Console billing is the authoritative, server-side record of
> what you were charged. Treat these numbers as a local planning aid.

---

## 7. Jev is not a chat or generative model

This matters for reading every result in this repository.

Jev takes a `state` and a set of **typed questions**, and returns **structured, typed answers with
probabilities** — not prose. It does not generate text, does not hold a conversation, and has no
memory between requests. Each request is independent.

- A `Choice` answer is a label plus a probability for every option and a `confidence`.
- A `Score` answer is a probability-weighted position on an ordered rubric, plus its distribution
  and a `confidence`.
- A `Noul` answer is a single probability that the answer is yes, with **no separate confidence** —
  with only two outcomes, the one number already describes the whole distribution.

The design rule that follows from this, and that shapes every experiment here: **code does the
arithmetic and the branching; Jev supplies the semantic judgment.** When you see this project ask
Jev for a count or a comparison, it is measuring a documented limitation, and the correct
code-side answer is included alongside it.

---

## 8. The experiments

Every experiment below is **designed and registered**. The "real run" column says whether it has
actually been run against the API, and the "records" column is the number of lines it owns in
`results/usage.jsonl` — those two are read off the log, not maintained by hand.

`core` — the foundational mechanics:

| Experiment | Real run | Records | What it measures |
|---|---|---|---|
| `00_model_info` | no | 0 | Which versioned ID each alias resolves to. |
| `01_primitives` | yes | 1 | Choice + Score + Noul in one request against one state (the smoke test). |
| `02_structured_addressing` | yes | 2 | Field-path addressing over structured state versus described addressing over prose state. |
| `03_parallel_questions` | yes | 12 | One batched request versus the same questions sent separately, in two order-balanced cycles. |
| `04_confidence` | yes | 2 | Specific versus ambiguous evidence; routed in code on confidence alone. |

`extended` — specific behaviours and documented limits:

| Experiment | Real run | Records | What it measures |
|---|---|---|---|
| `05_speculative_fanout` | yes | 6 | The same branching control flow run two ways: every candidate follow-up in one request (speculative fanout) versus the routed branch's follow-ups in a second request (staged). Two states, order-balanced, capped at 6 logical calls. |
| `06_composite_scoring` | yes | 3 | Four separate atomic Score questions per state, composed into one risk in Python with weights frozen before the run. Jev is asked for no arithmetic and no verdict. Three states, one request each. |
| `07_instruction_precision` | yes | 2 | Vague versus explicit decision boundaries on a byte-identical state. |
| `08_literal_reading` | no | 0 | Negation, implied conditions, and scope. |
| `09_numeric_limits` | no | 0 | A small demonstration of the documented counting and arithmetic limits. |
| `10_state_length` | no | 0 | Fixed core evidence with growing irrelevant filler. |
| `11_language_pair` | no | 0 | Equivalent English and Chinese input and questions. |
| `12_function_routing` | yes | 4 | Route a state to a name in a registry frozen before the run, and to one of that name's closed-set arguments, then call an inert handler. Four states, one request each; a frozen policy can only withhold execution. |
| `13_repeatability` | yes | 5 | One byte-identical Choice + Score + Noul request sent five times, to observe how much the answers and the reported usage move. |
| `13b_ambiguous_repeatability` | yes | 5 | `01_primitives`' own request sent five times, to observe run-to-run variation where the Choice and the Score are not at the ends of their scales. |

`08` and `09` are built from the official *Jev 1.13 jaggedness* page and are deliberately tiny:
the docs already state those limitations, so repeating them at scale would spend budget to learn
something already known. Their purpose is to see the failure mode once, locally, not to grade the
model. Neither has been run.

### `OPTIONAL_EDGE_COVERAGE_BACKLOG`

`00_model_info`, `08_literal_reading`, `09_numeric_limits`, `10_state_length`, and
`11_language_pair` have **no records**. They extend coverage of behaviour this bench already has a
reading on; none of them answers an open core-capability question, and none is a blocker for the
status below. Running one would start a new measurement rather than complete this one.

The list is derived, not maintained: `final-report` computes it as the registered experiments with
no canonical record, so an experiment leaves the backlog the moment it produces a line.

The most load-bearing of them is `00_model_info`, the only core-tier experiment that was never
run. The alias-to-version resolution it exists to record is nevertheless in every record of the
log, because every call records both `model_requested` and `model_resolved`.

---

## Current evaluation status

**`CORE_CAPABILITY_EXPLORATION_CLOSED`** — the core-capability questions this bench was built to
ask have each produced a local measurement, and every measurement is in the canonical log.
Nothing was adjusted after seeing an answer: no threshold, state, or criterion was revised once
results existed, and no negative or unexpected result was dropped.

All 42 canonical records are `status: ok`, every one resolved to `jev-1.13.0`, and the log carries
no credential material.

One boundary is carried forward deliberately rather than closed:

**`ACTUAL_HANDLER_EXECUTION_UNTESTED`** — in `12_function_routing` every resolved route was
withheld by the frozen policy, so the branch that reaches `HANDLERS[name](argument)` was never
entered under a live answer. This is **not a blocker**: that branch is Python-side plumbing rather
than an open question about the model, and the offline suite exercises it directly. No threshold
was moved and no state was chosen to make it execute, because either would have replaced a
measurement with a fit.

**`LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK`** — latency is recorded here and read
nowhere else. Sessions show a slow first call, and the fields needed to check that hypothesis are
present on the newer records only; the window is not decomposable from these records, and no
speedup is claimed anywhere.

The full findings, with every claim labelled OFFICIAL / DESIGN ASSUMPTION / LOCAL MEASUREMENT /
DERIVED CALCULATION / LIMITATION, are in **`results/JEV_LOCAL_EVALUATION_FINAL.md`** — a derived
artifact, regenerable with `final-report`.

Some experiments A/B two arms (batched vs separate, structured vs prose, vague vs explicit, English
vs Chinese, short vs long). Those are read from the per-case table each `run` prints, and from the
per-case rows in `usage.jsonl` — the summary aggregates by experiment, not by case.

### What the A/B experiments do and do not establish

An A/B here varies more than its name suggests, and the difference matters when reading a result.

- **`03_parallel_questions`** runs two order-balanced cycles — batched-then-separate, then
  separate-then-batched — because its first version put the batched arm first in every run and left
  arm identity perfectly confounded with request position. Twelve logical calls. Token and cost
  comparisons are tight: identical state, identical question definitions, one request carrying all
  five questions against five requests carrying one each. **Latency is still only observational**:
  two cycles balance the order but are nowhere near enough to claim a speedup, so this experiment
  never claims one.
- **`02_structured_addressing`** is **not** a clean "JSON versus prose" causal test. Three things
  move together: the state representation, whether a question can name a field path at all, and the
  payload length (the structured arm is longer). Token, latency, and cost differences are therefore
  **confounded by length** and are reported as observations, not attributed to representation.
  `state_chars` / `state_utf8_bytes` are recorded per case so the gap stays measurable. Both arms
  carry the same facts, the same question set, and identical criteria.
- **`04_confidence`** keeps both arms in one scenario with the same entities, similar length, and
  identical Choice and Score criteria, so the main variable is how specific the evidence is.
  Correctness and confidence are reported **separately**: the clear arm declares an expected label,
  the ambiguous arm declares none rather than inventing one, so "confidently wrong" stays visible.
  The Score is there to observe the ordinal distribution; **Score confidence is not correctness**
  and is not comparable to Choice confidence.
- **`07_instruction_precision`** holds the state byte-identical and puts criteria in **both** arms,
  so the answer space is the same. It varies how explicitly the decision boundary is stated, in the
  instructions and criteria **together** — it does **not** isolate instruction wording from criteria
  wording, and it does not claim to have isolated every prompt-engineering factor. The explicit
  criteria deliberately avoid the state's own nouns so a correct answer cannot come from lexical
  matching. Noul has no distribution and no confidence, so this experiment compares the Noul scalar,
  tokens, latency, and cost only.

### On thresholds

`04_confidence` routes in code on the answer's own confidence — `confidence < 0.60` escalates,
anything at or above it is accepted. That `0.60` is a **demonstration parameter**, not a tuned,
calibrated, or optimal value: the TypeSafe docs use 0.6 on one pattern page and 0.5 on another for
the same example, and state plainly that thresholds depend on your domain and must be tuned on your
own data. The gate's decision, and the basis string labelling it a demo, are written into each
record's `notes.derived` so the routing is auditable after the fact. Nothing here claims an optimal
threshold, and a passing gate is not evidence that the underlying answer was correct.

---

## 9. Ground rules

- All state in this repository is **synthetic test data**. No real personal or proprietary content.
- Official TypeSafe docs are the source of truth for product semantics:
  <https://docs.typesafe.ai/llms.txt>.
- Code does arithmetic; Jev does semantic judgment.
- Prefer batching questions that share a state.
- Always log the resolved model and the exact usage the API returned.
- No secrets in this repository, ever. The key comes from the environment or from the git-ignored
  `.secrets/typesafe.env`, and from nowhere else.
