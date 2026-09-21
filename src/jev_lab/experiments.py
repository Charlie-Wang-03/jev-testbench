"""The experiment registry.

Each experiment is a small, fixed set of `Case`s: one synthetic state plus a typed question set.
A case is one API call unless it explicitly asks for more. Nothing here loops without a bound,
and every experiment declares its cases up front so the request budget is knowable before a run.

The design rule the docs keep repeating is applied throughout: code does the arithmetic and the
branching, Jev does the semantic judgment.

All state is synthetic test data. Do not put real personal or proprietary content here.
"""

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from typesafe_sdk import (
    Choice,
    JSONContent,
    Noul,
    NoulCriteria,
    Question,
    Score,
    SystemOneResponse,
    TypeSafeAuthenticationError,
    TypeSafeClient,
)

from .client import ATTEMPT_COUNT_SOURCE, TransportProbe
from .composite import (
    COMPOSITE_ADVERSE,
    COMPOSITE_BENEFICIAL,
    COMPOSITE_DIMENSIONS,
    COMPOSITE_EXPECTED_ORDER,
    COMPOSITE_SCALE_LEVELS,
    COMPOSITE_TOP_LEVEL,
    COMPOSITE_WEIGHTS,
    composite_digest,
)
from .recorder import CallRecord, UsageRecorder
from .routing import (
    ROUTING_ARGUMENT_QUESTION,
    ROUTING_ARGUMENTS,
    ROUTING_CASE_ORDER,
    ROUTING_EXPECTED,
    ROUTING_FUNCTION_QUESTION,
    ROUTING_FUNCTIONS,
    ROUTING_REVIEW_QUESTION,
    routing_digest,
)

DEFAULT_MODEL = "jev-latest"

# Hard ceiling for a single `run` invocation. `run-all` must pass an explicit larger value.
DEFAULT_MAX_REQUESTS = 8

# `13_repeatability` sends one identical request five times. Five is the ceiling: it is the smallest
# count that shows a spread rather than a single pair, and every extra call buys less than the last.
REPEAT_CALLS = 5
MAX_REPEATS = 5

CORE = "core"
EXTENDED = "extended"


@dataclass(frozen=True)
class Case:
    """One state and the questions asked about it."""

    case_id: str
    state: JSONContent
    questions: Mapping[str, Question]
    notes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Experiment:
    """A named, bounded set of cases plus optional local interpretation of the answers."""

    name: str
    tier: str
    intent: str
    build_cases: Callable[[], list[Case]]
    # Optional LOCAL interpretation of an answer, called as ``digest(case, response)`` after a
    # successful call. Whatever it returns is merged into ``record.notes["derived"]``, so a
    # code-side decision such as a confidence gate is preserved in the canonical log. It must not
    # make any further API call. Returning ``{}`` means "nothing derived".
    digest: Callable[[Case, SystemOneResponse], dict[str, Any]] | None = None
    # Optional: the cases that should run *after* this one, chosen from its answer. This is what
    # lets an experiment model a real control flow -- the next payload depends on what came back,
    # so it cannot be written down in advance. Called as ``follow_up(case, response)`` only after a
    # successful call, and like ``digest`` it must be pure: it returns cases, it never calls the
    # API. Returning ``[]`` means "this branch is finished".
    #
    # The declared case list stays the *skeleton*: `run_experiment` runs it in order and splices
    # each follow-up in immediately after the case that produced it. When this is set, the case
    # list is no longer a full budget -- see ``call_ceiling``.
    follow_up: Callable[[Case, SystemOneResponse], list[Case]] | None = None
    # The most API calls this experiment can make. Required when ``follow_up`` is set, because the
    # declared case list then under-counts: a case that declares a follow-up is two calls, not one.
    # It is a ceiling, not a promise -- a failed stage 1 produces fewer calls, never more -- which
    # is exactly what a budget check needs. Left as ``None`` when the case list is exhaustive.
    call_ceiling: int | None = None

    def cases(self) -> list[Case]:
        """The cases for this experiment, rebuilt fresh so runs cannot share mutable state."""
        return self.build_cases()


def experiment_call_ceiling(experiment: Experiment) -> int:
    """The most API calls one experiment can make.

    For a fixed experiment that is just its case count. For one with a control flow it is the
    declared ``call_ceiling``, because its case list is a skeleton rather than the whole budget.
    """
    if experiment.call_ceiling is not None:
        return experiment.call_ceiling
    return len(experiment.cases())


# --------------------------------------------------------------------------------------
# Shared interpretation helpers: these run locally, on values the API returned.
# --------------------------------------------------------------------------------------


def answer_digest(response: SystemOneResponse) -> dict[str, Any]:
    """Summarize every answer compactly: the chosen value plus its distribution."""
    digest: dict[str, Any] = {}
    for name, answer in response.answers.items():
        kind = getattr(answer, "type", "unknown")
        entry: dict[str, Any] = {"type": kind}
        if kind == "choice":
            entry["choice"] = answer.choice
            entry["confidence"] = answer.confidence
            entry["probabilities"] = dict(answer.probabilities)
        elif kind == "score":
            entry["score"] = answer.score
            entry["confidence"] = answer.confidence
            entry["probabilities"] = {str(level): value for level, value in answer.probabilities.items()}
        elif kind == "noul":
            entry["noul"] = answer.noul
        digest[name] = entry
    return digest


def top_label(response: SystemOneResponse, name: str) -> str | None:
    """The selected label of a Choice answer, or ``None`` if that answer is another kind."""
    answer = response.answers.get(name)
    return getattr(answer, "choice", None)


def score_of(response: SystemOneResponse, name: str) -> float | None:
    """The expected score of a Score answer, or ``None`` for another answer kind."""
    answer = response.answers.get(name)
    return getattr(answer, "score", None)


def noul_of(response: SystemOneResponse, name: str) -> float | None:
    """The yes-probability of a Noul answer, or ``None`` for another answer kind."""
    answer = response.answers.get(name)
    return getattr(answer, "noul", None)


def normalized_score(response: SystemOneResponse, name: str, levels: int) -> float | None:
    """Put a Score on 0..1 by dividing by its top level number, as the docs recommend."""
    raw = score_of(response, name)
    return None if raw is None or levels < 2 else round(raw / (levels - 1), 4)


def confidence_of(response: SystemOneResponse, name: str) -> float | None:
    """The confidence of a Choice/Score answer; ``None`` for Noul, which has none."""
    return getattr(response.answers.get(name), "confidence", None)


# --------------------------------------------------------------------------------------
# Synthetic state fixtures
# --------------------------------------------------------------------------------------

TICKET_TEXT = (
    "I placed order #98423 last Thursday and was charged twice. "
    "I also can't log in after the site update. Adding Apple Pay would be really helpful. "
    "This is getting frustrating."
)

SHORT_STATE = "The export button crashes the settings page in Safari. It works in Chrome."

# Core evidence held fixed across every length tier in `10_state_length`.
FIXED_EVIDENCE = (
    "Bug report: exporting a report to PDF fails with a spinner that never finishes. "
    "The same export works for CSV. It started after the 4.2 release."
)

FILLER_PARAGRAPHS = (
    "The office coffee machine was serviced on Tuesday and the filter was replaced. ",
    "Team offsite planning continues; the venue shortlist now has four candidates. ",
    "The quarterly stationery order arrived, including 12 boxes of A4 paper. ",
    "A reminder that the parking permit renewals are due at the end of the month. ",
    "The internal wiki was reorganised and some page links may have moved. ",
)


def _pad(paragraphs: int) -> str:
    """Deterministic irrelevant filler, used only to grow the state."""
    return " ".join(FILLER_PARAGRAPHS[index % len(FILLER_PARAGRAPHS)] for index in range(paragraphs))


# --------------------------------------------------------------------------------------
# Experiment definitions
# --------------------------------------------------------------------------------------


def _00_model_info() -> list[Case]:
    """Two tiny calls so we can see which model each alias actually resolves to."""
    return [
        Case(
            case_id="resolve_jev_latest",
            state="Ping.",
            questions={"ok": Noul(instructions="Is the word `Ping` present in the state?")},
            notes={"alias": "jev-latest", "endpoint": "/v1/systemone"},
        ),
        Case(
            case_id="resolve_jev_preview",
            state="Ping.",
            questions={"ok": Noul(instructions="Is the word `Ping` present in the state?")},
            notes={"alias": "jev-preview", "endpoint": "/v1/systemone"},
        ),
    ]


# `01_primitives` and `13b_ambiguous_repeatability` send the *same* payload, so it is defined once
# here and referenced by both. Two things follow from sharing the objects rather than copying them:
# the two experiments cannot drift apart through an edit to one of them, and `13b` measures
# repeatability on a request that a real measurement has already been taken from. `01`'s own
# behaviour is unchanged -- it reads the same state and the same question objects it always did.
#
# The order of the dict is the order the questions go on the wire, so it is part of the payload.
PRIMITIVES_STATE = TICKET_TEXT

PRIMITIVES_QUESTIONS: dict[str, Question] = {
    "department": Choice(
        instructions="Which team should handle this ticket?",
        criteria={
            "billing": "Charges, invoices, refunds, subscriptions",
            "account": "Login, permissions, profile, security",
            "feature_request": "A request for functionality that does not exist yet",
            "other": "Anything that does not fit the options above",
        },
    ),
    "severity": Score(
        instructions="How severe is the problem the customer reports?",
        criteria=[
            "Cosmetic; the product still works",
            "A feature is broken or degraded but a workaround exists",
            "The customer cannot proceed at all; no workaround exists",
        ],
    ),
    "repeat_contact": Noul(
        instructions="Has the customer contacted support about this before?",
        criteria=NoulCriteria(
            true="Says or implies they have raised this already",
            false="No sign of any previous contact",
        ),
    ),
}


def _01_primitives() -> list[Case]:
    """One request carrying all three primitives against one shared state (the smoke test)."""
    return [
        Case(
            case_id="ticket_all_primitives",
            state=PRIMITIVES_STATE,
            questions=PRIMITIVES_QUESTIONS,
        )
    ]


# `02_structured_addressing` compares the two ways of pointing a question at the relevant part of
# a state: a formal field path over structured state, versus a natural-language description of the
# same place in prose state. Both arms carry identical facts and identical question sets; only the
# addressing clause of each instruction differs.
#
# This is deliberately NOT a clean "JSON versus prose" causal test. Three things move together here:
# the state representation, whether the question can name a field path at all, and the payload
# length. Token, latency, and cost differences between the arms are confounded by representation
# length and must be read as observations, not attributed to representation alone. The recorder
# stores `state_chars` / `state_utf8_bytes` per case so the length gap stays measurable.

ADDRESSING_NOUL_CRITERIA = NoulCriteria(
    true="They say they were charged more than once or ask for money back",
    false="They ask for something else",
)

ADDRESSING_CHOICE_CRITERIA: dict[str, str] = {
    "billing": "Charges, invoices, refunds, subscriptions",
    "account": "Login, permissions, profile, security",
    "other": "Anything that does not fit the options above",
}


def _addressing_questions(subject: str) -> dict[str, Question]:
    """The same Noul plus Choice, pointing at the state through ``subject``.

    ``subject`` is the only thing that varies between the arms: a backticked field path in the
    structured arm, a natural-language description in the prose arm. Criteria are identical.
    """
    return {
        "asks_for_refund": Noul(
            instructions=f"Is the customer asking for a refund of the amount in {subject}?",
            criteria=ADDRESSING_NOUL_CRITERIA,
        ),
        "department": Choice(
            instructions=f"Which team should handle the issue described in {subject}?",
            criteria=dict(ADDRESSING_CHOICE_CRITERIA),
        ),
    }


# The same four facts, stated once as structured data and once as prose.
STRUCTURED_TICKET: dict[str, Any] = {
    "ticket": {
        "id": "T-4471",
        "messages": [{"author": "customer", "text": "I was charged twice for order #98423."}],
    },
    "policy": {"refund_window_days": 30, "duplicate_charge": "Refund the duplicate in full"},
}

PROSE_TICKET = (
    'Ticket T-4471. The customer wrote: "I was charged twice for order #98423." '
    "Policy: the refund window is 30 days; for a duplicate charge, refund the duplicate in full."
)


def _02_structured_addressing() -> list[Case]:
    """Structured state with field-path addressing versus prose state with described addressing."""
    return [
        Case(
            case_id="structured_addressing",
            state=STRUCTURED_TICKET,
            questions=_addressing_questions("`ticket.messages[0].text`"),
            notes={"state_form": "json", "addressing": "backticked field path"},
        ),
        Case(
            case_id="prose_addressing",
            state=PROSE_TICKET,
            questions=_addressing_questions("the message the customer wrote"),
            notes={
                "state_form": "prose",
                "addressing": "natural-language description",
                "content": "same four facts as structured_addressing",
            },
        ),
    ]


ATOMIC_QUESTIONS: dict[str, Question] = {
    "charged_twice": Noul(instructions="Does the customer say they were charged twice?"),
    "cannot_log_in": Noul(instructions="Does the customer say they cannot log in?"),
    "wants_apple_pay": Noul(instructions="Does the customer ask for Apple Pay?"),
    "is_frustrated": Noul(instructions="Does the customer express frustration?"),
    "mentions_order_id": Noul(instructions="Does the customer give an order number?"),
}


# `03_parallel_questions` compares one batched request against the same questions asked one at a
# time. Its first version ran the batched arm first and the separate arms after it, which left arm
# identity perfectly confounded with request position. Two order-balanced cycles therefore run:
# batch-then-separate, then separate-then-batch. That is the step which makes an arm difference
# distinguishable from a warm connection difference.
#
# The first request of a session is *often* the slowest, but not reliably, so nothing depends on it.
# In `results/usage.jsonl` it holds for `02`, `04`, `07` and for `03`'s first cycle, and it fails for
# `03`'s second cycle (565 ms first, 631 ms later) and for `01_primitives` (679 ms). Treat a
# first-request effect as a hypothesis the position fields let you check, never as a rule.
#
# Token and cost comparisons stay tight: identical state, identical question definitions, one
# request carrying all five questions against five requests carrying one each. Latency is still
# only observational -- two cycles balance the order but are nowhere near enough for a speedup
# claim, so this experiment never makes one.
BATCH_ARM = "batched"
SEPARATE_ARM = "separate"
PARALLEL_CYCLES = 2


def _parallel_cases(shared_state: str, cycle: int, arm_first: str) -> list[Case]:
    """One order-balanced cycle: the named arm first, the other arm after it.

    Question order inside the separate arm is held constant across cycles on purpose, so it
    cancels out instead of varying alongside the arm.
    """
    if arm_first == BATCH_ARM:
        batched_index, separate_index = 1, 2
    else:
        batched_index, separate_index = 2, 1
    batched = Case(
        case_id=f"cycle{cycle}_{batched_index}_batched_single_request",
        state=shared_state,
        questions=dict(ATOMIC_QUESTIONS),
        notes={
            "arm": BATCH_ARM,
            "cycle": cycle,
            "position_in_cycle": batched_index,
            "questions": len(ATOMIC_QUESTIONS),
        },
    )
    separate = [
        Case(
            case_id=f"cycle{cycle}_{separate_index}_separate_{name}",
            state=shared_state,
            questions={name: question},
            notes={
                "arm": SEPARATE_ARM,
                "cycle": cycle,
                "position_in_cycle": separate_index + offset,
                "sibling_of": batched.case_id,
            },
        )
        for offset, (name, question) in enumerate(ATOMIC_QUESTIONS.items())
    ]
    return [batched, *separate] if arm_first == BATCH_ARM else [*separate, batched]


def _03_parallel_questions() -> list[Case]:
    """The batching claim: one request with five questions, versus five separate requests.

    The docs claim batching is 12.2x cheaper and 10.0x faster on a 13-question GDPR workload
    (cookbook `parallel_questions`). That is a vendor claim about a different workload; this
    experiment measures it here or not at all. Questions are identical in both arms.

    Twelve logical calls: two cycles of (one batched + five separate).
    """
    shared_state = f"{TICKET_TEXT}\n\n{FIXED_EVIDENCE}"
    cases: list[Case] = []
    for cycle in range(1, PARALLEL_CYCLES + 1):
        # Cycle 1 leads with the batched arm; cycle 2 leads with the separate arms.
        cases.extend(_parallel_cases(shared_state, cycle, BATCH_ARM if cycle % 2 else SEPARATE_ARM))
    return cases


# `04_confidence` watches how confidence moves when the evidence is specific versus ambiguous, and
# routes on it in code. Both arms sit in the same scenario and share the same entities and nearly
# the same length, so the main thing that varies is how specific the evidence is. The Choice
# criteria deliberately avoid the state's own verbs so neither arm gets a lexical shortcut.

# Demonstration threshold, NOT a tuned, calibrated, or optimal value. The official docs use 0.6 on
# one pattern page and 0.5 on another for the same example, and say thresholds must be tuned per
# domain. This number exists to exercise the gate in code, nothing more.
CONFIDENCE_GATE_THRESHOLD = 0.60
GATE_ACCEPT = "accept"
GATE_ESCALATE = "escalate"
GATE_THRESHOLD_BASIS = "demo threshold; not calibrated, not tuned on any data, not claimed optimal"

CONFIDENCE_CHOICE_CRITERIA: dict[str, str] = {
    "release_transfer": "The requester wants a queued money movement to be released for processing",
    "read_balance": "The requester wants to know how much money an account currently holds",
    "other": "The request is about something other than releasing a queued movement or reading a balance",
}

CONFIDENCE_SCORE_CRITERIA: list[str] = [
    "The request does not say what should happen next",
    "The request hints at what should happen next but other readings stay open",
    "The request states exactly what should happen next",
]

CONFIDENCE_QUESTIONS: dict[str, Question] = {
    "intent": Choice(
        instructions="What action is the request asking for?",
        criteria=dict(CONFIDENCE_CHOICE_CRITERIA),
    ),
    "specificity": Score(
        instructions="How specific is the request about what should happen next?",
        criteria=list(CONFIDENCE_SCORE_CRITERIA),
    ),
}


def _confidence_gate(confidence: float | None) -> dict[str, Any]:
    """Route in code from the answer's own confidence. Runs locally; no extra API call."""
    if confidence is None:
        return {"decision": "not_applicable", "reason": "the answer carries no confidence"}
    return {
        "decision": GATE_ACCEPT if confidence >= CONFIDENCE_GATE_THRESHOLD else GATE_ESCALATE,
        "threshold": CONFIDENCE_GATE_THRESHOLD,
        "threshold_basis": GATE_THRESHOLD_BASIS,
    }


def _confidence_digest(case: Case, response: SystemOneResponse) -> dict[str, Any]:
    """Report correctness and confidence as separate facts, and gate on confidence alone.

    Confidence is not correctness. When a case declares an expected label this reports whether the
    answer matched it; when it does not, `matches_expected` stays ``None`` rather than being
    forced, so "confidently wrong" stays visible instead of being averaged away.
    """
    selected = top_label(response, "intent")
    expected = case.notes.get("expected")
    chosen_confidence = confidence_of(response, "intent")
    return {
        "intent": selected,
        "intent_confidence": chosen_confidence,
        "expected": expected,
        "matches_expected": None if expected is None else selected == expected,
        "specificity_score": score_of(response, "specificity"),
        "specificity_confidence": confidence_of(response, "specificity"),
        "specificity_note": "Score confidence is not correctness and is not comparable to Choice confidence",
        "gate": _confidence_gate(chosen_confidence),
    }


def _04_confidence() -> list[Case]:
    """Specific versus ambiguous evidence in one scenario, with a code-side confidence gate."""
    return [
        Case(
            case_id="specific_evidence",
            state=(
                "Account 4471 has a $250 transfer to account 8891 waiting for approval. "
                "Go ahead and approve it."
            ),
            questions={name: question for name, question in CONFIDENCE_QUESTIONS.items()},
            notes={"ambiguity": "clear", "expected": "release_transfer"},
        ),
        Case(
            case_id="ambiguous_evidence",
            state=(
                "Account 4471 has a $250 transfer to account 8891 sitting there. "
                "I'm not sure what still needs to happen with it."
            ),
            questions={name: question for name, question in CONFIDENCE_QUESTIONS.items()},
            notes={
                "ambiguity": "ambiguous",
                "expected_policy": "no single label is correct; the state does not commit to an action",
            },
        ),
    ]


# `05_speculative_fanout` -- one request carrying questions that may never be needed, against a
# real two-stage control flow that asks only for what the first answer chose.
#
# This is NOT `03_parallel_questions` again. `03` measures what happens when independent questions
# are batched; nothing in it branches, so every question it sends is one it needs. Here the two
# arms differ in *what is asked*, not only in how it is split: the fanout arm pays for a branch it
# will probably not take, and the staged arm pays a second round trip to avoid that. Which of
# those costs more is the measurement, and the design does not decide it in advance.
#
# The scenario is first-line support triage. One primary decision -- who has to act next -- picks
# which downstream question set is worth asking:
#
#   fanout  : primary + BOTH branch sets in one request, then only the chosen branch is consumed
#   staged  : primary alone, then the chosen branch's set, sent as a second request
#
# The branch is chosen in Python from the label the primary returned. Jev is never asked which
# branch it is in: that would be a second judgment on top of the first, and it would make the
# routing unauditable against a frozen map.
FANOUT_ARM = "fanout"
STAGED_ARM = "staged"
STAGE_1 = 1
STAGE_2 = 2

# Two states, chosen to sit on opposite sides of the primary decision. A carries nothing to act
# on; B carries everything and describes a change the customer says they did not authorise. The
# expected branch for each is frozen here, before any run, so the routing can be checked against
# it afterwards. It is local bookkeeping: nothing about it reaches the wire.
FANOUT_STATES: dict[str, str] = {
    "A": (
        "Ticket #77120. The customer writes: 'The dashboard export gives me a blank file instead "
        "of the numbers, and I need them for a board meeting tomorrow morning.' Nothing in the "
        "ticket names a plan, an account, a browser, or the steps that produce the blank file."
    ),
    "B": (
        "Ticket #77121. The customer writes: 'Someone changed the payout account on my storefront "
        "on Sunday and I never authorised it. This is the second time this month.' The ticket "
        "carries the account id, the storefront name, the date of the change, and the browser "
        "session that made it."
    ),
}

FANOUT_EXPECTED_BRANCH: dict[str, str] = {
    "A": "request_more_detail",
    "B": "escalate_to_specialist",
}

FANOUT_NEXT_ACTION = Choice(
    instructions="What is the next step this ticket needs?",
    criteria={
        "request_more_detail": (
            "The ticket cannot proceed until the customer supplies something it does not contain"
        ),
        "escalate_to_specialist": "The ticket has to go to a team beyond first-line support",
    },
)

# Asked whichever branch is taken. It is what makes the staged arm's second request non-empty on
# both branches, so the round-trip comparison is two against one rather than two against two.
FANOUT_FOLLOWUP_URGENCY = Score(
    instructions="How much time pressure does the next step carry?",
    criteria=[
        "No deadline is stated and nothing is getting worse",
        "A deadline is stated but it is not immediate",
        "A deadline is imminent, or harm is ongoing",
    ],
)

FANOUT_MISSING_DETAIL = Choice(
    instructions="What is the one thing the customer has to supply?",
    criteria={
        "account_or_plan_identifier": "An account, plan, order, or subscription identifier",
        "reproduction_context": "The environment, device, or steps that produce the problem",
        "nothing_specific": "No single item stands out as the blocker",
    },
)

FANOUT_DETAIL_IS_BLOCKING = Noul(
    instructions="Is the ticket unable to proceed at all until the customer replies?"
)

FANOUT_SPECIALIST_TEAM = Choice(
    instructions="Which team should the ticket go to?",
    criteria={
        "trust_and_safety": "Account takeover, fraud, or a change the customer did not authorise",
        "billing_operations": "Invoices, charges, refunds, or payouts",
        "platform_engineering": "A defect in the product itself",
    },
)

FANOUT_IS_UNAUTHORISED_CHANGE = Noul(
    instructions="Does the ticket describe a change to the account that the customer says they "
    "did not make?"
)

# The primary question, alone. A staged first stage sends this dict; the fanout arm sends the same
# objects as part of a larger dict, which is what makes the two primary questions one question
# rather than two that happen to read alike.
FANOUT_PRIMARY_QUESTIONS: dict[str, Question] = {"next_action": FANOUT_NEXT_ACTION}

FANOUT_COMMON_QUESTIONS: dict[str, Question] = {"followup_urgency": FANOUT_FOLLOWUP_URGENCY}

# Per branch, the questions that branch alone needs. The frozen map the routing is read against.
FANOUT_BRANCH_SPECIFIC: dict[str, dict[str, Question]] = {
    "request_more_detail": {
        "missing_detail": FANOUT_MISSING_DETAIL,
        "detail_is_blocking": FANOUT_DETAIL_IS_BLOCKING,
    },
    "escalate_to_specialist": {
        "specialist_team": FANOUT_SPECIALIST_TEAM,
        "is_unauthorised_change": FANOUT_IS_UNAUTHORISED_CHANGE,
    },
}

FANOUT_BRANCH_QUESTIONS: dict[str, dict[str, Question]] = {
    branch: {**FANOUT_COMMON_QUESTIONS, **specific}
    for branch, specific in FANOUT_BRANCH_SPECIFIC.items()
}

# What the fanout arm sends: the primary, the branch-independent question, and *both* branches'
# specific questions. Six questions, of which at most four can be consumed.
FANOUT_QUESTIONS: dict[str, Question] = {
    **FANOUT_PRIMARY_QUESTIONS,
    **FANOUT_COMMON_QUESTIONS,
    **{
        name: question
        for specific in FANOUT_BRANCH_SPECIFIC.values()
        for name, question in specific.items()
    },
}

# The order pairs are declared in. Pair A leads with the fanout request and pair B leads with the
# staged one, so arm identity is not perfectly confounded with position in the run. It is reduced,
# not removed: the first call of the session is still a fanout call. That is why the position
# fields are on every record, and why nothing here attributes a latency difference to an arm.
FANOUT_DECLARED_ORDER: tuple[tuple[str, str], ...] = (
    ("A", FANOUT_ARM),
    ("A", STAGED_ARM),
    ("B", STAGED_ARM),
    ("B", FANOUT_ARM),
)

# Four declared cases, six calls: each staged first stage schedules its own second stage.
FANOUT_CALL_CEILING = 6


def fanout_branch(response: SystemOneResponse) -> str | None:
    """The branch the primary answer selects, or whatever label it returned instead.

    An unroutable label is returned as-is rather than mapped to a default: a label the frozen map
    does not know is a fact about this run, and silently folding it into a known branch would
    invent a routing decision that was never made.
    """
    return top_label(response, "next_action")


def fanout_routable(label: str | None) -> bool:
    """Whether a primary label names one of the frozen branches."""
    return label in FANOUT_BRANCH_QUESTIONS


def fanout_consumed(label: str | None, asked: Sequence[str]) -> list[str]:
    """The questions the fanout arm actually uses, given the branch its primary answer chose.

    Everything else in the request was paid for and not used. That split is the speculative
    overhead, and it is the reason this experiment exists.
    """
    served = set(FANOUT_PRIMARY_QUESTIONS)
    if fanout_routable(label):
        served |= set(FANOUT_BRANCH_QUESTIONS[str(label)])
    return [name for name in asked if name in served]


def _fanout_notes(pair: str, strategy: str, stage: int, round_trip: str) -> dict[str, Any]:
    """Local provenance for one case. None of it is serialized into the request."""
    notes: dict[str, Any] = {
        "pair": pair,
        "strategy": strategy,
        "stage": stage,
        "round_trip": round_trip,
    }
    if stage == STAGE_1:
        notes["branch_expected"] = FANOUT_EXPECTED_BRANCH[pair]
    return notes


def _05_speculative_fanout() -> list[Case]:
    """The declared skeleton: two fanout requests and two staged first stages, interleaved.

    Each staged first stage schedules its own second stage from its answer, so the declared four
    cases become at most six calls. Second stages are not listed here because they cannot be:
    which question set they carry is not known until the primary answer comes back.
    """
    cases: list[Case] = []
    for pair, strategy in FANOUT_DECLARED_ORDER:
        if strategy == FANOUT_ARM:
            cases.append(
                Case(
                    case_id=f"pair{pair}_fanout",
                    state=FANOUT_STATES[pair],
                    questions=FANOUT_QUESTIONS,
                    notes=_fanout_notes(pair, FANOUT_ARM, STAGE_1, "one request, read selectively"),
                )
            )
        else:
            cases.append(
                Case(
                    case_id=f"pair{pair}_staged_1",
                    state=FANOUT_STATES[pair],
                    questions=FANOUT_PRIMARY_QUESTIONS,
                    notes=_fanout_notes(pair, STAGED_ARM, STAGE_1, "first of two"),
                )
            )
    return cases


def _05_follow_up(case: Case, response: SystemOneResponse) -> list[Case]:
    """What runs next after an answer: the staged second stage, or nothing.

    A fanout case schedules nothing -- it already asked everything. A staged second stage
    schedules nothing -- it carries no primary question, so it routes nothing.

    When a staged first stage comes back with a label the frozen map does not know, no second
    request is sent. The alternative would be to pick a branch at run time, and a question set
    chosen that way has never been through the offline equivalence check, so the payload it put on
    the wire would be one no audit covered. Skipping is the rule that keeps every request this
    experiment can send inside the audited set. It is frozen here, before any run, and a run that
    lands on an unroutable label is recorded as what it is rather than retried.
    """
    if case.notes.get("strategy") != STAGED_ARM or case.notes.get("stage") != STAGE_1:
        return []
    label = fanout_branch(response)
    if not fanout_routable(label):
        return []
    return [
        Case(
            case_id=f"pair{case.notes['pair']}_staged_2",
            # The same state object the first stage sent, so the two stages differ only in the
            # questions. A re-serialized copy could drift; this cannot.
            state=case.state,
            questions=FANOUT_BRANCH_QUESTIONS[str(label)],
            notes=_fanout_notes(
                str(case.notes["pair"]), STAGED_ARM, STAGE_2, "second of two"
            )
            | {"branch": label},
        )
    ]


def _fanout_digest(case: Case, response: SystemOneResponse) -> dict[str, Any]:
    """Write the routing decision and the asked/consumed split into the canonical record.

    This is computed at run time on purpose. The split depends on the frozen branch map, so
    recomputing it in the report would make the number move if that map were ever edited; written
    here, it stays attached to the answers that produced it.

    Nothing here is a second judgment: the branch is a label the API returned, looked up in a dict.
    """
    asked = list(case.questions)
    derived: dict[str, Any] = {
        "strategy": case.notes.get("strategy"),
        "stage": case.notes.get("stage"),
        "questions_asked": asked,
    }
    if "next_action" not in case.questions:
        # A staged second stage carries no primary question, so it routes nothing. Its branch was
        # fixed by the answer to the stage before it.
        derived["branch_served"] = case.notes.get("branch")
        return derived

    label = fanout_branch(response)
    derived |= {
        "branch_taken": label,
        "branch_expected": case.notes.get("branch_expected"),
        "branch_matches_expected": label == case.notes.get("branch_expected"),
        "branch_routable": fanout_routable(label),
    }
    if case.notes.get("strategy") == FANOUT_ARM:
        consumed = fanout_consumed(label, asked)
        unused = [name for name in asked if name not in consumed]
        derived |= {
            "questions_consumed": consumed,
            "questions_unused": unused,
            "unused_question_count": len(unused),
        }
    else:
        derived |= {
            "branch_served": label if fanout_routable(label) else None,
            "next_questions": sorted(FANOUT_BRANCH_QUESTIONS.get(str(label), {})),
        }
    return derived


# `06_composite_scoring`: four separate atomic judgments, one composite computed in Python.
#
# "Separate" and not "independent": the four questions each ask one property, and the rubrics keep
# those questions apart in wording, but this experiment does not show the model treats them as
# independent -- the report says so itself. Calling them independent would assert more than the
# measurements support.
#
# The architecture principle under test is that Jev performs atomic semantic judgments while
# ordinary Python performs arithmetic and policy composition. So Jev is never asked to add, to
# weight, to normalize, to invert a direction, or to state a final risk figure. It answers four
# `Score` questions, each about one property, on a 0..3 rubric. Everything after that is a `float`
# and a dict of frozen weights in `composite.py`.
#
# The four rubrics are written to avoid the states' own vocabulary. A rubric that restated the
# states' nouns ("the residual", "the mesh", "the front") would let a correct answer come from
# lexical matching rather than from the judgment the question is asking for.
#
# None of the four asks for an overall verdict. A dimension that smuggled the composite conclusion
# into itself would make the whole composition circular, and the weights would then be decoration.

_QUESTION_INSTRUCTIONS: dict[str, str] = {
    "evidence_quality": "How well is this result supported by checks that are independent of the "
    "run that produced it?",
    "numerical_stability": "How sensitive is this result to the setting variations that were "
    "reported?",
    "reproducibility": "How consistently does this result repeat across independent runs?",
    "failure_severity": "How much would the problems reported with this result affect its "
    "scientific interpretation?",
}

_QUESTION_CRITERIA: dict[str, list[str]] = {
    "evidence_quality": [
        "No independent check on the result is reported",
        "A check is reported, but it is weak or covers only part of the result",
        "Independent checks adequately support the result",
        "Strong independent checks agree and would be enough to rely on the result",
    ],
    "numerical_stability": [
        "The result changes materially under the reported setting variations",
        "The result is materially sensitive to at least one reported setting",
        "The result is mostly stable, with only minor sensitivity to the reported settings",
        "The result is stable across every setting variation that was reported",
    ],
    "reproducibility": [
        "Independent runs do not reproduce the result",
        "Independent runs reproduce the result inconsistently",
        "Independent runs mostly reproduce the result",
        "Independent runs repeatedly reproduce the result",
    ],
    "failure_severity": [
        "Any problems reported have no effect on the interpretation",
        "The problems reported are local and minor",
        "The problems reported materially affect the interpretation",
        "The problems reported are severe enough to invalidate the interpretation",
    ],
}


def _composite_questions() -> dict[str, Question]:
    """The four separate atomic `Score` questions, one object each."""
    return {
        name: Score(
            instructions=_QUESTION_INSTRUCTIONS[name],
            criteria=list(_QUESTION_CRITERIA[name]),
        )
        for name in COMPOSITE_DIMENSIONS
    }


# The three synthetic states, all from one domain: validation of a numerical solver. Only the
# observation text differs between them. None states a verdict, and none uses the language of the
# rubrics ("independent check", "sensitive", "reproduce", "interpretation"), so an answer has to
# come from reading the observations rather than from matching a word.

COMPOSITE_STATES: dict[str, str] = {
    "low_risk": (
        "Validation record, steady advection-diffusion case, 2D. The run was repeated at three "
        "levels of refinement; between the two finest levels the solution changed by less than the "
        "tolerance that was declared before the run. The iteration error fell smoothly and did not "
        "stall. Five independent executions with perturbed starting fields agreed to within the "
        "declared tolerance. Nothing in the output went out of its physical range, so no clipping "
        "was applied."
    ),
    "mixed": (
        "Validation record, steady advection-diffusion case, 2D. Between the two finest levels of "
        "refinement the solution changed by about as much as the tolerance that was declared "
        "before the run, so the comparison is inconclusive rather than passing. The iteration "
        "error fell and then flattened above the target before the iteration limit. Three "
        "independent executions with perturbed starting fields agreed on the bulk of the field; a "
        "fourth placed a sharp feature noticeably further downstream. A few cells briefly left "
        "their physical range at one time step and were clipped."
    ),
    "high_risk": (
        "Validation record, steady advection-diffusion case, 2D, with a sharp internal "
        "discontinuity. Between the two finest levels of refinement the solution changed "
        "qualitatively, and the coarse and fine solutions do not put the discontinuity in the same "
        "place. The iteration error oscillates and never approaches the target. Independent "
        "executions with perturbed starting fields produced visibly different discontinuity "
        "positions, and two of them ended in a non-finite state. Large regions left their "
        "physical range and were clipped."
    ),
}


def _06_composite_scoring() -> list[Case]:
    """Three states, one request each, carrying the *same* four Score questions in the same order.

    Only the state changes. There is deliberately no separate-question arm: `03_parallel_questions`
    already measured whether one request carrying several questions is cheaper than several
    requests, and repeating that here would spend calls answering a question already answered.

    All three cases share one question mapping, and therefore one `Score` object per dimension, so
    "the same questions were asked" is a fact about object identity rather than about two
    definitions that happen to read alike. The mapping is built fresh per `cases()` call so two
    runs cannot share mutable state.
    """
    questions = _composite_questions()
    return [
        Case(
            case_id=name,
            state=COMPOSITE_STATES[name],
            questions=questions,
            notes={"scenario_class": name},
        )
        for name in COMPOSITE_EXPECTED_ORDER
    ]


# `07_instruction_precision` holds the state byte-identical and changes only how explicitly the
# decision boundary is spelled out. Both arms are Noul with criteria present, so the answer space
# is the same and neither arm is handicapped by missing criteria.
#
# What this does NOT do: isolate instruction wording from criteria wording. The two are changed
# together, as one "explicitness" variable, because that is what the docs recommend doing in
# practice. The explicit criteria also deliberately avoid the state's own nouns, so a correct
# answer cannot come from lexical matching alone.
#
# Noul answers carry no distribution and no confidence, so this experiment cannot compare those
# fields. It compares the Noul scalar, tokens, latency, and cost only.

INSTRUCTION_PRECISION_STATE = (
    "The report export spun for ten minutes and never finished. I gave up and used CSV."
)


def _07_instruction_precision() -> list[Case]:
    """One decision, stated with a vague boundary and then with an explicit one."""
    vague = Noul(
        instructions="Is this a serious issue?",
        criteria=NoulCriteria(
            true="Something went wrong for the user",
            false="Nothing went wrong for the user",
        ),
    )
    explicit = Noul(
        instructions=(
            "Does the state describe a situation where a primary requested capability could not "
            "complete, and no equivalent within-feature workaround allowed completion?"
        ),
        criteria=NoulCriteria(
            true=(
                "A primary requested capability could not complete, and no equivalent "
                "within-feature workaround allowed completion"
            ),
            false=(
                "The capability completed, or an equivalent within-feature workaround allowed "
                "completion, or no failure is described"
            ),
        ),
    )
    return [
        Case(
            case_id="vague_boundary",
            state=INSTRUCTION_PRECISION_STATE,
            questions={"blocked": vague},
            notes={"boundary": "vague", "criteria": "present but broad"},
        ),
        Case(
            case_id="explicit_boundary",
            state=INSTRUCTION_PRECISION_STATE,
            questions={"blocked": explicit},
            notes={
                "boundary": "explicit",
                "criteria": "present and specific",
                "leakage_control": "criteria avoid the state's own nouns on purpose",
            },
        ),
    ]


def _08_literal_reading() -> list[Case]:
    """Three small probes of the documented 'literal reading' failure mode.

    The docs say scoping words, negations, and implied conditions are taken at face value. Each
    probe pairs a direct question with its inverted or scoped twin, so the comparison is the
    finding. This is a probe of a documented behaviour, not an attempt to grade the model.
    """
    state = (
        "The customer wrote: 'I do not want a refund. I only want the duplicate charge removed, "
        "and please do not cancel the order.'"
    )
    return [
        Case(
            case_id="negation_direct",
            state=state,
            questions={"wants_refund": Noul(instructions="Does the customer want a refund?")},
            notes={"probe": "negation", "polarity": "direct"},
        ),
        Case(
            case_id="negation_inverted",
            state=state,
            questions={
                "wants_refund": Noul(
                    instructions="Is it true that the customer is asking for something other than a refund?"
                )
            },
            notes={"probe": "negation", "polarity": "inverted"},
        ),
        Case(
            case_id="implied_condition",
            state="The order shipped on Monday. Delivery takes five business days.",
            questions={
                "arrives_by_friday": Noul(
                    instructions="Will the order arrive by Friday of the same week?"
                ),
                "shipped": Noul(instructions="Has the order shipped?"),
            },
            notes={"probe": "implied_condition", "note": "weekday arithmetic belongs in code"},
        ),
        Case(
            case_id="scope",
            state="All contractors must submit timesheets weekly. Priya is a full-time employee.",
            questions={
                "priya_weekly_timesheet": Noul(
                    instructions="Must Priya submit a timesheet every week?"
                )
            },
            notes={"probe": "scope", "note": "applies a rule to someone outside its stated scope"},
        ),
    ]


def _09_numeric_limits() -> list[Case]:
    """A deliberately tiny demonstration of the documented counting and arithmetic limits.

    Only three calls, because the docs already state the limitation and repeating it at scale
    would burn budget to learn something already known. Each case also carries the correct
    code-side answer, computed locally.
    """
    items = ["typesafe", "apple", "california", "banana", "likes", "calibration", "orange", "vertex"]
    return [
        Case(
            case_id="counting_fruits",
            state={"items": items},
            questions={
                f"item_{index}": Noul(instructions=f"Is `items[{index}]` the name of a fruit?")
                for index in range(len(items))
            },
            notes={
                "known_limit": "counting is unreliable; docs recommend one question per item",
                "code_side": "sum the per-item answers in Python (this is the documented workaround)",
            },
        ),
        Case(
            case_id="counting_in_passage",
            state=(
                "The word 'risk' appears in the following sentence: 'We assessed the risk and "
                "accepted it, because the risk was small.'"
            ),
            questions={"occurrences": Noul(instructions="Does the word `risk` appear exactly twice?")},
            notes={
                "known_limit": "counting occurrences is unreliable",
                "code_side": "state.count('risk') == 2",
            },
        ),
        Case(
            case_id="numeric_comparison",
            state="Invoice A is $1,240.00 and invoice B is $1,000.00.",
            questions={"a_larger": Noul(instructions="Is invoice A larger than invoice B?")},
            notes={
                "known_limit": "numeric precision is a documented weakness",
                "code_side": "1240.00 > 1000.00",
            },
        ),
    ]


def _10_state_length() -> list[Case]:
    """Fixed core evidence, growing amounts of irrelevant filler.

    The docs say accuracy falls as unrelated content accumulates and that Jev suffers from
    context rot. The context limit is 64k tokens per request, with 32k for state plus the longest
    question (docs.typesafe.ai/models, "Context length"); these tiers stay far below it on purpose.
    """
    questions: dict[str, Question] = {
        "export_broken": Noul(instructions="Does the report claim that PDF export is broken?"),
        "started_after_release": Noul(instructions="Did the problem start after a release?"),
    }
    tiers = {
        "short": FIXED_EVIDENCE,
        "medium": f"{FIXED_EVIDENCE}\n\n{_pad(8)}",
        "longer": f"{FIXED_EVIDENCE}\n\n{_pad(40)}",
    }
    return [
        Case(
            case_id=f"length_{tier}",
            state=text,
            questions=questions,
            notes={"tier": tier, "core_evidence": "fixed", "filler": "irrelevant"},
        )
        for tier, text in tiers.items()
    ]


def _11_language_pair() -> list[Case]:
    """Semantically equivalent English and Chinese input and questions.

    The models page states English is the primary training language and that other languages,
    including CJK, are handled but not equally well. This measures that on our own content.
    """
    english = (
        "The customer says they were charged twice for order #98423 and wants the duplicate "
        "charge removed."
    )
    chinese = "客户表示订单 #98423 被重复扣款两次，希望删除重复收取的费用。"
    return [
        Case(
            case_id="english",
            state=english,
            questions={
                "charged_twice": Noul(instructions="Does the customer say they were charged twice?"),
                "wants_refund": Noul(instructions="Is the customer asking for a refund?"),
            },
            notes={"language": "en"},
        ),
        Case(
            case_id="chinese",
            state=chinese,
            questions={
                "charged_twice": Noul(instructions="客户是否表示被重复扣款两次？"),
                "wants_refund": Noul(instructions="客户是否要求退款？"),
            },
            notes={"language": "zh", "note": "semantically equivalent to the English case"},
        ),
    ]


# `12_function_routing`: Jev picks a route, Python calls a handler that was registered in advance.
#
# The registry, the closed argument sets, the two policy thresholds and the expected routes all live
# in `routing.py`. This module builds the questions and the states they are asked about, and nothing
# more -- the wire primitives stay in one place, as they do for `06`.
#
# What the model is asked for is a `Choice` over function names that were already in a dict, not a
# function, a call, a path, a query, or a line of code. Nothing in this experiment evaluates an
# answer, imports an answer, or turns an answer into anything executable: an answer is a string that
# is either a key of `routing.HANDLERS` or a reason the case stops.
#
# Two layers, deliberately: the function is one question and its argument is another. Folding them
# into one enumeration (`inspect_boundary_residuals`, `inspect_global_residuals`, ...) would make
# every route a separate label and hide which part of the decision failed when the answer is wrong.
# The two layers are also the reason all four argument questions ride in every request: the function
# is not known when the request is written, so the follow-up cannot be chosen before the fact.
#
# The registry is deliberately not written into the payload. The function names appear there for one
# reason only -- they are the labels the routing `Choice` offers -- and the expected answer is
# nowhere in the request at all.

# What each function does, as the routing `Choice` describes it. These descriptions are the whole of
# what the model is told about a function; none of them names a state, and none of them says when to
# use it.
ROUTING_FUNCTION_CRITERIA: dict[str, str] = {
    "inspect_residuals": "Look inside the domain at where a per-iteration error is concentrated",
    "compare_runs": "Set two existing runs of the same case against each other",
    "request_more_evidence": "Obtain a check or an artefact that does not exist yet",
    "escalate_for_review": "Hand the decision to a person because the record does not settle it",
}

# What each argument label means, as its own `Choice` describes it.
ROUTING_ARGUMENT_CRITERIA: dict[str, str] = {
    "global": "The whole domain, with no part singled out",
    "boundary": "The edges of the domain",
    "high_gradient_region": "The part of the domain where the solution changes steeply",
    "resolution": "The two runs were made with different cell counts",
    "seed": "The two runs were given different starting fields",
    "solver_configuration": "The two runs used different solver settings",
    "convergence_check": "A check on whether the iteration settled before it stopped",
    "independent_reproduction": "A repeat performed by something other than the program that "
    "produced the result",
    "diagnostic_plot": "A rendering of the field for a person to look at",
    "unresolved_discrepancy": "The record contains a disagreement that has not been accounted for",
    "unphysical_values": "The record shows quantities outside the range they are permitted to take",
    "resource_limit": "The record shows the run stopped for a reason other than a settled solution",
}

ROUTING_ARGUMENT_INSTRUCTIONS: dict[str, str] = {
    "inspect_residuals": "If this record's error is looked at in place, which part of the domain "
    "should be looked at?",
    "compare_runs": "If two runs of this case are set against each other, what is it that differs "
    "between them?",
    "request_more_evidence": "If something not in this record is obtained, what kind of thing "
    "should it be?",
    "escalate_for_review": "If a person takes this record over, what is the reason it reached them?",
}

# The four synthetic states. Same domain as `06`: validation of a numerical solver, and nothing but
# synthetic validation text.
#
# None of them contains a function name, an argument label, or a word telling the reader what to do
# about it ("call", "invoke", "route", "escalate", "tool"). Each states an observation and what is
# not yet known, which is what the routing question is for. A test holds that, because a state that
# named its own answer would measure string matching rather than routing.

ROUTING_STATES: dict[str, str] = {
    "oscillating_error": (
        "Validation record, steady advection-diffusion case, 2D. The iteration error fell for "
        "about two hundred steps and then began to rise again, and the rise has continued at "
        "roughly the same rate since. The movement is not spread through the field: it sits in the "
        "narrow band of cells that straddle the sharp front crossing the domain diagonally, while "
        "the rest of the field barely changes from one iteration to the next. The record holds the "
        "iteration history and the field at every tenth step, so that band can be looked at "
        "directly. What is not yet known is whether the movement there reflects how the front is "
        "being resolved."
    ),
    "refinement_difference": (
        "Validation record, steady advection-diffusion case, 2D. Two solutions of the same case "
        "exist: one computed on a 128-cell grid and one on a 512-cell grid. They differ by about "
        "four times the tolerance that was declared before the run, and the difference is spread "
        "across the domain rather than confined to one feature. The starting field was identical "
        "in both, and both used the same solver settings; only the fineness of the grid changed. "
        "Both solutions are stored, so the two can be set against each other directly. What is "
        "not yet known is whether the fineness of the grid is what accounts for the gap."
    ),
    "unchecked_result": (
        "Validation record, steady advection-diffusion case, 2D. The run stopped when the "
        "iteration error fell below the tolerance declared before it started, and the field it "
        "produced is smooth and inside its permitted range everywhere. Every number in the record "
        "was computed by the single program that produced it, including the error estimate, which "
        "was derived from the same iteration history it is meant to check. Nothing was run beside "
        "this run and nothing outside it was consulted. The result is about to be used as the "
        "basis for a decision, and what is missing is something this record cannot supply about "
        "itself."
    ),
    "out_of_range_values": (
        "Validation record, steady advection-diffusion case, 2D. In a band of cells along the "
        "outflow edge the concentration went below zero at two of the recorded steps, and the "
        "program clipped those cells back before continuing; the clipped cells are still visible "
        "in the final output. The rest of the field settled normally. Nothing in the record says "
        "whether a solution that had to be repaired mid-run may be used at all, and this "
        "repository holds no rule that decides it. Someone who owns that judgement needs to look "
        "at what happened before this record is used for anything."
    ),
}

# Local design metadata, written into the record's `notes` and never into the request.
ROUTING_SIDE_EFFECTS = "none; registered handlers only, and only when the frozen policy allows"


def _routing_questions() -> dict[str, Question]:
    """The six questions every state is asked, one object each.

    The routing `Choice` offers exactly the registry's names -- a test holds that against
    `routing.HANDLERS` rather than against a copy of the list -- and each argument `Choice` offers
    exactly the frozen labels for its own function.
    """
    questions: dict[str, Question] = {
        ROUTING_FUNCTION_QUESTION: Choice(
            instructions="Which of these should handle this record next?",
            criteria={name: ROUTING_FUNCTION_CRITERIA[name] for name in ROUTING_FUNCTIONS},
        )
    }
    for function in ROUTING_FUNCTIONS:
        questions[ROUTING_ARGUMENT_QUESTION[function]] = Choice(
            instructions=ROUTING_ARGUMENT_INSTRUCTIONS[function],
            criteria={
                label: ROUTING_ARGUMENT_CRITERIA[label] for label in ROUTING_ARGUMENTS[function]
            },
        )
    questions[ROUTING_REVIEW_QUESTION] = Noul(
        instructions="Should a person look at this record before anything is done with it?"
    )
    return questions


def _12_function_routing() -> list[Case]:
    """Four states, one request each, carrying the *same* six questions in the same order.

    Only the state changes. All four cases share one question mapping, and therefore one `Choice`
    object per route and per argument, so "the same questions were asked" is a fact about object
    identity rather than about four definitions that happen to read alike. The mapping is built
    fresh per `cases()` call so two runs cannot share mutable state.

    The expected route is carried in the case's local notes, which are written into the record and
    never serialized into the request. It is read only to fill in the comparison fields after the
    answer is in; nothing in the routing path consults it, so it cannot steer a route.
    """
    questions = _routing_questions()
    return [
        Case(
            case_id=case_id,
            state=ROUTING_STATES[case_id],
            questions=questions,
            notes={
                "expected_function": function,
                "expected_argument": argument,
                "expects_suppression": expects_suppression,
                "side_effects": ROUTING_SIDE_EFFECTS,
            },
        )
        for case_id, function, argument, expects_suppression in ROUTING_EXPECTED
    ]


# `13_repeatability` -- one payload, five times.
#
# The state is synthetic and carries two live readings at once: the order is both late and charged
# against the customer's account already, and the customer's own position on cancelling is
# conditional. None of that is stated as uncertainty; the situation simply does not resolve to one
# answer, which is what gives the three answer types room to land off 0 and 1.
REPEAT_STATE = (
    "Order #51207 was placed on the 3rd for a replacement kettle filter. "
    "The order page still shows 'processing', but the payment left my account on the 4th. "
    "Support said it would ship within two working days and it is now day five. "
    "I would rather not cancel if it is going to arrive this week."
)

REPEAT_CHOICE_CRITERIA: dict[str, str] = {
    "shipping_delay": "The order is late or has not shipped when it was expected to",
    "billing_discrepancy": "A charge was taken, or taken earlier, than the order justifies",
    "cancellation_request": "The customer wants the order cancelled",
    "product_question": "A question about the product itself, not about the order",
}

REPEAT_QUESTIONS: dict[str, Question] = {
    "primary_issue": Choice(
        instructions="Which single issue is the customer chiefly raising?",
        criteria=dict(REPEAT_CHOICE_CRITERIA),
    ),
    "urgency": Score(
        instructions="How much time pressure does the customer's situation carry?",
        criteria=[
            "No time pressure; the customer is asking for information",
            "Inconvenient, but the customer can wait",
            "Time-critical; the delay is causing active harm",
        ],
    ),
    "wants_to_cancel": Noul(instructions="Does the customer want the order cancelled?"),
}


def _13_repeatability() -> list[Case]:
    """The same request repeated, to observe run-to-run stability on an identical payload.

    This measures one thing: how much the answers and the reported usage move when nothing about
    the request moves. It is not a prompt-sensitivity test, not a batching test, and not a
    correctness test -- varying anything would destroy the measurement, so nothing varies. The five
    cases share one state object and one set of question objects; only the case id and the local
    notes differ, and neither of those is serialized into the request (see
    `TestRepeatabilityPayloadIdentity`).

    The state is deliberately mixed-signal. A state with an obvious single answer would push every
    probability to 0 or 1 and leave nothing to observe: a saturated distribution is stable for
    reasons that have nothing to do with repeatability. Nothing here asks the model to be unsure --
    the ambiguity is in the situation, which is where it belongs.

    All three question types ride in every request, so one call yields a Choice label with its full
    distribution, a Score with its ordinal distribution, and a Noul scalar.
    """
    state = REPEAT_STATE
    questions: dict[str, Question] = dict(REPEAT_QUESTIONS)
    return [
        Case(
            case_id=f"repeat_{index + 1}",
            state=state,
            questions=questions,
            notes={"repeat": index + 1, "of": REPEAT_CALLS},
        )
        for index in range(REPEAT_CALLS)
    ]


# `13b_ambiguous_repeatability` repeats `01_primitives` rather than a purpose-built case.
#
# The reason is that `13_repeatability` failed its own sub-goal: its Choice came back saturated at
# 1.0/0.0 and its Score at 0.98, so it measured repeatability at a corner of the scale and nothing
# about a field with two live options. `01_primitives` is the one payload in this bench with a *real*
# measurement showing a non-degenerate distribution -- its Choice returned 0.45 `other` against 0.44
# `billing`, and its Score spread 0.41/0.59 across two levels. A case designed to look ambiguous is
# not evidence that the model finds it so; this one carries a record of having been ambiguous.
#
# That historical record is prior evidence and nothing more: it says the payload *can* produce a
# non-saturated distribution, not that it will again. Section H of the design audit says the same
# thing from the other side -- whether this run is ambiguous is a result, not a property of the
# design, and a saturated result is recorded rather than retried.
#
# The repeat count is bound to `REPEAT_CALLS` rather than written as a second literal, so the two
# repeat experiments cannot silently diverge in size.
AMBIGUOUS_CALLS = REPEAT_CALLS


def _13b_ambiguous_repeatability() -> list[Case]:
    """`01_primitives`' exact request, sent five times, to observe run-to-run variation.

    The state and the question objects are the ones `01_primitives` sends -- not copies of them --
    so the two experiments cannot drift apart. Every call is byte-identical; `case_id` and `notes`
    are provenance for the log and never reach the API. Nothing here hints at uncertainty, adds a
    nonce, or varies wording: the ambiguity being measured is in the ticket, and the moment it is
    written into the question this stops being a measurement of the payload and becomes a
    measurement of an instruction to be unsure.
    """
    state = PRIMITIVES_STATE
    questions: dict[str, Question] = PRIMITIVES_QUESTIONS
    return [
        Case(
            case_id=f"ambiguous_{index + 1}",
            state=state,
            questions=questions,
            notes={"repeat": index + 1, "of": AMBIGUOUS_CALLS, "repeats": "01_primitives"},
        )
        for index in range(AMBIGUOUS_CALLS)
    ]


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------

EXPERIMENTS: dict[str, Experiment] = {
    "00_model_info": Experiment(
        "00_model_info",
        CORE,
        "List accessible models and record which versioned ID each alias resolves to.",
        _00_model_info,
    ),
    "01_primitives": Experiment(
        "01_primitives",
        CORE,
        "One request carrying Choice + Score + Noul against one state (the smoke test).",
        _01_primitives,
    ),
    "02_structured_addressing": Experiment(
        "02_structured_addressing",
        CORE,
        "Field-path addressing over structured state versus described addressing over prose state.",
        _02_structured_addressing,
    ),
    "03_parallel_questions": Experiment(
        "03_parallel_questions",
        CORE,
        "One batched request versus the same five questions sent separately, in two order-balanced cycles.",
        _03_parallel_questions,
    ),
    "04_confidence": Experiment(
        "04_confidence",
        CORE,
        "Specific versus ambiguous evidence in one scenario, gated in code on confidence alone.",
        _04_confidence,
        digest=_confidence_digest,
    ),
    "05_speculative_fanout": Experiment(
        "05_speculative_fanout",
        EXTENDED,
        "A branching control flow asked two ways: every possible follow-up in one request, or "
        "the chosen branch's follow-ups in a second request.",
        _05_speculative_fanout,
        digest=_fanout_digest,
        follow_up=_05_follow_up,
        call_ceiling=FANOUT_CALL_CEILING,
    ),
    "06_composite_scoring": Experiment(
        "06_composite_scoring",
        EXTENDED,
        "Four separate atomic Score judgments per state, composed into one risk by Python with "
        "weights "
        "frozen before the run. Jev is asked for no arithmetic and no verdict.",
        _06_composite_scoring,
        digest=composite_digest,
    ),
    "07_instruction_precision": Experiment(
        "07_instruction_precision",
        EXTENDED,
        "Vague versus explicit decision boundaries on a byte-identical state; criteria in both arms.",
        _07_instruction_precision,
    ),
    "08_literal_reading": Experiment(
        "08_literal_reading",
        EXTENDED,
        "Negation, implied conditions, and scope, following the documented jaggedness page.",
        _08_literal_reading,
    ),
    "09_numeric_limits": Experiment(
        "09_numeric_limits",
        EXTENDED,
        "A tiny demonstration of the documented counting and arithmetic limits.",
        _09_numeric_limits,
    ),
    "10_state_length": Experiment(
        "10_state_length",
        EXTENDED,
        "Fixed core evidence with growing irrelevant filler.",
        _10_state_length,
    ),
    "11_language_pair": Experiment(
        "11_language_pair",
        EXTENDED,
        "Equivalent English and Chinese input and questions.",
        _11_language_pair,
    ),
    "12_function_routing": Experiment(
        "12_function_routing",
        EXTENDED,
        "Route a request to a name in a registry frozen before the run and to one of that name's "
        "closed-set arguments, then call an inert handler; a frozen policy may only withhold it.",
        _12_function_routing,
        digest=routing_digest,
    ),
    "13_repeatability": Experiment(
        "13_repeatability",
        EXTENDED,
        f"One identical three-primitive request sent {REPEAT_CALLS} times, to observe run-to-run "
        "stability of the answers and the reported usage.",
        _13_repeatability,
    ),
    "13b_ambiguous_repeatability": Experiment(
        "13b_ambiguous_repeatability",
        EXTENDED,
        f"`01_primitives`' own request sent {AMBIGUOUS_CALLS} times, to observe run-to-run "
        "variation where the Choice and the Score are not at the ends of their scales.",
        _13b_ambiguous_repeatability,
    ),
}


def experiment_names() -> list[str]:
    """Registered experiment names, sorted."""
    return sorted(EXPERIMENTS)


def get_experiment(name: str) -> Experiment:
    """Look up an experiment by name, raising a helpful error when it is unknown."""
    try:
        return EXPERIMENTS[name]
    except KeyError:
        raise KeyError(f"unknown experiment {name!r}; known: {', '.join(experiment_names())}") from None


def experiments_for_tier(tier: str) -> list[Experiment]:
    """Registered experiments in the given tier, in name order."""
    return [EXPERIMENTS[name] for name in experiment_names() if EXPERIMENTS[name].tier == tier]


def total_cases(experiments: Sequence[Experiment]) -> int:
    """The most API calls the given experiments can make, for budgeting before a run.

    A ceiling, so a run can never be planned against a number the run then exceeds. For every
    fixed experiment it equals the case count exactly.
    """
    return sum(experiment_call_ceiling(experiment) for experiment in experiments)


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------


def _derived_notes(
    experiment: Experiment, case: Case, response: SystemOneResponse
) -> dict[str, Any]:
    """Local interpretation of a response: derived values, never extra API calls.

    Whatever this returns is merged into the case's provenance record under ``notes.derived``, so a
    code-side decision such as the confidence gate is preserved in the canonical log.
    """
    if experiment.digest is None:
        return {}
    return experiment.digest(case, response)


def _record_transport_attempts(
    record: CallRecord, probe: "TransportProbe | None", attempts_before: int | None
) -> None:
    """Write the locally observed attempt count for one logical call.

    Nothing is written when the probe was absent or never instrumented. Recording a zero there
    would be indistinguishable from a genuine zero-attempt call -- the SDK does raise before
    sending when a request fails validation -- so "not recorded" has to stay a distinct state.
    """
    if probe is None or not probe.attached or attempts_before is None:
        return
    attempts = max(probe.attempts - attempts_before, 0)
    record.transport_attempt_count = attempts
    record.transport_retry_count_observed = max(attempts - 1, 0)
    record.attempt_count_source = ATTEMPT_COUNT_SOURCE


def run_case(
    experiment: Experiment,
    case: Case,
    *,
    client: TypeSafeClient,
    recorder: UsageRecorder,
    model: str | None = None,
    case_sequence_index: int | None = None,
    probe: TransportProbe | None = None,
) -> tuple[CallRecord, SystemOneResponse | None]:
    """Run one case, appending exactly one provenance record whatever the outcome.

    `probe`, when supplied and instrumented, turns the outgoing HTTP attempts made inside this
    call's timing window into a measured count. The read happens before the request and again in a
    ``finally``, so a call that raises still records how many attempts it actually made.
    """
    with recorder.begin(
        experiment=experiment.name,
        case_id=case.case_id,
        model_requested=model or DEFAULT_MODEL,
        questions=case.questions,
        state=case.state,
        notes=case.notes,
        case_sequence_index=case_sequence_index,
    ) as pending:
        attempts_before = probe.attempts if probe is not None else None
        try:
            response = client.system_one(
                state=case.state,
                questions=case.questions,
                model=model,
            )
        except TypeSafeAuthenticationError:
            # No point spending the rest of the budget on calls that cannot succeed.
            pending.record.notes = {**pending.record.notes, "aborted": "authentication failed"}
            raise
        finally:
            _record_transport_attempts(pending.record, probe, attempts_before)
        pending.succeeded(response)
        derived = _derived_notes(experiment, case, response)
        if derived:
            pending.record.notes = {**pending.record.notes, "derived": derived}
        return pending.record, response


def run_experiment(
    experiment: Experiment,
    *,
    client: TypeSafeClient,
    recorder: UsageRecorder,
    model: str | None = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    on_case: Callable[[Case, CallRecord, SystemOneResponse], None] | None = None,
    on_error: Callable[[Case, Exception], None] | None = None,
    probe: "TransportProbe | None" = None,
) -> list[CallRecord]:
    """Run an experiment's cases in order, stopping at ``max_requests``.

    A case that fails records its error and the run continues, so a partial result still has
    provenance. An authentication failure aborts immediately rather than spending the rest of the
    budget on calls that cannot succeed. There are no hidden retries here; the SDK's own retry
    policy still applies inside each call, and `probe` measures how many attempts that produced.

    When the experiment declares a ``follow_up``, the answer to a case chooses what runs next. The
    chosen cases are spliced in immediately after the case that produced them, so a control flow
    stays contiguous instead of interleaving with the rest of the skeleton. A follow-up is only
    requested after a *successful* call: with no answer there is nothing to route on, and guessing
    a branch would put a payload on the wire that no offline audit ever covered.

    ``max_requests`` is counted in calls attempted, not in successful records, so a failing case
    still consumes budget.
    """
    records: list[CallRecord] = []
    queue: deque[Case] = deque(experiment.cases())
    attempted = 0
    while queue and attempted < max_requests:
        case = queue.popleft()
        attempted += 1
        try:
            record, response = run_case(
                experiment,
                case,
                client=client,
                recorder=recorder,
                model=model,
                case_sequence_index=attempted - 1,
                probe=probe,
            )
        except TypeSafeAuthenticationError:
            raise
        except Exception as error:  # noqa: BLE001 - a bench keeps going after a failed case.
            if on_error is not None:
                on_error(case, error)
            continue
        records.append(record)
        if on_case is not None:
            on_case(case, record, response)
        if experiment.follow_up is not None and response is not None:
            queue.extendleft(reversed(experiment.follow_up(case, response)))
    return records


__all__ = [
    "AMBIGUOUS_CALLS",
    "BATCH_ARM",
    "CORE",
    "DEFAULT_MAX_REQUESTS",
    "DEFAULT_MODEL",
    "FANOUT_ARM",
    "FANOUT_BRANCH_QUESTIONS",
    "FANOUT_BRANCH_SPECIFIC",
    "FANOUT_CALL_CEILING",
    "FANOUT_DECLARED_ORDER",
    "FANOUT_EXPECTED_BRANCH",
    "FANOUT_PRIMARY_QUESTIONS",
    "FANOUT_QUESTIONS",
    "FANOUT_STATES",
    "PRIMITIVES_QUESTIONS",
    "PRIMITIVES_STATE",
    "REPEAT_CALLS",
    "REPEAT_CHOICE_CRITERIA",
    "REPEAT_QUESTIONS",
    "REPEAT_STATE",
    "STAGED_ARM",
    "EXPERIMENTS",
    "EXTENDED",
    "MAX_REPEATS",
    "PARALLEL_CYCLES",
    "SEPARATE_ARM",
    "Case",
    "Experiment",
    "ROUTING_ARGUMENT_CRITERIA",
    "ROUTING_CASE_ORDER",
    "ROUTING_EXPECTED",
    "ROUTING_FUNCTION_CRITERIA",
    "ROUTING_SIDE_EFFECTS",
    "ROUTING_STATES",
    "answer_digest",
    "confidence_of",
    "experiment_call_ceiling",
    "experiment_names",
    "experiments_for_tier",
    "fanout_branch",
    "fanout_consumed",
    "fanout_routable",
    "get_experiment",
    "normalized_score",
    "noul_of",
    "run_case",
    "run_experiment",
    "score_of",
    "top_label",
    "total_cases",
]
