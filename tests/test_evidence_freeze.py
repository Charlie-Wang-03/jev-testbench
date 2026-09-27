"""The frozen evidence release must verify, and the verifier must actually be able to fail.

A verifier that has only ever been observed passing is not evidence of anything. So the tests below
do three separate jobs: they assert that the shipped release verifies, they assert that a
deliberately damaged manifest does **not**, and -- in ``TestReleaseVerification`` -- they assert the
version-lifecycle property that the first two cannot express: that a release is verified against
its own Git tree and keeps verifying after the working tree has moved on.

Everything here is offline. The suite blocks sockets outright (see ``conftest.py``), so a test that
reached the network would fail rather than pass quietly. The Git plumbing these tests use is local
``git`` on a temporary repository; nothing is fetched.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from jev_lab import evidence_freeze as ef

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / ef.MANIFEST_PATH

# Every one of these is a way the freeze could silently rot. Each is named for the failure it
# represents, so a red test says what broke without the reader opening the file.
TAMPERS = {
    "an evidence document was edited": lambda m: m["evidence_documents"]["docs/ERRATA.md"].update(
        {"sha256": "0" * 64}
    ),
    "a public document was edited": lambda m: m["public_documentation"]["README.md"].update(
        {"sha256": "0" * 64}
    ),
    "the core log gained a record": lambda m: m["canonical_measurements"][
        "results/usage.jsonl"
    ].update({"records": 43}),
    "the core log's bytes changed": lambda m: m["canonical_measurements"][
        "results/usage.jsonl"
    ].update({"sha256": "0" * 64}),
    "the P3 log changed": lambda m: m["canonical_measurements"][
        "results/p3_boundary_locus/usage.jsonl"
    ].update({"records": 11}),
    "a design became unrun": lambda m: m["experiment_registry"].update({"unrun": ["99_new"]}),
    "the registry shrank": lambda m: m["experiment_registry"].update({"registered": 9}),
    "the release version moved": lambda m: m.update({"release_version": "0.2.0"}),
    "the tag was renamed": lambda m: m.update({"planned_git_tag": "v1.0.0"}),
    "ERR-001's corrected count was broken": lambda m: m["canonical_measurements"][
        "results/usage.jsonl"
    ].update({"answers_by_type": {"choice": 45, "noul": 44, "score": 29}}),
    "a required key was dropped": lambda m: m.pop("scientific_state"),
    # The identity a release records is the one its own tree declared. This is what a hard-coded
    # name in the builder produces once the project is renamed on `main`: a manifest describing a
    # project the release never was.
    "the manifest names a project its tree never had": lambda m: m["project"].update(
        {"name": "jev-renamed-after-the-release"}
    ),
}


def _write_tampered(tmp_path: Path, mutate) -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutate(manifest)
    target = tmp_path / "tampered-manifest.json"
    target.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return target


class TestTheFreezeVerifies:
    def test_the_shipped_release_verifies_against_its_own_tag(self):
        """The published release, checked the way a reader checks it: from the tag.

        This is the assertion CI depends on. It fails if the tag is absent from the clone rather
        than skipping, because a release whose verification silently did not run is worse than one
        whose verification is red.
        """
        release = ef.Release.for_tag(ef.PLANNED_GIT_TAG)
        with ef.GitTreeSource(ef.PLANNED_GIT_TAG) as source:
            assert ef.verify_manifest(echo=lambda *_: None, source=source, release=release) == 0

    def test_building_twice_produces_identical_bytes(self, tmp_path):
        """Determinism is the property the whole manifest rests on.

        If two builds differed, a reader could not tell an edited manifest from a rebuilt one, and
        the freeze would be unverifiable in principle rather than merely unverified.
        """
        first = ef.write_manifest(tmp_path / "a.json")
        second = ef.write_manifest(tmp_path / "b.json")
        assert first.read_bytes() == second.read_bytes()

    def test_the_committed_manifest_is_what_the_code_builds_from_the_release(self):
        """A stale committed manifest would verify against itself and mean nothing.

        Built from the *tagged tree*, not the working tree. That is the invariant that survives a
        post-release branch: the manifest must be reproducible from the release alone, so a later
        rewrite of a README cannot make the manifest look like something nobody could have produced.
        """
        with ef.GitTreeSource(ef.PLANNED_GIT_TAG) as source:
            rebuilt = json.dumps(
                ef.build_manifest(source), indent=2, sort_keys=True, ensure_ascii=False
            ) + "\n"
        assert rebuilt == MANIFEST.read_text(encoding="utf-8"), (
            "the committed manifest is not what `evidence_freeze build` produces from "
            f"{ef.PLANNED_GIT_TAG}; run it against that tag and commit the result "
            "(or, if the release is already tagged, open a new version)"
        )

    def test_the_release_keeps_the_name_it_was_frozen_under(self):
        """`v0.1.0` was published as `jev-test`. The rename did not rewrite it.

        Project identity is a fact about a release, not a constant of the builder. Read from a
        hard-coded string, `build_manifest` pointed at the tag would describe the release with a
        name its tree never carried, and the committed manifest would stop being reproducible from
        the release alone. The two names differing here is the property under test, not drift to
        correct.
        """
        with ef.GitTreeSource(ef.PLANNED_GIT_TAG) as source:
            frozen = ef.build_manifest(source)["project"]
        current = ef.build_manifest()["project"]

        assert frozen["name"] == "jev-test"
        assert frozen["repository"] == "https://github.com/Charlie-Wang-03/jev-test"
        assert current["name"] == "jev-testbench"
        assert current["repository"] == "https://github.com/Charlie-Wang-03/jev-testbench"

    def test_the_historical_release_still_verifies_after_the_rename(self):
        """A rename on `main` must not invalidate a citation to the frozen tag."""
        release = ef.Release.for_tag(ef.PLANNED_GIT_TAG)
        with ef.GitTreeSource(ef.PLANNED_GIT_TAG) as source:
            assert ef.verify_manifest(echo=lambda *_: None, source=source, release=release) == 0


class TestTheVerifierCanFail:
    @pytest.mark.parametrize("label", sorted(TAMPERS))
    def test_a_damaged_manifest_is_rejected(self, tmp_path, label):
        target = _write_tampered(tmp_path, TAMPERS[label])
        assert ef.verify_manifest(manifest_path=target, echo=lambda *_: None) == 1

    def test_a_missing_manifest_is_rejected(self, tmp_path):
        assert ef.verify_manifest(manifest_path=tmp_path / "nope.json", echo=lambda *_: None) == 1

    def test_unparseable_json_is_rejected(self, tmp_path):
        target = tmp_path / "broken.json"
        target.write_text("{not json", encoding="utf-8")
        assert ef.verify_manifest(manifest_path=target, echo=lambda *_: None) == 1

    def test_a_listed_file_that_is_absent_is_rejected(self, tmp_path):
        target = _write_tampered(
            tmp_path,
            lambda m: m["evidence_documents"].update(
                {"docs/does-not-exist.md": {"sha256": "0" * 64, "class": "canonical_evidence"}}
            ),
        )
        assert ef.verify_manifest(manifest_path=target, echo=lambda *_: None) == 1

    def test_the_failure_message_says_not_to_edit_the_frozen_release(self, tmp_path, capsys):
        """The failure text is read by whoever broke CI, at the moment they broke it.

        The one wrong response available to them is to regenerate the manifest and move on, which
        would silently rewrite a frozen release. The message has to close that door.
        """
        target = _write_tampered(
            tmp_path, lambda m: m["evidence_documents"]["docs/ERRATA.md"].update({"sha256": "0" * 64})
        )
        captured = []
        ef.verify_manifest(manifest_path=target, echo=captured.append)
        text = "\n".join(captured)
        assert "immutable" in text
        assert "v0.2.0" in text


class TestTheManifestIsNotSelfReferential:
    def test_no_full_commit_sha_appears_anywhere(self):
        """The manifest must not name the commit that contains it.

        A file cannot contain its own commit's SHA -- writing it in would change the tree, which
        would change the commit, which would invalidate the SHA. The tag binds the manifest to the
        tree instead.

        The check is for a standalone 40-character hex run. The manifest is full of 64-character
        SHA-256 values by design -- those are file digests, which is the point of the file -- and a
        40-character run cannot hide inside one, because the boundary requires a non-hex character
        on both sides.
        """
        import re

        text = MANIFEST.read_text(encoding="utf-8")
        commit_shaped = re.findall(r"\b[0-9a-f]{40}\b", text)
        assert not commit_shaped, (
            f"the manifest contains a full 40-character commit SHA: {commit_shaped}. "
            "The tag binds the manifest to its tree; the manifest must not name its own commit."
        )

    def test_the_planned_tag_is_the_one_this_module_froze(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["planned_git_tag"] == ef.PLANNED_GIT_TAG == "v0.1.0"
        assert manifest["release_version"] == ef.FROZEN_VERSION == "0.1.0"


class TestTheFreezeMatchesTheEvidence:
    def test_both_canonical_logs_are_listed_with_their_record_counts(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        core = manifest["canonical_measurements"]["results/usage.jsonl"]
        p3 = manifest["canonical_measurements"]["results/p3_boundary_locus/usage.jsonl"]
        assert core["records"] == 42
        assert p3["records"] == 12

    def test_the_nine_non_claims_are_all_frozen(self):
        """Dropping a `NO_*` marker is how a release stops being honest about its own limits."""
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["scientific_state"]["non_claims"] == ef.NON_CLAIMS
        assert len(ef.NON_CLAIMS) == 9
        assert all(marker.startswith("NO_") for marker in ef.NON_CLAIMS)

    def test_the_non_claims_are_actually_stated_in_the_freeze_document(self):
        text = (REPO_ROOT / ef.EVIDENCE_DIR / "PUBLIC_EVIDENCE_FREEZE.md").read_text(encoding="utf-8")
        missing = [marker for marker in ef.NON_CLAIMS if marker not in text]
        assert not missing, f"frozen non-claims absent from the freeze document: {missing}"

    def test_the_p3_negative_result_is_preserved_word_for_word(self):
        """The null is the result. A freeze that softens it is not a freeze of this repository."""
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        text = (REPO_ROOT / ef.EVIDENCE_DIR / "PUBLIC_EVIDENCE_FREEZE.md").read_text(encoding="utf-8")
        # Compared with whitespace collapsed: the property is the words, not where the lines wrap.
        flattened = " ".join(text.split())
        null = manifest["scientific_state"]["primary_null"]
        assert "could not be attributed" in null
        assert ef.P3_VERDICT in text
        assert "could not be attributed to `instructions` or `criteria` alone" in flattened

    def test_every_frozen_document_exists_on_disk(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for section in ("evidence_documents", "public_documentation", "release_metadata"):
            for relative in manifest[section]:
                assert (REPO_ROOT / relative).is_file(), f"{section}: {relative} is missing"

    def test_the_historical_lineage_names_what_each_commit_is(self):
        """§8's rule, as a test: a SHA without an explanation is not provenance."""
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        commits = {entry["sha"]: entry for entry in manifest["historical_commits"]}
        for sha in ("db7d06f", "c0fc9cc", "bdcb637", "44fbbb1"):
            assert sha in commits, f"the lineage omits {sha}"
            assert commits[sha]["what_it_is"], f"{sha} is listed with no explanation"
            assert commits[sha]["type"] in {"MEASUREMENT", "PREREGISTRATION", "ANALYSIS", "DOCUMENTATION", "ENGINEERING"}
        assert "preregistration + original analyzer" in commits["db7d06f"]["what_it_is"]
        assert "immutable measurements" in commits["c0fc9cc"]["what_it_is"]
        assert "post-run analyzer repair, no new measurement" in commits["bdcb637"]["what_it_is"]

    def test_the_resolved_errata_is_not_described_as_a_live_defect(self):
        """ERR-002 is `RESOLVED`. Current HEAD must not be reported as still broken."""
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        errata = {entry["id"]: entry for entry in manifest["known_errata"]}
        assert errata["ERR-002"]["status"] == "RESOLVED"
        assert errata["ERR-002"]["current_head_is_affected"] is False
        assert errata["ERR-002"]["verdict_changed"] is False
        assert errata["ERR-001"]["status"] == "DOCUMENTED"
        assert errata["ERR-001"]["verdict_impact"] == "none"


# ---------------------------------------------------------------------------
# The version-lifecycle property
# ---------------------------------------------------------------------------
#
# A release is the tree its tag points at. The tests below build real, tiny Git repositories to
# check that, because the property is about *history* -- it cannot be shown on a working tree that
# only ever has one state. Two commits and a tag are enough: commit A is tagged, commit B moves the
# branch on, and the release at A must still verify.

SYNTHETIC_EXPERIMENT = "00_synthetic"

# The synthetic release's project identity, and the name `main` moves to afterwards. Project identity
# is per-release -- this repository's own `v0.1.0` was frozen as `jev-test` and the project was
# renamed `jev-testbench` later -- so the fixture reproduces that shape rather than only describing
# it: commit A is tagged under `SYNTHETIC_PROJECT`, commit B renames it, and the release at A must
# still verify and still report the name it was published under.
SYNTHETIC_PROJECT = "jev-synthetic"
RENAMED_PROJECT = "jev-synthetic-renamed"


def _pyproject(name: str) -> str:
    return (
        "[project]\n"
        'version = "0.1.0"\n'
        f'name = "{name}"\n'
        "\n"
        "[project.urls]\n"
        f'Repository = "https://example.invalid/{name}"\n'
    )


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, check=False, text=True
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed in the fixture: {proc.stderr}"
    return proc.stdout


def _synthetic_files() -> dict[str, str]:
    """The smallest tree that is structurally a release of this repository.

    Every marker the verifier looks for is a real constant from ``evidence_freeze``, so a marker
    being renamed fails here rather than passing against a stale literal.
    """
    record = {
        "schema_version": 4,
        "experiment": SYNTHETIC_EXPERIMENT,
        "model_requested": "jev-latest",
        "model_resolved": "jev-1.13.0",
        "status": "ok",
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "answers": {"q": {"type": "choice", "answer": "x"}},
    }
    markers = "\n".join(
        [ef.SCIENTIFIC_STATE, ef.P3_VERDICT, *ef.INHERITED_VERDICTS, *ef.NON_CLAIMS]
    )
    return {
        "src/jev_lab/experiments.py": (
            "# The registry, as this release defined it.\n"
            "EXPERIMENTS: dict[str, object] = {\n"
            f'    "{SYNTHETIC_EXPERIMENT}": object(),\n'
            "}\n"
        ),
        "docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md": f"# Freeze\n\n{markers}\n",
        "docs/EVIDENCE_PROVENANCE.md": f"# Provenance\n\n{ef.SCIENTIFIC_STATE}\n",
        "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md": f"# Result\n\n{ef.P3_VERDICT}\n",
        "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md": "# Preregistration\n",
        "docs/experiments/EXPERIMENT_REGISTRY.md": (
            "# Registry\n\nACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS\n"
        ),
        "README.md": "# The release README\n",
        "docs/README.md": "# The release docs index\n",
        "LICENSE": 'MIT License\n\nTHE SOFTWARE IS PROVIDED "AS IS"\n',
        "CITATION.cff": "cff-version: 1.2.0\nversion: 0.1.0\nlicense: MIT\n",
        "pyproject.toml": _pyproject(SYNTHETIC_PROJECT),
        "results/usage.jsonl": json.dumps(record) + "\n",
    }


def _synthetic_manifest(root: Path, files: dict[str, str]) -> dict:
    def digest(relative: str) -> str:
        return hashlib.sha256((root / relative).read_bytes()).hexdigest()

    return {
        "schema_version": 1,
        "release_version": "0.1.0",
        "planned_git_tag": "v0.1.0",
        "freeze_date": "2026-01-01",
        "project": {"name": SYNTHETIC_PROJECT, "license": "MIT"},
        "model_scope": {},
        "official_claim_snapshot": {},
        "canonical_measurements": {
            "results/usage.jsonl": {
                "stage": "P0",
                "records": 1,
                "sha256": digest("results/usage.jsonl"),
                "answers_by_type": {"choice": 1},
                "noul_answers_carrying_confidence": 0,
                "model_resolved": ["jev-1.13.0"],
            }
        },
        "evidence_documents": {
            relative: {"sha256": digest(relative), "class": "canonical_evidence"}
            for relative in (
                "docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md",
                "docs/EVIDENCE_PROVENANCE.md",
                "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md",
                "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md",
            )
        },
        "public_documentation": {
            relative: {"sha256": digest(relative), "class": "public_documentation"}
            for relative in ("README.md", "docs/README.md")
        },
        "release_metadata": {
            relative: {"sha256": digest(relative)}
            for relative in ("LICENSE", "CITATION.cff", "pyproject.toml")
        },
        "historical_commits": [],
        "known_errata": [],
        "experiment_registry": {
            "registered": 1,
            "with_records": 1,
            "unrun": [],
            "registered_names": [SYNTHETIC_EXPERIMENT],
            "retired_before_release": [],
        },
        "scientific_state": {
            "state": ef.SCIENTIFIC_STATE,
            "p3_verdict": ef.P3_VERDICT,
            "inherited_verdicts": ef.INHERITED_VERDICTS,
            "primary_null": "",
            "non_claims": ef.NON_CLAIMS,
        },
    }


def _make_release_repo(root: Path, *, tag_points_at_the_moved_tree: bool = False) -> Path:
    """Commit A, tag it, then move the branch on with commit B.

    ``tag_points_at_the_moved_tree`` moves the tag onto B instead -- a tag whose tree its own
    manifest does not describe. Nothing here touches the real repository or the real tag.
    """
    files = _synthetic_files()
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    manifest = _synthetic_manifest(root, files)
    (root / ef.Release.for_tag("v0.1.0").manifest_path).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    _git(root, "-c", "init.defaultBranch=main", "init", "-q")
    # Pinned so the fixture's bytes are the same on every platform: the manifest hashes files, and
    # a CRLF checkout would change them for reasons that have nothing to do with the test.
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Synthetic Test")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the release")
    _git(root, "tag", "-a", "-m", "synthetic release", "v0.1.0")

    (root / "README.md").write_text("# Rewritten after the release\n", encoding="utf-8", newline="\n")
    (root / "docs/README.md").write_text("# Index, reworded\n", encoding="utf-8", newline="\n")
    # The project is renamed after the release. Nothing about the tagged tree changes.
    (root / "pyproject.toml").write_text(
        _pyproject(RENAMED_PROJECT), encoding="utf-8", newline="\n"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "post-release documentation and rename")

    if tag_points_at_the_moved_tree:
        _git(root, "tag", "-f", "-a", "-m", "moved", "v0.1.0", "HEAD")
    return root


def _verify_in(repo: Path, *, tag: str = "v0.1.0", echo=None) -> tuple[int, str]:
    source = ef.GitTreeSource(tag, repo_root=repo)
    out: list[str] = []
    with source:
        code = ef.verify_manifest(
            echo=(echo or out.append), source=source, release=ef.Release.for_tag(tag)
        )
    return code, "\n".join(out)


class TestReleaseVerification:
    """`verify <tag>` answers the historical question; `verify-current` answers the other one."""

    def test_the_release_still_verifies_after_the_worktree_moves_on(self, tmp_path):
        """The regression this module was reshaped for.

        The tag was created before commit B rewrote ``README.md`` and ``docs/README.md``. Both are
        listed in the manifest. Verifying the release must nonetheless pass, because what a
        citation points at is the tree the tag commits to, not whatever the branch says later.
        """
        repo = _make_release_repo(tmp_path / "repo")
        assert (repo / "README.md").read_text(encoding="utf-8") == "# Rewritten after the release\n"

        code, output = _verify_in(repo)
        assert code == 0, output
        assert f"Verified historical evidence release: {ef.PLANNED_GIT_TAG}" in output

    def test_the_release_reads_the_registry_its_own_tree_defined(self, tmp_path):
        """A name added to today's registry must not retroactively break a past release.

        The synthetic tree registers exactly one experiment. The live registry in this process
        registers ten. If the verifier consulted the live code -- as it used to -- the counts could
        never agree, and no release could survive the next experiment being written.
        """
        repo = _make_release_repo(tmp_path / "repo")
        with ef.GitTreeSource("v0.1.0", repo_root=repo) as source:
            assert source.registry_names() == [SYNTHETIC_EXPERIMENT]
        assert len(ef.WorktreeSource(REPO_ROOT).registry_names()) > 1

        code, output = _verify_in(repo)
        assert code == 0, output

    def test_current_tree_mode_reports_the_drift_instead(self, tmp_path):
        """Same repository, the other question -- and the honest answer here is "no longer equal"."""
        repo = _make_release_repo(tmp_path / "repo")
        out: list[str] = []
        code = ef.verify_manifest(echo=out.append, source=ef.WorktreeSource(repo))
        text = "\n".join(out)
        assert code == 1
        assert "README.md" in text
        assert "docs/README.md" in text
        # The message has to say that presentation moving on is the expected shape of a
        # post-release branch, or the next person to see this red will "fix" it by rewriting a
        # frozen release. It has to say the opposite about evidence, and close the
        # regenerate-the-manifest door explicitly.
        assert "allowed to move on" in text
        assert "may not" in text
        assert "regenerated manifest" in text
        assert f"verify {ef.PLANNED_GIT_TAG}" in text

    def test_a_tag_whose_tree_does_not_match_its_manifest_fails(self, tmp_path):
        """Corruption inside a tagged tree is still a hard failure, not a special case."""
        repo = _make_release_repo(tmp_path / "repo", tag_points_at_the_moved_tree=True)
        code, output = _verify_in(repo)
        assert code == 1
        assert "README.md" in output
        assert "does not match the manifest it carries" in output

    def test_a_manifest_naming_a_different_release_is_rejected(self, tmp_path):
        """The tag and the manifest have to agree about which release this is."""
        repo = _make_release_repo(tmp_path / "repo")
        manifest_path = repo / ef.Release.for_tag("v0.1.0").manifest_path
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["planned_git_tag"] = "v0.2.0"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "a manifest describing a different release")
        _git(repo, "tag", "-f", "-a", "-m", "moved", "v0.1.0", "HEAD")

        code, output = _verify_in(repo)
        assert code == 1
        assert "planned_git_tag" in output

    def test_a_missing_tag_fails_closed_and_says_how_to_get_it(self, tmp_path):
        """Offline means offline: no tag, no verification, and no fetch behind the user's back."""
        repo = _make_release_repo(tmp_path / "repo")
        with pytest.raises(ef.ReleaseTagNotFound):
            ef.GitTreeSource("v0.9.9", repo_root=repo)

        out: list[str] = []
        assert ef.source_for_tag("v0.9.9", echo=out.append, repo_root=repo) is None
        text = "\n".join(out)
        assert "EVIDENCE" not in text  # no invented marker; the tag name is the identifier
        assert "git fetch --tags" in text
        assert "offline" in text

    def test_an_explicit_manifest_path_is_not_mixed_with_a_tagged_source(self, tmp_path):
        """Two ways of saying where the manifest is would leave the question ambiguous."""
        repo = _make_release_repo(tmp_path / "repo")
        source = ef.GitTreeSource("v0.1.0", repo_root=repo)
        with source:
            assert (
                ef.verify_manifest(
                    manifest_path=tmp_path / "whatever.json", source=source, echo=lambda *_: None
                )
                == 1
            )

    def test_a_release_that_declares_no_identity_fails_rather_than_raising(self, tmp_path):
        """Identity is read out of the tree, so a tree without one is a verdict, not a traceback."""
        repo = _make_release_repo(tmp_path / "repo")
        (repo / "pyproject.toml").unlink()
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "the release loses its pyproject.toml")
        _git(repo, "tag", "-f", "-a", "-m", "moved", "v0.1.0", "HEAD")

        code, output = _verify_in(repo)
        assert code == 1
        assert "pyproject.toml" in output

    def test_a_release_keeps_the_identity_its_own_tree_declared(self, tmp_path):
        """The fixture renames the project in commit B. The release at A keeps its own name.

        This is the regression the builder was reshaped for. `v0.1.0` was frozen as `jev-test` and
        the project became `jev-testbench` afterwards; a builder holding today's name would have
        made the old release describe itself as something it was never called, and verifying it
        would have failed on a rename that changed none of its evidence.
        """
        repo = _make_release_repo(tmp_path / "repo")
        with ef.GitTreeSource("v0.1.0", repo_root=repo) as source:
            assert ef.project_identity(source)[0] == SYNTHETIC_PROJECT
        assert ef.project_identity(ef.WorktreeSource(repo))[0] == RENAMED_PROJECT

        code, output = _verify_in(repo)
        assert code == 0, output

