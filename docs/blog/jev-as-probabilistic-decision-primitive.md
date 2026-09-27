# Treating Jev as a Probabilistic Decision Primitive for Agents: 54 API Calls, a Preregistered Null Result, and What I Learned About Model Evaluation

**English** | [简体中文](jev-as-probabilistic-decision-primitive.zh-CN.md)

I spent 54 API calls trying to answer one question: **if a model returns typed probabilistic answers instead of generated text, what does an agent's code look like?**

The conclusion first, because it determines how every section below should be read: **after 54 API calls, I did not end up with a result that survived scrutiny as a strong Jev-specific novel finding.** What did survive was more useful to me: an evaluation method someone else can audit, and a preregistered null result I had to report the way it came out.

This post is about how that happened.

---

## 1. An agent-engineering question

Generative LLMs are good at three things: generate, explain, transform. But in an agent's workflow, many steps are not generation at all — they are classify, route, score, branch, gate.

The usual way to build those steps is to ask the model for a JSON blob, then parse, validate and retry around it. That works — and it turns "the type is correct" into something you defend over and over: a missing brace, an integer that arrives as a string, a label the model invented because none of yours fit.

So there is an obvious question:

> What happens if the model itself defines "output" as a closed, typed probability distribution, rather than a piece of text you have to parse?

TypeSafe positions its Jev model as that kind of thing. Their launch post has the line I think captures the pitch most tightly — Jev as, in their words, "a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out."

That is **the vendor describing their own product. It is not my measurement.** This post will keep returning to that distinction, because it is the single most important discipline in the project.

To answer the question with something other than an impression, I built a measurement bench.

---

## 2. What Jev is, and what it is not

According to TypeSafe's documentation, a Jev call has roughly this shape:

```
state + a set of typed questions → a set of typed probabilistic answers
```

`state` is the input under evaluation — a string, a JSON object, or an array. The docs say every question in a request sees the **same** state and is evaluated independently of the others, which matters in §5.

Questions must be one of three types, and answers have three corresponding shapes:

- **Choice** — pick one from a supplied set of options. Returns the selected label and the full probability distribution over the options, summing to 1. The docs define `choice` as the highest-probability option.
- **Score** — a position along supplied levels. It can land between levels; the documented definition is the probability-weighted mean of the level numbers, and it comes with a `confidence`.
- **Noul** — a single number, P(yes). With two outcomes, one probability already describes the whole distribution, so it carries **no** separate `confidence` field.

Two things here are worth separating out, because I nearly blurred them myself.

**First, there is no free text in an answer.** Across the 42 core records I ran on one account at one model version, **45 of 45** Noul answers carried no `confidence` field, while every Choice and Score answer had one. That is the vendor's documented design; all I did locally was reproduce it. The 45-of-45 figure has a small story attached, and it is in §11.

**Second, `probability` and `confidence` are not the same thing.** `probability` is the distribution over the options. `confidence`, per the docs, is "a statistic computed from the returned distribution." Both arrive side by side in the same answer, and they are two different numbers. I hit this on my very first call (`01_primitives`): the winning option's probability was **0.45**, and the same answer's confidence was **0.26**.

If you take one sentence from this section, take this: **typed output solves the schema problem, not the semantic one.** An answer that is perfectly well-formed is not thereby correct, and it is not thereby something you should act on.

The vendor's own documentation is clearer about this than its marketing might suggest. Its known-limitations page lists the failure modes one by one — literal reading, weak numeric representation, date comparison, indirection, large state — and says outright that control flow belongs in your code. I did not discover that. The vendor published it.

---

## 3. I didn't take the docs on faith — I built a bench first

Product documentation describes how a product is supposed to behave. The gap between that and how it does behave is where the engineering cost lives. But "I have a feeling it's sometimes off" is not something you can act on.

So I built `jev-test`. Its goal is not to rate Jev or build a leaderboard, but that **every conclusion can be traced back to a log line.**

A few hard rules came out of that:

**Official claims and local measurements stay strictly apart.** Any vendor number is a claim about **their** workload, not a measurement of this machine, this account, or my inputs. Only a line written to `results/usage.jsonl` by a real call is a local measurement, and I say which of the two a sentence reports.

**The log is append-only.** One real API call produces exactly one record, whether it succeeds or raises. A failed call is still data. Nothing is deleted, reordered, or "fixed and written back." `results/usage.jsonl` is frozen once published. The two logs here have SHA-256 `38e67630…` and `17f36f75…`, and neither has moved a byte since.

**Record both the requested model and the resolved model.** I asked for the alias `jev-latest`; all 42 records came back as `jev-1.13.0`. Aliases drift; only the response says who answered.

**Label anything you didn't measure directly.** Token counts come from the API's `usage` values and are never estimated. Cost and latency are local derivations, labelled as such.

**Derived artifacts must not drift.** Everything under `results/` other than the two canonical logs is regenerated from them; CI does the regeneration, diffs against the committed copies, and fails on any difference. A derived report must never become a second source of truth.

**Preregister before you call.** The most important rule, and §8 is about it.

Partway through, I realised this repository is not only evaluating Jev. **It is also evaluating whether I am entitled to draw a larger conclusion from one model's output.** Most of the time, the answer was no.

### A note on cost

The 54 calls came to about **$0.001** by local estimate — a thousandth of a dollar. That is a **local estimate, not a bill**; TypeSafe Console billing is authoritative. The point: the barrier to independently checking a model's behaviour is lower than most people assume.

---

## 4. What the first round actually measured

Ten experiments were registered in the first round. All ten ran, producing **42 core records**. I grouped them by purpose rather than chronology, because purpose explains better what they probed:

| Theme | Experiments | What was being probed |
|---|---|---|
| **Output semantics** | `01_primitives`, `02_structured_addressing`, `06_composite_scoring` | The answer shapes of the three primitives; addressing into structured state; combining several atomic Scores into one risk number on the Python side (weights frozen before the run) |
| **Workflow economics** | `03_parallel_questions`, `05_speculative_fanout` | Batching questions over one shared state into a single request vs splitting them; carrying both branches' follow-up questions in one request vs waiting for the first answer to come back |
| **Decision behaviour** | `04_confidence`, `07_instruction_precision` | Confidence as an input to a code-side gate; a vague vs an explicit decision boundary |
| **Repeatability and control** | `13_repeatability`, `13b_ambiguous_repeatability`, `12_function_routing` | Sending a byte-identical request repeatedly; routing to a function name and arguments from a frozen registry |

Two are very small: `04_confidence` has **2** cases and `12_function_routing` makes **4** calls. Too few to support any ratio — they support one statement: this is how things went on these synthetic cases.

**None of the ten left behind a conclusion that is both new relative to TypeSafe's public material and supported by my own data** — the state the freeze document calls `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`. Three groups follow.

---

## 5. What I reproduced

One thing came out clean locally: **putting several questions that share one state into a single request cuts input tokens substantially.**

Concretely, `03_parallel_questions` put five questions over the same state into **one** request, and two order-balanced cycles together consumed **816** input tokens. Splitting the same five questions into **five separate** requests consumed **3,480** input tokens over the same two cycles.

From those two numbers: a **4.2647×** input ratio, a **76.55%** saving, and **10 of 10** selected values identical between arms, with a largest absolute difference of **0.0**.

The effect is real and large. Its boundaries travel with it:

- These are numbers from **one payload**, where all five questions read the same state — exactly the condition the saving depends on.
- They come from **two order-balanced cycles in one session**: not an average, and certainly not a distribution.
- It is **not** a general batching multiplier, and it **cannot** be placed next to the vendor's published multipliers. TypeSafe's `primitives.md` reports "13 questions batched into one call, 11.5× cheaper and 9.6× faster than 13 separate calls"; the parallel-questions page reports "12.2× cheaper and 10.0× faster." **Those are different workloads — different question counts, different payloads, different denominators, different sessions.** Putting "vendor: 12.2×" beside "local: 4.26×" and calling it "claimed vs. actual" is a category error.

The honest sentence is one line: **on this payload, the local measurement reproduced the shared-state amortisation the vendor describes.**

The mechanism is also **expected**: public third-party measurements went further on the same pattern, varying batch size and publishing an accuracy curve against it. My experiment used one fixed payload and never varied a batch parameter. So this one is a reproduction, not a finding.

---

## 6. The things that looked interesting and got deleted

This is the section I most wanted to write.

After the first round I had seven candidates that looked writable. I put each through adversarial review, asking the same question: **is this both new relative to TypeSafe's public material and supported by my own data?**

All seven failed. Two are worth sharing, because they are the best stories — and for exactly that reason, the ones that most needed deleting.

### A stable label is not a stable distribution

I sent the same 512-token request, byte for byte, five times. **The winning Choice label did not change once — 5 of 5.** Under that stable label, the distribution was moving: the top-two margin shifted by up to **0.07**, `Score` landed between **1.58 and 1.63**, `confidence` sat between **0.24 and 0.30**, and one run produced an **exact tie** between the top two options.

I found that genuinely interesting. Then I found it in the vendor's cookbook. TypeSafe's own docs report label flips on 2 of 8 questions and a non-zero per-label probability standard deviation (mean 0.0098, max 0.0515), and say outright that "when two labels are close, a small change can still flip the top label."

Which means **"the label is stable but the distribution moves" is directly implied by two things the vendor published.** They don't use my phrasing. But the observation is not the thing I thought it was.

More decisively, there is public material. A public chaos-test report describes sending **byte-identical requests** to Jev five times and getting `0.03, 0.03, 0.03, 0.04, 0.04`, with jitter floors measured over roughly 1,490 captured calls. So the design I assumed was ours — repeats on byte-identical requests — **had already been run, with a larger sample and better statistics.**

The conclusion: **an interesting observation is not a new finding.** What separates them is whether someone got there first.

### The ambiguous case that "crossed the 0.60 gate"

The second candidate came from `04_confidence`: a case I deliberately designed to be ambiguous returned intent `other` with confidence **0.61**, just over the 0.60 gate I had written in code, so it was accepted.

The story sounds like a model making a judgment call at a delicate boundary. It is not.

The `0.60` is **a constant I wrote myself in `experiments.py`**, labelled in the code comments as a demonstration threshold — never calibrated, never tuned on any data, not claimed to be optimal. TypeSafe's own docs use 0.5 on one page and 0.6 on another for the same worked example, and say thresholds must be tuned per domain.

Nor was the returned distribution close: **0.74 against 0.26, a margin of 0.48.** The ambiguity was a property of my state design, not of the returned distribution. The published k=3 approximation, `(3 × 0.74 − 1) / 2`, reproduces 0.61 **exactly** — it is an arithmetic result.

So: **`0.61 ≥ 0.60` is our own policy arithmetic, not a finding about the Jev model.** Move that constant and the conclusion changes, without a single model call taking place.

### And one about "the model refusing to act"

In `12_function_routing` I had the model route requests to a function registry frozen in advance. It matched the expected function **4 of 4** times and the expected arguments **4 of 4** times — and then my policy suppressed **4 of 4**, sending every one to `human_review`. The handler was never entered.

That is easy to write up as "the model won't act." But all four suppressions trace to constants in `routing.py`: the route confidences were 0.76 / 0.58 / 0.72 / 1.0 against a floor of 0.8, so the first three were held only for falling below that line; the fourth, at 1.0, was held by the `needs_human_review` threshold of 0.94 against 0.5. The comment next to the constant reads: *nothing in the docs says 0.8 is the right line*.

The honest sentence: **the router was declining to act on my instructions. Jev did not produce unusable confidence.**

**The point of this section is that the most blog-friendly stories were often the ones that failed scrutiny first.** Of the seven candidates, the two with the largest effect sizes — this section's first, and §5's 4.26× — died hardest, and in both cases what decided their fate was that **someone had already done it in public**, not that my data was weak.

No candidate was killed for being unattractive, and none was kept for being attractive.

---

## 7. The one thread worth pulling

Exactly one of the seven survived — not because the effect was large, but because **it had a specific, falsifiable unknown attached.**

It came from `07_instruction_precision`. On a **byte-identical 82-byte state**, I changed how the decision boundary was written: with a vague boundary a `Noul` returned **0.75**; with an explicit one it returned **0.20**. Same state bytes, a **0.55** difference on a 0–1 probability.

The effect is large. It has two problems.

**First, neither 0.75 nor 0.20 is ground truth.** Neither arm is "correct." They are two different numbers.

**Second, and this is the decisive one — my two arms changed `instructions` and `criteria` together.**

So the experiment **cannot** support any sentence like:

- ✗ "Jev weights criteria more heavily."
- ✗ "Rewording the prompt alone produced 0.55."
- ✓ The only available sentence: "On this payload, moving both fields together from vague to explicit moved `Noul` by 0.55."

And that ran straight into a question the vendor's docs do not answer. TypeSafe's known-limitations page lists literal reading as its first failure mode and prescribes: state explicit conditions in `instructions`, write edge cases into `criteria`. **But it gives that as a bundle. It never separates them.** The docs also say to treat `criteria` as an extension of `instructions`.

Which is the problem: **is that boundary carried by `instructions`, or by `criteria`?**

The vendor never decomposed it. My own data never decomposed it — I moved both fields together. Nor could I find a controlled attribution experiment in the public material. So it became the one question that passed review and was worth spending calls on.

One aside: the public-novelty check for that question came back `PUBLIC_NOVELTY_UNRESOLVED` — *unresolved*, not *nobody has done it*. Those are not the same claim.

---

## 8. P3: an actual preregistered experiment

Before the first request went out, I wrote down the design, the order, the statistics and every threshold, and committed them. It is the habit from this project I would most want to keep.

The design is a 2×2 that crosses the two fields:

| Arm | `instructions` | `criteria` |
|---|---|---|
| `N` | vague | vague |
| `I` | explicit | vague |
| `C` | vague | explicit |
| `B` | explicit | explicit |

Each arm repeats **3** times, for **12** calls — a hard ceiling written into the preregistration. No retry loops, no polling, no "let's run a few more and see."

The fixed order was `N1 → I1 → C1 → B1 → B2 → C2 → I2 → N2 → C3 → N3 → B3 → I3`, balanced at both ends and in the middle.

The preregistration also records a **design hazard** that I think matters more than the thresholds: the `I` and `C` arms must state **the same** boundary, differing only in *where it is written*. An arm whose instructions and criteria contradict each other triggers another failure mode the vendor documents, and that arm is then a protocol violation rather than a data point.

Finally, the `N` and `B` endpoint arms are three-repeat versions of the original `07` arms. Their job is **diagnostic** — to check whether the original effect is still there. Like every threshold, they were frozen before the first request, so nobody could use them to re-tune a threshold after the fact.

The GO and KILL conditions were fixed in advance too. The decisive one:

```
K1:  |I_med − C_med| < 0.1   →  attribution fails
```

---

## 9. P3's raw results

All 12 calls succeeded. Every raw value is listed — the medians summarise them, they do not replace them:

| Arm | Raw `Noul` values | Median | Range |
|---|---|---:|---:|
| `N` (both vague) | 0.77, 0.76, 0.75 | 0.76 | 0.02 |
| `I` (instructions only) | 0.31, 0.33, 0.29 | **0.31** | 0.04 |
| `C` (criteria only) | 0.37, 0.36, 0.33 | **0.36** | 0.04 |
| `B` (both explicit) | 0.20, 0.21, 0.20 | 0.20 | 0.01 |

The endpoints replicated. The original `07` observation was 0.75 → 0.20, a move of 0.55; this run gave an `N` median of **0.76** and a `B` median of **0.20**, a gap of **0.56**, at three repeats per arm on the same payload. The ordering held and so did the magnitude.

What actually happened is in the two single-field arms: **both moved most of the way to the explicit baseline.**

- `I`'s median of 0.31 is 0.45 below `N`'s 0.76 — **80.4%** of this run's 0.56 endpoint gap.
- `C`'s median of 0.36 is 0.40 below — **71.4%**.
- And the two single-field arms are only **0.05** apart.

**0.05 < 0.10. K1 fired.**

Under the preregistered rule, that means: **under this design and sample size, the original effect cannot be attributed to either `instructions` or `criteria` alone.**

Final verdict:

```
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
```

About those two percentages (80.4% and 71.4%): **they are descriptive arithmetic on the medians above, not part of the decision rule.** No threshold was derived from them, and ignoring them changes not one word of the verdict.

---

## 10. Why a null result is a good result

What P3 produced is not a "didn't work" result. It is a real negative result — and not a failed experiment. The original large effect **replicated**: the 0.55 move reappeared as a 0.56 gap, endpoints in the same order. What failed was the **attribution** — this design cannot say which field the effect comes from.

There is a research lesson here that I think matters more than the experiment:

> **A large effect is not an identified cause.**

Looking at 0.55, the natural impulse is to write "Jev weights X more heavily." But an experiment that moved two variables together cannot answer that question, however large the effect. Answering it needs no more calls — it needs a design that **separates the variables**, fixed before you see the data, or you will keep adjusting it until it says what you want to hear.

Equally important: **a null result must not be quietly retranslated into something friendlier.** For example:

- ✗ "Jev weighs both instructions and criteria." — This design cannot distinguish "both fields are doing work" from "a mixed-specificity construct is doing work." Those are different claims.
- ✗ "Criteria are what matter." — The data says the opposite, if anything: the `I` arm moved slightly further.

Two limits travel with the conclusion:

**`FIELD_ALIGNMENT_CAVEAT`**: the two crossed arms are "a wider field plus a narrower field," not two independently varying definitions. So the result describes the properties of **this mixed-specificity construction**, not where Jev "keeps" a decision boundary.

**n = 3 per arm**: three repeats support a median and a range. They **do not support any interval estimate**. So no confidence interval is reported — not because I didn't want one, but because the design cannot carry one.

The conclusion is what it literally says, with nothing added: **on this payload, at this sample size, under this design, the effect could not be attributed to a single field.**

---

## 11. The analyzer had a bug, and I wrote it into the record

After P3 I found a defect in the analyzer, and I left it in the repository in full.

Specifically: the preregistration defines GO-1 and GO-2 as **two independent conditions**. I wrote them as one merged test in the analyzer, so the pair `(GO-1 PASS, GO-2 FAIL)` **could not be represented in code at all**. And on this data, that pair is exactly what the preregistered rules compute: both single-field arms clear the GO-1 line (`I_med = 0.31`, `C_med = 0.36`, against a line of 0.475), but no assignment leaves a counterpart inside GO-2's vague baseline band. The defective analyzer reported GO-1 as FAIL and printed a line that contradicted the data.

Here is what I did:

- **Disclosed the defect at the commit that recorded the measurements**, right after the defective analyzer's freeze point — rather than waiting for someone else to find it.
- The repair was a **separate, later commit**. **No call was made or re-run during it.** The 12 records are byte-identical before and after.
- **No threshold and no rule changed.** The preregistration document is byte-identical to the freeze.
- The repaired analyzer **re-rendered the result document from the log, which never changed.**

The check that matters most: **the primary verdict from the original analyzer is identical to the corrected one.** The only thing that moved was the GO-1 flag, whose misreport never reached the verdict — because GO-1 alone never constituted a verdict. The frozen rule requires an arm clearing GO-1 **together with** a counterpart arm inside the GO-2 band, and no such pairing exists here. K1 is evaluated before the GO block, and it fired. So the defect got wrong **the display of the reasoning**, not the decision.

The point I want to make with this:

> **Preregistration cannot guarantee that your code is bug-free. Provenance can keep the repair of a bug from contaminating the measurement history.**

No number was re-measured and no record was rewritten. Someone arriving later can `git show` the pre-repair rendering, see the defect, the disclosure and the repair, and judge for themselves whether it holds together. **That is why the erroneous rendering is preserved in Git history instead of erased.**

One more thing, because it belongs to the same category. A line in the P1 audit said "42 of 42 Noul answers carry no `confidence` field." An independent check found the correct figure is **45 of 45** — 42 is the number of **records**, and the sentence was about **answers**; those 42 records hold 119 answers between them.

No conclusion changes (every Noul answer really does lack the field), but the number was wrong. I **did not edit P1's text**: it is a historical audit artifact, and editing it would leave a reader unable to tell which of its numbers have been touched. The correct value is in the [errata registry](../ERRATA.md), and P1 stands as written.

---

## 12. What is actually worth taking into engineering

Compressing 54 calls, these are the parts I think transfer.

### 1. Typed model output is not semantic truth

Passing schema validation ≠ being correct. All 42 of 42 responses here passed it, and **that establishes nothing** — no ground truth, no adversarial input, only format compliance on benign payloads. The weakest possible evidence for a type-safety claim.

### 2. Confidence is not a single-sample correctness oracle

The docs scope calibration to **a set** of predictions: confidence "describes the model's answer, not a guarantee that the answer is correct."

Locally, in `06_composite_scoring`, one dimension scored **1.62** on a 0–3 rubric at a confidence of **0.24** — and carried **97.4%** of the state's composite risk. The arithmetic was right, the confidence was low, and those are two different questions. A policy that reads low confidence as "wrong" and high confidence as "right" is reading the wrong number.

The boundary: **this project neither validated nor falsified Jev's calibration.** `04_confidence` has two cases; no reliability diagram, no ECE, no Brier score, no independent ground-truth dataset. Not in either direction.

### 3. Semantic routing and execution authorization should be separate layers

The most useful pattern I think came out of the project — and it came from a run that went **against** the design intent.

The model did its job: 4 of 4 correct functions, 4 of 4 correct arguments. Then the Python-side policy suppressed every one of them, and no handler was ever entered.

How the system should be written: **the model answers "what does this state mean," and code answers "are we allowed to act."** A system that reads "the model confidently picked a route" as "we may execute" has removed precisely the layer that produced this result.

The boundary: that **4 of 4** is **a count on synthetic cases, never a rate**. Every handler is inert. And **whether an allowed route would actually reach its handler under a real answer is something this project never observed** (`ACTUAL_HANDLER_EXECUTION_UNTESTED`). That limit is written down, not glossed over.

### 4. Batch economics are workload-dependent

Amortisation only shows up when the questions **share one state**. My 4.2647× belongs to one payload — not a property of Jev, not a general multiplier.

One counter-intuitive accounting note. In `05_speculative_fanout`, carrying both branches' follow-up questions in one request left 4 of 12 speculative answers unused, which looks like waste. But the arithmetic uses this product's price table: **Jev charges for input tokens and prices output tokens at zero**, and the unused answers are output tokens. The only billed side — input — came in **400 tokens lower**. So "paid for but never consumed" has no cost content here: a pricing frame sound one way inverts completely the other.

### 5. Keep the distribution, not just the label

Under byte-identical requests the label held 5 of 5 while the distribution underneath kept moving. Log only "which one was picked" and you cannot see that at all.

Once more, the boundary: **this is not our finding.** It is implied by the vendor's docs and was reproduced in public material at larger n. What is worth recording is a practice recommendation.

### 6. Evaluation infrastructure needs auditing too

This is the most valuable part of the project: canonical logs, derived artifacts regenerated from them, offline tests, an errata registry, hashes, freezes. **All of it gives "which numbers have been touched?" a mechanical answer** instead of an appeal to the author's credibility.

A concrete example. The log's `retry_count` field is **permanently `null`**: the SDK puts the retry count on the retried **request**, while the recorder reads the **response**. So `null` means "not reported", **never** "no retry happened." It was not backfilled and nobody reasons from it; it survives only so old lines stay readable. What works is `transport_attempt_count`, a locally counted number of outbound HTTP attempts — and even that supports one sentence: *this call was not observed to retry*, not "this is pure model inference latency."

---

## 13. Five experiments that were deleted

Before publishing, I retired **5 registered designs that were never run**, rather than executing them for completeness. They were all designed in good faith, and retired because they did not hold up. Two representative examples:

**`10_state_length`** — a fixed core of evidence padded with growing amounts of irrelevant filler. Three defects stacked: no independent ground truth ("correct" was my own reading of a bug report I wrote myself); **1** call per tier, which cannot separate context rot from random variation — and another of my experiments had already shown `Noul` moving on byte-identical payloads; and the "filler" was five sentences cycling on `index % 5`, so the "medium" and "longer" tiers differed by how often the same sentences repeated, **not by how much irrelevant content accumulated**. Repetition and accumulation are different manipulations: those tiers never varied the variable the experiment was named after.

**`11_language_pair`** — equivalent English and Chinese inputs. This retirement is the most instructive one, because the temptation to **keep** it was strongest: I and many readers are Chinese speakers, and a bilingual comparison would have looked good.

It had four independent problems: the arms were not equivalent (the English state has a customer wanting to reverse a duplicate charge, while the paired question asks about a refund — two different requests); language and phrasing were fully confounded (one wording per language, so any difference is "language × wording"); **1** call per arm; and the vendor docs had already answered the product-level question, stating that English is the primary training language and that other languages including CJK are accepted **but currently have lower accuracy**.

That last point is this project's rule doing its job: **"this result would be popular" is an argument about readers, not about design.** A confounded, underpowered design with ambiguous semantics does not become usable because of who its audience is.

**Not running a weak experiment is usually better than collecting another uninterpretable number.** Retiring an unrun design loses no evidence: a design is an intention, and deleting an intention is not discarding a result.

(This is also why there is no "registered but unrun" state here. Either it runs, or it is retired.)

---

## 14. What these experiments do not establish

Every "what we can say" should come with a "what we didn't." These are things this project **cannot establish** — not a "we'll get to it later" list: the evidence structure does not support them:

- **No general accuracy of any kind.** There is no ground truth anywhere in this bench. "4 of 4" is **a count on synthetic cases, never a rate**.
- **No validation or falsification of calibration, in either direction.** See §12.
- **No model latency benchmark, and no speedup claim.** Latency is recorded, but it is wall-clock around a bundle: DNS, TCP, TLS, connection-pool state, server queueing, upstream load, local scheduling. No arm is called "faster."
- **No general batching multiplier.** 4.2647× is a property of one payload.
- **No determinism verdict — in either direction.** Byte-identical requests returned differently shaped distributions, but that is a handful of repeats on two payloads, not a verdict; and nothing in the official material makes a determinism claim either way.
- **No broad hallucination benchmark.** The only axis measured here is **schema conformance on benign payloads**, with no adversarial attempt.
- **No production safety certification.** Every handler is inert; nothing wrote a file, sent a message, or produced a side effect.
- **No general conclusion about whether instructions or criteria matter more.** One payload, n = 3 per arm, and a null.
- **No NAS suitability conclusion.**

Two more that are not markers but bind just as much:

**No adjudication of vendor claims.** When an official number and a local number differ, this repository says they are **not commensurable** — not that the vendor is wrong, and not that the local run proves the vendor right. Vendor numbers are claims about their workload.

**Synthetic data boundary.** Every state is synthetic. There is no real personal, customer, or proprietary data anywhere in this repository.

---

## 15. NAS is a future question

I do plan, at some point, to evaluate whether Jev suits a NAS-class workload. But nothing here can support that direction: no NAS experiment, dataset or measurement exists in this repository, and among the five retired designs, the ones that might have touched search-adjacent behaviour were never run.

So there is one correct thing to say: **the next step, if I study whether Jev fits NAS, has to start from the structure of the NAS task and re-derive the measurement from there** — not start from "I've studied Jev, so let me find somewhere to apply it." **Having a hammer is not a reason to see a nail.**

---

## 16. Closing

Back to the opening question: if a model returns typed probabilistic answers instead of text, what does an agent become?

These 54 calls did not answer it. They did something smaller and earlier: they replaced "I think Jev is like this" with records someone else can check. The two prettiest effects, deleted because someone had been there first. The 0.55 that moved two variables together and therefore attributed nothing. An honest preregistered null, and an analyzer bug left in Git history in full.

At release, the repository's honest summary is this state string:

```
NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
```

**There is no Jev finding in this repository that is both new relative to TypeSafe's public material and supported by my own data.** Every large local effect either restates a documented behaviour or is an artifact of my own Python-side policy.

That is a good outcome. A repository built to test findings received a negative test result — it was doing its job, rather than accumulating trophies.

If you want to say something about this repository, [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md) sorts what may be said into three classes: what can be stated flatly, what must carry its scope, and what may not be said at all. **If you catch a sentence in this post that crosses it, that is not a wording problem. That is where the repository stops being worth citing.**

Evidence and reproduction paths:

- [`v0.1.0` evidence freeze](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) — cite the tag, not `main`
- [Evidence manifest](../evidence/v0.1.0/evidence-manifest.json) — SHA-256 for every frozen artifact, verified offline with one command
- [P1 — official claims audit](../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md)
- [P2 — novelty triage](../audits/P2_JEV_INSIGHT_TRIAGE.md)
- [P3 — boundary locus result](../audits/P3_BOUNDARY_LOCUS_RESULT.md)
- [P3 — preregistration](../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md)
- [Experiment registry](../experiments/EXPERIMENT_REGISTRY.md)
- [Errata](../ERRATA.md)

**License: MIT.** The code, both canonical logs and the derived reports are covered by the same license.

---

*One last note on what this project was for me. It was closer to a training exercise in model evaluation and agent engineering than a model benchmark. Most of what I learned was not on Jev's side.*
