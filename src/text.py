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
  a person, so they are not exempt from that gate, and RFC titles and
  OEIS names carry en dashes routinely. Replacement happens here,
  once, rather than at nine call sites.
"""

from __future__ import annotations

import re
import textwrap
import unicodedata
import urllib.parse

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

# What a fence's info string may carry. CommonMark says a backtick fence's
# info string may not contain a backtick; one there means the fence never
# opens and the whole snippet renders as Markdown. A language name is only
# ever letters, digits and a little punctuation, so that is all that passes.
_INFO_STRING = re.compile(r"[^0-9a-z+#._-]")

# A mention or an issue reference. Pushed in a commit message, `@name`
# notifies that account and `fixes #12` closes that issue, so a wiki edit
# could make this repository do either. The sign is swapped for its
# fullwidth twin, which reads the same and links to nothing.
_MENTION = re.compile(r"(?<![\w.])@(?=[A-Za-z0-9])")
_REFERENCE = re.compile(r"(?<!&)#(?=\d)")


def clean(value: str, *, allow_newlines: bool = False, code: bool = False) -> str:
    """Return `value` fit to be written into a commit message or Markdown.

    Every fetched string passes through here. The order matters: dashes are
    replaced before whitespace is collapsed, so the spaced hyphen that
    replaces them does not leave a double space behind.

    With `code=True` whitespace is kept exactly as it came, tabs included,
    because indentation is part of a program. Only the invisible characters,
    the comment delimiters and the banned dashes go.
    """
    if not value:
        return ""

    text = unicodedata.normalize("NFC", value)
    text = TROJAN.sub("", text)
    # To a fixpoint: removing an inner delimiter can glue its neighbours
    # into a new one ("--<!-->" is "-->" after one pass).
    while True:
        stripped = COMMENT_DELIMITERS.sub("", text)
        if stripped == text:
            break
        text = stripped
    text = BANNED_DASHES.sub(" - ", text)

    if code:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch) != "Cc")
        return "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")

    # Prose only: a decorator in a program is not a mention.
    text = _MENTION.sub("\uff20", text)
    text = _REFERENCE.sub("\uff03", text)

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


# Characters that would otherwise start Markdown syntax inside a table cell or
# a link label: a pipe ends the cell, brackets end the label, and the rest
# begin emphasis, strikethrough or code. The backtick stays in the set: an
# unmatched one in a title can pair with a backtick in the next line of the
# same paragraph and turn two links into one code span. The backslash goes
# first so one already in the text cannot pair with one this adds.
_INLINE_SPECIALS = re.compile(r"([\\|\[\]*_`~])")

# A line opening with one of these is a heading, a quote, a table row, a
# fence or a bullet rather than prose. A fence is three or more, so a code
# span that happens to start a line is left alone.
_BLOCK_OPENERS = re.compile(r"^(\s{0,3})([#>|]|`{3,}|~{3,}|[-+*](?=\s|$))")

# An ordered-list opener. Only ASCII punctuation can be escaped in Markdown,
# so the backslash goes before the delimiter, never before the digits.
_ORDERED_OPENER = re.compile(r"^(\s{0,3}\d{1,9})([.)])(?=\s|$)")

# A line that is nothing but a rule: a thematic break, or the underline that
# turns the line above it into a heading.
_RULE_LINE = re.compile(r"^(\s{0,3})([-*_=])(?=(?:\s*\2){2,}\s*$)")


def md_inline(value: str) -> str:
    """Escape a cleaned string for use inside a table cell or a link label."""
    return _INLINE_SPECIALS.sub(r"\\\1", clean(value)).replace("<", "&lt;")


def md_block(value: str) -> str:
    """Escape wrapped prose so no fetched line can become structure or a link.

    Applied to the journal only. A commit message is plain text, and the same
    backslashes there would be noise in `git log`. An ampersand is escaped so
    an entity the prose quotes (the Unicode entries do) is shown, not rendered.
    """
    lines = []
    for line in value.split("\n"):
        line = line.replace("\\", "\\\\")
        line = _RULE_LINE.sub(r"\1\\\2", line)
        line = _BLOCK_OPENERS.sub(r"\1\\\2", line)
        line = _ORDERED_OPENER.sub(r"\1\\\2", line)
        lines.append(line.replace("&", "&amp;").replace("[", "\\[").replace("<", "&lt;"))
    return "\n".join(lines)


def safe_url(url: str) -> str:
    """Percent-encode whatever would end a Markdown link early, and nothing else.

    A URL is not prose: an en dash in it is part of the address, so the dash
    rule does not apply here. Only the invisible characters are stripped;
    everything that is not URL-safe, non-ASCII included, is percent-encoded,
    and an existing percent escape is left exactly as it was.
    """
    text = unicodedata.normalize("NFC", url)
    text = TROJAN.sub("", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cc").strip()
    return urllib.parse.quote(text, safe="%:/?#[]@!$&*+,;=~-._")


def fence_info(language: str | None) -> str:
    """The info string after a fence: a language name reduced to what one can be."""
    first = (language or "").lower().split()
    return _INFO_STRING.sub("", first[0] if first else "")[:32]


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
    text = clean(code, code=True)
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
