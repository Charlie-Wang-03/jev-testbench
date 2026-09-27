"""The frozen evidence manifest for release ``v0.1.0``, and the offline check that it still holds.

A freeze is only worth citing if something can prove it has not moved. This module is that
something: it builds ``docs/evidence/v0.1.0/evidence-manifest.json`` from the repository, and it
re-verifies every claim in that manifest from disk.

Two commands, both strictly offline::

    uv run python -m jev_lab.evidence_freeze verify    # re-check the freeze (the default)
    uv run python -m jev_lab.evidence_freeze build     # regenerate the manifest

``verify`` opens no socket and never needs a credential. It reads the manifest, recomputes the
SHA-256 of every file the manifest lists, re-counts both canonical logs, and re-checks the release's
structural invariants. Any mismatch is a non-zero exit.

**Why this is not a framework.** It knows about exactly one release, ``v0.1.0``, and it is meant to
be replaced by a new module -- not extended -- when a ``v0.2.0`` freeze exists. A generic freeze
engine would have to discover which documents matter and what each one promises, and that judgment
is the actual content of a freeze. Hard-coding it here keeps the judgment reviewable.

**What CI does with it.** Every push runs ``verify``. Editing a canonical log, an audit, the
preregistration or the registry therefore fails the build until a new versioned freeze is created for
it. That is the mechanism that stops a frozen release from quietly going stale -- not a convention,
and not a comment asking people to be careful.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FROZEN_VERSION = "0.1.0"
PLANNED_GIT_TAG = "v0.1.0"
FREEZE_DATE = "2026-09-27"

EVIDENCE_DIR = Path("docs/evidence") / f"v{FROZEN_VERSION}"
MANIFEST_PATH = EVIDENCE_DIR / "evidence-manifest.json"

# The two canonical logs, and the facts about them that a citation depends on. These are *historical
# measurements*: they may never be updated in place, only superseded by a new version directory.
CANONICAL_LOGS: dict[str, dict[str, Any]] = {
    "results/usage.jsonl": {
        "stage": "P0",
        "description": "Core evaluation log. Frozen P0 evidence; append-only in name only, never extended.",
        "records": 42,
        "recorded_window_utc": ["2026-09-20T15:29:51Z", "2026-09-21T14:20:51Z"],
    },
    "results/p3_boundary_locus/usage.jsonl": {
        "stage": "P3",
        "description": "P3 boundary-locus log. Kept separate so P0's published digest stays valid.",
        "records": 12,
        "recorded_window_utc": ["2026-09-22T15:37:30Z", "2026-09-22T15:37:35Z"],
    },
}

# Canonical *evidence*: documents whose content is a measurement, an analysis of one, or the
# provenance that keeps the two distinguishable. Hashing these is the point of the freeze.
EVIDENCE_DOCUMENTS = [
    "results/JEV_LOCAL_EVALUATION_FINAL.md",
    "docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md",
    "docs/audits/P2_JEV_INSIGHT_TRIAGE.md",
    "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md",
    "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md",
    "docs/experiments/EXPERIMENT_REGISTRY.md",
    "docs/sources/TYPESAFE_OFFICIAL_SOURCES.md",
    "docs/EVIDENCE_PROVENANCE.md",
    "docs/findings/findings.md",
    "docs/ERRATA.md",
    "docs/evidence/README.md",
    "docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md",
    "docs/evidence/v0.1.0/RELEASE_NOTES.md",
    "docs/evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md",
]

# Public documentation: how the evidence is *presented*. Hashed so a reader can see the release
# whole, but a wording fix here is not a change to the evidence. Naming this separately is
# deliberate -- calling every markdown file "canonical evidence" would make the phrase meaningless.
PUBLIC_DOCUMENTATION = [
    "README.md",
    "README.zh-CN.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "FREEZE.md",
    "CLAUDE.md",
    "docs/README.md",
    "docs/OPEN_SOURCE_LICENSE_DECISION.md",
    "docs/architecture/architecture.md",
    "docs/architecture/architecture.zh-CN.md",
    "docs/methodology/evaluation.md",
    "docs/methodology/evaluation.zh-CN.md",
    "docs/guides/reproducibility.md",
    "docs/guides/reproducibility.zh-CN.md",
    "docs/guides/credentials.md",
    "docs/guides/credentials.zh-CN.md",
    "docs/findings/findings.zh-CN.md",
]

# Release metadata: the files that say *what this release is*, rather than what it found.
RELEASE_METADATA = ["LICENSE", "CITATION.cff", "pyproject.toml"]

# The historical lineage, with what each commit *is*. A list of SHAs with no explanation is not
# provenance; the label is the content.
HISTORICAL_COMMITS = [
    ("e20fad5", "P0", "MEASUREMENT", "The 42-record core freeze."),
    ("e9d54ca", "P0", "ANALYSIS", "Derived-report integrity fix for confidence gating. No record changed."),
    ("77357d9", "P0", "ANALYSIS", "Closes residual derived-report integrity gaps. No record changed."),
    ("ec04cb6", "P1", "ANALYSIS", "Audits official claims against the frozen evidence. No API call."),
    ("3125281", "P1", "DOCUMENTATION", "Repairs the P1 audit's own HEAD provenance. Findings not edited."),
    ("373e259", "P2", "ANALYSIS", "Novelty triage; seven candidates retired, two on prior art. No API call."),
    ("db7d06f", "P3", "PREREGISTRATION", "db7d06f = preregistration + original analyzer, frozen before the first request."),
    ("c0fc9cc", "P3", "MEASUREMENT", "c0fc9cc = immutable measurements + discovered defect disclosure."),
    ("bdcb637", "P3", "ANALYSIS", "bdcb637 = post-run analyzer repair, no new measurement."),
    ("cc778be", "P3.5", "DOCUMENTATION", "Reorganises public documentation."),
    ("c3f468d", "P3.5", "DOCUMENTATION", "Adds bilingual project documentation."),
    ("56eb159", "P3.5", "ENGINEERING", "Adds offline CI and repository quality gates."),
    ("251c883", "P3.5", "ENGINEERING", "Hardens repository for public release."),
    ("ad1dff4", "P3.6", "DOCUMENTATION", "MIT license, opaque-identifier decision, experiment retirement."),
    ("44fbbb1", "P3.6", "DOCUMENTATION", "States the verified test count, not the pre-commit one."),
]

# The verdicts this release inherits. Each is a string that appears in a frozen document; the
# verifier checks the strings rather than restating the reasoning.
SCIENTIFIC_STATE = "NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET"
P3_VERDICT = "P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION"
INHERITED_VERDICTS = [
    "P1_OFFICIAL_LOCAL_AUDIT_PASS",
    "P2_TRIAGE_PASS",
    "CORE_CAPABILITY_EXPLORATION_CLOSED",
]

# What the release explicitly does *not* establish. Frozen here so that a later edit cannot quietly
# drop one -- a non-claim is as much a part of the evidence as a claim.
NON_CLAIMS = [
    "NO_GENERAL_ACCURACY_CLAIM",
    "NO_CALIBRATION_VALIDATION",
    "NO_MODEL_LATENCY_BENCHMARK",
    "NO_UNIVERSAL_BATCHING_RATIO",
    "NO_DETERMINISM_VERDICT",
    "NO_BROAD_HALLUCINATION_BENCHMARK",
    "NO_PRODUCTION_SAFETY_CERTIFICATION",
    "NO_GENERAL_INSTRUCTION_VS_CRITERIA_FIELD_PREFERENCE",
    "NO_NAS_CLAIM",
]

SCIENTIFIC_STATE_EVIDENCE = "docs/EVIDENCE_PROVENANCE.md"

EXPECTED_SOURCES_REGISTRY_SHA256 = (
    "f823fc9f0d2f3464544daf43c264506785962ca0de9e8236b6c572a2775e47f3"
)


def sha256_of(path: Path) -> str:
    """SHA-256 of a file's bytes. Bytes, not text: line endings are part of the identity here."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_records(path: Path) -> list[dict[str, Any]]:
    """Parse a canonical JSONL log. Blank lines are skipped; anything else must be an object."""
    if not path.is_file():
        raise FileNotFoundError(path)
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path.as_posix()} line {number} is not JSON: {error}") from error
    return records


def _log_facts(relative: str) -> dict[str, Any]:
    """Everything the manifest asserts about one canonical log, recomputed from the file."""
    path = REPO_ROOT / relative
    records = read_records(path)
    answers = [answer for record in records for answer in record.get("answers", {}).values()]
    by_type: dict[str, int] = {}
    for answer in answers:
        by_type[str(answer.get("type"))] = by_type.get(str(answer.get("type")), 0) + 1
    stamps = sorted(str(r["timestamp_utc"]) for r in records if r.get("timestamp_utc"))
    return {
        "records": len(records),
        "sha256": sha256_of(path),
        "schema_versions_present": sorted({int(r["schema_version"]) for r in records if "schema_version" in r}),
        "model_requested": sorted({str(r.get("model_requested")) for r in records}),
        "model_resolved": sorted({str(r.get("model_resolved")) for r in records}),
        "status": sorted({str(r.get("status")) for r in records}),
        "answers_by_type": dict(sorted(by_type.items())),
        "noul_answers_carrying_confidence": sum(
            1 for answer in answers if answer.get("type") == "noul" and "confidence" in answer
        ),
        "recorded_window_utc": [stamps[0], stamps[-1]] if stamps else [],
    }


def _experiments_with_records() -> list[str]:
    """**Registered** experiment names that have at least one canonical record.

    Intersected with the registry rather than counting every ``experiment`` value found in a log:
    the P3 records carry ``experiment: "P3_boundary_locus"``, and P3 is deliberately not a registry
    member (see ``docs/experiments/EXPERIMENT_REGISTRY.md``). Counting it here would turn the
    zero-unrun invariant into a statement about log contents instead of about the registry.
    """
    from .experiments import EXPERIMENTS

    names = set()
    for relative in CANONICAL_LOGS:
        for record in read_records(REPO_ROOT / relative):
            name = record.get("experiment")
            if name in EXPERIMENTS:
                names.add(name)
    return sorted(names)


def build_manifest() -> dict[str, Any]:
    """Compose the manifest from the repository. Every hash is computed, never transcribed."""
    from .experiments import EXPERIMENTS

    registered = sorted(EXPERIMENTS)
    with_records = _experiments_with_records()
    registry_doc = (
        (REPO_ROOT / "docs/experiments/EXPERIMENT_REGISTRY.md").read_text(encoding="utf-8")
    )
    freeze_doc = (REPO_ROOT / (EVIDENCE_DIR / "PUBLIC_EVIDENCE_FREEZE.md")).read_text(encoding="utf-8")

    return {
        "schema_version": 1,
        "release_version": FROZEN_VERSION,
        "planned_git_tag": PLANNED_GIT_TAG,
        "freeze_date": FREEZE_DATE,
        "project": {
            "name": "jev-test",
            "description": (
                "A measurement bench for TypeSafe's Jev model and the audit trail of what it "
                "measured. The product is the trustworthiness of the evidence, not a discovery."
            ),
            "repository": "https://github.com/Charlie-Wang-03/jev-test",
            "license": "MIT",
            "license_file": "LICENSE",
            "python_requires": ">=3.13",
        },
        "model_scope": {
            "model_requested_by_default": "jev-latest",
            "model_resolved_in_frozen_logs": "jev-1.13.0",
            "note": (
                "A requested alias can move; only the response says which model answered. Both "
                "fields are recorded on every record, and every statement in this release is "
                "scoped to the resolved model observed here."
            ),
        },
        "official_claim_snapshot": {
            "statement": (
                "TypeSafe official claim snapshot: as observed during P1 audit / accessed: 2026-09-22."
            ),
            "accessed": "2026-09-22",
            "registry_path": "docs/sources/TYPESAFE_OFFICIAL_SOURCES.md",
            "registry_sha256": EXPECTED_SOURCES_REGISTRY_SHA256,
            "registered_ids": 35,
            "tier1_documents": 28,
            "jev_version_where_stated": "jev-1.13 / jev-1.13.0",
            "note": (
                "'The official docs as audited on 2026-09-22' and 'the official docs today' are "
                "different objects. This release is audited against the dated snapshot only, and "
                "does not track later changes to TypeSafe's documentation."
            ),
        },
        "canonical_measurements": {
            relative: {**spec, **_log_facts(relative)} for relative, spec in CANONICAL_LOGS.items()
        },
        "evidence_documents": {
            path: {"sha256": sha256_of(REPO_ROOT / path), "class": "canonical_evidence"}
            for path in EVIDENCE_DOCUMENTS
        },
        "public_documentation": {
            path: {"sha256": sha256_of(REPO_ROOT / path), "class": "public_documentation"}
            for path in PUBLIC_DOCUMENTATION
        },
        "release_metadata": {
            path: {"sha256": sha256_of(REPO_ROOT / path)} for path in RELEASE_METADATA
        },
        "historical_commits": [
            {"sha": sha, "stage": stage, "type": kind, "what_it_is": what}
            for sha, stage, kind, what in HISTORICAL_COMMITS
        ],
        "historical_commit_note": (
            "SHAs are listed with what each one is. A commit type here is a claim about the diff, "
            "checkable with `git show`. The distinction that matters most: an ANALYSIS commit may "
            "change code that reads a log, and may never change the log."
        ),
        "known_errata": [
            {
                "id": "ERR-001",
                "status": "DOCUMENTED",
                "artifact": "docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md",
                "row": "TS-JEV-SEM-004",
                "incorrect_text": "42 of 42 Noul answers carry no confidence field",
                "corrected_value": "45 of 45 Noul answers carry no confidence field",
                "verdict_impact": "none",
                "correction_is_historical": True,
            },
            {
                "id": "ERR-002",
                "status": "RESOLVED",
                "resolved_in": "bdcb637",
                "artifact": "src/jev_lab/p3_boundary_locus.py at c0fc9cc",
                "defect": (
                    "GO-1 and GO-2 were evaluated as a single conjunction, so the pair "
                    "(GO-1 PASS, GO-2 FAIL) was unrepresentable."
                ),
                "measurement_changed": False,
                "threshold_or_rule_changed": False,
                "verdict_changed": False,
                "verdict_impact": "none",
                "current_head_is_affected": False,
            },
        ],
        "experiment_registry": {
            "registered": len(registered),
            "with_records": len(with_records),
            "unrun": sorted(set(registered) - set(with_records)),
            "registered_names": registered,
            "retired_before_release": [
                "00_model_info",
                "08_literal_reading",
                "09_numeric_limits",
                "10_state_length",
                "11_language_pair",
            ],
            "p3_in_registry": "07_instruction_precision" in registered and "p3_boundary_locus" in registered,
            "invariant": "ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS",
            "registry_document": "docs/experiments/EXPERIMENT_REGISTRY.md",
            "registry_document_states_invariant": "ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS"
            in registry_doc,
        },
        "scientific_state": {
            "state": SCIENTIFIC_STATE,
            "p3_verdict": P3_VERDICT,
            "inherited_verdicts": INHERITED_VERDICTS,
            "primary_null": (
                "The original instruction-precision effect could not be attributed to "
                "`instructions` or `criteria` alone under the preregistered one-payload 2x2 design."
            ),
            "non_claims": NON_CLAIMS,
            "state_documented_in": SCIENTIFIC_STATE_EVIDENCE,
            "freeze_document_states_state": SCIENTIFIC_STATE in freeze_doc,
        },
    }


def write_manifest(path: Path | None = None) -> Path:
    """Write the manifest as deterministic JSON: sorted keys, LF endings, trailing newline."""
    target = path or (REPO_ROOT / MANIFEST_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_manifest(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def _check_manifest_shape(manifest: dict[str, Any], failures: list[str]) -> None:
    """The manifest must describe exactly the release this module was written for."""
    for key, expected in (
        ("release_version", FROZEN_VERSION),
        ("planned_git_tag", PLANNED_GIT_TAG),
    ):
        if manifest.get(key) != expected:
            failures.append(f"manifest {key} is {manifest.get(key)!r}, expected {expected!r}")
    for key in (
        "canonical_measurements",
        "evidence_documents",
        "public_documentation",
        "release_metadata",
        "historical_commits",
        "known_errata",
        "experiment_registry",
        "scientific_state",
        "official_claim_snapshot",
        "model_scope",
        "project",
    ):
        if key not in manifest:
            failures.append(f"manifest is missing the required key {key!r}")


def _check_hashes(manifest: dict[str, Any], failures: list[str]) -> int:
    """Recompute every listed digest. This is the check the whole freeze rests on."""
    checked = 0
    for section in ("evidence_documents", "public_documentation", "release_metadata"):
        entries = manifest.get(section)
        if not isinstance(entries, dict):
            failures.append(f"manifest section {section!r} is missing or not an object")
            continue
        for relative, entry in sorted(entries.items()):
            path = REPO_ROOT / relative
            if not path.is_file():
                failures.append(f"{section}: {relative} is listed in the manifest but is not on disk")
                continue
            actual = sha256_of(path)
            expected = entry.get("sha256")
            checked += 1
            if actual != expected:
                failures.append(
                    f"{section}: {relative} hashes to {actual}, manifest says {expected}"
                )
    return checked


def _check_canonical_measurements(manifest: dict[str, Any], failures: list[str]) -> int:
    """Recompute both logs' facts, and the one errata value derived from them (ERR-001)."""
    measured = manifest.get("canonical_measurements")
    if not isinstance(measured, dict):
        failures.append("manifest is missing canonical_measurements")
        return 0
    for relative, entry in sorted(measured.items()):
        try:
            actual = _log_facts(relative)
        except (FileNotFoundError, ValueError) as error:
            failures.append(f"canonical log {relative}: {error}")
            continue
        for key in ("records", "sha256", "answers_by_type", "noul_answers_carrying_confidence"):
            if actual[key] != entry.get(key):
                failures.append(
                    f"canonical log {relative}: {key} is {actual[key]!r}, manifest says {entry.get(key)!r}"
                )
        if actual["model_resolved"] != entry.get("model_resolved"):
            failures.append(
                f"canonical log {relative}: model_resolved is {actual['model_resolved']!r}, "
                f"manifest says {entry.get('model_resolved')!r}"
            )
    # ERR-001 carries a corrected count. If the log ever disagreed with it, the erratum would
    # become a second error rather than a correction.
    core = measured.get("results/usage.jsonl", {})
    noul = core.get("answers_by_type", {}).get("noul")
    if noul is not None and core.get("noul_answers_carrying_confidence") not in (0, None):
        failures.append(
            f"ERR-001 is invalidated: {core.get('noul_answers_carrying_confidence')} Noul answers "
            f"now carry a confidence field, so '45 of 45' no longer holds"
        )
    if noul is not None and noul != 45:
        failures.append(f"ERR-001 states 45 of 45 Noul answers; the core log now has {noul}")
    return len(measured)


def _check_registry(manifest: dict[str, Any], failures: list[str]) -> int:
    """`ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS`, checked against the code and the logs."""
    from .experiments import EXPERIMENTS

    registered = sorted(EXPERIMENTS)
    with_records = _experiments_with_records()
    unrun = sorted(set(registered) - set(with_records))
    if unrun:
        failures.append(
            f"the registry has {len(unrun)} unrun experiment(s): {unrun} — "
            "a design is run or retired, never parked"
        )
    entry = manifest.get("experiment_registry", {})
    for key, actual in (("registered", len(registered)), ("with_records", len(with_records))):
        if entry.get(key) != actual:
            failures.append(
                f"experiment_registry.{key} is {actual}, manifest says {entry.get(key)!r}"
            )
    if entry.get("unrun") not in ([], None):
        failures.append(f"manifest records unrun experiments: {entry['unrun']}")
    for name in entry.get("retired_before_release", []):
        if name in EXPERIMENTS:
            failures.append(f"{name} is recorded as retired but is still in the registry")
    return len(with_records)


def _check_release_metadata(manifest: dict[str, Any], failures: list[str]) -> None:
    """The license, the version and the citation metadata must all say the same thing."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if f'version = "{FROZEN_VERSION}"' not in pyproject:
        failures.append(f"pyproject.toml does not declare version {FROZEN_VERSION!r}")
    license_path = REPO_ROOT / "LICENSE"
    if not license_path.is_file():
        failures.append("no LICENSE file at the repository root")
    else:
        licence = license_path.read_text(encoding="utf-8")
        if licence.splitlines()[0].strip() != "MIT License":
            failures.append("LICENSE does not begin with the MIT text")
        if 'THE SOFTWARE IS PROVIDED "AS IS"' not in licence:
            failures.append("LICENSE is missing the MIT warranty disclaimer")
    citation = REPO_ROOT / "CITATION.cff"
    if not citation.is_file():
        failures.append("no CITATION.cff")
    else:
        text = citation.read_text(encoding="utf-8")
        for needle in (f"version: {FROZEN_VERSION}", "license: MIT", "cff-version:"):
            if needle not in text:
                failures.append(f"CITATION.cff is missing {needle!r}")
        if "doi" in text.lower():
            failures.append("CITATION.cff claims a DOI; this release has none")
    if manifest.get("project", {}).get("license") != "MIT":
        failures.append("manifest does not record the license as MIT")


def _check_scientific_state(manifest: dict[str, Any], failures: list[str]) -> None:
    """The inherited verdicts must still be the ones the frozen documents state."""
    path = REPO_ROOT / SCIENTIFIC_STATE_EVIDENCE
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if SCIENTIFIC_STATE not in text:
        failures.append(f"{SCIENTIFIC_STATE_EVIDENCE} no longer states {SCIENTIFIC_STATE}")

    p3_result = REPO_ROOT / "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md"
    p3_text = p3_result.read_text(encoding="utf-8") if p3_result.is_file() else ""
    if P3_VERDICT not in p3_text:
        failures.append(f"the P3 result document no longer states {P3_VERDICT}")

    freeze_doc = REPO_ROOT / (EVIDENCE_DIR / "PUBLIC_EVIDENCE_FREEZE.md")
    freeze_text = freeze_doc.read_text(encoding="utf-8") if freeze_doc.is_file() else ""
    for marker in [SCIENTIFIC_STATE, P3_VERDICT, *INHERITED_VERDICTS, *NON_CLAIMS]:
        if marker not in freeze_text:
            failures.append(f"PUBLIC_EVIDENCE_FREEZE.md does not state {marker}")

    prereg = REPO_ROOT / "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md"
    if not prereg.is_file():
        failures.append("the P3 preregistration is missing")

    for verdict in INHERITED_VERDICTS:
        if not any(verdict in (REPO_ROOT / p).read_text(encoding="utf-8") for p in EVIDENCE_DOCUMENTS):
            failures.append(f"no frozen evidence document states {verdict}")


def verify_manifest(manifest_path: Path | None = None, echo=print) -> int:
    """Re-check every claim in the freeze manifest. Returns 0 on success, 1 on any mismatch."""
    target = manifest_path or (REPO_ROOT / MANIFEST_PATH)
    failures: list[str] = []
    if not target.is_file():
        echo(f"FAIL  no freeze manifest at {target.as_posix()}")
        echo("      run: uv run python -m jev_lab.evidence_freeze build")
        return 1

    try:
        manifest = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        echo(f"FAIL  the freeze manifest is not valid JSON: {error}")
        return 1

    _check_manifest_shape(manifest, failures)
    files = _check_hashes(manifest, failures)
    logs = _check_canonical_measurements(manifest, failures)
    _check_registry(manifest, failures)
    _check_release_metadata(manifest, failures)
    _check_scientific_state(manifest, failures)

    if failures:
        echo(f"FAIL  {len(failures)} problem(s) in the v{FROZEN_VERSION} evidence freeze:")
        for failure in failures:
            echo(f"  - {failure}")
        echo(
            "\nThe frozen evidence has moved. Do not edit docs/evidence/"
            f"v{FROZEN_VERSION}/ to match: a frozen release is immutable. New evidence needs a new "
            "version directory (e.g. docs/evidence/v0.2.0/) that says what it supersedes."
        )
        return 1

    core = manifest["canonical_measurements"]["results/usage.jsonl"]
    p3 = manifest["canonical_measurements"]["results/p3_boundary_locus/usage.jsonl"]
    echo(f"PASS  evidence freeze v{FROZEN_VERSION} ({PLANNED_GIT_TAG}) verified")
    echo(f"  files hashed            {files}")
    echo(f"  canonical logs          {logs} ({core['records']} core + {p3['records']} P3 records)")
    echo(f"  core log sha256         {core['sha256']}")
    echo(f"  p3 log sha256           {p3['sha256']}")
    echo(f"  registry                {manifest['experiment_registry']['registered']} designs, 0 unrun")
    echo(f"  scientific state        {manifest['scientific_state']['state']}")
    echo(f"  p3 verdict              {manifest['scientific_state']['p3_verdict']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m jev_lab.evidence_freeze {verify,build}``. Strictly offline."""
    parser = argparse.ArgumentParser(prog="jev_lab.evidence_freeze", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("verify", help="re-check the frozen evidence manifest from disk (default)")
    sub.add_parser("build", help=f"regenerate {MANIFEST_PATH.as_posix()} from the repository")
    args = parser.parse_args(argv)

    if args.command == "build":
        target = write_manifest()
        print(f"wrote {target.as_posix()}")
        print("Re-check it with: uv run python -m jev_lab.evidence_freeze verify")
        return 0
    return verify_manifest()


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
