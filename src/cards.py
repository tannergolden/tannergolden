# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The two cards on the page, drawn as SVG and committed.

Nothing on the page is fetched from an image service at render time. Both
are drawn from what the GitHub API says about the account's public
repositories. Each comes in a light and a dark variant, and the page switches between them with a
`<picture>` element, because a media query inside an image is honoured by
browsers but not by every proxy in between.

The language card is a chart, so it follows the chart rules: thin bars from
one baseline, a rounded data-end, every bar labelled directly so identity
never rests on colour alone, and the numbers repeated in the image's alt text
as the table view a static image cannot otherwise offer. Colours are each
language's own Linguist colour, which is the convention a reader of GitHub
already carries; the label is what makes them distinguishable, not the hue.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from pathlib import Path
from xml.sax.saxutils import escape

import masthead
from config import ASSETS_DIR

# --- the masthead ------------------------------------------------------------------

# No plate: the text sits on whatever colour GitHub is painting behind it,
# and that is white on one theme and near-black on the other. No single
# green clears 4.5:1 on both, so there are two files and a <picture>, the
# same answer the cards reach for and for the same reason.
MASTHEAD_INK = {
    "dark": "#00ff41",   # 13.9:1 on GitHub's #0d1117. The neon one.
    "light": "#067d17",  # 5.3:1 on white. Neon there is 1.4:1, invisible.
}

# The masthead's own stack, not the one the cards use. Everything here is
# measured in cells, so which monospace actually resolves decides whether
# the cursor lands against the text: the fonts that advance 0.600 to 0.602
# go first, and Consolas at 0.550 goes last, behind two that Windows and
# Linux both have.
MASTHEAD_FONT = ("ui-monospace, 'SF Mono', SFMono-Regular, Menlo, 'Cascadia Mono', "
                 "'DejaVu Sans Mono', 'Liberation Mono', Consolas, monospace")

# On one row this is a desktop decision and only a desktop decision. A phone
# divides its column by the cell count and lands on the same eleven pixels
# whatever is set here, so the size is chosen for the reader who sees it
# unscaled: a little more presence than the 18 it started at, and an image
# still well inside GitHub's column.
MASTHEAD_FONT_SIZE = 20

# A terminal's line spacing, and enough air above and below that the bloom
# has somewhere to go. Both follow the font rather than sitting beside it,
# so changing one number changes the block.
ROW_HEIGHT = round(MASTHEAD_FONT_SIZE * 1.45)
PAD_Y = round(MASTHEAD_FONT_SIZE * 0.45)

# Where a line breaks, if it breaks.
#
# It is set to the plate's own width, so nothing wraps. A masthead that
# breaks mid-sentence reads as a mistake on every screen, and that cost falls
# on every reader rather than only on the ones holding a phone. What a phone
# gets instead is nothing at all: below the breakpoint in `masthead_region`
# the image is swapped for a blank, because the plate cannot be made to fit
# there and a masthead scaled down is a smear of green.
#
# Lower this and the renderer wraps, balanced, onto as many rows as it
# takes. A test holds that path open so it cannot rot while it is unused.
WRAP_CELLS = masthead.MAX_CELLS

# Where the prompt sits. The clip rectangle is anchored at x=0, so every
# width it animates through has to carry this inset AND the prompt, or the
# end of a row is cut off and it never finishes typing. This page has
# shipped that bug once already.
MASTHEAD_TEXT_X = 16

# The prompt glyph and the space after it. It never animates and it is never
# clipped: it is what says "terminal" before a single character is typed,
# what gives the cursor somewhere to be born, and what a renderer that does
# not animate at all still has to show. It sits on the first row only, and
# a wrapped row lines up under the text rather than under the prompt.
MASTHEAD_PROMPT = "\u276f"
PROMPT_CELLS = 2

# How loud the prompt is, per scheme. Neon wants holding back or it competes
# with the words; the muted green the light variant is stuck with needs the
# opposite. It is furniture either way, not content, which is why it is
# allowed to sit below the contrast bar the text has to clear.
PROMPT_OPACITY = {"dark": 0.5, "light": 0.72}

# One cell as a fraction of the em, and the tolerance the cursor lives on.
# SF Mono, Menlo, Cascadia Mono and DejaVu Sans Mono all advance 0.600 to
# 0.602. This is a hair wider than the widest of them, on purpose: a cell
# too narrow makes the clip lag the glyphs and the end of a row never
# arrives, while too wide only runs the reveal ahead of the text and leaves
# the cursor floating clear of it. 0.61 left that float visible at a quarter
# of a character per ten cells.
CELL_RATIO = 0.605

# Typing is a constant cadence, because a terminal has one. Giving every
# line the same fixed duration whatever its length made a short line crawl
# and a long one blur past at three times the speed.
TYPE_CADENCE = 0.050    # seconds per cell typed: twenty cells a second
ERASE_CADENCE = 0.018   # and per cell erased, which is a wipe, not a performance
ERASE_STEP = 3          # cells per erase mark: a third of the keyframes, same motion

# The pause once a line is complete: a beat to notice it, plus reading time.
# Two hundred words a minute puts a six word line at about 1.8 seconds, so a
# line twice as long earns twice the pause rather than the same one.
HOLD_BASE = 0.95
HOLD_PER_CELL = 0.040

# Half a blink. The cursor is SOLID while it types and erases, the way a
# real one is, and blinks only while a finished line sits waiting to be read.
BLINK_SECONDS = 0.5

# How finely a keyTime is written. Four places of a minute-long cycle is
# three and a half milliseconds, finer than a frame at 120Hz. Marks are
# rounded to it BEFORE they are compared, because SMIL requires keyTimes to
# increase and two moments a femtosecond apart round to one string.
TIME_PLACES = 4

def _num(value: float, places: int = TIME_PLACES) -> str:
    """The shortest honest spelling of a number, for a file emitted by the thousand."""
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return text or "0"


def wrap(line: str, cap: int | None = None) -> list:
    """The fewest rows that fit the cap, then the evenest split of that many.

    Evenest, not greedy. Greedy wrapping fills the first row and leaves the
    second holding two words, which reads as a mistake rather than as a
    wrapped line. Balancing means searching the split points, which is free
    at this size: no line here has more than nine words.
    """
    # Read at the call rather than bound as a default, because a default
    # argument is evaluated once at import and a module constant that
    # silently stops applying is a bug this repository has already had.
    cap = WRAP_CELLS if cap is None else cap
    words = line.split(" ")
    for rows in range(1, len(words) + 1):
        best = None
        for cuts in itertools.combinations(range(1, len(words)), rows - 1):
            bounds = (0, *cuts, len(words))
            groups = [" ".join(words[a:b]) for a, b in zip(bounds, bounds[1:])]
            widest = max(masthead.cells(group) for group in groups)
            if widest <= cap and (best is None or widest < best[0]):
                best = (widest, groups)
        if best:
            return best[1]
    return [line]


def _rhythm(line: str, total: float) -> list:
    """Per-cell delays that sum to `total` but do not march.

    Nobody types to a metronome: there is a beat before a new word and a
    longer one after a full stop, and no two keystrokes are the same length.
    The variation is drawn from the line's own text rather than from chance,
    so the same line always types the same way and a run that redrew nothing
    produces a file that changed nothing.

    An emoji is two cells wide and one keystroke. Its second cell arrives in
    no time at all, so the clip never comes to rest through the middle of a
    glyph showing half a face.
    """
    # Not a secret: a seed taken from the text so the same line always types
    # the same way. SystemRandom here would rewrite both images on every run
    # and commit a diff that says nothing.
    rng = random.Random(  # noqa: S311
        int(hashlib.sha256(line.encode("utf-8")).hexdigest()[:8], 16))
    weights, previous, joined = [], "", False
    for char in line:
        if char in masthead.COMBINING:  # drawn inside the glyph before it
            joined = char == "‍"
            continue
        if joined:
            joined = False
            continue
        weight = rng.uniform(0.74, 1.30)
        if previous == " ":
            weight *= 1.45
        elif previous in ",.!?:;":
            weight *= 2.10
        weights.append(weight)
        if ord(char) > 0x2100:
            weights.append(0.0)  # the second cell of the pair, arriving with the first
        previous = char
    spread = sum(weights)
    scale = total / spread if spread else 0.0
    return [weight * scale for weight in weights]


def typed_cells(line: str) -> int:
    """Cells actually typed, which is the line minus the spaces a wrap ate."""
    return sum(masthead.cells(row) for row in wrap(line))


def masthead_slot(line: str) -> float:
    """How long one line owns the plate: typed, read, then wiped."""
    return (TYPE_CADENCE + HOLD_PER_CELL + ERASE_CADENCE) * typed_cells(line) + HOLD_BASE


def _reveal(rows: list, start: float, slot: float, cycle: float, cell: float) -> tuple:
    """Discrete marks for one line, across however many rows it wrapped onto.

    One walk for the whole line. Each row clips the same walk, offset by the
    cells the rows above it already hold, so a row that has not been reached
    shows nothing and a row already passed stays full. The cursor belongs to
    the line rather than to a row: it moves down when the walk crosses a
    break, which is what a terminal cursor does.

    A rectangle whose width grows continuously reveals letters through their
    own middles, which reads as a wipe rather than as typing. Stepping it by
    whole cells is what makes it look typed, and `calcMode="discrete"` holds
    each step until the next one.
    """
    lengths = [masthead.cells(row) for row in rows]
    offsets, running = [], 0
    for length in lengths:
        offsets.append(running)
        running += length
    total = running
    typing = TYPE_CADENCE * total
    holding = HOLD_BASE + HOLD_PER_CELL * total
    left = MASTHEAD_TEXT_X + PROMPT_CELLS * cell

    def shot(step: int) -> tuple:
        """Where every row stands once `step` cells of the line have been typed."""
        widths = [left + min(max(step - offset, 0), length) * cell
                  for offset, length in zip(offsets, lengths)]
        here = max(index for index, offset in enumerate(offsets) if offset <= step)
        return widths, widths[here] + 1, here

    blank = ([0.0] * len(rows), 1.0, 0, 0)
    marks = [(0.0, *blank)]

    # The cursor arrives at the prompt, then one cell per keystroke.
    at = start
    marks.append((at, *shot(0), 1))
    for step, delay in enumerate(_rhythm("".join(rows), typing), start=1):
        at += delay
        marks.append((at, *shot(step), 1))

    # The line sits and is read. Only here does the cursor blink.
    settled, dark = start + typing, 0
    widths, tip, here = shot(total)
    marks.append((settled, widths, tip, here, 1))
    blink = settled + BLINK_SECONDS
    while blink < settled + holding:
        marks.append((blink, widths, tip, here, dark))
        blink, dark = blink + BLINK_SECONDS, 1 - dark

    # And back down, faster, three cells at a time.
    erased = settled + holding
    for index, step in enumerate(range(total, -1, -ERASE_STEP)):
        marks.append((erased + ERASE_CADENCE * ERASE_STEP * index, *shot(step), 1))
    marks.append((erased + ERASE_CADENCE * total, *shot(0), 1))
    marks.append((start + slot, *blank))
    marks.append((cycle, *blank))

    times, seen = [], []
    for moment, widths, tip, here, on in marks:
        moment = round(min(max(moment / cycle, 0.0), 1.0), TIME_PLACES)
        if times and moment <= times[-1]:
            # Two marks at one instant: the later one wins, which is what
            # lets an emoji's two cells arrive together. The time itself is
            # left alone, because keyTimes must not go backwards and a
            # rounded sum can land a mark a hair before the one before it.
            seen[-1] = (widths, tip, here, on)
            continue
        times.append(moment)
        seen.append((widths, tip, here, on))

    per_row = [[frame[0][index] for frame in seen] for index in range(len(rows))]
    return times, per_row, [f[1] for f in seen], [f[2] for f in seen], [f[3] for f in seen]


def _glow() -> list:
    """Light around the glyphs, with the glyphs themselves left alone.

    The first version blurred the text and merged that blur back over
    itself. That thickens every stroke and softens every edge, which on a
    phone, where a stroke is two pixels to begin with, is the difference
    between reading it and squinting at it. What a phosphor actually looks
    like is a hard glyph sitting in light, so both blurs are dimmed and laid
    BEHIND an untouched SourceGraphic: near light close in, far light well
    beyond, and nothing at all on the letterforms.

    The radii follow the font rather than sitting beside it, so the bloom
    does not change character when the type does.

    `color-interpolation-filters="sRGB"` is not a detail. The default is
    linearRGB, which turns a saturated green bloom into a pale grey one.
    """
    near = MASTHEAD_FONT_SIZE * 0.085
    far = MASTHEAD_FONT_SIZE * 0.24
    return [
        '<filter id="g" x="-10%" y="-45%" width="120%" height="190%" '
        'color-interpolation-filters="sRGB">',
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{_num(near, 2)}" result="near"/>',
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="{_num(far, 2)}" result="far"/>',
        '<feColorMatrix in="near" type="matrix" result="glow" '
        'values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.5 0"/>',
        '<feColorMatrix in="far" type="matrix" result="halo" '
        'values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.3 0"/>',
        '<feMerge><feMergeNode in="halo"/><feMergeNode in="glow"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge>',
        "</filter>",
    ]


def masthead_svg(lines: list, scheme: str = "dark") -> str:
    """The lines typed out on nothing, in pure SMIL.

    No script: GitHub strips those from an SVG in a README, which is why the
    animation is SMIL and the text is chosen in Python rather than here. The
    background is transparent, so the glow is only drawn on the dark variant,
    where a bloom reads as neon rather than as a smudge.

    ONE ROW. The plate is 34 cells and the generator only draws lines that
    fit it, so nothing here wraps, though the renderer still can: lower
    WRAP_CELLS and every line splits, balanced, onto as many rows as it
    takes. Which reader gets this image at all is decided outside it, by the
    media queries in `masthead_region`.

    THE GREETING RUNS ONCE. It is a greeting, and one that greets the same
    reader again every minute is a tic rather than a welcome. It types on its
    own timeline with `repeatCount="1"` and then stays gone, which leaves the
    drawn lines looping among themselves on a second timeline that begins
    where the first one ends.

    NO SMIL, NO BLANK. A renderer that ignores the animations shows the
    greeting complete, because the greeting's clip carries its full width as
    a plain attribute and an animation overrides that rather than supplying
    it. Reduced motion is NOT handled here: a preference media query inside
    an SVG loaded as an <img> never matches, which was checked in a real
    browser after a review called it doubtful. It is handled by
    `masthead_still_svg` and a <picture> source, where the query is
    evaluated against the page instead.
    """
    lines = [line for line in lines if line] or [masthead.GREETING]
    ink = MASTHEAD_INK.get(scheme, MASTHEAD_INK["dark"])
    cell = MASTHEAD_FONT_SIZE * CELL_RATIO
    rows = [wrap(line) for line in lines]

    tall = max(len(row) for row in rows)
    height = tall * ROW_HEIGHT + PAD_Y * 2
    widest = max(masthead.cells(row) for line in rows for row in line)
    left = MASTHEAD_TEXT_X + PROMPT_CELLS * cell
    width = int(left + widest * cell) + MASTHEAD_TEXT_X
    baselines = [PAD_Y + ROW_HEIGHT * index + ROW_HEIGHT // 2 + MASTHEAD_FONT_SIZE // 3
                 for index in range(tall)]

    # Two timelines. The first holds the greeting alone and never repeats;
    # the second holds everything else and repeats for as long as the page is
    # open, starting the moment the greeting has finished erasing. Each line
    # owns the plate for as long as its own length earns, so a short line no
    # longer waits out a slot cut for a long one.
    slots = [masthead_slot(line) for line in lines]
    intro = slots[0]
    loop = sum(slots[1:]) or intro
    intro_dur = f'dur="{_num(intro, 2)}s" repeatCount="1" fill="freeze"'
    loop_dur = f'begin="{_num(intro, 2)}s" dur="{_num(loop, 2)}s" repeatCount="indefinite"'

    frames, durs, running = [], [], 0.0
    for index in range(len(lines)):
        if index == 0:
            frames.append(_reveal(rows[0], 0.0, intro, intro, cell))
            durs.append(intro_dur)
        else:
            frames.append(_reveal(rows[index], running, slots[index], loop, cell))
            durs.append(loop_dur)
            running += slots[index]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">',
        '<title id="t">A terminal typing out what this account is for</title>',
        f"<desc id=\"d\">{escape(' / '.join(lines))}</desc>",
        "<defs>",
    ]
    if scheme == "dark":
        out += _glow()
    for index, (times, per_row, _, _, _) in enumerate(frames):
        key_times = ";".join(_num(t) for t in times)
        for row, widths in enumerate(per_row):
            # The greeting's rectangles are open before anything animates
            # them, so a renderer that ignores SMIL shows a finished greeting
            # rather than an empty box. `fill="freeze"` is what stops the
            # animation handing that same full width back at the end of its
            # one run.
            still = _num(left + masthead.cells(rows[0][row]) * cell, 1) if index == 0 else "0"
            out.append(
                f'<clipPath id="c{index}-{row}">'
                f'<rect x="0" y="0" width="{still}" height="{height}">'
                f'<animate attributeName="width" values="{";".join(_num(w, 1) for w in widths)}" '
                f'keyTimes="{key_times}" calcMode="discrete" {durs[index]}/></rect></clipPath>'
            )
    out.append("</defs>")
    out.append(
        "<style>"
        f"text{{font-family:{MASTHEAD_FONT};font-size:{MASTHEAD_FONT_SIZE}px;fill:{ink};"
        "white-space:pre;font-variant-ligatures:none;font-kerning:none;"
        "text-rendering:geometricPrecision}"
        f".p{{opacity:{PROMPT_OPACITY.get(scheme, 0.55)}}}"
        "</style>"
    )

    filtered = ' filter="url(#g)"' if scheme == "dark" else ""

    out.append(f'<g class="anim"{filtered}>')
    # The prompt is never clipped and never animates. It is the one thing on
    # the plate that is always there.
    out.append(
        f'<text class="p" x="{MASTHEAD_TEXT_X}" y="{baselines[0]}">{MASTHEAD_PROMPT}</text>'
    )
    for index, wrapped in enumerate(rows):
        for row, text in enumerate(wrapped):
            out.append(
                f'<text x="{_num(left, 1)}" y="{baselines[row]}" '
                f'clip-path="url(#c{index}-{row})">{escape(text)}</text>'
            )

    # One cursor per line, not per row. It sits at the typed edge and drops a
    # row when the line wraps, the way a terminal cursor does. Its opacity
    # carries both jobs at once: whether this line's turn is running at all,
    # and the blink, which only happens while a finished line waits.
    for index, (times, _, tips, here, lit) in enumerate(frames):
        key_times = ";".join(_num(t) for t in times)
        top = baselines[0] - MASTHEAD_FONT_SIZE + 2
        out.append(
            f'<g opacity="0"><animate attributeName="opacity" values="{";".join(str(b) for b in lit)}" '
            f'keyTimes="{key_times}" calcMode="discrete" {durs[index]}/>'
            f'<rect width="{_num(cell * 0.85, 1)}" height="{MASTHEAD_FONT_SIZE + 2}" fill="{ink}">'
            f'<animate attributeName="x" values="{";".join(_num(x, 1) for x in tips)}" '
            f'keyTimes="{key_times}" calcMode="discrete" {durs[index]}/>'
            f'<animate attributeName="y" '
            f'values="{";".join(str(top + ROW_HEIGHT * r) for r in here)}" '
            f'keyTimes="{key_times}" calcMode="discrete" {durs[index]}/></rect></g>'
        )
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


# How much of the set the still variant carries. Four rows is a terminal
# somebody has been typing in, which is the point; thirteen is a wall of
# text where a masthead should be.
STILL_ROWS = 4


def masthead_still_svg(lines: list, scheme: str = "dark") -> str:
    """The same masthead with nothing moving, for a reader who asked for that.

    Not a frame of the animation: a transcript of it. Each line gets its own
    prompt, the way a terminal shows what has already been typed, so reduced
    motion costs the reader the movement rather than the content.

    It exists as a separate FILE because the switch cannot live inside the
    image. `prefers-reduced-motion` in an SVG's own stylesheet never matches
    when that SVG is loaded as an <img>: the preference does not reach the
    isolated image document. A <picture> source is evaluated against the page
    itself, where it does.
    """
    shown = [line for line in lines if line][:STILL_ROWS] or [masthead.GREETING]
    ink = MASTHEAD_INK.get(scheme, MASTHEAD_INK["dark"])
    cell = MASTHEAD_FONT_SIZE * CELL_RATIO
    widest = max(masthead.cells(line) for line in shown)
    width = int(MASTHEAD_TEXT_X + (PROMPT_CELLS + widest) * cell) + MASTHEAD_TEXT_X
    height = len(shown) * ROW_HEIGHT + PAD_Y * 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">',
        '<title id="t">A terminal, and what it has been typing</title>',
        f"<desc id=\"d\">{escape(' / '.join(lines))}</desc>",
    ]
    if scheme == "dark":
        out += ["<defs>", *_glow(), "</defs>"]
    out.append(
        "<style>"
        f"text{{font-family:{MASTHEAD_FONT};font-size:{MASTHEAD_FONT_SIZE}px;fill:{ink};"
        "white-space:pre;font-variant-ligatures:none;font-kerning:none;"
        "text-rendering:geometricPrecision}"
        f".p{{opacity:{PROMPT_OPACITY.get(scheme, 0.55)}}}"
        "</style>"
    )
    out.append('<g filter="url(#g)">' if scheme == "dark" else "<g>")
    for row, line in enumerate(shown):
        baseline = PAD_Y + ROW_HEIGHT * row + ROW_HEIGHT // 2 + MASTHEAD_FONT_SIZE // 3
        out.append(
            f'<text x="{MASTHEAD_TEXT_X}" y="{baseline}">'
            f'<tspan class="p">{MASTHEAD_PROMPT}</tspan> {escape(line)}</text>'
        )
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def masthead_loop_seconds(lines: list) -> float:
    """How long the looping part takes to come round, for the record."""
    return sum(masthead_slot(line) for line in lines[1:]) or masthead_slot(lines[0])


def load_masthead_state() -> dict:
    """What the committed image says about itself."""
    try:
        loaded = json.loads(Path(f"{ASSETS_DIR}/masthead.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def load_masthead_lines() -> list:
    """What the committed image types, for the alt text of a render that drew nothing."""
    return [str(line) for line in (load_masthead_state().get("lines") or [])]


def masthead_memory() -> tuple:
    """The shapes the last draw used and the lines the last few did.

    This is what stops a random draw from repeating itself sooner than
    anybody expects. Read from the committed file rather than from a state
    directory, because the image and the memory of how it was drawn belong
    to the same commit and should never be able to disagree.
    """
    state = load_masthead_state()
    shapes = [str(s) for s in (state.get("shapes") or [])]
    recent = [str(line) for line in (state.get("recent") or [])]
    return shapes, recent


def write_masthead(lines: list) -> dict:
    """One file per colour scheme, because no green is legible on both.

    The JSON beside them is not a cache. It is the alt text for the many
    renders that do not redraw the image, and the memory the next redraw
    reads so it can avoid what this one just used.
    """
    drawn = list(lines)
    _, recent = masthead_memory()
    memory = [line for line in recent if line not in drawn] + drawn[1:]
    _write(f"{ASSETS_DIR}/masthead.json", json.dumps({
        "lines": drawn,
        "shapes": masthead.shapes_in(drawn),
        "recent": memory[-masthead.memory_size():],
        "loop_seconds": round(masthead_loop_seconds(drawn), 1),
    }, indent=2) + "\n")
    # What a phone gets instead. One transparent pixel: the <img> collapses
    # to nothing rather than reserving a band of empty page.
    _write(f"{ASSETS_DIR}/masthead-blank.svg",
           '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" '
           'viewBox="0 0 1 1" role="presentation" aria-hidden="true"></svg>\n')
    written = {}
    for scheme in MASTHEAD_INK:
        written[scheme] = _write(f"{ASSETS_DIR}/masthead-{scheme}.svg",
                                 masthead_svg(drawn, scheme))
        _write(f"{ASSETS_DIR}/masthead-still-{scheme}.svg",
               masthead_still_svg(drawn, scheme))
    return written


# GitHub's README gutters on a narrow screen, both sides together. The
# breakpoint below is the plate plus this: the width at which the image
# would have to start shrinking.
GUTTERS = 32


def masthead_breakpoint() -> int:
    """The viewport width below which the masthead can no longer be read.

    Derived rather than picked. The plate is as wide as it is, GitHub gives
    a README about this much less than the viewport, and below the sum the
    image gets scaled down and the type with it. A number typed in by hand
    here would be wrong the first time the plate changed.
    """
    cell = MASTHEAD_FONT_SIZE * CELL_RATIO
    plate = MASTHEAD_TEXT_X * 2 + (PROMPT_CELLS + masthead.PLATE_CELLS) * cell
    return int(plate) + GUTTERS - 1


def masthead_region() -> str:
    """The image, cache-busted, with every line it types in the alt text.

    FOUR SOURCES, AND THE ORDER IS THE WHOLE THING. A browser takes the
    first <source> whose media matches, so the narrower conditions come
    first: a phone in dark mode would never reach the width query if the
    colour one were above it, and a reader who has reduced motion AND dark
    mode would never reach the still.

    Width first. Below the breakpoint the image can only be scaled down, and
    a masthead scaled down is a smear of green where a first impression
    should be; nothing is better than that, so a phone is handed one
    transparent pixel.

    Reduced motion next, because this is the one place it can be honoured.
    The same query inside the SVG's own stylesheet never matches when the
    SVG is loaded as an <img>, since the preference does not reach the
    isolated image document; here it is evaluated against the page.

    Then the colour scheme, which is the ordinary case, and the <img> that
    carries the alt text for all of them. A screen reader reads alt from the
    <img> whichever source the browser picked, so hiding this on a phone
    stays a visual decision rather than an accessibility one.

    All of it rests on GitHub's markdown sanitiser keeping `media` on a
    <source> whatever the query says. That is documented nowhere and was
    checked rather than assumed: a probe pushed to a branch came back
    through the renderer intact.
    """
    lines = load_masthead_lines() or [masthead.GREETING]
    def tagged(name):
        path = f"{ASSETS_DIR}/{name}.svg"
        return f"{path}?v={content_tag(path)}"

    alt = escape(" / ".join(lines), {chr(34): "&quot;"})
    sources = [
        (f"(max-width: {masthead_breakpoint()}px)", "masthead-blank"),
        ("(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)",
         "masthead-still-dark"),
        ("(prefers-reduced-motion: reduce)", "masthead-still-light"),
        ("(prefers-color-scheme: dark)", "masthead-dark"),
    ]
    return "\n".join([
        "<picture>",
        *[f'  <source media="{media}" srcset="{tagged(name)}">' for media, name in sources],
        f'  <img alt="{alt}" src="{tagged("masthead-light")}">',
        "</picture>",
    ])


# --- writing the files ----------------------------------------------------------------

def _write(path: str, content: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")
    return path


def content_tag(path: str) -> str:
    """Eight hex characters of the file's hash: the cache-busting query string.

    GitHub's image proxy caches by URL, so a file rewritten at a stable path
    can keep showing its previous contents for hours. A tag derived from the
    bytes changes exactly when the image does and never otherwise.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]
    except OSError:
        return "0"


