# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named for the position it makes: an emoji, a title no other move has, and its plain words.

  from tictactoe_names import listing

Tic-Tac-Toe is small enough to name whole. Taken up to the board's eight
turns and mirrors, and read from the mover's side, a move can make 764
positions, and each has its own title: an order in the game's own words,
judged by perfect play. "Seize the Centre!" opens, "Save the Draw From a
Corner!" answers it, "Fork the Diagonal and the Side!" wins by force, and a
move that loses by force is named for what it gives away, under a warning sign:
"Hand Them the Diagonal!", "Box In Their Corner and Lose!".

Reading from the mover's side means the mark that moved first is written X: a
game O opened reads as one X opened with the marks swapped, so either side's
moves take the same 764 titles. The titles live in tictactoe_names.json with
the facts each one claims; tictactoe_names_table.py builds that table from the
rules, and a test holds the two to each other.

A title is the same wherever its position comes up, so two moves on one board
can share one only when they make the same position, as mirror images do (any
corner of the empty board). Those take the cell's place after a comma: "Claim a
Corner, Upper Left!". The emoji says what the move itself does: 🏆 wins, ⚠️
loses by force, 🛡️ blocks a threat (unless it wins or forks), ⚡ forks, 🎯
threatens, 🤝 draws on the last cell, and a quiet move shows where its mark
goes: ⭐ the centre, 📐 a corner, 📏 an edge. The words say it plainly: "X
takes the centre", "O blocks on c2, threatening a3", "X takes a3, three in a row
from a3 to c1". Stdlib only, with tictactoe_rules.py beside it.
"""
from __future__ import annotations

import collections
import functools
import json
from pathlib import Path

from tictactoe_rules import CENTRE, CORNERS, READING, O, Position, X, ending, legal, make, notation, other, threats

TABLE = Path(__file__).resolve().with_name("tictactoe_names.json")
# Where a cell is, for the two moves on one board that make mirror images of one position.
PLACES = {"a3": "Upper Left", "b3": "Top", "c3": "Upper Right", "a2": "Left", "c2": "Right", "a1": "Lower Left",
          "b1": "Bottom", "c1": "Lower Right"}
# What each cell is called in a move's words: the centre, a corner, or the middle of an edge.
CELL_WORDS = {"b2": "the centre", "a1": "the lower left corner", "c1": "the lower right corner",
              "a3": "the upper left corner", "c3": "the upper right corner", "b1": "the foot of the board",
              "b3": "the head of the board", "a2": "the left edge", "c2": "the right edge"}
SWAP = str.maketrans({X: O, O: X})
BLOCK = "🛡️"  # a move that blocks a threat shows as the block it is, unless it wins or forks: those outrank it
OUTRANK = {"🏆", "⚡"}
QUIET = {"⭐", "📐", "📏", "🤝"}  # a quiet move shows where its own mark goes, but on the last cell, the draw
SIGNS = {cell: "⭐" if cell == CENTRE else "📐" if cell in CORNERS else "📏" for cell in READING}


def forms(marks: str) -> list[str]:
    """The nine marks, as the board is read (a3 b3 c3 a2 b2 c2 a1 b1 c1), under each of the board's eight turns and
    mirrors."""
    out = []
    for _ in range(4):
        marks = "".join(marks[(2 - c) * 3 + r] for r in range(3) for c in range(3))  # a quarter turn
        out += [marks, "".join(marks[r * 3 + 2 - c] for r in range(3) for c in range(3))]  # and its mirror
    return out


def canonical(marks: str) -> str:
    """One form for all eight: the greatest, which sets the marks toward the upper left."""
    return max(forms(marks))


def made(position: Position, cell: str) -> str:
    """The table's key for the position a move makes: its marks, top row first, read from the mover's side, with the
    mark that moved first written X, and taken up to the board's turns and mirrors."""
    mover = position.turn
    after = make(position, cell)
    marks = "".join(after.at(c) or "." for c in READING)
    if (mover if marks.count(mover) > marks.count(other(mover)) else other(mover)) == O:
        marks = marks.translate(SWAP)
    marks = canonical(marks)
    return "/".join(marks[r:r + 3] for r in (0, 3, 6))


@functools.cache
def names() -> dict[str, dict]:
    """The table: each position a move can make, with its title, emoji, judgement and the facts its title claims."""
    return json.loads(TABLE.read_text(encoding="utf-8"))


def words(position: Position, cell: str) -> str:
    """The move in plain words: `X takes the centre`, `O blocks on c2, threatening a3`, `X takes a3, three in a row
    from a3 to c1`, `X takes c1, the last cell, for a draw`."""
    mark = position.turn
    after = make(position, cell)
    end = ending(after)
    if end and end.winner:
        return f"{mark} takes {cell}, three in a row from {end.line[0]} to {end.line[-1]}"
    blocks = cell in threats(position, other(mark))
    text = f"{mark} blocks on {cell}" if blocks else f"{mark} takes {CELL_WORDS[cell]}"
    if end:
        return f"{text}, the last cell, for a draw"
    makes, leaves = threats(after, mark), threats(after, other(mark))
    if makes:
        text += f", threatening {' and '.join(makes)}"
    if leaves:
        text += f", leaving {' and '.join(leaves)} to {other(mark)}"
    return text


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open cell as the board is read, each with its notation, emoji, title and words. The game and the move
    number change nothing: a move is named for the position it makes."""
    return [dict(entry) for entry in _listing(position)]


@functools.lru_cache(maxsize=256)
def _listing(position: Position) -> tuple[dict, ...]:
    cells = legal(position)
    keys = {cell: made(position, cell) for cell in cells}
    twins = collections.Counter(keys.values())
    out = []
    blocks = threats(position, other(position.turn))
    for cell in cells:
        entry = names()[keys[cell]]
        title = entry["title"] if twins[keys[cell]] == 1 else f"{entry['title'][:-1]}, {PLACES[cell]}!"
        sign = entry["emoji"]
        if cell in blocks and sign not in OUTRANK:
            sign = BLOCK
        elif sign in QUIET and not ending(make(position, cell)):
            sign = SIGNS[cell]
        out.append({"code": cell, "notation": notation(position, cell), "emoji": sign, "title": title,
                    "words": words(position, cell)})
    return tuple(out)
