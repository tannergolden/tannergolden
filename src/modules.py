# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The three daily modules: a Show HN post, a good first issue, a terminal tip.

It refreshes with the page rather than with the dispatches, and shares their
ledger so a command shows once and never again. It returns a small dict the
renderer knows how to lay out, or None when the source has nothing new, in
which case the previous value stays on the page: a module that cannot refresh
shows yesterday's command rather than a hole.
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
TLDR_PAGE = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/{name}.md"
# The tree, not the contents listing: the contents endpoint stops at a
# thousand files without saying so, and pages/common holds nearly twice
# that, so half the commands would never have been drawn.
TLDR_TREE = "https://api.github.com/repos/tldr-pages/tldr/git/trees/main:pages/common"
TLDR_LIST = "https://api.github.com/repos/tldr-pages/tldr/contents/pages/common"
TLDR_URL = "https://github.com/tldr-pages/tldr/blob/main/pages/common/{name}.md"

# A page worth drawing has more than a couple of things to say. One or two
# examples is a single-purpose tool, and a tip about it teaches a name.
MIN_EXAMPLES = 3

# `- Description of the example:` then a blank line then the command, fenced
# in single backticks. The whole tldr page format, in one expression.
EXAMPLE = re.compile(r"^- (.+?):\n\n`(.+?)`$", re.MULTILINE)
HEADING = re.compile(r"^# (.+)$", re.MULTILINE)

# tldr marks the letter a flag comes from: "E[x]tract a [f]ile". Useful in a
# terminal, noise on a page, and the brackets would have to be escaped as
# Markdown anyway.
MNEMONIC = re.compile(r"\[([A-Za-z])\]")

# A placeholder that offers the short and long spelling of one flag:
# {{[-C|--directory]}}. The long one is self-documenting, so it wins.
FLAG_CHOICE = re.compile(r"\{\{\[(-{1,2}[^|\]]+)\|(-{1,2}[^\]]+)\]\}\}")

# Anything else in double braces is a value the reader has to supply.
PLACEHOLDER = re.compile(r"\{\{(.+?)\}\}")

# An invocation that carries a flag or a pipe shows how a tool is driven.
# The bare `command path/to/file` form shows only that it exists.
TEACHES = re.compile(r"(?:^|\s)--?[A-Za-z]|\|")

# Below this many, preferring them stops being a preference and becomes a
# fixed choice: the page would show the same one example for ever.
MIN_WORTH_SHOWING = 3


def _describe(value: str) -> str:
    """An example's description, as prose rather than as terminal shorthand."""
    text = MNEMONIC.sub(r"\1", value)
    text = text.replace("`", "")  # code spans would be escaped, not rendered
    text = clean(text).rstrip(".")
    # "[c]reate an archive" loses its capital along with its brackets.
    return text[:1].upper() + text[1:]


def _invocation(value: str) -> str:
    """A command with its placeholders made readable, and its flags decided."""
    text = FLAG_CHOICE.sub(lambda m: m.group(2), value)
    text = PLACEHOLDER.sub(lambda m: f"<{m.group(1)}>", text)
    return clean(text, command=True)


def _summary(page: str) -> str:
    """The page's own one-line description of the tool, not of one example."""
    for line in page.split("\n"):
        if not line.startswith("> "):
            continue
        text = line[2:].strip()
        if text.lower().startswith("more information"):
            break
        return clean(text.replace("`", ""))
    return ""


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
    """One command and one way to use it, from tldr-pages, CC BY 4.0."""
    names = _tldr_names()
    if not names:
        return None
    _RNG.shuffle(names)
    for name in names[:12]:
        if ledger.seen("tip", name):
            continue
        page = net.get_text(TLDR_PAGE.format(name=name))
        if not page:
            continue
        examples = EXAMPLE.findall(page)
        if len(examples) < MIN_EXAMPLES:
            continue

        # The page heading is the command; the file name is a slug, and
        # `git-bisect` is not something anybody types.
        heading = HEADING.search(page)
        command = clean(heading.group(1)) if heading else clean(name.replace("-", " "))

        invocations = [(_describe(d), _invocation(c)) for d, c in examples]
        teaching = [pair for pair in invocations if TEACHES.search(pair[1])]
        worth_showing = teaching if len(teaching) >= MIN_WORTH_SHOWING else invocations
        description, example = _RNG.choice(worth_showing)
        if not description or not example:
            continue

        ledger.remember("tip", name)
        return {
            "id": name,
            "command": command,
            "summary": _summary(page),
            "description": description,
            "example": example,
            "url": TLDR_URL.format(name=name),
        }
    return None
