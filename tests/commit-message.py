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
from sources import Entry
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


def entry(**overrides) -> Entry:
    base = dict(
        kind="rfc", commit_type="docs", emoji="\U0001F4DD",
        subject="record RFC 2324, Hyper Text Coffee Pot Control Protocol",
        title="RFC 2324: HTCPCP",
        body="An April Fools' RFC from 1998 \u2014 defining HTCPCP, a protocol for controlling coffee pots. It gave the world HTTP status 418.",
        identifier="2324", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc2324",
        license="freely reproducible", attribution="L. Masinter",
    )
    base.update(overrides)
    return Entry(**base)


CASES = [
    entry(),
    entry(kind="unicode", commit_type="feat", emoji="✨", subject="add U+2603 ☃ SNOWMAN", title="U+2603 ☃ SNOWMAN", body="U+2603 is SNOWMAN."),
    entry(kind="rosetta", commit_type="refactor", emoji="♻️", subject="solve FizzBuzz in COBOL", title="FizzBuzz, solved in COBOL",
          body="The task, solved in COBOL.", code="       IDENTIFICATION DIVISION.\n       PROGRAM-ID. FIZZBUZZ.\n``` not a fence", code_language="cobol", code_trimmed=True, license="GFDL-1.2-only"),
    entry(kind="sequence", commit_type="test", emoji="\U0001F9EA", subject="continue 1, 1, 2, 3, 5, 8, 13, 21", title="1, 1, 2, 3, 5, 8, 13, 21, what comes next?", body="The next term is 34. This is A000045, Fibonacci numbers."),
    entry(kind="release", commit_type="chore", emoji="\U0001F9F9", subject="v35.0.0, Linux 0.01 turns 35", title="Linux 0.01 turns 35", body="Released in 1991 \u2013 thirty-five years ago."),
    entry(kind="born", commit_type="docs", subject="mark the birthday of Ada Lovelace, 1815", title="Ada Lovelace, born 1815", body="Born on this date <!-- JOURNAL:END --> in 1815."),
    entry(kind="bug", commit_type="fix", emoji="\U0001F41B", subject="revisit Therac-25", title="Therac-25", body="A race condition \u2015 in the control software."),
    entry(kind="falsehood", commit_type="fix", emoji="\U0001F41B", subject="correct what programmers believe about time", title="Falsehoods programmers believe about time", body="Time is not monotonic."),
    entry(kind="xkcd", subject="record xkcd 327, Exploits of a Mom", title="xkcd 327: Exploits of a Mom", body='The hover text reads: "Her daughter is named Help I\'m trapped in a driver\'s license factory."', license="CC-BY-NC-2.5"),
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


def test_code_is_fenced_beyond_its_own_backticks():
    message = commit_message(CASES[2])
    assert "\n````cobol\n" in message and "\n````\n" in message
    assert "cut to quotation length" in message


def test_body_is_wrapped_at_72():
    message = commit_message(entry(body="word " * 60))
    body_lines = message.split("\n\n", 1)[1].splitlines()
    assert all(len(line) <= 72 for line in body_lines if not line.startswith(("Source:", "Signed-off-by:", "Attribution:"))), body_lines


def test_refresh_message_passes_too():
    message = readme_commit_message(now(), ["the cards", "the Show HN post"])
    assert problems_for(message) == []
    assert message.startswith("chore(readme): \U0001F9F9 refresh the page\n\n")
