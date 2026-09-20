# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The three daily modules: a Show HN post, a good first issue, a terminal tip.

These refresh with the page rather than with the journal, and they share its
ledger so a post, an issue or a tip shows once and never again. Each returns a
small dict the renderer knows how to lay out, or None when the source has
nothing new, in which case the previous value stays on the page: a module
that cannot refresh shows yesterday's item rather than a hole.
"""

from __future__ import annotations

import os
import random
import re
import urllib.parse

import net
from state import Ledger
from text import clean

_RNG = random.SystemRandom()

HN_SHOW = "https://hacker-news.firebaseio.com/v0/showstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
GITHUB_SEARCH = "https://api.github.com/search/issues"
TLDR_INDEX = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/{name}.md"
# The tree, not the contents listing: the contents endpoint stops at a
# thousand files without saying so, and pages/common holds nearly twice
# that, so half the commands would never have been drawn.
TLDR_TREE = "https://api.github.com/repos/tldr-pages/tldr/git/trees/main:pages/common"
TLDR_LIST = "https://api.github.com/repos/tldr-pages/tldr/contents/pages/common"


def show_hn(ledger: Ledger) -> dict | None:
    ids = net.get_json(HN_SHOW)
    if not isinstance(ids, list):
        return None
    for story_id in ids[:30]:
        if ledger.seen("hn", str(story_id)):
            continue
        item = net.get_json(HN_ITEM.format(id=story_id))
        if not isinstance(item, dict) or item.get("type") != "story" or not item.get("title"):
            continue
        url = str(item.get("url") or f"https://news.ycombinator.com/item?id={story_id}")
        if not url.startswith("https://"):
            continue
        title = clean(str(item["title"]))
        title = re.sub(r"^show hn:\s*", "", title, flags=re.IGNORECASE)
        domain = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")
        ledger.remember("hn", str(story_id))
        return {
            "id": str(story_id),
            "title": title,
            "url": url,
            "points": int(item.get("score") or 0),
            "domain": clean(domain),
            "discussion": f"https://news.ycombinator.com/item?id={story_id}",
        }
    return None


def good_first_issue(ledger: Ledger, languages: list) -> dict | None:
    """One open, unassigned, recently touched good-first-issue in a stack language.

    Authenticated with the workflow token when present, which is the only
    thing the token is used for outside pushing: search is rate-limited hard
    for anonymous callers.
    """
    if not languages:
        return None
    language = _RNG.choice(languages)
    query = f'label:"good first issue" state:open no:assignee language:"{language}" comments:<5'
    headers = net.github_headers(os.environ.get("GITHUB_TOKEN"))
    payload = net.get_json_with_headers(GITHUB_SEARCH, {"q": query, "sort": "updated", "order": "desc", "per_page": 30}, headers)
    if not isinstance(payload, dict):
        return None
    for item in payload.get("items") or []:
        if not isinstance(item, dict) or item.get("pull_request"):
            continue
        url = str(item.get("html_url") or "")
        match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)$", url)
        if not match or ledger.seen("issue", url):
            continue
        ledger.remember("issue", url)
        return {
            "id": url,
            "repo": clean(match.group(1)),
            "number": int(match.group(2)),
            "title": clean(str(item.get("title") or "")),
            "url": url,
            "language": clean(language),
        }
    return None


def _tldr_names() -> list:
    headers = net.github_headers(os.environ.get("GITHUB_TOKEN"))
    tree = net.get_json_with_headers(TLDR_TREE, None, headers)
    entries = tree.get("tree") if isinstance(tree, dict) else None
    if not isinstance(entries, list):
        listing = net.get_json_with_headers(TLDR_LIST, None, headers)
        entries = listing if isinstance(listing, list) else []
    names = []
    for entry in entries:
        name = str(entry.get("path") or entry.get("name") or "") if isinstance(entry, dict) else ""
        if name.endswith(".md") and "/" not in name:
            names.append(name[:-3])
    return names


def terminal_tip(ledger: Ledger) -> dict | None:
    """One command and one example from tldr-pages, CC BY 4.0."""
    names = _tldr_names()
    if not names:
        return None
    _RNG.shuffle(names)
    for name in names[:12]:
        if ledger.seen("tip", name):
            continue
        page = net.get_text(TLDR_INDEX.format(name=name))
        if not page:
            continue
        examples = re.findall(r"^- (.+?):\n\n`(.+?)`$", page, flags=re.MULTILINE)
        if not examples:
            continue
        description, command = _RNG.choice(examples)
        ledger.remember("tip", name)
        return {
            "id": name,
            "command": clean(name),
            "description": clean(description).rstrip(".").replace("{{", "").replace("}}", ""),
            "example": clean(command).replace("{{", "<").replace("}}", ">"),
            "url": f"https://github.com/tldr-pages/tldr/blob/main/pages/common/{name}.md",
        }
    return None
