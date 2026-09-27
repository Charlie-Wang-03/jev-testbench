# GitHub Release draft — `v0.1.0`

**Status: DRAFT. Not published.** No GitHub Release exists for this repository. This file is the
text a Release would carry if the owner decides to create one, so that the decision can be made
against the actual wording rather than against a description of it.

**If published, it must be attached to the existing annotated tag `v0.1.0`** — not to a new tag, and
not to `main`. The release is the tree that tag points at.

---

## Draft body

> ### `jev-test` v0.1.0 — evidence freeze
>
> The first frozen, citable evidence release from this repository: a local evaluation bench for
> TypeSafe's Jev 1.13.0, and the results of using it honestly.
>
> **What is in it**
>
> - **42 core measurement records** (`results/usage.jsonl`) from ten registered experiments, each
>   one a real API call written by the recorder whether it succeeded or raised.
> - **12 preregistered P3 records** (`results/p3_boundary_locus/usage.jsonl`) from a 2×2 design
>   committed before the first request went out.
> - Every token count is the `usage` value the API returned. Nothing is estimated.
> - An offline verifier that re-hashes the whole frozen set from disk, with no network and no API key.
>
> **The result, stated plainly**
>
> ```
> NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
> ```
>
> This release contains no discovery about Jev. Across 42 core records and the official behaviours
> audited, nothing here is both new relative to TypeSafe's published material and supported by this
> repository's own data. Every large local effect either restates a documented behaviour or is an
> artifact of this repository's own Python-side policy. Seven triage candidates were retired,
> including the two with the largest local effect sizes — killed on prior art, not on weak data.
>
> **The one experiment that was run**
>
> ```
> P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
> ```
>
> A preregistered 2×2 crossed `instructions` and `criteria` on one payload, three repeats per arm.
> The original effect replicated — the `N` and `B` endpoints came back 0.56 apart — but the two
> single-field arms landed 0.05 apart, below the pre-registered separation, so the effect could not
> be attributed to either field alone. The effect is real on this payload; its *attribution* is what
> the design could not establish.
>
> **What it is not**
>
> No general accuracy claim. No calibration validation, in either direction. No latency benchmark. No
> universal batching ratio. No determinism verdict. No production safety certification. No claim
> about NAS. The full list, with reasons, is in
> [§ 7 of the freeze document](https://github.com/Charlie-Wang-03/jev-test/blob/v0.1.0/docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md).
>
> **The method is the contribution.** Every claim is labelled as an official claim, a local
> measurement, a derived calculation or a limitation. P3's design, thresholds and stopping rule were
> frozen before the first call. When an analyzer defect was found afterwards it was disclosed in the
> commit that recorded the measurements, repaired later without a new call, and the repair was shown
> to move no measurement, no threshold and no verdict. The erroneous rendering is still in Git
> history on purpose.
>
> **Reproducing it**
>
> ```console
> git clone https://github.com/Charlie-Wang-03/jev-test.git
> cd jev-test
> git checkout v0.1.0
> uv sync --locked
> uv run pytest
> uv run python -m jev_lab.evidence_freeze verify v0.1.0
> ```
>
> Offline, no key, no network. The verifier recomputes every SHA-256 in the manifest, re-counts both
> logs, and re-checks the registry, license, version and P3-verdict invariants.
>
> **License:** MIT, covering the code, both canonical logs and the derived reports.
>
> Cite the tag, not `main`. Citation metadata is in `CITATION.cff`.

---

## What this draft deliberately does not say

The claim contract that governs everything public about this release
([`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md)) rules out several phrasings
that a release announcement would normally reach for. Each was left out on purpose:

| Not said | Why |
|---|---|
| "major breakthrough", "novel findings" | There are none. The state string says so. |
| "production ready" | Every handler is inert; `ACTUAL_HANDLER_EXECUTION_UNTESTED`. |
| "benchmark", "leaderboard" | There is no ground truth anywhere in this bench. |
| "13× cheaper", any batching multiplier | The local ratio belongs to one payload and is not commensurable with the vendor's published figures. |
| "validated calibration" | Two confidence cases. Not a validation, in either direction. |
| "deterministic" / "non-deterministic" | A handful of repeats on two payloads is not a verdict either way. |

## Owner actions before this could be published

1. Decide whether a GitHub Release should exist at all. The tag alone is already the artifact; the
   release notes argue that no Release, DOI or PyPI publication was part of the freeze.
2. If yes, publish it **against the existing tag** `v0.1.0`, using the body above.
3. Do not attach it to a new tag, and do not create a tag on `main`.

**No part of this file is published by P5-C.**
