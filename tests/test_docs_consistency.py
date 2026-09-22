"""The bilingual documents must not drift apart. Offline: reads files, opens nothing.

A translated pair is a claim that both halves say the same thing. Nothing about that claim is
self-enforcing -- two files edited months apart will diverge, and the divergence that matters is
never the prose. It is the number, the hash, the verdict string, or the experiment name, because
those are the things a reader copies out.

So the invariant is enforced mechanically rather than promised in a comment. This module checks the
properties a reader would rely on:

* every English public document has its translated counterpart, and the two link to each other;
* every fact that must not differ -- hashes, status strings, filenames, experiment names, and the
  headline figures -- appears on both sides;
* every relative link points at a file that exists;
* no public document ships a placeholder.

The evidence artifacts (audits, preregistration, result, source registry) are deliberately **not**
paired. They are canonical in English only, so that the evidence layer has one textual source rather
than two that can drift. That asymmetry is asserted here too, so that adding a translation later is a
deliberate act rather than an accident.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The two canonical measurement logs, by content. These are the digests every document cites.
CANONICAL_HASHES = [
    "38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b",
    "17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e",
]

# (English, Simplified Chinese) pairs that must stay in sync.
PAIRED_DOCUMENTS = [
    ("README.md", "README.zh-CN.md"),
    ("docs/architecture/architecture.md", "docs/architecture/architecture.zh-CN.md"),
    ("docs/methodology/evaluation.md", "docs/methodology/evaluation.zh-CN.md"),
    ("docs/guides/reproducibility.md", "docs/guides/reproducibility.zh-CN.md"),
    ("docs/guides/credentials.md", "docs/guides/credentials.zh-CN.md"),
    ("docs/findings/findings.md", "docs/findings/findings.zh-CN.md"),
]

# Evidence artifacts: canonical in English, and intentionally not translated.
ENGLISH_ONLY_EVIDENCE = [
    "docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md",
    "docs/audits/P2_JEV_INSIGHT_TRIAGE.md",
    "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md",
    "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md",
    "docs/sources/TYPESAFE_OFFICIAL_SOURCES.md",
    "docs/EVIDENCE_PROVENANCE.md",
]

# Facts that must be identical on both sides of a pair. A number that appears in one language and
# not the other is the exact failure this file exists to catch.
SHARED_FACTS = [
    # Canonical log identity. If these drift, a citation is wrong.
    "38e67630a7c345f1719795401ceaf7de43b1c5ec16da2adb568fb7ef8dc40b1b",
    "17f36f7551d598a4724f4557d8b235d810ec4fb259d8d4b842eabc8f34c5d78e",
    "results/usage.jsonl",
    "results/p3_boundary_locus/usage.jsonl",
    # Verdicts and status strings.
    "CORE_CAPABILITY_EXPLORATION_CLOSED",
    "P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION",
    "P1_OFFICIAL_LOCAL_AUDIT_PASS",
    "P2_TRIAGE_PASS",
    "FIELD_ALIGNMENT_CAVEAT",
    "ACTUAL_HANDLER_EXECUTION_UNTESTED",
    # Counts and headline figures.
    "42",
    "12",
    "15",
    "10",
    "1044",
    "21,767",
    "3,594",
    "816",
    "3,480",
    "4.26",
    "76.55",
    # The P3 arms: medians, the separation that killed the attribution, the endpoint gap.
    "0.75",
    "0.20",
    "0.55",
    "0.31",
    "0.36",
    "0.76",
    "0.05",
    "0.56",
    "80.4",
    "71.4",
    # Model identity.
    "jev-1.13.0",
    "jev-latest",
]

# Authoring markers that mean a document is unfinished. Deliberately narrow: `placeholder` is a
# legitimate word in the credentials guide (it describes the committed template), so matching it
# would flag correct prose and train a reader to ignore this test.
PLACEHOLDERS = ["TODO", "TBD", "FIXME", "coming soon", "COMING SOON", "Lorem ipsum"]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# Markdown about code contains code-shaped text, and `HANDLERS[name](argument)` in a code span is
# not a broken link. A checker that cannot tell the difference is a checker people learn to ignore,
# so code is stripped before links are read.
FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
NON_FILE_SCHEMES = ("http://", "https://", "mailto:", "#")


def relative_links_in(relative_path: str) -> list[str]:
    """Link targets in one document that are supposed to name a path in this repository."""
    text = INLINE_CODE.sub("", FENCED_CODE.sub("", read(relative_path)))
    targets = (match.group("target") for match in MARKDOWN_LINK.finditer(text))
    return [
        target.split("#", 1)[0]
        for target in targets
        if not target.startswith(NON_FILE_SCHEMES) and target.split("#", 1)[0]
    ]


def all_markdown() -> list[Path]:
    """Every markdown file git tracks, in a stable order.

    Tracked, not every ``.md`` on disk. ``results/summary.md`` and ``results/capability_snapshot.md``
    are ignored, machine-written views, so globbing the working copy would make this check depend on
    whether someone had run the report commands -- and a document-quality gate is about the
    documents the repository actually ships.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(REPO_ROOT / name for name in listing.split("\0") if name)


class TestPairsExist:
    @pytest.mark.parametrize(("english", "chinese"), PAIRED_DOCUMENTS)
    def test_both_halves_of_every_pair_exist(self, english, chinese):
        assert (REPO_ROOT / english).is_file(), f"missing English half: {english}"
        assert (REPO_ROOT / chinese).is_file(), f"missing translated half: {chinese}"

    @pytest.mark.parametrize(("english", "chinese"), PAIRED_DOCUMENTS)
    def test_the_language_switch_is_two_way(self, english, chinese):
        """Each half must link to the other, by filename, so a reader can always get back."""
        assert Path(chinese).name in read(english), f"{english} does not link to {chinese}"
        assert Path(english).name in read(chinese), f"{chinese} does not link back to {english}"

    @pytest.mark.parametrize("artefact", ENGLISH_ONLY_EVIDENCE)
    def test_evidence_artifacts_stay_english_only(self, artefact):
        """The evidence layer keeps one canonical text. A translation would be a second one."""
        translated = REPO_ROOT / artefact.replace(".md", ".zh-CN.md")
        assert (REPO_ROOT / artefact).is_file(), f"missing evidence artifact: {artefact}"
        assert not translated.exists(), (
            f"{translated.name} exists; evidence artifacts are canonical in English only, so that "
            "the evidence layer has a single source rather than two that can drift"
        )


class TestPairsAgree:
    @pytest.mark.parametrize(("english", "chinese"), PAIRED_DOCUMENTS)
    def test_shared_facts_appear_on_both_sides(self, english, chinese):
        english_text, chinese_text = read(english), read(chinese)
        missing = [
            fact
            for fact in SHARED_FACTS
            if (fact in english_text) != (fact in chinese_text)
        ]
        assert not missing, (
            f"{english} and {chinese} disagree on: {missing}. "
            "Every hash, verdict, count and headline figure must appear in both halves."
        )

    @pytest.mark.parametrize(("english", "chinese"), PAIRED_DOCUMENTS)
    def test_the_canonical_hashes_are_never_paraphrased(self, english, chinese):
        """A hash is the one fact that must appear as one unbroken 64-character run, or not at all.

        A truncated or hyphen-wrapped digest still looks like a digest to a human reader, and a
        reader who copies it gets a value that does not verify. Presence is asserted by
        ``test_shared_facts_appear_on_both_sides``; this asserts the form.
        """
        for text, name in ((read(english), english), (read(chinese), chinese)):
            contiguous = set(re.findall(r"\b[0-9a-f]{64}\b", text))
            for digest in CANONICAL_HASHES:
                if digest not in text:
                    continue
                assert digest in contiguous, (
                    f"{name} contains the digest {digest[:12]}... but not as a contiguous "
                    "64-character run; it has been split or hyphenated"
                )


class TestLinksResolve:
    """A relative link is a promise that a file is there. Promises are cheap; this checks them."""

    @pytest.mark.parametrize(
        "document",
        [path.relative_to(REPO_ROOT).as_posix() for path in all_markdown()],
    )
    def test_every_relative_link_points_at_a_file_that_exists(self, document):
        # Fragments are dropped: an anchor is checked against nothing here, and a wrong one is a
        # markdownlint warning rather than a reader who cannot find the file.
        missing = [
            target
            for target in relative_links_in(document)
            if not (REPO_ROOT / document).parent.joinpath(target).resolve().exists()
        ]
        assert not missing, (
            f"{document} links to {missing}, which do not exist. Evidence documents are read by "
            "people deciding whether to trust this repository; a dead link is a small, visible "
            "piece of that judgment."
        )


class TestPublicDocumentsAreFinished:
    @pytest.mark.parametrize("path", [p for p, _ in PAIRED_DOCUMENTS])
    def test_no_english_public_document_ships_a_placeholder(self, path):
        text = read(path)
        found = [word for word in PLACEHOLDERS if word in text]
        assert not found, f"{path} contains placeholder text: {found}"

    @pytest.mark.parametrize("path", [p for _, p in PAIRED_DOCUMENTS])
    def test_no_translated_public_document_ships_a_placeholder(self, path):
        text = read(path)
        found = [word for word in PLACEHOLDERS if word in text]
        assert not found, f"{path} contains placeholder text: {found}"

    def test_the_license_gate_is_stated_not_glossed(self):
        """The repository has no license. Every public entry point has to say so plainly."""
        for path in ("README.md", "README.zh-CN.md"):
            text = read(path).lower()
            assert "license" in text, f"{path} does not mention the license state"
        assert "LICENSE_DECISION_REQUIRED_BEFORE_PUBLIC" in read(
            "docs/OPEN_SOURCE_LICENSE_DECISION.md"
        )

    def test_there_is_no_license_file_yet(self):
        """Guards the human gate: a LICENSE file may only appear once the owner has chosen one."""
        assert not (REPO_ROOT / "LICENSE").exists(), (
            "a LICENSE file exists, but no license decision has been recorded; "
            "see docs/OPEN_SOURCE_LICENSE_DECISION.md"
        )
