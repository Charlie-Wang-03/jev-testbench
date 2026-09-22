# Evidence provenance

The complete lineage of the measurements in this repository, from the original freeze to the P3
replication. This file exists because the interesting question about a measurement is not only
*what does it say* but *what happened to it afterwards*.

---

## 1. The lineage

```
e20fad5  Freeze local evaluation of TypeSafe Jev 1.13.0          MEASUREMENT   P0
   │                                                             → results/usage.jsonl (42 records)
   ├─ e9d54ca  Fix derived report integrity for confidence gating ANALYSIS
   └─ 77357d9  Close residual derived-report integrity gaps       ANALYSIS
   │
ec04cb6  Audit TypeSafe claims against frozen Jev evidence       ANALYSIS      P1
   └─ 3125281  Repair P1 audit HEAD provenance                   DOCUMENTATION
   │
373e259  Triage Jev-specific findings for replication            ANALYSIS      P2
   │
db7d06f  Preregister P3 boundary locus experiment                PREREGISTRATION  P3
   ├─ c0fc9cc  Record P3 boundary locus measurements             MEASUREMENT   P3
   └─ bdcb637  Repair P3 analyzer against frozen preregistration ANALYSIS      P3  ← final HEAD
```

Commit types, distinguished deliberately:

| Type | What it may change | What it may never change |
|---|---|---|
| **MEASUREMENT** | Adds records to a canonical log. | Anything already in a log. |
| **PREREGISTRATION** | Adds a design, thresholds and statistics *before* the first request. | Anything after a result exists. |
| **ANALYSIS** | Code that reads a log; prose that reports it. | The log itself. |
| **DOCUMENTATION** | Prose, provenance, navigation. | Any measurement or conclusion. |

A commit type is not metadata attached to a commit — it is a claim about what the diff does, and
each one below is checkable with `git show`.

---

## 2. The core freeze — `e20fad5`

The 42-record core evaluation. That commit added the canonical log and the bench that produced it.

| | |
|---|---|
| Canonical log | [`results/usage.jsonl`](../results/usage.jsonl) |
| Records | 42 |
| SHA-256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| Resolved model | `jev-1.13.0` on 42 of 42 records |
| Status | `ok` on 42 of 42 |

`FREEZE.md` is scoped to **this** freeze and remains a historical pointer to it. It is not a
description of the whole repository, which now extends past P0.

### The two analysis commits that followed

`e9d54ca` and `77357d9` changed the code that *renders* the derived report — integrity fixes in the
confidence-gating presentation. **No record was added, changed or removed by either**, which is
checkable: the log's SHA-256 is identical at `e20fad5` and at every commit after it.

The log's integrity is a separate question from the reporter's, and the lineage keeps them
separate on purpose.

---

## 3. P1 — official claims audit (`ec04cb6`, `3125281`)

**No API call was made in P1.** It is a purely analytical pass over the frozen 42 records and
TypeSafe's published documentation. Verdict: `P1_OFFICIAL_LOCAL_AUDIT_PASS`.

It audited every official claim it could locate, family by family (identity, output semantics,
calibration, batching, cost, latency, type safety, state handling, instruction precision,
repeatability, workflow), and assigned each a relationship label — including `ND`, used when local
records are not commensurable with a claim in either direction.

`3125281` then repaired the audit's own HEAD provenance: the audit had recorded a commit reference
that no longer described the file's own revision. That is a documentation fix about *where the
artifact lives*, not about what it found. The findings were not edited.

---

## 4. P2 — novelty triage (`373e259`)

**No API call was made in P2.** It triaged every candidate finding against one standard: *is this
both novel relative to TypeSafe's public material, and supported by our own data?*

Seven candidates were retired — including the two with the largest local effect sizes, killed on
prior art rather than on this repository's own data. One survived and became P3's question. Verdict:
`P2_TRIAGE_PASS`, scientific state `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`.

The distinction in that state string matters: it is the *first* of two "no finding" states. The
second would have forbidden further API spend. This one did not, because exactly one question still
cleared the novelty-and-falsifiability bar.

---

## 5. P3 — boundary locus (`db7d06f` → `c0fc9cc` → `bdcb637`)

The three-commit chain is the clearest example of the discipline this repository is trying to
demonstrate, and it is worth reading in order.

### Commit A — `db7d06f`: preregister

Froze the design, the payload, the thresholds, the decision rule, and the first version of the
analyzer — **before the first request was sent**. The preregistration document at this commit is
still byte-identical at HEAD.

### Commit B — `c0fc9cc`: record the measurements

Added the twelve measurements — and disclosed, **after the fact**, a defect in the analyzer that
Commit A had frozen. The analysis those twelve calls produced is preserved unedited at this commit:

```console
git show c0fc9cc:docs/audits/P3_BOUNDARY_LOCUS_RESULT.md    # the analysis as first recorded
git show c0fc9cc:src/jev_lab/p3_boundary_locus.py           # the analyzer that produced it
```

### Commit C — `bdcb637`: repair the analyzer

Corrected the analyzer and re-rendered the result document **from the unchanged log**.

**The defect.** In `analyze()`, GO-1 and GO-2 — two separate conditions in the preregistration —
were evaluated as a single conjunction, and both flags were read off that one result. The pair
`(GO-1 PASS, GO-2 FAIL)` was therefore unrepresentable, and on this data that is exactly the pair
the frozen rule computes. The defect reported GO-1 as FAIL and printed a note the data contradicts.

**What did not change.**

- **No call was made, and none was rerun.** The twelve records — their values, order and SHA-256 —
  are identical before and after.
- **No threshold and no rule was altered.** The correction changes which flag the frozen rule
  computes, not what the rule is. The preregistration is byte-identical to Commit A.
- **The primary verdict is unchanged.** `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION` results from both the
  original flags and the corrected ones. The only flag the correction moves is GO-1.

That last point is asserted **mechanically** — `tests/test_p3_boundary_locus.py` checks the
invariance against the real log rather than leaving it as prose.

> **A post-run analyzer fix did not alter measurements, thresholds, or the verdict.**

Nothing was amended, rebased, or force-pushed. Both measurement commits are the ones originally
pushed, and `git log --follow -- docs/audits/P3_BOUNDARY_LOCUS_RESULT.md` recovers the whole chain
from the file itself.

---

## 6. Two canonical logs, deliberately not merged

| Log | Records | SHA-256 | Why separate |
|---|---|---|---|
| [`results/usage.jsonl`](../results/usage.jsonl) | 42 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` | Frozen P0 evidence. |
| [`results/p3_boundary_locus/usage.jsonl`](../results/p3_boundary_locus/usage.jsonl) | 12 | `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` | Frozen P3 evidence. |

Appending P3's twelve records to the core log would have changed a published SHA-256 and
invalidated a freeze. A second file costs a little navigation and protects both artifacts. The
existence of two logs is the correct outcome here, not a wart.

P3 also keeps its analyzer **out of** the experiment registry: that registry feeds the frozen final
report and the backlog, and adding a member would change the meaning of both. The registry held
fifteen designs when P3 was written; it holds **ten** at this revision, after the P3.6 retirement
described in section 8. P3's exclusion is unaffected by that — it was never one of the fifteen.

---

## 7. The identifiers the records carry — `OWNER_DECISION_PUBLIC_OK`

Each record carries three opaque identifiers alongside its measurement: `request_id` per call,
`run_id` per CLI invocation, and `client_session_id` per connection pool. They were reviewed by the
repository owner before publication, and the decision is that they **stay as they are**.

The reasoning, in short:

- **They are not credentials** and are not derived from the API key.
- **They are opaque, not anonymous.** A `request_id` is a handle into TypeSafe's own request
  history, so a published record can be correlated with the request that produced it by anyone with
  backend access. That correlation is the field's purpose — it is what makes a record checkable
  against the service — and it is why the field is kept rather than hashed away.
- **A scan of both logs found no account ID, email address, IP address, username or local path**
  in or alongside any of the three. The scan covers the committed log text only.

**No historical identifier was hashed, redacted, rewritten, or removed.** The two SHA-256 digests in
section 6 cover the logs exactly as published and as they remain. The full account is in
[SECURITY.md § Opaque identifiers in the canonical logs](../SECURITY.md#opaque-identifiers-in-the-canonical-logs).

Note what this does **not** say: it is not a claim that the logs are anonymous. They contain the
full synthetic `state` of every request by design.

---

## 8. P3.6 — release closure and experiment retirement

The last stage before publication was not a measurement. It recorded two owner decisions and
closed the repository's registered-but-unrun experiment debt.

**What changed at P3.6:**

- **License settled.** The owner chose MIT; [`LICENSE`](../LICENSE) exists at the repository root
  and `pyproject.toml` carries the matching SPDX expression. The former
  `LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC` gate is closed and its record is rewritten as a
  decision rather than a question.
- **Opaque identifiers retained** by owner decision, as recorded in section 7.
- **Five unrun experiment designs were retired** from the active registry after an
  information-gain review. They are listed, with the reason for each, in
  [`docs/experiments/EXPERIMENT_REGISTRY.md`](experiments/EXPERIMENT_REGISTRY.md).

**What did not change:** neither canonical log was touched. No record was added, altered, reordered
or deleted, and both SHA-256 values in section 6 are the ones they had before this stage. P3.6 made
**no API call at all** — the retirement review was conducted over the repository's own designs and
the official documentation already recorded in
[`docs/sources/TYPESAFE_OFFICIAL_SOURCES.md`](sources/TYPESAFE_OFFICIAL_SOURCES.md).

That is also why the retirement is a *documentation* act and not a measurement one: deleting a
design that was never run removes no evidence. The designs themselves remain recoverable from git
history, which is where they belong.

> **An experiment that was never run is an intention. Retiring it is not the loss of a result.**

---

## 9. Verifying any of this

Every claim in this file is checkable from a clone, with no API key and no network:

```console
git log --oneline --decorate                    # the lineage above
git show c0fc9cc:docs/audits/P3_BOUNDARY_LOCUS_RESULT.md   # the pre-correction artifact
git rev-list --count main                       # commit count
git diff e20fad5 bdcb637 --stat -- results/usage.jsonl     # empty: the log never changed

uv run python -m jev_lab final-report           # rebuild the derived report from the log
uv run pytest                                   # 1054 tests, including the P3 invariance check
```

Hashing the canonical logs will reproduce the two SHA-256 values above exactly. That property is
why `.gitattributes` pins `eol=lf`: a Windows checkout that rewrote line endings would silently
change the artifact every hash in this repository refers to.
