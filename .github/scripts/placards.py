# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""What the placard pickers share: GitHub's API, text the kit can letter, and the settings they write.

issue.py and releases.py each pick something from GitHub and write it as
placards into the page's settings, .github/markdown.yaml, where
tannergolden/markdown reads every element it draws. Each picker owns one
region of the settings' `elements:` section, the lines between
`# NAME:start` and `# NAME:end`, and rewrites only those, so everything else
in the file stays as it was written. The placards name no print: the kit
draws them in the page's one theme. Stdlib only.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

API = "https://api.github.com"
UA = "tannergolden-profile"
# The README tells time in EST: every date it shows is the day in UTC-5, whatever the season.
EST = dt.timezone(dt.timedelta(hours=-5), "EST")
BANNED = {chr(0x2013): "an en dash", chr(0x2014): "an em dash", chr(0x2015): "a horizontal bar"}
# What the kit's outlines can letter: printable ASCII, the Latin-1 letters and a little typography.
LETTERS = ({chr(c) for c in range(0x20, 0x7F)} | {chr(c) for c in range(0xC0, 0x100)} - {chr(0xF7)}
           | {chr(c) for c in (0x2018, 0x2019, 0x201C, 0x201D, 0x2026)})
ELLIPSIS = chr(0x2026)

Fetch = Callable[..., bytes]  # (url, headers) for a GET, (url, headers, data) for a POST


def fetch_url(url: str, headers: dict, data: bytes | None = None) -> bytes:
    """A GET, or with `data` a POST, and the body of the answer."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **headers},
                                 method="GET" if data is None else "POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


# A request GitHub turns away for a rate limit waits as long as GitHub asks and tries again, twice
# at most. A longer wait than this means the limit will not lift within one run.
RETRIES = 2
LONGEST_WAIT = 90.0


def said_by(exc: urllib.error.HTTPError) -> str:
    """GitHub's own reason for an error response: the message in its JSON body, when it sent one."""
    try:
        return str(json.loads(exc.read() or b"{}").get("message", ""))[:200]
    except (OSError, ValueError, AttributeError):
        return ""


def wait_for(exc: urllib.error.HTTPError, said: str, now: float | None = None) -> float | None:
    """How long a rate-limited request should wait before trying again, or None when it should not."""
    if exc.code not in (403, 429):
        return None
    headers = exc.headers or {}
    retry, left, reset = (str(headers.get(k) or "").strip()
                          for k in ("retry-after", "x-ratelimit-remaining", "x-ratelimit-reset"))
    if retry.isdigit():
        wait = float(retry)
    elif left == "0" and reset.isdigit():
        wait = max(0.0, float(reset) - (time.time() if now is None else now)) + 1
    elif "rate limit" in said.lower():
        wait = 60.0  # a secondary limit that names no time: GitHub asks for at least a minute
    else:
        return None
    return wait if wait <= LONGEST_WAIT else None


def _headers(token: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github(fetch: Fetch, path: str, token: str = "", params: dict | None = None,
           sleep: Callable[[float], None] = time.sleep) -> Any:
    """One call to GitHub's REST API, parsed.

    A rate limit is waited out as GitHub asks, RETRIES times at most. Any other HTTPError (a 404
    included) reaches the caller, carrying GitHub's own reason so a notice can say why.
    """
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    return _answer(fetch, url, _headers(token), None, sleep)


def graphql(fetch: Fetch, query: str, variables: dict, token: str,
            sleep: Callable[[float], None] = time.sleep) -> dict:
    """One GraphQL query, and its data. An answer that is only errors raises ValueError, naming them."""
    body = json.dumps({"query": query, "variables": variables}).encode()
    answer = _answer(fetch, API + "/graphql", _headers(token), body, sleep)
    if not isinstance(answer, dict) or not isinstance(answer.get("data"), dict):
        errors = answer.get("errors") if isinstance(answer, dict) else None
        said = "; ".join(str(e.get("message", "")) for e in errors or [] if isinstance(e, dict))
        raise ValueError(f"GraphQL: {said or 'no data'}"[:300])
    return answer["data"]


def _answer(fetch: Fetch, url: str, headers: dict, data: bytes | None, sleep: Callable[[float], None]) -> Any:
    """The parsed answer to one request, rate limits waited out as GitHub asks."""
    for attempt in range(RETRIES + 1):
        try:
            return json.loads(fetch(url, headers) if data is None else fetch(url, headers, data))
        except urllib.error.HTTPError as exc:
            said = said_by(exc)
            wait = wait_for(exc, said)
            if wait is None or attempt == RETRIES:
                raise urllib.error.HTTPError(exc.url, exc.code, f"{exc.reason}: {said}" if said else exc.reason,
                                             exc.headers, None) from exc
            print(f"GitHub asked for a wait ({exc.code}{': ' + said if said else ''}); trying again in {wait:.0f}s")
            sleep(wait)
    raise AssertionError("unreachable")


def letterable(text: str, limit: int = 150) -> str | None:
    """A stranger's text as plain text the kit can draw, or None when too much of it cannot be."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub("\\s*[" + chr(0x2014) + chr(0x2015) + "]\\s*", " - ", text).replace(chr(0x2013), "-")
    text = unicodedata.normalize("NFC", text)
    letters = [ch for ch in text if unicodedata.category(ch).startswith("L")]
    kept = "".join(ch if ch in LETTERS else " " for ch in text)
    lost = sum(1 for ch in letters if ch not in LETTERS)
    kept = re.sub(r"\s+", " ", kept).strip(" -:")
    if len(kept) < 12 or lost > len(letters) * 0.2:  # a text in a script the kit cannot draw: skip it
        return None
    if len(kept) > limit:
        kept = kept[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-") + ELLIPSIS
    return kept


def eastern(stamp: str) -> dt.datetime:
    """An ISO 8601 time from GitHub's API, as it was in EST."""
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(EST)


def sentence(text: str) -> str:
    return text if text.endswith((".", "?", "!", ELLIPSIS)) else text + "."


def day(d: dt.date) -> str:
    """A date the way a placard's cell shows it: 26 SEP."""
    return f"{d.day} {d.strftime('%b').upper()}"


def _text(value: Any) -> str:
    """A value as YAML reads it back unchanged: double-quoted text, whose escapes JSON's are a part of."""
    return json.dumps(value, ensure_ascii=False)


def dump(doc: dict) -> str:
    """The placards as entries of the settings' `elements:` section: two spaces in, one field a line."""
    lines = []
    for eid, card in doc["elements"].items():
        lines.append(f"  {eid}:")
        for key, value in card.items():
            if key == "cells":
                lines.append("    cells:")
                lines += [f"      - [{_text(label)}, {_text(said)}]" for label, said in value]
            else:
                lines.append(f"    {key}: {_text(value)}")
    out = "".join(line + "\n" for line in lines)
    for ch, name in BANNED.items():
        if ch in out:
            raise SystemExit(f"the placards contain {name}")
    return out


def _region(lines: list[str], path: Path, name: str) -> tuple[int, int]:
    """The indexes of the region's `# NAME:start` and `# NAME:end` lines."""
    starts = [i for i, line in enumerate(lines) if line.strip().startswith(f"# {name}:start")]
    ends = [i for i, line in enumerate(lines) if line.strip().startswith(f"# {name}:end")]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise SystemExit(f"{path}: expected one '# {name}:start' line, and one '# {name}:end' line after it")
    return starts[0], ends[0]


def read(path: Path, name: str) -> dict:
    """The placards the region holds now, as `dump` wrote them: {"elements": {id: placard}}."""
    lines = path.read_text(encoding="utf-8").splitlines()
    a, b = _region(lines, path, name)
    cards: dict = {}
    card: dict = {}
    for line in lines[a + 1:b]:
        if not line.strip():
            continue
        if line.startswith("      - "):
            card["cells"].append(json.loads(line[8:]))
        elif line.startswith("    "):
            key, _, value = line.strip().partition(":")
            card[key] = [] if key == "cells" else json.loads(value)
        else:
            card = cards[line.strip().rstrip(":")] = {}
    return {"elements": cards}


def write(path: Path, name: str, doc: dict) -> bool:
    """Write the placards into the region, when they changed. True when they did."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    a, b = _region(lines, path, name)
    new = "".join(lines[:a + 1]) + dump(doc) + "".join(lines[b:])
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True
