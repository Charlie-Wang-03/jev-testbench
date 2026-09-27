# Claim audit — the bilingual technical blog

**Audited documents:**
[`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md) (English, canonical) and
[`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md) (Simplified Chinese).
**Standard:** [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md)
**Evidence base:** release `v0.1.0` — [`PUBLIC_EVIDENCE_FREEZE.md`](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md),
[`evidence-manifest.json`](../evidence/v0.1.0/evidence-manifest.json), and the two canonical logs.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 2 — bilingual. Supersedes the Chinese-only revision 1 (P5-A).

**What this file is.** Every substantive claim in either language, classified against the contract's
three classes — `A` (`SAFE_TO_STATE`), `B` (`SAFE_WITH_SCOPE`), `C` (`DO_NOT_STATE`) — with the
evidence it rests on, the location of the claim in each article, and whether the scope that class
requires is actually present in each language. It exists so a reader can check both articles without
re-reading the entire evidence set.

**How the numbers were checked.** Every figure in both articles was **re-derived from
`results/usage.jsonl` and `results/p3_boundary_locus/usage.jsonl` during this audit**, not copied
from the work order that commissioned the articles and not copied from the freeze document's prose.
Where a work order and the frozen evidence could disagree, the frozen evidence governed. They did not
disagree.

**One text is a translation of the other, and that is not a defence.** The contract binds every
public-facing sentence derived from the release. A translation can carry a scope into the wrong
clause, or drop it, while every number still matches — so each language gets its own scope column
and its own verdict, and a scope that is present in one language and absent in the other is a defect
in the absent one.

---

## 1. What changed in this revision

Three things, and the first is a correction.

### 1.1 A misclassification in revision 1

Revision 1 carried a row reading **"These 54 calls found nothing new about Jev"** and classified it
`SAFE_TO_STATE`. That classification was wrong, and not narrowly so. The sentence asserts an
absolute — that nothing new was found, full stop — where the frozen state is
`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`: a claim about *this* set of calls, at *this* release, with
two words of deliberate qualification (`strong`, `yet`) doing real work. Class A is available for a
claim about the repository's own state. It is not available for a universal negative about the
subject matter, and the contract's novelty rule says so directly:

> Any sentence about novelty must be scoped to "we found no public attribution", never "there is
> none".

Both articles now say the scoped thing, and the row is a class `B` row. The corrected statement is:

> The release reached `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`.

**`PUBLIC_NOVELTY_UNRESOLVED` still holds, and is unchanged.** The novelty check that was run for
the P3 question came back unresolved; it was not resolved by this revision, no new search was made,
and nothing about this audit converts it into a positive or a negative finding. "Unresolved" remains
the recorded status, and both articles say so in §7. The two rows are now cross-referenced so a
reader who reads one arrives at the other.

### 1.2 Novelty-scope edits to the Chinese text

Four Chinese sentences were rewritten in this revision. Three were novelty-scope, one was a
precision fix found while adapting:

| § | Was | Now | Why |
|---|---|---|---|
| intro | 这 54 次调用没有发现任何关于 Jev 的新东西。 | 这 54 次调用最终没有留下一个经得住审查、足以称为「强 Jev-specific 新发现」的结论。 | The original was stronger than the frozen state string. |
| §4 | 这 10 个实验都没有得出「Jev 特有」的新发现。 | 这 10 个实验都没有留下一条既相对于 TypeSafe 公开材料是新的、又被我自己的数据支持的结论 —— 也就是冻结文档所说的 `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`。 | Same defect, restated at the section level; now quotes the freeze's own canonical phrasing. |
| §16 | 这份仓库里没有任何关于 Jev 的发现，… | 这份仓库里没有一条…的 Jev 发现。 | Tightened to the scoped form; no claim changed. |
| §7 | …只改了问题的措辞：模糊的决策边界下… | …改了决策边界的写法：模糊的边界下… | 「只改了问题的措辞」 reads as the package description the contract forbids ("rewording the prompt alone produced 0.55"); the arms changed the boundary's *formulation*, not only its phrasing. |

The English article was written after these edits and never carried the unscoped form.

**No claim was added, removed or weakened by a change of verdict except row 3, rows 18 and 63**
(§2 below). The edits moved wording, not substance, and no conclusion in either article moved.

### 1.3 The English adaptation

`jev-as-probabilistic-decision-primitive.md` adds **zero new substantive claims**. It is an
adaptation, not a translation, with a 1:1 section correspondence to the Chinese (§1–§16 map to
§1–§16), and every figure, name and scope in it traces to a row below. No row in this audit has a
`—` in both language columns, and no row was added for the English alone.

One wording difference is material and is audited as row 3: the English opening says *"after 54 API
calls, I did not end up with a result that survived scrutiny as a strong Jev-specific novel
finding"*, and the Chinese says the equivalent. The two are the same claim, differently built, and
both are scoped.

---

## 2. The audit

**Column key.** *ZH* and *EN* give the section of each article holding the claim, in that article's
own numbering. *Scope* is `yes` (the class-B scope is present in the same or immediately adjacent
sentence), `n/a` (the class does not require one), or `MISSING` (the claim would be a defect).

| Claim ID | Semantic claim | Contract class | Evidence | Chinese | English | Scope in ZH | Scope in EN | Verdict |
|---|---|---|---|---|---|---|---|---|
| C-01 | 54 API calls in total | A — the release | 42 core + 12 P3 records in the two frozen logs | intro, §3 | intro, §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-02 | TypeSafe positions Jev as "a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out" | A — official sources | `TS-BLOG-INTRO`, via `docs/sources/TYPESAFE_OFFICIAL_SOURCES.md` | §1 | §1 | n/a | n/a | `SAFE_TO_STATE` |
| C-03 | **The release reached `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** (was: "found nothing new about Jev") | **B** — anything about novelty | Freeze §5.3; `BLOG_CLAIM_CONTRACT.md` novelty rule | intro, §16 | intro, §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-04 | A Jev call is `state + typed questions → typed answers`; all questions see the same state and are evaluated independently | A — official, attributed | `TS-DOC-STATE` | §2 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-05 | `Choice` returns a label plus a distribution over options; `probabilities` sum to 1; `choice` is the argmax | A — official + reproduced | `TS-DOC-CHOICE` | §2 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-06 | `Score` returns a value plus `confidence`, defined as the probability-weighted mean of the levels | A — official | `TS-DOC-SCORE` | §2 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-07 | `Noul` is a single probability with no separate `confidence`; **45 of 45** locally | B — typed output semantics; the 45/45 count needs the erratum | Log: `noul` carrying `confidence`: **0**. `ERR-001` | §2, §11 | §2, §11 | yes | yes | `SAFE_WITH_SCOPE` |
| C-08 | One `01_primitives` answer had winning probability 0.45 and confidence 0.26 | A — a named single record | Log: `01_primitives`/`department`, `choice: other`, `0.45` / `0.26` | §2 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-09 | Typed output solves the schema problem, not the semantic one | A — non-claim | `NO_BROAD_HALLUCINATION_BENCHMARK`, `NO_GENERAL_ACCURACY_CLAIM` | §2 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-10 | The vendor's known-limitations page lists literal reading, weak numerics, date comparison, indirection, large state, and puts control flow in code | A — official, attributed | `TS-DOC-JAG`, `TS-DOC-BUILD` | §2 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-11 | Vendor figures are claims about *their* workload; only a log line is a local measurement | A — repository practice | Freeze §7, no vendor-claim adjudication | §3 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-12 | The two logs' SHA-256 are `38e67630…` / `17f36f75…` and never changed | A — canonical log identity | Freeze §3; re-hashed during this audit | §3 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-13 | 42 records requested `jev-latest` and resolved `jev-1.13.0` | A — provenance | Log: `model_resolved = jev-1.13.0` on 42/42 | §3 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-14 | CI regenerates derived artifacts and fails on any difference | A — engineering | `.github/workflows/ci.yml`; freeze §5.2 | §3 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-15 | The 54 calls cost ≈ **$0.001** by local estimate | B — cost figures | Sum of `estimated_cost_usd` over both logs = `0.001084566` | §3 | §3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-16 | 10 registered experiments, all executed, 42 core records | A — registry | Freeze §4; `EXPERIMENT_REGISTRY.md` | §4 | §4 | n/a | n/a | `SAFE_TO_STATE` |
| C-17 | `04_confidence` has 2 cases; `12_function_routing` makes 4 calls | A — registry | Registry tables | §4 | §4 | yes | yes | `SAFE_TO_STATE` |
| C-18 | None of the 10 left a conclusion both new relative to TypeSafe's public material and supported by the data (was: "no Jev-specific new finding") | **B** — novelty, scoped | P2 §6; freeze §5.3 | §4 | §4 | yes | yes | `SAFE_WITH_SCOPE` |
| C-19 | Batching: 816 vs **3,480** input tokens; **4.2647×**; **76.55%** saved | B — batching ratio | Log: batched `[408, 408]`; separate sum `3480`; ratio `4.2647` | §5 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-20 | 10/10 selected values identical, largest absolute difference 0.0 | B — same row | Log: the five values repeat across both cycles and both arms | §5 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-21 | The local 4.26× must not be compared with the vendor's 12.2× | A — contract rule | `BLOG_CLAIM_CONTRACT.md` class B; P1 audit | §5 | §5 | yes | yes | `SAFE_TO_STATE` |
| C-22 | Public third-party measurements varied batch size and published an accuracy curve | B — third-party, cited as third-party | P2 §4.1 (D), P2 §7 `BLOG_CORE` | §5 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-23 | 13b: label unchanged 5/5; top-2 margin moved ≤ 0.07; `Score` 1.58–1.63; `confidence` 0.24–0.30; one exact tie | B — local measurement + a novelty claim that may only be scoped | Log: margins `0.07, 0.06, 0.02, 0.03, 0.00`; scores `1.58–1.63`; `department` confidences `0.24–0.30`; `ambiguous_5` `other 0.45 = billing 0.45` | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-24 | Official cookbook reports label flips on 2 of 8 questions and per-label std dev (mean 0.0098, max 0.0515) | B — official, attributed | P2 §4.1 (A); the vendor cookbook | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-25 | A public chaos test sent the identical request five times and got `0.03, 0.03, 0.03, 0.04, 0.04`, with jitter floors over ~1,490 calls | B — third-party, cited as third-party | P2 §4.8 | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-26 | The 0.60 gate is this repository's own constant, labelled a demonstration threshold, never calibrated | B — our own policy | `experiments.py` `CONFIDENCE_GATE_THRESHOLD`; P2 §4.1 (C) | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-27 | The ambiguous case returned 0.61 against a 0.74 vs 0.26 margin; the published k=3 expression reproduces 0.61 exactly | B — local measurement + derived | The `04` record; P2 §4.1 (C) | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-28 | Two official pages use different `confidence` thresholds for the same worked example, and both say thresholds are domain-specific | A — official sources; a recorded divergence | Freeze §8; `TS-DOC-CONF` vs `TS-DOC-CONFROUTE` | §6 | §6 | yes | yes | `SAFE_TO_STATE` |
| C-29 | Routing: 4/4 function matches, 4/4 argument matches, 4/4 suppressed, handler never entered | B — our architecture | The `12` records; P2 §4.1 (G) | §6, §12.3 | §6, §12.3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-30 | Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a 0.8 floor; the 1.0 case withheld by `needs_human_review` 0.94 ≥ 0.5 | B — our own policy; thresholds are demonstration parameters | Log: the four `function` answers carry those confidences; `needs_human_review` = 0.94 | §6 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-31 | `07`: an 82-byte byte-identical state, `Noul` 0.75 → 0.20, a 0.55 move | B — the `07` illustration | Log: `state_utf8_bytes = 82`; vague `0.75`, explicit `0.20` | §7 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-32 | The official remedy for the literal-reading edge is given as a bundle and never decomposed | A — official | `TS-DOC-JAG`; P2 §4.3 | §7 | §7 | yes | yes | `SAFE_TO_STATE` |
| C-33 | The novelty check returned `PUBLIC_NOVELTY_UNRESOLVED`, recorded as unresolved, never as "nobody has done this" | B — anything about novelty | P2 §4.8 | §7 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-34 | It was the only question that passed triage and was worth spending calls on | B — novelty | P2 §5: exactly one `R_GO` candidate | §7 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-35 | Design, order, statistics and thresholds were committed before the first request | A — preregistration | Freeze §5.1; `db7d06f` | §8 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-36 | A 2×2 of the two fields, 3 repeats per arm, 12 calls, declared as a hard ceiling | A — preregistration | `P3_BOUNDARY_LOCUS_PREREGISTRATION.md` §9; freeze §6.1 | §8 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-37 | The pre-registered design hazard: the crossed arms must state the same boundary | A — preregistration | Preregistration §9 | §8 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-38 | P3 raw values, medians and ranges for all four arms | A — local measurement | P3 log: `N` 0.77/0.76/0.75; `I` 0.31/0.33/0.29; `C` 0.37/0.36/0.33; `B` 0.20/0.21/0.20 | §9 | §9 | n/a | n/a | `SAFE_TO_STATE` |
| C-39 | The endpoints replicated the original observation: 0.76 → 0.20, gap 0.56 | B — endpoint replication | P3 log; original `07` values | §9 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-40 | Instruction-only recovered 80.4% of the gap; criteria-only 71.4% | B — descriptive arithmetic, not part of the decision rule | Derived from the medians: `0.45/0.56`, `0.40/0.56` | §9 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-41 | The two single-field arms are 0.05 apart, below the pre-registered 0.10, so K1 fired | B — the separation that killed the attribution | P3 log; freeze §6.1 | §9 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-42 | `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`; the effect could not be attributed to either field alone | A — primary null | Freeze §6.1; P3 result §3 | §9 | §9 | n/a | n/a | `SAFE_TO_STATE` |
| C-43 | The large effect replicated; the *attribution* is what failed | A — the null, stated correctly | P3 result §4 | §10 | §10 | n/a | n/a | `SAFE_TO_STATE` |
| C-44 | Two summaries are explicitly refused: "the boundary lives in both fields" and "criteria are what matter" | A — refusals | Freeze §6.1 names both as the two wrong summaries | §10 | §10 | n/a | n/a | `SAFE_TO_STATE` |
| C-45 | `FIELD_ALIGNMENT_CAVEAT` limits the result to this mixed-specificity construction | A — caveat | Freeze §6.1; P3 result §7 | §10 | §10 | yes | yes | `SAFE_TO_STATE` |
| C-46 | **n = 3 per arm** supports a median and a range and no interval estimate | A — caveat | Freeze §6.1 | §10 | §10 | yes | yes | `SAFE_TO_STATE` |
| C-47 | The analyzer defect, its disclosure, its post-run repair, and the invariance of every measurement, threshold and verdict | A — engineering + provenance | `ERR-002`; P3 result, "Post-run analyzer correction provenance" | §11 | §11 | n/a | n/a | `SAFE_TO_STATE` |
| C-48 | `ERR-001`: P1 states 42 of 42; the correct figure is 45 of 45; P1's text was not edited | B — the corrected count, which requires citing the erratum | Log recount; `ERRATA.md` | §11 | §11 | yes | yes | `SAFE_WITH_SCOPE` |
| C-49 | The 42 records carry 119 answers between them | A — canonical log | Log: 119 answers total | §11 | §11 | n/a | n/a | `SAFE_TO_STATE` |
| C-50 | 42/42 responses were schema-valid; that is the weakest kind of type-safety evidence | A — non-claim | `findings.md` §1 | §12.1 | §12.1 | yes | yes | `SAFE_TO_STATE` |
| C-51 | In `06_composite_scoring`, one dimension scored 1.62 on a 0–3 rubric at confidence 0.24 and carried 97.4% of that state's composite risk | A — local measurement, one named case | Log: `evidence_quality` raw 1.62, confidence 0.24; recomputed share **97.41%** | §12.2 | §12.2 | n/a | n/a | `SAFE_TO_STATE` |
| C-52 | Official calibration is group-scoped; confidence "describes the model's answer, not a guarantee that the answer is correct" | A — official, attributed | `TS-DOC-SYS1`, `TS-DOC-CONF` | §12.2 | §12.2 | yes | yes | `SAFE_TO_STATE` |
| C-53 | This project neither validated nor falsified calibration, in either direction | A — non-claim | `NO_CALIBRATION_VALIDATION` | §12.2 | §12.2 | n/a | n/a | `SAFE_TO_STATE` |
| C-54 | Semantic routing ≠ execution authorization; 4/4 is a count not a rate; handlers are inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` | A — our architecture + non-claims | `findings.md` §2; `12` records | §12.3 | §12.3 | yes | yes | `SAFE_TO_STATE` |
| C-55 | Batch economics are workload-dependent; amortisation needs a shared state | A — scope restated | Freeze §5.1 | §12.4 | §12.4 | yes | yes | `SAFE_TO_STATE` |
| C-56 | In `05`, 4 of 12 speculative answers were unconsumed, input fell by 400 tokens, and output is priced at zero | A — local measurement + the official price table | Log: fan-out 1412 in / staged 1812 in (= 400); 4 of 12 unconsumed | §12.4 | §12.4 | yes | yes | `SAFE_TO_STATE` |
| C-57 | `retry_count` is permanently `null` and means "not reported"; `transport_attempt_count` licenses exactly one sentence | A — engineering limitation | Freeze §3.3; `findings.md` §2 | §12.6 | §12.6 | yes | yes | `SAFE_TO_STATE` |
| C-58 | Five registered designs were retired before publication, never run | A — the inverse of the contract's `DO_NOT_STATE` row | Freeze §4; `EXPERIMENT_REGISTRY.md` | §13 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-59 | `10_state_length`'s three defects: no ground truth, n = 1 per tier, and filler that repeats five sentences rather than accumulating content | A — registry reasoning | Registry entry for `10_state_length` | §13 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-60 | `11_language_pair`'s four reasons, including that the official docs state English is primary and CJK currently has lower accuracy | A + official, attributed | Registry entry for `11_language_pair`; `TS-DOC-STATE` | §13 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-61 | The nine non-claims, in natural prose rather than as markers | A — non-claims | Freeze §7 | §14 | §14 | n/a | n/a | `SAFE_TO_STATE` |
| C-62 | No NAS experiment, dataset or measurement exists here; NAS is a future question to be re-derived from NAS task structure | A — non-claim | `NO_NAS_CLAIM`; freeze §7 | §15 | §15 | n/a | n/a | `SAFE_TO_STATE` |
| C-63 | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`; every large local effect restates a documented behaviour or is this repository's own policy | **B** — state of the science, stated as novelty | Freeze §5.3 | §16 | §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-64 | License: MIT | A — release fact | `LICENSE`; `pyproject.toml` | §16 | §16 | n/a | n/a | `SAFE_TO_STATE` |

---

## 3. Totals

| Verdict | Chinese | English |
|---|---:|---:|
| `SAFE_TO_STATE` | **42** | **42** |
| `SAFE_WITH_SCOPE` | **22** | **22** |
| `DO_NOT_STATE` | **0** | **0** |
| **Substantive claims audited** | **64** | **64** |

**`DO_NOT_STATE_ZH = 0`, `DO_NOT_STATE_EN = 0`.** Nothing in either article had to be deleted or
rewritten for asserting something the evidence does not carry.

**Why the class counts differ from revision 1.** Rows C-03, C-18 and C-63 moved from class `A` to
class `B`. All three are statements about novelty, and the contract's novelty rule requires a scope
for any such sentence. Revision 1 treated them as restatements of the frozen state string, which is
class `A` when the string is *quoted*; as prose they are novelty statements, and class `B` is the
honest classification. No claim, figure or conclusion changed — only the class it is filed under.
The total stayed at 64 and `DO_NOT_STATE` stayed at 0.

**Every one of the 64 rows is present in both languages.** No row has `MISSING` in either scope
column, and no row is scoped in one language and unscoped in the other.

---

## 4. The two mechanical parity gates

These checks prevent drift between the languages. They are **not** a substitute for the audit above:
a pair of articles can share every figure and still carry a scope into the wrong clause in one of
them, which is why each language has its own scope column.

### 4.1 Novelty parity (§19)

Neither article may contain an equivalent of *"nothing new about Jev"*, *"no novelty exists"*,
*"nobody has done this"*, or *"we discovered a novel Jev behaviour"*.

| Pattern | Chinese | English |
|---|---|---|
| nothing new about Jev / 没有发现任何关于 Jev 的新东西 | absent | absent |
| no novelty exists / 不存在新颖性 | absent | absent |
| nobody has done this / 没有人做过 | **only in the refusal** — §7: 我把它记成「未解决」，而不是「没有人做过」 | **only in the refusal** — §7: "I record that as *unresolved*, not as *nobody has done it*" |
| we discovered a novel Jev behaviour | absent | absent |

The third row is a true positive for the pattern and a pass for the gate. Both articles use the
phrase **only to refuse it**, in the sentence that states what `PUBLIC_NOVELTY_UNRESOLVED` does and
does not mean. A gate that could not tell an assertion from its refusal would be the wrong gate;
this one reports the distinction rather than hiding it.

Both articles state the frozen state string in a fenced block in §16 where a reader will see it, and
restate it in prose around the block. **Gate: PASS.**

### 4.2 Bilingual factual parity (§20)

Both articles must contain each of the following. Mechanical only; it prevents drift, it does not
establish that either sentence is true — the audit in §2 does that.

| Token | Chinese | English | | Token | Chinese | English |
|---|---|---|---|---|---|---|
| `54` | ✓ | ✓ | | `0.76` | ✓ | ✓ |
| `42` | ✓ | ✓ | | `0.31` | ✓ | ✓ |
| `12` | ✓ | ✓ | | `0.36` | ✓ | ✓ |
| `jev-1.13.0` | ✓ | ✓ | | `0.56` | ✓ | ✓ |
| `4.2647` | ✓ | ✓ | | `80.4` | ✓ | ✓ |
| `76.55` | ✓ | ✓ | | `71.4` | ✓ | ✓ |
| `0.75` | ✓ | ✓ | | `0.05` | ✓ | ✓ |
| `0.20` | ✓ | ✓ | | `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION` | ✓ | ✓ |
| `0.55` | ✓ | ✓ | | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET` | ✓ | ✓ |

18 of 18 tokens present in both languages. **Gate: PASS.**

---

## 5. Claims deliberately excluded, and how

These are the contract's class C statements — available at no scope, because no qualifier can create
the missing evidence. Each was excluded by construction, not caught in review:

| Excluded | Where both articles refuse it |
|---|---|
| Jev is generally more (or less) accurate than anything | §14 first bullet: no ground truth exists anywhere in the bench; "4 / 4" is a count, never a rate |
| This project validated or falsified calibration | §12.2: neither direction; 2 cases, no reliability diagram, no ECE, no Brier score |
| Jev is deterministic — or non-deterministic | §14: a few repeats on two payloads is not a verdict in either direction |
| Jev is universally 4.26× cheaper | §5: one payload, five questions sharing one state; not a general ratio and not comparable to the vendor figure |
| A general instruction-vs-criteria field preference | §10: the null, plus two explicitly refused summaries and `FIELD_ALIGNMENT_CAVEAT` |
| Jev is suitable for NAS (or any workload never run here) | §15: no NAS experiment, dataset or measurement exists |
| These observations are novel discoveries | §16: the state string, quoted; and §6, where the two largest effects are killed on prior art |
| Jev cannot hallucinate / these results certify schema safety | §2, §14: schema conformance on benign payloads is the only axis measured |
| This pattern is safe for production | §12.3: every handler is inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` |
| A vendor figure is "really" our number, or the reverse | §5: the two are not commensurable; the vendor figure describes a different workload |
| Jev is fast, with any figure attached | §14: latency is recorded, not benchmarked; no speedup is claimed |
| The four scoring dimensions are independent | Not asserted anywhere; §12.2 describes one composite without any independence claim |
| This release is peer-reviewed, endorsed, or a standard | Not asserted; §16 links the claim contract that forecloses it |
| The retired designs were run | §13: retired before publication, never run |

Two exclusions worth naming, because they were the most tempting in English prose as well:

- **The vendor's 12.2× vs the local 4.2647× juxtaposition.** Available in raw form, and it is exactly
  the shape of a viral chart. §5 gives both figures *with their sources* and then states they are not
  commensurable — the two numbers appear in the same paragraph only so the refusal has something to
  refuse.
- **"Stable label, moving distribution" as a discovery.** §6 keeps the observation and kills it in
  the same subsection, on prior art, before a reader can get attached to it.

---

## 6. Self-check from the contract

The contract's own seven-item list, run against both articles:

1. **Is every figure labelled** as OFFICIAL CLAIM, LOCAL MEASUREMENT or DERIVED CALCULATION? —
   Yes, in natural language rather than as tags, in both languages: 官方文档/厂商/"the docs report"…,
   我在…上测得…/"the local measurement…", 由这两个数可以直接算出…/"from those two numbers…".
2. **Does every figure keep its scope** — payload, repeat count, session, model version? — Yes in
   both languages; see the scope columns above. The two places where the scope was thinnest (§2's
   45/45 and §9's endpoint replication) are tightened in both.
3. **Does any sentence read bigger with the qualifier deleted?** — Four did, and all four were
   rewritten in the Chinese and never appeared in the English (§1.2 above).
4. **Is the null result in it?** — Yes in both: §9 gives the raw values, §10 is the null, §11 the
   defect. The P3 null is roughly a quarter of each article.
5. **Does it say `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** where a reader will see it? — Yes, §16
   in a fenced block in both, restated in prose around it in both.
6. **Would any sentence change if a TypeSafe engineer read it?** — No sentence was softened in
   either language for that reason. Two vendor-side observations (§6's threshold divergence, §12.4's
   price-table inversion) are included *because* they are unflattering to a naive framing, and are
   sourced to the vendor's own published material.
7. **Does it say what this is not?** — Yes, §14 is a dedicated non-claims section with nine items, in
   both languages.

---

## 7. What this audit does not cover

- **Prose quality, structure and audience fit.** The English article is an adaptation rather than a
  translation, so its sentences do not correspond one-to-one with the Chinese. Those are editorial
  questions, not claim-integrity ones, and nothing here should be read as endorsing them. What is
  audited is that no sentence in either language claims more than its evidence carries.
- **The editorial changes made to the Chinese in this revision** beyond §1.2. The four listed
  sentences are the ones that changed a claim's scope or precision; they are the ones this audit
  re-examined. No new scientific content was added to either article.
- **The frozen evidence itself.** This audit checks both articles *against* `v0.1.0`. It does not
  re-open the release's own claims, which are frozen and immutable.

**No new evidence defect was found while adapting or auditing either draft.** No
`P5_NEW_EVIDENCE_DEFECT_FOUND` condition arose: every figure checked against the canonical logs
matched, and no frozen artifact was modified.
