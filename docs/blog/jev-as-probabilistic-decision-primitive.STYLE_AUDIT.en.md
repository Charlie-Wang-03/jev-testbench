# Style audit — the English article

**Audited document:** [`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md)
**Audit date:** 2026-09-28 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 1 — the first style pass over the English text.

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

### 2.1 Natural English — **pass**

440 prose sentences across 192 paragraphs. Mean 12.7 words per sentence, median 11, longest 45. Mean
paragraph 29.4 words, median 21.

The longest sentences (45, 42, 42 words) were read individually, because a long sentence is where
translation shows first. Every one of them is **a list, not a run-on** — a four-part division of labour, a
three-part summary of what a vendor page reports, a chain of artifact types. That is a sentence that grew
because it is enumerating, which is what English does when it enumerates. **No sentence needed to be read
twice to be parsed.**

### 2.2 Not a literal translation — **pass**

The calque patterns that survive Chinese-to-English translation were counted directly. **`the fact that`:
0. `in order to`: 0. `so as to`: 0. `due to the`: 0. `as for`: 0. `the reason is that`: 1.** No sentence
reproduces Chinese clause order with English words.

The rhythm evidence points the same way. A translated paragraph tends toward uniform mid-length sentences;
this one runs from 1 word to 45 with a median of 11, which is a distribution that comes from writing for
effect rather than transferring structure. The ten `It is …` constructions were checked one by one (§3) —
all ten are subject-first English, none is the translated `It is worth noting that` opener, and that
opener does not appear at all.

### 2.3 Not paper voice — **pass**

Searched for: *in this work, we propose, our contributions, it is worth noting, furthermore, moreover, in
conclusion, this paper, we present, prior work, state of the art, we show, we argue, we demonstrate, we
believe, it should be noted, it is important to note, in summary, we note that, this study.*

**Zero occurrences of all twenty.** The article argues in the first person of a working engineer, not the
first person plural of a manuscript. The only `we` in the piece is inside a design principle and inside a
phrase the article quotes in order to reject.

### 2.4 Not marketing voice — **pass**

Searched for: *delve, leverage, unlock, paradigm, revolutionary, game-changing, seamless, robust,
cutting-edge, empower, supercharge, best-in-class, transform, synergy, ecosystem, holistic, world-class,
groundbreaking, effortless, turnkey.*

**Zero occurrences of all twenty.** The closest the article comes to a product claim is when it is
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
| `never` | 22 | Nineteen are the bench describing its own rules — *token counts are never estimated*, *the handler was never entered*, *the vendor never decomposed it* — or a statement about the world. None tells the reader what to do. |
| `must` | 3 | Two are the bench's own rules (*derived artifacts must not drift*; the `I` and `C` arms *must* state the same boundary); one is inside a quoted requirement. |
| `should` | 3 | One is a question the article asks itself (*should it be run anyway to justify the sunk cost?*), one is the word `should` inside prose about a design, one is descriptive. **No reader-directed `should`.** |
| `always` | 1 | *it is always `null`* — a fact about a log field. |
| `required` | 1 | Inside a section heading, *Care was required here*, about the project's own process. |
| `have to` | 1 | Descriptive. |
| `guarantee` | 2 | Both are the article saying what **cannot** be guaranteed. |

**Not one of the 33 tokens issues an instruction to the reader.** The one place the Chinese audit found
material overreach — a sentence that told the reader not to modify the article in order to look busy — has
no counterpart here, because the work order's rule against `Nobody could change the thresholds` was applied
when the English was written: the preregistration is described as what it is, a dated record of what was
decided before the first call, not as a lock on anyone.

### 2.7 Not AI-sounding — **pass**

| Marker | Count | Reading |
|---|---:|---|
| em dash `—` | 44 | ~1 per 830 characters. Present, characteristic of the author's own Chinese voice, and not saturated. |
| semicolon `;` | 20 | Used to join two related clauses; not a tic. |
| `not just` | 1 | Line 51, and the sentence continues into a reason rather than a payoff. |
| `here is` / `here's` | 0 | The 11 matches for the substring were `there is` / `there are`. |
| `let's` / `let us` | 0 | No fake-companion register. |
| `it turns out`, `in other words`, `that said`, `at its core`, `the real question` | 0 each | None of the standard connective padding. |
| `exactly` | 9 | Used as a precision word (***exactly** one record*), not as emphasis. |
| `importantly` | 2 | One is `the most important one` inside a list of three; one is `Most importantly` opening a sentence that carries a real caveat. Not a crutch. |

The tell that is hardest to remove from machine-written prose is **the balanced antithesis** — *it is not X;
it is Y* used as a rhythm rather than an argument. The article does use that shape, in both languages, and
it is the author's Chinese voice rather than a machine's. It is not present often enough to become a
template: the shape appears where a claim is actually being corrected, and the corrections are different
claims.

### 2.8 Short beats not overstruck — **pass**

95 sentences (21.6%) are 6 words or shorter; 42 (9.5%) are 4 words or shorter. That is a deliberate voice,
and the risk in that voice is a drumbeat the reader stops hearing.

**The measured guard: no run of short sentences exceeds three, and there are fourteen runs in 440
sentences.** The longest — *Each arm repeats 3 times. Twelve calls. No extras.*, and *Then something more
embarrassing happened. The experiment was fine. The analyzer was not.* — are landings, and each is
followed immediately by a longer sentence that explains something. **No paragraph is a sequence of
fragments, and no section is carried by rhythm alone.**

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
