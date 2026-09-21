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
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import masthead
import net
from config import ASSETS_DIR

LINGUIST = "https://raw.githubusercontent.com/github-linguist/linguist/master/lib/linguist/languages.yml"
GRAPHQL = "https://api.github.com/graphql"
API = "https://api.github.com"

# Surfaces and ink from the reference palette, one set per scheme. The dark
# set is its own selection, not an inversion of the light one.
THEMES = {
    "light": {"surface": "#fcfcfb", "border": "#e1e0d9", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "track": "#e1e0d9"},
    "dark": {"surface": "#1a1a19", "border": "#383835", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781", "track": "#2c2c2a"},
}

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# When the Linguist registry cannot be fetched, the languages this account is
# most likely to show still get their conventional colour.
FALLBACK_COLORS = {
    "Python": "#3572A5", "Shell": "#89e051", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Go": "#00ADD8", "Rust": "#dea584", "Makefile": "#427819", "HTML": "#e34c26", "CSS": "#663399",
    "Dockerfile": "#384d54", "Java": "#b07219", "C": "#555555", "C++": "#f34b7d", "Ruby": "#701516",
    "Jupyter Notebook": "#DA5B0B", "Lua": "#000080", "Swift": "#F05138", "Kotlin": "#A97BFF",
}


def _svg_header(width: int, height: int, title: str, theme: dict) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">\n'
        f"<title id=\"t\">{escape(title)}</title>\n"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" '
        f'fill="{theme["surface"]}" stroke="{theme["border"]}"/>\n'
    )


# --- the masthead ------------------------------------------------------------------

# No plate: the text sits on whatever colour GitHub is painting behind it,
# and that is white on one theme and near-black on the other. No single
# green clears 4.5:1 on both, so there are two files and a <picture>, the
# same answer the cards reach for and for the same reason.
MASTHEAD_INK = {
    "dark": "#00ff41",   # 13.9:1 on GitHub's #0d1117. The neon one.
    "light": "#067d17",  # 5.3:1 on white. Neon there is 1.4:1, invisible.
}

# Bigger than it looks like it should be, and that is the wrapping paying
# for itself. Once a row fits a phone's column without scaling, the font and
# the image grow together and the effective size on a phone barely moves:
# 18px in a 339px image lands at 17.4 on a 328px column, 22px in a 408px one
# lands at 17.7. The desktop reader is the one who notices, and they get a
# masthead with presence rather than a caption.
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
# GitHub scales a README image down to the column, and the column on a phone
# is about 330 CSS pixels. Fifty-one cells across that column is seven pixels
# a cell whatever the font says, so ONE ROW ON A PHONE IS ELEVEN PIXELS AND
# NO SETTING HERE CHANGES IT. Wrapping at twenty-six was the only thing that
# moved the number, and it moved it to twenty.
#
# It is set to the plate's own width anyway, so nothing wraps. A masthead
# that breaks mid-sentence reads as a mistake on every screen, and that cost
# falls on every reader rather than only on the ones holding a phone. What
# made eleven pixels survivable was the lighting: the glow used to be laid
# over the glyphs and is now only behind them, which is most of what the
# screenshot was actually complaining about.
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

    IT WRAPS. A line that fits on one row is a 570 pixel image, and GitHub
    scales that down to a phone's column until the text is eleven pixels of
    green smear. Wrapping at twenty six cells makes the image narrow enough
    to need no scaling at all, which is the difference between a masthead a
    phone can read and one it cannot.

    THE GREETING RUNS ONCE. It is a greeting, and one that greets the same
    reader again every minute is a tic rather than a welcome. It types on its
    own timeline with `repeatCount="1"` and then stays gone, which leaves the
    drawn lines looping among themselves on a second timeline that begins
    where the first one ends.

    THREE WAYS TO READ IT. A browser types it. A renderer with no SMIL shows
    the greeting complete, because the greeting's clip carries its full width
    as a plain attribute and an animation is what overrides that rather than
    what supplies it. A reader who has asked for less motion gets the same
    still line, from a layer the media query swaps in.
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
        ".still{display:none}"
        "@media (prefers-reduced-motion:reduce){.anim{display:none}.still{display:inline}}"
        "</style>"
    )

    filtered = ' filter="url(#g)"' if scheme == "dark" else ""

    # What a reader who asked for less motion sees instead: the same prompt,
    # the same greeting, none of it moving.
    still = [f'<g class="still"{filtered}>']
    for row, text in enumerate(rows[0]):
        prompt = f'<tspan class="p">{MASTHEAD_PROMPT}</tspan> ' if row == 0 else "  "
        still.append(f'<text x="{MASTHEAD_TEXT_X}" y="{baselines[row]}">'
                     f"{prompt}{escape(text)}</text>")
    out.append("".join(still) + "</g>")

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
    return {
        scheme: _write(f"{ASSETS_DIR}/masthead-{scheme}.svg", masthead_svg(drawn, scheme))
        for scheme in MASTHEAD_INK
    }


def masthead_region() -> str:
    """The image, cache-busted, with every line it types in the alt text."""
    return picture("masthead", " / ".join(load_masthead_lines() or [masthead.GREETING]))


# --- the account's numbers --------------------------------------------------------

def _headers(token: str | None) -> dict:
    return net.github_headers(token)


def _linguist_colors() -> dict:
    text = net.get_text(LINGUIST)
    if not text:
        return dict(FALLBACK_COLORS)
    colors = dict(FALLBACK_COLORS)
    current = None
    for line in text.splitlines():
        head = re.match(r"^([^\s#][^:]*):\s*$", line)
        if head:
            current = head.group(1).strip().strip('"')
            continue
        color = re.match(r"^\s+color:\s*\"?(#[0-9A-Fa-f]{6})\"?", line)
        if color and current:
            colors[current] = color.group(1)
    return colors


def github_stats(login: str, token: str | None) -> dict | None:
    """Public numbers for the account: repositories, stars, followers, this year's activity, languages."""
    headers = _headers(token)
    user = net.get_json_with_headers(f"{API}/users/{login}", None, headers)
    if not isinstance(user, dict) or "login" not in user:
        return None

    repos: list = []
    for page in range(1, 6):
        batch = net.get_json_with_headers(
            f"{API}/users/{login}/repos", {"per_page": 100, "type": "owner", "page": page}, headers
        )
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(r for r in batch if isinstance(r, dict))
        if len(batch) < 100:
            break

    own = [r for r in repos if not r.get("fork") and not r.get("archived")]
    stars = sum(int(r.get("stargazers_count") or 0) for r in own)
    forks = sum(int(r.get("forks_count") or 0) for r in own)

    languages: dict = {}
    for repo in own:
        url = repo.get("languages_url")
        if not url:
            continue
        found = net.get_json_with_headers(url, None, headers)
        if isinstance(found, dict):
            for name, size in found.items():
                languages[name] = languages.get(name, 0) + int(size or 0)

    year_start = datetime(datetime.now(timezone.utc).year, 1, 1, tzinfo=timezone.utc).isoformat()
    commits = pulls = issues = contributed = None
    if token:
        payload = net.post_json(
            GRAPHQL,
            {
                "query": (
                    "query($login:String!,$from:DateTime!){user(login:$login){"
                    "contributionsCollection(from:$from){totalCommitContributions "
                    "totalPullRequestContributions totalIssueContributions}"
                    "repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}}}"
                ),
                "variables": {"login": login, "from": year_start},
            },
            headers,
        )
        data = (payload or {}).get("data", {}).get("user") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            coll = data.get("contributionsCollection") or {}
            commits = coll.get("totalCommitContributions")
            pulls = coll.get("totalPullRequestContributions")
            issues = coll.get("totalIssueContributions")
            contributed = (data.get("repositoriesContributedTo") or {}).get("totalCount")

    return {
        "login": login,
        "public_repos": int(user.get("public_repos") or 0),
        "followers": int(user.get("followers") or 0),
        "stars": stars,
        "forks": forks,
        "commits": commits,
        "pulls": pulls,
        "issues": issues,
        "contributed": contributed,
        "languages": languages,
        "year": datetime.now(timezone.utc).year,
    }


# --- the two cards ------------------------------------------------------------------

def _fmt(value) -> str:
    if value is None:
        return "n/a"
    value = int(value)
    return f"{value / 1000:.1f}k" if value >= 10_000 else f"{value:,}"


def stats_svg(stats: dict, theme: dict) -> str:
    rows = [
        ("Public repositories", stats["public_repos"]),
        ("Stars earned", stats["stars"]),
        ("Followers", stats["followers"]),
        (f"Commits in {stats['year']}", stats["commits"]),
        (f"Pull requests in {stats['year']}", stats["pulls"]),
        ("Repositories contributed to", stats["contributed"]),
    ]
    width, row_h, top = 400, 26, 52
    height = top + row_h * len(rows) + 14
    out = [_svg_header(width, height, f"GitHub statistics for {stats['login']}", theme)]
    out.append(f'<style>text{{font-family:{SANS}}}</style>')
    out.append(f'<text x="20" y="30" font-size="15" font-weight="600" fill="{theme["ink"]}">{escape(stats["login"])}</text>')
    out.append(f'<text x="{width - 20}" y="30" font-size="11" text-anchor="end" fill="{theme["muted"]}">public activity</text>')
    for index, (label, value) in enumerate(rows):
        y = top + row_h * index + 12
        out.append(f'<text x="20" y="{y}" font-size="13" fill="{theme["ink2"]}">{escape(label)}</text>')
        out.append(f'<text x="{width - 20}" y="{y}" font-size="13" font-weight="600" text-anchor="end" fill="{theme["ink"]}">{escape(_fmt(value))}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def languages_svg(languages: dict, colors: dict, theme: dict, limit: int = 6) -> str:
    total = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    width, row_h, top_y, bar_x, bar_w, bar_h = 400, 28, 50, 130, 190, 12
    height = top_y + row_h * max(len(top), 1) + 12
    out = [_svg_header(width, height, "Top languages across public repositories", theme)]
    out.append(f'<style>text{{font-family:{SANS}}}</style>')
    out.append(f'<text x="20" y="30" font-size="15" font-weight="600" fill="{theme["ink"]}">Top languages</text>')
    out.append(f'<text x="{width - 20}" y="30" font-size="11" text-anchor="end" fill="{theme["muted"]}">by bytes, public repositories</text>')
    if not top:
        out.append(f'<text x="20" y="{top_y + 14}" font-size="13" fill="{theme["ink2"]}">No language data yet.</text>')
    for index, (name, size) in enumerate(top):
        share = size / total
        y = top_y + row_h * index
        fill = colors.get(name, theme["muted"])
        length = max(4.0, bar_w * share)
        out.append(f'<text x="20" y="{y + 10}" font-size="12" fill="{theme["ink2"]}">{escape(name)}</text>')
        out.append(f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{theme["track"]}"/>')
        # Rounded at the data end, square at the baseline: a rounded rect with
        # its left corners covered by a short square one.
        out.append(f'<rect x="{bar_x}" y="{y}" width="{length:.1f}" height="{bar_h}" rx="4" fill="{fill}"/>')
        if length > 8:
            out.append(f'<rect x="{bar_x}" y="{y}" width="4" height="{bar_h}" fill="{fill}"/>')
        out.append(f'<text x="{width - 20}" y="{y + 10}" font-size="12" font-weight="600" text-anchor="end" fill="{theme["ink"]}">{share * 100:.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def languages_alt(languages: dict, limit: int = 6) -> str:
    total = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    if not top:
        return "Top languages across public repositories: no data yet."
    parts = [f"{name} {size / total * 100:.1f}%" for name, size in top]
    return "Top languages across public repositories: " + ", ".join(parts) + "."


def stats_alt(stats: dict) -> str:
    return (
        f"GitHub statistics for {stats['login']}: {_fmt(stats['public_repos'])} public repositories, "
        f"{_fmt(stats['stars'])} stars, {_fmt(stats['followers'])} followers, "
        f"{_fmt(stats['commits'])} commits and {_fmt(stats['pulls'])} pull requests in {stats['year']}."
    )


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


def write_cards(stats: dict) -> dict:
    colors = _linguist_colors()
    written = {}
    for scheme, theme in THEMES.items():
        written[f"stats-{scheme}"] = _write(f"{ASSETS_DIR}/stats-{scheme}.svg", stats_svg(stats, theme))
        written[f"languages-{scheme}"] = _write(
            f"{ASSETS_DIR}/languages-{scheme}.svg", languages_svg(stats["languages"], colors, theme)
        )
    _write(
        f"{ASSETS_DIR}/cards.json",
        json.dumps({"stats_alt": stats_alt(stats), "languages_alt": languages_alt(stats["languages"])}, indent=2) + "\n",
    )
    return written


def load_card_alts() -> dict:
    try:
        return json.loads(Path(f"{ASSETS_DIR}/cards.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def picture(name: str, alt: str) -> str:
    """A `<picture>` that switches with the reader's colour scheme, cache-busted per file."""
    dark = f"{ASSETS_DIR}/{name}-dark.svg"
    light = f"{ASSETS_DIR}/{name}-light.svg"
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{dark}?v={content_tag(dark)}">\n'
        f'  <img alt="{escape(alt, {chr(34): "&quot;"})}" src="{light}?v={content_tag(light)}">\n'
        "</picture>"
    )
