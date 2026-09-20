# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The probe writes nothing; the dispatch badge goes red on failure and green again after."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import cards
import dispatches
import modules
import sources

ROOT = Path(__file__).resolve().parents[1]
KIT = Path(os.environ.get("EMBLEMS_KIT", ".emblems/src/badge-kit.py"))


def good(ledger, today):
    return sources.Dispatch(kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 1, Host Software", title="RFC 1", body="b", identifier="1", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc1", license="freely reproducible",)


def empty(ledger, today):
    return None


def broken(ledger, today):
    raise RuntimeError("the wiki is down <!-- --> \u2014 badly")


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}


def test_probe_reports_every_source_and_writes_nothing(repo, monkeypatch, capsys):
    monkeypatch.setattr(sources, "FETCHERS", {"rfc": good, "eol": empty, "lobsters": broken})
    monkeypatch.setattr(modules, "terminal_tip", lambda ledger: {"command": "jq"})
    monkeypatch.setattr(cards, "github_stats", lambda login, token: {"public_repos": 7, "languages": {"Python": 1}, "commits": 412})
    summary = repo / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    before = snapshot(repo)

    assert dispatches.probe() == 1  # one source raised
    out = capsys.readouterr().out
    # The name column is padded to the widest row, so match on the rest.
    rows = {line.split("  ")[0]: line.split("  ", 1)[1].strip() for line in out.splitlines() if line.strip()}
    assert rows["rfc"] == "ok     docs(rfc): \U0001F4DD record RFC 1, Host Software"
    assert rows["eol"] == "empty  nothing available today"
    assert rows["lobsters"].startswith("error  RuntimeError('the wiki is down") and "\u2014" not in out
    assert rows["tip"] == "ok     jq"
    assert rows["stats"] == "ok     7 public repositories, 1 languages, commits 412"

    after = snapshot(repo)
    assert {k: v for k, v in after.items() if k != "summary.md"} == before
    text = summary.read_text(encoding="utf-8")
    assert "| rfc | ✅ ok |" in text and "| lobsters | ❌ error |" in text and "<!--" not in text


def test_probe_is_clean_when_everything_answers(repo, monkeypatch):
    monkeypatch.setattr(sources, "FETCHERS", {"rfc": good})
    monkeypatch.setattr(modules, "terminal_tip", lambda ledger: None)
    monkeypatch.setattr(cards, "github_stats", lambda login, token: None)
    assert dispatches.probe() == 0


@pytest.fixture
def badge_repo(repo, monkeypatch):
    if not KIT.is_absolute() and not (ROOT / KIT).exists() and not KIT.exists():
        pytest.skip("the emblems kit is not checked out; set EMBLEMS_KIT")
    kit = KIT if KIT.is_absolute() else (ROOT / KIT)
    monkeypatch.setenv("EMBLEMS_KIT", str(kit))
    (repo / ".github").mkdir()
    shutil.copy(ROOT / ".github" / "badges.yml", repo / ".github" / "badges.yml")
    subprocess.run(["git", "init", "--quiet", "-b", "Development"], check=True)
    subprocess.run(["git", "config", "user.name", "A Person"], check=True)
    subprocess.run(["git", "config", "user.email", "person@example.test"], check=True)
    monkeypatch.setenv("DISPATCH_NO_PUSH", "1")
    return repo


def subjects():
    return subprocess.run(["git", "log", "--format=%s"], capture_output=True, text=True, check=True).stdout.splitlines()


def test_a_failed_run_turns_the_badge_red_and_a_good_one_turns_it_back(badge_repo):
    assert dispatches.badge_status() == "Passing"

    dispatches.mark_failed(RuntimeError("boom \u2014 with a dash"))
    assert dispatches.badge_status() == "Failing"
    assert subjects()[0] == "ci(dispatches): \u2699\ufe0f mark the last run as failed"
    body = subprocess.run(["git", "log", "-1", "--format=%b"], capture_output=True, text=True, check=True).stdout
    assert "RuntimeError: boom - with a dash" in body and "\u2014" not in body
    changed = subprocess.run(["git", "show", "--stat", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    assert ".github/badges.yml" in changed and "assets/badges/dynamic/dispatches.svg" in changed

    dispatches.mark_passing()
    assert dispatches.badge_status() == "Passing"
    assert subjects()[0] == "ci(dispatches): \U0001F552 mark the run passing again"

    dispatches.mark_passing()  # already green: nothing to do, nothing committed
    assert len(subjects()) == 2


def test_the_failure_commit_carries_none_of_the_failed_runs_writes(badge_repo, moment):
    from render import append_dispatch, record_recent
    from sources import Dispatch

    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "seed"], check=True)
    entry = Dispatch(kind="release", commit_type="feat", emoji="\u2728", subject="note X 1.0", title="X 1.0", body="b", identifier="x/x@v1.0", source_name="x/x", source_url="https://github.com/x/x/releases/tag/v1.0", license="Release metadata, reported as fact")
    path = append_dispatch(entry, moment)  # a run that got this far, then died
    record_recent(entry, moment, path)

    dispatches.mark_failed(RuntimeError("died after writing"))

    changed = subprocess.run(["git", "show", "--stat", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    assert "dispatches/" not in changed and "state/" not in changed
    assert ".github/badges.yml" in changed and "assets/badges/dynamic/dispatches.svg" in changed
    assert not Path(path).exists() and not Path("state/recent.json").exists()
    assert subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout == ""
    page = Path("README.md").read_text(encoding="utf-8")
    assert "No dispatches yet" in page


def test_main_marks_a_failure_and_still_raises(badge_repo, monkeypatch):
    monkeypatch.setattr(sources, "pick_dispatch", broken)
    monkeypatch.setattr(sys, "argv", ["dispatches.py", "--mode", "dispatch"])
    with pytest.raises(RuntimeError, match="the wiki is down"):
        dispatches.main()
    assert dispatches.badge_status() == "Failing"
