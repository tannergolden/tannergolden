# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac-Toe on the profile, the first tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py tictactoe .github/tictactoe

What the shared engine asks of the game: how a move is written in an issue's
title (its cell, `b2`), on the sheet and in a reply (`Xb2`, `Xb2+` for a
threat, `Xb2#` for the win), how a game ends, what its board sets out for
the page beside the fields every game shares, and what it calls things.

Each player keeps one mark in every game: the house plays X and GitHub O.
The Arbiter opens every game, for a side drawn at random, with a random
cell, so that side's mark goes down first: O moves first in a game the
Arbiter opened for GitHub. The board sets out the marks as three rows, top
first (`O../XX./O.X`), the side the Arbiter opened for (`opens`), the cells
each side could win on next (`threats`), who wins from here with perfect
play (`outlook`), a block the side to move must make (`alert`), and once the
game is won, the three cells it was won on (`line`). The rules are
tictactoe_rules.py's and the names tictactoe_names.py's. Stdlib only.
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
    return R.notation(position, code)


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the same as the sheet, `Xb2+`."""
    return R.notation(position, code)


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


def menace(position: R.Position) -> tuple[str, list[str]]:
    """The mark that just moved, and the cells it could win on next: what the side to move faces."""
    mark = R.other(position.turn)
    return mark, ([] if R.ending(position) else R.threats(position, mark))


def pressure(position: R.Position) -> tuple[str, str]:
    """What the side to move faces, as a reply's last line says it to the house, and of GitHub."""
    mark, cells = menace(position)
    said = " and ".join(cells)
    return (f"and {mark} threatens {said}", f"with {mark} threatening {said}") if cells else ("", "")


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move, as chess's calls a check."""
    _, cells = menace(position)
    return "" if not cells else " Block it!" if len(cells) == 1 else " Two threats!"


def calls(position: R.Position) -> list[str]:
    """What the banner tells the side to move, longest first."""
    _, cells = menace(position)
    return [] if not cells else [f"Block {cells[0]}! ", "Block it! "] if len(cells) == 1 else ["Two threats! "]


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the marks and the side the Arbiter opened for, and while the game goes on, each
    side's threats, who wins with perfect play from here, and a block the side to move must make."""
    position = positions[-1]
    out: dict = {"board": position.board, "opens": game["opens"]}
    if over:
        return out
    out["threats"] = {side: R.threats(position, mark) for side, mark in WORDS.items()}
    best = R.outlook(position)
    out["outlook"] = SIDE.get(best, "draw")
    if out["threats"][SIDE[R.other(position.turn)]]:
        out["alert"] = "must block"
    return out


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
