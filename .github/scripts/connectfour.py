# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Connect Four on the profile, the second tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py connectfour .github/connectfour

What the shared engine asks of the game: how a move is written in an issue's
title and on the sheet (its column, `4`, `4+` for a threat, `4#` for the
win) and in a reply (the disc's sign before it, `⚫4`, `⚪4+`), how a game
ends, what its board sets out for the page beside the fields every game
shares, and what it calls things.

The Arbiter opens every game, for a side drawn at random, since whoever drops
the first disc can force a win: that side drops the dark discs, which always
go first, and the other side the light ones, so the house's colour changes
from game to game. The board sets out the frame as six rows, top first, the
side that opened (`opens`) and the side with the light discs (`light`), the
columns each side could win down next (`threats`), a block the side to move
must make (`alert`), and once the game is won, the four cells it was won on
(`line`). The rules are connectfour_rules.py's and the names
connectfour_names.py's. Stdlib only.
"""
from __future__ import annotations

import re

import connectfour_rules as R
from connectfour_names import columns, listing
from page import GITHUB, HOUSE, other

KEY, TITLE = "connectfour", "Connect Four"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
ARBITER_OPENS = True
CODE = re.compile(r"[1-7]")  # a move as an issue's title carries it
FIRST, SECOND = "Dark", "Light"  # what each side is called: the side that moves first drops the dark discs
WORD = {R.DARK: FIRST, R.LIGHT: SECOND}
SIGN = {FIRST: "⚫", SECOND: "⚪"}
LEAD = {FIRST: "🪂", SECOND: "🪂"}  # what a reply and a commit lead with: the airborne's chute
WHY = ("The Arbiter opens every game for a side drawn at random, since whoever drops the first disc can force a win"
       " by opening in the centre column (James D. Allen and Victor Allis, independently, in 1988).")
RULE = "Four in a row wins, across, up or on a diagonal, and a full frame without one is a draw."
DRAWN = {"a full frame": "on a full frame"}

__all__ = ["listing"]


def start() -> R.Position:
    return R.START


def legal(position: R.Position) -> list[str]:
    return [str(col) for col in R.legal(position)]


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, int(code))


def notation(position: R.Position, code: str) -> str:
    return R.notation(position, int(code))


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the disc's sign, then the column, `⚫4+`."""
    return SIGN[WORD[position.turn]] + R.notation(position, int(code))


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, int(code))


def final(position: R.Position) -> str:
    return position.board


def ending(positions: list[R.Position], codes: list[str]) -> tuple[bool | None, str, list | None] | None:
    """How the game ends, if it does: whether Dark, the opener, won, how, and the four it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (None if end.winner is None else end.winner == R.DARK), end.reason, [list(cell) for cell in end.line] or None


def menace(position: R.Position) -> tuple[str, list[int]]:
    """The colour that just moved, and the columns it could win down next: what the side to move faces."""
    colour = R.other(position.turn)
    return WORD[colour], ([] if R.ending(position) else R.threats(position, colour))


def pressure(position: R.Position) -> tuple[str, str]:
    """What the side to move faces, as a reply's last line says it to the house, and of GitHub."""
    name, found = menace(position)
    said = columns(tuple(found)) if found else ""
    return (f"and {name} threatens {said}", f"with {name} threatening {said}") if found else ("", "")


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move, as chess's calls a check."""
    _, found = menace(position)
    return "" if not found else " Block it!" if len(found) == 1 else " Two threats!"


def calls(position: R.Position) -> list[str]:
    """What the banner tells the side to move, longest first."""
    _, found = menace(position)
    return [] if not found else [f"Block column {found[0]}! ", "Block it! "] if len(found) == 1 else ["Two threats! "]


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the frame, the side that opened and the side with the light discs, and while the game
    goes on, each side's threats and a block the side to move must make."""
    position, opens = positions[-1], game.get("opens", HOUSE)
    out: dict = {"board": position.board, "opens": opens, "light": other(opens)}
    if over:
        return out
    colours = {opens: R.DARK, other(opens): R.LIGHT}
    out["threats"] = {side: R.threats(position, colours[side]) for side in (HOUSE, GITHUB)}
    if out["threats"][opens if position.turn == R.LIGHT else other(opens)]:
        out["alert"] = "must block"
    return out


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: nothing, in Connect Four."""
    return {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return "four in a row!"


def summary(end, positions: list[R.Position]) -> str:
    """How the game ended, as the final board's banner says it."""
    if end.first is None:
        return "A full frame, and no four in a row"
    (c0, r0), (c1, r1) = end.line[0], end.line[-1]
    where = f"across row {r0}" if r0 == r1 else f"up column {c0}" if c0 == c1 else "on a diagonal"
    return f"Four {'dark' if end.first else 'light'} discs {where}"


def opening(code: str) -> list[str]:
    """The Arbiter's opening as a fresh board's banner names it, longest first."""
    return [f"a dark disc in column {code}", f"⚫ in column {code}", f"⚫{code}"]
