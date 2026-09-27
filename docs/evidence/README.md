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

Offline, from a clone of the tagged tree. No API key, no network:

```console
git checkout v0.1.0
uv sync --locked
uv run python -m jev_lab.evidence_freeze verify
```

The command reads the manifest, recomputes the SHA-256 of every file it lists, re-counts both
canonical logs from disk, and re-checks the release's structural invariants — the experiment registry
has no unrun design, the license is present, the project version matches, the P3 verdict is
unchanged. Any mismatch is a non-zero exit.

CI runs the same command on every push, so a later change to a canonical log, an audit or the
preregistration fails the build until a new versioned freeze is created for it. That is the mechanism
that keeps this directory from quietly going stale.
