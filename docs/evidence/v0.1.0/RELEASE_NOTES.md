# Release notes — `v0.1.0`

**Tag:** `v0.1.0` · **Version:** `0.1.0` · **Date:** 2026-09-27
**Freeze document:** [`PUBLIC_EVIDENCE_FREEZE.md`](PUBLIC_EVIDENCE_FREEZE.md) · **Manifest:**
[`evidence-manifest.json`](evidence-manifest.json) · **Errata:** [`docs/ERRATA.md`](../../ERRATA.md)

This is the first evidence freeze. It bundles the P0–P3.6 research and engineering output into one
versioned set so that it can be cited without pointing at a moving branch.

---

## What this release contains

- **Two canonical measurement logs**, published in full and never rewritten: 42 core records
  (`results/usage.jsonl`) and 12 P3 records (`results/p3_boundary_locus/usage.jsonl`). Every token
  count in them is the `usage` value the API returned.
- **The complete audit chain** from P1 to P3: an official-claims audit against a dated snapshot of
  TypeSafe's documentation, a novelty triage, and a preregistered two-field experiment with its
  result.
- **A provenance record** that distinguishes measurement commits from analysis commits from
  documentation commits, and shows that a post-run analyzer repair changed no measurement and no
  verdict.
- **An errata registry** for two historical defects that are deliberately not retroactively
  rewritten — one a miscount in the P1 audit, one a repaired analyzer that could not represent its
  own outcome pair.
- **An offline verifier** (`uv run python -m jev_lab.evidence_freeze verify`) that re-hashes every
  frozen artifact and re-checks the release's structural invariants from disk, with no network.
- **The measurement bench itself** and its offline test suite, which needs no API key.

---

## Key result state

```
NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
```

**This release contains no discovery about Jev.** Across 42 core records and the official behaviours
audited, there is no finding here that is both novel relative to TypeSafe's public material and
supported by this repository's own data. Every large local effect either restates an officially
documented behaviour or is an artifact of this repository's own Python-side policy.

The one question that cleared triage was tested and came back null:

```
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
```

**The original instruction-precision effect could not be attributed to `instructions` or `criteria`
alone under the preregistered one-payload 2×2 design.** Both single-field arms moved most of the way
to the explicit baseline and landed 0.05 apart against a 0.56 end-to-end gap, so the preregistered
separation rule fired. The effect is real on this payload; its *attribution* is what the design was
unable to establish.

Seven triage candidates were retired, **including the two with the largest local effect sizes** —
killed on prior art rather than on this repository's own data. Nothing was killed for being
unflattering and nothing was preserved for being interesting.

---

## Why release it anyway

A null result is only worth publishing alongside the method that produced it, and the method is the
contribution here.

- **Independent evaluation, with the negatives intact.** The repository's value is not that it found
  something; it is that a finding was pursued properly, did not survive, and is still in the record.
  Retired candidates are documented with the strongest counter-explanation for each rather than
  quietly dropped.
- **Preregistration as a working practice, not a slogan.** P3's design, payload, thresholds and
  decision rule were committed before the first request. When an analyzer defect was found
  afterwards, it was disclosed in the commit that recorded the measurements, repaired later without
  a new call, and the repair was shown mechanically to move no measurement, no threshold and no
  verdict.
- **Agent-control patterns that are actually exercised.** A fail-closed credential path, an
  append-only recorder that writes a record whether the call succeeds or raises, inert handlers, and
  a boundary between semantic judgment and arithmetic that keeps numbers in Python. Handlers are
  inert by design and no allowed route was observed reaching one under a real answer
  (`ACTUAL_HANDLER_EXECUTION_UNTESTED`) — the limit is stated, not glossed.
- **Evidence that a third party can check.** Every claim is labelled as an official claim, a local
  measurement, a derived calculation or a limitation; every number is recomputed from a committed
  log; and one command re-hashes the whole frozen set offline. A reader does not have to trust the
  prose — they can run the verifier.
- **It is cheap to disagree with.** The logs, the design and the thresholds are all published, and
  re-running any of it costs twelve calls. The intended use of this release is that someone checks
  it, not that someone believes it.

---

## What this release does not include

- **No new measurement.** P4 made no API call at all. Both canonical logs are byte-identical to the
  ones already published, and both SHA-256 values in the freeze document are unchanged.
- **No DOI, no GitHub Release, no PyPI publication.** The tag is the artifact.
- **No blog post.** The prose that will eventually cite this release is a separate stage; this
  release only fixes what that prose may say, in
  [`BLOG_CLAIM_CONTRACT.md`](BLOG_CLAIM_CONTRACT.md).
- **No change in repository visibility.** "Public evidence" here means public-*ready* evidence
  semantics — a citable, verifiable, versioned set — not a change to who can see the repository.

---

## Known limitations

The binding ones, in brief. The full list, with reasons, is
[§ 7 of the freeze document](PUBLIC_EVIDENCE_FREEZE.md#7-claims-explicitly-not-established).

- **No general accuracy claim.** There is no ground truth anywhere in this bench.
- **No calibration validation, in either direction.** Two confidence cases is not a validation.
- **No model latency benchmark.** Latency is a superset window, recorded not benchmarked.
- **No universal batching ratio.** `4.2647×` belongs to one payload with one shared state.
- **No determinism verdict** — in either direction.
- **No broad hallucination benchmark.** Only schema conformance on benign payloads.
- **No production safety certification.** Every handler is inert.
- **No general instruction-vs-criteria field preference.** One payload, n = 3 per arm, and a null.
- **No NAS claim.** Nothing here tests NAS.
- **Small n throughout.** P3's arms are three repeats each: enough for a median and a range, not
  enough for an interval estimate, and none is reported.
- **One payload, one account, one session, one model version** for the headline P3 numbers.
- **`retry_count` is permanently `null` in both logs** and must never be read as "no retries
  happened"; `transport_attempt_count` is the live field and is itself unrecorded on 7 core records.
- **Cost is a local estimate.** TypeSafe Console billing is authoritative.
- **The official-source comparison is against a dated snapshot** (accessed 2026-09-22), not against
  TypeSafe's documentation as it stands today.

---

## Verifying this release

Offline, no API key, no network:

```console
git checkout v0.1.0
uv sync --locked
uv run pytest
uv run python -m jev_lab.evidence_freeze verify
```

The verifier recomputes every SHA-256 in the freeze manifest, re-counts both logs, and re-checks the
registry, license, version and P3-verdict invariants. It exits non-zero on any mismatch, which is
also how CI prevents a later change to the logs or the audits from silently invalidating this freeze.

**The offline suite contains 1,091 tests at this revision**, all passing, with sockets blocked
outright, measured on the committed tree. That number is recorded here and nowhere else on purpose:
it belongs to one immutable revision, and a test count carried in a README is a number that goes
stale the next time someone adds a test. Everything else in this repository says "the full offline
suite" and means it.

The qualifier is not decoration. `test_docs_consistency` parametrizes its link check over
`git ls-files "*.md"`, so a markdown file that is written but not yet tracked contributes one fewer
test. Measured before this release's own documents were staged, the suite collected 1,086; the same
tree, measured after staging, collects 1,091. Five documents, five tests.

**Citation metadata:** [`CITATION.cff`](../../../CITATION.cff). Cite the tag, not `main`.

**License:** MIT, covering the code, both canonical logs and the derived reports.
