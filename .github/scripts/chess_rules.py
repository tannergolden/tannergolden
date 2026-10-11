#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of chess: positions, legal moves, their names, and how a game ends.

  from chess_rules import START, Position, legal_moves, make, san, ending

A position is the board, whose turn it is, the castling rights, the en
passant square and the two move clocks, read from and written as FEN. Every
legal move is generated, castling, en passant and promotion included, by
trying each piece's moves and keeping the ones that leave its own king safe;
the counts match the published perft numbers, which the tests hold it to.
Moves are written in UCI (e2e4, e7e8q) and named in SAN (e4, exd5, O-O,
e8=Q+, Qh4#).

A game ends when the rules end it, with nobody asking: checkmate, stalemate,
a fivefold repetition, seventy-five moves each with no capture and no pawn
moved, or too little material left for either side to mate. Those are the
draws FIDE makes automatic; the threefold repetition and the fifty-move rule
are only ever claimed, and nobody here claims. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass

FILES = "abcdefgh"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
PROMOTIONS = "qrbn"

KNIGHT = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAL = ((1, 1), (1, -1), (-1, 1), (-1, -1))
SLIDES = {"b": DIAGONAL, "r": ORTHOGONAL, "q": ORTHOGONAL + DIAGONAL}

# Moving from or onto one of these squares loses the castling rights named:
# the king's square both, a rook's corner its own side.
RIGHTS_LOST = {4: "KQ", 0: "Q", 7: "K", 60: "kq", 56: "q", 63: "k"}


class FenError(ValueError):
    """A FEN that does not describe a position."""


def square(label: str) -> int:
    """`e4` as an index from 0 (a1) to 63 (h8)."""
    return FILES.index(label[0]) + 8 * (int(label[1]) - 1)


def label(index: int) -> str:
    """The index's square, such as `e4`."""
    return FILES[index % 8] + str(index // 8 + 1)


def side(piece: str) -> str:
    """`w` for a white piece, `b` for a black one."""
    return "w" if piece.isupper() else "b"


def other(turn: str) -> str:
    return "b" if turn == "w" else "w"


def step(index: int, df: int, dr: int) -> int | None:
    """The square `df` files and `dr` ranks away, or None off the board."""
    f, r = index % 8 + df, index // 8 + dr
    return f + 8 * r if 0 <= f < 8 and 0 <= r < 8 else None


@dataclass(frozen=True)
class Move:
    start: int
    end: int
    promotion: str = ""  # q, r, b or n, for a pawn reaching the last rank

    @property
    def uci(self) -> str:
        return label(self.start) + label(self.end) + self.promotion

    @classmethod
    def from_uci(cls, text: str) -> Move:
        return cls(square(text[0:2]), square(text[2:4]), text[4:5])


@dataclass(frozen=True)
class Position:
    board: tuple[str, ...]  # 64 squares from a1 to h8: a piece letter, or "" when empty
    turn: str = "w"
    castling: str = "KQkq"  # the rights still held, "" for none
    ep: int | None = None  # the square a pawn just passed over, after a double step
    halfmove: int = 0  # plies since the last capture or pawn move
    fullmove: int = 1

    @classmethod
    def from_fen(cls, fen: str) -> Position:
        parts = fen.split()
        if len(parts) != 6:
            raise FenError(f"{fen!r} has {len(parts)} fields, not 6")
        placement, turn, castling, ep, halfmove, fullmove = parts
        ranks = placement.split("/")
        if len(ranks) != 8:
            raise FenError(f"{fen!r} has {len(ranks)} ranks, not 8")
        board = [""] * 64
        for row, text in enumerate(ranks):
            rank, f = 7 - row, 0
            for char in text:
                if char.isdigit():
                    f += int(char)
                elif char in "PNBRQKpnbrqk":
                    if f > 7:
                        raise FenError(f"rank {rank + 1} of {fen!r} is too long")
                    board[f + 8 * rank] = char
                    f += 1
                else:
                    raise FenError(f"{char!r} is not a piece")
            if f != 8:
                raise FenError(f"rank {rank + 1} of {fen!r} has {f} squares, not 8")
        if turn not in ("w", "b") or not halfmove.isdigit() or not fullmove.isdigit():
            raise FenError(f"{fen!r} has a malformed turn or clock")
        if castling != "-" and (not set(castling) <= set("KQkq") or len(set(castling)) != len(castling)):
            raise FenError(f"{castling!r} is not a set of castling rights")
        if ep != "-" and (len(ep) != 2 or ep[0] not in FILES or ep[1] != ("6" if turn == "w" else "3")):
            raise FenError(f"{ep!r} is not an en passant square with {turn} to move")
        if board.count("K") != 1 or board.count("k") != 1:
            raise FenError(f"{fen!r} does not have one king a side")
        return cls(tuple(board), turn, "" if castling == "-" else castling,
                   None if ep == "-" else square(ep), int(halfmove), int(fullmove))

    @property
    def fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            row, empty = "", 0
            for f in range(8):
                piece = self.board[f + 8 * rank]
                if piece:
                    row += (str(empty) if empty else "") + piece
                    empty = 0
                else:
                    empty += 1
            rows.append(row + (str(empty) if empty else ""))
        ep = label(self.ep) if self.ep is not None else "-"
        return f"{'/'.join(rows)} {self.turn} {self.castling or '-'} {ep} {self.halfmove} {self.fullmove}"


def king(position: Position, turn: str) -> int:
    return position.board.index("K" if turn == "w" else "k")


def attacked(board: tuple[str, ...], index: int, by: str) -> bool:
    """Whether a piece of `by` attacks the square."""
    def theirs(target: int | None, kinds: str) -> bool:
        if target is None:
            return False
        piece = board[target]
        return bool(piece) and side(piece) == by and piece.lower() in kinds

    behind = -1 if by == "w" else 1  # a pawn attacks forward, so look back along its way
    if any(theirs(step(index, df, behind), "p") for df in (-1, 1)):
        return True
    if any(theirs(step(index, df, dr), "n") for df, dr in KNIGHT):
        return True
    if any(theirs(step(index, df, dr), "k") for df, dr in KING):
        return True
    for directions, kinds in ((ORTHOGONAL, "rq"), (DIAGONAL, "bq")):
        for df, dr in directions:
            target = step(index, df, dr)
            while target is not None and not board[target]:
                target = step(target, df, dr)
            if theirs(target, kinds):
                return True
    return False


def in_check(position: Position) -> bool:
    return attacked(position.board, king(position, position.turn), other(position.turn))


def pseudo_moves(position: Position) -> list[Move]:
    """Every move the pieces can make, before asking whether it leaves its own king attacked."""
    board, turn, moves = position.board, position.turn, []
    forward, home, last = (1, 1, 7) if turn == "w" else (-1, 6, 0)

    def pawn_to(start: int, end: int) -> None:
        if end // 8 == last:
            moves.extend(Move(start, end, piece) for piece in PROMOTIONS)
        else:
            moves.append(Move(start, end))

    for start, piece in enumerate(board):
        if not piece or side(piece) != turn:
            continue
        kind = piece.lower()
        if kind == "p":
            one = step(start, 0, forward)
            if one is not None and not board[one]:
                pawn_to(start, one)
                two = step(one, 0, forward)
                if start // 8 == home and two is not None and not board[two]:
                    moves.append(Move(start, two))
            for df in (-1, 1):
                target = step(start, df, forward)
                if target is None:
                    continue
                if (board[target] and side(board[target]) != turn) or target == position.ep:
                    pawn_to(start, target)
        elif kind in "nk":
            for df, dr in KNIGHT if kind == "n" else KING:
                target = step(start, df, dr)
                if target is not None and (not board[target] or side(board[target]) != turn):
                    moves.append(Move(start, target))
        else:
            for df, dr in SLIDES[kind]:
                target = step(start, df, dr)
                while target is not None:
                    if board[target]:
                        if side(board[target]) != turn:
                            moves.append(Move(start, target))
                        break
                    moves.append(Move(start, target))
                    target = step(target, df, dr)
    moves.extend(castles(position))
    return moves


def castles(position: Position) -> list[Move]:
    """Castling: the right still held, the squares between empty, and the king never in, through or into check."""
    board, turn = position.board, position.turn
    rank = 0 if turn == "w" else 56
    rights = "".join(right.upper() for right in position.castling if (right.isupper()) == (turn == "w"))
    king_piece, rook_piece = ("K", "R") if turn == "w" else ("k", "r")
    if board[rank + 4] != king_piece:
        return []
    enemy, moves = other(turn), []
    for right, rook, between, crossed, end in (("K", 7, (5, 6), (4, 5, 6), 6), ("Q", 0, (1, 2, 3), (4, 3, 2), 2)):
        if right not in rights or board[rank + rook] != rook_piece:
            continue
        if any(board[rank + f] for f in between):
            continue
        if any(attacked(board, rank + f, enemy) for f in crossed):
            continue
        moves.append(Move(rank + 4, rank + end))
    return moves


def make(position: Position, move: Move) -> Position:
    """The position after the move, which is taken to be legal."""
    board = list(position.board)
    piece, captured = board[move.start], board[move.end]
    board[move.end], board[move.start] = piece, ""
    kind = piece.lower()
    if kind == "p" and move.end == position.ep and not captured:
        captured = board[move.end - 8 if position.turn == "w" else move.end + 8]
        board[move.end - 8 if position.turn == "w" else move.end + 8] = ""
    if move.promotion:
        board[move.end] = move.promotion.upper() if position.turn == "w" else move.promotion
    if kind == "k" and abs(move.end - move.start) == 2:
        rook_from, rook_to = (move.start + 3, move.start + 1) if move.end > move.start else (move.start - 4, move.start - 1)
        board[rook_to], board[rook_from] = board[rook_from], ""
    castling = position.castling
    for touched in (move.start, move.end):
        for right in RIGHTS_LOST.get(touched, ""):
            castling = castling.replace(right, "")
    ep = (move.start + move.end) // 2 if kind == "p" and abs(move.end - move.start) == 16 else None
    halfmove = 0 if kind == "p" or captured else position.halfmove + 1
    fullmove = position.fullmove + (position.turn == "b")
    return Position(tuple(board), other(position.turn), castling, ep, halfmove, fullmove)


def legal_moves(position: Position) -> list[Move]:
    turn = position.turn
    legal = []
    for move in pseudo_moves(position):
        after = make(position, move)
        if not attacked(after.board, king(after, turn), other(turn)):
            legal.append(move)
    return legal


def perft(position: Position, depth: int) -> int:
    """How many move sequences of this length the position has: the standard check of a move generator."""
    moves = legal_moves(position)
    if depth <= 1:
        return len(moves) if depth == 1 else 1
    return sum(perft(make(position, move), depth - 1) for move in moves)


def san(position: Position, move: Move, legal: list[Move] | None = None, replies: list[Move] | None = None) -> str:
    """The move's name in standard algebraic notation, with + for check and # for mate. `legal` and `replies`, the
    position's legal moves and the other side's after this one, save working them out again when they are known."""
    legal = legal_moves(position) if legal is None else legal
    piece = position.board[move.start]
    kind = piece.lower()
    if kind == "k" and abs(move.end - move.start) == 2:
        name = "O-O" if move.end > move.start else "O-O-O"
    elif kind == "p":
        capture = move.start % 8 != move.end % 8
        name = (FILES[move.start % 8] + "x" if capture else "") + label(move.end)
        name += "=" + move.promotion.upper() if move.promotion else ""
    else:
        rivals = [other_move for other_move in legal
                  if other_move.end == move.end and other_move.start != move.start
                  and position.board[other_move.start] == piece]
        which = ""
        if rivals:
            if all(rival.start % 8 != move.start % 8 for rival in rivals):
                which = FILES[move.start % 8]
            elif all(rival.start // 8 != move.start // 8 for rival in rivals):
                which = str(move.start // 8 + 1)
            else:
                which = label(move.start)
        name = kind.upper() + which + ("x" if position.board[move.end] else "") + label(move.end)
    after = make(position, move)
    if in_check(after):
        name += "#" if not (legal_moves(after) if replies is None else replies) else "+"
    return name


def repetition_key(position: Position) -> tuple:
    """What makes two positions the same for a repetition: the pieces, the turn, the rights, and an en passant
    capture only when one could actually be made."""
    ep = position.ep
    if ep is not None and not any(move.end == ep and position.board[move.start].lower() == "p"
                                  for move in legal_moves(position)):
        ep = None
    return position.board, position.turn, position.castling, ep


def insufficient(position: Position) -> bool:
    """Too little left for either side ever to mate: kings alone, a king and one minor piece against a king, or
    kings and bishops that all stand on squares of one colour."""
    rest = [(index, piece) for index, piece in enumerate(position.board) if piece and piece.lower() != "k"]
    if not rest:
        return True
    if len(rest) == 1 and rest[0][1].lower() in "bn":
        return True
    if all(piece.lower() == "b" for _, piece in rest):
        return len({(index % 8 + index // 8) % 2 for index, _ in rest}) == 1
    return False


@dataclass(frozen=True)
class Ending:
    reason: str  # checkmate, stalemate, fivefold repetition, seventy-five-move rule, insufficient material
    winner: str | None  # w or b for a checkmate, None for a draw

    @property
    def result(self) -> str:
        return {"w": "1-0", "b": "0-1"}.get(self.winner or "", "1/2-1/2")


def ending(history: list[Position]) -> Ending | None:
    """How the game ends at its last position, if it does. `history` runs from the first position to the last."""
    position = history[-1]
    if not legal_moves(position):
        return Ending("checkmate", other(position.turn)) if in_check(position) else Ending("stalemate", None)
    if insufficient(position):
        return Ending("insufficient material", None)
    if position.halfmove >= 150:
        return Ending("seventy-five-move rule", None)
    key = repetition_key(position)
    if sum(repetition_key(earlier) == key for earlier in history) >= 5:
        return Ending("fivefold repetition", None)
    return None
