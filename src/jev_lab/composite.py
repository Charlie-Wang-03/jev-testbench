"""`06_composite_scoring`: Jev judges, Python does the arithmetic.

The architecture this experiment is built around is the one the docs keep stating: System One
performs atomic semantic judgments, and ordinary code performs arithmetic and policy composition.
So the model is asked four `Score` questions -- one property each, on a 0..3 rubric -- and never
asked to add them, weight them, normalize them, invert a direction, or state a final risk. Those
are `float` operations on the Python side, in this module, with weights frozen before the run.

Two rules are load-bearing and are enforced by tests rather than by intent:

* **Confidence never enters the arithmetic.** A `Score` answer carries a confidence, and it is
  recorded, displayed, and used for nothing else. There is no confidence-weighted score, no
  confidence-discounted score, and no "composite confidence" -- the last would need a definition
  that does not currently exist, and averaging four confidences and giving the mean that name
  would invent one.
* **A missing or malformed dimension fails closed.** If a required answer is absent, is the wrong
  primitive, sits outside the rubric, carries an incompatible legend, or is not a finite number,
  the composite for that case is not computed at all. Nothing defaults to zero, nothing is
  dropped, no remaining weight is rescaled to compensate, and confidence is never substituted for
  a score. The case reports `COMPOSITE_SCORE_UNAVAILABLE` and the raw measurement stays exactly as
  the API returned it.

Precision: plain Python floats, computed left to right over a fixed dimension order, and the sum
is taken over the same contributions that are stored beside it, so
``composite_risk == sum(weighted_contribution)`` holds bit-for-bit rather than approximately.
Display rounding is a separate step applied at render time; it never feeds back into a stored
value.
"""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from .repeatability import format_ms, format_number

if TYPE_CHECKING:
    from typesafe_sdk import SystemOneResponse

COMPOSITE = "06_composite_scoring"

# The ordinal rubric every dimension shares. Four levels, 0..3.
COMPOSITE_SCALE_LEVELS = 4
COMPOSITE_TOP_LEVEL = COMPOSITE_SCALE_LEVELS - 1

COMPOSITE_DIMENSIONS: tuple[str, ...] = (
    "evidence_quality",
    "numerical_stability",
    "reproducibility",
    "failure_severity",
)

# Higher score means *better* for these three. They are inverted when they become risk.
COMPOSITE_BENEFICIAL: tuple[str, ...] = (
    "evidence_quality",
    "numerical_stability",
    "reproducibility",
)

# Higher score means *worse* for this one. It is NOT inverted, and a test holds that: inverting it
# would silently turn "severe, invalidating" into "no risk at all".
COMPOSITE_ADVERSE: tuple[str, ...] = ("failure_severity",)

# Frozen before any run. Nothing in the docs says these are the right weights; they are a design
# choice, no run may revise them, and every report that shows them says so.
COMPOSITE_WEIGHTS: dict[str, float] = {
    "evidence_quality": 0.30,
    "numerical_stability": 0.30,
    "reproducibility": 0.20,
    "failure_severity": 0.20,
}

# The scenario's ordinal sanity check, frozen before any run: the three states were written to sit
# in this order, and that is all it means. It is not an accuracy target, no exact value is
# expected, and a run that violates it is reported as it happened rather than repaired.
COMPOSITE_EXPECTED_ORDER: tuple[str, ...] = ("low_risk", "mixed", "high_risk")

# Raised when the observed composite order matches the frozen scenario order.
COMPOSITE_EXPECTED_ORDER_OBSERVED = "COMPOSITE_EXPECTED_ORDER_OBSERVED"

# Raised when it does not. The criteria and the weights are not to be edited to make this go away.
COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED = "COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED"

# Raised when a required dimension could not be used. The case's composite is not computed, and
# nothing is repaired in its place.
COMPOSITE_SCORE_UNAVAILABLE = "COMPOSITE_SCORE_UNAVAILABLE"

# Raised when the call that opened the client session is much the slowest in the experiment. It is a
# descriptive observation about this session's traffic, never a statement about a state: the first
# call is also the first state in the declared order, so position and state identity move together.
COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED = (
    "COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED"
)

# How much slower the session's first call must be than the slowest of the rest before the marker
# above is raised. A **demonstration parameter**: nothing in the docs says twice is the right line,
# it was fixed here for this experiment's three calls, and it gates nothing but the wording.
FIRST_REQUEST_LATENCY_OUTLIER_FACTOR = 2.0

RATIO_DECIMALS = 4
# Display precision for derived values. Chosen for reading, not for storage: the record keeps the
# full float and this is applied only on the way out.
DISPLAY_DECIMALS = 4


# --------------------------------------------------------------------------------------
# Arithmetic. Pure functions of numbers, with no API and no record involved.
# --------------------------------------------------------------------------------------


def normalize(score: float, top_level: int = COMPOSITE_TOP_LEVEL) -> float:
    """Put a rubric score on 0..1 by dividing by the top level, as the docs recommend."""
    return score / top_level


def risk_align(dimension: str, score: float, top_level: int = COMPOSITE_TOP_LEVEL) -> float:
    """Turn one dimension's score into a risk, in the direction *higher means worse*.

    The three beneficial dimensions are inverted so that a good result produces a low risk. The
    adverse dimension is already pointed the right way and is not inverted. A dimension that is in
    neither tuple is a programming error, not a data error, so it raises rather than defaulting.
    """
    if dimension in COMPOSITE_BENEFICIAL:
        return 1.0 - normalize(score, top_level)
    if dimension in COMPOSITE_ADVERSE:
        return normalize(score, top_level)
    raise KeyError(f"{dimension!r} is neither beneficial nor adverse; its direction is undefined")


def weighted_contribution(dimension: str, risk: float) -> float:
    """One dimension's share of the composite: its risk times its frozen weight."""
    return COMPOSITE_WEIGHTS[dimension] * risk


def composite_of(contributions: Sequence[float]) -> float:
    """The composite risk: the sum of the contributions, left to right, in the given order."""
    return sum(contributions)


def weights_sum() -> float:
    """The frozen weights' total. The design requires exactly 1.0; the tests assert it."""
    return sum(COMPOSITE_WEIGHTS.values())


# --------------------------------------------------------------------------------------
# Reading records
# --------------------------------------------------------------------------------------


def _note(record: Mapping[str, Any], key: str) -> Any:
    """Read one design-metadata key off a record, tolerating records written without notes."""
    return (record.get("notes") or {}).get(key)


def _derived(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """The locally computed values stored beside a record's answers, if they were stored."""
    return (record.get("notes") or {}).get("derived") or {}


def _answers(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """The answers a record carries, keyed by dimension name."""
    return record.get("answers") or {}


def _sum(records: Sequence[Mapping[str, Any]], field: str) -> float:
    """Sum one numeric field across records, treating an absent value as zero."""
    return sum(float(record.get(field) or 0) for record in records)


def case_order(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """The case ids in the order the run recorded them."""
    return [str(record.get("case_id")) for record in records]


# --------------------------------------------------------------------------------------
# The fail-closed check. One place, so no caller can skip it.
# --------------------------------------------------------------------------------------


def dimension_row(record: Mapping[str, Any], dimension: str) -> dict[str, Any]:
    """One dimension's raw answer and its derived values, or the reason it could not be used.

    The returned row always carries ``available``. When it is false the reason says what was wrong
    and *no* derived numbers are produced: there is no partial row to be accidentally summed, and
    nothing downstream can read a silent zero out of a missing answer.
    """
    row: dict[str, Any] = {"dimension": dimension, "weight": COMPOSITE_WEIGHTS.get(dimension)}
    answer = _answers(record).get(dimension)
    if answer is None:
        return row | {"available": False, "reason": "answer missing from the response"}
    kind = answer.get("type")
    if kind != "score":
        return row | {
            "available": False,
            "reason": f"answer is a {kind!r}, not a `score`",
        }
    legend = answer.get("legend") or {}
    if len(legend) != COMPOSITE_SCALE_LEVELS:
        return row | {
            "available": False,
            "reason": f"legend carries {len(legend)} level(s), rubric has {COMPOSITE_SCALE_LEVELS}",
        }
    raw = answer.get("score")
    if not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw != raw:
        return row | {"available": False, "reason": f"score is not a finite number ({raw!r})"}
    if not 0 <= raw <= COMPOSITE_TOP_LEVEL:
        return row | {
            "available": False,
            "reason": f"score {raw} is outside the rubric 0..{COMPOSITE_TOP_LEVEL}",
        }
    risk = risk_align(dimension, float(raw))
    contribution = weighted_contribution(dimension, risk)
    return row | {
        "available": True,
        "raw_score": float(raw),
        "normalized_score": normalize(float(raw)),
        "risk_aligned_value": risk,
        "weighted_contribution": contribution,
        "confidence": answer.get("confidence"),
        "probabilities": {str(level): value for level, value in (answer.get("probabilities") or {}).items()},
    }


def case_composite(record: Mapping[str, Any]) -> dict[str, Any]:
    """Every dimension's row for one case, plus the composite when all of them are usable.

    The composite is the sum of the very contributions returned in ``rows``, in this order, so the
    stored aggregate and the stored parts agree exactly rather than to within a rounding step.
    """
    rows = [dimension_row(record, dimension) for dimension in COMPOSITE_DIMENSIONS]
    unavailable = [row["dimension"] for row in rows if not row["available"]]
    result: dict[str, Any] = {
        "case_id": record.get("case_id"),
        "scenario_class": _note(record, "scenario_class"),
        "rows": rows,
    }
    if unavailable:
        return result | {
            "available": False,
            "unavailable": unavailable,
            "markers": [COMPOSITE_SCORE_UNAVAILABLE],
        }
    contributions = [row["weighted_contribution"] for row in rows]
    return result | {
        "available": True,
        "unavailable": [],
        "composite_risk": composite_of(contributions),
        "markers": [],
    }


def confidence_diagnostics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Min, max, and mean of the dimension confidences. A diagnostic, never an input.

    This is deliberately not called a composite confidence, and deliberately not given one. There
    is no definition of that quantity here, so the report presents the four numbers and their
    spread and stops.
    """
    values = [
        float(row["confidence"])
        for row in rows
        if row.get("available") and isinstance(row.get("confidence"), (int, float))
    ]
    if not values:
        return {"available": False, "values": []}
    return {
        "available": True,
        "values": values,
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def contribution_shares(case: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Each usable dimension's share of one case's composite. A decomposition, nothing more.

    A share says where a particular composite came from, not how much a dimension *ought* to
    matter. With three states and one observation each, no share here is evidence about how these
    dimensions behave in general, and a share is not a weight: the weights are frozen above and
    this is what they produced on this input.
    """
    composite = case.get("composite_risk")
    shares: list[dict[str, Any]] = []
    for row in case["rows"]:
        if not row["available"]:
            continue
        contribution = row["weighted_contribution"]
        shares.append(
            {
                "dimension": row["dimension"],
                "weight": row["weight"],
                "weighted_contribution": contribution,
                "share": (contribution / composite) if composite else None,
            }
        )
    return shares


def first_request_latency_outlier(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Whether the call that opened the session is far slower than the rest, and by how much.

    Returns the observation rather than a bare flag, so the report can state the ratio it is
    talking about instead of implying one. Missing latencies make the observation unavailable --
    "not recorded" is not a zero, and a ratio against an absent number would be invented.
    """
    head = [record for record in records if record.get("is_first_request_in_client_session")]
    rest = [record for record in records if not record.get("is_first_request_in_client_session")]
    latencies = [record.get("latency_ms") for record in (*head, *rest)]
    if not head or not rest or any(value is None for value in latencies):
        return {"available": False}
    first = float(head[0]["latency_ms"])
    slowest_rest = max(float(record["latency_ms"]) for record in rest)
    ratio = (first / slowest_rest) if slowest_rest else None
    return {
        "available": True,
        "first_latency_ms": first,
        "slowest_other_ms": slowest_rest,
        "ratio": ratio,
        "is_outlier": ratio is not None and ratio >= FIRST_REQUEST_LATENCY_OUTLIER_FACTOR,
    }


def probability_diagnostics(row: Mapping[str, Any]) -> dict[str, Any]:
    """The dominant rubric level and the margin over the runner-up. Not an input either."""
    probabilities = row.get("probabilities") or {}
    if not probabilities:
        return {"available": False}
    ranked = sorted(
        ((str(level), float(value)) for level, value in probabilities.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return {
        "available": True,
        "dominant_level": ranked[0][0],
        "dominant_probability": ranked[0][1],
        "margin": ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0),
    }


# --------------------------------------------------------------------------------------
# The whole analysis
# --------------------------------------------------------------------------------------


def composite_digest(case: Any, response: "SystemOneResponse") -> dict[str, Any]:
    """Write the per-dimension arithmetic into the canonical record, at run time.

    This is stored rather than recomputed at report time for the same reason `05` stores its
    routing decision: the weights are frozen now, and if a later edit ever changed them, a report
    recomputed under the new numbers would disagree with the record that was actually measured.
    Written here, the derived values stay attached to the answers that produced them.

    Only the arithmetic goes in. Confidence is not part of it, and no composite is written for a
    case that failed a check -- that case reports the reason instead.
    """
    from .recorder import serialize_answers

    record = {"case_id": case.case_id, "answers": serialize_answers(response)}
    result = case_composite(record)
    derived: dict[str, Any] = {
        "dimensions": {},
        "composite_available": result["available"],
    }
    for row in result["rows"]:
        if row["available"]:
            derived["dimensions"][row["dimension"]] = {
                "raw_score": row["raw_score"],
                "normalized_score": row["normalized_score"],
                "risk_aligned_value": row["risk_aligned_value"],
                "weight": row["weight"],
                "weighted_contribution": row["weighted_contribution"],
            }
        else:
            derived["dimensions"][row["dimension"]] = {"reason": row["reason"]}
    if result["available"]:
        derived["composite_risk"] = result["composite_risk"]
    return derived


def analyze_composite(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every derived quantity this experiment reports, computed from the canonical records.

    Nothing is carried in from the design's expectations except the frozen order itself, which is
    compared against rather than assumed. A run whose composites come out in a different order
    produces an analysis that says so.
    """
    cases = [case_composite(record) for record in records]
    scored = [case for case in cases if case["available"]]
    observed = [str(case["case_id"]) for case in sorted(scored, key=lambda c: c["composite_risk"])]
    expected = [name for name in COMPOSITE_EXPECTED_ORDER if name in case_order(records)]

    markers: list[str] = []
    for case in cases:
        markers.extend(case["markers"])
    latency = first_request_latency_outlier(records)
    if latency["available"] and latency["is_outlier"]:
        markers.append(COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED)
    if COMPOSITE_SCORE_UNAVAILABLE not in markers:
        if observed == expected:
            markers.append(COMPOSITE_EXPECTED_ORDER_OBSERVED)
        else:
            markers.append(COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED)

    return {
        "calls": len(records),
        "cases": cases,
        "expected_order": expected,
        "observed_order": observed,
        "markers": list(dict.fromkeys(markers)),
        "input_tokens": _sum(records, "input_tokens"),
        "output_tokens": _sum(records, "output_tokens"),
        "total_tokens": _sum(records, "total_tokens"),
        "cost_usd": _sum(records, "estimated_cost_usd"),
        "requests": len(records),
        "attempts": [record.get("transport_attempt_count") for record in records],
        "first_request_latency": latency,
    }


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _value(value: Any) -> str:
    """One derived number, at display precision. Presentation only -- never stored this way."""
    return "n/a" if value is None else format_number(float(value), DISPLAY_DECIMALS)


def _design_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What was sent and what was done with the answers, described from the records."""
    return [
        "**Design.** Four separate atomic `Score` questions per state, composed into one risk in "
        "Python.",
        "",
        f"- **Jev answers** {len(COMPOSITE_DIMENSIONS)} `Score` questions, one property each on a "
        f"0..{COMPOSITE_TOP_LEVEL} rubric. It is asked for no sum, no weight, no normalization, no "
        "direction inversion, and no verdict.",
        "- **Python does** the normalization, the direction alignment, the frozen weighting, and "
        "the sum — in `jev_lab/composite.py`, on floats, with the weights fixed before the run.",
        f"- **States.** {analysis['calls']} synthetic validation records from one domain, one "
        "request each, carrying the *same question objects* in the same order. Only the state "
        "changes; there is no separate-question arm, because `03_parallel_questions` already "
        "measured that split.",
        "",
    ]


def _weights_lines() -> list[str]:
    """The frozen weights, stated before any result is shown."""
    total = weights_sum()
    lines = [
        "### Frozen weights",
        "",
        "| dimension | direction | weight |",
        "|---|---|---|",
    ]
    for dimension in COMPOSITE_DIMENSIONS:
        if dimension in COMPOSITE_BENEFICIAL:
            direction = "higher score = better (inverted to risk)"
        else:
            direction = "higher score = worse (used as-is)"
        lines.append(f"| `{dimension}` | {direction} | {COMPOSITE_WEIGHTS[dimension]:.2f} |")
    lines += [
        f"| **total** | | **{total:.2f}** |",
        "",
        f"`normalized = score / {COMPOSITE_TOP_LEVEL}`; a beneficial dimension becomes "
        "`risk = 1 - normalized` and the adverse one becomes `risk = normalized`; "
        "`composite_risk = sum(weight × risk)`. The result is bounded to 0..1 by construction.",
        "",
        "> **These weights are a design choice, not a measurement.** Nothing in the documentation "
        "says 0.30/0.30/0.20/0.20 are the right weights for anything, they were fixed before the "
        "run, no run may revise them, and they do not come from the model. A different weighting "
        "is a different experiment.",
        "",
    ]
    return lines


def _dimension_table(case: Mapping[str, Any]) -> list[str]:
    """One case's per-dimension arithmetic, laid out so the sum can be checked by eye."""
    lines = [
        f"### `{case['case_id']}`",
        "",
        "| dimension | raw score | normalized | risk-aligned | weight | contribution | confidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in case["rows"]:
        if not row["available"]:
            lines.append(
                f"| `{row['dimension']}` | — | — | — | {row['weight']:.2f} | — | — |"
            )
            continue
        lines.append(
            f"| `{row['dimension']}` | {_value(row['raw_score'])} | "
            f"{_value(row['normalized_score'])} | {_value(row['risk_aligned_value'])} | "
            f"{row['weight']:.2f} | **{_value(row['weighted_contribution'])}** | "
            f"{_value(row['confidence'])} |"
        )
    lines.append("")
    if case["available"]:
        contributions = " + ".join(
            _value(row["weighted_contribution"]) for row in case["rows"]
        )
        lines += [
            f"**composite_risk = {contributions} = {_value(case['composite_risk'])}**",
            "",
            "The stored aggregate is the sum of the stored contributions in this order, so it "
            "agrees with them exactly and not merely to the displayed precision.",
            "",
        ]
    else:
        lines += [
            f"**`{COMPOSITE_SCORE_UNAVAILABLE}`** — "
            + "; ".join(
                f"`{row['dimension']}`: {row['reason']}"
                for row in case["rows"]
                if not row["available"]
            )
            + ".",
            "",
            "No composite was computed for this case. Nothing defaulted to zero, no dimension was "
            "dropped, no remaining weight was rescaled, and no confidence was substituted for a "
            "score. The raw measurement above is kept exactly as the API returned it.",
            "",
        ]
    return lines


def _diagnostic_lines(case: Mapping[str, Any]) -> list[str]:
    """Confidence and distribution, presented and explicitly not used."""
    lines: list[str] = []
    confidence = confidence_diagnostics(case["rows"])
    if confidence["available"]:
        lines.append(
            f"- **Dimension confidences** (diagnostic only): min "
            f"{_value(confidence['min'])}, max {_value(confidence['max'])}, mean "
            f"{_value(confidence['mean'])}. These four numbers enter no arithmetic. There is no "
            "such quantity as a composite confidence here — no definition of one exists, so none "
            "is computed and the mean is not given that name."
        )
    distributions = [
        (row["dimension"], probability_diagnostics(row))
        for row in case["rows"]
        if row.get("available")
    ]
    rendered = [
        f"`{dimension}` {diagnostics['dominant_level']} "
        f"(margin {_value(diagnostics['margin'])})"
        for dimension, diagnostics in distributions
        if diagnostics.get("available")
    ]
    if rendered:
        lines.append(
            "- **Dominant rubric level** (diagnostic only): "
            + "; ".join(rendered)
            + ". This shows how sharp the distribution behind an expected score was. It enters no "
            "arithmetic either."
        )
    return lines


def _decomposition_lines(cases: Sequence[Mapping[str, Any]]) -> list[str]:
    """Where each case's composite came from, stated as a decomposition and nothing else."""
    lines = [
        "### Contribution decomposition",
        "",
        "| case | largest contributor | its share | share range across dimensions |",
        "|---|---|---|---|",
    ]
    for case in cases:
        shares = contribution_shares(case)
        if not case.get("available") or not shares or not case.get("composite_risk"):
            # No composite, or a composite of exactly zero: either way no dimension is the largest
            # contributor, and naming one would be an artifact of the order the rows happen to be in.
            lines.append(f"| `{case['case_id']}` | — | — | — |")
            continue
        ranked = sorted(shares, key=lambda entry: -entry["weighted_contribution"])
        top = ranked[0]
        values = [entry["share"] for entry in shares if entry["share"] is not None]
        spread = f"{_value(min(values))}–{_value(max(values))}" if values else "n/a"
        lines.append(
            f"| `{case['case_id']}` | `{top['dimension']}` | **{_value(top['share'])}** | {spread} |"
        )
    lines += [
        "",
        "A share is where *this* composite came from, not how much a dimension ought to matter and "
        "not how much it would matter on another input. The weights are the frozen ones above; a "
        "share is only what those weights produced once combined with these particular scores. "
        "With one observation per state, no share here is evidence about these dimensions in "
        "general, and none of them is compared between states.",
        "",
    ]
    return lines


def _order_lines(analysis: Mapping[str, Any]) -> list[str]:
    """The frozen scenario order against the observed one, with neither called the answer."""
    expected = " < ".join(f"`{name}`" for name in analysis["expected_order"]) or "not recorded"
    observed = " < ".join(f"`{name}`" for name in analysis["observed_order"]) or "not computed"
    lines = [
        "### Scenario order",
        "",
        f"- **Expected (frozen before the run):** {expected}",
        f"- **Observed:** {observed}",
        "",
    ]
    if COMPOSITE_SCORE_UNAVAILABLE in analysis["markers"]:
        lines += [
            "At least one case produced no composite, so no ordering is reported. A missing case "
            "is not filled in and the chain is not completed from the remaining ones.",
            "",
        ]
    elif COMPOSITE_EXPECTED_ORDER_OBSERVED in analysis["markers"]:
        lines += [
            "The observed order matches the frozen one. The three states were written to sit in "
            "this order; that is all this comparison tests, and it is not an accuracy score.",
            "",
        ]
    else:
        lines += [
            f"**`{COMPOSITE_EXPECTED_ORDER_NOT_OBSERVED}`** — the observed order differs from the "
            "frozen one. It is reported as it happened. The criteria and the weights are not "
            "edited to make the order come out differently, and the run is not repeated until it "
            "does.",
            "",
        ]
    lines += [
        "> **This is not a benchmark.** The ordering is a sanity check on the synthetic scenario, "
        "written by hand, with three states and one observation each. It says nothing about how "
        "well the model judges risk on other inputs, and it is not an accuracy, a calibration, or "
        "a ground-truth score.",
        "",
    ]
    return lines


def _usage_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What the three calls used. Recorded, not compared between states."""
    attempts = analysis["attempts"]
    rendered = (
        ", ".join("not recorded" if value is None else str(value) for value in attempts)
        if attempts
        else "not recorded"
    )
    return [
        "### Usage",
        "",
        f"- {analysis['requests']} request(s): {analysis['input_tokens']:.0f} input, "
        f"{analysis['output_tokens']:.0f} output, {analysis['total_tokens']:.0f} total.",
        f"- `estimated_cost_usd` **${analysis['cost_usd']:.8f}** — a **local estimate** from this "
        "project's price table, keyed by the resolved model. TypeSafe Console billing is "
        "authoritative.",
        f"- `transport_attempt_count` per call, in order: {rendered}. A count of 1 licenses exactly "
        "one sentence — that call was not observed to retry — and is not evidence of pure model "
        "latency.",
        "- The three requests carry identical questions, so any token difference between them "
        "comes from the state. **No attempt is made to decompose it**: the API reports usage per "
        "request, so the tokens attributable to one part of a state are not separable from the "
        "rest, and no per-section figure is estimated here.",
        "",
    ]


def _latency_lines(analysis: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Latency, described and not compared. The declared order is stated because it confounds."""
    lines = ["### Latency — descriptive only", ""]
    for record in records:
        latency = record.get("latency_ms")
        lines.append(
            f"- `{record.get('case_id')}`: "
            + (
                f"**{format_ms(latency)} ms**"
                if latency is not None
                else "not recorded"
            )
            + (", the first request of the client session" if record.get("is_first_request_in_client_session") else "")
            + "."
        )
    lines += [
        "",
        "**The order is fixed and it confounds.** The three states run in the declared order "
        "`low_risk`, `mixed`, `high_risk`, which means state identity and request position move "
        "together: `low_risk` opens the client session and can carry connection setup its siblings "
        "do not. With three calls and one observation each, nothing here says which state was "
        "faster, and no such comparison is made.",
    ]
    first = analysis.get("first_request_latency") or {"available": False}
    if first.get("available") and first.get("is_outlier"):
        lines += [
            "",
            f"**`{COMPOSITE_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED}`** — the call that opened the "
            f"session is the longest of the three, at **{_value(first['ratio'])}x** the longest of "
            f"the rest. That call is also the first state in the declared order, so the two are "
            "confounded here and cannot be separated by these records. This is a description of "
            "this session's traffic, not a property of any state, and not a speed claim about "
            "either kind of input.",
        ]
    lines.append("")
    return lines


def _limits_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What three synthetic validations do not establish."""
    return [
        "### What this does not show",
        "",
        f"- **Sample size.** {analysis['calls']} state(s), one observation each, one session. "
        "Nothing here generalises to another domain, another rubric, or another number of "
        "dimensions.",
        "- **The weights are chosen, not derived.** 0.30/0.30/0.20/0.20 are a design decision. "
        "Nothing measured here says they are correct, and a different weighting would produce a "
        "different composite from the same four answers.",
        "- **The dimensions are designed to be orthogonal, not shown to be.** `numerical_stability` "
        "asks whether the result moves; `failure_severity` asks whether the movement matters. The "
        "rubrics separate those two questions, but no measurement here demonstrates that the model "
        "treats them as independent, and a shared reading of one state would show up as "
        "double-counting.",
        "- **Double counting is possible and is not estimated.** One underlying signal — an "
        "unstable solve, say — could move several atomic judgments at once, and the weighted sum "
        "would then count that one signal more than once. Three states with one observation each "
        "cannot estimate a covariance between dimensions, so none is computed here and no "
        "independence is claimed.",
        "- **The composite is not validated against anything.** There is no ground-truth risk for "
        "these states, so the composite is not scored, graded, or calibrated. It is a number "
        "produced by a stated formula.",
        "- **Nothing downstream acts on it.** No threshold is applied, no alert fires, no request "
        "is blocked. The scenario is validation text and the composite ends at the report.",
        "",
    ]


def build_composite_block(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Render `06_composite_scoring` from its canonical records.

    Every number is recomputed from the records on the way out, so a run whose answers differ
    renders differently -- including one whose composites come out in an order the scenario did not
    expect.
    """
    if not records:
        return []
    analysis = analyze_composite(records)
    lines = [f"## `{COMPOSITE}`", ""]
    lines += _design_lines(analysis)
    lines += _weights_lines()
    for case in analysis["cases"]:
        lines += _dimension_table(case)
        diagnostics = _diagnostic_lines(case)
        if diagnostics:
            lines += diagnostics + [""]
    lines += _decomposition_lines(analysis["cases"])
    lines += _order_lines(analysis)
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
    lines += _usage_lines(analysis)
    lines += _latency_lines(analysis, records)
    lines += _limits_lines(analysis)
    return lines
