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

<!-- MASTHEAD:BEGIN -->
<!-- MASTHEAD:END -->

<!-- AVAILABILITY:BEGIN -->
<!-- AVAILABILITY:END -->

<!-- DISPATCHES:BEGIN -->
old dispatches
<!-- DISPATCHES:END -->

<!-- MODULES:BEGIN -->
old modules
<!-- MODULES:END -->

prose after

<!-- UPDATED:BEGIN -->
<!-- UPDATED:END -->
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Run inside an empty repository tree with a page carrying every region."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text(PAGE, encoding="utf-8")
    (tmp_path / "profile.json").write_text('{"login": "someone"}', encoding="utf-8")
    os.makedirs(tmp_path / "state", exist_ok=True)
    return tmp_path


@pytest.fixture
def moment():
    return datetime(2026, 9, 20, 17, 5, 9, tzinfo=timezone.utc)  # 13:05:09 in New York


class FakeNet:
    """Serve canned responses to the network module, keyed by URL prefix.

    A test registers `text(prefix, body)` and `json(prefix, payload)`;
    anything unregistered answers None, which is what a source that is
    down answers. Every request is recorded so a test can assert what was
    asked for.
    """

    def __init__(self):
        self.texts = []
        self.jsons = []
        self.requests = []

    def text(self, prefix, body):
        self.texts.append((prefix, body))
        return self

    def json(self, prefix, payload):
        self.jsons.append((prefix, payload))
        return self

    def _lookup(self, table, url):
        self.requests.append(url)
        for prefix, value in table:
            if url.startswith(prefix):
                return value(url) if callable(value) else value
        return None

    def get_text(self, url, params=None, **kw):
        return self._lookup(self.texts, _with_params(url, params))

    def get_json(self, url, params=None, **kw):
        return self._lookup(self.jsons, _with_params(url, params))

    def get_json_with_headers(self, url, params, headers, **kw):
        return self._lookup(self.jsons, _with_params(url, params))

    def post_json(self, url, payload, headers, **kw):
        return self._lookup(self.jsons, url)


def _with_params(url, params):
    if not params:
        return url
    from urllib.parse import urlencode

    return f"{url}?{urlencode(params)}"


@pytest.fixture
def fake_net(monkeypatch):
    import net

    fake = FakeNet()
    for name in ("get_text", "get_json", "get_json_with_headers", "post_json"):
        monkeypatch.setattr(net, name, getattr(fake, name))
    return fake


@pytest.fixture
def seeded(monkeypatch):
    """A deterministic generator in place of the OS one, for tests only."""
    import random

    import modules
    import phrasing
    import sources

    rng = random.Random(7)  # noqa: S311 - a test seed
    monkeypatch.setattr(sources, "_RNG", rng)
    monkeypatch.setattr(phrasing, "_RNG", rng)
    monkeypatch.setattr(modules, "_RNG", rng)
    return rng
