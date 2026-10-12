# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of American checkers (English draughts): positions, legal moves, their codes, and how a game ends.

  from checkers_rules import START, Position, legal_moves, make, find, ending

The board is the thirty-two dark squares, numbered 1 to 32 in the standard way,
four to a row, from the dark side's back row (1 to 4) to the light side's (29
to 32). Dark's twelve men start on 1 to 12 and light's on 21 to 32, and dark
moves first; every message calls the dark side Black and the light side White,
as American checkers does. A man steps one square diagonally forward, a king
one square diagonally either way. A capture is a jump over a piece of the other
side to the empty square beyond it, and it is compulsory: a side that can jump
must, though it may choose which jump, the longest or not. A jump goes on while
the piece can take more, a man jumping only forward and a king either way, and
no piece is taken twice; a man that reaches the far row is crowned a king, and
its move ends there. Every legal move is generated, every jump to where it must
stop, and the counts of every move sequence from the start match the published
perft numbers, which the tests hold the generator to.

A position is the pieces and whose turn it is, read from and written as a PDN
FEN (B:W21,22,K30:B1,2,9), and a position read from one is held to what a game
can reach. Moves are written as checkers writes them: 11-15 for a step, 22x15
or 22x15x8 for a jump, a square for every landing.

A game ends when the rules end it, with nobody asking: a side with no legal
move on its turn loses, whether it has no piece left or none that can move.
Draws are automatic, since nobody is here to agree one: the same position with
the same side to move for the third time, or forty moves by each side, eighty
in all, with no capture and no man moved (the ACF's forty-move rule). A
finished game is written as a PDN record. Stdlib only.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from operator import attrgetter

DARK, LIGHT = "d", "l"  # dark moves first: Black's men, GitHub's on the profile, and light is White's, the house's
SIDES = {DARK: "Black", LIGHT: "White"}  # the words every message names the sides by
SQUARES = range(1, 33)
MEN = 12  # each side's men at the start, and the most pieces a side ever has
CROWN = {DARK: frozenset(range(29, 33)), LIGHT: frozenset(range(1, 5))}  # the far row, where a man is crowned
HOME = {DARK: frozenset(range(1, 5)), LIGHT: frozenset(range(29, 33))}  # each side's own back row
OWN = {DARK: frozenset("dD"), LIGHT: frozenset("lL")}  # a side's men and kings
QUIET = 80  # plies in a row with no capture and no man moved that draw a game: forty moves by each side
RESULTS = {DARK: "1-0", LIGHT: "0-1", None: "1/2-1/2"}  # as PDN writes a result, dark's score first
REASONS = ("no move left", "repetition", "forty moves")
SQUARE = r"(?:3[0-2]|[12][0-9]|[1-9])"
CODE = re.compile(rf"{SQUARE}(?:-{SQUARE}|(?:x{SQUARE})+)")  # a move as an issue's title and the sheet write it
# A move's code roughly as someone might type it, so a wrong one can be told what is wrong with it.
LOOSE = re.compile(r"[0-9]{1,9}(?:-[0-9]{1,9}|(?:x[0-9]{1,9})+)")
FEN = re.compile(r"([BW]):W([^:]*):B([^:]*)")
LISTED = re.compile(r"(K?)([1-9][0-9]?)")  # a square in a FEN's list, with a K before a king's


class FenError(ValueError):
    """A FEN that does not describe a position."""


def other(turn: str) -> str:
    return LIGHT if turn == DARK else DARK


def row_col(square: int) -> tuple[int, int]:
    """The square's row and column, both from 0, as the standard diagram draws it: the dark side's back row on top,
    square 1 in its second column."""
    row, index = divmod(square - 1, 4)
    return row, 2 * index + (1 if row % 2 == 0 else 0)


def square_at(row: int, col: int) -> int | None:
    """The dark square at the row and column, or None off the board or on a light square."""
    if not (0 <= row < 8 and 0 <= col < 8) or (row + col) % 2 == 0:
        return None
    return 4 * row + col // 2 + 1


def kind(piece: str) -> str:
    """`man` or `king`."""
    return "king" if piece.isupper() else "man"


# The way each piece goes, in rows: a dark man down the diagram toward 32, a light man up toward 1, a king both.
HEADINGS = {"d": (1,), "l": (-1,), "D": (-1, 1), "L": (-1, 1)}


def _table(letter: str) -> tuple[list[tuple[int, ...]], list[tuple[tuple[int, int], ...]]]:
    """Where a piece of `letter` can step from each square, and what it jumps and lands on from there, both listed
    by square so a move's squares come out in order: the row above before the row below, left before right."""
    steps: list[tuple[int, ...]] = [()]
    jumps: list[tuple[tuple[int, int], ...]] = [()]
    for square in SQUARES:
        row, col = row_col(square)
        near, far = [], []
        for dr in HEADINGS[letter]:
            for dc in (-1, 1):
                step = square_at(row + dr, col + dc)
                land = square_at(row + 2 * dr, col + 2 * dc)
                if step is not None:
                    near.append(step)
                    if land is not None:
                        far.append((step, land))
        steps.append(tuple(near))
        jumps.append(tuple(far))
    return steps, jumps


STEPS, JUMPS = {}, {}
for _letter in HEADINGS:
    STEPS[_letter], JUMPS[_letter] = _table(_letter)


class Pieces(dict):
    """A position's pieces by square, which nothing can change once the position is made: {1: "d", 30: "L"}, d and l
    for men, D and L for kings. A Position makes its own from whatever mapping it is given, and checks it first."""
    __slots__ = ()

    def _frozen(self, *args, **kwargs):
        raise TypeError("a position's pieces never change: make a move for the next position")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _frozen

    def __hash__(self) -> int:
        return hash(frozenset(self.items()))

    def __copy__(self) -> Pieces:
        return self

    def __deepcopy__(self, memo: dict) -> Pieces:
        return self

    def __reduce__(self):
        return Pieces, (dict(self),)


def _checked(pieces: Mapping, turn: str) -> dict[int, str]:
    """The pieces in square order, once they are a position a game can reach: a ValueError says what is wrong, and a
    TypeError when they are not a mapping at all."""
    if not isinstance(pieces, Mapping):
        raise TypeError(f"the pieces are {type(pieces).__name__}, not a mapping of squares to pieces")
    for square, piece in pieces.items():
        if isinstance(square, bool) or not isinstance(square, int) or square not in SQUARES:
            raise ValueError(f"{square!r} is not a square: they are numbered 1 to 32")
        if not isinstance(piece, str) or piece not in HEADINGS:
            raise ValueError(f"{piece!r} on {square} is not a piece: d and l are men, D and L kings")
    out = dict(sorted(pieces.items()))
    for side in (DARK, LIGHT):
        count = sum(1 for piece in out.values() if piece in OWN[side])
        if count > MEN:
            raise ValueError(f"{SIDES[side]} has {count} pieces, and a side never has more than {MEN}")
        crowned = sorted(square for square, piece in out.items() if piece == side and square in CROWN[side])
        if crowned:
            raise ValueError(f"{SIDES[side]} has a man on {crowned[0]}, its far row, where it would have been crowned")
    if not any(piece in OWN[other(turn)] for piece in out.values()):
        raise ValueError(f"{SIDES[other(turn)]} has no piece, so it can't have made the last move")
    return out


@dataclass(frozen=True)
class Position:
    pieces: Mapping[int, str]  # square 1..32 -> "d", "l" (men) or "D", "L" (kings)
    turn: str  # DARK or LIGHT

    def __post_init__(self) -> None:
        if self.turn not in SIDES:
            raise ValueError(f"{self.turn!r} is not a side to move: {DARK!r} for dark, {LIGHT!r} for light")
        if not isinstance(self.pieces, Pieces):  # a position's own pieces come checked already
            object.__setattr__(self, "pieces", Pieces(_checked(self.pieces, self.turn)))

    @property
    def fen(self) -> str:
        """The position as PDN writes it: whose turn, then the light pieces and the dark, a K before a king."""
        def listed(side: str) -> str:
            return ",".join(("K" if piece.isupper() else "") + str(square)
                            for square, piece in sorted(self.pieces.items()) if piece in OWN[side])
        return f"{'B' if self.turn == DARK else 'W'}:W{listed(LIGHT)}:B{listed(DARK)}"

    @classmethod
    def from_fen(cls, text: str) -> Position:
        """The position a PDN FEN describes, in the shape `fen` writes: B or W for the side to move, then the light
        pieces' squares and the dark's, a K before a king's. Anything else, or a position no game can reach, is a
        FenError."""
        match = FEN.fullmatch(text) if isinstance(text, str) else None
        if not match:
            raise FenError(f"{text!r} is not a checkers position in PDN, such as {START.fen}")
        pieces: dict[int, str] = {}
        for side, listed in ((LIGHT, match[2]), (DARK, match[3])):
            for token in listed.split(",") if listed else ():
                item = LISTED.fullmatch(token)
                if not item or int(item[2]) not in SQUARES:
                    raise FenError(f"{token!r} in {text!r} is not one of the squares 1 to 32, with a K before a king's")
                square = int(item[2])
                if square in pieces:
                    raise FenError(f"{text!r} puts two pieces on {square}")
                pieces[square] = side.upper() if item[1] else side
        try:
            return cls(pieces, DARK if match[1] == "B" else LIGHT)
        except ValueError as error:
            raise FenError(f"{text!r} is not a position a game can reach: {error}") from None


START = Position({**dict.fromkeys(range(1, 13), DARK), **dict.fromkeys(range(21, 33), LIGHT)}, DARK)


@dataclass(frozen=True, order=True)
class Move:
    path: tuple[int, ...]  # every square the piece stands on, from where it starts to where it lands
    captures: tuple[int, ...] = ()  # the squares of the pieces it takes, in order
    crowns: bool = False  # a man reaching the far row: it is crowned and its move ends there

    @property
    def code(self) -> str:
        """`11-15` for a step, `22x15` or `22x15x8` for a jump: a square for every landing."""
        return ("x" if self.captures else "-").join(map(str, self.path))


def jumps_from(pieces: Mapping[int, str], start: int, piece: str) -> list[Move]:
    """Every jump the piece on `start` can make, each followed to where it must stop: where nothing more can be
    taken, or where a man is crowned. The square it leaves is empty while it jumps, so a king may come back to it."""
    table = JUMPS[piece]
    enemy = OWN[LIGHT if piece in OWN[DARK] else DARK]
    crown = CROWN.get(piece, frozenset())
    if not any(pieces.get(over) in enemy and (land not in pieces or land == start) for over, land in table[start]):
        return []
    out: list[Move] = []

    def walk(at: int, path: tuple[int, ...], taken: tuple[int, ...]) -> None:
        onward = False
        for over, land in table[at]:
            if over in taken or pieces.get(over) not in enemy or (land in pieces and land != start):
                continue
            onward = True
            if land in crown:
                out.append(Move((*path, land), (*taken, over), True))
            else:
                walk(land, (*path, land), (*taken, over))
        if not onward and taken:
            out.append(Move(path, taken, False))

    walk(start, (start,), ())
    return out


def jumps(position: Position) -> list[Move]:
    """Every jump the side to move can make, which it must make one of when there is any."""
    mine = OWN[position.turn]
    return [move for square, piece in position.pieces.items() if piece in mine
            for move in jumps_from(position.pieces, square, piece)]


def legal_moves(position: Position) -> list[Move]:
    """Every legal move, in order of their squares as numbers (9-13, 9-14, 10-14), which is Move's own order: the
    jumps when there is any, since a capture is compulsory, and otherwise every step."""
    found = jumps(position)
    if not found:
        pieces, mine = position.pieces, OWN[position.turn]
        for square, piece in pieces.items():
            if piece in mine:
                crown = CROWN.get(piece, ())
                found += [Move((square, to), (), to in crown) for to in STEPS[piece][square] if to not in pieces]
    return sorted(found, key=attrgetter("path"))


def must_jump(position: Position) -> bool:
    """Whether the side to move has a capture to make, which the board's turn plate says as `must jump`."""
    return bool(jumps(position))


def make(position: Position, move: Move) -> Position:
    """The position after the move, which is taken to be legal: the piece lands, what it jumped is taken off, a man
    reaching the far row is crowned, and the other side is to move."""
    pieces = dict(position.pieces)
    piece = pieces.pop(move.path[0])
    for square in move.captures:
        del pieces[square]
    pieces[move.path[-1]] = piece.upper() if move.crowns else piece
    return Position(Pieces(pieces), other(position.turn))


def find(position: Position, code: str) -> Move | None:
    """The legal move written as `code`, or None when no legal move is."""
    return next((move for move in legal_moves(position) if move.code == code), None)


def perft(position: Position, depth: int) -> int:
    """How many move sequences of this length the position has: the standard check of a move generator."""
    moves = legal_moves(position)
    if depth <= 1:
        return len(moves) if depth == 1 else 1
    return sum(perft(make(position, move), depth - 1) for move in moves)


# --- how a game ends ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Ending:
    winner: str | None  # DARK, LIGHT, or None for a draw
    reason: str  # "no move left", "repetition" or "forty moves"
    result: str  # "1-0" dark wins, "0-1" light wins, "1/2-1/2", as PDN writes it with dark first


def quiet_plies(positions: Sequence[Position], moves: Sequence[Move]) -> int:
    """How many plies in a row, back from the last, moved only a king and took nothing: the forty-move count."""
    count = 0
    for index in range(len(moves) - 1, -1, -1):
        move, before = moves[index], positions[index]
        piece = before.pieces.get(move.path[0])
        if piece is None:
            raise ValueError(f"move {index + 1}, {move.code}, starts where there is no piece")
        if move.captures or piece.islower():
            break
        count += 1
    return count


def ending(positions: Sequence[Position], moves: Sequence[Move]) -> Ending | None:
    """How the game ends at its last position, if it does. `positions` runs from the first position to the last and
    `moves` between them, so that positions[i + 1] is make(positions[i], moves[i]). The side to move with no legal
    move loses; otherwise the game is drawn at the third time the same position comes round with the same side to
    move, or after eighty plies in a row with no capture and no man moved."""
    if not positions or len(positions) != len(moves) + 1:
        raise ValueError(f"a game of {len(moves)} moves has {len(moves) + 1} positions, not {len(positions)}")
    last = positions[-1]
    if not legal_moves(last):
        winner = other(last.turn)
        return Ending(winner, "no move left", RESULTS[winner])
    quiet = quiet_plies(positions, moves)
    if quiet >= QUIET:
        return Ending(None, "forty moves", RESULTS[None])
    # A capture or a man's move can never be undone, so a position can only come round again after the last of them.
    if sum(1 for position in positions[len(positions) - 1 - quiet:] if position == last) >= 3:
        return Ending(None, "repetition", RESULTS[None])
    return None


# --- why a move is not legal -------------------------------------------------------------------------------------
def _either(codes: Sequence[str]) -> str:
    """`22x15x8`, `22x15x8 or 22x15x6`, `a, b or c`, each in code type."""
    shown = [f"`{code}`" for code in codes]
    return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " or " + shown[-1]


def _jumpers(position: Position, moves: Sequence[Move]) -> str:
    """The pieces that can jump, as a sentence's subject: `the man on 22`, `a man on 22 or 26`, `the man on 22 or
    the king on 15`."""
    starts = sorted({move.path[0] for move in moves})
    kinds = [kind(position.pieces[square]) for square in starts]
    if len(starts) == 1:
        return f"the {kinds[0]} on {starts[0]}"
    if len(set(kinds)) == 1:
        squares = [str(square) for square in starts]
        return f"a {kinds[0]} on " + ", ".join(squares[:-1]) + " or " + squares[-1]
    named = [f"the {k} on {square}" for k, square in zip(kinds, starts, strict=True)]
    return ", ".join(named[:-1]) + " or " + named[-1]


def _forward(piece: str, start: int, end: int) -> bool:
    """Whether going from `start` to `end` is forward for the piece's side: down the diagram for dark."""
    rows = row_col(end)[0] - row_col(start)[0]
    return rows > 0 if piece.lower() == DARK else rows < 0


def _between(start: int, end: int) -> int | None:
    """The square a jump from `start` to `end` passes over, or None when `end` is not a jump from `start`."""
    (r1, c1), (r2, c2) = row_col(start), row_col(end)
    if abs(r2 - r1) != 2 or abs(c2 - c1) != 2:
        return None
    return square_at((r1 + r2) // 2, (c1 + c2) // 2)


def _why_not_step(position: Position, start: int, end: int, piece: str) -> str:
    (r1, c1), (r2, c2) = row_col(start), row_col(end)
    if abs(r2 - r1) != 1 or abs(c2 - c1) != 1:
        return f"a step goes to the next square along a diagonal, and {end} isn't next to {start}"
    if piece.islower() and not _forward(piece, start, end):
        return "a man only moves forward, toward the far row, and only a king can move back"
    if end in position.pieces:
        return f"there's already a {kind(position.pieces[end])} on {end}"
    return f"the {kind(piece)} on {start} can't move to {end}"


def _why_not_jump(position: Position, squares: Sequence[int], piece: str) -> str:
    """What is wrong with a jump along `squares`, leg by leg, or "" when every leg is a jump the piece can make."""
    pieces, taken = position.pieces, []
    for index, (start, end) in enumerate(pairwise(squares)):
        over = _between(start, end)
        if over is None:
            return (f"a jump goes over the next square on a diagonal to the one beyond it, and {end} isn't a jump"
                    f" from {start}")
        if piece.islower() and not _forward(piece, start, end):
            return "a man only jumps forward, toward the far row, and only a king can jump back"
        victim = pieces.get(over)
        if victim is None:
            return f"there's nothing on {over} to jump"
        if victim in OWN[position.turn]:
            return f"the {kind(victim)} on {over} is yours, and a jump only takes the other side's pieces"
        if over in taken:
            return f"the {kind(victim)} on {over} is taken already, and no piece is taken twice"
        if end in pieces and end != squares[0]:
            return f"a jump lands on an empty square, and there's a {kind(pieces[end])} on {end}"
        taken.append(over)
        if piece.islower() and end in CROWN[position.turn] and index < len(squares) - 2:
            return f"a man is crowned when it reaches the far row, and its move ends there, on {end}"
    return ""


def why_illegal(position: Position, code: str) -> str:
    """Why a move is not legal here, in a few plain words; "" when it is legal."""
    if not isinstance(code, str) or not LOOSE.fullmatch(code):
        return "a move is written square to square, such as `11-15` for a step or `22x15x8` for a jump"
    texts = re.split("[-x]", code)
    wrong = next((text for text in texts if text != str(int(text)) or int(text) not in SQUARES), None)
    if wrong is not None:
        return f"there's no square {wrong}, as the squares are numbered 1 to 32"
    squares = [int(text) for text in texts]
    moves = legal_moves(position)
    codes = {move.code for move in moves}
    if code in codes:
        return ""
    if not moves:
        return f"{SIDES[position.turn]} has no move left, so the game is over"
    start, piece = squares[0], position.pieces.get(squares[0])
    if piece is None:
        return f"there is no man of yours on {start}"
    if piece not in OWN[position.turn]:
        return f"the {kind(piece)} on {start} is {SIDES[other(position.turn)]}'s"
    compulsory = f"a capture is compulsory, so {_jumpers(position, moves)} must jump"
    if "-" in code:
        if code.replace("-", "x") in codes:
            return f"a jump is written with an x, as `{code.replace('-', 'x')}`"
        return compulsory if moves[0].captures else _why_not_step(position, start, squares[1], piece)
    if len(squares) == 2 and code.replace("x", "-") in codes:
        return f"a step is written with a dash, as `{code.replace('x', '-')}`"
    path = tuple(squares)
    onward = [move.code for move in moves if move.path[:len(path)] == path]
    if onward:
        return f"a jump goes on while it can take more, so this one carries on as {_either(onward)}"
    skipped = any(_between(a, b) is None for a, b in pairwise(path))  # a leg longer than one jump
    within = [move.code for move in moves if skipped and move.path[0] == start and move.path[-1] == path[-1]
              and _inside(path, move.path)]
    if within:
        return f"a jump names every square it lands on, so this one is {_either(within)}"
    return _why_not_jump(position, squares, piece) or compulsory


def _inside(short: Sequence[int], long: Sequence[int]) -> bool:
    """Whether `short` is `long` with some of its squares left out, in the same order."""
    rest = iter(long)
    return all(square in rest for square in short)


# --- the record ----------------------------------------------------------------------------------------------------
TAG = re.compile(r"[A-Za-z0-9_]{1,40}")
PLY = re.compile(rf"({CODE.pattern})(?: (\{{[^{{}}\r\n]*\}}))?")  # a move's code, then perhaps a comment on it
NOTE = re.compile(r"[^{}\r\n]{1,400}")


def _escaped(value: str) -> str:
    """A header's value as PDN quotes it: a backslash before each backslash and each double quote."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def pdn(moves_text: list[str], headers: dict[str, str], result: str, *, note: str = "") -> str:
    """The game as a PDN record: its headers in brackets, the game type (21, English draughts) and result among them,
    then the moves numbered as a score sheet numbers them, dark's first, and the result. Each entry of `moves_text` is
    one move's code, perhaps followed by a comment in braces (`11-15 {tannergolden}`); `note` closes the moves with a
    comment of its own. A move's number is written again before light's reply when a comment comes between them, as
    PDN asks. Lines run to 79 characters."""
    if result not in (*RESULTS.values(), "*"):
        raise ValueError(f"{result!r} is not a result: 1-0, 0-1, 1/2-1/2 or *")
    tags = dict(headers)
    for name, value in (("Result", result), ("GameType", "21")):
        if tags.setdefault(name, value) != value:
            raise ValueError(f"the {name} header is {tags[name]!r}, and this record's is {value!r}")
    lines = []
    for name, value in tags.items():
        if not isinstance(name, str) or not TAG.fullmatch(name):
            raise ValueError(f"{name!r} is not a header's name")
        if not isinstance(value, str) or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise ValueError(f"the {name} header's value {value!r} is not one line of text")
        lines.append(f'[{name} "{_escaped(value)}"]')
    turn = Position.from_fen(tags["FEN"]).turn if "FEN" in tags else DARK
    number, words, commented = 1, [], True
    for text in moves_text:
        ply = PLY.fullmatch(text) if isinstance(text, str) else None
        if not ply:
            raise ValueError(f"{text!r} is not a move's code, with perhaps a comment in braces after it")
        if turn == DARK or commented:
            words.append(f"{number}." if turn == DARK else f"{number}...")
        words.append(ply[1])
        if ply[2]:
            words.append(ply[2])
        commented = bool(ply[2])
        number += turn == LIGHT
        turn = other(turn)
    if note:
        if not NOTE.fullmatch(note):
            raise ValueError(f"{note!r} is not a comment: one line, without braces")
        words.append("{" + note + "}")
    words.append(result)
    movetext, line = [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > 79:
            movetext.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    movetext.append(line)
    return "\n".join(lines) + "\n\n" + "\n".join(movetext) + "\n"
