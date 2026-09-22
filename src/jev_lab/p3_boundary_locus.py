"""P3 — a minimal, preregistered replication that tries to attribute one boundary effect.

`07_instruction_precision` moved a byte-identical state's Noul from 0.75 to 0.20 by changing the
*instruction* and the *criteria* together. That design cannot say which of the two fields carried
the move, and the repository records that limit in `docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md`.
P3 is the smallest experiment that can answer it: the same 82-byte state and the same two
boundary texts, crossed 2x2, three repeats per arm, twelve logical calls and no more.

What this module is deliberately *not*:

* it is not registered in `EXPERIMENTS`. The fifteen-experiment registry feeds the frozen final
  report and the backlog, and adding a sixteenth member would change the meaning of both. P3 keeps
  its own log, its own entry point, and its own result document.
* it does not write to `results/usage.jsonl`. The 42 records there are frozen historical evidence;
  appending to them would invalidate a published SHA-256. P3 records into
  ``results/p3_boundary_locus/`` instead.
* it does not invent wording. All four arms are assembled from the exact strings the 07 experiment
  already used, and `tests/test_p3_boundary_locus.py` asserts object-level equality against the
  live registry rather than trusting the copy below to stay in step.

The design, the statistics, the thresholds, and the analysis rule are frozen in
`docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md` and are reproduced here as constants. A
number in this file that disagrees with that document is a bug, not a new decision.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typesafe_sdk import Noul, NoulCriteria, TypeSafeAuthenticationError, TypeSafeError

from .client import (
    MissingApiKeyError,
    SecretFileError,
    TransportProbe,
    open_client,
    require_api_key,
    scrub_secrets,
)
from .experiments import EXTENDED, Case, Experiment, noul_of, run_experiment
from .recorder import CallRecord, UsageRecorder, read_records

# --------------------------------------------------------------------------------------
# Frozen identity
# --------------------------------------------------------------------------------------

PREREGISTRATION_ID = "P3_BOUNDARY_LOCUS_V1"
EXPERIMENT_NAME = "P3_boundary_locus"
P3_QUESTION = "P3-Q1"

# The question name is the same one 07 used, so the answer lands under the same key.
QUESTION_NAME = "blocked"

# The model is named explicitly rather than left to the `jev-latest` alias. The 42 frozen records
# all resolved to this version, and an alias is free to move; a comparison against them is only
# meaningful if the same version answered. A response that resolves elsewhere stops the run.
P3_MODEL = "jev-1.13.0"

# The P3 log is a second canonical measurement, not a view over the first. Relative to the
# repository root, so the same directory is used from any working directory.
P3_RESULTS_DIR = Path("results") / "p3_boundary_locus"

# Hard ceiling. Twelve logical positions, and a failure consumes the position rather than buying
# another one.
MAX_LOGICAL_CALLS = 12
REPEATS_PER_ARM = 3

# --------------------------------------------------------------------------------------
# Frozen payload: the state and the two boundary texts, byte-identical to `07_instruction_precision`
# --------------------------------------------------------------------------------------

P3_STATE = "The report export spun for ten minutes and never finished. I gave up and used CSV."

VAGUE_INSTRUCTIONS = "Is this a serious issue?"
VAGUE_CRITERIA_TRUE = "Something went wrong for the user"
VAGUE_CRITERIA_FALSE = "Nothing went wrong for the user"

EXPLICIT_INSTRUCTIONS = (
    "Does the state describe a situation where a primary requested capability could not "
    "complete, and no equivalent within-feature workaround allowed completion?"
)
EXPLICIT_CRITERIA_TRUE = (
    "A primary requested capability could not complete, and no equivalent within-feature "
    "workaround allowed completion"
)
EXPLICIT_CRITERIA_FALSE = (
    "The capability completed, or an equivalent within-feature workaround allowed completion, "
    "or no failure is described"
)

# The two factors. Every arm is one cell of this 2x2, and the payload is identical across arms
# except for these two fields.
VAGUE = "vague"
EXPLICIT = "explicit"

# Arm -> (instruction specificity, criteria specificity).
ARM_SPECIFICITY: dict[str, tuple[str, str]] = {
    "N": (VAGUE, VAGUE),        # NEITHER     -- the 07 vague arm, verbatim
    "I": (EXPLICIT, VAGUE),     # INSTRUCTION_ONLY
    "C": (VAGUE, EXPLICIT),     # CRITERIA_ONLY
    "B": (EXPLICIT, EXPLICIT),  # BOTH        -- the 07 explicit arm, verbatim
}

ARMS: tuple[str, ...] = ("N", "I", "C", "B")

ARM_LABELS: dict[str, str] = {
    "N": "NEITHER",
    "I": "INSTRUCTION_ONLY",
    "C": "CRITERIA_ONLY",
    "B": "BOTH",
}

# Frozen running order: three counterbalanced rounds, so no arm sits in the same position every
# round. P3 makes no latency claim, so this controls the coarsest arm/position confound only and is
# not a substrate measurement.
ROUNDS: tuple[tuple[str, ...], ...] = (
    ("N", "I", "C", "B"),
    ("B", "C", "I", "N"),
    ("C", "N", "B", "I"),
)

# --------------------------------------------------------------------------------------
# Frozen decision constants
# --------------------------------------------------------------------------------------

# The 07 measurement these arms are compared against: one local run on 2026-09-21, two arms, one
# call each. A single observation per arm, not a stable estimate -- which is why P3 repeats.
OBSERVED_07_VAGUE = 0.75
OBSERVED_07_EXPLICIT = 0.20
OBSERVED_07_MOVE = OBSERVED_07_VAGUE - OBSERVED_07_EXPLICIT  # 0.55

# GO-1: a single-field arm reproduces at least 50% of the observed move, in the same direction.
GO1_RECOVERY_FRACTION = 0.50
GO1_MEDIAN_AT_MOST = round(OBSERVED_07_VAGUE - GO1_RECOVERY_FRACTION * OBSERVED_07_MOVE, 4)  # 0.475
# GO-2: the other single-field arm moves no more than 20% of that same move off the vague baseline,
# which is a band of +/- 0.11 around 0.75 -- not 20% of 0.75.
GO2_BAND_HALF_WIDTH = round(0.20 * OBSERVED_07_MOVE, 4)  # 0.11
GO2_MEDIAN_AT_LEAST = round(OBSERVED_07_VAGUE - GO2_BAND_HALF_WIDTH, 4)  # 0.64
GO2_MEDIAN_AT_MOST = round(OBSERVED_07_VAGUE + GO2_BAND_HALF_WIDTH, 4)  # 0.86
# GO-3: both single-field arms repeat tightly enough to be worth comparing at all.
GO3_SPREAD_AT_MOST = 0.05

# K1: the two single-field arms are too close together to have different causes.
K1_MIN_SEPARATION = 0.10

# Endpoint validity guard. E1 restates the original ordering; E2 requires the endpoint gap to still
# carry at least half the original effect, on the same 50% bar GO-1 uses. Both can only block a
# claim -- neither can produce one.
E1_REQUIRES = "N_med > B_med"
E2_MIN_ENDPOINT_GAP = round(0.50 * OBSERVED_07_MOVE, 4)  # 0.275

# Verdicts. Exactly these, and no partial-credit variant between them.
GO_LOCAL_LOCUS_SIGNAL = "P3_GO_LOCAL_LOCUS_SIGNAL"
KILL_NO_SINGLE_FIELD_ATTRIBUTION = "P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION"
ATTRIBUTION_NOT_INTERPRETABLE = "P3_ATTRIBUTION_NOT_INTERPRETABLE"
INCONCLUSIVE_AND_STOP = "P3_INCONCLUSIVE_AND_STOP"
DESIGN_INVALIDATED_BEFORE_SPEND = "P3_DESIGN_INVALIDATED_BEFORE_SPEND"
MODEL_VERSION_MISMATCH = "P3_MODEL_VERSION_MISMATCH"
EXECUTION_INCOMPLETE = "P3_EXECUTION_INCOMPLETE"

# Comparisons run on values rounded to this many decimals, so a value that lands exactly on a
# threshold behaves the same way every time instead of depending on binary-float representation.
COMPARISON_DECIMALS = 4

# The single-field arm whose median is expected to move, when there is a signal. Named here only so
# the analysis can say which arm moved, in either direction; it is not a prediction.
SINGLE_FIELD_ARMS: tuple[str, ...] = ("I", "C")


class ModelVersionMismatch(RuntimeError):
    """A response resolved to a model other than the one this experiment fixed in advance.

    Raised from inside the run loop, so the remaining positions are never spent: the comparison
    against the frozen 07 records is only meaningful at one version.
    """


class P3LogNotEmpty(RuntimeError):
    """The P3 log already holds records, so a fresh preregistered run would not be a fresh run."""


# --------------------------------------------------------------------------------------
# Frozen twelve-position sequence
# --------------------------------------------------------------------------------------


def frozen_sequence() -> list[tuple[str, int, int]]:
    """The twelve ``(arm, repeat, sequence_index)`` positions, in the order they will be run."""
    sequence: list[tuple[str, int, int]] = []
    for round_cases in ROUNDS:
        for arm in round_cases:
            repeat = sum(1 for existing, _, _ in sequence if existing == arm) + 1
            sequence.append((arm, repeat, len(sequence)))
    return sequence


def _criteria(instruction_specificity: str, criteria_specificity: str) -> NoulCriteria:
    """Build the criteria for one arm from the two frozen boundary texts."""
    if criteria_specificity == VAGUE:
        return NoulCriteria(true=VAGUE_CRITERIA_TRUE, false=VAGUE_CRITERIA_FALSE)
    return NoulCriteria(true=EXPLICIT_CRITERIA_TRUE, false=EXPLICIT_CRITERIA_FALSE)


def _instructions(instruction_specificity: str) -> str:
    """The instruction for one arm, chosen from the two frozen boundary texts."""
    return VAGUE_INSTRUCTIONS if instruction_specificity == VAGUE else EXPLICIT_INSTRUCTIONS


def arm_question(arm: str) -> Noul:
    """The exact question one arm sends. Built fresh so two arms cannot share mutable state."""
    instruction_specificity, criteria_specificity = ARM_SPECIFICITY[arm]
    return Noul(
        instructions=_instructions(instruction_specificity),
        criteria=_criteria(instruction_specificity, criteria_specificity),
    )


def p3_cases() -> list[Case]:
    """The twelve cases, in the frozen order, each carrying its arm identity in its notes."""
    cases: list[Case] = []
    for arm, repeat, sequence_index in frozen_sequence():
        instruction_specificity, criteria_specificity = ARM_SPECIFICITY[arm]
        cases.append(
            Case(
                case_id=f"{arm}_r{repeat}",
                state=P3_STATE,
                questions={QUESTION_NAME: arm_question(arm)},
                notes={
                    "p3_question": P3_QUESTION,
                    "arm": arm,
                    "arm_label": ARM_LABELS[arm],
                    "repeat": repeat,
                    "instruction_specificity": instruction_specificity,
                    "criteria_specificity": criteria_specificity,
                    "sequence_index": sequence_index,
                    "preregistration_id": PREREGISTRATION_ID,
                },
            )
        )
    return cases


def experiment() -> Experiment:
    """The P3 experiment object, handed to the shared runner.

    It is built on demand rather than held as a module global, and it is never added to
    `EXPERIMENTS`: the registry is what the frozen final report reads, and P3 must not change what
    those fifteen experiments mean.
    """
    return Experiment(
        name=EXPERIMENT_NAME,
        tier=EXTENDED,
        intent="Attribute the 07 boundary move to one field, or record that this sample cannot.",
        build_cases=p3_cases,
    )


# --------------------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmResult:
    """One arm's three Noul values and the statistics the preregistration fixed in advance."""

    arm: str
    label: str
    instruction_specificity: str
    criteria_specificity: str
    values: tuple[float, ...]
    median: float | None
    spread: float | None
    usable: int

    @property
    def complete(self) -> bool:
        """Whether the arm has as many usable values as the design called for."""
        return self.usable == REPEATS_PER_ARM


@dataclass(frozen=True)
class P3Analysis:
    """Everything the pre-registered decision rule reads, and nothing it does not."""

    records: int
    arms: dict[str, ArmResult]
    separation: float | None
    go1: bool
    go2: bool
    go3: bool
    k1: bool
    k2: bool
    k2_arms: tuple[str, ...]
    e1: bool
    e2: bool
    endpoint_gap: float | None
    moved_arm: str | None
    flat_arm: str | None
    verdict: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def go(self) -> bool:
        """All three GO conditions, which is the only way the GO verdict is reached."""
        return self.go1 and self.go2 and self.go3

    @property
    def kill(self) -> bool:
        """Either KILL condition."""
        return self.k1 or self.k2


def rounded(value: float) -> float:
    """Round a statistic for comparison and display, so a boundary value behaves deterministically."""
    return round(value, COMPARISON_DECIMALS)


def arm_statistics(arm: str, values: Sequence[float]) -> ArmResult:
    """Median and spread for one arm's raw values.

    Median rather than mean: with three repeats the median is one of the three actual observations,
    so an arm's central value is always a value the API really returned. The spread is the full
    range, reported alongside the raw values rather than instead of them.
    """
    instruction_specificity, criteria_specificity = ARM_SPECIFICITY[arm]
    if len(values) != REPEATS_PER_ARM:
        return ArmResult(
            arm=arm,
            label=ARM_LABELS[arm],
            instruction_specificity=instruction_specificity,
            criteria_specificity=criteria_specificity,
            values=tuple(values),
            median=None,
            spread=None,
            usable=len(values),
        )
    ordered = sorted(values)
    return ArmResult(
        arm=arm,
        label=ARM_LABELS[arm],
        instruction_specificity=instruction_specificity,
        criteria_specificity=criteria_specificity,
        values=tuple(values),
        median=rounded(statistics.median(ordered)),
        spread=rounded(ordered[-1] - ordered[0]),
        usable=len(values),
    )


def noul_value(record: Mapping[str, Any]) -> float | None:
    """The Noul this record holds for the P3 question, or ``None`` when it holds no usable one.

    A failed call, a missing answer, and a non-numeric value all land on ``None``. None of them is
    a zero, and none of them is quietly replaced by another observation.
    """
    if record.get("status") != "ok":
        return None
    answer = (record.get("answers") or {}).get(QUESTION_NAME)
    if not isinstance(answer, Mapping):
        return None
    value = answer.get("noul")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def values_by_arm(records: Sequence[Mapping[str, Any]]) -> dict[str, list[float]]:
    """Collect usable Noul values per arm, ordered by the position each record ran in.

    Ordering is by ``sequence_index`` from the record's own notes, not by the order the lines happen
    to sit in the file, so a log that was appended to out of order still reports each arm's three
    values in run order.
    """
    positioned: dict[str, list[tuple[int, float]]] = {arm: [] for arm in ARMS}
    for index, record in enumerate(records):
        notes = record.get("notes") or {}
        arm = notes.get("arm")
        if arm not in positioned:
            continue
        value = noul_value(record)
        if value is None:
            continue
        sequence_index = notes.get("sequence_index")
        order = sequence_index if isinstance(sequence_index, int) else index
        positioned[arm].append((order, value))
    return {arm: [value for _, value in sorted(pairs)] for arm, pairs in positioned.items()}


def analyze(records: Sequence[Mapping[str, Any]]) -> P3Analysis:
    """Apply the frozen decision rule to a P3 log.

    Evaluation order is fixed in the preregistration, because a verdict has to be a function of the
    numbers and not of the order somebody happened to check things in:

    1. completeness -- every arm needs all three values, or there is nothing to compare;
    2. endpoint validity -- the N and B endpoints must still show the original effect;
    3. KILL conditions;
    4. GO conditions;
    5. otherwise inconclusive.
    """
    by_arm = values_by_arm(records)
    arms = {arm: arm_statistics(arm, by_arm[arm]) for arm in ARMS}
    notes: list[str] = []

    incomplete = [arm for arm in ARMS if not arms[arm].complete]
    if len(records) != MAX_LOGICAL_CALLS:
        notes.append(
            "the P3 log is empty; no run has been recorded"
            if not records
            else f"the log holds {len(records)} record(s) where the frozen sequence is "
            f"{MAX_LOGICAL_CALLS} positions; the run stopped early or something appended to it"
        )
    if incomplete:
        notes.append(
            "arm(s) "
            + ", ".join(f"{arm} ({arms[arm].usable}/{REPEATS_PER_ARM} usable)" for arm in incomplete)
            + " did not produce a full set of values"
        )
    if incomplete or len(records) != MAX_LOGICAL_CALLS:
        return P3Analysis(
            records=len(records),
            arms=arms,
            separation=None,
            go1=False,
            go2=False,
            go3=False,
            k1=False,
            k2=False,
            k2_arms=(),
            e1=False,
            e2=False,
            endpoint_gap=None,
            moved_arm=None,
            flat_arm=None,
            verdict=EXECUTION_INCOMPLETE,
            notes=tuple(notes),
        )

    i_median = arms["I"].median
    c_median = arms["C"].median
    assert i_median is not None and c_median is not None  # guaranteed by the completeness check
    separation = rounded(abs(i_median - c_median))

    n_median = arms["N"].median
    b_median = arms["B"].median
    assert n_median is not None and b_median is not None
    endpoint_gap = rounded(n_median - b_median)
    e1 = n_median > b_median
    e2 = endpoint_gap >= E2_MIN_ENDPOINT_GAP
    if not e1:
        notes.append(f"endpoint ordering is not preserved: N_med={n_median} is not above B_med={b_median}")
    if e1 and not e2:
        notes.append(
            f"endpoint gap {endpoint_gap} is below the {E2_MIN_ENDPOINT_GAP} the guard requires, "
            "so the arms are being compared against a baseline that no longer shows the effect"
        )

    # GO-1 / GO-2 are symmetric in the two single-field arms: whichever one moved, the other has to
    # have stayed near the vague baseline. Both assignments are tried, and the condition holds if
    # either does.
    moved_arm: str | None = None
    flat_arm: str | None = None
    for candidate in SINGLE_FIELD_ARMS:
        other = next(arm for arm in SINGLE_FIELD_ARMS if arm != candidate)
        moved = arms[candidate].median
        flat = arms[other].median
        assert moved is not None and flat is not None
        if moved <= GO1_MEDIAN_AT_MOST and GO2_MEDIAN_AT_LEAST <= flat <= GO2_MEDIAN_AT_MOST:
            moved_arm, flat_arm = candidate, other
            break

    go1 = moved_arm is not None
    go2 = moved_arm is not None
    go3 = all(arms[arm].spread is not None and arms[arm].spread <= GO3_SPREAD_AT_MOST for arm in SINGLE_FIELD_ARMS)
    if not go1:
        notes.append(
            f"neither single-field arm reached the GO-1 median of <= {GO1_MEDIAN_AT_MOST}: "
            f"I_med={i_median}, C_med={c_median}"
        )

    k1 = separation < K1_MIN_SEPARATION
    k2_arms = tuple(
        arm
        for arm in ARMS
        if arms[arm].spread is not None and arms[arm].spread > separation
    )
    k2 = bool(k2_arms)
    if k1:
        notes.append(f"|I_med - C_med| = {separation} is below the K1 separation of {K1_MIN_SEPARATION}")
    if k2:
        notes.append(
            "within-arm spread exceeds the between-arm separation of "
            f"{separation} for: " + ", ".join(f"{arm} ({arms[arm].spread})" for arm in k2_arms)
        )

    if not (e1 and e2):
        verdict = ATTRIBUTION_NOT_INTERPRETABLE
    elif k1 or k2:
        verdict = KILL_NO_SINGLE_FIELD_ATTRIBUTION
    elif go1 and go2 and go3:
        verdict = GO_LOCAL_LOCUS_SIGNAL
    else:
        verdict = INCONCLUSIVE_AND_STOP

    return P3Analysis(
        records=len(records),
        arms=arms,
        separation=separation,
        go1=go1,
        go2=go2,
        go3=go3,
        k1=k1,
        k2=k2,
        k2_arms=k2_arms,
        e1=e1,
        e2=e2,
        endpoint_gap=endpoint_gap,
        moved_arm=moved_arm,
        flat_arm=flat_arm,
        verdict=verdict,
        notes=tuple(notes),
    )


# --------------------------------------------------------------------------------------
# Report rendering
# --------------------------------------------------------------------------------------

RESULT_DOC_PATH = Path("docs") / "audits" / "P3_BOUNDARY_LOCUS_RESULT.md"

_VERDICT_SENTENCES: dict[str, str] = {
    GO_LOCAL_LOCUS_SIGNAL: (
        "On this one preregistered payload, one field-specific arm reproduced most of the original "
        "explicit-boundary shift while the other stayed near the vague baseline, under three "
        "repeats per arm."
    ),
    KILL_NO_SINGLE_FIELD_ATTRIBUTION: (
        "The original 0.55 effect could not be attributed to one field under this design and "
        "sample size."
    ),
    ATTRIBUTION_NOT_INTERPRETABLE: (
        "The N and B endpoints did not still carry the original effect, so no single-field arm can "
        "be compared against a meaningful baseline. This is a validity failure, not a result about "
        "Jev."
    ),
    INCONCLUSIVE_AND_STOP: (
        "The twelve values satisfy neither the GO nor the KILL conditions. This is a complete "
        "result: the design could not distinguish the two fields at this sample size, and no "
        "further calls were made."
    ),
    EXECUTION_INCOMPLETE: (
        "The log does not hold a complete set of values for every arm, so the decision rule was "
        "never evaluated. Nothing is claimed about Jev."
    ),
}


def _pass(value: bool) -> str:
    """PASS / FAIL, spelled the same way for every condition."""
    return "PASS" if value else "FAIL"


def render_report(analysis: P3Analysis, *, records: Sequence[Mapping[str, Any]] = ()) -> str:
    """Render the P3 result document from an analysis, mechanically.

    Every number below comes from `analyze`; nothing is transcribed by hand, so the document cannot
    drift from the log it describes. The section labels keep the four kinds of statement apart --
    what was fixed before the run, what the API returned, what this project computed from it, and
    what none of it can support.
    """
    lines: list[str] = [
        "# P3 — Boundary locus: instructions vs criteria",
        "",
        f"**Preregistration**: `{PREREGISTRATION_ID}`",
        f"**Payload**: the `07_instruction_precision` state, byte-identical",
        f"**Model requested**: `{P3_MODEL}`",
        f"**Primary verdict**: `{analysis.verdict}`",
        "",
        "> " + _VERDICT_SENTENCES.get(analysis.verdict, "See the decision table below."),
        "",
        "---",
        "",
        "## 1. Preregistered design",
        "",
        "Four arms, one 2x2 of the two fields, three repeats each, twelve logical calls. The design,",
        "the order, the statistics and every threshold were committed before the first request.",
        "",
        "| arm | label | instructions | criteria |",
        "| --- | ----- | ------------ | -------- |",
    ]
    for arm in ARMS:
        result = analysis.arms[arm]
        lines.append(
            f"| `{arm}` | {result.label} | {result.instruction_specificity} | {result.criteria_specificity} |"
        )
    lines += [
        "",
        "Fixed order: "
        + " → ".join(f"{arm}{repeat}" for arm, repeat, _ in frozen_sequence())
        + ".",
        "",
        "## 2. Local measurement",
        "",
        f"Records in `{p3_log_path().as_posix()}`: **{analysis.records}**.",
        "",
        "| arm | raw Noul values | median | range |",
        "| --- | --------------- | -----: | ----: |",
    ]
    for arm in ARMS:
        result = analysis.arms[arm]
        raw = ", ".join("n/a" if value is None else f"{value:g}" for value in result.values) or "—"
        median = "n/a" if result.median is None else f"{result.median:g}"
        spread = "n/a" if result.spread is None else f"{result.spread:g}"
        lines.append(f"| `{arm}` | {raw} | {median} | {spread} |")

    lines += [
        "",
        "All three raw values are reported for every arm; the median is a summary of them, not a",
        "replacement for them.",
        "",
        "## 3. Derived calculation — the pre-registered decision rule",
        "",
        "| condition | rule | value | outcome |",
        "| --------- | ---- | ----- | ------- |",
        f"| GO-1 | some single-field arm median ≤ {GO1_MEDIAN_AT_MOST} | moved arm: "
        f"{analysis.moved_arm or 'none'} | {_pass(analysis.go1)} |",
        f"| GO-2 | the other within [{GO2_MEDIAN_AT_LEAST}, {GO2_MEDIAN_AT_MOST}] | flat arm: "
        f"{analysis.flat_arm or 'none'} | {_pass(analysis.go2)} |",
        f"| GO-3 | both spreads ≤ {GO3_SPREAD_AT_MOST} | "
        + ", ".join(
            f"{arm}={analysis.arms[arm].spread}" for arm in SINGLE_FIELD_ARMS
        )
        + f" | {_pass(analysis.go3)} |",
        f"| K1 | \\|I_med − C_med\\| ≥ {K1_MIN_SEPARATION} | "
        f"{analysis.separation} | {_pass(not analysis.k1)} |",
        f"| K2 | every arm's spread ≤ \\|I_med − C_med\\| | tripped by: "
        + (", ".join(analysis.k2_arms) if analysis.k2_arms else "none")
        + f" | {_pass(not analysis.k2)} |",
        f"| E1 | N_med > B_med | {E1_REQUIRES} | {_pass(analysis.e1)} |",
        f"| E2 | endpoint gap ≥ {E2_MIN_ENDPOINT_GAP} | {analysis.endpoint_gap} | {_pass(analysis.e2)} |",
        "",
        "KILL is reported as PASS when it did *not* fire. E1 and E2 are validity guards: they can",
        "block a claim, and they can never produce one.",
        "",
        "## 4. Endpoint replication sanity check",
        "",
        "`N` and `B` are three-repeat versions of the two `07_instruction_precision` arms. They are",
        "diagnostic only, and were never available to adjust a threshold after the fact.",
        "",
        f"* original observation: vague **{OBSERVED_07_VAGUE:g}**, explicit **{OBSERVED_07_EXPLICIT:g}** "
        f"(move **{OBSERVED_07_MOVE:g}**)",
        f"* this run: N median **{analysis.arms['N'].median}**, B median **{analysis.arms['B'].median}**, "
        f"gap **{analysis.endpoint_gap}**",
        f"* ordering preserved (E1): {_pass(analysis.e1)}; gap ≥ half the original move (E2): {_pass(analysis.e2)}",
        "",
        "## 5. Conditions and notes",
        "",
    ]
    if analysis.notes:
        lines += [f"* {note}" for note in analysis.notes]
    else:
        lines.append("* No condition notes: nothing tripped.")
    lines += [
        "",
        "## 6. Limitation",
        "",
        "* This is **one payload**, measured on one account, in one session, at one model version.",
        "  It is a local measurement and supports no general statement about Jev.",
        "* The endpoints are a single three-repeat arm each. n=3 supports a median and a range, and",
        "  no interval estimate; no confidence interval is reported because the design cannot",
        "  support one.",
        "* `FIELD_ALIGNMENT_CAVEAT`: the crossed arms pair a broader field with a narrower one rather",
        "  than two independently varying definitions. A result here is a statement about *this*",
        "  mixed-specificity construction, not about where Jev \"stores\" a decision boundary.",
        "* This experiment measures no accuracy: neither the vague nor the explicit boundary is",
        "  ground truth, so no arm is \"correct\".",
    ]
    if records:
        lines.append("")
        lines.append(f"*(analysis rendered from {len(records)} log record(s))*")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------
# Running the twelve positions
# --------------------------------------------------------------------------------------


def p3_log_path(results_dir: Path | str = P3_RESULTS_DIR) -> Path:
    """Path to the P3 canonical log. Deliberately not the repository's frozen root log."""
    return Path(results_dir) / "usage.jsonl"


def assert_log_empty(path: Path) -> None:
    """Fail closed unless the P3 log is absent or empty.

    A rerun appended to an existing log would mix two executions into one median and quietly break
    the claim that these twelve values came from one preregistered sequence.
    """
    if path.exists() and path.stat().st_size > 0:
        raise P3LogNotEmpty(
            f"{path.as_posix()} already holds records; P3 runs once against a fresh log. "
            "Move the existing log aside rather than appending to it."
        )


def run(*, results_dir: Path | str = P3_RESULTS_DIR, echo=print) -> int:
    """Execute the frozen twelve-call sequence, writing one record per position.

    One client, one session, serial. A position that fails keeps its record and is not retried; a
    response that resolves to a model other than ``P3_MODEL`` stops the run where it is.
    """
    log = p3_log_path(results_dir)
    assert_log_empty(log)

    try:
        require_api_key()
    except (MissingApiKeyError, SecretFileError) as error:
        echo(scrub_secrets(str(error)))
        return 2

    plan = frozen_sequence()
    if len(plan) != MAX_LOGICAL_CALLS:
        raise AssertionError(f"frozen sequence has {len(plan)} positions, expected {MAX_LOGICAL_CALLS}")

    echo(f"P3 {PREREGISTRATION_ID}: {len(plan)} logical calls, model={P3_MODEL}")
    echo("  " + " -> ".join(f"{arm}{repeat}" for arm, repeat, _ in plan))

    recorder = UsageRecorder(results_dir)
    probe = TransportProbe()
    stopped: str | None = None

    def on_case(case: Case, record: CallRecord, response: Any) -> None:
        nonlocal stopped
        value = noul_of(response, QUESTION_NAME)
        echo(
            f"  [{record.case_sequence_index}] {case.case_id:<6} "
            f"noul={value if value is not None else 'n/a'} "
            f"resolved={record.model_resolved or 'n/a'} attempts={record.transport_attempt_count}"
        )
        # A version that is not the frozen one invalidates the comparison against the 07 records, so
        # the remaining positions are not spent. The calls already made stay in the log.
        if record.model_resolved != P3_MODEL:
            stopped = record.model_resolved
            raise ModelVersionMismatch(
                f"response resolved to {record.model_resolved!r}, expected {P3_MODEL!r}; "
                "stopping before the remaining positions are spent"
            )

    def on_error(case: Case, error: Exception) -> None:
        echo(f"  {case.case_id} FAILED: {type(error).__name__}: {scrub_secrets(str(error))}")

    try:
        with open_client(model=P3_MODEL, probe=probe) as client:
            run_experiment(
                experiment(),
                client=client,
                recorder=recorder,
                model=P3_MODEL,
                max_requests=MAX_LOGICAL_CALLS,
                on_case=on_case,
                on_error=on_error,
                probe=probe,
            )
    except (MissingApiKeyError, SecretFileError) as error:
        echo(scrub_secrets(str(error)))
        return 2
    except TypeSafeAuthenticationError as error:
        echo(f"authentication failed: {scrub_secrets(str(error))}")
        return 2
    except ModelVersionMismatch as error:
        echo(f"\n{MODEL_VERSION_MISMATCH}: {error}")
    except TypeSafeError as error:
        echo(f"TypeSafe SDK error: {type(error).__name__}: {scrub_secrets(str(error))}")
        return 2

    records = list(read_records(log))
    echo(f"\nwrote {len(records)} record(s) to {log.as_posix()}")
    echo(f"run_id={recorder.run_id}")
    echo(f"client_session_id={recorder.client_session_id}")
    if stopped is not None:
        echo(f"model resolved to {stopped}, not {P3_MODEL}: run stopped early")
    return 0


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------


def analyze_command(*, results_dir: Path | str = P3_RESULTS_DIR, echo=print) -> int:
    """Read the P3 log and print the frozen decision rule's outcome."""
    log = p3_log_path(results_dir)
    records = list(read_records(log))
    analysis = analyze(records)
    echo(f"records={analysis.records}")
    for arm in ARMS:
        result = analysis.arms[arm]
        echo(
            f"  {arm} ({result.label:<16}) values={list(result.values)} "
            f"median={result.median} spread={result.spread}"
        )
    echo(f"|I_med - C_med| = {analysis.separation}")
    echo(f"GO-1={analysis.go1} GO-2={analysis.go2} GO-3={analysis.go3}")
    echo(f"K1={analysis.k1} K2={analysis.k2} endpoint E1={analysis.e1} E2={analysis.e2}")
    for note in analysis.notes:
        echo(f"  - {note}")
    echo(f"verdict: {analysis.verdict}")
    return 0


def report_command(
    *,
    results_dir: Path | str = P3_RESULTS_DIR,
    report_path: Path = RESULT_DOC_PATH,
    echo=print,
) -> int:
    """Render the result document from the P3 log, mechanically."""
    records = list(read_records(p3_log_path(results_dir)))
    lines = [
        "<!-- Generated by `python -m jev_lab.p3_boundary_locus report` from the P3 log.",
        f"     Analyzer: {PREREGISTRATION_ID}. Do not hand-edit: the numbers are derived. -->",
        "",
    ]
    text = "\n".join(lines) + render_report(analyze(records), records=records)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(text, encoding="utf-8", newline="\n")
    echo(f"wrote {report_path.as_posix()}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m jev_lab.p3_boundary_locus {run,analyze,report}``."""
    parser = argparse.ArgumentParser(prog="jev_lab.p3_boundary_locus", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help=f"execute the frozen {MAX_LOGICAL_CALLS}-call sequence")
    sub.add_parser("analyze", help="apply the frozen decision rule to the P3 log")
    sub.add_parser("report", help="render the result document from the P3 log")
    args = parser.parse_args(argv)
    if args.command == "run":
        return run()
    if args.command == "analyze":
        return analyze_command()
    return report_command()


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
