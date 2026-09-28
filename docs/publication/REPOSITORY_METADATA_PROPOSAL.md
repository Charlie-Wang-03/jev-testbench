# Repository metadata proposal

**Status: APPLIED, WITH OWNER-REQUESTED BILINGUAL ABOUT FOLLOW-UP.** The repository is public, the homepage remains empty, and topics are live. The owner subsequently requested that the About description become bilingual; the connected GitHub integration cannot write repository-administration fields, so that one follow-up is manual.

**One item in this file is no longer a proposal.** The repository rename was decided by the owner in
P5-E and applied: `PROJECT_RENAME: OWNER_APPROVED`, `jev-test` → `jev-testbench`. See
[Repository name](#repository-name) for exactly what that did and did not touch.

---

## Description

**Publication Closure recommendation:**

```
A lightweight, auditable Jev testbench built through Agentic Engineering, with frozen evidence, a
preregistered null result, and a bilingual reflection on cognitive debt.
```

This description names the current project rather than the historical `v0.1.0` release. It keeps
`benchmark`, performance numbers, novelty language and production claims out of the repository
metadata. `cognitive debt` is presented as a reflection topic, not as a scientific metric or a new
standard.

---

## Homepage

**Recommendation: leave the GitHub repository homepage field empty for the first publication.**

There is no external canonical site yet. Pointing the homepage field back to this same repository
adds no navigation value, while choosing an external venue now would turn an optional distribution
decision into part of the repository identity. If a durable personal/project site is published
later, the field can be set then without changing the evidence or release semantics.

---
## Topics

The live topic set is:

```text
agentic-engineering
ai-agents
jev
llm
model-evaluation
preregistration
probabilistic-ai
python
reproducibility
typesafe
typesafe-ai
```

The first ten match the Publication Closure recommendation. `typesafe-ai` was also applied by the
owner; it is a narrow discovery alias and does not widen any scientific claim.

Not used: `benchmark`, `leaderboard`, `calibration`, `production-ready`, or `cognitive-debt`.

---
## Repository name

**`PROJECT_RENAME: OWNER_APPROVED`** — decided by the owner in P5-E, and applied.

`jev-test` read as a scratch name because it was one when the repository was created. The owner
renamed it to **`jev-testbench`**, and chose to do it while the repository is still private, which is
the point at which a rename costs almost nothing.

What the rename did and did not touch:

| Aspect | Effect of the rename |
|---|---|
| The GitHub repository | Now `Charlie-Wang-03/jev-testbench`. The old path redirects to it. |
| The distribution name | Now `jev-testbench`. The import package stays `jev_lab`, because the supported interface is the CLI and the evidence files, not a Python library API. |
| The frozen release `v0.1.0` | **Unchanged.** It was published under the name `jev-test`, and that is a historical fact about it rather than a stale string. |
| [`docs/evidence/v0.1.0/`](../evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) | **Unchanged.** Its manifest still records `"name": "jev-test"`, and `evidence_freeze verify v0.1.0` still passes. |
| [`CITATION.cff`](../../CITATION.cff) | On the `v0.1.1` release commit, identifies the current `jev-testbench` Publication Closure release. The immutable `v0.1.0` tag keeps its own historical `CITATION.cff` under `jev-test`. |
| The bilingual blog | Current and human-approved. Historical `jev-test` mentions remain only where they describe the pre-rename project state or frozen provenance. |

The one thing that must not happen is creating a new repository at `Charlie-Wang-03/jev-test`. The
GitHub redirect from the old path to the new one is what keeps the historical links in the frozen
release, in the release notes and in the blog resolving. A new repository at the old path would take
that redirect over and break every one of them.

---

## Owner actions

Description, homepage and topics:

- [x] Apply the initial approved English description.
- [x] Apply topics.
- [x] Leave the homepage field empty.
- [ ] Replace the About description with the owner-requested bilingual wording recorded in the final publication closure record.

Name:

- [x] The repository rename — decided in P5-E: `PROJECT_RENAME: OWNER_APPROVED`.
- [x] Apply it: `Charlie-Wang-03/jev-test` → `Charlie-Wang-03/jev-testbench` — done by the owner.

**The repository is `PUBLIC`; homepage and topics are in their intended live state. Only the bilingual About wording follow-up remains.**
