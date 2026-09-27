# Process attribution audit — the Chinese article (P5-E1)

**Audited document:** [`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md)
**Basis of this audit:** `OWNER_DECLARED_PROJECT_PROCESS` — the owner's declaration of who did what,
recorded in [`AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md`](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md) §2.
**Not a basis:** the `v0.1.0` frozen evidence. See §6.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 2 — re-verified in P5-E1 against the editorially-corrected text. Supersedes revision 1 (P5-E).
The re-verification is recorded in §9; the findings of revision 1 stand unchanged.

---

## 1. What this audit is, and why it needed to exist

The Chinese article was written in the first person. Some of those first-person sentences describe
things the author did. Others describe things **an AI agent did while the author was responsible for
them**, and the P5-D text had folded both into the same "我". That is a factual defect of the same
kind the claim audit exists to catch, one layer over: the claim audit asks *does the evidence carry
this statement about Jev?*, and this audit asks *does the process carry this statement about who
acted?*

**This audit has a weaker evidential basis than the claim audit, and it says so up front.** "Who
wrote this line" is not recoverable from Git. Git records *when which lines changed*, not *who
decided they should change*. The role assignment in this repository is an **owner declaration** —
testimony about process, of the same kind a release note is testimony about a measurement, with the
difference that a measurement can be checked and this cannot. Everything below rests on that
declaration. Nothing below is strengthened by the fact that it was written down carefully.

**What it is not.** It is not a style audit (that is
[`…STYLE_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md)) and not a
claim audit (that is [`…CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md)).
A sentence can be perfectly attributed and still be a claim defect, and the three audits are kept
separate for that reason.

---

## 2. The four categories

Every process statement in the article is assigned exactly one. The categories are deliberately
about *who the action belongs to*, not about who typed the characters — a commit written by an agent
under an owner's standing instruction is `HUMAN_DECISION` if the decision was the owner's and
`AI_EXECUTION` if the execution was the agent's, and many sentences are both, in which case they are
split and counted twice rather than blurred into one.

| Category | Means | What it licenses in the prose |
|---|---|---|
| `HUMAN_DECISION` | The owner chose, approved, refused, set direction, or accepted responsibility | First person is correct and required: 决定 / 批准 / 否决 / 不愿意 / 拍板 |
| `AI_EXECUTION` | An AI agent carried the work out — code, tests, calls, repairs, drafts | **First person is not available.** The article must say 项目 / Claude Code / 记录显示 / 事后复核 |
| `PROJECT_OBSERVATION` | What the repository itself shows, independent of who acted | Neutral voice; the subject is the artifact, not a person |
| `AUTHORIAL_REFLECTION` | Framing, judgment, metaphor, editorial stance | First person or impersonal; asserts nothing about Jev or about who executed |

The rule the article is held to is narrow on purpose. It does **not** require every sentence to name
an actor — a narrative that did that would be unreadable and would over-claim precision the
declaration explicitly disclaims. It requires that **no sentence attributes to the owner an
execution the agent performed**, and that no sentence is left in a form that a reader would
reasonably take as an owner-execution claim when it is not.

---

## 3. The search

The ten first-person action phrases named in the work order, counted across the whole article:

| Phrase | Occurrences | Where | Classification |
|---|---:|---|---|
| 我跑了 | **1** | 结尾披露段 | **Quoted in order to refuse it.** The sentence is 写成「我跑了 54 次调用」会是一句不准确的话 — it names the construction and rejects it. Not an attribution defect; it is the repair. |
| 我写了 | 0 | — | — |
| 我实现了 | 0 | — | — |
| 我发现了 | 0 | — | — |
| 我设计了 | 0 | — | — |
| 我修了 | 0 | — | — |
| 我调用了 | 0 | — | — |
| 我生成了 | 0 | — | — |
| 我测了 | 0 | — | — |
| 我删了 | 0 | — | — |

**Nine of the ten are absent from the article entirely.** The tenth appears once, inside quotation
marks, as the example of what the article is *not* saying.

### 3.1 The wider sweep

A literal phrase list is not sufficient — an attribution defect can be phrased as 我在 `routing.py`
里设的 floor or 我改了两个字段 without matching any of the ten. So every remaining occurrence of 我
in the article was read in context. There are three, and none is an execution claim:

| Line | Text | Classification | Why it stands |
|---|---|---|---|
| 背景 | 但「我觉得它有时候不太行」这种印象，本身不能拿来做事 | `AUTHORIAL_REFLECTION` | Quotes a *reader's* impression as the thing being ruled out, in a subordinate clause. Asserts no action. |
| 测量台 | 不是关于这台机器、这个账号、我们这些输入的测量 | `HUMAN_DECISION` | Collective possessive over the project's own inputs — an ownership statement, not an action claim. |
| 三条经验 | 模型回答这个 state 是什么意思，代码回答我们被允许行动吗 | `AUTHORIAL_REFLECTION` | Generic "we" inside a design principle. Names no actor and no action in this project. |

One further construction is worth recording because it is the one place the article describes an
action with no actor named at all: **所以先建一个测量台，叫 `jev-testbench`**. Read alone, a reader
could take it as owner-execution. It is not left alone — the paragraph immediately following states
the Agentic Engineering division of labour and links it, and the closing disclosure returns to it.
The construction is `HUMAN_DECISION` (the project and its goal are the owner's) over `AI_EXECUTION`
(the bench was built by the agent), and both halves are stated in the article rather than one being
implied.

---

## 4. Item-by-item classification

Every process-bearing statement in the article, in reading order. *Article location* is by named
anchor, since the article has no numbered sections.

| # | Statement in the article | Category | How the article carries it |
|---|---|---|---|
| 1 | The question: whether typed primitives make agents easier to write | `HUMAN_DECISION` | Impersonal: 一开始的疑问很朴素. The owner set the question; no first-person execution claim. |
| 2 | Deciding to measure before answering | `HUMAN_DECISION` | 所以决定先测一遍 — bare 决定, no 我, and it is a decision rather than an execution. |
| 3 | Building `jev-testbench` as a measurement bench | `HUMAN_DECISION` + `AI_EXECUTION` | The goal is the owner's; the build is attributed to the agent in the paragraph that follows. |
| 4 | The Agentic Engineering division of labour | `PROJECT_OBSERVATION` | Stated as the project's method, linked to the AGENTIC document. Not first person. |
| 5 | Adding the vendor-claim rule, append-only log, provenance, derived-artifact rule | `HUMAN_DECISION` | 所以反过来先给项目加了一堆限制 — project-level constraints, owner-set. |
| 6 | Preregistration as a project rule | `HUMAN_DECISION` | 先预注册，再调用 — a rule, not an act. |
| 7 | Registering 10 experiments and running them | `HUMAN_DECISION` + `AI_EXECUTION` | 第一轮登记了 10 个实验，全部跑完 — both verbs impersonal, no actor claimed. |
| 8 | The batching measurement, 816 vs 3,480 | `AI_EXECUTION` | Passive/impersonal: 合计吃掉 816 输入 token. No 我 measured. |
| 9 | The repeatability measurement, 5 identical requests | `AI_EXECUTION` | 一份逐字节相同的 512-token 请求发了五次 — passive. |
| 10 | Reading the official cookbook and finding the prior art | `HUMAN_DECISION` + `AI_EXECUTION` | 然后去翻官方 cookbook，找到了它 — bare verb, no 我. The decision to check prior art is the owner's; the retrieval is the agent's. |
| 11 | The `04_confidence` ambiguous case and its 0.61 | `AI_EXECUTION` | Described as a property of the experiment (有一个特意设计的模糊用例), not of the author. **P5-E1 re-worded the verdict clause** to 因此 Python policy 判成 accept, which moves the last trace of agency off the case and onto the code that evaluates it. |
| 12 | `12_function_routing` and the four suppressions | `AI_EXECUTION` | 让模型把请求路由到… — the experiment is the subject. |
| 13 | The finding that the four suppressions trace to `routing.py` | `PROJECT_OBSERVATION` | 四个拦截全部能追溯到 `routing.py` — the artifact is the subject. |
| 14 | The four candidates all falling | `PROJECT_OBSERVATION` | Stated about the candidate list, with the differing reasons separated. |
| 15 | The `07` effect, 0.75 → 0.20 | `AI_EXECUTION` | 事情来自 `07_instruction_precision` — the experiment is the subject. |
| 16 | Both arms changed instructions **and** criteria | `AI_EXECUTION` | 两个臂同时改了 instructions 和 criteria — passive, and states the defect rather than excusing it. |
| 17 | Committing design, order, statistics and thresholds before the first request | `HUMAN_DECISION` | 全部写下来并提交了 — passive. The commitment is the owner's; the writing was the agent's; the sentence names neither, and the *binding* is what matters. |
| 18 | The 12 calls, hard-capped | `AI_EXECUTION` | 12 次调用全部成功 — passive. |
| 19 | K1 firing; `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION` | `PROJECT_OBSERVATION` | 按照预注册的规则，结论是… The rule produces the verdict; no one is credited with it. |
| 20 | The analyzer defect: disclosure, repair, preserved rendering | `AI_EXECUTION` + `HUMAN_DECISION` | Written impersonally throughout — 被披露的 / 没有等别人发现 / 修复是一次独立的、后置的提交. The owner's part is the decision not to hide it or re-run, carried as 没有被拿去重跑一次让自己好看点的实验. |
| 21 | `ERR-001`: the 45/45 count, P1 left unedited | `AI_EXECUTION` + `HUMAN_DECISION` | 独立复核的时候发现 / P1 的文本没有被改. The recount is the agent's; leaving the historical audit untouched is the owner's. |
| 22 | Retiring five registered, never-run designs | `HUMAN_DECISION` | 5 个已经登记但从未运行的实验全部被退休了. Experiment retirement is named in the owner's role list; the sentence is passive and the decision is the owner's. |
| 23 | The non-claims | `PROJECT_OBSERVATION` | Statements about what the evidence supports. |
| 24 | The NAS question being kept open | `HUMAN_DECISION` + `AUTHORIAL_REFLECTION` | 这个问题确实想留下来 — an intent, not an execution. |
| 25 | The closing disclosure of AI involvement | `PROJECT_OBSERVATION` | The role split, stated plainly. |
| 26 | Cognitive debt, its definition and the repayment argument | `AUTHORIAL_REFLECTION` | The owner's working concept, explicitly labelled as one. |
| 27 | The gorilla and fire metaphor | `AUTHORIAL_REFLECTION` | Used once, as a figure. |
| 28 | 这篇文章是开始偿还的第一笔 | `AUTHORIAL_REFLECTION` | Editorial stance about the article itself. |
| 29 | The rate divergence: implementation advanced faster than the owner's comprehension of it | `AUTHORIAL_REFLECTION` | **Split out as its own row in the P5-E1 re-verification.** Revision 1 folded it into row 26 as part of the cognitive-debt argument; it is a distinct process statement and is now counted as one. The P5-E1 wording made it *more* precise rather than less: the P5-E form (实施的速度主要由 agent 决定，而理解的速度仍然由人决定) named a generic 人 as the second party, and the corrected form (agent 把实施推进得远快于 owner 消化这些工作的速度) names the role. Neither form attributes an execution to the owner. |

**No row is unresolved.** Every statement either names an owner-level act, is impersonal with the
artifact or the rule as its subject, or is explicitly framed as reflection. `PROCESS_ATTRIBUTION_UNRESOLVED = 0`.

---

## 5. The disclosure, checked against the two failure modes it was written to avoid

The work order named two ways the ending could go wrong. Both were checked in the finished text.

**5.1 It must not be a "gotcha".** The disclosure is not saved for a twist: the Agentic Engineering
method is named in the **测量台** section, roughly a fifth of the way in, and the ending returns to it
rather than revealing it. The article states its own reason — 这篇文章的生产关系本身就是这个项目元层实验的一部分，所以它写在正文里，而不是藏在脚注里. A reader who stops halfway has already been told.

**5.2 It must not over-claim the AI's share.** The article uses 大部分 for the implementation and
主要 for each role, and it names the owner's own column explicitly — 决定这个项目要回答什么问题 /
决定每个阶段做什么不做什么 / 批准或者否决关键步骤 / 在那些只有 owner 能拍板的地方拍板. It does **not**
contain 全程完全由 AI 完成, 全部由 AI 完成, or any equivalent. The owner made the direction,
authorisation and acceptance decisions, and the article says so in the same paragraph as the
disclosure rather than in a hedge elsewhere.

**5.3 The one sentence that had to change rather than move.** The P5-D opening was 我跑了 54 次调用.
The replacement does not merely reword it — it names it and rejects it: 写成「我跑了 54 次调用」会是
一句不准确的话。具体调用主要是 agent 执行的。 This is the point of the whole audit in one sentence,
and it is deliberately kept in the article rather than performed silently.

---

## 6. Domain separation: these claims are not in the Jev contract

`Agentic Engineering`, the role attribution, 认知负债 and the authorial reflection are **not Jev
model claims**, and they are not entered into the scientific contract. They carry no
`SAFE_TO_STATE` or `SAFE_WITH_SCOPE` class, they are not audited in
[`…CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md) §2, and no qualifier
would make them auditable there — the contract's question is what the evidence carries about Jev,
and none of these statements is about Jev at all.

They are accounted for here, and by the owner declaration this audit rests on. The separation runs
both ways: if process statements were admitted to the evidence layer, the frozen verifier would be
attesting to text it cannot read; and if the evidence layer's authority were borrowed for the
process layer, this audit would be claiming a rigour it does not have — §1 says it cannot recover
"who acted" from Git, and no amount of cross-referencing would change that.

---

## 7. Totals

| Result | P5-D | P5-E | P5-E1 |
|---|---:|---:|---:|
| First-person singular pronouns (我, excluding 我们) | **92** | **2** | **2** |
| …of which assert an action performed in this project | 88 | **0** | **0** |
| …of which are quotations rather than assertions | 4 | **2** | **2** |
| First-person action phrases **absent** from the article | 8 of 10 | **9 of 10** | **9 of 10** |
| Process statements classified | — | 28 | **29** |
| `PROCESS_ATTRIBUTION_UNRESOLVED` | — | **0** | **0** |

**The two survivors are both quotations, and neither is an assertion by the article.** One is
「我觉得它有时候不太行」, a reader's impression being ruled out inside a subordinate clause. The
other is 「我跑了 54 次调用」, named in order to be called inaccurate. No sentence in the finished
article attributes an execution in this project to the owner.

The re-attributions were made by changing the *actor*, not by weakening the sentence. This is
checkable against the P5-D text, and the four that would have been most tempting to delete instead
are still present in full: the 0.60 constant is still named and still called uncalibrated; the
analyzer defect, its disclosure and its post-run repair are still described at the same length; P1
still stands unedited with the erratum carrying the corrected count; and the four routing
suppressions are still traced to `routing.py`. Nothing was removed to make the attribution easier,
and no number or scope clause changed in the process — the claim audit's
[bilingual token check](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md) confirms all 18
figures survive.

---

## 8. What this audit does not cover

- **Whether the owner declaration is true.** It is testimony. The audit checks the article against
  the declaration; it cannot check the declaration against the world. §1 says so, and repeating it
  here is the point rather than a formality.
- **Per-line or per-sentence attribution.** The declaration itself disclaims this: 每一行代码、每一
  句话都无法被精确归属. A claim of per-line accuracy in either direction would be false, so this audit
  works at the level of actions the article actually asserts.
- **The English article.** It is frozen at P5-B and was not modified or re-attributed in P5-E or P5-E1.
  It still contains the P5-B first-person framing, and any statement here about the Chinese is not a
  statement about it.
- **Jev claims.** Nothing here bears on whether a sentence about Jev is permitted. That is the claim
  audit's job, and the two are deliberately not merged.

---

## 9. The P5-E1 re-verification

P5-E1 corrected nine passages across the article. Its work order named one failure mode for this audit to
check for specifically: **that the editorial pass did not reintroduce an owner-performed-agent-execution
misattribution.** The whole search was therefore re-run against the corrected text, not spot-checked.

**Result: no drift.** `PROCESS_ATTRIBUTION_UNRESOLVED = 0`, and the counts in §7 are unchanged from
revision 1 in every row that existed in revision 1.

| Check | P5-E | P5-E1 | Note |
|---|---:|---:|---|
| The ten first-person action phrases | 9 of 10 absent | **9 of 10 absent** | 我跑了 still appears once, still only as the construction the article names and refuses. |
| 我 occurrences read in context | 3 | **3** | Same three lines. Two of the nine corrections touched lines that contain 我 — §3's canonical-log sentence and §6's rate-mismatch sentence — and neither added or removed one. |
| 我 as a total character count | 4 (2 singular + 2 我们) | **4 (2 singular + 2 我们)** | Unchanged. |
| Sentences attributing an execution to the owner | 0 | **0** | None. |

**Two of the nine corrections moved attribution in the right direction rather than merely preserving it.**

- **§6** replaced a sentence in which a generic 人 was the party whose understanding had to keep up
  (理解的速度仍然由人决定) with one that names the role (owner 消化这些工作的速度). The old form was not
  an owner-execution claim, but it was vaguer than the declaration it rests on, and vagueness in
  attribution is the failure mode one step removed from the one this audit exists to catch.
- **§5** moved the verdict on the `04_confidence` case from the case itself (于是被判成 accept) to the
  code that evaluates it (因此 Python policy 判成 accept). The case is a state; a state does not decide
  anything. The correction removes the last grammatical agent from a sentence that had been carrying one
  by ellipsis.

**What the pass did not do.** It did not delete a sentence to make attribution easier, and the check for
that is the same one revision 1 used: the four passages most tempting to remove are all still present in
full. One of the nine corrections *is* a deletion — the 删故事 compression, work order §9 — but it is a
*style* deletion, removing one of two near-identical statements of the device, and C-67's content survives
it (claim audit §1.5). It removed no actor and no action. The agent-execution
disclosure paragraph, the owner's four-part role list, and the 我跑了 refusal are all byte-for-byte what
revision 1 classified.
