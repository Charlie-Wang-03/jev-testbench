# Publication checklist

**Status: Publication Closure PC0–PC2 is reconciled on a private repository. Nothing has been published. The repository remains private until the owner explicitly decides otherwise.**

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
| **CI** | Green on the approved publication SHA and again after its fast-forward promotion to `main`. Offline, sockets blocked, `TYPESAFE_API_KEY` empty by construction. |
| **Bilingual claim audit** | 70 substantive claims × 2 languages: 45 `SAFE_TO_STATE` + 25 `SAFE_WITH_SCOPE` + 0 `DO_NOT_STATE`. `DO_NOT_STATE_ZH = 0`, `DO_NOT_STATE_EN = 0`. |
| **Relative links** | Asserted over every tracked `.md` by the offline suite. |
| **Tag verification** | `verify v0.1.0` reads the tag tree, not the working tree, so `main` may move while the release stays fixed. |
| **Offline test suite** | Green on Windows (development) and on Linux (CI). |
| **Project rename** | `jev-test` → `jev-testbench`, decided by the owner and applied in P5-E (`PROJECT_RENAME: OWNER_APPROVED`). The frozen `v0.1.0` tree is unchanged and keeps the name it was published under. See [`REPOSITORY_METADATA_PROPOSAL.md`](REPOSITORY_METADATA_PROPOSAL.md). |

**Also already true, and worth stating:** no API call has been made since the freeze. The P5-A, P5-B,
P5-C, P5-C1, P5-D and P5-E stages produced presentation, infrastructure and process documentation
only. The rename is an owner decision that has been taken; it is not a gate that passed, and it is
listed here because this file's other sections would otherwise still imply it was open.

---

## 2. Human editorial gate — CLOSED

The owner completed the required full human read. Publication Closure therefore treats the bilingual
blog as approved and frozen except for hard defects:

```text
CHINESE_HUMAN_EDITORIAL_APPROVED
ENGLISH_HUMAN_EDITORIAL_APPROVED
BILINGUAL_BLOG_HUMAN_APPROVED
BLOG_EDITING_CLOSED
```

The final English correction commit is `a2306ac7cb0c18bf9e9dd856633d50bb693e267f`.
The blog bodies are not reopened for wording preference, style work, audit metrics or AI rewriting.

---
## 3. Owner decisions required

The editorial decisions above are already closed. The following publication actions remain explicit owner decisions.

- [ ] **Make the GitHub repository public?** — Currently `PRIVATE`. This is the decision with the
      largest blast radius: it is not reversible in the sense that matters, because a public
      repository can be cloned, indexed and mirrored.
- [ ] **Promote `0.1.1.dev0` to `0.1.1`, or keep the development version?** — Publication Closure must decide this before any release action.
- [ ] **Create a new `v0.1.1` tag?** — If created, it must represent publication/presentation closure, not new Jev scientific evidence.
- [ ] **Create a GitHub Release for `v0.1.1`?** — The existing [`GITHUB_RELEASE_DRAFT.md`](GITHUB_RELEASE_DRAFT.md) is the earlier `v0.1.0` draft and is retained as decision history, not as an instruction to publish the historical tag now.
- [ ] **Approve the repository description and topics?** — Proposal in
      [`REPOSITORY_METADATA_PROPOSAL.md`](REPOSITORY_METADATA_PROPOSAL.md). Setting them is a GitHub
      side change, not a repository change.
- [ ] **Choose an external blog venue, if any?** — Comparison in
      [`BLOG_PUBLICATION_OPTIONS.md`](BLOG_PUBLICATION_OPTIONS.md). "Repository only" is a complete
      answer.
- [ ] **Send the TypeSafe V1 documentation feedback?** — Draft in
      [`TYPESAFE_FEEDBACK_DRAFT.md`](TYPESAFE_FEEDBACK_DRAFT.md). Every item is marked
      `NEEDS_FRESH_RECHECK_BEFORE_SEND` and nothing has been sent.

---

## PC0–PC2 Publication Closure checkpoint

| Item | Live state |
|---|---|
| Repository | `PRIVATE`; default branch `main` |
| Pre-promotion `main` | `ab9013d69f0fbd3a23352571d68e0a940df23492` |
| Approved branch | `docs/p5f-english-realignment` at `a2306ac7cb0c18bf9e9dd856633d50bb693e267f` |
| Promotion | fast-forward only; no merge commit, rebase, force push or history rewrite |
| Promoted `main` | `a2306ac7cb0c18bf9e9dd856633d50bb693e267f` before this checklist-only readiness repair |
| Evidence tag | `v0.1.0` dereferences to `37ef2e425d5e9e534f856a7243be848ff17f0cbb` |
| Core canonical log | 42 records; SHA-256 `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| P3 canonical log | 12 records; SHA-256 `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` |
| GitHub Releases | none |
| Development version | `0.1.1.dev0` |
| GitHub metadata | existing description; empty homepage; empty topics; no publication metadata applied |
| `AGENTS.md` | absent; `CLAUDE.md` exists instead |

Security/public-history reconciliation reused the earlier full-history/object-database audit through
`ab9013d` and separately scanned the nine documentation files added between that point and
`a2306ac`; no new credential-like token, auth header, cookie, machine-specific absolute path,
private IPv4 address or email address was found. No destructive history rewrite is required.

The Actions workflow is read-only (`contents: read`), uses no repository secret, empties
`TYPESAFE_API_KEY`, avoids `pull_request_target`, pins third-party Actions by commit SHA, and runs
the full offline test/build/evidence-verification path. `uv.lock` is committed and all external
dependency sources resolve through PyPI with artifact hashes. The GitHub connector could not read
Dependabot alert data, so this audit does not claim that every dependency is free of every known
vulnerability.

`main` currently has no branch protection and no repository ruleset. That is an operational
hardening choice for the public phase, not a content or evidence blocker.

No secret/privacy blocker, evidence drift, licensing blocker, broken-link blocker, CI blocker or
history-rewrite requirement was found.

```text
PUBLICATION_BASELINE_RECONCILED
PUBLICATION_MAIN_PROMOTED
PUBLIC_READINESS_AUDIT_PASS
```

These states authorize the owner-decision stage only. They do not authorize public visibility, a
new tag, a GitHub Release, metadata changes, external publication or TypeSafe contact.

---
## 4. Optional, and explicitly not blockers

Listed so that they are visible as choices rather than forgotten. **Nothing here is required, and
none of it should be treated as gating.**

- [ ] A social preview image for the repository (deliberately not generated; see below).
- [ ] GitHub Pages for the blog, if option B or C in the venue comparison is chosen.
- [ ] A DOI via Zenodo, if the release should be citable by DOI rather than by tag.
- [ ] `CITATION.cff` review — it exists and points at the tag; a DOI would change it.

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

**Repository state right now: `PRIVATE` · approved blog work promoted to `main` · no `v0.1.1` tag · no GitHub Release · no external blog publication · no TypeSafe message sent.**
