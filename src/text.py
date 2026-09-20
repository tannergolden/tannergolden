# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Everything that touches text arriving from the open internet.

THIS MODULE IS THE TRUST BOUNDARY. Every string fetched from a source passes
through `clean()` before it reaches a commit message, a Markdown file, or an
SVG. Nine sources feed this repository and four of them are wikis anyone can
edit, so the assumption throughout is that any fetched byte is hostile until
it has been through here.

What it defends against, in the order the damage would be worst:

  Region escape. The page is rewritten between HTML comment markers. Content
  carrying `-->` could close a marker early and hand the rest of the README
  to whoever wrote that wiki paragraph, so the comment delimiters are removed
  outright rather than escaped.

  Fence escape. A borrowed snippet is rendered inside a fenced block. A
  snippet containing its own fence would end the block and spill the rest as
  Markdown, so the fence is chosen to be longer than any backtick run inside.

  Trojan source. Bidirectional overrides and zero-width characters make text
  render differently from how it is stored, which is a published attack on
  code review. They are stripped; nothing legitimate here needs them.

  The house gate. `scripts/commit-check.py` in tannergolden/standards rejects
  U+2013 to U+2015 anywhere in a commit message. These commits are authored by
  a person, so they are not exempt from that gate, and RFC titles, xkcd
  titles and OEIS names carry en dashes routinely. Replacement happens here,
  once, rather than at nine call sites.
"""

from __future__ import annotations

import re
import textwrap
import unicodedata

from config import BODY_WRAP, MAX_SNIPPET_CHARS, MAX_SNIPPET_LINES, MAX_SUBJECT_LENGTH

# U+2013 EN DASH through U+2015 HORIZONTAL BAR. The em dash is the banned
# character; its neighbours go with it because none of the three belongs in a
# commit message and a range is harder to get wrong than a single code point.
# Written as escapes so this file never contains one.
BANNED_DASHES = re.compile("[\u2013-\u2015]")

# Bidirectional overrides and isolates, plus the zero-width characters. Text
# that renders differently from how it is stored has no honest use here.
TROJAN = re.compile("[​-‏‪-‮⁦-⁩﻿]")

# The comment delimiters that bound every machine-owned region on the page.
COMMENT_DELIMITERS = re.compile(r"<!--+|--+>")

# Runs of backticks, used to size a fence that cannot be escaped from.
BACKTICK_RUN = re.compile(r"`+")


def clean(value: str, *, allow_newlines: bool = False) -> str:
    """Return `value` fit to be written into a commit message or Markdown.

    Every fetched string passes through here. The order matters: dashes are
    replaced before whitespace is collapsed, so the spaced hyphen that
    replaces them does not leave a double space behind.
    """
    if not value:
        return ""

    text = unicodedata.normalize("NFC", value)
    text = TROJAN.sub("", text)
    text = COMMENT_DELIMITERS.sub("", text)
    text = BANNED_DASHES.sub(" - ", text)

    # Whitespace controls become spaces first, so two words a newline or a
    # tab separated stay two words. Every other control character is dropped,
    # keeping the newline only where the caller wants it.
    keep = "\n" if allow_newlines else ""
    text = re.sub(r"[\t\r\f\v]", " ", text)
    if not allow_newlines:
        text = text.replace("\n", " ")
    text = "".join(ch for ch in text if ch in keep or unicodedata.category(ch) != "Cc")

    if allow_newlines:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()

    return re.sub(r"\s+", " ", text).strip()


def is_clean(value: str) -> bool:
    """True when `value` carries nothing this module would have removed."""
    return not (
        BANNED_DASHES.search(value)
        or TROJAN.search(value)
        or COMMENT_DELIMITERS.search(value)
    )


def md_inline(value: str) -> str:
    """Escape a cleaned string for use inside a Markdown table cell."""
    return clean(value).replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;")


def fence_for(code: str) -> str:
    """Return a fence longer than the longest backtick run inside `code`.

    A snippet containing a triple backtick would otherwise end its own block
    and spill the remainder of the file as Markdown.
    """
    longest = max((len(m.group()) for m in BACKTICK_RUN.finditer(code)), default=0)
    return "`" * max(3, longest + 1)


def clamp_snippet(code: str) -> tuple[str, bool]:
    """Cut a borrowed snippet to quotation scale.

    Returns the snippet and whether anything was removed, so the caller can
    say so rather than silently presenting a fragment as the whole.
    """
    text = clean(code, allow_newlines=True)
    lines = text.split("\n")
    trimmed = False

    if len(lines) > MAX_SNIPPET_LINES:
        lines = lines[:MAX_SNIPPET_LINES]
        trimmed = True

    text = "\n".join(lines)
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[:MAX_SNIPPET_CHARS].rsplit("\n", 1)[0]
        trimmed = True

    return text.rstrip(), trimmed


def fit_subject(kind: str, scope: str, emoji: str, subject: str) -> str:
    """Build `type(scope): emoji subject`, trimmed to the house ceiling.

    The subject always opens with a lowercase imperative verb supplied by the
    caller, which is what satisfies the house rule that a subject starts with
    a lowercase letter after an optional emoji. Uppercase is common in the
    material itself: Unicode names are fully capped, RFC titles are title
    case, and a subject built by pasting one in would be rejected by the gate
    on every commit.
    """
    subject = clean(subject)
    prefix = f"{kind}({scope}): {emoji} "
    room = MAX_SUBJECT_LENGTH - len(prefix)

    if room < 12:  # pragma: no cover - a scope this long is a programming error
        raise ValueError(f"no room for a subject after {prefix!r}")

    if len(subject) > room:
        cut = subject[: room - 1].rsplit(" ", 1)[0]
        subject = f"{cut}…" if cut else subject[: room - 1] + "…"

    return prefix + subject


def wrap_body(text: str) -> str:
    """Wrap prose at the width the commit standard asks for."""
    paragraphs = clean(text, allow_newlines=True).split("\n\n")
    wrapped = [
        textwrap.fill(p, width=BODY_WRAP, break_long_words=False, break_on_hyphens=False)
        for p in paragraphs
        if p.strip()
    ]
    return "\n\n".join(wrapped)
