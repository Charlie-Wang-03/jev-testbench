# Documentation index

Everything in this repository is organised around one idea: **a claim is only as good as the
evidence label attached to it.** These pages are grouped by what you are trying to do.

Most public-facing documents exist in **English and Simplified Chinese**. The evidence artifacts
(the audits, the preregistration, the result, the source registry) are canonical in **English
only** — deliberately, so that the evidence layer has one textual source rather than two that can
drift apart.

> **Project name.** The project is `jev-testbench`. It was named `jev-test` until the rename in
> P5-E, and the frozen `v0.1.0` release keeps the name it was published under — a historical
> document saying `jev-test` is accurate about the release, not stale.
>
> **License: MIT.** See [`LICENSE`](../LICENSE) and the [license
> decision](OPEN_SOURCE_LICENSE_DECISION.md). One license covers the code, the two canonical logs,
> and the derived reports.
>
> **Released evidence: [`v0.1.0`](evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md).** If you are citing
> this repository, cite the tag, not `main`. The frozen set, its manifest and the rules for what may
> be said about it are under [`docs/evidence/`](evidence/README.md).

---

## Start here

| Document | What it is |
|---|---|
| [README](../README.md) | Project overview, the experiment map, and what you can and cannot conclude. |
| [Architecture](architecture/architecture.md) · [中文](architecture/architecture.zh-CN.md) | How data moves through the bench, the agent-control pattern, and the module map. |
| [Reproducibility](guides/reproducibility.md) · [中文](guides/reproducibility.zh-CN.md) | The fully-offline path, the live path, and what "reproduce" can honestly mean here. |
| [Agentic Engineering and cognitive debt](AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md) · [中文](AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.zh-CN.md) | How this bench was built: the human/AI division of labour, and the cognitive debt it left. **Process record — not evidence.** |

## Understand the evidence

| Document | What it is |
|---|---|
| [Findings](findings/findings.md) · [中文](findings/findings.zh-CN.md) | What reproduced, engineering lessons, findings deliberately killed, and scope limits. |
| [Technical blog](blog/jev-as-probabilistic-decision-primitive.md) · [中文](blog/jev-as-probabilistic-decision-primitive.zh-CN.md) | A narrative walk through the bench: what it measured, the preregistered null, and the evaluation lessons. Both language versions are current. The Chinese text is the approved narrative and is frozen; the English is a fresh adaptation from it, not a translation, and has since been through **two human editorial passes** — a micro-pass of seven wording corrections and a final human-read pass of seven sentence rewrites, neither of them structural. **Both language versions have completed human editorial review and are frozen for publication except for hard defects.** |
| [Blog claim audit](blog/jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md) | Every substantive claim in **either** article about Jev, about this bench's measurements, or about what TypeSafe published, mapped to its `BLOG_CLAIM_CONTRACT.md` class and its evidence. Revision 12 is the final human-read corrections: seven sentences rewritten, one row's statement narrowed, no row added, retired or reclassified — the totals hold at 70 — and §1.11 records the two further places where the English is deliberately narrower than the Chinese. Revision 11 was the English editorial micro-pass, whose §1.10 records the first four such places and why that direction is the safe one. Revision 10 was the bilingual re-audit that re-located all 70 claims in both articles, retired C-68, and restored the three cross-language parity gates — novelty, factual/numeric, scope — all `PASS`. §5 records what the contract deliberately does not reach. |
| [Blog style audit (中文)](blog/jev-as-probabilistic-decision-primitive.STYLE_AUDIT.zh-CN.md) | The L1–L4 style self-check for the Chinese text, with the technical exceptions and the evidence-contract overrides it runs under. Revision 7 recomputes the figures after the narrative positioning closure and adds a **Normative-tone check**; the one sentence that changed takes 单句成段 from 101 to 100, and nothing was added to compensate. Revision 6 recomputed the figures after the scope cleanup, when the article got shorter for the first time. |
| [Blog style audit (English)](blog/jev-as-probabilistic-decision-primitive.STYLE_AUDIT.en.md) | The same L1–L4 layers applied to the English text, plus the checks only English needs: literal-translation calques, paper voice, marketing voice, résumé voice, and whether the short-beat rhythm is overstruck. Revision 3 recomputes every count after the final human-read corrections and **states the counting method for the first time**, so that every figure can be re-run; the revisions 1–2 figures did not reproduce, and §2.0 says which numbers moved for that reason alone. Revision 2 recomputed after the editorial micro-pass. **Author-side audit — not a human editorial review.** |
| [Blog process attribution audit (中文)](blog/jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md) | Who did what, checked against the owner's process declaration rather than against the frozen evidence. Revision 4 recomputes after the scope cleanup, which removed one row. The categories and the rule are defined here, once. **Process record — not a Jev claim.** |
| [Blog process attribution audit (English)](blog/jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.en.md) | The same rule applied to the English text, which was checked rather than assumed clean because adaptation is where a first-person execution claim would reappear. Eleven of twelve first-person action phrases are absent; the twelfth is the sentence the article quotes in order to call it inaccurate. Revision 3 adds the two collective forms the final human-read corrections introduced, taking the sweep to seven. Revision 2 corrected a miscount of the P3 arm label and added the first five. `PROCESS_ATTRIBUTION_UNRESOLVED_EN = 0`. **Process record — not a Jev claim.** |
| [English realignment handoff](blog/ENGLISH_REALIGNMENT_HANDOFF.md) | The constraint the English realignment was performed under, written before the work began and now marked complete: **NAS content must not be carried into the new English adaptation, and nothing substituted for it.** Kept rather than replaced, with the handoff preserved unedited below the completion record. Holds `ENGLISH_REALIGNMENT = COMPLETE` and `PARITY = PASS`. |
| [Final local evaluation](../results/JEV_LOCAL_EVALUATION_FINAL.md) | All 42 records with every claim labelled. **Derived artifact** — regenerable, never a source of truth. |
| [P1 — official claims audit](audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md) | Every TypeSafe claim we could locate, audited against local evidence. Verdict: `P1_OFFICIAL_LOCAL_AUDIT_PASS`. |
| [P2 — novelty triage](audits/P2_JEV_INSIGHT_TRIAGE.md) | The triage that retired seven candidates, including the two with the largest effect sizes. Verdict: `P2_TRIAGE_PASS`. |
| [P3 — boundary locus result](audits/P3_BOUNDARY_LOCUS_RESULT.md) | The preregistered replication, and its null. Verdict: `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`. |
| [P3 — preregistration](experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) | The design, order, thresholds and statistics, frozen before the first request. |
| [Experiment registry](experiments/EXPERIMENT_REGISTRY.md) | The registry at the public-release revision: what ran, and what was retired before publication and why. |
| [Evidence provenance](EVIDENCE_PROVENANCE.md) | The P0–P3 lineage: which commits measured, which analysed, which only documented. |

## Reproduce and extend

| Document | What it is |
|---|---|
| [Methodology](methodology/evaluation.md) · [中文](methodology/evaluation.zh-CN.md) | Claim labelling, experiment design rules, and what the A/B arms do and do not establish. |
| [Credentials](guides/credentials.md) · [中文](guides/credentials.zh-CN.md) | How the API key is resolved, and the honest limits of that scheme. |
| [Contributing](../CONTRIBUTING.md) | Setup, the license, and the rules a change here has to preserve. |
| [Security](../SECURITY.md) | The real risks in this project, and how to report a problem. |

## Publication readiness

**Nothing in this section has been published.** The repository is private, no GitHub Release exists,
and no external post has been made. These files are the decision pack for the owner, prepared so the
decisions can be taken against exact wording rather than against a description of it.

| Document | What it is |
|---|---|
| [Publication checklist](publication/PUBLICATION_CHECKLIST.md) | What has passed mechanically, the human editorial gate, and the decisions only the owner can take. **Start here.** |
| [Blog publication options](publication/BLOG_PUBLICATION_OPTIONS.md) | Repository-only, external venues, or canonical-plus-syndication; the trade-offs, without a decision. |
| [GitHub Release draft](publication/GITHUB_RELEASE_DRAFT.md) | The exact release body that would be used, if a Release is decided on. Not published. |
| [Repository metadata proposal](publication/REPOSITORY_METADATA_PROPOSAL.md) | Proposed description and topics, with what is deliberately absent from them. Not applied. |
| [TypeSafe feedback draft](publication/TYPESAFE_FEEDBACK_DRAFT.md) | Four `V1_DOCUMENTATION_FEEDBACK` observations. **Not sent.** Every item needs a fresh recheck first. |

## Reference

| Document | What it is |
|---|---|
| [Official sources registry](sources/TYPESAFE_OFFICIAL_SOURCES.md) | Provenance for every TypeSafe document cited in this repository. |
| [Core freeze](../FREEZE.md) | The original 42-record freeze — a historical pointer, scoped to the core evaluation. |
| [License decision](OPEN_SOURCE_LICENSE_DECISION.md) | The recorded decision: MIT, and the alternative that was considered. |
| [Agent rules](../CLAUDE.md) | The working rules for coding agents in this repository. **Not a security boundary.** |

---

## Reading order, if you only read three things

1. [README](../README.md) — what this is and what it does not claim.
2. [Findings](findings/findings.md) — including the section on what was killed.
3. [P2 triage](audits/P2_JEV_INSIGHT_TRIAGE.md) — the reasoning behind those kills.
