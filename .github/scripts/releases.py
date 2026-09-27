#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Pick the README's latest releases: the two repositories on this account that shipped most recently.

  python3 .github/scripts/releases.py .github/releases.json [--owner tannergolden]

Every Wednesday it lists the account's public repositories, leaving out forks
and archived ones, and reads each one's latest release from GitHub's API.
The two published most recently become two placards for the elements kit
(tannergolden/banners/elements), which draws them in the page's one theme and
fills the README's elements:release-1 and elements:release-2 blocks. Each
shows the version, the day it shipped and the major tag a stub pins, and
links to its release notes. The account prunes superseded releases, so the
latest release is the only one a repository keeps.

If GitHub cannot be reached, last week's placards stay; a first run with no
release to show writes nothing. Stdlib only, with placards.py beside it;
reads GH_TOKEN when it is set.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import urllib.error
from dataclasses import dataclass
from pathlib import Path

from placards import LETTERS, Fetch, day, eastern, fetch_url, github, letterable, sentence, write

OWNER = "tannergolden"
SLOTS = ("release-1", "release-2")  # the README's element blocks, left to right
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass
class Release:
    owner: str
    name: str
    tag: str
    url: str
    published: dt.datetime
    about: str      # the repository's own description, letterable
    language: str
    pinned: str     # "@v1" when the major tag a stub pins stands beside the release, else ""


def repositories(fetch: Fetch, owner: str, token: str) -> list[dict]:
    """The account's public repositories, without forks or archived ones."""
    repos = github(fetch, f"/users/{owner}/repos", token, {"type": "owner", "sort": "pushed", "per_page": 100})
    return [r for r in repos if not r.get("fork") and not r.get("archived") and not r.get("private")]


def _missing(exc: urllib.error.HTTPError) -> bool:
    return exc.code == 404


def latest(fetch: Fetch, owner: str, name: str, token: str) -> dict | None:
    """The repository's latest release, or None when it has never published one."""
    try:
        rel = github(fetch, f"/repos/{owner}/{name}/releases/latest", token)
    except urllib.error.HTTPError as exc:
        if _missing(exc):
            return None
        raise
    usable = (rel.get("tag_name") and rel.get("published_at") and not rel.get("draft") and not rel.get("prerelease")
              and str(rel.get("html_url", "")).startswith("https://github.com/"))
    return rel if usable else None


def pinned(fetch: Fetch, owner: str, name: str, tag: str, token: str) -> str:
    """'@v1' when the moving major tag a stub pins exists beside the release, else ''."""
    m = SEMVER.match(tag)
    if not m:
        return ""
    major = f"v{m.group(1)}"
    try:
        github(fetch, f"/repos/{owner}/{name}/git/ref/tags/{major}", token)
    except urllib.error.HTTPError as exc:
        if _missing(exc):
            return ""
        raise
    return "@" + major


def about(text: str) -> str:
    """The repository's own description, cut at its first sentence when it runs long, else at its first clause."""
    text = (text or "").strip()
    if len(text) > 150:
        text = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    if len(text) > 150:
        # One long sentence: the part before its first colon or semicolon says what the project is.
        head = re.split(r"\s*[:;]\s", text, maxsplit=1)[0].rstrip(" ,")
        if len(head) >= 24:
            text = head + "."
    return letterable(text) or ""


def choose(fetch: Fetch, owner: str, token: str = "", want: int = len(SLOTS)) -> list[Release]:
    """The repositories whose latest release was published most recently, newest first."""
    found = []
    for repo in repositories(fetch, owner, token):
        rel = latest(fetch, owner, repo["name"], token)
        if rel:
            found.append((rel, repo))
    found.sort(key=lambda pair: pair[0]["published_at"], reverse=True)
    return [Release(owner=owner, name=repo["name"], tag=rel["tag_name"], url=rel["html_url"],
                    published=eastern(rel["published_at"]),
                    about=about(repo.get("description") or ""),
                    language="".join(ch for ch in (repo.get("language") or "")[:24] if ch in LETTERS).strip(),
                    pinned=pinned(fetch, owner, repo["name"], rel["tag_name"], token))
            for rel, repo in found[:want]]


def placard(r: Release) -> dict:
    """One placard for the elements kit: the repository on the plate, its release in the cells."""
    third = ["Pinned as", r.pinned.upper()] if r.pinned else ["Language", (r.language or "Not set").upper()]
    return {
        "kind": "placard", "owner": r.owner, "name": r.name, "icon": "package", "link": r.url,
        "desc": sentence(r.about) if r.about else f"Release {r.tag}.",
        "cells": [["Release", r.tag.upper()], ["Published", day(r.published.date())], third],
    }


def document(releases: list[Release]) -> dict:
    return {"elements": dict(zip(SLOTS, (placard(r) for r in releases)))}


def main(argv: list[str] | None = None, fetch: Fetch = fetch_url) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("data", type=Path, help="the elements kit's data file for the two placards")
    ap.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER") or OWNER)
    args = ap.parse_args(argv)
    try:
        releases = choose(fetch, args.owner, os.environ.get("GH_TOKEN", ""))
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        print(f"::notice::GitHub unavailable ({type(exc).__name__}: {exc})")
        releases = []
    if not releases:
        print("nothing drawn: " + ("last week's placards stay" if args.data.exists() else "no release to show yet"))
        return 0
    changed = write(args.data, document(releases))
    what = "; ".join(f"{r.name} {r.tag}" for r in releases)
    print(f"{what}: " + ("placards rewritten" if changed else "nothing moved"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
