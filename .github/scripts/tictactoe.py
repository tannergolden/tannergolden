# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac-Toe on the profile, the first tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py tictactoe .github/tictactoe

What the shared engine asks of the game: how a move is written in an issue's
title (its cell, `b2`), on the sheet and in a reply (`Xb2`, and `Xb2#` for
the move that wins), how a game ends, what its board sets out for the page
beside the fields every game shares, and what it calls things.

Each player keeps one mark in every game: the house plays X and GitHub O.
The Arbiter opens every game, for a side drawn at random, with a random
cell, so that side's mark goes down first: O moves first in a game the
Arbiter opened for GitHub. The board sets out the marks as three rows, top
first (`O../XX./O.X`), the side the Arbiter opened for (`opens`), and once
the game is won, the three cells it was won on (`line`). Nothing on the page
helps a player choose: no cell a side could win on next, no word of what
perfect play says, and no block called out, in the board, the banner or a
reply. The rules are tictactoe_rules.py's and the names tictactoe_names.py's.
Stdlib only.
"""
from __future__ import annotations

import re

import tictactoe_rules as R
from page import GITHUB, HOUSE
from tictactoe_names import listing

KEY, TITLE = "tictactoe", "Tic-Tac-Toe"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
ARBITER_OPENS, OPENER = True, None  # the Arbiter opens every game, for the side it draws
CODE = re.compile(r"[a-c][1-3]")  # a move as an issue's title carries it
WORDS = {HOUSE: R.X, GITHUB: R.O}  # what each side is called, in every game: the house plays X, GitHub O
SIDE = {mark: side for side, mark in WORDS.items()}
SIGN = {R.X: "❌", R.O: "⭕"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's mark
RESULTS = {HOUSE: "1-0", GITHUB: "0-1", None: "1/2-1/2"}  # X's score first, as chess writes White's
OPENS_NOTE = ("@{owner} always plays X and GitHub O, and the Arbiter opens every game for a side drawn at random,"
              " with a random first move.")
RULE = "Three in a row wins, and a full board without one is a draw."
DRAWN = {"a full board": "on a full board"}

__all__ = ["listing"]


def start(first: str) -> R.Position:
    """The empty board, the `first` side's mark to go down first."""
    return R.opening(WORDS[first])


def legal(position: R.Position) -> list[str]:
    return R.legal(position)


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, code)


def notation(position: R.Position, code: str) -> str:
    """The move as the score sheet writes it: `Xb2`, and `Xb2#` for the win."""
    return R.notation(position, code)


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the same as the sheet, `Xb2`."""
    return notation(position, code)


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, code)


def final(position: R.Position) -> str:
    return position.board


def ending(positions: list[R.Position], codes: list[str]) -> tuple[str | None, str, list | None] | None:
    """How the game ends, if it does: the side that won, how, and the line it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (SIDE[end.winner] if end.winner else None), end.reason, list(end.line) or None


def pressure(position: R.Position) -> tuple[str, str]:
    """What a reply's last line says the side to move faces: nothing, since no threat is called out."""
    return "", ""


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move: nothing, since no block is called for."""
    return ""


def calls(position: R.Position) -> list[str]:
    """What the banner tells the side to move: nothing beyond whose turn it is."""
    return []


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the marks and the side the Arbiter opened for."""
    return {"board": positions[-1].board, "opens": game["opens"]}


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: nothing, in Tic-Tac-Toe."""
    return {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return "three in a row!"


def summary(end, positions: list[R.Position]) -> str:
    """How the game ended, as the final board's banner says it."""
    if end.winner is None:
        return "A full board, and no three in a row"
    a, b, c = end.line
    return f"{WORDS[end.winner]} struck {a}, {b} and {c}"


def opening(code: str, side: str) -> list[str]:
    """The Arbiter's opening for `side` as a fresh board's banner names it, longest first."""
    return [f"{WORDS[side]} on {code}"]
