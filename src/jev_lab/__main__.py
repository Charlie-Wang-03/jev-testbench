"""Command line entry point: ``uv run python -m jev_lab <command>``.

Commands that call the API resolve the credential first (see ``client``) and report only whether it
is present and which source it came from. No command prints, logs, or writes the key itself.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from typesafe_sdk import SystemOneResponse, TypeSafeAuthenticationError, TypeSafeError

from . import experiments as lab
from .client import (
    API_KEY_ENV,
    MissingApiKeyError,
    SecretFileError,
    TransportProbe,
    api_key_status,
    open_client,
    require_api_key,
    scrub_secrets,
)
from .experiments import Case, Experiment
from .final_report import write_final_report
from .recorder import DEFAULT_RESULTS_DIR, CallRecord, UsageRecorder
from .report import generate_report
from .snapshot import write_snapshot

EXIT_OK = 0
EXIT_ERROR = 1


def _print_key_status() -> None:
    """Report only whether a key is configured -- never the value."""
    print(f"{API_KEY_ENV}: {api_key_status()}")


def _format_cost(record: CallRecord) -> str:
    """Render a cost, keeping 'unknown' distinct from 'zero'."""
    if record.estimated_cost_usd is None:
        return "unknown"
    return f"${record.estimated_cost_usd:.8f}"


def _format_attempts(record: CallRecord) -> str:
    """Render the observed transport attempts, keeping 'not recorded' distinct from 'one'."""
    if record.transport_attempt_count is None:
        return "not recorded"
    observed = record.transport_retry_count_observed
    return f"{record.transport_attempt_count} (retries observed: {observed})"


def _print_case_result(case: Case, record: CallRecord, response: SystemOneResponse | None) -> None:
    """Print one case's outcome, then the locally derived interpretation of its answers."""
    print(f"\n  case {case.case_id}")
    print(
        f"    model={record.model_resolved or 'n/a'}  "
        f"in={record.input_tokens}  out={record.output_tokens}  "
        f"latency={record.latency_ms}ms  cost={_format_cost(record)}"
    )
    if record.request_id:
        print(f"    request_id={record.request_id}")
    print(f"    attempts={_format_attempts(record)}")
    if response is not None:
        digest = lab.answer_digest(response)
        print(f"    answers={json.dumps(digest, indent=6, ensure_ascii=False)}")
    # Local, code-side interpretation (e.g. the confidence gate). Persisted in the record too.
    derived = record.notes.get("derived")
    if derived:
        print(f"    derived={json.dumps(derived, indent=6, ensure_ascii=False)}")


def _print_case_table(records: list[CallRecord]) -> None:
    """A compact per-case table, which is what A/B experiments are read from.

    ``run#`` is the call's position in the run and ``first`` marks the request that opened the
    connection pool. Both are in the record, and printing them here is deliberate: a first-request
    latency effect that is invisible in the table is one a reader will otherwise attribute to the
    arm.
    """
    if not records:
        print("\nNo successful calls recorded.")
        return
    print(
        f"\n  {'case_id':<36} {'run#':>4} {'first':>5} {'att':>4} {'in':>7} {'out':>6} "
        f"{'total':>7} {'latency_ms':>11} {'cost_usd':>12}"
    )
    for record in records:
        first = "*" if record.is_first_request_in_client_session else ""
        attempts = "n/r" if record.transport_attempt_count is None else str(record.transport_attempt_count)
        print(
            f"  {record.case_id:<36} {record.logical_request_index_in_run:>4} {first:>5} "
            f"{attempts:>4} {record.input_tokens:>7} {record.output_tokens:>6} "
            f"{record.total_tokens:>7} {str(record.latency_ms):>11} {_format_cost(record):>12}"
        )


def _run_experiments(
    selected: list[Experiment],
    *,
    model: str | None,
    max_requests: int,
    results_dir: Path,
) -> int:
    """Run experiments, writing one provenance record per call and printing per-case results."""
    _print_key_status()
    # Fail on the credential before printing a plan or spending anything. Both credential failures
    # land here: no key at all, and a local secret file that exists but cannot be used. The second
    # is not downgraded to the first -- a key meant to load and did not is a different problem, and
    # the message says which one it is without quoting anything out of the file.
    try:
        require_api_key()
    except (MissingApiKeyError, SecretFileError) as error:
        print(f"\n{scrub_secrets(str(error))}")
        return EXIT_ERROR
    planned = lab.total_cases(selected)
    if planned > max_requests:
        print(f"\nrefusing to run: {planned} cases planned but --max-requests is {max_requests}.")
        print("Pass a larger --max-requests if that spend is intended.")
        return EXIT_ERROR

    print(
        f"\nrunning {len(selected)} experiment(s), {planned} API call(s), "
        f"model requested={model or lab.DEFAULT_MODEL}"
    )

    # One client per invocation, so one session id: it groups the calls that shared a connection
    # pool, which is what makes a first-request latency effect visible after the fact.
    recorder = UsageRecorder(results_dir)
    # Counts outgoing HTTP attempts so a retry can be seen after the fact. It reads an integer and
    # nothing else: no header, URL, or body is ever inspected.
    probe = TransportProbe()
    all_records: list[CallRecord] = []
    try:
        with open_client(model=model, probe=probe) as client:
            for experiment in selected:
                print(f"\n== {experiment.name} — {experiment.intent}")
                records = lab.run_experiment(
                    experiment,
                    client=client,
                    recorder=recorder,
                    model=model,
                    max_requests=max_requests - len(all_records),
                    on_case=_print_case_result,
                    on_error=lambda case, error: print(
                        f"\n  case {case.case_id} FAILED: {type(error).__name__}: {scrub_secrets(str(error))}"
                    ),
                    probe=probe,
                )
                all_records.extend(records)
                _print_case_table(records)
    except (MissingApiKeyError, SecretFileError) as error:
        print(f"\n{scrub_secrets(str(error))}")
        return EXIT_ERROR
    except TypeSafeAuthenticationError as error:
        print(f"\nauthentication failed: {scrub_secrets(str(error))}")
        return EXIT_ERROR
    except TypeSafeError as error:
        print(f"\nTypeSafe SDK error: {type(error).__name__}: {scrub_secrets(str(error))}")
        return EXIT_ERROR

    print(f"\nwrote {len(all_records)} record(s) to {recorder.path.as_posix()}")
    print(f"run_id={recorder.run_id}")
    print(f"client_session_id={recorder.client_session_id}")
    print("Run `uv run python -m jev_lab report` to regenerate the summaries.")
    return EXIT_OK


def _cmd_list(args: argparse.Namespace) -> int:
    """List registered experiments, whether they have run, and the credential status."""
    _print_key_status()
    # `calls` is the ceiling, not the declared case count. For an experiment whose next request
    # depends on the last answer the two differ, and the ceiling is the one that budgets a run.
    print(f"\n{'experiment':<26} {'tier':<9} {'calls':>5}  intent")
    for name in lab.experiment_names():
        experiment = lab.EXPERIMENTS[name]
        calls = lab.experiment_call_ceiling(experiment)
        print(f"{name:<26} {experiment.tier:<9} {calls:>5}  {experiment.intent}")

    core = lab.experiments_for_tier(lab.CORE)
    extended = lab.experiments_for_tier(lab.EXTENDED)
    print(f"\ntiers: {lab.CORE}={lab.total_cases(core)} cases, {lab.EXTENDED}={lab.total_cases(extended)} cases")
    print(f"default budget for a single `run`: --max-requests {lab.DEFAULT_MAX_REQUESTS}")
    return EXIT_OK


def _cmd_run(args: argparse.Namespace) -> int:
    """Run one named experiment."""
    try:
        experiment = lab.get_experiment(args.experiment)
    except KeyError as error:
        print(str(error))
        return EXIT_ERROR
    return _run_experiments(
        [experiment],
        model=args.model,
        max_requests=args.max_requests,
        results_dir=args.results_dir,
    )


def _cmd_run_all(args: argparse.Namespace) -> int:
    """Run every experiment in a tier. Reserved for deliberate, human-initiated runs."""
    selected = lab.experiments_for_tier(args.tier)
    if not selected:
        print(f"no experiments in tier {args.tier!r}")
        return EXIT_ERROR
    planned = lab.total_cases(selected)
    if args.max_requests < planned:
        print(f"tier {args.tier!r} needs {planned} API calls; --max-requests is {args.max_requests}.")
        print(f"Re-run with --max-requests {planned} (or higher) to proceed deliberately.")
        return EXIT_ERROR
    return _run_experiments(
        selected,
        model=args.model,
        max_requests=args.max_requests,
        results_dir=args.results_dir,
    )


def _cmd_report(args: argparse.Namespace) -> int:
    """Regenerate the local summaries from the append-only JSONL log."""
    summary: dict[str, dict[str, Any]] = generate_report(args.results_dir)
    if not summary:
        print(f"no records in {args.results_dir / 'usage.jsonl'} yet")
        return EXIT_OK
    print(f"{'experiment':<26} {'reqs':>5} {'in':>8} {'out':>7} {'mean_ms':>9} {'cost_usd':>12}")
    for experiment, metrics in summary.items():
        cost = metrics["estimated_cost_usd"]
        cost_text = "n/a" if cost is None else f"${cost:.8f}"
        mean_ms = metrics["mean_latency_ms"]
        print(
            f"{experiment:<26} {metrics['requests']:>5} {metrics['input_tokens']:>8} "
            f"{metrics['output_tokens']:>7} {('n/a' if mean_ms is None else f'{mean_ms:.1f}'):>9} {cost_text:>12}"
        )
    print(f"\nwrote {(args.results_dir / 'summary.csv').as_posix()}")
    print(f"wrote {(args.results_dir / 'summary.md').as_posix()}")
    return EXIT_OK


def _cmd_snapshot(args: argparse.Namespace) -> int:
    """Derive results/capability_snapshot.md from the log. Reads only; never calls the API."""
    target = write_snapshot(args.results_dir)
    if target is None:
        print(f"no records in {args.results_dir / 'usage.jsonl'} yet")
        return EXIT_OK
    print(f"wrote {target.as_posix()}")
    print("This is a derived view. results/usage.jsonl remains the canonical record.")
    return EXIT_OK


def _cmd_final_report(args: argparse.Namespace) -> int:
    """Derive results/JEV_LOCAL_EVALUATION_FINAL.md from the log. Reads only; never calls the API."""
    target = write_final_report(args.results_dir)
    if target is None:
        print(f"no records in {args.results_dir / 'usage.jsonl'} yet")
        return EXIT_OK
    print(f"wrote {target.as_posix()}")
    print("This is a derived view. results/usage.jsonl remains the canonical record.")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    The help text names which commands reach the network. `run` and `run-all` spend real money
    against a real account, and someone who only skims `--help` should still come away knowing
    that. Labels are ASCII: help goes to stdout, whose encoding on Windows is the locale's, not
    UTF-8.
    """
    parser = argparse.ArgumentParser(
        prog="jev_lab",
        description=(
            "A minimal, auditable bench for measuring TypeSafe Jev locally. Four commands are "
            "offline: they read the committed log and open no socket. Two are live: they send "
            "real API calls and spend real money."
        ),
        epilog=(
            "Offline: list, report, snapshot, final-report.  "
            "Live, and needs TYPESAFE_API_KEY: run, run-all."
        ),
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Where usage.jsonl and the summaries live (default: results).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list",
        help="OFFLINE. List registered experiments, their tiers, call ceilings, credential status.",
    )
    subparsers.add_parser(
        "report", help="OFFLINE. Regenerate summary.csv and summary.md from the JSONL log."
    )
    subparsers.add_parser(
        "snapshot",
        help="OFFLINE. Regenerate the derived capability_snapshot.md from the JSONL log.",
    )
    subparsers.add_parser(
        "final-report",
        help="OFFLINE. Regenerate the derived JEV_LOCAL_EVALUATION_FINAL.md from the JSONL log.",
    )

    run = subparsers.add_parser(
        "run", help="LIVE. Run one experiment. Sends real API calls and spends real money."
    )
    run.add_argument("experiment", help="Experiment name, as shown by `list`.")
    run.add_argument("--model", default=None, help="Model override; default is the SDK's jev-latest.")
    run.add_argument(
        "--max-requests",
        type=int,
        default=lab.DEFAULT_MAX_REQUESTS,
        help=f"Hard ceiling on API calls for this invocation (default: {lab.DEFAULT_MAX_REQUESTS}).",
    )

    run_all = subparsers.add_parser(
        "run-all",
        help=(
            "LIVE. Run every experiment in a tier. Spends real money, and refuses to start "
            "without an explicit budget that covers the tier."
        ),
    )
    run_all.add_argument("--tier", required=True, choices=[lab.CORE, lab.EXTENDED])
    run_all.add_argument("--model", default=None, help="Model override; default is the SDK's jev-latest.")
    run_all.add_argument(
        "--max-requests",
        type=int,
        default=0,
        help="Must be at least the tier's case count; run-all refuses otherwise.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "list": _cmd_list,
        "run": _cmd_run,
        "run-all": _cmd_run_all,
        "report": _cmd_report,
        "snapshot": _cmd_snapshot,
        "final-report": _cmd_final_report,
    }
    try:
        return handlers[args.command](args)
    except KeyboardInterrupt:
        print("\ninterrupted")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
