# Open-source license decision

**Status:** `LICENSE_DECISION_RESOLVED_MIT`

**Decision: MIT.** The copyright holder chose MIT for this repository. The full license text is in
[`LICENSE`](../LICENSE) at the repository root, and `pyproject.toml` carries the matching SPDX
expression. The repository is licensed under MIT as of 2026.

The gate this file used to describe — **`LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC`** — is closed.
That string is retained here only so a reader who meets it in an older commit or a stale link can
find where it went.

---

## What was decided

| | |
|---|---|
| Decision | MIT |
| Decided by | The repository owner (Yichuan Wang) |
| Date recorded | 2026-09-23 |
| Deliverable | [`LICENSE`](../LICENSE) at the repository root, plus `license = "MIT"` and `license-files = ["LICENSE"]` in `pyproject.toml` |
| Supersedes | `LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC`, the state in which no license had been chosen |

## What MIT means here

- **Permissive, short, and the most widely understood.** Anyone may use, modify, and redistribute
  the code, including in closed-source products, provided the copyright notice and permission
  notice are preserved.
- **Permissiveness:** maximal. No conditions beyond attribution.
- **Patent grant:** **none.** MIT is silent on patents. This was weighed and accepted: the value of
  this repository is in its *evidence and its discipline* rather than in a patentable algorithm, so
  the explicit patent grant Apache-2.0 adds was judged not to change what a reader can do with it.
- **Attribution:** the license text must be included in copies or substantial portions.
- **Compatibility:** compatible with essentially everything, including Apache-2.0 and GPLv3
  projects consuming it.

### The alternative that was considered

**Apache-2.0** — permissive, longer, and explicit about patents and trademarks. Its substantive
difference from MIT is Section 3's patent grant, which terminates for anyone who sues over the
software; it also requires stating significant changes when you modify files. It is **not**
compatible with GPLv2, which the patent clause forbids.

It was the recommended alternative and was not chosen. The reasoning is recorded rather than
compressed to a preference: Apache-2.0 buys protection against a contributor patent reading on the
code, and the expected audience here is someone copying a measurement pattern into their own bench,
for whom the licence that adds the fewest obligations is the one that gets read.

### Options that were not chosen, briefly

- **BSD-2/3-Clause** — equivalent in spirit to MIT; the 3-clause version adds a non-endorsement
  clause. No patent grant.
- **MPL-2.0** — file-level copyleft. Reasonable middle ground; more obligation than this project
  needs.
- **GPL family** — strong copyleft. Would prevent this code from being used in closed products.
  Hard to justify for a measurement harness whose value is in its *evidence* rather than its code.

## A note on the evidence files

The two canonical logs and the derived reports are **data**, not code. MIT covers them by default
now that they sit in a licensed repository, and **no separate data license is applied** — one
license, stated once, is the decision here rather than a code/data split.

If you reuse the measurements elsewhere — in a blog post, a paper, a dataset — attribution is the
only condition MIT imposes, and it is the same condition the repository already asks for in
[`docs/EVIDENCE_PROVENANCE.md`](EVIDENCE_PROVENANCE.md).

## What this does not change

- **The repository's visibility is not set by this file.** The license is a terms decision; whether
  the repository is public is a separate owner decision.
- **No rights are granted retroactively that were not granted.** The canonical logs were published
  in this repository and remain byte-identical; MIT applies to them as part of the repository.
- **Nothing about the measurements or their interpretation changes.** The license settles what a
  reader may *do* with the material, not what the material *says*.

## Why this was a gate and not a default

Adding a license is easy. Removing one is not: a license, once granted, cannot be un-granted for
copies already distributed. It is also the one decision in this repository that is genuinely the
owner's rather than a technical judgement — it allocates rights, and rights allocation is not a
thing to infer from context.

So the repository recorded the options, recorded a recommendation, and waited for the owner. That
wait is now over, and the outcome is recorded above rather than inferred from the presence of a
`LICENSE` file.
