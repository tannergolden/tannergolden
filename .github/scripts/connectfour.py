# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Connect Four on the profile, the second tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py connectfour .github/connectfour

What the shared engine asks of the game: how a move is written in an issue's
title and on the sheet (its column, `4`, and `4#` for the drop that wins)
and in a reply (the disc's sign before it, `⚪4`, `⚫4#`), how a game ends,
what its board sets out for the page beside the fields every game shares,
and what it calls things.

Each player keeps one colour in every game: the house drops the white discs
(the board's `L`) and GitHub the black (`D`). The Arbiter opens every game,
for a side drawn at random, with a random disc, so that side's colour drops
first: a game it opened for the house starts with a white disc. The board
sets out the frame as six rows, top first, the side the Arbiter opened for
(`opens`), and once the game is won, the four cells it was won on (`line`).
Nothing on the page helps a player choose: no column a side could win down
next and no block called out, in the board or a reply. The rules are
connectfour_rules.py's and the names connectfour_names.py's. Stdlib only.
"""
from __future__ import annotations

import re

import connectfour_rules as R
from connectfour_names import listing
from page import GITHUB, HOUSE

KEY, TITLE = "connectfour", "Connect Four"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
ARBITER_OPENS, OPENER = True, None  # the Arbiter opens every game, for the side it draws
CODE = re.compile(r"[1-7]")  # a move as an issue's title carries it
WORDS = {HOUSE: "White", GITHUB: "Black"}  # what each side is called, in every game
COLOURS = {HOUSE: R.LIGHT, GITHUB: R.DARK}  # the discs each side drops: the house the light ones, GitHub the dark
SIDE = {colour: side for side, colour in COLOURS.items()}
WORD = {colour: WORDS[side] for side, colour in COLOURS.items()}
SIGN = {"White": "⚪", "Black": "⚫"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's disc
RESULTS = {HOUSE: "1-0", GITHUB: "0-1", None: "1/2-1/2"}  # White's score first, as chess writes it
OPENS_NOTE = ("@{owner} always drops the white discs and GitHub the black, and the Arbiter opens every game for a"
              " side drawn at random, with a random first disc.")
RULE = "Four in a row wins, across, up or on a diagonal, and a full frame without one is a draw."
DRAWN = {"a full frame": "on a full frame"}

__all__ = ["listing"]


def start(first: str) -> R.Position:
    """The empty frame, the `first` side's colour to drop first."""
    return R.opening(COLOURS[first])


def legal(position: R.Position) -> list[str]:
    return [str(col) for col in R.legal(position)]


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, int(code))


def notation(position: R.Position, code: str) -> str:
    """The move as the score sheet writes it: `4`, and `4#` for the win."""
    return R.notation(position, int(code))


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the disc's sign, then the column, `⚪4`."""
    return SIGN[WORD[position.turn]] + notation(position, code)


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, int(code))


def final(position: R.Position) -> str:
    return position.board


def ending(positions: list[R.Position], codes: list[str]) -> tuple[str | None, str, list | None] | None:
    """How the game ends, if it does: the side that won, how, and the four it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (SIDE[end.winner] if end.winner else None), end.reason, [list(cell) for cell in end.line] or None


def pressure(position: R.Position) -> tuple[str, str]:
    """What a reply's last line says the side to move faces: nothing, since no threat is called out."""
    return "", ""


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move: nothing, since no block is called for."""
    return ""


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the frame and the side the Arbiter opened for."""
    return {"board": positions[-1].board, "opens": game["opens"]}


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: nothing, in Connect Four."""
    return {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return "four in a row!"
