# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every generated commit against Conventional-Commits.md, rule by rule.

`tests/commit-message.py` carries the mechanical gate, `commit-check.py`,
which is what actually blocks a merge. This file carries the rules that
document states and no gate checks: imperative mood, the emoji mapping, the
72 character wrap, one footer block, and the absence of an AI trailer on a
commit no AI contributed to.

Each test names the section of the standard it comes from, so a change over
there has something here to fail against.
"""

from __future__ import annotations

import re

import pytest

from render import (
    commit_message,
    failure_commit_message,
    readme_commit_message,
    recovery_commit_message,
)
from sources import Dispatch
from state import now

# "Type: one of feat, fix, docs, style, refactor, perf, test, build, ci,
# chore, revert, security." Commit Anatomy.
TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert", "security")

# "One emoji after the colon reads well in a long log." Emoji Mapping. Not
# enforced anywhere, which is why it is asserted here.
EMOJI = {
    "feat": "✨\U0001F195\U0001F680",
    "fix": "\U0001F41B\U0001FA79\U0001F527",
    "docs": "\U0001F4DD\U0001F4DA\U0001F4D6",
    "style": "\U0001F3A8\U0001F484\U0001F9FC",
    "refactor": "♻\U0001F9E9\U0001FA9A",
    "perf": "⚡\U0001F3CE\U0001F4C8",
    "test": "\U0001F9EA\U0001F52C\U0001F9EB",
    "build": "\U0001F3D7\U0001F9F1\U0001F4E6",
    "ci": "\U0001F916⚙\U0001F552",
    "chore": "\U0001F9F9\U0001F5C2\U0001FA9B",
    "revert": "⏪\U0001F519↩",
    "security": "\U0001F512\U0001F6E1\U0001F6A8",
}

HEADER = re.compile(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\)(?P<breaking>!)?: (?P<subject>.+)$")
LEADING_EMOJI = re.compile("^(?P<emoji>[\U0001F000-\U0001FAFF←-⇿⌀-➿⤀-⯿])️?\\s")

# "Keep the subject imperative and present tense." Do And Do Not. A subject
# opens with a bare verb, so the third person s is the tell: "turns", "adds",
# "is". The list is the forms the generator can actually produce.
NOT_IMPERATIVE = re.compile(r"^(is|are|was|were|has|have|adds|turns|records|marks|solves|continues|corrects|revisits)\b")

BODY_WIDTH = 72


def dispatch(**overrides) -> Dispatch:
    base = dict(
        kind="unicode", commit_type="feat", emoji="✨", subject="add U+2603 ☃ SNOWMAN",
        title="U+2603 ☃ SNOWMAN",
        body="A symbol in the Miscellaneous Symbols block, in Unicode since version 1.1.",
        identifier="2603", source_name="Unicode Character Database",
        source_url="https://util.unicode.org/UnicodeJsps/character.jsp?a=2603", license="Unicode-3.0",
    )
    base.update(overrides)
    return Dispatch(**base)


# One of every kind the picker can draw, in the shape its fetcher builds.
KINDS = {
    "rosetta": dispatch(kind="rosetta", commit_type="refactor", emoji="♻️",
                        subject="solve FizzBuzz in COBOL", title="FizzBuzz, solved in COBOL",
                        body="Rosetta Code carries 82 solutions to this task. This is the COBOL one.",
                        code="       IDENTIFICATION DIVISION.\n       PROGRAM-ID. FIZZBUZZ.",
                        code_language="cobol", license="GFDL-1.2-only", attribution="Rosetta Code contributors"),
    "unicode": dispatch(),
    "rfc": dispatch(kind="rfc", commit_type="docs", emoji="\U0001F4DD",
                    subject="record RFC 2324, Hyper Text Coffee Pot Control Protocol", title="RFC 2324",
                    body="Published in April 1998, with the status informational.",
                    license="IETF Trust Legal Provisions; RFCs may be freely reproduced", attribution="L. Masinter"),
    "sequence": dispatch(kind="sequence", commit_type="test", emoji="\U0001F9EA",
                         subject="continue 0, 1, 3, 6, 10, 15, 21, 28",
                         title="0, 1, 3, 6, 10, 15, 21, 28, what comes next?",
                         body="The next term is 36. This is A000217, Triangular numbers.",
                         license="CC-BY-SA-4.0", spoiler=True),
    "bug": dispatch(kind="bug", commit_type="fix", emoji="\U0001F41B", subject="revisit the Mars Climate Orbiter",
                    title="Mars Climate Orbiter", body="Lost in 1999 over a mismatch of units.",
                    license="CC-BY-SA-4.0", attribution="Wikipedia contributors"),
    "falsehood": dispatch(kind="falsehood", commit_type="fix", emoji="\U0001F41B",
                          subject="correct what programmers believe about time",
                          title="Falsehoods programmers believe about time", body="Time is not monotonic.",
                          license="CC0-1.0 (the list); the article itself is not reproduced"),
}

MESSAGES = {name: commit_message(item) for name, item in KINDS.items()}
MESSAGES["readme"] = readme_commit_message(now(), ["the cards"])
MESSAGES["ci-failed"] = failure_commit_message("RuntimeError: the wiki is down", now())
MESSAGES["ci-passing"] = recovery_commit_message()


def parts(message: str) -> tuple:
    """Header, body, footer block. Footers are the last paragraph."""
    header, _, rest = message.strip().partition("\n\n")
    paragraphs = rest.split("\n\n")
    return header, "\n\n".join(paragraphs[:-1]), paragraphs[-1]


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_header_shape(name):
    """Commit Anatomy: type(scope): subject, the type from the list."""
    header = MESSAGES[name].split("\n", 1)[0]
    match = HEADER.match(header)
    assert match, header
    assert match.group("type") in TYPES, header
    assert len(header) <= BODY_WIDTH, f"{len(header)} characters: {header}"


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_subject_is_lowercase_imperative_after_one_emoji(name):
    """Commit Anatomy: a brief summary in lowercase, imperative mood."""
    match = HEADER.match(MESSAGES[name].split("\n", 1)[0])
    subject = match.group("subject")
    emoji = LEADING_EMOJI.match(subject)
    assert emoji, f"no leading emoji: {subject}"
    rest = LEADING_EMOJI.sub("", subject)
    assert rest[:1].islower() and rest[:1].isascii(), subject
    assert not NOT_IMPERATIVE.match(rest), f"not imperative mood: {subject}"
    assert not rest.endswith("."), f"subject ends in a full stop: {subject}"


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_emoji_matches_the_type(name):
    """Emoji Mapping: the emoji belongs to the row for that type."""
    match = HEADER.match(MESSAGES[name].split("\n", 1)[0])
    emoji = LEADING_EMOJI.match(match.group("subject")).group("emoji")
    allowed = EMOJI[match.group("type")]
    assert emoji in allowed, f"{match.group('type')} may not use {emoji}"


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_the_body_is_present_and_wrapped(name):
    """The Body Is Not Optional: required, one blank line after the subject, wrapped at 72.

    A reproduced program is the one thing that cannot be rewrapped without
    being corrupted, so a fenced block is measured as a unit and exempt.
    """
    _, body, _ = parts(MESSAGES[name])
    assert body.strip(), "a subject-only commit"
    inside_fence = False
    for line in body.split("\n"):
        if line.startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue
        assert len(line) <= BODY_WIDTH, f"{len(line)} characters: {line}"


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_one_footer_block_ending_in_the_sign_off(name):
    """Commit Anatomy: body, then footers, as one trailing block of trailers.

    Git reads only the last paragraph as trailers, so provenance split into
    a paragraph of its own would not be read as trailers at all.
    """
    _, _, footers = parts(MESSAGES[name])
    lines = footers.split("\n")
    assert all(re.match(r"^[A-Z][A-Za-z-]*: .+$", line) for line in lines), footers
    assert lines[-1].startswith("Signed-off-by: Tanner Golden <"), footers
    if name not in ("readme", "ci-failed", "ci-passing"):
        assert any(line.startswith("Source: https://") for line in lines), footers
        assert any(line.startswith("License: ") for line in lines), footers


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_no_ai_trailer_on_a_commit_no_ai_contributed_to(name):
    """Do Not: add a Co-Authored-By trailer for an AI that did not contribute."""
    assert "Co-Authored-By:" not in MESSAGES[name]
    assert "Claude" not in MESSAGES[name]


@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_no_banned_dash_anywhere(name):
    """Punctuation: never an em dash, in a subject or a body."""
    assert not re.search("[\u2013-\u2015]", MESSAGES[name])
