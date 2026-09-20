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
    header = fit_subject("feat", "unicode", "✨", "add U+2603 ☃ SNOWMAN")
    assert header == "feat(unicode): ✨ add U+2603 ☃ SNOWMAN"


def test_long_subject_is_cut_on_a_word_boundary():
    name = "ARABIC LIGATURE UIGHUR KIRGHIZ YEH WITH HAMZA ABOVE WITH ALEF MAKSURA ISOLATED FORM"
    header = fit_subject("feat", "unicode", "✨", f"add U+FBFA {name}")
    assert len(header) <= MAX_SUBJECT_LENGTH
    assert header.endswith("…")
    assert " WITH…" in header or header.endswith("ABOVE…") or header.endswith("HAMZA…")


def test_header_matches_the_house_regex_and_opens_lowercase():
    for kind, scope, emoji, subject in [
        ("docs", "rfc", "\U0001F4DD", "record RFC 2324, Hyper Text Coffee Pot Control Protocol"),
        ("refactor", "rosetta", "♻️", "solve FizzBuzz in COBOL"),
        ("test", "sequence", "\U0001F9EA", "continue 1, 1, 2, 3, 5, 8, 13, 21"),
        ("chore", "release", "\U0001F9F9", "v35.0.0, Linux 0.01 turns 35"),
    ]:
        header = fit_subject(kind, scope, emoji, subject)
        match = HOUSE_HEADER.match(header)
        assert match, header
        rest = EMOJI_PREFIX.sub("", match.group("subject"))
        assert rest[:1].islower() and rest[:1].isascii(), header


def test_hostile_subject_is_cleaned_before_fitting():
    header = fit_subject("docs", "rfc", "\U0001F4DD", "record RFC 1 \u2014 Host Software \u2013 Part 1 --> x")
    assert "\u2014" not in header and "\u2013" not in header and "-->" not in header
