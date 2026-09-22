"""Derive the closing evaluation report from the canonical usage log.

``results/JEV_LOCAL_EVALUATION_FINAL.md`` is a **derived artifact**. Every number in it is
recomputed from ``results/usage.jsonl`` on the way out, so it cannot drift from the log it
describes and can be regenerated at any time with ``uv run python -m jev_lab final-report``.

Two rules shape the writing:

* **Claims are labelled.** Every line that asserts something carries one of five tags --
  ``OFFICIAL``, ``DESIGN ASSUMPTION``, ``LOCAL MEASUREMENT``, ``DERIVED CALCULATION``,
  ``LIMITATION`` -- so a vendor statement about TypeSafe's workload is never read as something
  measured here, and a local observation is never read as a general rule.
* **The unsupported reading is named.** On this sample the tempting reading is usually the one the
  records do not carry, so each section states its own limits next to its numbers rather than in a
  disclaimer at the end.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .ambiguous import AMBIGUOUS
from .composite import (
    COMPOSITE,
    COMPOSITE_ADVERSE,
    COMPOSITE_BENEFICIAL,
    COMPOSITE_DIMENSIONS,
    COMPOSITE_EXPECTED_ORDER,
    COMPOSITE_SCALE_LEVELS,
    COMPOSITE_WEIGHTS,
    analyze_composite,
    confidence_diagnostics,
    contribution_shares,
)
from .experiments import (
    CONFIDENCE_GATE_THRESHOLD,
    EXPERIMENTS,
    GATE_ACCEPT,
    GATE_ESCALATE,
    experiment_call_ceiling,
    experiment_names,
)
from .fanout import (
    FANOUT,
    FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS,
    PARALLEL,
    analyze_fanout,
)
from .pricing import price_for
from .recorder import DEFAULT_RESULTS_DIR, read_records, summarize
from .repeatability import EXACT_TOP_PROBABILITY_TIE_OBSERVED, REPEATABILITY
from .repeatability import analyze as analyze_repeatability
from .report import TOTAL_LABEL, build_summary, plain_decimal
from .routing import (
    ACTUAL_HANDLER_EXECUTION_REALIZED,
    ACTUAL_HANDLER_EXECUTION_UNTESTED,
    FAIL_CLOSED_SUPPRESSION_REALIZED,
    ROUTING,
    ROUTING_CONFIDENCE_FLOOR,
    ROUTING_HUMAN_REVIEW_THRESHOLD,
    ROUTING_SUPPRESSION_EXPECTATION_MET,
    ROUTING_SUPPRESSION_EXPECTATION_MISSED,
    analyze_routing,
)

FINAL_REPORT_NAME = "JEV_LOCAL_EVALUATION_FINAL.md"

# The five kinds of claim. A line that states a fact carries exactly one of these, so the reader
# never has to guess whether a sentence is a vendor statement, a design choice, a measurement, an
# arithmetic result, or a boundary.
OFFICIAL = "OFFICIAL"
DESIGN_ASSUMPTION = "DESIGN ASSUMPTION"
LOCAL_MEASUREMENT = "LOCAL MEASUREMENT"
DERIVED_CALCULATION = "DERIVED CALCULATION"
LIMITATION = "LIMITATION"
CLAIM_KINDS: tuple[str, ...] = (
    OFFICIAL,
    DESIGN_ASSUMPTION,
    LOCAL_MEASUREMENT,
    DERIVED_CALCULATION,
    LIMITATION,
)

# Status markers. These are strings, not flags: they are greppable, they survive a copy-paste into
# another document, and a test can assert one is present or absent.
CORE_CAPABILITY_EXPLORATION_CLOSED = "CORE_CAPABILITY_EXPLORATION_CLOSED"
LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK = (
    "LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK"
)
OPTIONAL_EDGE_COVERAGE_BACKLOG = "OPTIONAL_EDGE_COVERAGE_BACKLOG"

# Experiments whose records predate the request-position fields. Named so the latency chapter can
# say which sessions it cannot describe rather than averaging over them.
PRIMITIVES = "01_primitives"
ADDRESSING = "02_structured_addressing"
CONFIDENCE = "04_confidence"
INSTRUCTION = "07_instruction_precision"

# The demo gate `04_confidence` applied in code, imported from the experiment that owns it. It is
# used only as the fallback wording when a record carries no gate of its own; the threshold these
# records were actually gated on is read back out of `notes.derived.gate` below.
RATIO_DECIMALS = 4
PERCENT_DECIMALS = 2


# --------------------------------------------------------------------------------------
# Presentation helpers
# --------------------------------------------------------------------------------------


def _claim(kind: str, text: str) -> str:
    """One labelled line. The tag is the first thing on the line, so it cannot be missed."""
    assert kind in CLAIM_KINDS, f"unknown claim kind {kind!r}"
    return f"- **{kind}** — {text}"


def _usd(value: float | None) -> str:
    """A cost, in plain decimal. Sub-cent values must not render as ``$0``."""
    if value is None:
        return "n/a"
    return "$" + plain_decimal(value, 6)


def _ratio(part: float, whole: float) -> str:
    if not whole:
        return "n/a"
    return f"{part / whole:.{RATIO_DECIMALS}f}x"


def _percent(part: float, whole: float) -> str:
    if not whole:
        return "n/a"
    return f"{100 * part / whole:.{PERCENT_DECIMALS}f}%"


def _difference_phrase(value: float, other: float, noun: str) -> str:
    """``value`` against ``other``, in whichever direction the two numbers actually went.

    Written as a phrase so it can be dropped into a sentence about either arm. The direction is
    chosen from the sign of the difference rather than fixed in the sentence around it: a log where
    the speculative arm spent fewer output tokens would otherwise be described with the wrong
    comparison word on a line that reported the right number.
    """
    if value == other:
        return f"the same number of {noun} as"
    return f"**{abs(value - other):.0f} {'fewer' if value < other else 'more'}** {noun} than"


def _saving_phrase(baseline: float, other: float, noun: str) -> str:
    """The gap between two measured totals, named in whichever direction it went.

    ``baseline - other`` is a saving when it is positive and an increase when it is negative. The
    wording follows the sign for the same reason `_difference_phrase` does: "a saving of -23.00%"
    is a sentence that assumes an outcome it did not get.
    """
    if not baseline:
        return f"no comparable baseline for the {noun}"
    share = 100 * (baseline - other) / baseline
    if share > 0:
        return f"a saving of **{share:.{PERCENT_DECIMALS}f}%** of the {noun}"
    if share < 0:
        return f"an increase of **{abs(share):.{PERCENT_DECIMALS}f}%** over the {noun}"
    return f"no change against the {noun}"


def _number(value: Any) -> str:
    """Render a number without float noise; pass non-numbers through.

    ``None`` renders as ``n/a`` rather than ``0``: every numeric field here can be absent, and a
    missing measurement is not a zero measurement.
    """
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _rounded(value: Any, digits: int = RATIO_DECIMALS) -> str:
    """Round for display, passing a missing value through as ``n/a`` instead of rounding it."""
    return "n/a" if value is None else _number(round(value, digits))


def _sum(records: Iterable[Mapping[str, Any]], field: str) -> float:
    return float(sum(record.get(field) or 0 for record in records))


def _table(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def _bullets(rows: Iterable[str]) -> list[str]:
    return [row for row in rows]


# --------------------------------------------------------------------------------------
# Derivations
# --------------------------------------------------------------------------------------


def measured_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """How many canonical records each experiment actually has. This is what "ran" means."""
    return dict(Counter(str(record.get("experiment")) for record in records))


def optional_backlog(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Registered experiments with no records, derived from the registry rather than a list.

    The point of deriving it is that the backlog cannot disagree with what actually ran: an
    experiment leaves this list the moment it produces a record, and nothing has to be edited by
    hand to say so.
    """
    measured = measured_counts(records)
    backlog = []
    for name in experiment_names():
        if measured.get(name):
            continue
        experiment = EXPERIMENTS[name]
        backlog.append(
            {
                "name": name,
                "tier": experiment.tier,
                "calls": experiment_call_ceiling(experiment),
                "intent": experiment.intent,
            }
        )
    return backlog


def session_latency(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Per client session: the first call's latency against the slowest later call.

    Sessions whose records predate the position fields produce ``first=None`` rather than a number
    inferred from timestamps: the log does not state which call opened the session, and a guess
    here would be indistinguishable from a measurement once it was written down.
    """
    sessions: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        sessions.setdefault(str(record.get("run_id")), []).append(record)
    rows = []
    for run_id, group in sessions.items():
        first = next(
            (r for r in group if r.get("is_first_request_in_client_session")), None
        )
        others = [
            float(r.get("latency_ms") or 0)
            for r in group
            if r is not first and r.get("latency_ms") is not None
        ]
        slowest_other = max(others) if others else None
        rows.append(
            {
                "run_id": run_id,
                "experiment": str(group[0].get("experiment")),
                "calls": len(group),
                "schema": group[0].get("schema_version"),
                "first_ms": None if first is None else float(first.get("latency_ms") or 0),
                "slowest_other_ms": slowest_other,
                "ratio": (
                    None
                    if first is None or not slowest_other
                    else float(first.get("latency_ms") or 0) / slowest_other
                ),
            }
        )
    return rows


def within_run_first_call_checks(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Where a *cycle* rather than a session opened with its slowest call, and where it did not.

    `03_parallel_questions` runs two order-balanced cycles inside one session, so "the first call
    of the group is the slow one" can be checked at two scopes. Reporting both is what keeps the
    first-call effect a hypothesis the fields let you test rather than a rule.
    """
    grouped: dict[tuple[str, Any], list[Mapping[str, Any]]] = {}
    for record in records:
        cycle = (record.get("notes") or {}).get("cycle")
        if cycle is None:
            continue
        grouped.setdefault((str(record.get("run_id")), cycle), []).append(record)
    checks = []
    for (run_id, cycle), group in grouped.items():
        ordered = sorted(group, key=lambda r: r.get("logical_request_index_in_run") or 0)
        if len(ordered) < 2:
            continue
        head = float(ordered[0].get("latency_ms") or 0)
        rest = [float(r.get("latency_ms") or 0) for r in ordered[1:]]
        checks.append(
            {
                "run_id": run_id,
                "cycle": cycle,
                "experiment": str(ordered[0].get("experiment")),
                "head_ms": head,
                "slowest_rest_ms": max(rest),
                "head_was_slowest": head >= max(rest),
            }
        )
    return checks


# --------------------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------------------


def _header(records: Sequence[Mapping[str, Any]]) -> list[str]:
    summary = summarize(list(records))
    first = records[0].get("timestamp_utc")
    last = records[-1].get("timestamp_utc")
    return [
        "# Jev Local Evaluation",
        "## Core Capability, Stability, Cost, and Agent-Control Findings",
        "",
        "> **This file is a derived artifact, not a measurement.** The canonical local record is "
        "`results/usage.jsonl`. Every number below is recomputed from it by "
        "`uv run python -m jev_lab final-report`, so this file cannot disagree with the log and "
        "must never be quoted in place of it.",
        "",
        "> **Scope.** Everything measured here comes from a handful of synthetic cases, on one "
        "machine, against one account, in a handful of sessions. It is not a benchmark, not a "
        "calibration, and not comparable to any published figure. Where a sentence is a vendor's "
        "statement rather than an observation, it says so.",
        "",
        "**Claim labels.** Every assertion below carries exactly one:",
        "",
        "| label | meaning |",
        "| --- | --- |",
        f"| **{OFFICIAL}** | a statement from TypeSafe's documentation or their published prices, "
        "about their workload. Not verified here. |",
        f"| **{DESIGN_ASSUMPTION}** | a choice this bench made before running, chosen rather than "
        "measured. |",
        f"| **{LOCAL_MEASUREMENT}** | a value an API response returned, or a fact about a call "
        "recorded in this log. |",
        f"| **{DERIVED_CALCULATION}** | arithmetic done in Python over measurements. Labelled so it "
        "is never mistaken for something the API reported. |",
        f"| **{LIMITATION}** | what the records do not support. |",
        "",
        f"Generated from {summary['requests']} canonical record(s), {first} to {last}.",
        "",
    ]


def _executive_summary(records: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> list[str]:
    totals = summary[TOTAL_LABEL]
    measured = measured_counts(records)
    models = Counter(str(record.get("model_resolved")) for record in records)
    requested = Counter(str(record.get("model_requested")) for record in records)
    statuses = Counter(str(record.get("status")) for record in records)
    sessions = {str(record.get("run_id")) for record in records}
    resolved = ", ".join(f"`{name}`" for name in sorted(models))
    asked = ", ".join(f"`{name}`" for name in sorted(requested))
    lines = ["## 1. Executive summary", ""]
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"resolved model: {resolved} on {models.most_common(1)[0][1]} of {len(records)} "
            f"record(s), requested as {asked}. An alias can move; only the response says which "
            "model answered, which is why both are recorded.",
        )
    )
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"{len(records)} real API call(s) recorded across {len(sessions)} run session(s); "
            f"status {', '.join(f'{name}={count}' for name, count in statuses.most_common())}.",
        )
    )
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"tokens, as the responses reported them: **{totals['input_tokens']:,} input**, "
            f"**{totals['output_tokens']:,} output**, **{totals['total_tokens']:,} total**.",
        )
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"estimated cost **{_usd(totals['estimated_cost_usd'])}**, from the local price table "
            "keyed by the resolved model. Console billing is authoritative.",
        )
    )
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"experiments actually run: {len(measured)} — "
            + ", ".join(f"`{name}` ({count})" for name, count in sorted(measured.items()))
            + ".",
        )
    )
    lines.append("")
    lines += [
        f"**{CORE_CAPABILITY_EXPLORATION_CLOSED}**",
        "",
        _claim(
            LOCAL_MEASUREMENT,
            f"{len(measured)} of {len(experiment_names())} registered experiment(s) have at least "
            "one canonical record, and every number this report states was recomputed from those "
            "records.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**nothing was adjusted after seeing an answer.** The thresholds, the weights, the "
            "expected labels, and the case lists were fixed before the runs; a report that moved "
            "one of them would be a fit rather than a measurement.",
        ),
        "",
    ]
    lines += _execution_boundary(records)
    return lines + [""]


def _execution_boundary(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Whether the allowed-handler branch was reached, read off the routing records themselves.

    This block used to be unconditional, which meant a log in which a handler *had* run would still
    have carried "untested" -- the exact silent downgrade the marker exists to prevent, in the
    direction that is easy to miss because it understates rather than overstates. It now follows
    the records in all three cases: never run, run and withheld, run and reached.
    """
    group = [r for r in records if r.get("experiment") == ROUTING]
    if not group:
        return [
            f"**{ACTUAL_HANDLER_EXECUTION_UNTESTED}**",
            "",
            _claim(
                LIMITATION,
                "`12_function_routing` has no records in this log, so the branch that calls an "
                "allowed handler has not been exercised under a live answer at all. That is an "
                "explicit boundary in this report, **not** a blocker: it is one untested branch "
                "rather than an open question about the model.",
            ),
            "",
        ]
    markers = set(analyze_routing(group)["markers"])
    if ACTUAL_HANDLER_EXECUTION_REALIZED in markers:
        return [
            f"**{ACTUAL_HANDLER_EXECUTION_REALIZED}**",
            "",
            _claim(
                LOCAL_MEASUREMENT,
                "at least one resolved route cleared both gates and called its inert handler, so "
                "the execution branch is exercised end to end on this input.",
            ),
            _claim(
                LIMITATION,
                "one execution of an inert handler is not a production-safety result: nothing "
                "outside this repository was touched, and no claim here extends to a real side "
                "effect.",
            ),
            "",
        ]
    return [
        f"**{ACTUAL_HANDLER_EXECUTION_UNTESTED}**",
        "",
        _claim(
            LOCAL_MEASUREMENT,
            "in the function-routing run, every resolved route was withheld by the frozen policy, "
            "so the branch that calls an allowed handler was never entered under a live answer.",
        ),
        _claim(
            LIMITATION,
            "that branch is carried forward as an explicit boundary, **not** as a blocker: it is "
            "Python-side plumbing rather than an open question about the model, and the offline "
            "suite exercises it. No threshold was moved and no state was chosen to make it "
            "execute, because either would have replaced a measurement with a fit.",
        ),
        "",
    ]


def _primitives(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == PRIMITIVES]
    if not group:
        return []
    record = group[0]
    answers = record.get("answers") or {}
    lines = ["## 2. Primitive behaviour — `01_primitives`", ""]
    for name, answer in answers.items():
        kind = answer.get("type")
        if kind == "choice":
            distribution = ", ".join(
                f"`{label}` {_number(value)}"
                for label, value in sorted(
                    (answer.get("probabilities") or {}).items(), key=lambda kv: -kv[1]
                )
            )
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"`{name}` (Choice) returned label `{answer.get('choice')}` with the full "
                    f"distribution {distribution}, and a separate `confidence` of "
                    f"{_number(answer.get('confidence'))}.",
                )
            )
        elif kind == "score":
            legend = answer.get("legend") or {}
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"`{name}` (Score) returned `{_number(answer.get('score'))}` on a legend of "
                    f"{len(legend)} described position(s) "
                    f"({', '.join(f'{key}={value[:28]}…' for key, value in sorted(legend.items()))}) "
                    f"with `confidence` {_number(answer.get('confidence'))}.",
                )
            )
        elif kind == "noul":
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"`{name}` (Noul) returned the single scalar "
                    f"{_number(answer.get('noul'))} — no distribution and no confidence field, "
                    "because the type carries neither.",
                )
            )
    choice = next((a for a in answers.values() if a.get("type") == "choice"), None)
    if choice:
        top = max((choice.get("probabilities") or {"": 0}).values())
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`confidence` ({_number(choice.get('confidence'))}) and the winning "
                f"probability ({_number(top)}) are different numbers reported side by side: "
                "confidence is not the top-1 probability, and one does not reconstruct the other.",
            )
        )
    lines.append(
        _claim(
            LIMITATION,
            "this is one payload and one response. Nothing here is a law about Choice, Score, or "
            "Noul; the repeats in `13b_ambiguous_repeatability` are what make any statement about "
            "run-to-run movement possible at all, and they are still one payload.",
        )
    )
    return lines + [""]


def _addressing(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == ADDRESSING]
    if len(group) < 2:
        return []
    lines = ["## 3. Structured addressing — `02_structured_addressing`", ""]
    by_form = {str((r.get("notes") or {}).get("state_form")): r for r in group}
    structured, prose = by_form.get("json"), by_form.get("prose")
    if structured and prose:
        difference = float(structured["input_tokens"]) - float(prose["input_tokens"])
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"input tokens differed: **{structured['input_tokens']}** with the structured "
                f"state (addressed by backticked field path) against **{prose['input_tokens']}** "
                f"with prose (described in words).",
            )
        )
        lines.append(
            _claim(
                DERIVED_CALCULATION,
                f"the structured request carried {abs(difference):.0f} more input token(s) "
                f"({_ratio(max(difference, 0), float(prose['input_tokens']))} of the prose arm's "
                "input) for the same four facts.",
            )
        )
        structured_answers = structured.get("answers") or {}
        prose_answers = prose.get("answers") or {}
        shared = sorted(set(structured_answers) & set(prose_answers))
        for name in shared:
            left, right = structured_answers[name], prose_answers[name]
            if left.get("type") == "choice":
                lines.append(
                    _claim(
                        LOCAL_MEASUREMENT,
                        f"`{name}` came back `{left.get('choice')}` in both arms, confidence "
                        f"{_number(left.get('confidence'))} against "
                        f"{_number(right.get('confidence'))}.",
                    )
                )
            elif left.get("type") == "noul":
                lines.append(
                    _claim(
                        LOCAL_MEASUREMENT,
                        f"`{name}` came back {_number(left.get('noul'))} against "
                        f"{_number(right.get('noul'))} — the two arms did not agree on this one.",
                    )
                )
    lines.append(
        _claim(
            LIMITATION,
            "the two arms differ in state form **and** in length, and there is one observation per "
            "arm in one session. The token difference is between two written states, not a causal "
            "effect of JSON over prose; no arm is the reference and no arm is called better.",
        )
    )
    return lines + [""]


def confidence_gate(record: Mapping[str, Any]) -> dict[str, Any] | None:
    """One record's confidence gate, read from the record and checked against its own numbers.

    The run froze its gate decision into ``notes.derived.gate`` at measurement time, and that
    stored decision is what gets reported -- but it is first recomputed from the confidence the
    answer carried and the threshold the record names. A report that trusted the stored decision
    while ignoring the numbers beside it could describe a gate that never ran, so the two are
    required to agree: a record whose stored decision and stored numbers disagree is not a record
    this report can describe, and picking either reading would be a guess. That case stops the
    build rather than printing a direction.

    Returns ``None`` when the record carries no gate at all, which is not an error -- an answer
    with no confidence has no gate to describe.
    """
    derived = (record.get("notes") or {}).get("derived") or {}
    gate = derived.get("gate") or {}
    decision = gate.get("decision")
    threshold = gate.get("threshold")
    answers = record.get("answers") or {}
    choice = next((answer for answer in answers.values() if answer.get("type") == "choice"), None)
    confidence = (choice or {}).get("confidence")
    if decision is None or threshold is None or confidence is None:
        return None
    recomputed = GATE_ACCEPT if float(confidence) >= float(threshold) else GATE_ESCALATE
    if recomputed != decision:
        raise ValueError(
            f"record {record.get('case_id')!r} stores gate decision {decision!r}, but its own "
            f"confidence {confidence} at threshold {threshold} recomputes to {recomputed!r}; the "
            "log and this build disagree about what the gate did, so no direction is reported"
        )
    return {
        "decision": decision,
        "threshold": float(threshold),
        "confidence": float(confidence),
        "cleared": decision == GATE_ACCEPT,
    }


def _gate_outcome(decisions: Sequence[tuple[str, Mapping[str, Any]]]) -> str:
    """Which cases cleared the gate, in whichever direction the records went.

    Written from the decisions rather than around them: a fixed sentence here would keep saying
    the ambiguous case was refused on a log where it was accepted, which is precisely the reading
    a derived report exists to prevent.
    """
    cleared = [label for label, gate in decisions if gate["cleared"]]
    withheld = [label for label, gate in decisions if not gate["cleared"]]
    if not cleared:
        return f"escalated on every one of these cases ({', '.join(withheld)}) — none cleared"
    if not withheld:
        return f"accepted and cleared on every one of these cases ({', '.join(cleared)})"
    return (
        f"accepted and cleared on {', '.join(cleared)}, and escalated without clearing on "
        f"{', '.join(withheld)}"
    )


def _confidence(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == CONFIDENCE]
    if len(group) < 2:
        return []
    lines = ["## 4. Confidence — `04_confidence`", ""]
    by_ambiguity = {str((r.get("notes") or {}).get("ambiguity")): r for r in group}
    for label, record in sorted(by_ambiguity.items()):
        answers = record.get("answers") or {}
        choice = next((a for a in answers.values() if a.get("type") == "choice"), None)
        score = next((a for a in answers.values() if a.get("type") == "score"), None)
        if choice:
            distribution = ", ".join(
                f"`{name}` {_number(value)}"
                for name, value in sorted(
                    (choice.get("probabilities") or {}).items(), key=lambda kv: -kv[1]
                )
            )
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"{label} evidence: `{choice.get('choice')}` at confidence "
                    f"{_number(choice.get('confidence'))}, distribution {distribution}.",
                )
            )
        if score:
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"{label} evidence: the specificity Score was "
                    f"{_number(score.get('score'))} with confidence "
                    f"{_number(score.get('confidence'))}.",
                )
            )
    gates = [
        (label, gate)
        for label, record in sorted(by_ambiguity.items())
        if (gate := confidence_gate(record)) is not None
    ]
    threshold = gates[0][1]["threshold"] if gates else CONFIDENCE_GATE_THRESHOLD
    lines.append(
        _claim(
            DESIGN_ASSUMPTION,
            f"the experiment gated in code on `confidence >= {_number(threshold)}` alone, "
            "a demonstration parameter that was fixed before the run, is not calibrated, and is "
            "not claimed to be optimal.",
        )
    )
    if gates:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the gate {_gate_outcome(gates)}, which is the gate behaving as written on these "
                "answers.",
            )
        )
    lines.append(
        _claim(
            LIMITATION,
            "**confidence is not correctness**, and a threshold on it is not a correctness filter: "
            "an arbitrary cut accepts an ambiguous case whenever its confidence happens to land "
            "above the line. The two are reported side by side and never combined, and no accuracy "
            "rate is computed anywhere in this report.",
        )
    )
    return lines + [""]


def _instruction(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == INSTRUCTION]
    if len(group) < 2:
        return []
    lines = ["## 5. Instruction sensitivity — `07_instruction_precision`", ""]
    by_boundary = {str((r.get("notes") or {}).get("boundary")): r for r in group}
    vague, explicit = by_boundary.get("vague"), by_boundary.get("explicit")
    left = right = None
    if vague and explicit:
        state_bytes = {int(r.get("state_utf8_bytes") or 0) for r in group}
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the state was byte-identical across both arms "
                f"({', '.join(str(value) for value in sorted(state_bytes))} UTF-8 byte(s) each); "
                "what differed was the wording of the question carrying the decision boundary, "
                f"and the input tokens with it ({vague['input_tokens']} against "
                f"{explicit['input_tokens']}).",
            )
        )
        vague_answer = next(iter((vague.get("answers") or {}).values()), {})
        explicit_answer = next(iter((explicit.get("answers") or {}).values()), {})
        left, right = vague_answer.get("noul"), explicit_answer.get("noul")
        if left is not None and right is not None:
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"the Noul moved from **{_number(left)}** under the vague boundary to "
                    f"**{_number(right)}** under the explicit one.",
                )
            )
            lines.append(
                _claim(
                    DERIVED_CALCULATION,
                    f"a difference of {_number(round(abs(float(left) - float(right)), 4))} on a "
                    "0–1 probability, from the same state bytes.",
                )
            )
    if left is not None and right is not None:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                "decision-boundary wording "
                + (
                    "materially changed the observed judgment in this case."
                    if float(left) != float(right)
                    else "left the observed judgment unchanged in this case; the two Nouls are the "
                    "same number on byte-identical state."
                ),
            )
        )
    lines.append(
        _claim(
            LIMITATION,
            "this says the wording mattered here, not which wording is right: neither arm is a "
            "ground truth, one pair is not a dose-response curve, and nothing here says a "
            "particular phrasing generalises to another task.",
        )
    )
    return lines + [""]


def _batching(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == PARALLEL]
    if not group:
        return []
    batched = [r for r in group if (r.get("notes") or {}).get("arm") == "batched"]
    separate = [r for r in group if (r.get("notes") or {}).get("arm") == "separate"]
    lines = ["## 6. Batching — `03_parallel_questions`", ""]
    batch_in, separate_in = _sum(batched, "input_tokens"), _sum(separate, "input_tokens")
    batch_out, separate_out = _sum(batched, "output_tokens"), _sum(separate, "output_tokens")
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"{len(batched)} batched request(s) carried **{batch_in:.0f} input / "
            f"{batch_out:.0f} output** tokens; the {len(separate)} separate request(s) carrying "
            f"the same questions carried **{separate_in:.0f} input / {separate_out:.0f} output**.",
        )
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"pooled input ratio **{_ratio(separate_in, batch_in)}** (separate over batched); "
            f"{_saving_phrase(separate_in, batch_in, 'input tokens the separate arm spent')}.",
        )
    )
    batch_cost, separate_cost = _sum(batched, "estimated_cost_usd"), _sum(separate, "estimated_cost_usd")
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"estimated cost {_usd(batch_cost)} against {_usd(separate_cost)}, a ratio of "
            f"{_ratio(separate_cost, batch_cost)}. The cost ratio equals the input ratio here "
            "because the encoded price for this model charges input only.",
        )
    )
    agreements = []
    for cycle in sorted({(r.get("notes") or {}).get("cycle") for r in group}):
        cycle_batch = [r for r in batched if (r.get("notes") or {}).get("cycle") == cycle]
        cycle_separate = [r for r in separate if (r.get("notes") or {}).get("cycle") == cycle]
        if not cycle_batch or not cycle_separate:
            continue
        batch_answers = cycle_batch[0].get("answers") or {}
        for record in cycle_separate:
            for name, answer in (record.get("answers") or {}).items():
                other = batch_answers.get(name)
                if other is None:
                    continue
                agreements.append(
                    {
                        "cycle": cycle,
                        "question": name,
                        "same": (other.get("choice"), other.get("noul"), other.get("score"))
                        == (answer.get("choice"), answer.get("noul"), answer.get("score")),
                    }
                )
    if agreements:
        same = sum(1 for entry in agreements if entry["same"])
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"of {len(agreements)} question(s) asked in both arms across the two cycles, "
                f"**{same}** returned the same selected value; this compares labels, not "
                "distributions.",
            )
        )
    attempts = [r.get("transport_attempt_count") for r in group]
    recorded = [value for value in attempts if value is not None]
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"transport attempts recorded on {len(recorded)} of {len(group)} call(s): "
            f"{', '.join(str(value) for value in recorded) or 'none'} — no HTTP retry was locally "
            "observed for them, which is all that count licenses.",
        )
    )
    # The spread against the effect it would be used to explain, computed here rather than asserted:
    # the sentence below used to state this comparison without ever making it, so a log where the
    # arms separated cleanly would still have carried the same "spread dominates" wording.
    batch_latencies = [float(r["latency_ms"]) for r in batched if r.get("latency_ms") is not None]
    separate_latencies = [
        float(r["latency_ms"]) for r in separate if r.get("latency_ms") is not None
    ]
    latency_lines = []
    if batch_latencies and separate_latencies:
        spread = max(batch_latencies) - min(batch_latencies)
        difference = abs(
            sum(batch_latencies) / len(batch_latencies)
            - sum(separate_latencies) / len(separate_latencies)
        )
        latency_lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the batched arm's own {len(batch_latencies)} observation(s) were spread by "
                f"**{_rounded(spread, 3)} ms**, against an arm-to-arm mean difference of "
                f"**{_rounded(difference, 3)} ms** — the within-arm spread is "
                f"{'larger' if spread > difference else 'not larger'} than the difference it would "
                "be used to explain.",
            )
        )
    latency_lines.append(
        _claim(
            LIMITATION,
            "latency here is reported as an observation and never as a speedup: two cycles cannot "
            "separate arm identity from request position, so no factor is attributed to batching.",
        )
    )
    lines += latency_lines + [
        "",
        _claim(
            DERIVED_CALCULATION,
            f"**core local finding.** Pooled over both cycles: {len(batched)} batched request(s) "
            f"carried {_difference_phrase(batch_in, separate_in, 'input tokens')} the "
            f"{len(separate)} separate request(s) carrying the same questions.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "the two arms were built with identical state and identical question definitions, "
            "which is what makes the input-token difference track the request split rather than "
            "some other difference between them.",
        ),
        _claim(
            OFFICIAL,
            "TypeSafe documents batching as a way to avoid re-sending shared state. That is a claim "
            "about their workload; the sentence above is about these two cycles of this payload.",
        ),
        _claim(
            LIMITATION,
            "two cycles, five questions, one state, one session. This is not a universal batching "
            "ratio, and it does not extend to payloads whose questions are not all over the same "
            "state.",
        ),
    ]
    return lines + [""]


def _choice_variation(choice: Mapping[str, Any], count: int) -> str:
    """The Choice half of one repeat experiment, or ``""`` when no Choice answer came back."""
    margin = choice.get("margin_summary")
    if not choice.get("observed") or margin is None:
        return ""
    return (
        f"Choice: the same label came back {count} time(s), with {choice['leader_switches']} "
        f"leader switch(es) and a top-2 margin range of {_number(round(margin['range'], 4))} "
        f"(min {_number(round(margin['min'], 4))}, max {_number(round(margin['max'], 4))})."
    )


def _score_variation(score: Mapping[str, Any], count: int) -> str:
    """The Score half of one repeat experiment, or ``""`` when no Score answer came back."""
    summary = score.get("summary")
    if not summary:
        return ""
    values = ", ".join(_number(value) for value in score["values"])
    confidence = score.get("confidence")
    tail = ""
    if confidence:
        tail = (
            f", confidence {_number(round(confidence['min'], 4))}–"
            f"{_number(round(confidence['max'], 4))}"
        )
    return (
        f"Score: values {values} (range {_number(round(summary['range'], 4))}){tail}."
    )


def _noul_variation(noul: Mapping[str, Any], count: int) -> str:
    """The Noul half of one repeat experiment, or ``""`` when no Noul answer came back."""
    summary = noul.get("summary")
    if not summary:
        return ""
    values = ", ".join(_number(value) for value in noul["values"])
    return f"Noul: values {values} (range {_number(round(summary['range'], 4))})."


def _variation_comparison(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    """Where two repeat payloads moved differently, named field by field.

    Only comparable when both payloads actually returned the field: the interesting statement is
    that variation is payload-dependent, and a payload with no Noul answer has no variation to
    compare -- it is not a payload whose Noul held still.
    """
    left_margin = left["choice"].get("margin_summary")
    right_margin = right["choice"].get("margin_summary")
    left_noul = left["noul"].get("summary")
    right_noul = right["noul"].get("summary")
    if not (left_margin and right_margin and left_noul and right_noul):
        return ""
    def movement(summary: Mapping[str, Any], noun: str) -> str:
        spread = round(summary["range"], 4)
        if spread == 0:
            return f"the {noun} did not move at all"
        return f"the {noun} moved by {_number(spread)}"

    return (
        f"the variation differed by field between the two payloads: in `{REPEATABILITY}` "
        f"{movement(left_margin, 'Choice margin')} and {movement(left_noul, 'Noul')}, while in "
        f"`{AMBIGUOUS}` {movement(right_margin, 'Choice margin')} and "
        f"{movement(right_noul, 'Noul')}."
    )


def _repeatability(records: Sequence[Mapping[str, Any]]) -> list[str]:
    marked = [r for r in records if r.get("experiment") == REPEATABILITY]
    ambiguous = [r for r in records if r.get("experiment") == AMBIGUOUS]
    if not marked and not ambiguous:
        return []
    lines = ["## 7. Repeatability — `13_repeatability` and `13b_ambiguous_repeatability`", ""]
    for label, group in ((REPEATABILITY, marked), (AMBIGUOUS, ambiguous)):
        if not group:
            continue
        analysis = analyze_repeatability(group)
        choice, score, noul = analysis["choice"], analysis["score"], analysis["noul"]
        lines.append(f"### `{label}` — {len(group)} byte-identical request(s)")
        lines.append("")
        for kind, field, render in (
            ("Choice", choice, _choice_variation),
            ("Score", score, _score_variation),
            ("Noul", noul, _noul_variation),
        ):
            rendered = render(field, len(group))
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT if rendered else LIMITATION,
                    rendered
                    or f"{kind}: no answer of this type was returned, so there is no variation to "
                    "describe. An absent answer is not a stable one.",
                )
            )
        markers = ", ".join(f"`{name}`" for name in analysis["markers"]) or "none"
        lines.append(_claim(LOCAL_MEASUREMENT, f"markers raised: {markers}."))
        lines.append("")
    if marked and ambiguous:
        left, right = analyze_repeatability(marked), analyze_repeatability(ambiguous)
        comparison = _variation_comparison(left, right)
        if comparison:
            lines.append(_claim(LOCAL_MEASUREMENT, comparison))
    lines += [
        "",
        *_stability_finding(
            [(label, analyze_repeatability(group))
             for label, group in ((REPEATABILITY, marked), (AMBIGUOUS, ambiguous))
             if group]
        ),
        _claim(
            LIMITATION,
            "two payloads, five calls each, two sessions. There is **no global noise bound** here: "
            "nothing in these records says what variation a different payload would show, and a "
            "single observation of a tie is not a distribution over ties.",
        ),
    ]
    return lines + [""]


def _stability_finding(analyses: Sequence[tuple[str, Mapping[str, Any]]]) -> list[str]:
    """The reading this chapter exists to support, written from the stability numbers.

    A fixed sentence sat here saying the label held while the numbers moved, and naming the
    ambiguous payload's tie as the clearest case, on any log at all. Both are read back now: the
    label clause from the leader switches, the margin clause from the ranges the analyses computed,
    and the tie only when its marker was actually raised.
    """
    if not analyses:
        return []
    calls = sum(analysis["calls"] for _, analysis in analyses)
    switches = sum(
        int(analysis["choice"].get("leader_switches") or 0) for _, analysis in analyses
    )
    margins = [
        analysis["choice"]["margin_summary"]["range"]
        for _, analysis in analyses
        if analysis["choice"].get("margin_summary") is not None
    ]
    stability = (
        "never switched, so a reader who kept only the label would have seen a perfectly "
        "reproducible answer"
        if switches == 0
        else f"switched {switches} time(s), so even the label was not fixed on these records"
    )
    margin_clause = (
        "while the top-2 margin underneath it moved over a range of up to "
        f"{_number(round(max(margins), 4))}"
        if margins
        else "and no top-2 margin was recorded to compare against it"
    )
    lines = [
        _claim(
            LOCAL_MEASUREMENT,
            f"**a stable label is not a fixed distribution.** Across {calls} byte-identical call(s) "
            f"the winning Choice label {stability}, {margin_clause}.",
        )
    ]
    ties = [
        label
        for label, analysis in analyses
        if EXACT_TOP_PROBABILITY_TIE_OBSERVED in analysis["markers"]
    ]
    if ties:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the clearest case is `{ties[0]}`: its decided label sits on an exact "
                "top-probability tie, which is what a decided label on an undecided distribution "
                "looks like in these records.",
            )
        )
    return lines


def _fanout(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == FANOUT]
    if not group:
        return []
    analysis = analyze_fanout(group)
    lines = ["## 8. Speculative fan-out — `05_speculative_fanout`", ""]
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"fan-out: {analysis['fanout_calls']} request(s), "
            f"**{analysis['fanout_input_tokens']:.0f} input / "
            f"{analysis['fanout_output_tokens']:.0f} output** tokens; staged: "
            f"{analysis['staged_calls']} request(s), **{analysis['staged_input_tokens']:.0f} input "
            f"/ {analysis['staged_output_tokens']:.0f} output**.",
        )
    )
    input_saving = _saving_phrase(
        analysis["staged_input_tokens"], analysis["fanout_input_tokens"], "staged arm's input"
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"pooled input ratio **{_ratio(analysis['staged_input_tokens'], analysis['fanout_input_tokens'])}** "
            f"(staged over fan-out), {input_saving}; estimated cost "
            f"{_usd(analysis['fanout_cost_usd'])} against "
            f"{_usd(analysis['staged_cost_usd'])}, ratio "
            f"{_ratio(analysis['staged_cost_usd'], analysis['fanout_cost_usd'])}.",
        )
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"output tokens moved separately: fan-out spent "
            f"{_difference_phrase(analysis['fanout_output_tokens'], analysis['staged_output_tokens'], 'output tokens')} "
            "staged, and at the encoded price for this model output is charged at $0/M, so this "
            "does not appear in the cost ratio above.",
        )
    )
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"of {analysis['fanout_questions_asked']} question(s) asked in the fan-out requests, "
            f"**{analysis['fanout_questions_consumed']} were consumed** by the code and "
            f"**{analysis['fanout_questions_unused']} were unused** — the speculative answers the "
            "second strategy never had to buy.",
        )
    )
    differing = [
        (entry["pair"], comparison["question"], comparison["differences"])
        for entry in analysis["pairs"]
        for comparison in entry["comparisons"]
        if comparison.get("differences")
    ]
    if differing:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"of the consumed answers compared field by field, "
                f"**{len(differing)} moved** between the two strategies — "
                + "; ".join(
                    f"{pair} `{question}` ({'; '.join(differences)})"
                    for pair, question, differences in differing
                )
                + ".",
            )
        )
        lines.append(
            _claim(
                LIMITATION,
                "a difference here is not an error and neither strategy is the reference: the same "
                "question was asked in different company, and the log does not say which reading is "
                "correct.",
            )
        )
    directions = [
        (entry["pair"], entry["latency_direction"])
        for entry in analysis["pairs"]
        if entry.get("latency_direction")
    ]
    if directions:
        # The per-pair directions were always read from the analysis; the sentence drawn from them
        # was not. It now follows the same marker the fan-out chapter already computes, so a log
        # where both pairs went the same way cannot keep the "inconsistent" wording.
        inconsistent = FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS in analysis["markers"]
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                "latency direction per pair: "
                + ", ".join(f"{pair} `{direction}`" for pair, direction in directions)
                + (
                    " — the direction is **inconsistent across pairs**, so no arm is faster here."
                    if inconsistent
                    else " — the direction is **consistent across pairs** "
                    f"({len(directions)} pair(s), one direction), which is one session's "
                    "observation and still not a speedup measurement."
                ),
            )
        )
    lines += [
        "",
        _claim(
            DERIVED_CALCULATION,
            "**core local finding.** Fan-out carried "
            f"{_difference_phrase(analysis['fanout_input_tokens'], analysis['staged_input_tokens'], 'input tokens')} "
            "staged and "
            f"{_difference_phrase(analysis['fanout_output_tokens'], analysis['staged_output_tokens'], 'output tokens')} "
            f"staged, while leaving {analysis['fanout_questions_unused']} of "
            f"{analysis['fanout_questions_asked']} speculative answer(s) unconsumed by the code.",
        ),
        _claim(
            LIMITATION,
            "two pairs, two states, one session, one branching shape. This is not a general "
            "batching-versus-staging rule; the trade depends on how much state is shared and how "
            "many branches are speculative.",
        ),
    ]
    return lines + [""]


def _ranked_contributions(case: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One case's contributions, largest first, each carrying the confidence of its own judgment.

    ``contribution_shares`` returns shares in dimension order and without the confidences, which is
    right for summing and wrong for talking about which judgment drove a composite. Joining the two
    here keeps that pairing in one place instead of at each use site.
    """
    confidences = {row["dimension"]: row.get("confidence") for row in case.get("rows") or []}
    ranked = [
        share | {"confidence": confidences.get(share["dimension"])}
        for share in contribution_shares(case)
    ]
    return sorted(ranked, key=lambda share: -share["weighted_contribution"])


def _composite(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == COMPOSITE]
    if not group:
        return []
    analysis = analyze_composite(group)
    lines = ["## 9. Composite scoring — `06_composite_scoring`", ""]
    lines.append(
        _claim(
            DESIGN_ASSUMPTION,
            f"Jev was asked for {len(COMPOSITE_DIMENSIONS)} **separate, atomic** Score judgments "
            f"per state ({', '.join(f'`{name}`' for name in COMPOSITE_DIMENSIONS)}), each on a "
            f"legend of {COMPOSITE_SCALE_LEVELS} described positions. Nothing in the payload asks "
            "the model to combine them, to count, or to return a verdict.",
        )
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            "Python did the arithmetic: normalize each Score by `score / (levels - 1)`, align it "
            "to risk direction, multiply by the frozen weight, and sum. Weights: "
            + ", ".join(f"`{name}` {_number(weight)}" for name, weight in COMPOSITE_WEIGHTS.items())
            + ".",
        )
    )
    lines.append("")
    scored = [case for case in analysis["cases"] if case.get("composite_risk") is not None]
    lines += _table(
        ["state", "composite risk", "largest contribution", "that contribution's confidence"],
        [
            (
                f"`{case['case_id']}`",
                _number(round(case["composite_risk"], 4)),
                f"`{ranked[0]['dimension']}` "
                f"({_number(round(ranked[0]['weighted_contribution'], 4))})",
                _number(ranked[0]["confidence"]),
            )
            for case in scored
            for ranked in [_ranked_contributions(case)]
            if ranked
        ],
    )
    lines.append("")
    observed = list(analysis["observed_order"])
    expected = list(analysis["expected_order"]) or list(COMPOSITE_EXPECTED_ORDER)
    risks = {case["case_id"]: case["composite_risk"] for case in scored}
    detail = ", ".join(
        f"`{name}` {_number(round(risks[name], 4))}" for name in observed if name in risks
    )
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"the states were written to sit in the order "
            f"{' < '.join(f'`{name}`' for name in expected)}; the composites came back "
            f"{' < '.join(f'`{name}`' for name in observed)} ({detail}). The observed order "
            f"{'matches' if observed == expected else 'does not match'} the frozen one — which "
            "tests the scenarios were written to separate, and is not an accuracy score.",
        )
    )
    diagnostics = confidence_diagnostics(
        [row for case in analysis["cases"] for row in case["rows"]]
    )
    low = next((case for case in scored if case["case_id"] == "low_risk"), None)
    if low:
        ranked = _ranked_contributions(low)
        if ranked:
            top = ranked[0]
            # "The lowest confidence recorded anywhere" is a claim about the whole run, so it is
            # only made when the run's own computed minimum agrees. Otherwise the number is still
            # reported, without the superlative attached to it.
            is_lowest = (
                diagnostics.get("available")
                and diagnostics.get("min") is not None
                and float(top["confidence"]) == float(diagnostics["min"])
            )
            lines.append(
                _claim(
                    LOCAL_MEASUREMENT,
                    f"in the lowest-risk state the largest single contribution came from "
                    f"`{top['dimension']}` at confidence **{_number(top['confidence'])}**"
                    + (
                        " — the lowest confidence recorded anywhere in this experiment —"
                        if is_lowest
                        else ","
                    )
                    + " and carried "
                    f"{_percent(top['weighted_contribution'], low['composite_risk'])} of that "
                    "state's composite.",
                )
            )
    if diagnostics.get("available"):
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the per-dimension confidences recorded across the run span "
                f"{_number(diagnostics['min'])} to {_number(diagnostics['max'])} "
                f"(mean {_number(round(diagnostics['mean'], 4))}).",
            )
        )
    lines += [
        _claim(
            DESIGN_ASSUMPTION,
            "confidence was deliberately kept **out of the arithmetic**: it is recorded beside each "
            "judgment as a diagnostic, and the composite is a function of the scores alone.",
        ),
        _claim(
            LIMITATION,
            "there is **no composite confidence**. No answer carries one, and none is synthesised "
            "in code, so a composite risk figure here cannot say how decided it is.",
        ),
        _claim(
            LIMITATION,
            f"the {len(COMPOSITE_DIMENSIONS)} dimensions are **separate, atomic, and "
            "designed-orthogonal** — they were written to look at different things. They are "
            "**not shown to be empirically independent**, and nothing here measures their "
            "correlation. A state that moves several of them at once can therefore be counted "
            "more than once by the weighted sum; that possibility is observed, not quantified.",
        ),
        _claim(
            LIMITATION,
            f"{len(COMPOSITE_BENEFICIAL)} dimension(s) are aligned so that a high Score is "
            f"beneficial and {len(COMPOSITE_ADVERSE)} is aligned the other way; the alignments are "
            "a design decision in code, and a wrong one would invert a contribution silently.",
        ),
    ]
    return lines + [""]


def _classification_sentence(analysis: Mapping[str, Any]) -> str:
    """The two target classifications, each against the denominator it was actually measured on.

    `FUNCTION_TARGET_REALIZED` is a statement about every case the run attempted, so its
    denominator is the call count. `ARGUMENT_TARGET_REALIZED` is a statement about the cases that
    resolved, so its denominator is the resolved count. Both used to print a *matched* count in
    place of the denominator, which read as a complete result on a log where only some matched:
    "all 3 case(s)" on a run of four. The conditions mirror the classification the routing module
    computes, and the label names are its vocabulary, unchanged.
    """
    calls = analysis["calls"]
    resolved = analysis["resolved_count"]
    if calls and resolved == calls and analysis["matched_count"] == calls:
        function_part = (
            f"`FUNCTION_TARGET_REALIZED` — all {calls} case(s) returned the pre-frozen expected "
            "function."
        )
    else:
        function_part = (
            f"`FUNCTION_TARGET_NOT_REALIZED` — {analysis['matched_count']} of {calls} case(s) "
            "returned the pre-frozen expected function."
        )
    if resolved and analysis["argument_matched_count"] == resolved:
        argument_part = (
            f"`ARGUMENT_TARGET_REALIZED` — all {resolved} resolved case(s) returned the argument "
            "label frozen with their state."
        )
    else:
        argument_part = (
            f"`ARGUMENT_TARGET_NOT_REALIZED` — {analysis['argument_matched_count']} of {resolved} "
            "resolved case(s) returned the argument label frozen with their state."
        )
    return f"{function_part} {argument_part}"


def _routing(records: Sequence[Mapping[str, Any]]) -> list[str]:
    group = [r for r in records if r.get("experiment") == ROUTING]
    if not group:
        return []
    analysis = analyze_routing(group)
    lines = ["## 10. Function routing — `12_function_routing`", ""]
    lines.append(
        _claim(
            DESIGN_ASSUMPTION,
            "the model chooses a function name from a registry frozen before the run and an "
            "argument label from that function's own closed set; Python looks the name up and calls "
            "the one function it names. No free-form generation is parsed, and no returned string "
            "is ever evaluated or imported.",
        )
    )
    lines.append("")
    lines += _table(
        ["case", "expected", "returned", "match", "confidence", "top-2 margin", "review signal"],
        [
            (
                f"`{case['case_id']}`",
                f"`{case['expected_function']}`",
                f"`{case['selected_function']}`",
                "yes" if case["matches_expected_function"] else "**no**",
                _number(case["confidence"]),
                _rounded(case["margin"]),
                _number(case["needs_human_review"]),
            )
            for case in analysis["cases"]
        ],
    )
    lines.append("")
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"function match: **{analysis['matched_count']} of {analysis['calls']}**; argument "
            f"match: **{analysis['argument_matched_count']} of {analysis['resolved_count']}** "
            "resolved case(s).",
        )
    )
    lines.append(
        _claim(
            LIMITATION,
            "these are counts on four synthetic cases with one observation each. They are not an "
            "accuracy rate, and the expected labels are the scenario's intention rather than an "
            "independent truth, so nothing here estimates how the model would route a request it "
            "has not seen.",
        )
    )
    lines.append("")
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            "**classifications.** " + _classification_sentence(analysis),
        )
    )
    lines.append("")
    for case in analysis["cases"]:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{case['case_id']}`: confidence {_number(case['confidence'])} "
                f"(floor {'cleared' if case['confidence_gate_pass'] else 'not cleared'} at "
                f"{ROUTING_CONFIDENCE_FLOOR}), review signal "
                f"{_number(case['needs_human_review'])} "
                f"({'cleared' if case['review_gate_pass'] else 'not cleared'} at "
                f"{ROUTING_HUMAN_REVIEW_THRESHOLD}), execution "
                f"{'allowed' if case['execution_allowed'] else 'withheld'}.",
            )
        )
    markers = set(analysis["markers"])
    if ROUTING_SUPPRESSION_EXPECTATION_MISSED in markers:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{ROUTING_SUPPRESSION_EXPECTATION_MISSED}` — "
                f"{analysis['unexpected_suppression_count']} case(s) the design wrote as routine "
                "were withheld, against "
                f"{analysis['suppression_expected_hit']} of "
                f"{analysis['suppression_expected_count']} expected suppression(s) observed. The "
                "pre-registered expectation and the answers disagree, and the disagreement is left "
                "standing: no threshold was moved after seeing it.",
            )
        )
    elif ROUTING_SUPPRESSION_EXPECTATION_MET in markers:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{ROUTING_SUPPRESSION_EXPECTATION_MET}` — the withheld case(s) are the ones the "
                "design expected to be withheld.",
            )
        )
    if ACTUAL_HANDLER_EXECUTION_REALIZED in markers:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                "`ACTUAL_HANDLER_EXECUTION_REALIZED` — at least one allowed route reached "
                "`HANDLERS[name](argument)` and produced the inert result.",
            )
        )
    else:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{ACTUAL_HANDLER_EXECUTION_UNTESTED}` — no handler was called: every resolved "
                f"route was withheld ({analysis['suppressed_count']} of {analysis['calls']}), so "
                "the allowed-route branch was never entered under a live answer.",
            )
        )
    if FAIL_CLOSED_SUPPRESSION_REALIZED in markers:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{FAIL_CLOSED_SUPPRESSION_REALIZED}` — {analysis['suppressed_count']} route(s) "
                "were withheld and no handler ran for any of them; nothing was substituted for a "
                "withheld route.",
            )
        )
    else:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"`{FAIL_CLOSED_SUPPRESSION_REALIZED}` is **not** carried on these records: either "
                "no route was suppressed, or a suppressed route reached a handler. The marker "
                "follows the records and is not asserted here.",
            )
        )
    resolved = analysis["resolved_count"]
    matched_count = analysis["matched_count"]
    argument_matched = analysis["argument_matched_count"]
    if resolved and matched_count == resolved == argument_matched:
        model_did = "produced the intended function and argument in every resolved case"
    else:
        model_did = (
            f"produced the intended function in {matched_count} of {resolved} resolved case(s) and "
            f"the intended argument in {argument_matched} of {resolved}"
        )
    # Which way the authorization went is read from the markers as well. The sentence used to end
    # "and the code still refused to act" on any log at all, so a log where a route did reach its
    # handler would have carried the opposite of what happened.
    if ACTUAL_HANDLER_EXECUTION_REALIZED in markers:
        policy_did = (
            f"the policy let {analysis['executed_count']} resolved route(s) through to its inert "
            "handler"
        )
        execution_note = (
            "the execution path from an allowed route to the handler **was** reached here, on an "
            "inert handler under a live answer; that is one route, and this report does not extend "
            "it to a route it did not see."
        )
    else:
        policy_did = "the policy withheld every resolved route, so no handler ran"
        execution_note = (
            "the execution path from an allowed route to the handler is **not** established by a "
            "live run here, and this report does not claim a full execution chain succeeded."
        )
    lines += [
        "",
        _claim(
            LOCAL_MEASUREMENT,
            f"**the model {model_did}** — a function name from a registry frozen before the run and "
            "an argument from that function's own closed set.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**semantic routing is not execution authorization.** The model's route selected which "
            "code was eligible to act; whether anything acted was decided afterwards and elsewhere "
            f"— {policy_did}. A system that treats a confident route as permission to act has "
            "removed the layer that produced this result.",
        ),
        _claim(LIMITATION, execution_note),
    ]
    return lines + [""]


def _ledger(summary: Mapping[str, Mapping[str, Any]], records: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["## 11. Token and cost ledger", ""]
    rows = []
    for name, metrics in summary.items():
        if name == TOTAL_LABEL:
            continue
        rows.append(
            (
                f"`{name}`",
                metrics["requests"],
                f"{metrics['input_tokens']:,}",
                f"{metrics['output_tokens']:,}",
                f"{metrics['total_tokens']:,}",
                _usd(metrics["estimated_cost_usd"]),
            )
        )
    total = summary[TOTAL_LABEL]
    rows.append(
        (
            f"**{TOTAL_LABEL}**",
            f"**{total['requests']}**",
            f"**{total['input_tokens']:,}**",
            f"**{total['output_tokens']:,}**",
            f"**{total['total_tokens']:,}**",
            f"**{_usd(total['estimated_cost_usd'])}**",
        )
    )
    lines += _table(["experiment", "requests", "input", "output", "total", "estimated cost"], rows)
    lines.append("")
    bases = sorted({str(record.get("cost_basis")) for record in records if record.get("cost_basis")})
    models = sorted({str(record.get("model_resolved")) for record in records})
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            "token counts are the `usage` values the responses returned. Nothing in this report "
            "estimates a token count, and no per-question or per-answer figure is derived from one.",
        )
    )
    lines.append(
        _claim(
            DERIVED_CALCULATION,
            f"cost is a local estimate, computed as reported input and output tokens against the "
            f"price table entry for the **resolved** model. Basis as encoded: "
            f"{'; '.join(bases) if bases else 'n/a'}.",
        )
    )
    for model in models:
        price = price_for(model)
        if price is not None:
            lines.append(
                _claim(
                    OFFICIAL,
                    f"published price for `{model}`: ${price.input_usd_per_million}/M input "
                    f"tokens, ${price.output_usd_per_million}/M output tokens. Output is charged at "
                    "$0/M as currently encoded, which is why output volume does not move the cost "
                    "column.",
                )
            )
    lines.append(
        _claim(
            LIMITATION,
            "**TypeSafe Console billing is authoritative.** These figures are this repository's "
            "arithmetic over one local price table; they are not an invoice, and an unknown "
            "resolved model produces `null` cost rather than another model's rate.",
        )
    )
    return lines + [""]


def _latency(records: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["## 12. Latency findings", ""]
    lines.append(
        _claim(
            DESIGN_ASSUMPTION,
            "latency here is local wall-clock around one logical call. It is recorded because it "
            "is free to record, not because this bench was built to measure it.",
        )
    )
    sessions = session_latency(records)
    positioned = [row for row in sessions if row["first_ms"] is not None]
    if positioned:
        lines.append("")
        lines += _table(
            ["run", "experiment", "calls", "first call (ms)", "slowest later (ms)", "ratio"],
            [
                (
                    f"`{row['run_id']}`",
                    f"`{row['experiment']}`",
                    row["calls"],
                    _number(row["first_ms"]),
                    _number(row["slowest_other_ms"]),
                    _ratio(row["first_ms"], row["slowest_other_ms"] or 0),
                )
                for row in positioned
            ],
        )
        lines.append("")
        ratios = [row["ratio"] for row in positioned if row["ratio"] is not None]
        slowest = [row for row in positioned if row["first_ms"] >= (row["slowest_other_ms"] or 0)]
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"the call that opened the client session was the slowest of its session in "
                f"**{len(slowest)} of {len(positioned)}** session(s) that record request position; "
                f"across those sessions the ratio ran from {min(ratios):.2f}x to {max(ratios):.2f}x.",
            )
        )
    unpositioned = [row for row in sessions if row["first_ms"] is None]
    if unpositioned:
        lines.append(
            _claim(
                LIMITATION,
                f"{len(unpositioned)} session(s) ({', '.join(f'`{row['experiment']}`' for row in unpositioned)}) "
                "predate the request-position fields. Their first call is not identified, their "
                "retries cannot be excluded, and this report does not average over them.",
            )
        )
    checks = within_run_first_call_checks(records)
    breaks = [check for check in checks if not check["head_was_slowest"]]
    if checks:
        lines.append(
            _claim(
                LOCAL_MEASUREMENT,
                f"within-run groups checked: {len(checks)}; groups whose first call was the "
                f"slowest: {len(checks) - len(breaks)}"
                + (
                    ". The exception(s): "
                    + "; ".join(
                        f"`{check['experiment']}` cycle {check['cycle']} opened at "
                        f"{_number(check['head_ms'])} ms and a later call in the same cycle took "
                        f"{_number(check['slowest_rest_ms'])} ms"
                        for check in breaks
                    )
                    + "."
                    if breaks
                    else "."
                ),
            )
        )
    recorded = [r for r in records if r.get("transport_attempt_count") is not None]
    single = [r for r in recorded if r.get("transport_attempt_count") == 1]
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"`transport_attempt_count` is recorded on {len(recorded)} of {len(records)} "
            f"record(s), and is 1 on {len(single)} of them. `attempts == 1` licenses exactly one "
            "sentence — that call was not observed to retry — and says nothing about what the "
            "window contained.",
        )
    )
    lines.append(
        _claim(
            LIMITATION,
            "`retry_count` is `null` on every record because the SDK sets the retry header on the "
            "request rather than the response. `null` means **not reported**, never `no retries`, "
            "and nothing here backfills it.",
        )
    )
    lines += [
        "",
        _claim(
            LIMITATION,
            "the window also contains DNS, TCP and TLS setup, connection-pool state, server-side "
            "queueing, upstream load, and local scheduling. Which of those moved a given call is "
            "not knowable from these records, and no decomposition is attempted.",
        ),
        "",
        f"**{LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK}**",
        "",
        _claim(
            LIMITATION,
            "no speedup table is produced and no arm is called faster on this evidence. The "
            "first-call pattern is a hypothesis these fields let a reader check, not a rule about "
            "the model.",
        ),
        "",
    ]
    return lines


def _architecture(records: Sequence[Mapping[str, Any]]) -> list[str]:
    measured = measured_experiment_names(records)
    return [
        "## 13. Agent-control architecture, distilled",
        "",
        _claim(
            DESIGN_ASSUMPTION,
            "**the pattern below is a design this bench followed, not a result it proved.** Each "
            "stage is a choice made before the run; the experiments behind it are "
            f"{', '.join(f'`{name}`' for name in measured) or 'none'}.",
        ),
        "",
        "```text",
        "unstructured state",
        "        ↓",
        "typed Jev questions            Choice / Score / Noul",
        "        ↓",
        "retain distributions + confidence",
        "        ↓",
        "ordinary Python policy",
        "        ↓",
        "optional: batching / fan-out",
        "        ↓",
        "deterministic arithmetic",
        "        ↓",
        "closed-set routing",
        "        ↓",
        "fail-closed authorization",
        "        ↓",
        "ordinary code",
        "```",
        "",
        _claim(
            DESIGN_ASSUMPTION,
            "**the model makes semantic judgments; the code does everything else.** Every "
            "arithmetic result in this report was computed in Python, and no question asked the "
            "model to count, sum, interpolate between score levels, or compare dates.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**the code owns the thresholds.** The confidence floor, the review threshold, and the "
            "composite weights are all code-side constants fixed before the run; the model never "
            "sees them and cannot move them.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**the code owns the side effects.** Handlers are registered in a dict, they are inert, "
            "and a route reaches one only after the policy allows it. Nothing the model returns is "
            "executed.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**closed sets over free-form generation.** A label from a frozen registry and an "
            "argument from that label's own frozen set are checkable; a sentence is not.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**confidence is a diagnostic and a policy input, never a correctness score.** It gates "
            "an action; it never edits an expectation and is never averaged into a result.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**keep the whole distribution.** The winning label is the smallest part of an answer: "
            "a near-tie and a unanimous label are the same entry in a count and different facts "
            "about the state.",
        ),
        _claim(
            DESIGN_ASSUMPTION,
            "**fail closed.** A malformed, missing, or unavailable answer stops the case; it is "
            "never defaulted, matched to a neighbour, or filled in from the branch that would have "
            "been taken.",
        ),
        "",
    ]


def handler_execution_reached(records: Sequence[Mapping[str, Any]]) -> bool:
    """Whether any routing record in this log reached its handler. Public: the tests read it."""
    group = [r for r in records if r.get("experiment") == ROUTING]
    if not group:
        return False
    return ACTUAL_HANDLER_EXECUTION_REALIZED in analyze_routing(group)["markers"]


def _not_established(records: Sequence[Mapping[str, Any]]) -> list[str]:
    if handler_execution_reached(records):
        execution_bullet = _claim(
            LIMITATION,
            "**one inert handler is not a real side effect.** The execution branch was reached, "
            "and the handler it reached writes nothing, sends nothing, and changes nothing outside "
            "this repository. No claim here extends to a handler that acts.",
        )
    else:
        execution_bullet = _claim(
            LIMITATION,
            "**the live allowed-handler execution path is untested.** "
            "`ACTUAL_HANDLER_EXECUTION_UNTESTED` stands: an allowed route has not been observed "
            "reaching `HANDLERS[name](argument)` under a real answer.",
        )
    return [
        "## 14. What this evaluation did not establish",
        "",
        _claim(LIMITATION, "**no general accuracy estimate.** There is no ground truth anywhere in "
               "this bench: expected labels are the design's intention, written alongside the "
               "states, and every count is over a handful of synthetic cases."),
        _claim(LIMITATION, "**no calibration claim.** Nothing here says a confidence of 0.8 "
               "corresponds to being right 80% of the time. Confidence was never compared against "
               "an outcome rate."),
        _claim(LIMITATION, "**no deterministic-model claim.** The opposite was observed: "
               "byte-identical requests returned differently-shaped distributions, so this model "
               "must be treated as producing variable answers."),
        _claim(LIMITATION, "**no universal repeatability bound.** Two payloads, five repeats each, "
               "two sessions. Nothing states a variance, a tolerance, or a bound that another "
               "payload would obey."),
        _claim(LIMITATION, "**no stable latency or speedup claim.** Sessions showed a slow first "
               "call and one in-run group broke the pattern; the window is not decomposable from "
               "these records."),
        _claim(LIMITATION, "**no general superiority over any other approach.** No LLM baseline was "
               "run, no alternative was benchmarked, and no comparison of that kind is implied."),
        _claim(LIMITATION, "**no universal batching ratio.** The batching and fan-out savings are "
               "properties of these payloads, where every question reads the same state."),
        _claim(LIMITATION, "**no proof that the composite dimensions are independent.** They are "
               "separate, atomic, and designed-orthogonal; their correlation was never measured."),
        _claim(LIMITATION, "**no real external side effect.** Every handler is inert. No file was "
               "written, no network call made, no message sent, no state changed outside this "
               "repository."),
        execution_bullet,
        _claim(LIMITATION, "**no production-safety certification.** Nothing here certifies this "
               "pattern as safe to run against real systems, real customer data, or real money."),
        "",
    ]


def _backlog(backlog: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["## 15. Optional edge-coverage backlog", "", f"**{OPTIONAL_EDGE_COVERAGE_BACKLOG}**", ""]
    if not backlog:
        return lines + [
            _claim(
                LOCAL_MEASUREMENT,
                f"all {len(EXPERIMENTS)} registered experiment(s) have at least one canonical "
                "record, so nothing is outstanding.",
            ),
            "",
        ]
    lines.append(
        _claim(
            LOCAL_MEASUREMENT,
            f"{len(backlog)} of {len(EXPERIMENTS)} registered experiment(s) have no canonical "
            "record. The list is computed from the registry and the log, so it empties itself as "
            "records arrive.",
        )
    )
    lines.append("")
    lines += _table(
        ["experiment", "tier", "planned calls", "what it would cover"],
        [
            (f"`{entry['name']}`", f"`{entry['tier']}`", entry["calls"], entry["intent"])
            for entry in backlog
        ],
    )
    lines += [
        "",
        _claim(LIMITATION, "these are **not** blockers for the freeze. They widen coverage of "
               "behaviour this bench already has a reading on; none of them is a core-capability "
               "question left unanswered, and running one would start a new measurement rather "
               "than complete this one."),
        "",
        _claim(DESIGN_ASSUMPTION, "the most load-bearing of them is `00_model_info`, a core-tier "
               "experiment that was never run: the alias-to-version resolution it exists to record "
               "is nevertheless in every record of the log, because every call records both the "
               "model requested and the model resolved."),
        "",
    ]
    return lines


def _secrets() -> list[str]:
    return [
        "## 16. Secret architecture",
        "",
        "```text",
        "TYPESAFE_API_KEY (environment)",
        "        ↓ overrides",
        ".secrets/typesafe.env  (repo root, git-ignored)",
        "        ↓ otherwise",
        "fail closed: no key, no request",
        "```",
        "",
        _claim(DESIGN_ASSUMPTION, "the credential has exactly two sources, resolved in that order "
               "by `jev_lab.client`. The environment wins when it is set, so an operator can "
               "override a stale file without editing it; there is no third source and no "
               "'search a few likely places' fallback."),
        _claim(DESIGN_ASSUMPTION, "an absent, empty, malformed, duplicated, or unreadable source "
               "stops the run before a request is sent. Nothing proceeds on a guess."),
        _claim(LIMITATION, "which of those two sources supplied the key for a given historical "
               "invocation is **not recorded in the canonical log**, so this report cannot "
               "reconstruct it. No record carries a credential source, and no other committed "
               "artifact is canonical for it. The two sources and their order are design facts "
               "stated above; which one answered a particular call is not a fact these records "
               "carry, and it is not inferred here."),
        _claim(LIMITATION, "the key is never printed, logged, hashed, fingerprinted, or measured "
               "here — not its value, length, prefix, suffix, or any derived identifier. Status "
               "reports `missing`, `exists (source=…)`, or `unusable (<kind>)` and nothing else."),
        _claim(LOCAL_MEASUREMENT, "the canonical log carries no credential material: no record "
               "names a credential source, and none carries an authorization header, an `sk-` "
               "prefix, or a token-shaped string."),
        _claim(DESIGN_ASSUMPTION, "that absence is checked rather than assumed: the offline suite "
               "scans the canonical log for those patterns and fails if one appears."),
        _claim(DESIGN_ASSUMPTION, "`.secrets/` is excluded by `.gitignore`; the check that proves "
               "it is `git check-ignore -v .secrets/typesafe.env` and a `git add --dry-run`, both "
               "of which the test suite runs. This document is not itself a security boundary, and "
               "no comment in it should be read as one."),
        _claim(LIMITATION, "the file's operating-system permissions are the platform's default and "
               "are not managed by this repository; on a shared or cloud-synced machine the "
               "directory may be readable by more than its owner."),
        "",
    ]


def _reproducibility(records: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        "## 17. Reproducibility index",
        "",
        "| artifact | role | regenerate with |",
        "| --- | --- | --- |",
        "| `results/usage.jsonl` | **canonical source of truth**, append-only | — never regenerated; "
        "only appended to by a real run |",
        "| `results/summary.csv` | derived | `uv run python -m jev_lab report` |",
        "| `results/summary.md` | derived | `uv run python -m jev_lab report` |",
        "| `results/capability_snapshot.md` | derived | `uv run python -m jev_lab snapshot` |",
        "| `results/JEV_LOCAL_EVALUATION_FINAL.md` | derived | "
        "`uv run python -m jev_lab final-report` |",
        "| `src/jev_lab/` | the bench: client, recorder, experiments, derivation modules | — |",
        "| `tests/` | offline suite; sockets are blocked and no test may call the API | "
        "`uv run pytest` |",
        "",
        _claim(LOCAL_MEASUREMENT, f"this report was derived from {len(records)} record(s). A "
               "revision of it that does not match the log is a stale copy of a derived file, not "
               "a second measurement."),
        _claim(LIMITATION, "nothing in this report is pinned to a revision, and the generator does "
               "not read the repository's version-control state: it is built from the log alone, so "
               "it cannot say which revision of the bench produced a record. The log's own hashes "
               "are the only fixity the records carry."),
        "",
    ]


# --------------------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------------------


def measured_experiment_names(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Registered experiments that have at least one record, in registry order."""
    measured = measured_counts(records)
    return [name for name in experiment_names() if measured.get(name)]


def build_final_report(records: Sequence[Mapping[str, Any]]) -> str:
    """Render the closing evaluation report for a list of canonical records."""
    if not records:
        return (
            "# Jev Local Evaluation\n\n"
            "No records in the log yet, so there is nothing to derive. Run an experiment first.\n"
        )
    summary = build_summary(records)
    lines: list[str] = []
    lines += _header(records)
    lines += _executive_summary(records, summary)
    lines += _primitives(records)
    lines += _addressing(records)
    lines += _confidence(records)
    lines += _instruction(records)
    lines += _batching(records)
    lines += _repeatability(records)
    lines += _fanout(records)
    lines += _composite(records)
    lines += _routing(records)
    lines += _ledger(summary, records)
    lines += _latency(records)
    lines += _architecture(records)
    lines += _not_established(records)
    lines += _backlog(optional_backlog(records))
    lines += _secrets()
    lines += _reproducibility(records)
    execution_marker = (
        ACTUAL_HANDLER_EXECUTION_REALIZED
        if handler_execution_reached(records)
        else ACTUAL_HANDLER_EXECUTION_UNTESTED
    )
    lines += [
        "---",
        "",
        f"`{CORE_CAPABILITY_EXPLORATION_CLOSED}` · "
        f"`{execution_marker}` · "
        f"`{LATENCY_NOT_ESTABLISHED_AS_MODEL_PERFORMANCE_BENCHMARK}` · "
        f"`{OPTIONAL_EDGE_COVERAGE_BACKLOG}`",
        "",
        "Derived from `results/usage.jsonl`, which remains the canonical record.",
        "",
    ]
    return _collapse_blank_lines(lines)


def _collapse_blank_lines(lines: Sequence[str]) -> str:
    """Join the sections, keeping at most one blank line between blocks.

    Each builder ends with its own spacer so it can be reused, which stacks up two where two
    chapters meet. Normalizing once here is cheaper than making every builder agree about who owns
    the separator.
    """
    out: list[str] = []
    for line in lines:
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    return "\n".join(out)


def write_final_report(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> Path | None:
    """Write the final report next to the log. Returns ``None`` when there is nothing to derive."""
    directory = Path(results_dir)
    records = list(read_records(directory / "usage.jsonl"))
    if not records:
        return None
    target = directory / FINAL_REPORT_NAME
    target.write_text(build_final_report(records), encoding="utf-8", newline="\n")
    return target
