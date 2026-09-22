# Methodology

**English** | [简体中文](evaluation.zh-CN.md)

How this bench decides what it is allowed to say. The rules below are not style preferences — they
are the reason a number in this repository means something specific.

---

## 1. Claim labelling

Every assertion in a derived report carries one of five tags:

| Label | Meaning |
|---|---|
| **OFFICIAL** | A statement from TypeSafe about *their* workload. Not evidence about this machine. |
| **DESIGN ASSUMPTION** | A choice this repository made, not a fact about the model. |
| **LOCAL MEASUREMENT** | Produced by a run in this repository, and present in a canonical log. |
| **DERIVED CALCULATION** | Arithmetic performed locally over measurements (latency, cost, ratios). |
| **LIMITATION** | An explicit boundary on what the evidence supports. |

The P1 audit uses a finer vocabulary for the relationship between an official claim and local
evidence, because "confirmed / not confirmed" is too blunt for it:

```
DR  DIRECT_LOCAL_REPRODUCTION      DS  DIRECTIONAL_LOCAL_SUPPORT
LE  LOCAL_EXTENSION                AT  APPARENT_TENSION
NT  NOT_LOCALLY_TESTED             ND  NOT_TESTABLE_WITH_CURRENT_DESIGN
NO  NOT_AN_OFFICIAL_CLAIM
```

`ND` is the one to notice. It is used when local records are **not commensurable** with a claim in
either direction — not a refutation and not a confirmation. The vendor's 70–500 ms latency band
sits there: this bench's window contains DNS, TCP, TLS setup, connection-pool state, server-side
queueing, upstream load and local scheduling, so the two numbers are not the same quantity.

### The separation rule

> An official claim is never restated as something this repository measured.

The clearest example: TypeSafe publishes a batching multiplier for their cookbook workload. This
bench measured **4.26×** on a different payload. Those two numbers must never be set side by side
as "official vs. actual" — different workload, different payload, different denominator, different
session. They are recorded as a claim and a measurement, and each stays in its own category.

---

## 2. Experiment design rules

- All state is **synthetic**. Never real personal, customer, or proprietary content.
- Every experiment declares a **fixed case list** up front, so the cost of a run is knowable before
  it starts. If an experiment would need a loop, it needs a documented constant cap instead.
- One real API call produces exactly **one record**, written by `UsageRecorder`, whether it
  succeeds or raises. Nothing bypasses the recorder.
- **Never estimate tokens.** Token counts are the `usage` values the API returned.
- Record **both** `model_requested` and `model_resolved`. An alias can move; only the response says
  which model answered.
- Code does arithmetic; Jev does semantic judgment. Jev is never asked to count, sum, compare
  numbers, interpolate between score levels, or compute a date difference. When an experiment
  *does* probe a documented numeric limit, the correct code-side answer is placed next to it.
- Normalize score scales **in code** (`score / (levels - 1)`) before combining them.

### Budgets

`run` defaults to a hard ceiling of **8** API calls. `run-all` **refuses to start** unless
`--max-requests` covers the tier — a bulk run must be an explicit human decision, never an
accident. An authentication failure aborts a run immediately rather than spending the rest of the
budget. A failed case records its error and the run continues, so a partial result still has
provenance.

### The one experiment with control flow

`05_speculative_fanout` lets the next request depend on the previous answer, so its four declared
cases can become six calls. It states that ceiling explicitly (`call_ceiling`) and the budget check
uses the ceiling, never the case count. Its branch rule was frozen before the run: a primary answer
naming no known branch sends **no** second request, because no offline-audited payload exists for a
branch chosen at run time.

---

## 3. What the A/B experiments do and do not establish

An A/B here varies more than its name suggests, and the difference matters when reading a result.

### `03_parallel_questions` — batched vs. separate

Two **order-balanced** cycles: batched-then-separate, then separate-then-batched. The first version
of this experiment put the batched arm first in every run, which left arm identity perfectly
confounded with request position — the reason the four position fields exist on every record now.

Token and cost comparisons are tight: identical state, identical question definitions, one request
carrying all five questions against five requests carrying one each. **Latency is still only
observational.** Two cycles balance the order but are nowhere near enough to claim a speedup, and
this experiment never claims one. The batched arm's own two observations spread by **2592.9 ms**
against an arm-to-arm mean difference of **1327.2 ms** — within-arm spread exceeds the difference.

### `02_structured_addressing` — structured vs. prose

**Not a clean causal test.** Three things move together: the state representation, whether a
question can name a field path at all, and the payload length (the structured arm is longer). Token,
latency and cost differences are therefore **confounded by length** and are reported as
observations, never attributed to representation. `state_chars` / `state_utf8_bytes` are recorded
per case so the gap stays measurable.

### `04_confidence` — specific vs. ambiguous

Both arms stay in one scenario with the same entities, similar length, and identical `Choice` and
`Score` criteria, so the main variable is how specific the evidence is. **Correctness and
confidence are reported separately**: the clear arm declares an expected label, the ambiguous arm
declares none rather than inventing one, so "confidently wrong" stays visible. `Score` confidence is
**not** correctness and is not comparable to `Choice` confidence.

### `07_instruction_precision` — vague vs. explicit

The state is held **byte-identical** and criteria are present in **both** arms, so the answer space
is the same. It varies how explicitly the decision boundary is stated, in the instructions and
criteria **together** — it does **not** isolate instruction wording from criteria wording. The
explicit criteria deliberately avoid the state's own nouns, so a correct answer cannot come from
lexical matching. `Noul` has no distribution and no confidence, so this experiment compares the
`Noul` scalar, tokens, latency and cost only.

### `05_speculative_fanout` — fan-out vs. staged

Fan-out pays for answers it may not use; staged pays for a second round trip. Waste here is counted
**in questions, never in tokens**, and the two arms differ in both request count and total
questions sent — so the comparison is a trade, not a ranking. No arm is called faster: the two
pairs disagreed on latency direction.

---

## 4. On thresholds

`04_confidence` routes in code on the answer's own confidence — `confidence < 0.60` escalates,
anything at or above it is accepted. `12_function_routing` uses a 0.8 route floor and a 0.5 review
line.

**Every one of those is a demonstration parameter.** Not tuned, not calibrated, not claimed
optimal. The TypeSafe docs themselves use 0.6 on one pattern page and 0.5 on another for the same
worked example, and state plainly that thresholds depend on your domain and must be tuned on your
own data. A local coincidence with a documented example is **not corroboration**.

Each gate's decision, and the basis string labelling it a demo, is written into the record's
`notes.derived`, so the routing is auditable after the fact. Nothing here claims an optimal
threshold, and a passing gate is **not** evidence that the underlying answer was correct.

---

## 5. Latency policy

Latency here is **wall-clock around one SDK call**, and it inherits a substrate: a fresh client pays
DNS, TCP and TLS that its siblings do not. A timing difference between two arms is therefore not
evidence about the model until order is controlled.

1. **Balance the order, always.** Neither arm may sit in the same position in every run. This is the
   one non-negotiable item, and the position fields exist to verify it after the fact.
2. **Report the first request separately; do not silently drop it.** The canonical log keeps every
   call. Any derived view that excludes warm-up observations says so explicitly.
3. **Do not skip repetition to save a couple of calls.** Two extra calls cost a fraction of a cent;
   an unbalanced comparison is worth nothing.
4. **Check the attempt count before reading any latency.** `transport_attempt_count` licenses
   exactly one sentence: *this call was not observed to make more than one HTTP attempt.*
5. **Never equate `attempts == 1` with pure model inference latency.** A single attempt still
   contains DNS, TCP, TLS, connection-pool state, server queueing, upstream model time and local
   scheduling. The count rules out *observed* HTTP retries and nothing else.

Even with balanced order the result is an **observed latency comparison**, and it is named that way.

### Why `retry_count` is dead

The SDK sets `X-TypeSafe-Retry-Count` on the retried *request*; the recorder reads that header off
the *response*, where the server does not echo it. It is therefore always `null`. It is kept only so
old lines stay readable, is never backfilled, and `null` in it **never** means "no retries
happened". The live fields are `transport_attempt_count` and `transport_retry_count_observed`,
counted in this process by a request event hook that increments an integer and inspects nothing —
no header, no URL, no body. It cannot leak a credential because it never looks at one.

The before/after delta assumes experiments run **serially**, which the CLI does. Introducing
concurrency would require re-auditing it.

---

## 6. Reading the log

`results/usage.jsonl` is the measurement. Every other file under `results/` is a view rebuilt from
it.

- **`notes`** carries the case's design metadata (which arm, an expected label where one exists)
  plus `notes.derived` — values computed locally from the answer, such as the confidence gate's
  routing decision. Derived values cost no extra API call.
- **A missing field means "not recorded"** and never means zero. Schema-1 rows lack the position
  fields; `attempt_count` is absent on the records that predate the probe.
- **Null means "not reported"**, never "none happened".
- **`results/` is committed selectively.** The two canonical logs and the final report are tracked;
  every other derived file is ignored, so a clone gets the measurements and rebuilds the views.

### The seven ground rules

1. Official TypeSafe docs are the source of truth for product semantics.
2. Official claims and local measurements are recorded separately, and each result says which it is.
3. Code does arithmetic; Jev does semantic judgment.
4. Prefer batching questions that share the same state.
5. Always log the resolved model and the exact `usage` the API returned.
6. No secrets in this repository, ever.
7. All state is synthetic.
