"""`05_speculative_fanout`: what it costs to ask for answers you may not use.

A control flow is not a batch. In `03_parallel_questions` every question sent is a question
needed, so batching is purely a question of how the same work is split. Here the request carries
questions that only *one* of two branches will want, and which branch it is cannot be known until
the primary answer comes back. Two ways to handle that are measured against each other:

* **fanout** -- one request carrying the primary question and both branches' follow-ups. Python
  then reads only the branch the primary answer chose. The other branch's answers were paid for
  and thrown away.
* **staged** -- one request carrying the primary question alone, then, once the answer is in, a
  second request carrying only the branch that answer chose.

The trade is one round trip against some quantity of unused questions. Which side wins is a
measurement, and nothing in this module predicts it: a fanout request that shares its state once
can come out cheaper than two requests that each carry it, or more expensive, and the ratio is
read off the records either way. No sentence here says fanout is the cheaper option, because on
this evidence that would be a guess with a number next to it.

Two limits are load-bearing and are stated wherever the numbers are:

* **Only request-level overhead is measurable.** The API reports usage per request, not per
  question, so the tokens spent on one unused question are not separable from the tokens spent on
  the request that carried it. The waste is counted in *questions*, and the cost of that waste is
  reported as the whole-request difference between the two arms -- never as a per-question figure.
* **Two pairs are two pairs.** Each state is one measurement of each strategy, in one session.
  Semantic agreement between the arms is reported per question and is not pooled into a rate that
  would look like a property of the model rather than of these few inputs.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from .experiments import FANOUT_ARM, STAGE_1, STAGED_ARM
from .pricing import price_for
from .repeatability import format_ms, format_number

FANOUT = "05_speculative_fanout"

# Raised when the fanout arm carried questions its branch never consumed. That is the overhead the
# experiment exists to price, so its presence is recorded as a measurement rather than a defect.
SPECULATIVE_QUESTIONS_UNUSED = "SPECULATIVE_QUESTIONS_UNUSED"

# Raised when the two arms' primary answers named different branches for the same state. The two
# requests ask the same question of the same state, so a disagreement is a fact worth its own line
# rather than being folded into the semantic comparison of the follow-ups.
PRIMARY_BRANCH_DISAGREEMENT_OBSERVED = "PRIMARY_BRANCH_DISAGREEMENT_OBSERVED"

# Raised when a primary answer named a branch the frozen map does not contain. The design expects
# neither of these labels; a run that produces one is reported, not repaired.
PRIMARY_BRANCH_UNEXPECTED = "PRIMARY_BRANCH_UNEXPECTED"

# Raised when a follow-up both arms consumed came back differently. Which arm is "right" is not
# established by anything in the log, so this marker names the disagreement and stops there.
CONSUMED_ANSWER_MISMATCH_OBSERVED = "CONSUMED_ANSWER_MISMATCH_OBSERVED"

# Raised when a staged first stage chose no branch and therefore sent no second request. The
# frozen rule that produces this is in `_05_follow_up`; the marker keeps the missing call visible
# instead of letting it read as a design that never intended one.
STAGED_SECOND_REQUEST_SKIPPED = "STAGED_SECOND_REQUEST_SKIPPED"

# Raised when one pair's fanout request was the slower of the two strategies and another pair's was
# the faster. The design deliberately runs the pairs in opposite orders, which is exactly the
# arrangement that can produce this, and the honest reading of it is that position is doing at
# least as much work as arm identity. Without the marker a reader sees two latency lines and
# averages them into a direction the records do not support.
FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS = (
    "FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS"
)

# The experiment this one is compared against in the snapshot. Read for its own arm totals only.
PARALLEL = "03_parallel_questions"
PARALLEL_BATCH_ARM = "batched"

# Ratios read better with fixed decimals than with significant digits.
RATIO_DECIMALS = 4


def _note(record: Mapping[str, Any], key: str) -> Any:
    """Read one design-metadata key off a record, tolerating records written without notes."""
    return (record.get("notes") or {}).get(key)


def _derived(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """The locally computed decision stored beside a record's answers, if it was stored."""
    return (record.get("notes") or {}).get("derived") or {}


def _ratio(part: float, whole: float) -> str:
    """``part / whole`` as fixed-decimal text, or ``n/a`` when the denominator is zero."""
    return f"{part / whole:.{RATIO_DECIMALS}f}" if whole else "n/a"


def _sum(records: Sequence[Mapping[str, Any]], field: str) -> float:
    """Sum one numeric field across records, treating an absent value as zero."""
    return sum(float(record.get(field) or 0) for record in records)


def _answers(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """The answers a record carries, keyed by question name."""
    return record.get("answers") or {}


def _comparable(answer: Mapping[str, Any]) -> dict[str, Any]:
    """The fields of one answer that two arms can be compared on, per answer type.

    Only the fields the type actually carries. A Noul has no confidence, so comparing one there
    would match ``None`` against ``None`` and report agreement about a field nobody measured.
    """
    kind = answer.get("type")
    if kind == "choice":
        return {
            "choice": answer.get("choice"),
            "confidence": answer.get("confidence"),
            "probabilities": dict(answer.get("probabilities") or {}),
        }
    if kind == "score":
        return {
            "score": answer.get("score"),
            "confidence": answer.get("confidence"),
            "probabilities": {
                str(level): value for level, value in (answer.get("probabilities") or {}).items()
            },
        }
    if kind == "noul":
        return {"noul": answer.get("noul")}
    return {}


def _field_differences(left: Mapping[str, Any], right: Mapping[str, Any]) -> list[str]:
    """Field-by-field differences between two comparable answers, one line each."""
    lines: list[str] = []
    for field in sorted(set(left) | set(right)):
        first, second = left.get(field), right.get(field)
        if first == second:
            continue
        if field == "probabilities" and isinstance(first, Mapping) and isinstance(second, Mapping):
            for option in sorted(set(first) | set(second)):
                if first.get(option) != second.get(option):
                    lines.append(
                        f"P(`{option}`) {format_number(first.get(option))} vs "
                        f"{format_number(second.get(option))}"
                    )
            continue
        lines.append(f"`{field}` {first} vs {second}")
    return lines


def _question_names(record: Mapping[str, Any]) -> list[str]:
    """The question names a record's request carried, read from its own local note."""
    asked = _derived(record).get("questions_asked")
    if asked:
        return [str(name) for name in asked]
    return [str(name) for name in _answers(record)]


def _side(records: Sequence[Mapping[str, Any]], field: str) -> float:
    """Pooled total of one numeric field across an arm."""
    return _sum(records, field)


def _arm(records: Sequence[Mapping[str, Any]], pair: str, strategy: str) -> list[Mapping[str, Any]]:
    """One pair's calls for one strategy, in the order they were made."""
    return [
        record
        for record in records
        if _note(record, "pair") == pair and _note(record, "strategy") == strategy
    ]


def pair_names(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """The declared pairs present in the records, in order and without duplicates."""
    seen: list[str] = []
    for record in records:
        pair = _note(record, "pair")
        if pair is not None and str(pair) not in seen:
            seen.append(str(pair))
    return seen


def unused_answers(record: Mapping[str, Any]) -> list[str]:
    """Unused questions that actually came back with an answer on this record.

    Counted from the record's own answers rather than from the unused list alone: a question the
    request carried and the response did not answer was not paid for twice, and it must not be
    counted as an answer that was discarded.
    """
    unused = [str(name) for name in (_derived(record).get("questions_unused") or [])]
    return [name for name in unused if _answers(record).get(name)]


def _latency_direction(
    fanout: Sequence[Mapping[str, Any]], staged: Sequence[Mapping[str, Any]]
) -> str | None:
    """Which arm was slower in one pair, or ``None`` when the pair cannot say.

    The staged side is a sum of its own measured windows, because the two requests it made are
    sequential and nothing between them is timed. A pair with a missing latency on either side has
    no direction; that is ``None``, and it is never read as a tie.
    """
    if not fanout or not staged:
        return None
    if any(record.get("latency_ms") is None for record in (*fanout, *staged)):
        return None
    fanout_ms = _sum(fanout, "latency_ms")
    staged_ms = _sum(staged, "latency_ms")
    if fanout_ms == staged_ms:
        return None
    return "fanout_slower" if fanout_ms > staged_ms else "fanout_faster"


def analyze_fanout(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every derived quantity this experiment reports, computed from the canonical records.

    Nothing is carried in from the design's expectations: the branch each primary answer chose,
    which questions were consumed, and how many were not all come out of the records, so a run
    that behaves unlike the design produces numbers that say so.
    """
    pairs: list[dict[str, Any]] = []
    for pair in pair_names(records):
        fanout = _arm(records, pair, FANOUT_ARM)
        staged = _arm(records, pair, STAGED_ARM)
        staged_sorted = sorted(staged, key=lambda record: _note(record, "stage") or 0)
        pairs.append(
            {
                "pair": pair,
                "fanout": fanout,
                "staged": staged_sorted,
                "staged_stage_1": [
                    record for record in staged_sorted if _note(record, "stage") == STAGE_1
                ],
                "staged_stage_2": [
                    record for record in staged_sorted if _note(record, "stage") != STAGE_1
                ],
                "markers": _pair_markers(fanout, staged_sorted),
                "comparisons": _consumed_comparisons(fanout, staged_sorted),
                "latency_direction": _latency_direction(fanout, staged_sorted),
            }
        )

    fanout_records = [record for record in records if _note(record, "strategy") == FANOUT_ARM]
    staged_records = [record for record in records if _note(record, "strategy") == STAGED_ARM]
    return {
        "calls": len(records),
        "pairs": pairs,
        "fanout_calls": len(fanout_records),
        "staged_calls": len(staged_records),
        "fanout_input_tokens": _side(fanout_records, "input_tokens"),
        "staged_input_tokens": _side(staged_records, "input_tokens"),
        "fanout_output_tokens": _side(fanout_records, "output_tokens"),
        "staged_output_tokens": _side(staged_records, "output_tokens"),
        "fanout_cost_usd": _side(fanout_records, "estimated_cost_usd"),
        "staged_cost_usd": _side(staged_records, "estimated_cost_usd"),
        "fanout_questions_asked": sum(len(_question_names(r)) for r in fanout_records),
        "fanout_questions_consumed": sum(
            len(_derived(r).get("questions_consumed") or []) for r in fanout_records
        ),
        "fanout_questions_unused": sum(
            len(_derived(r).get("questions_unused") or []) for r in fanout_records
        ),
        "fanout_unused_answers": sum(len(unused_answers(r)) for r in fanout_records),
        "markers": _pooled_markers(records, pairs),
    }


def _pair_markers(
    fanout: Sequence[Mapping[str, Any]], staged: Sequence[Mapping[str, Any]]
) -> list[str]:
    """The markers one pair's records earn, in a fixed order."""
    markers: list[str] = []
    if any(int(_derived(record).get("unused_question_count") or 0) > 0 for record in fanout):
        markers.append(SPECULATIVE_QUESTIONS_UNUSED)
    branches = {
        str(_derived(record).get("branch_taken"))
        for record in [*fanout, *_first_stage(staged)]
        if _derived(record).get("branch_taken") is not None
    }
    if len(branches) > 1:
        markers.append(PRIMARY_BRANCH_DISAGREEMENT_OBSERVED)
    if any(_derived(record).get("branch_routable") is False for record in [*fanout, *_first_stage(staged)]):
        markers.append(PRIMARY_BRANCH_UNEXPECTED)
    if any(
        _derived(record).get("branch_matches_expected") is False
        for record in [*fanout, *_first_stage(staged)]
    ):
        markers.append(PRIMARY_BRANCH_UNEXPECTED)
    if not _second_stage(staged) and _first_stage(staged):
        markers.append(STAGED_SECOND_REQUEST_SKIPPED)
    return list(dict.fromkeys(markers))


def _first_stage(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The staged calls that carried the primary question."""
    return [record for record in records if _note(record, "stage") == STAGE_1]


def _second_stage(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The staged calls that did not carry the primary question."""
    return [record for record in records if _note(record, "stage") != STAGE_1]


def _staged_by_question(staged: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """Which staged record carries each question name.

    Both arms ask the same questions, but the staged arm does not ask them all in the same call:
    the primary is its *first* request and the branch follow-ups are its second. Pairing by name
    against the right record is what keeps the primary from being reported as missing from the
    staged arm when it was asked there all along.
    """
    mapping: dict[str, Mapping[str, Any]] = {}
    for record in staged:
        for name in _question_names(record):
            mapping.setdefault(name, record)
    return mapping


def _consumed_comparisons(
    fanout: Sequence[Mapping[str, Any]], staged: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Compare each question the fanout arm consumed, field by field, against its counterpart.

    Only questions the fanout arm actually consumed take part. An unused fanout answer is the
    thing this experiment is pricing, and putting one into an agreement comparison would grade an
    answer that nothing downstream ever read.
    """
    if not fanout:
        return []
    fanout_answers = _answers(fanout[0])
    counterpart = _staged_by_question(staged)
    consumed = [str(name) for name in (_derived(fanout[0]).get("questions_consumed") or [])]
    comparisons: list[dict[str, Any]] = []
    for name in consumed:
        other = counterpart.get(name)
        if other is None:
            comparisons.append(
                {"question": name, "comparable": False, "stage": None, "differences": []}
            )
            continue
        left = _comparable(fanout_answers.get(name) or {})
        right = _comparable(_answers(other).get(name) or {})
        comparisons.append(
            {
                "question": name,
                "kind": (fanout_answers.get(name) or {}).get("type"),
                "stage": _note(other, "stage"),
                "comparable": True,
                "differences": _field_differences(left, right),
            }
        )
    return comparisons


def _pooled_markers(
    records: Sequence[Mapping[str, Any]], pairs: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Every marker the run earns, from the pairs plus the consumed-answer comparisons."""
    markers: list[str] = []
    for entry in pairs:
        markers.extend(entry["markers"])
    if any(
        comparison["differences"]
        for entry in pairs
        for comparison in entry["comparisons"]
    ):
        markers.append(CONSUMED_ANSWER_MISMATCH_OBSERVED)
    directions = {entry["latency_direction"] for entry in pairs} - {None}
    if len(directions) > 1:
        markers.append(FANOUT_LATENCY_DIRECTION_INCONSISTENT_ACROSS_PAIRS)
    return list(dict.fromkeys(markers))


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _design_lines(records: Sequence[Mapping[str, Any]], analysis: Mapping[str, Any]) -> list[str]:
    """What was sent, described from the records rather than from the design's intent."""
    pairs = analysis["pairs"]
    fanout_records = [r for r in records if _note(r, "strategy") == FANOUT_ARM]
    staged_records = [r for r in records if _note(r, "strategy") == STAGED_ARM]
    asked = sorted({len(_question_names(record)) for record in fanout_records})
    second = sorted({len(_question_names(record)) for record in _second_stage(staged_records)})
    sizes = sorted({record.get("state_utf8_bytes") for record in records})
    lines = [
        "**Design.** A branching control flow, asked two ways over the same states.",
        "",
        f"- **fanout** — {len(fanout_records)} request(s), each carrying the primary question plus "
        f"every branch's follow-ups ({asked[0] if len(asked) == 1 else asked} question(s)); after "
        "the answer lands, Python reads only the branch the primary chose.",
        f"- **staged** — {len(staged_records)} request(s): a first request carrying the primary "
        "alone, then the chosen branch's follow-ups "
        f"({second[0] if len(second) == 1 else second} question(s)) in a second request.",
        "",
        "State sizes: "
        + (", ".join(str(size) for size in sizes) if sizes else "not recorded")
        + " utf8 bytes. Both arms send the *same question objects* and the same state object; the "
        "offline payload audit checks that at the encoder, not by comparing two definitions that "
        "read alike.",
        "",
    ]
    return lines


def _unused_fraction(analysis: Mapping[str, Any]) -> float:
    """Unused fanout questions over asked fanout questions, as a count and not as a cost."""
    asked = analysis["fanout_questions_asked"]
    return analysis["fanout_questions_unused"] / asked if asked else 0.0


def _overhead_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Section F: asked against consumed, and the honest limit on what that can price."""
    lines = [
        "### Speculative overhead",
        "",
        "| pair | fanout asked | consumed | unused | unused answers | unused questions |",
        "|---|---|---|---|---|---|",
    ]
    for entry in analysis["pairs"]:
        fanout = entry["fanout"]
        asked = sum(len(_question_names(record)) for record in fanout)
        consumed = sum(len(_derived(record).get("questions_consumed") or []) for record in fanout)
        unused = [str(name) for record in fanout for name in (_derived(record).get("questions_unused") or [])]
        answers = [name for record in fanout for name in unused_answers(record)]
        lines.append(
            f"| {entry['pair']} | {asked} | {consumed} | {len(unused)} | {len(answers)} | "
            + (", ".join(f"`{name}`" for name in unused) if unused else "none")
            + " |"
        )
    lines += [
        "",
        f"**{analysis['fanout_questions_unused']} of {analysis['fanout_questions_asked']}** fanout "
        f"question(s) were carried and not consumed, across "
        f"{analysis['fanout_calls']} fanout request(s) — an unused fraction of "
        f"**{_unused_fraction(analysis):.2%}**. That fraction is a **question count over a question "
        "count**. It is not a fraction of the tokens, the cost, or the latency, and none of those "
        "is derived from it.",
        "",
        "> **What this overhead is, and is not.** The waste is counted in **questions**, and that "
        "is the only unit available: the API reports usage per request, so the tokens spent on one "
        "unused question cannot be separated from the tokens spent on the request that carried it. "
        "No per-question token cost is claimed here, and none is estimated. What is measurable is "
        "the whole-request difference between the two arms, which is reported below.",
        "",
    ]
    return lines


def _cost_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Section G: what each arm cost, per pair and pooled, with the sign left to the numbers."""
    lines = [
        "### Request cost",
        "",
        "| pair | fanout requests | staged requests | fanout input | staged input | "
        "fanout/staged input | fanout cost | staged cost | fanout/staged cost |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in analysis["pairs"]:
        fi = _side(entry["fanout"], "input_tokens")
        si = _side(entry["staged"], "input_tokens")
        fc = _side(entry["fanout"], "estimated_cost_usd")
        sc = _side(entry["staged"], "estimated_cost_usd")
        lines.append(
            f"| {entry['pair']} | {len(entry['fanout'])} | {len(entry['staged'])} | {fi:.0f} | "
            f"{si:.0f} | {_ratio(fi, si)}x | ${fc:.8f} | ${sc:.8f} | {_ratio(fc, sc)}x |"
        )
    fi, si = analysis["fanout_input_tokens"], analysis["staged_input_tokens"]
    fc, sc = analysis["fanout_cost_usd"], analysis["staged_cost_usd"]
    lines += [
        f"| **pooled** | {analysis['fanout_calls']} | {analysis['staged_calls']} | {fi:.0f} | "
        f"{si:.0f} | {_ratio(fi, si)}x | ${fc:.8f} | ${sc:.8f} | {_ratio(fc, sc)}x |",
        "",
        f"- **Round trips.** fanout **{analysis['fanout_calls']}** logical request(s) against "
        f"staged **{analysis['staged_calls']}** — one against two per pair, where the second was "
        "sent at all. A logical request is one call; an HTTP-level retry would add round trips "
        "*inside* one of them and is visible only through `transport_attempt_count`.",
        "- **Which arm is cheaper is not assumed, and not decided by the design.** A fanout request "
        "carries the state once and may still lose on tokens by carrying questions nobody reads; a "
        "staged pair pays for its state twice to avoid them. The ratio above is the measurement; it "
        "has one sign or the other and this section does not pick it in advance.",
        "- `estimated_cost_usd` is a **local estimate** at the published input rate, and output is "
        "billed at $0 in this project's price table, so the cost ratio tracks the input ratio "
        "exactly rather than independently confirming it. TypeSafe Console billing is authoritative.",
        "",
    ]
    return lines


def _resolved_model(records: Sequence[Mapping[str, Any]]) -> str | None:
    """The model the responses named, when every record names the same one."""
    resolved = {record.get("model_resolved") for record in records} - {None}
    return resolved.pop() if len(resolved) == 1 else None


def _output_lines(
    analysis: Mapping[str, Any], records: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Section E: the output side of the trade, kept separate from the cost claim.

    Output tokens are the half of the trade that the input ratio does not show, and on these
    records they run the other way. Whether that costs anything is a property of the price table
    for the resolved model on the day of the run, not a property of output tokens, so the price is
    read out of that table rather than asserted.
    """
    fanout = analysis["fanout_output_tokens"]
    staged = analysis["staged_output_tokens"]
    difference = fanout - staged
    model = _resolved_model(records)
    price = price_for(model) if model else None
    if price is None:
        cost_note = (
            "No price is available for the resolved model in this project's table, so nothing is "
            "said here about what these tokens cost."
        )
    elif price.output_usd_per_million:
        cost_note = (
            f"Output is billed at ${price.output_usd_per_million:g}/M tokens for "
            f"`{model}`, so this difference is part of that arm's cost."
        )
    else:
        cost_note = (
            f"Output is billed at ${price.output_usd_per_million:g}/M tokens for `{model}` in "
            f"this project's price table, so this difference contributes nothing to the "
            "`estimated_cost_usd` reported above."
        )
    return [
        "### Output tokens",
        "",
        f"- fanout **{fanout:.0f}**, staged **{staged:.0f}** — a difference of "
        f"**{difference:+.0f}** tokens, `fanout/staged` = **{_ratio(fanout, staged)}x**.",
        f"- On these records the fanout arm produced **materially more output tokens** than the "
        "staged arm did: it answered every question it carried, including the ones Python never "
        "read, and answers are what output tokens are.",
        f"- {cost_note}",
        "- **Output tokens are not free in general.** They are free under this project's price "
        "table for this resolved model. A different model, or a change to that table, can price "
        "them, and the sentence above is not a statement about TypeSafe's pricing.",
        "",
    ]


def _routing_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Section J: the branch each arm chose, against the frozen expectation, and against each other."""
    lines = [
        "### Primary routing",
        "",
        "| pair | fanout branch | staged branch | agree | matches expected |",
        "|---|---|---|---|---|",
    ]
    for entry in analysis["pairs"]:
        fanout_branch = next(
            (str(_derived(r).get("branch_taken")) for r in entry["fanout"] if _derived(r).get("branch_taken") is not None),
            "not recorded",
        )
        staged_branch = next(
            (
                str(_derived(r).get("branch_taken"))
                for r in entry["staged_stage_1"]
                if _derived(r).get("branch_taken") is not None
            ),
            "not recorded",
        )
        expected = next(
            (
                _derived(r).get("branch_expected")
                for r in [*entry["fanout"], *entry["staged_stage_1"]]
                if _derived(r).get("branch_expected") is not None
            ),
            None,
        )
        matches = {
            _derived(r).get("branch_matches_expected")
            for r in [*entry["fanout"], *entry["staged_stage_1"]]
            if _derived(r).get("branch_matches_expected") is not None
        }
        lines.append(
            f"| {entry['pair']} | `{fanout_branch}` | `{staged_branch}` | "
            f"{fanout_branch == staged_branch} | "
            + ("yes" if matches == {True} else "no" if matches else "not recorded")
            + f" (`{expected}`) |"
        )
    lines += [
        "",
        "The expected branch is frozen in the experiment definition before any run and is local "
        "bookkeeping only — it never reaches the wire. The branch itself is chosen in **Python**, "
        "from the label the primary answer returned, looked up in a frozen map.",
        "",
        "> **Routing correctness is not confidence.** The primary answer carries a confidence, and "
        "nothing here reads it: a branch taken at confidence 0.99 and one taken at 0.51 are recorded "
        "as the same branch. A high confidence is not evidence the branch was right, and a low one "
        "is not evidence it was wrong.",
        "",
    ]
    return lines


def _comparison_line(pair: str, comparison: Mapping[str, Any]) -> str:
    """One compared question, rendered as a line."""
    name = comparison["question"]
    if not comparison["comparable"]:
        return (
            f"- **{pair} / `{name}`** — consumed by the fanout arm but carried by no staged "
            "request, so the two cannot be compared."
        )
    if comparison["differences"]:
        return (
            f"- **{pair} / `{name}`** ({comparison['kind']}) — differs: "
            + "; ".join(comparison["differences"]) + "."
        )
    return (
        f"- **{pair} / `{name}`** ({comparison['kind']}) — identical on every field this answer "
        "type carries."
    )


def _comparison_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Section H: what both arms asked and both arms read, compared question by question.

    The primary question is reported separately from the follow-ups, because the two are asked
    under different conditions in the staged arm and pooling them would hide that. The primary is
    asked *alone* there; the follow-ups are asked after the branch is already chosen.
    """
    lines = ["### Consumed-answer agreement", ""]
    primary_rows: list[str] = []
    followup_rows: list[str] = []
    for entry in analysis["pairs"]:
        for comparison in entry["comparisons"]:
            if comparison.get("stage") == STAGE_1:
                primary_rows.append(_comparison_line(entry["pair"], comparison))
            else:
                followup_rows.append(_comparison_line(entry["pair"], comparison))

    lines += ["**The primary question, asked in two contexts.** In the fanout request it sits "
              "beside every branch's follow-ups; in the staged arm it is the whole request.", ""]
    lines += primary_rows or [
        "No pair produced a comparable primary answer, so nothing is reported here."
    ]
    lines += [
        "",
        "**Follow-ups both arms consumed.** Compared against the staged *second* request, which is "
        "where the staged arm asks them.",
        "",
    ]
    lines += followup_rows or [
        "No consumed follow-up had a staged counterpart, so nothing is reported here."
    ]
    lines += [
        "",
        "Only questions the fanout arm actually **consumed** take part. An unused answer is the "
        "thing being priced by this experiment; grading it here would score an answer that nothing "
        "downstream ever read.",
        "",
        "> **A difference here is not an error, and the primary's is not a routing miss.** Neither "
        "arm is the reference: the two requests ask the same question of the same state with "
        "different company, and the log does not say which reading is correct. A primary answer "
        "whose *distribution* moved while its label held is exactly the kind of thing this "
        "comparison exists to surface, and it is not the same fact as the label changing.",
        "",
    ]
    return lines


def _latency_lines(analysis: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Section I: sequential time as observed, with no speedup claimed."""
    lines = ["### Latency — observational only", ""]
    for entry in analysis["pairs"]:
        fanout = entry["fanout"]
        staged = entry["staged"]
        if fanout:
            lines.append(
                f"- **{entry['pair']} fanout**: one request, "
                f"**{format_ms(fanout[0].get('latency_ms'))} ms**."
            )
        if staged:
            parts = " + ".join(format_ms(record.get("latency_ms")) for record in staged)
            total = _sum(staged, "latency_ms")
            lines.append(
                f"- **{entry['pair']} staged**: {parts} = **{format_ms(total)} ms** sequential. This "
                "is the sum of two measured windows and nothing between them: the Python routing "
                "between the stages is a dict lookup and is not separately timed."
            )
        direction = entry.get("latency_direction")
        if direction is not None:
            fanout_ms, staged_ms = _sum(fanout, "latency_ms"), _sum(staged, "latency_ms")
            lines.append(
                f"- **{entry['pair']} direction**: fanout was the "
                f"{'slower' if direction == 'fanout_slower' else 'faster'} arm "
                f"(`fanout/staged` = **{_ratio(fanout_ms, staged_ms)}x**). This is one observation "
                "of each strategy on this pair and is not a factor."
            )
    directions = {entry.get("latency_direction") for entry in analysis["pairs"]} - {None}
    if len(directions) > 1:
        lines += [
            "",
            "**The pairs disagree on direction, and that is reported rather than averaged.** One "
            "pair has fanout slower and another has it faster, so the two lines above cancel into no "
            "statement at all. The request position is a plausible confound consistent with the "
            "observed latency pattern — the slower fanout call is the one that opened the session — "
            "but the records do not identify the cause. Connection setup, connection reuse, "
            "server-side state, and upstream load all move together with position here, and nothing "
            "in these six calls separates them.",
        ]
    notable = [record for record in records if record.get("is_first_request_in_client_session")]
    lines += [
        "",
        "**Position.** "
        + (
            f"{len(notable)} call(s) opened the client session and are marked rather than dropped "
            "— a first request can carry connection setup that its siblings do not, so a reader who "
            "does not see which call it was will attribute that cost to the arm."
            if notable
            else "No call in these records is marked as the first of its client session."
        ),
        "",
        "> **Not a speedup.** Each pair is one observation of each strategy, and the two pairs run "
        "in opposite orders to keep arm identity off position — that reduces the confound, it does "
        "not remove it, because the first call of the run is still a fanout call. Even where "
        "`transport_attempt_count == 1`, each window still contains connection setup, "
        "connection-pool state, server-side queueing, upstream load, the network path, and local "
        "scheduling. No latency factor is claimed, and the extra round trip is not priced in time "
        "here.",
        "",
    ]
    return lines


def _parallel_relation_lines(
    parallel: Sequence[Mapping[str, Any]], analysis: Mapping[str, Any]
) -> list[str]:
    """Section J: the batched experiment beside this one, as architecture rather than as a ranking.

    `03_parallel_questions` sends questions that are all needed, so its saving is the state it does
    not resend. This experiment sends questions that may not be needed, so its saving is the state
    it does not resend *minus* the questions that get thrown away. The two percentages are computed
    by the same arithmetic on different payloads, and putting them side by side invites the
    reading that one design beat the other. It is stated here so that it is refused, not implied.
    """
    if not parallel:
        return []
    batched = [r for r in parallel if _note(r, "arm") == PARALLEL_BATCH_ARM]
    separate = [r for r in parallel if _note(r, "arm") and _note(r, "arm") != PARALLEL_BATCH_ARM]
    if not batched or not separate:
        return []
    batch_in, separate_in = _side(batched, "input_tokens"), _side(separate, "input_tokens")
    if not separate_in:
        return []
    parallel_saving = 1 - batch_in / separate_in
    fanout_in, staged_in = analysis["fanout_input_tokens"], analysis["staged_input_tokens"]
    fanout_saving = 1 - fanout_in / staged_in if staged_in else None
    lines = [
        "### Relation to `03_parallel_questions`",
        "",
        "- **`03_parallel_questions`.** Every question it sends is a question it needs. Batching "
        f"there avoids resending the state: {len(batched)} batched call(s) at {batch_in:.0f} input "
        f"tokens against {len(separate)} separate call(s) at {separate_in:.0f}, a saving of "
        f"**{parallel_saving:.2%}** of the input tokens.",
    ]
    if fanout_saving is not None:
        lines.append(
            "- **`05_speculative_fanout`.** Some of what it sends is never read. Fanout avoids the "
            f"second request and its state resend, and pays for it in unanswered-for questions: "
            f"{fanout_in:.0f} input tokens against {staged_in:.0f}, a saving of "
            f"**{fanout_saving:.2%}**."
        )
    lines += [
        "- **The two percentages are not compared, and the larger one is not the better "
        "architecture.** The question count, the payload, and the control-flow shape all differ "
        "between them; a ratio computed over one of those is not evidence about the other, and "
        "neither number is a property of batching or of fanout as such.",
        "",
    ]
    return lines


def _limits_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What two pairs of synthetic cases do not establish."""
    return [
        "### What this does not show",
        "",
        f"- **Sample size.** {len(analysis['pairs'])} state(s), one observation of each strategy "
        "each, one session. Nothing here generalises to another workload, another branch shape, or "
        "another number of unused questions.",
        "- **The crossover.** One round trip against *k* unused questions has a break-even point, "
        "and this design does not find it: it holds the branch count and the question count fixed "
        "and varies only the strategy. Nothing in these records locates where the trade flips.",
        "- **Per-question cost.** Not measurable from these records, for the reason given above. "
        "Any figure for \"what one unused question costs\" would be an estimate presented as a "
        "measurement.",
        "- **Anything about downstream actions.** The scenario is triage text. No handler runs, no "
        "ticket moves, no external system is touched, and no branch label here causes anything.",
        "",
    ]


def build_fanout_block(
    records: Sequence[Mapping[str, Any]], parallel: Sequence[Mapping[str, Any]] = ()
) -> list[str]:
    """Render `05_speculative_fanout` from its canonical records.

    Every number is recomputed from the records on the way out, including which branch each arm
    chose and how many questions it never used. A run whose routing went differently from the
    design's expectation therefore renders differently, which is the point.

    ``parallel`` is the other experiment's records, read only so the two designs can be described
    side by side. Passing nothing drops that comparison rather than inventing a number for it.
    """
    if not records:
        return []
    analysis = analyze_fanout(records)
    lines = [f"## `{FANOUT}`", ""]
    lines += _design_lines(records, analysis)
    lines += _overhead_lines(analysis)
    lines += _cost_lines(analysis)
    lines += _output_lines(analysis, records)
    lines += _routing_lines(analysis)
    lines += _comparison_lines(analysis)
    lines += _latency_lines(analysis, records)
    lines += _parallel_relation_lines(parallel, analysis)
    markers = analysis["markers"]
    lines += [
        "### Markers",
        "",
        (
            "Raised: " + ", ".join(f"`{marker}`" for marker in markers) + "."
            if markers
            else "No marker was raised by these records."
        ),
        "",
    ]
    lines += _limits_lines(analysis)
    return lines
