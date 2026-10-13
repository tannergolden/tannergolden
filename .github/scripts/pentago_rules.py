# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Pentago: positions, legal moves, a quarter's turn, and how a game ends.

  from pentago_rules import Position, opening, legal, make, ending, notation

The board is six holes by six in four quarters of three by three: the upper
left (a4 to c6), the upper right (d4 to f6), the lower left (a1 to c3) and the
lower right (d1 to f3). Its holes are named as chess names squares, files a
to f from the left and ranks 1 to 6 from the foot.

A move sets a marble of the mover's colour in an empty hole and then turns
one quarter a quarter turn, clockwise or anticlockwise as the board is seen,
everything on it turning with it. It is written as the hole, the quarter and
the way, `e4-ur-cw`, the code an issue's title carries. Five marbles of one
colour in a row, across, up and down or on a diagonal, wins: if the marble
makes five on its own, the game is won before any quarter turns, and the move
is written as its hole alone with its `#`, `e4#`; else the quarter turns, and
five for the mover wins, five for the other side alone wins it for them, and
five for both is a draw. A full board without five is a draw.

The Ghost Rule sets two ghosts before the first marble (`opening`): marbles
that are nobody's, which turn with their quarters, so no five runs through
them. With two holes theirs, each side has seventeen marbles. A move's `#`
marks the one that won the game, whichever side it won it for, and nothing
marks a threat. Stdlib only.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

W, B, GHOST = "W", "B", "G"
FILES = "abcdef"
CELLS = tuple(f"{f}{r}" for r in range(1, 7) for f in FILES)  # a1, b1 ... f6: the order a position keeps
READING = tuple(f"{f}{r}" for r in range(6, 0, -1) for f in FILES)  # a6, b6 ... f1: the board as it is read
INDEX = {cell: i for i, cell in enumerate(CELLS)}
QUARTERS = {"ul": (0, 3), "ur": (3, 3), "ll": (0, 0), "lr": (3, 0)}  # each quarter's lowest file and rank
QNAME = {"ul": "upper left", "ur": "upper right", "ll": "lower left", "lr": "lower right"}
WAYS = {"cw": "clockwise", "acw": "anticlockwise"}
TURNS = tuple((q, w) for q in QUARTERS for w in WAYS)  # every turn, in the order a hole's links list them
SPOT = {(0, 2): "upper left corner", (1, 2): "top edge", (2, 2): "upper right corner", (0, 1): "left edge",
        (1, 1): "centre", (2, 1): "right edge", (0, 0): "lower left corner", (1, 0): "bottom edge",
        (2, 0): "lower right corner"}
COLOUR = {W: "white", B: "black"}


def other(colour: str) -> str:
    return B if colour == W else W


def xy(cell: str) -> tuple[int, int]:
    return FILES.index(cell[0]), int(cell[1]) - 1


def quarter_of(cell: str) -> str:
    x, y = xy(cell)
    return next(q for q, (qx, qy) in QUARTERS.items() if qx <= x < qx + 3 and qy <= y < qy + 3)


def spot_of(cell: str) -> tuple[int, int]:
    """Where a hole stands inside its quarter."""
    x, y = xy(cell)
    qx, qy = QUARTERS[quarter_of(cell)]
    return x - qx, y - qy


def _lines() -> tuple[tuple[int, ...], ...]:
    out = []

    def at(x, y):
        return INDEX[f"{FILES[x]}{y + 1}"]
    for y in range(6):
        out += [tuple(at(x + k, y) for k in range(5)) for x in range(2)]
    for x in range(6):
        out += [tuple(at(x, y + k) for k in range(5)) for y in range(2)]
    for x in range(2):
        for y in range(2):
            out += [tuple(at(x + k, y + k) for k in range(5)), tuple(at(x + k, y + 4 - k) for k in range(5))]
    return tuple(out)


LINES = _lines()  # the 32 lines of five, as places in a position


@functools.cache
def _turned(quarter: str, way: str) -> tuple[int, ...]:
    """Where each place of a position comes from once `quarter` has turned `way`: a permutation of the 36."""
    qx, qy = QUARTERS[quarter]
    source = list(range(36))
    for i in range(3):
        for j in range(3):
            ni, nj = (j, 2 - i) if way == "cw" else (2 - j, i)
            source[INDEX[f"{FILES[qx + ni]}{qy + nj + 1}"]] = INDEX[f"{FILES[qx + i]}{qy + j + 1}"]
    return tuple(source)


@dataclass(frozen=True)
class Position:
    holes: tuple[str, ...] = ("",) * 36  # each hole's marble in CELLS order: W, B, G for a ghost, or "" when empty
    first: str = W  # the colour that set the first marble in this game

    def at(self, cell: str) -> str:
        return self.holes[INDEX[cell]]

    @property
    def turn(self) -> str:
        """Whose marble goes in next: the first colour opens, and the two take turns."""
        return self.first if self.holes.count(W) == self.holes.count(B) else other(self.first)

    @property
    def board(self) -> str:
        """The board as the page's sheet takes it: six rows of W, B, G for a ghost or a dot, the top row first."""
        return "/".join("".join(self.at(f"{f}{r}") or "." for f in FILES) for r in range(6, 0, -1))

    @property
    def ghosts(self) -> list[str]:
        """Where the ghosts stand now, as the board is read: a turn can move them."""
        return [cell for cell in READING if self.at(cell) == GHOST]


def opening(first: str, ghosts=()) -> Position:
    """The empty board with its ghosts, `first` the colour that sets the first marble."""
    holes = ["G" if cell in ghosts else "" for cell in CELLS]
    return Position(tuple(holes), first)


def turned(holes: tuple[str, ...], quarter: str, way: str) -> tuple[str, ...]:
    return tuple(holes[i] for i in _turned(quarter, way))


def landed(cell: str, quarter: str, way: str) -> str:
    """Where a marble set in `cell` stands once `quarter` has turned `way`."""
    if quarter_of(cell) != quarter:
        return cell
    return CELLS[_turned(quarter, way).index(INDEX[cell])]


def fives(holes: tuple[str, ...], colour: str) -> list[tuple[int, ...]]:
    return [line for line in LINES if all(holes[i] == colour for i in line)]


def parse(code: str) -> tuple[str, str, str]:
    """A move's code, `e4-ur-cw`: its hole, its quarter and its way."""
    cell, quarter, way = code.split("-")
    return cell, quarter, way


@dataclass(frozen=True)
class Ending:
    winner: str | None  # W or B, or None for a draw
    reason: str  # "five in a row", "five for both" or "a full board"
    line: tuple[str, ...] = ()  # the five holes of a won line

    @property
    def result(self) -> str:
        """The result as a score sheet writes it, White's score first, as chess writes it."""
        return {W: "1-0", B: "0-1"}.get(self.winner or "", "1/2-1/2")


def ending(position: Position) -> Ending | None:
    """How the game ends at this position, if it does: five of one colour, five of both, or a full board."""
    white, black = fives(position.holes, W), fives(position.holes, B)
    if white and black:
        return Ending(None, "five for both")
    if white or black:
        colour = W if white else B
        return Ending(colour, "five in a row", tuple(CELLS[i] for i in (white or black)[0]))
    if all(position.holes):
        return Ending(None, "a full board")
    return None


def empty(position: Position) -> list[str]:
    """The empty holes, as the board is read."""
    return [cell for cell in READING if not position.at(cell)]


def legal(position: Position) -> list[str]:
    """Every move the side to move may make, each empty hole with each of its eight turns, as the board is read;
    none once the game is over."""
    if ending(position):
        return []
    return [f"{cell}-{q}-{w}" for cell in empty(position) for q, w in TURNS]


def make(position: Position, code: str) -> Position:
    """The position after the side to move sets its marble and, unless the marble alone made five, turns its
    quarter."""
    cell, quarter, way = parse(code)
    holes = list(position.holes)
    holes[INDEX[cell]] = position.turn
    holes = tuple(holes)
    if fives(holes, position.turn):
        return Position(holes, position.first)
    return Position(turned(holes, quarter, way), position.first)


def won_unturned(position: Position, code: str) -> bool:
    """Whether a move's marble makes five on its own, so its quarter never turns."""
    cell = parse(code)[0]
    holes = list(position.holes)
    holes[INDEX[cell]] = position.turn
    return bool(fives(tuple(holes), position.turn))


def notation(position: Position, code: str) -> str:
    """The move as a score sheet writes it: its hole, quarter and way, or its hole alone when the marble made five
    before any turn; then `#` when it ended the game with a win, whichever side's."""
    end = ending(make(position, code))
    mark = "#" if end and end.winner else ""
    return f"{parse(code)[0]}{mark}" if won_unturned(position, code) else f"{code}{mark}"


def why_illegal(position: Position, code: str) -> str:
    """Why a move can't be made, in a few words: a hole that is taken, or a hole alone, as a ghost's is written, with
    no quarter to turn."""
    if ending(position):
        return "the game is over"
    cell = code.split("-")[0]
    taken = position.at(cell)
    if taken == GHOST:
        return f"a ghost stands on {cell}"
    if taken:
        return f"there's already a {COLOUR[taken]} marble on {cell}"
    return f"a move names its hole, then the quarter it turns and which way, such as `{cell}-ul-cw`"
