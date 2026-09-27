# Process attribution audit — the English article

**Audited document:** [`jev-as-probabilistic-decision-primitive.md`](jev-as-probabilistic-decision-primitive.md)
**Basis of this audit:** `OWNER_DECLARED_PROJECT_PROCESS` — the owner's declaration of who did what,
recorded in [`AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md`](../AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md) §2.
**Not a basis:** the `v0.1.0` frozen evidence. The Chinese audit's §6 explains why that is so, and the
reasoning is not repeated here.
**Audit date:** 2026-09-28 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 2 — recomputed after the English editorial micro-pass. Revision 1 miscounted the bare `I`s by
one and did not count collective forms at all; both are corrected below, and the two new collective
phrases the micro-pass introduced are classified. **`PROCESS_ATTRIBUTION_UNRESOLVED_EN` is 0 in both
revisions** — the corrections change counts, not the verdict, because neither the mis-counted `I` nor any
collective form attributes an execution to the owner.

---

## 1. Why the English has its own file, and what it does not repeat

**The categories, the rule, the evidential limit and the domain separation are defined once, in
[`…PROCESS_ATTRIBUTION_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md),
and are not restated here.** That file is the definition; this one is a second application of it. The four
categories (`HUMAN_DECISION`, `AI_EXECUTION`, `PROJECT_OBSERVATION`, `AUTHORIAL_REFLECTION`), the rule that
*no sentence may attribute to the owner an execution the agent performed*, the statement that the basis is
testimony rather than evidence, and the refusal to claim per-line accuracy all hold here unchanged.

**Why a second application is needed at all.** The Chinese article was written in the first person and
folded owner decisions and agent executions into the same 我; 92 instances were re-attributed. **The English
adaptation was written from the re-attributed Chinese**, so it did not inherit that defect — but it was
checked rather than assumed, because English technical writing pulls hard toward *"I built this"*, and a
fresh adaptation is exactly where the claim would reappear if it were going to. A language that says *I*
more easily than Chinese does is not automatically a language that says *I* more accurately.

**What this file is not.** It is not a style audit (that is
[`…STYLE_AUDIT.en.md`](jev-as-probabilistic-decision-primitive.STYLE_AUDIT.en.md)) and not a claim audit
(that is [`…CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md)). A sentence can be
perfectly attributed and still be a claim defect, and the three audits are kept separate for that reason.

---

## 2. The search

Twelve first-person action phrases — the six named in the work order, plus six more of the same kind —
counted across the whole English article:

| Phrase | Occurrences | Where | Classification |
|---|---:|---|---|
| I ran | **1** | §16 | **Quoted in order to refuse it.** *Writing "I ran 54 calls" would be an inaccurate sentence. The calls themselves were primarily executed by the agent.* Not an attribution defect; it is the repair. |
| I wrote | 0 | — | — |
| I implemented | 0 | — | — |
| I discovered | 0 | — | — |
| I fixed | 0 | — | — |
| I executed | 0 | — | — |
| I built | 0 | — | — |
| I designed | 0 | — | — |
| I called | 0 | — | — |
| I generated | 0 | — | — |
| I tested | 0 | — | — |
| I deleted | 0 | — | — |

**Eleven of the twelve are absent from the article entirely.** The twelfth appears once, inside quotation
marks, as the example of what the article is *not* saying — the same sentence, in the same role, that the
Chinese audit records as 我跑了.

### 2.1 The wider sweep

A phrase list is not sufficient on its own, so every remaining first-person or collective form was read in
context.

**`I` as a word appears eight times. Seven of them are the P3 arm label** — `I` for the `instructions`-only
arm, in a table row, in the K1 expression `|I − C| = 0.05`, and in two sentences about medians. A variable
name is not a pronoun, and none of the seven is in the search. The eighth is the refusal above.
*(Revision 1 reported nine and eight. The extra one was a miscount of the arm label, not a second
pronoun.)*

| Line | Text | Classification | Why it stands |
|---|---|---|---|
| intro | What caught my attention about Jev was not another benchmark result. | `AUTHORIAL_REFLECTION` | Attention, not an action, and it is the article's only unquoted first-person singular. It claims no work. |
| §10 | What P3 produced is not "we failed to get a result". | `PROJECT_OBSERVATION` | A construction the article names in order to reject; the subject of the sentence is the experiment. |
| §12 | The model answers what this state means; the code answers whether we are allowed to act. | `AUTHORIAL_REFLECTION` | Generic *we* inside a design principle. Names no actor and no action in this project — the same sentence the Chinese audit classifies the same way. |
| §12 | …as "we may execute" has removed exactly the layer… | `AUTHORIAL_REFLECTION` | The same design principle, quoted back. Generic, and the same in the Chinese. |

### 2.2 The collective forms, counted rather than waved at

Revision 1 said the article's only `we` was in a design principle and a refused quotation. That was
imprecise then and is incomplete now, because the editorial micro-pass added one. **The collective forms
are counted here in full: `we` four times, `our` once, `us` zero, `me` zero, `my` once.**

| Line | Text | Classification | Why it stands |
|---|---|---|---|
| §7 | The vendor material **we** reviewed did not decompose it. | `PROJECT_OBSERVATION` | **New in the micro-pass.** Names a collective doing a piece of work — reviewing vendor material — not the owner doing an execution. The work it names is the P2 evidence review, which the disclosure in §16 assigns to ChatGPT under owner direction. An owner-attribution defect would require the sentence to say the owner did it; `we` says the project did. |
| §7 | And **our** public-material search did not turn up a controlled attribution experiment. | `PROJECT_OBSERVATION` | **New in the micro-pass**, and the same reading. It replaces an agentless *nothing … turned up*, which hid the searcher entirely; naming the searcher is the correction, not a new claim about who searched. |
| §10 | …is not "**we** failed to get a result". | `PROJECT_OBSERVATION` | A quoted construction the article rejects. |
| §12 | …whether **we** are allowed to act. | `AUTHORIAL_REFLECTION` | Generic *we* in a design principle. |
| §12 | …as "**we** may execute"… | `AUTHORIAL_REFLECTION` | The same principle, quoted back. |

**Why none of the five is an unresolved attribution.** The rule this audit applies is that *no sentence may
attribute to the owner an execution the agent performed*. A collective form that names the project's own
work does not do that — it is the same register the Chinese uses throughout (这个项目, 这里的数据) and the
same register this audit's own `PROJECT_OBSERVATION` category exists to name. **The one thing that would
make a collective form a defect is a sentence where `we` can only mean the owner, and there is none.** The
singular forms — the ones that can only mean a person — remain at two, and both are accounted for.

**There is no contraction that hides a first-person verb.** `we're`, `I've`, `I'd` and `we've` are all
absent.

**The passages that carry the process are impersonal in both languages, and where the English names an
actor it names the right one.** The Agentic Engineering division of labour is stated plainly in §2 — *the
human owner set direction and acceptance, ChatGPT did decomposition, planning and review, and Claude Code
went into the repository to implement* — and §16 returns to it: *Most of the implementation was done by AI
agents — writing code, changing tests, making those 12 calls, repairing the analyzer, maintaining the
documentation*, followed by each role's column and the owner's, which is the four-part list of decisions
only an owner can take. Where the English uses the passive — *nothing deleted, nothing reordered, nothing
quietly fixed and written back*; *the defect was disclosed in the commit*; *the 12 records are
byte-identical* — **no actor is claimed at all**, which is the same position the Chinese takes in the
corresponding sentences and not a weaker one.

---

## 3. Totals

| Result | English |
|---|---:|
| First-person singular pronouns (excluding the P3 arm label `I`) | **2** |
| …of which assert an action performed in this project | **0** |
| …of which are quotations rather than assertions | **1** |
| Collective forms (`we` / `our` / `us`) | **5** |
| …of which can only mean the owner | **0** |
| First-person action phrases **absent** from the article | **11 of 12** |
| Sentences attributing an execution in this project to the owner | **0** |
| `PROCESS_ATTRIBUTION_UNRESOLVED_EN` | **0** |

**No row is unresolved.** Every process-bearing statement either names an owner-level decision, is
impersonal with the project or the artifact as its subject, or is an authorial reflection that claims no
action. The finished English article attributes no execution in this project to the owner, and the one
sentence it could have used to do so is the sentence it quotes in order to call it inaccurate.

**The two counts that matter are the same in both languages, which is the parity result rather than two
separate readings.** The Chinese has two 我, both quotations of things the article refuses; the English has
two first-person singulars, one of them the corresponding refusal. Neither article contains a first-person
execution claim.

---

## 4. What this audit does not cover

- **Whether the owner declaration is true.** It is testimony. The audit checks the article against the
  declaration; it cannot check the declaration against the world. The Chinese audit's §1 says so at length,
  and repeating it here would not add evidence.
- **Per-sentence attribution.** The declaration itself disclaims this, and a claim of per-line accuracy in
  either direction would be false.
- **The Chinese article.** Audited in the file named above, whose findings this one does not amend.
- **Jev claims.** Nothing here bears on whether a sentence about Jev is permitted. That is the claim
  audit's job, and the two are deliberately not merged.
