# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every square named as tic-tac-toe players name it: an emoji, a name and its plain words, none of them a verdict.

  from tictac_names import listing, ghost_listing

A name is what a tic-tac-toe player calls the square inside its small board:
the Centre, a Corner or an Edge, the three moves there are in the game. It
never says which board the square is on or what the mark does to the game, so
a mark that wins and one that changes nothing read alike, and the notation
and the words beside it say exactly where it goes. Under the Ghost Rule a
ghost's square is named the same way, as a Centre Ghost, a Corner Ghost or
an Edge Ghost.

The emoji names the kind of square (🔳 a board's centre, 📐 a corner, 📏 an
edge, and 👻 a ghost's), the notation is the mark and the square (`Xe5`), or
the square alone for a ghost, and the words say it plainly: "X takes the upper
right corner of the centre board", "A ghost locks the centre of the centre
board". The game and the move number change nothing. Stdlib only, with
tictac_rules.py beside it.
"""
from __future__ import annotations

import functools

from tictac_rules import PLACE, READING, SQUARE, Position, board_of, legal, spot_of

GHOST = "👻"
SIGNS = {"Centre": "🔳", "Corner": "📐", "Edge": "📏"}


def kind(cell: str) -> str:
    """The square's kind inside its board, as the game names it: `Centre`, `Corner` or `Edge`."""
    x, y = spot_of(cell)
    return "Centre" if (x, y) == (1, 1) else "Corner" if x != 1 and y != 1 else "Edge"


def sign(cell: str) -> str:
    """A square's emoji: its board's centre, a corner or an edge."""
    return SIGNS[kind(cell)]


def place(cell: str) -> tuple[str, str]:
    """Where a square is: its square inside its board, and its board, in words."""
    return SQUARE[spot_of(cell)], PLACE[board_of(cell)]


def words(position: Position, cell: str) -> str:
    """The move in plain words: `X takes the upper right corner of the centre board`."""
    square, board = place(cell)
    return f"{position.turn} takes the {square} of the {board} board"


def ghost_words(cell: str) -> str:
    square, board = place(cell)
    return f"A ghost locks the {square} of the {board} board"


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every square the side to move may take, as the board is read, each with its notation, emoji, name and words.
    The game and the move number change nothing: a move is named for the kind of square its mark goes on."""
    return [dict(entry) for entry in _listing(position)]


@functools.lru_cache(maxsize=256)
def _listing(position: Position) -> tuple[dict, ...]:
    return tuple({"code": cell, "notation": f"{position.turn}{cell}", "emoji": sign(cell), "title": kind(cell),
                  "words": words(position, cell)} for cell in legal(position))


def ghost_listing(ghosts: tuple[str, ...]) -> list[dict]:
    """Every square a ghost could lock, as the board is read: all but a ghost's."""
    return [{"code": cell, "notation": cell, "emoji": GHOST, "title": f"{kind(cell)} Ghost",
             "words": ghost_words(cell)} for cell in READING if cell not in ghosts]
