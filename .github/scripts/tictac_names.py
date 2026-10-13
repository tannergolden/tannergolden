# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every square named for where its mark goes: an emoji, a title and its plain words, none of them a verdict.

  from tictac_names import listing, ghost_listing

A title says what the move is and never what it does to the game: the square
the mark takes inside its board and the board it stands in, "Take the Upper
Right Corner of the Centre Board!", so a mark that wins the game and one that
changes nothing read alike. Each of the 81 squares has a title of its own, so
every board tells its squares apart. Under the Ghost Rule a ghost's square is
named the same way: "Lock the Centre of the Centre Board!".

The emoji names the square only (🔳 a board's centre, 📐 a corner, 📏 an
edge, and 👻 a ghost's), the notation is the mark and the square (`Xe5`), or
the square alone for a ghost, and the words say it plainly: "X takes the upper
right corner of the centre board", "A ghost locks the centre of the centre
board". The game and the move number change nothing. Stdlib only, with
tictac_rules.py beside it.
"""
from __future__ import annotations

import functools

from tictac_rules import CELLS, PLACE, READING, SQUARE, Position, board_of, legal, spot_of

GHOST = "👻"


def sign(cell: str) -> str:
    """A square's emoji: its board's centre, a corner or an edge."""
    spot = spot_of(cell)
    return "🔳" if spot == (1, 1) else "📐" if spot[0] != 1 and spot[1] != 1 else "📏"


def place(cell: str) -> tuple[str, str]:
    """Where a square is: its square inside its board, and its board, in words."""
    return SQUARE[spot_of(cell)], PLACE[board_of(cell)]


def titled(verb: str, cell: str) -> str:
    """A title in the house's capitals: every word capitalized but `the` and `of`."""
    square, board = place(cell)
    words = f"{verb} the {square} of the {board} board".split()
    return " ".join(w if w in ("the", "of") else w[0].upper() + w[1:] for w in words) + "!"


def words(position: Position, cell: str) -> str:
    """The move in plain words: `X takes the upper right corner of the centre board`."""
    square, board = place(cell)
    return f"{position.turn} takes the {square} of the {board} board"


def ghost_words(cell: str) -> str:
    square, board = place(cell)
    return f"A ghost locks the {square} of the {board} board"


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every square the side to move may take, as the board is read, each with its notation, emoji, title and words.
    The game and the move number change nothing: a move is named for where its mark goes."""
    return [dict(entry) for entry in _listing(position)]


@functools.lru_cache(maxsize=256)
def _listing(position: Position) -> tuple[dict, ...]:
    return tuple({"code": cell, "notation": f"{position.turn}{cell}", "emoji": sign(cell),
                  "title": titled("take", cell), "words": words(position, cell)} for cell in legal(position))


def ghost_listing(ghosts: tuple[str, ...]) -> list[dict]:
    """Every square a ghost could lock, as the board is read: all but a ghost's."""
    return [{"code": cell, "notation": cell, "emoji": GHOST, "title": titled("lock", cell), "words": ghost_words(cell)}
            for cell in READING if cell not in ghosts]

