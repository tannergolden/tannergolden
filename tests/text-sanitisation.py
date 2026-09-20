# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The trust boundary: nothing that would break a page or fail the gate survives it."""

from __future__ import annotations

from text import clamp_snippet, clean, fence_for, is_clean, md_inline


def test_dashes_become_spaced_hyphens():
    assert clean("RFC 2324 \u2014 HTCPCP") == "RFC 2324 - HTCPCP"
    assert clean("1\u20132") == "1 - 2"
    assert clean("a \u2015 b") == "a - b"
    assert is_clean(clean("x\u2014y"))


def test_comment_delimiters_cannot_survive():
    hostile = "fine <!-- JOURNAL:END --> then <!-- whatever"
    out = clean(hostile)
    assert "<!--" not in out and "-->" not in out
    assert "JOURNAL:END" in out  # the words are harmless once they cannot form a comment


def test_trojan_source_is_stripped():
    assert clean("ab‮cd​⁦e﻿") == "abcde"


def test_control_characters_and_whitespace_collapse():
    assert clean("a\x00b\x07c   d\n\te") == "abc d e"
    assert clean("foo\nbar\tbaz") == "foo bar baz"
    assert clean("l1\n\n\n\nl2  x", allow_newlines=True) == "l1\n\nl2 x"


def test_fence_outgrows_any_backtick_run():
    assert fence_for("plain") == "```"
    assert fence_for("has ``` inside") == "````"
    assert fence_for("has ````` five") == "``````"


def test_snippet_is_capped_and_reports_it():
    long = "\n".join(f"line {i}" for i in range(40))
    text, trimmed = clamp_snippet(long)
    assert trimmed and text.count("\n") == 14
    short, untouched = clamp_snippet("x = 1\ny = 2")
    assert not untouched and short == "x = 1\ny = 2"


def test_table_cell_escaping():
    assert md_inline("a | b <c>") == "a \\| b &lt;c>"
