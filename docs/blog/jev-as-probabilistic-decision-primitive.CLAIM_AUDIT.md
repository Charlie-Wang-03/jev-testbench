# Claim audit — the technical blog

**Audited document:** [`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md)
(the Chinese text). It was rewritten as a narrative in P5-D, revised in P5-E (five human-review-confirmed
factual repairs, a reduction in punchline density, and a new closing movement on AI involvement and
cognitive debt), and corrected again in P5-E1 — nine narrowly-scoped editorial corrections, no structural
change, followed by three one-line micro corrections and one further correction that closes the reading
risk the third of those opened. **It then had a scope cleanup that removed two matters the project no
longer covers** — the internal governance status at the top of the article, and the whole NAS topic. §1.5
through §1.7 record what each pass changed and which rows it moved.
**Second document, tracked but not re-audited:**
[`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md)
(the English adaptation). **It is frozen and was not modified in P5-D, P5-E or P5-E1.** The P5-E1
corrections were applied to the Chinese only, and the English blob is byte-identical to its P5-B state.
Its column below records
what revision 2 established about it and is carried forward unchanged.
**Standard:** [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md)
**Evidence base:** release `v0.1.0` — [`PUBLIC_EVIDENCE_FREEZE.md`](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md),
[`evidence-manifest.json`](../evidence/v0.1.0/evidence-manifest.json), and the two canonical logs.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 8 — the blog boundary cleanup. The article lost its header governance note and all of its NAS
material, so C-62 and C-69 are retired here and C-65 is narrowed. **This is the first revision in which the
totals table goes down**: 73 rows to 71, with no new row and no verdict flip. Supersedes revision 7, which
resolved the antecedent reading risk revision 6 recorded and moved no figure.

**What this file is.** Every substantive claim in the Chinese article **about Jev, about this bench's
measurements, or about what TypeSafe has published**, classified against the contract's three classes —
`A` (`SAFE_TO_STATE`), `B` (`SAFE_WITH_SCOPE`), `C` (`DO_NOT_STATE`) — with the evidence it rests on,
where it sits in the article, and whether the scope that class requires is actually present.

**What it deliberately does not cover.** The article's process statements — who built this, who ran the
calls, what cognitive debt is — are **outside this contract by construction**, and §5 records that
separation rather than stretching the contract to reach them. They are audited in
[`…PROCESS_ATTRIBUTION_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md)
against the owner's process declaration.

**How the numbers were checked.** Every figure was re-derived from `results/usage.jsonl` and
`results/p3_boundary_locus/usage.jsonl`, not copied from the work order that commissioned the revision
and not copied from the freeze document's prose. Where a work order and the frozen evidence could
disagree, the frozen evidence governed. They did not disagree.

---

## 1. What changed in this revision

### 1.1 Five factual repairs, all confirmed by human editorial review

P5-E applied five repairs the human reviewer had confirmed as defects. Each is recorded here because
each one changed what the article is permitted to assert, and one of them changed a contract class.

| Repair | Was | Now | Effect on the audit |
|---|---|---|---|
| **A. Probability table** | 表里的数加起来是 1 | 展示层是量化过的，按两位小数显示时个别记录相加不严格等于 1；分布语义本身不变 | **C-05 moves `A` → `B`.** Dropping the new caveat would make the sentence false, which is the `B` criterion. Verified locally: **1 of 74** Choice answers in the 42 core records sums to `0.99` at two decimals. |
| **B. Story classification** | 效应最大的两个…两次都是「别人公开做过」决定了它们的命运 | Split: batching and repeatability were demoted by official/public prior art; the 0.61 gate and the routing blocks **were never Jev findings** but this bench's own policy and thresholds | **C-66 re-scoped.** The old sentence attributed one cause to four candidates that fell for two different reasons. |
| **C. MIT wording** | 代码、两个 canonical 日志和派生报告都覆盖在同一份许可下 | 项目采用 MIT License。见 `LICENSE` | C-64 unchanged in class; a scope claim about the *evidence* was deleted rather than narrowed. |
| **D. Psychological and biographical assertions** | 我当时冒出来的问题特别朴素 / 我当时是真的觉得这条挺有意思 / 我第一反应是想赶紧写点什么 / 我不是第一次做实验 | Stated about the material or the process, or deleted: 一开始的疑问很朴素 / 这条在四个候选里看起来最有意思 / 这个效应大到足以让人立刻动笔 | Not a contract change — these were never Jev claims. Recorded in the process attribution audit §4, overrides §6. |
| **E. "Nobody will check"** | 没人会去查 | 如果不把 evidence layer 单独分出来，这种讲法很容易显得合理 | C-11's scope sharpened; the generalisation about readers is gone. |

### 1.2 The repairs did not cost any figure, and the token check proves it

All 18 figures carried by revision 3 are still in the article, in the same scope. §4.2 lists them.

### 1.3 One movement was added, and it is outside this contract

The closing movement — the AI-involvement disclosure and the cognitive-debt working concept — is new in
P5-E and is **not entered as rows below**. §5 states why. The short version: the contract's question is
what the evidence carries about Jev, and none of that material is about Jev.

### 1.4 The English document is frozen, and the audit no longer treats the pair as symmetric

Revision 2 audited two documents as a publication pair, each with its own scope column. That reasoning
has not been withdrawn; what changed is the building. The Chinese has now been rewritten twice and the
English has not been touched since P5-B.

So the English column below records the **frozen P5-B adaptation**, unchanged since revision 2, and its
scope entries remain valid *for that text*. They are not evidence about the current Chinese, and this
revision makes no claim that the two still correspond. Rows C-65 through C-70 are Chinese-only framing,
and they carry `—` in the English column, which means **"not present in the frozen English"** and is
expected rather than a defect.

The publication index records the status in one line: *English adaptation pending re-alignment after
**Chinese human editorial approval**.* `ENGLISH_REALIGNMENT: NOT_STARTED`.

### 1.5 What P5-E1 changed, and which rows it moved

P5-E1 is an editorial correction pass, not a rewrite: no new structure, no new thesis, no new experiment,
no new evidence, and no change to the English document. Nine passages were corrected. Three of them
carried claim content, and those are the ones recorded here.

| Correction | Was | Now | Effect on the audit |
|---|---|---|---|
| **§3 — what counts as a local measurement** | 只有 `results/usage.jsonl` 里由真实调用写出来的一行，才算本地测量 | 只有真实调用写进 canonical log 的记录才算本地测量。核心阶段用 `results/usage.jsonl`，P3 用独立的 `results/p3_boundary_locus/usage.jsonl`，两个日志分开，不合并 | **C-11 re-worded, and C-73 added.** The old sentence named one log while the bench has two. The corrected sentence names the mechanism rather than a filename, and states the separation explicitly. No class change — both logs are frozen evidence. |
| **§4 — how cost and latency are classified** | 成本和延迟是本地推的，明确标成本地推导，不当事测量结果 | 成本由 token 用量和价格表推算，是本地推导，不是账单。延迟记录的是端到端本地 wall-clock，它是测量值，但不能被读成模型自身的推理延迟 benchmark | **C-15 re-worded, and C-74 added.** The old sentence put cost and latency in one bucket. They are not the same kind of statement: cost is a derived calculation, latency is a measurement with a confounded window. Splitting them is a tightening, and C-74 is what keeps the split from being read as a latency claim. |
| **§5 — the 0.61 gate** | 正好越过代码里设的 0.60 门槛，于是被判成 accept | 而代码里的 demonstration threshold 是 0.60，因此 Python policy 判成 accept | **C-26 re-worded, no class change.** The article now uses the constant's own label (*demonstration threshold*) and attributes the verdict to the policy that computes it, rather than to a threshold the case "crossed". Nothing about C-27's arithmetic changed. |

The other six corrections are style, attribution or precision-of-phrasing edits with no claim content:
§6 turns an agent-vs-human speed comparison into a **rate mismatch** (process attribution audit, not this
contract); §7 replaces a precise audit count with 多套审计、一份预注册和一套冻结证据, which is *less*
assertive, not more; §8 replaces 还有谁活着 with 维护者还能够独立解释、验证或重建; §9 deletes one of two
near-identical 删故事 paragraphs, leaving C-67's content intact in the survivor; and §15 forbids adding
any new colloquial device, so the style metrics were permitted to fall (they fell by one; style audit
revision 3).

**No figure was lost.** All 18 bilingual tokens in §4.2 were re-checked against the P5-E1 text and all 18
are present. `DO_NOT_STATE_ZH` remains **0**.

### 1.6 The micro corrections, and the fourth that closes the third's risk

Four sentences were corrected on top of P5-E1, one line each, and nothing else in the article changed. The
first three were applied together. **The third of them removed a number and, in doing so, left the
antecedent of 这些候选 doing work it did not do before**; revision 6 recorded that risk here rather than
resolving it, because it was an editorial judgment and the owner is the one who makes it. The fourth
correction is that judgment.

| Correction | Was | Now | Effect on the audit |
|---|---|---|---|
| **The mechanisms sentence** | 这些机制让说出假话更难，它们没有让解释真话变得可能 | 这些机制让说出假话更难，但不会自动让维护者获得独立解释、验证这些事实的能力 | **C-75 added.** The old form was an aphorism with no subject; the new form names the party and the capability. Slightly longer, strictly narrower. |
| **The state-string lead-in** | 发布的时候，这个仓库的诚实总结是这样一行状态 | 到这里，这个仓库能给出的最诚实总结，是这样一行状态 | **No row change, but it removes an inaccuracy.** *发布的时候* implies a publication event; nothing in this repository has been published, which docs/README says in one line. *到这里* is the accurate frame and the state string is unchanged. |
| **The candidate count, first form** | 七个候选跑完对抗性审查，只剩一个 | 这些候选逐个做完对抗性审查，最后只剩一个问题 | **C-66 scoped, and a reading risk recorded.** See below. |
| **The candidate count, final form** | 这些候选逐个做完对抗性审查，最后只剩一个问题 | 七个候选逐个做完对抗性审查后，最后只剩一个值得继续追的问题 | **C-66 re-scoped to its original width; the risk closed.** The set and the number are back, and the survivor is named as an open question rather than left to the reader. |

**The risk.** The first form deleted the triage total on the grounds that the article never set it up — the
sentence was the only place `七` appeared, and it appeared as a jump. What that cost was the antecedent:
*这些候选* sat immediately after four candidates that had **all** been retired, so the nearest reading said
one of those four survived, which is false. The surviving question (`07_instruction_precision`, C-34) was a
different candidate.

**The fix, and how it differs from the one revision 6 predicted.** Revision 6 said the smallest repair was
to restore the set *without* the count. The owner restored it *with* the count and changed what the survivor
is called. `七个候选` has no nearer antecedent than the triage set itself, so the sentence can no longer be
read as being about the four; the number is no longer a jump, because the sentence now says what the seven
went through and what came out.

**The second half of the fix is a tightening in the same direction as the rest of the pass.** The old
endings — 只剩一个, 只剩一个问题 — left the survivor's status to the reader. `值得继续追` states it: the
survivor is an **open question with a falsifiable unknown**, not an established finding. That is exactly how
the next paragraph describes it (它活下来的理由不是效应大，恰恰是它有一个明确的、可以证伪的未知), so the
sentence is now consistent with its own continuation and cannot be read as reporting a positive result.
**No row moves and no verdict flips:** C-66 is re-scoped back to its pre-correction width and keeps class
`B`, because the compression risk §7 tracks — *seven stories were deleted* standing in for *seven
discoveries were disproved* — is a property of the count, not of the sentence that carries it.

### 1.7 The scope cleanup: what left the article, and the rows that left with it

Two owner decisions, both about **what this blog is about**, not about what is true. Nothing here was
removed because it was unsafe to state; both removals are scope changes, and this audit records them that
way rather than as repairs.

**Decision A — internal governance status is not reader-facing prose.** The article's header carried an
italic note saying the English half was parked at P5-B, that cross-language parity was `SUSPENDED` rather
than `PASS` in this audit, and that the two halves were out of step. That is a true statement about this
repository's *process*, and it belongs in this file and in `docs/README.md`, where it still is. It does not
belong in an article a reader arrives at cold. **No row moves**: the note asserted nothing about Jev, about
this bench's measurements, or about TypeSafe's published material, so it was never in this audit's
inventory to begin with — it is recorded here because a reader comparing revisions will see it gone.

**Decision B — NAS is out of the project's scope.** The project's subject is *a small Jev bench built by
Agentic Engineering*; its meta-subject is *cognitive debt accumulated while building a project with AI*.
NAS was neither. Three pieces left the article:

| Piece | Was | Row effect |
|---|---|---|
| A clause in the non-claims list | 没有 NAS 适用性结论。 | **None.** C-61 covers the non-claims list as a unit; the list is one item shorter and the row is unchanged. |
| A framing clause in the first-person row | *still wanting to look at NAS*, and `NAS` in that row's location column | **C-65 narrowed.** A framing clause, not a separate claim, so the row survives and loses a clause. |
| A whole closing movement, seven lines | 从 Jev 能不能拿去做 NAS 到 不能因为手上有锤子，就把问题看成钉子 plus its section break | **C-62 and C-69 retired.** Both were supported *only* by this material: C-62 was the NAS non-claim itself, and C-69 was the aphorism attached to it. With the movement gone there is nothing left for either to describe. |

**The two retired rows are removed, not renumbered.** C-62 and C-69 are simply absent from §2, and every
other ID keeps the meaning it had in revision 2 — so a reader who cites C-65 or C-70 from an older revision
is still citing the right row. The gaps in the sequence are the record that something was taken out, and
this section is the record of what and why.

**One more removal, from §7's exclusion table rather than from §2.** The exclusion row *Jev is suitable for
NAS (or any workload never run here)* was deleted for a different reason: the contract still forecloses that
statement, but the table's column is *where the Chinese article refuses it*, and the article no longer
raises the topic, so there is no such place. The frozen evidence keeps `NO_NAS_CLAIM`; only the article's
scope changed.

**What this does to the totals.** 73 substantive claims become 71: **46 `A` + 25 `B` + 0 `C`**. Two rows out,
both `A`, no row in, no verdict flipped. `DO_NOT_STATE_ZH` is still **0** — and it is worth saying precisely
what that does and does not mean here: it counts statements the article makes that the evidence cannot carry,
and the article now makes two fewer statements, so a fall to zero would have been the wrong thing to read
even if the number had moved. It did not move. It was already zero.

**These states now live only in metadata.** `ENGLISH_REALIGNMENT = NOT_STARTED` and `PARITY = SUSPENDED` are
recorded in [`ENGLISH_REALIGNMENT_HANDOFF.md`](ENGLISH_REALIGNMENT_HANDOFF.md), which is a docs artifact, not
article prose. The handoff also carries the one instruction that follows from decision B: **NAS content must
not be carried into the new English adaptation.** The frozen English still contains it (§15), and removing
it there is a realignment task, not a cleanup task — the English file was not touched in this revision.

---

## 2. The audit

**Column key.** *ZH* gives the location in the Chinese article, by named anchor, since it has no numbered
sections. *EN* gives the section of the frozen English adaptation in that document's own numbering, or `—`
where the statement is not in it. *Scope* is `yes` (the class-B scope is present in the same or immediately
adjacent sentence), `n/a` (the class does not require one), or `MISSING` (the claim would be a defect).

| Claim ID | Semantic claim | Contract class | Evidence | Chinese | English | Scope in ZH | Scope in EN | Verdict |
|---|---|---|---|---|---|---|---|---|
| C-01 | 54 API calls in total | A — the release | 42 core + 12 P3 records in the two frozen logs | 开头, 测量台 | intro, §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-03 | **The release reached `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** | **B** — anything about novelty | Freeze §5.3; `BLOG_CLAIM_CONTRACT.md` novelty rule | 开头, 结尾 | intro, §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-04 | A Jev call is `state + typed questions → typed answers`; all questions see the same state and are evaluated independently | A — official, attributed | `TS-DOC-STATE` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-05 | `Choice` returns a label plus a distribution over options; `choice` is the argmax; **the API's displayed values are quantised, so two-decimal sums need not equal exactly 1** | **B** — official semantics plus a display-precision caveat that is load-bearing | `TS-DOC-CHOICE`; recomputed during this audit: 1 of 74 Choice answers sums to `0.99` | 背景 | §2 | yes | n/a | `SAFE_WITH_SCOPE` |
| C-06 | `Score` returns a value plus `confidence`, defined as the probability-weighted mean of the levels | A — official | `TS-DOC-SCORE` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-07 | `Noul` is a single probability with no separate `confidence`; **45 of 45** locally | B — typed output semantics; the 45/45 count needs the erratum | Log: `noul` carrying `confidence`: **0**. `ERR-001` | 背景, 勘误 | §2, §11 | yes | yes | `SAFE_WITH_SCOPE` |
| C-08 | One `01_primitives` answer had winning probability 0.45 and confidence 0.26 | A — a named single record | Log: `01_primitives`/`department`, `choice: other`, `0.45` / `0.26` | 背景 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-09 | Typed output solves the schema problem, not the semantic one | A — non-claim | `NO_BROAD_HALLUCINATION_BENCHMARK`, `NO_GENERAL_ACCURACY_CLAIM` | 背景 | §2 | n/a | n/a | `SAFE_TO_STATE` |
| C-10 | The vendor's known-limitations page lists literal reading, weak numerics, date comparison, indirection, large state, and puts control flow in code | A — official, attributed | `TS-DOC-JAG`, `TS-DOC-BUILD` | 背景 | §2 | yes | yes | `SAFE_TO_STATE` |
| C-11 | Vendor figures are claims about *their* workload; **only a record written by a real call into a canonical log** is a local measurement; separating the evidence layer is what keeps a convenient story from looking reasonable | A — repository practice | Freeze §7, no vendor-claim adjudication | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-12 | The two logs' SHA-256 are `38e67630…` / `17f36f75…` and never changed | A — canonical log identity | Freeze §3; re-hashed during this audit | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-13 | 42 records requested `jev-latest` and resolved `jev-1.13.0` | A — provenance | Log: `model_resolved = jev-1.13.0` on 42/42 | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-14 | CI regenerates derived artifacts and fails on any difference | A — engineering | `.github/workflows/ci.yml`; freeze §5.2 | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-15 | The 54 calls cost ≈ **$0.001** by local estimate; **cost is derived from token usage and the price table and is not a bill** | B — cost figures | Sum of `estimated_cost_usd` over both logs = `0.001084566`; `pricing.py` | 测量台 | §3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-16 | 10 registered experiments, all executed, 42 core records | A — registry | Freeze §4; `EXPERIMENT_REGISTRY.md` | 批处理 | §4 | n/a | n/a | `SAFE_TO_STATE` |
| C-17 | `04_confidence` has 2 cases; `12_function_routing` makes 4 calls | A — registry | Registry tables | 路由, 三条经验 | §4 | yes | yes | `SAFE_TO_STATE` |
| C-18 | None of the 10 left a conclusion both new relative to TypeSafe's public material and supported by the data | **B** — novelty, scoped | P2 §6; freeze §5.3 | 四个候选 | §4 | yes | yes | `SAFE_WITH_SCOPE` |
| C-19 | Batching: 816 vs **3,480** input tokens; **4.2647×**; **76.55%** saved | B — batching ratio | Log: batched `[408, 408]`; separate sum `3480`; ratio `4.2647` | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-20 | 10/10 selected values identical, largest absolute difference 0.0 | B — same row | Log: the five values repeat across both cycles and both arms | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-21 | The local 4.26× must not be compared with the vendor's 12.2× | A — contract rule | `BLOG_CLAIM_CONTRACT.md` class B; P1 audit | 批处理 | §5 | yes | yes | `SAFE_TO_STATE` |
| C-22 | Public third-party measurements varied batch size and published an accuracy curve | B — third-party, cited as third-party | P2 §4.1 (D), P2 §7 `BLOG_CORE` | 批处理 | §5 | yes | yes | `SAFE_WITH_SCOPE` |
| C-23 | 13b: label unchanged 5/5; top-2 margin moved ≤ 0.07; `Score` 1.58–1.63; `confidence` 0.24–0.30; one exact tie | B — local measurement + a novelty claim that may only be scoped | Log: margins `0.07, 0.06, 0.02, 0.03, 0.00`; scores `1.58–1.63`; `department` confidences `0.24–0.30`; `ambiguous_5` `other 0.45 = billing 0.45` | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-24 | Official cookbook reports label flips on 2 of 8 questions and per-label std dev (mean 0.0098, max 0.0515) | B — official, attributed | P2 §4.1 (A); the vendor cookbook | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-25 | A public chaos test sent the identical request five times and got `0.03, 0.03, 0.03, 0.04, 0.04`, with jitter floors over ~1,490 calls | B — third-party, cited as third-party | P2 §4.8 | 稳定标签 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-26 | The 0.60 gate is this repository's own constant, **named in the article by its own label, `demonstration threshold`**, never calibrated; the verdict is the Python policy's, not the model's | B — our own policy | `experiments.py` `CONFIDENCE_GATE_THRESHOLD`; P2 §4.1 (C) | 0.61 门槛 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-27 | The ambiguous case returned 0.61 against a 0.74 vs 0.26 margin; the published k=3 expression reproduces 0.61 exactly | B — local measurement + derived | The `04` record; P2 §4.1 (C) | 0.61 门槛 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-28 | Two official pages use different `confidence` thresholds for the same worked example, and both say thresholds are domain-specific | A — official sources; a recorded divergence | Freeze §8; `TS-DOC-CONF` vs `TS-DOC-CONFROUTE` | 0.61 门槛 | §6 | yes | yes | `SAFE_TO_STATE` |
| C-29 | Routing: 4/4 function matches, 4/4 argument matches, 4/4 suppressed, handler never entered | B — our architecture | The `12` records; P2 §4.1 (G) | 路由, 三条经验 | §6, §12.3 | yes | yes | `SAFE_WITH_SCOPE` |
| C-30 | Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a 0.8 floor; the 1.0 case withheld by `needs_human_review` 0.94 ≥ 0.5 | B — our own policy; thresholds are demonstration parameters | Log: the four `function` answers carry those confidences; `needs_human_review` = 0.94 | 路由 | §6 | yes | yes | `SAFE_WITH_SCOPE` |
| C-31 | `07`: an 82-byte byte-identical state, `Noul` 0.75 → 0.20, a 0.55 move | B — the `07` illustration | Log: `state_utf8_bytes = 82`; vague `0.75`, explicit `0.20` | 07 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-32 | The official remedy for the literal-reading edge is given as a bundle and never decomposed | A — official | `TS-DOC-JAG`; P2 §4.3 | 07 | §7 | yes | yes | `SAFE_TO_STATE` |
| C-33 | The novelty check returned `PUBLIC_NOVELTY_UNRESOLVED`, recorded as unresolved, never as "nobody has done this" | B — anything about novelty | P2 §4.8 | 07 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
| C-34 | It was the only question that passed triage and was worth spending calls on | B — novelty | P2 §5: exactly one `R_GO` candidate | 07 | §7 | yes | yes | `SAFE_WITH_SCOPE` |
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
| C-63 | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`; every large local effect restates a documented behaviour or is this repository's own policy | **B** — state of the science, stated as novelty | Freeze §5.3 | 结尾 | §16 | yes | yes | `SAFE_WITH_SCOPE` |
| C-64 | License: MIT | A — release fact | `LICENSE`; `pyproject.toml` | 附录 | §16 | n/a | n/a | `SAFE_TO_STATE` |
| C-65 | First-person framing of the author's own work: the opening curiosity about typed output; not wanting to run a design twice; finding the analyzer defect awkward rather than heroic | A — first-person, no product claim | Every item traces to work actually done and recorded; **re-attributed in P5-E** where the underlying action was an agent's. **The NAS item was dropped in revision 8** with the rest of the NAS material — it was a framing clause, not a separate claim | 开头, 测量台, 分析器 | — | n/a | n/a | `SAFE_TO_STATE` |
| C-66 | The narrative device: candidate findings were written up and then deleted; **the ones that fell, fell for two different reasons — prior art for batching and repeatability, this bench's own policy for the gate and the routing blocks** — and none was kept or killed for how it looked. **The article describes four in detail and states the triage total of seven once**, in the closing movement, where the survivor is named as 一个值得继续追的问题 rather than as a finding — so the prose carries the count *and* the survivor's open status (see §1.6 for the reading risk the first form of that sentence opened and the fourth correction closed) | **B** — novelty-adjacent | P2 §5–§6: seven triage candidates, all retired | 四个候选, 结尾 | — | yes | n/a | `SAFE_WITH_SCOPE` |
| C-67 | Method claims about this bench: an evaluation repository's job is to delete the stories its evidence cannot carry (carried by 一个用来检验发现的仓库…在做它该做的事，而不是在累积战利品); what it accumulates is that ability (carried by 这个仓库真正积累的，不是故事。是删故事的能力。). **P5-E1 deleted a third sentence that restated the first half ahead of the second**; the claim is unchanged and both halves still stand, one sentence apart. | A — methodology opinion about the bench, not about Jev | Freeze §5.3; the P2 triage outcome | 结尾 | — | n/a | n/a | `SAFE_TO_STATE` |
| C-68 | The project reads as training in model evaluation and agent engineering rather than as a model benchmark, and most of the learning was not on Jev's side | A — the author's own assessment | The author's first-hand account of the work | 结尾 | §16 | n/a | n/a | `SAFE_TO_STATE` |
| C-70 | The author is willing to put a name to the frozen state string | **B** — novelty-adjacent | Freeze §5.3; the string is quoted in the same paragraph and restated in scope around it | 结尾 | — | yes | n/a | `SAFE_WITH_SCOPE` |
| C-71 | No adjudication of vendor claims: incommensurable, not "the vendor is wrong" and not "the local run proves them right" | A — contract rule | `BLOG_CLAIM_CONTRACT.md`; P1 audit | 非声明 | §14 | n/a | n/a | `SAFE_TO_STATE` |
| C-72 | Every state is synthetic; there is no real personal, customer or proprietary data here | A — contract rule | Repository practice; freeze §7 | 非声明 | §14 | n/a | n/a | `SAFE_TO_STATE` |
| C-73 | The bench keeps **two** canonical logs: the core phases write `results/usage.jsonl`, P3 writes its own `results/p3_boundary_locus/usage.jsonl`, and the two are not merged | A — canonical log identity | Freeze §3 names both hashes; both logs re-hashed during this audit | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-74 | Latency is recorded as end-to-end local wall-clock; it is a measurement, **not** a model-inference latency benchmark | A — non-claim about what the latency figure means | `findings.md`; the transport-attempt rule in `CLAUDE.md`; freeze §3.3 | 测量台 | §3 | n/a | n/a | `SAFE_TO_STATE` |
| C-75 | External mechanisms — canonical logs, preregistration, claim audit, errata, the evidence freeze, offline tests — make false statements harder to make; **they do not by themselves give a maintainer the ability to independently explain and verify the facts they hold** | A — non-claim about what the mechanisms do | Freeze §7; the process attribution audit §6 domain separation | 结尾 | — | n/a | n/a | `SAFE_TO_STATE` |

---

## 3. Totals

| Verdict | Chinese (r8) | Chinese (r7) | Chinese (r5) | Chinese (r4) | Chinese (r3) | English (frozen r2) |
|---|---:|---:|---:|---:|---:|---:|
| `SAFE_TO_STATE` | **46** | 48 | 47 | 45 | 46 | **42** |
| `SAFE_WITH_SCOPE` | **25** | 25 | 25 | 25 | 24 | **22** |
| `DO_NOT_STATE` | **0** | **0** | **0** | **0** | **0** | **0** |
| **Substantive claims audited** | **71** | 73 | 72 | 70 | 70 | **64** |

**Revision 8 removes two rows and adds none, which is the first time this table has gone down.** C-62 and
C-69 were supported only by the NAS material, and the article no longer contains any; C-65 loses its NAS
clause but keeps its row. All three changes are recorded in §1.7 rather than by renumbering, so every other
ID in the table above still means what it meant in revision 2.

**There is no r6 column, because revision 7's figures are revision 6's.** The fourth correction re-scopes
C-66 and restores a number the article had dropped; it adds no row, removes no row, and flips no verdict, so
carrying r6 as its own column would repeat those numbers exactly. Revision 5 is the last column before r7
that differs, and it differs only by C-73, C-74 and C-75.

**`DO_NOT_STATE_ZH = 0`.** Nothing in the article had to be deleted or rewritten for asserting something
the evidence does not carry. The one class change is a **tightening**, not a new defect: C-05 moved from
`A` to `B` because the display-precision caveat is now load-bearing, and a reader who drops it would read
a false sentence. Repairing a claim by requiring its scope is the contract working, not failing.

**The three rows P5-E1 and the micro corrections added are all `A`, and none is a new assertion.** C-73,
C-74 and C-75 make explicit what the article previously left implicit — that there are two logs rather than
one, that a latency figure is a wall-clock measurement rather than a benchmark, and that external
mechanisms do not confer comprehension. An implicit statement that a reader could complete wrongly is the
same defect as an explicit one, which is why they are entered as rows rather than counted as wording.

**Every one of the 71 rows carries `yes` or `n/a` in the Chinese scope column.** No row is `MISSING`. The
two IDs this revision retired — **C-62 and C-69** — left with the material they described rather than being
dropped from the audit; §1.7 records both, and no ID above them was renumbered.

**Two further gaps in the sequence pre-date this revision and are not explained here.** `C-02` and `C-56`
have no row in §2 and no note anywhere in this file. They were already absent in revision 7, they are not
casualties of the scope cleanup, and this audit has not established what became of them. **They are recorded
here as an open documentation gap rather than left to look like two more removals** — a reader counting rows
against the totals would otherwise be short by two with nothing to point at. Reconstructing them is a task
for a future revision, not something this one should guess at.

**The English total stays at 64** because the English document did not change. **This is a consequence of
the freeze, not a parity result**, and it is why §4's parity gate is reported as suspended rather than
passed.

---

## 4. The two mechanical parity gates

These checks exist to prevent drift between the languages. **Both are affected by the freeze, and neither
may be reported as passing across the pair.**

### 4.1 Novelty parity — **within the Chinese: PASS. Across the pair: SUSPENDED**

The Chinese article may not contain an equivalent of *"nothing new about Jev"*, *"no novelty exists"*,
*"nobody has done this"*, or *"we discovered a novel Jev behaviour"*.

| Pattern | Chinese | Frozen English |
|---|---|---|
| nothing new about Jev / 没有发现任何关于 Jev 的新东西 | absent | absent |
| no novelty exists / 不存在新颖性 | absent | absent |
| nobody has done this / 没有人做过 | **only in the refusal** — 记成「未解决」，而不是「没有人做过」 | **only in the refusal** — §7 |
| we discovered a novel Jev behaviour | absent | absent |

The third row is a true positive for the pattern and a pass for the gate: the phrase appears **only to
refuse it**, in the sentence stating what `PUBLIC_NOVELTY_UNRESOLVED` does and does not mean.

**Within the Chinese: PASS.** The article states the frozen state string in a fenced block in the closing
movement, where a reader will see it, and restates it in scope around the block.

**The cross-language half of this gate is SUSPENDED, not passed.** With the English frozen and the Chinese
revised again, that check would compare two texts that are not currently aligned, and reporting it as a
pass would be reporting the wrong thing. `ENGLISH_REALIGNMENT: NOT_STARTED`.

### 4.2 Bilingual factual parity — **SUSPENDED**

Revision 2 checked 18 tokens in both languages. **That check is suspended**, for the same reason: its
subject is a pair that is not currently aligned. The Chinese article was verified to contain all 18 tokens
after the P5-E edits, and again after the P5-E1 corrections, so no figure was lost to the factual repairs,
the density reduction, the new closing movement or the editorial pass — but the gate as a *parity* gate is
not reported as passing.

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

9 of 9 first-column tokens and 9 of 9 second-column tokens present in the Chinese. **This was re-run
against the P5-E1 text and again after the micro corrections** — neither pass removed any of the 18, and
the token that came closest to being at risk, `54`, is carried by the sentence P5-E1 rewrote and is still
present. Note that `七` is *not* one of the 18 and never was: the count of triage candidates was prose, not
a parity token. That is why dropping it in the first micro correction, and restoring it in the fourth, both
move C-66's scope and neither moves this table — the gate is over figures the two languages must agree on,
not over every number the prose happens to use. The frozen English still
contains all 18 as of revision 2, and nothing in P5-D, P5-E or P5-E1 touched it.

---

## 5. Domain separation: what this contract does not reach

**P5-E added a closing movement that this audit does not classify, and the omission is deliberate.**
The AI-involvement disclosure, the role division, the cognitive-debt working concept, the externalised-
controls argument and the metaphor are **not Jev claims, not measurements, and not statements about
anything TypeSafe published**. The contract's three classes answer *what may be said about the evidence*;
none of that material is about the evidence.

Entering it below as `SAFE_TO_STATE` rows would be worse than leaving it out, in two directions at once:
it would claim the frozen verifier's authority for text the verifier cannot read, and it would let a
process claim borrow the credibility of a measurement claim it was never checked against.

**It is accounted for elsewhere, by a different mechanism:**

| Material | Accountable to | Where |
|---|---|---|
| Who decided, who executed, who is credited | `OWNER_DECLARED_PROJECT_PROCESS` | [`…PROCESS_ATTRIBUTION_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md) |
| The role table and the Agentic Engineering definition | the owner declaration | [`AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md`](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md) §1–§2 |
| 认知负债 as a working concept | the same, explicitly **not** a measurable quantity | [`AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md`](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md) §3 |
| The metaphor | nothing — it is a figure, used once | article, closing movement |

The separation is the point rather than a filing decision. If process statements were admitted to this
contract, the evidence layer would start underwriting claims it was never designed to check, and the
frozen verifier would be attesting to text it cannot parse.

---

## 6. Claims deliberately excluded, and how

These are the contract's class C statements — available at no scope, because no qualifier can create the
missing evidence. Each was excluded by construction, not caught in review:

| Excluded | Where the Chinese article refuses it |
|---|---|
| Jev is generally more (or less) accurate than anything | 非声明: no ground truth exists anywhere in the bench; "4 / 4" is a count, never a rate |
| This project validated or falsified calibration | 三条经验: neither direction; 2 cases, no reliability diagram, no ECE, no Brier score |
| Jev is deterministic — or non-deterministic | 非声明: a few repeats on two payloads is not a verdict in either direction |
| Jev is universally 4.26× cheaper | 批处理: one payload, five questions sharing one state; not a general ratio and not comparable to the vendor figure |
| A general instruction-vs-criteria field preference | 负结果: the null, plus two explicitly refused summaries and `FIELD_ALIGNMENT_CAVEAT` |
| These observations are novel discoveries | 结尾: the state string, quoted; and 四个候选, where the two largest effects are killed on prior art |
| Jev cannot hallucinate / these results certify schema safety | 背景, 非声明: schema conformance on benign payloads is the only axis measured |
| This pattern is safe for production | 三条经验: every handler is inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` |
| A vendor figure is "really" our number, or the reverse | 批处理: the two are not commensurable; the vendor figure describes a different workload |
| Jev is fast, with any figure attached | 非声明: latency is recorded, not benchmarked; no speedup is claimed |
| The four scoring dimensions are independent | Not asserted anywhere; 三条经验 describes one composite without any independence claim |
| This release is peer-reviewed, endorsed, or a standard | Not asserted; 非声明 links the claim contract that forecloses it |
| The retired designs were run | 退休实验: retired before publication, never run |
| **The probability table is exactly normalised as displayed** | 背景 (repair A): the displayed values are quantised; the claim is made about the distribution, not about the two-decimal rendering |

**One exclusion was removed from this table in revision 8, and the removal is not a contract change.** The
row read *Jev is suitable for NAS (or any workload never run here) → NAS: no NAS experiment, dataset or
measurement exists*. The article no longer raises that topic at all, so there is no longer a place in the
Chinese prose where it is refused — and a table whose column is *where the article refuses it* cannot carry
a row with no such place. **The contract still excludes the statement**, and the frozen evidence still
records `NO_NAS_CLAIM`; nothing under `docs/evidence/v0.1.0/` was touched. What changed is the article's
scope, not the contract's reach.

Two exclusions worth naming, because the revisions made them *more* tempting rather than less:

- **The vendor's 12.2× vs the local 4.2647×.** The narrative gives this a whole rhetorical movement —
  three attractive numbers, then a one-word paragraph, then the dismantling. The Chinese keeps both
  figures *with their sources* and then states they are not commensurable, so the two numbers appear in
  the same paragraph only so the refusal has something to refuse.
- **The 删故事 device as a finding.** C-66 is filed class `B` and not class `A` precisely because
  "seven stories were deleted" is one compression away from "seven discoveries were disproved", which
  would be false. **Repair B tightened this further**: the four candidates that fell did not fall for one
  reason, and the article now says which fell to prior art and which were never findings about Jev at all.
  **The first micro correction then removed the count itself**, which pushed the paraphrase back into P2;
  **the fourth put it back**, so "seven stories were deleted" is once more a compression of the prose. What
  the fourth correction added instead is the survivor's status — 一个值得继续追的问题 — which blocks the
  adjacent over-read ("one candidate was vindicated"). The class stays `B` for both reasons: the count is
  in the prose again, and the sentence's own guard against the plausible misreading is the qualifier that
  keeps it there.
  **P5-E1 removed one of the two restatements of the device** — the closing callback used to make the same
  point twice, and now makes it once, immediately before 但还有一个故事要删. That is a change in how
  often the device is *said*, not in what it asserts: C-67's two halves still both stand, one sentence
  apart. The compression risk it carries is unchanged and is why the class stays `B`-adjacent rather than
  being entered as a finding.

---

## 7. Self-check from the contract

The contract's own seven-item list, run against the current Chinese:

1. **Is every figure labelled** as OFFICIAL CLAIM, LOCAL MEASUREMENT or DERIVED CALCULATION? — Yes, in
   natural language rather than as tags.
2. **Does every figure keep its scope** — payload, repeat count, session, model version? — Yes; see the
   scope column. The thinnest place, the `45 / 45` count, is still scoped after two rewrites.
3. **Does any sentence read bigger with the qualifier deleted?** — This is the check P5-E was most exposed
   to, and it is exactly where repair A came from: `表里的数加起来是 1` read bigger with the display
   qualifier deleted, and the qualifier was missing. It is now present, and C-05 carries class `B`.
4. **Is the null result in it?** — Yes, and it is the article's structural climax: the raw values table,
   the K1 separation, the null, and the analyzer defect.
5. **Does it say `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** where a reader will see it? — Yes, in a fenced
   block near the end, restated in scope around the block.
6. **Would any sentence change if a TypeSafe engineer read it?** — No sentence was softened for that
   reason. The two vendor-side observations kept in the article are sourced to the vendor's own material,
   and repair C removed a licence-scope sentence rather than narrowing it.
7. **Does it say what this is not?** — Yes, in prose rather than as a marker list.

---

## 8. What this audit does not cover

- **Prose quality and style.** Audited separately in
  [`…STYLE_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md), and nothing in
  this file should be read as endorsing them. What is audited here is that no sentence claims more than
  its evidence carries.
- **Who did the work.** Audited separately in
  [`…PROCESS_ATTRIBUTION_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md),
  and §5 above records why that material is not entered here.
- **The frozen English document.** It was not read for revision, not re-scoped, and not re-aligned. Its
  column in §2 is revision 2's finding carried forward. Any statement here about the English is a
  statement about the text as it stood at P5-B. **This includes one known stale identifier:** the English
  still names the bench `jev-test`, which was the project's name until the P5-E rename. P5-E forbids
  modifying that file, so the stale name is left standing and is recorded here rather than quietly fixed.
  It is part of what the English re-alignment will have to resolve, alongside the language parity.
- **The frozen evidence itself.** This audit checks the article *against* `v0.1.0`. It does not re-open
  the release's own claims, which are frozen and immutable.

**No new evidence defect was found during the revisions or this audit.** No `P5_NEW_EVIDENCE_DEFECT_FOUND`
condition arose: every figure checked against the canonical logs matched, both canonical logs are
byte-identical to their frozen hashes, and no frozen artifact was modified.
