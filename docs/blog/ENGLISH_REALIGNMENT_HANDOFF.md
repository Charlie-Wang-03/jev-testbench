# English realignment — handoff

**Status:** `ENGLISH_REALIGNMENT = NOT_STARTED` · `PARITY = SUSPENDED`
**Written:** 2026-09-27, at the blog boundary cleanup (claim audit revision 8).
**Audience:** whoever performs the English realignment. This is a **docs artifact**, not article prose.

---

## Why this file exists

The Chinese article and the English article are out of step, and have been since P5-E. The Chinese text has
since been revised in P5-E, corrected in P5-E1, given three micro corrections plus a fourth that closed the
reading risk the third opened, and finally given a scope cleanup that removed two matters.

**None of that has been applied to the English file.** It is frozen at its P5-B state, byte-identical, and
was not touched by any of those passes. The claim audit's English column still records what revision 2
established about it and is carried forward unchanged.

This handoff exists because two pieces of state used to sit in the Chinese article's own header as an italic
note — the fact that the English half was parked, and the fact that parity was suspended. **Those states have
been removed from the article and live here instead.** They are process metadata about this repository. A
reader arriving at the blog cold should not have to read them to understand the article, and a reader who
does need them should find them in the audit layer.

The audit this handoff serves is
[`jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md);
its §1.7 is the itemised record of the scope cleanup.

## What the realignment has to resolve

1. **All of P5-E, P5-E1, the micro corrections and the fourth correction.** The Chinese narrative was
   rewritten and then repaired many times; the English still carries the pre-P5-E shape. The claim audit
   §1.1–§1.6 is the itemised list of what changed and why.
2. **The scope cleanup (claim audit §1.7).** Two owner decisions, both about scope rather than truth:
   - internal governance status does not belong in reader-facing prose;
   - **NAS is out of the project's scope.**

## The one instruction that is not negotiable

> **NAS content must not be carried into the new English adaptation.**

The frozen English currently contains it, in two places — a bullet in its non-claims list and a whole
section, *15. NAS is a future question*. **Both must be dropped in the realignment, not translated.**

The project's subject is now fixed as **a small Jev bench built by Agentic Engineering**, and its
meta-subject as **cognitive debt accumulated while building a project with AI**. NAS is neither. The
decision was made on scope, not on claim safety: the NAS statement was never unsafe, it is simply not this
project's subject, and the article must not be seen to be reserving a future application for Jev.

**Do not substitute another future application direction for it.** The removal is a subtraction, not a swap.

## What must not change while doing this

- The frozen set under `docs/evidence/v0.1.0/`, including
  [`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md). The contract still
  forecloses the NAS-suitability statement, and the frozen evidence still records `NO_NAS_CLAIM`. Removing
  the topic from the *article* does not withdraw the exclusion from the *contract*, and the realignment must
  not touch either.
- `results/**`, the P1/P2/P3 historical audits, and the `v0.1.0` release. This is a prose task.

## Why parity is `SUSPENDED` and not `FAIL`

Because it is a gate whose subject does not currently exist. A parity check compares two aligned documents;
these two are not aligned, so running the check and reporting a number would be worse than reporting
nothing. **`SUSPENDED` means the gate was not run, not that it was run and failed.** The 18 parity tokens
were last verified present in the Chinese after the micro corrections; the English is still at its P5-B
state and was not re-checked against it.

**On completion, parity becomes a real gate again** and this file should be replaced by its result.
