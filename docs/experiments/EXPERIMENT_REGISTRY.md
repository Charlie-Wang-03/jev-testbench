# Experiment registry — current state

**This file describes the registry at the public-release revision, not the history of it.** The
historical audits are [`docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md`](../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md)
and [`docs/audits/P2_JEV_INSIGHT_TRIAGE.md`](../audits/P2_JEV_INSIGHT_TRIAGE.md), which record what
was true when they were written and have not been edited to match this page.

There are exactly two categories, and no third:

| Category | Meaning |
|---|---|
| **Executed / evidence-bearing** | In `EXPERIMENTS`, in `src/jev_lab/experiments.py`, and has at least one canonical record. |
| **Retired before public release** | Not in `EXPERIMENTS`. Its code is in git history. It will never produce a record. |

**There is no "registered but not run" category.** A design that is registered and has no record is
an intention, and an intention is not evidence — it cannot be cited, it cannot be audited, and it
cannot be the reason a reader trusts anything else here. The registry therefore either runs a design
or retires it.

The invariant that follows is asserted mechanically, not in prose:
`tests/test_final_report.py::TestTheCanonicalLog::test_the_shipped_registry_has_no_unrun_experiment`
computes the registry-minus-log difference and requires it to be empty.

> `ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS`

---

## Executed / evidence-bearing

Ten experiments, all ten with canonical records in [`results/usage.jsonl`](../../results/usage.jsonl).
Call counts below are the declared **ceilings**; `05` reaches 6 because its control flow can branch.

### `core` — the foundational mechanics

| Experiment | Calls | Records | What it measures |
|---|---|---|---|
| `01_primitives` | 1 | 1 | `Choice` + `Score` + `Noul` in one request against one state. |
| `02_structured_addressing` | 2 | 2 | Field-path addressing over structured state vs. described addressing over prose. |
| `03_parallel_questions` | 12 | 12 | One batched request vs. the same questions sent separately, in two order-balanced cycles. |
| `04_confidence` | 2 | 2 | Specific vs. ambiguous evidence, gated in code on confidence alone. |

### `extended` — specific behaviours and documented limits

| Experiment | Calls | Records | What it measures |
|---|---|---|---|
| `05_speculative_fanout` | 6 | 6 | One request carrying both branches' follow-ups vs. a second request staged on the first answer. |
| `06_composite_scoring` | 3 | 3 | Four atomic `Score` questions composed into one risk in Python, weights frozen before the run. |
| `07_instruction_precision` | 2 | 2 | Vague vs. explicit decision boundaries on a byte-identical state. |
| `12_function_routing` | 4 | 4 | Route to a name in a registry frozen before the run, then to a closed-set argument. |
| `13_repeatability` | 5 | 5 | One byte-identical request sent five times. |
| `13b_ambiguous_repeatability` | 5 | 5 | A payload known to land mid-scale, sent five times. |

**Not in this registry, by design:** P3 (`src/jev_lab/p3_boundary_locus.py`). It is a preregistered
replication with its own log, its own entry point and its own result document. It is excluded so
that it cannot be reached by `run-all`. Its twelve records are in
[`results/p3_boundary_locus/usage.jsonl`](../../results/p3_boundary_locus/usage.jsonl).

---

## Retired before public release

Five designs were registered and never run. Each was reviewed against the same six questions before
publication, and each was retired. The retired designs were all introduced in the P0 freeze commit
[`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) and removed from the active
registry at the P3.6 release-closure commit; `git log --follow -- src/jev_lab/experiments.py`
recovers the full text of each.

The rubric applied to all five:

1. **Information gain** — can it tell us something the P0–P3 records and TypeSafe's official
   documentation have not already answered?
2. **Public value** — would a real run materially improve a developer-facing writeup, rather than
   add a few lines to a JSONL file?
3. **Design validity** — can the current design separate the target variable from its main
   confound?
4. **Interpretability** — is there a pre-defined conclusion that does not have to be explained
   after the fact?
5. **Maintenance cost** — is this worth supporting and explaining in a long-lived public repository?
6. **Redundancy** — have the official docs, another local experiment, or ordinary metadata already
   covered its main value?

### `00_model_info` — `DELETE_FROM_ACTIVE_REGISTRY`

| | |
|---|---|
| Former purpose | List accessible models and record which versioned ID each alias resolves to. |
| Tier / calls | `core` / 2 |
| Historical source | [`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) |

**Why retired.** The alias-to-version resolution it exists to record is *already in every record of
the canonical log*. All 42 records carry `model_requested = "jev-latest"` and
`model_resolved = "jev-1.13.0"`; the twelve P3 records carry `jev-1.13.0` on both sides. That is
the same fact, measured 54 times, as a by-product of calls that produced other evidence. Spending
two dedicated calls would add exactly one datum — `jev-preview` — which `TS-DOC-MODELS` already
states resolves to `jev-1.13.0`, and which is a transient property: aliases move, and the models
page says so. A resolution recorded today is stale the moment the alias moves.

The strongest argument for keeping it was that it is cheap and it is the only design that would
record `jev-preview` locally. That is real, but it buys a number whose entire value is that it is
current, which is the one property a frozen log cannot hold.

### `08_literal_reading` — `DELETE_FROM_ACTIVE_REGISTRY`

| | |
|---|---|
| Former purpose | Negation, implied conditions, and scope, following the documented jaggedness page. |
| Tier / calls | `extended` / 4 |
| Historical source | [`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) |

**Why retired.** `TS-DOC-JAG` is a vendor-published known-limitations page that already names
literal reading, indirection and double negatives explicitly, scoped to `jev-1.13`. Four
single-draw toy probes cannot add to, refine or falsify that. The design also has no repeat, so it
cannot separate a systematic failure mode from one sampling draw — a distinction this repository's
own `13b_ambiguous_repeatability` shows is material, since a `Noul` moved run-to-run on a
byte-identical payload. Two of the four cases are weaker still: `implied_condition` asks Jev to do
weekday arithmetic, which the repository's own rules say belongs in code, and the case's own note
admits it.

The strongest argument for keeping it was that negation and scope failures are the kind of error a
developer actually ships, so a local observation would be concrete and useful. True — but a concrete
observation of a documented failure mode, at n=1, with no pre-registered interpretation, is a
demonstration. Retiring it removes no evidence, because it produced none.

### `09_numeric_limits` — `DELETE_FROM_ACTIVE_REGISTRY`

| | |
|---|---|
| Former purpose | A tiny demonstration of the documented counting and arithmetic limits. |
| Tier / calls | `extended` / 3 |
| Historical source | [`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) |

**Why retired.** The design cannot falsify anything, and its own docstring says so: *"the docs
already state the limitation and repeating it at scale would burn budget to learn something already
known."* Each case already carries its correct code-side answer, computed locally — `state.count('risk') == 2`,
`1240.00 > 1000.00`. Running Jev would change no action anyone takes, because the recommended action
is already to do the arithmetic in Python.

There is a sharper problem than redundancy. The `counting_fruits` case sends **eight** `Noul`
questions — one per item — in a single request. That is precisely the workaround `TS-DOC-JAG`
recommends ("one question per item"), so even a correct result would not test the counting
limitation; it would demonstrate the workaround. The probe as written cannot reach the behaviour it
names.

### `10_state_length` — `DELETE_FROM_ACTIVE_REGISTRY`

| | |
|---|---|
| Former purpose | Fixed core evidence with growing irrelevant filler. |
| Tier / calls | `extended` / 3 |
| Historical source | [`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) |

**Why retired.** Three defects compound into a design that cannot support a length claim.

- **No independent ground truth.** The "correct" answers are this repository's own reading of a
  synthetic bug report it wrote itself. A change between tiers has no external referent.
- **n = 1 per tier.** One draw per tier cannot separate context rot from the run-to-run variation
  `13b` already measured on an *identical* payload.
- **The filler is not what it claims to be.** `FILLER_PARAGRAPHS` holds five sentences and `_pad`
  cycles them with `index % 5`. The "medium" and "longer" tiers therefore differ in how many times
  the *same* five sentences repeat, not in how much unrelated content accumulates. Repetition and
  accumulation are different manipulations, so the tiers do not vary the construct the experiment
  is named for.

Fixing all three means designing a real context-length study with a ground-truth set, multiple
draws per tier and genuinely varied filler. That is a new research programme, not a release-closure
task, and running the current design instead would invite a README claim the design cannot carry.

### `11_language_pair` — `DELETE_FROM_ACTIVE_REGISTRY`

| | |
|---|---|
| Former purpose | Equivalent English and Chinese input and questions. |
| Tier / calls | `extended` / 2 |
| Historical source | [`e20fad5`](https://github.com/Charlie-Wang-03/jev-test/commit/e20fad5) |

This is the one worth reading in full, because it is the case where the pull to keep an experiment
is strongest and least related to its evidence.

**Why retired — four independent reasons.**

1. **The two arms are not the semantic equivalents the design claims.** The English state says the
   customer "wants the duplicate charge removed", and the paired question asks "Is the customer
   asking for a refund?" Those are different propositions: removing a duplicate charge and issuing
   a refund are different remedies. The Chinese pair mirrors the same ambiguity rather than
   resolving it. So the expected answer is contestable in both arms, and a disagreement between
   them would be uninterpretable — it could be a language effect, a phrasing effect, or a
   disagreement with the question's premise.

2. **Language is perfectly confounded with phrasing.** Each language has exactly one wording, so any
   difference between the arms is *language × wording*, and nothing in the design separates them.
   This is the same structural flaw that made `07_instruction_precision` unable to attribute its
   effect — the flaw P3 was built specifically to fix, by crossing two fields 2×2 with repeats.
   Applying the repository's own standard, this design cannot attribute anything to language.

3. **n = 1 per arm.** Two calls total. The repository's own `13b` shows a `Noul` moving between
   repeats on a byte-identical request, and TypeSafe's own consistency cookbook reports answers
   spanning 0.43–0.53 across 15 repeats of one question. One draw per arm supports no comparison.

4. **The official documentation already answers the product question.** `TS-DOC-STATE` states that
   English is the primary training language and that other languages including CJK are accepted
   *"but currently have lower accuracy"*. A two-call local observation cannot add to, refine or
   falsify that, and it certainly cannot produce a general multilingual claim.

**On the audience argument.** The obvious reason to keep this one is that the repository owner and
a large part of the intended readership are Chinese speakers, and an English/Chinese result would
land well with that audience. That is an argument about the audience, not about the design, and it
is exactly the reasoning the rubric exists to reject: the design would still be confounded,
underpowered and semantically ambiguous, and publishing it would put a claim in front of that
audience that the evidence does not support. Retiring it is the more respectful choice.

---

## What "retired" means, and what it does not

**Does mean:**

- The design is not in `EXPERIMENTS`, so `list`, `run`, `run-all` and every documentation table no
  longer offer it.
- Its cases, its helper constants, and its tests are gone from the active surface. Its constants
  that were shared with a surviving experiment were kept and re-commented; `FIXED_EVIDENCE` is the
  one example, still used by `03_parallel_questions`.
- `tests/test_experiments.py::TestRegistryShape::test_no_retired_experiment_is_still_runnable`
  fails if any of the five names reappears in the registry.

**Does not mean:**

- **That it never existed.** The P1 audit's `REGISTERED_BUT_NOT_RUN` entries are historical records
  of a state that was true when written, and they have not been edited. This page is the current
  state; P1 is the historical one, and a reader who finds both should expect them to differ.
- **That the design was worthless.** Each was written as a genuine attempt to widen coverage of
  documented behaviour. They were retired on information gain and design validity, not on effort.
- **That the code is lost.** `git log --follow -- src/jev_lab/experiments.py` and
  `git show e20fad5:src/jev_lab/experiments.py` recover every one of them in full. Git history is
  the archive; this page is the index entry.
