# Frozen evidence releases

Each directory here is one **frozen, versioned** evidence release. A directory is created when a
release is tagged, and it is **never edited afterwards**.

| Version | Tag | Frozen | Contents |
|---|---|---|---|
| [`v0.1.0/`](v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) | `v0.1.0` | 2026-09-27 | The P0–P3.6 evidence freeze. |

---

## The rule: a frozen directory is immutable

**Once a version is tagged, nothing inside `docs/evidence/<version>/` changes.** Not a hash, not a
typo, not a sentence. The
[manifest](v0.1.0/evidence-manifest.json) is bound to the Git tree by the tag; editing a file here
after the tag exists would make the manifest describe something other than what a reader checks out
from that tag, and would break every citation that points at it.

**New evidence means a new version.** A new API experiment, a new scientific claim, a change to a
canonical log, or a corrected understanding all require a new directory — `docs/evidence/v0.2.0/`,
tag `v0.2.0` — that states what it supersedes and what it leaves standing. It never means editing
`v0.1.0/`.

**A correction is not an edit.** If something in a frozen release turns out to be wrong, it is
recorded in [`docs/ERRATA.md`](../ERRATA.md) — which states the incorrect text, the corrected value,
how the corrected value was derived, and whether any conclusion moves — and the frozen text stays as
written. A reader must always be able to tell which numbers in a historical document have been
touched. That property is worth more than a tidier file.

> **Errata are new versions, not edits.** The registry is append-only for the same reason the logs
> are.

---

## What is in a version directory

| File | What it is |
|---|---|
| [`PUBLIC_EVIDENCE_FREEZE.md`](v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) | The human-readable freeze: scope, canonical measurements, supported conclusions, negative results, explicit non-claims, provenance, citation. |
| [`evidence-manifest.json`](v0.1.0/evidence-manifest.json) | The machine-readable freeze: every frozen artifact with its SHA-256, the canonical record counts, the historical commit lineage, the registry state and the errata. |
| [`RELEASE_NOTES.md`](v0.1.0/RELEASE_NOTES.md) | What the release contains, its key result state, and its known limitations. |
| [`BLOG_CLAIM_CONTRACT.md`](v0.1.0/BLOG_CLAIM_CONTRACT.md) | The guardrail for anyone writing publicly about this release: what may be stated flatly, what may be stated only with its scope, and what may not be stated at all. |

---

## Verifying a freeze

Offline, from any checkout. No API key, no network:

```console
uv sync --locked
uv run python -m jev_lab.evidence_freeze verify v0.1.0
```

The command reads `v0.1.0`'s manifest **out of the `v0.1.0` Git tree**, recomputes the SHA-256 of
every file it lists at `v0.1.0:<path>`, re-counts both canonical logs, and re-checks the release's
structural invariants — the experiment registry has no unrun design, the license is present, the
project version matches the P3 verdict is unchanged. Any mismatch is a non-zero exit.

**You do not have to check the tag out first, and you do not have to be on it.** A release is the
tree its tag points at, so the verification goes to the tag and ignores the branch you are on. That
is what lets this directory be immutable *and* lets `main` keep moving — two properties that look
like they conflict until they are separated.

CI runs the same command on every push, against the tag. So a change to a canonical log, an audit or
the preregistration *inside the release* fails the build, while a README or a guide may be reworded
on `main` without a new release. The fix for a red run is never to edit `docs/evidence/v0.1.0/` to
match, and never to move the tag.

---

## Two questions, and why they are two commands

| Command | Question it answers | Expected after the release |
|---|---|---|
| `verify v0.1.0` | Is the published release still exactly what was published? | **PASS** |
| `verify-current` | Does this working tree still equal the release tree? | **Non-zero**, once anything has been reworded |

`verify-current` exiting non-zero is not a defect and is not a reason to change anything. It is the
honest answer to a different question, and it is useful exactly once: when a failure names a
canonical log, an audit, the preregistration or `ERRATA.md`, evidence has drifted on a branch it
should not have drifted on. When it names a README or an index, it has told you what changed and
there is nothing to fix.

Keeping the two apart matters more than it sounds. One command that checked the current tree against
a frozen manifest would make "someone reworded the docs" and "someone edited the evidence" produce
the identical red build — so the second, which is the one worth being told about, would be buried
under the first.

---

## What may change after a release

| Layer | After the release |
|---|---|
| **Presentation** — READMEs, this index, the guides, the blog | May be reworded or extended. No new release needed. |
| **Evidence** — the canonical logs, the audits, the preregistration, `ERRATA.md`, a release's own documents | May not change. A new version directory supersedes it. |

The split is not a rule anyone has to remember, because it is enforced: the first row is hashed as
`public_documentation`, the second as `evidence_documents` and `canonical_measurements`, and
`verify v0.1.0` recomputes both against the tag. This page is itself in the second row — the copy in
the release is frozen, and the copy you are reading may be reworded, which is what the verifier was
taught to tell apart.
