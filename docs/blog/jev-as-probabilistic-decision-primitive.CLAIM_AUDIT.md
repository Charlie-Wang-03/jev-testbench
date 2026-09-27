# Claim audit — the technical blog

**Audited document:** [`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md)
(the Chinese text). It was rewritten in P5-D as a narrative: the section headings are gone, the
material is re-ordered, and new first-person framing was added.
**Second document, tracked but not re-audited:**
[`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md)
(the English adaptation). **It is frozen and was not modified in P5-D.** Its column below records
what revision 2 established about it and is carried forward unchanged.
**Standard:** [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md)
**Evidence base:** release `v0.1.0` — [`PUBLIC_EVIDENCE_FREEZE.md`](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md),
[`evidence-manifest.json`](../evidence/v0.1.0/evidence-manifest.json), and the two canonical logs.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 3 — Chinese narrative rewrite. Supersedes revision 2 (bilingual, P5-B).

**What this file is.** Every substantive claim in the Chinese article, classified against the
contract's three classes — `A` (`SAFE_TO_STATE`), `B` (`SAFE_WITH_SCOPE`), `C` (`DO_NOT_STATE`) —
with the evidence it rests on, where it sits in the article, and whether the scope that class
requires is actually present. It exists so a reader can check the article without re-reading the
entire evidence set.

**How the numbers were checked.** Every figure was re-derived from `results/usage.jsonl` and
`results/p3_boundary_locus/usage.jsonl`, not copied from the work order that commissioned the
rewrite and not copied from the freeze document's prose. Where a work order and the frozen evidence
could disagree, the frozen evidence governed. They did not disagree.

---

## 1. What changed in this revision

### 1.1 The rewrite did not touch the evidence, and the audit is how that is checked

P5-D rewrote the Chinese article end to end: new opening, new order, no section headings, a
different voice. A rewrite of that size is exactly the kind of change that moves a claim without
anyone intending it — a scope clause dropped while compressing, a hedge lost to a shorter sentence,
an observation promoted to a finding because the new shape wanted a payoff. That is what this
revision exists to catch.

**The rewrite changed the prose, and it changed two claims' worth of content. Both are removals,
and both are recorded in §1.2.** Everything else in the article is the same set of statements the
P5-A audit already passed, said differently.

### 1.2 Two rows leave the article, and one count changes

| Row | Was | Status in the rewritten Chinese | Why |
|---|---|---|---|
| C-02 | The vendor positioning line, *"Think of Jev as a frontier-intelligence function call…"* | **Removed.** Not quoted anywhere in the article now. | Editorial only. It was class `A` and true; dropping a safe claim is never a contract defect. The rewrite opens on the author's curiosity instead of on the vendor's sentence. |
| C-56 | `05_speculative_fanout`: 4 of 12 speculative answers unconsumed, input down 400 tokens, output priced at zero | **Removed.** | The P5-D work order folded batching economics into the batching section and compressed the lessons to three paragraphs. The removal is authorised by that instruction, and the claim was class `A` in any case. |

**One count changed direction, and it is a tightening.** The `04_confidence` threshold narrative now
reads `0.61 大于等于 0.60` rather than `0.61 正好越过 0.60 门槛`. Both are true of the record, and
the new form is the one that cannot be read as the model having *chosen* to cross a line.

**No claim in the article was strengthened, and no scope was dropped while compressing.** The two
places where compression was most likely to cost a scope — the batching ratio's payload boundary and
the `4 / 4` routing count — carry the same scope they carried in revision 2, in both cases in the
same paragraph as the number.

### 1.3 The English document is frozen, and this audit no longer treats the pair as symmetric

Revision 2 audited two documents as a publication pair, each with its own scope column, on the
grounds that an adaptation carries its own contract obligations. That reasoning has not been
withdrawn. What changed is the building: the Chinese was rewritten and the English was not.

So the English column below records the **frozen P5-B adaptation**, unchanged since revision 2, and
its scope entries remain valid *for that text*. They are not evidence about the rewritten Chinese,
and this revision makes no claim that the two still correspond. Rows C-65 through C-70 are new
framing that exists only in the Chinese; they carry `—` in the English column, which in this
revision means **"not present in the frozen English"** and is expected rather than a defect.

The publication index records the same status in one line: *English adaptation pending re-alignment
after Chinese narrative rewrite.* `ENGLISH_REALIGNMENT: NOT_STARTED`.

---

## 2. The audit

**Column key.** *ZH* gives the location in the rewritten Chinese, by named anchor, since the article
no longer has numbered sections. *EN* gives the section of the frozen English adaptation in that
document's own numbering, or `—` where the statement is not in it. *Scope* is `yes` (the class-B
scope is present in the same or immediately adjacent sentence), `n/a` (the class does not require
one), or `MISSING` (the claim would be a defect).

| Claim ID | Semantic claim | Contract class | Evidence | Chinese | English | Scope in ZH | Scope in EN | Verdict |
|---|---|---|---|---|---|---|---|---|
| C-01 | 54 API calls in total | A — the release | 42 core + 12 P3 records in the two frozen logs | 开头, 测量台 | intro, §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-03 | **The release reached `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** | **B** — anything about novelty | Freeze §5.3; `BLOG_CLAIM_CONTRACT.md` novelty rule | 开头, 结尾 | intro, §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-04 | A Jev call is `state + typed questions → typed answers`; all questions see the same state and are evaluated independently | A — official, attributed | `TS-DOC-STATE` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-05 | `Choice` returns a label plus a distribution over options; `probabilities` sum to 1; `choice` is the argmax | A — official + reproduced | `TS-DOC-CHOICE` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-06 | `Score` returns a value plus `confidence`, defined as the probability-weighted mean of the levels | A — official | `TS-DOC-SCORE` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-07 | `Noul` is a single probability with no separate `confidence`; **45 of 45** locally | B — typed output semantics; the 45/45 count needs the erratum | Log: `noul` carrying `confidence`: **0**. `ERR-001` | 背景, 勘误 | §2, §11 | yes | yes | `SAFE_WITH_SCOPE` |
| C-08 | One `01_primitives` answer had winning probability 0.45 and confidence 0.26 | A — a named single record | Log: `01_primitives`/`department`, `choice: other`, `0.45` / `0.26` | 背景 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-09 | Typed output solves the schema problem, not the semantic one | A — non-claim | `NO_BROAD_HALLUCINATION_BENCHMARK`, `NO_GENERAL_ACCURACY_CLAIM` | 背景 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-10 | The vendor's known-limitations page lists literal reading, weak numerics, date comparison, indirection, large state, and puts control flow in code | A — official, attributed | `TS-DOC-JAG`, `TS-DOC-BUILD` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-11 | Vendor figures are claims about *their* workload; only a log line is a local measurement | A — repository practice | Freeze §7, no vendor-claim adjudication | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-12 | The two logs' SHA-256 are `38e67630…` / `17f36f75…` and never changed | A — canonical log identity | Freeze §3; re-hashed during this audit | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-13 | 42 records requested `jev-latest` and resolved `jev-1.13.0` | A — provenance | Log: `model_resolved = jev-1.13.0` on 42/42 | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-14 | CI regenerates derived artifacts and fails on any difference | A — engineering | `.github/workflows/ci.yml`; freeze §5.2 | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-15 | The 54 calls cost ≈ **$0.001** by local estimate | B — cost figures | Sum of `estimated_cost_usd` over both logs = `0.001084566` | 测量台 | §3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-16 | 10 registered experiments, all executed, 42 core records | A — registry | Freeze §4; `EXPERIMENT_REGISTRY.md` | 批处理 | §4 | n/a | n/a | `SAFE_TO_STATE` |
| C-17 | `04_confidence` has 2 cases; `12_function_routing` makes 4 calls | A — registry | Registry tables | 路由, 三条经验 | §4 | yes | yes | `SAFE_TO_STATE` |
| C-18 | None of the 10 left a conclusion both new relative to TypeSafe's public material and supported by the data | **B** — novelty, scoped | P2 §6; freeze §5.3 | 七个候选 | §4 | yes | yes | `SAFE_WITH_SCOPE` |
| C-19 | Batching: 816 vs **3,480** input tokens; **4.2647×**; **76.55%** saved | B — batching ratio | Log: batched `[408, 408]`; separate sum `3480`; ratio `4.2647` | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-20 | 10/10 selected values identical, largest absolute difference 0.0 | B — same row | Log: the five values repeat across both cycles and both arms | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-21 | The local 4.26× must not be compared with the vendor's 12.2× | A — contract rule | `BLOG_CLAIM_CONTRACT.md` class B; P1 audit | 批处理 | §5 | yes | yes | `SAFE_TO_STATE` |
| C-22 | Public third-party measurements varied batch size and published an accuracy curve | B — third-party, cited as third-party | P2 §4.1 (D), P2 §7 `BLOG_CORE` | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-23 | 13b: label unchanged 5/5; top-2 margin moved ≤ 0.07; `Score` 1.58–1.63; `confidence` 0.24–0.30; one exact tie | B — local measurement + a novelty claim that may only be scoped | Log: margins `0.07, 0.06, 0.02, 0.03, 0.00`; scores `1.58–1.63`; `department` confidences `0.24–0.30`; `ambiguous_5` `other 0.45 = billing 0.45` | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-24 | Official cookbook reports label flips on 2 of 8 questions and per-label std dev (mean 0.0098, max 0.0515) | B — official, attributed | P2 §4.1 (A); the vendor cookbook | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-25 | A public chaos test sent the identical request five times and got `0.03, 0.03, 0.03, 0.04, 0.04`, with jitter floors over ~1,490 calls | B — third-party, cited as third-party | P2 §4.8 | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-26 | The 0.60 gate is this repository's own constant, labelled a demonstration threshold, never calibrated | B — our own policy | `experiments.py` `CONFIDENCE_GATE_THRESHOLD`; P2 §4.1 (C) | 0.61 门槛 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-27 | The ambiguous case returned 0.61 against a 0.74 vs 0.26 margin; the published k=3 expression reproduces 0.61 exactly | B — local measurement + derived | The `04` record; P2 §4.1 (C) | 0.61 门槛 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-28 | Two official pages use different `confidence` thresholds for the same worked example, and both say thresholds are domain-specific | A — official sources; a recorded divergence | Freeze §8; `TS-DOC-CONF` vs `TS-DOC-CONFROUTE` | 0.61 门槛 | §6 | yes | yes | `SAFE_TO_STATE` |
| C-29 | Routing: 4/4 function matches, 4/4 argument matches, 4/4 suppressed, handler never entered | B — our architecture | The `12` records; P2 §4.1 (G) | 路由, 三条经验 | §6, §12.3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-30 | Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a 0.8 floor; the 1.0 case withheld by `needs_human_review` 0.94 ≥ 0.5 | B — our own policy; thresholds are demonstration parameters | Log: the four `function` answers carry those confidences; `needs_human_review` = 0.94 | 路由 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-31 | `07`: an 82-byte byte-identical state, `Noul` 0.75 → 0.20, a 0.55 move | B — the `07` illustration | Log: `state_utf8_bytes = 82`; vague `0.75`, explicit `0.20` | 07 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-32 | The official remedy for the literal-reading edge is given as a bundle and never decomposed | A — official | `TS-DOC-JAG`; P2 §4.3 | 07 | §7 | yes | yes | `SAFE_TO_STATE` |
| C-33 | The novelty check returned `PUBLIC_NOVELTY_UNRESOLVED`, recorded as unresolved, never as "nobody has done this" | B — anything about novelty | P2 §4.8 | 七个候选 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-34 | It was the only question that passed triage and was worth spending calls on | B — novelty | P2 §5: exactly one `R_GO` candidate | 七个候选 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-35 | Design, order, statistics and thresholds were committed before the first request | A — preregistration | Freeze §5.1; `db7d06f` | P3 设计 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-36 | A 2×2 of the two fields, 3 repeats per arm, 12 calls, declared as a hard ceiling | A — preregistration | `P3_BOUNDARY_LOCUS_PREREGISTRATION.md` §9; freeze §6.1 | P3 设计 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-37 | The pre-registered design hazard: the crossed arms must state the same boundary | A — preregistration | Preregistration §9 | P3 设计 | §8 | n/a | n/a | `SAFE_TO_STATE` |
| C-38 | P3 raw values, medians and ranges for all four arms | A — local measurement | P3 log: `N` 0.77/0.76/0.75; `I` 0.31/0.33/0.29; `C` 0.37/0.36/0.33; `B` 0.20/0.21/0.20 | P3 结果 | §9 | n/a | n/a | `SAFE_TO_STATE` |
| C-39 | The endpoints replicated the original observation: 0.76 → 0.20, gap 0.56 | B — endpoint replication | P3 log; original `07` values | P3 结果 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-40 | Instruction-only recovered 80.4% of the gap; criteria-only 71.4% | B — descriptive arithmetic, not part of the decision rule | Derived from the medians: `0.45/0.56`, `0.40/0.56` | P3 结果 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-41 | The two single-field arms are 0.05 apart, below the pre-registered 0.10, so K1 fired | B — the separation that killed the attribution | P3 log; freeze §6.1 | P3 结果 | §9 | yes | yes | `SAFE_WITH_SCOPE` |
| C-42 | `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`; the effect could not be attributed to either field alone | A — primary null | Freeze §6.1; P3 result §3 | P3 结果 | §9 | n/a | n/a | `SAFE_TO_STATE` |
| C-43 | The large effect replicated; the *attribution* is what failed | A — the null, stated correctly | P3 result §4 | 负结果 | §10 | n/a | n/a | `SAFE_TO_STATE` |
| C-44 | Two summaries are explicitly refused: "the boundary lives in both fields" and "criteria are what matter" | A — refusals | Freeze §6.1 names both as the two wrong summaries | 负结果 | §10 | n/a | n/a | `SAFE_TO_STATE` |
| C-45 | `FIELD_ALIGNMENT_CAVEAT` limits the result to this mixed-specificity construction | A — caveat | Freeze §6.1; P3 result §7 | 负结果 | §10 | yes | yes | `SAFE_TO_STATE` |
| C-46 | **n = 3 per arm** supports a median and a range and no interval estimate | A — caveat | Freeze §6.1 | 负结果 | §10 | yes | yes | `SAFE_TO_STATE` |
| C-47 | The analyzer defect, its disclosure in the commit that recorded the measurement, its post-run repair, the deliberate preservation of the incorrect rendering in Git history, and the invariance of every measurement, threshold and verdict | A — engineering + provenance | `ERR-002`; P3 result, "Post-run analyzer correction provenance" | 分析器 | §11 | n/a | n/a | `SAFE_TO_STATE` |
| C-48 | `ERR-001`: P1 states 42 of 42; the correct figure is 45 of 45; P1's text was not edited | B — the corrected count, which requires citing the erratum | Log recount; `ERRATA.md` | 勘误 | §11 | yes | yes | `SAFE_WITH_SCOPE` |
| C-49 | The 42 records carry 119 answers between them | A — canonical log | Log: 119 answers total | 勘误 | §11 | n/a | n/a | `SAFE_TO_STATE` |
| C-50 | 42/42 responses were schema-valid; that is the weakest kind of type-safety evidence | A — non-claim | `findings.md` §1 | 三条经验 | §12.1 | yes | yes | `SAFE_TO_STATE` |
| C-51 | In `06_composite_scoring`, one dimension scored 1.62 on a 0–3 rubric at confidence 0.24 and carried 97.4% of that state's composite risk | A — local measurement, one named case | Log: `evidence_quality` raw 1.62, confidence 0.24; recomputed share **97.41%** | 三条经验 | §12.2 | n/a | n/a | `SAFE_TO_STATE` |
| C-52 | Official calibration is group-scoped; confidence "describes the model's answer, not a guarantee that the answer is correct" | A — official, attributed | `TS-DOC-SYS1`, `TS-DOC-CONF` | 三条经验 | §12.2 | yes | yes | `SAFE_TO_STATE` |
| C-53 | This project neither validated nor falsified calibration, in either direction | A — non-claim | `NO_CALIBRATION_VALIDATION` | 三条经验 | §12.2 | n/a | n/a | `SAFE_TO_STATE` |
| C-54 | Semantic routing ≠ execution authorization; 4/4 is a count not a rate; handlers are inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` | A — our architecture + non-claims | `findings.md` §2; `12` records | 三条经验 | §12.3 | yes | yes | `SAFE_TO_STATE` |
| C-55 | Batch economics are workload-dependent; amortisation needs a shared state | A — scope restated | Freeze §5.1 | 批处理 | §12.4 | yes | yes | `SAFE_TO_STATE` |
| C-57 | `retry_count` is permanently `null` and means "not reported"; `transport_attempt_count` licenses exactly one sentence | A — engineering limitation | Freeze §3.3; `findings.md` §2 | 三条经验 | §12.6 | yes | yes | `SAFE_TO_STATE` |
| C-58 | Five registered designs were retired before publication, never run | A — the inverse of the contract's `DO_NOT_STATE` row | Freeze §4; `EXPERIMENT_REGISTRY.md` | 退休实验 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-59 | `10_state_length`'s three defects: no ground truth, n = 1 per tier, and filler that repeats five sentences rather than accumulating content | A — registry reasoning | Registry entry for `10_state_length` | 退休实验 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-60 | `11_language_pair`'s four reasons, including that the official docs state English is primary and CJK currently has lower accuracy | A + official, attributed | Registry entry for `11_language_pair`; `TS-DOC-STATE` | 退休实验 | §13 | yes | yes | `SAFE_TO_STATE` |
| C-61 | The nine non-claims, in natural prose rather than as markers | A — non-claims | Freeze §7 | 非声明 | §14 | n/a | n/a | `SAFE_TO_STATE` |
| C-62 | No NAS experiment, dataset or measurement exists here; NAS is a future question to be re-derived from NAS task structure | A — non-claim | `NO_NAS_CLAIM`; freeze §7 | NAS | §15 | n/a | n/a | `SAFE_TO_STATE` |
| C-63 | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`; every large local effect restates a documented behaviour or is this repository's own policy | **B** — state of the science, stated as novelty | Freeze §5.3 | 结尾 | §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-64 | License: MIT | A — release fact | `LICENSE`; `pyproject.toml` | 附录 | §16 | n/a | n/a | `SAFE_TO_STATE` |
| C-65 | First-person framing of the author's own work: the opening curiosity about typed output; not wanting to run a design twice; finding the analyzer defect awkward rather than heroic; still wanting to look at NAS | A — first-person, no product claim | The P5-D work order §11, §17, §30; every item traces to work actually done and recorded | 开头, 测量台, 分析器, NAS | — | n/a | n/a | `SAFE_TO_STATE` |
| C-66 | The narrative device: seven candidate findings were written up and then deleted; the most attractive ones died first, and none was kept or killed for how it looked | **B** — novelty-adjacent | P2 §5–§6: seven triage candidates, all retired; the two largest effects fell on prior art | 开头, 七个候选, 结尾 | — | yes | n/a | `SAFE_WITH_SCOPE` |
| C-67 | Method claims about this bench: an evaluation repository's job is to delete the stories its evidence cannot carry; what it accumulates is that ability | A — methodology opinion about the bench, not about Jev | Freeze §5.3; the P2 triage outcome | 结尾 | — | n/a | n/a | `SAFE_TO_STATE` |
| C-68 | The project reads as training in model evaluation and agent engineering rather than as a model benchmark, and most of the learning was not on Jev's side | A — the author's own assessment | The author's first-hand account of the work | 结尾 | §16 | n/a | n/a | `SAFE_TO_STATE` |
| C-69 | Not looking for applications because you already hold the tool | A — aphorism attached to the NAS non-claim | The NAS non-claim is C-62; this adds no factual content | NAS | — | n/a | n/a | `SAFE_TO_STATE` |
| C-70 | The author is willing to put a name to the frozen state string | **B** — novelty-adjacent | Freeze §5.3; the string is quoted in the same paragraph and restated in scope around it | 结尾 | — | yes | n/a | `SAFE_WITH_SCOPE` |
| C-71 | No adjudication of vendor claims: incommensurable, not "the vendor is wrong" and not "the local run proves them right" | A — contract rule | `BLOG_CLAIM_CONTRACT.md`; P1 audit | 非声明 | §14 | n/a | n/a | `SAFE_TO_STATE` |
| C-72 | Every state is synthetic; there is no real personal, customer or proprietary data here | A — contract rule | Repository practice; freeze §7 | 非声明 | §14 | n/a | n/a | `SAFE_TO_STATE` |

---

## 3. Totals

| Verdict | Chinese | English (frozen r2) |
|---|---:|---:|
| `SAFE_TO_STATE` | **46** | **42** |
| `SAFE_WITH_SCOPE` | **24** | **22** |
| `DO_NOT_STATE` | **0** | **0** |
| **Substantive claims audited** | **70** | **64** |

**`DO_NOT_STATE_ZH = 0`.** Nothing in the rewritten article had to be deleted or rewritten for
asserting something the evidence does not carry. That is the headline result of this revision: the
rewrite was free to reshape the prose as it liked, and it did not manufacture a claim in the process.

**Every one of the 70 rows carries `yes` or `n/a` in the Chinese scope column.** No row is `MISSING`.
The six rows added in this revision are class `A` except C-66 and C-70, both of which are
novelty-adjacent and both of which carry their scope.

**The English total stays at 64** because the English document did not change. The 6-row difference
is the six new Chinese framing rows, four of which (`C-65`, `C-67`, `C-69`, `C-70`) have no English
presence at all and two of which (`C-66` partly, `C-68`) map onto English sentences that revision 2
already covered under other rows. **This is a consequence of the freeze, not a parity result**, and
it is why §4's parity gate is reported as suspended rather than passed.

---

## 4. The two mechanical parity gates

These checks exist to prevent drift between the languages. **Both are affected by the freeze, and
neither may be reported as passing across the pair.**

### 4.1 Novelty parity — **within the Chinese: PASS. Across the pair: SUSPENDED**

The Chinese article may not contain an equivalent of *"nothing new about Jev"*, *"no novelty
exists"*, *"nobody has done this"*, or *"we discovered a novel Jev behaviour"*.

| Pattern | Chinese | Frozen English |
|---|---|---|
| nothing new about Jev / 没有发现任何关于 Jev 的新东西 | absent | absent |
| no novelty exists / 不存在新颖性 | absent | absent |
| nobody has done this / 没有人做过 | **only in the refusal** — 我把它记成「未解决」，而不是「没有人做过」 | **only in the refusal** — §7 |
| we discovered a novel Jev behaviour | absent | absent |

The third row is a true positive for the pattern and a pass for the gate: the phrase appears **only
to refuse it**, in the sentence stating what `PUBLIC_NOVELTY_UNRESOLVED` does and does not mean.

**Within the Chinese: PASS.** The article states the frozen state string in a fenced block in the
closing movement, where a reader will see it, and restates it in scope around the block.

**The cross-language half of this gate is SUSPENDED, not passed.** It originally checked that both
articles said the same scoped thing about novelty. With the English frozen and the Chinese rewritten,
that check would compare two texts that are not currently aligned, and reporting it as a pass would
be reporting the wrong thing. `ENGLISH_REALIGNMENT: NOT_STARTED`.

### 4.2 Bilingual factual parity — **SUSPENDED**

Revision 2 checked 18 tokens in both languages. **That check is suspended for this revision**, for
the same reason: its subject is a pair that is not currently aligned. The Chinese article was
verified to contain all 18 tokens, so no figure was lost in the rewrite, but the gate as a parity
gate is not reported as passing.

| Token | Chinese | | Token | Chinese |
|---|---|---|---|---|
| `54` | ✓ | | `0.76` | ✓ |
| `42` | ✓ | | `0.31` | ✓ |
| `12` | ✓ | | `0.36` | ✓ |
| `jev-1.13.0` | ✓ | | `0.56` | ✓ |
| `4.2647` | ✓ | | `80.4` | ✓ |
| `76.55` | ✓ | | `71.4` | ✓ |
| `0.75` | ✓ | | `0.05` | ✓ |
| `0.20` | ✓ | | `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION` | ✓ |
| `0.55` | ✓ | | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET` | ✓ |

9 of 9 first-column tokens and 9 of 9 second-column tokens present in the Chinese. The frozen English
still contains all 18 as of revision 2, and nothing in P5-D touched it.

---

## 5. Claims deliberately excluded, and how

These are the contract's class C statements — available at no scope, because no qualifier can create
the missing evidence. Each was excluded by construction, not caught in review:

| Excluded | Where the Chinese article refuses it |
|---|---|
| Jev is generally more (or less) accurate than anything | 非声明: no ground truth exists anywhere in the bench; "4 / 4" is a count, never a rate |
| This project validated or falsified calibration | 三条经验: neither direction; 2 cases, no reliability diagram, no ECE, no Brier score |
| Jev is deterministic — or non-deterministic | 非声明: a few repeats on two payloads is not a verdict in either direction |
| Jev is universally 4.26× cheaper | 批处理: one payload, five questions sharing one state; not a general ratio and not comparable to the vendor figure |
| A general instruction-vs-criteria field preference | 负结果: the null, plus two explicitly refused summaries and `FIELD_ALIGNMENT_CAVEAT` |
| Jev is suitable for NAS (or any workload never run here) | NAS: no NAS experiment, dataset or measurement exists |
| These observations are novel discoveries | 结尾: the state string, quoted; and 七个候选, where the two largest effects are killed on prior art |
| Jev cannot hallucinate / these results certify schema safety | 背景, 非声明: schema conformance on benign payloads is the only axis measured |
| This pattern is safe for production | 三条经验: every handler is inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` |
| A vendor figure is "really" our number, or the reverse | 批处理: the two are not commensurable; the vendor figure describes a different workload |
| Jev is fast, with any figure attached | 非声明: latency is recorded, not benchmarked; no speedup is claimed |
| The four scoring dimensions are independent | Not asserted anywhere; 三条经验 describes one composite without any independence claim |
| This release is peer-reviewed, endorsed, or a standard | Not asserted; 非声明 links the claim contract that forecloses it |
| The retired designs were run | 退休实验: retired before publication, never run |

Two exclusions worth naming, because the rewrite made them *more* tempting rather than less:

- **The vendor's 12.2× vs the local 4.2647×.** The rewrite gave this a whole rhetorical movement —
  three attractive numbers, then a one-word paragraph, then the dismantling. §5 is where a
  chart-driven article would stop. The Chinese keeps both figures *with their sources* and then
  states they are not commensurable, so the two numbers appear in the same paragraph only so the
  refusal has something to refuse.
- **The 删故事 device as a finding.** C-66 is filed class `B` and not class `A` precisely because
  "seven stories were deleted" is one compression away from "seven discoveries were disproved",
  which would be false. The article keeps it as a statement about the candidate list, and the
  scope column records where.

---

## 6. Self-check from the contract

The contract's own seven-item list, run against the rewritten Chinese:

1. **Is every figure labelled** as OFFICIAL CLAIM, LOCAL MEASUREMENT or DERIVED CALCULATION? — Yes,
   in natural language rather than as tags: 官方文档 / 厂商 / TypeSafe 自己的文档, 我在…上测得 /
   我跑完的, 由这两个数可以直接算出 / 相当于.
2. **Does every figure keep its scope** — payload, repeat count, session, model version? — Yes; see
   the scope column. The two thinnest places in revision 2 (the 45/45 count and the endpoint
   replication) are still scoped after the rewrite.
3. **Does any sentence read bigger with the qualifier deleted?** — This is the check the rewrite was
   most exposed to, and one sentence was rewritten because of it: `0.61 正好越过 0.60 门槛` became
   `0.61 大于等于 0.60`, which states the arithmetic rather than implying a decision. §1.2.
4. **Is the null result in it?** — Yes, and it is now the article's structural climax rather than one
   section among sixteen: the raw values table, the K1 separation, the null, and the analyzer defect.
   The P3 material is roughly a third of the rewrite.
5. **Does it say `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** where a reader will see it? — Yes, in a
   fenced block near the end, restated in scope around the block.
6. **Would any sentence change if a TypeSafe engineer read it?** — No sentence was softened for that
   reason. The two vendor-side observations kept in the rewrite (the threshold divergence, and the
   documented flakiness) are sourced to the vendor's own published material.
7. **Does it say what this is not?** — Yes, in prose rather than as a marker list, per the P5-D
   instruction to compress nine bullets into a few paragraphs.

---

## 7. What this audit does not cover

- **Prose quality, style and audience fit.** P5-D changed these deliberately and at length. They are
  audited separately in
  [`jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md),
  and nothing in this file should be read as endorsing them. What is audited here is that no sentence
  claims more than its evidence carries.
- **The frozen English document.** It was not read for revision, not re-scoped, and not re-aligned.
  Its column in §2 is revision 2's finding carried forward. Any statement here about the English is a
  statement about the text as it stood at P5-B.
- **The frozen evidence itself.** This audit checks the article *against* `v0.1.0`. It does not
  re-open the release's own claims, which are frozen and immutable.

**No new evidence defect was found during the rewrite or this audit.** No `P5_NEW_EVIDENCE_DEFECT_FOUND`
condition arose: every figure checked against the canonical logs matched, both canonical logs are
byte-identical to their frozen hashes, and no frozen artifact was modified.
