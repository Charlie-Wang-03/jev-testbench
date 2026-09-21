"""Shared test guards. Two invariants the rest of the suite is allowed to assume.

1. **No test may read this machine's real ``.secrets/typesafe.env``.**
2. **No test may open a network connection.**

The first matters because that file is a live credential once its owner fills it in, and the suite
runs on the same machine. Without a guard, any test that clears ``TYPESAFE_API_KEY`` and asks the
loader a question would be answered by whatever is in the local file -- so the suite would pass or
fail depending on a secret it must never touch, and a live key would be pulled into a test process
for no reason.

The second matters because an offline suite is only offline as long as somebody remembers to build
its transport. A test that passes an uninstrumented client reaches the real API, spends real money,
and records a real measurement in a temporary directory where nobody sees it. That happened once
while this file was being written, which is why the guard is here rather than in a comment.

Each guard fails loudly rather than silently doing something else, and each is redundant on purpose:
the cheap, readable layer is the one a reader will understand, and the blunt one is the one that
holds when the readable layer is bypassed.
"""

import socket
from pathlib import Path

import pytest

from jev_lab import client as client_module


def real_secret_file() -> Path:
    """The path a test must never read: this repository's own local secret file."""
    return client_module.repo_root() / client_module.SECRET_DIR_NAME / client_module.SECRET_FILE_NAME


@pytest.fixture(autouse=True)
def no_real_secret_file(monkeypatch, tmp_path):
    """Point the loader at an empty scratch path, and refuse to read the real one.

    Every test in this suite therefore sees *missing* from the local-file source unless it writes a
    file of its own. A test that wants one calls ``install_secret_file`` (or sets
    ``secret_file_path`` itself) and wins, because it runs after this fixture.

    Three layers, because the first one is easy to walk around:

    * ``secret_file_path`` is redirected, so the loader resolves a scratch path. Every internal
      caller goes through the module global and picks this up.
    * ``read_secret_file`` is wrapped, so handing the real path to it directly fails. This only
      covers callers that reach it as ``client.read_secret_file``: a test that does
      ``from jev_lab.client import read_secret_file`` holds the unwrapped function.
    * ``Path.read_text`` is wrapped, which is the layer that actually closes the hole -- the key is
      read by exactly one call, and no import style can get past the method it is read by.

    Yields the scratch path, which is deliberately never created. Note that the third layer means a
    test cannot read the real file even to assert something benign about it; that is the point, and
    a test that needs to know about the real file (e.g. that git ignores it) should ask git.
    """
    real = real_secret_file().resolve()
    decoy = tmp_path / client_module.SECRET_FILE_NAME
    monkeypatch.setattr(client_module, "secret_file_path", lambda: decoy)

    original_reader = client_module.read_secret_file

    def guarded_reader(path=None):
        target = Path(path or client_module.secret_file_path()).resolve()
        if target == real:
            raise AssertionError(_message(real))
        return original_reader(path)

    monkeypatch.setattr(client_module, "read_secret_file", guarded_reader)

    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if Path(self).resolve() == real:
            raise AssertionError(_message(real))
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    return decoy


def _message(real: Path) -> str:
    return (
        f"a test tried to read the repository's real secret file ({real.as_posix()}); "
        "tests must point the loader at a temporary file instead"
    )


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any attempt to open a socket. The suite is offline; `httpx2.MockTransport` is the way.

    Blunt by design and deliberately not limited to this project's code: it does not matter which
    layer would have made the connection, only that none is made. A blocked test is a test that was
    about to spend money and write a record nobody would read.
    """

    def blocked(*_args, **_kwargs):
        raise AssertionError(
            "a test tried to open a network connection; the suite must stay offline "
            "(build the client on an httpx2.MockTransport instead)"
        )

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
