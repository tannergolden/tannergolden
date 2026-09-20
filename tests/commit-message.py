# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every generated commit message passes the gate in tannergolden/standards.

`problems_for` below is the check from `scripts/commit-check.py` in that
repository, carried over verbatim in logic so that a change there which this
copy does not track shows up as a failing test here rather than as a rejected
commit on the profile.
"""

from __future__ import annotations

import re

import pytest

from render import commit_message, readme_commit_message
from sources import Dispatch
from state import now

DEFAULT_TYPES = "feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert,security".split(",")
BANNED_DASHES = re.compile("[\u2013-\u2015]")
EMOJI_PREFIX = re.compile("^[\U0001F000-\U0001FAFF←-⇿⌀-➿⤀-⯿]️?\\s")


def problems_for(message: str, types=DEFAULT_TYPES, max_header: int = 72) -> list:
    found = []
    header = message.split("\n", 1)[0].rstrip()
    if len(header) > max_header:
        found.append(f"the subject line is {len(header)} characters (limit {max_header})")
    match = re.match(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\)(?P<breaking>!)?: (?P<subject>.+)$", header)
    if not match:
        found.append("it does not match `<type>(<scope>): <subject>`")
    elif match.group("type") not in types:
        found.append(f"`{match.group('type')}` is not an allowed type")
    else:
        subject = EMOJI_PREFIX.sub("", match.group("subject"))
        if not subject[:1].islower() or not subject[:1].isascii():
            found.append("the subject must start with a lowercase letter, optionally after an emoji and a space")
    if BANNED_DASHES.search(message):
        found.append("it contains an em dash")
    return found


def entry(**overrides) -> Dispatch:
    base = dict(
        kind="rfc", commit_type="docs", emoji="\U0001F4DD",
        subject="record RFC 2324, Hyper Text Coffee Pot Control Protocol",
        title="RFC 2324: HTCPCP",
        body="An April Fools' RFC from 1998 \u2014 defining HTCPCP, a protocol for controlling coffee pots. It gave the world HTTP status 418.",
        identifier="2324", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc2324",
        license="freely reproducible", attribution="L. Masinter",
    )
    base.update(overrides)
    return Dispatch(**base)


CASES = [
    entry(),
    entry(kind="release", commit_type="feat", emoji="✨", subject="note Go 1.25.0",
          title="Go 1.25.0", body="Go 1.25.0 was published 2 days ago \u2013 the collector is eager now.",
          license="Release metadata, reported as fact", attribution=""),
    entry(kind="advisory", commit_type="security", emoji="\U0001F512",
          subject="flag the critical advisory in left-pad", title="GHSA-abcd-1234-efgh: left-pad",
          body="Critical severity in left-pad (npm) <!-- DISPATCHES:END --> published yesterday.",
          license="Advisory metadata, reported as fact", attribution=""),
    entry(kind="eol", commit_type="chore", emoji="\U0001F9F9",
          subject="mark Ubuntu 20.04 at end of life", title="Ubuntu 20.04, reaches end of life today",
          body="It stops receiving fixes \u2015 security ones included.", license="CC-BY-4.0", attribution=""),
    entry(kind="lobsters", commit_type="docs", emoji="\U0001F4DD",
          subject="read A thing somebody learned the hard way", title="A thing somebody learned the hard way",
          body="42 points on Lobsters, from example.invalid. Credit @octocat, fixes #12.",
          license="Title and score, reported as fact", attribution="submitted by someone"),
]



@pytest.mark.parametrize("item", CASES, ids=[c.kind for c in CASES])
def test_every_kind_passes_the_house_gate(item):
    message = commit_message(item)
    assert problems_for(message) == [], message
    _header, _, rest = message.partition("\n\n")
    assert rest.strip(), "the body is required on every commit"
    assert message.rstrip().endswith("Signed-off-by: Tanner Golden <24684994+tannergolden@users.noreply.github.com>")
    assert "Source: https://" in message
    assert "<!--" not in message and "-->" not in message


def test_mentions_and_references_cannot_reach_the_log():
    """A commit body is pushed: `@name` notifies and `fixes #12` closes."""
    message = commit_message(CASES[4])
    assert "@octocat" not in message and "#12" not in message
    assert "\uff20octocat" in message and "\uff0312" in message


def test_body_is_wrapped_at_72():
    message = commit_message(entry(body="word " * 60))
    body_lines = message.split("\n\n", 1)[1].splitlines()
    assert all(len(line) <= 72 for line in body_lines if not line.startswith(("Source:", "Signed-off-by:", "Attribution:"))), body_lines


def test_refresh_message_passes_too():
    message = readme_commit_message(now(), ["the cards", "the Show HN post"])
    assert problems_for(message) == []
    import phrasing

    header = message.split("\n", 1)[0]
    emoji, _, subject = header.removeprefix("chore(readme): ").partition(" ")
    assert emoji in phrasing.EMOJI["chore"]
    assert subject.split(" ")[0] in phrasing.VERBS["readme"] and subject.endswith(" the page")
