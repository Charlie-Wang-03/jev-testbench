# Publication checklist

**Status: PUBLICATION EXECUTED.** PC4 completed: the repository is public, `v0.1.1` and its GitHub Release exist, and the repository-hosted bilingual blog is live.

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
## 3. Owner publication decisions — APPROVED

The owner approved the recommended PC3 combination, and the approved GitHub-side publication actions have now been executed.

- [x] **Make the GitHub repository public.** — Executed.
- [x] **Promote `0.1.1.dev0` to `0.1.1`.** — Executed in the release commit; this is publication/presentation closure, not new Jev evidence.
- [x] **Create `v0.1.1`.** — Executed; annotated tag points at `22a211517b5133f1e8c67965f2a44054c342d8e5`.
- [x] **Create a GitHub Release for `v0.1.1`.** — Executed: `v0.1.1 — Publication Closure`.
- [x] **Apply repository metadata; leave homepage empty.** — Executed. The owner subsequently requested a bilingual About description; that follow-up remains manual because the GitHub integration lacks repository-administration write permission.
- [x] **First publication surface: repository-hosted bilingual blog only.** — No external platform publication in this closure.
- [x] **TypeSafe contact: `NO CONTACT`.** — The documentation-feedback draft remains unsent.

---

## PC0–PC2 Publication Closure checkpoint

| Item | Live state |
|---|---|
| Repository at PC0–PC2 checkpoint | `PRIVATE`; default branch `main` |
| Pre-promotion `main` | `ab9013d69f0fbd3a23352571d68e0a940df23492` |
| Approved branch | `docs/p5f-english-realignment` at `a2306ac7cb0c18bf9e9dd856633d50bb693e267f` |
| Promotion | fast-forward only; no merge commit, rebase, force push or history rewrite |
| Promoted `main` | `a2306ac7cb0c18bf9e9dd856633d50bb693e267f` before this checklist-only readiness repair |
| Evidence tag | `v0.1.0` dereferences to `37ef2e425d5e9e534f856a7243be848ff17f0cbb` |
| Core canonical log | 42 records; SHA-256 `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| P3 canonical log | 12 records; SHA-256 `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` |
| GitHub Releases at PC0–PC2 checkpoint | none |
| Release version on `main` | `0.1.1` |
| GitHub metadata at PC0–PC2 checkpoint | existing description; empty homepage; empty topics; no publication metadata applied |
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

The owner subsequently approved the recommended PC3 combination. PC4 executed the `v0.1.1` tag,
GitHub Release, approved metadata and `PRIVATE → PUBLIC` transition after the exact release commit
passed all gates. External publication and TypeSafe contact remain explicitly out of scope.

---
## 4. Optional, and explicitly not blockers

Listed so that they are visible as choices rather than forgotten. **Nothing here is required, and
none of it should be treated as gating.**

- [ ] A social preview image for the repository (deliberately not generated; see below).
- [ ] GitHub Pages for the blog, if option B or C in the venue comparison is chosen.
- [ ] A DOI via Zenodo, if the release should be citable by DOI rather than by tag.
- [x] `CITATION.cff` review — `main` now identifies `v0.1.1`; the immutable `v0.1.0` tag retains its historical citation metadata.

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

**Repository state right now: `PUBLIC` · `v0.1.1` tag and GitHub Release live · repository-hosted bilingual blog live · no external blog publication · no TypeSafe message sent.**
