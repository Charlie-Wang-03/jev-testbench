# P2 — Evidence Classification & Jev-Specific Insight Triage

**Stage:** P2 — adversarial triage of the seven P1 candidates. **Analysis only. No experiment, no
inference call, no change to the measurement layer.**
**Canonical local evidence:** `results/usage.jsonl` — 42 records, SHA-256
`38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` (read-only throughout).
**Official sources:** [TYPESAFE_OFFICIAL_SOURCES.md](../sources/TYPESAFE_OFFICIAL_SOURCES.md) — all
28 Tier-1 bodies re-fetched and hash-matched during P2 (see its `R-1` entry).
**Input:** [P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md](P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md) §9.
**Triage date:** 2026-09-22.

---

## 1. Primary verdict

```
P2_TRIAGE_PASS
```

All seven P1 candidates were triaged individually, none was merged with another, and every one has a
stated strongest counter-explanation that was steelmanned rather than dismissed. The triage did **not**
preserve a candidate for narrative reasons, and it retired the two candidates with the largest local
effect sizes (`A`, `D`) on the strength of prior art rather than on the strength of our own data.

**The triage is deliberately permitted to conclude that nothing here is novel about Jev, and that is
part of what it found.** One question survives as worth a bounded P3; one more is recorded as blocked
on methodology.

---

## 2. Scientific state

```
NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
```

This is the *first* of the two "no finding" states, not the second. The distinction is exact:

- There is **one** open question (`B′`, §9) that meets the `N3` bar and is worth a small, bounded,
  pre-registered P3. That is why this is `NO_STRONG_..._YET`.
- It is **not** `CURRENT_EVIDENCE_DOES_NOT_SUPPORT_JEV_SPECIFIC_NOVELTY`, because that state forbids
  any further API spend, and `B′` is a genuine, cheap, falsifiable question.

What the evidence does support, stated plainly:

> Across 42 records and 15 claimed official behaviours, this bench has **no finding about Jev that is
> both novel relative to TypeSafe's public material and supported by our own data**. Every large local
> effect either restates an officially documented behaviour or is an artifact of our own Python-side
> policy. The two candidates with the biggest numbers (`A`, `D`) are the two with the most prior art —
> official *and* independent public.

---

## 3. P1 promotion and clerical correction

### 3.1 Clerical correction (documentation provenance only)

P1 §12 (`Git state`) recorded the branch point as the branch's own HEAD and described two files as
uncommitted after they had been committed. The single conflated row was split so that the two hashes
are attributed correctly:

| Attribution | Commit |
| --- | --- |
| Branch point / `main` at P1 start | `77357d96be081f2b521d753e3f0b1ce7708b5566` |
| P1 audit commit / branch HEAD | `ec04cb6f7ff3a03f25ca5feea89ad4c64322caa4` |

Committed as `3125281` *before* promotion, so that `main` receives the corrected provenance record
rather than carrying a stale hash permanently.

**Nothing else in P1 was edited.** No claim, relationship label, caveat, apparent tension or verdict
was touched. This is a provenance repair, and P1 is **not** reopened: `P1_OFFICIAL_LOCAL_AUDIT_PASS`
stands as issued. The two numeric sharpening points that P2's re-reading turned up are recorded in §4.9
as *P2 findings about P1's characterisation*, not as edits to P1.

### 3.2 Promotion

| Item | Value |
| --- | --- |
| Pre-promotion `origin/main` | `77357d96be081f2b521d753e3f0b1ce7708b5566` — unchanged from the P1 baseline ✅ |
| Ancestry check | `git merge-base --is-ancestor origin/main origin/audit/p1-official-local-evidence` → **PASS** |
| Merge method | `git merge --ff-only` → `Updating 77357d9..3125281`, **no merge commit** |
| Push | `77357d9..3125281  main -> main` |
| `origin/main` after promotion | `312528198a4c206b747fdb4c12791d66d56520b0` == **P1 final HEAD** ✅ |
| Baseline movement | **None.** No `P2_PROMOTION_BASELINE_MOVED`; no force push anywhere. |
| P2 branch | `audit/p2-insight-triage`, created from the new `main` |

---

## 4. Seven-candidate triage

### 4.1 The matrix

`A′` and `B′` are **P2-surfaced refinements**, not P1 candidates: triage split each of `A` and `B` into
the part P1 actually stated and a narrower question that the stated part does not reach. They are
listed separately so that no candidate is merged and no refinement is smuggled in as a candidate.

| Candidate | N class | B value | R decision | Strongest supporting evidence | Strongest counter-explanation | What would falsify it? |
| --- | --- | --- | --- | --- | --- | --- |
| **A** — stable label ≠ stable distribution | `N0_OFFICIALLY_DOCUMENTED` | `B_MEDIUM` | `R_KILL` | `13b`: label `other` **5/5** (6/6 with `01_primitives`) on byte-identical 512-token requests, while the top-2 margin moved **0.00–0.07**, `confidence` **0.24–0.30** and Score **1.58–1.63**; one exact top-probability tie. | Ordinary sampling variation **already public twice over**. TypeSafe's own choices cookbook reports label flips on 2 of 8 questions, a mean probability std dev of `0.0098` (max single-label `0.0515`), and states "Small changes can still switch the top label when two labels are close". Independently, a public chaos test sent Jev **the identical request five times and got 0.03, 0.03, 0.03, 0.04, 0.04**, and a public judge benchmark reports variance `0.0000149` on identical frozen cases over 100 repetitions. Our observation is a narrower restatement. | As an observation it is unfalsifiable and was not falsified — it was **devalued by prior art**. The claim that the *sub-label* level is new is falsified directly by the cookbook's own flip count plus its non-zero std dev, and the claim that the byte-identical design is new is falsified by the public five-identical-call receipt. |
| **A′** — is variability a function of boundary proximity? *(P2-surfaced)* | `N2_LOCAL_EXTENSION` | `B_LOW` | `R_HOLD` | A clean local contrast: the clear-cut payload `13` returned **byte-identical** distributions 5/5 (`{0.01, 0.98, 0.01}`, one-hot Choice at 1.0), while the mid-scale payload `13b` moved on every repeat. Consistent with the cookbook's "when two labels are close". | **Ceiling effect, not a discovery.** A distribution pinned at 1.0/0.0 has no room to move, so `13`'s "stability" is saturation rather than robustness — the contrast is confounded by construction. Separately, "a sampled classifier varies more near a decision boundary" is generic, not Jev-specific. | A design that holds *available headroom* constant while moving distance-to-boundary, and shows movement still scales with proximity. **No such design exists yet** — the boundary cannot be located a priori without a pilot, so this fails `N3`'s falsifiability criterion and is held rather than proposed. |
| **B** — instruction boundary 0.75 → 0.20 | `N1_INDEPENDENT_REPRODUCTION` | `B_MEDIUM` | `R_KILL` | `07`: an 82-byte byte-identical state, Noul **0.75 → 0.20** (input 318 vs 358 tokens). A 0.55 move on a 0–1 probability. | **A direct instance of a documented edge, already prescribed.** The jaggedness page says to "state the exact condition in the `instructions`. Be specific. Put boundary cases in the criteria", and lists literal reading as failure mode #1 with that remedy. Our arms changed instruction **and** criteria together, so the design cannot attribute the move; each arm is **n = 1**; and neither 0.75 nor 0.20 is a ground truth. | A design isolating one field (`B′`), or repeats showing the 0.55 move is not reproducible. As stated, more calls would only re-observe the documented edge. |
| **B′** — which field carries the boundary? *(P2-surfaced)* | `N3_PLAUSIBLE_JEV_SPECIFIC_OPEN_QUESTION` | `B_MEDIUM` | **`R_GO`** | The official remedy is given as a **bundle**, and is never decomposed: the docs say to be specific in the instruction *and* to put boundary cases in the criteria, and to "treat the criteria as an extension of the instruction". Our largest locally-observed effect (0.55) was produced with both fields changed at once, and the repo itself records that confound. No controlled attribution receipt was found in public material — third-party guides repeat the bundle and advise fixing the criteria, but without a controlled test. | The two fields are *supposed* to move together by official guidance, so decoupling them may simply invoke the **other** documented edge (failure mode #7, "contradictory instructions and criteria") instead of revealing a locus — a design hazard, mitigated only if both arms state the same boundary and differ solely in **where** it is stated, not in whether they agree. Any result is a single-payload effect size with no ground truth. | Pre-registered: if the two single-field arms differ by < 0.10, or within-arm spread exceeds the between-arm difference, the boundary is not attributable to a field at this sample size. See §9. |
| **C** — ambiguous case cleared a 0.60 gate | `NX_NOT_A_JEV_FINDING` | `B_HIGH` | `R_KILL` | `04`: `ambiguous_evidence` returned intent `other` at confidence **0.61** against our **0.60** floor → `accept`. | **Pure threshold arithmetic on our own constant.** `experiments.py` defines `CONFIDENCE_GATE_THRESHOLD = 0.60` and labels it in-code as a "demo threshold; not calibrated, not tuned on any data, not claimed optimal". The published k=3 expression `(3 × 0.74 − 1) / 2` reproduces the 0.61 **exactly**. And the answer was not even close: 0.74 vs 0.26, a margin of 0.48 — the "ambiguity" was a property of our *state* design, not of the returned distribution. | Nothing about Jev is falsifiable here. A claim of a Jev-side finding is falsified by pointing at the constant in this repository's own source. |
| **D** — batching cuts input tokens | `N1_INDEPENDENT_REPRODUCTION` | `B_HIGH` | `R_KILL` | `03`: **816 vs 3480** pooled input tokens → **4.2647x** (76.55% saved), **10/10** selected values identical, largest absolute difference **0.0**, 2 batched vs 10 separate calls across two order-balanced cycles. | **Expected shared-state amortisation, and publicly measured in more detail than ours.** The docs recommend same-state batching; a public Postgres extension reports ~**435 tokens for one row alone vs ~175 per row in batches of 20**, plus an accuracy-versus-batch-size curve (batches of 1–20 at 100%, 40 at 92–98%, 80 at 77–94%) — a study that goes *further* than this bench, which never varied batch size or question/state ratio. Our ratio is a property of one 5-question payload and is explicitly not comparable to the vendor's 12.2x. | Nothing about Jev. A claim that 4.2647x is a Jev property is falsified by changing the state-to-question token ratio, which our own `03` design varies by construction. |
| **E** — fan-out vs staged trades input against output | `NX_NOT_A_JEV_FINDING` | `B_MEDIUM` | `R_KILL` | `05`: fan-out 2 requests at 1412 in / 402 out; staged 4 requests at 1812 in / 273 out (**1.2833x**); fan-out carries 6 questions per request against 1+3 staged; **4 of 12** speculative answers unconsumed. | **Generic speculative-execution tradeoff.** Any batched/speculative design trades unconsumed outputs for fewer round trips. The docs already state the benefit — irrelevant results are "simply ignored" and speculative questions "save a round trip when they are not [irrelevant]" — and the docs make no cost claim at all about unused answers. Decisively: on Jev the "wasted" resource is **output tokens, which the published rate card prices at zero**, so the *unconsumed-but-paid-for* framing has **no cost content on this product** — the input tokens, the only billed quantity, went **down** by 400. | The cost framing is falsified by the documented price table (input billed, output free). Nothing else here is a Jev claim. |
| **F** — `confidence` is not recomputable from the logged `probabilities` | `NX_NOT_A_JEV_FINDING` | `B_MEDIUM` | `R_KILL` | Across 74 Choice/Score answers: **4 collision groups** where an identical logged probability *vector* carries a different `confidence`. The largest two are one-hot: the 3-option vector `(1.0, 0.0, 0.0)` occurs **13×** — **11 at `confidence` 1.0, 2 at 0.99** — and the 4-option vector `(1.0, 0.0, 0.0, 0.0)` occurs **9×** — **7 at 1.0, 2 at 0.99**. The other two are near-duplicate pairs on non-degenerate vectors: `(0.59, 0.41, 0.0)` at 0.38 and 0.39, and `(0.92, 0.08, 0.0)` at 0.75 and 0.76. (Keyed on the sorted probability vector, not on option names — the claim being tested is identifiability from the returned distribution, for which option labels are irrelevant.) The published k=3 expression `(3 × peak − 1)/2` deviates by up to **0.130** (k=4: up to **0.153**), which is far outside 2-dp rounding — so the published expression is decisively **not** the production formula. | **Quantized API representation limits identifiability — an artifact of the record, not a behaviour of the model.** `confidence.md` states confidence is "a statistic computed from the probability distribution" and never publishes the production formula, calling its own published expression an approximation. Nothing observed contradicts any official statement. The whole finding is about how much our record can resolve. | Not a Jev claim, so nothing about Jev is at stake. The methodological rule it yields (§4.7) would be falsified by finding two answers with identical logged probabilities **and** identical confidence whose *unrounded* distributions provably differed — which requires a channel this record does not have. |
| **G** — every correct route was suppressed | `NX_NOT_A_JEV_FINDING` | `B_HIGH` | `R_KILL` | `12`: **4/4** function matches and **4/4** argument matches, yet **4/4** routes withheld to `human_review` and the handler never entered. Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a frozen **0.8** floor; the 1.0 case withheld by `needs_human_review` 0.94 ≥ **0.5**. | **Our own Python-side policy, and the source says so.** `routing.py` documents `ROUTING_CONFIDENCE_FLOOR = 0.8` as "Nothing in the docs says 0.8 is the right line" and `ROUTING_HUMAN_REVIEW_THRESHOLD = 0.5` as the same status. Three routes fail only because 0.8 sits above their confidence; the fourth fails only because 0.5 sits below its review Noul. **Moving either constant would change the outcome without any model call.** Nothing about the model is measured. | A claim that Jev "routes badly" is falsified by moving our own thresholds and watching the outcome change — and the repo already logs `ROUTING_SUPPRESSION_EXPECTATION_MISSED` rather than hiding it. |

### 4.2 Why `A` was killed despite being our cleanest local result

`A` is the observation this bench explains best and the one with the least left to say. P1 §9 asked
whether the *sub-label* level is "a genuinely finer observation, or a restatement". Triage's answer is
**restatement**, on two independent grounds that each suffice:

1. **Officially entailed.** The cookbook reports label flips on 2 of 8 questions *and* a non-zero
   per-label probability std dev (`0.0098` mean, `0.0515` max). A question that held its label steady
   while the label-level spread is non-zero *is* "stable label, moving distribution". The vendor does
   not use our sentence; the sentence is not the thing.
2. **Independently reproduced in public, with more data.** The byte-identical design that P1 tentatively
   advanced as our one clean axis — "our repeats sent byte-identical payloads with no added unique
   field" (P1 `TS-JEV-REP-005`) — is exactly what a public chaos test already did, reporting five
   identical calls returning `0.03, 0.03, 0.03, 0.04, 0.04` and jitter floors over ~1,490 captured
   calls. The vendor's own disclosed confound ("cannot separate sensitivity to the irrelevant field from
   variation that would occur on identical requests") has therefore already been answered publicly. Our
   two payloads add nothing to it.

**On the specific sub-questions P1 §9 asked:** the mid-scale engineered payload does **not** bring new
information (it is a targeted instance of an entailed behaviour); the exact tie is a **single
curiosity** — one exact top-tie in 45 Choice answers, and it is a coincidence of one draw, since `13b`'s
distribution moved every repeat and so the tie is not a stable property of any payload; and the top-2
margin variation has no independent meaning beyond the already-documented "close probabilities permit
routing changes".

**Explicitly not over-read:** `n = 5/6` on two payloads is not a variance estimate, and nothing in this
triage treats it as one.

### 4.3 `B` — the one place the bench had something left

The single most important triage outcome is that the candidate with the **largest effect size**
(0.75 → 0.20, a 0.55 move) is `N1` as stated and becomes `N3` only in a narrower form that P1 did not
state. The reasoning:

- As stated, `B` is the official remedy for a named edge, executed once. That is `N1`.
- The **decomposition** the docs never make — whether the boundary is read from `instructions` or from
  `criteria` — is not answered officially (the remedy is a bundle), not answered by our data (our arms
  moved both fields together, and the repo records that), and not answered by public material found in
  the `§16` check (third-party guides repeat the bundle and advise "fix the criteria" without a
  controlled attribution test).
- It clears all four `N3` criteria **except** that its design carries a documented hazard (§4.1 `B′`
  counter-explanation), which is why it is proposed with a pre-registered `KILL` condition rather than
  as a promising finding.

### 4.4 `E` — a framing that inverts on this product's price table

`E` deserves a note because its framing is attractive and, on Jev, backwards. "4 of 12 speculative
answers unconsumed" reads like waste until it is priced: Jev bills **input** tokens and prices **output**
tokens at zero. The unconsumed answers are output tokens. Meanwhile the input side — the only billed
side — was **400 tokens lower** for fan-out. So the local measurement says fan-out was *cheaper on the
billed quantity and cheaper in round trips*, while producing more of the free one. The
unconsumed-but-paid-for framing is not a Jev insight and is not even a correct cost statement here.

### 4.5 `F` — the sharpest result in the triage is about our record, not the model

`F` produced the most precise facts P2 established, and none of them is a finding about TypeSafe:

- The published k=3 expression does not reproduce the returned `confidence` on **all** k=3 answers —
  maximum deviation **0.130** — which is **beyond what 2-dp rounding of the probabilities can explain**.
  A worked check: reproducing the observed 0.75–0.76 on `{0: 0.08, 1: 0.0, 2: 0.92}` would require an
  unrounded peak of **0.833–0.840**, against a logged peak of 0.92 whose true value is within ±0.005 of
  it — a gap an order of magnitude larger than rounding can bridge.
- Consequently the deviation is **not** a rounding artifact, and the published expression is decisively
  not the production formula — which the docs themselves imply by calling it an approximation.
- The collision groups show `confidence` retains information the logged probabilities have lost. The
  one-hot cases are the clearest: an identical `(1.0, 0.0, 0.0)` presenting **11 times at 1.0 and twice
  at 0.99** is only consistent with `confidence` having been computed on a pre-rounding distribution
  that differed between those calls — at full certainty the rounded vector has nowhere to hide it.

### 4.6 `G` — the lesson is real and is not ours

"Semantic routing ≠ execution authorization" is good engineering writing, and P1 registered it as our
architecture principle. Triage confirms it should **stay** registered that way. Every one of the four
suppressions is attributable to a constant in this repository, not to the model: three to a floor the
source explicitly disclaims, one to a review threshold with the same status. The model matched the
intended function and argument **4/4**; our policy declined to act **4/4**. The honest line is that the
router refused to execute *on our instructions*, not that Jev produced unusable confidence.

### 4.7 Methodological constraint established by `F`

Carried forward as a hard rule for any future experiment in this repository:

```
DO_NOT_RECONSTRUCT_CONFIDENCE_FROM_QUANTIZED_PROBABILITIES
```

- The API's `probabilities` are a **2-dp representation**; `confidence` carries information they do not.
- Therefore: do not fit, infer, "correct", or second-guess any `confidence` from logged `probabilities`;
  do not treat the published k=3 expression as the definition; and do not compute a downstream quantity
  that assumes the two are interchangeable.
- Where a design needs a threshold on the distribution's shape, read the returned `confidence` **or**
  declare a code-side statistic over the returned probabilities — and say which, because they are not
  the same number.

This is a `P2`-level constraint on *future* designs. It changes nothing about the 42 existing records,
which stand as the API returned them.

### 4.8 Public-novelty check (`§16` secondary standard)

Scope: run only for the survivors, `A` (then `N2`) and `B′` (`N3`). No broad external search was run for
candidates already classified `N0`/`N1`/`NX`.

**Result — `A`: `PUBLIC_PRIOR_ART_FOUND`, decisively.** A public chaos-test writeup reports sending Jev
the **identical request five times** and receiving `0.03, 0.03, 0.03, 0.04, 0.04`, with measured jitter
floors (identity 0.042, question-reorder 0.059, paraphrase cohort 0.073) over roughly 1,490 captured
calls; a public judge benchmark reports variance `0.0000149` on identical frozen cases across 100
repetitions; a further writeup describes "near-identical probabilities on repeated questions". This is
the same phenomenon, independently reported, with greater statistical power than ours. **`A` is not
merely unresolved — it is already public.**

**Result — `B′`: `PUBLIC_NOVELTY_UNRESOLVED`.** Public guides restate the official bundle and one
advises that middling agreement with high confidence means the *criteria* need fixing — but no
controlled, receipted attribution between instruction and criteria was found. Per the `§16` rule, this
is recorded as **unresolved**, not as "nobody has discovered this".

**Admissibility.** These third-party sources are used **only** to answer "has someone already publicly
reported this?", per `§16`. They are **not** used to adjudicate any official claim and are **not**
evidence about Jev — the same restriction P1's source registry applies to all third-party material.
Vendor and local figures are unaffected by anything found here.

### 4.9 Two numeric sharpenings of P1's characterisation (P2 findings)

Re-reading the log produced two cases where P1's prose is looser than the data. **Neither changes a P1
conclusion, and P1's text was not edited** — they are recorded here so a later stage does not inherit
the loose bound:

| P1 wording | P2 measurement | Effect on the P1 conclusion |
| --- | --- | --- |
| `TS-JEV-SEM-003` / §6: the five Score deviations run "0.01–0.02" | All five deviate by **exactly 0.0100** (n = 29, 24 within 0.006) | None. "within rounding error" is unchanged and in fact tighter. |
| §7.3: the k=3 approximation "reproduces local values within ~0.01" | k=3 (n = 43) mean deviation **0.0103** but **maximum 0.1300** (worst: `05/pairB_fanout/followup_urgency`, predicted 0.88, actual 0.75, peak 0.92); k=4 (n = 27) mean 0.0222, **maximum 0.1533**; k=2 (n = 4) max 0.0100 | **Strengthens** P1's conclusion. "Not reproducible from the logged probabilities" is better supported by a 0.130 max than by a 0.01 one — and means are misleading here, which is why both are reported. |

One further precision, on the audit's own consistency check: 45 Choice answers contain **exactly one
exact top-probability tie** (`13b` / `ambiguous_5`: `other` 0.45 = `billing` 0.45, `choice` = `other`).
The `choice == argmax` check holds 45/45, but at that one record it holds only because `other` precedes
`billing` in the logged dictionary order — so the check is **under-powered at ties**, not wrong.
`TS-JEV-SEM-001`'s "no counter-example" remains true; it should carry this caveat in any downstream
writeup.

---

## 5. Survivors

Only `R_GO` candidates are listed. **There is exactly one.**

| Candidate | Why it survives | Ceiling on what it can mean |
| --- | --- | --- |
| **`B′`** — which input field carries a decision boundary, `instructions` or `criteria`? | The official remedy for the literal-reading edge is given as a bundle and never decomposed; our largest local effect (0.55) was produced with both fields changed together; no controlled public attribution was found. Cheap, order-controlled, and pre-registerable with a real falsifier. | **Low and stated up front.** One payload, one Noul, **n = 3 per arm**, no ground truth for any arm. A positive result identifies a locus for *this* boundary on *this* payload, not a general rule, and must never be written as "Jev reads X and not Y". A null result is equally publishable as "the boundary is set by the pair at this sample size". |

`A′` is recorded under `R_HOLD`, **not** under survivors, because it fails `N3`'s falsifiability
criterion as currently designable.

---

## 6. Killed candidates

Seven rows are `R_KILL` (`A`, `B`, `C`, `D`, `E`, `F`, `G`). The reasons, not the labels:

- **`A` — killed by prior art, not by weakness.** Our cleanest local result. Its phenomenon is
  officially entailed (flips *and* non-zero per-label std devs in the vendor's own cookbook) and the one
  axis we thought was ours — byte-identical requests — has already been done publicly with more calls
  and better statistics. Further API calls would re-observe a documented, publicly reproduced fact.
- **`B` (as stated) — killed as an instance, not as an effect.** The 0.55 move is real and large, but it
  is the official remedy for officially-named failure mode #1 applied once, with instruction and
  criteria changed together and n = 1 per arm. The effect does not die here; its *attribution* moves to
  `B′`.
- **`C` — killed as arithmetic.** `0.61 ≥ 0.60` is a comparison in our own source, against a constant
  that source labels uncalibrated and not claimed optimal, on a case whose returned distribution was not
  close (0.74 vs 0.26). The published k=3 expression reproduces the 0.61 exactly. There is no Jev
  question underneath it. Its `B_HIGH` blog value survives independently — see §7.
- **`D` — killed as expected amortisation, and as the weakest version of public work.** Shared-state
  batching saving input tokens is the documented mechanism; a public Postgres extension measures it per
  row *and* against an accuracy-versus-batch-size curve, which this bench never varied. Re-running more
  batching payloads would buy a fourth decimal on a known amortisation, which is exactly the low-value
  spend P2 is meant to prevent.
- **`E` — killed as generic, and as mis-framed on this product.** Speculative-execution tradeoffs are
  not Jev-specific; the docs already state the round-trip benefit; and the "wasted" tokens are the
  *free* ones, so the framing is not even a correct cost claim here.
- **`F` — killed as a measurement-fidelity issue.** It is about our record's resolution, not the model's
  behaviour. Its value is the constraint in §4.7 and the two sharpenings in §4.9, both of which are
  methodological, not scientific.
- **`G` — killed as our policy.** Every suppression traces to a constant in `routing.py` that the source
  itself disclaims; moving either constant changes the outcome with no model call. The model matched
  what we asked **4/4**.

**No candidate was killed for being unflattering, and no candidate was preserved for being interesting.**
`A` and `D` — the two with the best story and the biggest numbers — were the two killed hardest, and
both because prior art, not our data, decided it.

---

## 7. Blog Evidence Register

P2 writes no blog. This register states what a developer writeup could stand on **without** depending on
P3 finding novelty. The writeup's premise is that a careful measurement bench, built and audited in the
open, reports what it can and cannot support — which does not require a novel finding about Jev.

### `BLOG_CORE`

| Item | Basis | Required attribution |
| --- | --- | --- |
| What Jev actually is: three typed primitives, no free-text field in any answer, Noul carries no `confidence` | All 42 records; answer-level keys are exactly `type` + `choice`/`score`/`noul` (+ `confidence`, `probabilities`, `legend`) with no free-text field anywhere; **45/45** Noul answers carry no `confidence` | Vendor's documented design, **reproduced** locally |
| Same-state batching: local reproduction, and its correct scale | `03` — 816 vs 3480 pooled input tokens, **4.2647x**, 76.55%, **10/10** values identical, max difference 0.0 | **Local measurement of one payload.** Must **not** be compared to the vendor's 12.2x (different workload, denominator, session) |
| `confidence` ≠ a guarantee about an individual answer | `04` — a case accepted at 0.61 vs a 0.60 floor; underlying Choice split | The group-level scoping is **official** (`system-one`, `machine-learning-primer`, `score`). Our two cases *illustrate* it; they cannot test calibration |
| Fail-closed routing, and semantic routing ≠ execution authorization | `12` — 4/4 correct function and argument, 4/4 suppressed, handler never entered | **Our architecture**, registered `NO` in P1. The thresholds are demonstration parameters |
| Evidence and provenance methodology | Whole-repo: append-only log, one call → one record on success *or* raise, `model_requested` vs `model_resolved`, `retry_count` is dead and `transport_attempt_count` is the live field, latency is not a model benchmark, derived reports regenerable byte-for-byte from the log, canonical SHA-256, and the P1→P2 audit trail | **This repository's own practice** — no vendor claim involved |
| `DO_NOT_RECONSTRUCT_CONFIDENCE_FROM_QUANTIZED_PROBABILITIES` | §4.5–4.7 — 4 collision groups, k=3 deviations to 0.130, one-hot at both 0.99 and 1.0 | **A limit of the returned representation**, explicitly not a claim that TypeSafe computes anything wrongly |
| Independent public work converges with this bench | Public reports of Jev varying on identical requests; public per-row batching amortisation figures | **Third-party, cited as third-party.** Used to show convergent evidence, **never** as our measurement of Jev |

### `BLOG_SUPPORTING`

- The clean official↔local correspondences: `choice` == argmax 45/45 (**with** the single-tie caveat
  from §4.9), `score` == probability-weighted mean within 0.0100 (29 answers, 24 exact), Noul-without-
  `confidence` 45/45, score legend/`probabilities` key agreement 29/29, answer independence under
  batching 10/10.
- The `07` boundary move (0.75 → 0.20) as an **illustration of a documented edge**, with the
  both-fields-changed confound stated in the same breath.
- The apparent tensions P1 recorded — the single 0.99 probability sum, the 70–500 ms band our window is
  not commensurable with, the docs-internal multiplier and threshold drift — presented as *recorded, not
  adjudicated*.
- The fan-out/staged split including the price-table inversion (§4.4), which is a good worked example of
  pricing a "waste" claim.
- The P2 method itself: three-dimensional triage, steelmanned counter-explanations, and a triage that
  retires its own best story.

### `BLOG_EXCLUDE`

| Excluded | Why |
| --- | --- |
| Any calibration validation **or** falsification | No ground truth exists anywhere in this bench. `04` has two cases |
| Any latency or speedup claim | `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK` stands; `03`'s within-arm spread exceeded its arm difference |
| `4.2647x` as a property of Jev, or set beside the vendor's 12.2x | Different workload, denominator and session |
| "Stable label ≠ stable distribution" as a novel observation | Vendor-documented **and** publicly reproduced (§4.2) |
| The 0.99 record as a defect | Presentation precision; the invariant is stated at the precision the API reports |
| Any determinism verdict, in either direction | Small n; the official FAQ answer was never retrievable; public work already covers it |
| `A′`'s boundary-proximity contrast | Confounded by the ceiling effect — do not publish until designed |
| `ROUTING_SUPPRESSION_EXPECTATION_MISSED` as a model result | It is our threshold choice (§4.6) |
| Any vendor number presented as something this repo verified | Vendor claims describe the vendor's workload |

---

## 8. Vendor Feedback Candidates

**P2 sends nothing.** This section pre-classifies for a later stage only. Scale: `V0_NONE` /
`V1_DOCUMENTATION_FEEDBACK` / `V2_REPRODUCIBLE_BEHAVIOUR_REPORT` / `V3_POTENTIAL_PRODUCT_ISSUE`.

| Item | Class | Reasoning |
| --- | --- | --- |
| Batching multiplier differs between two official surfaces — `primitives.md` says "11.5x cheaper and 9.6x faster"; the `parallel_questions` cookbook and its `llms.txt` summary say "12.2x cheaper and 10.0x faster", and the cookbook's own table (`$0.006090` vs `$0.000497`; `2.71s` vs `0.27s`) yields 12.25x / 10.04x | **`V1_DOCUMENTATION_FEEDBACK`** | A drift between a derived summary and the page that computes it. The cookbook is self-consistent; `primitives.md` is the outlier. **A docs-consistency matter — not a model behaviour and not a product issue.** |
| Confidence thresholds differ between two official pages for the same worked example — `confidence.md` uses `< 0.5` and `> 0.9`; `confidence-routing.md` uses a "0.6 floor" and `> 0.85` | **`V1_DOCUMENTATION_FEEDBACK`** | Both pages state thresholds are domain-specific and must be tuned, so this is a demonstration-parameter difference, not a contradiction. Worth flagging only because a reader can mistake a constant for a product default. |
| FAQ **answers** on the home page and the launch post are client-rendered and were not present in the retrieved payload; only question titles were recoverable, including "Is Jev deterministic?" | **`V1_DOCUMENTATION_FEEDBACK`** | An accessibility/retrievability matter for documentation consumers and agents. Reported as a retrieval limitation, **not** as the vendor withholding anything. |
| The returned `probabilities` are a 2-dp representation while `confidence` evidently carries more precision; `confidence.md` says confidence is derived from the probabilities and offers the full `probabilities` precisely so users can substitute their own measure | **`V1_DOCUMENTATION_FEEDBACK`** | A note that the *returned* distribution is a rounded view — and that a user-supplied statistic computed from it is therefore approximate in a way `confidence` is not — would help. **No invariant is violated and no official statement is contradicted**: the docs call their own published expression an approximation and never publish the production formula. Deliberately **not** `V2`/`V3`. |
| `A`–`G` findings generally, including the 0.75 → 0.20 move and the suppressed router | **`V0_NONE`** | These are documented behaviour (`A`, `B`), our own policy (`C`, `G`), expected amortisation (`D`), a generic tradeoff (`E`) or a limit of our record (`F`). **Nothing here justifies contacting the vendor.** |

**There are no `V2` or `V3` candidates.** Nothing in 42 records and this audit warrants a reproducible
behaviour report or a potential product issue, and this document should not be read as implying one is
pending.

---

## 9. P3 proposed falsifiable questions

One `R_GO` candidate, so one pre-registered question. **P2 designs it and stops. It does not run it.**

```
P3-Q1 — Does a decision boundary live in `instructions` or in `criteria`?

Hypothesis:
  The §6 gap in the official material — the remedy for the literal-reading edge is given
  only as a bundle — is real and decomposable. Specifically: with the boundary stated in
  exactly one of the two fields, the Noul moves toward the 07 "explicit" value (0.20) when
  the boundary is stated in `criteria` and stays near the 07 "vague" value (0.75) when it is
  stated only in `instructions`, i.e. the criteria text is the load-bearing field.

Null / alternative explanation:
  (a) The H0 reversal: the instruction text is load-bearing and the criteria text is not.
  (b) Neither field alone moves the answer: the boundary is set only by the pair, which
      would mean the official bundle advice is not just sufficient but necessary.
  (c) Neither single-field arm moves materially: the 0.55 move observed in 07 was a
      one-off draw from an unstable payload, and there is no locus to attribute.
  (b) and (c) are both informative and both count as pre-registered KILL outcomes for the
  *hypothesis* — not as failures of the experiment.

Independent variable:
  Which field carries the boundary definition. Four arms, same underlying boundary:
    1. neither   (vague instruction, boundary omitted from criteria)   <- anchor, 07 vague
    2. instruction only  (explicit boundary in `instructions`; criteria unchanged from arm 1)
    3. criteria only     (boundary enumerated in criteria; instruction unchanged from arm 1)
    4. both      (07 explicit boundary arm)                            <- anchor, 07 explicit
  DESIGN HAZARD, pre-registered: arms 2 and 3 must state the SAME boundary and differ only
  in WHERE it is stated. If either arm instead makes the instruction and criteria
  inconsistent, it invokes a different documented edge (jaggedness failure mode #7,
  "contradictory instructions and criteria") and the result is void. Any arm whose two
  fields disagree about the boundary is a protocol violation, not a datum.

Controlled variables:
  The 82-byte state, byte-identical in every arm (arm 1 and arm 4 states already exist in
  the canonical log). One Noul question, unchanged wording except as the independent
  variable requires. Same resolved model, verified per response and recorded as
  `model_resolved` alongside `model_requested`. One client session; serial execution, never
  concurrent (the `TransportProbe` before/after delta assumes serial runs). Equal repeat
  count per arm. Thresholds, criteria sets, expected labels and payloads frozen and written
  down BEFORE the first call. All state synthetic.

Primary observable:
  The returned `noul` value per call, and its within-arm spread across repeats.
  Reported per arm as a range, never as a mean alone, and never with a confidence interval —
  3 repeats does not support one.

Pre-registered GO condition:
  One single-field arm reproduces >= 50% of the 0.55 both-fields move in the 07 direction
  (i.e. |noul - 0.75| >= 0.275), the other single-field arm moves <= 20% of it
  (|noul - 0.75| <= 0.11), each with within-arm spread <= 0.05. This identifies a locus.

Pre-registered KILL condition:
  The two single-field arms differ from each other by < 0.10; OR within-arm spread exceeds
  the between-arm difference in any arm; OR any arm is found to have made its instruction
  and criteria mutually inconsistent (hazard above). KILL means: do not extend, do not add
  payloads to rescue it, and report "the boundary is not attributable to a single field at
  this sample size".

Maximum API calls:
  12. 4 arms x 3 repeats. This is a hard ceiling, declared up front, and no retry loop,
  poll, or repeat increase may be added. If a call fails, it is recorded as a failed call
  and is NOT re-run beyond the declared count.

Cost ceiling:
  12 calls, each in the ~320-360 input-token range seen in 07, is on the order of 4,000
  input tokens; at the published rate that is well under one ten-thousandth of a dollar.
  Output tokens are free. TypeSafe Console billing remains authoritative.

Decision rule if GO fires:
  One working note that a locus exists for this boundary on this payload. NOT "Jev reads
  criteria and ignores instructions". Any generalisation would require new arms on
  independently authored payloads, which would be a separate pre-registration.
```

**Relationship to `R_HOLD` `A′`: `B′` does not depend on it, and `A′` is not proposed here.** If a
later stage wants `A′`, the unsolved prerequisite is stated in §4.1: a design that holds available
headroom constant while varying distance-to-boundary.

---

## 10. What changed in our understanding of Jev

Deliberately short, and limited to what the evidence supports.

1. **Nothing in P2 changed what we believe Jev *is*.** No `N3` finding emerged, and every P1
   relationship label survives the re-read — which was performed against pages re-fetched and
   hash-matched to the P1 registry, not against memory.
2. **Our understanding of the *distribution of novelty* inverted.** The bench's two largest local
   effects (`A`'s movement, `D`'s 4.2647x) are the two with the most prior art — one entailed by an
   official cookbook and independently reproduced in public, the other measured publicly in more
   detail than we managed. The bench's *least* documented behaviour is its smallest-scale one: a
   0.55 move on a single Noul pair, where the open part is attribution rather than existence.
3. **We now know our record is less identifiable than P1 implied, in two specific places.** `choice` is
   not determined by the logged probabilities at an exact tie (1 of 45 Choice answers); and
   `confidence` is not a function of the logged probabilities (4 collision groups). Both are limits on
   the record, not on the model, and both now have a written rule (§4.7) rather than a silent
   assumption.
4. **Independent public work converges with our numbers** on non-determinism across identical requests
   and on batching amortisation. That raises confidence in the *bench* — it is measuring what others
   measure — and adds no information about Jev that was not already public.
5. **The strongest defensible claim this bench can make about Jev remains a reproduction claim.**
   Where it says something official is true here, that is a local reproduction of a published
   behaviour; where it says something is large, that is a property of a synthetic payload.

---

## 11. Files changed

| File | Status | Nature |
| --- | --- | --- |
| `docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md` | modified — **§12 only** | Provenance repair: one conflated row split into branch point (`77357d9`) and P1 audit commit (`ec04cb6`); the "untracked files" row corrected to reflect the committed state. Verified by diff to touch no claim, label, caveat, tension or verdict. Committed **on the P1 branch as `3125281`, before promotion**, so `main` carries the corrected record rather than a permanently stale hash. |
| `docs/sources/TYPESAFE_OFFICIAL_SOURCES.md` | modified | Added `R-1` re-verification log: all 28 Tier-1 bodies re-fetched and hash-matched during P2, with the limits of that statement stated. No existing source entry altered. |
| `docs/audits/P2_JEV_INSIGHT_TRIAGE.md` | added | This triage |

**What the P2 commit itself contains:** the `TYPESAFE_OFFICIAL_SOURCES.md` modification and this
document — nothing more (`git diff --stat 3125281` reports one file changed, 21 insertions, plus one
untracked addition). The P1 doc edit is in `3125281`, i.e. already in `main` before the P2 branch was
cut, so it does not appear in the P2 diff.

**Nothing else changed.** In particular, **no** change to `results/usage.jsonl`,
`src/jev_lab/experiments.py`, `routing.py`, `composite.py`, `repeatability.py`, `recorder.py`,
`pricing.py`, any test, any threshold, any criterion, any expected label, or any payload. No new
experiment was registered. No scratch script was added to the repository.

---

## 12. Validation

| Check | Result |
| --- | --- |
| `uv run pytest` | **888 passed, 0 failed** — 888 collected, exit code 0, no `F`/`E` markers (offline suite; run on the P2 branch) |
| Canonical record count | **42** — unchanged |
| Canonical SHA-256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` — **unchanged** |
| `results/usage.jsonl` mutated by P2? | **No** — read-only; re-hashed after all analysis |
| Inference API calls made by P2? | **No.** All TypeSafe access was public HTTPS `GET` of documentation pages. No `POST /v1/systemone`, no SDK client, no `run`/`run-all`. |
| `.secrets/` accessed? | **No.** Never opened, read, hashed or quoted. No credential state was queried and no key value was ever read. |
| New experiments? | **None.** No case list registered, no threshold, criterion or payload touched. |
| P3 started? | **No.** One question designed (§9), zero calls made. |
| `TYPESAFE_LOG_LEVEL=debug`? | **Not enabled** — the SDK does not redact request/response bodies, so it never was and was not turned on. |
| Anti-goals honoured | No retry loop, poll or unbounded repeat was added; no vendor claim is presented as a local measurement; no local run is generalised into a universal rule; no "blog value" was equated with novelty; no general LLM/agent principle was written as Jev-specific; no counter-evidence was weakened to keep a candidate alive. |
| Third-party source discipline | Public sources appear **only** in §4.8's novelty check and §7's convergence item, cited as third-party, and are **not** used to adjudicate any official claim. |

---

## 13. Git state

| Item | Value |
| --- | --- |
| Branch | `audit/p2-insight-triage` |
| Branch point | `312528198a4c206b747fdb4c12791d66d56520b0` (the promoted `main`) |
| `origin/main` | `312528198a4c206b747fdb4c12791d66d56520b0` — P1 promoted, pushed, **not** further modified by P2 |
| `main` merged into this branch? | **No** |
| Commit | `Triage Jev-specific findings for replication` |
| Push | `audit/p2-insight-triage` pushed; `main` untouched by P2 |
| P1 branch | `audit/p1-official-local-evidence` at `3125281`, promoted and left in place |

---

## 14. Handoff

One `R_GO` candidate qualifies, so a minimal P3 is authorized — and it is authorized as a **small,
pre-registered, 12-call attribution test**, not as a novelty hunt.

```
NEXT_AUTHORIZED_STAGE:
P3 — Minimal Jev-Specific Replication

P3_NOT_STARTED
```

Standing conditions for whoever runs P3:

- **One question only: `P3-Q1` (§9).** Do not add arms, payloads or repeats beyond the declared
  4 × 3 ceiling to rescue a failing result.
- **The pre-registered `KILL` conditions are binding.** A `KILL` outcome is a result to report, not a
  design to fix.
- **`DO_NOT_RECONSTRUCT_CONFIDENCE_FROM_QUANTIZED_PROBABILITIES` (§4.7) applies to every new design.**
- **`A′` is not authorized.** It stays `R_HOLD` until a design exists that holds available headroom
  constant while varying distance-to-boundary.
- **No `V2`/`V3` vendor contact is warranted** from anything in this triage (§8), and P2 sent nothing.

If a later stage judges even `P3-Q1` not worth 12 calls, the honest alternative is to skip P3 and go
straight to repository professionalization — the blog register in §7 does not depend on P3 producing
novelty. That call belongs to the next stage, not to this one, and P2 stops here.
