# Open-source license decision

**Status:** `LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC`

**This repository has no open-source license.** That is a deliberate stopping point, not an
oversight. Choosing a license is the copyright holder's decision, and no tooling or agent should
make it on their behalf.

Until a license is chosen, default copyright applies: **all rights reserved**. The repository can
be read, but it is not legally reusable, and it must not be published under an open-source
description. See [Before publishing](#before-publishing) below.

---

## What needs deciding

| | |
|---|---|
| Decision required | Which open-source license, if any |
| Decided by | The repository owner |
| Blocks | Publishing the repository as open source; accepting outside contributions |
| Does *not* block | The repository remaining private; internal use; local experiments |
| Deliverable when decided | A `LICENSE` file at the repository root, plus a `license` field and classifier in `pyproject.toml` |

## Candidates

Two are worth considering for a project of this shape.

### MIT

**Permissive, short, and the most widely understood.** Anyone may use, modify, and redistribute the
code, including in closed-source products, provided the copyright notice and permission notice are
preserved.

- **Permissiveness:** maximal. No conditions beyond attribution.
- **Patent grant:** **none.** MIT is silent on patents. A contributor who holds a patent reading on
  the code has not explicitly licensed it. In practice this rarely matters for a measurement bench;
  it matters more for a library that implements an algorithm.
- **Attribution:** the license text must be included in copies or substantial portions.
- **Compatibility:** compatible with essentially everything, including Apache-2.0 and GPLv3
  projects consuming it.
- **Best when:** you want the least friction for anyone who wants to use or adapt the code, and you
  are not worried about patent exposure.

### Apache-2.0

**Permissive, longer, and explicit about patents and trademarks.**

- **Permissiveness:** high — same practical freedoms as MIT for most users.
- **Patent grant:** **explicit.** Section 3 grants a patent license from contributors, and
  terminates it for anyone who sues over the software. This is the substantive difference from MIT.
- **Attribution:** requires preserving notices, and requires stating **significant changes** when
  you modify files.
- **Compatibility:** compatible with GPLv3; **not** compatible with GPLv2 (the patent clause adds
  restrictions GPLv2 forbids).
- **Best when:** contributors or downstream users may have patents in the area, or you want the
  explicit patent grant and the clearer contribution terms.

### Other options, briefly

- **BSD-2/3-Clause** — equivalent in spirit to MIT; the 3-clause version adds a non-endorsement
  clause. No patent grant.
- **MPL-2.0** — file-level copyleft. Modifications to covered files must be shared, but you may
  combine with closed code. Reasonable middle ground; more obligation than this project needs.
- **GPL family** — strong copyleft. Would prevent this code from being used in closed products.
  Hard to justify for a measurement harness whose value is in its *evidence* rather than its code.
- **No license / all rights reserved** — the current state. Readable, not reusable. Defensible if
  the intent is to publish the findings as a writeup rather than to run an open-source project.

## Recommendation

> **Recommended: MIT.**
> **Alternative: Apache-2.0** if an explicit patent grant matters to you.

**Why MIT for this repository.** The value here is the *evidence and its discipline*, not the code.
The code is a harness: it exists so the measurements can be inspected and re-run, and the most
useful thing a reader can do with it is copy the pattern into their own bench. MIT maximises that
with the fewest conditions attached.

**Why you might prefer Apache-2.0 instead.** If you expect this to be used inside companies where
patent exposure is a live question, or you want the explicit contribution terms and the
"state significant changes" obligation, Apache-2.0 is the better choice. It costs the reader
almost nothing in practice.

Either is defensible. The difference is narrow, and it is a judgement about the audience rather
than about the code.

### A note on the evidence files

The two canonical logs and the derived reports are **data**, not code. A code license covers them
by default when they sit in a licensed repository, but if you intend to reuse the measurements
elsewhere — in a blog post, a paper, a dataset — it is worth stating explicitly. A common shape is
code under MIT and data/findings under **CC BY 4.0**, which requires attribution and nothing else.
That is optional; it is mentioned here so the choice is visible rather than accidental.

## Before publishing

Do not describe this repository as open source, and do not publish it under an open-source
description, until:

1. The license is chosen by the copyright holder.
2. A `LICENSE` file exists at the repository root with the full license text.
3. `pyproject.toml` carries a matching `license` field and the corresponding Trove classifier.
4. The [README](../README.md) license section is updated to name the chosen license.

Until all four are done, the status string is
**`LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC`**, and the repository must stay private.

## Why this is a gate and not a default

Adding a license is easy. Removing one is not: a license, once granted, cannot be un-granted for
copies already distributed. It is also the one decision in this repository that is genuinely the
owner's rather than a technical judgement — it allocates rights, and rights allocation is not a
thing to infer from context.

So this repository does the only honest thing available: it records the options, records a
recommendation, and **waits**.
