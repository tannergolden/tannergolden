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


def test_inline_escaping_covers_link_labels_and_emphasis():
    from text import md_block, safe_url

    assert md_inline("U+005D ] RIGHT SQUARE BRACKET") == "U+005D \\] RIGHT SQUARE BRACKET"
    assert md_inline("a_b *c* `d` [e]") == "a\\_b \\*c\\* \\`d\\` \\[e\\]"
    assert md_block("# of things\n> quoted\n- item\n1. first\nplain [x](y) <b>") == (
        "\\# of things\n\\> quoted\n\\- item\n1\\. first\nplain \\[x](y) &lt;b>"
    )
    assert md_block("well-known, not a list") == "well-known, not a list"
    # A backslash already in the text cannot pair with one this adds.
    assert md_block("see \\[click here](https://x.example/)") == "see \\\\\\[click here](https://x.example/)"
    # Rules and setext underlines, but not a code span that starts a line.
    assert md_block("heading?\n---\n* * *\n___\n===") == "heading?\n\\---\n\\* * *\n\\___\n\\==="
    assert md_block("`strftime` at line start") == "`strftime` at line start"
    assert md_block("```\nfence") == "\\```\nfence"
    assert md_inline("Foo ~~gone~~ Bar") == "Foo \\~\\~gone\\~\\~ Bar"
    assert safe_url("https://x.example/wiki/A (B)?oldid=1&x=%20") == "https://x.example/wiki/A%20%28B%29?oldid=1&x=%20"
    # A URL is an address, not prose: its dash stays a dash, encoded.
    assert safe_url("https://blog.example/foo\u2013bar") == "https://blog.example/foo%E2%80%93bar"
    assert safe_url("https://x.example/a'b\u200b") == "https://x.example/a%27b"
