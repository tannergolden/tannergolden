# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac-Toe on the profile, the first tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py tictactoe .github/tictactoe

What the shared engine asks of the game: how a move is written in an issue's
title (its cell, `b2`), on the sheet and in a reply (`Xb2`, `Xb2+` for a
threat, `Xb2#` for the win), how a game ends, what its board sets out for
the page beside the fields every game shares, and what it calls things.

The Arbiter opens every game, for a side drawn at random: that side plays X,
which always moves first, and the other side O, so the house's mark changes
from game to game. The board sets out the marks as three rows, top first
(`O../XX./O.X`), the side that plays X (`x`), the cells each side could win
on next (`threats`), who wins from here with perfect play (`outlook`), a
block the side to move must make (`alert`), and once the game is won, the
three cells it was won on (`line`). The rules are tictactoe_rules.py's and
the names tictactoe_names.py's. Stdlib only.
"""
from __future__ import annotations

import re

import tictactoe_rules as R
from page import GITHUB, HOUSE, other
from tictactoe_names import listing

KEY, TITLE = "tictactoe", "Tic-Tac-Toe"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
ARBITER_OPENS = True
CODE = re.compile(r"[a-c][1-3]")  # a move as an issue's title carries it
FIRST, SECOND = R.X, R.O  # what each side is called: the side that moves first plays X
SIGN = {R.X: "❌", R.O: "⭕"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's mark
WHY = ("The Arbiter opens every game for a side drawn at random, since X moves first and wins far more often when"
       " anyone slips: of the 255,168 possible games, X wins 131,184, O wins 77,904 and 46,080 are drawn.")
RULE = "Three in a row wins, and a full board without one is a draw."
DRAWN = {"a full board": "on a full board"}

__all__ = ["listing"]


def start() -> R.Position:
    return R.START


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


def ending(positions: list[R.Position], codes: list[str]) -> tuple[bool | None, str, list | None] | None:
    """How the game ends, if it does: whether X, the opener, won, how, and the line it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (None if end.winner is None else end.winner == R.X), end.reason, list(end.line) or None


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
    """The board's own fields: the marks, the side that plays X, and while the game goes on, each side's threats,
    who wins with perfect play from here, and a block the side to move must make."""
    position, opens = positions[-1], game.get("opens", HOUSE)
    out: dict = {"board": position.board, "x": opens}
    if over:
        return out
    marks = {opens: R.X, other(opens): R.O}
    out["threats"] = {side: R.threats(position, marks[side]) for side in (HOUSE, GITHUB)}
    best = R.outlook(position)
    out["outlook"] = "draw" if best == "draw" else opens if best == R.X else other(opens)
    if out["threats"][opens if position.turn == R.O else other(opens)]:
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
    if end.first is None:
        return "A full board, and no three in a row"
    a, b, c = end.line
    return f"{R.X if end.first else R.O} struck {a}, {b} and {c}"


def opening(code: str) -> list[str]:
    """The Arbiter's opening as a fresh board's banner names it, longest first."""
    return [f"X on {code}"]
