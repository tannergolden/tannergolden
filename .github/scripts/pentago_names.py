# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every empty hole named for where its marble goes: an emoji, a title and its plain words, none of them a verdict.

  from pentago_names import listing, ghost_listing, entry

A Pentago move is two choices, a hole and then a quarter to turn and which
way, so the board lists every empty hole once, with its eight turns after it,
each a code of its own (`e4-ur-cw`) that its link carries. A title says what
the hole is and never what the move would do: the hole inside its quarter and
the quarter it stands in, "Take the Centre of the Upper Left Quarter!", so a
move that wins and one that changes nothing read alike. Each of the 36 holes
has a title of its own. Under the Ghost Rule a ghost's hole is one choice:
"Ghost the Centre of the Upper Left Quarter!".

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


def titled(verb: str, cell: str) -> str:
    """A title in the house's capitals: every word capitalized but `the` and `of`."""
    words = f"{verb} the {SPOT[spot_of(cell)]} of the {QNAME[quarter_of(cell)]} quarter".split()
    return " ".join(w if w in ("the", "of") else w[0].upper() + w[1:] for w in words) + "!"


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every empty hole the side to move may set its marble in, as the board is read, each with its notation, emoji,
    title and words, and its eight turns, each with its own code. The game and the move number change nothing."""
    if ending(position):
        return []
    colour = position.turn
    return [{"code": cell, "notation": cell, "emoji": SIGNS[colour], "title": titled("take", cell),
             "words": f"A {COLOUR[colour]} marble on {cell}, then a quarter turns",
             "turns": [(q, w, f"{cell}-{q}-{w}") for q, w in TURNS]} for cell in empty(position)]


def entry(position: Position, code: str) -> dict:
    """One move as a reply and the board's last move name it: its emoji, the title of its hole, and its words, the
    turn it made said in full."""
    cell, quarter, way = parse(code)
    colour = position.turn
    words = f"A {COLOUR[colour]} marble on {cell}"
    if not won_unturned(position, code):
        words += f", then the {QNAME[quarter]} quarter turns {WAYS[way]}"
    return {"code": code, "notation": code, "emoji": SIGNS[colour], "title": titled("take", cell), "words": words}


def ghost_words(cell: str) -> str:
    return f"A ghost on {cell}, the {SPOT[spot_of(cell)]} of the {QNAME[quarter_of(cell)]} quarter"


def ghost_listing(ghosts: tuple[str, ...]) -> list[dict]:
    """Every hole a ghost could stand in, as the board is read: all but a ghost's."""
    return [{"code": cell, "notation": cell, "emoji": GHOST, "title": titled("ghost", cell), "words": ghost_words(cell)}
            for cell in READING if cell not in ghosts]
