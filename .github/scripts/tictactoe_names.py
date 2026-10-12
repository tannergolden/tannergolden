# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named for where its mark goes: an emoji, a title and its plain words, none of them a verdict.

  from tictactoe_names import listing

A title says what the move is and never what it does to the game: the cell
the mark takes (the centre, a corner or an edge) and where the marks around it
stand, in a few plain words, a call to the side to move:

- "by" names the marks touching the cell, by a side or at a corner: "Take the
  Corner by Their Edge!" (their marks touching it are one edge), "Mark the Edge
  by Your Corner and Their Centre!", "by Their Centre Alone" (and none of
  yours), "by Two of Theirs", "by No Mark", and for a few cells the mark
  beside the one that touches it, "by Their Edge Beside Your Corner";
- "Across From" the mark facing the cell over the centre: "Take the Corner
  Across From Theirs!";
- "Along From" the corners on either side of a corner, a cell apart along the
  edge of the board: "Take a Corner Along From Yours!";
- "Away From" the marks that do none of these: "Take an Edge Away From Their
  Corner!";
- the mover's own count: "Lay Your Third Mark in the Corner", "Take Your
  Second Corner".

A title never names a row, a column or a diagonal and what it holds, never a
threat, a block or a win, and nothing that needs a move ahead: a corner that
wins and a corner that does nothing read alike, each named for its place among
the marks. The emoji names the cell only (🔳 the centre, 📐 a corner, 📏 an
edge), the notation is the mark and the cell (`Xb2`), and the words say it
plainly: "X takes the upper left corner", with ", the last cell" on the ninth.

A move is read from the mover's side, the mark that moved first written X, and
taken up to the board's eight turns and mirrors: 2,096 moves, making the 764
positions the game reaches once a mark goes down. tictactoe_names_table.py
builds each move's title into tictactoe_names.json with the facts it claims.
On every board the titles differ and tell the cells apart: a title says "the
corner" when it is true of that cell alone, and two cells that are mirror
images of each other share one title and add their place after a comma ("Take
a Corner Along From Theirs, Upper Left!"). The game and the move number change
nothing. Stdlib only, with tictactoe_rules.py beside it.
"""
from __future__ import annotations

import collections
import functools
import json
from pathlib import Path

from tictactoe_rules import CENTRE, CORNERS, READING, O, Position, legal, make, other

TABLE = Path(__file__).resolve().with_name("tictactoe_names.json")
# Where a cell is, for the two moves on one board that are mirror images of each other.
PLACES = {"a3": "Upper Left", "b3": "Top", "c3": "Upper Right", "a2": "Left", "c2": "Right", "a1": "Lower Left",
          "b1": "Bottom", "c1": "Lower Right"}
# What each cell is called in a move's words: the centre, a corner, or an edge.
CELL_WORDS = {"b2": "the centre", "a3": "the upper left corner", "c3": "the upper right corner",
              "a1": "the lower left corner", "c1": "the lower right corner", "b3": "the top edge",
              "b1": "the bottom edge", "a2": "the left edge", "c2": "the right edge"}
SIGNS = {cell: "🔳" if cell == CENTRE else "📐" if cell in CORNERS else "📏" for cell in READING}  # the cell, no more
SWAP = str.maketrans("XOxo", "OXox")


def forms(marks: str) -> list[str]:
    """The nine marks, as the board is read (a3 b3 c3 a2 b2 c2 a1 b1 c1), under each of the board's eight turns and
    mirrors."""
    out = []
    for _ in range(4):
        marks = "".join(marks[(2 - c) * 3 + r] for r in range(3) for c in range(3))  # a quarter turn
        out += [marks, "".join(marks[r * 3 + 2 - c] for r in range(3) for c in range(3))]  # and its mirror
    return out


def canonical(marks: str) -> str:
    """One form for all eight: the greatest."""
    return max(forms(marks))


def made(position: Position, cell: str) -> str:
    """The table's key for a move: the marks after it, top row first, the new mark in lower case, read from the
    mover's side (the mark that moved first written X) and taken up to the board's turns and mirrors."""
    mover = position.turn
    after = make(position, cell)
    marks = "".join(after.at(c).lower() if c == cell else after.at(c) or "." for c in READING)
    first = mover if marks.upper().count(mover) > marks.upper().count(other(mover)) else other(mover)
    marks = canonical(marks.translate(SWAP) if first == O else marks)
    return "/".join(marks[r:r + 3] for r in (0, 3, 6))


@functools.cache
def names() -> dict[str, dict]:
    """The table: each move up to the board's turns and mirrors, with its title and the facts the title claims."""
    return json.loads(TABLE.read_text(encoding="utf-8"))


def words(position: Position, cell: str) -> str:
    """The move in plain words: `X takes the upper left corner`, `O takes the centre`, and on the ninth mark
    `X takes the lower right corner, the last cell`."""
    text = f"{position.turn} takes {CELL_WORDS[cell]}"
    return f"{text}, the last cell" if len(legal(position)) == 1 else text


def notation(position: Position, cell: str) -> str:
    """The move as the board lists it: its mark and cell, `Xb2`, and nothing more."""
    return f"{position.turn}{cell}"


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open cell as the board is read, each with its notation, emoji, title and words. The game and the move
    number change nothing: a move is named for where its mark goes."""
    return [dict(entry) for entry in _listing(position)]


@functools.lru_cache(maxsize=256)
def _listing(position: Position) -> tuple[dict, ...]:
    cells = legal(position)
    keys = {cell: made(position, cell) for cell in cells}
    twins = collections.Counter(keys.values())
    out = []
    for cell in cells:
        title = names()[keys[cell]]["title"]
        if twins[keys[cell]] > 1:
            title = f"{title[:-1]}, {PLACES[cell]}!"
        out.append({"code": cell, "notation": notation(position, cell), "emoji": SIGNS[cell], "title": title,
                    "words": words(position, cell)})
    return tuple(out)

