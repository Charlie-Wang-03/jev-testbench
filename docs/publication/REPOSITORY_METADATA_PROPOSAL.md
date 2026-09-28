# Repository metadata proposal

**Status: PROPOSAL ONLY. The description, homepage and topics below are not applied.** No GitHub description or
topic has been changed. These are GitHub-side fields; changing them is the owner's action, and this
file exists so the decision can be made against exact wording.

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

GitHub allows up to 20. The recommended set stays intentionally narrow.

**Publication Closure recommendation (10):**

| Topic | Why |
|---|---|
| `jev` | The subject itself. |
| `typesafe` | Product/vendor namespace used by the project. |
| `llm` | Broad discovery term for the surrounding model ecosystem. |
| `ai-agents` | The engineering context in which the primitive is evaluated. |
| `agentic-engineering` | The project-building/process layer explicitly documented here. |
| `model-evaluation` | The measurement and evidence discipline. |
| `reproducibility` | Frozen logs, deterministic derived artifacts and offline verification. |
| `preregistration` | The defining P3 design practice. |
| `probabilistic-ai` | The probabilistic-decision framing. |
| `python` | Implementation language. |

Not recommended: `benchmark`, `leaderboard`, `calibration`, `production-ready`, or
`cognitive-debt`. The first four would widen or misstate the project; the last would make a
project-level working concept look like an established technical taxonomy.
---|---|---|
| `jev` | The subject. Low volume, high precision — anyone searching it wants this. | Yes |
| `typesafe` | Same. | Yes |
| `llm` | The broad discovery term. High volume, but it is how most people would find this at all. | Yes |
| `ai-agents` | The engineering audience, and the half of the repository that is not evaluation. | Yes |
| `model-evaluation` | The method. | Yes |
| `reproducibility` | A stated value of the repository, not just a property of it. | Yes |
| `preregistration` | The distinguishing topic, and the one that carries the strongest signal about what this repository does differently. | Yes |
| `probabilistic-ai` | The paradigm the subject belongs to. | Yes |
| `python` | The implementation language. Ordinary, but it is a real filter for the audience. | Yes |

**Considered and not recommended:**

| Topic | Why not |
|---|---|
| `benchmark` / `benchmarking` | Attracts the reading the repository spends its whole text refusing. The wrong audience arrives expecting a leaderboard. |
| `uncertainty-quantification` / `calibration` | Accurate as a topic, but the repository explicitly does **not** validate calibration, and a topic tag does not carry a scope. |
| `llm-evaluation` alongside `model-evaluation` | Near-duplicate; two tags that mean the same thing spend a slot without adding reach. |
| `typesafe-ai` alongside `typesafe` | Same. |
| `data-science`, `machine-learning`, `artificial-intelligence` | Too broad to be a filter — they would put this in front of everyone and communicate nothing. |

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
| [`CITATION.cff`](../../CITATION.cff) | Keeps `version: 0.1.0` and the title it was published under; its URLs follow the repository. |
| The bilingual blog | Current and human-approved. Historical `jev-test` mentions remain only where they describe the pre-rename project state or frozen provenance. |

The one thing that must not happen is creating a new repository at `Charlie-Wang-03/jev-test`. The
GitHub redirect from the old path to the new one is what keeps the historical links in the frozen
release, in the release notes and in the blog resolving. A new repository at the old path would take
that redirect over and break every one of them.

---

## Owner actions

Description and topics:

- [ ] Approve, edit or reject the description above.
- [ ] Approve, edit or reject the topic set.
- [ ] Apply the approved metadata on GitHub.

Name:

- [x] The repository rename — decided in P5-E: `PROJECT_RENAME: OWNER_APPROVED`.
- [x] Apply it: `Charlie-Wang-03/jev-test` → `Charlie-Wang-03/jev-testbench` — done by the owner.

**No GitHub description, homepage or topic has been modified. The repository is `PRIVATE`; this file remains a proposal until the owner approves Publication Closure actions.**
