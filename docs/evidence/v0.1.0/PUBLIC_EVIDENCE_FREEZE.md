# Public evidence freeze — `v0.1.0`

**Release:** `0.1.0` · **Tag:** `v0.1.0` · **Manifest:**
[`evidence-manifest.json`](evidence-manifest.json) · **Release notes:**
[`RELEASE_NOTES.md`](RELEASE_NOTES.md)

This document freezes the research and engineering output of stages P0 through P3.6 into one
citable set. It exists so that a blog post, a résumé line, an issue, a third-party reproduction or a
later stage can point at a *version* instead of at a moving branch, and can say what that version
did and did not establish.

**A citation of this release is a citation of the tree at tag `v0.1.0`, not of `main`.** `main` will
move. The canonical logs will not; their digests are in section 3.

---

## 1. Scope

**What this release is.** A measurement bench for TypeSafe's Jev model, plus the audit trail of what
it measured. Its product is the trustworthiness of the evidence: labelled claims, append-only logs,
preregistration before request, and negative results kept rather than dropped.

**What this release is not.** It is not a product, not an SDK, not a benchmark suite, and not a
performance study. Nothing in it is a statement about TypeSafe's service at large, about any other
account, or about any workload other than the synthetic ones in these logs.

### Version semantics — this directory is immutable

**Once `v0.1.0` is tagged, nothing under `docs/evidence/v0.1.0/` may be edited.** Not a hash, not a
typo, not a sentence. The manifest is bound to the Git tree by the tag, and editing any file here
after the tag exists would make the manifest describe something other than what a reader checks out
from `v0.1.0`.

Genuinely new evidence — a new API experiment, a new scientific claim, a change to a canonical log —
requires a **new version directory** (`docs/evidence/v0.2.0/`, tag `v0.2.0`). It never means editing
this one. Corrections to *this* release, if one is ever needed, are recorded as errata (section 9)
in a later version that references this one; the historical text stays as written.

The one permitted change in this directory is the addition of a **new version directory** beside it.

---

## 2. What is frozen

Three classes of artifact, deliberately named differently because they are not the same kind of
thing:

| Class | What it is | Frozen here? |
|---|---|---|
| **Canonical measurements** | The two `usage.jsonl` logs. One record per real API call, success or failure. | **Yes** — by SHA-256; never rewritten. |
| **Canonical evidence documents** | The audits, the preregistration, the result, the source registry, the derived final report, the findings, the errata registry, the provenance record. | **Yes** — by SHA-256 as a set. |
| **Public documentation** | READMEs, architecture, methodology, credential and reproducibility guides, contributing, security. | **Not measurement evidence.** Hashed for completeness only; a wording fix here is not a change to the evidence. |

The distinction matters. A README paragraph is a *presentation* of the evidence and may be reworded
in a later release without invalidating anything. A record in `results/usage.jsonl` is the evidence,
and changing one byte of it invalidates every hash and citation that refers to it.

**Everything frozen here is hashed in [`evidence-manifest.json`](evidence-manifest.json)**, which a
reader can re-verify offline with a single command (section 10).

---

## 3. Canonical measurements

### 3.1 Core evaluation log — P0

| | |
|---|---|
| Path | [`results/usage.jsonl`](../../../results/usage.jsonl) |
| Records | **42** |
| SHA-256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| `schema_version` present | `1` (7 records), `3` (35 records) |
| `model_requested` | `jev-latest` on 42 of 42 |
| `model_resolved` | `jev-1.13.0` on 42 of 42 |
| Status | `ok` on 42 of 42 |
| Recorded window (UTC) | 2026-09-20T15:29:51Z → 2026-09-21T14:20:51Z |
| Answers by type | `choice` 45, `noul` 45, `score` 29 (119 total) |

Two schema versions appear in one log because `SCHEMA_VERSION` was bumped mid-collection; the field
is recorded per record precisely so a reader can tell which revision wrote which line, and the log
was **not** retroactively rewritten to homogenise them.

### 3.2 P3 boundary-locus log

| | |
|---|---|
| Path | [`results/p3_boundary_locus/usage.jsonl`](../../../results/p3_boundary_locus/usage.jsonl) |
| Records | **12** |
| SHA-256 | `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` |
| `schema_version` present | `3` |
| `model_requested` / `model_resolved` | `jev-1.13.0` on both sides, 12 of 12 |
| Status | `ok` on 12 of 12 |
| Recorded window (UTC) | 2026-09-22T15:37:30Z → 2026-09-22T15:37:35Z |

P3's twelve records are in a **separate file on purpose.** Appending them to the core log would have
changed a published SHA-256 and invalidated a freeze. Two logs cost a little navigation and protect
both artifacts.

### 3.3 What the two logs do not contain

- **No estimation.** Every token count is the `usage` value the API returned. Nothing here is
  inferred from character counts or from a tokenizer.
- **No retry accounting.** `retry_count` is `null` on all 54 records, because the SDK sets
  `X-TypeSafe-Retry-Count` on the retried *request* and not on the response, so the field can never
  be populated. **`null` means "not reported", never "no retries happened".** The live field is
  `transport_attempt_count`, a local count of outgoing HTTP attempts; it reads `1` on 35 core
  records and is **not recorded** on the other 7, which is not the same as zero.
- **No cost from the vendor.** Cost is a local estimate against one published price table. TypeSafe
  Console billing is authoritative.

---

## 4. Experiment inventory

The registry at this revision holds **10** designs. All 10 have at least one canonical record:
`ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS`.

| Experiment | Records | Tier |
|---|---:|---|
| `01_primitives` | 1 | core |
| `02_structured_addressing` | 2 | core |
| `03_parallel_questions` | 12 | core |
| `04_confidence` | 2 | core |
| `05_speculative_fanout` | 6 | core |
| `06_composite_scoring` | 3 | core |
| `07_instruction_precision` | 2 | core |
| `12_function_routing` | 4 | core |
| `13_repeatability` | 5 | core |
| `13b_ambiguous_repeatability` | 5 | core |

**Retired before public release (5, never run):** `00_model_info`, `08_literal_reading`,
`09_numeric_limits`, `10_state_length`, `11_language_pair`. Each was reviewed for information gain
against the official documentation and none cleared the bar; the reasoning for each is in
[`EXPERIMENT_REGISTRY.md`](../../experiments/EXPERIMENT_REGISTRY.md). They were never run, so
retiring them removed no evidence — an experiment that was never run is an intention, and deleting an
intention is not the loss of a result.

**P3 is not in this registry, and that is deliberate.** The registry feeds the frozen derived report
and its backlog; adding a member would change what both of them mean. P3's design lives in its
[preregistration](../../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) and it is reachable only
through its own subcommand, so `run-all` cannot reach it.

**No experiment in this release can be run without an explicit budget** and a real key. Nothing in
this repository makes an API call as a side effect of installing, testing, or building it.

---

## 5. Strongest supported conclusions

Each conclusion inherits from exactly one stage and is stated with the scope that stage established.
Nothing here is upgraded, generalised, or merged across stages.

### 5.1 Reproduced under this bench's own conditions

**Typed output semantics hold as documented (LOCAL MEASUREMENT, P1).** `Choice` returns a label plus
a probability distribution over its options; `Noul` returns a single probability and no separate
`confidence` field; `Score` returns a value and a `confidence`. Across the core log's 119 answers
this is exact: 45 `noul` answers, 0 of them carrying a `confidence` key.
*Scope: one account, one model version, synthetic states.*

**Batching questions that share one state reduces input tokens (LOCAL MEASUREMENT, P1).**
`03_parallel_questions` sent five questions over one state in one payload and used materially fewer
input tokens than the same questions asked separately.
*Scope: one payload. The factor is `4.2647x` on that payload over two order-balanced cycles in one
session. It is not TypeSafe's published `12.2x`, it is not comparable to it, and it is not a property
of Jev.*

**The instruction/criteria effect is large end-to-end (LOCAL MEASUREMENT, P3).** On the
`07_instruction_precision` payload, moving both fields from vague to explicit moved the `Noul`
median from `0.76` to `0.20` — a gap of `0.56`, with the endpoint ordering replicating the original
`0.75 → 0.20` observation.
*Scope: one payload, one account, one session, three repeats per endpoint arm, one model version.*

### 5.2 Engineering properties, demonstrated rather than asserted

**Fail-closed credential resolution (P0–P3).** An absent, empty, malformed, duplicated or unreadable
key source stops the run before a request is sent. There is no fallback that guesses.
*Scope: the two documented sources only.*

**Append-only provenance (P0–P3).** Every real API call produces exactly one record, written by one
recorder, whether it succeeds or raises. The core log's SHA-256 is identical at `e20fad5` and at
every commit since, including `bdcb637` — verified, not asserted.
*Scope: this repository's log-writing path.*

**Derived artifacts cannot drift (P0, P3).** Every number in `results/JEV_LOCAL_EVALUATION_FINAL.md`
is recomputed from the committed logs on the way out, and CI regenerates the file and fails if it
differs from what is committed. A derived file cannot become a second source of truth.
*Scope: the three generator commands in this repository.*

**A post-run analyzer repair moved no measurement and no verdict (P3).** See section 9, ERR-002.

### 5.3 The state of the science

This release inherits three verdicts and reaches one scientific state. All four are the frozen
stages' own strings, quoted rather than paraphrased:

| Stage | Verdict | What it means here |
|---|---|---|
| P0 | `CORE_CAPABILITY_EXPLORATION_CLOSED` | The core exploration is finished; the log is frozen and not extended. |
| P1 | `P1_OFFICIAL_LOCAL_AUDIT_PASS` | Every official claim located was audited against local evidence and labelled. |
| P2 | `P2_TRIAGE_PASS` | Every candidate was triaged individually, with its strongest counter-explanation steelmanned. |
| — | **`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** | The scientific state after P3. |

> **`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** (P2's exact state string.)

Across 42 core records and the official behaviours audited in P1, this bench has **no finding about
Jev that is both novel relative to TypeSafe's public material and supported by its own data.** Every
large local effect either restates an officially documented behaviour or is an artifact of this
repository's own Python-side policy.

That is the *first* of two "no finding" states. It is not
`CURRENT_EVIDENCE_DOES_NOT_SUPPORT_JEV_SPECIFIC_NOVELTY`, because one question (`B′`) cleared the
bar and was worth a bounded experiment — and P3 then ran it and returned a null (section 6).

**This is a deliberate outcome, not a failure.** The repository exists to test findings, not to
accumulate them, and the tests came back negative.

---

## 6. Negative results

**Negative results are kept here on the same footing as positive ones.** A repository that reports
only what worked is not evidence.

### 6.1 The P3 primary result — the preregistered null

```
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
```

**The original instruction-precision effect could not be attributed to `instructions` or `criteria`
alone under the preregistered one-payload 2×2 design.**

Four arms, a 2×2 of the two fields, three repeats each, twelve logical calls. Design, order,
statistics and thresholds committed before the first request.

| Arm | `Noul` values | Median | Range |
|---|---|---:|---:|
| neither | 0.77, 0.76, 0.75 | 0.76 | 0.02 |
| instruction only | 0.31, 0.33, 0.29 | **0.31** | 0.04 |
| criteria only | 0.37, 0.36, 0.33 | **0.36** | 0.04 |
| both | 0.20, 0.21, 0.20 | 0.20 | 0.01 |

Both single-field arms moved most of the way toward the explicit baseline and landed **0.05 apart
from each other** against a 0.56 end-to-end gap. The preregistered separation rule (K1, `|I_med −
C_med| < 0.1`) fired, and no assignment of a single-field arm left its counterpart inside the
vague-baseline band (GO-2 FAIL).

**The correct summary is the one above, and the two wrong summaries are:** *the boundary lives in
both fields* — the design cannot distinguish that from a mixed-specificity artifact — and *criteria
are what matter* — the data says the opposite of a preference, if anything.

Two limits are load-bearing. `FIELD_ALIGNMENT_CAVEAT`: the crossed arms pair a broader field with a
narrower one rather than two independently varying definitions, so a result here is a statement
about *this* mixed-specificity construction. And n = 3 per arm supports a median and a range and
**no interval estimate**; no confidence interval is reported because the design cannot support one.

### 6.2 Candidates retired by triage (P2)

Seven candidates were retired, including **the two with the largest local effect sizes**, which were
killed on prior art rather than on this repository's own data. No candidate was killed for being
unflattering and none was preserved for being interesting. The full table, with the strongest
counter-explanation for each, is in
[`findings.md` § 3](../../findings/findings.md#3-negative-and-killed-findings).

### 6.3 A candidate held, not published

*Is variability a function of boundary proximity?* Mid-scale payloads moved on every repeat; a
payload pinned at 1.0/0.0 could not. Held because it fails the falsifiability bar — the boundary
cannot be located in advance without a pilot — and because the contrast is confounded by a ceiling
effect: a distribution pinned at 1.0/0.0 has no room to move, so its stability is saturation, not
robustness. **Not authorized for publication until redesigned.**

### 6.4 The novelty check that came back unresolved

The one candidate that reached P3 did so with its public-novelty check returning
`PUBLIC_NOVELTY_UNRESOLVED`. That is recorded as **unresolved** — never as "nobody has discovered
this". A null result under an unresolved novelty check is a null result about our measurement, not a
claim of priority in either direction.

---

## 7. Claims explicitly NOT established

Nine markers. Each names something a reader might reasonably *expect* this repository to show and
that it does **not** show. Several are restatements of P1's own non-claims section, kept in its more
precise wording where that wording exists.

| Marker | What is not established | Why |
|---|---|---|
| `NO_GENERAL_ACCURACY_CLAIM` | Any accuracy rate, for Jev or for anything else. | There is no ground truth anywhere in this bench. Expected labels are the design's intention, written alongside the states. "2 of 2" and "4 of 4" are **counts on synthetic cases, never rates**. |
| `NO_CALIBRATION_VALIDATION` | Calibration, **in either direction**. | No reliability diagram, no ECE, no Brier score, no independent ground-truth dataset. `04_confidence` contains **two** cases. This repository neither validates nor falsifies any calibration claim, and must never be cited as doing either. |
| `NO_MODEL_LATENCY_BENCHMARK` | Any latency benchmark or speedup. | Local wall-clock is a superset window recorded because it was free to record; it contains DNS, TCP, TLS, connection-pool state, server queueing, upstream load and local scheduling. No arm is called faster. `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK` stands. |
| `NO_UNIVERSAL_BATCHING_RATIO` | Any general claim that batching is N× cheaper. | `4.2647x` is a property of **one payload** with five questions sharing one state, over two order-balanced cycles in one session. Not the vendor's `12.2x`, not comparable to it, not a property of Jev. |
| `NO_DETERMINISM_VERDICT` | Determinism — **and also non-determinism**. | Byte-identical requests returned differently-shaped distributions here, but that is a small number of repeats on two payloads, not a verdict. The official FAQ entry was not retrievable, and no official source read makes a determinism claim in either direction. |
| `NO_BROAD_HALLUCINATION_BENCHMARK` | Any factual-correctness or hallucination rate. | Nothing here probes factual correctness. The only axis measured is **schema conformance**, on benign payloads, with no adversarial attempt. |
| `NO_PRODUCTION_SAFETY_CERTIFICATION` | That any pattern here is safe in production. | Nothing certifies these patterns against real systems, real customer data, or real money. Every handler in the bench is inert; no file was written, no message sent, and no allowed route was observed reaching its handler under a real answer (`ACTUAL_HANDLER_EXECUTION_UNTESTED`). |
| `NO_GENERAL_INSTRUCTION_VS_CRITERIA_FIELD_PREFERENCE` | Any general rule about which field matters more. | P3 measured one payload at n = 3 per arm under `FIELD_ALIGNMENT_CAVEAT` and returned a null. It supports no ordering between the fields, on this payload or any other. |
| `NO_NAS_CLAIM` | Any suitability for NAS or any architectural-search workload. | Nothing in this release tests NAS. The repository contains no NAS experiment, no NAS dataset, and no NAS measurement, and the two retired designs that might have touched search-adjacent behaviour were never run. |

### Two further limits that are not markers but are equally binding

**No vendor-claim adjudication.** Where an official figure and a local figure differ, this
repository says they are not commensurable. It never reports a vendor number as "actually" a local
one, or a local one as evidence about the vendor's workload. An official claim is a claim about
TypeSafe's workload; only a line in a log here is a local measurement.

**No composite-dimension independence.** The four scoring dimensions are separate, atomic and
orthogonal by design. Their correlation was never measured.

**If you are writing about this release, read
[`BLOG_CLAIM_CONTRACT.md`](BLOG_CLAIM_CONTRACT.md) first.** It restates section 5, section 6 and this
section as a three-way contract — what may be stated flatly, what may be stated only with its scope
attached, and what may not be stated at all.

---

## 8. Official-source snapshot

The TypeSafe material cited throughout this release was read during the P1 audit. That snapshot is
what this release is audited against:

> **TypeSafe official claim snapshot: as observed during P1 audit / accessed: 2026-09-22.**

| | |
|---|---|
| Registry | [`docs/sources/TYPESAFE_OFFICIAL_SOURCES.md`](../../sources/TYPESAFE_OFFICIAL_SOURCES.md) |
| Registry SHA-256 | `f823fc9f0d2f3464544daf43c264506785962ca0de9e8236b6c572a2775e47f3` |
| Registered IDs | **35** — `TS-IDX` (the documentation index itself) plus 34 sources |
| Tier-1 product/technical docs | **28** |
| Jev version stated in the sources | `jev-1.13` / `jev-1.13.0` where stated |
| Per-source digests | Recorded in the registry, one SHA-256 per fetched document |

**The distinction this section exists to make.** "The official docs as audited on 2026-09-22" and
"the official docs today" are different objects. TypeSafe's documentation can change at any time and
this repository does not track it. If a page has been edited since, that is **not** a discrepancy in
this release — it is a divergence between two snapshots, and the correct response is a new audit, not
a correction to this one. P1's own freshness policy is in the registry.

Source-internal divergences were recorded rather than resolved: the registry lists five (`D-1` to
`D-5`), including two different `confidence` thresholds used for the same worked example on two
official pages. This repository does not adjudicate them.

---

## 9. Known errata

Two entries. The full registry, with derivations and recovery commands, is
[`docs/ERRATA.md`](../../ERRATA.md). A summary, because a reader of a frozen release is entitled to
know what is wrong in it without following a link:

### ERR-001 — P1 states the wrong `Noul` count · status `DOCUMENTED`

P1's row `TS-JEV-SEM-004` says **"42 of 42"** `Noul` answers carry no `confidence` field. The correct
figure is **45 of 45**. 42 is the **record** count; the claim is about **answers**, and the 42
records carry 119 answers between them.

Recomputed independently for the errata registry from the canonical log rather than from any earlier
report — `Counter({'choice': 45, 'noul': 45, 'score': 29})`, `noul` answers carrying a `confidence`
key: 0.

**Consequence: none.** The claim P1 makes is exactly what the log shows. Correcting 42 to 45
sharpens a count that was already true in substance; it strengthens, weakens and retracts nothing.
**P1's frozen text was not edited**, because it is a historical audit artifact and silently
correcting it would destroy the reader's ability to tell which of its numbers had been touched.

### ERR-002 — P3's original analyzer could not represent its own outcome pair · status `RESOLVED`

In the analyzer frozen at `db7d06f`, GO-1 and GO-2 — two separate conditions in the preregistration —
were evaluated as a single conjunction, making the pair `(GO-1 PASS, GO-2 FAIL)` unrepresentable. On
that data, that is exactly the pair the frozen rule computes. The defective analyzer reported GO-1 as
FAIL and printed a note the data contradicts.

Corrected at `bdcb637` (**post-run analyzer repair, no new measurement**). No call was made and none
was rerun; the twelve records are byte-identical before and after; no threshold and no rule was
altered; the preregistration is byte-identical to `db7d06f`; and the primary verdict is unchanged,
because GO-1 alone was never sufficient. The defect made the *reasoning display* wrong, not the
decision. `tests/test_p3_boundary_locus.py` asserts this invariance mechanically against the real
log.

**This is `RESOLVED`, not outstanding. It is not a defect in the current code**, and this release
must not be described as carrying a broken analyzer. The pre-correction analysis is preserved at
`c0fc9cc` and recoverable with `git show` — that preservation is the point, not a wart.

---

## 10. Reproduction

Everything needed to check this release is offline and needs no API key. From a clone:

```console
git clone https://github.com/Charlie-Wang-03/jev-test.git
cd jev-test
git checkout v0.1.0          # the frozen tree, not main

uv sync --locked
uv run pytest                # the full offline suite; sockets are blocked outright

uv run python -m jev_lab.evidence_freeze verify   # re-hash every frozen artifact
```

`verify` reads [`evidence-manifest.json`](evidence-manifest.json), recomputes the SHA-256 of every
listed file, re-counts both canonical logs, and re-checks the registry, license, version and P3
verdict invariants — all from disk, with no network access of any kind. It exits non-zero on any
mismatch. It is the mechanical form of every claim in this document.

The derived report can also be rebuilt and compared:

```console
uv run python -m jev_lab report
uv run python -m jev_lab snapshot
uv run python -m jev_lab final-report
uv run python -m jev_lab.p3_boundary_locus report
```

**What reproduction can and cannot mean here.** Reproducing the **method** is the goal. Reproducing
the **digits** is not something this design can promise: the model alias can move (only the response
says which model answered), the model is probabilistic (byte-identical requests returned
differently-shaped distributions), the substrate differs (latency contains the network and the
machine), and the account and session differ (cost is a local estimate; the vendor's Console billing
is authoritative). A live run that produces different numbers has **not** falsified the frozen ones,
and a live run that matches them has not validated them. It has produced a second measurement.

`results/usage.jsonl` is **frozen, not append-only-growing.** Appending to it would invalidate a
published hash and destroy the citation. New measurements get their own log in their own directory —
use `--results-dir`.

---

## 11. Provenance

Full record: [`docs/EVIDENCE_PROVENANCE.md`](../../EVIDENCE_PROVENANCE.md). The lineage, and what each
commit *is*:

| Commit | Stage | What it did |
|---|---|---|
| `e20fad5` | P0 | **MEASUREMENT.** The 42-record core freeze. |
| `e9d54ca`, `77357d9` | P0 | **ANALYSIS.** Derived-report integrity fixes. No record added, changed or removed. |
| `ec04cb6` | P1 | **ANALYSIS.** Audit of official claims against the frozen evidence. No API call. |
| `3125281` | P1 | **DOCUMENTATION.** Repaired the audit's own HEAD provenance. Findings not edited. |
| `373e259` | P2 | **ANALYSIS.** Novelty triage. No API call. |
| `db7d06f` | P3 | **PREREGISTRATION.** `db7d06f = preregistration + original analyzer`, frozen before the first request. |
| `c0fc9cc` | P3 | **MEASUREMENT.** `c0fc9cc = immutable measurements + discovered defect disclosure` — the twelve records, and the analyzer defect disclosed after the fact. |
| `bdcb637` | P3 | **ANALYSIS.** `bdcb637 = post-run analyzer repair, no new measurement`. |
| `cc778be`, `c3f468d` | P3.5 | **DOCUMENTATION.** Repository reorganisation and bilingual documentation. |
| `56eb159`, `251c883` | P3.5 | **ENGINEERING.** Offline CI, quality gates, public-release hardening. |
| `ad1dff4` | P3.6 | **DOCUMENTATION.** MIT license, opaque-identifier decision, experiment retirement. |
| `44fbbb1` | P3.6 | **DOCUMENTATION.** Corrected the stated test count to the verified one. |

A commit type here is not metadata attached to a commit — it is a claim about what the diff does,
and each is checkable with `git show`. The distinction that matters most: **an ANALYSIS commit may
change code that reads a log, and may never change the log.**

**Nothing was amended, rebased, squashed or force-pushed.** Both measurement commits are the ones
originally pushed, and the full lineage is linear on `main`.

---

## 12. Citation

```bibtex
@misc{jev-test-v0.1.0,
  title        = {jev-test: local evaluation bench and evidence freeze for TypeSafe Jev 1.13.0},
  author       = {Wang, Yichuan},
  year         = {2026},
  version      = {0.1.0},
  howpublished = {\url{https://github.com/Charlie-Wang-03/jev-test/tree/v0.1.0}},
  note         = {Tag v0.1.0. Core log 42 records, SHA-256
                  38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b.
                  No DOI is assigned to this release.}
}
```

Machine-readable metadata: [`CITATION.cff`](../../../CITATION.cff).

**When citing, cite the tag, not `main`**, and carry the scope with the claim. This release's own
honest summary is section 5.3: `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`. The value it offers a
citation is not a discovery — it is a worked example of independent, preregistered, reproducible
evaluation with its negatives intact.

**No DOI exists for this release and none is claimed.** It is not published to PyPI and no GitHub
Release has been created; the tag is the artifact.

---

**License: MIT** — covers the code, both canonical logs, and the derived reports. See
[`LICENSE`](../../../LICENSE) and the
[license decision](../../OPEN_SOURCE_LICENSE_DECISION.md).
