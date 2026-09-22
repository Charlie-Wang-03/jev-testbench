# Documentation index

Everything in this repository is organised around one idea: **a claim is only as good as the
evidence label attached to it.** These pages are grouped by what you are trying to do.

Most public-facing documents exist in **English and Simplified Chinese**. The evidence artifacts
(the audits, the preregistration, the result, the source registry) are canonical in **English
only** — deliberately, so that the evidence layer has one textual source rather than two that can
drift apart.

---

## Start here

| Document | What it is |
|---|---|
| [README](../README.md) | Project overview, the experiment map, and what you can and cannot conclude. |
| [Architecture](architecture/architecture.md) · [中文](architecture/architecture.zh-CN.md) | How data moves through the bench, the agent-control pattern, and the module map. |
| [Reproducibility](guides/reproducibility.md) · [中文](guides/reproducibility.zh-CN.md) | The fully-offline path, the live path, and what "reproduce" can honestly mean here. |

## Understand the evidence

| Document | What it is |
|---|---|
| [Findings](findings/findings.md) · [中文](findings/findings.zh-CN.md) | What reproduced, engineering lessons, findings deliberately killed, and scope limits. |
| [Final local evaluation](../results/JEV_LOCAL_EVALUATION_FINAL.md) | All 42 records with every claim labelled. **Derived artifact** — regenerable, never a source of truth. |
| [P1 — official claims audit](audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md) | Every TypeSafe claim we could locate, audited against local evidence. Verdict: `P1_OFFICIAL_LOCAL_AUDIT_PASS`. |
| [P2 — novelty triage](audits/P2_JEV_INSIGHT_TRIAGE.md) | The triage that retired seven candidates, including the two with the largest effect sizes. Verdict: `P2_TRIAGE_PASS`. |
| [P3 — boundary locus result](audits/P3_BOUNDARY_LOCUS_RESULT.md) | The preregistered replication, and its null. Verdict: `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`. |
| [P3 — preregistration](experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) | The design, order, thresholds and statistics, frozen before the first request. |
| [Evidence provenance](EVIDENCE_PROVENANCE.md) | The P0–P3 lineage: which commits measured, which analysed, which only documented. |

## Reproduce and extend

| Document | What it is |
|---|---|
| [Methodology](methodology/evaluation.md) · [中文](methodology/evaluation.zh-CN.md) | Claim labelling, experiment design rules, and what the A/B arms do and do not establish. |
| [Credentials](guides/credentials.md) · [中文](guides/credentials.zh-CN.md) | How the API key is resolved, and the honest limits of that scheme. |
| [Contributing](../CONTRIBUTING.md) | Setup, the offline-first rule, and what a change here has to preserve. |
| [Security](../SECURITY.md) | The real risks in this project, and how to report a problem. |

## Reference

| Document | What it is |
|---|---|
| [Official sources registry](sources/TYPESAFE_OFFICIAL_SOURCES.md) | Provenance for every TypeSafe document cited in this repository. |
| [Core freeze](../FREEZE.md) | The original 42-record freeze — a historical pointer, scoped to the core evaluation. |
| [License decision](OPEN_SOURCE_LICENSE_DECISION.md) | Why this repository currently has no open-source license. |
| [Agent rules](../CLAUDE.md) | The working rules for coding agents in this repository. **Not a security boundary.** |

---

## Reading order, if you only read three things

1. [README](../README.md) — what this is and what it does not claim.
2. [Findings](findings/findings.md) — including the section on what was killed.
3. [P2 triage](audits/P2_JEV_INSIGHT_TRIAGE.md) — the reasoning behind those kills.
