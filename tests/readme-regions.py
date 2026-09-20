# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Only the inside of a marked region is ever written; everything else is byte-identical."""

from __future__ import annotations

from pathlib import Path

import pytest

from render import read_region, replace_region, update_readme


def test_replace_touches_only_the_region(repo):
    before = Path("README.md").read_text(encoding="utf-8")
    after = replace_region(before, "DISPATCHES", "new dispatches")
    assert read_region(after, "DISPATCHES") == "new dispatches"
    assert read_region(after, "MODULES") == "old modules"
    head, _, _ = before.partition("<!-- DISPATCHES:BEGIN -->")
    assert after.startswith(head)
    _, _, tail = before.partition("<!-- DISPATCHES:END -->")
    assert after.endswith(tail)


def test_missing_marker_refuses_to_write(repo):
    with pytest.raises(ValueError):
        replace_region("no markers here", "DISPATCHES", "x")


def test_update_readme_reports_change(repo):
    assert update_readme({"UPDATED": "Last updated now."}) is True
    assert update_readme({"UPDATED": "Last updated now."}) is False
    text = Path("README.md").read_text(encoding="utf-8")
    assert "prose before" in text and "prose after" in text
