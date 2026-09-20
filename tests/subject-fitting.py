# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every header fits under 72 characters and opens as the house gate requires."""

from __future__ import annotations

import re

from config import MAX_SUBJECT_LENGTH
from text import fit_subject

HOUSE_HEADER = re.compile(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\)(?P<breaking>!)?: (?P<subject>.+)$")
EMOJI_PREFIX = re.compile("^[\U0001F000-\U0001FAFF←-⇿⌀-➿⤀-⯿]️?\\s")


def test_short_subject_is_left_alone():
    header = fit_subject("feat", "release", "✨", "note Go 1.25.0")
    assert header == "feat(release): ✨ note Go 1.25.0"


def test_long_subject_is_cut_on_a_word_boundary():
    # A Lobsters title is whatever its submitter typed, and nothing caps it.
    title = "An extremely long account of something somebody learned the hard way about distributed systems"
    header = fit_subject("docs", "lobsters", "\U0001F4DD", f"read {title}")
    assert len(header) <= MAX_SUBJECT_LENGTH
    assert header.endswith("…")
    # Cut on a word boundary: the last word is whole, not sliced.
    assert header.removesuffix("…").split(" ")[-1] in title.split(" ")


def test_header_matches_the_house_regex_and_opens_lowercase():
    for kind, scope, emoji, subject in [
        ("docs", "rfc", "\U0001F4DD", "record RFC 2324, Hyper Text Coffee Pot Control Protocol"),
        ("security", "advisory", "\U0001F512", "flag the critical advisory in left-pad"),
        ("chore", "eol", "\U0001F9F9", "mark Ubuntu 20.04 at end of life"),
        ("feat", "release", "✨", "note Kubernetes 1.34.0"),
    ]:
        header = fit_subject(kind, scope, emoji, subject)
        match = HOUSE_HEADER.match(header)
        assert match, header
        rest = EMOJI_PREFIX.sub("", match.group("subject"))
        assert rest[:1].islower() and rest[:1].isascii(), header


def test_hostile_subject_is_cleaned_before_fitting():
    header = fit_subject("docs", "rfc", "\U0001F4DD", "record RFC 1 \u2014 Host Software \u2013 Part 1 --> x")
    assert "\u2014" not in header and "\u2013" not in header and "-->" not in header
