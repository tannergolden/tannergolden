# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named for what it is: an emoji, a title, and the move in plain English.

  from chess_names import listing, words

A title is an order in chess's own words that says what the move is, and
never what it does to the game: the piece that moves, by the name its side
gives it; the square it goes to, and whether that is forward, back or along
its rank; what it takes, when it takes; and what the rules make of it:
castling, promotion and to what, en passant. "Bring Out the King's Knight
to f3!", "March the e-Pawn Two Squares!", "Take the Knight on d6 With the
e-Pawn!", "Castle Kingside!", "Take the Rook on a8 From b7, Crown a Queen!".

Nothing in a name looks past the move. No title, emoji, notation or words
says check, mate or stalemate, a threat, an attack or a defence, what a
capture comes to, an opening the books name, or a plan, so a move that mates
and a move that gives the queen away read just as any other move of their
piece does. A player choosing from the list learns nothing from it that the
board does not already show.

A piece is named as its side names it from where it stands: a knight or
a rook on its home square by the wing it starts on (the King's Knight on
g1, the Queen's Rook on a8), a bishop by the colour of its squares while
it is its side's only bishop of that colour (the King's Bishop is
White's on the light squares and Black's on the dark), a pawn by its
file, the king and the queen by themselves, and any other piece by its
kind. The verb says the way it goes: a pawn is pushed one square or
marched two; a knight, a bishop or the queen going forward from its home
square is brought out; any other piece going forward is sent, one going
back is brought back, a rook or a queen going along its rank is swung,
and the king steps forward, back or across. A capture takes, castling
castles, and a pawn reaching the last rank is crowned. When two moves
would read alike, as when two knights can reach one square, each names
the square its piece leaves.

The emoji is the kind of move, the same for every move of that kind: 🏰 for
castling, 👑 for a promotion, ⚔️ for any other capture, and otherwise the
piece's own: 🤴 the king, 👸 the queen, 🗼 a rook, ⛪ a bishop, 🐴 a knight,
♟️ a pawn. The notation is SAN without its marks for check and mate, a
capture keeping its x. The words say the move exactly, as a score sheet
would: "Knight from g1 to f3", "Pawn from e2 to e4, two squares", "Queen
from e5 takes the knight on d6", "Pawn from e5 takes the pawn on d5, en
passant", "Pawn from b7 takes the rook on a8, becoming a queen", "King from
e1 to g1, castling kingside".

A name depends on the position and the move alone, never on the game, the
move number, the clocks or chance, so the same position always names its
moves the same way, and no two moves on one board share a title. Naming
reads the board as it stands and plays nothing out, so it is quick. Stdlib
only, with chess_rules.py beside it.
"""
from __future__ import annotations

from collections import Counter

from chess_rules import FILES, Move, Position, label, legal_moves, side

PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
KINDS = {kind: piece.capitalize() for kind, piece in PIECES.items()}  # as a title names a piece: Knight
ORDER = "kqrbnp"  # the list's order: the king's moves first, the pawns' last
PROMOTIONS = "qrbn"  # a promotion's four moves, the queen first
BACK_RANK = "rnbqkbnr"  # each file's piece on its side's back rank, from a to h, as the game sets them out
LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
# One emoji to a kind of move, the same for every move of that kind: castling, a promotion, any other capture, and
# otherwise the piece that moves.
EMOJI = {"castle": "🏰", "promotion": "👑", "capture": "⚔️",
         "k": "🤴", "q": "👸", "r": "🗼", "b": "⛪", "n": "🐴", "p": "♟️"}


def rank_of(index: int, turn: str) -> int:
    """The square's rank as `turn` counts it, from 0 for its own back rank to 7 for the other side's."""
    return index // 8 if turn == "w" else 7 - index // 8


def light(index: int) -> bool:
    """Whether the square is a light one: h1 is, a1 is not."""
    return (index % 8 + index // 8) % 2 == 1


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


def at_home(board: tuple[str, ...], index: int) -> bool:
    """Whether the piece on the square stands where the game sets one of its kind out: a knight on b1 or g1, a
    bishop on c1 or f1, a rook on a1 or h1 or the queen on d1, and on the eighth rank for Black."""
    piece = board[index]
    return rank_of(index, side(piece)) == 0 and BACK_RANK[index % 8] == piece.lower()


def called(board: tuple[str, ...], index: int) -> str:
    """The piece on the square as its side calls it: the King, the Queen, the e-Pawn; the King's or Queen's Knight
    and Rook on their home squares; the King's or Queen's Bishop by the colour of its squares, while it is the only
    one of its side on them; or the Knight, the Rook or the Bishop."""
    piece = board[index]
    kind, turn = piece.lower(), side(piece)
    if kind == "p":
        return f"the {FILES[index % 8]}-Pawn"
    if kind == "b":
        shade = light(index)
        if sum(1 for i, other in enumerate(board) if other == piece and light(i) == shade) == 1:
            return f"the {'King' if shade == (turn == 'w') else 'Queen'}'s Bishop"
    elif kind in "nr" and at_home(board, index):
        return f"the {'King' if index % 8 >= 4 else 'Queen'}'s {KINDS[kind]}"
    return f"the {KINDS[kind]}"


def titles(position: Position, move: Move) -> tuple[str, str]:
    """The move's title, and the same title naming the square its piece leaves, for a board where two moves would
    otherwise read alike. Only a knight, a bishop, a rook or a queen can ever need the second, since a pawn is
    named by its file and there is one king."""
    board, turn = position.board, position.turn
    kind = board[move.start].lower()
    to, start, file = label(move.end), label(move.start), FILES[move.start % 8]
    if castling(position, move):
        title = "Castle Kingside!" if move.end > move.start else "Castle Queenside!"
        return title, title
    at = captured(position, move)
    victim = KINDS[board[at].lower()] if at is not None else ""
    if move.promotion:
        way = f"Take the {victim} on {to} From {start}" if victim else f"Push the {file}-Pawn to {to}"
        title = f"{way}, Crown a {KINDS[move.promotion]}!"
        return title, title
    if at is not None and at != move.end:
        title = f"Take the Pawn on {label(at)} en Passant With the {file}-Pawn!"
        return title, title
    name, piece = called(board, move.start), KINDS[kind]
    if victim:
        title = f"Take the {victim} on {to} With {name}!"
        if kind == "p":
            return title, title
        return title, f"Take the {victim} on {to} With the {piece} From {start}!"
    if kind == "p":
        two = abs(move.end - move.start) == 16
        title = f"March the {file}-Pawn Two Squares!" if two else f"Push the {file}-Pawn to {to}!"
        return title, title
    rise = rank_of(move.end, turn) - rank_of(move.start, turn)
    if kind == "k":
        title = f"Step the King {'Forward' if rise > 0 else 'Back' if rise < 0 else 'Across'} to {to}!"
        return title, title
    if rise > 0 and kind in "nbq" and at_home(board, move.start):
        return f"Bring Out {name} to {to}!", f"Bring Out the {piece} From {start} to {to}!"
    if rise > 0:
        return f"Send {name} to {to}!", f"Send the {piece} From {start} to {to}!"
    if rise < 0:
        return f"Bring {name} Back to {to}!", f"Bring the {piece} Back From {start} to {to}!"
    return f"Swing {name} to {to}!", f"Swing the {piece} From {start} to {to}!"


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
    its emoji, its words and a title no other move here has. The names depend on the position alone: `game` and
    `ply` are taken for the callers that pass them, and unused."""
    board = position.board
    legal = legal_moves(position)
    moves = sorted(legal, key=lambda m: (ORDER.index(board[m.start].lower()), m.end % 8, -(m.end // 8), m.start,
                                         PROMOTIONS.index(m.promotion) if m.promotion else len(PROMOTIONS)))
    named = [titles(position, move) for move in moves]
    alike = Counter(title for title, _ in named)
    return [{"uci": move.uci, "san": notation(position, move, legal), "piece": PIECES[board[move.start].lower()],
             "emoji": emoji(position, move), "title": exact if alike[title] > 1 else title,
             "words": words(position, move)}
            for move, (title, exact) in zip(moves, named, strict=True)]
