# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Connect Four: positions, legal drops, threats, and how a game ends.

  from connectfour_rules import START, Position, legal, make, ending, threats

A frame of seven columns and six rows: columns 1 to 7 from the left, rows 1
to 6 from the foot. The two colours take turns, a disc at a time, and a disc
falls to the lowest open cell of the column it is dropped down. Four in a
row wins, across, up or on a diagonal, and a full frame with no four is a
draw. The dark discs (`D`, Black's) drop first unless a position says the
light ones (`L`, White's) do (`first`): on the profile each player keeps one
colour, and the side the Arbiter opens for drops first. A move is written as
its column, `4`, with a `+` when it leaves its side a column to win down
next (a threat) and a `#` when it connects four, as chess marks a check and
a mate.

A threat is a column a side could drop down and win at once: the cell its
disc would land on completes four. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DARK, LIGHT = "D", "L"  # the board's letters: the dark discs are Black's, the light ones White's
COLS, ROWS = 7, 6
COLOUR = {DARK: "black", LIGHT: "white"}  # what a move's words call each colour's discs
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))  # across, up, and the two diagonals


def other(colour: str) -> str:
    return LIGHT if colour == DARK else DARK


@dataclass(frozen=True)
class Position:
    cells: tuple[str, ...] = ("",) * (COLS * ROWS)  # by (row - 1) * 7 + (column - 1): D, L, or "" when open
    last: tuple[int, int] | None = field(default=None, compare=False)  # where the last disc landed, column and row
    first: str = DARK  # the colour that dropped first in this game

    def at(self, col: int, row: int) -> str:
        return self.cells[(row - 1) * COLS + col - 1] if 1 <= col <= COLS and 1 <= row <= ROWS else ""

    def height(self, col: int) -> int:
        """How many discs the column holds."""
        return sum(1 for row in range(1, ROWS + 1) if self.at(col, row))

    @property
    def turn(self) -> str:
        """Whose disc drops next: the first colour opens, and the two take turns."""
        return self.first if self.cells.count(DARK) == self.cells.count(LIGHT) else other(self.first)

    @property
    def board(self) -> str:
        """The frame as the page's sheet takes it: six rows of L, D or a dot, the top row first."""
        return "/".join("".join(self.at(col, row) or "." for col in range(1, COLS + 1)) for row in range(ROWS, 0, -1))

    @classmethod
    def from_board(cls, text: str, first: str = DARK) -> Position:
        """The position a frame describes, `first` the colour that dropped first."""
        rows = text.split("/")
        if len(rows) != ROWS or any(len(row) != COLS or set(row) - set("DL.") for row in rows):
            raise ValueError(f"{text!r} is not six rows of seven D, L or dots")
        if first not in (DARK, LIGHT):
            raise ValueError(f"{first!r} is not a colour: D or L")
        cells = [""] * (COLS * ROWS)
        for i, row in enumerate(rows):
            for j, ch in enumerate(row):
                if ch != ".":
                    cells[(ROWS - 1 - i) * COLS + j] = ch
        position = cls(tuple(cells), first=first)
        if any(position.at(col, row) and not position.at(col, row - 1)
               for col in range(1, COLS + 1) for row in range(2, ROWS + 1)):
            raise ValueError(f"{text!r} has a disc over an open cell, and discs fall")
        if cells.count(first) - cells.count(other(first)) not in (0, 1):
            raise ValueError(f"{text!r} is not a frame the two sides could fill by taking turns,"
                             f" {COLOUR[first]} first")
        return position


START = Position()  # the dark discs to drop first


def opening(first: str) -> Position:
    """The empty frame, with `first` the colour that drops first."""
    return Position(first=first)


@dataclass(frozen=True)
class Ending:
    winner: str | None  # D or L, or None for a draw
    reason: str  # "four in a row" or "a full frame"
    line: tuple[tuple[int, int], ...] = ()  # the four cells connected, each a column and a row, along the line

    @property
    def result(self) -> str:
        """The result as a score sheet writes it, White's score first, as chess writes White's."""
        return {LIGHT: "1-0", DARK: "0-1"}.get(self.winner or "", "1/2-1/2")


def _at(cells: tuple[str, ...] | list[str], col: int, row: int) -> str:
    return cells[(row - 1) * COLS + col - 1] if 1 <= col <= COLS and 1 <= row <= ROWS else ""


def run(cells: tuple[str, ...] | list[str], col: int, row: int, dc: int, dr: int) -> list[tuple[int, int]]:
    """The cells of the disc's colour in an unbroken line through it, one way along it and the other, in order."""
    colour = _at(cells, col, row)
    back = 0
    while _at(cells, col - (back + 1) * dc, row - (back + 1) * dr) == colour:
        back += 1
    found = []
    c, r = col - back * dc, row - back * dr
    while _at(cells, c, r) == colour:
        found.append((c, r))
        c, r = c + dc, r + dr
    return found


def four(position: Position | tuple[str, ...] | list[str], col: int, row: int) -> tuple[tuple[int, int], ...]:
    """Four in a row through the disc at the cell, if it makes one: the first four of the line that hold it, across,
    then up, then on a diagonal."""
    cells = position.cells if isinstance(position, Position) else position
    if not _at(cells, col, row):
        return ()
    for dc, dr in DIRECTIONS:
        found = run(cells, col, row, dc, dr)
        if len(found) >= 4:
            at = found.index((col, row))
            start = min(max(0, at - 3), len(found) - 4)
            return tuple(found[start:start + 4])
    return ()


def ending(position: Position) -> Ending | None:
    """How the game ends at this position, if it does: four in a row, or a full frame with none."""
    spots = [position.last] if position.last else [(c, r) for c in range(1, COLS + 1) for r in range(1, ROWS + 1)]
    for col, row in spots:
        line = four(position, col, row)
        if line:
            return Ending(position.at(col, row), "four in a row", line)
    if all(position.cells):
        return Ending(None, "a full frame")
    return None


def legal(position: Position) -> list[int]:
    """Every column with room left, from the left; none once the game is over."""
    if ending(position):
        return []
    return [col for col in range(1, COLS + 1) if position.height(col) < ROWS]


def make(position: Position, col: int) -> Position:
    """The position after the side to move drops a disc down the column, which is taken to have room."""
    row = position.height(col) + 1
    cells = list(position.cells)
    cells[(row - 1) * COLS + col - 1] = position.turn
    return Position(tuple(cells), (col, row), position.first)


def threats(position: Position, colour: str) -> list[int]:
    """The columns, from the left, that `colour` could drop down and connect four at once."""
    out, cells = [], list(position.cells)
    for col in range(1, COLS + 1):
        row = position.height(col) + 1
        if row > ROWS:
            continue
        cells[(row - 1) * COLS + col - 1] = colour
        if four(cells, col, row):
            out.append(col)
        cells[(row - 1) * COLS + col - 1] = ""
    return out


def notation(position: Position, col: int) -> str:
    """The move as a score sheet writes it: its column, then `#` when it connects four and `+` when it threatens."""
    colour = position.turn
    after = make(position, col)
    end = ending(after)
    suffix = "#" if end and end.winner == colour else "+" if not end and threats(after, colour) else ""
    return f"{col}{suffix}"


def why_illegal(position: Position, col: int) -> str:
    """Why a disc can't go down the column, in a few words."""
    if position.height(col) >= ROWS:
        return f"column {col} is full"
    return "the game is over"
