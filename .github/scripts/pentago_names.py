# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every empty hole named as Pentago players name it: an emoji, a name and its plain words, none of them a verdict.

  from pentago_names import listing, ghost_listing, entry

A Pentago move is two choices, a hole for the marble and then a quarter to
twist a notch and which way (a game block, as the rules call a quarter), so
the board lists every empty hole once, with its eight turns after it, each a
code of its own (`e4-ur-cw`) that its link carries. A name is what a player
calls the hole inside its quarter: the Centre, a Corner or an Edge. It never
says which quarter the hole is in or what the move would do, so a move that
wins and one that changes nothing read alike, and the notation and the words
beside it say exactly where it goes.
Under the Ghost Rule a ghost's hole is one choice, named the same way: a
Centre Ghost, a Corner Ghost or an Edge Ghost.

The emoji is the mover's marble (⚪ the house's White, ⚫ GitHub's Black, and
👻 a ghost), and the words say it plainly: "A white marble on e4, then a
quarter turns" on the list, and once the move is made, "A white marble on e4,
then the upper right quarter turns clockwise", or "A white marble on e4" when
the marble made five before any turn. The game and the move number change
nothing. Stdlib only, with pentago_rules.py beside it.
"""
from __future__ import annotations

from pentago_rules import (COLOUR, QNAME, READING, SPOT, TURNS, WAYS, B, Position, empty, ending, parse, quarter_of,
                           spot_of, won_unturned)

SIGNS = {"W": "⚪", B: "⚫"}
GHOST = "👻"


def kind(cell: str) -> str:
    """The hole's kind inside its block, as the game names it: `Centre`, `Corner` or `Edge`."""
    x, y = spot_of(cell)
    return "Centre" if (x, y) == (1, 1) else "Corner" if x != 1 and y != 1 else "Edge"


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every empty hole the side to move may set its marble in, as the board is read, each with its notation, emoji,
    name and words, and its eight turns, each with its own code. The game and the move number change nothing."""
    if ending(position):
        return []
    colour = position.turn
    return [{"code": cell, "notation": cell, "emoji": SIGNS[colour], "title": kind(cell),
             "words": f"A {COLOUR[colour]} marble on {cell}, then a quarter turns",
             "turns": [(q, w, f"{cell}-{q}-{w}") for q, w in TURNS]} for cell in empty(position)]


def entry(position: Position, code: str) -> dict:
    """One move as a reply and the board's last move name it: its emoji, the name of its hole, and its words, the
    turn it made said in full."""
    cell, quarter, way = parse(code)
    colour = position.turn
    words = f"A {COLOUR[colour]} marble on {cell}"
    if not won_unturned(position, code):
        words += f", then the {QNAME[quarter]} quarter turns {WAYS[way]}"
    return {"code": code, "notation": code, "emoji": SIGNS[colour], "title": kind(cell), "words": words}


def ghost_words(cell: str) -> str:
    return f"A ghost on {cell}, the {SPOT[spot_of(cell)]} of the {QNAME[quarter_of(cell)]} quarter"


def ghost_listing(ghosts: tuple[str, ...]) -> list[dict]:
    """Every hole a ghost could stand in, as the board is read: all but a ghost's."""
    return [{"code": cell, "notation": cell, "emoji": GHOST, "title": f"{kind(cell)} Ghost",
             "words": ghost_words(cell)} for cell in READING if cell not in ghosts]
