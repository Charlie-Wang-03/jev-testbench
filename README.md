# jev-test

**English** | [简体中文](README.zh-CN.md)

An auditable experimental harness for studying **TypeSafe Jev** as a typed probabilistic decision
primitive for LLM and agent workflows.

Jev is not a chat model. It takes a `state` and a set of **typed questions**, and returns
**structured answers with probabilities** — a `Choice` label with a distribution, a `Score`
position on an ordered rubric, or a `Noul` scalar probability. It does not generate prose, hold a
conversation, or remember anything between requests. See
[What is Jev?](#1-what-is-jev) for sources.

This repository is a measurement bench for that primitive. Every real API call appends exactly one
line to an append-only JSONL log, and every claim in these documents is labelled as an official
vendor claim, a design assumption, a local measurement, a derived calculation, or a limitation.

The main result is a negative one, and it is stated rather than softened:
`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`. Nothing here is both new relative to TypeSafe's published
material and supported by this repository's own data. The section that bounds every other claim is
[what you cannot conclude](#7-what-you-can-not-conclude-from-this-repository).

**Status:** `CORE_CAPABILITY_EXPLORATION_CLOSED` · **Tests:** the full offline suite passing ·
**Evidence:** [42 core records](results/usage.jsonl) + [12 P3 records](results/p3_boundary_locus/usage.jsonl) ·
**Release:** [v0.1.0 evidence freeze](docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md)

---

## 1. What is Jev?

**TypeSafe's own description** (not this repository's conclusion):

> Jev is a typed probabilistic decision model — a "System One" model that turns unstructured state
> into typed probabilistic decisions.

Sources: <https://docs.typesafe.ai/llms.txt> · <https://typesafe.ai>

This bench measures what that primitive does **on this machine, with this account, on our
inputs**. A performance or accuracy statement from TypeSafe is recorded here as an
**OFFICIAL CLAIM** about *their* workload. It is never presented as something we verified.

## 2. What is this repository?

An experimental harness — not an API demo, not a leaderboard, and not a general accuracy
benchmark. Its value comes from the trustworthiness of one artifact:

| | |
|---|---|
| Core canonical log | [`results/usage.jsonl`](results/usage.jsonl) — 42 records |
| Core log SHA-256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| P3 canonical log | [`results/p3_boundary_locus/usage.jsonl`](results/p3_boundary_locus/usage.jsonl) — 12 records |
| P3 log SHA-256 | `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` |
| Resolved model | `jev-1.13.0` on 42 of 42 records (requested as `jev-latest`) |
| Tokens | 21,767 input / 3,594 output — as returned by the API, never estimated |

Two canonical logs, deliberately not merged: the 42-record core evaluation is frozen historical
evidence, and appending to it would invalidate a published hash. P3 kept its own log for the same
reason. See [Evidence provenance](docs/EVIDENCE_PROVENANCE.md).

## 3. Why does it exist?

Because the interesting question about a probabilistic decision primitive is not "is it good?" but
**"what exactly did it do, and what can I actually conclude from that?"**

- **Not an API demo.** Nothing here is written to show the product at its best.
- **Not a leaderboard.** There is no ground truth anywhere in this bench, so there is no accuracy
  score to rank.
- **Not a general benchmark.** Every number describes one payload, one account, one session, at one
  model version.
- **Evidence-oriented.** Failed calls are records. Negative results are kept. A finding that turns
  out to be neither novel nor supported is written up as *killed*, not quietly dropped.

## 4. What did we test?

10 experiments are registered, and **all 10 have been run** — the registry has no unrun design in
it. Two tiers:

**`core` — the foundational mechanics**

| Experiment | Calls | What it measures |
|---|---|---|
| `01_primitives` | 1 | `Choice` + `Score` + `Noul` in one request against one state. |
| `02_structured_addressing` | 2 | Field-path addressing over structured state vs. described addressing over prose state. |
| `03_parallel_questions` | 12 | One batched request vs. the same questions sent separately, in two order-balanced cycles. |
| `04_confidence` | 2 | Specific vs. ambiguous evidence, routed in code on confidence alone. |

**`extended` — specific behaviours and documented limits**

| Experiment | Calls | What it measures |
|---|---|---|
| `05_speculative_fanout` | 6 | One request carrying both branches' follow-ups vs. a second request staged on the first answer. |
| `06_composite_scoring` | 3 | Four atomic `Score` questions composed into one risk **in Python**, weights frozen before the run. |
| `07_instruction_precision` | 2 | Vague vs. explicit decision boundaries on a byte-identical 82-byte state. |
| `12_function_routing` | 4 | Route a state to a name in a registry frozen before the run, then to a closed-set argument. |
| `13_repeatability` | 5 | One byte-identical request sent five times. |
| `13b_ambiguous_repeatability` | 5 | A payload known to land mid-scale, sent five times. |

**P3 — a preregistered replication** ([design](docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) · [result](docs/audits/P3_BOUNDARY_LOCUS_RESULT.md))

Experiment `07` moved a `Noul` from 0.75 to 0.20 by changing the *instructions* and the *criteria*
together, so it could not say which field carried the move. P3 crossed the two fields 2×2, three
repeats per arm, twelve calls, with the design and thresholds frozen before the first request.

Five further experiments were designed for this bench and **retired before publication** rather
than run: `00_model_info`, `08_literal_reading`, `09_numeric_limits`, `10_state_length` and
`11_language_pair`. Each was reviewed against a fixed six-question rubric — information gain,
public value, design validity, interpretability, maintenance cost, redundancy against the official
documentation — and none cleared the bar. The reasoning for each is in
[the experiment registry](docs/experiments/EXPERIMENT_REGISTRY.md); their code is in git history.

An experiment that was never run is an intention, not evidence, and this repository does not keep
a backlog of intentions. There is therefore **no "registered but not run" state** here.

## 5. What did we learn?

The most robust results. Every one is a **local measurement** unless marked otherwise.

**Typed output semantics reproduce cleanly here.** All 42 responses were schema-valid and typed
only — no free-text field anywhere. Across 45 `Choice` answers the returned label was always the
highest-probability option; across 29 `Score` answers, 24 reproduced the probability-weighted mean
within 0.006. `Noul` answers carry no separate `confidence` field, because with only two outcomes
the one number already describes the whole distribution. *(This is the weakest kind of support for
a type-safety claim: it shows schema conformance on benign payloads, not factual correctness.)*

**Same-state batching materially reduces repeated-state input usage in this workload.** Sending 5
questions over one state in a single request cost **816 input tokens**; sending the same 5
questions separately cost **3,480** — a **4.26× pooled input ratio, 76.55% fewer input tokens**,
with **10 of 10** selected values identical across the two arms. *This is one payload where every
question reads the same state. It is not a universal batching ratio, and it is not comparable to
the vendor's own published multiplier, which describes a different workload.*

**Confidence is useful as a policy input, but it is not a per-answer correctness guarantee.** The
official docs scope calibration to *groups* of predictions and state that confidence "describes
the model's answer, not a guarantee that the answer is correct" — this repo's two confidence cases
*illustrate* that scoping and cannot test it. The local cautionary example: in `06`, a dimension
scored 1.62 against a confidence of **0.24**, and that dimension carried 97.4% of that state's
composite risk.

**Instruction and criteria specificity materially moved one payload.** On a **byte-identical**
82-byte state, a vague decision boundary returned `Noul` **0.75** and an explicit one returned
**0.20** — a move of **0.55** on a 0–1 probability. Neither arm is ground truth, and one pair is
not a dose–response curve.

**P3 could not attribute that move to either field.** Verdict:
**`P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`**. Instruction-only reached a median of 0.31 and
criteria-only 0.36 — both clear of the vague baseline (0.76), and only **0.05 apart from each
other**, against a 0.56 end-to-end gap. The pre-registered rule killed the attribution: no
assignment of a single-field arm left its counterpart near the vague baseline. Descriptive only:
instruction-only recovered 80.4% of the gap and criteria-only 71.4%. **A null result is a result.**

**Repeating an identical request moves the distribution underneath a stable label.** Across ten
byte-identical calls the winning `Choice` label never switched, while the top-2 margin underneath
it moved by up to 0.07 and one repeat produced an exact tie. The *effect* is real; it is not a
novel finding, and P2 killed it as one — see below.

**Routing and authorization are separate engineering layers.** In `12_function_routing` the model
matched the intended function 4 of 4 times and the intended argument 4 of 4 times — and a policy
frozen before the run withheld **every** route, so no handler ran at all. Whether to act was
decided in Python, after the model answered. A system that treats a confident route as permission
to act has removed the layer that produced this result.

**And — the part that matters most — several good-looking findings were deliberately killed.** P2
triaged every candidate against the standard: *is this both novel relative to TypeSafe's public
material, and supported by our own data?* Seven candidates were retired, including the two with the
largest local effect sizes:

| Killed candidate | Why |
|---|---|
| "Stable label, moving distribution" | Not novel — officially entailed and already publicly reproduced with more data than ours. |
| Batching cuts input tokens | Expected shared-state amortisation; public measurements go further (they varied batch size). |
| The 0.75 → 0.20 instruction effect | A direct instance of a documented failure mode with a documented remedy. |
| The ambiguous case clearing a 0.60 gate | Pure threshold arithmetic on **our own** constant — the expression reproduces 0.61 exactly. |
| Fan-out trades input for output | Generic speculative-execution tradeoff — and on this product the "wasted" resource is output tokens, which the price card rates at zero. |
| `confidence` not recomputable from logged `probabilities` | An artifact of 2-decimal API rounding — a limit of our *record*, not a behaviour of the model. |
| Every correct route was suppressed | Our own Python policy, and the source comments say so. |

> **No candidate was killed for being unflattering, and no candidate was preserved for being
> interesting.**

The one candidate that survived triage was the P3 question above — and P3 then returned a null.
**This repository currently reports no Jev-specific finding that is both novel and supported by its
own data.** That is the honest state of the evidence, and it is the point of the exercise.

Full write-ups: [Findings](docs/findings/findings.md) ·
[P1 official-claims audit](docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md) ·
[P2 novelty triage](docs/audits/P2_JEV_INSIGHT_TRIAGE.md) ·
[P3 result](docs/audits/P3_BOUNDARY_LOCUS_RESULT.md).

## 6. What can you reproduce?

### Fully offline — no API key needed

```console
uv sync --locked
uv run pytest                                    # the offline suite, sockets blocked
uv run python -m jev_lab report                  # summary.csv, summary.md
uv run python -m jev_lab snapshot                # capability_snapshot.md
uv run python -m jev_lab final-report            # JEV_LOCAL_EVALUATION_FINAL.md
```

The tests never touch the network — the suite blocks sockets outright, so an accidental API call
fails rather than spends. Every derived report is rebuilt from the committed canonical logs, so the
numbers in them cannot drift from the records they describe.

### Live reproduction — needs a TypeSafe account

```console
uv run python -m jev_lab list                    # experiments, call ceilings, credential status
uv run python -m jev_lab run 01_primitives       # one experiment, ceiling of 8 calls
uv run python -m jev_lab run-all --tier core     # a whole tier; refuses without an explicit budget
```

**These commands spend real money.** `run` defaults to a hard ceiling of 8 API calls; `run-all`
refuses to start unless `--max-requests` covers the tier. See
[Credentials](docs/guides/credentials.md) and [Reproducibility](docs/guides/reproducibility.md).

> **Frozen measurements are historical measurements, not golden outputs.** A fresh live run will
> not necessarily reproduce these numbers. The model alias `jev-latest` can move, the account and
> session differ, and this is a probabilistic model — byte-identical requests returned
> differently-shaped distributions here. Reproducing the *method* is the goal; reproducing the
> *digits* is not something this design can promise.

## 7. What you can NOT conclude from this repository

Stated plainly, because it is the most important section here:

- **No general accuracy.** There is no ground truth anywhere in this bench. "4 of 4" is a count on
  synthetic cases, never a rate.
- **No calibration validation — in either direction.** No outcome rate exists here, so this repo
  must never be cited as validating *or* falsifying calibration.
- **No model latency benchmark.** Latency is recorded, not benchmarked. No speedup is claimed, and
  no arm is called faster.
- **No determinism guarantee — and no non-determinism guarantee.** A handful of repeats on two
  payloads is not a determinism verdict.
- **No universal batching ratio.** The 4.26× figure is a property of one payload where all
  questions share one state.
- **No broad hallucination benchmark.** Nothing here probes factual correctness; "can't
  hallucinate" carries the vendor's own "not empirical" qualifier.
- **No production-safety certification.** Every handler is inert. Nothing here certifies any
  pattern as safe against real systems, real customer data, or real money.
- **No vendor-claim adjudication.** Official figures are recorded as claims about TypeSafe's
  workload and are never restated as things we measured.

Cost figures are **local estimates** from one price table. TypeSafe Console billing is
authoritative.

---

## Documentation

**[docs/README.md](docs/README.md)** is the documentation index, grouped by what you are trying to
do: start here, understand the evidence, or reproduce and extend.

| | |
|---|---|
| [Architecture](docs/architecture/architecture.md) | Data flow, the agent-control pattern, module map. |
| [Findings](docs/findings/findings.md) | What reproduced, engineering lessons, killed findings, scope limits. |
| [Methodology](docs/methodology/evaluation.md) | Claim labelling, experiment design, what A/B arms do and do not establish. |
| [Reproducibility](docs/guides/reproducibility.md) | Offline and live paths, what "reproduce" can and cannot mean here. |
| [Credentials](docs/guides/credentials.md) | How the API key is resolved, and what that scheme does not buy you. |
| [Technical write-up](docs/blog/jev-as-probabilistic-decision-primitive.md) · [中文](docs/blog/jev-as-probabilistic-decision-primitive.zh-CN.md) | The narrative version: what the bench measured, and why the null is the result. |
| [Evidence provenance](docs/EVIDENCE_PROVENANCE.md) | The P0–P3 lineage: measurement commits vs. analysis commits. |
| [Final evaluation](results/JEV_LOCAL_EVALUATION_FINAL.md) | All 42 records, every claim labelled. *Derived artifact.* |
| [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) | How to work in this repo, and how to report a problem. |

## Ground rules

- Official TypeSafe docs are the source of truth for product semantics:
  <https://docs.typesafe.ai/llms.txt>. A local observation that contradicts them is recorded as a
  finding, not silently "fixed".
- Official claims and local measurements are recorded separately, and each result says which it is.
- **Code does arithmetic; Jev does semantic judgment.** Jev is never asked to count, sum, compare,
  interpolate, or compute a date difference.
- Token counts are the `usage` values the API returned. **Nothing here estimates a token count.**
- Both `model_requested` and `model_resolved` are recorded, because an alias can move.
- `results/usage.jsonl` is append-only. Nothing is rewritten, reordered, or deleted — including
  rows for failed calls. A failed call is data.
- All state is synthetic. No real personal, customer, or proprietary data.
- No secrets in this repository, ever.

## License

**MIT.** See [`LICENSE`](LICENSE), and [the license decision](docs/OPEN_SOURCE_LICENSE_DECISION.md)
for the reasoning and the alternative that was considered. One license covers the code, the two
canonical logs, and the derived reports; no separate data license is applied.
