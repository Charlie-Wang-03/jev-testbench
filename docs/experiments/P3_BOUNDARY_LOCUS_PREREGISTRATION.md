# P3 — Boundary locus: instructions vs criteria (PRE-REGISTRATION)

**Preregistration ID**: `P3_BOUNDARY_LOCUS_V1`
**Experiment name**: `P3_boundary_locus`
**Status**: frozen before the first API call. Nothing below may be edited after a measurement.
**Question**: `P3-Q1`

This document is written and committed **before any Jev inference call**. It fixes the payload, the
arms, the order, the repeat count, the statistic, the decision rule, and the failure classification.
After the first request, none of them may change — including in response to a result that would be
more interesting if one of them were different.

---

## 1. The question

`07_instruction_precision` moved one byte-identical state's Noul from **0.75** to **0.20** by
changing the `instructions` and the `criteria` together (`docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md`,
row TS-JEV-LIMIT-001). The design deliberately changed both fields as one "explicitness" variable, so
it cannot say which field carried the 0.55 move. That limit is already recorded in this repository.

P3 asks exactly one thing:

> On the `07_instruction_precision` payload, is the boundary effect driven mainly by making
> `instructions` explicit, mainly by making `criteria` explicit, or can this sample not attribute it
> to one field?

**Any answer is a valid outcome**, including "cannot attribute". P3 is a *replication* experiment,
not a novelty hunt. A clean answer of "no single field" is a complete result, not a failure.

---

## 2. Frozen payload

The state, both instructions, and both criteria are the `07_instruction_precision` strings, reused
byte-for-byte. No wording is "improved".

**State** (82 bytes, byte-identical in all four arms):

```
The report export spun for ten minutes and never finished. I gave up and used CSV.
```

**Vague boundary** (the 07 vague arm, verbatim):

* instructions: `Is this a serious issue?`
* criteria true: `Something went wrong for the user`
* criteria false: `Nothing went wrong for the user`

**Explicit boundary** (the 07 explicit arm, verbatim):

* instructions: `Does the state describe a situation where a primary requested capability could not complete, and no equivalent within-feature workaround allowed completion?`
* criteria true: `A primary requested capability could not complete, and no equivalent within-feature workaround allowed completion`
* criteria false: `The capability completed, or an equivalent within-feature workaround allowed completion, or no failure is described`

The point of P3 is to pull apart two factors that already existed. Re-writing either boundary would
create a question the P2 triage never preregistered, and would make the result incomparable to 07.

---

## 3. Arms

A 2x2 of the two fields. Four arms, nothing else varies.

| arm | label | instructions | criteria |
| --- | ----- | ------------ | -------- |
| `N` | NEITHER | vague | vague |
| `I` | INSTRUCTION_ONLY | explicit | vague |
| `C` | CRITERIA_ONLY | vague | explicit |
| `B` | BOTH | explicit | explicit |

Two of these are not new:

* **`N` is the 07 `vague_boundary` question, object for object.**
* **`B` is the 07 `explicit_boundary` question, object for object.**

This is asserted against the live registry rather than checked by eye:
`test_arm_n_equals_the_07_vague_question_object` and `test_arm_b_equals_the_07_explicit_question_object`
compare `model_dump()` of the assembled question against `get_experiment("07_instruction_precision")`.
The single-field arms are asserted to differ from `N` in exactly one field
(`test_instruction_only_swaps_the_instruction_and_nothing_else`,
`test_criteria_only_swaps_the_criteria_and_nothing_else`).

---

## 4. Semantic consistency gate (pre-spend)

P2 named this experiment's largest risk before it was designed: a single-field arm may not be an
isolated variable at all, but rather a construction whose `instructions` and `criteria` disagree,
which would exercise a *different* documented failure mode (TS-JEV-LIMIT-008, contradictory
instructions and criteria) instead of the one under study.

The gate below was run **before any call**. It asks, per crossed arm: do `instructions` and the
true/false `criteria` still answer the same binary proposition, differing only in boundary
specificity?

Two propositions are in play:

* **P_vague** — "is this a serious issue?" An evaluative judgment with no stated operational boundary.
* **P_explicit** — "a primary requested capability could not complete, and no equivalent
  within-feature workaround allowed completion." A two-clause operational test.

### Arm `I` — explicit instructions, vague criteria

* instruction's yes-region: capability blocked **and** no workaround.
* criteria true: "something went wrong for the user"; criteria false: "nothing went wrong for the user".
* **Direction test**: does the instruction's yes imply the criteria's true? Yes — a primary
  capability failing outright with no workaround is hard to describe as "nothing went wrong for the
  user". **There is no state in which the instruction demands `true` while the criteria demand
  `false`.**
* **Divergence region**: a state where the capability was blocked *but* a workaround existed. The
  instruction reads that as `false`; the vague criteria's true-condition may still cover it.
  **The frozen payload sits in this region**: the export never finished (capability blocked) and the
  user fell back to CSV (arguably an equivalent within-feature workaround).
* **Finding**: breadth mismatch — here the *criteria are broader* than the instruction. Aligned in
  the yes-region. No direct contradiction.

### Arm `C` — vague instructions, explicit criteria

* instruction's yes-region: "serious issue", unscoped.
* criteria true: the operational test; criteria false: its exhaustive negation (completed, or a
  workaround allowed completion, or no failure described).
* **Direction test**: could the instruction demand `true` while the criteria demand `false`?
  Because "serious issue" is unscoped, a state could in principle be serious for reasons outside
  capability completion (data loss, security, cost). So the two are not equivalent.
* **For this payload**: the state is a capability-failure narrative, so the criteria are a
  legitimate operationalization of "serious issue" here, and no direct conflict arises.
* **Finding**: breadth mismatch — the criteria *narrow* the instruction to one operationalization.
  No direct contradiction.

### Gate outcome

```
SEMANTIC GATE: PASS — proceed with FIELD_ALIGNMENT_CAVEAT
```

Neither crossed arm exhibits a direct semantic contradiction: in neither arm does the instruction's
yes require the criteria's false, nor do the two sides define unrelated events. Both crossed arms
pair a broader field with a narrower one.

**Therefore, recorded now, before any measurement:**

> `FIELD_ALIGNMENT_CAVEAT` — the crossed arms are mixed-specificity constructions, not two
> independently varying definitions. Any result from P3 is a statement about *this* construction on
> *this* payload. It is not evidence that Jev internally "stores" a decision boundary in a
> particular field, and it does not license "Jev primarily reads criteria" or "Jev primarily reads
> instructions" as general claims.

**A pre-registered interpretation hazard, stated in advance**: because the payload sits in arm `I`'s
divergence region, `I` is the arm where the two fields can pull toward different answers. If `I`
returns an intermediate value, that is a plausible resolution of that tension and must **not** be
read as a locus signal on its own. The GO conditions below are deliberately written so that a single
mid-range arm cannot produce a GO verdict.

---

## 5. Order

Frozen, deterministic, counterbalanced. No re-ordering after the run.

```
Round 1:  N -> I -> C -> B
Round 2:  B -> C -> I -> N
Round 3:  C -> N -> B -> I
```

Which is the twelve-position sequence:

```
N1 I1 C1 B1 B2 C2 I2 N2 C3 N3 B3 I3
```

Each arm occupies each round-position exactly once. All twelve calls run through **one
`TypeSafeClient`**, in **one client session**, **serially**. No concurrency.

P3 makes **no latency claim**, so ordering controls only the coarsest arm/position confound and is
not a substrate measurement. `transport_attempt_count` and `transport_retry_count_observed` are
still recorded for every call, per the repository's latency rules.

---

## 6. Repeats and budget

* repeats per arm: **3**
* arms: **4**
* logical calls: **4 x 3 = 12**

`MAX_LOGICAL_CALLS = 12` is a hard ceiling, enforced by the runner.

Not permitted: a 13th call; re-running a failed position; "three more to confirm"; adaptive
repeat counts; a new payload; a new arm. The SDK's own transport retries do not create a new logical
call, but they must be visible via the attempt-count fields.

**A logical request that fails consumes its position.** It is not re-executed, and the count does
not become 13.

---

## 7. Model version

**The moving alias `jev-latest` is not used.** The requested model is fixed:

```
jev-1.13.0
```

The 42 frozen records all resolved to `jev-1.13.0`, and a comparison against them is only meaningful
at the same version. `model_requested` and `model_resolved` are recorded on every row.

If a response reports `model_resolved != jev-1.13.0`, the run **stops before spending the remaining
positions** and reports `P3_MODEL_VERSION_MISMATCH`. Calls already made stay in the log and are not
deleted.

---

## 8. Statistics — frozen before the first call

Three repeats leave one ambiguity open that is closed here, in advance:

```
arm central value  = median of the 3 Noul values
within-arm spread  = max - min
```

* Median, not mean: with n=3 the median is one of the three values the API actually returned, so an
  arm's central value is always a real observation rather than an average of them.
* **All three raw values are reported.** The median summarises them; it does not replace them.
* **No confidence interval.** n=3 cannot support a meaningful interval estimate, so none is computed.
* Comparisons are made on values rounded to 4 decimals, so a value landing exactly on a threshold
  behaves the same way every time rather than depending on binary-float representation.

---

## 9. Decision rule — frozen

The comparison baseline is the 07 observation: **vague 0.75 -> explicit 0.20**, a move of **0.55**.
That is one local run, one call per arm — a single observation, which is why P3 repeats.

Let:

```
I_med = median(INSTRUCTION_ONLY)
C_med = median(CRITERIA_ONLY)
```

### GO conditions — all three required

| id | condition | meaning |
| --- | --------- | ------- |
| GO-1 | some single-field arm has `median <= 0.475` | reproduces >= 50% of the 0.55 move, same direction (`0.75 - 0.275 = 0.475`) |
| GO-2 | the other single-field arm has `0.64 <= median <= 0.86` | moves <= 20% of that move (`abs(median - 0.75) <= 0.11`) |
| GO-3 | **both** single-field arms have `spread <= 0.05` | tight enough to compare at all |

GO-1 and GO-2 are **symmetric**: whichever single-field arm moved, the other must have stayed near
the vague baseline. Both assignments are tried; the condition holds if either does.

Thresholds are **inclusive**. `median == 0.475` passes GO-1; `median == 0.64` and `median == 0.86`
pass GO-2; `spread == 0.05` passes GO-3.

All three must hold for the verdict `P3_GO_LOCAL_LOCUS_SIGNAL`.

### KILL conditions — any one fires the KILL

| id | condition |
| --- | --------- |
| K1 | `abs(I_med - C_med) < 0.10` |
| K2 | **any** arm has `within-arm spread > abs(I_med - C_med)` |
| K3 | the pre-spend semantic audit finds a crossed arm's instructions and criteria mutually inconsistent |

K2 reads **all four arms**. GO-3 is deliberately scoped to "both single-field arms"; K2's "any arm"
is deliberately unscoped, and that contrast is intended. No arm's noise may exceed the
between-arm separation the attribution rests on.

K3 applies only before the spend. Fired pre-spend it means `0` calls and an immediate stop.

Any KILL condition yields `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`. **After a KILL, redesigning and
continuing to call is forbidden.**

### Endpoint validity guard

`N` and `B` are three-repeat versions of the two 07 endpoints. They are **diagnostic only** and were
never available to adjust a threshold after the fact.

| id | condition |
| --- | --------- |
| E1 | `N_med > B_med` |
| E2 | `N_med - B_med >= 0.275` (at least half the original 0.55 endpoint gap) |

If E1 or E2 fails, the endpoints no longer carry the effect the arms are being compared against, and
even a numerically satisfied GO is **not** claimed:

```
P3_ATTRIBUTION_NOT_INTERPRETABLE
```

E2 uses the same "at least 50% of the original move" bar as GO-1, rather than an invented number. It
guards the degenerate case where the endpoints have collapsed together while a single-field arm
still lands under the GO-1 line — a GO claimed against a baseline that no longer shows the effect.

Both guards are **conservative**: they can block a claim. **They can never produce one, and they can
never turn a KILL into a GO.**

### Evaluation order — frozen

A verdict must be a function of the numbers, not of the order somebody happened to check them in:

1. **Completeness** — every arm needs all three values and the log needs exactly 12 records,
   otherwise `P3_EXECUTION_INCOMPLETE`.
2. **Endpoint validity** — E1 and E2, otherwise `P3_ATTRIBUTION_NOT_INTERPRETABLE`.
3. **KILL** — K1 or K2, otherwise
4. **GO** — GO-1 and GO-2 and GO-3, otherwise
5. `P3_INCONCLUSIVE_AND_STOP`.

GO and KILL cannot both fire: GO-1 with GO-2 implies a separation of at least `0.64 - 0.475 = 0.165`,
which clears K1's 0.10, and GO-3's `spread <= 0.05` then clears K2. The rule is still ordered
explicitly so the outcome never depends on evaluation order.

### Verdict vocabulary

Exactly these, with no partial-credit variant between them:

```
P3_GO_LOCAL_LOCUS_SIGNAL
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
P3_ATTRIBUTION_NOT_INTERPRETABLE
P3_INCONCLUSIVE_AND_STOP
P3_DESIGN_INVALIDATED_BEFORE_SPEND
P3_MODEL_VERSION_MISMATCH
P3_EXECUTION_INCOMPLETE
```

---

## 10. Result interpretation ceiling

**If GO**, the strongest licensed statement is:

> On this one preregistered payload, one field-specific arm reproduced most of the original
> explicit-boundary shift while the other remained near the vague baseline, under three repeats per
> arm.

Not licensed, at any time:

> Jev stores the decision boundary in `criteria`.
> Jev generally ignores `instructions`.
> Jev primarily reads `criteria`.

**If KILL**, the required statement is:

> The original 0.55 effect could not be attributed to one field under this design and sample size.

That is a complete result. It is not a failed experiment.

---

## 11. Canonical log

The measurement source of truth is:

```
results/p3_boundary_locus/usage.jsonl
```

**`results/usage.jsonl` is not appended to.** Its 42 records are frozen historical evidence; writing
P3 rows into it would invalidate the published SHA-256 and destroy the provenance of P0–P2.

The P3 log follows the same rules as the root log:

* append-only, one row per real logical call, written by `UsageRecorder`;
* a failed call still produces a row — a failed call is data;
* never rewritten, truncated, reordered, or deleted.

It must be absent or empty before the run, and hold exactly 12 records afterwards. Fewer than 12
successful records is **never** a reason to run more calls.

### Record schema

Every row is a schema-3 `CallRecord`, with `experiment = "P3_boundary_locus"`, plus these notes:

| note | value |
| ---- | ----- |
| `p3_question` | `"P3-Q1"` |
| `arm` | `N` \| `I` \| `C` \| `B` |
| `arm_label` | `NEITHER` \| `INSTRUCTION_ONLY` \| `CRITERIA_ONLY` \| `BOTH` |
| `repeat` | `1` \| `2` \| `3` |
| `instruction_specificity` | `vague` \| `explicit` |
| `criteria_specificity` | `vague` \| `explicit` |
| `sequence_index` | `0..11` |
| `preregistration_id` | `"P3_BOUNDARY_LOCUS_V1"` |

No credential material is recorded. Noul carries no separate confidence, so the primary result is
the `noul` scalar alone, with ordinary usage and latency provenance. The repository rule
`DO_NOT_RECONSTRUCT_CONFIDENCE_FROM_QUANTIZED_PROBABILITIES` continues to apply; P3 does not need a
confidence and does not derive one.

---

## 12. Pre-spend offline tests

The first API call may not be made until the whole suite passes:

```
uv run pytest
```

P3-specific offline tests (`tests/test_p3_boundary_locus.py`) establish at minimum:

* all four arms send the state byte-identically, and it equals the 07 state;
* `N` equals the original vague question object, `B` equals the original explicit question object;
* `I` and `C` each swap exactly one field, verified field by field;
* exactly 4 arms, exactly 3 repeats each, exactly 12 logical positions;
* the running order is the frozen counterbalanced order;
* the hard ceiling is 12 and the runner passes it;
* the median and spread implementations are correct;
* GO threshold boundary equality behaves inclusively, and just outside does not;
* K1 and K2 logic, including K2's unscoped "any arm" reading;
* the endpoint validity guard, including that it cannot promote a KILL to a GO;
* the analyzer follows synthetic records, including early-stopped and incomplete logs;
* the dedicated results path is not the root `results/usage.jsonl`;
* `run` refuses a log that already holds records.

Any failure here means **no API call**.

---

## 13. Provenance

Two commits, and the order matters.

**Commit A — before any API call**

```
Preregister P3 boundary locus experiment
```

Contains: the experiment module, the analyzer, the tests, this document, and the minimal
`.gitignore` rule that tracks the P3 log. Commit A must be **pushed**, the working tree **clean**,
and its SHA **recorded** before the first request.

**Commit B — after the API calls**

```
Record P3 boundary locus measurements
```

Contains only: `results/p3_boundary_locus/usage.jsonl`, the generated result document, and any
purely factual measurement manifest. **Commit B must not modify experiment code or decision
thresholds.**

If an analyzer bug surfaces after seeing the numbers: **stop and report it.** Fixing the analyzer
while looking at the result and then still calling the analysis preregistered is not acceptable.

All twelve measurements must come from the exact code and thresholds in Commit A.
