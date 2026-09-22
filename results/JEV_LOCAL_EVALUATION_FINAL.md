# Jev Local Evaluation
## Core Capability, Stability, Cost, and Agent-Control Findings

> **This file is a derived artifact, not a measurement.** The canonical local record is `results/usage.jsonl`. Every number below is recomputed from it by `uv run python -m jev_lab final-report`, so this file cannot disagree with the log and must never be quoted in place of it.

> **Scope.** Everything measured here comes from a handful of synthetic cases, on one machine, against one account, in a handful of sessions. It is not a benchmark, not a calibration, and not comparable to any published figure. Where a sentence is a vendor's statement rather than an observation, it says so.

**Claim labels.** Every assertion below carries exactly one:

| label | meaning |
| --- | --- |
| **OFFICIAL** | a statement from TypeSafe's documentation or their published prices, about their workload. Not verified here. |
| **DESIGN ASSUMPTION** | a choice this bench made before running, chosen rather than measured. |
| **LOCAL MEASUREMENT** | a value an API response returned, or a fact about a call recorded in this log. |
| **DERIVED CALCULATION** | arithmetic done in Python over measurements. Labelled so it is never mistaken for something the API reported. |
| **LIMITATION** | what the records do not support. |

Generated from 42 canonical record(s), 2026-09-20T15:29:51Z to 2026-09-21T14:20:51Z.

## 1. Executive summary

- **LOCAL MEASUREMENT** — resolved model: `jev-1.13.0` on 42 of 42 record(s), requested as `jev-latest`. An alias can move; only the response says which model answered, which is why both are recorded.
- **LOCAL MEASUREMENT** — 42 real API call(s) recorded across 10 run session(s); status ok=42.
- **LOCAL MEASUREMENT** — tokens, as the responses reported them: **21,767 input**, **3,594 output**, **25,361 total**.
- **DERIVED CALCULATION** — estimated cost **$0.000914214**, from the local price table keyed by the resolved model. Console billing is authoritative.
- **LOCAL MEASUREMENT** — experiments actually run: 10 — `01_primitives` (1), `02_structured_addressing` (2), `03_parallel_questions` (12), `04_confidence` (2), `05_speculative_fanout` (6), `06_composite_scoring` (3), `07_instruction_precision` (2), `12_function_routing` (4), `13_repeatability` (5), `13b_ambiguous_repeatability` (5).

**CORE_CAPABILITY_EXPLORATION_CLOSED**

- **LOCAL MEASUREMENT** — 10 of 10 registered experiment(s) have at least one canonical record, and every number this report states was recomputed from those records.
- **DESIGN ASSUMPTION** — **nothing was adjusted after seeing an answer.** The thresholds, the weights, the expected labels, and the case lists were fixed before the runs; a report that moved one of them would be a fit rather than a measurement.

**ACTUAL_HANDLER_EXECUTION_UNTESTED**

- **LOCAL MEASUREMENT** — in the function-routing run, every resolved route was withheld by the frozen policy, so the branch that calls an allowed handler was never entered under a live answer.
- **LIMITATION** — that branch is carried forward as an explicit boundary, **not** as a blocker: it is Python-side plumbing rather than an open question about the model, and the offline suite exercises it. No threshold was moved and no state was chosen to make it execute, because either would have replaced a measurement with a fit.

## 2. Primitive behaviour — `01_primitives`

- **LOCAL MEASUREMENT** — `department` (Choice) returned label `other` with the full distribution `other` 0.45, `billing` 0.44, `account` 0.11, `feature_request` 0, and a separate `confidence` of 0.26.
- **LOCAL MEASUREMENT** — `severity` (Score) returned `1.59` on a legend of 3 described position(s) (0=Cosmetic; the product still …, 1=A feature is broken or degra…, 2=The customer cannot proceed …) with `confidence` 0.39.
- **LOCAL MEASUREMENT** — `repeat_contact` (Noul) returned the single scalar 0.12 — no distribution and no confidence field, because the type carries neither.
- **LOCAL MEASUREMENT** — `confidence` (0.26) and the winning probability (0.45) are different numbers reported side by side: confidence is not the top-1 probability, and one does not reconstruct the other.
- **LIMITATION** — this is one payload and one response. Nothing here is a law about Choice, Score, or Noul; the repeats in `13b_ambiguous_repeatability` are what make any statement about run-to-run movement possible at all, and they are still one payload.

## 3. Structured addressing — `02_structured_addressing`

- **LOCAL MEASUREMENT** — input tokens differed: **493** with the structured state (addressed by backticked field path) against **452** with prose (described in words).
- **DERIVED CALCULATION** — the structured request carried 41 more input token(s) (0.0907x of the prose arm's input) for the same four facts.
- **LOCAL MEASUREMENT** — `asks_for_refund` came back 0.81 against 0.89 — the two arms did not agree on this one.
- **LOCAL MEASUREMENT** — `department` came back `billing` in both arms, confidence 1 against 1.
- **LIMITATION** — the two arms differ in state form **and** in length, and there is one observation per arm in one session. The token difference is between two written states, not a causal effect of JSON over prose; no arm is the reference and no arm is called better.

## 4. Confidence — `04_confidence`

- **LOCAL MEASUREMENT** — ambiguous evidence: `other` at confidence 0.61, distribution `other` 0.74, `release_transfer` 0.26, `read_balance` 0.
- **LOCAL MEASUREMENT** — ambiguous evidence: the specificity Score was 0.06 with confidence 0.91.
- **LOCAL MEASUREMENT** — clear evidence: `release_transfer` at confidence 1, distribution `release_transfer` 1, `read_balance` 0, `other` 0.
- **LOCAL MEASUREMENT** — clear evidence: the specificity Score was 2 with confidence 1.
- **DESIGN ASSUMPTION** — the experiment gated in code on `confidence >= 0.6` alone, a demonstration parameter that was fixed before the run, is not calibrated, and is not claimed to be optimal.
- **LOCAL MEASUREMENT** — the gate accepted and cleared on every one of these cases (ambiguous, clear), which is the gate behaving as written on these answers.
- **LIMITATION** — **confidence is not correctness**, and a threshold on it is not a correctness filter: an arbitrary cut accepts an ambiguous case whenever its confidence happens to land above the line. The two are reported side by side and never combined, and no accuracy rate is computed anywhere in this report.

## 5. Instruction sensitivity — `07_instruction_precision`

- **LOCAL MEASUREMENT** — the state was byte-identical across both arms (82 UTF-8 byte(s) each); what differed was the wording of the question carrying the decision boundary, and the input tokens with it (318 against 358).
- **LOCAL MEASUREMENT** — the Noul moved from **0.75** under the vague boundary to **0.2** under the explicit one.
- **DERIVED CALCULATION** — a difference of 0.55 on a 0–1 probability, from the same state bytes.
- **LOCAL MEASUREMENT** — decision-boundary wording materially changed the observed judgment in this case.
- **LIMITATION** — this says the wording mattered here, not which wording is right: neither arm is a ground truth, one pair is not a dose-response curve, and nothing here says a particular phrasing generalises to another task.

## 6. Batching — `03_parallel_questions`

- **LOCAL MEASUREMENT** — 2 batched request(s) carried **816 input / 194 output** tokens; the 10 separate request(s) carrying the same questions carried **3480 input / 226 output**.
- **DERIVED CALCULATION** — pooled input ratio **4.2647x** (separate over batched); a saving of **76.55%** of the input tokens the separate arm spent.
- **DERIVED CALCULATION** — estimated cost $0.000034272 against $0.00014616, a ratio of 4.2647x. The cost ratio equals the input ratio here because the encoded price for this model charges input only.
- **LOCAL MEASUREMENT** — of 10 question(s) asked in both arms across the two cycles, **10** returned the same selected value; this compares labels, not distributions.
- **LOCAL MEASUREMENT** — transport attempts recorded on 12 of 12 call(s): 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 — no HTTP retry was locally observed for them, which is all that count licenses.
- **LOCAL MEASUREMENT** — the batched arm's own 2 observation(s) were spread by **2592.925 ms**, against an arm-to-arm mean difference of **1327.166 ms** — the within-arm spread is larger than the difference it would be used to explain.
- **LIMITATION** — latency here is reported as an observation and never as a speedup: two cycles cannot separate arm identity from request position, so no factor is attributed to batching.

- **DERIVED CALCULATION** — **core local finding.** Pooled over both cycles: 2 batched request(s) carried **2664 fewer** input tokens than the 10 separate request(s) carrying the same questions.
- **DESIGN ASSUMPTION** — the two arms were built with identical state and identical question definitions, which is what makes the input-token difference track the request split rather than some other difference between them.
- **OFFICIAL** — TypeSafe documents batching as a way to avoid re-sending shared state. That is a claim about their workload; the sentence above is about these two cycles of this payload.
- **LIMITATION** — two cycles, five questions, one state, one session. This is not a universal batching ratio, and it does not extend to payloads whose questions are not all over the same state.

## 7. Repeatability — `13_repeatability` and `13b_ambiguous_repeatability`

### `13_repeatability` — 5 byte-identical request(s)

- **LOCAL MEASUREMENT** — Choice: the same label came back 5 time(s), with 0 leader switch(es) and a top-2 margin range of 0 (min 1, max 1).
- **LOCAL MEASUREMENT** — Score: values 1, 1, 1, 1, 1 (range 0), confidence 0.98–0.98.
- **LOCAL MEASUREMENT** — Noul: values 0.11, 0.11, 0.1, 0.11, 0.11 (range 0.01).
- **LOCAL MEASUREMENT** — markers raised: `SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED`.

### `13b_ambiguous_repeatability` — 5 byte-identical request(s)

- **LOCAL MEASUREMENT** — Choice: the same label came back 5 time(s), with 0 leader switch(es) and a top-2 margin range of 0.07 (min 0, max 0.07).
- **LOCAL MEASUREMENT** — Score: values 1.58, 1.63, 1.61, 1.59, 1.61 (range 0.05), confidence 0.36–0.44.
- **LOCAL MEASUREMENT** — Noul: values 0.13, 0.13, 0.13, 0.13, 0.13 (range 0).
- **LOCAL MEASUREMENT** — markers raised: `EXACT_TOP_PROBABILITY_TIE_OBSERVED`.

- **LOCAL MEASUREMENT** — the variation differed by field between the two payloads: in `13_repeatability` the Choice margin did not move at all and the Noul moved by 0.01, while in `13b_ambiguous_repeatability` the Choice margin moved by 0.07 and the Noul did not move at all.

- **LOCAL MEASUREMENT** — **a stable label is not a fixed distribution.** Across 10 byte-identical call(s) the winning Choice label never switched, so a reader who kept only the label would have seen a perfectly reproducible answer, while the top-2 margin underneath it moved over a range of up to 0.07.
- **LOCAL MEASUREMENT** — the clearest case is `13b_ambiguous_repeatability`: its decided label sits on an exact top-probability tie, which is what a decided label on an undecided distribution looks like in these records.
- **LIMITATION** — two payloads, five calls each, two sessions. There is **no global noise bound** here: nothing in these records says what variation a different payload would show, and a single observation of a tie is not a distribution over ties.

## 8. Speculative fan-out — `05_speculative_fanout`

- **LOCAL MEASUREMENT** — fan-out: 2 request(s), **1412 input / 402 output** tokens; staged: 4 request(s), **1812 input / 273 output**.
- **DERIVED CALCULATION** — pooled input ratio **1.2833x** (staged over fan-out), a saving of **22.08%** of the staged arm's input; estimated cost $0.000059304 against $0.000076104, ratio 1.2833x.
- **DERIVED CALCULATION** — output tokens moved separately: fan-out spent **129 more** output tokens than staged, and at the encoded price for this model output is charged at $0/M, so this does not appear in the cost ratio above.
- **LOCAL MEASUREMENT** — of 12 question(s) asked in the fan-out requests, **8 were consumed** by the code and **4 were unused** — the speculative answers the second strategy never had to buy.
- **LOCAL MEASUREMENT** — of the consumed answers compared field by field, **6 moved** between the two strategies — A `followup_urgency` (`confidence` 0.81 vs 0.78; P(`1`) 0.13 vs 0.14; P(`2`) 0.87 vs 0.86; `score` 1.87 vs 1.86); A `missing_detail` (`confidence` 0.74 vs 0.71; P(`nothing_specific`) 0.16 vs 0.18; P(`reproduction_context`) 0.83 vs 0.81); A `detail_is_blocking` (`noul` 0.42 vs 0.41); B `next_action` (P(`escalate_to_specialist`) 0.96 vs 0.97; P(`request_more_detail`) 0.04 vs 0.03); B `followup_urgency` (`confidence` 0.75 vs 0.76); B `is_unauthorised_change` (`noul` 0.98 vs 0.97).
- **LIMITATION** — a difference here is not an error and neither strategy is the reference: the same question was asked in different company, and the log does not say which reading is correct.
- **LOCAL MEASUREMENT** — latency direction per pair: A `fanout_slower`, B `fanout_faster` — the direction is **inconsistent across pairs**, so no arm is faster here.

- **DERIVED CALCULATION** — **core local finding.** Fan-out carried **400 fewer** input tokens than staged and **129 more** output tokens than staged, while leaving 4 of 12 speculative answer(s) unconsumed by the code.
- **LIMITATION** — two pairs, two states, one session, one branching shape. This is not a general batching-versus-staging rule; the trade depends on how much state is shared and how many branches are speculative.

## 9. Composite scoring — `06_composite_scoring`

- **DESIGN ASSUMPTION** — Jev was asked for 4 **separate, atomic** Score judgments per state (`evidence_quality`, `numerical_stability`, `reproducibility`, `failure_severity`), each on a legend of 4 described positions. Nothing in the payload asks the model to combine them, to count, or to return a verdict.
- **DERIVED CALCULATION** — Python did the arithmetic: normalize each Score by `score / (levels - 1)`, align it to risk direction, multiply by the frozen weight, and sum. Weights: `evidence_quality` 0.3, `numerical_stability` 0.3, `reproducibility` 0.2, `failure_severity` 0.2.

| state | composite risk | largest contribution | that contribution's confidence |
| --- | --- | --- | --- |
| `low_risk` | 0.1417 | `evidence_quality` (0.138) | 0.24 |
| `mixed` | 0.619 | `numerical_stability` (0.21) | 0.67 |
| `high_risk` | 0.887 | `numerical_stability` (0.299) | 0.99 |

- **LOCAL MEASUREMENT** — the states were written to sit in the order `low_risk` < `mixed` < `high_risk`; the composites came back `low_risk` < `mixed` < `high_risk` (`low_risk` 0.1417, `mixed` 0.619, `high_risk` 0.887). The observed order matches the frozen one — which tests the scenarios were written to separate, and is not an accuracy score.
- **LOCAL MEASUREMENT** — in the lowest-risk state the largest single contribution came from `evidence_quality` at confidence **0.24** — the lowest confidence recorded anywhere in this experiment — and carried 97.41% of that state's composite.
- **LOCAL MEASUREMENT** — the per-dimension confidences recorded across the run span 0.24 to 1 (mean 0.8142).
- **DESIGN ASSUMPTION** — confidence was deliberately kept **out of the arithmetic**: it is recorded beside each judgment as a diagnostic, and the composite is a function of the scores alone.
- **LIMITATION** — there is **no composite confidence**. No answer carries one, and none is synthesised in code, so a composite risk figure here cannot say how decided it is.
- **LIMITATION** — the 4 dimensions are **separate, atomic, and designed-orthogonal** — they were written to look at different things. They are **not shown to be empirically independent**, and nothing here measures their correlation. A state that moves several of them at once can therefore be counted more than once by the weighted sum; that possibility is observed, not quantified.
- **LIMITATION** — 3 dimension(s) are aligned so that a high Score is beneficial and 1 is aligned the other way; the alignments are a design decision in code, and a wrong one would invert a contribution silently.

## 10. Function routing — `12_function_routing`

- **DESIGN ASSUMPTION** — the model chooses a function name from a registry frozen before the run and an argument label from that function's own closed set; Python looks the name up and calls the one function it names. No free-form generation is parsed, and no returned string is ever evaluated or imported.

| case | expected | returned | match | confidence | top-2 margin | review signal |
| --- | --- | --- | --- | --- | --- | --- |
| `oscillating_error` | `inspect_residuals` | `inspect_residuals` | yes | 0.76 | 0.67 | 0.79 |
| `refinement_difference` | `compare_runs` | `compare_runs` | yes | 0.58 | 0.49 | 0.75 |
| `unchecked_result` | `request_more_evidence` | `request_more_evidence` | yes | 0.72 | 0.63 | 0.8 |
| `out_of_range_values` | `escalate_for_review` | `escalate_for_review` | yes | 1 | 1 | 0.94 |

- **LOCAL MEASUREMENT** — function match: **4 of 4**; argument match: **4 of 4** resolved case(s).
- **LIMITATION** — these are counts on four synthetic cases with one observation each. They are not an accuracy rate, and the expected labels are the scenario's intention rather than an independent truth, so nothing here estimates how the model would route a request it has not seen.

- **LOCAL MEASUREMENT** — **classifications.** `FUNCTION_TARGET_REALIZED` — all 4 case(s) returned the pre-frozen expected function. `ARGUMENT_TARGET_REALIZED` — all 4 resolved case(s) returned the argument label frozen with their state.

- **LOCAL MEASUREMENT** — `oscillating_error`: confidence 0.76 (floor not cleared at 0.8), review signal 0.79 (not cleared at 0.5), execution withheld.
- **LOCAL MEASUREMENT** — `refinement_difference`: confidence 0.58 (floor not cleared at 0.8), review signal 0.75 (not cleared at 0.5), execution withheld.
- **LOCAL MEASUREMENT** — `unchecked_result`: confidence 0.72 (floor not cleared at 0.8), review signal 0.8 (not cleared at 0.5), execution withheld.
- **LOCAL MEASUREMENT** — `out_of_range_values`: confidence 1 (floor cleared at 0.8), review signal 0.94 (not cleared at 0.5), execution withheld.
- **LOCAL MEASUREMENT** — `ROUTING_SUPPRESSION_EXPECTATION_MISSED` — 3 case(s) the design wrote as routine were withheld, against 1 of 1 expected suppression(s) observed. The pre-registered expectation and the answers disagree, and the disagreement is left standing: no threshold was moved after seeing it.
- **LOCAL MEASUREMENT** — `ACTUAL_HANDLER_EXECUTION_UNTESTED` — no handler was called: every resolved route was withheld (4 of 4), so the allowed-route branch was never entered under a live answer.
- **LOCAL MEASUREMENT** — `FAIL_CLOSED_SUPPRESSION_REALIZED` — 4 route(s) were withheld and no handler ran for any of them; nothing was substituted for a withheld route.

- **LOCAL MEASUREMENT** — **the model produced the intended function and argument in every resolved case** — a function name from a registry frozen before the run and an argument from that function's own closed set.
- **DESIGN ASSUMPTION** — **semantic routing is not execution authorization.** The model's route selected which code was eligible to act; whether anything acted was decided afterwards and elsewhere — the policy withheld every resolved route, so no handler ran. A system that treats a confident route as permission to act has removed the layer that produced this result.
- **LIMITATION** — the execution path from an allowed route to the handler is **not** established by a live run here, and this report does not claim a full execution chain succeeded.

## 11. Token and cost ledger

| experiment | requests | input | output | total | estimated cost |
| --- | --- | --- | --- | --- | --- |
| `01_primitives` | 1 | 512 | 77 | 589 | $0.000021504 |
| `02_structured_addressing` | 2 | 945 | 114 | 1,059 | $0.00003969 |
| `04_confidence` | 2 | 919 | 113 | 1,032 | $0.000038598 |
| `07_instruction_precision` | 2 | 676 | 40 | 716 | $0.000028392 |
| `03_parallel_questions` | 12 | 4,296 | 420 | 4,716 | $0.000180432 |
| `13_repeatability` | 5 | 2,690 | 455 | 3,145 | $0.00011298 |
| `13b_ambiguous_repeatability` | 5 | 2,560 | 385 | 2,945 | $0.00010752 |
| `05_speculative_fanout` | 6 | 3,224 | 675 | 3,899 | $0.000135408 |
| `06_composite_scoring` | 3 | 2,097 | 213 | 2,310 | $0.000088074 |
| `12_function_routing` | 4 | 3,848 | 1,102 | 4,950 | $0.000161616 |
| **TOTAL** | **42** | **21,767** | **3,594** | **25,361** | **$0.000914214** |

- **LOCAL MEASUREMENT** — token counts are the `usage` values the responses returned. Nothing in this report estimates a token count, and no per-question or per-answer figure is derived from one.
- **DERIVED CALCULATION** — cost is a local estimate, computed as reported input and output tokens against the price table entry for the **resolved** model. Basis as encoded: jev-1.13.0: input $0.042/M tokens, output $0.0/M tokens.
- **OFFICIAL** — published price for `jev-1.13.0`: $0.042/M input tokens, $0.0/M output tokens. Output is charged at $0/M as currently encoded, which is why output volume does not move the cost column.
- **LIMITATION** — **TypeSafe Console billing is authoritative.** These figures are this repository's arithmetic over one local price table; they are not an invoice, and an unknown resolved model produces `null` cost rather than another model's rate.

## 12. Latency findings

- **DESIGN ASSUMPTION** — latency here is local wall-clock around one logical call. It is recorded because it is free to record, not because this bench was built to measure it.

| run | experiment | calls | first call (ms) | slowest later (ms) | ratio |
| --- | --- | --- | --- | --- | --- |
| `d8b16aab7ab1` | `03_parallel_questions` | 12 | 3204.053 | 648.729 | 4.9390x |
| `c04a7033c420` | `13_repeatability` | 5 | 2449.657 | 653.96 | 3.7459x |
| `29f21ab11575` | `13b_ambiguous_repeatability` | 5 | 2373.98 | 598.42 | 3.9671x |
| `9c568d1980ec` | `05_speculative_fanout` | 6 | 2407.913 | 634.038 | 3.7977x |
| `4b6e742a3ed3` | `06_composite_scoring` | 3 | 2374.121 | 625.546 | 3.7953x |
| `66be503b34a7` | `12_function_routing` | 4 | 827.045 | 316.99 | 2.6091x |

- **LOCAL MEASUREMENT** — the call that opened the client session was the slowest of its session in **6 of 6** session(s) that record request position; across those sessions the ratio ran from 2.61x to 4.94x.
- **LIMITATION** — 4 session(s) (`01_primitives`, `02_structured_addressing`, `04_confidence`, `07_instruction_precision`) predate the request-position fields. Their first call is not identified, their retries cannot be excluded, and this report does not average over them.
- **LOCAL MEASUREMENT** — within-run groups checked: 2; groups whose first call was the slowest: 1. The exception(s): `03_parallel_questions` cycle 2 opened at 565.435 ms and a later call in the same cycle took 631.096 ms.
- **LOCAL MEASUREMENT** — `transport_attempt_count` is recorded on 35 of 42 record(s), and is 1 on 35 of them. `attempts == 1` licenses exactly one sentence — that call was not observed to retry — and says nothing about what the window contained.
- **LIMITATION** — `retry_count` is `null` on every record because the SDK sets the retry header on the request rather than the response. `null` means **not reported**, never `no retries`, and nothing here backfills it.

- **LIMITATION** — the window also contains DNS, TCP and TLS setup, connection-pool state, server-side queueing, upstream load, and local scheduling. Which of those moved a given call is not knowable from these records, and no decomposition is attempted.

**LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK**

- **LIMITATION** — no speedup table is produced and no arm is called faster on this evidence. The first-call pattern is a hypothesis these fields let a reader check, not a rule about the model.

## 13. Agent-control architecture, distilled

- **DESIGN ASSUMPTION** — **the pattern below is a design this bench followed, not a result it proved.** Each stage is a choice made before the run; the experiments behind it are `01_primitives`, `02_structured_addressing`, `03_parallel_questions`, `04_confidence`, `05_speculative_fanout`, `06_composite_scoring`, `07_instruction_precision`, `12_function_routing`, `13_repeatability`, `13b_ambiguous_repeatability`.

```text
unstructured state
        ↓
typed Jev questions            Choice / Score / Noul
        ↓
retain distributions + confidence
        ↓
ordinary Python policy
        ↓
optional: batching / fan-out
        ↓
deterministic arithmetic
        ↓
closed-set routing
        ↓
fail-closed authorization
        ↓
ordinary code
```

- **DESIGN ASSUMPTION** — **the model makes semantic judgments; the code does everything else.** Every arithmetic result in this report was computed in Python, and no question asked the model to count, sum, interpolate between score levels, or compare dates.
- **DESIGN ASSUMPTION** — **the code owns the thresholds.** The confidence floor, the review threshold, and the composite weights are all code-side constants fixed before the run; the model never sees them and cannot move them.
- **DESIGN ASSUMPTION** — **the code owns the side effects.** Handlers are registered in a dict, they are inert, and a route reaches one only after the policy allows it. Nothing the model returns is executed.
- **DESIGN ASSUMPTION** — **closed sets over free-form generation.** A label from a frozen registry and an argument from that label's own frozen set are checkable; a sentence is not.
- **DESIGN ASSUMPTION** — **confidence is a diagnostic and a policy input, never a correctness score.** It gates an action; it never edits an expectation and is never averaged into a result.
- **DESIGN ASSUMPTION** — **keep the whole distribution.** The winning label is the smallest part of an answer: a near-tie and a unanimous label are the same entry in a count and different facts about the state.
- **DESIGN ASSUMPTION** — **fail closed.** A malformed, missing, or unavailable answer stops the case; it is never defaulted, matched to a neighbour, or filled in from the branch that would have been taken.

## 14. What this evaluation did not establish

- **LIMITATION** — **no general accuracy estimate.** There is no ground truth anywhere in this bench: expected labels are the design's intention, written alongside the states, and every count is over a handful of synthetic cases.
- **LIMITATION** — **no calibration claim.** Nothing here says a confidence of 0.8 corresponds to being right 80% of the time. Confidence was never compared against an outcome rate.
- **LIMITATION** — **no deterministic-model claim.** The opposite was observed: byte-identical requests returned differently-shaped distributions, so this model must be treated as producing variable answers.
- **LIMITATION** — **no universal repeatability bound.** Two payloads, five repeats each, two sessions. Nothing states a variance, a tolerance, or a bound that another payload would obey.
- **LIMITATION** — **no stable latency or speedup claim.** Sessions showed a slow first call and one in-run group broke the pattern; the window is not decomposable from these records.
- **LIMITATION** — **no general superiority over any other approach.** No LLM baseline was run, no alternative was benchmarked, and no comparison of that kind is implied.
- **LIMITATION** — **no universal batching ratio.** The batching and fan-out savings are properties of these payloads, where every question reads the same state.
- **LIMITATION** — **no proof that the composite dimensions are independent.** They are separate, atomic, and designed-orthogonal; their correlation was never measured.
- **LIMITATION** — **no real external side effect.** Every handler is inert. No file was written, no network call made, no message sent, no state changed outside this repository.
- **LIMITATION** — **the live allowed-handler execution path is untested.** `ACTUAL_HANDLER_EXECUTION_UNTESTED` stands: an allowed route has not been observed reaching `HANDLERS[name](argument)` under a real answer.
- **LIMITATION** — **no production-safety certification.** Nothing here certifies this pattern as safe to run against real systems, real customer data, or real money.

## 15. Unrun experiments

**OPTIONAL_EDGE_COVERAGE_BACKLOG**

- **LOCAL MEASUREMENT** — all 10 registered experiment(s) have at least one canonical record, so nothing is outstanding.

## 16. Secret architecture

```text
TYPESAFE_API_KEY (environment)
        ↓ overrides
.secrets/typesafe.env  (repo root, git-ignored)
        ↓ otherwise
fail closed: no key, no request
```

- **DESIGN ASSUMPTION** — the credential has exactly two sources, resolved in that order by `jev_lab.client`. The environment wins when it is set, so an operator can override a stale file without editing it; there is no third source and no 'search a few likely places' fallback.
- **DESIGN ASSUMPTION** — an absent, empty, malformed, duplicated, or unreadable source stops the run before a request is sent. Nothing proceeds on a guess.
- **LIMITATION** — which of those two sources supplied the key for a given historical invocation is **not recorded in the canonical log**, so this report cannot reconstruct it. No record carries a credential source, and no other committed artifact is canonical for it. The two sources and their order are design facts stated above; which one answered a particular call is not a fact these records carry, and it is not inferred here.
- **LIMITATION** — the key is never printed, logged, hashed, fingerprinted, or measured here — not its value, length, prefix, suffix, or any derived identifier. Status reports `missing`, `exists (source=…)`, or `unusable (<kind>)` and nothing else.
- **LOCAL MEASUREMENT** — the canonical log carries no credential material: no record names a credential source, and none carries an authorization header, an `sk-` prefix, or a token-shaped string.
- **DESIGN ASSUMPTION** — that absence is checked rather than assumed: the offline suite scans the canonical log for those patterns and fails if one appears.
- **DESIGN ASSUMPTION** — `.secrets/` is excluded by `.gitignore`; the check that proves it is `git check-ignore -v .secrets/typesafe.env` and a `git add --dry-run`, both of which the test suite runs. This document is not itself a security boundary, and no comment in it should be read as one.
- **LIMITATION** — the file's operating-system permissions are the platform's default and are not managed by this repository; on a shared or cloud-synced machine the directory may be readable by more than its owner.

## 17. Reproducibility index

| artifact | role | regenerate with |
| --- | --- | --- |
| `results/usage.jsonl` | **canonical source of truth**, append-only | — never regenerated; only appended to by a real run |
| `results/summary.csv` | derived | `uv run python -m jev_lab report` |
| `results/summary.md` | derived | `uv run python -m jev_lab report` |
| `results/capability_snapshot.md` | derived | `uv run python -m jev_lab snapshot` |
| `results/JEV_LOCAL_EVALUATION_FINAL.md` | derived | `uv run python -m jev_lab final-report` |
| `src/jev_lab/` | the bench: client, recorder, experiments, derivation modules | — |
| `tests/` | offline suite; sockets are blocked and no test may call the API | `uv run pytest` |

- **LOCAL MEASUREMENT** — this report was derived from 42 record(s). A revision of it that does not match the log is a stale copy of a derived file, not a second measurement.
- **LIMITATION** — nothing in this report is pinned to a revision, and the generator does not read the repository's version-control state: it is built from the log alone, so it cannot say which revision of the bench produced a record. The log's own hashes are the only fixity the records carry.

---

`CORE_CAPABILITY_EXPLORATION_CLOSED` · `ACTUAL_HANDLER_EXECUTION_UNTESTED` · `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK` · `OPTIONAL_EDGE_COVERAGE_BACKLOG`

Derived from `results/usage.jsonl`, which remains the canonical record.
