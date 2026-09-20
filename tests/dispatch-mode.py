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
        kind="release", commit_type="feat", emoji="✨", subject="note Go 1.25.0",
        title="Go 1.25.0", body="Go 1.25.0 was published 2 days ago.", identifier="golang/go@v1.25.0",
        source_name="golang/go", source_url="https://github.com/golang/go/releases/tag/v1.25.0",
        license="Release metadata, reported as fact",
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
    assert log == ["feat(release): ✨ note Go 1.25.0"]
    schedule = Schedule("state/schedule.json")
    assert not schedule.is_fresh
    # The refresh is deliberately left due, so the next tick fills the page.
    assert "next_refresh" not in json.loads(Path("state/schedule.json").read_text(encoding="utf-8"))
    assert schedule.next_refresh < schedule.next_dispatch
    ledger = json.loads(Path("state/ledger.json").read_text(encoding="utf-8"))
    assert ledger == {"release": ["golang/go@v1.25.0"]}
    committed = subprocess.run(["git", "show", "--stat", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    for path in ("README.md", "dispatches/2026/September.md", "state/ledger.json", "state/recent.json", "state/schedule.json"):
        assert path in committed, path
    page = Path("README.md").read_text(encoding="utf-8")
    assert "| `feat(release)` | [Go 1.25.0](dispatches/2026/September.md#dispatch-" in page
