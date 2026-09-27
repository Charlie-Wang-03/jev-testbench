# After 54 Jev Calls: An Agentic Engineering Testbench and a Case of Cognitive Debt

**English** | [简体中文](jev-as-probabilistic-decision-primitive.zh-CN.md)

What caught my attention about Jev was not another benchmark result.

It is that Jev does not really want to talk to you.

No prose, no explanation. You ask it something, and it hands back a label and a probability table, and that is the entire reply.

The first question was an ordinary one. If a model is built for classify, route, score and gate, does that make an agent any easier to write?

So the plan was to measure it before answering that.

54 calls.

---

## 1. One minute of background

A Jev call has roughly this shape. You give it a `state`, plus a set of typed questions. It gives you back a set of typed answers. Every question in a request sees the same `state` and is evaluated independently — one question cannot see another's answer. That detail matters later.

There are three question types.

**Choice** is the most direct: give it a set of options and it returns the winner plus a probability distribution over them. Watch the display layer here. The probabilities the API returns are quantised, and when you print them at two decimal places, individual records do not add up to exactly 1. That is a display artefact, not distribution semantics: the distribution itself is still a probability distribution over the options.

**Score** is slightly less obvious. It does not pick one of 1, 2, 3 — the value can land between levels. The documented definition is the probability-weighted mean of the level numbers, and it comes with a `confidence`.

**Noul** is the simplest: a single number, P(yes).

Two things here were easy to confuse at first.

The first is that there is no free text in an answer. Across the 42 core records, **45 of 45** Noul answers carried no `confidence` field, while every Choice and Score answer had one. That 45 / 45 was written down incorrectly at one point; the story is in §11.

The second is that `probability` and `confidence` are not the same thing. `probability` is the distribution over the options; `confidence`, per the documentation, is a statistic computed from the returned distribution. They arrive side by side in the same answer, and they are two different numbers. The very first call ran into this: the winning option's probability was **0.45**, and the confidence on that same answer was **0.26**.

If you take one sentence out of this section, take this one: **a typed output solves the schema problem, not the semantic problem.** Being perfectly well-formed does not make an answer correct, and it certainly does not make it something to execute.

TypeSafe's own documentation is fairly blunt about this. Its known-limitations page lists literal reading, weak numeric representation, date comparison, indirection and large state one by one, and says outright that control flow belongs in code, with the model confined to narrow decisions. That is not a finding from here. The vendor published it.

---

## 2. A bench, not an opinion

Product documentation describes how a product is supposed to work. The distance between that and how it actually behaves is where the engineering cost lives.

But an impression that something is sometimes off is not something you can build on.

So the project's first move was to build a measurement bench called `jev-testbench`. Its goal was not to rate Jev and not to build a leaderboard. It had exactly one goal: **every conclusion has to be traceable to a log line.**

The bench was not typed out line by line by hand. The whole project was built the Agentic Engineering way — the human owner set direction and acceptance, ChatGPT did decomposition, planning and review, and Claude Code went into the repository to implement, change code, run experiments and write tests. The full account of that division of labour is in [Agentic Engineering and cognitive debt](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md), and this article comes back to it at the end, because it is not just a note about who did what. It is where the second half of this project's subject comes from.

Once the first round had run, a problem showed up immediately.

Writing the article at that point would have been easy, and it would have looked great.

Pick the two largest effects, draw a chart, and say Jev is stronger than the documentation claims in one place, or weaker in another.

If the evidence layer had not been separated out, that story would have been very easy to make plausible.

So the project went the other way and put a set of constraints on itself first.

The top one: any number the vendor publishes is a claim about **their** workload, not a measurement of this machine, this account, or these inputs. Only a record written by a real call into the canonical log counts as a local measurement. The core phase writes to `results/usage.jsonl`; P3 writes to its own `results/p3_boundary_locus/usage.jsonl`. The two logs are kept separate and never merged. And when writing, every sentence has to say which of the two it is reporting.

Then the log itself. One real call produces exactly one record, whether it succeeds or raises. A failed call is still data — nothing deleted, nothing reordered, nothing quietly fixed and written back. The two logs used here have SHA-256 `38e67630…` and `17f36f75…`, and neither has moved a byte since.

Model identity gets recorded too. The request asks for the alias `jev-latest`, but all 42 records came back as `jev-1.13.0`. An alias can drift; only the response says who actually answered. So both fields are recorded.

Token counts come from the API's `usage` values and are never estimated. Cost is derived from token usage and the price table — a local derivation, not a bill. Latency is end-to-end local wall-clock: it is a measurement, but it must not be read as a benchmark of the model's own inference latency.

One more: derived artifacts must not drift. Everything under `results/` other than the two canonical logs is regenerated from them. CI regenerates it, compares against the committed version, and fails on any difference. A derived report can never become a second source of truth.

And the most important one: **preregister, then call.** More on that in §8.

Somewhere in the middle of this, a realisation arrived. This repository was not only evaluating Jev. It was also evaluating something else: **what it takes to be entitled to draw a larger conclusion from one model's output.**

Most of the time, the answer was: not enough.

A word on cost, since it is worth knowing. Those 54 calls came to roughly **$0.001** by local estimate — a thousandth of a dollar. That is a local estimate, not a bill; TypeSafe Console billing is authoritative. The point of mentioning it is that the barrier to independently checking a model's behaviour is lower than most people assume.

---

## 3. What the first round actually measured

The first round registered ten experiments, ran all ten, and produced **42 core records**. Not in registration order, though — in order of how hard they were to take apart, starting with the prettiest number.

The first candidate was batching.

Put five questions that share one `state` into a single request, and two order-balanced cycles together consumed **816** input tokens. Split the same five questions into five independent requests, same two cycles, and they consumed **3,480**.

3,480 divided by 816 is **4.2647×**. A **76.55%** saving on input tokens.

And between the two arms, all **10 of 10** selected values were identical, with a largest absolute difference of **0.0**.

Beautiful.

But the boundaries travel with the number. This is a figure from **one payload**, where all five questions read the same `state` — which is precisely the condition the saving depends on. It came from **two order-balanced cycles in a single session**: not an average, and certainly not a distribution. It is not a general multiplier.

Most importantly, it cannot be placed beside the vendor's published multipliers. TypeSafe's `primitives.md` reports that 13 questions batched into one call are 11.5× cheaper and 9.6× faster than 13 separate calls; the parallel-questions page reports 12.2× and 10.0×. Those are different workloads — different question counts, different payloads, different denominators, different sessions. Putting "vendor: 12.2×" next to "local: 4.26×" and calling it "claimed vs. actual" is a category error.

The honest version is one sentence: **on this payload, the local measurement reproduced the shared-state amortisation the vendor describes.**

It is also the expected mechanism. Public third-party measurements went further on the same pattern — they varied batch size and published an accuracy curve against it. This experiment used one fixed payload from beginning to end.

So this one is a reproduction, not a discovery.

---

## 4. The second candidate, and the moving water

The second candidate was repeatability.

The same 512-token request went out five times, byte for byte. The winning Choice label did not change once: **5 of 5**.

Underneath that motionless label, the distribution was moving. The top-two margin shifted by up to **0.07**. `Score` landed between **1.58** and **1.63**, `confidence` between **0.24** and **0.30**, and one run produced an **exact tie** between the top two options.

The label looked rock solid. The water underneath it never stopped moving.

Of the four candidates, this one looked the most interesting.

Then the vendor's cookbook turned out to have it. TypeSafe's own documentation reports label flips on 2 of 8 questions, gives per-label probability standard deviations (mean **0.0098**, largest single label **0.0515**), and says plainly that when two labels are close, a small change can still flip the top label.

Different wording. The same thing, already in there.

More decisive is the public material. A public chaos-test report describes sending byte-identical requests to Jev five times and getting **0.03, 0.03, 0.03, 0.04, 0.04**, with jitter floors measured over roughly **1,490** captured calls.

So "repeat with byte-identical requests" was not an original design. Someone had already done it, with a larger sample and better statistics.

**An interesting observation is not a new finding.** What sits between the two is whether anyone got there first.

---

## 5. The shortest candidate, and the clearest lesson

The third candidate is the shortest, and the best one for showing what the problem actually is.

`04_confidence` contains a case deliberately designed to be ambiguous. It returned intent `other` with confidence **0.61**, while the demonstration threshold in the code was **0.60** — so the Python policy accepted it.

Written that way, it sounds like a model making a judgment call on a delicate boundary.

That reading does not hold.

The **0.60** is a constant in `experiments.py`, labelled in the code comments as a demonstration threshold — never calibrated, never tuned on any data, not claimed to be optimal. TypeSafe's own documentation uses both 0.5 and 0.6 for the same worked example on two different pages, and says outright that thresholds have to be tuned per domain.

Nor was the returned distribution anywhere near the boundary. **0.74 against 0.26**, a margin of **0.48**. That "ambiguity" was a property of the state design, not of the returned distribution. The published k=3 approximation, `(3 × 0.74 − 1) / 2`, reproduces **0.61** exactly. It is an arithmetic result.

0.61 being greater than or equal to 0.60 is the bench's own policy arithmetic, not a Jev finding. Move that constant and the conclusion changes, without a single model call taking place.

---

## 6. The candidate whose deletion is the most instructive

The fourth candidate has the most instructive deletion of the four, and it was the last one to go.

`12_function_routing` had the model route requests to a function registry frozen in advance. The model matched the expected function **4 of 4** times and the expected arguments **4 of 4** times.

Then all **4 of 4** were stopped by the Python-side policy and sent to `human_review`. The handler was never entered.

That is dangerously easy to write up as "the model would not act".

It is also not a finding about Jev.

All four interceptions trace back to `routing.py`. The route confidences were **0.76**, **0.58**, **0.72** and **1.0** against a floor of **0.8** — the first three were held only for falling below that line. The fourth, at 1.0, was held by `needs_human_review` at a threshold of **0.94** against **0.5**.

Right next to that constant there is a comment: `nothing in the docs says 0.8 is the right line`.

The router was declining to act, on the bench's own instructions. Jev did not produce unusable confidence.

Put the four candidates together and the pattern is uncomfortable: **the stories most suitable for a blog post were exactly the ones that most needed deleting.**

But they did not fail for the same reason, and that is worth separating. Batching and repeatability were demoted by official and public prior art — someone got there first, and did it more completely. The 0.61 threshold and the routing interceptions were not demoted by prior art at all. They were never findings about Jev; they are what this bench's own policy and thresholds necessarily produce once you run them.

No candidate was killed for being unattractive, and none was kept for being attractive.

---

## 7. Seven candidates, one question

Seven candidates went through adversarial review. One question was left worth following.

It survived not because the effect was large, but because it came with a specific, falsifiable unknown.

It came from `07_instruction_precision`. On a byte-identical **82-byte** `state`, the way the decision boundary was written was changed. With a vague boundary, a Noul returned **0.75**. With an explicit one, it returned **0.20**.

The same state bytes, a **0.55** difference on a 0-to-1 probability.

The effect is large enough to make you start writing immediately. It has two problems.

First, neither 0.75 nor 0.20 is ground truth. Neither arm is correct. They are two different numbers.

Second, and this is the decisive one: the two arms changed `instructions` and `criteria` **together**.

So this experiment cannot support any sentence of the following kind. It cannot say Jev weights criteria more heavily. It cannot say that changing the prompt wording alone produced the 0.55.

The only sentence available is this one: on this payload, moving both fields together from vague to explicit moved `Noul` by 0.55.

And that ran straight into a question the official documentation does not answer. TypeSafe's known-limitations page lists literal reading as its first failure mode, and its remedy is to state explicit conditions in `instructions` and write edge cases into `criteria`. The documentation also offers the line that `criteria` should be treated as an extension of `instructions`.

But it gives that as a bundle. It has never been taken apart.

**Is that boundary carried by `instructions`, or by `criteria`?**

The vendor never decomposed it. The data here never decomposed it — both fields moved together. And nothing in the public material turned up a controlled attribution experiment.

So: which field was actually doing the work?

That became the one question that passed review and was worth spending more calls on.

One aside. The public-novelty check for that question came back `PUBLIC_NOVELTY_UNRESOLVED`. Recorded as *unresolved*, not as *nobody has done it*. Those are not the same statement.

---

## 8. Care was required here

At this point there was a large 0.55 effect, a question that sounded good, and a complete set of freedoms that would have made it easy to tell the story smoothly.

So the replication got its own preregistration — the project called it P3 — and before the first request went out, the design, the order, the statistics and every threshold were written down and committed.

The design is a 2×2 that crosses the two fields:

| Arm | `instructions` | `criteria` |
|---|---|---|
| `N` | vague | vague |
| `I` | explicit | vague |
| `C` | vague | explicit |
| `B` | explicit | explicit |

Each arm repeats **3** times.

**12** calls in total.

Twelve calls. No extras.

That is a hard ceiling written into the preregistration. No retry loops, no polling, no "let's add a few and see."

The order was fixed in advance as well: `N1 → I1 → C1 → B1 → B2 → C2 → I2 → N2 → C3 → N3 → B3 → I3`, balanced at both ends and in the middle.

The preregistration also records a design hazard that matters more than the thresholds. The `I` and `C` arms must state **the same** boundary, differing only in where it is written. If an arm makes `instructions` and `criteria` contradict each other, it triggers another failure mode the vendor documents, and that arm is a protocol violation rather than a data point.

The `N` and `B` endpoint arms are three-repeat versions of the original `07` arms. Their job is diagnostic — to check whether the original effect is still there this time. They were frozen before the first request, exactly like the thresholds.

Those thresholds were fixed before the first request went out. Changing them later would have changed the analysis too — it would no longer have been the preregistered experiment.

The decisive KILL condition reads like this:

```
K1:  |I_med − C_med| < 0.1   →  attribution fails
```

---

## 9. P3's raw results

All twelve calls succeeded.

Every raw value is listed below. The medians summarise them; they do not replace them.

| Arm | Raw `Noul` values | Median | Range |
|---|---|---:|---:|
| `N` (both vague) | 0.77, 0.76, 0.75 | 0.76 | 0.02 |
| `I` (instructions only) | 0.31, 0.33, 0.29 | **0.31** | 0.04 |
| `C` (criteria only) | 0.37, 0.36, 0.33 | **0.36** | 0.04 |
| `B` (both explicit) | 0.20, 0.21, 0.20 | 0.20 | 0.01 |

The endpoint replication worked. The original `07` observation moved 0.75 to 0.20, a shift of 0.55; this run produced an `N` median of **0.76** and a `B` median of **0.20**, a gap of **0.56**, at three repeats per arm on the same payload. The ordering held, and so did the magnitude.

And looking at this, an impulse is very easy to have.

`I` is lower than `C`. Does that mean `instructions` matter more?

That reading does not work, because a K1 was written down before the data existed.

What actually happened is in the two single-field arms: both moved most of the way toward the explicit baseline. `I`'s median of 0.31 is 0.45 below `N`'s 0.76 — **80.4%** of this run's 0.56 endpoint gap. `C`'s median of 0.36 is 0.40 below — **71.4%**.

And between the two single-field arms there is only **0.05**.

```
|I − C| = 0.05
threshold = 0.10
```

0.05 is less than 0.10. K1 fired.

Under the preregistered rule, the conclusion is that **under this design and this sample size, the original effect cannot be attributed to either `instructions` or `criteria` alone.**

```
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
```

About those two percentages, 80.4% and 71.4%, one thing has to be said clearly. They are descriptive arithmetic on the medians above, not part of the decision rule. No threshold was derived from them, and ignoring them entirely would not change a single word of the verdict.

---

## 10. A large effect is not an identified cause

What P3 produced is not "we failed to get a result". It is a real negative result.

The experiment did not fail. The original large effect **replicated**: the 0.55 move reappeared as a 0.56 gap, with the endpoints in the same order. What failed was the **attribution**. This design cannot say which field the effect comes from.

**A large effect is not the same thing as an identified cause.**

Looking at 0.55, the natural impulse is to write "Jev weights X more heavily" immediately. But an experiment that changed two variables together cannot answer that question, however large the effect. Answering it needs no additional calls — it needs a design that pulls the variables apart. And that design has to be settled before the data is seen, or the temptation is to keep adjusting it until it says what you want to hear.

Nor can a null result be quietly translated into something friendlier.

It cannot be said that "Jev weights both `instructions` and `criteria`". This design cannot distinguish "both fields are doing work" from "a mixed-specificity construct is doing work". Those are different things.

It also cannot be said that "`criteria` are the key". The data says the opposite, if anything: the `I` arm moved a little further.

Two further limits are load-bearing and travel with the conclusion.

`FIELD_ALIGNMENT_CAVEAT`. The two crossed arms are a wider field plus a narrower field, not two independently varying definitions. So this result describes the properties of this mixed-specificity construction — not where Jev actually stores a decision boundary.

n = 3. Three repeats support a median and a range. They do not support any interval estimate. That is why no confidence interval is reported here: not because one was unwanted, but because this design cannot carry one.

The conclusion is what it literally says, with nothing added. On this payload, at this sample size, under this design, the effect cannot be attributed to a single field.

That KILL condition was written before the data, and it was genuinely executed. That is the one thing preregistration can actually deliver.

---

## 11. The analyzer was broken

Then something more embarrassing happened.

The experiment was fine.

The analyzer was not.

In the preregistration, GO-1 and GO-2 are two independent conditions. The analyzer wrote them as a single merged test, which made the pair `(GO-1 PASS, GO-2 FAIL)` impossible to represent in code at all. And on this data, that pair is exactly what the preregistered rules compute: both single-field arms clear the GO-1 line (`I_med = 0.31`, `C_med = 0.36`, against a line of 0.475), and no assignment leaves a counterpart inside GO-2's vague baseline band. The defective analyzer reported GO-1 as FAIL and printed a line that contradicted the data.

The defect was disclosed in the commit that recorded the measurements, right after the defective analyzer's freeze point — it did not wait for someone else to find it. The repair was a separate, later commit. **No call was made, and no call was re-run.** The 12 records are byte-identical before and after. No threshold and no rule changed; the preregistration document is byte-identical to its frozen state. The repaired analyzer re-rendered the result document from a log that never changed.

The check that matters most is this one: **the primary verdict computed by the original analyzer is identical to the corrected one.**

Why? Because GO-1 alone never constituted a verdict. The frozen rule requires an arm clearing GO-1 together with a counterpart arm sitting inside the GO-2 band, and this data contains no such pairing. K1 is evaluated before the GO block, and it fired.

So what the defect got wrong was **the display of the reasoning, not the decision**.

This is not going to be written as a hero narrative. It is a bug. It was found, it was recorded, and it was not turned into a re-run that would have made things look better.

Preregistration cannot guarantee that the code has no bugs. But provenance can keep a bug's repair from contaminating the measurement history.

Someone arriving later can `git show` the pre-repair rendering, see the defect, see the disclosure, see the repair, and judge for themselves whether it holds together. That is why the bad rendering was preserved in Git history instead of being erased.

And it was not the only one.

A line in the P1 audit said that 42 of 42 Noul answers carried no `confidence` field.

An independent check found that the correct number is **45 of 45**.

Why?

Because records and answers had been mixed up. 42 is the number of records; the sentence was about answers; and those 42 records hold **119** answers between them.

No conclusion changed — every Noul answer really does lack that field. But the number was wrong.

P1's text was not edited, because it is a historical audit artifact. Edit it, and a reader can no longer tell which of its numbers have been touched. The correct value lives in the [errata registry](../ERRATA.md), and P1 stands as written.

Put those two stories together and they say the same thing. **This repository does not care whether it looks like it made a mistake. It cares whether you can still judge for yourself whether it made one.**

---

## 12. Three things worth carrying elsewhere

After all of that, three items were left that transfer to other work.

The first is about typed output. Passing schema validation is not the same as being correct. All 42 of 42 responses passed validation, and that establishes nothing at all: no ground truth, no adversarial input, only format compliance on benign payloads. It is the weakest form of evidence available in support of a type-safety claim.

Connected to it is `confidence`. The official documentation scopes calibration to a set of predictions, and says plainly that confidence describes the model's answer, not a guarantee that the answer is correct. There is a sharper local example. In `06_composite_scoring`, one dimension scored **1.62** on a 0-to-3 rubric at a confidence of only **0.24**, while carrying **97.4%** of that state's composite risk. The arithmetic was right, the confidence was low, and they are simply two different questions. A policy that reads low confidence as "the answer is wrong" and high confidence as "the answer is right" is reading the wrong number.

The boundary has to be stated here. This project neither validated nor falsified Jev's calibration. `04_confidence` has two cases, no reliability diagram, no ECE, no Brier score, no independent ground-truth dataset. Not in either direction.

The second is that semantic routing and execution authorization belong in separate layers. This is the most useful pattern the project produced, and it came out of a run that went against the design's intent. The model did the work well — 4 of 4 correct functions, 4 of 4 correct arguments — and then the Python-side policy stopped every one of them, and the handler was never entered.

The system answers two different questions in two different places. The model answers what this state means; the code answers whether we are allowed to act. A system that reads "the model confidently picked a route" as "we may execute" has removed exactly the layer that produced this result.

The boundary again: that 4 of 4 is a count on synthetic cases, never an accuracy rate. Every handler is inert — nothing wrote a file, sent a message, or produced a real side effect. And whether an allowed route would actually reach its handler under a real answer is something this project never observed (`ACTUAL_HANDLER_EXECUTION_UNTESTED`). That limit is written down.

The third is less an engineering recommendation than a discipline. **Evaluation infrastructure needs auditing too, and that turned out to be the most valuable part of this project.** Canonical logs, derived artifacts regenerated from them, offline tests, an errata registry, hashes, freezes — all of it exists so that "which numbers have been touched?" has a mechanical answer instead of an appeal to the author's credibility.

A concrete example. The log has a `retry_count` field, and it is always `null`. The reason is that the SDK writes the retry count onto the retried **request**, while the recorder reads the **response**. So `null` means "not reported" and never "no retry happened". The field was not backfilled and nobody reasons from it; it stays there only so that old lines remain readable. What does work is `transport_attempt_count`, a locally counted number of outbound HTTP attempts. And even that supports exactly one sentence — this call was not observed to retry — not "this is pure model inference latency".

---

## 13. Five experiments that were deleted

One more thing that was done the hard way.

Before public release, five registered designs that had never been run were all retired, rather than executed for the sake of completeness.

They had all been designed in good faith. They were retired because they did not hold up. Two examples.

`10_state_length` loaded a fixed core of evidence with growing amounts of unrelated filler text. Three defects stacked on top of each other. There was no independent ground truth — the "correct" answer was a reading of a synthetic bug report written by the project itself. Each length tier had **1** call, which cannot separate context rot from random variation, and another experiment in the same project had already shown `Noul` moving on byte-identical payloads. And the filler paragraphs were actually five sentences cycling on `index % 5`, so the difference between the "medium" and "longer" tiers was how many times the same five sentences repeated, not how much unrelated content had accumulated. Repetition and accumulation are different manipulations, which means those two tiers never varied the variable the experiment was named after.

`11_language_pair` was equivalent English and Chinese inputs. This retirement is the one most worth reading, because the temptation to keep it was the strongest. A large share of readers are Chinese speakers, and a bilingual comparison would have looked good.

It had four independent problems. The two arms were not semantically equivalent — the English state has a customer wanting to reverse a duplicate charge, while the paired question asks whether to issue a refund, which are two different requests. Language and phrasing were completely confounded, with one wording per language, so any difference is language times phrasing. Each arm had **1** call. And the official documentation had already answered the product-level question, stating directly that English is the primary training language and that other languages, including CJK, are accepted but currently less accurate.

That last point is the project's own rule doing its job. "This result would be popular" is an argument about readers, not an argument about design. A confounded, underpowered design with ambiguous semantics does not become usable because of who its audience is.

When an experiment's code is already written, should it be run anyway to justify the sunk cost?

The answer is no.

Not running a bad experiment is usually better than getting a number you cannot interpret. Retiring a never-run design loses no evidence. A design that was never run is only an intention, and deleting an intention is not the same as discarding a result.

(Which is also why this repository has no "registered but unrun" state. It either runs, or it is retired.)

---

## 14. What these experiments do not establish

This section is not a set of caveats to be added later. The evidence structure does not support these statements, and that is a property of the design rather than of the write-up.

**No general accuracy.** There is no ground truth anywhere in this bench. "4 of 4" is a count on synthetic cases, never a rate.

**No validation or falsification of calibration**, in either direction.

**No model latency benchmark, and no speedup conclusion.** Latency was recorded, but it wraps an entire bundle: DNS, TCP, TLS, connection-pool state, server queueing, upstream load, local scheduling. No arm is called faster.

**No general batching multiplier.** 4.2647× is a property of one payload.

**No determinism verdict, in either direction.** Byte-identical requests returned differently shaped distributions, but that is a handful of repeats on two payloads, which is not enough to be a verdict.

A few more, briefly. There is no broad hallucination benchmark here; the only axis measured is schema conformance on benign payloads. There is no production-safety certification; every handler is inert. And there is no general conclusion about whether `instructions` or `criteria` matter more.

Two more that are not markers but bind just as much.

**No adjudication of vendor claims.** When an official number and a local number differ, this repository says they are not commensurable — not that the vendor is wrong, and not that the local run proves the vendor right. Vendor numbers are claims about their workload.

**All state is synthetic.** There is no real personal, customer, or proprietary data anywhere in this repository.

The full list is in [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md) and the freeze documents. Only the ones most likely to be misread are repeated here.

---

## 15. Back to the beginning

The point of all this was to see what Jev was actually good for.

After 54 calls, most of the prettiest stories did not survive.

That outcome is better than expected.

What this repository actually accumulated, it turned out, was not stories.

It was the ability to delete them.

The most honest summary it can offer is a single state string:

```
NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
```

There is no Jev finding here that is both new relative to TypeSafe's public material and supported by this project's own data. Every large local effect either restates a behaviour the vendor has already documented, or is an artefact of this bench's own Python-side policy.

That is a good result. A repository built to test findings received a negative test result, which means it was doing what it was built for rather than accumulating trophies.

About Jev, this conclusion is willing to sign its name.

But there was one more story to delete.

---

## 16. The last story

That story is about the project itself.

It goes like this. This was a project that its owner fully understood and built by hand.

No.

Most of the implementation was done by AI agents — writing code, changing tests, making those 12 calls, repairing the analyzer, maintaining the documentation. ChatGPT's part was mainly problem decomposition, stage planning, evidence review and writing supervision. Claude Code's part was mainly going into the repository and implementing: code changes, tests, actually executing the Jev calls, and the drafts and structural rewrites of this article. The owner's part was a different kind of action altogether: deciding what question the project should answer, deciding what each stage would and would not do, approving or rejecting key steps, and making the calls that only an owner can make — the license, retiring experiments, the article's style, and renaming the project.

Writing "I ran 54 calls" would be an inaccurate sentence. The calls themselves were primarily executed by the agent.

This is not a gotcha. The production relationship behind this article is itself part of the project's meta-level experiment, which is why it is written into the body of the text rather than hidden in a footnote.

Looking at that division of labour, a more uncomfortable question surfaces.

If an agent pushes implementation forward much faster than the owner can absorb that work, those two curves diverge.

In this project they did diverge. It ran 10 registered experiments, recorded 54 calls, froze a release, and left behind several audits, a preregistration and a frozen evidence set. Every one of those things is real, running and mechanically checkable. But the range of what the owner can independently explain, independently verify and independently modify did not expand at the same rate.

That gap has a working name.

```
cognitive debt
≈
implemented / automated / recorded project complexity
−
complexity the owner can independently explain / verify / modify
```

This is only a working concept. It is not a term this project introduced to research, and it is not a measurable quantity. It has no units, no instrument, and no value anywhere in this repository; those lines are there to point at a shape.

What this project does about it is externalise it. Canonical logs, preregistration, claim audits, an errata registry, an evidence freeze, offline tests. Those things are real and they work: they preserve facts, constrain narratives, and support later reconstruction, so that a person a year from now — including the owner — can walk back through them.

But they do not automatically become human understanding.

A passing test is a fact about an artifact, not a fact about the person who delivered it. A frozen manifest can prove that a set of bytes did not move; it cannot prove that the maintainer can still independently explain, verify or rebuild those bytes. These mechanisms make it harder to say false things, but they do not automatically give the maintainer the ability to independently explain and verify those facts. The whole set of external mechanisms, and the part it is not responsible for, is written up in [Agentic Engineering and cognitive debt](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md).

There is a metaphor for this.

Give a gorilla a machine gun and its ability to act goes up dramatically.

But firepower is not understanding. Exploring fire is useful; playing with fire is dangerous; and fire does not automatically turn the ape into a human.

On the surface, `jev-testbench` is a testbench for Jev.

At another level, it has also been testing its owner.

This article is the first payment on that debt, not proof that the debt is gone.

---

Evidence and reproduction

- [`v0.1.0` evidence freeze](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) — cite the tag, not `main`
- [Evidence manifest](../evidence/v0.1.0/evidence-manifest.json) — SHA-256 for every frozen artifact, verified offline with one command
- [P1 — official claims audit](../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md)
- [P2 — novelty triage](../audits/P2_JEV_INSIGHT_TRIAGE.md)
- [P3 — boundary locus result](../audits/P3_BOUNDARY_LOCUS_RESULT.md)
- [P3 — preregistration](../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md)
- [Experiment registry](../experiments/EXPERIMENT_REGISTRY.md)
- [Errata](../ERRATA.md)
- [Agentic Engineering and cognitive debt](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md)

The project is under the MIT License. See [`LICENSE`](../../LICENSE).
