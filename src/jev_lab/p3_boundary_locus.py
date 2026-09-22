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
from collections.abc import Mapping, Sequence
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
    go1_arms: tuple[str, ...]
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
            go1_arms=(),
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

    # GO-1 and GO-2 are separate conditions in the preregistration (§9), and are computed
    # separately here. GO-1 is existential over the two single-field arms: one of them has to reach
    # the line, and which one is not part of the condition. GO-2 is the paired half -- *the other*
    # arm, the counterpart of an arm that itself satisfies GO-1, has to sit inside the
    # vague-baseline band. Both assignments are tried, in the frozen arm order.
    #
    # Reading both flags off one conjunction, as this analyzer used to, makes (GO-1 PASS,
    # GO-2 FAIL) unrepresentable -- and that is a real shape: both single-field arms can reach the
    # GO-1 line while neither leaves the other near the baseline. GO-2 implies GO-1 and never the
    # reverse, so the flag pairs that can occur are (T, T), (T, F) and (F, F).
    go1_arms = tuple(
        arm
        for arm in SINGLE_FIELD_ARMS
        if arms[arm].median is not None and arms[arm].median <= GO1_MEDIAN_AT_MOST
    )
    go1 = bool(go1_arms)

    moved_arm: str | None = None
    flat_arm: str | None = None
    for candidate in go1_arms:
        other = next(arm for arm in SINGLE_FIELD_ARMS if arm != candidate)
        flat = arms[other].median
        assert flat is not None  # guaranteed by the completeness check above
        if GO2_MEDIAN_AT_LEAST <= flat <= GO2_MEDIAN_AT_MOST:
            moved_arm, flat_arm = candidate, other
            break
    go2 = moved_arm is not None

    go3 = all(arms[arm].spread is not None and arms[arm].spread <= GO3_SPREAD_AT_MOST for arm in SINGLE_FIELD_ARMS)
    if not go1:
        notes.append(
            f"neither single-field arm reached the GO-1 median of <= {GO1_MEDIAN_AT_MOST}: "
            f"I_med={i_median}, C_med={c_median}"
        )
    elif not go2:
        # The failure the old conjunction could not describe, so the note is built from the arms
        # rather than from a fixed sentence: which arms qualified, and what their medians were.
        subject = (
            "both single-field arms satisfy"
            if len(go1_arms) == len(SINGLE_FIELD_ARMS)
            else f"{go1_arms[0]} is the only single-field arm that satisfies"
        )
        notes.append(
            f"{subject} GO-1 (median <= {GO1_MEDIAN_AT_MOST}): "
            + ", ".join(f"{arm}_med={arms[arm].median}" for arm in SINGLE_FIELD_ARMS)
            + "; GO-2 still fails, because no assignment of a GO-1 arm as the moved arm leaves its "
            f"counterpart inside the vague-baseline band "
            f"[{GO2_MEDIAN_AT_LEAST}, {GO2_MEDIAN_AT_MOST}]"
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
        go1_arms=go1_arms,
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

# The history of the analyzer that produced the analysis above. No log record can express this, so it
# is not derived from the measurement -- but it is emitted by the report generator all the same, so
# that the committed document stays byte-for-byte reproducible instead of being a generated file with
# a hand-appended tail. Commit C is named positionally rather than by SHA: a file cannot carry the
# hash of the commit that contains it, and any SHA written here would be wrong one commit later.
CORRECTION_PROVENANCE = """
---
## Post-run analyzer correction provenance

Everything above was rendered mechanically from `results/p3_boundary_locus/usage.jsonl` by the
corrected analyzer. This section records how the artifact reached that state. It is the one part of
this file that is not derived from the log, and no measurement changed while it was written.

**The sequence.**

* **Commit A** (`db7d06f`, *Preregister P3 boundary locus experiment*) froze the design, the payload,
  the thresholds, and the first version of this analyzer — before the first request was sent.
* **Commit B** (`c0fc9cc`, *Record P3 boundary locus measurements*) added the twelve measurements and
  disclosed, after the fact, a defect in that analyzer. The analysis those twelve calls produced is
  preserved unedited at that commit.
* **Commit C**, *Repair P3 analyzer against frozen preregistration* — the commit that carries this
  file — corrected the analyzer and re-rendered this document from the unchanged log. Commit C's own
  SHA is not written here because a file cannot name the commit that contains it; it is the third
  commit on this chain, and `git log --follow -- docs/audits/P3_BOUNDARY_LOCUS_RESULT.md` recovers it.

**The defect.** In `analyze()`, GO-1 and GO-2 — two separate conditions in the preregistration (§9) —
were evaluated as a single conjunction, and both flags were then read off that one result. The pair
`(GO-1 PASS, GO-2 FAIL)` was therefore unrepresentable, and on this data that is the pair the frozen
rule computes: both single-field arms reach the GO-1 line (`I_med = 0.31`, `C_med = 0.36`, against a
line of 0.475), while no assignment of either as the moved arm leaves its counterpart inside the
GO-2 band. The defect reported GO-1 as FAIL and printed the note *"neither single-field arm reached
the GO-1 median of <= 0.475"*, which this data contradicts. Section 3 above is the corrected
rendering; section 5 is the descriptive arithmetic that a hand-written audit addendum had carried,
now generated from the log instead.

**What did not change.**

* **No call was made** while correcting this, and none was rerun. The twelve records in
  `results/p3_boundary_locus/usage.jsonl` — their values, order, and SHA-256 — are identical before
  and after.
* **No threshold and no rule was altered.** The correction changes which flag the frozen rule
  computes, not what the rule is. The preregistration is byte-identical to Commit A.
* **The primary verdict is unchanged.** The original flags and the corrected flags both yield
  `P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`: the endpoint guards pass, K1 is evaluated before the GO
  block, and it fires. The only flag the correction moves is GO-1.
  `tests/test_p3_boundary_locus.py` asserts this invariance mechanically against the real log rather
  than leaving it as prose.

**Where the pre-correction artifact is.** Commit B holds the complete earlier rendering, including
the incorrect GO-1 row and the original audit addendum. It is recoverable from Git, not from this
file:

```console
git show c0fc9cc:docs/audits/P3_BOUNDARY_LOCUS_RESULT.md    # the 2026-09-22 analysis as recorded
git show c0fc9cc:src/jev_lab/p3_boundary_locus.py           # the analyzer that produced it
```

Nothing was amended, rebased, or force-pushed; both measurement commits are the ones originally
pushed.
"""

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
    """PASS / FAIL, for the GO conditions and the two endpoint guards."""
    return "PASS" if value else "FAIL"


def _kill(value: bool) -> str:
    """FIRES / CLEAR, for the KILL conditions, each of which is stated as a rule that fires."""
    return "FIRES" if value else "CLEAR"


# What a condition reads when the decision rule never reached it. Distinct from all three status
# vocabularies on purpose: a rule that was not evaluated did not pass, did not fail, and did not fire.
NOT_EVALUATED = "not evaluated"


def _assignment_trials(analysis: P3Analysis) -> str:
    """The pairings the GO rule tried, as ``moved X → counterpart Y=value``.

    GO-2 is only tried from an arm that already satisfies GO-1, so this is empty exactly when GO-1
    fails. Rendered from the arms rather than retyped, so it cannot disagree with the flags.
    """
    trials: list[str] = []
    for arm in analysis.go1_arms:
        other = next(candidate for candidate in SINGLE_FIELD_ARMS if candidate != arm)
        trials.append(f"moved {arm} → counterpart {other}={analysis.arms[other].median}")
    return "; ".join(trials) if trials else "no arm satisfies GO-1, so no pairing is tried"


def _assignment_summary(analysis: P3Analysis) -> str:
    """Which arm the GO path would have called moved, and which flat -- or why it named none."""
    if analysis.moved_arm is not None and analysis.flat_arm is not None:
        return f"GO assignment: moved `{analysis.moved_arm}`, flat `{analysis.flat_arm}`."
    if not analysis.go1_arms:
        return "GO assignment: none. No single-field arm satisfies GO-1."
    named = " and ".join(f"`{arm}`" for arm in analysis.go1_arms)
    verb = "satisfies" if len(analysis.go1_arms) == 1 else "satisfy"
    return (
        f"GO assignment: none. {named} {verb} GO-1, but no pairing of a GO-1 arm with a counterpart "
        "inside the GO-2 band exists."
    )


def _descriptive_context(analysis: P3Analysis) -> list[str]:
    """Arithmetic on the medians that describes what the twelve calls did.

    Deliberately outside the decision rule: these numbers were not available to it, no threshold was
    set from them, and the verdict is the same if they are ignored. They are rendered rather than
    written by hand so the document cannot drift from the log it describes.
    """
    gap = analysis.endpoint_gap
    baseline = analysis.arms["N"].median
    lines: list[str] = []
    if not gap or baseline is None:
        return lines
    for arm in SINGLE_FIELD_ARMS:
        median = analysis.arms[arm].median
        if median is None:
            continue
        recovery = round(100 * (baseline - median) / gap, 1)
        lines.append(
            f"* `{arm}_med={median:g}` sits {baseline - median:.2f} below `N_med={baseline:g}`, "
            f"recovering {recovery:.1f}% of this run's {gap:.2f} endpoint gap."
        )
    if analysis.separation is not None:
        lines.append(
            f"* the two single-field arms are {analysis.separation:.2f} apart, against a `N`-to-`B` "
            f"gap of {gap:.2f}."
        )
    return lines


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
        "**Payload**: the `07_instruction_precision` state, byte-identical",
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

    # Status cells for the decision table. A rule the analyzer never reached -- the only case being
    # a log too incomplete to evaluate at all -- has no PASS, FAIL, FIRES or CLEAR to report, and
    # saying "CLEAR" for a condition that was never read would be a false statement about the data.
    evaluated = analysis.verdict != EXECUTION_INCOMPLETE

    def status(rendered: str) -> str:
        return rendered if evaluated else NOT_EVALUATED

    go1_status = status(_pass(analysis.go1))
    go2_status = status(_pass(analysis.go2))
    go3_status = status(_pass(analysis.go3))
    k1_status = status(_kill(analysis.k1))
    k2_status = status(_kill(analysis.k2))
    e1_status = status(_pass(analysis.e1))
    e2_status = status(_pass(analysis.e2))

    largest_spread = max(
        (analysis.arms[arm].spread for arm in ARMS if analysis.arms[arm].spread is not None),
        default=None,
    )
    if analysis.k2_arms:
        k2_observed = "tripped by " + ", ".join(
            f"{arm}={analysis.arms[arm].spread}" for arm in analysis.k2_arms
        )
    elif evaluated and largest_spread is not None:
        k2_observed = f"largest spread {largest_spread:g} ≤ {analysis.separation}"
    else:
        k2_observed = "n/a"

    lines += [
        "",
        "All three raw values are reported for every arm; the median is a summary of them, not a",
        "replacement for them.",
        "",
        "## 3. Derived calculation — the pre-registered decision rule",
        "",
        "Each rule is stated in the direction the preregistration fixes it, and its status is",
        "reported in that rule's own vocabulary: the GO conditions and the two endpoint guards read",
        "PASS / FAIL, the KILL conditions read FIRES / CLEAR. A KILL condition is written as the rule",
        "that *fires*, never as its complement.",
        "",
        "| condition | rule | observed | status |",
        "| --------- | ---- | -------- | ------ |",
        f"| GO-1 | some single-field arm median ≤ {GO1_MEDIAN_AT_MOST} | "
        + ", ".join(f"{arm}_med={analysis.arms[arm].median}" for arm in SINGLE_FIELD_ARMS)
        + f" | {go1_status} |",
        f"| GO-2 | that arm's counterpart inside [{GO2_MEDIAN_AT_LEAST}, {GO2_MEDIAN_AT_MOST}] | "
        + _assignment_trials(analysis)
        + f" | {go2_status} |",
        f"| GO-3 | both single-field spreads ≤ {GO3_SPREAD_AT_MOST} | "
        + ", ".join(f"{arm}_spread={analysis.arms[arm].spread}" for arm in SINGLE_FIELD_ARMS)
        + f" | {go3_status} |",
        f"| K1 | \\|I_med − C_med\\| < {K1_MIN_SEPARATION} | {analysis.separation} | {k1_status} |",
        f"| K2 | any arm's spread > \\|I_med − C_med\\| | {k2_observed} | {k2_status} |",
        f"| E1 | N_med > B_med | "
        f"{analysis.arms['N'].median} > {analysis.arms['B'].median} | {e1_status} |",
        f"| E2 | N_med − B_med ≥ {E2_MIN_ENDPOINT_GAP} | {analysis.endpoint_gap} | {e2_status} |",
        "",
        _assignment_summary(analysis),
        "",
        "E1 and E2 are validity guards: they can block a claim, and they can never produce one.",
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
        f"* ordering preserved (E1): {e1_status}; gap ≥ half the original move (E2): {e2_status}",
        "",
        "## 5. Descriptive context — not part of the decision rule",
        "",
    ]
    lines += _descriptive_context(analysis) or [
        "* n/a — the log does not hold a complete set of values to describe."
    ]
    lines += [
        "",
        "These are arithmetic on the medians above, recorded because they describe what the twelve",
        "calls did. They are **not** inputs to the decision rule, no threshold was set from them, and",
        "the verdict is unchanged if they are ignored.",
        "",
        "## 6. Conditions and notes",
        "",
    ]
    if analysis.notes:
        lines += [f"* {note}" for note in analysis.notes]
    else:
        lines.append("* No condition notes: nothing tripped.")
    lines += [
        "",
        "## 7. Limitation",
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
    """Render the result document from the P3 log, mechanically.

    The whole file is written here, provenance section included, so that regenerating it twice gives
    the same bytes and no part of the committed document is a hand edit.
    """
    records = list(read_records(p3_log_path(results_dir)))
    lines = [
        "<!-- Generated by `python -m jev_lab.p3_boundary_locus report` from the P3 log.",
        f"     Analyzer: {PREREGISTRATION_ID}. Do not hand-edit: the numbers are derived. -->",
        "",
    ]
    text = "\n".join(lines) + render_report(analyze(records), records=records) + CORRECTION_PROVENANCE
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
