# Publication checklist

**Status: every automated gate is green. Nothing has been published. The repository is private and
must stay private until the owner decides otherwise.**

This checklist separates three things that are easy to blur together: what has already been
established mechanically, what only a human can establish, and what only the owner can decide.
Nothing in the third group is pre-approved by anything in the first.

---

## 1. Already passed

Established by running things, not by asserting them. None of it needs a TypeSafe API key or makes a
Jev inference call; installing dependencies is the only step that needs network access.

| Gate | Evidence |
|---|---|
| **Evidence frozen** | Tag `v0.1.0` → `37ef2e4`; `evidence_freeze verify v0.1.0` PASS, 34 files hashed. |
| **Canonical logs unchanged** | `38e67630…` (42 core) and `17f36f75…` (12 P3). Re-hashed during the audit. |
| **License resolved** | MIT; `LICENSE`, `pyproject.toml` and both READMEs agree. Asserted by the suite. |
| **Secret audit** | Current tree and full reachable history, all branches and tags. No credential, token, key, local path or personal identifier found. See the P5-C report. |
| **CI** | Green on Linux for the P5-P, P5-B and P5-C revisions. Offline, sockets blocked, `TYPESAFE_API_KEY` empty by construction. |
| **Bilingual claim audit** | 64 claims × 2 languages. `DO_NOT_STATE_ZH = 0`, `DO_NOT_STATE_EN = 0`. |
| **Relative links** | Asserted over every tracked `.md` by the offline suite. |
| **Tag verification** | `verify v0.1.0` reads the tag tree, not the working tree, so `main` may move while the release stays fixed. |
| **Offline test suite** | Green on Windows (development) and on Linux (CI). |

**Also already true, and worth stating:** no API call has been made since the freeze. The P5-A, P5-B,
P5-C and P5-C1 stages produced presentation and infrastructure only.

---

## 2. `HUMAN_EDITORIAL_REVIEW_REQUIRED_BEFORE_EXTERNAL_PUBLICATION`

**This gate is open. It has not been satisfied, and nothing automated can satisfy it.**

### What it is, and what it is not

It is **not** an evidence gate. The evidence layer is complete: the claims are audited, the numbers
are re-derived from the canonical logs, CI is green, the freeze verifies. Scientific integrity is
not what is outstanding.

It is an **editorial and publication-quality gate.** Specifically:

- The Chinese article has been rewritten in four places (§1.2 of the claim audit) since it was first
  drafted, and never read end to end by anyone afterwards.
- The English article is an adaptation written in one session. It has never been read by a native
  English technical reader, and it has never been read by anyone other than its author and the agent
  that produced it.
- The claim audit checks what the articles **assert**. It says nothing about whether they read well,
  whether the English lands as natural prose, or whether a section is unclear to someone who does
  not already know the project.

**An agent cannot substitute for this read.** Producing more analysis of the text is not the same
act as a human reading it, and P5-C does not claim otherwise. The distinction is the point of this
section: the mechanical gates are genuinely finished, and this one is genuinely not.

### What the owner must actually do

- [ ] Read the **Chinese article** in full:
      [`jev-as-probabilistic-decision-primitive.zh-CN.md`](../blog/jev-as-probabilistic-decision-primitive.zh-CN.md)
- [ ] Read the **English article** in full, or at minimum the opening, §6, §10, §11 and §16:
      [`jev-as-probabilistic-decision-primitive.md`](../blog/jev-as-probabilistic-decision-primitive.md)
- [ ] Confirm each is something you are willing to have your name on.

Until those boxes are ticked by the owner, external publication is not ready — regardless of how
green everything above is.

---

## 3. Owner decisions required

None of these has been taken. Each is a decision, not a task that was missed.

- [ ] **Make the GitHub repository public?** — Currently `PRIVATE`. This is the decision with the
      largest blast radius: it is not reversible in the sense that matters, because a public
      repository can be cloned, indexed and mirrored.
- [ ] **Create a GitHub Release for `v0.1.0`?** — Draft text is in
      [`GITHUB_RELEASE_DRAFT.md`](GITHUB_RELEASE_DRAFT.md). The freeze notes record that no Release
      was part of the release; the tag is already the artifact.
- [ ] **Approve the repository description and topics?** — Proposal in
      [`REPOSITORY_METADATA_PROPOSAL.md`](REPOSITORY_METADATA_PROPOSAL.md). Setting them is a GitHub
      side change, not a repository change.
- [ ] **Approve the Chinese source article for publication?** — Only after the human read in §2.
- [ ] **Approve the English adaptation for publication?** — Only after the human read in §2.
- [ ] **Choose an external blog venue, if any?** — Comparison in
      [`BLOG_PUBLICATION_OPTIONS.md`](BLOG_PUBLICATION_OPTIONS.md). "Repository only" is a complete
      answer.
- [ ] **Send the TypeSafe V1 documentation feedback?** — Draft in
      [`TYPESAFE_FEEDBACK_DRAFT.md`](TYPESAFE_FEEDBACK_DRAFT.md). Every item is marked
      `NEEDS_FRESH_RECHECK_BEFORE_SEND` and nothing has been sent.

---

## 4. Optional, and explicitly not blockers

Listed so that they are visible as choices rather than forgotten. **Nothing here is required, and
none of it should be treated as gating.**

- [ ] A social preview image for the repository (deliberately not generated; see below).
- [ ] GitHub Pages for the blog, if option B or C in the venue comparison is chosen.
- [ ] A DOI via Zenodo, if the release should be citable by DOI rather than by tag.
- [ ] `CITATION.cff` review — it exists and points at the tag; a DOI would change it.
- [ ] Renaming the repository from `jev-test`. It reads as a scratch name. A rename is disruptive
      (redirects, citation links, the freeze's own URLs) and is the owner's call; P5-C does not
      rename it and suggests no name.

**No decorative assets were created during P5-C.** No logo, no social card, no architecture
illustration. Adding image assets to a release candidate that is otherwise byte-accounted-for would
pollute it for no benefit at this stage.

---

## 5. Standing rule for anything published later

Whoever publishes any version of these articles, anywhere:

1. **The canonical text stays `docs/blog/**`.** Any platform copy is downstream of it.
2. **A platform adaptation must not widen a claim.** Reformatting for a venue is fine; adding a
   sentence that the claim audit did not cover is not.
3. **Link to `v0.1.0`, not to `main`.** `main` moves; the release does not.
4. **A correction goes to the canonical text first**, then propagates.

**Repository state right now: `PRIVATE` · no GitHub Release · no external blog publication · no
TypeSafe message sent.**
