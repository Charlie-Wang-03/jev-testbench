# Repository metadata proposal

**Status: PROPOSAL ONLY. The description and topics below are not applied.** No GitHub description or
topic has been changed. These are GitHub-side fields; changing them is the owner's action, and this
file exists so the decision can be made against exact wording.

**One item in this file is no longer a proposal.** The repository rename was decided by the owner in
P5-E and applied: `PROJECT_RENAME: OWNER_APPROVED`, `jev-test` → `jev-testbench`. See
[Repository name](#repository-name) for exactly what that did and did not touch.

---

## Description

**Recommended:**

```
Auditable experiments on TypeSafe Jev: typed probabilistic decisions, agent control patterns,
preregistration, and a null result kept in the record.
```

138 characters — comfortably inside GitHub's 350-character limit, and inside the length a person
actually reads in a repository list.

### Why each part is there

| Phrase | Does this work |
|---|---|
| "Auditable experiments on TypeSafe Jev" | Says what the repository *is* and what it is *about*, and "on" rather than "by" or "for" keeps independence readable. |
| "typed probabilistic decisions" | The subject matter, in the vendor's own term of art. |
| "agent control patterns" | The engineering half, and the part a developer searching for it would recognise. |
| "preregistration" | The method claim, and the least common word here — it is the distinguishing one. |
| "a null result kept in the record" | The finding. Stated positively, and without making the null sound like a failure. |

### What is deliberately absent

| Not present | Why |
|---|---|
| Any novelty or discovery word | The release's state string is `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`. A description is the wrong place to widen that. |
| "benchmark" / "leaderboard" | There is no ground truth anywhere in this bench. Calling it a benchmark would invite exactly the reading the repository refuses. |
| "production-ready" / "enterprise" | Every handler is inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED`. |
| A speed, cost or accuracy number | The one batching figure belongs to a single payload and is not commensurable with the vendor's published multipliers. A number in a description has no room for its scope. |
| "official" / "TypeSafe-approved" | It is not. This is an independent third-party evaluation. |

### Alternatives, if the recommended one does not fit the owner's taste

**Shorter** — for a repository list where the description is truncated anyway:

```
Independent, auditable experiments on TypeSafe Jev — and the null result they produced.
```

**More explicit about independence** — if there is any concern that "TypeSafe Jev" reads as an
official repository:

```
Independent evaluation bench for TypeSafe Jev: preregistered experiments, canonical logs, and
evidence anyone can re-verify offline.
```

---

## Topics

GitHub allows up to 20. More than about ten stops helping and starts diluting.

**Recommended set (9):**

| Topic | Why | Keep? |
|---|---|---|
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
| The English blog adaptation | Still says `jev-test` where it describes the build. It is frozen pending re-alignment, not overlooked. |

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

**No GitHub description or topic has been modified. The repository is `PRIVATE`, the description and
the topics are unchanged, and `PROJECT_RENAME` is the only item here that is settled.**
