# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The HTTPS client: 4xx is an answer, gzip is bounded, and nothing leaves over plain HTTP."""

from __future__ import annotations

import gzip
import io
import urllib.error
import urllib.request

import pytest

import net


class Response:
    def __init__(self, body, headers=None):
        self.body, self.headers = body, headers or {}

    def read(self, n=-1):
        return self.body if n < 0 else self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_a_404_is_not_retried(monkeypatch):
    calls = []

    def urlopen(request, timeout):
        calls.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO(b""))

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(net.time, "sleep", lambda s: None)
    assert net.get_json("https://x.example/missing") is None
    assert len(calls) == 1


def test_a_truncated_gzip_body_is_a_failure_not_a_crash(monkeypatch):
    payload = gzip.compress(b'{"a": 1}' * 100)[:-8]
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: Response(payload, {"Content-Encoding": "gzip"}))
    monkeypatch.setattr(net.time, "sleep", lambda s: None)
    assert net.get_json("https://x.example/") is None


def test_an_inflated_body_is_capped(monkeypatch):
    monkeypatch.setattr(net, "MAX_BYTES", 64)
    payload = gzip.compress(b"x" * 10_000)
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: Response(payload, {"Content-Encoding": "gzip"}))
    assert net.get_text("https://x.example/") is None
    small = gzip.compress(b"hello")
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: Response(small, {"Content-Encoding": "gzip"}))
    assert net.get_text("https://x.example/") == "hello"


def test_plain_http_is_refused():
    with pytest.raises(ValueError):
        net.get_text("http://x.example/")


def test_github_headers_pin_the_api_version():
    assert net.github_headers(None) == {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    assert net.github_headers("t")["Authorization"] == "Bearer t"
