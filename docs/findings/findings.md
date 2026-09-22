# Findings

**English** | [简体中文](findings.zh-CN.md)

What this bench learned about TypeSafe Jev, organised by how much weight each item will bear.

Read this alongside its counterpart: [what you cannot conclude](../../README.md#7-what-you-can-not-conclude-from-this-repository).
A finding here is a **local measurement** unless it is explicitly marked otherwise — one payload,
one account, one session, at one model version.

**Evidence:** [42 core records](../../results/usage.jsonl) ·
[12 P3 records](../../results/p3_boundary_locus/usage.jsonl) · resolved model `jev-1.13.0`

---

## 1. Reproduced

Behaviour that was observed here and is consistent with what TypeSafe documents. None of it is
novel — that is the point of listing it separately.

### Typed output semantics

All **42 of 42** responses were schema-valid and typed only; no answer carried a free-text field.
Across **45** `Choice` answers the returned label was the highest-probability option every time,
with no counter-example. Across **29** `Score` answers, **24** reproduced the probability-weighted
mean within 0.006, and no `Choice` label ever fell outside the criteria it was given.

`Noul` answers carry **no** separate `confidence` field — with only two outcomes, the single
probability already describes the whole distribution. Every `Choice` and `Score` answer does carry
one, and the two are different numbers reported side by side: in `01_primitives` the winning
probability was 0.45 while the confidence was 0.26.

> **How much this is worth.** This is schema conformance on benign payloads, measured over a
> handful of synthetic cases. It is the weakest kind of support for a type-safety claim. It says
> nothing about factual correctness, and the vendor's own published "zero hallucinations" figure is
> labelled by the vendor as **not empirical** — that qualifier has to travel with any citation of
> it.

### Batching questions that share a state

Sending five questions over one state in a **single** request cost **816 input tokens**. Sending
the same five questions as **five separate** requests cost **3,480**. That is a pooled input ratio
of **4.26×**, a **76.55%** saving, and **10 of 10** selected values were identical across the two
arms.

The saving is real and it is large. Two things it is not:

- **Not a universal batching ratio.** Every question in this payload reads the same state, which is
  exactly the condition the saving depends on.
- **Not comparable to the vendor's published multiplier.** TypeSafe's own figures describe a
  different workload — different question count, different payload, different denominator,
  different session. Setting the two side by side as "official vs. actual" would be a category
  error, and [the P1 audit](../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md) says so explicitly.

The *effect* was expected — it is straightforward shared-state amortisation, and public third-party
measurements of the same pattern go further than this bench does (they varied batch size; this
bench did not). See [killed findings](#3-negative-and-killed-findings).

### Instruction and criteria specificity move the answer

On a **byte-identical 82-byte state**, changing only the question wording moved a `Noul` from
**0.75** (vague decision boundary) to **0.20** (explicit) — a difference of **0.55** on a 0–1
probability, from the same state bytes.

This is a real, large effect on this payload, and it is consistent with a failure mode TypeSafe
documents and prescribes a remedy for. Two limits travel with it: the two arms changed the
*instruction* and the *criteria* wording **together**, so this design cannot attribute the move to
either one; and neither 0.75 nor 0.20 is ground truth, so neither arm is "correct".

That unattributed 0.55 became the P3 question.

### Repeatability of identical requests

Ten byte-identical requests across two payloads. The winning `Choice` label **never switched** —
5 of 5 on one payload, 5 of 5 on the other, 6 of 6 counting the historical record the second
payload reuses.

Underneath that stable label, the distribution moved. On the clear-cut payload the `Noul` varied by
0.01 across five repeats. On the mid-scale payload the top-2 margin moved by up to **0.07**,
`Score` ranged **1.58–1.63**, and one repeat produced an **exact tie** between the top two options.

> **A stable label is not a fixed distribution.** That sentence was written down here, then
> **killed in P2** for not being novel — the underlying fact is officially documented, and public
> reproductions carry more data than this one does. It is recorded as a reproduced observation, not
> as a discovery. See below.

---

## 2. Engineering lessons

Transferable conclusions from building and running the bench. These are about system design, not
about the model's internals — this project has no documentation of those, and does not name any.

### Confidence is a policy input, never a correctness score

The official docs scope calibration to **groups** of predictions and state that confidence
"describes the model's answer, not a guarantee that the answer is correct." Two local cases
*illustrate* that scoping; they cannot test it.

The local cautionary example is sharper than the rule. In `06_composite_scoring`, one dimension
scored **1.62** on a 0–3 rubric against a confidence of **0.24**, and that dimension carried
**97.4%** of that state's composite risk. The arithmetic was correct. The confidence was low. They
are simply different questions, and a policy that reads a low confidence as "wrong" or a high one
as "right" is reading the wrong number.

This is also why `composite.py` forbids confidence from entering any arithmetic: confidence is
recorded, displayed, and used for nothing else.

### Semantic routing is not execution authorization

The single most useful pattern this bench produced, and it comes from a run that went *against* the
design's expectation.

In `12_function_routing`, the model matched the intended function **4 of 4** times and the intended
argument **4 of 4** times. The policy frozen before the run withheld **every** route, so
`HANDLERS[name](argument)` was never reached under a live answer. Nothing was substituted.

Both facts are worth holding at once. The model's part worked; the authorization decision was made
in Python, afterwards, and it said no. A system that treats a confident route as permission to act
has removed the layer that produced this outcome — and the four suppressions are fully explained by
constants this repository chose, not by anything the model did. `routing.py` says so in a comment
next to the constant: *nothing in the docs says 0.8 is the right line*.

That count — **4 of 4** — is a count on synthetic cases, **not an accuracy rate**.

### Fail closed, and record the failure

An absent, empty, malformed, duplicated, or unreadable credential stops a run **before** a request
is sent. A label outside the frozen registry, a missing argument, or an argument outside the
selected function's frozen set all refuse to execute. A run that cannot proceed does not proceed
partially and hope.

The recording rule is the same shape: **a failed call is still a record.** It carries its position
fields and its attempt count, because those are written before the request goes out. The log is
append-only, and "bad" rows are data.

### Provenance has to be a mechanism, not a promise

Several properties of this repository are true because something mechanical enforces them, not
because a document asks nicely:

- `retry_count` is always `null` because the SDK sets its header on the *request* and the recorder
  reads the *response*. The field is kept so old lines stay readable, is never backfilled, and
  `null` means **not reported** — never "no retries happened".
- `transport_attempt_count` counts wire attempts locally, with `attempt_count_source` naming the
  mechanism. It licenses exactly one sentence: *this call was not observed to retry.* It does
  **not** license "this is pure model latency" — DNS, TCP, TLS, connection-pool state, server
  queueing, upstream load and local scheduling all sit inside the same window.
- Position fields (`case_sequence_index`, `logical_request_index_in_run`, `client_session_id`,
  `is_first_request_in_client_session`) exist because position and arm identity were perfectly
  confounded in the first three A/B experiments. A missing field means **not recorded** and never
  means zero.
- `model_requested` and `model_resolved` are both recorded, because an alias can move and only the
  response says which model actually answered.

The general lesson: if a property matters, put it somewhere a machine checks it. A comment in a
document is a convention, and conventions are exactly what quietly stop being true.

### Derived artifacts cannot drift if they are recomputed

Every file under `results/` except the two canonical logs is rebuilt from the logs on demand.
`final-report` recomputes each number as it writes, so a report that disagrees with the log is
detectably stale rather than quietly authoritative. The authoritative artifacts are tracked;
the derived ones are gitignored precisely so they cannot become a second source of truth.

---

## 3. Negative and killed findings

**This section is the one that distinguishes the project.** These are results that looked
interesting, were investigated properly, and did not survive.

P2 applied one standard to every candidate: *is this both novel relative to TypeSafe's public
material, **and** supported by our own data?* Seven candidates were retired. The two with the
**largest local effect sizes** were retired on the strength of prior art, not on the strength of
this repository's own data. As the triage puts it:

> No candidate was killed for being unflattering, and no candidate was preserved for being
> interesting.

### Killed

| Candidate | Class | Why it did not survive |
|---|---|---|
| Stable label, moving distribution | Officially documented | **Both** grounds suffice independently: it is officially entailed by the vendor's own reported label flips and non-zero label spread, **and** a public reproduction sent the identical request five times and published the jitter floors over ~1,490 captured calls. The vendor does not use our sentence; the sentence is not the thing. |
| Batching cuts input tokens | Independent reproduction | Expected shared-state amortisation. Public third-party measurements report per-row token costs for batches of 20 **and** an accuracy-versus-batch-size curve — a study that goes further than this bench, which never varied batch size. |
| The 0.75 → 0.20 instruction effect | Officially documented | A direct instance of a documented failure mode, with a remedy the docs already prescribe. Each arm was n = 1 and neither value is ground truth. The *effect* did not die — its *attribution* moved to P3. |
| Ambiguous case cleared a 0.60 gate | Our own policy | Pure threshold arithmetic on a constant this repository chose. The published k=3 expression reproduces 0.61 **exactly**, and the returned margin was 0.74 vs. 0.26 — the "ambiguity" was a property of the state design, not of the returned distribution. |
| Fan-out trades input for output | Not a Jev finding | Generic speculative-execution tradeoff. And on this product the "wasted" resource is **output** tokens, which the published price card rates at zero — so "unconsumed but paid for" has no cost content here. The billed quantity went **down** by 400 input tokens. |
| `confidence` not recomputable from `probabilities` | Not a Jev finding | An artifact of 2-decimal API rounding, not a behaviour of the model. Across 74 answers there were 4 collision groups — most starkly `(1.0, 0.0, 0.0)` appearing 13 times, 11 at confidence 1.0 and 2 at 0.99. The finding is about how much **our record** can resolve. |
| Every correct route was suppressed | Our own policy | The suppressions are fully explained by constants chosen here — a 0.8 floor and a 0.5 review line. Moving either constant would change the outcome with no model call at all. The honest line is that the router refused to execute *on our instructions*. |

### Held, then not authorized

One candidate was **held** rather than killed: *is variability a function of boundary proximity?*
Mid-scale payloads moved on every repeat; a payload pinned at 1.0/0.0 could not. It was held
because the boundary cannot be located in advance without a pilot — so it fails the falsifiability
bar — and because the contrast is confounded by a **ceiling effect**: a distribution pinned at
1.0/0.0 has no room to move, so its "stability" is saturation, not robustness. Not authorized for
publication until redesigned.

### The one that survived, and then returned a null

Exactly one candidate cleared triage: **which input field carries a decision boundary — the
instructions or the criteria?** The official remedy for the literal-reading failure mode is given
as a bundle and never decomposed; the largest local effect (0.55) was produced with both fields
changed together; and no controlled public attribution was found. Note the novelty check came back
`PUBLIC_NOVELTY_UNRESOLVED` — recorded as *unresolved*, never as "nobody has discovered this".

P3 ran it: four arms, a 2×2 of the two fields, three repeats each, twelve calls, design and
thresholds frozen before the first request.

**Verdict: `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`.**

| Arm | Noul values | Median | Range |
|---|---|---:|---:|
| neither | 0.77, 0.76, 0.75 | 0.76 | 0.02 |
| instruction only | 0.31, 0.33, 0.29 | **0.31** | 0.04 |
| criteria only | 0.37, 0.36, 0.33 | **0.36** | 0.04 |
| both | 0.20, 0.21, 0.20 | 0.20 | 0.01 |

Both single-field arms moved most of the way to the explicit baseline, and they landed **0.05
apart from each other** against a 0.56 end-to-end gap. The pre-registered rule (K1) killed the
attribution: no assignment of a single-field arm left its counterpart near the vague baseline.

Descriptive arithmetic, recorded but **not** part of the decision rule: instruction-only recovered
80.4% of the gap, criteria-only 71.4%. The endpoint arms replicated — the original run's 0.75 → 0.20
move came back as 0.76 → 0.20.

**A null result is a result.** The correct summary is *the effect could not be attributed to one
field under this design and this sample size* — not *the boundary lives in both fields*, and
certainly not *criteria are what matter*. Two limits are load-bearing here: the crossed arms pair a
broader field with a narrower one rather than two independently varying definitions
(`FIELD_ALIGNMENT_CAVEAT`), and n = 3 per arm supports a median and a range and no interval
estimate.

Full reasoning: [P3 result](../audits/P3_BOUNDARY_LOCUS_RESULT.md) ·
[P3 preregistration](../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) ·
[P2 triage](../audits/P2_JEV_INSIGHT_TRIAGE.md).

---

## 4. Not established

Scope limits for the whole repository. These are not open tasks; they are the edges of what this
evidence can carry.

| Not established | Why |
|---|---|
| General accuracy | There is no ground truth anywhere in this bench. "4 of 4" is a count on synthetic cases, never a rate. |
| Calibration — in either direction | No outcome rate exists. **This repo must never be cited as validating or falsifying calibration.** |
| Model latency benchmark | Latency is recorded, not benchmarked. No speedup is claimed and no arm is called faster. |
| Determinism — or non-determinism | A handful of repeats on two payloads is not a determinism verdict. |
| Universal batching ratio | The 4.26× figure is a property of one payload where all questions share one state. |
| Broad hallucination benchmark | Nothing here probes factual correctness. Only schema conformance on benign payloads was measured. |
| Composite-dimension independence | The correlation between the four dimensions was never measured. |
| A tested allowed-handler execution path | `ACTUAL_HANDLER_EXECUTION_UNTESTED` stands: an allowed route has not been observed reaching the handler under a real answer. |
| Any real external side effect | Every handler is inert. No file was written, no network call made, no message sent. |
| Production safety | Nothing here certifies any pattern as safe against real systems, real customer data, or real money. |
| Vendor-claim adjudication | Official figures are recorded as claims about TypeSafe's workload, never restated as local measurements. |

### The current honest state of the evidence

> Across 42 core records and 15 claimed official behaviours, this bench has **no finding about Jev
> that is both novel relative to TypeSafe's public material and supported by its own data.** Every
> large local effect either restates an officially documented behaviour or is an artifact of our own
> Python-side policy.

That is the state after P1, P2 and P3. It is a deliberate outcome, not a failure — the repository
exists to test findings, not to accumulate them, and the tests came back negative. A future
experiment could change it; nothing so far has.

### A known documentation defect

The P1 audit states that "42 of 42" `Noul` answers carry no `confidence` field. Verified directly
against the canonical log during P3.5, the correct count is **45 of 45** — P1 conflated the Noul
count with the record count. The claim itself is unaffected: every `Noul` answer in the log does
lack the field. P1's frozen text was **not** edited, because it is a historical audit artifact.
Recorded here rather than silently corrected.
