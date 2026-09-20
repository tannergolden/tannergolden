# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The commit itself: authored by the person, committed by the machine, signed, from a file."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import dispatches
from render import commit_message
from sources import Dispatch


def run(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def test_author_is_the_person_and_committer_is_the_workflow(repo, monkeypatch):
    run("init", "--quiet", "-b", "Development")
    run("config", "user.name", "Claude")
    run("config", "user.email", "noreply@anthropic.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "github-actions[bot]")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com")
    monkeypatch.setenv("DISPATCH_NO_PUSH", "1")
    Path("dispatches").mkdir()
    Path("dispatches/2026").mkdir()
    Path("dispatches/2026/September.md").write_text("entry\n", encoding="utf-8")

    entry = Dispatch(
        kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 2324, HTCPCP",
        title="RFC 2324", body="A teapot.", identifier="2324", source_name="RFC Editor",
        source_url="https://www.rfc-editor.org/rfc/rfc2324", license="freely reproducible",
    )
    assert dispatches.commit(commit_message(entry)) is True
    assert dispatches.commit(commit_message(entry)) is False  # nothing left to stage

    who = run("log", "-1", "--format=%an <%ae>|%cn <%ce>").strip()
    assert who == (
        "Tanner Golden <24684994+tannergolden@users.noreply.github.com>"
        "|github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"
    )
    message = run("log", "-1", "--format=%B")
    assert message.startswith("docs(rfc): \U0001F4DD record RFC 2324, HTCPCP\n\nA teapot.\n")
    assert "Signed-off-by: Tanner Golden <24684994+tannergolden@users.noreply.github.com>" in message
    assert run("show", "--stat", "--format=", "HEAD").count("dispatches/2026/September.md") == 1
    dispatches.push()  # honours DISPATCH_NO_PUSH and returns without a remote
    assert os.environ["DISPATCH_NO_PUSH"] == "1"


def test_a_local_run_keeps_the_configured_committer(repo, monkeypatch):
    run("init", "--quiet", "-b", "Development")
    run("config", "user.name", "A Person")
    run("config", "user.email", "person@example.test")
    for key in ("GITHUB_ACTIONS", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(key, raising=False)
    Path("dispatches").mkdir()
    Path("dispatches/x.md").write_text("x\n", encoding="utf-8")
    entry = Dispatch(
        kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 1, Host Software", title="RFC 1", body="b", identifier="1", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc1", license="freely reproducible",
    )
    assert dispatches.commit(commit_message(entry))
    assert run("log", "-1", "--format=%an|%cn <%ce>").strip() == "Tanner Golden|A Person <person@example.test>"


def test_under_actions_the_committer_defaults_to_the_bot(repo, monkeypatch):
    run("init", "--quiet", "-b", "Development")
    run("config", "user.name", "A Person")
    run("config", "user.email", "person@example.test")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    for key in ("GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(key, raising=False)
    Path("dispatches").mkdir()
    Path("dispatches/x.md").write_text("x\n", encoding="utf-8")
    entry = Dispatch(
        kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 1, Host Software", title="RFC 1", body="b", identifier="1", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc1", license="freely reproducible",
    )
    assert dispatches.commit(commit_message(entry))
    assert run("log", "-1", "--format=%cn").strip() == "github-actions[bot]"
