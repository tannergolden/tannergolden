#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: an emoji, a title, and what the move does in plain English.

  from chess_names import listing, words

Every title is an order to an army, in chess's own words: "Fork King and
Rook!", "Pin the Knight to the King!", "Castle Short!", "Push the Passed
Pawn!". The army's voice stays wherever its word is a true chess idea
("Muster the Knights!", "Invade the Seventh Rank!", "Seize the Open File!"),
and never where it would hide what the move does: a knight sent to the rim
says so, a quiet move is never an attack, and a move that loses is never
praised.

`survey` reads the whole board once: every move, where it leads and what
the other side can answer, whether that answer mates, what each move wins
or gives away in the exchanges that follow, and whether the other side
threatens mate. `read` then takes one move apart: a mate, and which kind; a
stalemate; an opening the books name; a promotion or a castle; double and
discovered checks; a fork, a skewer or a pin; a capture that wins material,
trades, wins it back, or gives it up; a check; a threat of mate, or of a
piece; a piece saved or guarded; a pawn offered; an outpost, development,
the centre, a fianchetto; a passed pawn pushed, luft for the king, the king
brought up or taking the opposition in an endgame; a rook on the seventh
rank, on an open file or behind its passed pawn, a battery, the rooks
connected or lifted; and where any other move goes. The most telling of
those is the move's theme.

Some moves are judged against the others on the board, where the board can
know it: the only legal move, and the only move that stops a mate in one,
are named as such; a move that allows mate in one where another move would
not, or loses material in the exchanges that follow (the static exchange,
one move deep) where another would keep it, gets a warning and says what it
loses; a sacrifice says what it gives up.

A theme gives the emoji, one to a theme so the emoji down the list read as
a key, and the titles: tiers of true synonyms, from the plainest to the most
exact. Every move takes its plainest tier, and moves that would read alike
(two knights developing, two moves that both fork the king and rook) each
step up a tier until the titles name what tells them apart: which knight,
which file, which target, which square. A hash of the position and the move
picks among the synonyms of a tier, so the same position names its moves
the same way whatever game or move number it comes up in, and no two moves
on one board share a title. Stdlib only, with chess_rules.py beside it.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass

from chess_rules import (
    DIAGONAL,
    FILES,
    KING,
    KNIGHT,
    ORTHOGONAL,
    START,
    Move,
    Position,
    attacked,
    in_check,
    insufficient,
    king,
    label,
    legal_moves,
    make,
    other,
    pseudo_moves,
    san,
    side,
    step,
)

PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100}
ORDER = "kqrbnp"  # the list's order: the king's moves first, the pawns' last
CENTRE = frozenset((27, 28, 35, 36))  # d4, e4, d5 and e5
LINES = {"b": DIAGONAL, "r": ORTHOGONAL, "q": ORTHOGONAL + DIAGONAL}
MINORS = {"w": {1: "n", 6: "n", 2: "b", 5: "b"}, "b": {57: "n", 62: "n", 58: "b", 61: "b"}}  # each minor's home
FIANCHETTO = {"w": {9: 2, 14: 5}, "b": {49: 58, 54: 61}}  # b2 and g2 (b7, g7), each with its bishop's home
TARGET_F7 = {"w": 53, "b": 13}  # f7 and f2, each side's square next to its king that only the king guards
ENDGAME = 13  # a side with no more than a rook and a minor piece (or a queen and a minor) in front of its pawns
LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
# The words of command a title opens with: every one an order a commander gives, in chess's own words.
COMMANDS = frozenset("""
    Accept Activate Advance Aim Answer Attack Back Bail Block Break Bring Build Capture Castle Centralise Challenge
    Chase Check Checkmate Command Connect Cover Crown Decline Defend Deliver Develop Discover Double Drop End Escape
    Exchange Fall Fianchetto Fight Find Force Forfeit Fork Free Freeze Gain Gambit Get Give Go Grab Guard Hang
    Harass Hide Hit Invade Kick Launch Leave Let Level Lift Line Link Make March Mate Meet Move Muster Nail Nudge
    Occupy Offer Open Park Parry Pin Plant Play Post Prepare Promote Protect Pull Push Put Queen Question Redeploy
    Regroup Remove Rescue Restore Retreat Roll Rule Run Sacrifice Save Seize Send Set Settle Shield Shift Sidestep
    Skewer Smother Snap Stack Stake Stalemate Step Stop Storm Strike Support Swap Sweep Swing Take Threaten Throw
    Trade Train Tuck Underpromote Unleash Unmask Walk Win
""".split())

# The openings the books name, each by the moves that reach it: a move that reaches the position, by any order of
# moves, is named for it. The names are the ones every opening book uses, and only the well-known.
BOOK_LINES = (
    ("e2e4", ("Open With the King's Pawn!", "Seize the Centre With the King's Pawn!")),
    ("d2d4", ("Open With the Queen's Pawn!", "Seize the Centre With the Queen's Pawn!")),
    ("c2c4", ("Play the English!", "Open With the English!")),
    ("f2f4", ("Play Bird's Opening!",)),
    ("b2b4", ("Play the Polish Opening!",)),
    ("g2g4", ("Launch Grob's Attack!", "Play Grob's Attack!")),
    ("b2b3", ("Play the Nimzo-Larsen Attack!",)),
    ("e2e4 e7e5", ("Play the Open Game!", "Meet the King's Pawn Head-On!")),
    ("e2e4 c7c5", ("Play the Sicilian!", "Answer With the Sicilian!", "Fight Back With the Sicilian!")),
    ("e2e4 e7e6", ("Play the French!", "Answer With the French Defence!")),
    ("e2e4 c7c6", ("Play the Caro-Kann!", "Answer With the Caro-Kann!")),
    ("e2e4 d7d5", ("Play the Scandinavian!", "Strike Back With the Scandinavian!")),
    ("e2e4 g8f6", ("Play Alekhine's Defence!",)),
    ("e2e4 d7d6", ("Play the Pirc!", "Answer With the Pirc Defence!")),
    ("e2e4 g7g6", ("Play the Modern Defence!",)),
    ("d2d4 d7d5", ("Play the Closed Game!", "Meet the Queen's Pawn Head-On!")),
    ("d2d4 g8f6", ("Play an Indian Defence!", "Answer With an Indian Defence!")),
    ("d2d4 f7f5", ("Play the Dutch!", "Answer With the Dutch Defence!")),
    ("d2d4 c7c5", ("Play the Old Benoni!",)),
    ("d2d4 e7e5", ("Offer the Englund Gambit!",)),
    ("f2f4 e7e5", ("Offer From's Gambit!",)),
    ("c2c4 e7e5", ("Play the Reversed Sicilian!",)),
    ("c2c4 c7c5", ("Play the Symmetrical English!",)),
    ("e2e4 e7e5 f2f4", ("Offer the King's Gambit!", "Play the King's Gambit!")),
    ("e2e4 e7e5 b1c3", ("Play the Vienna!", "Play the Vienna Game!")),
    ("e2e4 e7e5 f1c4", ("Play the Bishop's Opening!",)),
    ("e2e4 e7e5 d2d4", ("Play the Centre Game!",)),
    ("e2e4 e7e5 d1h5", ("Play the Wayward Queen Attack!",)),
    ("e2e4 c7c5 c2c3", ("Play the Alapin!", "Play the Alapin Sicilian!")),
    ("e2e4 c7c5 b1c3", ("Play the Closed Sicilian!",)),
    ("e2e4 c7c5 b2b4", ("Offer the Wing Gambit!",)),
    ("e2e4 c7c5 d2d4 c5d4 c2c3", ("Offer the Smith-Morra Gambit!",)),
    ("e2e4 c7c5 g1f3 d7d6 d2d4", ("Open the Sicilian!", "Break Open the Sicilian!")),
    ("e2e4 c7c5 g1f3 b8c6 d2d4", ("Open the Sicilian!", "Break Open the Sicilian!")),
    ("e2e4 c7c5 g1f3 e7e6 d2d4", ("Open the Sicilian!", "Break Open the Sicilian!")),
    ("e2e4 c7c5 g1f3 b8c6 f1b5", ("Play the Rossolimo!",)),
    ("e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6", ("Play the Najdorf!",)),
    ("e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6", ("Unleash the Dragon!", "Play the Dragon!")),
    ("e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 e7e6", ("Play the Scheveningen!",)),
    ("e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 b8c6", ("Play the Classical Sicilian!",)),
    ("e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4 g8f6 b1c3 e7e5", ("Play the Sveshnikov!",)),
    ("e2e4 e7e6 d2d4 d7d5 e4e5", ("Play the Advance French!",)),
    ("e2e4 e7e6 d2d4 d7d5 b1d2", ("Play the Tarrasch French!",)),
    ("e2e4 e7e6 d2d4 d7d5 e4d5", ("Play the Exchange French!",)),
    ("e2e4 c7c6 d2d4 d7d5 e4e5", ("Play the Advance Caro-Kann!",)),
    ("d2d4 d7d5 c2c4", ("Offer the Queen's Gambit!", "Play the Queen's Gambit!")),
    ("d2d4 d7d5 c1f4", ("Play the London System!",)),
    ("d2d4 g8f6 c1f4", ("Play the London System!",)),
    ("d2d4 d7d5 e2e4", ("Offer the Blackmar-Diemer Gambit!",)),
    ("d2d4 g8f6 c1g5", ("Play the Trompowsky!",)),
    ("d2d4 f7f5 e2e4", ("Offer the Staunton Gambit!",)),
    ("d2d4 d7d5 c2c4 e7e6", ("Decline the Queen's Gambit!",)),
    ("d2d4 d7d5 c2c4 d5c4", ("Accept the Queen's Gambit!",)),
    ("d2d4 d7d5 c2c4 c7c6", ("Play the Slav!", "Play the Slav Defence!")),
    ("d2d4 d7d5 c2c4 b8c6", ("Play the Chigorin!", "Play the Chigorin Defence!")),
    ("d2d4 d7d5 c2c4 e7e5", ("Play the Albin Countergambit!",)),
    ("d2d4 g8f6 c2c4 e7e5", ("Offer the Budapest Gambit!",)),
    ("d2d4 g8f6 c2c4 c7c5 d4d5 b7b5", ("Offer the Benko Gambit!",)),
    ("d2d4 g8f6 c2c4 c7c5 d4d5 e7e6", ("Play the Modern Benoni!",)),
    ("d2d4 g8f6 c2c4 e7e6 b1c3 f8b4", ("Play the Nimzo-Indian!",)),
    ("d2d4 g8f6 c2c4 e7e6 g1f3 b7b6", ("Play the Queen's Indian!",)),
    ("d2d4 g8f6 c2c4 e7e6 g1f3 f8b4", ("Play the Bogo-Indian!",)),
    ("d2d4 g8f6 c2c4 e7e6 g2g3", ("Play the Catalan!",)),
    ("d2d4 g8f6 c2c4 g7g6 b1c3 f8g7", ("Play the King's Indian!",)),
    ("d2d4 g8f6 c2c4 g7g6 b1c3 d7d5", ("Play the Grunfeld!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1b5", ("Play the Ruy Lopez!", "Play the Spanish Game!")),
    ("e2e4 e7e5 g1f3 b8c6 f1c4", ("Play the Italian!", "Play the Italian Game!")),
    ("e2e4 e7e5 g1f3 b8c6 d2d4", ("Play the Scotch!", "Play the Scotch Game!")),
    ("e2e4 e7e5 g1f3 b8c6 b1c3", ("Play the Three Knights!",)),
    ("e2e4 e7e5 g1f3 b8c6 c2c3", ("Play the Ponziani!",)),
    ("e2e4 e7e5 g1f3 b8c6 b1c3 g8f6", ("Play the Four Knights!",)),
    ("e2e4 e7e5 g1f3 d7d6", ("Play the Philidor!", "Play Philidor's Defence!")),
    ("e2e4 e7e5 g1f3 g8f6", ("Play the Petrov!", "Play the Petrov Defence!")),
    ("e2e4 e7e5 f2f4 e5f4", ("Accept the King's Gambit!",)),
    ("e2e4 e7e5 f2f4 d7d5", ("Play the Falkbeer Countergambit!",)),
    ("e2e4 e7e5 f2f4 f8c5", ("Decline the King's Gambit!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 a7a6", ("Play the Morphy Defence!", "Question the Bishop!")),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 g8f6", ("Play the Berlin!", "Play the Berlin Defence!")),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 f7f5", ("Play the Schliemann!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 f8c5", ("Play the Classical Defence!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 d7d6", ("Play the Steinitz Defence!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1b5 c6d4", ("Play Bird's Defence!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 f8c5", ("Play the Giuoco Piano!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6", ("Play the Two Knights!", "Play the Two Knights Defence!")),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 f8e7", ("Play the Hungarian Defence!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 b2b4", ("Offer the Evans Gambit!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5", ("Play the Knight Attack!",)),
    ("e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f7", ("Go for the Fried Liver!",)),
)
# The two mates every beginner is taught, by the moves that reach them.
FOOLS_LINES = ("f2f3 e7e5 g2g4 d8h4", "f2f4 e7e5 g2g4 d8h4", "f2f3 e7e6 g2g4 d8h4", "f2f4 e7e6 g2g4 d8h4")


def placement(position: Position) -> str:
    """The pieces and whose turn it is: what makes an opening the same however its moves came."""
    return " ".join(position.fen.split()[:2])


def replayed(line: str) -> Position:
    position = Position.from_fen(START)
    for uci in line.split():
        position = make(position, Move.from_uci(uci))
    return position


BOOK = {placement(replayed(line)): titles for line, titles in BOOK_LINES}
FOOLS = frozenset(replayed(line).board for line in FOOLS_LINES)


# --- the board as a chess player reads it ---------------------------------------------------------------------------

def rank_of(index: int, turn: str) -> int:
    """The square's rank as `turn` counts it, from 0 for its own back rank to 7 for the other side's."""
    return index // 8 if turn == "w" else 7 - index // 8


def name(kind: str) -> str:
    return PIECES[kind].capitalize()


def reach(board: tuple[str, ...], index: int) -> list[int]:
    """The squares the piece on `index` attacks."""
    piece = board[index]
    kind, forward = piece.lower(), 1 if side(piece) == "w" else -1
    if kind == "p":
        return [t for t in (step(index, -1, forward), step(index, 1, forward)) if t is not None]
    if kind in "nk":
        return [t for df, dr in (KNIGHT if kind == "n" else KING) if (t := step(index, df, dr)) is not None]
    out = []
    for df, dr in LINES[kind]:
        target = step(index, df, dr)
        while target is not None:
            out.append(target)
            if board[target]:
                break
            target = step(target, df, dr)
    return out


def attackers(board, index: int, by: str) -> list[int]:
    """The squares of `by`'s pieces that attack the square."""
    found = []

    def theirs(target: int | None, kinds: str) -> None:
        if target is not None and board[target] and side(board[target]) == by and board[target].lower() in kinds:
            found.append(target)

    behind = -1 if by == "w" else 1  # a pawn attacks forward, so look back along its way
    for df in (-1, 1):
        theirs(step(index, df, behind), "p")
    for df, dr in KNIGHT:
        theirs(step(index, df, dr), "n")
    for df, dr in KING:
        theirs(step(index, df, dr), "k")
    for directions, kinds in ((ORTHOGONAL, "rq"), (DIAGONAL, "bq")):
        for df, dr in directions:
            target = step(index, df, dr)
            while target is not None and not board[target]:
                target = step(target, df, dr)
            theirs(target, kinds)
    return found


def along(board, index: int, df: int, dr: int) -> list[int]:
    """The occupied squares on the line from `index`, nearest first."""
    out, target = [], step(index, df, dr)
    while target is not None:
        if board[target]:
            out.append(target)
        target = step(target, df, dr)
    return out


def see(board, start: int, end: int, passing: bool = False) -> int:
    """What the side moving from `start` to `end` comes out with in material once both sides have taken on `end` in
    turn, each with its cheapest piece, either side stopping when taking again would lose: the static exchange. A
    move to an empty square gains nothing first, so a result below zero means the piece is lost there."""
    squares = list(board)
    mover = side(squares[start])
    gains = [0]
    if passing:
        squares[end - 8 if mover == "w" else end + 8] = ""
        gains = [VALUE["p"]]
    elif squares[end]:
        gains = [VALUE[squares[end].lower()]]
    standing = VALUE[squares[start].lower()]
    squares[end], squares[start] = squares[start], ""
    turn = other(mover)
    while True:
        found = attackers(squares, end, turn)
        if not found:
            break
        taker = min(found, key=lambda i: VALUE[squares[i].lower()])
        if squares[taker].lower() == "k":  # a king takes only where nothing can take it back
            trial = squares[:]
            trial[end], trial[taker] = trial[taker], ""
            if attackers(trial, end, other(turn)):
                break
        gains.append(standing - gains[-1])
        standing = VALUE[squares[taker].lower()]
        squares[end], squares[taker] = squares[taker], ""
        turn = other(turn)
    for i in range(len(gains) - 1, 0, -1):
        gains[i - 1] = -max(-gains[i - 1], gains[i])
    return gains[0]


def winnable(board, index: int, by: str) -> bool:
    """Whether `by` could already take the piece on the square for a profit: a threat against it is nothing new."""
    return any(see(board, a, index) > 0 for a in attackers(board, index, by))


def victim(position: Position, move: Move) -> int | None:
    """The square of the piece the move takes (for en passant, the pawn that passed), or None."""
    if position.board[move.end]:
        return move.end
    if position.board[move.start].lower() == "p" and move.end == position.ep:
        return move.end - 8 if position.turn == "w" else move.end + 8
    return None


def won(position: Position, move: Move) -> int:
    """What a move wins in the exchanges on the square it takes on, a promotion's new piece included."""
    gain = see(position.board, move.start, move.end, victim(position, move) not in (None, move.end))
    if move.promotion:
        gain += VALUE[move.promotion] - VALUE["p"]
        if attackers(position.board, move.end, other(position.turn)):  # the new piece is taken where it stands
            gain -= VALUE[move.promotion] - VALUE["p"]
    return gain


def has_legal(position: Position) -> bool:
    """Whether the side to move has a legal move, trying the king's first and stopping at the first that is."""
    turn = position.turn
    home = king(position, turn)
    for move in sorted(pseudo_moves(position), key=lambda m: m.start != home):
        after = make(position, move)
        if not attacked(after.board, king(after, turn), other(turn)):
            return True
    return False


def gives_check(position: Position, move: Move) -> bool:
    """Whether the move checks the other king: from the square it lands on, or along a line it opens."""
    board, turn = position.board, position.turn
    kind = board[move.start].lower()
    if (kind == "k" and abs(move.end - move.start) == 2) or (kind == "p" and move.end == position.ep):
        return in_check(make(position, move))  # castling and en passant move two pieces at once
    target = board.index("k" if turn == "w" else "K")
    squares = list(board)
    squares[move.start] = ""
    squares[move.end] = (move.promotion.upper() if turn == "w" else move.promotion) if move.promotion else \
        board[move.start]
    if target in reach(squares, move.end):
        return True
    df, dr = (move.start % 8 > target % 8) - (move.start % 8 < target % 8), \
        (move.start // 8 > target // 8) - (move.start // 8 < target // 8)
    if not (move.start % 8 == target % 8 or move.start // 8 == target // 8
            or abs(move.start % 8 - target % 8) == abs(move.start // 8 - target // 8)):
        return False
    found = along(squares, target, df, dr)
    if not found:
        return False
    piece = squares[found[0]]
    sliders = "bq" if df and dr else "rq"
    return side(piece) == turn and piece.lower() in sliders


def mating(position: Position, moves: list[Move]) -> Move | None:
    """The first of `moves` that mates, or None."""
    return next(iter(mates(position, moves, first=True)), None)


def mates(position: Position, moves: list[Move], first: bool = False, legal: bool = True) -> list[Move]:
    """The moves among `moves` that mate, stopping at the first when `first`. With `legal` false the moves may leave
    their own king in check, and those are passed over."""
    found = []
    for move in moves:
        if not gives_check(position, move):
            continue
        after = make(position, move)
        if not legal and attacked(after.board, king(after, position.turn), other(position.turn)):
            continue
        if not has_legal(after):
            found.append(move)
            if first:
                break
    return found


def skipped(position: Position) -> Position:
    """The board with the other side to move, as if a move were passed: what a side threatens is what it could do
    if it were its turn again."""
    return Position(position.board, other(position.turn), position.castling, None, position.halfmove,
                    position.fullmove)


def material(board, turn: str) -> int:
    """What `turn`'s pieces are worth beyond the other side's."""
    return sum(VALUE[p.lower()] * (1 if side(p) == turn else -1) for p in board if p and p.lower() != "k")


def officers(board, turn: str) -> int:
    """What `turn`'s pieces other than its king and pawns are worth."""
    return sum(VALUE[p.lower()] for p in board if p and side(p) == turn and p.lower() in "nbrq")


def to_centre(index: int) -> int:
    """How many king steps the square is from the nearest of the four centre squares."""
    f, r = index % 8, index // 8
    return max(max(3 - f, f - 4, 0), max(3 - r, r - 4, 0))


def fen4(position: Position) -> str:
    """The position as the rules count it the same: the pieces, the turn, the castling rights, and the en passant
    square only when a pawn can take there. The clocks are left out, so a position names its moves the same way
    whenever it comes up."""
    placement_, turn, castling, ep = position.fen.split()[:4]
    if ep != "-" and not any(move.end == position.ep and position.board[move.start].lower() == "p"
                             for move in legal_moves(position)):
        ep = "-"
    return f"{placement_} {turn} {castling} {ep}"


@dataclass(frozen=True)
class Board:
    """What a board says about every move on it, worked out once."""
    position: Position
    moves: tuple[Move, ...]
    after: dict
    replies: dict
    checked: bool  # the side to move is in check
    threat: bool  # the other side would mate in one if this side passed
    allows: dict  # for each move, the other side's mate in one it allows, or None
    net: dict  # for each move, what it wins, less what the other side can then win by taking
    lost: dict  # for each move, the square of the piece the other side's best capture takes, or None
    best: int  # the most any move nets that does not allow mate
    endgame: bool
    mating: frozenset  # the mates in one on the board, each as the piece that mates and its square
    danger: frozenset  # the squares of this side's pieces the other side could take for a profit


@functools.lru_cache(maxsize=256)
def survey(key: str) -> Board:
    """The board at `key` (a position without its clocks), every move on it played out one move deep."""
    position = Position.from_fen(key + " 0 1")
    moves = tuple(legal_moves(position))
    after = {move: make(position, move) for move in moves}
    replies = {move: legal_moves(after[move]) for move in moves}
    checked = in_check(position)
    threat = False
    if not checked:
        passed = skipped(position)
        threat = bool(mates(passed, pseudo_moves(passed), first=True, legal=False))
    allows = {move: mating(after[move], replies[move]) for move in moves}
    net, lost = {}, {}
    for move in moves:
        here, gain, square = after[move], 0, None
        captures = sorted(((won(here, r), r) for r in replies[move] if victim(here, r) is not None or r.promotion),
                          key=lambda pair: -pair[0])
        for value, reply in captures:
            if value <= 0:
                break
            then = make(here, reply)
            if value >= 2 and mating(then, legal_moves(then)):
                continue  # taking walks into mate, so it is no gain
            gain, square = value, victim(here, reply) if victim(here, reply) is not None else reply.end
            break
        taken = victim(position, move)
        immediate = (VALUE[position.board[taken].lower()] if taken is not None else 0) + \
            (VALUE[move.promotion] - VALUE["p"] if move.promotion else 0)
        net[move], lost[move] = immediate - gain, square
    safe = [net[move] for move in moves if not allows[move]] or list(net.values()) or [0]
    mating_now = frozenset((position.board[m.start].lower(), m.end) for m in moves
                           if not replies[m] and in_check(after[m]))
    enemy = other(position.turn)
    danger = frozenset(i for i, piece in enumerate(position.board) if piece and side(piece) == position.turn
                       and piece.lower() != "k"
                       and any(see(position.board, a, i) > 0 for a in attackers(position.board, i, enemy)))
    return Board(position, moves, after, replies, checked, threat, allows, net, lost, max(safe),
                 max(officers(position.board, "w"), officers(position.board, "b")) <= ENDGAME, mating_now, danger)


@dataclass(frozen=True)
class Reading:
    """What one move does, as a name reads it."""
    kind: str  # the piece that moves: p, n, b, r, q or k
    start: int
    end: int
    turn: str  # w or b
    taken: str = ""  # the kind it takes
    passing: bool = False  # it takes en passant
    castle: str = ""  # "king" or "queen", the side it castles to
    crown: str = ""  # what a pawn becomes on the last rank
    check: bool = False
    double: bool = False  # two pieces give check at once
    discovered: bool = False  # the check comes from a piece the move uncovered
    revealed: str = ""  # the kind of the piece whose check or attack the move uncovered
    checkers: tuple[str, ...] = ()  # the kinds giving check
    mate: bool = False
    mate_kind: str = ""  # "fool", "scholar", "smothered" or "back-rank", for the mates with a name
    stalemate: bool = False
    only: bool = False  # the only legal move
    evade: str = ""  # out of check: "king", "king-take" (the king takes the checker), "capture" or "block"
    allows: str = ""  # the blunder of allowing mate in one: "mate", or "fool" for Fool's Mate
    stops: str = ""  # the move stops a mate in one: "only" when nothing else does, "yes" when others do too
    blunder: str = ""  # material dropped where another move keeps it: "hang" the moved piece, "drop" another
    lost: str = ""  # the kind of the piece a blunder or sacrifice loses, or "promotion" for a pawn let through
    sacrifice: bool = False  # it gives up the moved piece, for a check, a threat or a capture
    greek: bool = False  # the bishop's sacrifice on h7 (h2) with check, against a king on g8 (g1)
    book: tuple[str, ...] = ()  # the opening's names, when the move reaches a position the books name
    see: int = 0  # what the exchange on its square comes to
    net: int = 0  # what the move wins, less what the other side can then win by taking
    free: bool = False  # what it takes cannot be taken back
    level: bool = False  # the capture wins back material the side was down
    dead: str = ""  # the capture leaves too little on the board for either side to mate: "thrown" when another
    # move would have won material instead, "saving" when the side was behind, "even" otherwise
    fork: tuple[str, ...] = ()  # the pieces it attacks at once, most valuable first
    skewer: tuple[str, ...] = ()  # the piece it attacks and the one behind it, worth less
    pin: tuple[str, ...] = ()  # the piece it pins and what that piece shields
    unmasked: str = ""  # the piece a discovered attack hits
    mate_threat: str = ""  # the square it threatens mate on
    threat: str = ""  # the piece worth having that it newly attacks
    threat_square: int = -1
    escaped: bool = False  # it was in danger where it stood, and is not where it lands
    guarded: str = ""  # a piece of its own that was in danger, and is not once it moves
    guard: str = ""  # how: "defend" or "block"
    offer: bool = False  # a pawn pushed where it can be taken for nothing
    outpost: bool = False  # a knight or bishop in the other half where no pawn of theirs can ever attack it
    backed: bool = False  # and a pawn of its own guards it there
    first: bool = False  # a knight or bishop leaves its home square
    rim: bool = False  # a knight to the a- or h-file
    fianchetto: bool = False
    aims_f7: bool = False  # a bishop that now bears on f7 (f2), with the pawn still on it
    toward: bool = False  # a knight that now covers a centre square
    centre: bool = False  # it lands on d4, e4, d5 or e5
    passed: bool = False  # a pawn with no pawn of the other side ahead of it, on its file or beside it
    seventh: bool = False  # a rook or queen entering the other side's second rank
    luft: bool = False  # a pawn step that gives the castled king a square off the back rank
    frees: str = ""  # the piece a pawn move opens a line for: "b" for a bishop, "q" for the queen
    frees_square: int = -1  # where the piece it frees stands
    prepares: str = ""  # "Kingside" or "Queenside", the fianchetto a pawn step makes room for
    covers: int = -1  # the square a pawn newly guards, a centre square first
    space: bool = False  # a pawn into the other half
    two: bool = False  # a pawn's two-square step
    forfeit: bool = False  # a king move that gives up castling
    gives_up: str = ""  # a rook leaving its corner gives up castling on that side: "Short" or "Long"
    opposition: bool = False  # in a pawn ending, the kings face each other one square apart, the other side to move
    behind_passer: str = ""  # a rook to the file of its own passed pawn, behind it: the pawn's file
    endgame: bool = False
    corner: bool = False  # the king tucked into a corner
    open_file: str = ""  # a rook to an "open" or "half-open" file
    battery: str = ""  # the piece it lines up with: "q", "b" or "r"
    battery_line: str = ""  # "file", "rank" or "diagonal"
    battery_king: bool = False  # the battery points at the other king or a square next to it
    connects: bool = False  # the two rooks see each other on the back rank, and did not before
    lift: bool = False  # a rook straight up from the back rank to the third or fourth rank
    early: bool = False  # the queen's first move while most of the minor pieces are still at home
    long_diagonal: bool = False  # a bishop on a long diagonal with a clear view along it
    aims_king: bool = False  # a bishop, rook or queen now on a line with the other king
    invades: bool = False  # a piece crossing into the other half
    promote_next: bool = False  # a pawn on the seventh that can queen on its next move
    forced_king: bool = False  # a check only a king move answers
    hits: str = ""  # the most valuable piece of theirs the moved piece attacks, for a discovered check
    ahead: int = 0  # what the side's material is worth beyond the other side's, before the move
    guarded_square: int = -1
    advance: int = 0  # ranks gained toward the other side, negative for a retreat
    distance: int = 0  # squares travelled, the longer way
    sideways: int = 0  # files crossed


def read(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> Reading:
    """What the move does: every trait a name can be made from. `after` and `replies` are accepted for the callers
    that know them; the board's survey has them already."""
    return reading(fen4(position), move)


@functools.lru_cache(maxsize=4096)
def reading(key: str, move: Move) -> Reading:
    """The move read on the board at `key`, worked out once."""
    board_ = survey(key)
    position = board_.position  # the same position, without its clocks, which no reading depends on
    board, turn = position.board, position.turn
    enemy = other(turn)
    after = board_.after[move]
    replies = board_.replies[move]
    now = after.board
    kind = board[move.start].lower()
    mover = now[move.end].lower()  # what stands on the square after: the new piece, for a promotion
    taken_at = victim(position, move)
    passing = taken_at is not None and taken_at != move.end
    taken = board[taken_at].lower() if taken_at is not None else ""
    castle = "" if kind != "k" or abs(move.end - move.start) != 2 else ("king" if move.end > move.start else "queen")
    rook_to = (move.start + 1 if castle == "king" else move.start - 1) if castle else move.end
    check = in_check(after)
    mate = check and not replies
    their_king = king(after, enemy)
    checking = [i for i, piece in enumerate(now) if piece and side(piece) == turn and their_king in reach(now, i)]
    direct = rook_to in checking
    revealed = next((now[i].lower() for i in checking if i != rook_to), "") if check else ""
    exchange = see(board, move.start, move.end, passing) if not castle else 0
    traits: dict = {}

    # what the move gives away, judged against the other moves on the board
    allowing = board_.allows[move]
    if allowing is not None and not mate and any(board_.allows[m] is None for m in board_.moves):
        traits["allows"] = "fool" if make(after, allowing).board in FOOLS else "mate"
    keeping = [m for m in board_.moves if board_.allows[m] is None]
    if any(board_.allows[m] is not None for m in board_.moves) and keeping == [move]:
        traits["stops"] = "only"
    elif board_.threat and allowing is None and any(board_.allows[m] is not None for m in board_.moves):
        traits["stops"] = "yes"
    lost_at = board_.lost[move]
    net = board_.net[move]

    # a mate, and which kind
    mate_kind = ""
    if mate:
        neighbours = [t for df, dr in KING if (t := step(their_king, df, dr)) is not None]
        in_front = [t for t in neighbours if rank_of(t, enemy) == 1]
        if now in FOOLS:
            mate_kind = "fool"
        elif (mover == "q" and taken == "p" and move.end == TARGET_F7[turn] and their_king == (60 if turn == "w" else 4)
              and any(now[i].lower() == "b" and side(now[i]) == turn and move.end in reach(now, i) for i in range(64)
                      if now[i]) and sum(1 for piece in now if piece) >= 28):
            mate_kind = "scholar"
        elif move.promotion:
            mate_kind = ""  # a promotion that mates is named for the piece it makes
        elif mover == "n" and all(now[t] and side(now[t]) == enemy for t in neighbours):
            mate_kind = "smothered"
        elif (mover in "rq" and direct and rank_of(their_king, enemy) == 0 and move.end // 8 == their_king // 8
              and all(now[t] and side(now[t]) == enemy for t in in_front)):
            mate_kind = "back-rank"

    # what lands where: forks, skewers and pins, threats, and whether the piece is safe there
    safe = not castle and not any(victim(after, r) == move.end and won(after, r) > 0 for r in replies)
    targets = []
    if not castle:
        for target in reach(now, move.end):
            piece = now[target]
            if not piece or side(piece) != enemy or piece.lower() == "p":
                continue
            k = piece.lower()
            if k == "k" or VALUE[k] > VALUE[mover] or not attackers(now, target, enemy):
                targets.append(k)
    fork = tuple(sorted(targets, key=ORDER.index)) if len(targets) > 1 and safe else ()
    pin, skewer = (), ()
    if mover in LINES and safe and not castle:
        before_pins = set()
        if kind in LINES:
            for df, dr in LINES[kind]:
                found = along(board, move.start, df, dr)[:2]
                if len(found) == 2:
                    before_pins.add(tuple(found))
        for df, dr in LINES[mover]:
            found = along(now, move.end, df, dr)[:2]
            if len(found) < 2 or any(side(now[i]) != enemy for i in found):
                continue
            front, back = now[found[0]].lower(), now[found[1]].lower()
            if (front in "nbrq" and tuple(found) not in before_pins and not pin
                    and (back == "k" or (back in "qr" and VALUE[back] > VALUE[front]
                                         and (VALUE[back] > VALUE[mover] or not attackers(now, found[1], enemy))))):
                pin = (front, back)
            if back in "pk" or skewer:
                continue
            if front == "k":
                # any block parries the skewer, and so does taking the piece without losing by it
                blocked = any(after.board[r.start].lower() != "k" and (victim(after, r) != move.end
                                                                      or won(after, r) >= 0) for r in replies)
                flights = [r.end for r in replies if after.board[r.start].lower() == "k"]
                guarded_by_king = any(found[1] in [t for df2, dr2 in KING if (t := step(f, df2, dr2)) is not None]
                                      for f in flights)
                if not blocked and (VALUE[back] > VALUE[mover] or (not attackers(now, found[1], enemy)
                                                                   and not guarded_by_king)):
                    skewer = (front, back)
            elif (front in "qr" and VALUE[front] > VALUE[back] and VALUE[front] > VALUE[mover]
                  and (VALUE[back] > VALUE[mover] or not attackers(now, found[1], enemy))):
                skewer = (front, back)
    if check:
        pin = ()

    # a new attack on one piece worth having, by the moved piece, or by one it uncovered
    threat, threat_square = "", -1
    if safe and not check:
        before_reach = set(reach(board, move.start)) if not castle else set()
        best = -1
        for target in reach(now, move.end):
            piece = now[target]
            if not piece or side(piece) != enemy or piece.lower() == "k" or target in before_reach:
                continue
            k = piece.lower()
            if (VALUE[k] > VALUE[mover] or not attackers(now, target, enemy)) and VALUE[k] > best \
                    and not winnable(board, target, turn):
                threat, threat_square, best = k, target, VALUE[k]
    unmasked = ""
    if not check:
        for i, piece in enumerate(now):
            if not piece or side(piece) != turn or piece.lower() not in LINES or i == move.end:
                continue
            for df, dr in LINES[piece.lower()]:
                was = along(board, i, df, dr)
                if not was or was[0] != move.start:
                    continue
                found = along(now, i, df, dr)
                if not found or side(now[found[0]]) != enemy:
                    continue
                k = now[found[0]].lower()
                if k not in "pk" and (VALUE[k] > VALUE[piece.lower()] or not attackers(now, found[0], enemy)) \
                        and not winnable(board, found[0], turn):
                    if not unmasked or VALUE[k] > VALUE[unmasked]:
                        unmasked, traits["revealed"] = k, piece.lower()

    # a threat of mate: what this side could mate with if it moved again
    mate_threat = ""
    if not check and not mate:
        again = skipped(after)
        new = [m for m in mates(again, pseudo_moves(again), legal=False)
               if (again.board[m.start].lower(), m.end) not in board_.mating]  # a mate it makes, not one it keeps
        if new:
            mate_threat = label(new[0].end)

    # danger: pieces that could be taken for profit before the move, and whether they still can be after it
    escaped = not taken and not castle and move.start in board_.danger and safe
    guarded, guard, guarded_square = "", "", -1
    if not taken and not castle:
        for i in sorted(board_.danger):
            piece = board[i]
            if i == move.start or now[i] != piece:
                continue
            if any(victim(after, r) == i and won(after, r) > 0 for r in replies):
                continue
            how = ""
            if i in reach(now, move.end):
                how = "defend"
            elif any(between(a, i, move.end) for a in attackers(board, i, enemy)):
                how = "block"
            if how and (not guarded or VALUE[piece.lower()] > VALUE[guarded]):
                guarded, guard, guarded_square = piece.lower(), how, i

    # a pawn's own traits
    rank = rank_of(move.end, turn)
    ahead = range(rank + 1, 8)
    files = [f for f in (move.end % 8 - 1, move.end % 8, move.end % 8 + 1) if 0 <= f < 8]
    their_pawn = "p" if turn == "w" else "P"
    our_pawn = "P" if turn == "w" else "p"
    passed = (kind == "p" and not move.promotion
              and not any(now[f + 8 * (r if turn == "w" else 7 - r)] == their_pawn for f in files for r in ahead))
    promote_next = False
    if kind == "p" and rank == 6:
        forward = step(move.end, 0, 1 if turn == "w" else -1)
        promote_next = (forward is not None and not now[forward]) or any(
            (t := step(move.end, df, 1 if turn == "w" else -1)) is not None and now[t] and side(now[t]) == enemy
            for df in (-1, 1))
    offer = (kind == "p" and not taken and not move.promotion and not safe and net >= -1)
    luft = False
    if kind == "p" and not taken and move.end - move.start in (8, -8):
        home = king(position, turn)
        castled = rank_of(home, turn) == 0 and home % 8 not in (3, 4)  # a king gone to a wing of its back rank
        if castled and rank_of(move.start, turn) == 1 and abs(home % 8 - move.start % 8) <= 1:
            front = [t for df in (-1, 0, 1) if (t := step(home, df, 1 if turn == "w" else -1)) is not None]
            before_free = [t for t in front if not board[t] and not attacked(board, t, enemy)]
            after_free = [t for t in front if not now[t] and not attacked(now, t, enemy)]
            luft = not before_free and move.start in after_free
    frees, frees_square = "", -1
    if kind == "p" and not taken:
        for i, piece in enumerate(board):
            if not piece or side(piece) != turn or piece.lower() not in "bq":
                continue
            for df, dr in DIAGONAL if piece.lower() == "b" else ORTHOGONAL + DIAGONAL:
                was = along(board, i, df, dr)
                if not was or was[0] != move.start:
                    continue
                gained, target = 0, move.start
                while target is not None and not now[target]:
                    gained += 1
                    target = step(target, df, dr)
                if gained >= 2 and (piece.lower() == "b" or not frees):
                    frees, frees_square = piece.lower(), i
    prepares = ""
    if kind == "p" and move.start in FIANCHETTO[turn] and abs(move.end - move.start) == 8:
        bishop_home = FIANCHETTO[turn][move.start]
        if board[bishop_home] == ("B" if turn == "w" else "b"):
            prepares = "Kingside" if move.start % 8 == 6 else "Queenside"
    covers = -1
    if kind == "p" and not move.promotion:
        new = [t for t in reach(now, move.end) if t not in reach(board, move.start)]
        if new:
            covers = min(new, key=lambda t: (t not in CENTRE, to_centre(t), abs(t % 8 - 3.5)))
    two = kind == "p" and abs(move.end - move.start) == 16

    # the minor pieces' traits
    first = kind in "nb" and MINORS[turn].get(move.start) == kind
    rim = kind == "n" and move.end % 8 in (0, 7)
    fianchetto = kind == "b" and first and move.end in FIANCHETTO[turn]
    aims_f7 = (kind == "b" and TARGET_F7[turn] in reach(now, move.end) and now[TARGET_F7[turn]] == their_pawn
               and TARGET_F7[turn] not in reach(board, move.start))
    toward = kind == "n" and any(t in CENTRE for t in reach(now, move.end))
    outpost, backed = False, False
    if mover in "nb" and kind in "nb" and rank in (4, 5) and 1 <= move.end % 8 <= 6 and safe:
        f, r = move.end % 8, move.end // 8
        beyond = range(r + 1, 8) if turn == "w" else range(0, r)
        outpost = not any(now[g + 8 * rr] == their_pawn for g in (f - 1, f + 1) for rr in beyond)
        back = -1 if turn == "w" else 1
        backed = any((t := step(move.end, df, back)) is not None and now[t] == our_pawn for df in (-1, 1))

    # the heavy pieces' and the king's traits
    seventh = mover in "rq" and kind in "rq" and rank == 6 and rank_of(move.start, turn) != 6
    open_file = ""
    if kind == "r" and move.start % 8 != move.end % 8 and not castle:
        column = [now[move.end % 8 + 8 * r] for r in range(8)]
        if our_pawn not in column:
            open_file = "half-open" if their_pawn in column else "open"
    battery, battery_line, battery_king = "", "", False
    if mover in LINES and not castle:
        near = {t for dk, rk in KING if (t := step(their_king, dk, rk)) is not None} | {their_king}
        for df, dr in LINES[mover]:
            diagonal = df != 0 and dr != 0
            for front, back in ((move.end, along(now, move.end, -df, -dr)[:1]),
                                *[(i, [move.end]) for i in along(now, move.end, df, dr)[:1]]):
                partner_at = back[0] if front == move.end and back else front
                if not back or partner_at == move.end or side(now[partner_at]) != turn:
                    continue
                partner = now[partner_at].lower()
                if not ((diagonal and {mover, partner} <= {"q", "b"} and "q" in (mover, partner))
                        or (not diagonal and {mover, partner} <= {"q", "r"} and (mover, partner) != ("q", "q"))):
                    continue
                if kind == mover and move.start in (*line_squares(partner_at, df, dr),
                                                    *line_squares(partner_at, -df, -dr)):
                    continue  # the two were on this line already
                ray, target = [], step(front, df, dr)
                while target is not None:
                    ray.append(target)
                    if now[target]:
                        break
                    target = step(target, df, dr)
                # a battery worth the name: aimed at the king's door, or heavy pieces doubled on a file that is
                # open or half-open into the other half, or on the seventh rank
                at_king = any(t in near for t in ray)
                line = "diagonal" if diagonal else "file" if df == 0 else "rank"
                column = [now[move.end % 8 + 8 * rr] for rr in range(8)]
                on_file = (line == "file" and our_pawn not in column and dr == (1 if turn == "w" else -1)
                           and any(rank_of(t, turn) >= 4 for t in ray))
                on_seventh = line == "rank" and rank == 6
                if at_king or on_file or on_seventh:
                    battery, battery_line, battery_king = partner, line, at_king
                    break
            if battery:
                break
    rooks_before = [i for i, p in enumerate(board) if p == ("R" if turn == "w" else "r") and rank_of(i, turn) == 0]
    rooks_after = [i for i, p in enumerate(now) if p == ("R" if turn == "w" else "r") and rank_of(i, turn) == 0]

    def connected(squares, rooks) -> bool:
        return len(rooks) == 2 and all(not squares[i] for i in range(min(rooks) + 1, max(rooks)))

    connects = connected(now, rooks_after) and not connected(board, rooks_before)
    lift = (kind == "r" and move.start % 8 == move.end % 8 and rank_of(move.start, turn) == 0 and rank in (2, 3))
    early = (kind == "q" and move.start == (3 if turn == "w" else 59)
             and sum(1 for i, k in MINORS[turn].items() if board[i].lower() == k and side(board[i]) == turn) >= 3)
    long_diagonal = False
    if mover == "b" and kind == "b":
        f, r = move.end % 8, move.end // 8
        for diagonal in ((1, 1),) if f == r else ((1, -1),) if f + r == 7 else ():
            seen = 0
            for sign in (1, -1):
                target = step(move.end, diagonal[0] * sign, diagonal[1] * sign)
                while target is not None and not now[target]:
                    seen += 1
                    target = step(target, diagonal[0] * sign, diagonal[1] * sign)
            long_diagonal = seen >= 4
    aims_king = False
    if mover in LINES and not check and not castle:
        def on_line(index: int) -> bool:
            return any(their_king in line_squares(index, df, dr) for df, dr in LINES[mover])
        aims_king = on_line(move.end) and not (kind == mover and on_line(move.start))
    forfeit = kind == "k" and not castle and any(
        (right.isupper()) == (turn == "w") for right in position.castling)
    corner = kind == "k" and not castle and move.end in ((0, 7) if turn == "w" else (56, 63))
    pawn_ending = all(not piece or piece.lower() in "kp" for piece in now)
    opposition = (kind == "k" and not castle and pawn_ending
                  and ((move.end % 8 == their_king % 8 and abs(move.end // 8 - their_king // 8) == 2)
                       or (move.end // 8 == their_king // 8 and abs(move.end % 8 - their_king % 8) == 2)))
    behind_passer = ""
    if kind == "r" and not castle:
        ahead_of_rook = along(now, move.end, 0, 1 if turn == "w" else -1)[:1]
        if ahead_of_rook and now[ahead_of_rook[0]] == our_pawn and move.start % 8 != move.end % 8:
            pawn_at = ahead_of_rook[0]
            f = pawn_at % 8
            rows = range(pawn_at // 8 + 1, 8) if turn == "w" else range(0, pawn_at // 8)
            if not any(now[g + 8 * rr] == their_pawn for g in (f - 1, f, f + 1) if 0 <= g < 8 for rr in rows):
                behind_passer = FILES[f]
    gives_up = ""
    if kind == "r" and move.start in ((0, 7) if turn == "w" else (56, 63)):
        right = "K" if move.start % 8 == 7 else "Q"
        if (right if turn == "w" else right.lower()) in position.castling:
            gives_up = "Short" if right == "K" else "Long"
    invades = kind in "nbrq" and rank >= 4 and rank_of(move.start, turn) < 4

    book = BOOK.get(placement(after), ())
    level = bool(taken) and exchange >= VALUE[taken] and material(board, turn) == -VALUE[taken]
    free = bool(taken) and not any(victim(after, r) == move.end for r in replies)
    dead = ""
    if taken and insufficient(after):
        thrown = any(board_.net[m] >= max(3, net + 1) and not insufficient(board_.after[m]) for m in board_.moves)
        dead = "thrown" if thrown else "saving" if material(board, turn) <= -3 else "even"
    blunder, lost, sacrifice = "", "", False
    if not mate and "allows" not in traits and lost_at is not None and net <= -2:
        lost = now[lost_at].lower() or "promotion"  # an empty square: the other side queens there
        forcing = (check or bool(mate_threat) or bool(fork)
                   or (threat and VALUE[threat] >= -net) or (unmasked and VALUE[unmasked] >= -net))
        if lost_at == move.end and forcing:
            sacrifice = True
        elif board_.best - net >= 2 and not forcing:
            blunder = "hang" if lost_at == move.end else "queen" if lost == "promotion" else "drop"
    greek = (sacrifice and kind == "b" and taken == "p" and check and move.end == (55 if turn == "w" else 15)
             and their_king == (62 if turn == "w" else 6))
    evade = ""
    if board_.checked:
        checking_us = attackers(board, king(position, turn), enemy)
        took_checker = taken_at is not None and taken_at in checking_us
        evade = ("king-take" if took_checker else "king") if kind == "k" else "capture" if took_checker else "block"
    forced_king = check and bool(replies) and all(now[r.start].lower() == "k" for r in replies)
    hits = "" if castle else max((now[t].lower() for t in reach(now, move.end) if now[t] and side(now[t]) == enemy
                                  and now[t].lower() not in "pk"), key=lambda k: VALUE[k], default="")
    return Reading(
        kind=kind, start=move.start, end=move.end, turn=turn, taken=taken, passing=passing, castle=castle,
        crown=move.promotion, check=check, double=len(checking) > 1, discovered=check and not direct,
        revealed=traits.get("revealed", revealed),
        checkers=tuple(sorted({now[i].lower() for i in checking}, key=ORDER.index)), mate=mate, mate_kind=mate_kind,
        stalemate=not check and not replies, only=len(board_.moves) == 1, evade=evade,
        allows=traits.get("allows", ""), stops=traits.get("stops", ""), blunder=blunder, lost=lost,
        sacrifice=sacrifice, greek=greek, book=book, see=exchange, net=net, free=free, level=level, dead=dead,
        fork=fork, skewer=skewer, pin=pin, unmasked=unmasked, mate_threat=mate_threat, threat=threat,
        threat_square=threat_square, escaped=escaped, guarded=guarded, guard=guard, offer=offer, outpost=outpost,
        backed=backed, first=first, rim=rim, fianchetto=fianchetto, aims_f7=aims_f7, toward=toward,
        centre=move.end in CENTRE, passed=passed, seventh=seventh, luft=luft, frees=frees, frees_square=frees_square,
        prepares=prepares, covers=covers, space=kind == "p" and rank >= 4, two=two, forfeit=forfeit,
        gives_up=gives_up, opposition=opposition, behind_passer=behind_passer, endgame=board_.endgame, corner=corner,
        promote_next=promote_next, forced_king=forced_king, hits=hits, ahead=material(board, turn),
        guarded_square=guarded_square, open_file=open_file, battery=battery, battery_line=battery_line,
        battery_king=battery_king, connects=connects, lift=lift, early=early, long_diagonal=long_diagonal,
        aims_king=aims_king, invades=invades, advance=rank - rank_of(move.start, turn),
        distance=max(abs(move.end % 8 - move.start % 8), abs(move.end // 8 - move.start // 8)),
        sideways=abs(move.end % 8 - move.start % 8))


def line_squares(index: int, df: int, dr: int) -> list[int]:
    """Every square on the line from `index`, whatever stands on them."""
    out, target = [], step(index, df, dr)
    while target is not None:
        out.append(target)
        target = step(target, df, dr)
    return out


def between(a: int, b: int, c: int) -> bool:
    """Whether square `c` lies strictly between `a` and `b` on a straight line."""
    fa, ra, fb, rb, fc, rc = a % 8, a // 8, b % 8, b // 8, c % 8, c // 8
    df, dr = fb - fa, rb - ra
    if not (df == 0 or dr == 0 or abs(df) == abs(dr)):
        return False
    steps = max(abs(df), abs(dr))
    sf, sr = (df > 0) - (df < 0), (dr > 0) - (dr < 0)
    return any((fa + sf * i, ra + sr * i) == (fc, rc) for i in range(1, steps))


# --- the themes, from the most telling down ------------------------------------------------------------------------

def theme(r: Reading) -> str:
    """The most telling thing the move does, which its title is about."""
    if r.mate:
        return r.mate_kind or "mate"
    if r.stalemate:
        return "stalemate"
    if r.only:
        return "only"
    if r.allows:
        return "allows"
    if r.book:  # an opening the books name is known theory, gambits and sacrifices included
        return "book"
    if r.blunder:
        return "blunder"
    if r.stops == "only":
        return "only-stop"
    if r.dead:
        return "dead"
    if r.crown:
        return "crown" if r.crown == "q" else "underpromote"
    if r.castle:
        return "castle"
    if r.evade:
        return "evade"
    if r.double:
        return "double"
    if r.discovered:
        return "discovery"
    if "k" in r.fork and "q" in r.fork:
        return "royal-fork"
    if r.sacrifice:
        return "greek" if r.greek else "sacrifice"
    if r.taken == "q":
        return "queen"
    if r.fork and (r.check or len(r.fork) > 2):
        return "fork"
    if r.skewer:
        return "skewer"
    if r.taken and r.check:
        return "strike"
    if r.passing:
        return "passing"
    if r.taken:
        if r.level:
            return "level"
        if r.free:
            return "free"
        if r.see > 0:
            return "win"
        return "trade" if r.see == 0 else "capture"
    if r.stops:
        return "stop"
    if r.check:
        return "check"
    if r.mate_threat:
        return "mate-threat"
    if r.fork:
        return "fork"
    if r.pin:
        return "pin"
    if r.unmasked:
        return "unmask"
    if r.threat:
        return "threat"
    if r.escaped:
        return "escape"
    if r.guarded:
        return "guard"
    if r.offer:
        return "offer"
    if r.outpost:
        return "outpost"
    if r.kind == "p":
        if r.passed:
            return "passed"
        if r.centre:
            return "centre"
        if r.luft:
            return "luft"
        if r.prepares:
            return "prepare"
        if r.frees == "b":
            return "free-bishop"
        if r.covers in CENTRE:
            return "cover"
        if r.frees == "q":
            return "free-queen"
        if r.space:
            return "space"
        return "stride" if r.two else "push"
    if r.first:
        if r.rim:
            return "rim-develop"
        if r.fianchetto:
            return "fianchetto"
        return "aim-f7" if r.aims_f7 else "develop"
    if r.kind == "k":
        if r.forfeit:
            return "forfeit"
        if r.opposition:
            return "opposition"
        if r.endgame and (to_centre(r.end) < to_centre(r.start) or r.advance > 0):
            return "activate"
        return "tuck" if r.corner else "king"
    if r.seventh:
        return "seventh"
    if r.behind_passer:
        return "behind-passer"
    if r.battery:
        return "battery"
    if r.open_file:
        return "open-file"
    if r.connects:
        return "connect"
    if r.lift:
        return "lift"
    if r.early:
        return "sortie"
    if r.centre:
        return "centralise"
    if r.long_diagonal:
        return "diagonal"
    if r.aims_king:
        return "aim"
    if r.rim:
        return "rim"
    if r.gives_up:
        return "rook-forfeit"
    if r.advance < 0:
        return "retreat"
    if r.invades:
        return "invade"
    return "long" if r.sideways >= 5 else "quiet"


# One emoji to a theme, so the emoji down the list read as a key to the moves; a move judged to lose gets WARNING.
WARNING = "⚠️"
EMOJI = {
    "fool": "🏆", "scholar": "🏆", "smothered": "🏆", "back-rank": "🏆", "mate": "🏆", "stalemate": "🤝",
    "only": "❗", "allows": WARNING, "blunder": WARNING, "only-stop": "❗", "book": "📖", "dead": "🤝", "crown": "👑",
    "underpromote": "🎖️", "castle": "🏰", "evade": "🛡️", "double": "🌩️", "discovery": "🎭", "royal-fork": "🍴",
    "sacrifice": "🎲", "greek": "🎲", "queen": "💥", "fork": "🍴", "skewer": "🍢", "strike": "⚔️", "passing": "👻",
    "level": "⚖️", "free": "🎁", "win": "💰", "trade": "🔄", "capture": "⚔️", "stop": "🛡️", "check": "⚡",
    "mate-threat": "☠️", "pin": "📌", "unmask": "🎭", "threat": "🎯", "escape": "💨", "guard": "🛡️", "offer": "🎲",
    "outpost": "🚩", "passed": "🏃", "centre": "🏛️", "luft": "🌬️", "prepare": "🔭", "free-bishop": "🔓",
    "cover": "♟️", "free-queen": "🔓", "space": "♟️", "stride": "♟️", "push": "♟️", "rim-develop": "🌑",
    "fianchetto": "🔭", "aim-f7": "🌅", "develop": "🌅", "forfeit": "🚶", "activate": "🚶", "tuck": "🚶",
    "king": "🚶", "seventh": "🔥", "battery": "🔋", "open-file": "🛣️", "connect": "🔗", "lift": "🏗️",
    "sortie": "👸", "centralise": "🏛️", "diagonal": "🔭", "aim": "🏹", "rim": "🌑", "retreat": "↩️",
    "invade": "🗡️", "long": "🌠", "quiet": "🔀", "rook-forfeit": "🚶", "opposition": "🤺", "behind-passer": "🏃",
}
NTH = {2: "Third", 3: "Fourth", 4: "Fifth", 5: "Sixth", 6: "Seventh", 7: "Eighth"}
LOST_WORTH = {1: "Pawn", 3: "Piece", 5: "Rook", 9: "Queen"}  # what a side down this much is down


def ident(r: Reading, board) -> str:
    """The moving piece, pointed out as a player would: the h-Pawn, the King's Knight, the Rook on a1."""
    us = r.turn
    if r.kind == "p":
        return f"the {FILES[r.start % 8]}-Pawn"
    if r.kind == "k":
        return "the King"
    mine = [i for i, p in enumerate(board) if p and side(p) == us and p.lower() == r.kind]
    if r.kind == "n" and r.start in MINORS[us]:
        return "the King's Knight" if r.start % 8 == 6 else "the Queen's Knight"
    if r.kind == "b" and bishop_name(board, r.start) != "Bishop":
        return f"the {bishop_name(board, r.start)}"
    if r.kind == "r" and r.start in ((0, 7) if us == "w" else (56, 63)):
        right = ("K" if r.start % 8 == 7 else "Q") if us == "w" else ("k" if r.start % 8 == 7 else "q")
        if right in survey_rights(board, us, right):
            return "the King's Rook" if r.start % 8 == 7 else "the Queen's Rook"
    if len(mine) == 1:
        return f"the {name(r.kind)}"
    return f"the {name(r.kind)} on {label(r.start)}"


def survey_rights(board, us: str, right: str) -> str:
    """The castling right, as long as the king and that rook stand at home: a rook with the right is the original."""
    return right if board[4 if us == "w" else 60] == ("K" if us == "w" else "k") else ""


def actions(r: Reading) -> list[str]:
    """What the move does, said plainly, from the plainest to the most exact: the first half of a warning."""
    to, frm, P = label(r.end), label(r.start), name(r.kind)
    if r.castle:
        return ["Castle Short" if r.castle == "king" else "Castle Long"]
    if r.crown:
        return [f"Promote to a {name(r.crown)}", f"Promote to a {name(r.crown)} on {to}",
                f"Promote on {to} from {frm}"]
    pawn = f"the {FILES[r.start % 8]}-Pawn"
    if r.taken:
        by = pawn if r.kind == "p" else f"the {P}"
        return [f"Take the {name(r.taken)}", f"Take the {name(r.taken)} with {by}", f"Take on {to} with {by}",
                f"Take on {to} from {frm}"]
    if r.kind == "p":
        return [f"Push {pawn}", f"Push {pawn} to {to}"]
    return [f"Move the {P}", f"Move the {P} to {to}", f"Move the {P} from {frm} to {to}"]


def listed(kinds: tuple[str, ...]) -> str:
    """Pieces a fork or skewer catches, as an order names them: King and Rook, Both Rooks, Queen, Rook and Knight."""
    names = [name(k) for k in kinds]
    if len(names) == 2 and names[0] == names[1]:
        return f"Both {names[0]}s"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def tiers(r: Reading, board_: Board) -> list[list[str]]:
    """The move's titles, in tiers from the plainest to the most exact: every title in a tier says the same thing
    about the move, and a later tier adds what tells it apart from moves that read the same, ending with the piece
    named by its square."""
    key = theme(r)
    board = board_.position.board
    P, to, frm, f = name(r.kind), label(r.end), label(r.start), FILES[r.start % 8]
    T = name(r.taken) if r.taken else ""
    N = name(r.crown) if r.crown else ""
    a_T = "an" if T[:1] in "AEIOU" else "a"
    who = ident(r, board)
    by = who if r.kind == "p" else f"the {P}"  # the piece, as "with ..." names it
    exact = who if r.kind == "p" else f"the {P} on {frm}"  # the piece, named by its square
    go = f"Push the {f}-Pawn to {to}" if r.kind == "p" else f"Move the {P} to {to}"  # the move, said plainly
    go_exact = f"Push the {f}-Pawn to {to}" if r.kind == "p" else f"Move {exact} to {to}"
    if r.taken:
        go, go_exact = f"Take on {to} with {by}", f"Take on {to} with {exact}"

    def fit(*options: str) -> list[str]:
        """The first of `options` short enough to draw, as a tier of one."""
        return next(([o] for o in options if len(o) <= LONGEST), [])

    def ladder(base: list[str], *with_piece: str) -> list[list[str]]:
        """A theme's tiers from its plainest titles: then the call with the piece, then with the piece and the
        square it goes to, then with the piece named by the square it leaves, each keeping what the last said."""
        core = base[0][:-1]
        return [base, fit(*with_piece), fit(f"{go}, {core}!", f"{core} with the {P} from {to}!"),
                fit(f"{go_exact}, {core}!", f"{core} with {exact}!")]
    t: list[list[str]]
    if key == "fool":
        t = [["Deliver Fool's Mate!", "Checkmate with Fool's Mate!"]]
    elif key == "scholar":
        t = [["Deliver Scholar's Mate!", "Checkmate with Scholar's Mate!"]]
    elif key == "smothered":
        t = ladder(["Deliver Smothered Mate!", "Smother the King, Checkmate!"])
    elif key == "back-rank":
        t = ladder(["Deliver Back-Rank Mate!", "Checkmate on the Back Rank!"], f"Mate on the Back Rank with {by}!")
    elif key == "mate":
        if r.crown and r.taken:
            t = [[f"Take the {T}, Make a {N}, Checkmate!", f"Capture the {T}, Promote to a {N}, Mate!"],
                 [f"Take on {to} from {frm}, Make a {N}, Mate!"]]
        elif r.crown:
            t = [[f"Promote to a {N} with Checkmate!", f"Make a {N} and Checkmate!"],
                 [f"Promote to a {N} on {to} with Checkmate!"], [f"Promote on {to} from {frm}, Checkmate!"]]
        elif r.castle:
            t = [["Castle with Checkmate!"]]
        elif r.passing:
            t = [["Checkmate en Passant!", "Take en Passant with Checkmate!"], [f"Checkmate en Passant with {who}!"]]
        elif r.double:
            t = ladder(["Checkmate with Double Check!", "Deliver Mate by Double Check!"],
                       f"Mate by Double Check with {by}!")
        elif r.discovered:
            t = ladder(["Deliver Discovered Checkmate!", "Unmask Checkmate!"], f"Move the {P}, Discover Checkmate!")
        elif r.taken:
            t = ladder([f"Take the {T} with Checkmate!", f"Capture the {T} and Checkmate!"],
                       f"Take the {T} with {by}, Checkmate!")
        else:
            t = ladder(["Checkmate!", "Deliver Checkmate!", "Checkmate the King!", "End It with Checkmate!"],
                       f"Checkmate with {by}!")
            t[1] = [f"Checkmate with {by}!", f"Deliver Mate with {by}!"]
    elif key == "stalemate":
        if r.ahead >= 3:
            t = ladder(["Settle for Stalemate!", "Let Them Off with Stalemate!"], f"Settle for Stalemate with {by}!")
        elif r.ahead <= -3:
            t = ladder(["Save the Game with Stalemate!", "Escape into Stalemate!", "Bail Out with Stalemate!"],
                       f"Save the Game, Stalemate with {by}!")
        else:
            t = ladder(["Stalemate the King!", "Force Stalemate!", "Freeze the Board in Stalemate!"],
                       f"Stalemate with {by}!")
    elif key == "only":
        t = [[*(["Take the Only Way Out!"] if r.evade else []), "Play the Only Legal Move!",
              "Make the Only Move There Is!"]]
    elif key == "allows":
        ending = ("into Fool's Mate!",) if r.allows == "fool" else (", Allow Mate in One!", ", Walk into Mate!")
        t = [[a + (" " if e[0] != "," else "") + e for e in ending] for a in actions(r)]
    elif key == "blunder":
        L = name(r.lost) if r.lost in PIECES else ""
        if r.blunder == "queen":
            t = [[f"{a}, Let Them Queen!", f"{a}, Let Them Make a Queen!"] for a in actions(r)]
        elif r.blunder == "hang" and r.taken:
            t = [[f"Take the {T}, Lose the {L}!"], [f"Take the {T} on {to}, Lose the {L}!"],
                 [f"Take on {to} with {exact} and Lose It!"]]
        elif r.blunder == "hang":
            t = [[f"Hang the {P}!", f"Leave the {P} Hanging!", f"Throw Away the {P}!"],
                 [f"Hang the {P} on {to}!", f"Leave the {P} Hanging on {to}!"], [f"Hang the {P} from {frm} on {to}!"]]
        else:
            t = [[f"{a}, Drop the {L}!", f"{a}, Leave the {L} Hanging!"] for a in actions(r)]
    elif key == "only-stop":
        t = [["Find the Only Move That Stops Mate!", "Play the Only Move That Stops Mate!"]]
    elif key == "book":
        t = [list(r.book)]
    elif key == "dead":
        took = f"Take the {T}" + (f", Make a {N}" if r.crown else "")
        if r.dead == "thrown":
            t = [[f"{took}, Settle for a Draw!", f"{took}, Only a Draw!"],
                 [f"Take on {to} with {exact}, Settle for a Draw!"]]
        elif r.dead == "saving":
            t = [[f"{took} and Save the Draw!", f"{took}, Escape with a Draw!"],
                 [f"Take on {to} with {exact}, Save the Draw!"]]
        else:
            t = [[f"{took} and Draw the Game!", f"{took}, Capture into a Dead Draw!"],
                 [f"Take on {to} with {exact}, Draw!"]]
    elif key == "crown":
        if r.taken:
            t = [[f"Take the {T} and Make a Queen!", f"Capture the {T} and Promote!"],
                 [f"Take the {T} on {to}, Make a Queen!"], [f"Take on {to} from {frm}, Make a Queen!"]]
        elif r.check:
            t = [["Queen with Check!", "Promote to a Queen with Check!"], [f"Queen on {to} with Check!"]]
        else:
            t = [["Promote to a Queen!", "Queen the Pawn!", "Crown a New Queen!", "Make a New Queen!"],
                 [f"Queen the {f}-Pawn!"], [f"Queen the Pawn on {to}!"]]
    elif key == "underpromote":
        if r.taken:
            t = [[f"Take the {T}, Promote to a {N}!"], [f"Take the {T} on {to}, Promote to a {N}!"],
                 [f"Take on {to} from {frm}, Make a {N}!"]]
        elif r.check:
            t = [[f"Promote to a {N} with Check!", f"Underpromote to a {N} with Check!"],
                 [f"Promote to a {N} on {to} with Check!"]]
        else:
            t = [[f"Underpromote to a {N}!", f"Promote to a {N}!"], [f"Underpromote to a {N} on {to}!"]]
    elif key == "castle":
        if r.castle == "king":
            t = [["Castle Short with Check!", "Castle Kingside with Check!"]] if r.check else [
                ["Castle Short!", "Castle Kingside!", "Castle Short and Raise the Drawbridge!",
                 "Tuck the King Away, Castle Short!"]]
        else:
            rook = "d1" if r.turn == "w" else "d8"
            t = [["Castle Long with Check!", "Castle Queenside with Check!"]] if r.check else [
                ["Castle Long!", "Castle Queenside!", "Castle Long, Rook to the d-File!",
                 f"Castle Long and Bring the Rook to {rook}!"]]
    elif key == "evade":
        if r.evade == "king-take":
            t = [[f"Take the Checking {T} with the King!", f"Capture the Checking {T} with the King!"]]
        elif r.evade == "king" and r.taken:
            t = [[f"Step Out of Check, Take the {T}!", f"Take the {T} with the King!"],
                 [f"Step Out of Check, Take the {T} on {to}!"]]
        elif r.evade == "king":
            t = [["Step Out of Check!", "Sidestep the Check!", "Walk the King Out of Check!"],
                 [f"Step the King to {to}!", f"Walk the King to {to}!"]]
        elif r.evade == "capture":
            t = [[f"Take the Checking {T}!", f"Capture the Checking {T}!", f"Remove the Checking {T}!"],
                 [f"Take the Checking {T} with {by}!"], [f"Take the Checking {T} with {exact}!"]]
        else:
            t = ladder(["Block the Check!", "Shield the King!", "Block the Line of Check!"],
                       f"Block the Check with {by}!")
            t[1] = [f"Block the Check with {by}!", f"Shield the King with {by}!"]
    elif key == "double":
        pair = listed(r.checkers) if len(r.checkers) == 2 else "Two Pieces"
        t = ladder(["Give Double Check!", "Double Check the King!", "Hit the King with Double Check!"],
                   f"Double Check with {pair}!")
    elif key == "discovery":
        base = ["Give Discovered Check!", "Unleash a Discovered Check!", "Unmask a Discovered Check!"]
        if r.hits:
            base = [f"Discover Check and Hit the {name(r.hits)}!", *base]
        first = f"Take the {T}, Discover Check!" if r.taken else f"{go.split(' to ')[0]}, Discover Check!"
        t = [base, [first], fit(f"{go}, Discover Check!"), fit(f"{go_exact}, Discover Check!")]
    elif key == "royal-fork":
        if "r" in r.fork:
            t = ladder(["Strike a Family Fork!", "Fork the Whole Royal Family!"], f"Strike a Family Fork with {by}!")
        else:
            t = ladder(["Fork King and Queen!", "Strike a Royal Fork!", "Fork the King and Queen!"],
                       f"Fork King and Queen with {by}!")
    elif key == "sacrifice":
        # the price is always named, and a heavy one is never dressed up as a sacrifice
        price = f" for {a_T} {T}" if r.taken else ""
        verbs = ("Give Up",) if r.net <= -5 else ("Sacrifice", "Give Up")
        base = [f"{verb} the {P}{price}!" for verb in verbs]
        if r.check and not r.taken:
            base += [f"{verb} the {P} with Check!" for verb in verbs]
        t = [base, [f"{verbs[0]} the {P} on {to}{price}!"], [f"{verbs[0]} {exact} on {to}{price}!"]]
    elif key == "greek":
        t = [["Offer the Greek Gift!", f"Sacrifice the Bishop on {to}!"]]
    elif key == "queen":
        if r.kind == "q" and r.see == 0 and not r.free:
            t = [["Trade Queens!", "Swap Off the Queens!", "Exchange Queens!"]]
        elif r.free:
            t = [["Take the Undefended Queen!", "Grab the Free Queen!", "Win the Queen for Nothing!"],
                 [f"Take the Free Queen with {by}!"], [f"Take the Free Queen with {exact}!"]]
        else:
            t = [["Win the Queen!", "Take the Queen!", "Bring Down the Queen!", "Capture the Queen!"],
                 [f"Win the Queen with {by}!", f"Take the Queen with {by}!"], [f"Take the Queen with {exact}!"]]
            if r.check:
                t[0] = ["Take the Queen with Check!", "Capture the Queen with Check!"]
    elif key == "fork":
        caught = listed(r.fork[:3])
        t = ladder([f"Fork {caught}!", f"Hit {caught} at Once!"], f"Fork {caught} with {by}!")
    elif key == "skewer":
        pair = f"{name(r.skewer[0])} and {name(r.skewer[1])}"
        t = ladder([f"Skewer {pair}!", f"Skewer the {pair}!", f"Run a Skewer Through {pair}!"],
                   f"Skewer {pair} with {by}!")
    elif key == "strike":
        t = [[f"Take the {T} with Check!", f"Capture the {T} with Check!"], [f"Take the {T} with {by}, Check!"],
             fit(f"Take the {T} on {to} with {by}, Check!", f"Take on {to} with {by}, Check!"),
             fit(f"Take on {to} with {exact}, Check!")]
    elif key == "passing":
        t = [["Take en Passant!", "Capture en Passant!", "Strike en Passant!"], [f"Take en Passant with {who}!"]]
    elif key == "level":
        worth = LOST_WORTH.get(VALUE[r.taken], "Material")
        t = [[f"Win Back the {worth}!", "Restore the Material Balance!", "Level the Material!"],
             [f"Win Back the {worth} with {by}!"], fit(f"Win Back the {worth} on {to} with {by}!"),
             fit(f"Win Back the {worth} with {exact}!")]
    elif key == "free":
        t = [[f"Take the Free {T}!", f"Grab the Undefended {T}!", f"Snap Up the Loose {T}!"],
             [f"Take the Free {T} with {by}!"], fit(f"Take the Free {T} on {to} with {by}!"),
             fit(f"Take the Free {T} with {exact}!")]
    elif key == "win":
        if r.kind in "nb" and r.taken == "r" and r.see == 2:
            t = ladder(["Win the Exchange!", "Take the Rook, Win the Exchange!"], f"Win the Exchange with {by}!")
        elif r.see == VALUE[r.taken] - VALUE[r.kind]:
            t = [[f"Win the {T} for a {P}!", f"Give a {P}, Take {a_T} {T}!"], [f"Win the {T} for {by}!"],
                 fit(f"Win the {T} on {to} for {by}!"), fit(f"Win the {T} on {to} for {exact}!")]
        else:
            t = [[f"Take the {T} and Win Material!", "Win Material!"], [f"Win Material on {to}!"],
                 fit(f"Win Material on {to} with {by}!"), fit(f"Win Material on {to} with {exact}!")]
    elif key == "trade":
        if r.kind == r.taken and r.kind != "p":
            t = [[f"Trade {P}s!", f"Swap {P}s!", f"Exchange {P}s!"], [f"Trade {P}s on {to}!"],
                 fit(f"Trade {P}s on {to} from {frm}!")]
        elif r.kind == r.taken:
            t = [["Trade Pawns!", "Swap Pawns!", "Exchange Pawns!"], [f"Trade Pawns on {to}!"],
                 [f"Trade Pawns with {who}!"], [f"Trade Pawns on {to} with {who}!"]]
        elif VALUE[r.kind] == VALUE[r.taken]:
            t = [[f"Trade {P} for {T}!", f"Give the {P} for the {T}!"], [f"Trade {P} for {T} on {to}!"],
                 fit(f"Trade {exact} for the {T} on {to}!", f"Trade {P} for {T} on {to} from {frm}!")]
        else:
            t = [[f"Trade Off on {to}!", f"Exchange on {to}!"], [f"Trade Off on {to} with {by}!"],
                 fit(f"Trade Off on {to} with {exact}!")]
    elif key == "capture":
        t = [[f"Take the {T}!", f"Capture the {T}!"], [f"Take the {T} with {by}!"],
             fit(f"Take the {T} on {to} with {by}!", f"Take on {to} with {by}!"), fit(f"Take on {to} with {exact}!")]
    elif key == "stop":
        t = ladder(["Stop the Mate!", "Parry the Mate Threat!", "Defend Against Mate!"], f"Stop the Mate with {who}!")
    elif key == "check":
        base = ["Check the King!", "Give Check!", "Put the King in Check!"]
        if r.first:
            base = ["Develop with Check!", f"Bring Out the {P} with Check!"]
        elif r.forced_king:
            base = ["Force the King to Move!", "Check and Make the King Move!"]
        t = [base, [f"Check with {by}!", f"Give Check with {by}!"], fit(f"Check with {by} from {to}!"),
             fit(f"Check from {to} with {exact}!")]
    elif key == "mate-threat":
        t = ladder(["Threaten Mate!", "Threaten Checkmate!", "Set Up a Mate Threat!"],
                   f"Threaten Mate on {r.mate_threat}!")
    elif key == "pin":
        pinned, shield = name(r.pin[0]), name(r.pin[1])
        t = [[f"Pin the {pinned} to the {shield}!", f"Nail the {pinned} to the {shield}!"],
             fit(f"Pin the {pinned} to the {shield} with {by}!"),
             fit(f"{go}, Pin the {pinned}!", f"Pin the {pinned} to the {shield} from {to}!"),
             fit(f"{go_exact}, Pin the {pinned}!")]
    elif key == "unmask":
        U, S = name(r.unmasked), name(r.revealed)
        mover = f"{f}-Pawn" if r.kind == "p" else P
        t = [[f"Discover an Attack on the {U}!", f"Unmask an Attack on the {U}!"],
             [f"Unmask the {S} Against the {U}!"], fit(f"Unmask the {S} on the {U}, {mover} to {to}!"),
             fit(f"Unmask the {S} on the {U}, {mover} from {frm}!")]
    elif key == "threat":
        target = name(r.threat)
        if r.threat == "p":
            target = f"{FILES[r.threat_square % 8]}-Pawn"
        after = board_.after[Move(r.start, r.end, r.crown)]
        undefended = not attackers(after.board, r.threat_square, other(r.turn))
        base = [f"Attack the {target}!", f"Threaten the {target}!", f"Hit the {target}!", f"Go After the {target}!"]
        if undefended:
            base = [f"Attack the Undefended {target}!", f"Hit the Loose {target}!"]
        if r.threat == "q":
            base += ["Chase the Queen!", "Harass the Queen!"]
        if r.first:
            base += [f"Develop and Hit the {target}!", f"Develop with Tempo on the {target}!"]
        if r.kind == "p" and r.threat != "p":
            base += [f"Kick the {target} with {who}!"]
        t = [base, [f"Hit the {target} with {by}!", f"Attack the {target} with {by}!"],
             fit(f"{go}, Hit the {target}!", f"Hit the {target} with the {P} from {to}!"),
             fit(f"{go_exact}, Hit the {target}!")]
    elif key == "escape":
        base = [f"Save {by}!", f"Get {by} to Safety!", f"Rescue {by}!", f"Pull {by} Out of Danger!"]
        t = [base, fit(f"Get {by} to Safety on {to}!"), fit(f"Get {exact} to Safety on {to}!")]
    elif key == "guard":
        G = name(r.guarded) if r.guarded != "p" else f"{FILES[r.guarded_square % 8]}-Pawn"
        if r.guard == "defend":
            t = ladder([f"Defend the {G}!", f"Guard the {G}!", f"Protect the {G}!", f"Cover the {G}!"],
                       f"Defend the {G} with {by}!")
        else:
            t = ladder([f"Shield the {G}!", f"Block the Attack on the {G}!"], f"Shield the {G} with {by}!")
    elif key == "offer":
        t = [[f"Offer the {f}-Pawn!", f"Gambit the {f}-Pawn!"], [f"Offer the {f}-Pawn on {to}!"]]
    elif key == "outpost":
        base = [f"Plant the {P} on an Outpost!", f"Post the {P} on an Outpost!"]
        if r.backed:
            base.append(f"Plant the {P} on a Pawn-Backed Outpost!")
        t = [base, [f"Plant the {P} on the {to} Outpost!"], fit(f"Plant {exact} on the {to} Outpost!")]
    elif key == "develop":
        if r.kind == "n":
            base = ["Develop the Knight!", "Bring Out the Knight!", "Muster the Knights!"]
            if r.toward:
                base.append("Develop the Knight Toward the Centre!")
            t = [base, [f"Develop {who}!", f"Bring Out {who}!"], [f"Develop {who} to {to}!"]]
        else:
            t = [["Develop the Bishop!", "Bring Out the Bishop!"], [f"Develop {who}!", f"Bring Out {who}!"],
                 [f"Develop the Bishop to {to}!", f"Post the Bishop on {to}!"]]
    elif key == "aim-f7":
        target = label(TARGET_F7[r.turn])
        t = [[f"Aim the Bishop at {target}!", f"Develop the Bishop, Eye {target}!"],
             [f"Aim the Bishop at {target} from {to}!"]]
    elif key == "fianchetto":
        t = [["Fianchetto the Bishop!", "Post the Bishop on the Long Diagonal!"], [f"Fianchetto {who}!"]]
    elif key == "rim-develop":
        t = [["Develop the Knight to the Rim!", "Put the Knight on the Rim!", "Send the Knight to the Rim!"],
             [f"Put {who} on the Rim!", f"Develop {who} to the Rim!"], [f"Put the Knight on the Rim at {to}!"]]
    elif key == "passed":
        if rank_of(r.end, r.turn) == 6:
            base = ["Push the Passed Pawn to the Seventh!", "Bring the Pawn One Step from Queening!"]
            if r.promote_next:
                base.append("Threaten to Queen!")
        else:
            base = ["Push the Passed Pawn!", "Advance the Passed Pawn!", "Roll the Passed Pawn Forward!"]
        t = [base, [f"Push the Passed {f}-Pawn!", f"Advance the Passed {f}-Pawn!"], [f"Push the Passed Pawn to {to}!"]]
    elif key == "centre":
        t = [["Seize the Centre!", "Stake a Claim in the Centre!", "Occupy the Centre!", "Plant a Pawn in the Centre!"],
             [f"Seize the Centre with the {f}-Pawn!", f"Push the {f}-Pawn into the Centre!"],
             [f"Seize the Centre on {to}!"]]
    elif key == "luft":
        t = [["Make Luft for the King!", "Give the King Some Air!", "Open an Escape Square for the King!"],
             [f"Make Luft with the {f}-Pawn!"]]
    elif key == "prepare":
        bishop = "King's Bishop" if r.prepares == "Kingside" else "Queen's Bishop"
        t = [[f"Prepare the {r.prepares} Fianchetto!", f"Make Room to Fianchetto the {bishop}!"]]
    elif key == "free-bishop":
        bishop = bishop_name(board, r.frees_square)
        t = [[f"Free the {bishop}!", f"Open a Diagonal for the {bishop}!", f"Open Lines for the {bishop}!"],
             [f"Push the {f}-Pawn, Free the {bishop}!"], [f"Push the {f}-Pawn to {to}, Free the {bishop}!"]]
    elif key == "cover":
        t = [covering(r, board_), [f"{covering(r, board_)[0][:-1]} from {to}!"]]
    elif key == "free-queen":
        t = [["Open a Line for the Queen!", "Free the Queen!"], [f"Push the {f}-Pawn, Free the Queen!"],
             [f"Push the {f}-Pawn to {to}, Free the Queen!"]]
    elif key == "space":
        t = [[f"Gain Space with the {f}-Pawn!", f"Grab Space with the {f}-Pawn!",
              f"Push the {f}-Pawn into Their Half!"], [f"Gain Space with the {f}-Pawn on {to}!"]]
    elif key == "stride":
        t = [[f"March the {f}-Pawn Two Squares!", f"Push the {f}-Pawn Two Squares!",
              f"Advance the {f}-Pawn Two Squares!"]]
    elif key == "push":
        if rank_of(r.end, r.turn) <= 3:
            t = [covering(r, board_), [f"Push the {f}-Pawn to {to}!"]]
        else:
            t = [[f"Push the {f}-Pawn!", f"Advance the {f}-Pawn!", f"Nudge the {f}-Pawn Forward!"],
                 [f"Push the {f}-Pawn to {to}!"]]
    elif key == "forfeit":
        t = [["Give Up the Right to Castle!", "Forfeit Castling!"],
             [f"Step the King to {to}, Forfeit Castling!", f"Move the King to {to}, Give Up Castling!"]]
    elif key == "activate":
        base = ["Activate the King!", "Bring the King Into Play!"]
        if to_centre(r.end) < to_centre(r.start):
            base.append("Centralise the King!")
        if r.advance > 0:
            base.append("March the King Up!")
        t = [base, [f"March the King to {to}!", f"Activate the King on {to}!"]]
    elif key == "opposition":
        t = [["Take the Opposition!", "Seize the Opposition!", "Face Down the King, Take the Opposition!"],
             [f"Take the Opposition on {to}!"]]
    elif key == "behind-passer":
        t = [["Put the Rook Behind the Passed Pawn!", "Back the Passed Pawn from Behind!"],
             [f"Put the Rook Behind the Passed {r.behind_passer}-Pawn!"],
             fit(f"Put {exact} Behind the Passed Pawn!")]
    elif key == "tuck":
        t = [["Tuck the King into the Corner!", "Hide the King in the Corner!"], [f"Tuck the King into {to}!"]]
    elif key == "king":
        base = (["Step the King Up!", "Walk the King Forward!"] if r.advance > 0 else
                ["Step the King Back!", "Pull the King Back!"] if r.advance < 0 else
                ["Step the King Aside!", "Shift the King Over!"])
        t = [base, [f"Step the King to {to}!", f"Walk the King to {to}!"]]
    elif key == "seventh":
        t = ladder(["Invade the Seventh Rank!", "Seize the Seventh Rank!", "Storm the Seventh Rank!"],
                   f"Invade the Seventh with {by}!")
        t[1] = [f"Invade the Seventh with {by}!", f"Put {by} on the Seventh!"]
    elif key == "battery":
        F = FILES[r.end % 8]
        nth = NTH.get(rank_of(r.end, r.turn), "Back")
        if {r.kind, r.battery} == {"r"}:
            if r.battery_line == "file":
                t = [["Double the Rooks!", "Double Rooks on the File!"], [f"Double Rooks on the {F}-File!"]]
            else:
                t = [["Double the Rooks!", "Double Rooks on the Rank!"], [f"Double Rooks on the {nth} Rank!"]]
        elif "b" in (r.kind, r.battery):
            t = [["Line Up Queen and Bishop!", "Build a Queen and Bishop Battery!"],
                 [f"Line Up Queen and Bishop on {to}!"]]
        elif r.battery_line == "file":
            t = [["Line Up Queen and Rook!", "Stack Queen and Rook!"], [f"Stack Queen and Rook on the {F}-File!"]]
        else:
            t = [["Line Up Queen and Rook!", "Line Up the Heavy Pieces!"],
                 [f"Line Up Queen and Rook on the {nth} Rank!"]]
        if r.battery_king:
            t[0] = ["Aim the Battery at the King!", "Train the Battery on the King!"]
    elif key == "open-file":
        F = FILES[r.end % 8]
        kind_of = "Open" if r.open_file == "open" else "Half-Open"
        base = ["Seize the Open File!", "Take the Open File!", "Grab the Open File!"] if kind_of == "Open" else [
            "Take the Half-Open File!", "Seize the Half-Open File!"]
        t = [base, [f"Seize the {kind_of} {F}-File!", f"Take the {kind_of} {F}-File!"],
             [f"Seize the {kind_of} {F}-File with {exact}!"]]
    elif key == "rook-forfeit":
        t = [[f"Give Up Castling {r.gives_up}!", f"Forfeit Castling {r.gives_up}!"],
             [f"Move the Rook to {to}, Give Up Castling {r.gives_up}!"]]
    elif key == "connect":
        t = ladder(["Connect the Rooks!", "Link Up the Rooks!"], f"Move the {P}, Connect the Rooks!")
    elif key == "lift":
        t = [["Lift the Rook!", "Make a Rook Lift!"], [f"Lift the Rook to the {NTH[rank_of(r.end, r.turn)]} Rank!"],
             [f"Lift the Rook to {to}!"]]
    elif key == "sortie":
        t = [["Bring Out the Queen Early!", "Send the Queen Out Early!", "Launch an Early Queen Sortie!"],
             [f"Bring the Queen Out to {to}!", f"Send the Queen Out to {to}!"]]
    elif key == "centralise":
        t = [[f"Centralise the {P}!", f"Post the {P} in the Centre!", f"Bring the {P} to the Centre!"],
             [f"Centralise the {P} on {to}!"], fit(f"Centralise {exact} on {to}!")]
    elif key == "diagonal":
        t = [["Seize the Long Diagonal!", "Command the Long Diagonal!", "Rule the Long Diagonal!"],
             [f"Seize the Long Diagonal on {to}!"], fit(f"{go_exact}, Seize the Long Diagonal!")]
    elif key == "aim":
        t = [[f"Aim the {P} at the King!", f"Train the {P} on the King!", f"Line Up the {P} on the King!"],
             [f"Aim the {P} at the King from {to}!"], fit(f"Aim {exact} at the King from {to}!")]
    elif key == "rim":
        t = [["Put the Knight on the Rim!", "Send the Knight to the Rim!", "Park the Knight on the Edge!"],
             [f"Put the Knight on the Rim at {to}!"], fit(f"Put {exact} on the Rim at {to}!")]
    elif key == "retreat":
        t = [[f"Pull the {P} Back!", f"Retreat the {P}!", f"Fall Back with the {P}!", f"Drop the {P} Back!"],
             [f"Pull the {P} Back to {to}!", f"Retreat the {P} to {to}!"], fit(f"Retreat {exact} to {to}!")]
    elif key == "invade":
        t = [[f"Invade with the {P}!", f"Send the {P} into Enemy Territory!", f"Push the {P} into Their Half!"],
             [f"Invade with the {P} on {to}!"], fit(f"Invade on {to} with {exact}!")]
    elif key == "long":
        t = [[f"Swing the {P} Across the Board!", f"Sweep the {P} Across the Board!"], [f"Swing the {P} Over to {to}!"],
             fit(f"Swing {exact} Over to {to}!")]
    else:  # quiet
        if r.advance > 0:
            t = [[f"Advance the {P}!", f"Bring the {P} Forward!", f"Move the {P} Up!"],
                 [f"Advance the {P} to {to}!", f"Bring the {P} Up to {to}!"], [f"Advance {exact} to {to}!"]]
        else:
            t = [[f"Shift the {P}!", f"Redeploy the {P}!", f"Regroup the {P}!"],
                 [f"Shift the {P} to {to}!", f"Redeploy the {P} to {to}!"], [f"Shift {exact} to {to}!"]]
    last = (f"Promote on {to} from {frm} to a {N}!" if r.crown else f"Move the {P} from {frm} to {to}!")
    t = [[title for title in tier if len(title) <= LONGEST] for tier in t] + [[last]]
    return [tier for tier in t if tier]


def covering(r: Reading, board_: Board) -> list[str]:
    """A pawn step's titles for the square it newly guards: covered when empty, supported when a piece of its own
    stands there, struck at when one of the other side's does."""
    c, f = label(r.covers), FILES[r.start % 8]
    there = board_.position.board[r.covers]
    if not there:
        return [f"Cover {c} with the {f}-Pawn!", f"Push the {f}-Pawn to Cover {c}!", f"Guard {c} with the {f}-Pawn!"]
    if side(there) == r.turn:
        return [f"Support {c} with the {f}-Pawn!", f"Back Up {c} with the {f}-Pawn!"]
    return [f"Strike at {c} with the {f}-Pawn!", f"Challenge {c} with the {f}-Pawn!"]


def bishop_name(board, square: int) -> str:
    """A bishop as a player names it: the King's Bishop or the Queen's, by the colour of its squares, or plain
    Bishop when its side has two of one colour."""
    piece = board[square]
    us, light = side(piece), (square % 8 + square // 8) % 2 == 1
    alike = sum(1 for i, p in enumerate(board) if p == piece and ((i % 8 + i // 8) % 2 == 1) == light)
    if alike != 1:
        return "Bishop"
    return "King's Bishop" if light == (us == "w") else "Queen's Bishop"


def pick(key: str, uci: str, level: int, count: int) -> int:
    """Which of a tier's `count` synonyms a move takes: a hash of the position, the move and the tier, so the same
    position always gives the same title and different positions vary."""
    return int.from_bytes(hashlib.sha256(f"{key}|{uci}|{level}".encode()).digest()[:8], "big") % count


def assign(key: str, ucis: list[str], options: list[list[list[str]]]) -> list[str]:
    """One title for each move: every move starts at its plainest tier, and moves whose titles say the same thing
    (the first synonym of their tiers alike) or read the same (the picked synonyms alike) step up a tier together,
    until no two titles on the board are alike."""
    level = [0] * len(options)
    while True:
        canon = [options[i][level[i]][0] for i in range(len(options))]
        shown = [options[i][level[i]][pick(key, ucis[i], level[i], len(options[i][level[i]]))]
                 for i in range(len(options))]
        groups: dict = defaultdict(list)
        for i in range(len(options)):
            groups["canon", canon[i]].append(i)
            groups["shown", shown[i]].append(i)
        clashing = {i for members in groups.values() if len(members) > 1 for i in members}
        climbing = {i for i in clashing if level[i] < len(options[i]) - 1}
        if not climbing:
            return shown
        for i in climbing:
            level[i] += 1


def words(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> str:
    """The move in plain English: `Knight from g1 to f3`, `Pawn from c7 takes the knight on d6, check`."""
    board = position.board
    kind = board[move.start].lower()
    start, end = FILES[move.start % 8] + str(move.start // 8 + 1), FILES[move.end % 8] + str(move.end // 8 + 1)
    if kind == "k" and abs(move.end - move.start) == 2:
        text = "Castle kingside" if move.end > move.start else "Castle queenside"
    elif kind == "p" and move.end == position.ep and not board[move.end]:
        text = f"Pawn from {start} takes the pawn on {end[0]}{start[1]}, en passant"
    elif board[move.end]:
        text = f"{PIECES[kind].capitalize()} from {start} takes the {PIECES[board[move.end].lower()]} on {end}"
    elif kind == "p" and abs(move.end - move.start) == 16:
        text = f"Pawn from {start} to {end}, two squares"
    else:
        text = f"{PIECES[kind].capitalize()} from {start} to {end}"
    if move.promotion:
        text += f", becoming a {PIECES[move.promotion]}"
    after = make(position, move) if after is None else after
    replies = legal_moves(after) if replies is None else replies
    if in_check(after):
        text += ", checkmate" if not replies else ", check"
    elif not replies:
        text += ", stalemate"
    return text


# A preposition of four letters or more takes a capital in a title, as the other three games write theirs:
# "Cover b4 With the a-Pawn!", as Checkers' "Open With Old Faithful!" and Tic-Tac-Toe's "Save the Draw From
# the Centre!".
LONG_PREPOSITION = re.compile(r"(?<= )(with|into|from|onto|over|upon)(?= )")


def cased(title: str) -> str:
    """The title with its long prepositions capitalised."""
    return LONG_PREPOSITION.sub(lambda m: m.group(1).capitalize(), title)


def listing(position: Position, game: int = 0, ply: int = 0) -> list[dict]:
    """Every legal move in the list's order, each with its SAN, its words and a title no other move here has. The
    names depend on the position alone: `game` and `ply` are taken for the callers that pass them, and unused."""
    return copy.deepcopy(_listing(fen4(position)))


@functools.lru_cache(maxsize=256)
def _listing(key: str) -> list[dict]:
    board_ = survey(key)
    position = board_.position
    legal = list(board_.moves)
    order = {"q": 0, "r": 1, "b": 2, "n": 3, "": 4}
    moves = sorted(legal, key=lambda m: (ORDER.index(position.board[m.start].lower()), m.end % 8, -(m.end // 8),
                                         m.start, order[m.promotion]))
    readings = [reading(key, move) for move in moves]
    options = [tiers(r, board_) for r in readings]
    titles = assign(key, [move.uci for move in moves], options)
    out = []
    for move, r, title in zip(moves, readings, titles, strict=True):
        after, replies = board_.after[move], board_.replies[move]
        emoji = WARNING if (theme(r) == "stalemate" and r.ahead >= 3) or r.dead == "thrown" else EMOJI[theme(r)]
        out.append({"uci": move.uci, "san": san(position, move, legal, replies),
                    "piece": PIECES[position.board[move.start].lower()], "emoji": emoji, "title": cased(title),
                    "words": words(position, move, after, replies)})
    return out
