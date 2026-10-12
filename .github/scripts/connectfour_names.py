# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named for what its drop plainly is in Connect Four: an emoji, a commander's call, and plain words.

  from connectfour_names import listing

A name says only what anyone can see of a drop on the frame: the colour of
the disc, the column it goes down, the row it lands on and what it lands on
(the frame's floor, a disc of its own colour, or one of the other side's),
whether that column is the centre or an edge, and whether the disc fills the
column's last row. It never says what the drop does to the game, and nothing
in it is found by looking ahead: a drop that connects four, one that takes the
cell the other side would connect four on, one that lets them connect four
next and one that changes nothing read the same when they go down the same
column to the same row, onto the same colour.

The emoji names the kind of drop, the same for every drop of that kind: 🔝
the disc that fills a column's last row, 🧱 a disc onto another, of either
colour, and a column's first disc by its column, ⬅️ and ➡️ the edges and ⬇️
any other, the centre's too: no column is starred, since the centre is the
strongest in the game and a star there would read as advice. The title is a
commander's call
in the game's own words, "Stack White on White in Column 6!", and always names
the column, so no two drops on one board share a title. A hash of the cell the
disc lands on picks among the true calls kept for its kind, so a drop is
called the same on every frame, whichever colour drops it. The notation is the
column alone, `4`, and the words say where the disc goes and nothing more: "A
white disc down column 4, to row 1". Stdlib only, with connectfour_rules.py
beside it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from connectfour_rules import COLS, DARK, LIGHT, ROWS, Position, legal, other

DISC = {DARK: "black", LIGHT: "white"}  # each colour's discs, as a move's words name them
SIDE = {DARK: "Black", LIGHT: "White"}  # and each colour, as a call names it
LONGEST = 48  # the longest title tannergolden/markdown takes
WORDS = 80  # the longest words tannergolden/markdown takes
CENTRE, EDGES = 4, {1: "Left", COLS: "Right"}
PLACE = {CENTRE: "the Centre Column", 1: "the Left Edge", COLS: "the Right Edge"}  # a column by its region


@dataclass(frozen=True)
class Drop:
    """What one drop plainly is: the disc, where it goes, and what it lands on."""
    colour: str  # the disc's, D or L: the side to drop's
    col: int  # the column it goes down, 1 to 7 from the left
    row: int  # the row it lands on, 1 to 6 from the foot
    below: str  # what it lands on: "floor" on row 1, "own" on a disc of its colour, "theirs" on the other side's


def drop(position: Position, col: int) -> Drop:
    """What dropping a disc down the column is, the side to drop being whichever the position says."""
    row = position.height(col) + 1
    under = position.at(col, row - 1)
    return Drop(position.turn, col, row, "floor" if not under else "own" if under == position.turn else "theirs")


def kind(d: Drop) -> str:
    """The kind of drop its emoji names: the disc that fills the column's last row, else a disc onto another, and for
    a column's first disc, whether the column is an edge."""
    if d.row == ROWS:
        return "top"
    if d.below != "floor":
        return "onto"
    return "left" if d.col == 1 else "right" if d.col == COLS else "floor"


# --- the calls -------------------------------------------------------------------------------------------------------
# Each call is a true title for every drop it is kept for: the disc that fills its column's last row, or else one
# that lands on the floor, on its own colour or on the other side's. `{colour}` is the disc's colour and `{other}` the
# other side's, `{row}` the row the disc lands on, and the column is `{place}` ("Column 3", "the Centre Column", "the
# Left Edge"), `{at}` the same as a place ("in Column 3", "on the Left Edge") and `{down}` the way the disc goes
# ("Down Column 3"). A hash of the calls kept and the cell the disc lands on picks one.
EMOJI = {"top": "🔝", "onto": "🧱", "left": "⬅️", "right": "➡️", "floor": "⬇️"}
TITLES = {
    "floor": ("Drop {colour} {down}!", "Send a {colour} Disc {down}!", "Slide {colour} {down} to Row 1!",
              "Drop {colour} to Row 1 {at}!", "Lay the First Disc {at}!", "Send {colour} to the Floor {at}!"),
    "own": ("Stack {colour} on {colour} {at}!", "Drop {colour} Onto {colour} {at}!", "Lay {colour} Over {colour} {at}!",
            "Stack {colour} to Row {row} {at}!", "Set {colour} Atop {colour} {at}!", "Put {colour} on {colour} {at}!"),
    "theirs": ("Lay {colour} on {other} {at}!", "Drop {colour} Onto {other} {at}!", "Set {colour} Atop {other} {at}!",
               "Stack {colour} on {other} {at}!", "Land {colour} on {other} {at}!", "Put {colour} on {other} {at}!"),
    "top": ("Top Off {place}!", "Fill {place} to the Top!", "Top Off {place} With {colour}!",
            "Fill the Top Cell {at}!", "Lay the Sixth Disc {at}!", "Drop {colour} to Row 6 {at}!"),
}


def calls(d: Drop) -> str:
    """Which of TITLES' calls fit the drop: those for the disc that fills its column, else those for what it lands
    on."""
    return "top" if d.row == ROWS else d.below


def facts(d: Drop) -> dict:
    """What a call can name about the drop: the two colours, the row it lands on, and its column as a place."""
    place = PLACE.get(d.col, f"Column {d.col}")
    return {"colour": SIDE[d.colour], "other": SIDE[other(d.colour)], "row": d.row, "place": place,
            "at": f"{'on' if d.col in EDGES else 'in'} {place}", "down": f"Down {place}"}


def title(d: Drop) -> tuple[str, str]:
    """The drop's emoji and title. A hash of the calls that fit and the cell the disc lands on picks the call, and
    nothing else does: not the rest of the frame, not the colour, and not what the drop does."""
    key = calls(d)
    seed = int.from_bytes(hashlib.sha256(f"connectfour:{key}:{d.col}:{d.row}".encode()).digest()[:8], "big")
    return EMOJI[kind(d)], TITLES[key][seed % len(TITLES[key])].format(**facts(d))


# --- the words -------------------------------------------------------------------------------------------------------
def said(d: Drop) -> str:
    """The words for a drop: where the disc goes, and nothing more."""
    return f"A {DISC[d.colour]} disc down column {d.col}, to row {d.row}"


def words(position: Position, col: int) -> str:
    """The drop in plain words: `A white disc down column 4, to row 1`."""
    return said(drop(position, col))


# --- the board's list ------------------------------------------------------------------------------------------------
def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open column from the left, each with its notation (the column alone), its words, an emoji and a title
    no other drop here has. The game and the move number name nothing: a drop is named for what it is alone."""
    out = []
    for col in legal(position):
        d = drop(position, col)
        emoji, name = title(d)
        out.append({"code": str(col), "notation": str(col), "emoji": emoji, "title": name, "words": said(d)})
    return out
