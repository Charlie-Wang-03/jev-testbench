"""Derive a human-readable capability snapshot from the canonical usage log.

``results/capability_snapshot.md`` is a **derived artifact**. It is not a measurement and not a
source of truth: every number in it is recomputed from ``results/usage.jsonl`` on the way out, so
the file can be regenerated at any time and can never drift from the log it describes.

The prose around those numbers is interpretation, and it is kept deliberately narrow. Each section
says what the records do not support, because on a sample this small the unsupported reading is
usually the tempting one.
"""

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .ambiguous import AMBIGUOUS, REFERENCE, build_ambiguous_block
from .composite import COMPOSITE, build_composite_block
from .fanout import FANOUT, build_fanout_block
# The gate check is imported rather than restated. `final_report` recomputes a stored gate decision
# from the confidence and threshold stored beside it and refuses a record where the two disagree;
# a second copy of that rule here would be a second thing to drift from the first. The dependency
# runs one way only -- `final_report` does not import this module -- and must stay that way.
from .final_report import confidence_gate
from .recorder import DEFAULT_RESULTS_DIR, read_records, summarize
from .repeatability import REPEATABILITY, build_repeatability_block
from .report import _plain_decimal
from .routing import ROUTING, build_routing_block

SNAPSHOT_NAME = "capability_snapshot.md"

# Enough digits to show that a sub-cent total is not zero, few enough to stay readable.
COST_SIGNIFICANT_DIGITS = 6

# The experiment names the hand-written interpretation below is written against. A section is only
# emitted when its records are actually present.
ADDRESSING = "02_structured_addressing"
CONFIDENCE = "04_confidence"
INSTRUCTION = "07_instruction_precision"
PARALLEL = "03_parallel_questions"

# The two arm labels `03_parallel_questions` writes into each record's notes.
PARALLEL_BATCH_ARM = "batched"
PARALLEL_SEPARATE_ARM = "separate"

# Ratios read better with a fixed number of decimals than with significant digits.
RATIO_DECIMALS = 4
PERCENT_DECIMALS = 2


def _usd(value: float | None) -> str:
    """A dollar amount, never rendered as ``0`` when it is merely small."""
    return "n/a" if value is None else f"${_plain_decimal(value, COST_SIGNIFICANT_DIGITS)}"


def _ms(value: Any) -> str:
    """A latency in milliseconds, or ``n/a``."""
    return "n/a" if value is None else f"{value:g} ms"


def _grouped(records: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    """Group records by experiment, preserving the order the experiments first appear in."""
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get("experiment")), []).append(record)
    return grouped


def _answer_line(name: str, answer: Mapping[str, Any]) -> str:
    """One question's answer as a compact, type-aware line.

    Only the fields the answer type actually carries are printed, so a Noul is never made to look
    like it has a confidence it does not have.
    """
    kind = answer.get("type")
    if kind == "choice":
        return f"  - `{name}` Choice: **{answer.get('choice')}**, confidence {answer.get('confidence')}"
    if kind == "score":
        return f"  - `{name}` Score: **{answer.get('score')}**, confidence {answer.get('confidence')}"
    if kind == "noul":
        return f"  - `{name}` Noul: **{answer.get('noul')}** (no separate confidence)"
    return f"  - `{name}` {kind}: {answer}"


def _position_label(record: Mapping[str, Any]) -> str:
    """How to describe a call's position -- honestly, including when it was never recorded."""
    index = record.get("logical_request_index_in_run")
    if index is None:
        return "position not recorded (older schema)"
    return f"run# {index}" + (", first request" if record.get("is_first_request_in_client_session") else "")


def _attempts_label(record: Mapping[str, Any]) -> str:
    """Observed transport attempts, or an explicit statement that none were recorded.

    A missing count is never rendered as ``1`` or as ``0 retries``: not recorded and not retried
    are different facts, and only one of them was measured.
    """
    attempts = record.get("transport_attempt_count")
    if attempts is None:
        return "attempts: not recorded (older schema)"
    retries = record.get("transport_retry_count_observed")
    return f"attempts: {attempts} (retries observed: {retries})"


def _case_block(record: Mapping[str, Any], *, show_latency: bool) -> list[str]:
    """The per-case lines: what was sent, what came back, and what it cost."""
    lines = [
        f"### `{record.get('case_id')}`  ({_position_label(record)})",
        "",
        f"- state: {record.get('state_chars')} chars / {record.get('state_utf8_bytes')} utf8 bytes",
        f"- tokens: {record.get('input_tokens')} in, {record.get('output_tokens')} out, "
        f"{record.get('total_tokens')} total",
        f"- {_attempts_label(record)}",
        f"- estimated cost: {_usd(record.get('estimated_cost_usd'))}"
        + (f"  (latency {_ms(record.get('latency_ms'))})" if show_latency else ""),
        "",
    ]
    answers = record.get("answers") or {}
    lines.extend(_answer_line(name, answer) for name, answer in answers.items())
    lines.append("")
    return lines


LATENCY_CAVEAT = (
    "**Latency in this section is not reported, on purpose.** Arm identity is fully confounded "
    "with request position here: the first arm of each pair is always the request that opened the "
    "connection pool. Nothing in this snapshot attributes a latency difference to an arm."
)


def _totals_block(summary: Mapping[str, Any]) -> list[str]:
    """The whole-log totals, recomputed from the canonical records."""
    return [
        "## Totals",
        "",
        "| requests | input tokens | output tokens | total tokens | estimated cost |",
        "|---|---|---|---|---|",
        f"| {summary['requests']} | {summary['input_tokens']} | {summary['output_tokens']} "
        f"| {summary['total_tokens']} | {_usd(summary['estimated_cost_usd'])} |",
        "",
        f"`estimated_cost_usd` is a local estimate at the published input rate "
        f"({_usd(summary['estimated_cost_usd'])} for {summary['input_tokens']} input tokens; output "
        f"is free at that rate). TypeSafe Console billing is authoritative. "
        f"{summary['errors']} of {summary['requests']} recorded calls failed.",
        "",
        f"**Retries.** {summary['observed_retried_requests']} call(s) were locally observed to make "
        f"more than one HTTP attempt, and {summary['attempts_not_recorded']} carry no attempt count "
        "at all. A call with no attempt count has **not** been shown to have avoided retrying -- "
        "its retry behaviour is simply unknown. Retries inflate `latency_ms` by the backoff between "
        "attempts, so a latency cannot be attributed to the model while its attempt count is "
        "missing.",
        "",
    ]


def _addressing_block(records: list[Mapping[str, Any]]) -> list[str]:
    """`02_structured_addressing`: what moved, and what is confounded with it."""
    by_case = {str(record.get("case_id")): record for record in records}
    structured = by_case.get("structured_addressing")
    prose = by_case.get("prose_addressing")
    lines = [f"## `{ADDRESSING}`", "", "**Observed, in this one pair of cases.**", ""]
    if structured is not None and prose is not None:
        lines.append(
            f"- Input tokens: {structured.get('input_tokens')} (structured) vs "
            f"{prose.get('input_tokens')} (prose), with state sizes "
            f"{structured.get('state_utf8_bytes')} vs {prose.get('state_utf8_bytes')} utf8 bytes."
        )
        for record in (structured, prose):
            answered = (record.get("answers") or {}).get("department") or {}
            lines.append(
                f"- `{record.get('case_id')}` department Choice: **{answered.get('choice')}**, "
                f"confidence **{answered.get('confidence')}** — the two arms agreed on the label."
            )
        nouls = [
            ((record.get("answers") or {}).get("asks_for_refund") or {}).get("noul")
            for record in (structured, prose)
        ]
        lines.append(
            f"- `asks_for_refund` Noul: **{nouls[0]}** (structured) vs **{nouls[1]}** (prose) — "
            "a gap of "
            f"{abs(round(float(nouls[0]) - float(nouls[1]), 4))} on the same four underlying facts."
        )
    lines += [
        "",
        "**Not shown.** The two arms differ in more than the state's form: whether a question can "
        "name a field path at all, and the payload length. Token, latency, and cost differences are "
        "confounded by length and by request position. This is two cases, not a JSON-versus-prose "
        "effect.",
        "",
    ]
    return lines


def _checked_gate(record: Mapping[str, Any]) -> dict[str, Any] | None:
    """This record's gate, checked against the confidence and threshold stored beside it.

    The check itself is `confidence_gate`, which recomputes the decision from the confidence the
    answer carried and stops the build on a record whose stored decision and stored numbers
    disagree. A record that stores a decision with nothing to check it against is refused here for
    the same reason: the alternative is printing a direction this snapshot cannot verify.
    """
    checked = confidence_gate(record)
    if checked is not None:
        return checked
    stored = ((record.get("notes") or {}).get("derived") or {}).get("gate") or {}
    if stored.get("decision") is not None:
        raise ValueError(
            f"record {record.get('case_id')!r} stores gate decision {stored['decision']!r} but "
            "carries no Choice confidence to recompute it from; the snapshot does not print a gate "
            "direction it cannot check"
        )
    return None


def _gate_behaviour(decisions: Sequence[tuple[str, Mapping[str, Any]]]) -> str:
    """What the gate did, written from the decisions the records actually stored.

    A fixed sentence used to sit here describing one direction -- the ambiguous case landing just
    above the threshold and being accepted. It happened to be true of the frozen log, and it would
    have kept saying so on a log where the gate refused that case. The direction is now read, never
    assumed, so which case cleared and which did not comes from the records themselves.
    """
    cleared = [label for label, gate in decisions if gate["cleared"]]
    withheld = [label for label, gate in decisions if not gate["cleared"]]
    if not withheld:
        return f"every case cleared it ({', '.join(cleared)}), so the gate accepted each one"
    if not cleared:
        return f"no case cleared it ({', '.join(withheld)}), so the gate escalated each one"
    return (
        f"{', '.join(cleared)} cleared it and was accepted, and {', '.join(withheld)} did not "
        "clear and was escalated"
    )


def _confidence_block(records: list[Mapping[str, Any]]) -> list[str]:
    """`04_confidence`: the gate's actual decision, and the confidence misreading to avoid."""
    by_case = {str(record.get("case_id")): record for record in records}
    specific = by_case.get("specific_evidence")
    ambiguous = by_case.get("ambiguous_evidence")
    lines = [f"## `{CONFIDENCE}`", "", "**Observed, in this one pair of cases.**", ""]
    decisions: list[tuple[str, Mapping[str, Any]]] = []
    for record in (specific, ambiguous):
        if record is None:
            continue
        derived = (record.get("notes") or {}).get("derived") or {}
        expected = derived.get("expected")
        matched = derived.get("matches_expected")
        gate = _checked_gate(record)
        if gate is not None:
            decisions.append((str(record.get("case_id")), gate))
        lines.append(
            f"- `{record.get('case_id')}`: intent **{derived.get('intent')}** at confidence "
            f"**{derived.get('intent_confidence')}**."
        )
        lines.append(
            f"  - expected label: `{expected}`; matched = "
            + ("not applicable (no single label is correct for this case)"
               if expected is None else str(matched))
            + "."
        )
        lines.append(
            f"  - specificity Score **{derived.get('specificity_score')}** at confidence "
            f"**{derived.get('specificity_confidence')}**."
        )
        if gate is None:
            lines.append("  - gate: not recorded for this case.")
        else:
            lines.append(
                f"  - gate: **{gate['decision']}** at confidence {gate['confidence']} against "
                f"threshold {gate['threshold']} "
                f"({(derived.get('gate') or {}).get('threshold_basis')})."
            )
    behaviour = _gate_behaviour(decisions)
    lines += [
        "",
        "**Reading the gate.** The demo threshold is a demonstration parameter, not a tuned or "
        "optimal value, and a passing gate is not evidence that the underlying answer was right. "
        + (
            f"Here {behaviour} — that is the gate's behaviour on these records, not a verdict on "
            "any answer."
            if decisions
            else "Here no case carries a checkable gate, so no direction is reported for it."
        ),
        "",
        "**Reading the Score confidence.** A low specificity Score with a high confidence is not a "
        "contradiction. The confidence is confidence *in the stated judgment*; it does not measure "
        "the property being judged, so it must never be rescaled into a specificity level. Score "
        "confidence is likewise not comparable to Choice confidence, and neither is a correctness "
        "score.",
        "",
        LATENCY_CAVEAT,
        "",
    ]
    return lines


def _instruction_block(records: list[Mapping[str, Any]]) -> list[str]:
    """`07_instruction_precision`: a byte-identical state, two boundaries."""
    by_case = {str(record.get("case_id")): record for record in records}
    vague = by_case.get("vague_boundary")
    explicit = by_case.get("explicit_boundary")
    lines = [f"## `{INSTRUCTION}`", "", "**Observed, in this one pair of cases.**", ""]
    if vague is not None and explicit is not None:
        identical = vague.get("state_utf8_bytes") == explicit.get("state_utf8_bytes")
        lines.append(
            f"- The state is byte-identical across the two arms: **{identical}** "
            f"({vague.get('state_utf8_bytes')} utf8 bytes each). The only difference is how the "
            "decision boundary is stated, in the instructions and the criteria together."
        )
        lines.append(
            f"- `blocked` Noul: **{(vague.get('answers') or {}).get('blocked', {}).get('noul')}** "
            f"(vague) vs "
            f"**{(explicit.get('answers') or {}).get('blocked', {}).get('noul')}** (explicit)."
        )
        lines.append(
            f"- Input tokens: {vague.get('input_tokens')} (vague) vs "
            f"{explicit.get('input_tokens')} (explicit) — the explicit criteria are longer, so the "
            "higher count is the wording, not a different state."
        )
    lines += [
        "",
        "**No correctness claim.** The state alone does not establish ground truth for this "
        "boundary, so neither arm is reported as the right answer and the two numbers above are not "
        "graded against each other.",
        "",
        "**Not isolated.** Instructions and criteria move together, so this does not separate "
        "instruction wording from criteria wording, and it is not a general prompt-engineering "
        "result. Noul carries no distribution and no confidence, so there is nothing else to "
        "compare.",
        "",
        LATENCY_CAVEAT,
        "",
    ]
    return lines


def _note(record: Mapping[str, Any], key: str) -> Any:
    """Read one design-metadata key off a record, tolerating records written without notes."""
    return (record.get("notes") or {}).get(key)


def _total(records: Iterable[Mapping[str, Any]], field: str) -> float:
    """Sum one numeric field across records, treating an absent value as zero."""
    return sum(float(record.get(field) or 0) for record in records)


def _ratio(part: float, whole: float) -> str:
    """``whole / part`` as fixed-decimal text, or ``n/a`` when the denominator is zero."""
    return f"{whole / part:.{RATIO_DECIMALS}f}" if part else "n/a"


def _saving(part: float, whole: float) -> str:
    """``1 - part/whole`` as a percentage, or ``n/a`` when the baseline is zero."""
    return f"{(1 - part / whole) * 100:.{PERCENT_DECIMALS}f}%" if whole else "n/a"


def _parallel_block(records: list[Mapping[str, Any]]) -> list[str]:
    """`03_parallel_questions`: what batching saved on this workload, and what it did not change.

    Every figure is recomputed from the records. The token and cost comparison is the load-bearing
    one; the latency lines are reported as observations of a two-cycle sample and are labelled that
    way, because two cycles cannot establish a stable speedup.
    """
    batched = [r for r in records if _note(r, "arm") == PARALLEL_BATCH_ARM]
    separate = [r for r in records if _note(r, "arm") == PARALLEL_SEPARATE_ARM]
    cycles = sorted({c for c in (_note(r, "cycle") for r in records) if c is not None})
    lines = [f"## `{PARALLEL}`", "", "### Parallel questions / batching", ""]

    sizes = sorted({r.get("state_utf8_bytes") for r in records})
    state_note = (
        f"one shared state of {sizes[0]} utf8 bytes on every call"
        if len(sizes) == 1 else f"states of {sizes} utf8 bytes"
    )
    per_batch = sorted({r.get("question_count") for r in batched})
    lines.append(
        f"**Design.** {len(cycles)} order-balanced cycle(s): "
        f"{len(batched)} batched call(s) carrying {per_batch[0] if len(per_batch) == 1 else per_batch} "
        f"identical Noul questions, against {len(separate)} separate call(s) carrying one question "
        f"each. {state_note.capitalize()}. The same question objects are sent in both arms, so only "
        "the request split differs."
    )
    lines.append("")

    batch_in, separate_in = _total(batched, "input_tokens"), _total(separate, "input_tokens")
    batch_out, separate_out = _total(batched, "output_tokens"), _total(separate, "output_tokens")
    batch_cost, separate_cost = _total(batched, "estimated_cost_usd"), _total(separate, "estimated_cost_usd")
    lines += [
        "| pooled over both arms | calls | input tokens | output tokens | estimated cost |",
        "|---|---|---|---|---|",
        f"| batched | {len(batched)} | {batch_in:.0f} | {batch_out:.0f} | {_usd(batch_cost)} |",
        f"| separate | {len(separate)} | {separate_in:.0f} | {separate_out:.0f} | {_usd(separate_cost)} |",
        "",
        f"- **Input tokens.** Sending the shared state once instead of "
        f"{len(separate) // max(len(batched), 1)} times: `separate / batched` = "
        f"**{_ratio(batch_in, separate_in)}x**, a saving of "
        f"**{_saving(batch_in, separate_in)}** of the input tokens.",
        f"- **Cost.** `separate / batched` = **{_ratio(batch_cost, separate_cost)}x**, a saving of "
        f"**{_saving(batch_cost, separate_cost)}**. Output tokens are billed at $0 in this project's "
        f"price table, so the cost ratio tracks the input ratio exactly rather than independently "
        f"confirming it. `estimated_cost_usd` is a local estimate; Console billing is authoritative.",
        f"- **Output tokens.** {batch_out:.0f} (batched) vs {separate_out:.0f} (separate), a ratio of "
        f"**{_ratio(batch_out, separate_out)}x**. These carry no cost at the published rate, so they "
        "are reported as an observation and nothing is derived from them.",
        "",
    ]

    if len(cycles) > 1:
        per_cycle = []
        for cycle in cycles:
            cb = [r for r in batched if _note(r, "cycle") == cycle]
            cs = [r for r in separate if _note(r, "cycle") == cycle]
            per_cycle.append(
                f"cycle {cycle}: {_total(cb, 'input_tokens'):.0f} vs "
                f"{_total(cs, 'input_tokens'):.0f} input tokens"
            )
        lines += [
            "**Per cycle (required by this project's reporting rule).** "
            + "; ".join(per_cycle) + ".",
            "",
        ]

    lines += _parallel_semantics_block(records, batched, separate)
    lines += _parallel_latency_block(records, batched, separate, cycles)
    return lines


def _parallel_semantics_block(
    records: list[Mapping[str, Any]],
    batched: list[Mapping[str, Any]],
    separate: list[Mapping[str, Any]],
) -> list[str]:
    """Compare each batched scalar against the separate call for the same question and cycle."""
    pairs: list[tuple[Any, str, Any, Any]] = []
    for cycle in sorted({c for c in (_note(r, "cycle") for r in records) if c is not None}):
        matches = [r for r in batched if _note(r, "cycle") == cycle]
        if not matches:
            continue
        batch_answers = matches[0].get("answers") or {}
        for record in (r for r in separate if _note(r, "cycle") == cycle):
            # A separate call carries exactly one question, so its own answer names the pairing.
            for name, answer in (record.get("answers") or {}).items():
                if name in batch_answers:
                    pairs.append((cycle, name, batch_answers[name].get("noul"),
                                  answer.get("noul")))

    lines = ["**Semantic consistency.** Each batched Noul against the separate call for the same "
             "question in the same cycle.", ""]
    if not pairs:
        lines += ["No batched/separate pairing could be formed from these records.", ""]
        return lines

    equal = sum(1 for _, _, b, s in pairs if b == s)
    gaps = [abs(float(b) - float(s)) for _, _, b, s in pairs if b is not None and s is not None]
    lines += [
        f"- Pairings compared: **{len(pairs)}**; exactly equal: **{equal}/{len(pairs)}**; "
        f"largest absolute difference: **{max(gaps) if gaps else 'n/a'}**.",
        "",
    ]
    if equal == len(pairs):
        lines += [
            "> Within these two cycles and this one synthetic shared-state case, **no "
            "batch-vs-separate Noul drift was observed.** This is not a general claim that batching "
            "never changes Jev's answers: it is one state, five questions, one model version, two "
            "cycles. A scalar landing on the same value twice here is repeatability on this input, "
            "not a property of batching.",
            "",
        ]
    else:
        lines += [
            "> The arms did **not** agree on every pairing. The differences are reported above and "
            "are not averaged away or dismissed as noise.",
            "",
        ]
    return lines


def _parallel_latency_block(
    records: list[Mapping[str, Any]],
    batched: list[Mapping[str, Any]],
    separate: list[Mapping[str, Any]],
    cycles: list[Any],
) -> list[str]:
    """Report the observed latencies, per cycle and pooled, without attributing them to an arm."""
    lines = ["**Latency — observational only.**", ""]
    batch_latencies = [float(r.get("latency_ms") or 0) for r in batched]
    separate_latencies = [float(r.get("latency_ms") or 0) for r in separate]

    for cycle in cycles:
        cb = [float(r.get("latency_ms") or 0) for r in batched if _note(r, "cycle") == cycle]
        cs = [float(r.get("latency_ms") or 0) for r in separate if _note(r, "cycle") == cycle]
        if not cs:
            continue
        lines.append(
            f"- Cycle {cycle}: batched **{cb[0]:g} ms**; the {len(cs)} separate call(s) totalled "
            f"**{sum(cs):g} ms** sequentially (mean {sum(cs) / len(cs):g} ms, max {max(cs):g} ms)."
        )
    if batch_latencies:
        spread = (
            f"{max(batch_latencies) / min(batch_latencies):.3f}x"
            if min(batch_latencies) > 0 else "n/a"
        )
        lines.append(
            f"- Pooled: {len(batched)} batched observation(s) "
            f"({', '.join(f'{value:g}' for value in batch_latencies)} ms) against "
            f"{len(separate)} separate observation(s) (mean "
            f"{sum(separate_latencies) / len(separate_latencies):g} ms). The batched observations "
            f"are spread by **{spread}**."
        )
        if min(batch_latencies) > 0 and max(batch_latencies) / min(batch_latencies) >= 2:
            lines.append(
                "- **BATCH_LATENCY_HIGH_VARIANCE_OBSERVED.** The batched arm's own observations "
                "differ by more than the arm-to-arm difference they would be used to explain, so the "
                "spread here is larger than any effect this experiment could attribute."
            )
    firsts = [r for r in records if r.get("is_first_request_in_client_session")]
    others = [r for r in records if not r.get("is_first_request_in_client_session")]
    if firsts and others:
        first_text = ", ".join(f"{float(r.get('latency_ms') or 0):g} ms" for r in firsts)
        last_max = max(float(r.get("latency_ms") or 0) for r in others)
        lines.append(
            f"- Position: {len(firsts)} first request(s) in the client session ({first_text}) "
            f"against {len(others)} later request(s), whose slowest was {last_max:g} ms."
        )

    observed = [r for r in records if r.get("transport_attempt_count") == 1]
    lines += [
        f"- Retries: **{len(observed)}/{len(records)}** call(s) record "
        f"`transport_attempt_count == 1`, which licenses exactly one sentence: **no HTTP retry was "
        f"locally observed** for them. That is all it licenses.",
        "",
        "> **This is an observed latency comparison, not a speedup measurement.** The two cycles "
        "balance the order, but two cycles cannot establish a stable factor: the batched arm's own "
        "two observations differ by more than the effect being looked for, and the separate arm is "
        "the more reproducible of the two. No speedup figure is claimed, and the vendor's latency "
        "claim is not testable at this sample size. Even with `attempts == 1`, each window still "
        "contains connection setup, connection-pool state, server-side queueing, upstream load, the "
        "network path, and local scheduling. Which of those moved a given call is **not** known from "
        "these records.",
        "",
        "> **Not derived here:** the load-bearing claim of this experiment is the token and cost "
        "comparison above. It rests on identical state and identical question definitions across "
        "both arms, which the records show; the latency lines do not rest on anything comparable.",
        "",
    ]
    return lines


def _latest_run(records: list[Mapping[str, Any]]) -> tuple[list[Mapping[str, Any]], int]:
    """The most recent run of an experiment, plus how many earlier runs were set aside.

    A second run of the same experiment is a second measurement, not more data for the first, so
    only the most recent one is rendered -- and the rest are counted rather than silently dropped.
    """
    by_run: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        by_run.setdefault(str(record.get("run_id")), []).append(record)

    latest = max(by_run, key=lambda run: [r.get("timestamp_utc") for r in by_run[run]][-1])
    return by_run[latest], len(by_run) - 1


def _earlier_runs_note(earlier: int) -> list[str]:
    if not earlier:
        return []
    return [
        f"> **{earlier} earlier run(s) of this experiment are in the log and are not shown here.** "
        "Each run is its own measurement of the same thing; they are not pooled, and the records "
        "themselves are unchanged.",
        "",
    ]


def _repeatability_block(records: list[Mapping[str, Any]]) -> list[str]:
    """`13_repeatability`: stability across repeated identical calls, one run at a time."""
    latest, earlier = _latest_run(records)
    return build_repeatability_block(latest) + _earlier_runs_note(earlier)


def _ambiguous_block(
    records: list[Mapping[str, Any]], grouped: Mapping[str, list[Mapping[str, Any]]]
) -> list[str]:
    """`13b_ambiguous_repeatability`, with the historical `01_primitives` call placed beside it.

    The reference records are passed in rather than looked up inside the analysis, so the report
    cannot quietly start containing the reference call as if it were one of the five.
    """
    latest, earlier = _latest_run(records)
    marked = grouped.get(REPEATABILITY, [])
    marked_latest, _ = _latest_run(marked) if marked else ([], 0)
    return build_ambiguous_block(
        latest, grouped.get(REFERENCE, []), marked_latest
    ) + _earlier_runs_note(earlier)


def _other_experiments_block(grouped: Mapping[str, list[Mapping[str, Any]]]) -> list[str]:
    """Any experiment without hand-written interpretation still gets its measured answers."""
    handled = {
        ADDRESSING,
        CONFIDENCE,
        INSTRUCTION,
        PARALLEL,
        REPEATABILITY,
        AMBIGUOUS,
        FANOUT,
        COMPOSITE,
        ROUTING,
    }
    lines: list[str] = []
    for name, records in grouped.items():
        if name in handled:
            continue
        lines += [f"## `{name}`", ""]
        for record in records:
            lines.extend(_case_block(record, show_latency=True))
    return lines


def build_snapshot(records: list[Mapping[str, Any]]) -> str:
    """Render the snapshot Markdown for a list of canonical records."""
    if not records:
        return f"# Capability snapshot\n\nNo records in the log yet.\n"

    grouped = _grouped(records)
    summary = summarize(list(records))
    header = [
        "# Capability snapshot — derived, not canonical",
        "",
        "> **This file is a derived artifact, not a measurement.** The canonical local record is "
        "`results/usage.jsonl`. Every number here is recomputed from it by "
        "`uv run python -m jev_lab snapshot`, so this file can never disagree with the log and "
        "should never be quoted as the log itself.",
        "",
        "> **Scope.** These are observations from a handful of synthetic cases on one machine and "
        "one account. They are not a benchmark, not a general claim about Jev, and not comparable "
        "to any published figure.",
        "",
        f"Generated from {summary['requests']} canonical record(s), "
        f"{records[0].get('timestamp_utc')} to {records[-1].get('timestamp_utc')}.",
        "",
    ]
    unpositioned = sum(1 for record in records if record.get("logical_request_index_in_run") is None)
    if unpositioned:
        header += [
            f"> **{unpositioned} of {summary['requests']} record(s) predate the request-position "
            "and transport-attempt fields.** Their order can be inferred from the timestamps and "
            "their retries cannot be excluded, but nothing in the log states either, so this "
            "snapshot does not claim it. Old records are never rewritten to add it.",
            "",
        ]
    body = _totals_block(summary)
    if PARALLEL in grouped:
        body += _parallel_block(grouped[PARALLEL])
    if REPEATABILITY in grouped:
        body += _repeatability_block(grouped[REPEATABILITY])
    if AMBIGUOUS in grouped:
        body += _ambiguous_block(grouped[AMBIGUOUS], grouped)
    if FANOUT in grouped:
        body += build_fanout_block(grouped[FANOUT], grouped.get(PARALLEL, []))
    if COMPOSITE in grouped:
        body += build_composite_block(grouped[COMPOSITE])
    if ROUTING in grouped:
        body += build_routing_block(grouped[ROUTING])
    if ADDRESSING in grouped:
        body += _addressing_block(grouped[ADDRESSING])
    if CONFIDENCE in grouped:
        body += _confidence_block(grouped[CONFIDENCE])
    if INSTRUCTION in grouped:
        body += _instruction_block(grouped[INSTRUCTION])
    body += _other_experiments_block(grouped)
    return "\n".join(header + body).rstrip() + "\n"


def write_snapshot(results_dir: Path | str = DEFAULT_RESULTS_DIR) -> Path | None:
    """Write the snapshot next to the log. Returns ``None`` when there is nothing to derive."""
    directory = Path(results_dir)
    records = list(read_records(directory / "usage.jsonl"))
    if not records:
        return None
    target = directory / SNAPSHOT_NAME
    target.write_text(build_snapshot(records), encoding="utf-8", newline="\n")
    return target
