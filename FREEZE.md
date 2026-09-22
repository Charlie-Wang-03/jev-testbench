# Freeze

> **Scope note.** This file is the historical pointer to the **P0 core freeze** — the 42-record
> evaluation described below — and it is scoped to that freeze alone. The repository has since
> grown past it: P1 audited official claims, P2 triaged the findings for novelty, and P3 ran a
> preregistered replication in its own log. Those stages are **not** described here and did not
> alter anything below. For the complete lineage, see
> [docs/EVIDENCE_PROVENANCE.md](docs/EVIDENCE_PROVENANCE.md).

**`JEV_CORE_EXPLORATION_FROZEN`**

This repository holds a frozen local evaluation of TypeSafe's Jev model. The pointer below is
enough to identify the measurement; the full findings are in the report, which is derived from
the log rather than authored.

| | |
|---|---|
| canonical record | `results/usage.jsonl` |
| records | 42 |
| sha256 | `38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b` |
| resolved model | `jev-1.13.0` |
| real API requests | 42 |
| real-run experiments | 10 of 15 registered |
| derived report | `results/JEV_LOCAL_EVALUATION_FINAL.md` |

The canonical log is append-only. Nothing in it was rewritten, reordered, or deleted to reach this
freeze, and no threshold, state, or criterion was revised after a result was seen.

## What the freeze does not claim

These are retained boundaries, not open tasks:

- `ACTUAL_HANDLER_EXECUTION_UNTESTED` — every resolved route in `12_function_routing` was withheld
  by the frozen policy, so the allowed-handler branch was never entered under a live answer.
- `LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK` — latency is recorded, not benchmarked.
- No general accuracy or calibration claim. Expected labels are the design's intention, not
  independent ground truth.
- The optional edge-coverage backlog remains unrun: `00_model_info`, `08_literal_reading`,
  `09_numeric_limits`, `10_state_length`, `11_language_pair`.

## Secret policy

The API key is supplied by `TYPESAFE_API_KEY` in the environment, or by `.secrets/typesafe.env` in
this directory, and by nothing else.

**`.secrets/typesafe.env` is local-only and must never be committed.** It is git-ignored, it is
not tracked, and `git add --dry-run .` does not stage it. `.secrets.example/typesafe.env` is the
committed template and holds a placeholder only.

## Reading the log

`results/usage.jsonl` is the measurement; every other file under `results/` is a view rebuilt from
it by one of:

```console
uv run python -m jev_lab report        # summary.csv, summary.md
uv run python -m jev_lab snapshot      # capability_snapshot.md
uv run python -m jev_lab final-report  # JEV_LOCAL_EVALUATION_FINAL.md
```

None of them calls the API, and none of them writes to the log. The full command set, the record
schema, and the measurement ground rules are in
[docs/methodology/evaluation.md](docs/methodology/evaluation.md) and
[docs/guides/reproducibility.md](docs/guides/reproducibility.md).
