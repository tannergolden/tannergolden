# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named as players name it: an emoji, a name, and the move in plain English.

  from chess_names import listing, words

A name is what a chess player calls the move, and it says what the move is,
never where it goes or what it does to the game. The rules' own moves go by
the rules' own names: Kingside Castling and Queenside Castling, En Passant,
a Promotion to Queen, and an Underpromotion to Rook, to Bishop or to Knight.
A capture reads as descriptive notation reads one, the piece that takes and
the piece it takes: "Knight Takes Bishop", "Pawn Takes Pawn". A pawn's push
is a Pawn Push, or a Double Pawn Push when it goes two squares; any other
piece going back toward its own side makes a retreat ("Bishop Retreat"),
and any other move is its piece's ("Knight Move", "King Move"). No name
holds a square, so one name fits many moves on a board, and the notation
and the words beside it tell them apart.

Nothing in a name looks past the move. No name, emoji, notation or words
says check, mate or stalemate, a threat, an attack or a defence, what a
capture comes to, an opening the books name, or a plan, so a move that mates
and a move that gives the queen away read just as any other move of their
piece does. A player choosing from the list learns nothing from it that the
board does not already show.

The emoji is the kind of move, the same for every move of that kind: 🏰 for
castling, 👑 for a promotion, ⚔️ for any other capture, and otherwise the
piece's own: 🤴 the king, 👸 the queen, 🗼 a rook, ⛪ a bishop, 🐴 a knight,
♟️ a pawn. The notation is SAN without its marks for check and mate, a
capture keeping its x. The words say the move exactly, as a score sheet
would: "Knight from g1 to f3", "Pawn from e2 to e4, two squares", "Queen
from e5 takes the knight on d6", "Pawn from e5 takes the pawn on d5, en
passant", "Pawn from b7 takes the rook on a8, becoming a queen", "King from
e1 to g1, castling kingside".

A name depends on the move alone, never on the game, the move number, the
clocks or chance, so the same position always names its moves the same way.
Naming reads the board as it stands and plays nothing out, so it is quick.
Stdlib only, with chess_rules.py beside it.
"""
from __future__ import annotations

from chess_rules import FILES, Move, Position, label, legal_moves

PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
KINDS = {kind: piece.capitalize() for kind, piece in PIECES.items()}  # as a title names a piece: Knight
ORDER = "kqrbnp"  # the list's order: the king's moves first, the pawns' last
PROMOTIONS = "qrbn"  # a promotion's four moves, the queen first
PROMOTED = {"q": "Promotion to Queen", "r": "Underpromotion to Rook", "b": "Underpromotion to Bishop",
            "n": "Underpromotion to Knight"}  # what a promotion is called by what it makes
LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
# One emoji to a kind of move, the same for every move of that kind: castling, a promotion, any other capture, and
# otherwise the piece that moves.
EMOJI = {"castle": "🏰", "promotion": "👑", "capture": "⚔️",
         "k": "🤴", "q": "👸", "r": "🗼", "b": "⛪", "n": "🐴", "p": "♟️"}


def rank_of(index: int, turn: str) -> int:
    """The square's rank as `turn` counts it, from 0 for its own back rank to 7 for the other side's."""
    return index // 8 if turn == "w" else 7 - index // 8


def castling(position: Position, move: Move) -> bool:
    """Whether the move castles: the king going two squares along its rank."""
    return position.board[move.start].lower() == "k" and abs(move.end - move.start) == 2


def captured(position: Position, move: Move) -> int | None:
    """The square of the piece the move takes (for en passant, the pawn that passed it), or None."""
    if position.board[move.end]:
        return move.end
    if (position.board[move.start].lower() == "p" and move.end == position.ep
            and move.start % 8 != move.end % 8):
        return move.end - 8 if position.turn == "w" else move.end + 8
    return None


def title(position: Position, move: Move) -> str:
    """The move's name as a player calls it, which holds no square: `Kingside Castling`, `Promotion to Queen`,
    `Underpromotion to Knight`, `En Passant`, `Knight Takes Bishop`, `Pawn Push`, `Double Pawn Push`, `Bishop
    Retreat`, `Queen Move`."""
    board = position.board
    kind = board[move.start].lower()
    if castling(position, move):
        return "Kingside Castling" if move.end > move.start else "Queenside Castling"
    if move.promotion:
        return PROMOTED[move.promotion]
    at = captured(position, move)
    if at is not None:
        return "En Passant" if at != move.end else f"{KINDS[kind]} Takes {KINDS[board[at].lower()]}"
    if kind == "p":
        return "Double Pawn Push" if abs(move.end - move.start) == 16 else "Pawn Push"
    if kind != "k" and rank_of(move.end, position.turn) < rank_of(move.start, position.turn):
        return f"{KINDS[kind]} Retreat"
    return f"{KINDS[kind]} Move"


def emoji(position: Position, move: Move) -> str:
    """The kind of move: castling, a promotion, any other capture, or else the piece that moves."""
    if castling(position, move):
        return EMOJI["castle"]
    if move.promotion:
        return EMOJI["promotion"]
    if captured(position, move) is not None:
        return EMOJI["capture"]
    return EMOJI[position.board[move.start].lower()]


def notation(position: Position, move: Move, legal: list[Move]) -> str:
    """The move in SAN without its marks for check and mate: `Nf3`, `exd5`, `Rad1`, `O-O`, `e8=Q`. A capture keeps
    its x. `legal` is the position's legal moves, which say whether another piece of the kind could go there too."""
    board = position.board
    piece = board[move.start]
    kind = piece.lower()
    if castling(position, move):
        return "O-O" if move.end > move.start else "O-O-O"
    if kind == "p":
        text = (FILES[move.start % 8] + "x" if move.start % 8 != move.end % 8 else "") + label(move.end)
        return text + ("=" + move.promotion.upper() if move.promotion else "")
    rivals = [other for other in legal if other.end == move.end and other.start != move.start
              and board[other.start] == piece]
    which = ""
    if rivals:
        if all(rival.start % 8 != move.start % 8 for rival in rivals):
            which = FILES[move.start % 8]
        elif all(rival.start // 8 != move.start // 8 for rival in rivals):
            which = str(move.start // 8 + 1)
        else:
            which = label(move.start)
    return kind.upper() + which + ("x" if board[move.end] else "") + label(move.end)


def words(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> str:
    """The move in plain English: `Knight from g1 to f3`, `Pawn from c5 takes the knight on d6`. `after` and
    `replies` are taken for the callers that pass them, and unused: the words never say where the move leads."""
    board = position.board
    kind = board[move.start].lower()
    start, end = label(move.start), label(move.end)
    at = captured(position, move)
    if castling(position, move):
        text = f"King from {start} to {end}, castling {'kingside' if move.end > move.start else 'queenside'}"
    elif at is not None and at != move.end:
        text = f"Pawn from {start} takes the pawn on {label(at)}, en passant"
    elif at is not None:
        text = f"{KINDS[kind]} from {start} takes the {PIECES[board[at].lower()]} on {end}"
    elif kind == "p" and abs(move.end - move.start) == 16:
        text = f"Pawn from {start} to {end}, two squares"
    else:
        text = f"{KINDS[kind]} from {start} to {end}"
    if move.promotion:
        text += f", becoming a {PIECES[move.promotion]}"
    return text


def listing(position: Position, game: int = 0, ply: int = 0) -> list[dict]:
    """Every legal move in the list's order, the king's first and the pawns' last, each with its SAN, its piece,
    its emoji, its words and its name. The names depend on the move alone: `game` and `ply` are taken for the
    callers that pass them, and unused."""
    board = position.board
    legal = legal_moves(position)
    moves = sorted(legal, key=lambda m: (ORDER.index(board[m.start].lower()), m.end % 8, -(m.end // 8), m.start,
                                         PROMOTIONS.index(m.promotion) if m.promotion else len(PROMOTIONS)))
    return [{"uci": move.uci, "san": notation(position, move, legal), "piece": PIECES[board[move.start].lower()],
             "emoji": emoji(position, move), "title": title(position, move), "words": words(position, move)}
            for move in moves]
