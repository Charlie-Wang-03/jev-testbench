"""The frozen evidence manifest for release ``v0.1.0``, and the offline check that it still holds.

A freeze is only worth citing if something can prove it has not moved. This module is that
something: it builds ``docs/evidence/v0.1.0/evidence-manifest.json`` from the repository, and it
re-verifies every claim in that manifest.

Three commands, all strictly offline::

    uv run python -m jev_lab.evidence_freeze verify [TAG]    # verify the released tree (default)
    uv run python -m jev_lab.evidence_freeze verify-current  # drift report against this worktree
    uv run python -m jev_lab.evidence_freeze build           # regenerate the manifest

**A release is verified against its own Git tree, not against the working tree.** ``verify v0.1.0``
reads the manifest at ``v0.1.0:docs/evidence/v0.1.0/evidence-manifest.json`` and hashes every
artifact it lists at ``v0.1.0:<path>``, through ``git cat-file``. That single change is what makes a
frozen release immutable *and* lets ``main`` keep moving: editing a README, a guide, or even the
working-tree copy of a frozen manifest changes the current tree, not the tagged one, so it cannot
invalidate a citation.

The two modes answer different questions and are deliberately not one command. ``verify`` asks "is
the published release still exactly what was published?"; ``verify-current`` asks "does this working
tree still equal the release tree?". On any post-release branch the second answer is honestly *no*,
so its non-zero exit is a drift report rather than a release-integrity failure -- the output says so
in as many words, because a red exit that means "expected" is a bug report waiting to happen.

``verify`` opens no socket, spawns no network call and never needs a credential. It reads the
manifest, recomputes the SHA-256 of every file the manifest lists, re-counts both canonical logs,
and re-checks the release's structural invariants. Any mismatch is a non-zero exit.

**Why this is not a framework.** The *tag* is a parameter, because a future ``v0.2.0`` needs to be
verifiable by the same code without this module having to be rewritten first. Everything else --
which sections a release has, which documents count as evidence, which invariants hold -- is
hard-coded, because a generic freeze engine would have to discover what matters and what each
artifact promises, and that judgment is the actual content of a freeze. Keeping it here keeps it
reviewable.

**What CI does with it.** Every push runs ``verify v0.1.0``, which reads the tag. Editing a canonical
log, an audit or the preregistration therefore fails the build -- as it should, because those are
the artifacts a citation depends on. Editing a README or a guide does not, and that is the point of
this design: presentation may be reworded on ``main`` without a new release, while evidence may not.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of(path: Path) -> str:
    """SHA-256 of a file's bytes. Bytes, not text: line endings are part of the identity here."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_records(data: bytes, where: str) -> list[dict[str, Any]]:
    """Parse a canonical JSONL log. Blank lines are skipped; anything else must be an object."""
    records = []
    for number, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{where} line {number} is not JSON: {error}") from error
    return records


def read_records(path: Path) -> list[dict[str, Any]]:
    """Parse a canonical JSONL log from the filesystem."""
    if not path.is_file():
        raise FileNotFoundError(path)
    return _parse_records(path.read_bytes(), path.as_posix())


# ---------------------------------------------------------------------------
# Where a verification reads from
# ---------------------------------------------------------------------------
#
# Every check below is a statement of the form "this artifact still hashes to what the manifest
# says". Which artifacts that is, is fixed. *Where they are read from* is not, and that is the one
# thing this release had to get right: a published release is the tree its tag points at, not
# whatever the working tree happens to contain today.


class ReleaseTagNotFound(RuntimeError):
    """The tag naming a release is not in this clone. Fail closed; never fetch."""


class ReleaseObjectMissing(RuntimeError):
    """The tag resolves, but an object the manifest needs is not in the object store."""


class EvidenceSource(Protocol):
    """Somewhere the frozen artifacts can be read from: a Git tree, or the working tree."""

    label: str

    def read_bytes(self, relative: str) -> bytes: ...
    def sha256(self, relative: str) -> str: ...
    def is_file(self, relative: str) -> bool: ...
    def registry_names(self) -> list[str]: ...


class WorktreeSource:
    """Reads the working tree. Answers "what does the checkout in front of me currently say?".

    This is the *current-tree* source. It is the right one for ``build`` -- you compose a new
    manifest from the tree you are about to freeze -- and for ``verify-current``, whose whole job is
    to report how far the working tree has drifted from a release. It is the wrong one for
    verifying a published release, and that was the bug this module used to have.
    """

    def __init__(self, root: Path = REPO_ROOT) -> None:
        self.root = root
        self.label = f"working tree at {root.as_posix()}"

    def read_bytes(self, relative: str) -> bytes:
        return (self.root / relative).read_bytes()

    def sha256(self, relative: str) -> str:
        return sha256_bytes(self.read_bytes(relative))

    def is_file(self, relative: str) -> bool:
        return (self.root / relative).is_file()

    def registry_names(self) -> list[str]:
        """The registry this tree defines, read the same way the tag source reads its own.

        Both sources parse ``experiments.py`` rather than importing it, so that ``build`` composes
        the registry section identically whichever tree it is pointed at -- and so that composing a
        manifest never executes the code it is describing.
        """
        return registry_names_from_source(
            (self.root / "src/jev_lab/experiments.py").read_text(encoding="utf-8")
        )

    def close(self) -> None:
        return None

    def __enter__(self) -> "WorktreeSource":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class GitTreeSource:
    """Reads a release's artifacts out of the Git object store, at a tag.

    Nothing is checked out and no working-tree file is touched: ``git ls-tree`` maps every path in
    the tagged tree to its blob id, and one long-lived ``git cat-file --batch`` serves the bytes.
    No network call is made, so this works on a plane and in CI alike -- and it cannot be fooled by
    a local edit, because the bytes it hashes are the ones the tag commits to.

    ``release:`` paths that are absent from the tree read as missing rather than raising, so a
    manifest listing a file the release never had is reported as a failure and not a traceback.
    """

    def __init__(self, tag: str, repo_root: Path = REPO_ROOT) -> None:
        self.tag = tag
        self.repo_root = repo_root
        self.commit = self._resolve()
        self._entries: dict[str, str] | None = None
        self._batch: subprocess.Popen[bytes] | None = None
        self._cache: dict[str, bytes] = {}

    # -- git plumbing ------------------------------------------------------

    def _git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", *args], cwd=self.repo_root, capture_output=True, check=False
        )

    def _resolve(self) -> str:
        """Peel the tag to the commit it names. ``^{commit}`` works for annotated and light tags."""
        proc = self._git("rev-parse", "--verify", "--quiet", f"refs/tags/{self.tag}^{{commit}}")
        sha = proc.stdout.decode("ascii", "replace").strip()
        if proc.returncode != 0 or not sha:
            raise ReleaseTagNotFound(f"no tag {self.tag!r} in {self.repo_root.as_posix()}")
        return sha

    def _tree(self) -> dict[str, str]:
        if self._entries is None:
            proc = self._git("ls-tree", "-r", "-z", self.commit)
            if proc.returncode != 0:
                raise ReleaseObjectMissing(
                    f"cannot list the tree of {self.tag}: {proc.stderr.decode('utf-8', 'replace').strip()}"
                )
            entries: dict[str, str] = {}
            for chunk in proc.stdout.split(b"\0"):
                if not chunk:
                    continue
                meta, _, path = chunk.partition(b"\t")
                fields = meta.split()
                if len(fields) == 3 and fields[1] == b"blob":
                    entries[path.decode("utf-8")] = fields[2].decode("ascii")
            self._entries = entries
        return self._entries

    def _blob(self, sha: str) -> bytes:
        if self._batch is None:
            self._batch = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=self.repo_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        assert self._batch.stdin is not None and self._batch.stdout is not None
        self._batch.stdin.write(f"{sha}\n".encode("ascii"))
        self._batch.stdin.flush()
        header = self._batch.stdout.readline()
        fields = header.split()
        if len(fields) < 3:
            raise ReleaseObjectMissing(
                f"blob {sha} is missing from {self.repo_root.as_posix()} -- "
                "this is usually a shallow or partial clone; `git fetch --tags` should fix it"
            )
        size = int(fields[2])
        data = self._batch.stdout.read(size)
        self._batch.stdout.read(1)  # the newline git writes after the payload
        return data

    # -- EvidenceSource ----------------------------------------------------

    @property
    def label(self) -> str:
        return f"git tag {self.tag} (commit {self.commit[:7]})"

    def read_bytes(self, relative: str) -> bytes:
        if relative not in self._cache:
            sha = self._tree().get(relative)
            if sha is None:
                raise FileNotFoundError(f"{relative} is not in the {self.tag} tree")
            self._cache[relative] = self._blob(sha)
        return self._cache[relative]

    def sha256(self, relative: str) -> str:
        return sha256_bytes(self.read_bytes(relative))

    def is_file(self, relative: str) -> bool:
        return relative in self._tree()

    def registry_names(self) -> list[str]:
        """The names the release's *own* registry defined, parsed but never executed."""
        return registry_names_from_source(
            self.read_bytes("src/jev_lab/experiments.py").decode("utf-8")
        )

    def close(self) -> None:
        if self._batch is not None:
            if self._batch.stdin is not None:
                self._batch.stdin.close()
            self._batch.wait(timeout=10)
            self._batch = None

    def __enter__(self) -> "GitTreeSource":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def registry_names_from_source(text: str) -> list[str]:
    """Extract the keys of ``EXPERIMENTS`` from ``experiments.py`` by parsing, never importing.

    A release's registry is whatever its own tree said it was. Importing today's module would answer
    a different question -- what the registry says *now* -- and it would execute code out of a tree
    that is supposed to be inert evidence.
    """
    for node in ast.parse(text).body:
        if isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        elif isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        else:
            continue
        if not any(isinstance(t, ast.Name) and t.id == "EXPERIMENTS" for t in targets):
            continue
        if not isinstance(value, ast.Dict):
            continue
        return sorted(
            key.value
            for key in value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        )
    raise ValueError("no EXPERIMENTS mapping found in src/jev_lab/experiments.py")


@dataclass(frozen=True)
class Release:
    """Which release is under verification, and where its artifacts are expected to live."""

    tag: str
    version: str
    manifest_path: Path
    evidence_dir: Path

    @classmethod
    def for_tag(cls, tag: str) -> "Release":
        version = tag[1:] if tag.startswith("v") else tag
        if not version or not all(part.isdigit() for part in version.split(".")):
            raise ValueError(f"{tag!r} is not a release tag of the form v<major>.<minor>.<patch>")
        directory = Path("docs/evidence") / tag
        return cls(tag, version, directory / "evidence-manifest.json", directory)

    @classmethod
    def frozen(cls) -> "Release":
        """The release this module's constants describe, for checks with no tag to read."""
        return cls(PLANNED_GIT_TAG, FROZEN_VERSION, MANIFEST_PATH, EVIDENCE_DIR)

    def next_version(self) -> str:
        """The version a superseding release would plausibly take. Used only to name an example."""
        parts = self.version.split(".")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            return f"{parts[0]}.{int(parts[1]) + 1}.0"
        return f"{self.version}.next"


def source_for_tag(tag: str, echo=print, repo_root: Path = REPO_ROOT) -> GitTreeSource | None:
    """Open a tagged tree, or report why it could not be opened. Never fetches."""
    try:
        return GitTreeSource(tag, repo_root=repo_root)
    except ReleaseTagNotFound as error:
        echo(f"FAIL  {error}")
        echo(
            "      this verifier is offline by design and will not fetch. If the tag exists on the\n"
            "      remote, `git fetch --tags` brings it in; a shallow clone needs it too."
        )
        return None


def _log_facts(relative: str, source: EvidenceSource) -> dict[str, Any]:
    """Everything the manifest asserts about one canonical log, recomputed from the source."""
    records = _parse_records(source.read_bytes(relative), relative)
    answers = [answer for record in records for answer in record.get("answers", {}).values()]
    by_type: dict[str, int] = {}
    for answer in answers:
        by_type[str(answer.get("type"))] = by_type.get(str(answer.get("type")), 0) + 1
    stamps = sorted(str(r["timestamp_utc"]) for r in records if r.get("timestamp_utc"))
    return {
        "records": len(records),
        "sha256": source.sha256(relative),
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


def _experiments_with_records(source: EvidenceSource, registered: Sequence[str]) -> list[str]:
    """**Registered** experiment names that have at least one canonical record.

    Intersected with the registry rather than counting every ``experiment`` value found in a log:
    the P3 records carry ``experiment: "P3_boundary_locus"``, and P3 is deliberately not a registry
    member (see ``docs/experiments/EXPERIMENT_REGISTRY.md``). Counting it here would turn the
    zero-unrun invariant into a statement about log contents instead of about the registry.
    """
    known = set(registered)
    names: set[str] = set()
    for relative in CANONICAL_LOGS:
        if not source.is_file(relative):
            continue
        for record in _parse_records(source.read_bytes(relative), relative):
            name = record.get("experiment")
            if name in known:
                names.add(str(name))
    return sorted(names)


def project_identity(source: EvidenceSource) -> tuple[str, str]:
    """The distribution name and repository URL **as the source tree declared them**.

    Project identity is a per-release fact, not a constant of this module. ``v0.1.0`` was frozen
    under the name ``jev-test``; the project was renamed ``jev-testbench`` afterwards, and a
    release's own tree is the only authority on what that release called itself. Reading the two
    fields out of ``pyproject.toml`` is what lets ``build_manifest`` pointed at the ``v0.1.0`` tag
    still reproduce the committed manifest after ``main`` has moved on -- the same reason
    ``_check_release_metadata`` reads the version out of the source rather than comparing it
    against today's.

    Hard-coding today's name here instead would make the builder describe a historical release with
    a name its tree never carried, and the committed manifest could no longer be rebuilt from the
    release alone.
    """
    if not source.is_file("pyproject.toml"):
        raise ValueError(f"no pyproject.toml in {source.label}; cannot read the project identity")
    project = tomllib.loads(source.read_bytes("pyproject.toml").decode("utf-8")).get("project", {})
    name = project.get("name")
    urls = project.get("urls", {})
    repository = urls.get("Repository") or urls.get("Homepage")
    if not name or not repository:
        raise ValueError(
            f"pyproject.toml in {source.label} declares no project.name and/or no "
            "project.urls Repository or Homepage; the manifest's project section is built from "
            "those two fields, and an absent one is not a value to guess"
        )
    return name, repository


def build_manifest(
    source: EvidenceSource | None = None, release: Release | None = None
) -> dict[str, Any]:
    """Compose the manifest from a source. Every hash is computed, never transcribed.

    With the default source this composes today's freeze from the working tree. Given a
    ``GitTreeSource`` it recomposes an *already published* release from its own tag -- which is how
    the test suite checks that the committed manifest is what the code builds from the release,
    rather than merely that it verifies against itself.

    Project identity is read from whichever tree ``source`` names, so recomposing a past release
    reproduces the name that release was published under rather than today's.
    """
    if source is None:
        source = WorktreeSource()
    if release is None:
        release = Release.for_tag(source.tag) if isinstance(source, GitTreeSource) else Release.frozen()

    registered = source.registry_names()
    with_records = _experiments_with_records(source, registered)
    registry_doc = source.read_bytes("docs/experiments/EXPERIMENT_REGISTRY.md").decode("utf-8")
    freeze_doc = source.read_bytes(
        (release.evidence_dir / "PUBLIC_EVIDENCE_FREEZE.md").as_posix()
    ).decode("utf-8")
    # `name` and `repository` are per-release facts read from the tree being described. The other
    # three are properties of the scientific artifact and are the same for every release of it.
    name, repository = project_identity(source)

    return {
        "schema_version": 1,
        "release_version": release.version,
        "planned_git_tag": release.tag,
        "freeze_date": FREEZE_DATE,
        "project": {
            "name": name,
            "description": (
                "A measurement bench for TypeSafe's Jev model and the audit trail of what it "
                "measured. The product is the trustworthiness of the evidence, not a discovery."
            ),
            "repository": repository,
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
            relative: {**spec, **_log_facts(relative, source)}
            for relative, spec in CANONICAL_LOGS.items()
        },
        "evidence_documents": {
            path: {"sha256": source.sha256(path), "class": "canonical_evidence"}
            for path in EVIDENCE_DOCUMENTS
        },
        "public_documentation": {
            path: {"sha256": source.sha256(path), "class": "public_documentation"}
            for path in PUBLIC_DOCUMENTATION
        },
        "release_metadata": {
            path: {"sha256": source.sha256(path)} for path in RELEASE_METADATA
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


def write_manifest(path: Path | None = None, source: EvidenceSource | None = None) -> Path:
    """Write the manifest as deterministic JSON: sorted keys, LF endings, trailing newline."""
    target = path or (REPO_ROOT / MANIFEST_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_manifest(source), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def _check_manifest_shape(manifest: dict[str, Any], failures: list[str], release: Release) -> None:
    """The manifest must describe exactly the release whose tree it was read out of."""
    for key, expected in (
        ("release_version", release.version),
        ("planned_git_tag", release.tag),
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


def _check_hashes(manifest: dict[str, Any], failures: list[str], source: EvidenceSource) -> int:
    """Recompute every listed digest. This is the check the whole freeze rests on."""
    checked = 0
    for section in ("evidence_documents", "public_documentation", "release_metadata"):
        entries = manifest.get(section)
        if not isinstance(entries, dict):
            failures.append(f"manifest section {section!r} is missing or not an object")
            continue
        for relative, entry in sorted(entries.items()):
            if not source.is_file(relative):
                failures.append(
                    f"{section}: {relative} is listed in the manifest but is not in {source.label}"
                )
                continue
            try:
                actual = source.sha256(relative)
            except (OSError, ReleaseObjectMissing) as error:
                failures.append(f"{section}: {relative} could not be read: {error}")
                continue
            expected = entry.get("sha256")
            checked += 1
            if actual != expected:
                failures.append(
                    f"{section}: {relative} hashes to {actual}, manifest says {expected}"
                )
    return checked


def _check_canonical_measurements(
    manifest: dict[str, Any], failures: list[str], source: EvidenceSource
) -> int:
    """Recompute both logs' facts, and the one errata value derived from them (ERR-001)."""
    measured = manifest.get("canonical_measurements")
    if not isinstance(measured, dict):
        failures.append("manifest is missing canonical_measurements")
        return 0
    for relative, entry in sorted(measured.items()):
        try:
            actual = _log_facts(relative, source)
        except (FileNotFoundError, ReleaseObjectMissing, ValueError) as error:
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


def _check_registry(
    manifest: dict[str, Any], failures: list[str], source: EvidenceSource
) -> int:
    """`ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS`, checked against the registry and the logs.

    Both sides are read from the *same* source. For a released tree that means the registry the
    release's own ``experiments.py`` defined, intersected with the release's own logs -- a closed
    statement about the release. Reading today's registry instead would make a future ``main`` that
    adds an experiment retroactively break a past release, which is precisely the failure this
    module was fixed for.
    """
    registered = source.registry_names()
    with_records = _experiments_with_records(source, registered)
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
    if entry.get("registered_names") not in (registered, None):
        failures.append(
            f"experiment_registry.registered_names is {entry.get('registered_names')!r}, "
            f"the registry in {source.label} defines {registered!r}"
        )
    if entry.get("unrun") not in ([], None):
        failures.append(f"manifest records unrun experiments: {entry['unrun']}")
    for name in entry.get("retired_before_release", []):
        if name in registered:
            failures.append(f"{name} is recorded as retired but is still in the registry")
    return len(with_records)


def _read_text(source: EvidenceSource, relative: str) -> str:
    """Text at a path, or the empty string when the path is not there. Missing is reported, not raised."""
    if not source.is_file(relative):
        return ""
    return source.read_bytes(relative).decode("utf-8")


def _check_release_metadata(
    manifest: dict[str, Any], failures: list[str], source: EvidenceSource, release: Release
) -> None:
    """The license, the version and the citation metadata must all say the same thing.

    Read from the source, not from the working tree: a future ``main`` that bumps ``pyproject.toml``
    to the next version must not make the *previous* release look inconsistent with itself.
    """
    if not source.is_file("pyproject.toml"):
        failures.append(f"no pyproject.toml in {source.label}")
    else:
        if f'version = "{release.version}"' not in _read_text(source, "pyproject.toml"):
            failures.append(f"pyproject.toml does not declare version {release.version!r}")
        # The name a release records is the name its own tree declared. A mismatch is not
        # cosmetic: it means the manifest describes a project the release never was, which is
        # exactly what a hard-coded identity in the builder produces once the project is renamed
        # on `main`. A tree that declares no name at all is reported rather than raised -- a
        # damaged release is a verdict, and a traceback is not one.
        try:
            declared_name, _ = project_identity(source)
        except ValueError as error:
            failures.append(str(error))
        else:
            recorded_name = manifest.get("project", {}).get("name")
            if recorded_name != declared_name:
                failures.append(
                    f"manifest records project name {recorded_name!r}, but pyproject.toml in "
                    f"{source.label} declares {declared_name!r}"
                )

    if not source.is_file("LICENSE"):
        failures.append("no LICENSE file at the repository root")
    else:
        licence = _read_text(source, "LICENSE")
        if licence.splitlines()[0].strip() != "MIT License":
            failures.append("LICENSE does not begin with the MIT text")
        if 'THE SOFTWARE IS PROVIDED "AS IS"' not in licence:
            failures.append("LICENSE is missing the MIT warranty disclaimer")

    if not source.is_file("CITATION.cff"):
        failures.append("no CITATION.cff")
    else:
        text = _read_text(source, "CITATION.cff")
        for needle in (f"version: {release.version}", "license: MIT", "cff-version:"):
            if needle not in text:
                failures.append(f"CITATION.cff is missing {needle!r}")
        if "doi" in text.lower():
            failures.append("CITATION.cff claims a DOI; this release has none")
    if manifest.get("project", {}).get("license") != "MIT":
        failures.append("manifest does not record the license as MIT")


def _check_scientific_state(
    manifest: dict[str, Any], failures: list[str], source: EvidenceSource, release: Release
) -> None:
    """The inherited verdicts must still be the ones the frozen documents state."""
    text = _read_text(source, SCIENTIFIC_STATE_EVIDENCE)
    if SCIENTIFIC_STATE not in text:
        failures.append(
            f"{SCIENTIFIC_STATE_EVIDENCE} (in {source.label}) no longer states {SCIENTIFIC_STATE}"
        )

    p3_text = _read_text(source, "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md")
    if P3_VERDICT not in p3_text:
        failures.append(f"the P3 result document no longer states {P3_VERDICT}")

    freeze_text = _read_text(source, (release.evidence_dir / "PUBLIC_EVIDENCE_FREEZE.md").as_posix())
    for marker in [SCIENTIFIC_STATE, P3_VERDICT, *INHERITED_VERDICTS, *NON_CLAIMS]:
        if marker not in freeze_text:
            failures.append(f"PUBLIC_EVIDENCE_FREEZE.md does not state {marker}")

    if not source.is_file("docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md"):
        failures.append("the P3 preregistration is missing")

    # The set of documents that count as evidence is the manifest's own declaration, so this stays
    # a statement about the release rather than about whatever this module's constants list today.
    declared = list(manifest.get("evidence_documents", {}))
    for verdict in INHERITED_VERDICTS:
        if not any(verdict in _read_text(source, path) for path in declared):
            failures.append(f"no frozen evidence document states {verdict}")


def verify_manifest(
    manifest_path: Path | None = None,
    echo=print,
    source: EvidenceSource | None = None,
    release: Release | None = None,
) -> int:
    """Re-check every claim in a freeze manifest. Returns 0 on success, 1 on any mismatch.

    ``source`` decides what the manifest is checked *against*, and it is the whole point of this
    module's shape. A ``GitTreeSource`` verifies a published release against its own tag -- the
    historical question. The default ``WorktreeSource`` asks whether the checkout in front of you
    still equals the release -- the current-tree question. They are different questions with
    different right answers, so they are different calls rather than one call with a flag.
    """
    if manifest_path is not None and isinstance(source, GitTreeSource):
        echo("FAIL  an explicit manifest path cannot be combined with a tagged source")
        return 1
    if source is None:
        source = WorktreeSource()
    historical = isinstance(source, GitTreeSource)
    if release is None:
        release = Release.for_tag(source.tag) if historical else Release.frozen()

    failures: list[str] = []
    if manifest_path is not None:
        try:
            raw = manifest_path.read_bytes()
        except OSError:
            echo(f"FAIL  no freeze manifest at {manifest_path.as_posix()}")
            echo("      run: uv run python -m jev_lab.evidence_freeze build")
            return 1
        where = manifest_path.as_posix()
    else:
        relative = release.manifest_path.as_posix()
        where = f"{release.tag}:{relative}" if historical else relative
        if not source.is_file(relative):
            echo(f"FAIL  no freeze manifest at {where}")
            if not historical:
                echo("      run: uv run python -m jev_lab.evidence_freeze build")
            return 1
        raw = source.read_bytes(relative)

    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        echo(f"FAIL  the freeze manifest is not valid JSON: {error}")
        return 1

    _check_manifest_shape(manifest, failures, release)
    files = _check_hashes(manifest, failures, source)
    logs = _check_canonical_measurements(manifest, failures, source)
    _check_registry(manifest, failures, source)
    _check_release_metadata(manifest, failures, source, release)
    _check_scientific_state(manifest, failures, source, release)

    label = f"v{release.version}"
    if failures:
        echo(f"FAIL  {len(failures)} problem(s) in the {label} evidence freeze:")
        for failure in failures:
            echo(f"  - {failure}")
        echo(f"\n  checked against: {source.label}")
        if historical:
            echo(
                f"The tree at {release.tag} does not match the manifest it carries. Do not edit\n"
                f"docs/evidence/{release.tag}/ to match, and do not move the tag: both are what a\n"
                "citation points at. A release that is genuinely wrong is superseded by a new\n"
                "version directory, never repaired in place."
            )
        else:
            echo(
                f"The working tree differs from the {label} release tree.\n\n"
                "  A README, an index or a guide may be reworded after a release. Presentation is\n"
                "  allowed to move on, and this exit is then a report of what moved rather than a\n"
                "  defect.\n\n"
                "  A canonical log, an audit, the preregistration or ERRATA may not. Those are what\n"
                "  a citation depends on. If a failure above names one of them, the fix is a new\n"
                f"  version directory (e.g. docs/evidence/v{release.next_version()}/) -- never an\n"
                "  edit to the frozen release, and never a regenerated manifest, which would leave\n"
                "  the release describing something it never said.\n\n"
                f"  The {label} directory is immutable. A new release supersedes it; nothing\n"
                "  rewrites it.\n\n"
                "Verify the release itself, from its tag, with:\n"
                f"    uv run python -m jev_lab.evidence_freeze verify {release.tag}"
            )
        return 1

    core = manifest.get("canonical_measurements", {}).get("results/usage.jsonl", {})
    p3 = manifest.get("canonical_measurements", {}).get("results/p3_boundary_locus/usage.jsonl", {})
    heading = (
        f"PASS  Verified historical evidence release: {release.tag}"
        if historical
        else f"PASS  the working tree matches the {label} release tree"
    )
    echo(heading)
    echo(f"  source                  {source.label}")
    echo(f"  manifest                {where}")
    echo(f"  files hashed            {files}")
    echo(
        f"  canonical logs          {logs} "
        f"({core.get('records')} core + {p3.get('records')} P3 records)"
    )
    echo(f"  core log sha256         {core.get('sha256')}")
    echo(f"  p3 log sha256           {p3.get('sha256')}")
    echo(f"  registry                {manifest['experiment_registry']['registered']} designs, 0 unrun")
    echo(f"  scientific state        {manifest['scientific_state']['state']}")
    echo(f"  p3 verdict              {manifest['scientific_state']['p3_verdict']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m jev_lab.evidence_freeze {verify,verify-current,build}``. Strictly offline."""
    parser = argparse.ArgumentParser(prog="jev_lab.evidence_freeze", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    verify_parser = sub.add_parser(
        "verify", help="verify a released tree, read from its Git tag (default)"
    )
    verify_parser.add_argument(
        "tag",
        nargs="?",
        default=PLANNED_GIT_TAG,
        help=f"the release tag to verify (default: {PLANNED_GIT_TAG})",
    )
    sub.add_parser(
        "verify-current",
        help="report how the working tree differs from a frozen release; not a release check",
    )
    sub.add_parser("build", help=f"regenerate {MANIFEST_PATH.as_posix()} from the repository")
    args = parser.parse_args(argv)

    if args.command == "build":
        target = write_manifest()
        print(f"wrote {target.as_posix()}")
        print("Re-check it with: uv run python -m jev_lab.evidence_freeze verify")
        return 0

    if args.command == "verify-current":
        return verify_manifest(source=WorktreeSource())

    tag = getattr(args, "tag", PLANNED_GIT_TAG)
    try:
        release = Release.for_tag(tag)
    except ValueError as error:
        print(f"FAIL  {error}")
        return 1
    source = source_for_tag(tag)
    if source is None:
        return 1
    with source:
        return verify_manifest(source=source, release=release)


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
