# GitHub Release notes — `v0.1.1`

**Status: PUBLISHED.** This file is the repository copy of the body published in the GitHub Release `v0.1.1 — Publication Closure`. Post-public corrections must keep this copy and the Release object semantically aligned.

**Release title:** `v0.1.1 — Publication Closure`

---

## Published body

> ## `v0.1.1` — Publication Closure
>
> `v0.1.1` is the public-facing closure of `jev-testbench`: a lightweight Jev testbench built
> through Agentic Engineering, with its evidence trail, null result and bilingual technical blog
> kept intact.
>
> **This is not a new Jev scientific-evidence release.** Publication Closure made zero new Jev API
> calls, ran zero new experiments and rewrote zero measurements.
>
> ### The two releases mean different things
>
> - **`v0.1.0`** is the immutable historical evidence/software freeze. It was frozen under the
>   historical project name `jev-test` and remains bound to commit
>   `37ef2e425d5e9e534f856a7243be848ff17f0cbb`.
> - **`v0.1.1`** is the publication/presentation closure under the current project name
>   `jev-testbench`: project identity, public-facing documentation, Agentic Engineering/process
>   material and the human-approved bilingual blog.
> - Genuinely new Jev scientific evidence is reserved for **`v0.2.0` or later**.
>
> ### Scientific state carried forward unchanged
>
> ```text
> NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET
> P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION
> PUBLIC_NOVELTY_UNRESOLVED
> ```
>
> The canonical evidence is still exactly 42 core records plus 12 P3 records. The two published
> SHA-256 digests remain:
>
> ```text
> results/usage.jsonl
> 38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b
>
> results/p3_boundary_locus/usage.jsonl
> 17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e
> ```
>
> ### What Publication Closure adds
>
> - the current `jev-testbench` project identity without rewriting `v0.1.0` provenance;
> - a public-facing README and documentation index that keep the project explicitly outside the
>   benchmark / leaderboard / production-certification category;
> - the Agentic Engineering and cognitive-debt process record, kept separate from scientific
>   evidence;
> - the Chinese and English technical articles after human editorial approval;
> - publication-readiness, security/privacy, license, CI and reproducibility checks.
>
> ### Reproduce the public-facing release offline
>
> ```console
> git clone https://github.com/Charlie-Wang-03/jev-testbench.git
> cd jev-testbench
> git checkout v0.1.1
> uv sync --locked
> uv run pytest
> uv build
> uv run python -m jev_lab report
> uv run python -m jev_lab snapshot
> uv run python -m jev_lab final-report
> uv run python -m jev_lab.evidence_freeze verify v0.1.0
> ```
>
> The verifier deliberately targets `v0.1.0`: that tag is the scientific evidence anchor even when
> the public-facing project has moved on.
>
> ### Scope
>
> This project does not establish general Jev accuracy, calibration validity, model latency, a
> universal batching multiplier, determinism in either direction, or production safety. It is not a
> Jev benchmark or leaderboard. The preregistered P3 experiment returned a null attribution result,
> and that result remains part of the release rather than being repackaged.
>
> ### License and citation
>
> MIT. `CITATION.cff` in `v0.1.1` should identify the current `jev-testbench` publication release.
> The `CITATION.cff` stored inside the immutable `v0.1.0` tag remains the citation metadata for the
> historical evidence freeze.

---

## Executed release contract

The release commit carries `0.1.1` consistently in `pyproject.toml`, `uv.lock`,
`jev_lab.__version__` and `CITATION.cff`; its full offline CI passed before publication. The
annotated `v0.1.1` tag points at `22a211517b5133f1e8c67965f2a44054c342d8e5`, and the GitHub
Release is attached to that tag. `v0.1.0` remains unchanged.
