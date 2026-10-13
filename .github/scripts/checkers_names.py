# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named as checkers players name it: an emoji, a name, and the move in plain words.

  from checkers_names import name, named

A name is what a checkers player calls the move, and it says what the move
is, never where it goes or what it does to the game. The laws of checkers
know a move and a capturing move, each by a man or a king, and the names
follow them: a Man Move or a King Move; a Single Jump, a Double Jump or a
Triple Jump by how many pieces it takes, and a Multiple Jump past three, a
king's with "King" before it ("King Jump", "King Double Jump"); and a man
that reaches the far row and is crowned makes a Crowning Move, or a Crowning
Jump when it gets there by jumping ("Crowning Double Jump"). No name holds a square, so one
name fits many moves on a board, and the notation and the words beside it
tell them apart.

Nothing is read ahead, so no name calls a move good or bad, says what it
leaves the other side or what it sets up, or names an opening, and two moves
of one kind read alike whatever follows them. Naming a jump tells no move
from another either: the rules force a jump whenever there is one, and then
every move listed is a jump.

The emoji is the kind of move, the same for every move of that kind: 👣 a
man's step, ⚜️ a king's step, ⚔️ a jump that takes one piece, ⛓️ a jump that
takes two or more, and 👑 a man crowned, by a step or at the end of a jump.

The words say the move as a score sheet would: "Man from 11 to 15", "Man
from 20 jumps 16, landing on 11", "King from 21 jumps 25, landing on 30",
with ", crowned" for a man crowned. Black (GitHub's side, on 1 to 12) moves
first and White (the house's, on 21 to 32) replies; the rules' letters for
the sides, d and l, never reach a reader. Stdlib only, with checkers_rules.py
beside it.
"""
from __future__ import annotations

import functools
from collections.abc import Sequence

from checkers_rules import Move, Position, legal_moves

LONGEST = 48  # the longest title tannergolden/markdown draws in the list
WORDS_LONGEST = 80  # the longest words it takes
# The emoji of each kind of move, one to a kind, so the column reads as a key to the list.
EMOJI = {"step": "👣", "king": "⚜️", "jump": "⚔️", "jumps": "⛓️", "crown": "👑"}
JUMPS = ("Jump", "Double Jump", "Triple Jump")  # a jump that takes one, two or three pieces; more is a Multiple Jump


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


def title(position: Position, move: Move) -> str:
    """The move's name as a checkers player calls it, two to four words that hold no square: `Man Move`, `King Move`,
    `Crowning Move`, `Single Jump`, `Double Jump`, `Triple Jump` or `Multiple Jump`, a king's with `King` before it and
    a man's that ends crowned with `Crowning`: `King Jump`, `King Double Jump`, `Crowning Jump`."""
    taken = len(move.captures)
    if not taken:
        return "Crowning Move" if move.crowns else f"{kind_word(position.pieces[move.path[0]])} Move"
    jump = JUMPS[taken - 1] if taken <= len(JUMPS) else "Multiple Jump"
    if move.crowns:
        return f"Crowning {jump}"
    if position.pieces[move.path[0]].isupper():
        return f"King {jump}"
    return "Single Jump" if taken == 1 else jump


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


# --- naming a board -----------------------------------------------------------------------------------------------
def named(position: Position) -> list[tuple[Move, str, str, str]]:
    """Every legal move in order, each with its emoji, its name and its words."""
    return list(_named(position))


def name(position: Position, move: Move) -> tuple[str, str, str]:
    """The move's emoji, name and words, as the board's list names it. A ValueError when it is not a legal move
    here."""
    for listed_move, emoji, title_, said in _named(position):
        if listed_move == move:
            return emoji, title_, said
    raise ValueError(f"{move.code} is not a legal move in {position.fen}")


@functools.lru_cache(maxsize=64)
def _named(position: Position) -> tuple[tuple[Move, str, str, str], ...]:
    return tuple((move, EMOJI[kind(position, move)], title(position, move), words(position, move))
                 for move in legal_moves(position))
