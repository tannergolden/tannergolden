# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Tic-Tac-Toe: positions, legal moves, threats, how a game ends, and perfect play from anywhere.

  from tictactoe_rules import START, Position, legal, make, ending, threats, outlook

Nine cells, named as chess names squares: files a to c from the left and
ranks 1 to 3 from the foot, so a1 is the lower left and c3 the upper right.
The two marks take turns, a mark to a cell; three in a row wins, and a full
board with no line is a draw. X moves first unless a position says O does
(`first`): on the profile each player keeps one mark, and the side the
Arbiter opens for moves first. A move is written as its mark and cell,
`Xb2`, with a `+` when it leaves its side a cell to win on next (a threat)
and a `#` when it wins, as chess marks a check and a mate.

The game is small enough to solve whole: `outlook` plays every line out to
say who wins with perfect play from a position, whichever mark moved first,
and it is a draw from the start. The tests hold it to a plain search of
every game, and the rules to the game's known counts of positions and games,
either mark first. Stdlib only.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

X, O = "X", "O"
FILES = "abc"
CELLS = tuple(f"{f}{r}" for r in (1, 2, 3) for f in FILES)  # a1, b1, c1, a2 ... c3: the order a position keeps
READING = tuple(f"{f}{r}" for r in (3, 2, 1) for f in FILES)  # a3, b3, c3 ... c1: the board as it is read
LINES = (("a1", "b1", "c1"), ("a2", "b2", "c2"), ("a3", "b3", "c3"), ("a1", "a2", "a3"), ("b1", "b2", "b3"),
         ("c1", "c2", "c3"), ("a1", "b2", "c3"), ("a3", "b2", "c1"))
CENTRE, CORNERS = "b2", ("a1", "c1", "a3", "c3")
INDEX = {cell: i for i, cell in enumerate(CELLS)}
SPOTS = tuple(tuple(INDEX[cell] for cell in line) for line in LINES)  # each line as its cells' places in a position
ORDER = tuple(INDEX[cell] for cell in READING)


def other(mark: str) -> str:
    return O if mark == X else X


@dataclass(frozen=True)
class Position:
    marks: tuple[str, ...] = ("",) * 9  # each cell's mark in CELLS order: X, O, or "" for an open cell
    first: str = X  # the mark that moved first in this game

    def at(self, cell: str) -> str:
        return self.marks[INDEX[cell]]

    @property
    def turn(self) -> str:
        """Whose mark goes down next: the first mark opens, and the two take turns."""
        return self.first if self.marks.count(X) == self.marks.count(O) else other(self.first)

    @property
    def board(self) -> str:
        """The board as the page's sheet takes it: three rows of X, O or a dot, the top row first, `O../XX./O.X`."""
        return "/".join("".join(self.at(f"{f}{r}") or "." for f in FILES) for r in (3, 2, 1))

    @classmethod
    def from_board(cls, text: str, first: str = X) -> Position:
        """The position a board describes, `first` the mark that moved first."""
        rows = text.split("/")
        if len(rows) != 3 or any(len(row) != 3 or set(row) - set("XO.") for row in rows):
            raise ValueError(f"{text!r} is not three rows of X, O or a dot")
        if first not in (X, O):
            raise ValueError(f"{first!r} is not a mark: X or O")
        marks = {f"{FILES[f]}{3 - r}": ch for r, row in enumerate(rows) for f, ch in enumerate(row) if ch != "."}
        position = cls(tuple(marks.get(cell, "") for cell in CELLS), first)
        if position.marks.count(first) - position.marks.count(other(first)) not in (0, 1):
            raise ValueError(f"{text!r} is not a board the two sides could reach by taking turns, {first} first")
        return position


START = Position()  # X to move first


def opening(first: str) -> Position:
    """The empty board, with `first` the mark that moves first."""
    return Position(first=first)


@dataclass(frozen=True)
class Ending:
    winner: str | None  # X or O, or None for a draw
    reason: str  # "three in a row" or "a full board"
    line: tuple[str, ...] = ()  # the three cells of a won line, in the order LINES gives them

    @property
    def result(self) -> str:
        """The result as a score sheet writes it, X's score first, as chess writes White's."""
        return {X: "1-0", O: "0-1"}.get(self.winner or "", "1/2-1/2")


def won(position: Position) -> tuple[str, tuple[str, ...]] | None:
    """The mark that has three in a row, and the line, if either has."""
    marks = position.marks
    for line, (a, b, c) in zip(LINES, SPOTS):
        if marks[a] and marks[a] == marks[b] == marks[c]:
            return marks[a], line
    return None


def ending(position: Position) -> Ending | None:
    """How the game ends at this position, if it does: three in a row, or a full board with none."""
    line = won(position)
    if line:
        return Ending(line[0], "three in a row", line[1])
    if all(position.marks):
        return Ending(None, "a full board")
    return None


def legal(position: Position) -> list[str]:
    """Every open cell, as the board is read, top row first; none once the game is over."""
    if ending(position):
        return []
    return [READING[n] for n, i in enumerate(ORDER) if not position.marks[i]]


def make(position: Position, cell: str) -> Position:
    """The position after the side to move marks the cell, which is taken to be open."""
    marks = list(position.marks)
    marks[INDEX[cell]] = position.turn
    return Position(tuple(marks), position.first)


def threats(position: Position, mark: str) -> list[str]:
    """The open cells, as the board is read, where `mark` would complete three in a row."""
    marks, out = position.marks, []
    for n, i in enumerate(ORDER):
        if not marks[i] and any(i in spots and all(marks[j] == mark for j in spots if j != i) for spots in SPOTS):
            out.append(READING[n])
    return out


@functools.cache
def _value(marks: tuple[str, ...], turn: str) -> int:
    """The worth of the marks with `turn` to move, with perfect play: 1 when X wins, -1 when O does, 0 for a draw.
    Whose turn it is, not which mark moved first, is all perfect play asks."""
    end = ending(Position(marks))
    if end:
        return {X: 1, O: -1}.get(end.winner or "", 0)
    values = [_value(marks[:i] + (turn,) + marks[i + 1:], other(turn)) for i, mark in enumerate(marks) if not mark]
    return max(values) if turn == X else min(values)


def outlook(position: Position) -> str:
    """Who wins from here with perfect play on both sides: X, O, or "draw"."""
    return {1: X, -1: O, 0: "draw"}[_value(position.marks, position.turn)]


def notation(position: Position, cell: str) -> str:
    """The move as a score sheet writes it: its mark and cell, then `#` when it wins and `+` when it threatens."""
    mark = position.turn
    after = make(position, cell)
    end = ending(after)
    suffix = "#" if end and end.winner == mark else "+" if not end and threats(after, mark) else ""
    return f"{mark}{cell}{suffix}"


def why_illegal(position: Position, cell: str) -> str:
    """Why a cell can't be marked, in a few words."""
    taken = position.at(cell)
    if taken:
        return f"there's already an {taken} on {cell}"
    return "the game is over"
