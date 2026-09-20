# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Fixtures: a scratch repository tree to write into, and a page with regions."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

PAGE = """<!-- frontmatter -->
# Title

prose before

<!-- TYPING:BEGIN -->
old typing
<!-- TYPING:END -->

<!-- JOURNAL:BEGIN -->
old journal
<!-- JOURNAL:END -->

<!-- MODULES:BEGIN -->
<!-- MODULES:END -->

<!-- CARDS:BEGIN -->
<!-- CARDS:END -->

prose after

<!-- UPDATED:BEGIN -->
<!-- UPDATED:END -->
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Run inside an empty repository tree with a page carrying every region."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "profile.json").write_text('{"phrases": ["one", "two"], "issue_languages": ["Python"]}', encoding="utf-8")
    os.makedirs(tmp_path / "state", exist_ok=True)
    return tmp_path


@pytest.fixture
def moment():
    return datetime(2026, 9, 20, 17, 5, 9, tzinfo=timezone.utc)  # 13:05:09 in New York
