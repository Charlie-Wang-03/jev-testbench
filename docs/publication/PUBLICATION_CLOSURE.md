# Publication Closure

**Status: PUBLICATION CLOSURE COMPLETE.**

This is the operational closure record for `Charlie-Wang-03/jev-testbench`. It is not scientific
evidence and does not modify the frozen `v0.1.0` evidence set.

---

## 1. Public state

| Item | Live state |
|---|---|
| Repository | `https://github.com/Charlie-Wang-03/jev-testbench` |
| Visibility | `PUBLIC` |
| Default branch | `main` |
| Release commit | `22a211517b5133f1e8c67965f2a44054c342d8e5` |
| Historical evidence tag | `v0.1.0` → `37ef2e425d5e9e534f856a7243be848ff17f0cbb` |
| Publication tag | `v0.1.1` → `22a211517b5133f1e8c67965f2a44054c342d8e5` |
| GitHub Release | `https://github.com/Charlie-Wang-03/jev-testbench/releases/tag/v0.1.1` |
| Release title | `v0.1.1 — Publication Closure` |
| License | MIT |
| External blog copy | none |
| TypeSafe contact | none |

The `v0.1.1` Release object was corrected after publication to remove one stale use of
“candidate”; the tag and source tree did not move.

---

## 2. Release semantics

```text
v0.1.0
= immutable historical evidence/software freeze
= historical project name: jev-test
= scientific evidence anchor

v0.1.1
= public-facing / presentation closure
= current project name: jev-testbench
= zero new Jev API calls
= zero new experiments
= zero measurement rewrites

v0.2.0+
= reserved for genuinely new scientific evidence
```

The carried-forward scientific state remains:

```text
NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
PUBLIC_NOVELTY_UNRESOLVED
```

---

## 3. Evidence integrity

| Artifact | Records | SHA-256 |
|---|---:|---|
| `results/usage.jsonl` | 42 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| `results/p3_boundary_locus/usage.jsonl` | 12 | `17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e` |

`v0.1.0` still dereferences to its historical evidence commit. Publication Closure did not edit
`docs/evidence/v0.1.0/**`, either canonical log, the analyzer-bug history or the errata history.

---

## 4. Publication execution

PC4 completed the following sequence:

1. `0.1.1.dev0 → 0.1.1` in package/version metadata.
2. `CITATION.cff` moved to the current `jev-testbench / v0.1.1` publication identity while the
   immutable `v0.1.0` tag retained its own historical citation file.
3. The exact release SHA passed locked install, lint, the full offline test suite, package build,
   deterministic derived-artifact regeneration and `v0.1.0` evidence verification.
4. Annotated tag `v0.1.1` was created at the exact green release commit.
5. GitHub Release `v0.1.1 — Publication Closure` was created against that tag.
6. Repository description/topics were applied and the repository changed from `PRIVATE` to
   `PUBLIC`.
7. The repository-hosted English and Chinese blog files became the first publication surface. No
   external-platform copy was created.

---

## 5. Post-public acceptance

Verified from live GitHub repository state:

- repository reports `private=false` / `visibility=public`;
- `v0.1.0` remains unchanged;
- the GitHub Release exists, is neither draft nor prerelease, and is attached to `v0.1.1`;
- English and Chinese README switchers are present;
- English and Chinese blog switchers are present;
- `LICENSE` at `v0.1.1` is MIT;
- `CITATION.cff` at `v0.1.1` reports version `0.1.1` and points to the `v0.1.1` tree;
- the exact release snapshot has a successful Linux CI run;
- no open pull request exists;
- repository search found no current-tree private server address or Windows absolute-path leak.

The owner explicitly waived a separate anonymous clean-clone gate for final closure. The operational
handoff instead requires the existing local checkout to fetch/prune remote refs and fast-forward to
the final public `main` after this closure commit.

---

## 6. Owner-requested maintenance — COMPLETE

### 6.1 Bilingual About description

The live GitHub About description is bilingual:

```text
A lightweight, auditable Jev testbench built through Agentic Engineering, with frozen evidence, a preregistered null result, and a bilingual technical blog. 基于 Agentic Engineering 的轻量、可审计 Jev 实验台，包含冻结证据、预注册负结果、双语技术博客与认知负债反思。
```

Homepage remains empty.

### 6.2 Branch cleanup

The remote branch surface now contains only:

```text
main
```

The 14 historical working branches were fully merged before deletion; there are no open pull
requests. Historical release provenance remains independently anchored by the annotated `v0.1.0`
and `v0.1.1` tags.

---
## 7. Closure state

```text
PUBLICATION_BASELINE_RECONCILED
PUBLICATION_MAIN_PROMOTED
PUBLIC_READINESS_AUDIT_PASS
OWNER_PUBLICATION_DECISIONS_APPROVED

REPOSITORY_PUBLICATION_COMPLETE
RELEASE_PUBLICATION_COMPLETE
BILINGUAL_BLOG_PUBLICATION_COMPLETE

POST_PUBLICATION_ACCEPTANCE_PASS
OWNER_REQUESTED_MAINTENANCE_COMPLETE

PUBLICATION_CLOSURE_COMPLETE
```

Publication Closure is complete. Future work begins from the public `main` state and must not rewrite
`v0.1.0`, move `v0.1.1`, or reinterpret `v0.1.1` as new Jev scientific evidence.
