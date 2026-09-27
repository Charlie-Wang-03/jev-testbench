# Claim audit — `jev-as-probabilistic-decision-primitive.zh-CN.md`

**Audited document:** [`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md)
**Standard:** [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md)
**Evidence base:** release `v0.1.0` — [`PUBLIC_EVIDENCE_FREEZE.md`](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md),
[`evidence-manifest.json`](../evidence/v0.1.0/evidence-manifest.json), and the two canonical logs.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**

**What this file is.** Every substantive claim in the draft, classified against the contract's three
classes — `A` (`SAFE_TO_STATE`), `B` (`SAFE_WITH_SCOPE`), `C` (`DO_NOT_STATE`) — with the evidence it
rests on and whether the scope that class requires is actually present in the prose. It is the
mechanical form of §21 of the P5-A work order, and it exists so that a reader can check the draft
without re-reading the entire evidence set.

**How the numbers were checked.** Every figure in the draft was **re-derived from
`results/usage.jsonl` and `results/p3_boundary_locus/usage.jsonl` during this audit**, not copied
from the work order that commissioned the article and not copied from the freeze document's prose.
Where the work order's text and the frozen evidence could disagree, the frozen evidence governed.
They did not disagree.

---

## 1. The audit

| # | Blog claim (location) | Contract class | Evidence | Scope present? | Verdict |
|---|---|---|---|---|---|
| 1 | 54 API calls in total (§ intro, §3) | A — about the release | 42 core + 12 P3 records in the two frozen logs | n/a — a count of the logs themselves | `SAFE_TO_STATE` |
| 2 | TypeSafe positions Jev as "unstructured state in, typed probabilistic decisions out" (§1) | A — official sources | `TS-BLOG-INTRO`, quoted via `docs/sources/TYPESAFE_OFFICIAL_SOURCES.md` | n/a — labelled 厂商对自己的定位 in the same paragraph | `SAFE_TO_STATE` |
| 3 | These 54 calls found nothing new about Jev (§ intro, §16) | A — state of the science | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`, freeze §5.3 | n/a — restates the frozen state string | `SAFE_TO_STATE` |
| 4 | One Jev call is `state + typed questions → typed answers`; all questions see the same state and are evaluated independently (§2) | A — official, attributed | `TS-DOC-STATE` | Yes — attributed 按照 TypeSafe 官方文档的描述 | `SAFE_TO_STATE` |
| 5 | `Choice` returns a label plus a distribution over options; `probabilities` sums to 1; `choice` is the argmax (§2) | A — official + reproduced | `TS-DOC-CHOICE`; local reproduction scoped in row 7 | Yes — 官方定义 in the sentence | `SAFE_TO_STATE` |
| 6 | `Score` returns a value plus `confidence`, defined as the probability-weighted mean of the levels (§2) | A — official | `TS-DOC-SCORE` | Yes — 官方定义 in the sentence | `SAFE_TO_STATE` |
| 7 | `Noul` is a single probability with no separate `confidence`; **45 of 45** locally (§2, §11) | **B** — typed output semantics; and the 45/45 row, which requires citing the erratum | Log: `Counter({'choice': 45, 'noul': 45, 'score': 29})`, `noul` carrying `confidence`: **0**. `ERR-001` | Yes — 42 条核心记录（一个账号、一个模型版本）in the same sentence; the erratum is reached via §11's link to `../ERRATA.md` | `SAFE_WITH_SCOPE` |
| 8 | One `01_primitives` answer had winning probability 0.45 and confidence 0.26 (§2) | A — a named single record | Log: `01_primitives`/`department`, `choice: other`, `probabilities.other = 0.45`, `confidence = 0.26` | Yes — the experiment and its single-call nature are named | `SAFE_TO_STATE` |
| 9 | "Typed output solves the schema problem, not the semantic one" (§2) | A — non-claim | `NO_BROAD_HALLUCINATION_BENCHMARK`, `NO_GENERAL_ACCURACY_CLAIM`; `findings.md` §1 | n/a — asserts a limit, not a capability | `SAFE_TO_STATE` |
| 10 | The vendor's known-limitations page lists literal reading, weak numerics, date comparison, indirection, large state, and says control flow belongs in code (§2) | A — official, attributed | `TS-DOC-JAG`, `TS-DOC-BUILD` | Yes — 这不是我发现的，是厂商公开写的 | `SAFE_TO_STATE` |
| 11 | Vendor figures are claims about *their* workload; only a log line is a local measurement (§3) | A — repository practice | Freeze §7, "No vendor-claim adjudication" | n/a — states the rule itself | `SAFE_TO_STATE` |
| 12 | The two logs' SHA-256 are `38e67630…` / `17f36f75…` and never changed (§3) | A — canonical log identity | Freeze §3; re-hashed during this audit | n/a | `SAFE_TO_STATE` |
| 13 | 42 records requested `jev-latest` and resolved `jev-1.13.0` (§3) | A — provenance | Log: `model_resolved = jev-1.13.0` on 42/42 | n/a | `SAFE_TO_STATE` |
| 14 | CI regenerates derived artifacts and fails on any difference (§3) | A — engineering | `.github/workflows/ci.yml`; freeze §5.2 | n/a — a property of this repository | `SAFE_TO_STATE` |
| 15 | The 54 calls cost ≈ **$0.001** by local estimate (§3) | **B** — cost figures | Sum of `estimated_cost_usd` over both logs = `0.001084566` | Yes — 本地估算，不是账单；TypeSafe Console 的计费才是权威, in the same sentence | `SAFE_WITH_SCOPE` |
| 16 | 10 registered experiments, all executed, 42 core records (§4) | A — registry | Freeze §4; `EXPERIMENT_REGISTRY.md` | n/a | `SAFE_TO_STATE` |
| 17 | `04_confidence` has 2 cases; `12_function_routing` makes 4 calls (§4) | A — registry | Registry tables | Yes — followed in the same paragraph by 小到不能支撑任何比率 | `SAFE_TO_STATE` |
| 18 | None of the 10 produced a Jev-specific new finding (§4) | A — triage outcome | P2 §6; freeze §5.3 | n/a | `SAFE_TO_STATE` |
| 19 | Batching: 816 vs **3,480** input tokens; **4.2647×**; **76.55%** saved (§5) | **B** — batching ratio | Log: batched `[408, 408]`; separate sum `3480`; ratio `4.2647` | Yes — 一份 payload、五个问题共享同一 state、两个顺序平衡循环、一次会话 | `SAFE_WITH_SCOPE` |
| 20 | 10/10 selected values identical, largest absolute difference 0.0 (§5) | **B** — same row | Log: the five values repeat identically across both cycles and both arms | Yes — same bullet list | `SAFE_WITH_SCOPE` |
| 21 | The local 4.26× must not be compared with the vendor's 12.2× (§5) | A — contract rule | `BLOG_CLAIM_CONTRACT.md` class B; P1 audit | Yes — both vendor figures named with their own source pages, then called a category error | `SAFE_TO_STATE` |
| 22 | Public third-party measurements varied batch size and published an accuracy curve, going further than this bench (§5) | **B** — third-party, cited as third-party | P2 §4.1 (D), P2 §7 `BLOG_CORE` | Yes — 公开的第三方测量 in the same sentence | `SAFE_WITH_SCOPE` |
| 23 | 13b: label unchanged 5/5; top-2 margin moved ≤ 0.07; `Score` 1.58–1.63; `confidence` 0.24–0.30; one exact tie (§6) | **B** — local measurement, and a novelty claim that may only be scoped | Log: margins `0.07, 0.06, 0.02, 0.03, 0.00`; scores `1.58–1.63`; confidences `0.24–0.30`; `ambiguous_5` `other 0.45 = billing 0.45` | Yes — payload named as 逐字节相同的 512-token 请求; killed in the same subsection as prior art | `SAFE_WITH_SCOPE` |
| 24 | Official cookbook reports label flips on 2 of 8 questions and per-label std dev (mean 0.0098, max 0.0515) (§6) | **B** — official, attributed | P2 §4.1 (A); the vendor cookbook | Yes — TypeSafe 自己的文档报告了 | `SAFE_WITH_SCOPE` |
| 25 | A public chaos test sent the identical request five times and got `0.03, 0.03, 0.03, 0.04, 0.04`, with jitter floors over ~1,490 calls (§6) | **B** — third-party, cited as third-party | P2 §4.8 | Yes — 有一份公开的 chaos test 报告说 | `SAFE_WITH_SCOPE` |
| 26 | The 0.60 gate is this repository's own constant, labelled a demonstration threshold, never calibrated (§6) | **B** — our own policy | `experiments.py` `CONFIDENCE_GATE_THRESHOLD`; P2 §4.1 (C) | Yes — 我自己在 experiments.py 里写下的常量 + 没有校准过、没有在任何数据上调过、不声称最优 | `SAFE_WITH_SCOPE` |
| 27 | The ambiguous case returned 0.61 against a 0.74 vs 0.26 margin; the published k=3 expression reproduces 0.61 exactly (§6) | **B** — local measurement + derived | The `04` record; P2 §4.1 (C) | Yes — the margin is given, and the value is framed as 一个算术结果 | `SAFE_WITH_SCOPE` |
| 28 | Two official pages use different `confidence` thresholds for the same worked example, and both say thresholds are domain-specific (§6) | A — official sources; a recorded divergence | Freeze §8; `TS-DOC-CONF` vs `TS-DOC-CONFROUTE` | Yes — attributed, and stated as a divergence rather than adjudicated | `SAFE_TO_STATE` |
| 29 | Routing: 4/4 function matches, 4/4 argument matches, 4/4 suppressed, handler never entered (§6, §12) | A — our architecture | The `12` records; P2 §4.1 (G) | Yes — traced to our own constants in the same paragraph; §12.3 carries 不是准确率 and `ACTUAL_HANDLER_EXECUTION_UNTESTED` | `SAFE_WITH_SCOPE` |
| 30 | Route confidences 0.76 / 0.58 / 0.72 / 1.0 against a 0.8 floor; the 1.0 case withheld by `needs_human_review` 0.94 ≥ 0.5 (§6) | **B** — our own policy, thresholds are demonstration parameters | Log: the four `function` answers carry exactly those confidences; `out_of_range_values`/`needs_human_review` = 0.94 | Yes — 我自己在 routing.py 里写的常量; the disclaiming comment is quoted | `SAFE_WITH_SCOPE` |
| 31 | `07`: an 82-byte byte-identical state, `Noul` 0.75 → 0.20, a 0.55 move (§7) | **B** — the `07` illustration | Log: `state_utf8_bytes = 82`; vague `0.75`, explicit `0.20` | Yes — the both-fields-changed confound and the absence of ground truth are stated in the same breath | `SAFE_WITH_SCOPE` |
| 32 | The official remedy for the literal-reading edge is given as a bundle and never decomposed (§7) | A — official | `TS-DOC-JAG`; P2 §4.3 | Yes — attributed throughout | `SAFE_TO_STATE` |
| 33 | The novelty check returned `PUBLIC_NOVELTY_UNRESOLVED`, recorded as unresolved, never as "nobody has done this" (§7) | **B** — anything about novelty | P2 §4.8 | Yes — 我把它记成「未解决」，而不是「没有人做过」 | `SAFE_WITH_SCOPE` |
| 34 | It was the only question that passed triage and was worth spending calls on (§7) | **B** — novelty | P2 §5: exactly one `R_GO` candidate | Yes — the following sentence restates the `UNRESOLVED` status | `SAFE_WITH_SCOPE` |
| 35 | Design, order, statistics and thresholds were committed before the first request (§8) | A — preregistration | Freeze §5.1; `db7d06f` | n/a | `SAFE_TO_STATE` |
| 36 | A 2×2 of the two fields, 3 repeats per arm, 12 calls, declared as a hard ceiling (§8) | A — preregistration | `P3_BOUNDARY_LOCUS_PREREGISTRATION.md` §9; freeze §6.1 | n/a | `SAFE_TO_STATE` |
| 37 | The pre-registered design hazard: the crossed arms must state the same boundary (§8) | A — preregistration | Preregistration §9 | n/a | `SAFE_TO_STATE` |
| 38 | P3 raw values, medians and ranges for all four arms (§9) | A — local measurement | P3 log: `N` 0.77/0.76/0.75; `I` 0.31/0.33/0.29; `C` 0.37/0.36/0.33; `B` 0.20/0.21/0.20 | n/a — the raw values are given, not just the summary | `SAFE_TO_STATE` |
| 39 | The endpoints replicated the original observation: 0.76 → 0.20, gap 0.56 (§9) | **B** — endpoint replication | P3 log; original `07` values | Yes — 每个臂 3 次重复、同一份 payload; and the claim is limited to 次序 and 量级 | `SAFE_WITH_SCOPE` |
| 40 | Instruction-only recovered 80.4% of the gap; criteria-only 71.4% (§9) | **B** — descriptive arithmetic, not part of the decision rule | Derived from the medians: `0.45/0.56`, `0.40/0.56` | Yes — explicitly 描述性算术，不是决策规则的一部分, and the verdict is unchanged if they are ignored | `SAFE_WITH_SCOPE` |
| 41 | The two single-field arms are 0.05 apart, below the pre-registered 0.10, so K1 fired (§9) | **B** — the separation that killed the attribution | P3 log; freeze §6.1 | Yes — and §10 states this is not evidence that the effect lives in both fields | `SAFE_WITH_SCOPE` |
| 42 | `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`; the effect could not be attributed to either field alone (§9) | A — primary null | Freeze §6.1; P3 result §3 | n/a | `SAFE_TO_STATE` |
| 43 | The large effect replicated; the *attribution* is what failed (§10) | A — the null, stated correctly | P3 result §4 | n/a | `SAFE_TO_STATE` |
| 44 | Two summaries are explicitly refused: "the boundary lives in both fields" and "criteria are what matter" (§10) | A — refusals | Freeze §6.1 names both as the two wrong summaries | n/a — refusing a claim cannot overclaim | `SAFE_TO_STATE` |
| 45 | `FIELD_ALIGNMENT_CAVEAT` limits the result to this mixed-specificity construction (§10) | A — caveat | Freeze §6.1; P3 result §7 | n/a | `SAFE_TO_STATE` |
| 46 | n = 3 supports a median and a range and no interval estimate (§10) | A — caveat | Freeze §6.1 | n/a | `SAFE_TO_STATE` |
| 47 | The analyzer defect, its disclosure, its post-run repair, and the invariance of every measurement, threshold and verdict (§11) | A — engineering + provenance | `ERR-002`; P3 result, "Post-run analyzer correction provenance" | n/a — no call was made during the repair | `SAFE_TO_STATE` |
| 48 | `ERR-001`: P1 states 42 of 42; the correct figure is 45 of 45; P1's text was not edited (§11) | **B** — the corrected count, which requires citing the erratum | Log recount; `ERRATA.md` | Yes — a link to `../ERRATA.md` in the same paragraph | `SAFE_WITH_SCOPE` |
| 49 | The 42 records carry 119 answers between them (§11) | A — canonical log | Log: 119 answers total | n/a | `SAFE_TO_STATE` |
| 50 | 42/42 responses were schema-valid; that is the weakest kind of type-safety evidence, and says nothing about factual correctness (§12.1) | A — non-claim | `findings.md` §1 | Yes — stated with the limit attached | `SAFE_TO_STATE` |
| 51 | In `06_composite_scoring`, one dimension scored 1.62 on a 0–3 rubric at confidence 0.24 and carried 97.4% of that state's composite risk (§12.2) | A — local measurement, one named case | Log: `evidence_quality` raw 1.62, confidence 0.24; recomputed share **97.41%** | n/a — a single named case, no rate implied | `SAFE_TO_STATE` |
| 52 | Official calibration is group-scoped; confidence "describes the model's answer, not a guarantee that the answer is correct" (§12.2) | A — official, attributed | `TS-DOC-SYS1`, `TS-DOC-CONF` | Yes — attributed to 官方文档 | `SAFE_TO_STATE` |
| 53 | This project neither validated nor falsified calibration, in either direction (§12.2) | A — non-claim | `NO_CALIBRATION_VALIDATION` | n/a | `SAFE_TO_STATE` |
| 54 | Semantic routing ≠ execution authorization; 4/4 is a count not a rate; handlers are inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED` (§12.3) | A — our architecture + non-claims | `findings.md` §2; `12` records | Yes — all three limits in the same subsection | `SAFE_TO_STATE` |
| 55 | Batch economics are workload-dependent; amortisation needs a shared state (§12.4) | A — scope restated | Freeze §5.1 | Yes | `SAFE_TO_STATE` |
| 56 | In `05`, 4 of 12 speculative answers were unconsumed, input fell by 400 tokens, and output is priced at zero (§12.4) | A — local measurement + the official price table | Log: fan-out 1412 in / staged 1812 in (= 400); 4 of 12 unconsumed | Yes — the numbers are given in the sentence | `SAFE_TO_STATE` |
| 57 | `retry_count` is permanently `null` and means "not reported"; `transport_attempt_count` licenses exactly one sentence (§12.6) | A — engineering limitation | Freeze §3.3; `findings.md` §2 | Yes — 不是「没有发生重试」 stated | `SAFE_TO_STATE` |
| 58 | Five registered designs were retired before publication, never run (§13) | A — the inverse of the contract's `DO_NOT_STATE` row | Freeze §4; `EXPERIMENT_REGISTRY.md` | Yes — 从未运行 stated | `SAFE_TO_STATE` |
| 59 | `10_state_length`'s three defects: no ground truth, n = 1 per tier, and filler that repeats five sentences rather than accumulating content (§13) | A — registry reasoning | Registry entry for `10_state_length` | Yes — each defect named | `SAFE_TO_STATE` |
| 60 | `11_language_pair`'s four reasons, including that the official docs state English is primary and CJK currently has lower accuracy (§13) | A + official, attributed | Registry entry for `11_language_pair`; `TS-DOC-STATE` | Yes — attributed to 官方文档 | `SAFE_TO_STATE` |
| 61 | The nine non-claims, in natural Chinese rather than as markers (§14) | A — non-claims | Freeze §7 | n/a — each is a refusal or a limit | `SAFE_TO_STATE` |
| 62 | No NAS experiment, dataset or measurement exists here; NAS is a future question to be re-derived from NAS task structure (§15) | A — non-claim | `NO_NAS_CLAIM`; freeze §7 | n/a | `SAFE_TO_STATE` |
| 63 | `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`; every large local effect restates a documented behaviour or is this repository's own policy (§16) | A — state of the science | Freeze §5.3 | n/a | `SAFE_TO_STATE` |
| 64 | License: MIT (§16) | A — release fact | `LICENSE`; `pyproject.toml` | n/a | `SAFE_TO_STATE` |

---

## 2. Totals

| Verdict | Count |
|---|---:|
| `SAFE_TO_STATE` | **45** |
| `SAFE_WITH_SCOPE` | **19** |
| `DO_NOT_STATE` | **0** |
| **Substantive claims audited** | **64** |

**`DO_NOT_STATE = 0`.** Nothing in the draft had to be deleted or rewritten for asserting something
the evidence does not carry.

---

## 3. Claims deliberately excluded, and how

These are the contract's class C statements — available at no scope, because no qualifier can create
the missing evidence. Each was excluded by construction, not caught in review:

| Excluded | Where the draft refuses it |
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

Two further exclusions worth naming, because they were the most tempting:

- **The vendor's 12.2× vs the local 4.2647× juxtaposition.** Available in raw form, and it is exactly
  the shape of a viral chart. §5 gives both figures *with their sources* and then states they are not
  commensurable — the two numbers appear in the same paragraph only so the refusal has something to
  refuse.
- **"Stable label, moving distribution" as a discovery.** §6 keeps the observation and kills it in
  the same subsection, on prior art, before a reader can get attached to it.

---

## 4. Self-check from the contract

The contract's own seven-item list, run against the draft:

1. **Is every figure labelled** as OFFICIAL CLAIM, LOCAL MEASUREMENT or DERIVED CALCULATION? —
   Yes, in natural language rather than as tags: 官方文档/厂商 says…, 我在…上测得…, 由这两个数可以直接算出….
2. **Does every figure keep its scope** — payload, repeat count, session, model version? — Yes for
   every figure where the contract requires it; see column 4 above. The two places where the scope
   was thinnest (§2's 45/45 and §9's endpoint replication) were tightened during this audit rather
   than argued about.
3. **Does any sentence read bigger with the qualifier deleted?** — Two did, and both were rewritten.
   §7 previously described the surviving question as 既新颖 ("novel"), which asserts a novelty the
   `PUBLIC_NOVELTY_UNRESOLVED` status does not carry; it now says the question 通过了审查 ("passed
   triage"). §3 previously said the 54 calls cost 不到一美元 ("under a dollar"), which is true but
   invites a reader to imagine fifty cents; it now carries the derived figure, ≈ $0.001.
4. **Is the null result in it?** — Yes: §9 gives the raw values, §10 is the null, and §11 the defect.
   The P3 null is roughly a quarter of the article.
5. **Does it say `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`** where a reader will see it? — Yes, §16,
   in a fenced block, and restated in plain Chinese around it.
6. **Would any sentence change if a TypeSafe engineer read it?** — No sentence was softened for
   that reason. Two vendor-side observations (§6's threshold divergence, §12.4's price-table
   inversion) are included *because* they are unflattering to a naive framing and are sourced to the
   vendor's own published material.
7. **Does it say what this is not?** — Yes, §14 is a dedicated non-claims section with nine items.

---

## 5. What this audit does not cover

- **The English adaptation.** This audit covers the Chinese draft only. The contract binds every
  public-facing sentence derived from the release, so the English version needs its own pass over
  this same table — a translation can carry a scope to the wrong clause, or drop it, and the
  numbers will still match.
- **Prose quality, structure and audience fit.** Those are editorial questions, not claim-integrity
  ones, and nothing here should be read as endorsing them.
- **The frozen evidence itself.** This audit checks the draft *against* `v0.1.0`. It does not
  re-open the release's own claims, which are frozen and immutable.

**No new evidence defect was found while writing or auditing this draft.** No `P5_NEW_EVIDENCE_DEFECT_FOUND`
condition arose: every figure checked against the canonical logs matched, and no frozen artifact was
modified.
