# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named for what it is: an emoji, a title, and the move in plain words.

  from checkers_names import name, named

A name says what the move is and never what it does to the game. It is made
from the move alone: the piece that moves, a man or a king; the squares it
starts and lands on, numbered 1 to 32 as American checkers numbers them; for
a jump, the pieces it takes and where they stand; and crowning, when a man
reaches the far row. Nothing is read ahead, so no name calls a move good or
bad, says what it leaves the other side or what it sets up, or names an
opening, and two moves of one kind read alike whatever follows them. Naming
a jump tells no move from another either: the rules force a jump whenever
there is one, and then every move listed is a jump.

The emoji is the kind of move, the same for every move of that kind: 👣 a
man's step, ⚜️ a king's step, ⚔️ a jump that takes one piece, ⛓️ a jump that
takes two or more, and 👑 a man crowned, by a step or at the end of a jump.

A title is a call in checkers' own words. A man's step says where it goes
from and to ("Advance the Man From 9 to 13!"), and a king's step which
side's end of the board it goes toward as well ("Send the King From 14 to 18
Toward White's Side!"), since a king goes either way. A man reaching the far
row is crowned ("Crown the Man From 27 on 31!"). A jump says what it takes
("Jump the Man on 16!", "Double Jump the Men on 26 and 19!"), with the king
when a king jumps ("Jump the Man on 16 With the King!"), and where a man
that jumps to the far row is crowned ("Jump the King on 26, Crowned on
31!").

Every move of one kind on a board reads in one form, so only its squares and
pieces tell it from the rest. The men's steps share a verb, as the kings'
steps do, picked by a hash of the position, so the same board and move always
give the same name. The jumps of one kind and count, by men or by kings,
share the plainest form that fits all of them in 48 characters and tells
each from the rest: what each takes, naming what each piece is when there is
room; then where each starts as well; then where each starts and lands. A
step names both its squares, so no two steps share a title, and no two moves
on a board ever do.

The words say the move as a score sheet would: "Man from 11 to 15", "Man
from 20 jumps 16, landing on 11", "King from 21 jumps 25, landing on 30",
with ", crowned" for a man crowned. Black (GitHub's side, on 1 to 12) moves
first and White (the house's, on 21 to 32) replies; the rules' letters for
the sides, d and l, never reach a reader. Stdlib only, with checkers_rules.py
beside it.
"""
from __future__ import annotations

import functools
import hashlib
from collections import Counter, defaultdict
from collections.abc import Sequence

from checkers_rules import DARK, LIGHT, SIDES, Move, Position, legal_moves, row_col

LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
NUMBERS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")
# The emoji of each kind of move, one to a kind, so the column reads as a key to the list.
EMOJI = {"step": "👣", "king": "⚜️", "jump": "⚔️", "jumps": "⛓️", "crown": "👑"}
MARCH = ("Advance", "March", "Push")  # a man's step, which is always forward
SEND = ("Send", "Move")  # a king's step, which goes either way
JUMPS = {2: "Double Jump", 3: "Triple Jump"}  # a jump of two or three, as a checkers player calls it
PLURAL = {"Man": "Men", "King": "Kings", "Piece": "Pieces"}
WITH_KING = " With the King"


def kind(position: Position, move: Move) -> str:
    """The kind of move, which its emoji shows: `crown` for a man crowned, by a step or a jump; `jumps` for a jump
    that takes two or more, `jump` for one that takes one; `king` for a king's step and `step` for a man's."""
    if move.crowns:
        return "crown"
    if move.captures:
        return "jumps" if len(move.captures) > 1 else "jump"
    return "king" if position.pieces[move.path[0]].isupper() else "step"


def kind_word(piece: str) -> str:
    """`Man` or `King`."""
    return "King" if piece.isupper() else "Man"


def toward(start: int, end: int) -> str:
    """`White` or `Black`: whose end of the board a step from `start` to `end` goes toward. Black's men start on 1
    to 12, at the top of the standard diagram, and White's on 21 to 32, at its foot."""
    return SIDES[LIGHT] if row_col(end)[0] > row_col(start)[0] else SIDES[DARK]


def listed(squares: Sequence[int]) -> str:
    """`6`, `15 and 6`, `6, 15 and 24`."""
    numbers = [str(square) for square in squares]
    return numbers[0] if len(numbers) == 1 else ", ".join(numbers[:-1]) + " and " + numbers[-1]


def words(position: Position, move: Move) -> str:
    """The move in plain English, as a score sheet would say it: `Man from 11 to 15`, `Man from 20 jumps 16, landing
    on 11`, `Man from 19 jumps 15 and 6, landing on 1, crowned`. A king takes nine pieces at most, all on the inner
    squares its jumps pass over, so the longest words run to 70 characters, inside the 80 the kit takes."""
    who = kind_word(position.pieces[move.path[0]])
    start, end = move.path[0], move.path[-1]
    if move.captures:
        text = f"{who} from {start} jumps {listed(move.captures)}, landing on {end}"
    else:
        text = f"{who} from {start} to {end}"
    return text + (", crowned" if move.crowns else "")


def seed(position: Position, move: Move) -> int:
    """The move's seed on this board: the same position and move always give the same number."""
    digest = hashlib.sha256(f"{position.fen}:{move.code}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


# --- the titles ---------------------------------------------------------------------------------------------------
def fits(title: str) -> bool:
    return 0 < len(title) <= LONGEST


def step_title(position: Position, move: Move, verbs: dict[str, str]) -> str:
    """A step's title, which names both its squares: `Advance the Man From 9 to 13!`, `Crown the Man From 27 on
    31!`, `Send the King From 14 to 18 Toward White's Side!`."""
    start, end = move.path
    if move.crowns:
        return f"Crown the Man From {start} on {end}!"
    if position.pieces[start].isupper():
        return f"{verbs['king']} the King From {start} to {end} Toward {toward(start, end)}'s Side!"
    return f"{verbs['step']} the Man From {start} to {end}!"


def takes(position: Position, move: Move) -> list[tuple[str, str]]:
    """What a jump takes, as its title can say it: its verb and the pieces, four ways from the most told to the
    least. What each piece is and where it stands (`Double Jump`, `the Man on 15 and the King on 6`); what they are
    together and where they stand (`Double Jump`, `the Pieces on 15 and 6`); where they stand (`Double Jump`, `15
    and 6`); and how many they are (`Jump`, `Two Pieces`). A jump of one says the first every way."""
    squares = move.captures
    kinds = [kind_word(position.pieces[square]) for square in squares]
    if len(squares) == 1:
        return [("Jump", f"the {kinds[0]} on {squares[0]}")] * 4
    verb = JUMPS.get(len(squares), "Jump")
    noun = PLURAL[kinds[0] if len(set(kinds)) == 1 else "Piece"]
    together = f"the {noun} on {listed(squares)}"
    each = (f"the {kinds[0]} on {squares[0]} and the {kinds[1]} on {squares[1]}"
            if len(squares) == 2 and kinds[0] != kinds[1] else together)
    return [(verb, each), (verb, together), (verb, listed(squares)),
            ("Jump", f"{NUMBERS[len(squares)].capitalize()} {noun}")]


def family_titles(position: Position, members: Sequence[Move]) -> dict[Move, str]:
    """Titles for a family of jumps on one board, those of one kind and count by men or by kings, all in one form:
    the plainest that fits every one of them and tells each from the rest. It says what each takes, as fully as
    there is room for, with the king when a king jumps; then where each starts as well; then where each starts and
    lands. A jump is its start and the pieces it takes in turn, so those tell any two apart, unless a king's long
    run takes too many to list beside its start; then each says its code."""
    crowning = members[0].crowns  # and then where it lands is said already, where it is crowned
    movers = (WITH_KING, "") if position.pieces[members[0].path[0]].isupper() else ("",)
    pieces = {move: takes(position, move) for move in members}
    for span in ("", " From {s}") if crowning else ("", " From {s}", " From {s} to {e}"):
        for mover in movers:
            for told in range(4):
                titles = {}
                for move in members:
                    verb, what = pieces[move][told]
                    where = span.format(s=move.path[0], e=move.path[-1])
                    crowned = f", Crowned on {move.path[-1]}" if crowning else ""
                    titles[move] = f"{verb} {what}{mover}{where}{crowned}!"
                if all(fits(title) for title in titles.values()) and len(set(titles.values())) == len(titles):
                    return titles
    return {move: f"Jump {move.code}!" for move in members}


# --- naming a board -----------------------------------------------------------------------------------------------
def named(position: Position) -> list[tuple[Move, str, str, str]]:
    """Every legal move in order, each with its emoji, a title no other move here has, and its words."""
    return list(_named(position))


def name(position: Position, move: Move) -> tuple[str, str, str]:
    """The move's emoji, title and words, as the board's list names it. A ValueError when it is not a legal move
    here."""
    for listed_move, emoji, title, said in _named(position):
        if listed_move == move:
            return emoji, title, said
    raise ValueError(f"{move.code} is not a legal move in {position.fen}")


@functools.lru_cache(maxsize=64)
def _named(position: Position) -> tuple[tuple[Move, str, str, str], ...]:
    moves = legal_moves(position)
    kinds = {move: kind(position, move) for move in moves}
    # One verb for every man's step on the board, and one for every king's, picked by the position and the first.
    verbs = {}
    for key, choices in (("step", MARCH), ("king", SEND)):
        first = next((move for move in moves if kinds[move] == key), None)
        if first is not None:
            verbs[key] = choices[seed(position, first) % len(choices)]
    titles = {move: step_title(position, move, verbs) for move in moves if not move.captures}
    families = defaultdict(list)
    for move in moves:
        if move.captures:
            families[(kinds[move], position.pieces[move.path[0]].isupper(), len(move.captures))].append(move)
    for members in families.values():
        titles.update(family_titles(position, members))
    # A step names both its squares, and families of jumps never share a title, but if two did, each would say its code.
    shared = Counter(titles[move] for move in moves if move.captures)
    titles = {move: f"Jump {move.code}!" if shared[title] > 1 else title for move, title in titles.items()}
    return tuple((move, EMOJI[kinds[move]], titles[move], words(position, move)) for move in moves)
