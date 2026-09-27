"""The frozen evidence release must verify, and the verifier must actually be able to fail.

A verifier that has only ever been observed passing is not evidence of anything. So the tests below
do two separate jobs: they assert that the shipped release verifies, and they assert that a
deliberately damaged manifest does **not**. The second job is the one that makes the first one mean
something.

Everything here is offline. The suite blocks sockets outright (see ``conftest.py``), so a test that
reached the network would fail rather than pass quietly.
"""

import json
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
}


def _write_tampered(tmp_path: Path, mutate) -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutate(manifest)
    target = tmp_path / "tampered-manifest.json"
    target.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return target


class TestTheFreezeVerifies:
    def test_the_shipped_manifest_passes(self, capsys):
        assert ef.verify_manifest(echo=lambda *_: None) == 0

    def test_building_twice_produces_identical_bytes(self, tmp_path):
        """Determinism is the property the whole manifest rests on.

        If two builds differed, a reader could not tell an edited manifest from a rebuilt one, and
        the freeze would be unverifiable in principle rather than merely unverified.
        """
        first = ef.write_manifest(tmp_path / "a.json")
        second = ef.write_manifest(tmp_path / "b.json")
        assert first.read_bytes() == second.read_bytes()

    def test_the_committed_manifest_is_what_the_code_builds(self, tmp_path):
        """A stale committed manifest would verify against itself and mean nothing."""
        rebuilt = ef.write_manifest(tmp_path / "rebuilt.json")
        assert rebuilt.read_text(encoding="utf-8") == MANIFEST.read_text(encoding="utf-8"), (
            "the committed manifest is not what `evidence_freeze build` produces; "
            "run it and commit the result (or, if the release is already tagged, open a new version)"
        )


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
