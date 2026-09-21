"""Derive run-to-run stability statistics from repeated identical calls.

``13_repeatability`` sends one byte-identical request several times. This module reads those
records back and reports how much moved. It is a **derived view**: every number is recomputed from
``results/usage.jsonl``, and nothing here is a second source of truth.

Two rules shape the wording below, and both exist because the tempting sentence is wrong:

* These records show what was observed, not why. Identical inputs producing identical outputs is
  reported as *no drift observed*; identical inputs producing different outputs is reported as
  *observed variation*. Neither is promoted into a claim about how an answer was produced, and no
  internal mechanism is named, because this project has no official documentation of one.
* Token usage is analysed on its own footing. The payload is identical across calls, but that is
  not a reason to assume the reported usage is: if the token counts differ, that is a finding about
  accounting rather than a mistake to be smoothed over.
"""

import statistics
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

REPEATABILITY = "13_repeatability"

# Markers the analysis raises when the data warrants them. They are literal strings so a reader (and
# a test) can find them.
TOKEN_ACCOUNTING_VARIATION_OBSERVED = "TOKEN_ACCOUNTING_VARIATION_OBSERVED"
SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED = "SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED"
EXACT_TOP_PROBABILITY_TIE_OBSERVED = "EXACT_TOP_PROBABILITY_TIE_OBSERVED"

# How much of a value's own magnitude a drift has to exceed before it is called a drift at all.
# Float equality on values the API returns as decimals is not the point here; this is a floor for
# "the number moved", not a significance test.
EXACT_EPSILON = 0.0

# Demonstration parameters. Both bound how a result is *described*; neither gates an experiment, and
# neither suppresses a number. A run that exceeds either is reported as exceeding it.
#
# The Noul range at or below which observed movement is called small.
SMALL_NOUL_RANGE = 0.05
# The leading probability at or above which a probability field is called concentrated.
CONCENTRATED_TOP_PROBABILITY = 0.9

# The precision `latency_ms` is stored at. Printing matches it exactly rather than rounding again.
LATENCY_DECIMALS = 3


def _answers(record: Mapping[str, Any]) -> Mapping[str, Any]:
    return record.get("answers") or {}


def _by_type(records: Sequence[Mapping[str, Any]], kind: str) -> list[tuple[str, Mapping[str, Any]]]:
    """Every answer of one type, as ``(question_name, answer)`` pairs, in record order.

    A call that failed contributes no answers and is simply absent here; the caller reports how many
    calls were analysed so a short list is never mistaken for agreement.
    """
    found: list[tuple[str, Mapping[str, Any]]] = []
    for record in records:
        for name, answer in _answers(record).items():
            if isinstance(answer, Mapping) and answer.get("type") == kind:
                found.append((name, answer))
    return found


def _summary(values: Sequence[float]) -> dict[str, float] | None:
    """min / max / mean / range for a list of numbers, or ``None`` when there are none."""
    if not values:
        return None
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "range": max(values) - min(values),
    }


def _distribution(pairs: Iterable[tuple[Any, float]]) -> dict[str, dict[str, float]]:
    """Group a stream of ``(key, value)`` into per-key min/max/mean."""
    grouped: dict[str, list[float]] = {}
    for key, value in pairs:
        grouped.setdefault(str(key), []).append(float(value))
    return {key: _summary(values) for key, values in sorted(grouped.items())}


def _label_summary(labels: Sequence[str | None]) -> dict[str, Any]:
    """How often the same label came back, and what the field of labels looked like."""
    present = [label for label in labels if label is not None]
    if not present:
        return {"labels": list(labels), "agreeing_count": 0, "agreeing_label": None, "distinct": 0}
    counts = {label: present.count(label) for label in dict.fromkeys(present)}
    best = max(counts.values())
    # On a tie, name the label that appeared first, so the report never implies a winner that the
    # data does not pick.
    winner = next(label for label in dict.fromkeys(present) if counts[label] == best)
    return {
        "labels": list(labels),
        "agreeing_count": best,
        "agreeing_label": winner,
        "distinct": len(counts),
        "counts": counts,
    }


def analyze(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Recompute every stability statistic for one run of identical calls.

    ``records`` should be the records of a single run, in call order. Only ``status == "ok"`` rows
    carry answers, so failures are excluded from the semantic statistics and counted separately --
    a failed call is not agreement.
    """
    ordered = list(records)
    ok = [record for record in ordered if record.get("status") == "ok"]
    failed = len(ordered) - len(ok)

    choice_pairs = _by_type(ok, "choice")
    score_pairs = _by_type(ok, "score")
    noul_pairs = _by_type(ok, "noul")

    choice = _choice_block(choice_pairs)
    score = _score_block(score_pairs)
    noul = _noul_block(noul_pairs)
    tokens = _token_block(ok)
    transport = _transport_block(ordered)

    resolved = [record.get("model_resolved") for record in ok]
    input_tokens = [int(record.get("input_tokens") or 0) for record in ok]
    latencies = [record.get("latency_ms") for record in ordered]

    noul_range = (noul["summary"] or {}).get("range")
    tied_calls = sum(1 for row in choice["ranking"] + score["ranking"] if row.get("tied"))
    markers = []
    if tokens["varies"]:
        markers.append(TOKEN_ACCOUNTING_VARIATION_OBSERVED)
    if noul_range is not None and EXACT_EPSILON < noul_range <= SMALL_NOUL_RANGE:
        markers.append(SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED)
    if tied_calls:
        markers.append(EXACT_TOP_PROBABILITY_TIE_OBSERVED)

    return {
        "calls": len(ordered),
        "ok_calls": len(ok),
        "failed_calls": failed,
        "choice": choice,
        "score": score,
        "noul": noul,
        "tokens": tokens,
        "model": {
            "resolved": resolved,
            "consistent": len(set(resolved)) <= 1 and bool(resolved),
            "requested": sorted({str(record.get("model_requested")) for record in ordered}),
        },
        "transport": transport,
        "latency": {
            "values": latencies,
            "first": next(
                (record.get("latency_ms") for record in ordered
                 if record.get("is_first_request_in_client_session")), None),
            "others": [record.get("latency_ms") for record in ordered
                       if not record.get("is_first_request_in_client_session")],
        },
        # Where on its scale each field landed. A field at the end of its scale repeats for reasons a
        # field in the middle need not share, so a run made only of the former is reported as such.
        "shape": {
            "choice_saturated": choice["saturated"],
            "choice_top_probability": choice["top_probability"],
            "score_top_probability": score["top_probability"],
            "score_concentrated": score["concentrated"],
        },
        "markers": markers,
        # The invariant this experiment exists to hold. A caller that got here with a varying
        # payload has measured something other than repeatability, and the report says so.
        "payload_identical": len({tuple(sorted(_answers(record))) for record in ordered}) <= 1,
        "input_tokens_identical": len(set(input_tokens)) <= 1,
    }


def _flat_probabilities(pairs: Sequence[tuple[str, Mapping[str, Any]]]) -> list[float]:
    """Every probability in a field, across every call, with its option or level name dropped."""
    return [float(value) for _, answer in pairs
            for value in (answer.get("probabilities") or {}).values()]


def _ranking(
    pairs: Sequence[tuple[str, Mapping[str, Any]]], label_key: str | None = None
) -> list[dict[str, Any]]:
    """Per call, the two leading options and the gap between them.

    The gap is the whole point of a near-tie case: a field whose top two options sit 0.01 apart can
    come back in either order without either ordering being wrong, and that is invisible in a label
    count alone.

    An exact tie has no first place. When the answer names one of the tied options -- Choice reports
    the label it picked -- that name is used, because otherwise a name-ordering convention here
    would contradict the label the API itself returned. With no name to prefer, the tie is broken
    alphabetically so this function returns the same ranking every time it reads the same record,
    and the row is flagged as tied so the report can say so.
    """
    rows: list[dict[str, Any]] = []
    for _, answer in pairs:
        field = {str(key): float(value) for key, value in (answer.get("probabilities") or {}).items()}
        if len(field) < 2:
            rows.append({"leader": None, "runner_up": None, "margin": None, "tied": False,
                         "leader_probability": None, "runner_up_probability": None})
            continue
        ranked = sorted(field.items(), key=lambda item: (-item[1], item[0]))
        tied = ranked[0][1] == ranked[1][1]
        reported = answer.get(label_key) if label_key else None
        if tied and reported in (ranked[0][0], ranked[1][0]):
            ranked = [(str(reported), field[str(reported)])] + [
                item for item in ranked if item[0] != str(reported)]
        (leader, best), (runner_up, second) = ranked[0], ranked[1]
        rows.append({
            "leader": leader,
            "runner_up": runner_up,
            "leader_probability": best,
            "runner_up_probability": second,
            "margin": best - second,
            "tied": tied,
        })
    return rows


def _switches(names: Sequence[str | None]) -> int:
    """How many times a sequence of names changes from one call to the next."""
    return sum(1 for previous, current in zip(names, names[1:]) if previous != current)


def _choice_block(pairs: Sequence[tuple[str, Mapping[str, Any]]]) -> dict[str, Any]:
    labels = [answer.get("choice") for _, answer in pairs]
    probabilities = _distribution(
        (key, value)
        for _, answer in pairs
        for key, value in (answer.get("probabilities") or {}).items()
    )
    spread = None
    if probabilities:
        spread = max(summary["max"] - summary["min"] for summary in probabilities.values())
    confidences = [float(answer["confidence"]) for _, answer in pairs
                   if answer.get("confidence") is not None]
    flat = _flat_probabilities(pairs)
    ranking = _ranking(pairs, label_key="choice")
    leaders = [row["leader"] for row in ranking]
    runners_up = [row["runner_up"] for row in ranking]
    return {
        "question": pairs[0][0] if pairs else None,
        "labels": _label_summary(labels),
        "probabilities": probabilities,
        "max_probability_spread": spread,
        "confidence": _summary(confidences),
        "top_probability": max(flat) if flat else None,
        # Exact, so it needs no parameter: every option was a certainty or an impossibility.
        "saturated": bool(flat) and all(value in (0.0, 1.0) for value in flat),
        "ranking": ranking,
        "leaders": leaders,
        "runner_up": _label_summary(runners_up),
        "margins": [row["margin"] for row in ranking],
        "margin_summary": _summary([row["margin"] for row in ranking
                                    if row["margin"] is not None]),
        # The two ways a near-tie can be unstable: the ordering between the top two changes, or the
        # pair occupying those places changes even though the order does not.
        "leader_switches": _switches(leaders),
        "runner_up_switches": _switches(runners_up),
        "observed": len(pairs),
    }


def _score_block(pairs: Sequence[tuple[str, Mapping[str, Any]]]) -> dict[str, Any]:
    scores = [float(answer["score"]) for _, answer in pairs if answer.get("score") is not None]
    probabilities = _distribution(
        (key, value)
        for _, answer in pairs
        for key, value in (answer.get("probabilities") or {}).items()
    )
    spread = None
    if probabilities:
        spread = max(summary["max"] - summary["min"] for summary in probabilities.values())
    confidences = [float(answer["confidence"]) for _, answer in pairs
                   if answer.get("confidence") is not None]
    top = max(_flat_probabilities(pairs), default=None)
    ranking = _ranking(pairs)
    levels = [row["leader"] for row in ranking]
    return {
        "question": pairs[0][0] if pairs else None,
        "values": scores,
        "summary": _summary(scores),
        "probabilities": probabilities,
        "max_probability_spread": spread,
        "confidence": _summary(confidences),
        "top_probability": top,
        "concentrated": top is not None and top >= CONCENTRATED_TOP_PROBABILITY,
        "ranking": ranking,
        # Which ordinal level carried the most mass, and whether that changed between calls. On a
        # rubric with two live levels this is the score's equivalent of a flipped label.
        "dominant_levels": levels,
        "dominant_level_switches": _switches(levels),
        "margins": [row["margin"] for row in ranking],
        "margin_summary": _summary([row["margin"] for row in ranking
                                    if row["margin"] is not None]),
        "observed": len(pairs),
    }


def _noul_block(pairs: Sequence[tuple[str, Mapping[str, Any]]]) -> dict[str, Any]:
    values = [float(answer["noul"]) for _, answer in pairs if answer.get("noul") is not None]
    deviation = max((abs(value - values[0]) for value in values), default=None) if values else None
    return {
        "question": pairs[0][0] if pairs else None,
        "values": values,
        "summary": _summary(values),
        "max_deviation_from_first": deviation,
        "observed": len(pairs),
    }


def _token_block(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Unique reported token counts. Identical payloads are not assumed to bill identically."""
    counts = {
        "input": sorted({int(record.get("input_tokens") or 0) for record in records}),
        "output": sorted({int(record.get("output_tokens") or 0) for record in records}),
        "total": sorted({int(record.get("total_tokens") or 0) for record in records}),
    }
    return {
        "unique": counts,
        "varies": any(len(values) > 1 for values in counts.values()),
    }


def _transport_block(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    attempts = [record.get("transport_attempt_count") for record in records]
    return {
        "single_attempt": sum(1 for value in attempts if value == 1),
        "multiple_attempts": sum(1 for value in attempts if isinstance(value, int) and value > 1),
        "not_recorded": sum(1 for value in attempts if value is None),
    }


def format_number(value: float | None, digits: int = 6) -> str:
    """A compact number for the report, or ``n/a``."""
    if value is None:
        return "n/a"
    return f"{value:.{digits}g}"


def format_ms(value: float | None) -> str:
    """A latency in the precision the log stores: ``latency_ms`` is recorded rounded to three
    decimals, so printing fewer digits would drop one the record actually has."""
    if value is None:
        return "n/a"
    return f"{value:.{LATENCY_DECIMALS}f}"


def build_repeatability_block(
    records: Sequence[Mapping[str, Any]], title: str = REPEATABILITY
) -> list[str]:
    """Render the repeatability section for the capability snapshot.

    The caller passes the records of one run. Everything printed here is recomputed from them. The
    title is the section heading; the shape of the report does not depend on which experiment it is
    describing, because the questions it answers are the same ones.
    """
    analysis = analyze(records)
    lines = [f"## `{title}`", "", "### Run-to-run stability", ""]

    if not analysis["ok_calls"]:
        lines += ["No successful call in this run produced an answer to compare.", ""]
        return lines

    lines += [
        f"**Design.** {analysis['calls']} call(s) of one byte-identical request in a single client "
        f"session; {analysis['ok_calls']} produced an answer"
        + (f", {analysis['failed_calls']} failed" if analysis["failed_calls"] else "")
        + ". One Choice, one Score and one Noul ride in every request, so each call yields three "
        "independent observations of the same payload.",
        "",
        "> **What this is not.** Nothing varies between these calls, so this is not a prompt "
        "sensitivity test, not a batching test, and not a correctness test. Five identical requests "
        "returning identical answers is reported as **no drift observed, and nothing more**: it does "
        "not establish that a sixth call would agree, and it says nothing about how an answer was "
        "produced. A difference would likewise be reported as observed variation, without being "
        "attributed to any internal mechanism -- this project has no official documentation of one, "
        "so it does not name one.",
        "",
    ]

    lines += _choice_lines(analysis["choice"])
    lines += _score_lines(analysis["score"])
    lines += _noul_lines(analysis["noul"], analysis["markers"])
    lines += _shape_lines(analysis["shape"])
    lines += _token_lines(analysis["tokens"], analysis["ok_calls"])
    lines += _model_lines(analysis["model"])
    lines += _transport_lines(analysis["transport"])
    lines += _latency_lines(analysis["latency"])
    return lines


def _choice_lines(block: Mapping[str, Any]) -> list[str]:
    if not block["observed"]:
        return []
    question = block["question"]
    labels = block["labels"]
    lines = [
        f"**Choice — `{question}`.**",
        "",
        f"- Labels, in call order: {', '.join(repr(label) for label in labels['labels'])}.",
        f"- Label agreement: **{labels['agreeing_count']} of {len(labels['labels'])}** call(s) chose "
        f"`{labels['agreeing_label']}`; {labels['distinct']} distinct label(s) appeared.",
        "",
        "| option | min | max | mean |",
        "|---|---|---|---|",
    ]
    for option, summary in block["probabilities"].items():
        lines.append(
            f"| `{option}` | {format_number(summary['min'])} | {format_number(summary['max'])} "
            f"| {format_number(summary['mean'])} |"
        )
    confidence = block["confidence"]
    lines += [
        "",
        f"- Largest probability spread across the field: "
        f"**{format_number(block['max_probability_spread'])}**.",
    ]
    if confidence:
        lines.append(
            f"- Confidence: min {format_number(confidence['min'])}, max "
            f"{format_number(confidence['max'])}, mean {format_number(confidence['mean'])}, "
            f"range **{format_number(confidence['range'])}**."
        )
    lines += _ranking_lines(block, "option")
    lines.append("")
    return lines


def _ranking_lines(block: Mapping[str, Any], unit: str) -> list[str]:
    """The top-two gap, and whether the top two stayed put. Shared by Choice and Score.

    A label can be stable while the field underneath it moves, so the margin is reported next to
    the agreement count rather than instead of it.
    """
    margins = [margin for margin in block.get("margins") or [] if margin is not None]
    if not margins:
        return []
    summary = block.get("margin_summary") or {}
    leaders = [leader for leader in block.get("leaders") or block.get("dominant_levels") or []]
    lines = [
        "",
        f"- Top-1 / top-2 margin, in call order: "
        f"{', '.join(format_number(margin) for margin in margins)}.",
        f"- Margin: min {format_number(summary.get('min'))}, max {format_number(summary.get('max'))}, "
        f"mean {format_number(summary.get('mean'))}, range "
        f"**{format_number(summary.get('range'))}**.",
        f"- Leading {unit}, in call order: {', '.join(f'`{name}`' for name in leaders)}.",
    ]
    tied_calls = sum(1 for row in block.get("ranking") or [] if row.get("tied"))
    if tied_calls:
        lines.append(
            f"- **{EXACT_TOP_PROBABILITY_TIE_OBSERVED}** on {tied_calls} of "
            f"{len(block.get('ranking') or [])} call(s): the top two {unit}s hold the *same* "
            "probability, so the ordering between them is not a quantity this call measured. A tie "
            "has no first place; where the answer named one of the tied options, that name is "
            "reported above, and the name is the API's label rather than evidence that it led on "
            "probability. Nothing here says how that name was arrived at, because these records do "
            "not address it."
        )
    switches = block.get("leader_switches", block.get("dominant_level_switches", 0))
    if switches:
        lines.append(
            f"- **The leading {unit} changed between calls {switches} time(s)** out of "
            f"{max(len(leaders) - 1, 0)} step(s). The two leaders are close enough that the "
            "ordering between them is not settled across these calls."
        )
    else:
        lines.append(
            f"- The leading {unit} was the same on every call, so no ordering between the top two "
            "was observed to change here."
        )
    return lines


def _score_lines(block: Mapping[str, Any]) -> list[str]:
    if not block["observed"]:
        return []
    question = block["question"]
    summary = block["summary"] or {}
    lines = [
        f"**Score — `{question}`.**",
        "",
        f"- Values, in call order: {', '.join(format_number(value) for value in block['values'])}.",
        f"- min {format_number(summary.get('min'))}, max {format_number(summary.get('max'))}, "
        f"mean {format_number(summary.get('mean'))}, range "
        f"**{format_number(summary.get('range'))}** (on the rubric as returned, before any "
        "normalisation).",
        "",
        "| level | min | max | mean |",
        "|---|---|---|---|",
    ]
    for level, level_summary in block["probabilities"].items():
        lines.append(
            f"| {level} | {format_number(level_summary['min'])} "
            f"| {format_number(level_summary['max'])} | {format_number(level_summary['mean'])} |"
        )
    confidence = block["confidence"]
    lines += [
        "",
        f"- Largest probability spread across the field: "
        f"**{format_number(block['max_probability_spread'])}**.",
    ]
    if confidence:
        lines.append(
            f"- Confidence: min {format_number(confidence['min'])}, max "
            f"{format_number(confidence['max'])}, mean {format_number(confidence['mean'])}, "
            f"range **{format_number(confidence['range'])}**."
        )
    lines += _ranking_lines(block, "level")
    lines += [
        "",
        "Score confidence is confidence in the stated judgment; it is not the property being "
        "judged and it is not comparable to Choice confidence.",
        "",
    ]
    return lines


def _noul_lines(block: Mapping[str, Any], markers: Sequence[str]) -> list[str]:
    if not block["observed"]:
        return []
    summary = block["summary"] or {}
    lines = [
        f"**Noul — `{block['question']}`.**",
        "",
        f"- Values, in call order: {', '.join(format_number(value) for value in block['values'])}.",
        f"- min {format_number(summary.get('min'))}, max {format_number(summary.get('max'))}, "
        f"mean {format_number(summary.get('mean'))}, range "
        f"**{format_number(summary.get('range'))}**.",
        f"- Largest absolute deviation from the first call: "
        f"**{format_number(block['max_deviation_from_first'])}**.",
    ]
    if SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED in markers:
        lines += [
            "",
            f"> **{SMALL_NOUL_RUN_TO_RUN_VARIATION_OBSERVED}.** The Noul did not return the same "
            f"value on every call, and the spread stayed at or below the {SMALL_NOUL_RANGE:g} "
            "smallness parameter this section declares -- a reporting convention, not a "
            "significance test. The movement is reported as what it is: a difference between the "
            "values the API returned. These records do not show what produced it.",
        ]
    lines += [
        "",
        "A Noul carries no separate confidence: with two outcomes, the scalar already describes the "
        "whole distribution.",
        "",
    ]
    return lines


def _shape_lines(shape: Mapping[str, Any]) -> list[str]:
    """Where on its scale each field landed, and what that leaves untested.

    A field sitting at a corner of its scale repeats for reasons a field with mass spread across it
    need not share. This paragraph exists so a clean result at a corner is not read as a clean
    result everywhere.
    """
    notes: list[str] = []
    if shape["choice_saturated"]:
        notes.append(
            "**Choice is saturated.** Every option came back at exactly 1 or 0 on every call, so "
            "the judgment was settled before it was repeated. This run is not evidence about "
            "repeatability where two options are close, because it contains no such call."
        )
    if shape["score_concentrated"]:
        notes.append(
            f"**Score is concentrated.** One level carried "
            f"{format_number(shape['score_top_probability'])} of the mass on every call, which is "
            "near the end of the rubric rather than in the middle of it. Repeatability at that "
            "point is what was measured; repeatability of a rubric whose levels are nearly even is "
            "not."
        )
    if not notes:
        return []
    count = "one" if len(notes) == 1 else "two" if len(notes) == 2 else str(len(notes))
    return [
        "**What the shapes of these distributions limit.** Instances of this experiment differ in "
        f"where on their scales the answers land, and this one landed near the end of {count} of "
        "them.",
        "",
        *[f"- {note}" for note in notes],
        "",
    ]


def _token_lines(tokens: Mapping[str, Any], ok_calls: int) -> list[str]:
    unique = tokens["unique"]
    lines = ["**Reported token usage.** Identical payloads are not assumed to account identically.", ""]
    for label in ("input", "output", "total"):
        values = unique[label]
        rendered = ", ".join(str(value) for value in values)
        if len(values) == 1:
            lines.append(f"- {label.capitalize()} tokens: **exactly equal** across all {ok_calls} "
                         f"call(s), at {rendered}.")
        else:
            lines.append(f"- {label.capitalize()} tokens: **{len(values)} distinct values** across "
                         f"{ok_calls} call(s): {rendered}.")
    if tokens["varies"]:
        lines += [
            "",
            f"> **{TOKEN_ACCOUNTING_VARIATION_OBSERVED}.** The requests were byte-identical, so "
            "this is variation in what the API reported, not in what was sent. The token counts in "
            "`usage.jsonl` stay exactly as the API returned them; nothing here averages them into a "
            "single figure or treats one call as the true cost of the request.",
            "",
        ]
    else:
        lines += [
            "",
            "> No variation was observed in the reported token counts for this identical payload.",
            "",
        ]
    return lines


def _model_lines(model: Mapping[str, Any]) -> list[str]:
    resolved = model["resolved"]
    same = model["consistent"]
    rendered = ", ".join(str(value) for value in resolved)
    return [
        "**Resolved model.**",
        "",
        f"- Requested: {', '.join(model['requested'])}. Resolved, in call order: {rendered}.",
        f"- One model answered every call: **{same}**"
        + ("" if same else " — the alias moved mid-run, so the answers above are not all from one "
                           "model and the comparison is not clean."),
        "",
    ]


def _transport_lines(transport: Mapping[str, Any]) -> list[str]:
    lines = [
        "**Transport.**",
        "",
        f"- Calls observed with exactly one HTTP attempt: **{transport['single_attempt']}**; with "
        f"more than one: **{transport['multiple_attempts']}**; with no attempt count recorded: "
        f"**{transport['not_recorded']}**.",
    ]
    if transport["single_attempt"] and not transport["multiple_attempts"]:
        lines.append("- No HTTP retry was locally observed for any call in this run.")
    if transport["not_recorded"]:
        lines.append("- A call with no attempt count has not been shown to have avoided retrying; "
                     "its retry behaviour is simply unknown.")
    lines.append("")
    return lines


def _latency_lines(latency: Mapping[str, Any]) -> list[str]:
    values = [float(value) for value in latency["values"] if value is not None]
    lines = ["**Latency — descriptive only, and separate from the stability above.**", ""]
    if values:
        lines.append(
            f"- All {len(values)} call(s): min {format_ms(min(values))} ms, "
            f"max {format_ms(max(values))} ms, mean {format_ms(statistics.fmean(values))} ms."
        )
    if latency["first"] is not None:
        others = [float(value) for value in latency["others"] if value is not None]
        line = (f"- First request of the session (marked, not dropped): "
                f"{format_ms(latency['first'])} ms")
        if others:
            line += (f"; the other {len(others)} call(s) ranged {format_ms(min(others))}–"
                     f"{format_ms(max(others))} ms.")
        lines.append(line)
    lines += [
        "",
        "> Latency repeatability and answer repeatability are different measurements and are not "
        "combined here. A stable answer with an unstable latency, or the reverse, is a normal "
        "result and neither one explains the other.",
        "",
    ]
    return lines
