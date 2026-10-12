# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: an emoji, a title, and what the move does in plain English.

  from checkers_names import name, named

A title is a commander's call in checkers' own words, so a player who knows
the game knows the move by its name: "Open the Kelso!", "Answer With the
Single Corner!", "Fire the Two-for-One Shot!", "King Me!", "Break the
Bridge!", "Drive the King From the Double Corner!". It never claims what the
move does not do, and it never praises a move that loses: a move that gives a
man away for nothing is called that, under a warning sign. The words say the
move exactly, as a score sheet would: "Man from 11 to 15", "Man from 20 jumps
16, landing on 11", "King from 21 jumps 25, landing on 30". Black (GitHub,
the dark men on 1 to 12) moves first and White (the house, on 21 to 32)
replies; the rules' letters for the sides, d and l, never reach a reader.

`read` takes a move apart, and `theme` picks the most telling thing it does.
The readings, in the order they win:

  1. It leaves the other side no move: it takes their last piece, or blocks
     every piece they have. The winning move. 🏆
  2. It completes a named opening (below). 📖
  3. What the jumps that follow by force come to. A capture is compulsory,
     so a move that leaves the other side a jump starts a run of captures
     both sides must make, each taking the best it can, and counting what
     each side takes says what the move really does. One that loses pieces
     this way when another move does not is the blunder (⚠️), unless it
     gives a man for a king of ours, crowned on the way or as soon as the
     way is clear (🎁); when every move loses, the least loss cuts our
     losses (🩸). One that gives pieces and takes more back is a shot (💣),
     "the two-for-one".
  4. The only move that loses nothing, when every other loses something. 🔑
  5. Crowning a man, by a step or at the end of a jump. 👑
  6. An exchange: it gives and takes back as many, give one, take one. ⚖️
  7. A jump, by what it takes: one (⚔️), two (💥), three or more (🔥); a
     king, a man taken for free (nothing jumps back), or the only move there
     is, which the rules force.
  8. In the endgame, driving a lone king out of the double corner, where it
     shuttles between the corner's two squares to hold the draw. 🧹
  9. A squeeze: every move they have now loses material by force, and the
     piece of theirs with nowhere safe to step, or their last, is trapped. 🕸️
 10. Running a man to one step from the crown, perhaps past stopping. 🏃
 11. Threatening a jump that wins a piece (🏹); slipping a threatened piece
     out of reach (💨); guarding one (🛡️), often by backing it up on the
     square the jump would land on.
 12. The only legal move, when nothing else is told of it. ☝️
 13. A man stepping into the dog hole (🕳️): for White, 5 against Black's
     man on 1, or 12 against the man on 3; for Black, 28 against White's man
     on 32, or 21 against the man on 30, where it can't move until the man
     holding it does. Breaking the bridge, the men on 1 and 3 for Black and
     on 30 and 32 for White that guard the king row (🌉).
 14. A king's move: into a double corner, or shuttling within one (🏰); to
     the centre, forward or back (⚜️).
 15. A man brought out of the back row or the single corner, perhaps with
     the bridge kept. 🚪
 16. Where a man goes: the centre, 14, 15, 18 and 19 (🎯); beside a piece of
     theirs it leaves with no step at all (🚧); the edge (🧱); the long
     diagonal from 4 to 29 (🛤️); or up its single-corner or double-corner
     side, the halves of the board on its single corner's hand and its
     double corner's (👣).

The emoji is the reading's, one to a reading, so the column reads as a key.
A title is drawn from its reading's calls, chosen by the position, and when
two moves on one board share a reading, each says which it is with a true
detail: the square its piece moves from or lands on, the piece it threatens
or saves, or for jumps that share both ends, where it jumps first. No two
moves on one board share a title, and the same position and move always give
the same one.

The openings. A move that completes a named opening is named for it: Black's
first move ("Open the Kelso!"), White's reply ("Answer With the Single
Corner!"), and the later moves that make the named lines ("Enter the
Glasgow!"). A position reached by the same moves in another order is the
same opening. Only names found with the same moves in at least two of these
sources are used:

  [B] Encyclopaedia Britannica, 11th edition (1911), "Draughts".
  [H] Professor Hoffmann, Hoyle's Games Modernized (1923), "Draughts",
      Project Gutenberg ebook 39445.
  [R] Fred Reinfeld, How to Win at Checkers (1957), its opening groups.
  [S] startcheckers.com, the 11-15, 10-15 and 11-16 opening pages.
  [Q] John Savard, quadibloc.com, "Checkers" and its openings.
  [L] Solitaire Laboratory, "Checkers and Draughts".
  [O] The Orac and SAGE draughts guide, github.com/orac81/Orac-Draughts.
  [N] Bob Newell, The Checker Maven and its lessons, bobnewell.net.
  [I] Irish Draughts, "What's a good opening move?", irishdraughts.org.
  [F] Martin Fierz, Cake, its evaluation (github.com/martinfierz/cake).

  9-13 the Edinburgh [R O Q]; 9-14 the Double Corner [R O Q]; 10-14 the
  Denny [R O Q]; 10-15 the Kelso [R O Q]; 11-15 Old Faithful [Q I]; 11-16
  the Bristol [R O Q]; 12-16 the Dundee [R O B]. 11-15 21-17 the Switcher
  [B S]; 11-15 22-18 the Single Corner [H O S]; 11-15 23-18 the Cross [H O];
  11-15 24-19 the Second Double Corner [B H O]; 11-15 24-20 the Ayrshire
  Lassie [B N]; 10-15 23-18 the Kelso Cross [B S]; 11-16 23-18 the Bristol
  Cross [S L]; 11-16 24-19 the Paisley [S L]. 11-15 22-17 15-19 the Dyke
  [H S]; 11-15 23-19 9-13 the Will o' the Wisp [H S]; 11-16 24-20 16-19 the
  Bristol [H Q]. 11-15 23-19 9-14 27-23 the Defiance [H O]; 11-15 23-18 8-11
  18-14 the Waterloo [S Q]. 11-15 23-19 8-11 22-17, then 4-8 the Old
  Fourteenth [H O S], 11-16 the Glasgow [B H], 9-13 the Laird and Lady
  [H S] and 3-8 the Alma [B S]; 11-15 23-19 9-14 22-17, then 5-9 the Fife
  [H S], 6-9 the Souter [H S] and 7-11 the Whilter [H S]; 11-15 22-17 8-11
  17-13 15-18 the Maid of the Mill [H S].

The bridge is [O N]'s, and the dog holes are [O F]'s. The Pioneer is left
out, since its sources give it different moves, and the three-move ballots
go unnumbered, since no copy of their list could be read; those with a name
of their own, such as the Dyke and the Will o' the Wisp, are named above.
Stdlib only, with checkers_rules.py beside it.
"""
from __future__ import annotations

import functools
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from operator import attrgetter

from checkers_rules import (
    CROWN,
    HOME,
    OWN,
    SQUARES,
    START,
    STEPS,
    Move,
    Position,
    find,
    jumps,
    legal_moves,
    make,
    other,
    row_col,
)

BLACK = START.turn  # GitHub plays Black, the dark men on 1 to 12, and moves first
WHITE = other(BLACK)  # the house plays White, on 21 to 32
LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
NUMBERS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")
JUMPS = {2: "Double", 3: "Triple"}  # a jump of two or three, as a checkers player calls it
ORDINALS = ("First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth",
            "Eleventh", "Twelfth")

# --- the board's places ------------------------------------------------------------------------------------------
CENTRE = frozenset((14, 15, 18, 19))  # the four squares in the middle
EDGE = frozenset(square for square in SQUARES if row_col(square)[1] in (0, 7))  # 4, 5, 12, 13, 20, 21, 28, 29
LONG_DIAGONAL = frozenset((4, 8, 11, 15, 18, 22, 25, 29))  # the single-corner diagonal, from corner to corner
DOUBLE_CORNERS = (frozenset((1, 5)), frozenset((28, 32)))  # Black's and White's: two squares, side by side
BRIDGE = {BLACK: (1, 3), WHITE: (30, 32)}  # the two back-row men that guard each side's king row [O N]
SINGLE_CORNER = {BLACK: (4, 8), WHITE: (29, 25)}  # each side's single corner and the square in front of it [O]
# A man of the side on the hole, held by the other side's man on the square beside it, can't move till that man
# does: the dog holes [O F].
DOG_HOLES = {WHITE: {5: 1, 12: 3}, BLACK: {28: 32, 21: 30}}

# --- the openings --------------------------------------------------------------------------------------------------
# Each named opening as the moves that make it from the start, the last of them the move named for it. The sources
# that give each name these moves are listed above.
OPENINGS = (
    ("the Edinburgh", "9-13"), ("the Double Corner", "9-14"), ("the Denny", "10-14"), ("the Kelso", "10-15"),
    ("Old Faithful", "11-15"), ("the Bristol", "11-16"), ("the Dundee", "12-16"),
    ("the Switcher", "11-15 21-17"), ("the Single Corner", "11-15 22-18"), ("the Cross", "11-15 23-18"),
    ("the Second Double Corner", "11-15 24-19"), ("the Ayrshire Lassie", "11-15 24-20"),
    ("the Kelso Cross", "10-15 23-18"), ("the Bristol Cross", "11-16 23-18"), ("the Paisley", "11-16 24-19"),
    ("the Dyke", "11-15 22-17 15-19"), ("the Will o' the Wisp", "11-15 23-19 9-13"),
    ("the Bristol", "11-16 24-20 16-19"),
    ("the Defiance", "11-15 23-19 9-14 27-23"), ("the Waterloo", "11-15 23-18 8-11 18-14"),
    ("the Old Fourteenth", "11-15 23-19 8-11 22-17 4-8"), ("the Glasgow", "11-15 23-19 8-11 22-17 11-16"),
    ("the Laird and Lady", "11-15 23-19 8-11 22-17 9-13"), ("the Alma", "11-15 23-19 8-11 22-17 3-8"),
    ("the Fife", "11-15 23-19 9-14 22-17 5-9"), ("the Souter", "11-15 23-19 9-14 22-17 6-9"),
    ("the Whilter", "11-15 23-19 9-14 22-17 7-11"), ("the Maid of the Mill", "11-15 22-17 8-11 17-13 15-18"),
)


def opening_title(name_: str, codes: tuple[str, ...]) -> str:
    """The call for the move that completes the opening: Black's first move opens it, White's reply answers with it,
    and a later move enters the line, or completes the one its first move already named."""
    if len(codes) == 1:
        return f"Open {name_}!" if name_.startswith("the ") else f"Open With {name_}!"
    if len(codes) % 2 == 0:
        return f"Answer With {name_}!"
    first = next(title for title, moves in OPENINGS if moves == codes[0])
    return f"Complete {name_}!" if first == name_ else f"Enter {name_}!"


def _book() -> dict[tuple[Position, str], tuple[str, str]]:
    """Every named opening's last move, by the position it is played from and its code: its name and title."""
    book = {}
    for name_, text in OPENINGS:
        codes = tuple(text.split())
        position = START
        for code in codes[:-1]:
            position = make(position, find(position, code))
        book[(position, codes[-1])] = (name_, opening_title(name_, codes))
    return book


BOOK = _book()

# --- the jumps that follow by force ------------------------------------------------------------------------------
WORTH = {"d": 2, "l": 2, "D": 3, "L": 3}  # in half-men: a man is two, a king three
CROWNING = 1  # what crowning a man adds: a man made a king


@dataclass(frozen=True)
class Line:
    """The jumps that follow by force while the side to move has one, both sides taking the best they can (a
    capture is compulsory, so the side to move must take one), and what they come to for the side to move."""
    value: int = 0  # what it nets, in half-men: a man is two, a king three, and crowning a man adds one
    taken: tuple[str, ...] = ()  # the pieces it takes, in order
    lost: tuple[str, ...] = ()  # the pieces of its own it loses
    crowned: bool = False  # it crowns a man on the way
    crowned_them: bool = False  # the other side crowns one
    most: int = 0  # the most it takes in one jump
    most_them: int = 0  # the most the other side takes in one
    moves: tuple[Move, ...] = ()  # the jumps, the side to move's first


NOTHING = Line()


def gain(position: Position, move: Move) -> int:
    """What the move takes, in half-men, with one more when it crowns a man."""
    return sum(WORTH[position.pieces[square]] for square in move.captures) + (CROWNING if move.crowns else 0)


@functools.lru_cache(maxsize=1 << 16)
def line(position: Position) -> Line:
    """The best run of jumps the side to move has, each answered the best way, while it has a jump to make: nothing
    when it has none. Of jumps that come to the same, the first in the list's order."""
    best = NOTHING
    for move in sorted(jumps(position), key=attrgetter("path")):
        rest = line(make(position, move))
        took = tuple(position.pieces[square] for square in move.captures)
        value = gain(position, move) - rest.value
        if not best.moves or value > best.value:
            best = Line(value, took + rest.lost, rest.taken, move.crowns or rest.crowned_them, rest.crowned,
                        max(len(took), rest.most_them), rest.most, (move, *rest.moves))
    return best


def winning_jumps(position: Position) -> list[Move]:
    """The side to move's jumps that win material by force, each answered the best way."""
    return [move for move in sorted(jumps(position), key=attrgetter("path"))
            if gain(position, move) - line(make(position, move)).value > 0]


def passed(position: Position) -> Position:
    """The same pieces with the other side to move: what it could do, were it its turn."""
    return Position(position.pieces, other(position.turn))


# --- reading a move --------------------------------------------------------------------------------------------
def depth(square: int, turn: str) -> int:
    """The square's row as `turn` counts it, from 0 on its own back row to 7 on the far row, where it is crowned."""
    row = row_col(square)[0]
    return row if turn == BLACK else 7 - row


def side_of(square: int, turn: str) -> str:
    """`Single` or `Double`: which half of the board the square is in, by `turn`'s own corners. Each side has its
    single corner on its left hand and its double corner on its right."""
    left = row_col(square)[1] <= 3
    return "Single" if left == (turn == WHITE) else "Double"


def kind_word(piece: str) -> str:
    return "King" if piece.isupper() else "Man"


def counted(count: int, pieces: tuple[str, ...]) -> str:
    """`a Man`, `Two Men`, `a King`, `Two Pieces`: what `count` of `pieces` are called."""
    nouns = {kind_word(piece) for piece in pieces}
    noun = nouns.pop() if len(nouns) == 1 else "Piece"
    if count == 1:
        return f"a {noun}"
    return f"{NUMBERS[count].capitalize()} {'Men' if noun == 'Man' else noun + 's'}"


def steps(position: Position, square: int) -> list[Move]:
    """The steps the piece on `square` could take, whoever's turn it is, captures or not."""
    piece = position.pieces[square]
    crown = CROWN.get(piece, frozenset())
    return [Move((square, to), (), to in crown) for to in STEPS[piece][square] if to not in position.pieces]


def safe_steps(position: Position, square: int) -> tuple[int, int]:
    """How many steps the piece on `square` has, its side to move, and on how many of them no jump of the other
    side's that wins material then takes it."""
    found = steps(position, square)
    safe = sum(1 for step in found if not any(step.path[-1] in move.captures
                                              for move in winning_jumps(make(position, step))))
    return len(found), safe


@dataclass(frozen=True)
class Reading:
    """What one move does, as a name reads it."""
    piece: str  # the piece that moves: d or l for a man, D or L for a king
    start: int
    end: int
    path: tuple[int, ...]
    captures: tuple[int, ...] = ()  # the squares it takes on
    taken: tuple[str, ...] = ()  # the pieces it takes there
    crowned: bool = False
    wins: bool = False  # it leaves the other side no move
    last: bool = False  # it takes the other side's last piece
    only: bool = False  # it is the only legal move
    opening: str = ""  # the named opening it completes
    call: str = ""  # and that opening's call
    answered: bool = False  # the other side has a jump to make after it, as it must
    value: int = 0  # what it nets by force, captures and all, in half-men
    gained: tuple[str, ...] = ()  # every piece it takes by force: its own jump's, and those after
    lost: tuple[str, ...] = ()  # every piece of ours lost by force
    lost_at: int = 0  # where the first of them stands
    crowns: bool = False  # a man of ours is crowned in the jumps that follow, or by the move
    kinged: bool = False  # and when they are done, we have more kings than before the move
    breaks: bool = False  # their jumps open the way for a man of ours to be crowned on our next move
    their_most: int = 0  # the most they take in one jump in those
    pending: bool = False  # they had a jump waiting before the move, and the move leaves them one
    worse: bool = False  # another move here nets more by force
    alone: bool = False  # it loses nothing, and every other move here loses something
    ahead: bool = False  # the side moving has more pieces than the other
    threats: tuple[int, ...] = ()  # where the pieces of theirs stand that it threatens to win by a jump
    threatened: tuple[str, ...] = ()  # and what they are
    escaped: bool = False  # the piece could be won where it stood, and can't be where it lands
    guarded: int = 0  # where a piece of ours stands that could be won, and can't be now
    guarded_piece: str = ""  # and what it is
    backed: bool = False  # the move lands on the square that jump would land on
    squeeze: bool = False  # every move they have loses material by force
    trapped: int = 0  # where a piece of theirs stands with no safe step, threatened or their last, in the squeeze
    trapped_piece: str = ""  # and what it is
    blocked: int = 0  # where a piece of theirs stands that had a step before the move and has none after it
    blocked_piece: str = ""  # and what it is
    driven: bool = False  # their lone king must now leave the double corner, or be taken
    near: bool = False  # a man one step from the crown
    sure: bool = False  # and nothing they do keeps it from being crowned next move
    hole: bool = False  # a man into a dog hole
    bridge: str = ""  # `break` when a man leaves its bridge, `keep` when another back man leaves and the bridge stays
    corner: str = ""  # `clear` when a man leaves its single corner empty, `out` when one of two leaves
    back: bool = False  # a man off its own back row
    refuge: str = ""  # a king into a double corner: `in`, or `shuttle` from one of its squares to the other
    advance: int = 0  # rows it gains toward the far row: fewer than none for a king going home

    @property
    def turn(self) -> str:
        return self.piece.lower()

    @property
    def kind(self) -> str:
        return kind_word(self.piece)

    @property
    def rank(self) -> int:
        """How far up the board it lands, from 0 on its own back row to 7 on the far row."""
        return depth(self.end, self.turn)


@dataclass(frozen=True)
class Board:
    """What a whole board tells the moves on it, worked out once."""
    position: Position
    moves: tuple[Move, ...]
    afters: dict = field(default_factory=dict)  # the position after each move
    lines: dict = field(default_factory=dict)  # the jumps that follow each by force, the other side's first
    values: dict = field(default_factory=dict)  # what each nets by force
    danger: frozenset[int] = frozenset()  # our pieces their jumps that win material take first, were it their turn
    landings: dict = field(default_factory=dict)  # where those jumps land first, by the square of the piece taken
    squeezed: bool = False  # were it their turn now, every move they have would lose material by force
    pending: bool = False  # were it their turn now, they would have a jump to make


@functools.lru_cache(maxsize=64)
def survey(position: Position) -> Board:
    """The board's moves, what each comes to by force, and what of ours is in danger before any of them."""
    moves = tuple(legal_moves(position))
    afters = {move: make(position, move) for move in moves}
    lines = {move: line(afters[move]) for move in moves}
    values = {move: gain(position, move) - lines[move].value for move in moves}
    danger, landings = set(), defaultdict(set)
    theirs = passed(position)
    for move in winning_jumps(theirs):
        danger.add(move.captures[0])
        landings[move.captures[0]].add(move.path[1])
    answers = legal_moves(theirs)
    squeezed = bool(answers) and all(line(make(theirs, answer)).value > 0 for answer in answers)
    return Board(position, moves, afters, lines, values, frozenset(danger),
                 {square: frozenset(lands) for square, lands in landings.items()}, squeezed, bool(jumps(theirs)))


def read(position: Position, move: Move) -> Reading:
    """What the move does: every trait a name can be made from. A ValueError when it is not a legal move here."""
    board = survey(position)
    if move not in board.afters:
        raise ValueError(f"{move.code} is not a legal move in {position.fen}")
    pieces, turn = position.pieces, position.turn
    start, end = move.path[0], move.path[-1]
    piece = pieces[start]
    after, rest, value = board.afters[move], board.lines[move], board.values[move]
    rival = OWN[other(turn)]
    replies = legal_moves(after)
    others = [board.values[move_] for move_ in board.moves if move_ != move]
    mine = sum(1 for p in pieces.values() if p in OWN[turn])
    facts: dict = {
        "piece": piece, "start": start, "end": end, "path": move.path, "captures": move.captures,
        "taken": tuple(pieces[square] for square in move.captures), "crowned": move.crowns,
        "wins": not replies, "last": not any(p in rival for p in after.pieces.values()),
        "only": len(board.moves) == 1, "answered": bool(rest.moves), "value": value,
        "gained": tuple(pieces[square] for square in move.captures) + rest.lost, "lost": rest.taken,
        "crowns": move.crowns or rest.crowned_them, "their_most": rest.most,
        "pending": board.pending and bool(rest.moves) and not move.captures,
        "worse": value < max(board.values.values()), "alone": value >= 0 and bool(others) and max(others) < 0,
        "ahead": mine > len(pieces) - mine, "advance": depth(end, turn) - depth(start, turn),
    }
    if rest.moves:  # the first of ours their jumps take: their jumps are every other one, theirs first
        facts["lost_at"] = next((square for jump in rest.moves[::2] for square in jump.captures), 0)
    last = after
    for jump in rest.moves:
        last = make(last, jump)
    facts["kinged"] = (sum(1 for p in last.pieces.values() if p == turn.upper())
                       > sum(1 for p in pieces.values() if p == turn.upper()))
    # A breakthrough: their jumps clear the way, and a man of ours can then be crowned, as it couldn't before the move
    # or straight after it.
    facts["breaks"] = (len(rest.moves) % 2 == 1 and any(answer.crowns for answer in legal_moves(last))
                       and not any(move_.crowns for move_ in board.moves)
                       and not any(step.crowns for square, p in after.pieces.items() if p == turn
                                   for step in steps(after, square)))
    if (position, move.code) in BOOK:
        facts["opening"], facts["call"] = BOOK[(position, move.code)]
    if not move.captures and not rest.moves:
        facts.update(_quiet(board, move, after, replies))
    if piece.islower():
        facts.update(_structure(position, move))
    elif any(end in corner for corner in DOUBLE_CORNERS):
        facts["refuge"] = "shuttle" if any({start, end} <= corner for corner in DOUBLE_CORNERS) else "in"
    return Reading(**facts)


def _quiet(board: Board, move: Move, after: Position, replies: list[Move]) -> dict:
    """What a move that leaves the other side no jump does: what it threatens, saves, traps or runs for."""
    position, turn = board.position, board.position.turn
    start, end = move.path[0], move.path[-1]
    facts: dict = {}
    targets: list[int] = []
    for jump in winning_jumps(passed(after)):
        if jump.captures[0] not in targets:
            targets.append(jump.captures[0])
    facts["threats"] = tuple(targets)
    facts["threatened"] = tuple(after.pieces[square] for square in targets)
    if board.danger:  # they could have won a piece of ours, and now have no jump at all
        if start in board.danger:
            facts["escaped"] = True
        else:
            saved = min(board.danger)
            facts["guarded"], facts["guarded_piece"] = saved, position.pieces[saved]
            facts["backed"] = end in board.landings.get(saved, ())
    # Every move they have loses material by force: a squeeze, and a trap for the piece of theirs it threatens that
    # can't step anywhere safe, or for their last piece.
    before = passed(position)
    rivals = [square for square, p in after.pieces.items() if p in OWN[other(turn)]]
    if not board.squeezed and replies and all(line(make(after, reply)).value > 0 for reply in replies):
        facts["squeeze"] = True
        trapped = next((square for square in targets if not safe_steps(after, square)[1]), 0)
        trapped = trapped or (rivals[0] if len(rivals) == 1 else 0)
        if trapped:
            facts["trapped"], facts["trapped_piece"] = trapped, after.pieces[trapped]
    # A piece of theirs beside the move that had a step before it and has none at all after it: blocked.
    if not facts.get("trapped"):
        er, ec = row_col(end)
        for square in sorted(after.pieces):
            r, c = row_col(square)
            if after.pieces[square] in OWN[other(turn)] and abs(r - er) == abs(c - ec) == 1 \
                    and steps(before, square) and not steps(after, square):
                facts["blocked"], facts["blocked_piece"] = square, after.pieces[square]
                break
    # Their lone king in a double corner, that could step safely to the corner's other square and now can't.
    if len(rivals) == 1 and after.pieces[rivals[0]].isupper() and replies:
        king = rivals[0]
        corner = next((pair for pair in DOUBLE_CORNERS if king in pair), frozenset())
        if corner:
            mate = min(corner - {king})

            def shuttles(state: Position) -> bool:
                return any(step.path[-1] == mate for step in steps(state, king)) and not any(
                    mate in jump.captures for jump in winning_jumps(make(state, Move((king, mate)))))
            facts["driven"] = shuttles(before) and not shuttles(after)
    # A man one step from the crown with a crowning square open ahead, and whether nothing they do keeps it from the
    # crown next move.
    if position.pieces[start].islower() and depth(end, turn) == 6 and steps(after, end):
        facts["near"] = True
        facts["sure"] = bool(replies) and all(
            any(answer.path[0] == end and answer.crowns for answer in legal_moves(make(after, reply)))
            for reply in replies)
    return facts


def _structure(position: Position, move: Move) -> dict:
    """What a man's move does to its own back row and corners: the bridge, the single corner, the dog hole."""
    pieces, turn = position.pieces, position.turn
    start, end = move.path[0], move.path[-1]
    facts: dict = {}
    holder = DOG_HOLES[turn].get(end)
    if holder and pieces.get(holder) == other(turn):
        facts["hole"] = True
    bridge = BRIDGE[turn]
    intact = all(pieces.get(square) == turn for square in bridge)
    if start in HOME[turn]:
        facts["back"] = True
        if intact and start in bridge:
            facts["bridge"] = "break"
        elif intact and start not in SINGLE_CORNER[turn]:
            facts["bridge"] = "keep"
    if start in SINGLE_CORNER[turn] and end not in SINGLE_CORNER[turn]:
        left = [square for square in SINGLE_CORNER[turn] if square != start and pieces.get(square) == turn]
        facts["corner"] = "out" if left else "clear"
    return facts


# --- the themes: what a move is named for -------------------------------------------------------------------------
# Each theme's emoji, one to a theme, so the column reads as a key to the moves.
THEMES = {
    "win": "🏆", "opening": "📖", "blunder": "⚠️", "sacrifice": "🎁", "losing": "🩸", "shot": "💣",
    "key": "🔑", "crown": "👑", "exchange": "⚖️", "jump": "⚔️", "double": "💥", "multi": "🔥",
    "drive": "🧹", "trap": "🕸️", "block": "🚧", "runaway": "🏃", "threat": "🏹", "escape": "💨", "guard": "🛡️",
    "only": "☝️", "hole": "🕳️", "bridge": "🌉", "back": "🚪", "refuge": "🏰", "king": "⚜️", "centre": "🎯",
    "edge": "🧱", "diagonal": "🛤️", "side": "👣",
}


def theme(r: Reading) -> str:
    """The most telling thing the move does, which its title is about."""
    if r.wins:
        return "win"
    if r.opening:
        return "opening"
    if r.captures:
        if r.value < 0 and r.worse:
            return "blunder"
        if r.crowned:
            return "crown"
        if r.alone:
            return "key"
        if r.value < 0 and not r.only:
            return "losing"
        return "jump" if len(r.captures) == 1 else "double" if len(r.captures) == 2 else "multi"
    if r.answered and r.value < 0:
        if (r.kinged or r.breaks) and len(r.lost) - len(r.gained) == 1 and not r.crowned \
                and not any(p.isupper() for p in r.lost):
            return "sacrifice"
        return "blunder" if r.worse else "losing"
    if r.answered and len(r.gained) > len(r.lost):
        return "shot"
    for key, holds in (("key", r.alone), ("crown", r.crowned), ("exchange", r.answered), ("drive", r.driven),
                       ("trap", r.trapped or r.squeeze), ("runaway", r.near), ("threat", r.threats), ("escape", r.escaped),
                       ("guard", r.guarded), ("only", r.only), ("hole", r.hole), ("bridge", r.bridge == "break")):
        if holds:
            return key
    if r.kind == "King":
        return "refuge" if r.refuge else "king"
    if r.corner or r.back:
        return "back"
    if r.end in CENTRE:
        return "centre"
    if r.blocked:
        return "block"
    if r.end in EDGE:
        return "edge"
    return "diagonal" if r.end in LONG_DIAGONAL else "side"


# --- the calls ----------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Call:
    """One way to say what a move does: alone on its board, and with the details that tell it from others with the
    same call. A detail is empty when the call has no form with it."""
    base: str
    by: str = ""  # with the square the piece moves from
    at: str = ""  # with the square it lands on


def _forms(base: str, by: str = " From {s}", at: str = " at {e}") -> tuple[str, str, str]:
    """A call and its two details, each a pattern for the start {s} and end {e}: `Take the Centre!`, `Take the Centre
    From {s}!`, `Take the Centre at {e}!`."""
    stem = base[:-1]
    return base, (stem + by + "!") if by else "", (stem + at + "!") if at else ""


def _calls(r: Reading, *forms: tuple[str, str, str]) -> list[Call]:
    """The calls with the move's squares in their details."""
    return [Call(base, by.format(s=r.start, e=r.end), at.format(s=r.start, e=r.end)) for base, by, at in forms]


def calls(r: Reading, key: str) -> list[Call]:
    """The calls the move's theme has for it, every one of them true of it, in a fixed order."""
    return CALLERS[key](r)


def _win(r: Reading) -> list[Call]:
    n = len(r.captures)
    if r.last:
        last = kind_word(r.taken[0]) if n == 1 else NUMBERS[n].capitalize()
        return _calls(r, _forms(f"Take Their Last {last}!", at=""), _forms("Clear the Board!", at=""),
                      _forms("Wipe the Board Clean!", at=""))
    if r.captures:
        return _calls(r, ("Jump and Leave Them No Move!", "Jump From {s} and Leave Them No Move!", ""),
                      ("Take It and Shut Them In!", "Take It From {s} and Shut Them In!", ""))
    return _calls(r, _forms("Leave Them No Move!"), _forms("Block Their Last Move!"),
                  ("Shut Them In for Good!", "Shut Them In From {s}!", "Shut Them In at {e}!"))


def _opening(r: Reading) -> list[Call]:
    return [Call(r.call)]


def _blunder(r: Reading) -> list[Call]:
    if r.captures and r.their_most >= 2:
        return _calls(r, _forms("Jump Into Their Shot!", at=""),
                      _forms(f"Jump Into Their {JUMPS.get(r.their_most, 'Long')} Jump!", at=""))
    if r.captures:
        return _calls(r, _forms("Jump Into a Losing Trade!", at=""), _forms("Take the Losing Jump!", at=""))
    net = len(r.lost) - len(r.gained)
    first = f"the {kind_word(r.lost[0])} on {r.lost_at}" if r.lost_at else ""
    if r.crowned and not r.kinged:
        return _calls(r, ("Crown a Man, Only to Lose Him!", "", ""))
    if r.kinged:  # a man crowned and kept, and more lost than taken on the way
        return _calls(r, _forms(f"Give {counted(max(net, 1), r.lost)} for a King!", at=""))
    forms = []
    if r.their_most >= 2:
        size = JUMPS.get(r.their_most, f"{NUMBERS[r.their_most].capitalize()}-Piece")
        forms.append((f"Walk Into Their {size} Jump!", "", ""))
    if net >= 1:
        lost = counted(net, r.lost)
        forms.append((f"Throw Away {lost}!", f"Throw Away {first}!" if first else "", ""))
        if not r.gained:
            forms.append((f"Hand Them {lost} for Nothing!", f"Hand Them {first} for Nothing!" if first else "", ""))
        if first:  # the man that moves, or one it leaves behind
            forms.append((f"Give Away {first}!" if r.lost_at == r.end else f"Leave {first} to Be Jumped!", "", ""))
    else:
        forms.append(("Trade a King for a Man!", "", ""))
    return _calls(r, *forms)


def _sacrifice(r: Reading) -> list[Call]:
    lost = counted(len(r.lost) - len(r.gained), r.lost)
    if r.kinged:
        return _calls(r, _forms(f"Give {lost} for a King!", at=""), _forms(f"Pay {lost} for a Crown!", at=""))
    return _calls(r, _forms(f"Give {lost} to Break Through!", at=""),
                  _forms(f"Sacrifice {lost} for the Crown!", at=""))


def _losing(r: Reading) -> list[Call]:
    if r.captures:
        return _calls(r, _forms("Jump and Cut Your Losses!", at=""), _forms("Take the Lesser Loss!", at=""))
    if r.crowned and not r.kinged:
        return _calls(r, ("Crown a Man, Only to Lose Him!", "", ""))
    given = f"Give Up the {kind_word(r.lost[0])} on {r.lost_at}!" if r.lost_at else ""
    return _calls(r, ("Cut Your Losses!", given, ""))


def _shot(r: Reading) -> list[Call]:
    gave, took = NUMBERS[len(r.lost)].capitalize(), NUMBERS[len(r.gained)].capitalize()
    forms = [_forms(f"Fire the {took}-for-{gave} Shot!", at=""), _forms(f"Give {gave}, Take {took}!", at=""),
             _forms(f"Spring the {took}-for-{gave}!", at="")]
    if r.kinged:
        forms.insert(0, _forms("Shoot Through to the King Row!", at=""))
    return _calls(r, *forms)


def _key(r: Reading) -> list[Call]:
    if r.captures:
        return _calls(r, _forms("Take the Only Safe Jump!", at=""), _forms("Find the Only Jump That Holds!", at=""))
    if r.crowned:
        return _calls(r, ("King Me, the Only Safe Move!", "", "King Me on {e}, the Only Safe Move!"))
    if r.escaped:
        return _calls(r, (f"Save the {r.kind} on {r.start}, the Only Way!", "", "Save It at {e}, the Only Way!"))
    if r.guarded:
        return _calls(r, (f"Save the {kind_word(r.guarded_piece)} on {r.guarded}, the Only Way!", "",
                          f"Save the {kind_word(r.guarded_piece)} on {r.guarded} From {{s}}!"))
    return _calls(r, _forms("Find the Only Safe Move!"), _forms("Make the Only Move That Holds!"))


def _crown(r: Reading) -> list[Call]:
    n = len(r.captures)
    if n:
        jump = "Jump" if n == 1 else f"{JUMPS.get(n, NUMBERS[n].capitalize() + '-Piece')} Jump"
        return _calls(r, (f"{jump} and King Me!", f"{jump} From {{s}} and King Me!", f"{jump} to {{e}} and King Me!"),
                      (f"{jump} Through to the Crown!", f"{jump} From {{s}} to the Crown!",
                       f"{jump} to the Crown on {{e}}!"),
                      (f"Take {counted(n, r.taken)} and Be Crowned!", "", ""))
    return _calls(r, _forms("King Me!", at=" on {e}"), ("Crown Him!", "Crown the Man From {s}!", "Crown Him on {e}!"),
                  _forms("Make a King!", at=" on {e}"), _forms("Reach the King Row!"))


def _exchange(r: Reading) -> list[Call]:
    gave, took = len(r.lost), len(r.gained)
    if r.kinged:
        if gave == took == 1:
            return _calls(r, _forms("Trade Into a King!", at=""), _forms("Trade One and Crown!", at=""))
        return _calls(r, _forms(f"Give {NUMBERS[gave].capitalize()}, Take {NUMBERS[took].capitalize()} and Crown!",
                                at=""))
    if gave == took and any(p.isupper() for p in r.gained) and not any(p.isupper() for p in r.lost):
        return _calls(r, _forms("Trade a Man for Their King!", at=""))
    if gave != took:
        return _calls(r, _forms(f"Give {NUMBERS[gave].capitalize()}, Take {NUMBERS[took].capitalize()}!", at=""))
    forms = [_forms("Trade Down While Ahead!", at="")] if r.ahead else []
    if gave == 1 and r.pending:  # their jump was waiting already: the move lets it come, and takes one back
        forms += [_forms("Accept the Trade!", at=""), _forms("Let Them Trade One for One!", at="")]
    elif gave == 1:
        forms += [_forms("Force a Trade!", at=""), _forms("Give One, Take One!", at=""),
                  _forms("Offer an Even Trade!", at="")]
    else:
        count = NUMBERS[gave].capitalize()
        forms += [_forms(f"Trade {count} for {count}!", at=""), _forms(f"Give {count}, Take {count}!", at="")]
    return _calls(r, *forms)


def _jump(r: Reading) -> list[Call]:
    """A jump's calls, by what it takes and how: one, two or more, a king among them, taken for free, or forced."""
    n = len(r.captures)
    free = not r.lost
    if n == 1:
        target = f"{kind_word(r.taken[0])} on {r.captures[0]}"
        if r.only:
            return _calls(r, (f"Take the Forced Jump Over {r.captures[0]}!", "", ""))
        forms = []
        if r.taken[0].isupper():
            forms.append(_forms(f"Take Their King on {r.captures[0]}!", at=""))
        if free:
            forms.append(_forms(f"Take the {target} for Free!", at=""))
        if r.kind == "King":
            forms.append((f"Strike the {target} With the King!", f"Strike the {target} From {{s}}!", ""))
        forms += [_forms(f"Jump the {target}!", at=" to {e}"), _forms(f"Take the {target}!", at=" to {e}")]
        return _calls(r, *forms)
    count = NUMBERS[n].capitalize()
    size = JUMPS.get(n)
    forms = []
    if r.only:
        return _calls(r, (f"Take the Forced {size} Jump!" if size else f"Take All {count}, as You Must!", "", ""))
    if any(p.isupper() for p in r.taken):
        forms.append((f"Take {count}, King and All!", f"Take {count}, King and All, From {{s}}!", ""))
    if free:
        forms.append(_forms(f"Take {count} for Free!", at=" to {e}"))
    if size:
        forms += [(f"{size} Jump Them!", f"{size} Jump From {{s}}!", f"{size} Jump to {{e}}!"),
                  (f"Take {count} in One Move!", f"Take {count} From {{s}}!", f"Take {count}, Landing on {{e}}!")]
    else:
        forms += [(f"Take {count} in One Move!", f"Take {count} From {{s}}!", f"Take {count}, Landing on {{e}}!"),
                  (f"Jump {count} in a Row!", f"Jump {count} in a Row From {{s}}!", f"Jump {count} to {{e}}!")]
    return _calls(r, *forms)


def _drive(r: Reading) -> list[Call]:
    return _calls(r, *(((f"{verb} the King {out} the Double Corner!", f"{verb} Him Out With the {r.kind} on {{s}}!",
                         f"{verb} Him Out of the Corner at {{e}}!"))
                       for verb, out in (("Drive", "From"), ("Force", "Out of"), ("Smoke", "Out of"))))


def _trap(r: Reading) -> list[Call]:
    if not r.trapped:
        return _calls(r, _forms("Leave Them No Safe Move!"))
    target = f"{kind_word(r.trapped_piece)} on {r.trapped}"
    return _calls(r, *(_forms(f"{verb} the {target}!", at=", Landing on {e}") for verb in ("Trap", "Snare", "Box In")))


def _block(r: Reading) -> list[Call]:
    target = f"{kind_word(r.blocked_piece)} on {r.blocked}"
    return _calls(r, *(_forms(f"{verb} the {target}!", at=", Landing on {e}")
                       for verb in ("Block", "Hem In", "Pin Down")))


def _runaway(r: Reading) -> list[Call]:
    if r.sure:
        return _calls(r, _forms("Make the Crown Certain!"), _forms("Break Through for a King!"))
    return _calls(r, _forms("Knock on the King Row!"), _forms("Run for the King Row!", at=" to {e}"),
                  _forms("Race for the Crown!", at=" to {e}"))


def _threat(r: Reading) -> list[Call]:
    if len(r.threats) > 1:
        return _calls(r, _forms("Threaten Two at Once!"), _forms("Aim at Two at Once!"))
    target = f"{kind_word(r.threatened[0])} on {r.threats[0]}"
    return _calls(r, *(_forms(f"{verb} the {target}!", at=", Landing on {e}")
                       for verb in ("Threaten", "Aim at", "Menace", "Go After")))


def _escape(r: Reading) -> list[Call]:
    return _calls(r, ("Slip Out of the Jump!", f"Slip the {r.kind} on {{s}} Out of the Jump!", "Slip Away to {e}!"),
                  ("Dodge the Jump!", f"Dodge the Jump With the {r.kind} on {{s}}!", "Dodge the Jump at {e}!"),
                  ("Get Clear of the Jump!", f"Get the {r.kind} on {{s}} Clear!", "Get Clear to {e}!"))


def _guard(r: Reading) -> list[Call]:
    saved = f"{kind_word(r.guarded_piece)} on {r.guarded}"
    verbs = ("Back Up", "Shore Up", "Guard") if r.backed else ("Guard", "Cover", "Protect")
    return _calls(r, *(_forms(f"{verb} the {saved}!", at=", Landing on {e}") for verb in verbs))


def _only(r: Reading) -> list[Call]:
    return _calls(r, ("Make the Only Move There Is!", "", ""), ("Take the One Move Left!", "", ""))


def _hole(r: Reading) -> list[Call]:
    return _calls(r, _forms("Step Into the Dog Hole!"), _forms("Sink Into the Dog Hole!"))


def _bridge(r: Reading) -> list[Call]:
    return _calls(r, _forms("Break the Bridge!", at=" to {e}"), _forms("Give Up the Bridge!", at=" to {e}"))


def _back(r: Reading) -> list[Call]:
    if r.corner == "clear":
        return _calls(r, _forms("Clear the Single Corner!", at=" to {e}"))
    if r.corner == "out":
        return _calls(r, ("Bring Out a Single-Corner Man!", "Bring Out the Single-Corner Man on {s}!",
                          "Bring a Single-Corner Man to {e}!"))
    if r.bridge == "keep":
        return _calls(r, ("Keep the Bridge, Bring Out a Man!", "Keep the Bridge, Bring Out the Man on {s}!",
                          "Keep the Bridge, Bring a Man to {e}!"))
    return _calls(r, ("Bring Out a Back-Row Man!", "Bring Out the Back-Row Man on {s}!",
                      "Bring a Back-Row Man to {e}!"),
                  ("Bring Up a Back-Row Man!", "Bring Up the Back-Row Man on {s}!", "Bring a Back-Row Man Up to {e}!"))


def _refuge(r: Reading) -> list[Call]:
    if r.refuge == "shuttle":
        return _calls(r, _forms("Shuttle in the Double Corner!", at=" to {e}"), _forms("Hold the Double Corner!"))
    return _calls(r, _forms("Shelter in the Double Corner!"), _forms("Run for the Double Corner!"),
                  _forms("Take Refuge in the Double Corner!"))


def _king(r: Reading) -> list[Call]:
    if r.end in CENTRE:
        return _calls(r, _forms("Centre the King!", at=" on {e}"),
                      ("Plant the King in the Centre!", "Plant the King on {s} in the Centre!",
                       "Plant the King in the Centre at {e}!"))
    if r.advance > 0:
        return _calls(r, *((f"{verb} the King {way}!", f"{verb} the King on {{s}} {way}!",
                            f"{verb} the King {way} to {{e}}!")
                           for verb, way in (("Send", "Forward"), ("Drive", "Forward"), ("Bring", "Up"))))
    return _calls(r, ("Pull the King Back!", "Pull the King on {s} Back!", "Pull the King Back to {e}!"),
                  ("Bring the King Home!", "Bring the King on {s} Home!", "Bring the King Home to {e}!"),
                  ("Fall Back With the King!", "Fall Back With the King on {s}!", "Fall Back to {e} With the King!"))


def _centre(r: Reading) -> list[Call]:
    return _calls(r, *(_forms(f"{verb}!") for verb in ("Take the Centre", "Seize the Centre", "Claim the Centre",
                                                       "Plant a Man in the Centre")))


def _edge(r: Reading) -> list[Call]:
    return _calls(r, _forms("Take the Edge!"), _forms("Hug the Edge!"),
                  ("Post a Man on the Edge!", "Post the Man on {s} on the Edge!", "Post a Man on the Edge at {e}!"))


def _diagonal(r: Reading) -> list[Call]:
    if r.start in LONG_DIAGONAL:
        return _calls(r, _forms("Advance Along the Long Diagonal!", at=" to {e}"),
                      _forms("Push Along the Long Diagonal!", at=" to {e}"))
    return _calls(r, _forms("Step Onto the Long Diagonal!"), _forms("Take the Long Diagonal!"))


def _side(r: Reading) -> list[Call]:
    wing = f"{side_of(r.end, r.turn)}-Corner Side"
    return _calls(r, *(_forms(f"{verb} the {wing}!", at=" to {e}")
                       for verb in ("Press", "Push Up", "Advance on", "Move Up")))


CALLERS = {
    "win": _win, "opening": _opening, "blunder": _blunder, "sacrifice": _sacrifice, "losing": _losing,
    "shot": _shot, "key": _key, "crown": _crown, "exchange": _exchange, "jump": _jump, "double": _jump,
    "multi": _jump, "drive": _drive, "trap": _trap, "block": _block, "runaway": _runaway, "threat": _threat,
    "escape": _escape, "guard": _guard, "only": _only, "hole": _hole, "bridge": _bridge, "back": _back,
    "refuge": _refuge, "king": _king, "centre": _centre, "edge": _edge, "diagonal": _diagonal, "side": _side,
}


# --- naming a board ---------------------------------------------------------------------------------------------
def listed(squares: tuple[int, ...]) -> str:
    """`6`, `15 and 6`, `6, 15 and 24`."""
    numbers = [str(square) for square in squares]
    return numbers[0] if len(numbers) == 1 else ", ".join(numbers[:-1]) + " and " + numbers[-1]


def words(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> str:
    """The move in plain English: `Man from 11 to 15`, `Man from 20 jumps 16, landing on 11`, `Man from 19 jumps 15
    and 6, landing on 1, crowned`, with `winning the game` when it leaves the other side no move."""
    who = "King" if position.pieces[move.path[0]].isupper() else "Man"
    start, end = move.path[0], move.path[-1]
    if move.captures:
        text = f"{who} from {start} jumps {listed(move.captures)}, landing on {end}"
    else:
        text = f"{who} from {start} to {end}"
    if replies is None:
        replies = legal_moves(make(position, move) if after is None else after)
    tail = (", crowned" if move.crowns else "") + ("" if replies else ", winning the game")
    if len(text + tail) > WORDS_LONGEST:  # a king's long run of jumps: how many, not which
        text = f"{who} from {start} jumps {NUMBERS[len(move.captures)]} pieces, landing on {end}"
    return text + tail


def seed(position: Position, move: Move) -> int:
    """The move's seed on this board: the same position and move always give the same name."""
    digest = hashlib.sha256(f"{position.fen}:{move.code}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def named(position: Position) -> list[tuple[Move, str, str, str]]:
    """Every legal move in order, each with its emoji, a title no other move here has, and its words."""
    return list(_named(position))


def name(position: Position, move: Move) -> tuple[str, str, str]:
    """The move's emoji, title and words, as the board's list names it."""
    for listed_move, emoji, title_, words_ in _named(position):
        if listed_move == move:
            return emoji, title_, words_
    raise ValueError(f"{move.code} is not a legal move in {position.fen}")


def fits(title_: str) -> bool:
    return 0 < len(title_) <= LONGEST


def route(move: Move, twins: list[Move]) -> str:
    """Where a jump goes, as far as it takes to tell it from others that take as many with the same start and end:
    `Second Jump to 30` when no other's second jump lands on 30, else its landings in turn until no other's begin
    the same way."""
    for index in range(1, len(move.path) - 1):
        if all(twin.path[index] != move.path[index] for twin in twins):
            return f"{ORDINALS[index - 1]} Jump to {move.path[index]}"
    for index in range(2, len(move.path)):
        if all(twin.path[:index + 1] != move.path[:index + 1] for twin in twins):
            return f"via {listed(move.path[1:index + 1])}"
    return f"via {listed(move.path[1:-1])}"


@functools.lru_cache(maxsize=64)
def _named(position: Position) -> tuple[tuple[Move, str, str, str], ...]:
    board = survey(position)
    readings = {move: read(position, move) for move in board.moves}
    keys = {move: theme(readings[move]) for move in board.moves}
    groups: dict[str, list[Move]] = defaultdict(list)
    for move in board.moves:
        groups[keys[move]].append(move)
    titles: dict[Move, str] = {}
    for key, members in groups.items():
        # one call for the whole group, chosen by the position and its first move, so its moves read alike
        pick = seed(position, members[0])
        chosen = {}
        for move in members:
            options = [call for call in calls(readings[move], key) if fits(call.base)]
            chosen[move] = options[pick % len(options)]
        titles.update(_distinct(key, members, chosen))
    used: set[str] = set()
    out = []
    for move in board.moves:
        title_ = titles[move]
        if title_ in used or not fits(title_):  # taken already, or too long: say where it goes, or the move itself
            title_ = next(text for text in (f"{title_[:-1]}, {move.path[0]} to {move.path[-1]}!", f"Play {move.code}!")
                          if text not in used and fits(text))
        used.add(title_)
        out.append((move, THEMES[keys[move]], title_, words(position, move, board.afters[move])))
    return tuple(out)


# The detail a theme's moves are told apart by first: where the piece lands, or else where it moves from.
LANDING = frozenset(("centre", "edge", "diagonal", "crown", "refuge", "king", "escape", "runaway", "hole"))
# Themes about a piece's own way across the board, told apart at the last by where it goes from and to; the rest,
# about what the move does to others, by the move itself.
WAYS = LANDING | {"side", "back", "bridge"}


def _distinct(key: str, members: list[Move], chosen: dict[Move, Call]) -> dict[Move, str]:
    """Titles for the moves of one theme on a board, each its own. A move whose call no other here shares keeps it
    alone; the rest each take the detail that tells them apart: where the piece lands or where it moves from, the
    theme's own first, or both, or for jumps that share both ends, where each goes first."""
    bases = [chosen[move].base for move in members]
    order = ("at", "by") if key in LANDING else ("by", "at")
    out = {}
    for move in members:
        if bases.count(chosen[move].base) == 1:
            out[move] = chosen[move].base
            continue
        for form in order:
            text = getattr(chosen[move], form)
            if fits(text) and sum(getattr(chosen[other_], form) == text for other_ in members) == 1 \
                    and text not in bases:
                out[move] = text
                break
    for move in members:
        if move in out and list(out.values()).count(out[move]) == 1:
            continue
        twins = [other_ for other_ in members if other_ != move and other_.path[0] == move.path[0]
                 and other_.path[-1] == move.path[-1] and len(other_.captures) == len(move.captures)]
        if twins:
            detail = route(move, twins)
        else:
            detail = f"From {move.path[0]} to {move.path[-1]}" if key in WAYS else f"With {move.code}"
        text = f"{chosen[move].base[:-1]}, {detail}!" if twins else f"{chosen[move].base[:-1]} {detail}!"
        short = f"Take {NUMBERS[len(move.captures)].capitalize()}" if move.captures else "Move"
        out[move] = next((option for option in (text, f"{short}, {detail}!") if fits(option)), f"Play {move.code}!")
    return out
