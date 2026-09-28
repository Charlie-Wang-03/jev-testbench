# Style audit — the English article

**Audited document:** [`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md)
**Audit date:** 2026-09-28 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 3 — recomputed after the final human-read corrections. Seven corrections were applied,
rewriting seven lines: **eleven sentences were replaced by ten**, so the prose sentence count falls by one.
**Every check below still passes.** This revision also **states the counting method for the first time**
(§2.0), because revisions 1 and 2 reported figures whose method was never recorded and which no longer
reproduce. The figures below are therefore not a correction of an error in the article; they are the same
article counted by a method a reader can re-run. §2.0 says which numbers moved for that reason alone.

**Revision:** 2 — recomputed after the English editorial micro-pass. Seven wording corrections were applied
to the article; **every check below still passes, and no check was run differently to get that result.**
The counts that moved are named where they occur: `never` 22 → 21, `should` 3 → 2, sentences of six words
or fewer 95 → 94, and the collective forms now exist and are counted (§2.3). **Two of the seven
corrections removed short beats rather than adding them** — the question-and-answer pair in the retired-
experiment reflection became a single beat — which is the direction this audit prefers and is why §2.8's
numbers fell rather than rose.

---

## 1. Scope, and what is deliberately not here

This file checks **one thing: whether the English reads as English written by someone who had something
to say, rather than as a translation, a paper, a pitch, a CV, a rulebook, or a machine.** It exists
because the English article was adapted from the approved Chinese, and adaptation is the process most
likely to leave foreign rhythm behind.

**The framework is not rebuilt here.** The four-layer check, the over-stylization check and the
normative-tone check are defined in
[`…STYLE_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md) and apply
unchanged; what follows is their result on the English text plus the checks that only English needs.
**This is not a second style standard**, and where the two files differ in what they measure, it is
because the two languages fail differently, not because the bar moved.

**Not covered here:** whether any sentence is *permitted* (that is
[`…CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md)) and who is credited with what
(that is [`…PROCESS_ATTRIBUTION_AUDIT.en.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.en.md)).
A sentence can read beautifully and still be a claim defect.

---

## 2. The eight checks

### 2.0 How these numbers are counted

Added in revision 3, so that every figure below can be reproduced instead of taken on trust:

- A **prose paragraph** is a blank-line-separated block that is not a heading, a table row, a fenced
  block, a horizontal rule, or a list item.
- A **prose sentence** ends at `.`, `!` or `?` followed by whitespace. Inline code spans are masked to a
  single token and emphasis markers are removed first, so that a bolded sentence still ends where it
  reads as ending. A fragment with no terminal punctuation counts as one sentence.
- A **word** is a whitespace-separated token.
- A **run** is two or more consecutive sentences of six words or fewer, bounded by a longer sentence.

Marker counts (§2.6, §2.7) are **whole-file** counts taken with word boundaries and case-insensitively, and
are independent of the paragraph rule above. §2.4's word list is the one place a count is taken as a
**substring** rather than as a word, because the question there is whether the word appears at all; where
that changes the answer, the row says so. Where a raw match turns out to be a substring of a different word,
the match is shown and explained rather than quietly excluded — `here is` inside `there is`, `robust` inside
`robustness`.

**What this method is not.** It is not a standard, and it is not what revisions 1 and 2 used. Those
revisions reported 440 sentences and 192 paragraphs; the same article counts 438 and 207 here. Neither
pair is wrong, because a paragraph is a convention rather than a fact — but only one of them can be
re-run by a reader, and it is this one.

### 2.1 Natural English — **pass**

438 prose sentences across 207 paragraphs. Mean 13.4 words per sentence, median 12, shortest 1, longest
52. Mean paragraph 28.4 words, median 20.

The longest sentences (52, 41, 40, 39, 39 words) were read individually, because a long sentence is where
translation shows first. Every one of them is **a list or a colon-led enumeration, not a run-on** — a
five-part division of labour with a list of owner decisions after the colon, a set of figures with their
qualifiers, a chain of artifact types. That is a sentence that grew because it is itemising, which is what
English does when it itemises. **No sentence needed to be read twice to be parsed.**

### 2.2 Not a literal translation — **pass**

The calque patterns that survive Chinese-to-English translation were counted directly. **`the fact that`:
0. `in order to`: 0. `so as to`: 0. `due to the`: 0. `as for`: 0. `the reason is that`: 1.** No sentence
reproduces Chinese clause order with English words.

The rhythm evidence points the same way. A translated paragraph tends toward uniform mid-length sentences;
this one runs from 1 word to 52 with a median of 12, which is a distribution that comes from writing for
effect rather than transferring structure. The ten `It is …` constructions were checked one by one (§3) —
all ten are subject-first English, none is the translated `It is worth noting that` opener, and that
opener does not appear at all.

### 2.3 Not paper voice — **pass**

Searched for: *in this work, we propose, our contributions, it is worth noting, furthermore, moreover, in
conclusion, this paper, we present, prior work, state of the art, we show, we argue, we demonstrate, we
believe, it should be noted, it is important to note, in summary, we note that, this study.*

**Zero occurrences of all twenty.** The article argues in the first person of a working engineer, not the
first person plural of a manuscript. **It does contain seven collective forms — `we` six times, `our`
once, `us` never** — and none of them is the manuscript's `we`. Three are the project's own evidence
review (*the material we reviewed*, *the vendor material we reviewed*, *our public-material search*), which
names collective work this project did rather than the authorial `we` of a paper. One is a decision this
project made about its own analysis (*we did not treat n = 3 as enough*), added by the final read. One is
a phrase the article quotes in order to reject it (*"we failed to get a result"*). The last two are the
design-principle passage, one generic (*whether we are allowed to act*) and one quoted (*"we may
execute"*). **The manuscript `we` is the one that means "I, plus the reader's indulgence"; none of these
seven does.** *(Revision 2 counted five. The final read added the analysis decision above; the count of
six `we` is higher than the five forms revision 2 listed because that revision's list and its total did
not agree, and this one was recounted from the text.)*

### 2.4 Not marketing voice — **pass**

Searched for: *delve, leverage, unlock, paradigm, revolutionary, game-changing, seamless, robust,
cutting-edge, empower, supercharge, best-in-class, transform, synergy, ecosystem, holistic, world-class,
groundbreaking, effortless, turnkey.*

**Nineteen of the twenty occur zero times. The twentieth is a substring, not a use.** `robust` matches
once, inside **adversarial robustness** — the technical noun, in the sentence that says the 42-of-42 result
establishes no adversarial robustness. It was introduced by the final read and it is the opposite of a
product claim: the word appears in order to say what was *not* established. **Zero occurrences of the
twenty in their marketing sense.** The closest the article otherwise comes to a product claim is when it is
explicitly *refusing* one — the vendor's multipliers are named as the vendor's, and the local number is
called a measurement of one workload rather than a multiplier.

### 2.5 Not résumé voice — **pass**

`responsible for`: 1 occurrence, and it is `the person responsible for …` inside a sentence about what a
frozen manifest *cannot* prove. No ownership claims, no delivery verbs attached to the author, no list of
technologies as accomplishments. The AI-involvement disclosure in §16 is written as a description of a
process, not as a credit.

### 2.6 Not overly normative — **pass**

This is the check the Chinese audit answers with a three-question scan and the verdict `No material
normative overreach.` **The English reaches the same verdict by the same three questions.**

| Normative token | Count | What it is doing |
|---|---:|---|
| `never` | 19 | Five are the bench describing its own rules or its own instrument (*the two logs … are never merged*, *token counts … are never estimated*, *a derived report can never become a second source of truth*, *a log that never changed*, *GO-1 alone never constituted a verdict*); six say what something is **not** (*never an accuracy rate*, *never a rate*, *never findings about Jev*, *never "no retry happened"*, *never calibrated*, *never tuned on any data*); eight are observations about the data, the run or the design (*the handler was never entered*, twice; *the water underneath it never stopped moving*; *the data here never decomposed it*; *this project never observed*; *designs that had never been run*; *never varied the variable*; *was never run*). **None tells the reader what to do.** |
| `must` | 3 | Two are the bench's own rules (*derived artifacts must not drift*; the `I` and `C` arms *must* state the same boundary); one is inside a quoted requirement. |
| `should` | 2 | One is the word `should` inside prose about a design, one is a descriptive clause. **No reader-directed `should`.** *(Revision 1 counted three; the third was the self-directed question in the retired-experiment reflection, which the micro-pass rewrote as a statement of what happened.)* |
| `always` | 2 | One is *it is always `null`*, a fact about a log field; one is *the material we reviewed always presents the two together*, added by the final read and scoped to the material actually reviewed. |
| `required` | 1 | Inside a section heading, *Care was required here*, about the project's own process. |
| `have to` | 1 | Descriptive. |
| `guarantee` | 2 | Both are the article saying what **cannot** be guaranteed. |

**Not one of the 30 tokens issues an instruction to the reader.** The one place the Chinese audit found
material overreach — a sentence that told the reader not to modify the article in order to look busy — has
no counterpart here, because the work order's rule against `Nobody could change the thresholds` was applied
when the English was written: the preregistration is described as what it is, a dated record of what was
decided before the first call, not as a lock on anyone.

**Each pass over this article has removed these tokens rather than added them, with one exception.** The
micro-pass removed two — *The vendor never decomposed it* lost its `never` when it was narrowed to the
material actually reviewed, and the self-directed `should` disappeared with the question it belonged to.
The final read removed three more: `never` *taken apart*, `cannot carry one`, and the second-person clause
*until it says what you want to hear*. It added exactly one `always`, in the sentence that replaced
*It has never been taken apart*, where the global assertion became a statement about the material
reviewed. **No correction was made by rewording around a token**, which is the way this check can be
satisfied without being passed.

### 2.7 Not AI-sounding — **pass**

| Marker | Count | Reading |
|---|---:|---|
| em dash `—` | 44 | ~1 per 870 characters. Present, characteristic of the author's own Chinese voice, and not saturated. |
| semicolon `;` | 20 | Used to join two related clauses; not a tic. |
| `not just` | 1 | Line 51, and the sentence continues into a reason rather than a payoff. |
| `here is` / `here's` | 0 | A bordered count; the raw substring matches were all `there is` / `there are`. |
| `let's` / `let us` | 1 | **Inside quotation marks, and it is the only one.** The sentence is *No retry loops, no polling, no "let's add a few and see"* — the article quoting a habit in order to forbid it, matching 不允许「再补几次看看」 in the Chinese. **It is not the article addressing the reader in a companion register**, which is what this marker is for. *(Revision 1 reported 0. That was a miscount; the distinction between adopting a register and quoting one is the reason the count is taken with context rather than alone.)* |
| `it turns out`, `in other words`, `that said`, `at its core`, `the real question` | 0 each | None of the standard connective padding. |
| `exactly` | 9 | Used as a precision word (***exactly** one record*), not as emphasis. |
| `importantly` | 1 | *Most importantly, it cannot be placed beside the vendor's published multipliers* — a real caveat, not a crutch. **The count is of `importantly` only.** Revision 2 recorded this as 2 by folding in *the most important one*, which is a different word; the final read separates them, and `important` occurs once. |
| second person `you` | 10 | Down from 11. The one removed — *until it says what you want to hear* — went with the general advice it belonged to. The ten that remain are impersonal, in the way English uses *you* for *one*: describing how the API behaves (*You give it a `state`*; *when you print them at two decimal places*; *once you run them*), what an argument can be built on, and, once, the repository's own posture — *it cares whether you can still judge for yourself whether it made one*. **None issues an instruction.** The one that comes closest, *If you take one sentence out of this section, take this one*, is an offer about the article's own contents. |

The tell that is hardest to remove from machine-written prose is **the balanced antithesis** — *it is not X;
it is Y* used as a rhythm rather than an argument. The article does use that shape, in both languages, and
it is the author's Chinese voice rather than a machine's. It is not present often enough to become a
template: the shape appears where a claim is actually being corrected, and the corrections are different
claims.

### 2.8 Short beats not overstruck — **pass**

89 sentences (20.3%) are 6 words or shorter; 36 (8.2%) are 4 words or shorter. That is a deliberate voice,
and the risk in that voice is a drumbeat the reader stops hearing.

**The measured guard: no run of short sentences exceeds four, and there are thirteen runs in 438
sentences.** The longest is the one the article builds on purpose — *Each arm repeats 3 times. 12 calls in
total. Twelve calls. No extras.* — and the others of three are *Different wording. The same thing, already
in there. More decisive is the public material.* and *Then something more embarrassing happened. The
experiment was fine. The analyzer was not.* Every one of them is a landing, and each is followed
immediately by a longer sentence that explains something. **No paragraph is a sequence of fragments, and
no section is carried by rhythm alone.**

**Both later passes moved these numbers down, which is the right direction for this check.** The
micro-pass rewrote the retired-experiment reflection's question-and-answer pair into a single statement of
what the project did. The final read removed one more beat, *The answer is no.*'s successor in the same
paragraph, and did not replace it. **Beats removed, none added, and nothing was written to put a new
punchline where an old one had been.** The beats that survive sit between longer explanatory sentences, so
they land rather than accumulate — which is why the run count is thirteen and not higher.

---

## 3. The one construction that was checked line by line

`It is …` is the natural home of the paper-voice opener and the translated *it is worth noting that*, so all
ten instances were read rather than counted:

> It is that Jev does not really want to talk to you · It is where the second half of this project's
> subject comes from · It is not a general multiplier · It is also the expected mechanism · It is an
> arithmetic result · It is also not a finding about Jev · It is a real negative result · It is a bug · It
> is the weakest form of evidence available in support of a type-safety claim · It is not a term this
> project introduced to research, and it is not a measurable quantity

**Ten of ten are subject-first English with a concrete referent.** Eight carry a demonstrative or a
backward reference to the previous sentence, which is what the construction is for. None is an opener, and
none delays the subject to sound careful.

---

## 4. L1–L4, applied to the English

The same four layers the Chinese audit runs, with the English text as the object:

- **L1 — sentence and paragraph**: pass. Sentence length is varied deliberately; paragraph length is
  varied; no paragraph does two jobs.
- **L2 — section**: pass. Sixteen numbered sections plus an unnumbered intro and appendix, each with one
  job, and the section titles say what the job is. The two forward cross-references in the body (`the story
  is in §11`, `More on that in §8`) both resolve.
- **L3 — whole document**: pass. The narrative runs from an ordinary question, through three candidate
  experiments, a negative result, a broken analyzer, to what the project does and does not establish. The
  article does not change register halfway; it does not become a guide, a checklist or a manifesto in its
  final third.
- **L4 — the reader**: pass. Nothing requires internal stage numbering, an approval state, or a
  governance term to be understood. A developer who has never heard of this repository can read the whole
  piece; §7 is satisfied.

---

## 5. Verdict

| Check | Result |
|---|---|
| Natural English | **pass** |
| Not a literal translation | **pass** |
| Not paper voice | **pass** |
| Not marketing voice | **pass** |
| Not résumé voice | **pass** |
| Not overly normative | **pass** |
| Not AI-sounding | **pass** |
| Short beats not overstruck | **pass** |
| L1–L4 | **pass (4 of 4)** |

**`ENGLISH_STYLE = PASS`.**

**What this verdict is not.** It is the author's own reading, made with counts attached so that a reader
can disagree with a number instead of a taste. **It is not a human editorial review, and it does not
stand in for one** — the work order requires the English article to pass human editorial review as well,
and this file records only that it is ready to be put in front of one.
