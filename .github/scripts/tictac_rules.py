# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Tic-Tac: positions, legal moves, where a mark sends the other side, and how a game ends.

  from tictac_rules import Position, opening, legal, make, ending, notation

Tic-Tac is Tic-Tac-Toe on nine boards at once, three a side, the game also
known as Ultimate Tic-Tac-Toe. Its 81 squares are named as chess names
squares: files a to i from the left and ranks 1 to 9 from the foot, so a1 is
the lower left square and i9 the upper right. The nine small boards are named
as Tic-Tac-Toe names its cells, a1 the lower left board and c3 the upper
right.

The two marks take turns, a mark to a square. Where a mark goes inside its
board sends the other side to the board in that place on the big board: take
a board's upper right corner and the other side plays in the upper right
board. Three in a row inside a board wins that board, which closes; a board
whose open squares are all taken without a line is drawn, and closes too. A
side sent to a closed board, and the side that makes the first mark, may play
any open square of any open board. Three boards won in a row wins the game;
once neither side can still win three boards in a row, the game is drawn.

The Ghost Rule locks two squares before the first mark (`ghosts`): nobody can
take a ghost's square, no line runs through it, and a board with a ghost is
full once its other squares are taken. A move is written as its mark and
square, `Xe5`, and with a `#` when it wins the game, as chess marks a mate.
Nothing marks a threat. Stdlib only.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

X, O = "X", "O"
FILES = "abcdefghi"
CELLS = tuple(f"{f}{r}" for r in range(1, 10) for f in FILES)  # a1, b1 ... i9: the order a position keeps
READING = tuple(f"{f}{r}" for r in range(9, 0, -1) for f in FILES)  # a9, b9 ... i1: the board as it is read
INDEX = {cell: i for i, cell in enumerate(CELLS)}
LINES = (((0, 0), (1, 0), (2, 0)), ((0, 1), (1, 1), (2, 1)), ((0, 2), (1, 2), (2, 2)),
         ((0, 0), (0, 1), (0, 2)), ((1, 0), (1, 1), (1, 2)), ((2, 0), (2, 1), (2, 2)),
         ((0, 0), (1, 1), (2, 2)), ((0, 2), (1, 1), (2, 0)))
BOARDS = tuple((bx, by) for by in (2, 1, 0) for bx in range(3))  # the boards as the big board is read
PLACE = {(0, 2): "upper left", (1, 2): "top", (2, 2): "upper right", (0, 1): "left", (1, 1): "centre",
         (2, 1): "right", (0, 0): "lower left", (1, 0): "bottom", (2, 0): "lower right"}
SQUARE = {(0, 2): "upper left corner", (1, 2): "top edge", (2, 2): "upper right corner", (0, 1): "left edge",
          (1, 1): "centre", (2, 1): "right edge", (0, 0): "lower left corner", (1, 0): "bottom edge",
          (2, 0): "lower right corner"}
DRAWN = "draw"


def other(mark: str) -> str:
    return O if mark == X else X


def xy(cell: str) -> tuple[int, int]:
    return FILES.index(cell[0]), int(cell[1]) - 1


def board_of(cell: str) -> tuple[int, int]:
    """The board a square stands in, by its file and rank on the big board, from 0 at the lower left."""
    x, y = xy(cell)
    return x // 3, y // 3


def spot_of(cell: str) -> tuple[int, int]:
    """Where a square stands inside its board: the board on the big board it sends the other side to."""
    x, y = xy(cell)
    return x % 3, y % 3


def board_name(b: tuple[int, int]) -> str:
    """A board as Tic-Tac-Toe names a cell: a1 the lower left board, c3 the upper right."""
    return f"{'abc'[b[0]]}{b[1] + 1}"


@functools.cache
def squares_of(b: tuple[int, int]) -> tuple[str, ...]:
    """A board's nine squares, as it is read: its top row first, each from the left."""
    bx, by = b
    return tuple(f"{FILES[bx * 3 + i]}{by * 3 + j + 1}" for j in (2, 1, 0) for i in range(3))


@functools.cache
def lines_of(b: tuple[int, int]) -> tuple[tuple[str, ...], ...]:
    """A board's eight lines of three, as squares."""
    bx, by = b
    return tuple(tuple(f"{FILES[bx * 3 + i]}{by * 3 + j + 1}" for i, j in line) for line in LINES)


@dataclass(frozen=True)
class Position:
    marks: tuple[str, ...] = ("",) * 81  # each square's mark in CELLS order: X, O, or "" for an open square
    first: str = X  # the mark that moved first in this game
    ghosts: frozenset = frozenset()  # the squares the Ghost Rule locked
    last: str = ""  # the square of the last mark, which says where the next is sent

    def at(self, cell: str) -> str:
        return self.marks[INDEX[cell]]

    @property
    def turn(self) -> str:
        """Whose mark goes down next: the first mark opens, and the two take turns."""
        return self.first if self.marks.count(X) == self.marks.count(O) else other(self.first)

    def taken(self, cell: str) -> bool:
        return bool(self.marks[INDEX[cell]]) or cell in self.ghosts

    @property
    def closed(self) -> dict[tuple[int, int], str | None]:
        """Each board as it stands: won by X or O, drawn, or None while it is open."""
        return _closed(self.marks, self.ghosts)

    @property
    def target(self) -> tuple[int, int] | None:
        """The board the side to move is sent to, or None when it may play any open board."""
        if not self.last:
            return None
        b = spot_of(self.last)
        return b if self.closed[b] is None else None

    @property
    def board(self) -> str:
        """The board as the page's sheet takes it: nine rows of X, O, G for a ghost or a dot, the top row first."""
        return "/".join("".join("G" if f"{f}{r}" in self.ghosts else self.at(f"{f}{r}") or "." for f in FILES)
                        for r in range(9, 0, -1))


@functools.lru_cache(maxsize=4096)
def _closed(marks: tuple[str, ...], ghosts: frozenset) -> dict:
    out = {}
    for b in BOARDS:
        won = next((m for m in (X, O) if any(all(marks[INDEX[c]] == m for c in line) for line in lines_of(b))), None)
        full = all(marks[INDEX[c]] or c in ghosts for c in squares_of(b))
        out[b] = won or (DRAWN if full else None)
    return out


def opening(first: str, ghosts=()) -> Position:
    """The empty board with its ghosts, `first` the mark that makes the first mark."""
    return Position(first=first, ghosts=frozenset(ghosts))


@dataclass(frozen=True)
class Ending:
    winner: str | None  # X or O, or None for a draw
    reason: str  # "three boards in a row" or "no line left"
    line: tuple[str, ...] = ()  # the three boards of a won line, named as Tic-Tac-Toe names cells

    @property
    def result(self) -> str:
        """The result as a score sheet writes it, X's score first, as chess writes White's."""
        return {X: "1-0", O: "0-1"}.get(self.winner or "", "1/2-1/2")


def ending(position: Position) -> Ending | None:
    """How the game ends at this position, if it does: three boards in a row, or no line of three boards left that
    either mark could still win."""
    closed = position.closed
    for line in LINES:
        for mark in (X, O):
            if all(closed[b] == mark for b in line):
                return Ending(mark, "three boards in a row", tuple(board_name(b) for b in line))

    def open_to(mark: str) -> bool:
        return any(all(closed[b] in (None, mark) for b in line) for line in LINES)
    if not open_to(X) and not open_to(O):
        return Ending(None, "no line left")
    return None


def legal(position: Position) -> list[str]:
    """Every square the side to move may take, as the board is read, top row first; none once the game is over.
    In the board it is sent to while that board is open, else in any open board."""
    if ending(position):
        return []
    closed, target = position.closed, position.target
    boards = [target] if target else [b for b in BOARDS if closed[b] is None]
    allowed = {c for b in boards for c in squares_of(b)}
    return [c for c in READING if c in allowed and not position.taken(c)]


def make(position: Position, cell: str) -> Position:
    """The position after the side to move marks the square, which is taken to be legal."""
    marks = list(position.marks)
    marks[INDEX[cell]] = position.turn
    return Position(tuple(marks), position.first, position.ghosts, cell)


def notation(position: Position, cell: str) -> str:
    """The move as a score sheet writes it: its mark and square, then `#` when it wins the game."""
    mark = position.turn
    end = ending(make(position, cell))
    return f"{mark}{cell}{'#' if end and end.winner == mark else ''}"


def why_illegal(position: Position, cell: str) -> str:
    """Why a square can't be taken, in a few words."""
    if ending(position):
        return "the game is over"
    if cell in position.ghosts:
        return f"a ghost locks {cell}, so nobody can take it"
    taken = position.at(cell)
    if taken:
        return f"there's already an {taken} on {cell}"
    target = position.target
    if target and board_of(cell) != target:
        return f"the last mark sent {position.turn} to the {PLACE[target]} board, so it must go there"
    return f"the {PLACE[board_of(cell)]} board is closed"
