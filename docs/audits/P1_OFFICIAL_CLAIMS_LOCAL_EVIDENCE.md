# P1 — Official Claims × Local Evidence Audit

**Stage:** P1 — source audit + evidence mapping. Not a new experiment, not a verdict hunt.
**Canonical local evidence:** `results/usage.jsonl` — 42 records, SHA-256
`38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b`.
**Official sources:** see [TYPESAFE_OFFICIAL_SOURCES.md](../sources/TYPESAFE_OFFICIAL_SOURCES.md).
**Audit date:** 2026-09-22. **No Jev/TypeSafe inference call was made in this stage.**

---

## 1. Primary verdict

```
P1_OFFICIAL_LOCAL_AUDIT_PASS
```

All four source-provenance, claim-separation, evidence-discipline and completeness gates were
met, and the canonical log was untouched. Three caveats are recorded rather than hidden, because
each one *limits* what this audit could read:

1. **Two official FAQ bodies were not retrievable** (home page and launch post — client-rendered
   accordions). Only question titles were recoverable, including "Is Jev deterministic?". The
   determinism question is therefore answered from Tier 1 documentation, not from the FAQ, and the
   audit says so instead of guessing.
2. **TypeSafe's own two surfaces disagree on the batching multiplier** (12.2x/10.0x vs 11.5x/9.6x).
   Both are recorded; neither is treated as authoritative over the other.
3. **Local `confidence` is not reproducible from the logged `probabilities`.** This is a limit on
   our own record, and it is written up in §7 as a caveat on any downstream claim — not as a
   finding about TypeSafe.

---

## 2. Promotion result

| Item | Value |
| --- | --- |
| Old `main` (pre-promotion) | `e20fad51acf39c232cddf822f016f09867d937ba` |
| Repair branch HEAD | `77357d96be081f2b521d753e3f0b1ce7708b5566` |
| Ancestry check | `git merge-base --is-ancestor origin/main origin/repair/p0-report-integrity` → PASS |
| Merge method | `git merge --ff-only` → `Updating e20fad5..77357d9`, **no merge commit** |
| Push | `e20fad5..77357d9  main -> main` |
| New `origin/main` | `77357d96be081f2b521d753e3f0b1ce7708b5566` ✅ |
| Canonical log after promotion | 42 records |
| Canonical SHA-256 after promotion | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` (unchanged) |
| Working tree | clean |
| Offline suite before promotion | **888 passed** |

No `force push` was used and no baseline movement was encountered.

---

## 3. Official source inventory

Full provenance, URLs, access timestamps, content hashes and per-source paraphrases are in
[TYPESAFE_OFFICIAL_SOURCES.md](../sources/TYPESAFE_OFFICIAL_SOURCES.md). Summary:

| Source ID | Type | Date | Accessed | Scope |
| --- | --- | --- | --- | --- |
| TS-IDX | Docs index (`llms.txt`) | — | 2026-09-22 | Whole doc set |
| TS-DOC-INTRO | Docs — Introduction | — | 2026-09-22 | Jev, general |
| TS-DOC-SYS1 | Docs — System One | — | 2026-09-22 | Jev, general |
| TS-DOC-STATE | Docs — State | — | 2026-09-22 | Jev, general |
| TS-DOC-PRIM | Docs — Primitives | — | 2026-09-22 | Jev, general |
| TS-DOC-CHOICE | Docs — Choice | — | 2026-09-22 | Examples show `jev-1.13.0` |
| TS-DOC-SCORE | Docs — Score | — | 2026-09-22 | Examples show `jev-1.13.0` |
| TS-DOC-NOUL | Docs — Noul | — | 2026-09-22 | Examples show `jev-1.13.0` |
| TS-DOC-ADV | Docs — Advanced: structure | — | 2026-09-22 | Jev, general |
| TS-DOC-CONF | Docs — Confidence | — | 2026-09-22 | Jev, general |
| TS-DOC-PRIMER | Docs — AI primer | — | 2026-09-22 | RLCD, calibration |
| TS-DOC-BUILD | Docs — How to build | — | 2026-09-22 | Architecture guidance |
| TS-DOC-USECASE | Docs — Use cases | — | 2026-09-22 | Capability catalog |
| TS-DOC-PATTERNS | Docs — Patterns | — | 2026-09-22 | Four patterns |
| TS-DOC-FANOUT | Docs — Speculative fan-out | — | 2026-09-22 | Batching pattern |
| TS-DOC-CONFROUTE | Docs — Confidence-gated routing | — | 2026-09-22 | 0.6 / >0.85 demo |
| TS-DOC-COMPOSITE | Docs — Composite scoring | — | 2026-09-22 | Weighted scoring |
| TS-DOC-INTENT | Docs — Intent routing | — | 2026-09-22 | Routing pattern |
| TS-DOC-MODELS | Docs — Models | — | 2026-09-22 | `jev-1.13.0`, price, limits, aliases |
| TS-DOC-JAG | Docs — Jev 1.13 jaggedness | Page states "Last reviewed 2026-09-17" | 2026-09-22 | **Scoped to `jev-1.13`** |
| TS-DOC-API | Docs — API reference | — | 2026-09-22 | `POST /v1/systemone` |
| TS-DOC-SKILL | Docs — Agent skill | — | 2026-09-22 | Agent integration |
| TS-DOC-CODINGAGENTS | Docs — Jev with coding agents | — | 2026-09-22 | What Jev is not |
| TS-DOC-SDK / TS-DOC-SDKRESP | Docs — SDK | — | 2026-09-22 | Python/JS SDK types |
| TS-DOC-CB-PAR | Cookbook — Parallel questions | — | 2026-09-22 | 13-question GDPR workload |
| TS-DOC-CB-CN | Cookbook — Self-consistency: nouls | "sampled on 2026-09-11" | 2026-09-22 | `jev-latest` → `jev-1.13.0`, 15 repeats |
| TS-DOC-CB-CC | Cookbook — Self-consistency: choices | "sampled on 2026-09-11" | 2026-09-22 | `jev-latest` → `jev-1.13.0`, 15 repeats |
| TS-SITE-HOME | Product page — home | — | 2026-09-22 | Marketing claims + FAQ titles |
| TS-SITE-MANIFESTO | Product page — manifesto | — | 2026-09-22 | Research positioning |
| TS-BLOG-INTRO | Blog — Introducing System One Models & Jev | **Sep 15, 2026** | 2026-09-22 | Flagship launch claim table |
| TS-BLOG-ANTIBENCH | Blog — Lies, Damned Lies, and Benchmarks | **Sep 11, 2026** | 2026-09-22 | Vendor's own eval stance |
| TS-BLOG-BITTEREST | Blog — The Bitterest Lesson | — | 2026-09-22 | Methodology essay; no Jev claims |
| TS-BLOG-TOOGOOD | Blog — AI: too good to be true… | — | 2026-09-22 | **Body not retrieved**; no claim rests on it |

**Version scope.** Every official claim below was published against `jev-1.13` / `jev-1.13.0`, the
same version that resolved on all 42 local records. The jaggedness page explicitly scopes itself to
`jev-1.13` and says many listed edges "will be fixed in later versions"; the Models page warns
aliases move. **A claim recorded here is a claim about Jev 1.13 as published on 2026-09-22, not a
permanent property.**

---

## 4. Claim inventory

Only claims that affect how Jev is understood, how our experiments read, or what a later writeup
could say are registered. Verbatim fragments are short and appear only where the exact wording is
itself the thing being audited.

Relationship labels: `DR` = `DIRECT_LOCAL_REPRODUCTION`, `DS` = `DIRECTIONAL_LOCAL_SUPPORT`,
`LE` = `LOCAL_EXTENSION`, `AT` = `APPARENT_TENSION`, `NT` = `NOT_LOCALLY_TESTED`,
`ND` = `NOT_TESTABLE_WITH_CURRENT_DESIGN`, `NO` = `NOT_AN_OFFICIAL_CLAIM`.

### Family A — Model identity / positioning

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-ID-001 | Jev is a System One model: it returns typed decisions and probabilities rather than generated text. | TS-DOC-INTRO, TS-DOC-SYS1, TS-BLOG-INTRO | Jev 1.13 | 01, 04, 05, 06, 12, 13, 13b | All 42 responses contain only typed `choice` / `score` / `noul` answers; no free-text field exists in any answer. | DR | Reproduction of the *shape*, not of any quality claim. | no |
| TS-JEV-ID-002 | "unstructured state in, typed probabilistic decisions out" | TS-BLOG-INTRO | Jev 1.13 | 01–13b | Every request took synthetic text/JSON state and returned typed answers with probabilities. | DR | Our states are small and synthetic. | no |
| TS-JEV-ID-003 | Jev is not a chat/code-completion model; it does not call tools or choose actions. | TS-DOC-CODINGAGENTS, TS-DOC-BUILD | Jev 1.13 | 12_function_routing | The model returned a *name* from a frozen registry; the code, not the model, was the only thing that could call a handler. | DR | Executing the handler is our design, not a model property. | no |
| TS-JEV-ID-004 | Text input only: string, JSON object, or array; no image/audio/video. | TS-DOC-SYS1, TS-DOC-STATE, TS-DOC-MODELS | Jev 1.13 | all | Every local state was text or JSON; modalities were never exercised. | DS | We never sent non-text, so this is untested in the negative direction. | no |

### Family B — Output semantics

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-SEM-001 | `choice` is the highest-probability option; `probabilities` is the full distribution; `confidence` summarises its spread. | TS-DOC-CHOICE | Jev 1.13 | 01, 02, 04, 05, 12, 13, 13b | **45 of 45** Choice answers: `choice` equals the argmax of `probabilities`. No counter-example. | DR | Argmax agreement is a consistency check, not a correctness check. | no |
| TS-JEV-SEM-002 | "The sum of all values is 1." | TS-DOC-CHOICE, TS-DOC-SCORE | Jev 1.13 | all with probabilities | 245 probability entries. **One** record sums to 0.99: `12_function_routing` / `refinement_difference` / `function` (`inspect` 0.01, `compare` 0.68, `request` 0.19, `escalate` 0.11). | AT | Probabilities are reported to 2 decimal places, so independent rounding of a true 1.00 distribution can legitimately present as 0.99. Treated as a **presentation-precision** tension, not a violated invariant. | yes |
| TS-JEV-SEM-003 | `score` is a position on the levels and equals the probability-weighted mean of the level numbers. | TS-DOC-SCORE | Jev 1.13 | 01, 04, 05, 06, 13, 13b | 29 Score answers: **24 reproduce the weighted mean within 0.006**; 5 deviate by 0.01–0.02, all on 4-level scales. | DR | The 5 deviations are within the error that 2-dp probability rounding can produce on a 4-level scale. The *formula* reproduces; exact agreement is limited by reported precision. | no |
| TS-JEV-SEM-004 | A Noul answer is a single P(yes) and carries **no separate `confidence`**. | TS-DOC-NOUL | Jev 1.13 | 01, 02, 04, 05, 12, 13, 13b | **42 of 42** Noul answers carry no `confidence` field; every Choice/Score answer does. | DR | Clean binary observation. | no |
| TS-JEV-SEM-005 | Every answer is constrained to the options supplied; the model never returns a value outside them. | TS-DOC-PRIM | Jev 1.13 | all | All 25 distinct Choice labels observed appear literally in the declared criteria; no out-of-set value in 42 records. | DR | Our criteria were fixed, small closed sets; this is not an adversarial test of containment. | no |
| TS-JEV-SEM-006 | A Choice accepts **up to 255 options**. | TS-DOC-CHOICE, TS-BLOG-INTRO | Jev 1.13 | — | Largest cardinality observed locally is **4** (both Choice and Score). | ND | Existing designs cannot speak to high cardinality; the claim was never approached. | no |
| TS-JEV-SEM-007 | Answers are independent: adding or removing questions does not change the others' results. | TS-DOC-PRIM | Jev 1.13 | 03_parallel_questions | Same 5 Nouls, batched in 1 request vs split across 5: **10 of 10** selected values identical, largest absolute difference **0.0**, in both order-balanced cycles. | DR | Two cycles, one payload, five questions, one session. | no |

### Family C — Calibration / confidence

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-CONF-001 | "Calibrated: higher confidence means higher accuracy." | TS-BLOG-INTRO | Jev 1.13 | 04_confidence | 2 cases; confidence 0.61 and 1.0, both gated `accept`. | ND | **No ground truth and no outcome rate exist anywhere in this bench.** Two synthetic cases cannot speak to a calibration curve. This repo must never be cited as validating or falsifying calibration. | no |
| TS-JEV-CONF-002 | Calibration is a **group-level** property: "Calibration is measured across groups of predictions; it does not guarantee that an individual answer is correct." | TS-DOC-SYS1, TS-DOC-PRIMER | Jev 1.13 | 04_confidence | The ambiguous case cleared a 0.60 gate at 0.61 while the underlying Choice was genuinely split. | DS | The local record *illustrates* the official scoping; it does not test it. | no |
| TS-JEV-CONF-003 | `confidence` is computed from the probability spread, collapsed to 0–1; TypeSafe ships a default but does not lock users into it. | TS-DOC-CONF | Jev 1.13 | all with confidence | The docs' worked approximation `(k·peak − 1)/(k − 1)` reproduces local values within ~0.01 at k=2–3; several k=4 Score answers deviate by up to 0.12. | LE | The docs call their published expression an **"approximation"** and never publish the production formula. This is a **limit on our ability to reproduce confidence from the log**, not a contradiction. See §7.3. | yes |
| TS-JEV-CONF-004 | Confidence "describes the model's answer, not a guarantee that the answer is correct." | TS-DOC-SCORE | Jev 1.13 | 04, 06 | `06` `low_risk` `evidence_quality`: score 1.62 at confidence **0.24** — a nearly flat 4-level spread carrying low confidence while sitting mid-scale. | DS | Consistent with the official scoping; one observation. | no |
| TS-JEV-CONF-005 | Threshold values are domain-specific and must be tuned on your own data; a threshold is not one number. | TS-DOC-CONF, TS-DOC-CONFROUTE | Jev 1.13 | 04, 12 | Local gates (0.60; 0.8 floor / 0.5 review) were fixed **before** the runs and are labelled demonstration parameters, never tuned, never claimed optimal. | DR | Officially required, locally honoured — but nothing here *validates* any threshold. | no |

### Family D — Parallel sampling / batching

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-BATCH-001 | Every question in a request is evaluated in parallel against the same state, independently. | TS-DOC-PRIM, TS-DOC-FANOUT, TS-DOC-SYS1 | Jev 1.13 | 03_parallel_questions | 5 questions carried in one request returned the same 5 values as 5 single-question requests. | DR | Same answers is evidence of independence; it is not a measurement of parallelism. | no |
| TS-JEV-BATCH-002 | "Adding questions barely changes the response time." | TS-DOC-PRIM, TS-DOC-CHOICE | Jev 1.13 | 03, 05 | The batched arm's own 2 observations were spread by **2592.9 ms**, against an arm-to-arm mean difference of **1327.2 ms** — within-arm spread exceeds the difference it would explain. | ND | Two cycles cannot separate arm identity from request position. The report refuses a speedup claim and so does this audit. | no |
| TS-JEV-BATCH-003 | Batching 13 questions is **12.2x cheaper and 10.0x faster** (cookbook) / **11.5x cheaper and 9.6x faster** (`primitives.md`). | TS-DOC-CB-PAR, TS-IDX, TS-DOC-PRIM | Vendor GDPR workload | 03_parallel_questions | Local pooled input ratio **4.2647x** (separate ÷ batched), a **76.55%** input-token saving, **10/10** answers matching. | DS | **Not comparable to the vendor figure.** Different workload (5 questions vs 13), different payload, different denominator, different session. The two numbers must never be set side by side as "official vs actual". | yes |

### Family E — Cost

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-COST-001 | Input $42/Btok = **$0.042 per Mtok**; output tokens are **free**. | TS-DOC-MODELS, TS-BLOG-INTRO, TS-SITE-HOME | `jev-1.13.0` | all | `pricing.py` encodes exactly this, keyed on the **resolved** model. All 42 records priced; `cost_basis` identical on 42/42; **0** unknown-cost records. | DR | The API returns token counts only — there is no cost field. Cost is our arithmetic over a published price table. | no |
| TS-JEV-COST-002 | "238x Lower input price than Claude Fable 5.1." | TS-SITE-HOME | Vendor comparison | — | No comparison run exists; no other vendor model was contacted. | NT | A vendor-vs-vendor comparison; nothing local speaks to it. | no |
| TS-JEV-COST-003 | "444.6x Cheaper" / "193.6x Faster". | TS-SITE-HOME, TS-BLOG-INTRO | Vendor's 4 published workflows | — | Our own ratios (4.2647x batching, 1.2833x fan-out) are for unrelated payloads. | NT | The blog post itself calls these "on the higher end of real world gains" and discloses the workflows were built by its own capabilities team. | no |
| TS-JEV-COST-004 | Pricing "can't prove it isn't subsidized"; expected to go down, not up. | TS-BLOG-INTRO, TS-SITE-HOME FAQ title | Commercial | — | Local cost figures are arithmetic over today's published rate. | NT | Any cost statement from this repo is rate-at-audit-date only. | no |

### Family F — Latency / speed

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-LAT-001 | "End-to-end response time is **70ms-500ms** for TypeSafe." | TS-BLOG-INTRO | Vendor service, measured from their laptops on the West Coast | 03, 05, 06, 12, 13, 13b | Local wall-clock: min 273.0 ms, median 576.1 ms, max 3204.1 ms. **3 of 42** records fall inside 70–500 ms; 39 exceed 500 ms. | ND | **Not a refutation and not a confirmation.** Our window is a superset: it contains DNS, TCP, TLS, connection-pool state, server queueing, upstream load and local scheduling. The vendor's band is about their service from their machines on their workload. The definitions are not the same quantity. | no |
| TS-JEV-LAT-002 | "40x-200x faster for the same levels of frontier intelligence for System One shaped queries." | TS-BLOG-INTRO | Vendor workloads | — | No LLM baseline was ever run in this repo. | ND | There is no comparison arm, no reference model, and no shared workload. | no |
| TS-JEV-LAT-003 | Sessions opened slow: the first call of each client session was the slowest in **6 of 6** sessions that record request position (2.61x–4.94x). | *Local observation, no official claim* | This machine, these sessions | 03, 05, 06, 12, 13, 13b | First-call latency 827–3204 ms vs later calls 273–654 ms. One reported counter-example inside a run. | NO | This is our confound, not a TypeSafe claim. It is listed here to keep it from being misread as a model property. | no |

### Family G — Type safety / hallucination

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-TYPE-001 | "The model never makes type errors." | TS-BLOG-INTRO, TS-SITE-HOME | Jev 1.13 | all | 42/42 responses were schema-valid; every answer matched its declared `type`; every Choice label was in the supplied criteria. | DR | **This is the weakest kind of support.** Our payloads were well-formed and benign; a single counter-example would be needed to falsify, and we did not go looking. | no |
| TS-JEV-TYPE-002 | The support for that claim is *schema matching*; the published "0%" figure is **"not empirical"** — the vendor says so itself. | TS-BLOG-INTRO (Nuance section) | Jev 1.13 | all | Consistent: our 42 records are all schema-valid. | DS | The vendor's strongest-sounding number is explicitly self-labelled as guaranteed-by-construction, not measured. Any downstream writeup must carry that qualifier. | no |
| TS-JEV-TYPE-003 | Jev "**can't hallucinate**". | TS-BLOG-INTRO | Jev 1.13 | — | No local experiment probes factual correctness of any answer. | ND | The vendor's own framing ties hallucination to *type/schema* validity ("Hallucination and type-safety are intrinsically related"). Whether the phrase also implies semantic factual correctness is **not resolved by the source**, and this repo has no design that could test it. | yes |
| TS-JEV-TYPE-004 | "Zero Hallucinations". | TS-SITE-HOME | Jev 1.13 | — | As above. | ND | Same scoping problem, in starker marketing register. | no |

### Family H — Structured state / addressing

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-STATE-001 | State may be a string, JSON object, or array; all questions see the same state. | TS-DOC-STATE | Jev 1.13 | 01, 02, 05, 06, 07, 12, 13, 13b | Locally used both prose string states and JSON object states; both accepted. | DR | Basic shape acceptance only. | no |
| TS-JEV-STATE-002 | Naming a field by dot-and-index path tells the model which part of the state to judge. | TS-DOC-PRIM | Jev 1.13 | 02_structured_addressing | Structured arm addressed `` `ticket.messages[0].text` ``; prose arm described the same field in words. Both returned `billing` at confidence 1.0; the Noul moved **0.81 → 0.89**. | DS | **Confounded by design, and the repo says so**: representation, addressability *and* payload length all move together (493 vs 452 input tokens). This cannot support "JSON > prose" or the reverse. | no |
| TS-JEV-STATE-003 | Accuracy falls as state grows with content unrelated to the decision; "Jev suffers from context rot". | TS-DOC-JAG | **`jev-1.13`** | — | `10_state_length` is registered but has **zero records**. | NT | Registered-but-not-run. An experiment design is not evidence. | yes |
| TS-JEV-STATE-004 | Context length: 64k tokens per request; 32k for `state` plus the longest question. | TS-DOC-MODELS | `jev-1.13.0` | — | Largest local state is on the order of hundreds of tokens. | NT | The limit was never approached; no boundary behaviour observed. | no |

### Family I — Instruction precision / jaggedness / known limits

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-LIMIT-001 | **Literal reading**: "answers the question you wrote, not the one you meant"; scoping words, negations and implied conditions are read at face value. | TS-DOC-JAG | **`jev-1.13`** | 07_instruction_precision | Byte-identical 82-byte state; only the instruction (and its criteria) changed: vague boundary → Noul **0.75**; explicit boundary → Noul **0.20**. | LE | The direction matches the documented edge. But our two arms changed instruction **and** criteria wording together, so this does not isolate literal reading from criteria wording — the repo states that limit explicitly. | yes |
| TS-JEV-LIMIT-002 | Jev does not count reliably; the error grows with the size of the thing counted. | TS-DOC-JAG | **`jev-1.13`** | — | `09_numeric_limits` registered, **zero records**. | NT | — | yes |
| TS-JEV-LIMIT-003 | Weak on numeric representations; "score levels are weak in numerical calibration"; do not interpolate an exact magnitude between levels. | TS-DOC-JAG | **`jev-1.13`** | 06_composite_scoring | Our composite experiment deliberately **never** asks Jev for arithmetic: 4 atomic Scores are combined by Python with frozen weights, and `composite.py` states "Confidence never enters the arithmetic". | DR | We reproduce the *prescribed workaround*, not the limitation itself. The limitation was never probed. | no |
| TS-JEV-LIMIT-004 | Dates are read as text, not as ordered quantities. | TS-DOC-JAG | **`jev-1.13`** | — | No date question was ever asked locally. | NT | — | no |
| TS-JEV-LIMIT-005 | Indirection and double negatives cost accuracy; multi-hop questions are unreliable. | TS-DOC-JAG | **`jev-1.13`** | — | `08_literal_reading` registered (negation / implied condition / scope), **zero records**. | NT | — | yes |
| TS-JEV-LIMIT-006 | Accuracy falls with irrelevant detail; filter before sending. | TS-DOC-JAG | **`jev-1.13`** | — | `10_state_length` registered, **zero records**. | NT | — | yes |
| TS-JEV-LIMIT-007 | State is not treated as hostile; adversarial content can move the answer. | TS-DOC-JAG | **`jev-1.13`** | — | No adversarial or injection payload was ever sent. | NT | — | no |
| TS-JEV-LIMIT-008 | Contradictory `instructions` and `criteria` confuse the model. | TS-DOC-JAG | **`jev-1.13`** | 07_instruction_precision | Both local arms kept instruction and criteria aligned; the contrast is *vague vs explicit*, not *contradictory vs aligned*. | NT | The contradictory-instruction edge was never exercised. | no |
| TS-JEV-LIMIT-009 | Structural invariants are **not** guaranteed: `P(noul)` need not equal `1 − P(not noul)`; a worked example sums to 1.19; Choice `yes`/`no` need not track the equivalent Noul. | TS-DOC-JAG | **`jev-1.13`** | 01, 13b (partial) | We never asked a question and its negation in one request. `13b` shows a stable Choice label over a moving distribution, which is a *different* non-invariance. | NT | The specific documented invariants were not probed. The directional lesson (do not rely on identities between separate questions) is honoured in our designs. | no |
| TS-JEV-LIMIT-010 | Jev is not trained to generate text; forcing it is slow and works poorly. | TS-DOC-JAG | **`jev-1.13`** | all | No local experiment asked for generation; every question was closed-set. | DR | Reproduction of the guidance, not a test of the failure mode. | no |

### Family J — Repeatability / determinism / consistency

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-REP-001 | "`jev-1.13` is **extremely consistent**, meaning you should expect **quantitatively similar** outputs for semantically similar inputs." | TS-DOC-JAG | **`jev-1.13`** | 13, 13b | `13`: 5 byte-identical requests → same Choice label 5/5, Score 1.0×5, Noul 0.11/0.11/0.10/0.11/0.11. `13b`: same label 6/6 across two days, Score 1.58–1.63. | DR | Direction and magnitude both fit "quantitatively similar". Two payloads, five repeats each. | yes |
| TS-JEV-REP-002 | "More consistent: returns similar answers for similar inputs." | TS-BLOG-INTRO | Jev 1.13 | 13, 13b | As above. | DR | Same caveat: two payloads. | no |
| TS-JEV-REP-003 | Cookbook: TypeSafe mean per-question probability **standard deviation 0.0102**; its `covered` answers span **0.43–0.53**, crossing a 0.5 threshold. | TS-DOC-CB-CN | `jev-latest` → `jev-1.13.0`, 15 repeats, 2026-09-11 | 13, 13b | `13` Noul range 0.01 across 5 repeats; `13b` Score range 0.05 and Noul range 0.00 across 5. | DS | **Different workload, different questions, 5 repeats not 15.** Same order of magnitude, which is all that can be said. | no |
| TS-JEV-REP-004 | Cookbook: **"TypeSafe flips on 2 of the 8 questions"** across 15 repeats; plural-label repeat rate **90.8%**; with a 0.60 top-probability gate, agreement rises to **99.2%** with automatic labels on **74.2%**. | TS-DOC-CB-CC | `jev-latest` → `jev-1.13.0`, 15 repeats, 2026-09-11 | 13b_ambiguous_repeatability | Local: Choice label stable **6/6** while `confidence` moved **0.24–0.30** and the top-2 margin moved over a range of **0.07**; one exact top-probability tie observed. | LE | **The vendor already documents that its own labels flip and that distributions move.** The local record extends this to the sub-label level (label stable, distribution not) on a case engineered to sit mid-scale. Whether that is "new" is a P2 question; P1 asserts only that the documented picture is broader than "stable label". | yes |
| TS-JEV-REP-005 | The cookbook design adds a fresh `uid` per call and states it **"cannot separate sensitivity to the irrelevant field from variation that would occur on identical requests."** | TS-DOC-CB-CN, TS-DOC-CB-CC | Their design | 13, 13b | Our repeats sent **byte-identical** payloads with no added unique field, so our design does not carry that specific confound. | LE | Our design is cleaner on this one axis; that is a design difference, not a superiority claim. Conversely, we cannot speak to input-perturbation sensitivity at all. | yes |

### Family K — Workflow / routing / agent use

| Claim ID | Official claim (paraphrase) | Source | Scope | Local experiment | Local observation | Relationship | Caveat | P2? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TS-JEV-WF-001 | Confidence-gated routing: the answer says *what*, confidence says *whether to act*; gate at different levels by risk. | TS-DOC-CONFROUTE, TS-DOC-CONF | Jev 1.13 | 04_confidence, 12_function_routing | `04` gated on `confidence >= 0.6` alone. `12` used a 0.8 route floor and a 0.5 review threshold; all 4 routes were withheld and no handler ran. | DR | The pattern is reproduced; nothing here validates the thresholds. | yes |
| TS-JEV-WF-002 | Speculative fan-out: ask every question the code might need, including ones that matter only sometimes. | TS-DOC-FANOUT, TS-DOC-PRIM | Jev 1.13 | 05_speculative_fanout | Fan-out carried **400 fewer** input tokens than staged and **129 more** output tokens, while leaving **4 of 12** speculative answers unconsumed. | LE | Two pairs. The unused-question cost is **not separable per question** — usage is reported per request, so waste is counted in questions, never in tokens. | yes |
| TS-JEV-WF-003 | Composite scoring: break a judgment into atomic Scores and combine with weights you control in code. | TS-DOC-COMPOSITE, TS-DOC-PRIM | Jev 1.13 | 06_composite_scoring | 4 atomic Scores per state, combined by Python with weights frozen before the run (0.3/0.3/0.2/0.2); Jev was asked for no arithmetic and no verdict. | DR | "Jev was asked for no arithmetic" is a design property, verified by reading the payloads. | no |
| TS-JEV-WF-004 | Intent routing: classify first, then route to deterministic code, a specialist model, or a human. | TS-DOC-INTENT | Jev 1.13 | 12_function_routing | 4/4 function matches and 4/4 argument matches; every route suppressed fail-closed to `human_review`, handler never called. | DR | Counts on four synthetic cases with one observation each — explicitly **not an accuracy rate**. | yes |
| TS-JEV-WF-005 | Code owns control flow; the model does not choose its own next action. | TS-DOC-BUILD, TS-DOC-CODINGAGENTS | Jev 1.13 | all | Every experiment kept branching, thresholds, arithmetic and side effects in Python; the model returned only typed values. | DR | A design property we implemented, not a model property we measured. | no |

### Non-official items currently present in the repo

These are recorded so they cannot later be mistaken for vendor claims.

| Item | Origin | Label |
| --- | --- | --- |
| "Semantic routing ≠ execution authorization" | Our architecture principle | `NO` |
| "Confidence is a diagnostic and a policy input, never a correctness score" | Partly official (TS-DOC-SCORE says confidence "describes the model's answer, not a guarantee that the answer is correct"), but the *strong* form — never entering arithmetic, never producing a composite confidence — is our design choice | `NO` (strong form) |
| Fail-closed suppression when a gate is not cleared | Our design choice; `routing.py` policy | `NO` |
| Frozen thresholds (0.60, 0.8, 0.5) fixed before the run | Our design choice | `NO` |
| "A stable label is not a stable distribution" | Our phrasing of an observation; the *underlying fact* is already documented by the vendor in TS-DOC-CB-CC | `NO` as a coinage; the phenomenon is official |
| The first-call-is-slowest session pattern | Our local confound | `NO` |

---

## 5. Experiment mapping

All 15 registered experiments. `REGISTERED_BUT_NOT_RUN` means zero canonical records; an
experiment design is **not** evidence.

### Run (10 experiments, 42 records)

| Experiment | Records | Official claim(s) it speaks to | What the local record observed | What it does NOT establish | P2 candidate? |
| --- | --- | --- | --- | --- | --- |
| `01_primitives` | 1 | ID-001, ID-002, SEM-001, SEM-003, SEM-004, SEM-005 | One request, 3 primitives: Choice `other` conf 0.26 (peak 0.45, `billing` 0.44); Score 1.59 conf 0.39; Noul 0.12 with no confidence field. | Anything general. One payload, one response. Its Choice is a near-tie (0.45 vs 0.44) — a strong argument *against* reading its label as a verdict. | no |
| `02_structured_addressing` | 2 | STATE-001, STATE-002 | Same facts, two representations. `department` = `billing` at confidence 1.0 in both arms; Noul moved 0.81 → 0.89. Input tokens 493 (structured) vs 452 (prose). | "JSON > prose" or the reverse. Representation, addressability and payload length move together. | no |
| `03_parallel_questions` | 12 | BATCH-001, BATCH-002, BATCH-003 | 2 batched calls (816 in / 194 out) vs 10 separate calls (3480 in / 226 out) carrying the same 5 Nouls. **10/10** selected values identical, largest absolute difference **0.0**. Pooled input ratio 4.2647x (76.55%). Latency within-arm spread 2592.9 ms > arm difference 1327.2 ms. | Any universal batching ratio; any speedup; per-question cost of the batched form. | yes |
| `04_confidence` | 2 | CONF-001, CONF-002, CONF-005, WF-001 | Clear case: `release_transfer` conf 1.0, Score 2.0 conf 1.0. Ambiguous case: `other` conf **0.61** vs a **0.60** floor → accepted and cleared. | Calibration. Any accuracy rate. Correctness of either answer. | yes |
| `05_speculative_fanout` | 6 | WF-002, BATCH-002 | Fan-out 2 requests (1412 in / 402 out) vs staged 4 requests (1812 in / 273 out); ratio 1.2833x. 8 of 12 speculative answers consumed, 4 unused. 6 consumed fields moved slightly between arms. Latency direction inconsistent across the two pairs. | Which strategy is cheaper *in general*; the token cost of a single wasted question. | yes |
| `06_composite_scoring` | 3 | WF-003, LIMIT-003, CONF-004 | 4 atomic Scores per state on a 4-level scale, composed by Python. Composite 0.1417 / 0.619 / 0.887 in the frozen expected order. Per-dimension confidence spanned 0.24–1.0. | That the dimensions are empirically independent; any accuracy (there is no ground truth); any composite confidence (none exists). | no |
| `07_instruction_precision` | 2 | LIMIT-001, LIMIT-008 | Byte-identical 82-byte state, one Noul. Vague boundary **0.75** → explicit boundary **0.20**. A 0.55 move on a 0–1 probability from the same bytes. | That instruction wording alone caused it (criteria wording moved too); that 0.20 is "correct" — neither arm is a ground truth. | yes |
| `12_function_routing` | 4 | WF-001, WF-004, ID-003 | 4/4 function matches, 4/4 argument matches. All four routes **withheld**; no handler ever called. Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a frozen 0.8 floor; the fourth was withheld by `needs_human_review` 0.94 ≥ 0.5. 3 of 4 argument questions per call were asked, paid for, and unused. | An accuracy rate. That the allowed-handler path works — it was never entered. | yes |
| `13_repeatability` | 5 | REP-001, REP-002, REP-003 | 5 byte-identical requests. Choice label 5/5 same, 0 leader switches. Score 1.0×5, confidence 0.98×5. Noul 0.11/0.11/0.10/0.11/0.11 (range 0.01). Token counts byte-identical across all 5. | A variance, tolerance or bound for any other payload. | yes |
| `13b_ambiguous_repeatability` | 5 | REP-001, REP-004, REP-005, SEM-001 | `01_primitives`' payload ×5. Choice label `other` **6/6** (with the historical record), 0 leader switches — while confidence moved **0.24–0.30**, top-2 margin moved over **0.07**, Score moved **1.58–1.63** (range 0.05), one exact top-probability tie observed. Noul stable at 0.13. | A noise bound. That the label is *robust* rather than *lucky*. | yes |

### Registered but not run (5 experiments)

| Experiment | Tier | Declared cases | Official claim(s) it would speak to | Status |
| --- | --- | --- | --- | --- |
| `00_model_info` | core | 2 | TS-DOC-MODELS alias/version resolution | `REGISTERED_BUT_NOT_RUN` |
| `08_literal_reading` | extended | 4 | LIMIT-001, LIMIT-005 (negation, implied condition, scope) | `REGISTERED_BUT_NOT_RUN` |
| `09_numeric_limits` | extended | 3 | LIMIT-002 (counting), LIMIT-003 (numeric) | `REGISTERED_BUT_NOT_RUN` |
| `10_state_length` | extended | 3 | STATE-003, LIMIT-006 (context rot) | `REGISTERED_BUT_NOT_RUN` |
| `11_language_pair` | extended | 2 | TS-DOC-MODELS language support ("English is the primary training language… CJK handled but not equally well") | `REGISTERED_BUT_NOT_RUN` |

---

## 6. Strongest official ↔ local correspondences

Ranked by how clean the match is, not by how flattering the number is.

1. **`choice` == argmax, 45/45.** TS-DOC-CHOICE defines `choice` as the highest-probability
   option. Every Choice answer in the log satisfies it, with no counter-example. A clean
   `DIRECT_LOCAL_REPRODUCTION` of a stated output invariant.

2. **`score` == probability-weighted mean, 24/29 within 0.006.** TS-DOC-SCORE gives the exact
   formula and a worked example (`0×0.0 + 1×0.57 + 2×0.43 = 1.43`). The local values reproduce it;
   the five deviations (0.01–0.02) are all 4-level scales and sit inside the error that 2-dp
   probability rounding can produce. The *formula* is confirmed; exact agreement is bounded by
   reported precision.

3. **Noul carries no `confidence`, 42/42.** TS-DOC-NOUL states this explicitly and explains why
   (a two-outcome distribution is fully described by one number). Zero exceptions locally.

4. **Option containment, 42/42.** TS-DOC-PRIM: "The model returns a probability distribution over
   your options or levels, never a value outside them." All 25 distinct Choice labels observed
   appear literally in the declared criteria.

5. **Answer independence under batching, 10/10.** TS-DOC-PRIM: "One question's answer is not hidden
   context for another. You can add or remove questions without changing the others' results."
   `03_parallel_questions` tested exactly this — the same five questions batched in one request vs
   split across five — and every selected value matched, in both order-balanced cycles.

6. **The prescribed workarounds are the ones we implemented.** TS-DOC-JAG says to keep arithmetic in
   code, count in code, and not to interpolate magnitudes between Score levels. `06_composite_scoring`
   does exactly that: four atomic Scores, weights and arithmetic in Python, and the model asked for
   no arithmetic and no verdict.

7. **Repeatability, direction and rough magnitude.** TS-DOC-JAG calls `jev-1.13` "extremely
   consistent" and promises "quantitatively similar" outputs. `13` and `13b` show stable selected
   labels across 5–6 byte-identical calls with small movements underneath. The vendor's own
   cookbook (SD 0.0102 over 15 repeats) is the same order of magnitude as our 5-repeat spreads —
   on a different workload, which is why this is support and not reproduction.

---

## 7. Apparent tensions

Described conservatively. **None of these is a contradiction**, and none should be written up as
one.

### 7.1 One record's probabilities sum to 0.99, not 1.00

TS-DOC-CHOICE and TS-DOC-SCORE both state the sum is 1. In
`12_function_routing` / `refinement_difference` / `function` the reported distribution is
`inspect 0.01, compare 0.68, request 0.19, escalate 0.11` — sum **0.99**. This is the only such
record in 245 probability entries.

**Assessment:** probabilities are reported to **2 decimal places**. Independent rounding of four
values from a true distribution summing to 1.00 can present as 0.99 or 1.01 without any invariant
being violated. This is a **presentation-precision** tension, not a semantic one. Recorded because
a reader scanning the log will notice it, and because the correct response is to read the
documented invariant at the precision the API reports — not to "fix" the row, which would violate
append-only provenance.

### 7.2 Local wall-clock sits mostly above the published 70–500 ms band

The launch post states "End-to-end response time is **70ms-500ms** for TypeSafe." Locally, only
**3 of 42** records fall inside that band; median is 576.1 ms and the maximum is 3204.1 ms.

**This is not a refutation and must never be presented as one.** Reasons, all of which apply:

- The local window is a **superset** of the claimed quantity. It contains DNS, TCP and TLS setup,
  connection-pool state, server-side queueing, upstream load and local scheduling. The report's own
  §12 lists these and refuses to decompose them.
- The vendor states where their numbers come from: "our published evals are generally run from our
  laptops on the West Coast (this is where our service is currently based)". Different client, different
  path, different workload.
- The local sessions are **one machine, one account, one region**, across a handful of sessions.
- The vendor's own stated band is itself a claim about *their* service on *their* workload.

The strongest defensible statement is: *our records are not commensurable with that claim, in either
direction.* Classified `NOT_TESTABLE_WITH_CURRENT_DESIGN`.

### 7.3 Local `confidence` cannot be recomputed from the logged `probabilities`

This is a limit on **our own record**, discovered during the audit and recorded here so no downstream
stage builds on a false assumption.

`confidence.md` explains confidence qualitatively and gives an **approximation** — "This demo uses
`(3 × largest probability − 1) / 2` to approximate confidence for three options" — without ever
publishing the production formula. Testing that expression against the log:

- It reproduces local values within ~0.01 on the k=2 and k=3 cases, which are exactly the
  cardinalities the docs give worked examples for.
- It does **not** reproduce several k=4 Score answers; deviations run up to 0.12.
- Decisively: **two local answers report byte-identical distributions but different confidence.**
  `score {0: 0.08, 1: 0.0, 2: 0.92}` appears with confidence **0.76**
  (`05_speculative_fanout` / `pairB_staged_2`) and **0.75**
  (`05_speculative_fanout` / `pairB_fanout`). Likewise `score {0: 0.0, 1: 0.41, 2: 0.59}` with
  **0.39** (`01_primitives`) and **0.38** (`13b_ambiguous_repeatability` / `ambiguous_4`).

So `confidence` is **not a function of the probabilities as the log records them**. The API's
`probabilities` are quantized to 2 dp; `confidence` evidently carries more precision than that.
`recorder.serialize_answers` calls `answer.model_dump(mode="json")` and applies no rounding, so the
2-dp quantisation is the API's representation, not an artifact this repository introduces.

**What this licenses:** nothing about TypeSafe. The vendor never published the formula, and calling
their published expression an "approximation" is consistent with what we see.

**What this forbids:** reconstructing, second-guessing, or "correcting" any logged `confidence`
from the logged `probabilities`; treating the k=3 approximation as the definition; and computing any
downstream quantity that assumes the two are interchangeable.

### 7.4 Two official surfaces disagree on the batching multiplier

`primitives.md` says batching 13 questions is "11.5x cheaper and 9.6x faster". The
`parallel_questions` cookbook — and the `llms.txt` summary of it — say **"12.2x cheaper and 10.0x
faster"**, backed by a printed table (`$0.000497 / 0.27s` vs `$0.006090 / 2.71s`) whose arithmetic
yields 12.25x and 10.04x.

**Assessment:** a docs-internal drift between a derived summary and the page that produces it. The
cookbook's own table is self-consistent; the `primitives.md` figure is the outlier relative to it.
Recorded, not resolved — and specifically **not** adjudicated using any third-party source. Any
citation of "the" official batching multiplier must name which page it came from.

### 7.5 Two official pages use different thresholds for the same worked example

`confidence.md` uses a 0.5 floor and `> 0.9` to execute a transfer. `confidence-routing.md` uses a
"0.6 floor" and `> 0.85` for the same voice-banking scenario.

**Assessment:** a demonstration-parameter difference, not a contradiction — both pages state that
thresholds are domain-specific and must be tuned. Recorded because a reader could otherwise mistake
either constant for a product default. Note that "0.6" occurs three independent times in this
material (the routing page's floor, the choices cookbook's gate, and our own `04_confidence`
threshold); **none of the three is a calibrated default**, and our coincidence with it is not
corroboration.

### 7.6 Vendor "no type errors" / "can't hallucinate" vs the vendor's own Nuance section

The launch post claims Jev "can't hallucinate" in its main claim body and, in its own Nuance
section, restates the support as *schema matching being guaranteed* and labels the figure **"not
empirical"**.

**Assessment:** a register difference **inside a single source**, which the source itself
discloses. It is not a local finding and this repository contributes no evidence either way. It is
recorded because the strong phrase travels further than its qualifier, and because any future
writeup must carry the qualifier with the phrase.

---

## 8. Things this repository does NOT establish

Stated without hedging, because each is a place a reader could over-read.

- **No general accuracy.** There is no ground truth anywhere in this bench. Expected labels are the
  design's intention, written alongside the states. Nothing here is an accuracy rate, and
  "2 of 2" or "4 of 4" are counts on synthetic cases, never rates.
- **No calibration validation, in either direction.** We have no reliability diagram, no ECE, no
  Brier score, no independent ground-truth dataset. `04_confidence` contains **two** cases. This
  repository neither validates nor falsifies any calibration claim — and the vendor's own scoping
  ("measured across groups of predictions; it does not guarantee that an individual answer is
  correct") is the frame our two cases illustrate, not test.
- **No model latency benchmark.** Local wall-clock is a superset window recorded because it was
  free to record. No speedup is claimed, no arm is called faster, and
  `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK` stands.
- **No universal batching ratio.** `4.2647x` is a property of one payload with five questions
  sharing one state, over two order-balanced cycles in one session. It is not the vendor's 12.2x,
  not comparable to it, and not a property of Jev.
- **No deterministic-model guarantee — and no non-determinism guarantee.** The repo states the
  opposite of determinism as an *observation* ("byte-identical requests returned differently-shaped
  distributions"). What we have is a small number of repeats on two payloads, not a determinism
  verdict. The official FAQ question "Is Jev deterministic?" was **not retrievable**, and no
  official source we could read makes a determinism claim in either direction.
- **No broad hallucination benchmark.** Nothing here probes factual correctness. The only
  "hallucination" axis we can speak to is schema conformance, on benign payloads, with no
  adversarial attempt.
- **No composite-dimension independence.** The four dimensions are separate, atomic and
  design-orthogonal. Their correlation was never measured.
- **No real external side effect and no tested allowed-handler path.** Every handler is inert;
  `ACTUAL_HANDLER_EXECUTION_UNTESTED` stands.
- **No production-safety certification.** Nothing here certifies this pattern against real systems,
  real customer data, or real money.
- **No vendor-claim adjudication.** Where a vendor number and a local number differ, this audit
  says the two are not commensurable. It never reports a vendor figure as "actually" a local one,
  and never reports a local figure as evidence about the vendor's workload.

---

## 9. P2 Candidate Register

Candidates worth deeper triage. **No novelty is claimed here.** P2 alone decides between
`officially known`, `independently reproduced`, `locally novel observation`, and `unsupported`.

| Candidate | Statement | Source / evidence basis | Question P2 must answer |
| --- | --- | --- | --- |
| **A** | A stable selected label does not imply a stable underlying probability distribution. | `13b_ambiguous_repeatability` — label `other` **6/6** (across two days), confidence **0.24–0.30**, top-2 margin range **0.07**, Score **1.58–1.63**, one exact top-probability tie. | The vendor's choices cookbook **already documents label flipping (2 of 8) and distribution movement**, so the phenomenon is official. Is the *sub-label* level — label fixed while the distribution underneath it moves, on a payload engineered to sit mid-scale — a genuinely finer observation, or a restatement? |
| **B** | Decision-boundary wording moved one byte-identical state's Noul from 0.75 to 0.20. | `07_instruction_precision` — 82-byte state, byte-identical in both arms; vague → explicit boundary. | Is this a direct reproduction of the documented literal-reading/jaggedness edge (TS-DOC-JAG), or a more specific local extension? Note the design changes **instruction and criteria wording together**, so it cannot isolate which drove the move — a limitation the repo already records. |
| **C** | A confidence gate accepted an intentionally ambiguous case at 0.61 against a 0.60 floor. | `04_confidence` — `ambiguous_evidence`; confidence 0.61, gate `accept`. | Is this merely correct threshold semantics (the documented "three paths" pattern behaving as specified), or does it support an independent observation about developer misuse risk? **Do not prejudge.** Note the vendor's own cookbook uses a 0.60 gate too, which weakens any novelty claim. |
| **D** | Batched shared-state questions cut local input tokens materially while every selected value matched. | `03_parallel_questions` — 816 vs 3480 input tokens, ratio 4.2647x (76.55%); **10/10** values identical, largest difference 0.0. | Is this pure reproduction of the officially documented mechanism ("ask every question that uses the same state in one request"), or is there an implementation-level insight worth summarising? The vendor's 12.2x is a different workload and must not be compared. |
| **E** | Fan-out versus staged control flow trades input tokens against output tokens. | `05_speculative_fanout` — fan-out **400 fewer** input / **129 more** output tokens; **4 of 12** speculative answers unconsumed; per-question waste is **not separable** because usage is reported per request. | Is the *unconsumed-but-paid-for* framing a useful addition to the documented pattern, or just the documented pattern costing what it says it costs? |
| **F** | `confidence` cannot be recomputed from the recorded `probabilities`. | Whole-log check: identical reported distributions carry different confidence (`{0:0.08, 1:0.0, 2:0.92}` → 0.76 and 0.75; `{0:0.0, 1:0.41, 2:0.59}` → 0.39 and 0.38). Probabilities are quantized to 2 dp by the API, not by our recorder. | **A candidate about our own measurement fidelity, not about TypeSafe.** Does the canonical record preserve enough precision to reproduce the confidence the API returned? If not, what does that cost any future claim that reasons about confidence *and* probabilities together? |
| **G** | All four routes in a frozen-policy router were withheld; the allowed-handler path was never entered. | `12_function_routing` — 4/4 correct function and argument, yet 4/4 suppressed to `human_review`; route confidences 0.76/0.58/0.72/1.0 against a 0.8 floor. | The repo already logs `ROUTING_SUPPRESSION_EXPECTATION_MISSED`. Is the interaction between a *correct* route and a suppression policy a generalisable design insight, or an artifact of one frozen 0.8 floor? |

**Explicitly not listed as candidates:** anything about calibration, model latency, general
accuracy, universal batching ratios, or determinism. Section 8 explains why each is out of reach of
the current design.

---

## 10. Files changed

| File | Status | Nature |
| --- | --- | --- |
| `docs/sources/TYPESAFE_OFFICIAL_SOURCES.md` | added | Source provenance registry (new `docs/` tree) |
| `docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md` | added | This audit |

**No code changed. No test changed. No experiment payload changed. No threshold, criterion or
expected label changed.** `results/usage.jsonl` was read only.

---

## 11. Validation

| Check | Result |
| --- | --- |
| `uv run pytest` | **888 passed** (before promotion, from the repair branch HEAD) |
| Canonical record count | 42 |
| Canonical SHA-256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` (matches the frozen baseline) |
| Log mutated by P1? | **No** — read-only; verified by re-hashing after all audit work |
| Inference calls made? | **No.** All TypeSafe access was public HTTPS `GET` of documentation, product and blog pages. No `POST /v1/systemone`, no SDK client, no `run`/`run-all` invocation. |
| `.secrets/` accessed? | **No.** Never opened, read, hashed or quoted. |
| Derived artifacts regenerable? | Yes — `capability_snapshot.md` and `JEV_LOCAL_EVALUATION_FINAL.md` rebuild byte-for-byte from `usage.jsonl`; both generators contain no clock, RNG or hash dependence, and the "generated from … to …" line uses record timestamps, not build time. |
| Audit-side verification performed | Mechanical checks run directly against the log: `choice` == argmax (45/45); `score` == weighted mean (24/29 within 0.006); Noul-without-confidence (42/42); label containment (25/25 labels in declared criteria); `question_count` == `len(answers)` (42/42); probability-sum check (1 record at 0.99); probability decimal-place survey; identical-distribution/different-confidence search. |

---

## 12. Git state

| Item | Value |
| --- | --- |
| Branch | `audit/p1-official-local-evidence` |
| HEAD | `77357d96be081f2b521d753e3f0b1ce7708b5566` (branched from the promoted `main`) |
| `main` | `77357d96be081f2b521d753e3f0b1ce7708b5566` — promoted, pushed |
| Working tree | two new untracked files under `docs/`, nothing modified |
| `main` merged into this branch? | No |

Committed to `audit/p1-official-local-evidence` with the message
`Audit TypeSafe claims against frozen Jev evidence`. `main` is **not** merged and not modified by
this stage.

---

## 13. Handoff

```
NEXT_AUTHORIZED_STAGE:
P2 — Evidence Classification & Jev-Specific Insight Triage

P2_NOT_STARTED
```

P1 is complete and stops here. The seven candidates in §9 are handed over as **candidates only**;
P2 owns the classification of each into `officially known` / `independently reproduced` /
`locally novel observation` / `unsupported`.
