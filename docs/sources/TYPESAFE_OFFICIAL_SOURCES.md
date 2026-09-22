# TypeSafe Official Sources — P1 Provenance Registry

**Audit stage:** P1 — Official Claims × Local Evidence Audit
**Publisher of all sources below:** TypeSafe AI
**Retrieval window (UTC):** 2026-09-22T13:20:05Z (docs) through 2026-09-22T13:2xZ (site/blog)
**Retrieval method:** direct HTTPS `GET` of public pages. No TypeSafe inference endpoint was
called during this audit.

## How to read this file

This file records *provenance*, not interpretation. Interpretation and mapping to local
evidence live in [docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md](../audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md).

Rules applied here:

- **Paraphrase first.** Verbatim fragments are used only where the exact wording itself is the
  thing being audited (a number, a product phrase, a hedge). They are marked with `"…"` and kept short.
- **Source-specific wording is preserved, not unified.** Where two official pages say different
  things, both are recorded as-is and the difference is flagged. See
  [Recorded source-internal divergences](#recorded-source-internal-divergences).
- **No third-party source is used** to adjudicate a disagreement between official pages.
- **Hashes are content fingerprints, not a security boundary.** They let a later audit detect
  that a live page changed. Dynamic pages may re-render and change hash without any semantic change.
- This file does not mirror whole third-party pages into the repository.

---

## Tier 1 — Product / technical documentation

All documentation pages were retrieved from `https://docs.typesafe.ai/`. Appending `.md` to a page
path returns raw Markdown; that is what was fetched.

| Source ID | Title | URL | Accessed (UTC) | Relevant version/applicability | SHA-256 (retrieved body) |
|---|---|---|---|---|---|
| TS-IDX | Documentation index (`llms.txt`) | https://docs.typesafe.ai/llms.txt | 2026-09-22T13:2xZ | Whole doc set | `486685db6fec679ca3c7149f15b19c1ab069adbbc7a4b2369e80e5fc0f8caf64` |
| TS-DOC-INTRO | Introduction | https://docs.typesafe.ai/introduction.md | 2026-09-22T13:20:05Z | Jev (general) | `73eb533b5397d508e1cf606c88d5111f0e70bb8dd1d4841c45502c50d520e072` |
| TS-DOC-SYS1 | System One (concept) | https://docs.typesafe.ai/concepts/system-one.md | 2026-09-22T13:20:05Z | Jev (general) | `e072211498bc1b6ed22d14aae2c2716903f4a8112e908cc45c35af65d3b84895` |
| TS-DOC-STATE | State (concept) | https://docs.typesafe.ai/concepts/state.md | 2026-09-22T13:20:05Z | Jev (general) | `6871d59470c6af330b10be302a7382ab4c175ee8994886ad48df2fe6bb315462` |
| TS-DOC-PRIM | Primitives (Questions) | https://docs.typesafe.ai/primitives.md | 2026-09-22T13:20:05Z | Jev (general) | `130d9136a2f01497e72920a6e8d96073056d86d838ca13b8a505e4adb87651f6` |
| TS-DOC-CHOICE | Choice | https://docs.typesafe.ai/primitives/choice.md | 2026-09-22T13:20:05Z | Jev (general); examples show `jev-1.13.0` | `4c55085131f8f2d7ae1faefdec52b1c7b379d40657d701cd2c786021cfe9dac9` |
| TS-DOC-SCORE | Score | https://docs.typesafe.ai/primitives/score.md | 2026-09-22T13:20:05Z | Jev (general) | `5afe0db1d2d108c3bf35f73f5fddbfcd2b9ade2d3c6f553af8a02b2bfd005ae9` |
| TS-DOC-NOUL | Noul | https://docs.typesafe.ai/primitives/noul.md | 2026-09-22T13:20:05Z | Jev (general) | `aa7bff0d04bd42614e0e851a9ad4917ccc6287c882bc5dece7689b085ef789e6` |
| TS-DOC-ADV | Advanced: structure | https://docs.typesafe.ai/primitives/advanced.md | 2026-09-22T13:20:05Z | Jev (general) | `73eeedee0c3ff68e5964c914ba006e4f59522fa8222e43bd960418febd13ea7f` |
| TS-DOC-CONF | Confidence | https://docs.typesafe.ai/confidence.md | 2026-09-22T13:20:05Z | Jev (general) | `97dafe98b77979906a2ad456013dd85a70dcecd109d0644b096817d910997ea5` |
| TS-DOC-PRIMER | AI primer | https://docs.typesafe.ai/introduction/machine-learning-primer.md | 2026-09-22T13:20:05Z | Jev (general); describes RLCD | `45e6a22bc175f2ce1c404271dd26559179a6f6a83bde2dfcdbd963dbc1649551` |
| TS-DOC-BUILD | How to build with TypeSafe | https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md | 2026-09-22T13:20:05Z | Jev (general) | `d9f4d34c1349bf5acb55c99d6a1651eacfc481ad8d1f78ccb8776769da729a49` |
| TS-DOC-USECASE | Example use cases | https://docs.typesafe.ai/concepts/use-case-map.md | 2026-09-22T13:20:05Z | Jev (general) | `9d193b6379d17a3ac2f236eda9f15136e32b360e78a66bef03ce59605edfac2d` |
| TS-DOC-PATTERNS | Patterns (index) | https://docs.typesafe.ai/patterns.md | 2026-09-22T13:20:05Z | Jev (general) | `3c810e35f9587e0432c0fae4448961e54233ecbe51a4ba091721d55a0e5bc107` |
| TS-DOC-FANOUT | Speculative fan-out | https://docs.typesafe.ai/patterns/fan-out.md | 2026-09-22T13:20:05Z | Jev (general) | `8d7a251ea6b735cb4994c1e0a95166cc0b3febce7d18189c3aa5e1673f182c91` |
| TS-DOC-CONFROUTE | Confidence-gated routing | https://docs.typesafe.ai/patterns/confidence-routing.md | 2026-09-22T13:20:05Z | Jev (general) | `7a4de8d39a24c5d6b7e74b1b170fbbe101ca69419af39bac6da4e0c1f678b7bf` |
| TS-DOC-COMPOSITE | Composite scoring | https://docs.typesafe.ai/patterns/composite-scoring.md | 2026-09-22T13:20:05Z | Jev (general) | `538f42d614fbf29cbfa0aa9fee1859651083a0b67c4b31a21d2710f3fe84d9f5` |
| TS-DOC-INTENT | Intent routing | https://docs.typesafe.ai/patterns/intent-routing.md | 2026-09-22T13:20:05Z | Jev (general) | `84b670d502b3f41165a901495688dc7bd586ff3082854f5432a7a4962d697cfb` |
| TS-DOC-MODELS | Models | https://docs.typesafe.ai/models.md | 2026-09-22T13:20:05Z | `jev-1.13.0`; aliases `jev-latest`, `jev-preview` | `9d20bb3c90a0147532d0b20ddc4c64579391be7842e965543b27bad684eeb4d6` |
| TS-DOC-JAG | Jev 1.13 jaggedness | https://docs.typesafe.ai/model-jaggedness/jev-1.13.md | 2026-09-22T13:20:05Z | **Explicitly scoped to `jev-1.13`**; page states "Last reviewed 2026-09-17" | `e69329bd32e91ac08f0bd2681ceb4aacc34923b9190e29c15c8f75d8e22950e2` |
| TS-DOC-API | API reference | https://docs.typesafe.ai/api.md | 2026-09-22T13:20:05Z | `POST /v1/systemone` | `7ea1c82d9d16bd06e3d38885a5292548293f91e6d1ade4682c27398ced51a9e5` |
| TS-DOC-SKILL | Agent skill | https://docs.typesafe.ai/agent-skill.md | 2026-09-22T13:20:05Z | Claude Code / Codex agents | `5ed8f74a133760523a67674f0feaac6ac88d9f1d242574ce3c9c4965f6e037c4` |
| TS-DOC-CODINGAGENTS | Jev with coding agents | https://docs.typesafe.ai/introduction/coding-agents.md | 2026-09-22T13:2xZ | Jev (general) | `e61ec46260302e87e21ca65fe2a1d67ae6c2741a4a586645ace5dd7d9f501175` |
| TS-DOC-SDK | Client SDKs (index) | https://docs.typesafe.ai/sdk.md | 2026-09-22T13:20:05Z | Python + JS SDKs | `bbd9d2eaad4c605150fcead2dcb1fdb8415a10f6e5481186e185e7e8d4826a97` |
| TS-DOC-SDKRESP | SDK: Answers and responses | https://docs.typesafe.ai/sdk/python/api/types/responses.md | 2026-09-22T13:20:05Z | Python SDK | `7b0167d010dc165b6584939a550c8ec35d31c003f0e8095638a46a037b6f6f8a` |
| TS-DOC-CB-PAR | Cookbook: Parallel questions | https://docs.typesafe.ai/cookbooks/parallel_questions.md | 2026-09-22T13:20:05Z | 13-question GDPR briefing | `53dfe4516fd67b9bfc5abc9a50a6f4db6426b5b2951d41cd91e2fec45aded2fe` |
| TS-DOC-CB-CN | Cookbook: Self-consistency — nouls | https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md | 2026-09-22T13:20:05Z | `jev-latest` on production API, "sampled on 2026-09-11" | `cee9cb98c52cfbf588e0dda5defd0ba0c0d78e1162df7f20ba7bed1ece9935ff` |
| TS-DOC-CB-CC | Cookbook: Self-consistency — choices | https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md | 2026-09-22T13:20:05Z | `jev-latest` on production API, "sampled on 2026-09-11" | `e0444c2c4e9c9440595692eaa2806157d43080adc525f94fe5c204b2d7bafe36` |

### Short paraphrase of what each Tier 1 source asserts

- **TS-IDX** — Machine-readable index of the doc set. Also carries one-line summaries per page;
  two of those summaries embed performance multipliers (see divergences).
- **TS-DOC-INTRO** — Jev is the first System One model; the pitch is that forcing a text generator
  to emit structured decisions creates a parse/validate mismatch, which Jev removes. Returns typed
  values and probability distributions; Choice and Score also return `confidence`.
- **TS-DOC-SYS1** — System One models return typed answers and probabilities rather than generated
  text. States calibration is *group-level*: "Calibration is measured across groups of predictions;
  it does not guarantee that an individual answer is correct." Jev accepts **text input only**
  (string, JSON object, or array of text); no image/audio/video.
- **TS-DOC-STATE** — State is the evaluation input; may be string, JSON object, or array. All
  questions see the same state and are evaluated independently. English is the primary training
  language; other languages including CJK are accepted "but currently have lower accuracy".
- **TS-DOC-PRIM** — Three question types. Answers are constrained to supplied options and are
  independent of one another. Notes a Noul `0.5` means equiprobable yes/no, *not* a mid-scale
  value. Question IDs are not sent to the model.
- **TS-DOC-CHOICE** — `choice` is the highest-probability option; `probabilities` sums to 1;
  `confidence` is derived from the spread. A Choice accepts **up to 255 options**. Worked
  examples give concrete `confidence` values alongside their distributions.
- **TS-DOC-SCORE** — `score` is a position along the levels, can land between levels, and is the
  probability-weighted mean of level numbers. `legend` maps level numbers to descriptions.
  Explicitly notes **different distributions can produce the same score**, and that confidence
  "describes the model's answer, not a guarantee that the answer is correct".
- **TS-DOC-NOUL** — A Noul answer is a single number: P(yes). It carries **no separate
  `confidence`** because a two-outcome distribution is fully described by one number. Table of
  recorded example values. Notes the value is not a degree scale for the underlying property.
- **TS-DOC-ADV** — `instructions` and `criteria` entries accept `string`, `object`, `array`, or
  `null`. Structured criteria sharpen option boundaries.
- **TS-DOC-CONF** — `confidence` is a statistic computed from the returned distribution, collapsed
  to 0–1. TypeSafe supplies a default but explicitly does not lock you into their definition;
  `probabilities` are always returned. Proposes a three-band usage pattern (act / caution /
  don't act). States thresholds are domain-specific and should be tuned on your own data.
- **TS-DOC-PRIMER** — Describes RLCD. States the calibration contract as a frequency statement
  (0.2-probability outcomes occur ~20% of the time, etc.) and immediately scopes it: "These rates
  describe groups of predictions, not a guarantee about any single answer."
- **TS-DOC-BUILD** — Design guidance: keep control flow in code, give the model narrow decisions.
- **TS-DOC-USECASE** — Catalog of use cases (routing, ranking, extraction, verification, guardrails).
- **TS-DOC-PATTERNS** — Index of four architectural patterns: speculative fan-out, confidence-gated
  routing, composite scoring, intent routing.
- **TS-DOC-FANOUT** — Ask every question your code might need, including speculative ones, and let
  code decide relevance. All questions in a request are evaluated in parallel.
- **TS-DOC-CONFROUTE** — Confidence as a second decision axis: the answer says *what*, confidence
  says *whether to act*. 0.6 floor plus per-action thresholds (e.g. >0.85 for a transfer).
- **TS-DOC-COMPOSITE** — Decompose a judgment into atomic Scores, normalize and weight in code.
- **TS-DOC-INTENT** — Classify first, then route to deterministic code, a specialist LLM, or a human.
- **TS-DOC-MODELS** — `jev-1.13.0` is the current model. Price **$42 per billion input tokens /
  $0.042 per Mtok**; output tokens are **free**. Rate limits 250,000 tok/s and 1,200 req/min.
  Context: **64k tokens per request; 32k for `state` plus the longest question**. Aliases
  `jev-latest` and `jev-preview` both currently point to `jev-1.13.0`. Aliases move, so the
  response's `model` field should be logged. Not fine-tuned per customer.
- **TS-DOC-JAG** — Vendor-published known-limitations page for `jev-1.13`: literal reading, weak
  counting, weak math/numeric representations, date comparison, indirection, large state /
  context rot, adversarial content, contradictory instructions, non-guaranteed structural
  invariants, and no text generation.
- **TS-DOC-API** — `POST /v1/systemone`. Response carries `model`, `answers`, and `usage` with
  `input_tokens` / `output_tokens`. **The API returns token counts only; there is no `cost` field
  in the API response.**
- **TS-DOC-SKILL / TS-DOC-CODINGAGENTS** — Jev is not a drop-in LLM replacement for a coding
  agent; it makes no attempt at tool-calling or file editing.
- **TS-DOC-SDK / TS-DOC-SDKRESP** — SDK types mirror the HTTP shapes.
- **TS-DOC-CB-PAR** — Batching 13 questions into one call vs 13 separate calls: table shows
  `$0.000497 / 0.27s` vs `$0.006090 / 2.71s`, printed as **"12.2x cheaper, 10.0x faster"**, with
  "no change in answers".
- **TS-DOC-CB-CN** — 15 repeats × 14 Nouls over one insurance claim. Reports TypeSafe mean
  per-question probability **standard deviation `0.0102`**; reports its `covered` answers
  spanning **0.43–0.53**, i.e. crossing a 0.5 threshold. Documents that each call carried a fresh
  `uid` and that the design **"cannot separate sensitivity to the irrelevant field from variation
  that would occur on identical requests."**
- **TS-DOC-CB-CC** — 15 repeats × 8 Choices over one borderline moderation post. Reports plural-label
  repeat rates (LLM conditions 87.5%–100%, TypeSafe **90.8%**); reports **"TypeSafe flips on 2 of
  the 8 questions"**; with a 0.60 top-probability gate, TypeSafe agreement rises to **99.2%** with
  automatic labels on **74.2%** of answers.

---

## Tier 2 — Official product pages

| Source ID | Title | URL | Accessed (UTC) | Scope | SHA-256 (retrieved body) |
|---|---|---|---|---|---|
| TS-SITE-HOME | TypeSafe AI home page | https://typesafe.ai/ | 2026-09-22T13:2xZ | Product marketing + FAQ | `f4c726c5d209df1c5d870913172c32d0d40bedf9d57d64179cdd8ca2e4f45d93` |
| TS-SITE-MANIFESTO | Manifesto | https://typesafe.ai/manifesto | 2026-09-22T13:2xZ | Research positioning | `ec6df20a0e29f10f10cc090b62f29b54aca2c1de708bcc4a2e3fb3d44da29ef1` |

### What TS-SITE-HOME asserts

- Headline performance claim: **"193.6x Faster, 444.6x Cheaper."** with the qualifier
  *"based on workflows for System One tasks (proof)"*.
- A side-by-side demo pair: TypeSafe **$0.000081, 0.114s** vs LLMs **$0.013880, 8.566s**.
- **"Zero Hallucinations"**.
- **"$42 Per Billion input tokens"**, and **"238x Lower input price than Claude Fable 5.1"**.
- "Every Jev decision comes with a confidence estimate, so your software can act when confidence
  is high and escalate when it is not."
- Describes Jev as "more like code: reliable, fast, self-consistent, and type-safe".
- FAQ question titles are present in the static payload, including **"Is Jev deterministic?"**,
  "Is Jev just a smaller LLM?", "Can Jev still get things wrong?", "Are these prices temporary or
  subsidized?", "What is Jev good at? Where does it struggle?".

> **Retrieval limitation (recorded, not worked around).** The home page FAQ **answers** are not
> present in the statically fetched payload — the accordion bodies are client-side rendered and the
> closed state is what the server returns. Only question titles were recoverable. The answer to
> "Is Jev deterministic?" therefore **could not be read during this audit from the home page**.
> Whether TypeSafe states a determinism position anywhere official is resolved from Tier 1 docs
> instead (see TS-DOC-JAG and TS-DOC-MODELS), not guessed.

### What TS-SITE-MANIFESTO asserts

Research-positioning narrative, **not** a capability claim about Jev. Its thesis: the bottleneck is
not raw intelligence but that "today's intelligence is hard to build on"; current AI is trained to
be a helpful assistant, which presumes a human on the other side of the model, whereas software is
"built out of simple logic and layered abstractions, with every branch auditable". Includes the
"horseless carriage" argument that new technology is first forced into the shape of what it
replaces. Recorded here because it is the origin of the "more like code / auditable branches"
framing that reappears as a product claim on TS-SITE-HOME — but the manifesto itself does not
claim any measurable property of Jev.

### What TS-BLOG-BITTEREST asserts

Position essay on ML methodology, not a Jev claim. Argues "doing the right task > data > compute >
algorithms", with InstructGPT/RLHF as the worked example. Relevant only as context for why TypeSafe
frames its own evaluation around workflows rather than benchmark leaderboards. No Jev capability,
version, price, or performance statement appears in it.

### What TS-BLOG-TOOGOOD asserts — **not recovered**

**Retrieval limitation.** The post body is client-rendered and was not present in the fetched
payload; only the page shell and navigation were returned. The one-line summary carried on
TS-SITE-HOME's blog list is "RLHF-trained language models please humans and assist rather than make
reliable autonomous decisions. What comes next?" — recorded as an index-level blurb only.
**No claim in the companion audit file rests on this source.**

---

## Tier 3 — Official blog

| Source ID | Title | Publication date | URL | Accessed (UTC) | SHA-256 (retrieved body) |
|---|---|---|---|---|---|
| TS-BLOG-INTRO | Introducing System One Models & Jev | **Sep 15, 2026** | https://typesafe.ai/blog/introducing-system-one-models-and-jev | 2026-09-22T13:2xZ | `19a428f4d388bb5f218cdb950f11d28d67677e887c01a753010258c621c5cb27` |
| TS-BLOG-ANTIBENCH | Lies, Damned Lies, and Benchmarks | **Sep 11, 2026** | https://typesafe.ai/blog/antibenchmaxxing | 2026-09-22T13:2xZ | `4447e3953ab9f72816288cdf6c0cf6b1e3aa5e9b9e71b02479f3484b193a4412` |
| TS-BLOG-BITTEREST | The Bitterest Lesson | (not recovered) | https://typesafe.ai/blog/bitterest-lesson | 2026-09-22T13:2xZ | `00cd7b580cd95941eaeb59a467270a6af56ea7000fff3e712831ee68873dea8e` |
| TS-BLOG-TOOGOOD | AI: too good to be true, too bad to be useful | (not recovered) | https://typesafe.ai/blog/ai-too-good-to-be-true-too-bad-to-be-useful-typesafe-ai | 2026-09-22T13:2xZ | `80e9928f6dce2dd71f56d97055ffc955836a12aa5d10d1e2b2947272628a11f1` |

### What TS-BLOG-INTRO asserts

This is the flagship launch post (author: Diogo Almeida, founder) and the densest single source of
product-level claims. It is presented partly as a claim table, partly as explicit hedging.

**Model identity**

- Jev is the first TypeSafe model in a new class called System One Models, "built to make fast,
  structured decisions that software can use directly".
- "Think of Jev as a frontier-intelligence function call: unstructured state in, typed
  probabilistic decisions out."
- Claims Jev "achieves similar levels of intelligence on System One tasks compared to existing
  LLMs, while being two orders of magnitude faster and more efficient."

**Output semantics / type safety**

- LLM row: outputs are strings, which "need to be parsed + validated", and there is "always some
  risk that the AI goes off the rails".
- System One row: "Type-safe structured values. Possible outputs and structure are defined in
  advance. The model never makes type errors. All answers are accompanied with calibrated
  probabilities and confidence scores."

**Hallucination**

- "While Jev gives up string generation, it's optimized for structured outputs and **can't
  hallucinate**."
- In its own Nuance section the post scopes this to schema conformance and says so directly:
  "Our number is not empirical. Schema matching is guaranteed, thus we can confidently add 0% into
  the plots." The accompanying LLM numbers are attributed to OpenRouter with an acknowledged
  sampling bias. The post's framing line is "Hallucination and type-safety are intrinsically
  related".

**Sampling / parallelism**

- LLM sampling is described as "Sequential… one token at a time"; System One sampling as
  "Parallel. Generates all outputs in a single query."

**Confidence / calibration**

- LLM row: models "tend to be overconfident and inconsistent"; "If a model can do a task 95% of
  the time but doesn't say when it's in the 5%, it can't automate that task."
- System One row: "Always communicates confidence and uncertainty with every output. **Calibrated:
  higher confidence means higher accuracy. More consistent: returns similar answers for similar
  inputs.**"

**Cost**

- "Input tokens: $0.042 / MTok ($42 per billion tokens). Output tokens: FREE (too cheap to meter)."

**Speed**

- "End-to-end response time is **70ms-500ms** for TypeSafe. This can range from **40x-200x faster**
  for the same levels of frontier intelligence for System One shaped queries."
- The post's own receipt for the headline numbers: "This is where the claims of **193.6x faster,
  444.6x cheaper** on our home page comes from, and we expect that these are on the higher end of
  real world gains." It also discloses that the workflows were built by the model capabilities
  team ("some bias could exist") and that the reference answers average GPT-6 Astra and Fable 5.1,
  which "biases answers towards OpenAI and Anthropic's models".

**Workflow evaluation methodology**

- Reference probabilities are the average of the largest/most expensive external models, with the
  same fixed compute graph (workflow) for every model — explicitly to avoid harness engineering
  and ground-truth overfitting.

**Cardinality**

- "Jev supports a cardinality up to 255." For higher-cardinality choices the demos use a two-stage
  score-then-choose system.

**Verifiability framing**

- The post separates claims it calls easily falsifiable ("Speed per call", "Cost per call",
  "No type errors") from "our bolder claims", for which it supplies Nuance sections. It volunteers
  that its published evals "are generally run from our laptops on the West Coast", and that it
  "can't prove it isn't subsidized" regarding pricing.

**Not recovered:** the post's FAQ answers (Why was a new training algorithm needed? Is Jev just a
smaller LLM? How does Jev perform against public benchmarks? etc.) are again client-rendered and
were not present in the fetched payload. Only the question titles were recoverable.

### What TS-BLOG-ANTIBENCH asserts

Methodology/position piece, not a Jev capability claim. Its relevant assertions for this audit:

- Benchmarks get "benchmaxxed" when builders can optimize against a public score.
- TypeSafe's stated policy: **"no standard benchmark table in our model releases"**, new evals to be
  "dated snapshots and immediately retired once posted rather than hill-climbed", and publication
  of caveats and "evidence that looks bad for us".
- Advises users to "run your own private evals, treat public ones with a grain of salt".

This is directly relevant to how this repository should frame its own numbers, and it is an
official statement of the vendor's own epistemic stance.

---

## Recorded source-internal divergences

Divergences are recorded, not resolved. Per the P1 rules, no third-party source is used to
adjudicate, and the wording is not "unified".

### D-1 — Parallel-questions multiplier: 12.2x/10.0x vs 11.5x/9.6x

The same cookbook is summarized with two different pairs of multipliers, in two official places,
on the same retrieval day.

| Location | Wording |
|---|---|
| TS-DOC-CB-PAR (cookbook body) and TS-IDX (`llms.txt` summary) | "batching every question into one TypeSafe call is **12.2x cheaper and 10.0x faster** with no change in answers", backed in the body by a table `$0.000497 / 0.27s` vs `$0.006090 / 2.71s` |
| TS-DOC-PRIM (`primitives.md`, "Ask speculative questions") | "batching 13 questions into one call is **11.5x cheaper and 9.6x faster** than 13 separate calls, with no change in the answers" |

Classification: **docs precision difference / drift between a derived summary and the page that
produces it.** The cookbook body's own printed table is internally consistent with 12.2x/10.0x
(`0.006090/0.000497 = 12.25`; `2.71/0.27 = 10.04`). The `primitives.md` figure is the outlier
relative to that table. Both are official; both are recorded. This audit does **not** treat the
`primitives.md` number as authoritative over the cookbook that computes it, nor vice versa — it
records that the vendor's own two surfaces disagree and that any citation of "the" official
batching multiplier must name which page it came from.

### D-2 — Confidence thresholds for the same worked example

Two official pages use the same voice-banking example with different demonstration thresholds:

| Location | Wording |
|---|---|
| TS-DOC-CONF | "If `confidence < 0.5`: Model is genuinely unsure. Don't guess." then `confidence > 0.9` to execute a transfer |
| TS-DOC-CONFROUTE | "The **0.6 floor** catches anything the model is genuinely uncertain about… approving a transfer requires very high confidence (**>0.85**)" |

Classification: **demonstration-parameter difference between two pages, not a contradiction.**
Both pages state that thresholds are domain-specific and must be tuned; TS-DOC-CONF says so
explicitly. Recorded because a reader could otherwise mistake either constant for a product
default. This repository's own 0.60 gate in experiment `04_confidence` coincides numerically with
the TS-DOC-CONFROUTE floor and the 0.60 gate in TS-DOC-CB-CC — three independent occurrences of a
"0.6" in this material, none of which is a calibrated default.

### D-3 — Terminology for the Score aggregate

TS-DOC-SCORE defines `score` as "the probability-weighted mean of the level numbers". TS-DOC-JAG
refers to score outputs as "(e.g., **expectations** and probability)". Both refer to the same
returned aggregate. Classification: **terminology looseness across pages**, not a semantic
conflict.

### D-4 — Headline speed/cost multipliers vs their own scoping

TS-SITE-HOME states "193.6x Faster, 444.6x Cheaper" with a footnote qualifier; TS-BLOG-INTRO
states the same numbers and adds that they come from four published workflows built by the model
capabilities team, are "on the higher end of real world gains", and are measured against a
reference answer averaged from two specific frontier models. Classification: **marketing
simplification vs docs/blog precision** — a layered claim, not an inconsistency, but the
qualifiers are load-bearing and must travel with the number.

### D-5 — "Can't hallucinate" vs "schema matching is guaranteed"

TS-BLOG-INTRO uses the phrase "can't hallucinate" in its main claim body and then, in its own
Nuance section, restates the underlying support as *schema matching* being guaranteed and labels
the figure "not empirical". Classification: **register difference within a single source.**
The strong phrase is not retracted, but the source itself supplies the narrower mechanism. This is
material to how "hallucination" should be scoped in any downstream writeup.

---

## Sources deliberately NOT used

- **Third-party blog posts, leaderboards, aggregators, or review sites** — excluded by the P1
  source hierarchy. Where official pages cite third parties (e.g. the home page's comparison to
  another vendor's list price, the launch post's OpenRouter LLM numbers), the third-party figure is
  recorded only as *what TypeSafe asserted about it*, never as an independent measurement.
- **This repository's own README** — it is a local artifact, not a TypeSafe source, even where it
  paraphrases TypeSafe material. Anything in it that resembles an official claim is re-verified
  against the live pages above for this audit.
- **The TypeSafe inference API** — read-only public pages only. No inference call was made.

---

## Freshness and drift policy for future audits

- Every claim in the companion audit file cites a Source ID resolvable in this file.
- If a page's retrieved hash changes materially on re-fetch, re-read it before reusing any claim.
- Claims from TS-DOC-JAG and TS-DOC-CB-* carry an extra caveat: they are scoped to `jev-1.13` /
  `jev-latest`-as-sampled, and both the jaggedness page and the models page anticipate change
  ("Many of these will be fixed in later versions"; aliases move).
- The `Accessed` column is the audit's own timestamp. Any claim below is only asserted **as of that
  retrieval**, not as a permanent property of TypeSafe's product.

---

## Re-verification log

### R-1 — P2 re-fetch, 2026-09-22

Before any P2 classification resting on a Tier-1 page, **every Tier-1 body in the table above was
re-fetched and re-hashed**: 27 page bodies plus `llms.txt` (28 bodies total). All 28 SHA-256 values
matched the ones recorded at P1, so **no official Tier-1 page is assumed to have drifted between P1
and P2**. No Tier-2 or Tier-3 source was re-fetched during P2.

This matters for how a P2 verdict may be read: a P2 judgment that a candidate is
`N0_OFFICIALLY_DOCUMENTED` is made against the *same text* P1 audited, not against a page that may
have been edited since. It does not extend the sources' validity beyond 2026-09-22, and it says
nothing about pages that were never retrievable (the home-page and launch-post FAQ bodies) or about
page content that changes without changing the retrieved body.

Retrieval method: direct HTTPS `GET` of the public `*.md` page paths and `llms.txt`. **No TypeSafe
inference endpoint was called, and no API key was read, during the P2 re-fetch or at any point in
P2.**
