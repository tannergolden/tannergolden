# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Pentago on the profile, the second tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py pentago .github/pentago

What the shared engine asks of the game: how a move is written in an issue's
title (its hole, quarter and way, `e4-ur-cw`, or a ghost's hole, `b5`), on the
sheet and in a reply (the same, with a `#` for the move that won), how a game
ends, what its board sets out for the page beside the fields every game
shares, and what it calls things.

A move sets a marble and then turns any quarter a quarter turn, and five in a
row wins, for the mover or, if the turn makes five for the other side alone,
for the other side. Each player keeps one colour in every game: the house
plays White and GitHub Black. The Ghost Rule opens every game: the Arbiter
draws the side that sets the first ghost, a marble that is nobody's, the
other side sets the second, and then the Arbiter draws the side that sets the
first marble. The board sets out the marbles and ghosts as six rows, top
first, the side drawn to set the first ghost (`places`), the side drawn to
open (`opens`), and once the game is won, the five holes it was won on
(`line`). The README lists every empty hole once with a link for each of its
eight turns. Nothing on the page helps a player choose: no hole or turn that
would make five, and no block called out, in the board or a reply. The rules
are pentago_rules.py's and the names pentago_names.py's. Stdlib only.
"""
from __future__ import annotations

import re

import pentago_rules as R
from page import GITHUB, HOUSE
from pentago_names import entry, ghost_listing, listing

KEY, TITLE = "pentago", "Pentago"
EXT, RECORD = "txt", "record"  # a finished game's file, and what the note's link calls it
GHOST_RULE, OPENER = True, None  # each side sets a ghost, then the Arbiter draws who opens
CODE = re.compile(r"[a-f][1-6](?:-(?:ul|ur|ll|lr)-(?:cw|acw))?")  # a move as an issue's title carries it
GHOST_CODE = re.compile(r"[a-f][1-6]")  # a ghost's hole
WORDS = {HOUSE: "White", GITHUB: "Black"}  # what each side is called, in every game
COLOURS = {HOUSE: R.W, GITHUB: R.B}  # the marbles each side sets: the house the white ones, GitHub the black
SIDE = {colour: side for side, colour in COLOURS.items()}
SIGN = {"White": "⚪", "Black": "⚫"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's marble
RESULTS = {HOUSE: "1-0", GITHUB: "0-1", None: "1/2-1/2"}  # White's score first, as chess writes it
GHOSTS = ("set", "sets", "sets a ghost", "set")  # a ghost's verb, said of a side, in full, and done
SPOT = "hole"  # what a ghost stands on, as a refusal names it
OPENS_NOTE = ("@{owner} always plays White and GitHub Black. Under the Ghost Rule each side first sets a ghost, a"
              " marble that is nobody's, and then the Arbiter draws who sets the first marble.")
RULE = ("A move sets a marble, then turns any quarter a quarter turn; five in a row wins, for the other side if the"
        " turn makes five for it alone, and five for both or a full board is a draw.")
DRAWN = {"five for both": "with five for both sides", "a full board": "on a full board"}

__all__ = ["entry", "ghost_listing", "listing"]


def start(first: str, ghosts=()) -> R.Position:
    """The empty board with its ghosts, the `first` side's colour to set the first marble."""
    return R.opening(COLOURS[first], ghosts)


def ghost_cells(ghosts) -> list[str]:
    """Every hole a ghost could stand in: all but a ghost's."""
    return [cell for cell in R.READING if cell not in ghosts]


def ghost_board(ghosts) -> str:
    """The board before its first marble: its ghosts alone."""
    return R.opening(R.W, ghosts).board


def legal(position: R.Position) -> list[str]:
    return R.legal(position)


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, code)


def notation(position: R.Position, code: str) -> str:
    """The move as the score sheet writes it: `e4-ur-cw`, its hole alone when the marble made five before any turn,
    and a `#` on the move that won."""
    return R.notation(position, code)


def shown(position: R.Position, code: str) -> str:
    """The move as a reply writes it: the same as the sheet."""
    return notation(position, code)


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, code)


def final(position: R.Position) -> str:
    return position.board


def ending(positions: list[R.Position], codes: list[str]) -> tuple[str | None, str, list | None] | None:
    """How the game ends, if it does: the side that won, how, and the five it was won on."""
    end = R.ending(positions[-1])
    if end is None:
        return None
    return (SIDE[end.winner] if end.winner else None), end.reason, list(end.line) or None


def alert(position: R.Position | None) -> str:
    """What the turn's plate says: a ghost to set, and nothing once both are down."""
    return "set a ghost" if position is None else ""


def pressure(position: R.Position) -> tuple[str, str]:
    """What a reply's last line says the side to move faces: nothing, since no threat is called out."""
    return "", ""


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move: nothing, since no block is called for."""
    return ""


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the marbles and ghosts, the side drawn to set the first ghost, and once both ghosts
    are down, the side drawn to set the first marble."""
    board = positions[-1].board if positions else ghost_board([g["move"] for g in game.get("ghosts", [])])
    out = {"board": board, "places": game["places"]}
    if game.get("opens"):
        out["opens"] = game["opens"]
    return out


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: nothing, in Pentago."""
    return {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return "five in a row!"
