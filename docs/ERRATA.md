# Errata registry

**What this file is.** A register of known defects in this repository's *historical* artifacts —
documents and code that have already been published and that this repository deliberately does
**not** retroactively rewrite. Each entry states what the artifact says, what is actually true, how
the corrected value was derived, and whether any conclusion moves.

**What this file is not.** It is not a changelog, and it is not a second copy of the evidence. It
records only errors that a reader of the frozen artifacts could otherwise be misled by. A defect
that a later commit already fixed in place is registered here with status `RESOLVED` and no
outstanding action; a defect in a historical artifact is registered as `DOCUMENTED`, which means the
correct value lives here and the artifact is left as it was.

**Why historical artifacts are not edited.** The audit trail is the product. A P1 audit that was
silently corrected in 2026 would no longer be the document that produced the P1 verdict, and a
reader could not tell which of its numbers had been touched. Editing it would buy a tidier file at
the cost of the one property that makes the file worth citing. So the defect is recorded here, and
the artifact keeps its error.

Every entry below is verifiable against the frozen canonical logs. Nothing here requires an API
call, and nothing here was produced by one.

**Status vocabulary**

| Status | Meaning |
|---|---|
| `DOCUMENTED` | The artifact is historical and stays as written. The correct value is recorded here. No conclusion changes. |
| `RESOLVED` | A later commit corrected the defect in the active code or the regenerated artifact. Kept here for provenance. |

---

## ERR-001 — P1 audit states the wrong Noul count

| | |
|---|---|
| **Status** | `DOCUMENTED` |
| **Artifact** | [`docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md`](audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md), row `TS-JEV-SEM-004` |
| **Found** | During P3.5, and re-derived independently for this registry during P4 |
| **Verdict impact** | **None** |

**Incorrect text.** The row reads:

> **42 of 42** Noul answers carry no `confidence` field; every Choice/Score answer does.

**What is actually true.** The canonical core log contains **45** `noul` answers, and **none** of
them carries a `confidence` key. The correct figure is **45 of 45**.

**How the correct value was derived.** Independently of any earlier report, by reading
`results/usage.jsonl` (42 records, SHA-256 `38e67630…`) and counting answers by `type` across every
record's `answers` map:

```console
uv run python -c "
import json, collections
recs = [json.loads(l) for l in open('results/usage.jsonl', encoding='utf-8')]
c = collections.Counter(a['type'] for r in recs for a in r['answers'].values())
confirmed = sum(1 for r in recs for a in r['answers'].values()
                if a['type'] == 'noul' and 'confidence' in a)
print(c, 'noul carrying confidence:', confirmed)"
# Counter({'choice': 45, 'noul': 45, 'score': 29}) noul carrying confidence: 0
```

**Why the error happened.** 42 is the **record** count, not the answer count. P1 read the size of
the log and used it as the denominator for a claim about answers. Records and answers are different
populations: one record can carry several answers, and the core log's 42 records carry 119 answers
between them.

**Scientific consequence.** None. The claim P1 makes — that a `Noul` answer carries a single
probability and no separate `confidence`, unlike `Choice` and `Score` — is exactly what the log
shows. Correcting 42 to 45 sharpens a count that was already true in substance; it does not
strengthen, weaken or retract anything. The row's classification (`DR`, for reproduced), its
`TS-DOC-NOUL` source, and its "clean binary observation" note all stand.

**Whether this file's own numbers are affected.** No. `docs/findings/findings.md`, the derived final
report, and the freeze documents state 45 and were computed from the log, not copied from P1.

---

## ERR-002 — P3 analyzer could not represent its own frozen outcome pair

| | |
|---|---|
| **Status** | `RESOLVED` — corrected in `bdcb637` |
| **Artifact** | `src/jev_lab/p3_boundary_locus.py` at commit `c0fc9cc`, and the result document it rendered |
| **Found** | During P3, disclosed in the commit that recorded the measurements |
| **Verdict impact** | **None** — the verdict is unchanged by the correction |

**The defect.** In `analyze()`, GO-1 and GO-2 are two separate conditions in the preregistration
(§9). The analyzer wrote them as a single branch, so the pair `(GO-1 PASS, GO-2 FAIL)` was
unrepresentable. On this data that is exactly the pair the frozen rule computes: both single-field
arms reach the GO-1 line (`I_med = 0.31`, `C_med = 0.36`, against a `≤ 0.475` bar) while neither
leaves its counterpart inside the GO-2 vague-baseline band. The defective analyzer reported GO-1 as
FAIL and printed the note *"neither single-field arm reached the GO-1 median of <= 0.475"*, which
this data contradicts.

**How it was corrected.** Commit `bdcb637` (*Repair P3 analyzer against frozen preregistration*)
separated the two conditions in `analyze()` and re-rendered the result document **from the
unchanged log**. The correction flag was derived from the generated document, not typed in.

**Why this does not move the verdict.** Three properties hold, each independently checkable:

- **No measurement changed.** `git diff c0fc9cc bdcb637 --stat -- results/` is empty. The twelve
  records in `results/p3_boundary_locus/usage.jsonl` are byte-identical before and after.
- **No threshold and no rule was altered.** The preregistration document at `db7d06f` is unchanged.
- **The verdict is the same.** The only flag the correction moves is GO-1, and GO-1 alone was never
  sufficient — the frozen rule requires a GO-1 arm *paired* with a counterpart inside the GO-2 band,
  and no such pairing exists on this data. `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION` is what the
  uncorrected rule computes too; the defect made the reasoning display wrong, not the decision.

**Where the pre-correction artifact is.** Commit `c0fc9cc` holds the earlier rendering, including
the incorrect GO-1 row. It is recoverable from Git:

```console
git show c0fc9cc:docs/audits/P3_BOUNDARY_LOCUS_RESULT.md   # the analysis as first recorded
git show c0fc9cc:src/jev_lab/p3_boundary_locus.py          # the analyzer that produced it
```

Full provenance: [P3 result § Post-run analyzer correction provenance](audits/P3_BOUNDARY_LOCUS_RESULT.md)
and [EVIDENCE_PROVENANCE.md § 5](EVIDENCE_PROVENANCE.md).

---

## Registering a new entry

An entry belongs here only if all of the following hold:

1. The defect is in an artifact that has already been published or frozen.
2. The correct value can be re-derived from the canonical logs or from Git, without an API call.
3. The artifact will **not** be retroactively edited.

If a defect is corrected in place by a new commit, it does not need a `DOCUMENTED` entry — record
it in the commit and, if it changes an interpretation, in the relevant audit. This file exists for
the errors that are being deliberately left standing.

**Frozen release binding.** At release `v0.1.0` this registry contains exactly two entries, both
listed above. The registry is part of the frozen evidence set; see
[`docs/evidence/v0.1.0/evidence-manifest.json`](evidence/v0.1.0/evidence-manifest.json).
