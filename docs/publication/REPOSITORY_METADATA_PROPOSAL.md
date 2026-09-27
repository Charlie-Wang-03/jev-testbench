# Repository metadata proposal

**Status: PROPOSAL ONLY. Nothing has been applied.** No description, topic, name or setting on
`Charlie-Wang-03/jev-test` has been changed by P5-C. These are GitHub-side fields; changing them is
the owner's action, and this file exists so the decision can be made against exact wording.

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

**Not changed, and no rename is proposed here.**

`jev-test` reads as a scratch name, and it was one when the repository was created. It now holds a
frozen evidence release with a citation pointing at it. A rename is a real cost:

- GitHub redirects the old path, but the **citation and the freeze documents name the URL**;
- the release notes and the blog both link to `Charlie-Wang-03/jev-test`;
- the tag `v0.1.0` does not encode the repository name, so the release itself would survive a rename
  intact — the links around it would not.

That balance may well favour renaming *before* publication rather than after, since a rename while
the repository is private costs almost nothing and a rename afterwards costs redirects and stale
citations. It is the owner's call, and P5-C takes no action either way.

---

## Owner actions, none taken

- [ ] Approve, edit or reject the description above.
- [ ] Approve, edit or reject the topic set.
- [ ] Decide about a repository rename, if any, **before** visibility changes rather than after.
- [ ] Apply the approved metadata on GitHub.

**No metadata has been modified. The repository is `PRIVATE` and its description and topics are
unchanged.**
