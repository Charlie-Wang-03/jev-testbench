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
import tomllib
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
    # A process record rather than a measurement, but a public document in both languages, so the
    # same no-drift rule applies: it is a pair, and the two halves must keep saying one thing.
    (
        "docs/AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.md",
        "docs/AGENTIC_ENGINEERING_AND_COGNITIVE_DEBT.zh-CN.md",
    ),
]

# Evidence artifacts: canonical in English, and intentionally not translated.
ENGLISH_ONLY_EVIDENCE = [
    "docs/audits/P1_OFFICIAL_CLAIMS_LOCAL_EVIDENCE.md",
    "docs/audits/P2_JEV_INSIGHT_TRIAGE.md",
    "docs/audits/P3_BOUNDARY_LOCUS_RESULT.md",
    "docs/experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md",
    "docs/experiments/EXPERIMENT_REGISTRY.md",
    "docs/sources/TYPESAFE_OFFICIAL_SOURCES.md",
    "docs/EVIDENCE_PROVENANCE.md",
    "docs/ERRATA.md",
    # The released freeze is an evidence artifact, and the strongest one: it is the set a citation
    # points at. A second-language copy would be a second text making the same promises about
    # hashes, with no mechanism keeping the two in step.
    "docs/evidence/README.md",
    "docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md",
    "docs/evidence/v0.1.0/RELEASE_NOTES.md",
    "docs/evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md",
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
    "10",
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
    # The released evidence freeze. Both halves must name the same version: a README pair that
    # disagrees about which release is frozen is a citation waiting to point at the wrong tree.
    "v0.1.0",
    "docs/evidence/v0.1.0/PUBLIC_EVIDENCE_FREEZE.md",
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

class TestLicenseIsResolved:
    """The owner chose MIT. These assert the choice is stated once and agrees with itself.

    The predecessor of this class guarded the opposite state -- no `LICENSE` file, because no
    decision had been recorded. That gate is closed, and a test that still asserted its absence
    would now be asserting that the repository is unlicensed. What replaces it is the same
    discipline pointed the other way: the file, the packaging metadata, and both READMEs must say
    the *same* thing, because a license stated in two vocabularies is a license that can drift.
    """

    def test_a_license_file_exists(self):
        licence = REPO_ROOT / "LICENSE"
        assert licence.is_file(), (
            "no LICENSE file, but docs/OPEN_SOURCE_LICENSE_DECISION.md records that the owner "
            "chose MIT"
        )

    def test_the_license_file_is_the_mit_text_not_a_pointer(self):
        """A file that says 'see the project page' grants nothing. The grant has to be in it."""
        text = read("LICENSE")
        assert text.splitlines()[0].strip() == "MIT License"
        assert "Permission is hereby granted, free of charge" in text
        assert 'THE SOFTWARE IS PROVIDED "AS IS"' in text
        # The two operative clauses of MIT. Without the second, the grant is unconditional.
        assert "The above copyright notice and this permission notice shall be included" in text

    def test_the_copyright_line_names_the_packaging_author(self):
        """One author identity in the repository, not a second one invented for the license."""
        author = tomllib.loads(read("pyproject.toml"))["project"]["authors"][0]["name"]
        assert f"Copyright (c) 2026 {author}" in read("LICENSE"), (
            "the LICENSE copyright line does not name the author recorded in pyproject.toml"
        )

    def test_packaging_metadata_declares_the_same_license(self):
        project = tomllib.loads(read("pyproject.toml"))["project"]
        assert project["license"] == "MIT"
        assert project["license-files"] == ["LICENSE"]

    def test_the_license_is_not_also_declared_as_a_classifier(self):
        """PEP 639 deprecates `License ::` classifiers beside an SPDX expression.

        Shipping both states the same term in two vocabularies. The expression is the one the
        build backend turns into `License-Expression`, so it is the one that stays.
        """
        classifiers = tomllib.loads(read("pyproject.toml"))["project"]["classifiers"]
        licences = [entry for entry in classifiers if entry.startswith("License ::")]
        assert not licences, f"SPDX expression and licence classifiers both present: {licences}"

    def test_no_second_license_is_applied_to_the_evidence(self):
        """One licence, stated once. A data licence here would need its own decision record."""
        root_files = {path.name for path in REPO_ROOT.iterdir() if path.is_file()}
        for alternative in ("LICENSE-CC", "LICENSE-DATA", "LICENSE-APACHE", "COPYING"):
            assert alternative not in root_files, f"{alternative} was added without a decision"

    def test_the_decision_document_records_the_outcome(self):
        text = read("docs/OPEN_SOURCE_LICENSE_DECISION.md")
        assert "LICENSE_DECISION_RESOLVED_MIT" in text
        assert "**Decision: MIT.**" in text

    @pytest.mark.parametrize(("english", "chinese"), PAIRED_DOCUMENTS[:1])
    def test_both_readmes_name_the_chosen_license(self, english, chinese):
        """The README is the entry point. 'A license exists' is not the same as naming it."""
        for path in (english, chinese):
            assert "MIT" in read(path), f"{path} does not name the chosen license"


class TestTheRegistryHasNoUnrunExperiment:
    """`ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS`, as a documentation invariant.

    The list of retired designs is stated in the README, in the experiment registry, and in the
    repository's own registry code. Three copies of one list is three chances to drift, so the
    README is checked against the code here, and the documentation set is checked against both.
    """

    RETIRED = [
        "00_model_info",
        "08_literal_reading",
        "09_numeric_limits",
        "10_state_length",
        "11_language_pair",
    ]

    def test_the_readmes_do_not_offer_a_retired_experiment_as_runnable(self):
        """`list` would not run these. The README must not imply otherwise."""
        for path in ("README.md", "README.zh-CN.md"):
            text = read(path)
            for name in self.RETIRED:
                assert name in text, (
                    f"{path} does not mention the retired design {name}. A reader who meets the "
                    "name in the P1 audit needs the README to say what happened to it."
                )
            assert "retired" in text.lower() or "退役" in text, (
                f"{path} names the retired designs without saying they were retired"
            )

    def test_the_registry_document_has_exactly_two_categories(self):
        """The document is the current registry, so it must not grow a third column.

        Every retired design carries an explicit retire decision rather than a "later" marker:
        an intention with no record cannot be cited, so there is no state in which one is
        parked.
        """
        text = read("docs/experiments/EXPERIMENT_REGISTRY.md")
        for name in self.RETIRED:
            assert name in text, f"EXPERIMENT_REGISTRY.md does not account for {name}"
        assert "Executed / evidence-bearing" in text
        assert "Retired before public release" in text
        assert "DELETE_FROM_ACTIVE_REGISTRY" in text
        assert "ACTIVE_REGISTRY_HAS_ZERO_UNRUN_EXPERIMENTS" in text
        for deferred in ("KEEP_FOR_LATER", "BACKLOG", "MAYBE"):
            assert deferred not in text, (
                f"{deferred} is a deferred state; a design is run or retired, never parked"
            )

    def test_every_retired_design_is_absent_from_the_code(self):
        """The doc and the registry must agree, so this reads the source rather than a copy."""
        from jev_lab.experiments import EXPERIMENTS

        assert not [name for name in self.RETIRED if name in EXPERIMENTS]


class TestThePublicationPackStaysConsistent:
    """The pack the owner decides against must not contradict the release it describes.

    Everything in `docs/publication/` is decision support: a release body, a venue comparison, a
    metadata proposal, a feedback draft and a checklist. It is read *before* the decision, not after
    -- so a stale line here is read as fact at exactly the moment it matters.

    Two failure modes are worth a mechanical guard, and the link checker catches neither:

    * **A claim that outruns the freeze.** The state string is
      `NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET` and the public-novelty check is
      `PUBLIC_NOVELTY_UNRESOLVED`. Prose saying "no discovery" settles a question the evidence
      deliberately leaves open, and it is a *stronger* statement than the string it paraphrases.
      This is the overclaim that is easy to miss, because it reads as modesty.
    * **A task that is already done.** A checklist item asking the owner to decide something that
      was resolved before the pack existed spends their attention on a non-decision, and makes the
      items around it less trustworthy.

    The refusal forms stay legal: the release draft quotes "nobody has done this" in the sentence
    that *declines* the claim, which is the opposite of making it. Only the assertive forms are
    forbidden, so this checks for `nobody has found`.
    """

    # Wording that states more than the frozen release supports, in the negative direction.
    OVERCLAIMS = [
        "no discovery",
        "nothing new exists",
        "there are no discoveries",
        "nobody has found",
    ]

    # Work finished before this pack existed, so it is not an open owner decision.
    RESOLVED_TASKS = [
        "Decide about P4",
        "Chinese-language README",
    ]

    # The rename was an open question when this pack was written and was decided by the owner in
    # P5-E. The pack must record the decision rather than continue to offer it.
    RENAME_DECIDED = "PROJECT_RENAME: OWNER_APPROVED"
    STEP_RENAME = "no rename is proposed"
    RESOLVED_RENAME_ASK = "Decide about a repository rename"

    PUBLICATION_FILES = {
        "PUBLICATION_CHECKLIST.md",
        "GITHUB_RELEASE_DRAFT.md",
        "BLOG_PUBLICATION_OPTIONS.md",
        "REPOSITORY_METADATA_PROPOSAL.md",
        "TYPESAFE_FEEDBACK_DRAFT.md",
        "PUBLICATION_CLOSURE.md",
    }

    STATUS_MARKERS = {
        "PUBLICATION_CHECKLIST.md": "publication closure complete",
        "GITHUB_RELEASE_DRAFT.md": "published",
        "BLOG_PUBLICATION_OPTIONS.md": "executed",
        "REPOSITORY_METADATA_PROPOSAL.md": "applied",
        "TYPESAFE_FEEDBACK_DRAFT.md": "not sent",
        "PUBLICATION_CLOSURE.md": "publication closure complete",
    }

    def _pack_files(self) -> list[Path]:
        return sorted((REPO_ROOT / "docs/publication").glob("*.md"))

    def test_the_publication_directory_is_the_five_records_plus_closure(self):
        assert {path.name for path in self._pack_files()} == self.PUBLICATION_FILES

    @pytest.mark.parametrize("phrase", OVERCLAIMS)
    def test_no_pack_document_outruns_the_frozen_novelty_state(self, phrase):
        for path in self._pack_files():
            assert phrase not in read(f"docs/publication/{path.name}"), (
                f"{path.name} contains {phrase!r}. The freeze records that no *strong Jev-specific "
                "novel* finding survived scrutiny, and the public-novelty check is UNRESOLVED. "
                "Neither licenses a statement that nothing exists."
            )

    def test_the_release_draft_carries_the_states_that_scope_it(self):
        text = read("docs/publication/GITHUB_RELEASE_DRAFT.md")
        assert "NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET" in text
        assert "PUBLIC_NOVELTY_UNRESOLVED" in text
        assert "P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION" in text

    @pytest.mark.parametrize("task", RESOLVED_TASKS)
    def test_no_pack_document_asks_for_a_decision_already_taken(self, task):
        for path in self._pack_files():
            assert task not in read(f"docs/publication/{path.name}"), (
                f"{path.name} still carries {task!r} as an open item. P4 finished with the v0.1.0 "
                "freeze, and README.zh-CN.md exists and is linked from both README switchers, so "
                "neither is a decision left to make."
            )

    def test_the_pack_records_the_rename_as_a_decision_already_taken(self):
        assert self.RENAME_DECIDED in read("docs/publication/REPOSITORY_METADATA_PROPOSAL.md")
        for path in self._pack_files():
            text = read(f"docs/publication/{path.name}")
            for stale in (self.STEP_RENAME, self.RESOLVED_RENAME_ASK):
                assert stale not in text

    def test_every_publication_document_status_matches_live_phase(self):
        for path in self._pack_files():
            status = next(
                (
                    line
                    for line in read(f"docs/publication/{path.name}").splitlines()
                    if line.startswith("**Status:")
                ),
                None,
            )
            assert status is not None, f"{path.name} has no `**Status:` line"
            marker = self.STATUS_MARKERS[path.name]
            assert marker in status.lower(), (
                f"{path.name} status does not carry the expected live-phase marker {marker!r}: "
                f"{status!r}"
            )

    def test_publication_closure_keeps_the_two_release_roles_distinct(self):
        text = read("docs/publication/PUBLICATION_CLOSURE.md")
        assert "v0.1.0" in text
        assert "v0.1.1" in text
        assert "scientific evidence anchor" in text
        assert "zero new Jev API calls" in text
        assert "PUBLICATION_CLOSURE_COMPLETE" in text
        assert "PUBLICATION_CLOSURE_COMPLETE = NO" not in text
