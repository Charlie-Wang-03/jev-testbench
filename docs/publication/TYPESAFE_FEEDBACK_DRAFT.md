# TypeSafe documentation feedback — draft

**Status: DRAFT. Not sent. No message has been transmitted to TypeSafe or to anyone else.**

Four observations from the P2 triage were classified `V1_DOCUMENTATION_FEEDBACK`. None was ever
classified `V2_REPRODUCIBLE_BEHAVIOUR_REPORT` or `V3_POTENTIAL_PRODUCT_ISSUE`, and nothing found
since changes that. This file exists so that if the owner decides to send something, the wording is
already reviewable — not because sending is recommended.

**The framing all four share:** these are documentation-consistency observations from a dated
snapshot. None is a claim about model behaviour, none is a defect report, and each one is the kind of
thing a docs maintainer can act on in a few minutes.

---

## Why every item below is marked `NEEDS_FRESH_RECHECK_BEFORE_SEND`

The observations come from the frozen source snapshot in
[`TYPESAFE_OFFICIAL_SOURCES.md`](../sources/TYPESAFE_OFFICIAL_SOURCES.md), retrieved **2026-09-22**
and pinned by SHA-256. P5-C is not permitted to do fresh external research, so nothing here can be
confirmed as still true today.

Documentation drift of this kind is frequently fixed — that is what makes it worth reporting. Sending
a five-day-old observation without re-fetching would risk telling a docs team about something they
already corrected. **Every item carries the marker for that reason**, and re-fetching is cheap: four
URLs, no API key.

---

## V1-1 — Batching multiplier differs between two official surfaces

```
NEEDS_FRESH_RECHECK_BEFORE_SEND
```

| Source | ID | URL | Snapshot SHA-256 |
|---|---|---|---|
| Primitives — "Ask speculative questions" | `TS-DOC-PRIM` | `https://docs.typesafe.ai/primitives.md` | `130d9136a2f01497e72920a6e8d96073056d86d838ca13b8a505e4adb87651f6` |
| Cookbook: Parallel questions | `TS-DOC-CB-PAR` | `https://docs.typesafe.ai/cookbooks/parallel_questions.md` | `53dfe4516fd67b9bfc5abc9a50a6f4db6426b5b2951d41cd91e2fec45aded2fe` |
| Documentation index | `TS-IDX` | `https://docs.typesafe.ai/llms.txt` | `486685db6fec679ca3c7149f15b19c1ab069adbbc7a4b2369e80e5fc0f8caf64` |

**Observation.** `primitives.md` states that batching 13 questions into one call is "11.5x cheaper
and 9.6x faster" than 13 separate calls. The parallel-questions cookbook and the `llms.txt` summary
both state "12.2x cheaper and 10.0x faster" for the same comparison, and the cookbook's own table
(`$0.006090` vs `$0.000497`; `2.71s` vs `0.27s`) computes to 12.25x and 10.04x.

**Reading.** The cookbook is internally consistent; `primitives.md` is the outlier. This looks like a
derived summary that did not track the page it summarises.

**Not claimed:** nothing about model cost or speed. This is arithmetic on published figures, and the
only question it raises is which of two official pages carries the current number.

---

## V1-2 — Confidence thresholds differ between two pages for the same example

```
NEEDS_FRESH_RECHECK_BEFORE_SEND
```

| Source | ID | URL | Snapshot SHA-256 |
|---|---|---|---|
| Confidence | `TS-DOC-CONF` | `https://docs.typesafe.ai/confidence.md` | `97dafe98b77979906a2ad456013dd85a70dcecd109d0644b096817d910997ea5` |
| Confidence-gated routing | `TS-DOC-CONFROUTE` | `https://docs.typesafe.ai/patterns/confidence-routing.md` | `7a4de8d39a24c5d6b7e74b1b170fbbe101ca69419af39bac6da4e0c1f678b7bf` |

**Observation.** For the same worked example — a transfer approval — `confidence.md` uses
`confidence < 0.5` for genuine uncertainty and `confidence > 0.9` to execute, while
`confidence-routing.md` describes a "0.6 floor" and requires `> 0.85`.

**Reading.** Both pages state that thresholds are domain-specific and must be tuned, so this is a
difference in demonstration parameters rather than a contradiction. It is worth flagging only
because a reader skimming either page can mistake the constant for a product default.

**Not claimed:** no suggestion that either page is wrong, and no suggestion that a default exists.

---

## V1-3 — FAQ answers are not retrievable from the page payload

```
NEEDS_FRESH_RECHECK_BEFORE_SEND
```

| Source | ID | URL |
|---|---|---|
| Home page | `TS-SITE-HOME` | `https://typesafe.ai/` |
| Launch post | `TS-BLOG-INTRO` | `https://typesafe.ai/blog/introducing-system-one-models-and-jev` |

**Observation.** The FAQ **answers** on both pages are client-rendered and were not present in the
retrieved payload; only the question titles were recoverable — including "Is Jev deterministic?",
which is a question this repository would have liked to read the official answer to.

**Reading.** An accessibility and retrievability note for documentation consumers, including agents
that fetch pages as text. The question titles being visible while the answers are not is the part
that makes this worth a line.

**Not claimed:** nothing about intent. This is reported as a retrieval limitation of the pages as
fetched, not as the vendor withholding anything. Both pages render normally in a browser.

---

## V1-4 — Returned `probabilities` are 2-dp while `confidence` carries more precision

```
NEEDS_FRESH_RECHECK_BEFORE_SEND
```

| Source | ID | URL | Snapshot SHA-256 |
|---|---|---|---|
| Confidence | `TS-DOC-CONF` | `https://docs.typesafe.ai/confidence.md` | `97dafe98b77979906a2ad456013dd85a70dcecd109d0644b096817d910997ea5` |

**Observation.** The `probabilities` returned in an answer are a two-decimal-place representation,
while `confidence` evidently carries more precision. `confidence.md` says `confidence` is derived
from the probabilities and publishes the full `probabilities` precisely so that a user can substitute
their own statistic.

**Reading.** A note in the docs saying that a user-supplied statistic computed from the *returned*
distribution is approximate in a way the returned `confidence` is not would help — the two look
interchangeable and are not quite.

**Not claimed:** no invariant is violated and no official statement is contradicted. The docs call
their own published expression an approximation and never publish the production formula. This was
deliberately **not** classified as a product issue.

---

## What sending would require

1. **Re-fetch all four URLs** and confirm each drift still exists. Drop any that has been fixed.
2. **Re-check the claim contract** before quoting any local number in the message; the same
   [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md) that governs the blog
   governs this.
3. **Keep it to the observations.** No local measurement belongs in this message — none of the four
   items depends on one, and adding one would turn a docs note into a claim about the product.
4. **Send from the owner's own address**, as the owner's own message. P5-C does not send anything.

**Nothing has been sent. No draft has been transmitted, and no TypeSafe channel has been contacted.**
