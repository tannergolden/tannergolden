# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The generated masthead, and the promise that every line it can draw is one
worth showing.

The space is small enough to walk end to end, which is the point: a generator
nobody can enumerate is a generator nobody can vouch for. Every assertion here
runs over `every_line()` rather than over a sample, so "no combination
embarrasses this page" is checked rather than hoped for.
"""

from __future__ import annotations

import re

import cards
import masthead

BANNED_DASH = re.compile(f"[{chr(0x2013)}-{chr(0x2015)}]")
LEADING_EMOJI = re.compile(r"^[^\sA-Za-z0-9]+️?\s")


def test_the_space_is_large_enough_to_be_worth_generating():
    """Lines are not the number that matters; a reader takes in the whole set."""
    assert masthead.combinations() == 239
    assert masthead.mastheads() == 822_553


def test_every_line_that_can_be_drawn_fits_the_plate(repo):
    """The image is as wide as its longest line, so this is a layout rule."""
    for line in masthead.every_line():
        assert masthead.cells(line) <= masthead.MAX_CELLS, line


def test_every_line_opens_with_an_emoji_and_then_words():
    for line in masthead.every_line():
        assert LEADING_EMOJI.match(line), line
        rest = LEADING_EMOJI.sub("", line)
        assert rest[:1].isupper(), line
        assert 3 <= len(rest.split()) <= 8, f"{len(rest.split())} words: {line}"


def test_no_line_carries_a_dash_the_house_bans():
    for line in masthead.every_line():
        assert not BANNED_DASH.search(line), line


def test_no_line_can_break_out_of_the_svg_or_the_page():
    """Nothing here is fetched, but the renderer escapes regardless."""
    for line in masthead.every_line():
        assert "<" not in line and ">" not in line and "&" not in line, line
        assert "-->" not in line, line


def test_the_greeting_is_always_first_and_never_drawn_twice():
    for _ in range(50):
        lines = masthead.lines()
        assert lines[0] == masthead.GREETING
        assert lines[0].startswith("\U0001F44B\U0001F3FB")
        assert masthead.GREETING not in lines[1:]
        assert len(lines) == masthead.LINES_PER_MASTHEAD + 1


def test_one_masthead_never_says_the_same_thing_twice(repo):
    """Frames are drawn without replacement, so no two lines share a shape."""
    shapes = {id(frame): frame for frame in masthead.FRAMES}
    assert len(shapes) == len(masthead.FRAMES)
    for _ in range(80):
        drawn = masthead.lines()[1:]
        assert len(set(drawn)) == len(drawn)
        # Two lines from one frame would share their emoji.
        emoji = [line.split(" ")[0] for line in drawn]
        assert len(set(emoji)) == len(emoji), drawn


def test_the_wording_actually_varies():
    seen = {tuple(masthead.lines()) for _ in range(200)}
    assert len(seen) > 150, f"only {len(seen)} distinct mastheads in 200 draws"


# --- the drawn image -----------------------------------------------------------

def test_the_svg_carries_no_script_and_every_line_in_its_title(repo):
    """GitHub strips script from an SVG in a README, which is why this is SMIL."""
    lines = masthead.lines()
    svg = cards.masthead_svg(lines)
    assert "<script" not in svg and "javascript:" not in svg
    assert "onload" not in svg and "onclick" not in svg
    for line in lines:
        assert line in svg


def test_the_reveal_steps_one_cell_at_a_time(repo):
    """A continuous width reveals letters through their middles; discrete types."""
    svg = cards.masthead_svg(["\U0001F44B\U0001F3FB Hello World!"])
    assert svg.count("<animate") == svg.count('calcMode="discrete"')


def test_the_plate_is_black_and_the_ink_is_legible_on_it(repo):
    """Neon green comes to 1.33:1 on the page's light surface and 14.9:1 here."""
    svg = cards.masthead_svg(masthead.lines())
    assert cards.CRT["plate"] in svg and cards.CRT["ink"] in svg
    assert "prefers-color-scheme" not in svg, "a terminal is black either way"


def test_the_glow_degrades_rather_than_breaks(repo):
    """A filter is the one thing here whose survival through GitHub is unproven."""
    svg = cards.masthead_svg(masthead.lines())
    assert "feGaussianBlur" in svg
    # The text is a child of the filtered group, so a stripped filter leaves
    # the glyphs where they are rather than removing them.
    body = svg.split('<g filter="url(#g)">', 1)[1]
    assert body.count("<text") == len(masthead.lines())


def test_the_image_is_one_file_with_every_line_in_its_alt(repo):
    lines = masthead.lines()
    cards.write_masthead(lines)
    region = cards.masthead_region()
    assert region.startswith("<img alt=")
    assert "<picture>" not in region, "a terminal needs no light variant"
    assert re.search(r"masthead\.svg\?v=[0-9a-f]{8}", region), region
    for line in lines:
        assert line in region


def test_a_redrawn_masthead_gets_a_new_url(repo):
    cards.write_masthead(["\U0001F44B\U0001F3FB Hello World!"])
    before = cards.masthead_region()
    cards.write_masthead(["\U0001F44B\U0001F3FB Hello World!", "\U0001F916 Nobody typed this line"])
    assert cards.masthead_region() != before


def test_the_alt_text_survives_a_render_that_drew_nothing(repo):
    """Most renders do not redraw the image, and still have to describe it."""
    lines = masthead.lines()
    cards.write_masthead(lines)
    assert cards.load_masthead_lines() == lines
    assert " / ".join(lines) in cards.masthead_region()
