# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every generated commit against Conventional-Commits.md, rule by rule.

`tests/commit-message.py` carries the mechanical gate, `commit-check.py`,
which is what actually blocks a merge. This file carries the rules the
document states and no gate checks: imperative mood, the emoji mapping, the
72 character wrap, one footer block, and the absence of an AI trailer on a
commit no AI contributed to.

Each rule is a function, so it can be asserted twice: once against the
canonical example of every kind, where a failure names the rule, and once
across many redraws of the varying wording, where the point is that no
combination the pools can produce escapes the standard.

Each rule names the section it comes from, so a change over there has
something here to fail against.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

import phrasing
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

# The Emoji Mapping table, transcribed here independently of src/phrasing.py
# so the two have to agree. Importing the pools from the module under test
# would make this assert that a file equals itself.
EMOJI_ROWS = {
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
# opens with a bare verb, so a third person or participle form is the tell.
THIRD_PERSON = re.compile(r"^\w+(s|ed|ing)$")

BODY_WIDTH = 72

# U+2013 EN DASH through U+2015 HORIZONTAL BAR, built from code points so
# this file never contains one of them itself.
BANNED_DASH = re.compile(f"[{chr(0x2013)}-{chr(0x2015)}]")


def parts(message: str) -> tuple:
    """Header, body, footer block. Footers are the last paragraph."""
    header, _, rest = message.strip().partition("\n\n")
    paragraphs = rest.split("\n\n")
    return header, "\n\n".join(paragraphs[:-1]), paragraphs[-1]


# --- the rules ----------------------------------------------------------------

def rule_header_shape(message: str) -> None:
    """Commit Anatomy: type(scope): subject, the type from the list, under 72."""
    header = message.split("\n", 1)[0]
    match = HEADER.match(header)
    assert match, header
    assert match.group("type") in TYPES, header
    assert len(header) <= BODY_WIDTH, f"{len(header)} characters: {header}"


def rule_subject_is_lowercase_imperative(message: str) -> None:
    """Commit Anatomy: a brief summary in lowercase, imperative mood."""
    subject = HEADER.match(message.split("\n", 1)[0]).group("subject")
    assert LEADING_EMOJI.match(subject), f"no leading emoji: {subject}"
    rest = LEADING_EMOJI.sub("", subject)
    assert rest[:1].islower() and rest[:1].isascii(), subject
    assert not rest.endswith("."), f"subject ends in a full stop: {subject}"
    assert not THIRD_PERSON.match(rest.split(" ")[0]), f"not imperative mood: {subject}"


def rule_emoji_matches_the_type(message: str) -> None:
    """Emoji Mapping: the emoji belongs to the row for that type."""
    match = HEADER.match(message.split("\n", 1)[0])
    emoji = LEADING_EMOJI.match(match.group("subject")).group("emoji")
    assert emoji in EMOJI_ROWS[match.group("type")], f"{match.group('type')} may not use {emoji}"


def rule_body_present_and_wrapped(message: str) -> None:
    """The Body Is Not Optional: required, wrapped at 72.

    A reproduced program is the one thing that cannot be rewrapped without
    being corrupted, so a fenced block is exempt and recorded as a departure.
    """
    body = parts(message)[1]
    assert body.strip(), "a subject-only commit"
    inside_fence = False
    for line in body.split("\n"):
        if line.startswith("```"):
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            assert len(line) <= BODY_WIDTH, f"{len(line)} characters: {line}"


def rule_one_footer_block(message: str) -> None:
    """Commit Anatomy: body, then footers, as one trailing block of trailers.

    Git reads only the last paragraph as trailers, so provenance split into a
    paragraph of its own would not be read as trailers at all.
    """
    footers = parts(message)[2].split("\n")
    assert all(re.match(r"^[A-Z][A-Za-z-]*: .+$", line) for line in footers), footers
    assert footers[-1].startswith("Signed-off-by: Tanner Golden <"), footers


def rule_no_ai_trailer(message: str) -> None:
    """Do Not: add a Co-Authored-By trailer for an AI that did not contribute."""
    assert "Co-Authored-By:" not in message
    assert "Claude" not in message


def rule_no_banned_dash(message: str) -> None:
    """Punctuation: never an em dash, in a subject or a body."""
    assert not BANNED_DASH.search(message)


RULES = (
    rule_header_shape,
    rule_subject_is_lowercase_imperative,
    rule_emoji_matches_the_type,
    rule_body_present_and_wrapped,
    rule_one_footer_block,
    rule_no_ai_trailer,
    rule_no_banned_dash,
)


# --- one canonical example of every kind ---------------------------------------

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


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.__name__.removeprefix("rule_"))
@pytest.mark.parametrize("name", sorted(MESSAGES))
def test_the_canonical_example_of_every_kind(name, rule):
    rule(MESSAGES[name])


# --- and every redraw of the varying wording ------------------------------------

DRAWS = 80


def redraws(name: str) -> list:
    """The same dispatch with its verb and emoji drawn again, many times.

    This is what a fetcher does on every call, so a combination that broke a
    rule would reach the page eventually rather than never.
    """
    base = KINDS[name]
    _, _, tail = base.subject.partition(" ")
    return [
        commit_message(replace(
            base,
            emoji=phrasing.emoji_for(base.commit_type),
            subject=f"{phrasing.verb_for(name)} {tail}",
        ))
        for _ in range(DRAWS)
    ]


@pytest.mark.parametrize("name", sorted(KINDS))
def test_no_redraw_escapes_the_standard(name):
    for message in redraws(name):
        for rule in RULES:
            rule(message)


@pytest.mark.parametrize("name", sorted(KINDS))
def test_the_wording_actually_varies(name):
    """The point of the pools: a screen of log is not one sentence repeated."""
    subjects = [HEADER.match(m.split("\n", 1)[0]).group("subject") for m in redraws(name)]
    verbs = {LEADING_EMOJI.sub("", s).split(" ")[0] for s in subjects}
    emoji = {LEADING_EMOJI.match(s).group("emoji") for s in subjects}
    assert verbs == set(phrasing.VERBS[name]), f"{name}: {verbs}"
    assert len(emoji) == 3, f"{name} drew {len(emoji)} of 3 emoji in {DRAWS} draws"


def test_the_pools_are_the_standards_rows_and_nothing_wider():
    """src/phrasing.py may not invent an emoji the mapping table does not list."""
    assert set(phrasing.EMOJI) == set(EMOJI_ROWS)
    for commit_type, pool in phrasing.EMOJI.items():
        assert len(pool) == 3, commit_type
        for emoji in pool:
            assert emoji.rstrip("️") in EMOJI_ROWS[commit_type], f"{commit_type}: {emoji}"


def test_every_verb_in_every_pool_is_a_bare_imperative():
    for kind, pool in phrasing.VERBS.items():
        assert pool, kind
        for verb in pool:
            assert verb.isascii() and verb.islower() and verb.isalpha(), f"{kind}: {verb}"
            assert not THIRD_PERSON.match(verb), f"{kind}: {verb} is not imperative"


def test_the_status_commits_do_not_vary():
    """The two the workflow writes about itself stay uniform, so they grep."""
    assert {failure_commit_message("boom", now()).split("\n", 1)[0] for _ in range(20)} == {
        "ci(dispatches): ⚙️ mark the last run as failed"
    }
    assert {recovery_commit_message().split("\n", 1)[0] for _ in range(20)} == {
        "ci(dispatches): \U0001F552 mark the run passing again"
    }
