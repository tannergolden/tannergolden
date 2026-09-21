# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Wording that varies, inside what the commit standard allows.

Every dispatch of a kind used to open with the same verb and wear the same
emoji, so a screen of `git log` read as one sentence with the nouns swapped:
add, add, add, add. The content was never repeated, the sentence around it
always was.

The pools here vary the verb, the emoji and the opening clause, drawn from
the operating system's entropy source like every other thing in this
repository that varies.

WHAT MAY NOT BE WIDENED. The emoji pools are the mapping table in
Conventional-Commits.md, row for row, and the verbs are bare imperatives
because the standard asks for imperative mood. A pool that breaks either is
caught by `tests/commit-standard.py`, which runs the whole standard over
many draws rather than over one sample.

The commits the workflow writes about itself, the two that turn the badge
red and green, are deliberately NOT varied. Those are status markers. A
person greps for them.
"""

from __future__ import annotations

import random

_RNG = random.SystemRandom()

# The Emoji Mapping table, row for row. Three per type, as published.
EMOJI = {
    "feat": ("✨", "\U0001F195", "\U0001F680"),
    "fix": ("\U0001F41B", "\U0001FA79", "\U0001F527"),
    "docs": ("\U0001F4DD", "\U0001F4DA", "\U0001F4D6"),
    "style": ("\U0001F3A8", "\U0001F484", "\U0001F9FC"),
    "refactor": ("♻️", "\U0001F9E9", "\U0001FA9A"),
    "perf": ("⚡️", "\U0001F3CE️", "\U0001F4C8"),
    "test": ("\U0001F9EA", "\U0001F52C", "\U0001F9EB"),
    "build": ("\U0001F3D7️", "\U0001F9F1", "\U0001F4E6"),
    "ci": ("\U0001F916", "⚙️", "\U0001F552"),
    "chore": ("\U0001F9F9", "\U0001F5C2️", "\U0001FA9B"),
    "revert": ("⏪", "\U0001F519", "↩️"),
    "security": ("\U0001F512", "\U0001F6E1️", "\U0001F6A8"),
}

# Bare imperatives, one pool per kind. Read them as a log: "encode U+2603",
# "cite RFC 2324", "extend 1, 1, 2, 3". Each has to make sense in front of
# whatever that kind puts after it, which is why they are not shared.
VERBS = {
    "hn": ("read", "follow", "note", "surface"),
    "trending": ("star", "watch", "track", "clone"),
    "lobsters": ("read", "bookmark", "keep", "queue"),
    "availability": ("show", "mark", "post", "set"),
    "masthead": ("redraw", "retype", "recompose", "reprint"),
    "readme": ("refresh", "redraw", "update"),
}


def emoji_for(commit_type: str) -> str:
    """One emoji from that type's row in the standard's mapping table."""
    return _RNG.choice(EMOJI[commit_type])


def verb_for(kind: str) -> str:
    """One bare imperative from that kind's pool."""
    return _RNG.choice(VERBS[kind])


def one_of(*phrasings: str) -> str:
    """One of several ways to say the same thing.

    Used for the opening clause of a body, where the same facts read as a
    template when the sentence around them never changes.
    """
    return _RNG.choice(phrasings)
