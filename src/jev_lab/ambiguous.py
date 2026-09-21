"""`13b_ambiguous_repeatability`: stability where the field has two live options.

`13_repeatability` measured repeatability at the corner of a scale -- its Choice came back at
1.0/0.0 and its Score at 0.98 -- so it could say nothing about a field whose top two options are
close together. `13b` repeats `01_primitives` instead, because that payload has a *measurement*
showing it can land off the ends of its scales.

What that history does and does not buy is the whole point of this module, so it is written here
rather than implied:

* **Prior evidence, not a guarantee.** The historical `01_primitives` call returned `other` at 0.45
  against `billing` at 0.44, and a Score spread 0.41/0.59 over two levels. That is prior evidence
  that this payload *can* produce a non-saturated distribution. It is not a guarantee that it will
  again, and nothing in the design can make it one -- whether a run is ambiguous is an outcome.
* **One point is not a baseline.** The historical call is a single observation from an earlier run
  in a different client session. It is shown beside the five new calls and never pooled with them.
  Nothing here compares the two as if they were samples of the same thing, and no long-term
  stability claim is built on a single earlier value.

If the five calls do come back saturated, that is recorded as a result -- the marker below fires and
the answer is reported as what it is. It is not a reason to rerun until the sample looks better, and
no record is ever adjusted to fit the design's expectation.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from .repeatability import (
    analyze,
    build_repeatability_block,
    format_number,
)

AMBIGUOUS = "13b_ambiguous_repeatability"

# The experiment whose payload this one repeats. Its recorded answers are the historical reference.
REFERENCE = "01_primitives"

# Raised when the five calls landed at the ends of their scales anyway. The experiment's sub-goal was
# to measure a non-degenerate distribution; this marker is how a failure of that sub-goal is
# recorded rather than smoothed over.
AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED = "AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED"


def _answers_of_type(record: Mapping[str, Any], kind: str) -> dict[str, Mapping[str, Any]]:
    """The answers of one primitive type in a record, keyed by question name."""
    return {
        str(name): answer
        for name, answer in (record.get("answers") or {}).items()
        if isinstance(answer, Mapping) and answer.get("type") == kind
    }


def _in_range(value: float | None, summary: Mapping[str, Any] | None) -> str:
    """Where a reference value sits relative to a range of new observations."""
    if value is None or not summary:
        return "not comparable"
    if value < summary["min"]:
        return "below the observed range"
    if value > summary["max"]:
        return "above the observed range"
    return "inside the observed range"


def _reference_notes(
    reference: Mapping[str, Any], analysis: Mapping[str, Any]
) -> list[str]:
    """Compare one historical call to the new run, field by field, without pooling them."""
    notes: list[str] = []
    reference_choice = _answers_of_type(reference, "choice")
    reference_score = _answers_of_type(reference, "score")
    reference_noul = _answers_of_type(reference, "noul")

    for name, answer in reference_choice.items():
        block = analysis["choice"]
        if block["question"] != name:
            notes.append(
                f"- Choice `{name}` in the historical call has no counterpart in this run, so no "
                "comparison is made."
            )
            continue
        probabilities = answer.get("probabilities") or {}
        outside = []
        for option, value in probabilities.items():
            summary = block["probabilities"].get(str(option))
            if summary is None:
                outside.append(f"`{option}` is absent from this run")
                continue
            if float(value) < summary["min"] or float(value) > summary["max"]:
                outside.append(
                    f"`{option}` was {format_number(value)} then, outside {format_number(summary['min'])}"
                    f"-{format_number(summary['max'])} now"
                )
        winner = answer.get("choice")
        if block["leaders"] and all(leader == winner for leader in block["leaders"]):
            winner_text = (
                f"the historical winner `{winner}` was also the leading option on all "
                f"{block['observed']} call(s) here"
            )
        elif winner in block["leaders"]:
            matched = sum(1 for leader in block["leaders"] if leader == winner)
            winner_text = (
                f"the historical winner `{winner}` led on **{matched} of {block['observed']}** "
                "call(s) here, so the two top options did not order the same way"
            )
        else:
            winner_text = (
                f"the historical winner `{winner}` never led here; this run's leading option(s) "
                f"were {', '.join(f'`{leader}`' for leader in dict.fromkeys(block['leaders']))}"
            )
        notes.append(
            f"- Choice `{name}`: {winner_text}. "
            + ("Every option stayed inside the range observed here."
               if not outside else "Moved beyond it: " + "; ".join(outside) + ".")
        )
        reference_confidence = answer.get("confidence")
        confidence_summary = block["confidence"]
        notes.append(
            f"  - Confidence: {format_number(reference_confidence)}, "
            f"{_in_range(reference_confidence, confidence_summary)} of "
            f"{format_number((confidence_summary or {}).get('min'))}"
            f"-{format_number((confidence_summary or {}).get('max'))} here."
        )

    for name, answer in reference_score.items():
        block = analysis["score"]
        if block["question"] != name:
            notes.append(
                f"- Score `{name}` in the historical call has no counterpart in this run, so no "
                "comparison is made."
            )
            continue
        value = answer.get("score")
        summary = block["summary"]
        notes.append(
            f"- Score `{name}`: the historical score was {format_number(value)}, "
            f"{_in_range(value, summary)} of {format_number((summary or {}).get('min'))}"
            f"-{format_number((summary or {}).get('max'))} here."
        )
        for level, probability in (answer.get("probabilities") or {}).items():
            level_summary = block["probabilities"].get(str(level))
            if level_summary is None:
                notes.append(f"  - Level `{level}` is absent from this run's Score.")
                continue
            notes.append(
                f"  - P({level}) was {format_number(probability)}, "
                f"{_in_range(probability, level_summary)} of "
                f"{format_number(level_summary['min'])}-{format_number(level_summary['max'])} here."
            )
        reference_confidence = answer.get("confidence")
        confidence_summary = block["confidence"]
        notes.append(
            f"  - Confidence: {format_number(reference_confidence)}, "
            f"{_in_range(reference_confidence, confidence_summary)} of "
            f"{format_number((confidence_summary or {}).get('min'))}"
            f"-{format_number((confidence_summary or {}).get('max'))} here."
        )

    for name, answer in reference_noul.items():
        block = analysis["noul"]
        if block["question"] != name:
            notes.append(
                f"- Noul `{name}` in the historical call has no counterpart in this run, so no "
                "comparison is made."
            )
            continue
        value = answer.get("noul")
        summary = block["summary"]
        notes.append(
            f"- Noul `{name}`: the historical value was {format_number(value)}, "
            f"{_in_range(value, summary)} of {format_number((summary or {}).get('min'))}"
            f"-{format_number((summary or {}).get('max'))} here."
        )

    return notes


def _target_lines(analysis: Mapping[str, Any]) -> list[str]:
    """State whether this run actually landed where the design needed it to."""
    saturated_choice = analysis["shape"]["choice_saturated"]
    concentrated_score = analysis["shape"]["score_concentrated"]
    lines = ["**Was the target realized?**", ""]
    if not saturated_choice and not concentrated_score:
        lines += [
            "- Neither the Choice nor the Score came back at the end of its scale, so these calls "
            "do carry information about a field whose top options are close together.",
        ]
    else:
        missed = []
        if saturated_choice:
            missed.append("the Choice came back saturated at exactly 1.0/0.0")
        if concentrated_score:
            missed.append(
                f"one Score level carried {format_number(analysis['shape']['score_top_probability'])}"
                " of the mass"
            )
        lines += [
            f"> **{AMBIGUOUS_REPEATABILITY_TARGET_NOT_REALIZED}.** "
            + " and ".join(missed)
            + ". The sub-goal of this experiment was to measure a non-degenerate distribution, and "
            "this run did not land in one. The result is recorded as it came back: the records are "
            "not adjusted, and the experiment is not rerun over until it agrees with the design.",
        ]
    lines += [
        "",
        "The historical `01_primitives` call is prior evidence that this payload **can** produce a "
        "non-saturated Choice and Score -- it is not a guarantee that it will, and it does not make "
        "this run's shape a design outcome rather than a result.",
        "",
    ]
    return lines


def _comparison_row(label: str, left: str, right: str) -> str:
    return f"| {label} | {left} | {right} |"


def build_comparison_block(
    marked_records: Sequence[Mapping[str, Any]],
    ambiguous_records: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Put the two repeat experiments side by side, and stop where the evidence stops.

    This is the comparison the first repeat experiment could not make: one case whose fields sat at
    the ends of their scales, and one whose fields did not. Both are described by the same derived
    quantities, so the difference between them is read off the records rather than asserted.

    Two cases are two cases. The temptation is to read the pair as a relationship -- variation as a
    function of where a field sits on its scale -- and nothing here supports that: there is no
    measurement between the extremes, no replication at either, and one session apiece. So the
    section reports the contrast and says plainly that it is not a curve.
    """
    from .repeatability import REPEATABILITY

    if not marked_records or not ambiguous_records:
        return []
    left, right = analyze(marked_records), analyze(ambiguous_records)

    def leading(analysis: Mapping[str, Any], kind: str) -> str:
        block = analysis[kind]
        top = block["top_probability"]
        return format_number(top) if top is not None else "n/a"

    def spread(analysis: Mapping[str, Any], kind: str) -> str:
        value = analysis[kind]["max_probability_spread"]
        return format_number(value) if value is not None else "n/a"

    def ties(analysis: Mapping[str, Any]) -> str:
        ranking = analysis["choice"]["ranking"]
        return f"{sum(1 for row in ranking if row.get('tied'))} of {len(ranking)}"

    lines = [
        "### Repeatability comparison",
        "",
        f"| derived quantity | `{REPEATABILITY}` | `{AMBIGUOUS}` |",
        "|---|---|---|",
        _comparison_row("Choice: leading probability",
                        leading(left, "choice"), leading(right, "choice")),
        _comparison_row("Choice: largest probability spread",
                        spread(left, "choice"), spread(right, "choice")),
        _comparison_row("Choice: calls with an exact top-two tie", ties(left), ties(right)),
        _comparison_row("Score: leading level probability",
                        leading(left, "score"), leading(right, "score")),
        _comparison_row("Score: largest probability spread",
                        spread(left, "score"), spread(right, "score")),
        _comparison_row("Noul: range",
                        format_number((left["noul"]["summary"] or {}).get("range")),
                        format_number((right["noul"]["summary"] or {}).get("range"))),
        "",
        "Read across a row, the two experiments differ in **where on their scales the fields sat**, "
        "and that is the one thing this table is evidence about. In the first, the Choice was exactly "
        "1 or 0 on every call and the Noul moved; in the second, the Choice carried two live options "
        "and the Noul did not move at all.",
        "",
        "> **What this pair does not establish.** Observed variation appears to depend on the region "
        "of the scale a field lands in, and these two cases are consistent with that. They do not "
        "show it. Two cases, one session each, no measurement between the extremes and no repeat at "
        "either -- that is not a function of probability region or of confidence, and no curve is "
        "fitted here. A third case in the middle of a scale would be needed before the sentence "
        "\"variation depends on region\" could be more than a description of these two runs.",
        "",
    ]
    return lines


def build_ambiguous_block(
    repeat_records: Sequence[Mapping[str, Any]],
    reference_records: Sequence[Mapping[str, Any]] = (),
    comparison_records: Sequence[Mapping[str, Any]] = (),
) -> list[str]:
    """Render `13b_ambiguous_repeatability`: the new run, then the historical call beside it.

    The two are deliberately rendered as separate sections. Pooling five same-session calls with one
    call from an earlier session would produce a number that describes neither, and the point of the
    reference is to be a fixed outside marker, not a sixth sample.
    """
    lines = build_repeatability_block(repeat_records, title=AMBIGUOUS)
    analysis = analyze(repeat_records)
    lines += ["### Near-tie behaviour", ""]
    lines += _target_lines(analysis)

    lines += [
        f"### Historical reference: `{REFERENCE}`",
        "",
        "Shown for comparison and **not** pooled with the calls above: a different run, a different "
        "client session, and one observation rather than five. A single earlier point can show that "
        "a value moved; it cannot show that a value is stable.",
        "",
    ]
    if not reference_records:
        lines += [
            f"No `{REFERENCE}` record is present in the log, so there is nothing to compare "
            "against.",
            "",
        ]
    else:
        for reference in reference_records:
            lines += [
                f"- Recorded {reference.get('timestamp_utc')} in run `{reference.get('run_id')}`, "
                f"model `{reference.get('model_resolved')}`.",
            ]
        lines.append("")
        for reference in reference_records:
            lines += _reference_notes(reference, analysis)
        lines.append("")

    lines += build_comparison_block(comparison_records, repeat_records)
    return lines
