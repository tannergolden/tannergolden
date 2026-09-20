# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The trust boundary: nothing that would break a page or fail the gate survives it."""

from __future__ import annotations

from text import clean, fence_for, is_clean, md_inline


def test_dashes_become_spaced_hyphens():
    assert clean("RFC 2324 \u2014 HTCPCP") == "RFC 2324 - HTCPCP"
    assert clean("1\u20132") == "1 - 2"
    assert clean("a \u2015 b") == "a - b"
    assert is_clean(clean("x\u2014y"))


def test_comment_delimiters_cannot_survive():
    hostile = "fine <!-- DISPATCHES:END --> then <!-- whatever"
    out = clean(hostile)
    assert "<!--" not in out and "-->" not in out
    assert "DISPATCHES:END" in out  # the words are harmless once they cannot form a comment
    # Removing an inner delimiter must not glue a new one together.
    for glued in ("--<!-->", "<-->!--", "x --<!--> y", "<!<!---->--"):
        assert is_clean(clean(glued)), (glued, clean(glued))


def test_mentions_and_references_are_defused():
    out = clean("ping @octocat, fixes #12, see owner/repo#7, but C# and a@b.c stay")
    assert "@octocat" not in out and "#12" not in out and "repo#7" not in out
    assert "\uff20octocat" in out and "\uff0312" in out and "repo\uff037" in out
    assert "C# " in out and "a@b.c" in out


def test_trojan_source_is_stripped():
    assert clean("ab‮cd​⁦e﻿") == "abcde"


def test_prose_lines_do_not_keep_leading_whitespace():
    """An RFC abstract arrives with its paragraphs indented; a page shows the space."""
    assert clean("A para.\n\n This one is indented.\n  So is this.", allow_newlines=True) == (
        "A para.\n\nThis one is indented.\nSo is this."
    )


def test_control_characters_and_whitespace_collapse():
    assert clean("a\x00b\x07c   d\n\te") == "abc d e"
    assert clean("foo\nbar\tbaz") == "foo bar baz"
    assert clean("l1\n\n\n\nl2  x", allow_newlines=True) == "l1\n\nl2 x"


def test_fence_outgrows_any_backtick_run():
    assert fence_for("plain") == "```"
    assert fence_for("has ``` inside") == "````"
    assert fence_for("has ````` five") == "``````"


def test_table_cell_escaping():
    assert md_inline("a | b <c>") == "a \\| b &lt;c>"


def test_inline_escaping_covers_link_labels_and_emphasis():
    from text import md_block, safe_url

    assert md_inline("U+005D ] RIGHT SQUARE BRACKET") == "U+005D \\] RIGHT SQUARE BRACKET"
    assert md_inline("a_b *c* `d` [e]") == "a\\_b \\*c\\* \\`d\\` \\[e\\]"
    assert md_block("the entity &#x2603; and R&D") == "the entity &amp;#x2603; and R&amp;D"
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
