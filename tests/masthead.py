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
import render

BANNED_DASH = re.compile(f"[{chr(0x2013)}-{chr(0x2015)}]")
LEADING_EMOJI = re.compile(r"^[^\sA-Za-z0-9]+️?\s")


def test_the_thousandth_line_is_the_greeting():
    """A round number is a promise, so it fails the day a pool drifts."""
    assert masthead.combinations() + 1 == masthead.TOTAL_LINES == 1000
    assert len(masthead.FRAMES) == 64
    assert len(set(masthead.every_line())) == masthead.combinations(), "a line is duplicated"
    assert masthead.GREETING not in set(masthead.every_line())


def test_there_are_enough_frames_to_draw_the_set_from(repo):
    """lines() samples distinct frames, so fewer frames than lines is a silent cap.

    Comfortably more, not barely more: drawing twelve from twelve would put
    every shape on every masthead, and the emoji down the left would be the
    same twelve every time however the words varied.
    """
    assert len(masthead.FRAMES) >= 2 * masthead.LINES_PER_MASTHEAD
    assert len(masthead.lines()) == masthead.LINES_PER_MASTHEAD + 1


def test_the_masthead_count_matches_brute_force_on_a_small_case():
    """mastheads() is a symmetric polynomial, not a walk over the subsets.

    Walking C(38, 12) would be 2.7 billion steps. The identity is worth
    checking somewhere it can be checked exhaustively.
    """
    import itertools
    import math

    small, k = masthead.FRAMES[:7], 3
    brute = sum(math.prod(f.combinations() for f in c)
                for c in itertools.combinations(small, k))
    sizes = [f.combinations() for f in small]
    totals = [1] + [0] * k
    for size in sizes:
        for i in range(k, 0, -1):
            totals[i] += totals[i - 1] * size
    assert totals[k] == brute


# --- the commit the schedule writes -------------------------------------------

def test_the_commit_is_drawn_rather_than_written(repo):
    """Twice a day forever, so the same paragraph would wear out fast."""
    assert masthead.commit_messages() > 5_000
    seen = {render.masthead_commit_message(["x"] * 13) for _ in range(300)}
    assert len(seen) > 250, f"only {len(seen)} distinct messages in 300 draws"


def test_every_commit_body_is_a_why_and_not_a_restatement(repo):
    """The Body Is Not Optional. A generated body is the easiest place to fail it."""
    for _ in range(200):
        message = render.masthead_commit_message(["x"] * 13)
        header, _, rest = message.partition("\n\n")
        body = rest.rsplit("\n\nSigned-off-by:", 1)[0]
        flat = " ".join(body.split())

        assert body.count("\n\n") == 1, body
        assert len(flat.split()) > 25, "a body this short cannot be a why"
        # Never opens with the subject's own verb.
        assert not flat.lower().startswith(header.split(" ")[2]), flat
        # Says why a redraw exists, and why it is on a clock.
        assert any(w in flat for w in ("finite", "committed file", "replace the")), flat
        assert any(w in flat for w in ("Twice a day", "twelve-hour clock")), flat


def test_no_commit_frame_can_produce_a_stray_placeholder(repo):
    """One frame wants the numbers; the others must not be handed them."""
    for _ in range(200):
        assert "{}" not in render.masthead_commit_message(["x"] * 13)
    for frame in masthead.COMMIT_WHY:
        for line in frame.every():
            assert line.count("{}") in (0, 3), line


def test_every_line_that_can_be_drawn_fits_the_plate(repo):
    """The image is as wide as its longest line, so this is a layout rule."""
    for line in masthead.every_line():
        assert masthead.cells(line) <= masthead.MAX_CELLS, line


def test_every_line_opens_with_an_emoji_and_then_words():
    for line in masthead.every_line():
        assert LEADING_EMOJI.match(line), line
        rest = LEADING_EMOJI.sub("", line)
        assert rest[:1].isupper(), line
        assert 4 <= len(rest.split()) <= 8, f"{len(rest.split())} words: {line}"


def test_every_frame_has_its_own_emoji():
    """Two frames sharing one would read as the same shape twice in a set."""
    emoji = [f.emoji for f in masthead.FRAMES]
    assert len(set(emoji)) == len(emoji), "an emoji is used by two frames"
    assert all(emoji), "a masthead line without an emoji"


def test_every_frame_earns_its_place():
    """A frame whose slots are not interchangeable produces nonsense, and the
    only defence is that each one is small enough to have been read."""
    for frame in masthead.FRAMES:
        assert frame.combinations() >= 4, frame.shape
        assert frame.shape.count("{}") == len(frame.slots), frame.shape
        for pool in frame.slots:
            assert len(set(pool)) == len(pool), pool


def test_no_line_carries_a_dash_the_house_bans():
    for line in masthead.every_line():
        assert not BANNED_DASH.search(line), line


def test_no_line_can_break_out_of_the_svg_or_the_page():
    """Nothing here is fetched, but the renderer escapes regardless."""
    for line in masthead.every_line():
        assert "<" not in line and ">" not in line and "&" not in line, line
        assert "-->" not in line, line


def test_the_greeting_types_once_and_the_rest_loop_without_it(repo):
    """A greeting that greets the same reader every minute is a tic.

    Two timelines: the greeting runs on its own with repeatCount="1" and
    then stays gone, and everything else loops among itself, beginning where
    the greeting finished erasing.
    """
    lines = masthead.lines()
    svg = cards.masthead_svg(lines, "dark")
    intro = cards.masthead_slot(lines[0])

    once = re.findall(r'dur="([\d.]+)s" repeatCount="1"', svg)
    assert once, "the greeting never stops repeating"
    assert all(float(d) == round(intro, 2) for d in once), once

    loop = set(re.findall(r'begin="([\d.]+)s" dur="([\d.]+)s" repeatCount="indefinite"', svg))
    assert len(loop) == 1, loop
    begin, dur = loop.pop()
    assert float(begin) == round(intro, 2), "the loop must start where the greeting ends"
    assert float(dur) == round(cards.masthead_loop_seconds(lines), 2)

    # The greeting's own clip is the one that does not repeat, and it freezes
    # closed rather than reverting to the width it carries for renderers
    # that never animated it at all.
    greeting_clip = svg.split('<clipPath id="c0-0">')[1].split("</clipPath>")[0]
    assert 'repeatCount="1"' in greeting_clip and "begin=" not in greeting_clip
    assert 'fill="freeze"' in greeting_clip


def test_the_greeting_is_always_first_and_never_drawn_twice():
    for _ in range(50):
        lines = masthead.lines()
        assert lines[0] == masthead.GREETING
        assert lines[0].startswith("\U0001F44B\U0001F3FB")
        assert masthead.GREETING not in lines[1:]
        assert len(lines) == masthead.LINES_PER_MASTHEAD + 1


def test_the_drawn_count_is_what_the_module_says_it_is():
    """A hardcoded default here silently ignored the constant beside it."""
    assert len(masthead.lines()) == masthead.LINES_PER_MASTHEAD + 1
    assert masthead.LINES_PER_MASTHEAD <= len(masthead.FRAMES)


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


def test_the_reveal_reaches_the_end_of_every_row(repo):
    """The bug a screenshot found: the last character never finished typing.

    The clip rectangle is anchored at x=0 and the text starts beyond the
    prompt, so a width measured from the text's own left edge stopped a
    character and a half short of the end. Every row has to be fully
    uncovered at the top of its hold, and the image has to be wide enough to
    hold what the clip uncovers.
    """
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO
    left = cards.MASTHEAD_TEXT_X + cards.PROMPT_CELLS * cell
    for line in (max(masthead.every_line(), key=masthead.cells), masthead.GREETING):
        svg = cards.masthead_svg([line])
        for row, (_times, widths) in zip(cards.wrap(line), _clip_frames(svg)):
            ends_at = left + masthead.cells(row) * cell
            assert max(widths) + 0.5 >= ends_at, f"{max(widths)} < {ends_at}: {row}"
            assert int(re.search(r'<svg[^>]*width="(\d+)"', svg).group(1)) >= ends_at


def test_nothing_is_drawn_behind_the_text(repo):
    """Transparent, so the text sits on whatever GitHub paints behind it."""
    for scheme in cards.MASTHEAD_INK:
        svg = cards.masthead_svg(masthead.lines(), scheme)
        assert "<rect" in svg, "the cursor is a rect"
        # ...but no full-bleed plate behind everything.
        assert 'rx="8"' not in svg and "#0d0208" not in svg


def test_each_scheme_gets_a_green_that_is_legible_on_it(repo):
    """Neon is 13.9:1 on GitHub dark and 1.4:1 on white, which is invisible.

    No single green clears the bar on both, which is the whole reason this
    ships two files instead of one.
    """
    assert cards.MASTHEAD_INK["dark"] == "#00ff41"
    assert cards.MASTHEAD_INK["light"] != cards.MASTHEAD_INK["dark"]
    for scheme, ink in cards.MASTHEAD_INK.items():
        svg = cards.masthead_svg(masthead.lines(), scheme)
        assert f"fill:{ink}" in svg
        assert all(other not in svg for other in cards.MASTHEAD_INK.values() if other != ink)


def test_the_bloom_is_only_drawn_where_it_reads_as_neon(repo):
    """On a light background a glow around dark green is a smudge."""
    assert "feGaussianBlur" in cards.masthead_svg(masthead.lines(), "dark")
    assert "feGaussianBlur" not in cards.masthead_svg(masthead.lines(), "light")


def test_the_glow_degrades_rather_than_breaks(repo):
    """A filter is the one thing here whose survival through GitHub is unproven."""
    svg = cards.masthead_svg(masthead.lines())
    assert "feGaussianBlur" in svg
    # The text is a child of the filtered group, so a stripped filter leaves
    # the glyphs where they are rather than removing them.
    lines = masthead.lines()
    body = cards.masthead_svg(lines).split('<g class="anim" filter="url(#g)">', 1)[1]
    rows = sum(len(cards.wrap(line)) for line in lines)
    assert body.count("<text") == rows + 1  # every row, and the prompt


def test_the_region_switches_with_the_readers_scheme(repo):
    lines = masthead.lines()
    cards.write_masthead(lines)
    region = cards.masthead_region()
    assert region.startswith("<picture>")
    assert "(prefers-color-scheme: dark)" in region
    assert re.search(r"masthead-dark\.svg\?v=[0-9a-f]{8}", region), region
    assert re.search(r"masthead-light\.svg\?v=[0-9a-f]{8}", region), region
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


# --- how it types --------------------------------------------------------------

def _clip_frames(svg: str) -> list:
    """Every clip animation in the file, as (times, widths)."""
    found = re.findall(
        r'<animate attributeName="width" values="([^"]+)" keyTimes="([^"]+)"', svg)
    return [([float(t) for t in times.split(";")], [float(w) for w in widths.split(";")])
            for widths, times in found]


def test_the_keyframes_are_ordered_and_complete(repo):
    """SMIL requires keyTimes to increase, start at 0 and end at 1.

    Two bugs have hidden here. A rounding error put one mark a femtosecond
    before the one ahead of it; writing four decimal places then collapsed
    two distinct moments into one string. Either leaves a browser with an
    animation it refuses to run at all, and the image goes blank.
    """
    lines = masthead.lines()
    for scheme in cards.MASTHEAD_INK:
        svg = cards.masthead_svg(lines, scheme)
        frames = _clip_frames(svg)
        assert len(frames) == sum(len(cards.wrap(line)) for line in lines)
        for times, widths in frames:
            assert len(times) == len(widths)
            assert times[0] == 0.0 and times[-1] == 1.0, (times[0], times[-1])
            assert all(b > a for a, b in zip(times, times[1:])), "keyTimes went backwards"


def test_every_animation_in_the_file_agrees_on_its_own_timing(repo):
    """The cursor rides its line's keyTimes; a list of a different length
    would slide it away from the text it is supposed to follow.

    One clip per row, one cursor per line: the cursor moves down a row when
    the line wraps rather than each row keeping one of its own.
    """
    lines = masthead.lines()
    svg = cards.masthead_svg(lines)
    widths = re.findall(r'attributeName="width" values="([^"]+)" keyTimes="([^"]+)"', svg)
    xs = re.findall(r'attributeName="x" values="([^"]+)" keyTimes="([^"]+)"', svg)
    ys = re.findall(r'attributeName="y" values="([^"]+)" keyTimes="([^"]+)"', svg)
    ops = re.findall(r'attributeName="opacity" values="([^"]+)" keyTimes="([^"]+)"', svg)

    assert len(widths) == sum(len(cards.wrap(line)) for line in lines)
    assert len(xs) == len(ys) == len(ops) == len(lines)
    for (values, times), (_, other), (_, third) in zip(xs, ys, ops):
        assert times == other == third
        assert len(values.split(";")) == len(times.split(";"))

    # And every row of a line rides that same line's timing.
    at = 0
    for line, (_, cursor_times) in zip(lines, xs):
        for _ in cards.wrap(line):
            assert widths[at][1] == cursor_times
            at += 1


def test_every_line_types_at_the_same_speed(repo):
    """The bug in the model this replaced: one fixed duration for every line.

    A seventeen cell greeting and a forty nine cell line both took 1.6
    seconds, so one crawled and the other blurred past at three times the
    speed. A terminal has one cadence.
    """
    for line in (masthead.GREETING, max(masthead.every_line(), key=masthead.cells)):
        expected = cards.TYPE_CADENCE * masthead.cells(line)
        assert abs(sum(cards._rhythm(line, expected)) - expected) < 1e-9


def test_a_longer_line_is_held_longer_than_a_short_one(repo):
    """Reading time is length times a rate plus a constant, so the hold is too."""
    short = min(masthead.every_line(), key=masthead.cells)
    long = max(masthead.every_line(), key=masthead.cells)
    assert cards.masthead_slot(long) > cards.masthead_slot(short) * 1.3
    # But no line owns the plate so long that a visitor gives up on it.
    assert cards.masthead_slot(long) < 8.0


def test_the_loop_comes_round_inside_a_first_visit(repo):
    """Median time on a page a visitor has not seen before is under a minute.

    The whole set has to have been typed by then, or the lines at the bottom
    of the draw are lines nobody ever reads. Each line is held for as long as
    its own length earns, so the loop varies with what was drawn: the median
    is what has to clear the bar, and the worst set the frames can produce is
    what has to stay inside a reader's patience.
    """
    import statistics

    loops = [cards.masthead_loop_seconds(masthead.lines()) for _ in range(200)]
    assert statistics.median(loops) < 60.0, statistics.median(loops)
    assert min(loops) > 35.0, "the set goes past too fast to read"

    longest = sorted((max(masthead.cells(line) for line in frame.every())
                      for frame in masthead.FRAMES), reverse=True)
    worst = sum(cards.masthead_slot("x" * c)
                for c in longest[:masthead.LINES_PER_MASTHEAD])
    assert worst < 75.0, worst


def test_the_typing_is_not_a_metronome_but_is_the_same_every_time(repo):
    """Human rhythm, drawn from the line's own text rather than from chance.

    Drawn from chance, a run that changed nothing would still rewrite both
    images, and every redraw would be a commit whether or not the words moved.
    """
    line = "\U0001F680 Shipping a change behind a gate"
    total = cards.TYPE_CADENCE * masthead.cells(line)
    once = cards._rhythm(line, total)
    assert once == cards._rhythm(line, total), "the same line typed two different ways"
    assert once != cards._rhythm(line + " again", total)
    beats = [d for d in once if d > 0]
    assert max(beats) > min(beats) * 1.5, "this is a metronome"


def test_an_emoji_never_rests_half_revealed(repo):
    """An emoji is two cells wide and one keystroke.

    Stepping through the middle of one leaves the clip resting on half a
    face for a tenth of a second, which is the sort of thing a reader sees
    without being able to say what is wrong.
    """
    line = "\U0001F680 Shipping a change behind a gate"
    delays = cards._rhythm(line, cards.TYPE_CADENCE * masthead.cells(line))
    assert delays[1] == 0.0, "the second cell of the emoji waits its own turn"
    assert delays[0] > 0.0


# --- how it degrades -----------------------------------------------------------

def test_a_renderer_with_no_animation_still_shows_the_greeting(repo):
    """SMIL is a browser feature, not a universal one.

    Every clip starts at width zero, so a renderer that ignores the
    animations shows an empty box. The greeting's rectangle therefore
    carries its full width as a plain attribute, which an animation
    overrides rather than supplies, and freezes closed when it is done.
    """
    lines = masthead.lines()
    svg = cards.masthead_svg(lines)
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO
    left = cards.MASTHEAD_TEXT_X + cards.PROMPT_CELLS * cell

    for row, text in enumerate(cards.wrap(lines[0])):
        clip = svg.split(f'<clipPath id="c0-{row}">')[1].split("</clipPath>")[0]
        static = float(re.search(r'<rect x="0" y="0" width="([\d.]+)"', clip).group(1))
        opened = left + masthead.cells(text) * cell
        assert static + 0.05 >= opened, f"{static} < {opened}: a still renderer shows nothing"

    for index in range(1, len(lines)):
        for row in range(len(cards.wrap(lines[index]))):
            clip = svg.split(f'<clipPath id="c{index}-{row}">')[1].split("</clipPath>")[0]
            assert '<rect x="0" y="0" width="0"' in clip, "a later line would overlap the first"


def test_a_reader_who_asked_for_less_motion_gets_a_still_line(repo):
    """Text that types itself is exactly the motion that setting is about."""
    for scheme in cards.MASTHEAD_INK:
        svg = cards.masthead_svg(masthead.lines(), scheme)
        assert "@media (prefers-reduced-motion:reduce)" in svg
        assert ".anim{display:none}" in svg and ".still{display:inline}" in svg
        still = svg.split('<g class="still"')[1].split("</g>")[0]
        assert masthead.GREETING in still
        assert "clip-path" not in still and "<animate" not in still


def test_the_prompt_is_always_there_and_never_moves(repo):
    """It is what says terminal before a character has been typed."""
    for scheme in cards.MASTHEAD_INK:
        svg = cards.masthead_svg(masthead.lines(), scheme)
        prompt = f'<text class="p" x="{cards.MASTHEAD_TEXT_X}"'
        assert prompt in svg
        drawn = svg.split(prompt)[1].split("</text>")[0]
        assert cards.MASTHEAD_PROMPT in drawn
        assert "<animate" not in drawn and "clip-path" not in drawn


def test_the_typed_text_starts_beyond_the_prompt(repo):
    """The clip is anchored at x=0, so every width it animates through has to
    carry the inset and the prompt both. Missing the inset cut the last
    character and a half off the longest line once already."""
    line = max(masthead.every_line(), key=masthead.cells)
    svg = cards.masthead_svg([line])
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO
    left = cards.MASTHEAD_TEXT_X + cards.PROMPT_CELLS * cell

    assert f'<text x="{left:.1f}"' in svg or f'<text x="{left:.0f}"' in svg, left
    for row, (_times, widths) in zip(cards.wrap(line), _clip_frames(svg)):
        assert max(widths) + 0.05 >= left + masthead.cells(row) * cell
        assert int(re.search(r'<svg[^>]*width="(\d+)"', svg).group(1)) >= max(widths)


# --- the cursor ----------------------------------------------------------------

def test_the_cursor_is_solid_while_it_types_and_blinks_only_when_it_waits(repo):
    """A real cursor does not blink mid-word. It blinks when nothing is happening."""
    line = "\U0001F680 Shipping a change behind a gate"
    svg = cards.masthead_svg([line])
    times, _widths = _clip_frames(svg)[0]
    lit = [int(v) for v in
           re.search(r'attributeName="opacity" values="([^"]+)"', svg).group(1).split(";")]

    slot = cards.masthead_slot(line)
    typing = cards.TYPE_CADENCE * masthead.cells(line) / slot
    holding = typing + (cards.HOLD_BASE + cards.HOLD_PER_CELL * masthead.cells(line)) / slot

    during_typing = [on for at, on in zip(times, lit) if 0 < at < typing]
    assert during_typing and all(during_typing), "the cursor blinked mid-word"
    during_erase = [on for at, on in zip(times, lit) if holding < at < 0.999]
    assert during_erase and all(during_erase), "the cursor blinked while erasing"
    while_waiting = [on for at, on in zip(times, lit) if typing < at < holding]
    assert 0 in while_waiting and 1 in while_waiting, "the cursor never blinked at all"
    assert lit[-1] == 0, "the cursor outlives its line"


def test_the_cursor_rides_the_end_of_what_has_been_typed(repo):
    """Behind the text it is a smudge; far ahead of it, it belongs to nothing."""
    svg = cards.masthead_svg([masthead.GREETING])
    _times, widths = _clip_frames(svg)[0]
    xs = [float(v) for v in
          re.search(r'attributeName="x" values="([^"]+)"', svg).group(1).split(";")]
    assert len(xs) == len(widths)
    assert all(0 < x - w <= 2 for x, w in zip(xs, widths)), "the cursor left the text"


# --- lighting ------------------------------------------------------------------

def test_the_bloom_has_a_core_and_a_halo_rather_than_one_smear(repo):
    """One blur merged with itself is a blurry copy of the text.

    A phosphor has a hard centre and soft light well beyond it, which is two
    passes at different radii with the wide one dimmed.
    """
    svg = cards.masthead_svg(masthead.lines(), "dark")
    radii = [float(r) for r in re.findall(r'stdDeviation="([\d.]+)"', svg)]
    assert len(radii) == 2, radii
    assert max(radii) > 3 * min(radii), "both passes are the same blur"
    # The halo is dimmed, or it reads as a second copy rather than as light.
    assert re.search(r'feColorMatrix[^>]*0 0 0 0\.\d+ 0"', svg), "the halo is not dimmed"


def test_the_filter_keeps_its_colour(repo):
    """The default filter space is linearRGB, which turns a saturated green
    bloom into a pale grey one. This is the one attribute that stops it."""
    assert 'color-interpolation-filters="sRGB"' in cards.masthead_svg(masthead.lines(), "dark")


# --- what the next draw remembers ------------------------------------------------

def test_two_draws_in_a_row_share_no_shape(repo):
    """Twelve of sixty-four shapes, twice a day, puts yesterday's shape back
    on the page more often than not. Excluding the last draw's frames costs
    nothing: fifty-two remain, and four times as many as a draw needs."""
    for _ in range(40):
        first = masthead.lines()
        second = masthead.lines(avoid_shapes=masthead.shapes_in(first))
        assert not set(masthead.shapes_in(first)) & set(masthead.shapes_in(second))
        assert len(second) == masthead.LINES_PER_MASTHEAD + 1


def test_a_line_drawn_recently_is_not_drawn_again(repo):
    """Four days of memory, so a reader coming back tomorrow meets sentences
    rather than reruns."""
    for _ in range(40):
        recent = masthead.lines()[1:]
        again = masthead.lines(avoid_lines=recent)[1:]
        assert not set(recent) & set(again)


def test_the_memory_never_starves_the_draw(repo):
    """Asked to avoid more than exists, it draws anyway: a masthead with a
    hole in it is worse than a line somebody has seen before."""
    everything = [f.emoji for f in masthead.FRAMES]
    assert len(masthead.lines(avoid_shapes=everything)) == masthead.LINES_PER_MASTHEAD + 1
    assert len(masthead.lines(avoid_lines=list(masthead.every_line()))) \
        == masthead.LINES_PER_MASTHEAD + 1


def test_the_memory_is_written_beside_the_image_and_stays_bounded(repo):
    """The image and the record of how it was drawn belong to one commit, so
    they can never disagree about what the page is showing."""
    seen = []
    for _ in range(12):
        shapes, recent = cards.masthead_memory()
        drawn = masthead.lines(avoid_shapes=shapes, avoid_lines=recent)
        cards.write_masthead(drawn)
        seen.append(drawn)
        assert cards.masthead_memory()[0] == masthead.shapes_in(drawn)
        assert len(cards.masthead_memory()[1]) <= masthead.memory_size()

    # Across more draws than the memory holds, nothing repeats inside it.
    for earlier, later in zip(seen, seen[1:]):
        assert not set(masthead.shapes_in(earlier)) & set(masthead.shapes_in(later))
    window = masthead.MEMORY_DRAWS
    for index in range(window, len(seen)):
        back = {line for draw in seen[index - window:index] for line in draw[1:]}
        assert not back & set(seen[index][1:]), "a line came back inside the window"


def test_the_committed_file_says_how_long_its_loop_takes(repo):
    """A number somebody can check against the reason the schedule exists."""
    lines = masthead.lines()
    cards.write_masthead(lines)
    state = cards.load_masthead_state()
    assert state["lines"] == lines
    assert abs(state["loop_seconds"] - cards.masthead_loop_seconds(lines)) < 0.1


# --- reading it on a phone -------------------------------------------------------

# The narrowest column a README gets in practice: a 360px phone viewport
# once GitHub's own gutters are taken out.
PHONE_COLUMN = 328


def _widest_image() -> float:
    """The widest image the generator can produce, in CSS pixels."""
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO
    return cards.MASTHEAD_TEXT_X * 2 + (cards.PROMPT_CELLS + cards.WRAP_CELLS) * cell


def test_every_line_the_generator_can_draw_fits_two_rows(repo):
    """The promise the whole wrap rests on, checked over all thousand.

    Three rows would make the image half again as tall for no gain, and the
    cap is chosen to be the last value where none of them needs one: at
    twenty four cells, twelve lines spill onto a third row.
    """
    for line in masthead.every_line():
        rows = cards.wrap(line)
        assert len(rows) <= 2, f"{len(rows)} rows: {line}"
        for row in rows:
            assert masthead.cells(row) <= cards.WRAP_CELLS, row


def test_the_masthead_is_readable_on_a_phone_without_being_shrunk(repo):
    """The bug a screenshot found, and the reason this wraps at all.

    GitHub scales a README image down to the column. One row of forty nine
    cells is a 570 pixel image, which arrives on a phone at 0.6 scale and an
    effective font of eleven pixels: a green smear. Wrapping holds the image
    narrow enough that almost nothing is lost.
    """
    scale = min(1.0, PHONE_COLUMN / _widest_image())
    assert cards.MASTHEAD_FONT_SIZE * scale >= 16.0, (
        f"{cards.MASTHEAD_FONT_SIZE * scale:.1f}px on a phone is too small to read")

    # And the real draws, which are narrower than the worst case.
    for _ in range(20):
        svg = cards.masthead_svg(masthead.lines())
        width = int(re.search(r'<svg[^>]*width="(\d+)"', svg).group(1))
        assert width <= _widest_image() + 1, width
        assert cards.MASTHEAD_FONT_SIZE * min(1.0, PHONE_COLUMN / width) >= 16.0


def test_wrapping_loses_nothing_and_invents_nothing(repo):
    """A wrap that drops or duplicates a word is a wrap nobody would catch."""
    for line in masthead.every_line():
        assert " ".join(cards.wrap(line)) == line


def test_the_wrap_is_balanced_rather_than_greedy(repo):
    """Greedy fills the first row and leaves the second holding two words,
    which reads as a mistake rather than as a wrapped line."""
    crowded = 0
    for line in masthead.every_line():
        rows = cards.wrap(line)
        if len(rows) < 2:
            continue
        shortest, longest = min(map(masthead.cells, rows)), max(map(masthead.cells, rows))
        if longest > shortest * 2:
            crowded += 1
    assert crowded == 0, f"{crowded} lines wrapped lopsidedly"


def test_a_wrapped_row_lines_up_under_the_text_and_not_the_prompt(repo):
    """The prompt belongs to the line, not to each row of it."""
    line = max(masthead.every_line(), key=masthead.cells)
    svg = cards.masthead_svg([line])
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO
    left = cards.MASTHEAD_TEXT_X + cards.PROMPT_CELLS * cell

    assert svg.count(cards.MASTHEAD_PROMPT) == 2, "one prompt animated, one still"
    xs = set(re.findall(r'<text x="([\d.]+)" y="\d+" clip-path=', svg))
    assert xs == {f"{left:.1f}"}, xs


def test_the_rows_sit_on_their_own_baselines(repo):
    """Two rows on one baseline is one row of mush."""
    line = max(masthead.every_line(), key=masthead.cells)
    svg = cards.masthead_svg([line])
    ys = [int(y) for y in re.findall(r'<text x="[\d.]+" y="(\d+)" clip-path=', svg)]
    assert len(ys) == len(cards.wrap(line)) == 2
    assert ys[1] - ys[0] == cards.ROW_HEIGHT
    assert int(re.search(r'<svg[^>]*height="(\d+)"', svg).group(1)) > ys[-1]


def test_the_cursor_drops_a_row_when_the_line_wraps(repo):
    """A terminal cursor follows the text onto the next row. This one has to
    as well, or it sits at the end of the first row while the second types."""
    line = max(masthead.every_line(), key=masthead.cells)
    svg = cards.masthead_svg([line])
    ys = [int(v) for v in
          re.search(r'attributeName="y" values="([^"]+)"', svg).group(1).split(";")]
    assert len(set(ys)) == 2, "the cursor never left the first row"
    assert max(ys) - min(ys) == cards.ROW_HEIGHT
    # It goes down once and comes back once, rather than flickering between.
    moves = sum(1 for a, b in zip(ys, ys[1:]) if a != b)
    assert moves == 2, moves


def test_only_one_cursor_is_ever_lit(repo):
    """Thirteen lines share one loop. Two cursors on screen at once is the
    kind of thing a reader sees without being able to say what is wrong."""
    lines = masthead.lines()
    svg = cards.masthead_svg(lines)
    tracks = re.findall(r'attributeName="opacity" values="([^"]+)" keyTimes="([^"]+)"', svg)
    assert len(tracks) == len(lines)

    # The greeting runs on its own timeline before the loop begins, so the
    # ones that can overlap are the looping lines.
    loop = [([int(v) for v in values.split(";")], [float(t) for t in times.split(";")])
            for values, times in tracks[1:]]
    moments = sorted({t for _, times in loop for t in times})
    for at in moments:
        lit = 0
        for values, times in loop:
            held = max((i for i, t in enumerate(times) if t <= at), default=0)
            lit += values[held]
        assert lit <= 1, f"{lit} cursors lit at {at}"
