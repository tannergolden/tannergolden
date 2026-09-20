# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""`--mode dispatch` sends exactly one dispatch, commits it, and moves the schedule."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import dispatches
import sources
from sources import Dispatch
from state import Schedule


def fake_pick(ledger, today):
    return Dispatch(
        kind="trending", commit_type="feat", emoji="✨", subject="star someone/fast-thing",
        title="someone/fast-thing", body="4200 stars on a repository first pushed 9 days ago.",
        identifier="someone/fast-thing", source_name="GitHub",
        source_url="https://github.com/someone/fast-thing",
        license="Repository metadata, reported as fact",
    )


def test_dispatch_mode_sends_one_and_reschedules(repo, monkeypatch):
    subprocess.run(["git", "init", "--quiet", "-b", "Development"], check=True)
    subprocess.run(["git", "config", "user.name", "A Person"], check=True)
    subprocess.run(["git", "config", "user.email", "person@example.test"], check=True)
    monkeypatch.setenv("DISPATCH_NO_PUSH", "1")
    monkeypatch.setattr(sources, "pick_dispatch", fake_pick)
    monkeypatch.setattr(sys, "argv", ["dispatches.py", "--mode", "dispatch"])

    assert dispatches.main() == 0

    log = subprocess.run(["git", "log", "--format=%s"], capture_output=True, text=True, check=True).stdout.splitlines()
    assert log == ["feat(trending): ✨ star someone/fast-thing"]
    schedule = Schedule("state/schedule.json")
    assert not schedule.is_fresh
    # The refresh is deliberately left due, so the next tick fills the page.
    assert "next_refresh" not in json.loads(Path("state/schedule.json").read_text(encoding="utf-8"))
    assert schedule.next_refresh < schedule.next_dispatch
    ledger = json.loads(Path("state/ledger.json").read_text(encoding="utf-8"))
    # The kind's own id, and the link claim every kind also files.
    assert ledger == {"trending": ["someone/fast-thing"],
                      "link": ["github.com/someone/fast-thing"]}
    committed = subprocess.run(["git", "show", "--stat", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    for path in ("README.md", "dispatches/2026/September.md", "state/ledger.json", "state/recent.json", "state/schedule.json"):
        assert path in committed, path
    page = Path("README.md").read_text(encoding="utf-8")
    assert "| `feat(trending)` | [someone/fast-thing](dispatches/2026/September.md#dispatch-" in page
