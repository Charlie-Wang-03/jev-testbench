# Blog publication options

**Status: OWNER APPROVED. Not published yet.** The first publication surface is the GitHub repository itself, with the canonical bilingual Markdown under `docs/blog/**`. No external-platform publication is part of this closure.

**What is being placed.** A pair of articles —
[Chinese source](../../docs/blog/jev-as-probabilistic-decision-primitive.zh-CN.md) and
[English adaptation](../../docs/blog/jev-as-probabilistic-decision-primitive.md) — that are written
against a frozen evidence release and are already audited claim by claim
([audit](../blog/jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md)). They are technical
narrative, roughly 5,500 English words, and they lean on tables, fenced code and long canonical
strings (`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`).

**A constraint that outranks every criterion below.** The articles' value is that a reader can check
them. Any venue that breaks the relative links to `v0.1.0`, or that cannot render the tables and the
canonical strings intact, damages the thing the articles are for. Rendering fidelity is not cosmetic
here.

---

## A. GitHub repository only

The articles live at `docs/blog/**` and are reached from the repository's own index.

| Criterion | Assessment |
|---|---|
| Technical audience | Strong and self-selecting. The people who arrive are the people who read repositories. |
| Bilingual support | **Best available.** Two files, two languages, side by side, each linking to the other, both under the same claim audit. No platform can currently improve on this. |
| Markdown fidelity | **Exact.** GitHub renders the source that the audit audited. Nothing is transformed. |
| Tables / code / canonical strings | **Exact.** Relative links to `../evidence/v0.1.0/` resolve inside the repository. |
| Canonical link | Trivial: the repository URL, and the tag for the evidence. |
| Edit history | **Best available.** Every change is a commit with a message explaining it; errors are corrected by later commits that stay visible. |
| Search / discovery | **Weakest of the three.** No feed, no topic tags, no recommender. Discovery depends on someone linking to it. |
| Portability | Total. It is plain Markdown in Git. |

**The trade is honest:** maximum fidelity and provenance, minimum reach.

---

## B. GitHub + an external platform

The repository keeps the evidence and the audit; an external venue carries a copy for reach. No
single platform serves both languages well, and they differ most on exactly that axis.

| Venue | Technical audience | Bilingual | Markdown fidelity | Tables / long code | Canonical link | Edit history | Discovery | Portability |
|---|---|---|---|---|---|---|---|---|
| **GitHub Pages** (Jekyll/Hugo) | Medium | Good — two pages, your own routing | High | High | Trivial | Via Git, if built from the repo | Low — no built-in feed | High |
| **dev.to** | Strong, developer-heavy | One language per post; a Chinese post reaches a small slice of the same feed | High | High | Good (canonical URL field) | Post revisions, not public | Medium | High (Markdown in/out) |
| **Medium** | Broad, less technical | One language per post | Low — its editor rewrites Markdown | Medium; code blocks render, tables historically unreliable | Only via a note in the prose | Not public | Medium–high | **Low** — export is lossy |
| **知乎** | Large Chinese technical readership | Chinese only | **Low** — no Markdown; code and tables must be rebuilt by hand | Weak | Via a link in the prose | Not public | High, in Chinese | Low |
| **掘金** | Chinese developer readership | Chinese only | Medium — accepts Markdown, normalises some syntax | Good | Via a link in the prose | Not public | High, in Chinese | Medium |
| **Personal site** | Whatever you build | **Full control** — best of any external option | Full control | Full control | Full control | Full control | Depends entirely on the site | Full control |

**Two notes that matter more than the table.**

- **No platform is good at both languages.** dev.to, Medium and the Chinese venues each serve one
  language well. A bilingual pair therefore means either two platform accounts and two publishing
  acts, or a canonical pair on GitHub with one language syndicated.
- **None of these venues gives you the edit history the repository already has.** A correction on
  GitHub is a commit a reader can see; a correction on a platform is a silent edit or a new post.

---

## C. One canonical location plus syndication

The repository Markdown stays the canonical text; any platform version is a publication copy that
links back to the tag and the repository.

This is the structure the articles were written to fit — both already point at
`v0.1.0` rather than at `main`, so a copy that preserves those links keeps the provenance chain
intact. It also answers the rendering-fidelity problem: the platform copy may be adapted for the
platform, but the canonical text — the one the claim audit covers — is the Markdown that never
moved.

**Where the trade-offs land:**

- Corrections have one home, and the platform copies are understood to be downstream of it.
- A reader who arrives from a platform can always reach the evidence, if the canonical link survives
  the platform's link handling.
- The platform copy must not be *improved* on the way out. Any adaptation for platform formatting
  must not widen a claim — see [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md).

The cost is duplicated maintenance: two places to correct if something changes.

---

## Publication Closure recommendation

**For the first publication, choose option A: the public GitHub repository with the two canonical
Markdown articles under `docs/blog/**`.**

That is sufficient for this project's first publication because the repository is not merely a
code host: it is also the provenance surface. The bilingual switchers, evidence links, claim audit,
Git history and frozen tag all work best when the reader stays in the repository that produced
them. An external venue would add reach, but it would not add evidence, reproducibility or
publication completeness.

Option C remains a sensible **later distribution step** if reach becomes a separate goal. If that
happens, the repository Markdown remains canonical and any platform copy stays downstream; the
platform adaptation must not widen a claim.

**Owner decision:** repository-only first publication. External syndication is deferred and is not part of Publication Closure. No external account has been created and nothing has been posted externally.
