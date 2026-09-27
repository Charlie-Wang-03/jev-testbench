# Agentic Engineering and cognitive debt

**English** | [简体中文](AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.zh-CN.md)

**Status: project process record — not evidence.** Nothing on this page is a measurement, and none
of it is covered by the evidence freeze or by the [claim
contract](evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md). The measurements live in the canonical logs and
the rules for talking about them live in the contract; this page is a different kind of object, and
it is kept separate on purpose.

Two questions are easy to blur together here, so they are named separately throughout:

- **The object level** — what TypeSafe Jev does, on this machine, on our inputs. This is evidence.
- **The meta level** — what building this bench did to the maintainer's understanding of it. This is
  this page.

---

## 1. What "Agentic Engineering" means here

This is **not** a definition of the industry term. It describes one arrangement, scoped to this
repository. Stated any more broadly it would claim more than a single project can support.

The arrangement has four parts:

```
Human owner
+
ChatGPT            — planning and review
+
Claude Code        — implementation and execution
+
Git, tests, canonical evidence
```

The fourth part is not decoration. What makes the arrangement work at all is that the collaboration
runs through **artifacts that outlive the conversation**: commits, a test suite, an append-only log
whose records are written whether a call succeeds or raises, audit documents, and a written stage
order for each phase. A suggestion that never reached a commit did not happen here; a claim that
cannot be traced to a log line is not made here.

That is the whole of the definition. It says nothing about whether the arrangement is efficient,
wise, or reproducible elsewhere, and this project has not measured any of those.

---

## 2. Who did what

**This attribution is the owner's declaration.** It is not derived from the repository and cannot be
verified from it: Git records *when lines changed*, not *who decided they should*. A reader should
treat the table below as testimony about process, in the same way the release notes are testimony
about a measurement — with the difference that the measurements are checkable and this is not.

The division is stated with **"primarily"** on purpose. Every line of code and every sentence cannot
be attributed precisely, and a claim of precise attribution would be false in both directions.

| Participant | Primarily responsible for |
|---|---|
| **Human owner** | Raising the original question; setting the project's goals; choosing each stage's direction; approving and rejecting key steps; the decisions that are the owner's alone — license, publication of opaque identifiers, experiment retirement, article style, and the project rename; carrying final authorship and publication responsibility. |
| **ChatGPT** | Problem decomposition; stage planning; reviewing evidence; suggesting experiment designs; defining acceptance criteria; writing the next stage's work order; editorial and writing supervision. |
| **Claude Code** | Entering the repository and implementing; code changes; tests; the actual execution of Jev experiments; repairs; documentation maintenance; drafting and structurally rewriting the articles. |

Two things this table is not. It is not a claim that the AI systems were interchangeable — they were
given different work and the outputs differed. And it is not a claim that the human owner was
passive: the direction, the refusals and the final signature are the parts that were never
delegated.

---

## 3. Cognitive debt: a working concept for this project

**Cognitive debt** is used here as a *working concept*. It is not offered as a scholarly term
originating in this project, and no priority is claimed for it.

The working definition:

> the gap between the complexity that has been implemented, automated and recorded in this project,
> and the owner's ability to independently explain, verify and modify that complexity.

Informally, and only informally:

```
cognitive debt  ≈  implemented project complexity  −  independently understood project complexity
```

**This is not a measurable quantity.** It has no unit, no instrument, and no value anywhere in this
repository. The expression above is a way of pointing at a shape, not a formula. It cannot be
computed from the canonical logs, from line counts, or from how many stages have passed, and nothing
in [`results/`](../results/usage.jsonl) bears on it.

Concretely, in this project the gap showed up as things that were **true and working** while being
**not fully explainable by the owner on demand** — a module whose behaviour could be described at a
high level but not reconstructed from memory, a frozen release whose verification path could be run
but not derived, a document that existed because a process asked for it and had stopped being read
by anyone.

The debt is not a defect in the code, and it is not the same as an unfinished task. An unfinished
task is work not yet done. Cognitive debt is work that *is* done, in a form its owner cannot
independently re-derive.

---

## 4. Externalised controls are not understanding

This is the limitation that matters most, and the rest of this page exists to state it plainly.

This repository has a real set of externalised controls:

| Control | What it is |
|---|---|
| [Canonical logs](../results/usage.jsonl) | Append-only records, one per real API call, written by the recorder whether the call succeeded or raised. |
| [Preregistration](experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md) | The design, thresholds and stopping rule for P3, frozen before the first request. |
| [Claim audits](blog/jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md) | Every substantive claim in the article, mapped to the contract class that permits it. |
| [Errata](ERRATA.md) | Defects found after the fact, disclosed and tracked rather than quietly repaired. |
| [Evidence freeze](evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md) | Version `v0.1.0`, its manifest, and an offline verifier that re-hashes the whole set. |
| [Tests](../tests/) | An offline suite that blocks sockets, so a test cannot silently reach the live API. |

These controls do three real things. They **preserve facts** — the log does not soften when a result
is disappointing. They **constrain stories** — the claim contract refuses phrasings the data does
not support, in both languages. And they **support later reconstruction** — someone, including the
owner a year from now, can follow them back.

They do **not** automatically become human understanding.

That distinction is the point. A passing test is a fact about the artifact, not about the person who
ships it. A frozen manifest proves that a set of bytes has not moved; it does not prove that anyone
alive could rebuild those bytes. A claim audit checks what the article is permitted to assert; it
does not check that the author could defend the assertion in a room without it.

The controls make it **harder to say something false**. They do not make it **possible to explain
what is true**. Those are different capabilities, and having the first is easy to mistake for having
the second — which is itself a good description of how the debt accumulates.

---

## 5. What this page does not claim

- It is not a Jev claim. It is outside the [claim contract](evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md),
  and the contract's `SAFE_TO_STATE` and `SAFE_WITH_SCOPE` classes do not govern it. Process claims
  are the owner's declaration and this record; evidence claims are the contract and the freeze.
- It is not a measurement. No number here is derived from the canonical logs. Nothing here should be
  quoted as a finding about Jev, about TypeSafe, or about AI-assisted development in general.
- It is not a verdict on the practice. This is one project's record, and the sample size is one.
  Whether the arrangement was worth its cost is a judgment the owner has not asked this document to
  make.
- It is not an endorsement of the metaphor that the article closes on. The article uses a figure of
  speech once, as a figure of speech.

**Keeping these two domains apart is not bookkeeping.** If process statements were allowed into the
evidence layer, the layer's guarantees would start laundering claims they were never built to check,
and the freeze's verifier would be attesting to prose it cannot read.
