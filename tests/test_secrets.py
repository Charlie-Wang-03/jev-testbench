"""The credential loader: precedence, the local secret file, and what must never escape.

Everything here is offline. Keys are dummy strings written into pytest's temporary directories;
``conftest.py`` guarantees the repository's own ``.secrets/typesafe.env`` is unreachable from this
process, so these tests describe the loader rather than this machine's configuration.

The last class drives the real SDK and the real ``open_client`` over an ``httpx2.MockTransport``,
which is the only way to show that a key from the local file actually reaches the wire.
"""

import subprocess

import httpx2
import pytest

from jev_lab import client as client_module
from jev_lab.client import (
    EXISTS,
    MISSING,
    SOURCE_ENVIRONMENT,
    SOURCE_LOCAL_SECRET_FILE,
    UNUSABLE,
    TransportProbe,
    api_key,
    api_key_status,
    credential,
    open_client,
    read_secret_file,
    require_api_key,
    scrub_secrets,
    secret_file_path,
    SecretFileError,
    MissingApiKeyError,
)
from jev_lab.experiments import get_experiment, run_experiment
from jev_lab.recorder import UsageRecorder
from jev_lab import __main__ as cli

# Dummy credentials. Nothing here is, or resembles, a live key. The distinctive tails matter: a
# test below asserts that no slice of a key appears in a status string, and a value ending in a
# common word would collide with the words in that string rather than with a key.
FROM_FILE = "sk-dummy-filevalue-9f3a1c"
FROM_ENVIRONMENT = "sk-dummy-envvalue-7b2e5d"

EXAMPLE_FILE = client_module.repo_root() / ".secrets.example" / "typesafe.env"


def install_secret_file(monkeypatch, tmp_path, text, name=client_module.SECRET_FILE_NAME):
    """Write ``text`` to a scratch secret file and point the loader at it. Returns the path."""
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(client_module, "secret_file_path", lambda: path)
    return path


def without_environment(monkeypatch):
    """Remove the environment variable so the file is the only source under consideration."""
    monkeypatch.delenv(client_module.API_KEY_ENV, raising=False)


class TestPrecedence:
    """Environment first, local file second, fail closed third -- and no fourth source."""

    def test_the_environment_wins_over_the_file(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        assert credential() == (FROM_ENVIRONMENT, SOURCE_ENVIRONMENT)

    def test_a_blank_environment_value_falls_through_to_the_file(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        monkeypatch.setenv(client_module.API_KEY_ENV, "   ")
        assert credential() == (FROM_FILE, SOURCE_LOCAL_SECRET_FILE)

    def test_the_file_answers_when_the_environment_is_unset(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        assert credential() == (FROM_FILE, SOURCE_LOCAL_SECRET_FILE)
        assert api_key_status() == f"{EXISTS} (source={SOURCE_LOCAL_SECRET_FILE})"

    def test_the_file_is_not_read_when_the_environment_has_a_value(self, monkeypatch, tmp_path):
        # A file that would fail closed if it were consulted. The environment must short-circuit it.
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        assert credential() == (FROM_ENVIRONMENT, SOURCE_ENVIRONMENT)

    def test_no_key_anywhere_is_missing(self, monkeypatch):
        without_environment(monkeypatch)
        assert credential() is None
        assert api_key() is None
        assert api_key_status() == MISSING

    def test_a_missing_key_fails_closed(self, monkeypatch):
        without_environment(monkeypatch)
        with pytest.raises(MissingApiKeyError):
            require_api_key()

    def test_the_file_is_the_only_path_considered(self, monkeypatch, tmp_path):
        # A stray `.env` or `typesafe.env` next to the working directory is not a source. The loader
        # reads one path and never scans, so a file dropped elsewhere changes nothing.
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / ".env").write_text(f"TYPESAFE_API_KEY={FROM_FILE}\n", encoding="utf-8")
        (elsewhere / "typesafe.env").write_text(f"TYPESAFE_API_KEY={FROM_FILE}\n", encoding="utf-8")
        monkeypatch.chdir(elsewhere)
        without_environment(monkeypatch)
        assert credential() is None


class TestTheLocalFile:
    """A deliberately narrow format: one name, one assignment, no interpretation."""

    def test_a_valid_file_provides_the_key(self, monkeypatch, tmp_path):
        path = install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE
        assert path.exists()

    def test_comments_and_blank_lines_are_ignored(self, monkeypatch, tmp_path):
        install_secret_file(
            monkeypatch,
            tmp_path,
            "# a comment\n\n   \nTYPESAFE_API_KEY=" + FROM_FILE + "\n\n# trailing comment\n",
        )
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE

    def test_an_indented_comment_is_still_a_comment(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"   # indented\nTYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE

    def test_no_final_newline_is_fine(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE

    def test_crlf_line_endings_are_accepted(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"# comment\r\nTYPESAFE_API_KEY={FROM_FILE}\r\n")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE

    def test_surrounding_whitespace_is_stripped_from_the_value(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY=  {FROM_FILE}\t\n")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE

    def test_a_missing_file_is_missing_not_an_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr(client_module, "secret_file_path", lambda: tmp_path / "absent.env")
        without_environment(monkeypatch)
        assert read_secret_file() is None
        assert api_key_status() == MISSING

    def test_an_empty_value_is_missing_not_an_empty_key(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=\n")
        without_environment(monkeypatch)
        assert read_secret_file() is None
        assert api_key_status() == MISSING

    def test_the_placeholder_file_is_missing_until_it_is_filled_in(self, monkeypatch, tmp_path):
        # The exact contents of the file this repository creates for a human to edit.
        install_secret_file(
            monkeypatch,
            tmp_path,
            "# Local credentials for this machine. Never commit this file.\n"
            "# Format: TYPESAFE_API_KEY=<your-key>\n"
            "# Paste the key after the equals sign, then save. This file is git-ignored.\n"
            "\n"
            "TYPESAFE_API_KEY=\n",
        )
        without_environment(monkeypatch)
        assert api_key_status() == MISSING

    def test_an_inline_hash_is_part_of_the_value(self, monkeypatch, tmp_path):
        # Documented strictness: there is no inline-comment syntax, so the value is the whole rest
        # of the line. A reader who writes a trailing comment gets a value that does not work,
        # rather than a value silently edited on their behalf.
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE} # mine\n")
        without_environment(monkeypatch)
        assert read_secret_file() == f"{FROM_FILE} # mine"

    def test_only_newlines_split_lines(self, monkeypatch, tmp_path):
        # `str.splitlines` also breaks on U+0085, U+2028 and friends. A value containing one must
        # stay one value, or a key could be silently truncated.
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY=part\u0085{FROM_FILE}\n")
        without_environment(monkeypatch)
        assert read_secret_file() == f"part\u0085{FROM_FILE}"

    def test_an_unreadable_file_fails_closed(self, monkeypatch, tmp_path):
        # A directory where the file should be: present, and impossible to read.
        path = tmp_path / client_module.SECRET_FILE_NAME
        path.mkdir()
        monkeypatch.setattr(client_module, "secret_file_path", lambda: path)
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert caught.value.kind == "unreadable"


class TestFailClosed:
    """A file that exists but cannot be used is an error, never a quiet downgrade to *missing*."""

    def test_a_duplicate_key_fails_closed(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert caught.value.kind == "duplicate-key"

    def test_a_duplicate_key_is_reported_as_unusable(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        without_environment(monkeypatch)
        assert api_key_status() == f"{UNUSABLE} (duplicate-key)"

    def test_a_second_key_does_not_silently_win(self, monkeypatch, tmp_path):
        # The failure mode this prevents: a stale line left above a fresh one, with the fresh one
        # taking effect and the reader believing the stale one did.
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nTYPESAFE_API_KEY={FROM_ENVIRONMENT}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError):
            credential()

    def test_an_unexpected_name_fails_closed(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nTYPESAFE_OTHER={FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert caught.value.kind == "malformed"

    def test_a_line_without_an_equals_sign_fails_closed(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nnonsense line\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert caught.value.kind == "malformed"

    def test_a_space_before_the_equals_sign_fails_closed(self, monkeypatch, tmp_path):
        # `TYPESAFE_API_KEY =x` is not an assignment in this format; a parser that shrugged at it
        # would let a file look configured while nothing was read.
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY ={FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert caught.value.kind == "malformed"

    def test_require_api_key_propagates_the_file_error(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError):
            require_api_key()

    def test_open_client_does_not_swallow_the_file_error(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError):
            with open_client():
                pytest.fail("the client must not be yielded when the credential did not load")

    def test_scrub_secrets_still_works_when_the_file_is_unusable(self, monkeypatch, tmp_path):
        # It runs on error paths, so it must not raise on an error path.
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        assert scrub_secrets(f"failed with {FROM_ENVIRONMENT}") == "failed with ***"

    def test_the_cli_reports_the_file_error_without_a_traceback(self, monkeypatch, tmp_path, capsys):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=one\nTYPESAFE_API_KEY=two\n")
        without_environment(monkeypatch)
        assert cli._run_experiments([get_experiment("01_primitives")], model=None, max_requests=1, results_dir=tmp_path) == 1
        printed = capsys.readouterr().out
        assert "duplicate-key" in printed
        assert "Traceback" not in printed


class TestNoShellSemantics:
    """The file is data. Nothing in it is expanded, substituted, sourced, or executed."""

    def test_dollar_substitution_is_not_expanded(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=$(echo hi)\n")
        without_environment(monkeypatch)
        assert read_secret_file() == "$(echo hi)"

    def test_variable_references_are_not_expanded(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SOME_OTHER_VARIABLE", FROM_ENVIRONMENT)
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=${SOME_OTHER_VARIABLE}\n")
        without_environment(monkeypatch)
        assert read_secret_file() == "${SOME_OTHER_VARIABLE}"

    def test_backticks_are_not_executed(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, "TYPESAFE_API_KEY=`echo hi`\n")
        without_environment(monkeypatch)
        assert read_secret_file() == "`echo hi`"

    def test_a_command_substitution_in_the_file_is_never_run(self, monkeypatch, tmp_path):
        canary = tmp_path / "canary"
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY=$(touch {canary.as_posix()})\n")
        without_environment(monkeypatch)
        read_secret_file()
        assert not canary.exists()

    def test_export_and_quotes_are_ordinary_characters(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, 'export TYPESAFE_API_KEY="quoted"\n')
        without_environment(monkeypatch)
        # `export NAME="quoted"` is not `NAME=value` here, so it fails closed rather than being
        # interpreted -- which is the point: the loader is not a shell.
        with pytest.raises(SecretFileError):
            read_secret_file()

    def test_quotes_around_a_value_are_kept(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, 'TYPESAFE_API_KEY="quoted"\n')
        without_environment(monkeypatch)
        assert read_secret_file() == '"quoted"'

    def test_no_dotenv_dependency_was_added(self):
        # The format is ours and small. A dependency that implements shell-like `.env` semantics
        # would bring the expansions this loader refuses.
        pyproject = (client_module.repo_root() / "pyproject.toml").read_text(encoding="utf-8")
        assert "dotenv" not in pyproject


class TestTheSecretNeverEscapes:
    """Nothing that reports on the credential may contain any part of it."""

    def test_the_status_names_the_source_and_nothing_else(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        status = api_key_status()
        assert FROM_FILE not in status
        assert FROM_FILE[:8] not in status
        assert FROM_FILE[-6:] not in status
        assert status == f"{EXISTS} (source={SOURCE_LOCAL_SECRET_FILE})"

    def test_the_environment_status_carries_no_part_of_the_key(self, monkeypatch):
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        status = api_key_status()
        assert FROM_ENVIRONMENT not in status
        assert FROM_ENVIRONMENT[:8] not in status

    def test_a_duplicate_key_error_does_not_quote_the_key(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nTYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert FROM_FILE not in str(caught.value)
        assert FROM_FILE[:8] not in str(caught.value)

    def test_a_malformed_line_error_does_not_echo_the_line(self, monkeypatch, tmp_path):
        # The line that broke the parse is a plausible place to put a key by mistake.
        install_secret_file(monkeypatch, tmp_path, f"{FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert FROM_FILE not in str(caught.value)
        assert FROM_FILE[:8] not in str(caught.value)

    def test_an_unexpected_name_error_does_not_echo_the_value(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_OTHER={FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        assert FROM_FILE not in str(caught.value)

    def test_the_error_names_the_problem_and_the_file(self, monkeypatch, tmp_path):
        path = install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nTYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        with pytest.raises(SecretFileError) as caught:
            read_secret_file()
        message = str(caught.value)
        assert "duplicate-key" in message
        assert path.name in message

    def test_the_missing_key_message_contains_no_key(self, monkeypatch):
        without_environment(monkeypatch)
        with pytest.raises(MissingApiKeyError) as caught:
            require_api_key()
        message = str(caught.value)
        assert client_module.API_KEY_ENV in message
        assert MISSING in message

    def test_the_unusable_status_carries_only_the_kind(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\nTYPESAFE_API_KEY=x\n")
        without_environment(monkeypatch)
        status = api_key_status()
        assert FROM_FILE not in status
        assert status == f"{UNUSABLE} (duplicate-key)"


class TestRepositoryRootResolution:
    """The loader finds the repository, not the working directory."""

    def test_the_secret_path_does_not_depend_on_the_working_directory(self, monkeypatch, tmp_path):
        before = secret_file_path()
        monkeypatch.chdir(tmp_path)
        assert secret_file_path() == before

    def test_the_secret_path_survives_a_subdirectory(self, monkeypatch):
        nested = client_module.repo_root() / "src" / "jev_lab"
        monkeypatch.chdir(nested)
        assert secret_file_path() == client_module.repo_root() / ".secrets" / "typesafe.env"

    def test_the_root_is_this_repository(self):
        root = client_module.repo_root()
        assert (root / "pyproject.toml").is_file()
        assert (root / "src" / "jev_lab" / "client.py").is_file()

    def test_the_secret_path_is_inside_the_repository(self):
        # A path outside the repository would mean a search had happened somewhere it should not.
        path = secret_file_path()
        assert client_module.repo_root() in path.parents
        assert path.name == client_module.SECRET_FILE_NAME

    def test_the_example_file_is_the_one_next_to_it(self):
        assert EXAMPLE_FILE.parent.name == ".secrets.example"
        assert EXAMPLE_FILE.parent.parent == client_module.repo_root()

    def test_the_loader_reads_one_path_and_no_other(self, monkeypatch, tmp_path):
        # Two candidate files exist; only the configured one is consulted.
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        (tmp_path / "other.env").write_text(f"TYPESAFE_API_KEY={FROM_ENVIRONMENT}\n", encoding="utf-8")
        without_environment(monkeypatch)
        assert read_secret_file() == FROM_FILE


class TestGitSafety:
    """The local secret file cannot be committed by accident."""

    @staticmethod
    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=client_module.repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_gitignore_names_the_secrets_directory(self):
        text = (client_module.repo_root() / ".gitignore").read_text(encoding="utf-8")
        rules = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        assert ".secrets/" in rules

    def test_gitignore_covers_a_secret_file_by_name_too(self):
        # Belt and braces: a `.env` written outside `.secrets/` is still ignored.
        text = (client_module.repo_root() / ".gitignore").read_text(encoding="utf-8")
        rules = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        for rule in (".env", "*.env", "*.secret", "*.secrets"):
            assert rule in rules

    @staticmethod
    def reported_pattern(output: str) -> str:
        """The rule git names for a path, e.g. ``.gitignore:28:.secrets/`` -> ``.secrets/``.

        A leading ``!`` in the pattern is the signal that the match re-includes the path. The exit
        code is not: `git check-ignore -v` reports a negation and still exits 0.
        """
        return output.split("\t")[0].split(":", 2)[-1]

    def test_git_ignores_the_local_secret_file(self):
        result = self.git("check-ignore", "-v", ".secrets/typesafe.env")
        assert result.returncode == 0
        pattern = self.reported_pattern(result.stdout)
        assert pattern == ".secrets/"
        assert not pattern.startswith("!")

    def test_git_ignores_any_file_inside_the_secrets_directory(self):
        # The rule is on the directory, so a differently-named credential is covered too.
        result = self.git("check-ignore", "-v", ".secrets/anything-at-all")
        assert self.reported_pattern(result.stdout) == ".secrets/"

    def test_the_local_secret_file_could_not_be_committed(self):
        # The strongest form of the claim, and the one that matters: git itself refuses the add.
        # `--dry-run` writes nothing.
        assert self.git("add", "--dry-run", ".secrets/typesafe.env").returncode != 0

    def test_the_local_secret_file_is_not_tracked(self):
        assert self.git("ls-files", "--", ".secrets").stdout.strip() == ""

    def test_no_secret_path_appears_in_history(self):
        assert self.git("log", "--all", "--oneline", "--", ".secrets/").stdout.strip() == ""

    def test_the_example_file_is_not_ignored(self):
        # The template is meant to be committed, so the ignore rules must not swallow it. It has
        # been tracked since the first commit, and plain `check-ignore` reports no rule at all for
        # a path already in the index -- so the rule itself is inspected with `--no-index`.
        result = self.git("check-ignore", "-v", "--no-index", ".secrets.example/typesafe.env")
        assert self.reported_pattern(result.stdout).startswith("!")

    def test_the_example_file_could_be_committed(self):
        assert self.git("add", "--dry-run", ".secrets.example/typesafe.env").returncode == 0

    def test_the_example_file_carries_a_placeholder_not_a_key(self):
        assert EXAMPLE_FILE.read_text(encoding="utf-8").strip() == "TYPESAFE_API_KEY=YOUR_TYPESAFE_API_KEY_HERE"

    def test_the_placeholder_is_a_value_the_loader_cannot_recognise(self):
        # A documented limitation, asserted so it cannot be forgotten: copy the template into place
        # without editing it and the loader reports a key, because the placeholder is a syntactically
        # valid value. Nothing here can tell it from a real key -- the API rejects it, loudly, which
        # is the fail-closed outcome. The README says to edit the file, and the file says so twice.
        assert read_secret_file(EXAMPLE_FILE) == "YOUR_TYPESAFE_API_KEY_HERE"


class TestTheSuiteGuard:
    """The guards in `conftest.py`, tested -- they are what keep live keys out of this process."""

    def test_tests_do_not_see_the_repositorys_secret_file(self):
        from conftest import real_secret_file

        # Asked through the module, the way production code asks: a test that imported the function
        # by name would hold the unwrapped one and this check would pass for the wrong reason.
        assert client_module.secret_file_path() != real_secret_file()

    def test_reaching_for_the_real_file_fails_loudly(self):
        from conftest import real_secret_file

        with pytest.raises(AssertionError):
            client_module.read_secret_file(real_secret_file())

    def test_reading_the_real_file_any_other_way_fails_loudly(self):
        from conftest import real_secret_file

        # The import-by-name path: the reader held directly, skipping the module attribute the
        # wrapper replaced. `Path.read_text` is the layer that stops this one.
        with pytest.raises(AssertionError):
            real_secret_file().read_text(encoding="utf-8")

    def test_the_guard_does_not_block_temporary_files(self, tmp_path):
        # A guard that failed everything would be as useless as no guard.
        assert read_secret_file(tmp_path / "absent.env") is None

    def test_the_suite_cannot_open_a_socket(self):
        import socket

        with pytest.raises(AssertionError):
            socket.create_connection(("api.typesafe.ai", 443), timeout=0.1)


class TestTheSdkReceivesTheKey:
    """The real `open_client` and the real SDK, over a mock transport. No socket is opened."""

    RESPONSE = {
        "model": "jev-1.13.0",
        "answers": {
            "department": {
                "type": "choice",
                "choice": "billing",
                "confidence": 0.8,
                "probabilities": {"billing": 0.9, "account": 0.1, "other": 0.0},
            }
        },
        "usage": {"input_tokens": 100, "output_tokens": 10},
    }

    def instrument_with(self, monkeypatch, captured):
        """Route the client's transport to a mock, keeping the real construction path."""

        def handler(request):
            captured["authorization"] = request.headers.get("authorization")
            return httpx2.Response(200, json=self.RESPONSE)

        def instrument(self, *, timeout, transport=None):
            self._attached = True
            return httpx2.Client(timeout=timeout, transport=httpx2.MockTransport(handler))

        monkeypatch.setattr(TransportProbe, "instrument", instrument)

    def test_the_key_from_the_local_file_reaches_the_wire(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        without_environment(monkeypatch)
        captured = {}
        self.instrument_with(monkeypatch, captured)
        # `probe=` is what routes the client through the mock. Without it `open_client` builds an
        # uninstrumented client, and the call goes to the real API -- which `conftest.no_network`
        # now turns into a failure instead of a live request.
        with open_client(model="jev-test", probe=TransportProbe()) as client:
            run_experiment(get_experiment("01_primitives"), client=client, recorder=UsageRecorder(tmp_path))
        assert captured["authorization"] == f"Bearer {FROM_FILE}"

    def test_the_environment_key_wins_on_the_wire(self, monkeypatch, tmp_path):
        install_secret_file(monkeypatch, tmp_path, f"TYPESAFE_API_KEY={FROM_FILE}\n")
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        captured = {}
        self.instrument_with(monkeypatch, captured)
        with open_client(model="jev-test", probe=TransportProbe()) as client:
            run_experiment(get_experiment("01_primitives"), client=client, recorder=UsageRecorder(tmp_path))
        assert captured["authorization"] == f"Bearer {FROM_ENVIRONMENT}"

    def test_the_sdk_still_resolves_the_environment_on_its_own(self, monkeypatch, tmp_path):
        # Our loader passes the key explicitly; the SDK's own documented behaviour is unchanged for
        # anyone constructing a client directly.
        monkeypatch.setenv(client_module.API_KEY_ENV, FROM_ENVIRONMENT)
        captured = {}
        instrumented = TransportProbe()
        self.instrument_with(monkeypatch, captured)
        from typesafe_sdk import TypeSafeClient

        with TypeSafeClient(model="jev-test", http_client=instrumented.instrument(timeout=5.0)) as client:
            run_experiment(get_experiment("01_primitives"), client=client, recorder=UsageRecorder(tmp_path))
        assert captured["authorization"] == f"Bearer {FROM_ENVIRONMENT}"

    def test_the_sdk_still_refuses_a_client_with_no_key_at_all(self, monkeypatch):
        from typesafe_sdk import TypeSafeClient, TypeSafeError

        without_environment(monkeypatch)
        with pytest.raises(TypeSafeError):
            TypeSafeClient(model="jev-test")
