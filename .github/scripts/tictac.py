# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac on the profile, the first tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py tictac .github/tictac

What the shared engine asks of the game: how a move is written in an issue's
title (its square, `e5`), on the sheet and in a reply (`Xe5`, and `Xe5#` for
the move that wins), how a game ends, what its board sets out for the page
beside the fields every game shares, and what it calls things.

Tic-Tac is Tic-Tac-Toe on nine boards at once, the game also known as
Ultimate Tic-Tac-Toe: where a mark goes in its board sends the other side to
the board in that place, three in a row wins a board, and three boards in a
row wins the game. Each player keeps one mark in every game: the house plays
X and GitHub O. The Ghost Rule opens every game: the Arbiter draws the side
that locks the first square with a ghost, the other side locks the second,
and then the Arbiter draws the side that makes the first mark, anywhere. The
board sets out the marks and ghosts as nine rows, top first, the side drawn
to place the first ghost (`places`), the side drawn to open (`opens`), where
the side to move must play (`alert`), and once the game is won, the three
boards it was won on (`line`). Nothing on the page helps a player choose: no
square a side could win a board on next, no board a side could win the game
on, and no block called out, in the board or a reply. The rules are
tictac_rules.py's and the names tictac_names.py's. Stdlib only.
"""
from __future__ import annotations

import re

import tictac_rules as R
from page import GITHUB, HOUSE
from tictac_names import ghost_listing, listing

KEY, TITLE = "tictac", "Tic-Tac"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
GHOST_RULE, OPENER = True, None  # each side sets a ghost, then the Arbiter draws who opens
CODE = re.compile(r"[a-i][1-9]")  # a move as an issue's title carries it, a ghost's or a mark's: its square
GHOST_CODE = CODE
WORDS = {HOUSE: R.X, GITHUB: R.O}  # what each side is called, in every game: the house plays X, GitHub O
SIDE = {mark: side for side, mark in WORDS.items()}
SIGN = {R.X: "❌", R.O: "⭕"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's mark
RESULTS = {HOUSE: "1-0", GITHUB: "0-1", None: "1/2-1/2"}  # X's score first, as chess writes White's
GHOSTS = ("place", "places", "locks a square", "placed")  # a ghost's verb, said of a side, in full, and done
SPOT = "square"  # what a ghost stands on, as a refusal names it
OPENS_NOTE = ("@{owner} always plays X and GitHub O. Under the Ghost Rule each side first locks a square with a ghost,"
              " and then the Arbiter draws who makes the first mark.")
RULE = ("Where a mark goes in its board sends the other side to the board in that place, three in a row wins a board,"
        " and three boards in a row wins the game; once neither side can win three boards in a row, it is a draw.")
DRAWN = {"no line left": "with no line of three boards left for either side"}

__all__ = ["ghost_listing", "listing"]


def start(first: str, ghosts=()) -> R.Position:
    """The empty board with its ghosts, the `first` side's mark to go down first."""
    return R.opening(WORDS[first], ghosts)


def ghost_cells(ghosts) -> list[str]:
    """Every square a ghost could lock: all but a ghost's."""
    return [cell for cell in R.READING if cell not in ghosts]


def ghost_board(ghosts) -> str:
    """The board before its first mark: its ghosts alone."""
    return R.opening(R.X, ghosts).board


def legal(position: R.Position) -> list[str]:
    return R.legal(position)


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, code)


def notation(position: R.Position, code: str) -> str:
    """The move as the score sheet writes it: `Xe5`, and `Xe5#` for the win."""
    return R.notation(position, code)


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the same as the sheet, `Xe5`."""
    return notation(position, code)


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, code)


def final(position: R.Position) -> str:
    return position.board


def ending(positions: list[R.Position], codes: list[str]) -> tuple[str | None, str, list | None] | None:
    """How the game ends, if it does: the side that won, how, and the three boards it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (SIDE[end.winner] if end.winner else None), end.reason, list(end.line) or None


def alert(position: R.Position | None) -> str:
    """What the turn's plate says, the rules alone: a ghost to place, the board the side to move is sent to, or any
    board."""
    if position is None:
        return "place a ghost"
    target = position.target
    return f"{R.PLACE[target]} board" if target else "any board"


def pressure(position: R.Position) -> tuple[str, str]:
    """What a reply's last line says the side to move faces: where the rules send it, the house's way and GitHub's."""
    target = position.target
    said = f"in the {R.PLACE[target]} board" if target else "in any open board"
    return said, said


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move: nothing, since no block is called for."""
    return ""


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the marks and ghosts, the side drawn to place the first ghost, and once both ghosts
    are down, the side drawn to make the first mark."""
    board = positions[-1].board if positions else ghost_board([g["move"] for g in game.get("ghosts", [])])
    out = {"board": board, "places": game["places"]}
    if game.get("opens"):
        out["opens"] = game["opens"]
    return out


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: nothing, in Tic-Tac."""
    return {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return "three boards in a row!"
