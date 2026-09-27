# Blog claim contract — writing about `v0.1.0`

**Who this is for.** Whoever writes the technical blog post about this repository. It is a
guardrail, not a draft: it fixes *what may be said* and leaves *how to say it* entirely open.

**What it binds.** Every public-facing sentence derived from this release — blog prose, thread,
talk, README rewrite, issue comment, résumé bullet. It is the claim source of truth. If a sentence
you want to write is not in class A or class B below, it is not available, no matter how well it
would read.

**Why it exists.** The repository's entire value is that its claims are calibrated to its evidence.
A blog post that overstates one result does not merely add a bad sentence — it retroactively
degrades the thing being cited, because a reader who catches the overstatement has no reason to trust
the other numbers.

**Where the content comes from.** Sections 5, 6 and 7 of
[`PUBLIC_EVIDENCE_FREEZE.md`](PUBLIC_EVIDENCE_FREEZE.md), which inherit from
[`findings.md`](../../findings/findings.md), the [P1 audit](../../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md),
the [P2 triage](../../audits/P2_JEV_INSIGHT_TRIAGE.md) and the
[P3 result](../../audits/P3_BOUNDARY_LOCUS_RESULT.md). Nothing here is a new claim; this file only
classifies claims that already exist.

**The two standing rules.**

1. **Label every number.** A sentence carrying a figure must let the reader tell whether it is an
   OFFICIAL CLAIM by TypeSafe about *their* workload, a LOCAL MEASUREMENT from these logs, or a
   DERIVED CALCULATION from them. A vendor figure presented as something we measured is the single
   worst failure available here.
2. **Carry the scope with the number.** A figure separated from its scope is a different and larger
   claim. "4.26× cheaper" and "4.26× fewer input tokens on one payload where five questions shared
   one state" are not the same sentence.

---

## A. `SAFE_TO_STATE`

Sentences that may be written flatly, without a qualifier attached. Each is a statement about **this
repository** — what it did, what it contains, what state it reached. That is the class where flat
assertion is honest, because the claim is about the artifact and the artifact is in front of the
reader.

**About the release itself**

- This repository is a measurement bench for TypeSafe's Jev model; its product is the auditability of
  its evidence.
- Release `v0.1.0` freezes the P0–P3.6 output into a versioned, citable evidence set.
- The frozen core log holds 42 records with SHA-256 `38e67630…`; the P3 log holds 12 records with
  SHA-256 `17f36f75…`. Both are published in full, unredacted.
- **No API call is made by installing, testing, building, or running the report commands.** Only
  `run` and `run-all` spend money, and neither works without an explicit budget.
- The P3 twelve calls were made under a design, payload, threshold set and decision rule **committed
  before the first request**.
- The offline suite blocks sockets outright, so an accidental API call fails loudly.

**About the state of the science**

- **The scientific state of this release is `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`.**
- **The primary P3 result is a null: `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`.** The original
  instruction-precision effect could not be attributed to `instructions` or `criteria` alone under
  the preregistered one-payload 2×2 design.
- Seven triage candidates were retired, **including the two with the largest local effect sizes**,
  and they were retired on prior art rather than on this repository's own data.
- A candidate *was killed for being interesting* nowhere in this repository. No candidate was
  preserved for narrative reasons.
- The negative results are published on the same footing as the positive ones.
- **A null result is a result.** The repository is designed to test findings, not to accumulate them.

**About the engineering**

- Every real API call produces exactly one record, whether it succeeds or raises, and the core log's
  SHA-256 is identical at `e20fad5` and at every commit since — including after the P3 analyzer
  repair. This is verified by CI, not asserted in prose.
- An analyzer defect was found **after** P3's measurements were taken and was disclosed in the commit
  that recorded them, then repaired in a later commit that made no new measurement and changed no
  threshold, rule or verdict.
- Derived artifacts are regenerated in CI and the build fails if the committed copy differs.
- Credential resolution fails closed: an absent, empty, malformed, duplicated or unreadable source
  stops the run before a request is sent, rather than proceeding with a guess.

**About the official sources**

- The audit is against a **dated snapshot**: TypeSafe's material as read during P1, accessed
  2026-09-22, with a per-document digest recorded for every source.
- Five source-internal divergences were recorded rather than resolved — including two official pages
  using different `confidence` thresholds for the same worked example.

---

## B. `SAFE_WITH_SCOPE`

Sentences that may be written **only with the scope attached**, in the same sentence or an
immediately adjacent one. The scope in the right-hand column is not decoration and is not
interchangeable with a shorter one.

| Statement | Scope that must accompany it |
|---|---|
| Batching questions that share one state reduced input tokens by **4.2647×** | "on one payload, with five questions sharing one state, over two order-balanced cycles in one session." Also: this is **not** TypeSafe's published `12.2×` and is not comparable to it. |
| Both fields moving vague → explicit moved the `Noul` median **0.76 → 0.20** (gap `0.56`) | "on one synthetic payload, on one account, in one session, three repeats per endpoint arm, at one model version." |
| Instruction-only recovered **80.4%** of that gap; criteria-only **71.4%** | These are **descriptive arithmetic, not part of the decision rule**. No threshold was set from them and the verdict is unchanged if they are ignored. Say so. |
| The two single-field arms landed **0.05 apart** while each moved most of the way to the explicit baseline | The preregistered separation rule killed the attribution. This is **not** evidence that the effect lives in both fields. |
| The endpoint arms replicated the original observation | "as an ordering and a gap magnitude, on this payload, at n = 3 per arm." |
| Typed output semantics: `Choice` = label + distribution, `Noul` = one probability and no `confidence`, `Score` = value + `confidence` | "across 119 answers from 42 synthetic records on one account at one model version." |
| **45 of 45** `Noul` answers carry no `confidence` field | This is the corrected count. P1's frozen text says 42 of 42; the correct figure and the reason are in the [errata registry](../../ERRATA.md#err-001--p1-audit-states-the-wrong-noul-count). If you cite P1's number, cite the erratum too. |
| Latency was recorded and is reported per record | "as wall-clock around one SDK call, containing DNS, TCP, TLS, connection-pool state, server queueing, upstream load and local scheduling. No speedup is claimed and no arm is called faster." |
| Cost figures | "a local estimate against one published price table. **TypeSafe Console billing is authoritative.**" |
| `transport_attempt_count` reads `1` on 35 core records | "this call was not observed to retry." That licenses **exactly one sentence**. It does **not** license "this is pure model inference latency." It is a local observation, never a server-side statement. It is **not recorded** on the other 7 records, and a missing attempt count is not a zero. |
| Any figure from `results/JEV_LOCAL_EVALUATION_FINAL.md` | "a derived artifact, regenerated from the canonical log." Cite the log, not the report, for a number that matters. |
| A future live run reproducing (or failing to reproduce) these numbers | "a second measurement." It has **not** validated the frozen numbers and has **not** falsified them. |
| Anything about novelty | P3's question was reached with its public-novelty check `PUBLIC_NOVELTY_UNRESOLVED` — recorded as unresolved, **never** as "nobody has found this". Any sentence about novelty must be scoped to "we found no public attribution", never "there is none". |

---

## C. `DO_NOT_STATE`

Statements that are **not available at any scope**, because the evidence does not exist and no
qualifier can create it. Each is listed with the reason, so that a writer who wants one can see which
gap would have to be closed first.

| Do not state | Reason |
|---|---|
| **Jev is generally more accurate** (or less accurate) than anything | There is no ground truth anywhere in this bench. `NO_GENERAL_ACCURACY_CLAIM`. "4 of 4" is a count on synthetic cases, never a rate. |
| **Our experiment validates (or falsifies) Jev's calibration** | No reliability diagram, no ECE, no Brier score, no independent ground-truth dataset; `04_confidence` has two cases. `NO_CALIBRATION_VALIDATION`. |
| **Jev is deterministic** — and equally, **Jev is non-deterministic** | A handful of repeats on two payloads is not a verdict in either direction, and no official source read makes a claim either way. `NO_DETERMINISM_VERDICT`. |
| **Jev is universally 4.26× cheaper** | `4.2647×` is a property of one payload with one shared state. It is not a price ratio, not a general ratio, and not comparable to the vendor's figure. `NO_UNIVERSAL_BATCHING_RATIO`. |
| **Jev has a general preference for criteria over instructions** (or the reverse) | P3 measured one payload at n = 3 per arm under `FIELD_ALIGNMENT_CAVEAT` and returned a null on attribution. It supports no ordering, and it does not support "the boundary lives in both fields" either. `NO_GENERAL_INSTRUCTION_VS_CRITERIA_FIELD_PREFERENCE`. |
| **Jev is proven suitable for NAS** (or for architecture search, or for any workload this repo never ran) | Nothing in this release tests NAS. There is no NAS experiment, dataset or measurement here. `NO_NAS_CLAIM`. |
| **Our observations are novel discoveries** | P2's triage found that every large local effect either restates an officially documented behaviour or is an artifact of our own Python-side policy, and the state string is `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`. The novelty checks that were run came back public-artifact-positive or `UNRESOLVED`. |
| **Jev cannot hallucinate** / **our results certify schema safety** | Nothing here probes factual correctness, and the only axis measured is schema conformance on benign payloads with no adversarial attempt. `NO_BROAD_HALLUCINATION_BENCHMARK`. |
| **This pattern is safe for production** | Every handler is inert; no allowed route was observed reaching its handler under a real answer (`ACTUAL_HANDLER_EXECUTION_UNTESTED`). `NO_PRODUCTION_SAFETY_CERTIFICATION`. |
| **A TypeSafe figure is "really" our number** (or the reverse) | Official figures are claims about TypeSafe's workload. They are not commensurable with these logs in either direction, and no adjudication is offered. |
| **Jev is fast** — with any figure attached | Latency here is a superset window, not a benchmark. `NO_MODEL_LATENCY_BENCHMARK` / `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK`. |
| **The four scoring dimensions are independent** | Their correlation was never measured. |
| **This release is peer-reviewed, endorsed by TypeSafe, or a standard** | It is one account's self-published local evidence. It has no DOI, no GitHub Release and no PyPI publication. |
| **The retired designs were run** | Five designs were registered at freeze and retired before publication, never run. Retiring an unrun design removes no evidence. |

**One more, about the repository rather than the model:** do not describe this repo's conventions as
a security boundary. They are conventions a cooperative reader follows; the mechanisms that hold are
enumerated in [`CLAUDE.md`](../../../CLAUDE.md), and the limits are in
[`SECURITY.md`](../../../SECURITY.md).

---

## Self-check before publishing

Run these against the draft. They are cheap, and each one maps to a real failure mode above.

1. **Is every figure labelled** as OFFICIAL CLAIM, LOCAL MEASUREMENT, or DERIVED CALCULATION?
2. **Does every figure keep its scope** — payload, repeat count, session, model version?
3. **Is there any sentence that survives deleting the qualifier** and reads *bigger* without it? Fix
   that sentence, not the qualifier.
4. **Is the null result in it?** A post that reports only the interesting effect is a post that
   misrepresents this repository. The P3 null and the retired candidates are the story.
5. **Does it say `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** anywhere a reader will see it, or does
   it leave the impression of a discovery?
6. **Would any sentence change** if a TypeSafe engineer read it? If yes, is it because it is wrong,
   or because it is unflattering? Only the first is a reason to edit.
7. **Does it say what this is not?** A post with no non-claims section has almost certainly
   overclaimed somewhere else.

**If a sentence is not in A and not in B-with-its-scope, it is not available.** The correct response
is to rewrite the sentence down to what the evidence carries — never to widen the evidence.
