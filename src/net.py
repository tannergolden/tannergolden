# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""A small HTTPS client, because nine sources is not a reason to add a dependency.

Stdlib only, matching the rest of this account's tooling: the workflow runs on
a bare `python3` with nothing to install and nothing to cache.

Three behaviours are deliberate. Requests carry a descriptive User-Agent,
because Wikidata rejects a request without one and every other source here is
a volunteer project entitled to know who is calling. Responses are read
through a size ceiling, so a source that starts returning a gigabyte cannot
take the runner down with it. And a failure returns None rather than raising,
because a source being down is an ordinary Tuesday: the caller falls back to
another kind, which is the designed response to any source failing.
"""

from __future__ import annotations

import gzip
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from config import USER_AGENT

TIMEOUT = 30
ATTEMPTS = 3
MAX_BYTES = 32 * 1024 * 1024


def _fetch(url: str, *, accept: str, extra: dict | None = None, data: bytes | None = None, timeout: int = TIMEOUT) -> bytes | None:
    if not url.lower().startswith("https://"):
        raise ValueError(f"refusing a non-HTTPS request to {url!r}")

    headers = {"User-Agent": USER_AGENT, "Accept": accept, "Accept-Encoding": "gzip"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    headers.update(extra or {})
    request = urllib.request.Request(url, data=data, headers=headers)  # noqa: S310 - scheme is checked above

    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    print(f"::warning::{url} exceeded {MAX_BYTES} bytes; discarding.")
                    return None
                if response.headers.get("Content-Encoding") == "gzip":
                    # Inflate through the same ceiling: a small compressed
                    # body can be a very large one once decompressed.
                    body = gzip.GzipFile(fileobj=io.BytesIO(body)).read(MAX_BYTES + 1)
                    if len(body) > MAX_BYTES:
                        print(f"::warning::{url} inflated past {MAX_BYTES} bytes; discarding.")
                        return None
                return body
        except urllib.error.HTTPError as exc:
            # A 4xx is an answer, not an outage: the thing is not there, or
            # not for us. Asking again would only get the same answer slower.
            if 400 <= exc.code < 500 and exc.code != 429:
                print(f"::warning::{url} answered {exc.code}.")
                return None
            if attempt == ATTEMPTS - 1:
                print(f"::warning::{url} failed after {ATTEMPTS} attempts ({exc}).")
                return None
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, OSError, ValueError, EOFError, gzip.BadGzipFile) as exc:
            if attempt == ATTEMPTS - 1:
                print(f"::warning::{url} failed after {ATTEMPTS} attempts ({exc}).")
                return None
            # Linear rather than exponential: these are polite retries against
            # volunteer infrastructure, not a race to get served.
            time.sleep(2 * (attempt + 1))
    return None


def github_headers(token: str | None) -> dict:
    """The headers every call to api.github.com carries, the API version pinned."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_json(url: str, params: dict | None = None, *, timeout: int = TIMEOUT) -> Any | None:
    return get_json_with_headers(url, params, None, timeout=timeout)


def get_json_with_headers(url: str, params: dict | None, headers: dict | None, *, timeout: int = TIMEOUT) -> Any | None:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    body = _fetch(url, accept="application/json", extra=headers, timeout=timeout)
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except ValueError as exc:
        print(f"::warning::{url} did not return JSON ({exc}).")
        return None


def get_text(url: str, params: dict | None = None) -> str | None:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    body = _fetch(url, accept="text/plain, text/html;q=0.9, */*;q=0.8")
    return None if body is None else body.decode("utf-8", "replace")


def post_json(url: str, payload: dict, headers: dict | None) -> Any | None:
    body = _fetch(url, accept="application/json", extra=headers, data=json.dumps(payload).encode("utf-8"))
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except ValueError as exc:
        print(f"::warning::{url} did not return JSON ({exc}).")
        return None
