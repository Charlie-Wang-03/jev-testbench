"""`12_function_routing`: Jev chooses a route, Python runs a handler that was frozen in advance.

The architecture this experiment is built around is the one the docs keep stating: Jev performs an
atomic semantic judgment, and ordinary code performs the dispatch. Here the judgment is a `Choice`
over a **registry of function names fixed before the run**, followed by a second `Choice` over a
**closed set of argument labels for that function**. Python then looks the name up in a dict and
calls a handler that does nothing.

Six rules are load-bearing, and tests hold each one:

* **Jev never produces code.** No answer is `eval`-ed, `exec`-ed, imported, or turned into a dotted
  path. The only thing an answer can select is a key that was already in the registry when the run
  started, and the only call Python makes is `HANDLERS[name](value)`.
* **The registry is closed.** A label the registry does not carry is not routed to a fallback and is
  not "close enough" to one. There is no fuzzy matching, no first-entry default, and no handler
  built at run time. The case reports `FUNCTION_ROUTE_UNAVAILABLE`.
* **Arguments are a closed set per function.** The model selects a label; it does not author one. A
  value outside the allowed set for the selected function fails closed rather than being passed
  through, coerced, or dropped.
* **Absent routing never becomes a default.** A missing answer, a wrong primitive, a missing
  argument, or an unusable argument label all stop before execution.
* **The handlers are inert.** Each returns a fixed dict and nothing else: no file, no network, no
  subprocess, no shell, no mail, no change to this project. The execution result that reaches the
  log comes from Python, and the model's response has no field that could carry one.
* **The human-review policy is frozen, and it can only suppress.** A handler runs only when the
  frozen policy permits it. The policy can never *add* an action, and a policy input that cannot be
  read suppresses rather than passes.

Correctness is reported as a count on four synthetic cases. It is not an accuracy: the expected
labels were written alongside the states, before the run, so they are the scenario's intention
rather than an independent truth, and four cases support no rate.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from .repeatability import format_ms, format_number

if TYPE_CHECKING:
    from typesafe_sdk import SystemOneResponse

ROUTING = "12_function_routing"


# --------------------------------------------------------------------------------------
# The registry. Frozen before the run; nothing else is reachable.
# --------------------------------------------------------------------------------------


def inspect_residuals(region: str) -> dict[str, Any]:
    """Return a fixed dict describing where a residual was looked at. Reads nothing."""
    return {
        "handler": "inspect_residuals",
        "region": region,
        "executed": True,
        "side_effect": False,
    }


def compare_runs(comparison: str) -> dict[str, Any]:
    """Return a fixed dict describing which two runs were set against each other. Reads nothing."""
    return {
        "handler": "compare_runs",
        "comparison": comparison,
        "executed": True,
        "side_effect": False,
    }


def request_more_evidence(evidence_type: str) -> dict[str, Any]:
    """Return a fixed dict describing what was asked for. Fetches nothing."""
    return {
        "handler": "request_more_evidence",
        "evidence_type": evidence_type,
        "executed": True,
        "side_effect": False,
    }


def escalate_for_review(reason: str) -> dict[str, Any]:
    """Return a fixed dict describing what would be sent for review. Contacts nobody."""
    return {
        "handler": "escalate_for_review",
        "reason": reason,
        "executed": True,
        "side_effect": False,
    }


# The only names that can ever be dispatched, and the only callables they can reach. `HANDLERS` is
# the sole lookup path: no caller indexes this module by a name that came off the wire without
# going through `route_decision`, and `route_decision` refuses anything not already in this dict.
HANDLERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "inspect_residuals": inspect_residuals,
    "compare_runs": compare_runs,
    "request_more_evidence": request_more_evidence,
    "escalate_for_review": escalate_for_review,
}

ROUTING_FUNCTIONS: tuple[str, ...] = tuple(HANDLERS)

# One required argument per function, each a closed set. The model selects from these; it never
# supplies free text, a path, a query, a URL, or a number.
ROUTING_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "inspect_residuals": ("global", "boundary", "high_gradient_region"),
    "compare_runs": ("resolution", "seed", "solver_configuration"),
    "request_more_evidence": ("convergence_check", "independent_reproduction", "diagnostic_plot"),
    "escalate_for_review": ("unresolved_discrepancy", "unphysical_values", "resource_limit"),
}

# What the argument is called once selected: the keyword the handler is called with, and the name
# the record uses. Display and dispatch only -- it is never sent anywhere.
ROUTING_ARGUMENT_NAME: dict[str, str] = {
    "inspect_residuals": "region",
    "compare_runs": "comparison",
    "request_more_evidence": "evidence_type",
    "escalate_for_review": "reason",
}

# The question that carries each function's argument. Every request asks all four -- the function is
# not known when the request is written -- and Python consumes only the one belonging to the
# selected function. This is `05_speculative_fanout`'s fan-out pattern applied to routing.
ROUTING_ARGUMENT_QUESTION: dict[str, str] = {
    "inspect_residuals": "argument_inspect_residuals",
    "compare_runs": "argument_compare_runs",
    "request_more_evidence": "argument_more_evidence",
    "escalate_for_review": "argument_escalate_for_review",
}

ROUTING_ARGUMENT_QUESTIONS: tuple[str, ...] = tuple(
    ROUTING_ARGUMENT_QUESTION[name] for name in ROUTING_FUNCTIONS
)

# The question carrying the function Choice itself.
ROUTING_FUNCTION_QUESTION = "function"
# The Noul that feeds the human-review half of the policy.
ROUTING_REVIEW_QUESTION = "needs_human_review"

# The four synthetic cases: (case id, expected function, expected argument, expected to need
# review). Written with the states, before any request, and kept here so the expectation table the
# report renders and the notes the records carry cannot drift apart.
ROUTING_EXPECTED: tuple[tuple[str, str, str, bool], ...] = (
    ("oscillating_error", "inspect_residuals", "high_gradient_region", False),
    ("refinement_difference", "compare_runs", "resolution", False),
    ("unchecked_result", "request_more_evidence", "independent_reproduction", False),
    ("out_of_range_values", "escalate_for_review", "unphysical_values", True),
)

ROUTING_CASE_ORDER: tuple[str, ...] = tuple(row[0] for row in ROUTING_EXPECTED)


def arguments_for(function: str) -> tuple[str, ...]:
    """The allowed argument labels for one function. Raises for a name outside the registry."""
    return ROUTING_ARGUMENTS[function]


def argument_allowed(function: str, label: Any) -> bool:
    """Whether ``label`` is one of the frozen labels for ``function``. Exact match only."""
    return isinstance(label, str) and label in ROUTING_ARGUMENTS.get(function, ())


# --------------------------------------------------------------------------------------
# The frozen policy. Both numbers below are demonstration parameters.
# --------------------------------------------------------------------------------------

# A route is executed only when its Choice confidence reaches this floor. Nothing in the docs says
# 0.8 is the right line, it was fixed here for these four calls before any of them ran, and it gates
# the handler and nothing else. It is **not calibrated** and not claimed to be optimal.
ROUTING_CONFIDENCE_FLOOR = 0.8

# A route is executed only when `needs_human_review` comes back below this. Same status: a
# demonstration parameter, fixed before the run, uncalibrated, and not a recommendation.
ROUTING_HUMAN_REVIEW_THRESHOLD = 0.5

# --------------------------------------------------------------------------------------
# Outcomes and markers
# --------------------------------------------------------------------------------------

# The route could not be resolved at all: an answer was missing, was the wrong primitive, carried a
# label the registry does not hold, or carried an argument the frozen set does not allow. No handler
# is called, no fallback is taken, and the raw measurement stays exactly as the API returned it.
FUNCTION_ROUTE_UNAVAILABLE = "FUNCTION_ROUTE_UNAVAILABLE"

# The route resolved, and the frozen policy declined to execute it. No handler is called.
FUNCTION_EXECUTION_SUPPRESSED = "FUNCTION_EXECUTION_SUPPRESSED"

# Every case resolved and every returned function matched the label frozen with its state.
ROUTING_EXPECTED_FUNCTIONS_OBSERVED = "ROUTING_EXPECTED_FUNCTIONS_OBSERVED"

# At least one case resolved to a different function than the one frozen with its state.
ROUTING_FUNCTION_MISMATCH_OBSERVED = "ROUTING_FUNCTION_MISMATCH_OBSERVED"

# The state written to be the one a person should look at did trip the policy, and the one written
# not to did not. Either way it is reported as it happened; neither the states nor the thresholds
# are edited afterwards.
#
# Both directions are compared, because they are different failures. A case written to need review
# that runs anyway is one; a case written *not* to need review that is withheld is the other, and
# only the second one says the frozen policy and the model's answers disagree about a scenario the
# design believed was routine. If either occurs, the expectation was missed -- and a missed
# expectation is a finding to report, never something to close by moving a threshold afterwards.
ROUTING_SUPPRESSION_EXPECTATION_MET = "ROUTING_SUPPRESSION_EXPECTATION_MET"
ROUTING_SUPPRESSION_EXPECTATION_MISSED = "ROUTING_SUPPRESSION_EXPECTATION_MISSED"

# The policy withheld at least one route and no handler ran for any withheld route. This is the
# mechanism working: a route existed, the frozen policy declined it, and nothing happened. It says
# nothing about whether withholding was the *right* decision for that scenario -- that is what the
# expectation markers above are for, and the two can disagree.
FAIL_CLOSED_SUPPRESSION_REALIZED = "FAIL_CLOSED_SUPPRESSION_REALIZED"

# Which part of the chain a real run actually reached. A run that routes correctly and then
# withholds every route has exercised routing, argument selection, and the policy, but has *not*
# exercised `HANDLERS[name](argument)` on a live route: the execution branch is never entered, so
# no handler result is measured under real answers. Offline tests can show the branch exists; only
# a run that takes it can show it runs. The two markers are kept apart so a report cannot describe
# a withheld run as a demonstration of the whole chain.
ACTUAL_HANDLER_EXECUTION_REALIZED = "ACTUAL_HANDLER_EXECUTION_REALIZED"
ACTUAL_HANDLER_EXECUTION_UNTESTED = "ACTUAL_HANDLER_EXECUTION_UNTESTED"

# Raised when the call that opened the client session is much the slowest in the experiment. A
# descriptive observation about this session's traffic, never a statement about a route: the first
# call is also the first case in the declared order, so position and case identity move together.
ROUTING_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED = "ROUTING_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED"

# How much slower the session's first call must be before the marker above is raised. A
# **demonstration parameter**: nothing says twice is the right line, it was fixed here for this
# experiment's four calls, and it gates nothing but the wording.
FIRST_REQUEST_LATENCY_OUTLIER_FACTOR = 2.0

# Outcome labels, one per case. They describe what Python did, not what the model said.
OUTCOME_EXECUTED = "executed"
OUTCOME_HUMAN_REVIEW = "human_review"
OUTCOME_ROUTE_UNAVAILABLE = "route_unavailable"

# Display precision for derived values. Chosen for reading, not for storage: the record keeps the
# full float and this is applied only on the way out.
DISPLAY_DECIMALS = 4


# --------------------------------------------------------------------------------------
# Reading records
# --------------------------------------------------------------------------------------


def _note(record: Mapping[str, Any], key: str) -> Any:
    """Read one design-metadata key off a record, tolerating records written without notes."""
    return (record.get("notes") or {}).get(key)


def _answers(record: Mapping[str, Any]) -> Mapping[str, Any]:
    """The answers a record carries, keyed by question name."""
    return record.get("answers") or {}


def _finite(value: Any) -> float | None:
    """A number, or ``None`` for anything that is not one. ``bool`` and ``NaN`` are not numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return None if number != number or number in (float("inf"), float("-inf")) else number


def _sum(records: Sequence[Mapping[str, Any]], field: str) -> float:
    """Sum one numeric field across records, treating an absent value as zero."""
    return sum(float(record.get(field) or 0) for record in records)


# --------------------------------------------------------------------------------------
# The decision. One place, so no caller can dispatch without going through it.
# --------------------------------------------------------------------------------------


def noul_answer(record: Mapping[str, Any], name: str) -> Any:
    """The value of a Noul answer, or ``None`` for a missing one or another answer kind."""
    answer = _answers(record).get(name)
    if answer is None or answer.get("type") != "noul":
        return None
    return answer.get("noul")


def _unavailable(
    record: Mapping[str, Any], reason: str, asked: Sequence[str]
) -> dict[str, Any]:
    """The fail-closed decision: the reason, no route, no handler, and nothing repaired."""
    return {
        "case_id": record.get("case_id"),
        "expected_function": _note(record, "expected_function"),
        "expected_argument": _note(record, "expected_argument"),
        "expects_suppression": _note(record, "expects_suppression"),
        "available": False,
        "unavailable_reason": reason,
        "selected_function": None,
        "selected_arguments": {},
        "argument_question": None,
        "argument_questions_asked": list(asked),
        "argument_answers_consumed": [],
        "argument_answers_unused": list(asked),
        "confidence": None,
        "probabilities": {},
        "dominant_probability": None,
        "margin": None,
        "needs_human_review": None,
        "outcome": OUTCOME_ROUTE_UNAVAILABLE,
        "handler_called": False,
        "handler_result": None,
        # Not `False`: the policy was never reached, so no gate was evaluated. The handler did not
        # run, and a report says so through the outcome, not by claiming a gate declined it.
        "execution_suppressed": False,
        "suppression_reason": None,
        "confidence_gate_pass": None,
        "review_gate_pass": None,
        "execution_allowed": None,
        "matches_expected_function": None,
        "matches_expected_argument": None,
        "markers": [FUNCTION_ROUTE_UNAVAILABLE],
    }


def route_decision(record: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve one record into a dispatch decision, or into the reason there is none.

    Every exit below either executes a registered handler or returns a reason. There is no third
    path: no default handler, no nearest name, no argument guessed from the state, and no attempt to
    repair a partially-readable answer. A decision that cannot be completed is reported as
    unavailable, and the handler is not called.

    The expected labels are read from the record's own design notes and are used *only* to fill in
    the comparison fields. Nothing here reads them before the decision is made, so an expectation
    can never steer a route, and a returned label that disagrees with one is recorded as a
    disagreement rather than corrected.
    """
    asked = list(ROUTING_ARGUMENT_QUESTIONS)
    function_answer = _answers(record).get(ROUTING_FUNCTION_QUESTION)
    if function_answer is None:
        return _unavailable(record, "the routing answer is missing from the response", asked)
    kind = function_answer.get("type")
    if kind != "choice":
        return _unavailable(record, f"the routing answer is a {kind!r}, not a `choice`", asked)

    label = function_answer.get("choice")
    if not isinstance(label, str) or label not in HANDLERS:
        # The registry is closed. An unknown label is not matched to a similar one, and the first
        # entry is not used as a stand-in.
        return _unavailable(
            record,
            f"the returned label {label!r} is not a name in the frozen registry",
            asked,
        )

    question = ROUTING_ARGUMENT_QUESTION[label]
    argument_answer = _answers(record).get(question)
    if argument_answer is None:
        return _unavailable(
            record, f"the argument answer {question!r} for `{label}` is missing", asked
        )
    argument_kind = argument_answer.get("type")
    if argument_kind != "choice":
        return _unavailable(
            record,
            f"the argument answer {question!r} is a {argument_kind!r}, not a `choice`",
            asked,
        )
    value = argument_answer.get("choice")
    if not argument_allowed(label, value):
        return _unavailable(
            record,
            f"the returned argument {value!r} is not in the frozen set for `{label}`",
            asked,
        )

    probabilities = {
        str(name): float(number)
        for name, number in (function_answer.get("probabilities") or {}).items()
        if _finite(number) is not None
    }
    ranked = sorted(probabilities.items(), key=lambda item: (-item[1], item[0]))
    decision: dict[str, Any] = {
        "case_id": record.get("case_id"),
        "expected_function": _note(record, "expected_function"),
        "expected_argument": _note(record, "expected_argument"),
        "expects_suppression": _note(record, "expects_suppression"),
        "available": True,
        "unavailable_reason": None,
        "selected_function": label,
        "selected_arguments": {ROUTING_ARGUMENT_NAME[label]: value},
        "argument_question": question,
        "argument_questions_asked": asked,
        "argument_answers_consumed": [question],
        "argument_answers_unused": [name for name in asked if name != question],
        "confidence": _finite(function_answer.get("confidence")),
        "probabilities": probabilities,
        "dominant_probability": ranked[0][1] if ranked else None,
        "margin": (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else None,
        "needs_human_review": _finite(noul_answer(record, ROUTING_REVIEW_QUESTION)),
        "markers": [],
    }
    decision |= _policy(decision)
    decision |= {
        "matches_expected_function": (
            None
            if decision["expected_function"] is None
            else label == decision["expected_function"]
        ),
        "matches_expected_argument": (
            None
            if decision["expected_argument"] is None
            else value == decision["expected_argument"]
        ),
    }
    return decision


def _gates(confidence: float | None, review: float | None) -> dict[str, Any]:
    """Both gates, evaluated independently, from the two numbers the policy reads.

    `_policy` stops at the first gate that fails, so the single `suppression_reason` it records
    names one condition and can be read as "this is the only thing standing in the way". Evaluating
    each gate on its own is what makes the difference visible: a case withheld by the confidence
    floor alone would run if the floor moved, and a case that also fails the review gate would not.

    A gate whose input is missing is ``None`` -- *not evaluated* is not the same as *failed*, and a
    report that rendered them the same way would invent a comparison. The policy suppresses in both
    cases, so `execution_allowed` is `True` only when both gates passed.
    """
    confidence_pass = None if confidence is None else confidence >= ROUTING_CONFIDENCE_FLOOR
    review_pass = None if review is None else review < ROUTING_HUMAN_REVIEW_THRESHOLD
    return {
        "confidence_gate_pass": confidence_pass,
        "review_gate_pass": review_pass,
        "execution_allowed": confidence_pass is True and review_pass is True,
    }


def _policy(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the frozen human-review policy and execute the handler only if it allows it.

    The policy reads two numbers, both frozen above, and can only ever move a case from *executed*
    to *suppressed*. An input it cannot read -- a missing confidence, a missing review signal --
    suppresses rather than passing, because the policy was not consulted successfully and proceeding
    would mean acting on a check that never ran.
    """
    confidence = decision["confidence"]
    review = decision["needs_human_review"]
    gates = _gates(confidence, review)
    if confidence is None:
        return _suppressed(decision, "the route's confidence was not recorded", gates)
    if confidence < ROUTING_CONFIDENCE_FLOOR:
        return _suppressed(
            decision,
            f"route confidence {confidence} is below the frozen floor {ROUTING_CONFIDENCE_FLOOR}",
            gates,
        )
    if review is None:
        return _suppressed(decision, "`needs_human_review` was not recorded", gates)
    if review >= ROUTING_HUMAN_REVIEW_THRESHOLD:
        return _suppressed(
            decision,
            f"`needs_human_review` {review} is at or above the frozen threshold "
            f"{ROUTING_HUMAN_REVIEW_THRESHOLD}",
            gates,
        )
    return _executed(decision, gates)


def _suppressed(
    decision: Mapping[str, Any], reason: str, gates: Mapping[str, Any]
) -> dict[str, Any]:
    """The decision with the handler withheld. Nothing is called and nothing is substituted."""
    return {
        "outcome": OUTCOME_HUMAN_REVIEW,
        "handler_called": False,
        "handler_result": None,
        "execution_suppressed": True,
        "suppression_reason": reason,
        "markers": [FUNCTION_EXECUTION_SUPPRESSED],
    } | dict(gates)


def _executed(decision: Mapping[str, Any], gates: Mapping[str, Any]) -> dict[str, Any]:
    """The decision with the handler run. The result below comes from Python, not the response."""
    function = decision["selected_function"]
    name, value = next(iter(decision["selected_arguments"].items()))
    assert name == ROUTING_ARGUMENT_NAME[function]
    return {
        "outcome": OUTCOME_EXECUTED,
        "handler_called": True,
        "handler_result": HANDLERS[function](value),
        "execution_suppressed": False,
        "suppression_reason": None,
        "markers": [],
    } | dict(gates)


def analyze_routing(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Every derived quantity this experiment reports, computed from the canonical records.

    The counts are counts. `functions_matched` is `n` of four synthetic cases chosen by hand, and it
    is not turned into a rate anywhere: with one observation per case and expectations written
    alongside the states, a percentage would carry a precision this design does not have.
    """
    cases = [route_decision(record) for record in records]
    resolved = [case for case in cases if case["available"]]
    matched = [case for case in resolved if case["matches_expected_function"]]
    argument_matched = [case for case in resolved if case["matches_expected_argument"]]
    suppressed = [case for case in cases if case["execution_suppressed"]]
    executed = [case for case in cases if case["handler_called"]]
    unavailable = [case for case in cases if not case["available"]]

    markers: list[str] = []
    for case in cases:
        markers.extend(case["markers"])
    if unavailable:
        markers.append(FUNCTION_ROUTE_UNAVAILABLE)
    elif len(matched) == len(cases):
        markers.append(ROUTING_EXPECTED_FUNCTIONS_OBSERVED)
    elif len(matched) < len(resolved):
        markers.append(ROUTING_FUNCTION_MISMATCH_OBSERVED)

    # The state written to be the one a person should look at, and the states written not to be. The
    # comparison is fixed with the states; a run that disagrees is reported as it happened.
    expected_to_suppress = [case for case in cases if case["expects_suppression"]]
    observed_suppression = [case for case in expected_to_suppress if case["execution_suppressed"]]

    # Both directions, and only where an expectation was actually recorded: a record with no
    # `expects_suppression` note has no expectation to miss, and counting its suppression as
    # unexpected would manufacture a disagreement out of missing metadata.
    expectation_recorded = [case for case in cases if case["expects_suppression"] is not None]
    unexpectedly_suppressed = [
        case
        for case in cases
        if case["execution_suppressed"] and case["expects_suppression"] is False
    ]
    unrealized_suppression = [
        case
        for case in cases
        if case["expects_suppression"] is True and not case["execution_suppressed"]
    ]
    if expectation_recorded:
        if unexpectedly_suppressed or unrealized_suppression:
            markers.append(ROUTING_SUPPRESSION_EXPECTATION_MISSED)
        else:
            markers.append(ROUTING_SUPPRESSION_EXPECTATION_MET)

    # Which gate withheld each suppressed case, recomputed from the two numbers rather than read off
    # the single stored reason. `_policy` stops at the first failure, so its reason names one gate;
    # a case that fails both would look like it fails only the first.
    withheld_by_both = [
        case
        for case in suppressed
        if case["confidence_gate_pass"] is not True and case["review_gate_pass"] is not True
    ]
    withheld_by_review_alone = [
        case
        for case in suppressed
        if case["confidence_gate_pass"] is True and case["review_gate_pass"] is not True
    ]
    withheld_by_confidence_alone = [
        case
        for case in suppressed
        if case["confidence_gate_pass"] is not True and case["review_gate_pass"] is True
    ]

    # The mechanism working, stated separately from the policy's verdict. Withholding at least one
    # route while running no handler for it is what fail-closed means; whether the *right* routes
    # were withheld is the expectation comparison above, and the two are allowed to disagree.
    if suppressed and all(not case["handler_called"] for case in suppressed):
        markers.append(FAIL_CLOSED_SUPPRESSION_REALIZED)

    # What a real run actually reached. `executed_count == 0` with routes resolved means the
    # execution branch was never entered under live answers -- the offline tests cover that branch,
    # this run did not.
    if executed:
        markers.append(ACTUAL_HANDLER_EXECUTION_REALIZED)
    elif cases:
        markers.append(ACTUAL_HANDLER_EXECUTION_UNTESTED)

    latency = first_request_latency_outlier(records)
    if latency["available"] and latency["is_outlier"]:
        markers.append(ROUTING_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED)

    return {
        "calls": len(records),
        "cases": cases,
        "resolved_count": len(resolved),
        "matched_count": len(matched),
        "argument_matched_count": len(argument_matched),
        "unavailable_count": len(unavailable),
        # Both suppression counts are kept: a case can be suppressed because the policy declined to
        # act on a route the scenario did not intend, and that is not the same thing as the state
        # written for review having tripped it.
        "suppressed_count": len(suppressed),
        "executed_count": len(executed),
        "suppression_expected_count": len(expected_to_suppress),
        "suppression_expected_hit": len(observed_suppression),
        "unexpected_suppression_count": len(unexpectedly_suppressed),
        "unrealized_suppression_count": len(unrealized_suppression),
        "expectation_recorded_count": len(expectation_recorded),
        "unexpected_suppression_cases": [case["case_id"] for case in unexpectedly_suppressed],
        "unrealized_suppression_cases": [case["case_id"] for case in unrealized_suppression],
        "withheld_by_both_gates_count": len(withheld_by_both),
        "withheld_by_review_alone_count": len(withheld_by_review_alone),
        "withheld_by_confidence_alone_count": len(withheld_by_confidence_alone),
        "markers": list(dict.fromkeys(markers)),
        "input_tokens": _sum(records, "input_tokens"),
        "output_tokens": _sum(records, "output_tokens"),
        "total_tokens": _sum(records, "total_tokens"),
        "cost_usd": _sum(records, "estimated_cost_usd"),
        "requests": len(records),
        "attempts": [record.get("transport_attempt_count") for record in records],
        "first_request_latency": latency,
    }


def first_request_latency_outlier(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Whether the call that opened the session is far slower than the rest, and by how much.

    Returns the observation rather than a bare flag, so the report can state the ratio it is talking
    about instead of implying one. Missing latencies make the observation unavailable -- "not
    recorded" is not a zero, and a ratio against an absent number would be invented.
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


# --------------------------------------------------------------------------------------
# The record's derived block, written at run time
# --------------------------------------------------------------------------------------


def routing_digest(case: Any, response: "SystemOneResponse") -> dict[str, Any]:
    """Write the dispatch decision and its result into the canonical record, at run time.

    Stored rather than recomputed at report time for the same reason `05` stores its routing
    decision: the registry, the argument sets and the policy thresholds are frozen now, and if a
    later edit changed any of them, a report recomputed under the new ones would disagree with the
    record that was actually measured. Written here, the decision stays attached to the answers that
    produced it -- including a decision that failed closed, which is stored as the reason rather
    than omitted.

    The handler runs inside this function. That is the only place it runs, and it runs only when
    `route_decision` says the policy allowed it.
    """
    from .recorder import serialize_answers

    record = {
        "case_id": case.case_id,
        "answers": serialize_answers(response),
        "notes": dict(case.notes),
    }
    decision = route_decision(record)
    derived: dict[str, Any] = {
        "expected_function": decision["expected_function"],
        "expected_argument": decision["expected_argument"],
        "expects_suppression": decision["expects_suppression"],
        "registry": list(ROUTING_FUNCTIONS),
        "argument_schema": {name: list(values) for name, values in ROUTING_ARGUMENTS.items()},
        "argument_questions_asked": decision["argument_questions_asked"],
        "outcome": decision["outcome"],
        "handler_called": decision["handler_called"],
        "execution_suppressed": decision["execution_suppressed"],
        "suppression_reason": decision["suppression_reason"],
    }
    if not decision["available"]:
        derived["route_unavailable_reason"] = decision["unavailable_reason"]
        return derived
    derived |= {
        "selected_function": decision["selected_function"],
        "selected_arguments": decision["selected_arguments"],
        "route_confidence": decision["confidence"],
        "argument_answers_consumed": decision["argument_answers_consumed"],
        "argument_answers_unused": decision["argument_answers_unused"],
        "needs_human_review": decision["needs_human_review"],
        "matches_expected_function": decision["matches_expected_function"],
        "matches_expected_argument": decision["matches_expected_argument"],
        "handler_result": decision["handler_result"],
    }
    return derived


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _value(value: Any) -> str:
    """One derived number, at display precision. Presentation only -- never stored this way."""
    return "n/a" if value is None else format_number(float(value), DISPLAY_DECIMALS)


def _bool(value: Any) -> str:
    """A three-valued comparison field, with `not recorded` kept distinct from `no`."""
    return "not recorded" if value is None else ("yes" if value else "no")


def _design_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What was sent and what was done with the answers, described from the records."""
    return [
        "**Design.** One `Choice` over a registry of four function names, one `Choice` per function "
        "over its closed set of argument labels, and one `Noul`. Python selects a handler and calls "
        "it; Jev produces no code and no side effect.",
        "",
        f"- **Jev answers** a routing `Choice` over the registry, "
        f"{len(ROUTING_FUNCTIONS)} speculative argument `Choice`s (one per function, all in the "
        "same request, since the function is not known when the request is written), and a "
        f"`{ROUTING_REVIEW_QUESTION}` `Noul`. It is asked for no argument value outside those sets, "
        "no code, and no verdict about what should happen next.",
        "- **Python does** the dispatch — in `jev_lab/routing.py`, by looking the returned label up "
        "in a dict that was frozen before the run and calling the one function it names.",
        "- **No `Score` rides along.** A `Score` question would have to earn its tokens: nothing in "
        "the frozen policy reads one, and `04_confidence` and `06_composite_scoring` already "
        "measure how the ordinal scale behaves. Asking for one here would add a question no branch "
        "of the code consults.",
        f"- **States.** {analysis['calls']} synthetic validation records from one domain, one "
        "request each, carrying the *same question objects* in the same order. Only the state "
        "changes.",
        "",
    ]


def _registry_lines() -> list[str]:
    """The frozen registry and argument sets, stated before any result is shown."""
    lines = [
        "### Frozen registry",
        "",
        "| function | argument | allowed labels |",
        "|---|---|---|",
    ]
    for function in ROUTING_FUNCTIONS:
        allowed = ", ".join(f"`{label}`" for label in ROUTING_ARGUMENTS[function])
        lines.append(f"| `{function}` | `{ROUTING_ARGUMENT_NAME[function]}` | {allowed} |")
    lines += [
        "",
        "Python reaches a handler only through `HANDLERS[function]`, and only after `route_decision` "
        "has checked the label against this table. A label outside it is not matched to a neighbour, "
        "not defaulted to the first entry, and not turned into a handler at run time.",
        "",
        "> **Every handler is inert.** Each returns a fixed dict and does nothing else: no file "
        "write, no network call, no subprocess, no shell, no mail, and no change to this project. "
        "The `handler_result` in the log is produced by Python; the model's response has no field "
        "that could carry one.",
        "",
    ]
    return lines


def _policy_lines() -> list[str]:
    """The frozen human-review policy, stated before any result is shown."""
    return [
        "### Frozen human-review policy",
        "",
        f"A handler is called only when the route's `Choice` confidence is at least "
        f"**{ROUTING_CONFIDENCE_FLOOR}** *and* `needs_human_review` is below "
        f"**{ROUTING_HUMAN_REVIEW_THRESHOLD}**. Otherwise the case reports "
        f"`{OUTCOME_HUMAN_REVIEW}`: no handler runs, and nothing is substituted for it.",
        "",
        "- **An unreadable input suppresses.** A missing, non-numeric, or absent confidence or "
        "review signal is not treated as a pass. The policy was not consulted successfully, so the "
        "case does not proceed.",
        "- **The policy can only withhold.** It has no branch that starts an action the model did "
        "not select, and no branch that picks a different function.",
        "",
        f"> **{ROUTING_CONFIDENCE_FLOOR} and {ROUTING_HUMAN_REVIEW_THRESHOLD} are demonstration "
        "parameters.** They are uncalibrated and not claimed to be optimal. The docs say thresholds "
        "must be tuned per domain and give different values for the same example on different "
        "pages; nothing measured here says these two are right, they were fixed before the run, "
        "and a different pair is a different experiment.",
        "",
    ]


def _expected_lines() -> list[str]:
    """The labels frozen with the states, before any result is shown."""
    lines = [
        "### Expected routes (frozen with the states)",
        "",
        "| case | expected function | expected argument | expected to need review |",
        "|---|---|---|---|",
    ]
    for case_id, function, argument, expects in ROUTING_EXPECTED:
        lines.append(
            f"| `{case_id}` | `{function}` | `{argument}` | {'yes' if expects else 'no'} |"
        )
    lines += [
        "",
        "These four rows were written with the states, before any request was sent, and they live "
        "only in the local design notes: they are not in the payload, and nothing in the routing "
        "path reads them before a decision is made. They are **the scenario's intention**, not an "
        "independent truth about what the right route is.",
        "",
    ]
    return lines


def _case_table(analysis: Mapping[str, Any]) -> list[str]:
    """One row per case: what was expected, what came back, and what Python did about it."""
    lines = [
        "### Routes",
        "",
        "| case | expected function | returned function | match | confidence | top-2 margin | "
        "needs review | outcome |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for case in analysis["cases"]:
        if not case["available"]:
            lines.append(
                f"| `{case['case_id']}` | "
                f"{'`' + case['expected_function'] + '`' if case['expected_function'] else '—'} | "
                f"**not routed** | — | — | — | — | "
                f"`{OUTCOME_ROUTE_UNAVAILABLE}` |"
            )
            continue
        outcome = (
            f"`{OUTCOME_EXECUTED}`" if case["handler_called"] else f"`{case['outcome']}`"
        )
        lines.append(
            f"| `{case['case_id']}` | `{case['expected_function']}` | "
            f"`{case['selected_function']}` | {_bool(case['matches_expected_function'])} | "
            f"{_value(case['confidence'])} | {_value(case['margin'])} | "
            f"{_value(case['needs_human_review'])} | {outcome} |"
        )
    lines += [
        "",
        "| case | expected argument | returned argument | match |",
        "|---|---|---|---|",
    ]
    for case in analysis["cases"]:
        if not case["available"]:
            lines.append(f"| `{case['case_id']}` | — | — | — |")
            continue
        name, value = next(iter(case["selected_arguments"].items()))
        lines.append(
            f"| `{case['case_id']}` | `{case['expected_argument']}` | `{name}={value}` | "
            f"{_bool(case['matches_expected_argument'])} |"
        )
    lines.append("")
    for case in analysis["cases"]:
        if not case["available"]:
            lines += [
                f"- `{case['case_id']}` — **no handler called.** "
                f"{case['unavailable_reason']}. Nothing was substituted: no fallback function, no "
                "argument defaulted or dropped, and no handler built at run time.",
            ]
        elif case["execution_suppressed"]:
            lines += [
                f"- `{case['case_id']}` — **no handler called.** {case['suppression_reason']}. The "
                f"frozen policy withheld execution; the route itself was `{case['selected_function']}`.",
            ]
        else:
            _name, _value_ = next(iter(case["selected_arguments"].items()))
            lines += [
                f"- `{case['case_id']}` — `{case['selected_function']}` called with "
                f"`{_name}={_value_}` → `{case['handler_result']}`.",
            ]
    lines.append("")
    return lines


def _count_lines(analysis: Mapping[str, Any]) -> list[str]:
    """The counts, and the refusal to turn them into a rate."""
    return [
        "### Counts",
        "",
        f"- **Functions matched:** {analysis['matched_count']} of {analysis['calls']} cases "
        f"({analysis['resolved_count']} resolved, {analysis['unavailable_count']} unavailable).",
        f"- **Arguments matched:** {analysis['argument_matched_count']} of "
        f"{analysis['resolved_count']} resolved cases.",
        f"- **Handlers executed:** {analysis['executed_count']} of {analysis['calls']} cases.",
        f"- **Suppressed for human review:** {analysis['suppressed_count']} of {analysis['calls']} "
        f"cases. The {analysis['suppression_expected_count']} case(s) written to need review were "
        f"among them {analysis['suppression_expected_hit']} time(s).",
        "",
        "> **These are counts on four synthetic cases, not an accuracy.** A rate over four "
        "hand-written cases would carry a precision this design does not have. The expected labels "
        "are the scenario's intention, written alongside the states, so they are not an independent "
        "truth, and nothing here estimates how the model would route a request it has not seen.",
        "",
    ]


def _cases(names: Sequence[str]) -> str:
    """Case ids for a sentence, or a word for the empty list. Never an empty gap in the prose."""
    return ", ".join(f"`{name}`" for name in names) if names else "none"


def _gate_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Both gates, evaluated separately, because the stored reason names only the first failure."""
    lines = [
        "### Gate decomposition",
        "",
        "The policy applies the two gates in order and records the reason it stopped at, so a "
        "stored `suppression_reason` names a single condition and reads as the only obstacle. Both "
        "gates are re-evaluated here independently, from the numbers in the answers, because the "
        "outcomes differ: a route withheld by the confidence floor alone would run if the floor "
        "moved, and one that also fails the review gate would not.",
        "",
        "| case | confidence | ≥ floor | needs review | < threshold | execution allowed |",
        "|---|---|---|---|---|---|",
    ]
    for case in analysis["cases"]:
        if not case["available"]:
            lines.append(
                f"| `{case['case_id']}` | — | not evaluated | — | not evaluated | not evaluated |"
            )
            continue
        lines.append(
            f"| `{case['case_id']}` | {_value(case['confidence'])} | "
            f"{_bool(case['confidence_gate_pass'])} | {_value(case['needs_human_review'])} | "
            f"{_bool(case['review_gate_pass'])} | {_bool(case['execution_allowed'])} |"
        )
    lines += [
        "",
        f"- Withheld by both gates: {analysis['withheld_by_both_gates_count']} of "
        f"{analysis['suppressed_count']} suppressed case(s).",
        f"- Withheld by the review gate alone, the confidence floor having passed: "
        f"{analysis['withheld_by_review_alone_count']}.",
        f"- Withheld by the confidence floor alone, the review gate having passed: "
        f"{analysis['withheld_by_confidence_alone_count']}.",
    ]
    if analysis["suppressed_count"] and not (
        analysis["withheld_by_review_alone_count"] or analysis["withheld_by_confidence_alone_count"]
    ):
        lines += [
            "",
            "Every suppressed case failed **both** gates. In these records, then, the withholding "
            "does not depend on the confidence floor: removing it would not have allowed any of "
            "them through, because the review signal alone withholds all of them. That is a "
            "description of these four answers and not an argument for a different floor — both "
            "numbers were fixed before the run, the policy is stated above, and neither is edited "
            "afterwards.",
        ]
    lines.append("")
    return lines


def _suppression_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What the design expected to be withheld, against what was withheld."""
    lines = [
        "### Expected suppression versus observed",
        "",
        "| case | written to need review | suppressed | agreement |",
        "|---|---|---|---|",
    ]
    for case in analysis["cases"]:
        expects = case["expects_suppression"]
        actual = case["execution_suppressed"]
        if expects is None:
            agrees = "not recorded"
        else:
            agrees = "yes" if bool(expects) == bool(actual) else "**no**"
        lines.append(f"| `{case['case_id']}` | {_bool(expects)} | {_bool(actual)} | {agrees} |")
    lines += [
        "",
        f"- Expectations recorded: {analysis['expectation_recorded_count']} of "
        f"{analysis['calls']} case(s).",
        f"- Suppressed although the design did not expect it: "
        f"{analysis['unexpected_suppression_count']} "
        f"({_cases(analysis['unexpected_suppression_cases'])}).",
        f"- Expected to be suppressed but allowed to run: "
        f"{analysis['unrealized_suppression_count']} "
        f"({_cases(analysis['unrealized_suppression_cases'])}).",
        "",
    ]
    if analysis["unexpected_suppression_count"] or analysis["unrealized_suppression_count"]:
        lines += [
            f"> **`{ROUTING_SUPPRESSION_EXPECTATION_MISSED}`** — the pre-registered expectation and "
            "the model's answers disagree about at least one scenario. That disagreement is the "
            "finding. It is **not** repaired here: the states, the criteria, and both thresholds "
            "are the ones fixed before the run, and adjusting any of them after seeing these "
            "answers would replace a measurement with a fit. A case the design wrote as routine "
            "coming back with a high `needs_human_review` is evidence about the design's assumption, "
            "not a defect to be tuned away.",
            "",
        ]
    elif analysis["expectation_recorded_count"]:
        lines += [
            f"> **`{ROUTING_SUPPRESSION_EXPECTATION_MET}`** — every recorded expectation matched "
            "what the policy did.",
            "",
        ]
    return lines


def _execution_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What ran, what did not, and which part of the chain a real run actually reached."""
    lines = [
        "### Handler execution",
        "",
        f"- `handler_called`: true in {analysis['executed_count']} of {analysis['calls']} case(s). "
        f"`execution_suppressed`: true in {analysis['suppressed_count']} of {analysis['calls']}.",
        "- `handler_result`: `null` where no handler ran. That is the absence of a result, not an "
        "empty one, and it is never filled in from the route the case would have taken.",
        "",
    ]
    if analysis["executed_count"] == 0 and analysis["resolved_count"]:
        lines += [
            f"> **`{ACTUAL_HANDLER_EXECUTION_UNTESTED}`** — every route that resolved was withheld, "
            "so no handler was called under a live answer and no `handler_result` was measured. "
            "This run establishes that the model returned a function name from the frozen registry "
            "and an argument label from that function's frozen set, and that the Python policy "
            "withheld execution exactly as written. It does **not** establish that an allowed route "
            "reaches `HANDLERS[name](argument)` and comes back with the inert result: that branch "
            "was never entered. The offline tests exercise it, but a test of a branch and a live run "
            "through it are different evidence. **This is not a full execution-chain result.**",
            "",
        ]
    elif analysis["executed_count"]:
        ran = [case["case_id"] for case in analysis["cases"] if case["handler_called"]]
        lines += [
            f"> **`{ACTUAL_HANDLER_EXECUTION_REALIZED}`** — the policy allowed {_cases(ran)}, and "
            "the handler named by the returned label ran with the returned argument. The result is "
            "inert by construction and the record says so.",
            "",
        ]
    lines += [
        "Nothing in this path can act on a route the model did not select: the registry is a dict "
        "frozen before the run, the argument sets are frozen with it, and the policy has no branch "
        "that substitutes one label for another.",
        "",
    ]
    return lines


def _classification_lines(analysis: Mapping[str, Any]) -> list[str]:
    """The measurement classifications, derived rather than asserted.

    Each is a statement about these records only. The positive form of the first two is the one
    this project's vocabulary defines; `..._NOT_REALIZED` is written out as its complement so a
    partial result cannot be reported with a word that means a full one.
    """
    calls = analysis["calls"]
    lines = ["### Classifications", ""]
    if not calls:
        return lines + ["No records, so no classification is stated.", ""]

    if analysis["resolved_count"] == calls and analysis["matched_count"] == calls:
        lines.append(
            f"- **FUNCTION_TARGET_REALIZED** — all {calls} case(s) returned the pre-frozen "
            "expected function."
        )
    else:
        lines.append(
            f"- **FUNCTION_TARGET_NOT_REALIZED** — {analysis['matched_count']} of {calls} case(s) "
            "returned the expected function "
            f"({analysis['unavailable_count']} unresolved)."
        )

    if analysis["resolved_count"] and analysis["argument_matched_count"] == analysis["resolved_count"]:
        lines.append(
            f"- **ARGUMENT_TARGET_REALIZED** — all {analysis['resolved_count']} resolved case(s) "
            "returned the argument frozen with their state."
        )
    else:
        lines.append(
            f"- **ARGUMENT_TARGET_NOT_REALIZED** — {analysis['argument_matched_count']} of "
            f"{analysis['resolved_count']} resolved case(s) returned the expected argument."
        )

    if analysis["expectation_recorded_count"]:
        if analysis["unexpected_suppression_count"] or analysis["unrealized_suppression_count"]:
            lines.append(
                f"- **{ROUTING_SUPPRESSION_EXPECTATION_MISSED}** — "
                f"{analysis['unexpected_suppression_count']} unexpected suppression(s), "
                f"{analysis['unrealized_suppression_count']} unrealized expectation(s)."
            )
        else:
            lines.append(f"- **{ROUTING_SUPPRESSION_EXPECTATION_MET}** — every expectation matched.")

    if analysis["executed_count"]:
        lines.append(
            f"- **{ACTUAL_HANDLER_EXECUTION_REALIZED}** — a handler ran in "
            f"{analysis['executed_count']} case(s) under live answers."
        )
    else:
        lines.append(
            f"- **{ACTUAL_HANDLER_EXECUTION_UNTESTED}** — no handler ran; the execution branch was "
            "not entered by this run."
        )
    lines.append("")
    return lines


def _distribution_lines(analysis: Mapping[str, Any]) -> list[str]:
    """The full routing distributions, kept whole, because the label alone hides the margin."""
    lines = [
        "### Routing distributions",
        "",
        "| case | full distribution over the registry |",
        "|---|---|",
    ]
    for case in analysis["cases"]:
        if not case["available"]:
            lines.append(f"| `{case['case_id']}` | not routed |")
            continue
        rendered = ", ".join(
            f"`{name}` {_value(value)}" for name, value in sorted(case["probabilities"].items())
        )
        lines.append(f"| `{case['case_id']}` | {rendered or 'not recorded'} |")
    lines += [
        "",
        "The full distribution is kept rather than the winning label alone, because a label that "
        "matches an expectation says nothing about how decided that answer was. A route taken with "
        "a margin of 0.01 and one taken with a margin of 0.9 are the same entry in the counts table "
        "above.",
        "",
        "> **A stable label is not a stable distribution.** `13b_ambiguous_repeatability` sent one "
        "unchanged payload five times and observed the same labels come back on differently-shaped "
        "probabilities, so a repeated label would not imply that the numbers in this table repeat. "
        "Four cases, one observation each: nothing here is a repeatability claim.",
        "",
    ]
    return lines


def _confidence_lines(analysis: Mapping[str, Any]) -> list[str]:
    """Confidence described and explicitly not confused with correctness."""
    pairs = [
        (case["case_id"], case["confidence"], case["matches_expected_function"])
        for case in analysis["cases"]
        if case["available"]
    ]
    if not pairs:
        return []
    return [
        "### Confidence is not correctness",
        "",
        "- "
        + "; ".join(
            f"`{case_id}` routed with confidence {_value(confidence)}, matched expected: "
            f"{_bool(matches)}"
            for case_id, confidence, matches in pairs
        )
        + ".",
        "",
        "The two are reported side by side and never combined. A high confidence is not a guarantee "
        "of a correct route and a low one is not evidence of a wrong one; confidence is not a "
        "graded correctness and there is no threshold at which it becomes one. It gates execution "
        "above and nothing else, and it never edits an expected label.",
        "",
    ]


def _speculation_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What the speculative argument questions cost and what was consumed."""
    lines = [
        "### Speculative argument questions",
        "",
        "Every request carries all four argument questions, because the function is not known when "
        "the request is written. Python consumes exactly one of them — the one belonging to the "
        "selected function — and the rest are recorded as unused.",
        "",
    ]
    for case in analysis["cases"]:
        if not case["available"]:
            lines.append(
                f"- `{case['case_id']}`: {len(case['argument_questions_asked'])} argument "
                "question(s) asked, none consumed, all unused (no route)."
            )
            continue
        lines.append(
            f"- `{case['case_id']}`: {len(case['argument_questions_asked'])} asked, "
            f"`{case['argument_answers_consumed'][0]}` consumed, "
            f"{len(case['argument_answers_unused'])} unused."
        )
    lines += [
        "",
        "> **The cost of the unused answers is not decomposed.** The API reports usage once per "
        "request, so the tokens attributable to one question inside a request are not separable "
        "from the rest. No per-question figure is estimated here, and the unused answers' cost is "
        "not stated — it is included in the request totals and is not attributed beyond that.",
        "",
        "This is `05_speculative_fanout`'s pattern: ask every branch's follow-up in one request "
        "rather than spending a second round trip discovering which branch was taken. Whether that "
        "trade is worth it is a question `05` measured for its own payloads, not one this "
        "experiment re-derives.",
        "",
    ]
    return lines


def _usage_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What the four calls used. Recorded, not compared between cases."""
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
        "- The four requests carry identical questions, so any token difference between them comes "
        "from the state. **No attempt is made to decompose it**, and no per-question or per-answer "
        "figure is estimated.",
        "",
    ]


def _latency_lines(analysis: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Latency, described and not compared. The declared order is stated because it confounds."""
    lines = ["### Latency — descriptive only", ""]
    for record in records:
        latency = record.get("latency_ms")
        lines.append(
            f"- `{record.get('case_id')}`: "
            + (f"**{format_ms(latency)} ms**" if latency is not None else "not recorded")
            + (
                ", the first request of the client session"
                if record.get("is_first_request_in_client_session")
                else ""
            )
            + "."
        )
    lines += [
        "",
        "**The order is fixed, and it confounds.** The four cases run in the declared order, one "
        "each, so case identity and request position move together: the first case opens the client "
        "session and can carry connection setup its siblings do not. With four calls and one "
        "observation each, nothing here says which route resolved faster, and no such comparison is "
        "made — a per-route latency claim would need an order-balanced design this experiment does "
        "not have.",
    ]
    first = analysis.get("first_request_latency") or {"available": False}
    if first.get("available") and first.get("is_outlier"):
        lines += [
            "",
            f"**`{ROUTING_FIRST_REQUEST_LATENCY_OUTLIER_OBSERVED}`** — the call that opened the "
            f"session is the longest of the four, at **{_value(first['ratio'])}x** the longest of "
            "the rest. That call is also the first case in the declared order, so the two are "
            "confounded here and cannot be separated by these records. This describes this "
            "session's traffic, not a property of any route.",
        ]
    lines.append("")
    return lines


def _limits_lines(analysis: Mapping[str, Any]) -> list[str]:
    """What four synthetic routing cases do not establish."""
    return [
        "### What this does not show",
        "",
        f"- **Sample size.** {analysis['calls']} synthetic case(s), one observation each, one "
        "session. Nothing here generalises to another registry, another argument set, another "
        "domain, or a request the states did not anticipate.",
        "- **The expected routes are the scenario's intention.** They were written with the states, "
        "not derived from an independent authority, and no case has a ground-truth label. A "
        "disagreement is a disagreement with the design, not evidence that the model is wrong.",
        "- **A routing result is not a correctness result.** Nothing downstream in this repository "
        "acts on a route: no handler changes anything, so a wrong route here costs nothing and no "
        "consequence was measured.",
        "- **The registry is small and its labels are distinct.** Four functions with clearly "
        "separated descriptions are the easy end of routing. Nothing here says anything about a "
        "registry with dozens of overlapping entries, where the names themselves carry most of the "
        "signal.",
        "- **One state per route.** Each function is the expected answer for exactly one case, so "
        "the counts cannot separate a route the model reads from a route the state happens to "
        "resemble.",
        "- **Thresholds are demonstration parameters.** The confidence floor and the review "
        "threshold were fixed for these four calls and are uncalibrated; a different pair would "
        "move cases between `executed` and `human_review` without any answer changing.",
        "",
    ]


def build_routing_block(records: Sequence[Mapping[str, Any]]) -> list[str]:
    """Render `12_function_routing` from its canonical records.

    Every decision is recomputed from the records on the way out, so a run whose answers differ
    renders differently — including one that routes nowhere, or routes somewhere the states did not
    expect.
    """
    if not records:
        return []
    analysis = analyze_routing(records)
    lines = [f"## `{ROUTING}`", ""]
    lines += _design_lines(analysis)
    lines += _registry_lines()
    lines += _policy_lines()
    lines += _expected_lines()
    lines += _case_table(analysis)
    lines += _count_lines(analysis)
    lines += _gate_lines(analysis)
    lines += _suppression_lines(analysis)
    lines += _execution_lines(analysis)
    lines += _classification_lines(analysis)
    lines += _distribution_lines(analysis)
    lines += _confidence_lines(analysis)
    lines += _speculation_lines(analysis)
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
