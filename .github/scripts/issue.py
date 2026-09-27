#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Pick the README's good first issues: two open issues a newcomer could take this week.

  python3 .github/scripts/issue.py .github/good-first-issue.json [--today YYYY-MM-DD]

Every Friday it asks GitHub's search API for the most-starred public
projects that have open issues labeled `good first issue`, then asks
GraphQL, ten projects a query, for each one's newest such issues, and keeps
the ones opened in the past week that are still open, unassigned and not
linked to an open pull request. The two most-starred projects with such an
issue each give their newest one; a quiet week looks back a month. One
search and a few queries: searching each project's issues instead runs
into search's secondary rate limits within a minute. It writes them as two placards for the elements kit
(tannergolden/banners/elements), which draws them in the page's one theme
and fills the README's elements:issue-1 and elements:issue-2 blocks.

If GitHub cannot be reached, or nothing qualifies, last week's placards
stay. A first run with nothing to show writes one placard that opens
GitHub's own search instead. Titles come from strangers, so they are cut
down to plain text the kit can letter. Stdlib only, with placards.py beside it; reads
GH_TOKEN, which GraphQL needs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import urllib.error
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from placards import API, EST, LETTERS, Fetch, day, dump, eastern, fetch_url, github, graphql, letterable, sentence, write  # noqa: F401

LABEL = "good first issue"
SLOTS = ("issue-1", "issue-2")  # the README's element blocks, left to right
MIN_STARS = 1000  # a floor, so an issue always comes from a project people use
PROJECTS = 60     # how many of the most-starred projects to look through
BATCH = 10        # projects per GraphQL query
NEWEST = 20       # each project's newest open good first issues, the ones a month can hold
WINDOWS = (7, 30)  # days to look back: this week first, then the month
BROWSE = ("https://github.com/search?q=" + urllib.parse.quote_plus(f'label:"{LABEL}" is:issue is:open no:assignee')
          + "&type=issues&s=created&o=desc")


@dataclass
class Pick:
    owner: str
    name: str
    number: int
    title: str      # plain text the kit can letter
    url: str
    stars: int
    language: str
    opened: dt.date


# -- text ---------------------------------------------------------------------------------------

def compact(n: int) -> str:
    """Stars the way GitHub shows them: 999, 1.5K, 48.2K, 181K, 1.2M."""
    for size, unit in ((1_000_000, "M"), (1_000, "K")):
        if n >= size:
            v = n / size
            return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 100 else f"{v:.0f}") + unit
    return str(n)


# -- GitHub search -------------------------------------------------------------------------------

def search(fetch: Fetch, what: str, query: str, sort: str, per_page: int, token: str) -> list[dict]:
    params = {"q": query, "sort": sort, "order": "desc", "per_page": per_page}
    return github(fetch, f"/search/{what}", token, params).get("items", [])


def projects(fetch: Fetch, token: str) -> list[dict]:
    """The most-starred public projects with open good first issues, most stars first."""
    found = search(fetch, "repositories", f"good-first-issues:>0 stars:>={MIN_STARS} archived:false is:public",
                   "stars", PROJECTS, token)
    keep = [r for r in found if not r.get("archived") and not r.get("fork")
            and r.get("stargazers_count", 0) >= MIN_STARS and str(r.get("html_url", "")).startswith("https://github.com/")]
    return sorted(keep, key=lambda r: -r["stargazers_count"])


# Each project's newest open good first issues, with what decides whether one is still free.
ISSUES = """fragment newest on Repository {
  issues(labels: ["%s"], states: OPEN, first: %d, orderBy: {field: CREATED_AT, direction: DESC}) {
    nodes {
      number title url createdAt locked
      assignees { totalCount }
      closedByPullRequestsReferences(first: 1) { totalCount }
    }
  }
}""" % (LABEL, NEWEST)


def newest_issues(fetch: Fetch, repos: list[dict], token: str) -> dict[str, list[dict]]:
    """Each project's newest open good first issues, newest first, by lowercase full name: one query."""
    pairs = [r["full_name"].split("/", 1) for r in repos]
    head = ", ".join(f"$o{i}: String!, $n{i}: String!" for i in range(len(pairs)))
    body = " ".join(f"r{i}: repository(owner: $o{i}, name: $n{i}) {{ ...newest }}" for i in range(len(pairs)))
    variables = {k: v for i, (owner, name) in enumerate(pairs) for k, v in ((f"o{i}", owner), (f"n{i}", name))}
    data = graphql(fetch, f"query({head}) {{ {body} }}\n{ISSUES}", variables, token)
    return {r["full_name"].lower(): [as_item(node, r["full_name"])
                                     for node in ((data.get(f"r{i}") or {}).get("issues") or {}).get("nodes") or [] if node]
            for i, r in enumerate(repos)}


def as_item(node: dict, full_name: str) -> dict:
    """An issue from GraphQL in the shape the REST API gives one, so one test of fitness serves both."""
    return {"number": node.get("number", 0), "title": node.get("title") or "", "html_url": node.get("url") or "",
            "repository_url": f"{API}/repos/{full_name}", "state": "open", "locked": bool(node.get("locked")),
            "assigned": int((node.get("assignees") or {}).get("totalCount") or 0),
            "linked": int((node.get("closedByPullRequestsReferences") or {}).get("totalCount") or 0),
            "created_at": node.get("createdAt") or ""}


def usable(item: dict) -> bool:
    """Still open, nobody on it, no pull request on the way, and a title that is just a title."""
    return ("pull_request" not in item and item.get("state") == "open" and not item.get("locked")
            and not item.get("assignee") and not item.get("assignees") and not item.get("assigned")
            and not item.get("linked") and bool(item.get("created_at"))
            and str(item.get("html_url", "")).startswith("https://github.com/")
            and not re.search(r"https?://|www\.", item.get("title", ""), re.I))


def repo_of(item: dict) -> str:
    return item.get("repository_url", "").rsplit("/repos/", 1)[-1].lower()


def make_pick(item: dict, repo: dict) -> Pick | None:
    title = letterable(item.get("title", ""))
    if title is None:
        return None
    owner, _, name = repo["full_name"].partition("/")
    return Pick(owner=owner, name=name, number=int(item.get("number", 0)), title=title, url=item["html_url"],
                stars=int(repo.get("stargazers_count", 0)), language="".join(ch for ch in (repo.get("language") or "")[:24] if ch in LETTERS).strip(),
                opened=eastern(item["created_at"]).date())


def choose(fetch: Fetch, today: dt.date, token: str = "", want: int = len(SLOTS), batch: int = BATCH) -> list[Pick]:
    """The newest usable issue from each of the most-starred projects that have one, this week or else this month."""
    ranked = projects(fetch, token)
    newest: dict[str, list[dict]] = {}
    picks: dict[str, Pick] = {}
    for days in WINDOWS:
        since = today - dt.timedelta(days=days)
        for i in range(0, len(ranked), batch):
            group = ranked[i:i + batch]
            todo = [r for r in group if r["full_name"].lower() not in newest]
            if todo:  # a batch is asked for once; the month looks through what the week already fetched
                newest.update(newest_issues(fetch, todo, token))
            for repo in group:  # star order, so the first projects with an issue are the most-starred
                name = repo["full_name"].lower()
                if name in picks:
                    continue
                for it in newest.get(name, []):
                    if usable(it) and eastern(it["created_at"]).date() >= since:
                        pick = make_pick(it, repo)
                        if pick:
                            picks[name] = pick
                            break
                if len(picks) >= want:
                    return sorted(picks.values(), key=lambda p: -p.stars)
    return sorted(picks.values(), key=lambda p: -p.stars)


# -- the placards --------------------------------------------------------------------------------

def placard(p: Pick) -> dict:
    """One placard for the elements kit: the project on the plate, the issue as the description."""
    return {
        "kind": "placard", "owner": p.owner, "name": p.name, "icon": "flag", "link": p.url,
        "desc": sentence(f"#{p.number}: {p.title}"),
        "cells": [["Stars", compact(p.stars)], ["Language", (p.language or "Not set").upper()],
                  ["Opened", day(p.opened)]],
    }


def browse() -> dict:
    """The placard for a slot with no issue: GitHub's own search, newest first."""
    return {
        "kind": "placard", "owner": "github", "name": "good first issues", "icon": "search", "link": BROWSE,
        "desc": "Every open, unassigned issue labeled good first issue, newest first. Pick a project you already use.",
        "cells": [["Label", "GOOD FIRST ISSUE"], ["State", "OPEN"], ["Sort", "NEWEST"]],
    }


def document(picks: list[Pick]) -> dict:
    cards = [placard(p) for p in picks[:len(SLOTS)]]
    if len(cards) < len(SLOTS):
        cards.append(browse())
    return {"elements": dict(zip(SLOTS, cards))}


def main(argv: list[str] | None = None, fetch: Fetch = fetch_url) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("data", type=Path, help="the elements kit's data file for the two placards")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="the day to draw for, for reproducible output")
    args = ap.parse_args(argv)
    today = args.today or dt.datetime.now(EST).date()
    try:
        picks = choose(fetch, today, os.environ.get("GH_TOKEN", ""))
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        print(f"::notice::GitHub search unavailable ({type(exc).__name__}: {exc})")
        picks = []
    if not picks and args.data.exists():
        print("nothing drawn: last week's placards stay")
        return 0
    changed = write(args.data, document(picks))
    what = "; ".join(f"{p.owner}/{p.name}#{p.number}" for p in picks) or "no issue, the search placard"
    print(f"{today}: {what}: " + ("placards rewritten" if changed else "nothing moved"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
