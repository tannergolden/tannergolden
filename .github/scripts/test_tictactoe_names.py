# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named for the position it makes: the 764 titles held to the rules, to perfect play and to each
other, and every board's listing as the engine shows it, whichever mark moved first.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

A title's truth is read here phrase by phrase, from tictactoe_rules.py alone and by code that shares nothing with
the script that builds the table: every word of a title belongs to a phrase this file knows, and every phrase is
true of the position its title names.
"""
from __future__ import annotations

import collections
import functools
import itertools
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tictactoe_names_table as T
import tictactoe_rules as R
from tictactoe_names import PLACES, TABLE, canonical, listing, made, names, words

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
SMALL = {"a", "an", "the", "and", "to", "of", "on", "at", "for", "in"}  # the words Title Case leaves small
SWAP = str.maketrans("XO", "OX")
TITLES = names()


# --- boards either mark opened ------------------------------------------------------------------------------------
def opening(first: str) -> R.Position:
    """The empty board, `first` to move."""
    return R.opening(first)


def board(text: str, first: str = R.X) -> R.Position:
    """A position from three rows of marks, `first` the mark that opened."""
    return R.Position.from_board(text, first)


def play(position: R.Position, cell: str) -> R.Position:
    return R.make(position, cell)


def outlook(position: R.Position) -> str:
    """Who wins with perfect play: X, O or "draw", whichever mark opened."""
    return R.outlook(position)


def reach(first: str) -> list[R.Position]:
    """Every position the game can reach, `first` to move first, the empty board and every finished one included."""
    seen, todo = {}, [opening(first)]
    while todo:
        position = todo.pop()
        if position.marks not in seen:
            seen[position.marks] = position
            todo += [play(position, cell) for cell in R.legal(position)]
    return [seen[marks] for marks in sorted(seen)]


REACHED = {first: reach(first) for first in (R.X, R.O)}
LISTED = {first: {position: listing(position, 1, 1) for position in found if R.legal(position)}
          for first, found in REACHED.items()}  # every board's listing, once for every test here


def reading(position: R.Position) -> str:
    """The marks as the board is read, top row first: `XO.X.O...`."""
    return "".join(position.at(cell) or "." for cell in R.READING)


def rows(marks: str) -> str:
    return "/".join(marks[r:r + 3] for r in (0, 3, 6))


# --- a position as the rules see it, from the side that just moved -----------------------------------------------
CORNERS, EDGES = set(R.CORNERS), {"b3", "a2", "c2", "b1"}
ACROSS = {cell: R.READING[8 - i] for i, cell in enumerate(R.READING)}  # the cell across the centre
BESIDE = {"a3": ("b3", "a2"), "c3": ("b3", "c2"), "a1": ("a2", "b1"), "c1": ("c2", "b1")}  # a corner's two edges
NUMBER = {"No": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9}
KINDS = {"Centre": {R.CENTRE}, "Corner": CORNERS, "Edge": EDGES}


def kind(cell: str) -> str:
    return "Centre" if cell == R.CENTRE else "Corner" if cell in CORNERS else "Edge"


def line_kind(line: tuple[str, ...]) -> str:
    """A line as the titles call it: a Diagonal (corner to corner through the centre), a Middle (edge to edge through
    it) or a Side."""
    if R.CENTRE not in line:
        return "Side"
    return "Diagonal" if any(cell in CORNERS for cell in line) else "Middle"


def two_words(found: list[str]) -> str:
    order = ("Centre", "Diagonal", "Middle", "Side", "Edge")
    a, b = sorted(found, key=order.index)
    if a == b:
        return {"Diagonal": "Both Diagonals", "Middle": "Both Middles", "Side": "Two Sides", "Edge": "Two Edges"}[a]
    return f"the {a} and the {b}"


def shape(cells: list[str]) -> str | None:
    """Two or three marks as one shape, as a player would say it: Opposite Corners, the Centre and an Edge."""
    if len(cells) == 2:
        a, b = sorted(cells, key=lambda c: ("Centre", "Corner", "Edge").index(kind(c)))
        if a == R.CENTRE:
            return f"the Centre and {'a' if b in CORNERS else 'an'} {kind(b)}"
        if kind(a) == kind(b):
            return f"{'Opposite' if ACROSS[a] == b else 'Adjacent'} {kind(a)}s"
        return "a Corner and Its Edge" if b in BESIDE[a] else "a Corner and a Far Edge"
    if len(cells) == 3:
        count = collections.Counter(kind(c) for c in cells)
        parts = (["the Centre"] if count["Centre"] else []) + [
            f"{'a' if k == 'Corner' else 'an'} {k}" if count[k] == 1 else f"{['', '', 'Two', 'Three'][count[k]]} {k}s"
            for k in ("Corner", "Edge") if count[k]]
        return " and ".join(parts) if len(parts) > 1 else None
    return None


def worth(position: R.Position, mark: str) -> str:
    best = R.outlook(position)
    return "draw" if best == "draw" else "win" if best == mark else "loss"


class View:
    """A position from the table, read from the side that just moved (the mover) against the other (them)."""

    def __init__(self, key: str):
        p = self.position = R.Position.from_board(key)
        self.n = sum(1 for mark in p.marks if mark)
        self.mover = R.X if self.n % 2 else R.O
        self.them = R.other(self.mover)
        self.mine = [c for c in R.READING if p.at(c) == self.mover]
        self.theirs = [c for c in R.READING if p.at(c) == self.them]
        self.empty = [c for c in R.READING if not p.at(c)]
        self.won = [line for line in R.LINES if all(p.at(c) == self.mover for c in line)]
        self.mt = R.threats(p, self.mover)  # where the mover could win next
        self.tt = R.threats(p, self.them)  # where they could
        self.result = worth(p, self.mover)

    def lines(self, mark: str, third: str) -> list[tuple[str, ...]]:
        """The lines with two of `mark` on them and the third cell `third`: "" for open, or the other mark."""
        return [line for line in R.LINES if sum(self.position.at(c) == mark for c in line) == 2
                and any(self.position.at(c) == third for c in line)]

    def threat_word(self, cell: str, mark: str) -> str:
        """A threat named by where it wins: the Centre, or a Diagonal or a Middle won on a corner or an edge, or a
        Side won on a corner, or an Edge (a side won on its edge)."""
        if cell == R.CENTRE:
            return "Centre"
        found = [line_kind(line) for line in self.lines(mark, "") if cell in line]
        return ("Side" if cell in CORNERS else "Edge") if found[0] == "Side" else found[0]

    def race(self, cells: list[str], mark: str) -> str:
        """The kind of line a single threat wins, or Fork for two threats (one cell that would win two kinds of line
        has no one name)."""
        found = {line_kind(line) for line in self.lines(mark, "") if cells[0] in line}
        return "Fork" if len(cells) > 1 else found.pop() if len(found) == 1 else "?"

    @functools.cached_property
    def made_from(self) -> list[R.Position]:
        """Every board, the mover to move, from which one of the mover's marks makes this position."""
        out = []
        for cell in self.mine:
            marks = list(self.position.marks)
            marks[R.INDEX[cell]] = ""
            before = R.Position(tuple(marks))
            if not R.ending(before):
                out.append(before)
        return out

    @functools.cached_property
    def before(self) -> set[str]:
        """What those boards were worth to the mover."""
        return {worth(b, self.mover) for b in self.made_from}

    @functools.cached_property
    def only(self) -> bool:
        """Whether from every one of those boards this is the one position, up to the board's turns and mirrors, a
        move can make that keeps what the board was worth."""
        for b in self.made_from:
            keep = worth(b, self.mover)
            kept = {canonical(reading(R.make(b, c))) for c in R.legal(b) if worth(R.make(b, c), self.mover) == keep}
            if len(kept) != 1:
                return False
        return True

    @functools.cached_property
    def replies(self) -> dict[str, str]:
        """What each open cell is worth to them, as their reply."""
        return {c: worth(R.make(self.position, c), self.them) for c in self.empty}

    @functools.cached_property
    def forks(self) -> list[str]:
        """The cells where their mark would make two threats the mover can't answer with a win."""
        out = []
        for c in self.empty:
            after = R.make(self.position, c)
            if not R.ending(after) and len(R.threats(after, self.them)) >= 2 and not R.threats(after, self.mover):
                out.append(c)
        return out

    @functools.cached_property
    def block(self) -> list[str]:
        """When the mover threatens one cell: the threats their block there makes."""
        return R.threats(R.make(self.position, self.mt[0]), self.them) if len(self.mt) == 1 else []

    @functools.cached_property
    def soon(self) -> bool:
        """Whether they win within their next two marks whatever the mover does: a fork, or a block that forks."""
        for c in self.empty:
            after = R.make(self.position, c)
            if R.ending(after):
                continue
            if all(not R.ending(R.make(after, r)) and R.threats(R.make(after, r), self.them) for r in R.legal(after)):
                return True
        return False

    @functools.cached_property
    def fork_next(self) -> bool:
        """Whether, after their block of the mover's one threat, the mover has a fork they cannot answer."""
        blocked = R.make(self.position, self.mt[0])
        for c in R.legal(blocked):
            after = R.make(blocked, c)
            if not R.ending(after) and len(R.threats(after, self.mover)) >= 2 and not R.threats(after, self.them):
                return True
        return False

    def guards(self) -> str | None:
        """The lines of theirs the mover holds a mark on, two of theirs beside it, as a title says them."""
        found = [line_kind(line) for line in self.lines(self.them, self.mover)]
        if len(found) > 2:
            return f"{['', '', '', 'Three', 'Four', 'Five'][len(found)]} Lines"
        return two_words(found) if len(found) == 2 else f"the {found[0]}" if found else None

    def pairs(self) -> list[tuple[tuple[str, ...], str]]:
        """Each line with two of the mover's marks and one of theirs, with the cell theirs is on."""
        return [(line, next(c for c in line if self.position.at(c) == self.them))
                for line in self.lines(self.mover, self.them)]

    def safe(self) -> tuple[list[str], list[str]]:
        """Their replies that keep the most they can, and the ones that lose some of it."""
        best = max(self.replies.values(), key=["loss", "draw", "win"].index)
        return ([c for c, r in self.replies.items() if r == best], [c for c, r in self.replies.items() if r != best])

    def count(self, cells: list[str], k: str) -> int:
        return sum(1 for c in cells if kind(c) == k)


@functools.cache
def view(key: str) -> View:
    return View(key)


def their_marks(v: View) -> str | None:
    """Their marks as a winning title passes them: a shape of two, or how many of each kind."""
    if len(v.theirs) == 2:
        a, b = sorted(v.theirs, key=lambda c: ("Centre", "Corner", "Edge").index(kind(c)))
        if a == R.CENTRE:
            return f"Centre and {kind(b)}"
        if kind(a) == kind(b):
            return f"{'Opposite' if ACROSS[a] == b else 'Adjacent'} {kind(a)}s"
        return "Corner and Its Edge" if b in BESIDE[a] else "Corner and Far Edge"
    count = collections.Counter(kind(c) for c in v.theirs)
    parts = [k if count[k] == 1 else f"{['', '', 'Two', 'Three', 'Four'][count[k]]} {k}s"
             for k in ("Centre", "Corner", "Edge") if count[k]]
    return " and ".join(parts) if len(parts) <= 2 else None


def blocked(v: View) -> set[str]:
    """The kinds of the mover's lines that hold two of its marks and one of theirs, not on the centre (a flank) nor
    on an edge between two of its corners (a split)."""
    return {line_kind(line) for line, cell in v.pairs()
            if cell != R.CENTRE and not (cell in EDGES and all(c in CORNERS for c in line if c != cell))}


# --- every phrase a title can hold, with what makes it true ------------------------------------------------------
LINE = r"(Diagonal|Middle|Side)"
WHERE = r"(Centre|Diagonal|Middle|Side|Edge)"  # where a threat wins
COUNT = r"(Two|Three|Four|Five|Six|Seven|Eight|Nine)"
PAIR = r"(Both Diagonals|Both Middles|Two Sides|Two Edges|the (?:Centre|Diagonal|Middle|Side) and the \w+)"
SHAPE = (r"(the Centre and (?:a Corner|an Edge|Two Corners|Two Edges|a Corner and an Edge)|Opposite Corners|"
         r"Adjacent Corners|Opposite Edges|Adjacent Edges|a Corner and Its Edge|a Corner and a Far Edge|"
         r"Two Corners and an Edge|a Corner and Two Edges)")
GROUP = r"(?:Centre|Corner|Edge|(?:Two|Three|Four) (?:Corners|Edges))"
THEIRS = rf"((?:Opposite|Adjacent) (?:Corners|Edges)|Corner and (?:Its|Far) Edge|{GROUP}(?: and {GROUP})?)"


def word(v: View, cells: list[str], mark: str) -> str:
    return v.threat_word(cells[0], mark) if len(cells) == 1 else "?"


def fork_said(v: View) -> str:
    found = [v.threat_word(c, v.mover) for c in v.mt]
    return two_words(found) if len(found) == 2 else "Three Ways" if len(found) == 3 else "?"


def won(v: View) -> list[str]:
    return sorted(line_kind(line) for line in v.won)


# (pattern, truth): a phrase a title may hold, and what must be true of its position when it does. A phrase is read
# whole before any shorter one inside it, in the order below.
PHRASES = [
    # three in a row
    (rf"Win {PAIR} at Once", lambda v, m: len(v.won) == 2 and two_words(won(v)) == m[1]),
    (rf"Win the {LINE} on the Last Cell", lambda v, m: won(v) == [m[1]] and not v.empty),
    (r"Win on the Last Cell", lambda v, m: len(v.won) == 1 and not v.empty),
    (rf"Win Your {LINE} Before Theirs", lambda v, m: won(v) == [m[1]] and v.tt and v.race(v.tt, v.them) == m[1]),
    (rf"Win the {LINE} Before Their (Diagonal|Middle|Side|Fork)",
     lambda v, m: won(v) == [m[1]] and v.tt and v.race(v.tt, v.them) == m[2] != m[1]),
    (rf"Win the Race Down the {LINE}", lambda v, m: won(v) == [m[1]] and v.tt),
    (r"Take One (Diagonal|Middle) Over the Other|Take One (Side) Over Another",
     lambda v, m: won(v) == [m[1] or m[2]] and v.race(v.mt, v.mover) == (m[1] or m[2])),
    (rf"Take the {LINE} Over (Two|Three) More", lambda v, m: won(v) == [m[1]] and len(v.mt) == NUMBER[m[2]]),
    (rf"Take the {LINE} Over the (Diagonal|Middle|Side)",
     lambda v, m: won(v) == [m[1]] and len(v.mt) == 1 and v.race(v.mt, v.mover) == m[2] != m[1]),
    (rf"Win the {LINE}", lambda v, m: won(v) == [m[1]]),
    (r"Draw on the Last Cell", lambda v, m: not v.won and not v.empty),
    # winning by force
    (rf"Fork {PAIR}|Fork Three Ways",
     lambda v, m: v.result == "win" and not v.won and m[0] == f"Fork {fork_said(v)}"),
    (rf"Threaten the {WHERE} and Fork Next",
     lambda v, m: v.result == "win" and len(v.mt) == 1 and word(v, v.mt, v.mover) == m[1] and v.fork_next),
    (r"and Fork Next", lambda v, m: v.result == "win" and len(v.mt) == 1 and v.fork_next),
    (r"and Fork", lambda v, m: v.result == "win" and len(v.mt) >= 2 and not v.won),
    (r"Leave Them No Safe Reply", lambda v, m: v.result == "win" and set(v.replies.values()) == {"loss"}),
    # losing at once
    (rf"Hand Them the {WHERE} on the Last Cell",
     lambda v, m: v.result == "loss" and len(v.empty) == 1 and word(v, v.tt, v.them) == m[1]),
    (r"(?:and )?Hand Them the Last Cell", lambda v, m: v.result == "loss" and v.tt == v.empty),
    (rf"Hand Them the {WHERE}", lambda v, m: v.result == "loss" and word(v, v.tt, v.them) == m[1]),
    (r"(?:and )?Leave Them (Two|Three) Wins", lambda v, m: v.result == "loss" and len(v.tt) == NUMBER[m[1]]),
    (rf"Leave Them {PAIR}", lambda v, m: v.result == "loss" and len(v.tt) == 2
     and two_words([v.threat_word(c, v.them) for c in v.tt]) == m[1]),
    (r"Guard One (Diagonal|Middle) and Lose to the Other|Guard One (Side) and Lose to Another",
     lambda v, m: v.result == "loss" and v.guards() == f"the {m[1] or m[2]}"
     and word(v, v.tt, v.them) == (m[1] or m[2])),
    (rf"Fork Too Late for the {WHERE}",
     lambda v, m: v.result == "loss" and len(v.mt) >= 2 and word(v, v.tt, v.them) == m[1]),
    (r"Fork Too Late", lambda v, m: v.result == "loss" and len(v.mt) >= 2 and v.tt),
    (rf"and Lose to the {WHERE}", lambda v, m: v.result == "loss" and word(v, v.tt, v.them) == m[1]),
    (r"and Lose to Theirs", lambda v, m: v.result == "loss" and len(v.mt) == 1
     and word(v, v.tt, v.them) == word(v, v.mt, v.mover)),
    (r"and Lose", lambda v, m: v.result == "loss" and v.tt),
    # losing to a fork, now or later
    (rf"Chase the {WHERE} Into a Fork",
     lambda v, m: v.result == "loss" and word(v, v.mt, v.mover) == m[1] and len(v.block) >= 2),
    (r"Force a Block That Forks You", lambda v, m: v.result == "loss" and len(v.block) >= 2),
    (r"Let Them Fork From (the Centre|a Corner|an Edge)", lambda v, m: v.result == "loss" and not v.tt and v.forks
     and all(kind(c) == m[1].split()[-1] for c in v.forks)),
    (rf"Leave Them {COUNT} Ways to Fork",
     lambda v, m: v.result == "loss" and not v.tt and not v.mt and len(v.forks) == NUMBER[m[1]]),
    (r"(?:and )?Let Them Fork", lambda v, m: v.result == "loss" and not v.tt and v.soon),
    (rf"Chase the {WHERE} Into Their Trap",
     lambda v, m: v.result == "loss" and not v.tt and word(v, v.mt, v.mover) == m[1] and not v.soon),
    (r"(?:and )?Walk Into Their Trap", lambda v, m: v.result == "loss" and not v.tt and not v.soon),
    # holding, saving and slipping
    (r"Force a Block That Threatens Back", lambda v, m: v.result == "draw" and v.block),
    (rf"(?:and )?Threaten the {WHERE}", lambda v, m: v.result == "draw" and word(v, v.mt, v.mover) == m[1]),
    (rf"Chase the {WHERE}", lambda v, m: v.result == "loss" and word(v, v.mt, v.mover) == m[1]),
    (r"(?:and )?Let the Win Slip", lambda v, m: v.result == "draw" and v.before == {"win"}),
    (r"Hold the Draw|and Hold", lambda v, m: v.result == "draw" and v.before == {"draw"}),
    (r"to Save the Draw", lambda v, m: v.result == "draw" and v.before == {"draw"} and v.only),
    (r"Leave Them One Safe Reply", lambda v, m: v.result == "draw" and len(v.safe()[0]) == 1 and v.safe()[1]),
    (r"Leave Them No Safe (Corner|Edge)", lambda v, m: v.result == "draw" and v.safe()[1]
     and not KINDS[m[1]] & set(v.safe()[0]) and KINDS[m[1]] & set(v.safe()[1])),
    (r"Set a Trap", lambda v, m: v.result == "draw" and v.safe()[1]),
    # where the marks stand
    (r"Guard(?:ing)? (the \w+ and the \w+|the \w+|Both Diagonals|Both Middles|Two Sides|\w+ Lines)",
     lambda v, m: v.guards() == m[1]),
    (r"Flank(?:ing)? Their Centre(?: From the (Corner|Edge)s)?",
     lambda v, m: any(cell == R.CENTRE and (not m[1] or kind(line[0]) == m[1]) for line, cell in v.pairs())),
    (r"With Your Corners Split",
     lambda v, m: any(cell in EDGES and line_kind(line) == "Side" for line, cell in v.pairs())),
    (rf"With Your {LINE} Blocked", lambda v, m: m[1] in blocked(v)),
    (r"Box(?:ing)? In Their Corner", lambda v, m: any(v.position.at(c) == v.them and set(e) <= set(v.mine)
                                                      for c, e in BESIDE.items())),
    (r"Surround(?:ing)? an Open Corner", lambda v, m: any(not v.position.at(c) and set(e) <= set(v.mine)
                                                          for c, e in BESIDE.items())),
    (r"Wall(?:ing)? In Your (?:Own )?Corner", lambda v, m: any(c in v.mine and set(e) <= set(v.mine)
                                                               for c, e in BESIDE.items())),
    (r"With Your Corner Boxed In",
     lambda v, m: any(c in v.mine and set(e) <= set(v.theirs) for c, e in BESIDE.items())),
    (r"Fac(?:e|ing) Their (Corner|Edge)", lambda v, m: any(ACROSS[c] in v.theirs for c in v.mine if kind(c) == m[1])),
    (r"Crowd(?:ing)? Their Corner", lambda v, m: any(e in v.mine for c in v.theirs if c in CORNERS for e in BESIDE[c])),
    (r"Scatter Your Marks|With Your Marks Scattered", lambda v, m: len(v.mine) >= 2 and not any(
        any(a in line and b in line for line in R.LINES) for a, b in itertools.combinations(v.mine, 2))),
    (r"Keep the Centre|Holding the Centre", lambda v, m: v.position.at(R.CENTRE) == v.mover),
    (r"Leave the Centre Open|With the Centre Open", lambda v, m: not v.position.at(R.CENTRE)),
    (r"Play Round Their Centre|Against Their Centre", lambda v, m: v.position.at(R.CENTRE) == v.them),
    (rf"(?:Keep|With) {SHAPE}", lambda v, m: shape(v.mine) == m[1]),
    (rf"(?:Keep|With) {COUNT} Corners", lambda v, m: v.count(v.mine, "Corner") == NUMBER[m[1]]),
    (r"(?:Keep|With) Every Corner", lambda v, m: v.count(v.mine, "Corner") == 4),
    (rf"(?:Keep|With) {COUNT} Edges", lambda v, m: v.count(v.mine, "Edge") == NUMBER[m[1]]),
    (r"(?:Keep|With) Every Edge", lambda v, m: v.count(v.mine, "Edge") == 4),
    (r"Stick to the Edges|Stay Off the Corners|With No Corner",
     lambda v, m: v.count(v.mine, "Corner") == 0 and (m[0] != "Stay Off the Corners" or R.CENTRE in v.mine)),
    (r"Keep Off the Edges|With No Edge", lambda v, m: v.count(v.mine, "Edge") == 0),
    (r"Run Out of Lines|With No Line Left|Keep One Line Alive|With One Line Left",
     lambda v, m: sum(1 for line in R.LINES if not any(v.position.at(c) == v.them for c in line))
     == (1 if "One" in m[0] else 0)),
    (rf"Past Their {THEIRS}", lambda v, m: their_marks(v) == m[1]),
    (rf"{COUNT} Marks In", lambda v, m: v.n == NUMBER[m[1]]),
    (r"^Fork", lambda v, m: v.result == "win" and len(v.mt) >= 2 and not v.won),  # a fork, its lines unsaid
]
PHRASES = [(re.compile(rf"(?<![\w-])(?:{pattern})(?![\w-])"), truth) for pattern, truth in PHRASES]


def claims(title: str) -> tuple[list[tuple[re.Match, object]], str]:
    """The phrases a title is made of, each read whole before the shorter ones, and the words left over."""
    text, found = title.rstrip("!"), []
    for pattern, truth in PHRASES:
        while m := pattern.search(text):
            found.append((m, truth))
            text = text[:m.start()] + "|" * (m.end() - m.start()) + text[m.end():]
    return found, " ".join(text.replace("|", " ").split())


# --- the tests ---------------------------------------------------------------------------------------------------
class Counts(unittest.TestCase):
    """The game counted whole, as the table counts it, either mark first."""

    def test_the_game_is_counted_whole(self):
        for first in (R.X, R.O):
            self.assertEqual(len(REACHED[first]), 5478, f"every position the game reaches, {first} first")
        shapes = {canonical(reading(p)) for p in REACHED[R.X]}
        self.assertEqual(len(shapes), 765, "765 once the board's turns and mirrors are set aside")
        shapes.discard("." * 9)
        self.assertEqual(set(TITLES), {rows(s) for s in shapes}, "764 a move makes, every one named")
        ends = collections.Counter(R.ending(p).winner or "draw" for p in map(R.Position.from_board, TITLES)
                                   if R.ending(p))
        self.assertEqual(ends, {R.X: 91, R.O: 44, "draw": 3}, "138 of them end the game")

    def test_either_mark_first_makes_the_same_positions(self):
        for first in (R.X, R.O):
            keys = {made(p, c) for p in LISTED[first] for c in R.legal(p)}
            self.assertEqual(keys, set(TITLES), f"{first} first")


class Table(unittest.TestCase):
    def test_the_table_is_what_the_script_makes(self):
        self.assertEqual(T.render(T.table()), TABLE.read_text(encoding="utf-8"),
                         "run tictactoe_names_table.py to build tictactoe_names.json again")

    def test_every_title_is_its_own(self):
        titles = collections.Counter(entry["title"] for entry in TITLES.values())
        self.assertEqual(len(titles), 764, [t for t, n in titles.items() if n > 1])

    def test_no_two_titles_claim_the_same_facts_in_other_words(self):
        """Two titles that claimed the same facts in other words would be one name twice: "Guard the Side and Leave
        Them Two Wins" and "Leave Them Two Wins Guarding the Side"."""
        claimed = collections.Counter(frozenset(e["facts"]) for k, e in TITLES.items() if view(k).n > 2)
        self.assertEqual(max(claimed.values()), 1, [sorted(f) for f, n in claimed.items() if n > 1])

    def test_the_script_plays_perfectly(self):
        for key in TITLES:
            v = view(key)
            self.assertEqual(T.worth(key.replace("/", ""), v.mover), {"win": 1, "draw": 0, "loss": -1}[v.result])

    def test_every_title_is_an_order_in_title_case(self):
        for key, entry in TITLES.items():
            title = entry["title"]
            with self.subTest(key=key, title=title):
                self.assertTrue(KIT_TITLE.fullmatch(title))
                self.assertTrue(title.endswith("!") and title.count("!") == 1)
                self.assertLessEqual(len(title), 48)
                self.assertNotRegex(title, r"\b[a-c][1-3]\b|\b[XO]\b|\d", "a title names no cell, mark or number")
                for w in title.rstrip("!").split()[1:]:
                    self.assertTrue(w in SMALL or w[0].isupper(), w)
                for dash in DASHES:
                    self.assertNotIn(dash, title)

    def test_every_title_is_true_of_its_position_phrase_by_phrase(self):
        """Every word of every title past the opening two marks belongs to a phrase, and every phrase is true."""
        used = collections.Counter()
        for key, entry in TITLES.items():
            v = view(key)
            if v.n <= 2:
                continue
            found, rest = claims(entry["title"])
            with self.subTest(key=key, title=entry["title"]):
                self.assertEqual(rest, "", "every word belongs to a phrase that is checked")
                for m, truth in found:
                    self.assertTrue(truth(v, m), f"{m[0]!r} is not true of {key}")
                    used[m.re.pattern] += 1
        self.assertGreater(len(used), 60, "the phrases run wide")

    def test_every_title_carries_its_judgement(self):
        """A loss warns and only a loss does, a win says so, and a drawn title claims no more than every board that
        makes its position agrees on."""
        for key, entry in TITLES.items():
            v, title, judged = view(key), entry["title"], entry["judgement"]
            with self.subTest(key=key, title=title):
                self.assertEqual(entry["emoji"] == "⚠️", v.result == "loss")
                self.assertEqual(entry["emoji"] == "🏆", bool(v.won))
                self.assertEqual(entry["emoji"] == "⚡", not v.won and v.result == "win" and len(v.mt) != 1)
                self.assertEqual(entry["emoji"] == "🎯", not v.won and v.result != "loss" and len(v.mt) == 1)
                if v.won:
                    self.assertRegex(title, r"^(Win|Take) ")
                    self.assertTrue(judged.startswith("wins: three in a row"))
                elif not v.empty:
                    self.assertEqual(entry["emoji"], "🤝")
                    self.assertTrue(title.startswith("Draw on the Last Cell"))
                elif v.result == "win":
                    self.assertRegex(title, r"Fork|No Safe Reply")
                    self.assertTrue(judged.startswith("wins by force"))
                elif v.result == "loss":
                    self.assertRegex(title, r"Lose|Hand Them|Leave Them (Two|Three|Both|the)|Let Them Fork|"
                                            r"Ways to Fork|Forks You|Into a Fork|Trap|Too Late")
                    self.assertRegex(judged, r"^(throws away a won game and )?loses by force")
                    self.assertEqual(judged.startswith("throws away"), v.before == {"win"})
                else:
                    self.assertNotRegex(title, r"Win (?!Slip)|Fork|Lose|Hand Them")
                    self.assertEqual("Slip" in title, v.before == {"win"})
                    self.assertEqual(judged.startswith("throws away a won game"), v.before == {"win"})
                    self.assertEqual(judged.startswith("holds the draw"), v.before == {"draw"})
                    self.assertEqual("the only move" in judged, v.before == {"draw"} and v.only)
                    if v.n > 1:
                        self.assertEqual("Save the Draw" in title, v.before == {"draw"} and v.only)


class Openings(unittest.TestCase):
    """The first two marks, named for where they stand and judged as perfect play judges them."""

    def replies(self, *cells: str) -> dict[str, dict]:
        position = R.START
        for cell in cells:
            position = R.make(position, cell)
        return {entry["code"]: entry for entry in listing(position, 1, 1)}

    def test_the_three_openings(self):
        opened = self.replies()
        self.assertEqual((opened["b2"]["emoji"], opened["b2"]["title"]), ("⭐", "Seize the Centre!"))
        self.assertEqual((opened["a3"]["emoji"], opened["a3"]["title"]), ("📐", "Claim a Corner, Upper Left!"))
        self.assertEqual((opened["c1"]["emoji"], opened["c1"]["title"]), ("📐", "Claim a Corner, Lower Right!"))
        self.assertEqual((opened["b3"]["emoji"], opened["b3"]["title"]), ("📏", "Open on an Edge, Top!"))
        self.assertEqual(opened["a2"]["title"], "Open on an Edge, Left!")

    def test_against_the_centre_a_corner_holds_and_an_edge_loses(self):
        for cell, entry in self.replies("b2").items():
            if cell in CORNERS:
                self.assertEqual((entry["emoji"], entry["title"]),
                                 ("📐", f"Save the Draw From a Corner, {PLACES[cell]}!"))
            else:
                self.assertEqual((entry["emoji"], entry["title"]),
                                 ("⚠️", f"Take an Edge and Lose to the Centre, {PLACES[cell]}!"))
            self.assertEqual(outlook(R.make(R.make(R.START, "b2"), cell)) == "draw", cell in CORNERS)

    def test_against_a_corner_only_the_centre_holds(self):
        replies = self.replies("a3")
        self.assertEqual((replies["b2"]["emoji"], replies["b2"]["title"]), ("⭐", "Save the Draw From the Centre!"))
        self.assertEqual(replies["c1"]["title"], "Take the Opposite Corner and Lose!")
        self.assertEqual(replies["c3"]["title"], "Take an Adjacent Corner and Lose, Upper Right!")
        self.assertEqual(replies["b3"]["title"], "Take an Adjacent Edge and Lose, Top!")
        self.assertEqual(replies["c2"]["title"], "Take a Far Edge and Lose, Right!")
        for cell, entry in replies.items():
            self.assertEqual(entry["emoji"] == "⚠️", cell != "b2")
            self.assertEqual(outlook(R.make(R.make(R.START, "a3"), cell)) == "draw", cell == "b2")

    def test_against_an_edge_three_replies_hold(self):
        replies = self.replies("b3")
        self.assertEqual(replies["b2"]["title"], "Hold the Centre Against Their Edge!")
        self.assertEqual(replies["a3"]["title"], "Hold the Corner Beside Their Edge, Upper Left!")
        self.assertEqual(replies["b1"]["title"], "Hold the Edge Across From Theirs!")
        self.assertEqual(replies["a2"]["title"], "Take the Edge Beside Theirs and Lose, Left!")
        self.assertEqual(replies["a1"]["title"], "Take a Far Corner and Lose, Lower Left!")
        for cell, entry in replies.items():
            holds = outlook(R.make(R.make(R.START, "b3"), cell)) == "draw"
            self.assertEqual((entry["emoji"] == "⚠️", entry["title"].startswith("Hold")), (not holds, holds), cell)


class Moments(unittest.TestCase):
    """The turning points of a game, named for what they are."""

    def entry(self, text: str, cell: str, first: str = R.X) -> dict:
        return next(e for e in listing(board(text, first), 1, 1) if e["code"] == cell)

    def test_a_fork_is_named_for_the_two_lines_it_threatens(self):
        entry = self.entry("XOX/O../...", "b2")
        self.assertEqual((entry["emoji"], entry["title"]), ("⚡", "Fork Both Diagonals!"))
        self.assertEqual(entry["words"], "X takes the centre, threatening a1 and c1")

    def test_a_block_shows_as_one_and_every_other_cell_loses(self):
        named = {e["code"]: e for e in listing(board("XX./.O./..."), 1, 1)}
        self.assertEqual(named["c3"]["emoji"], "🛡️")
        self.assertEqual(named["c3"]["words"], "O blocks on c3, threatening a1")
        self.assertEqual(named["c3"]["title"], TITLES[made(board("XX./.O./..."), "c3")]["title"])
        self.assertTrue(all(e["emoji"] == "⚠️" for cell, e in named.items() if cell != "c3"))

    def test_a_win_is_three_in_a_row_on_its_line(self):
        entry = self.entry("XX./OO./...", "c3")
        self.assertEqual((entry["emoji"], entry["notation"]), ("🏆", "Xc3#"))
        self.assertEqual(entry["words"], "X takes c3, three in a row from a3 to c3")
        self.assertTrue(entry["title"].startswith("Win the Side Before Their Middle"), entry["title"])

    def test_passing_up_the_win_is_named_as_the_slip_it_is(self):
        entry = self.entry("XX./OO./...", "c2")  # X blocks the middle when c3 wins: a draw
        self.assertEqual(outlook(play(board("XX./OO./..."), "c2")), "draw")
        self.assertIn("Let the Win Slip", entry["title"])

    def test_the_only_move_that_holds_is_named_as_the_save(self):
        named = {e["code"]: e for e in listing(board("X../.O./..X"), 1, 1)}  # O against opposite corners
        for cell, entry in named.items():
            if cell in EDGES:
                self.assertEqual(entry["title"], f"Threaten the Middle to Save the Draw, {PLACES[cell]}!")
            else:
                self.assertEqual(entry["title"], f"Chase the Diagonal Into a Fork, {PLACES[cell]}!")
                self.assertEqual(entry["emoji"], "⚠️")

    def test_the_last_cell_draws(self):
        entry = self.entry("XOX/XOO/OX.", "c1")
        self.assertEqual((entry["emoji"], entry["title"]), ("🤝", "Draw on the Last Cell!"))
        self.assertEqual(entry["words"], "X takes the lower right corner, the last cell, for a draw")


class Words(unittest.TestCase):
    """A move's words say what it does, plainly, whichever mark opened."""

    CASES = (
        ("OOX/..X/...", "c1", "X takes c1, three in a row from c1 to c3"),
        ("XX./..O/...", "c3", "O blocks on c3, threatening c1"),
        (".XX/..O/...", "a3", "O blocks on a3"),
        (".XX/..O/...", "a2", "O takes the left edge, threatening b2, leaving a3 to X"),
        ("OXX/..O/...", "b2", "X takes the centre, threatening a1 and b1"),
        (".OX/.../...", "b2", "X takes the centre, threatening a1"),
        (".../.../...", "a3", "X takes the upper left corner"),
        (".../.../...", "b3", "X takes the head of the board"),
        ("X.X/.O./X.O", "b1", "O takes the foot of the board, threatening b3, leaving b3 and a2 to X"),
        ("XOX/XOO/OX.", "c1", "X takes the lower right corner, the last cell, for a draw"),
    )

    def test_the_words_say_what_the_move_does(self):
        for text, cell, said in self.CASES:
            self.assertEqual(words(board(text), cell), said)

    def test_o_s_moves_read_the_same_when_o_moved_first(self):
        self.assertEqual(words(opening(R.O), "b2"), "O takes the centre")
        position = board("OO./.X./...", R.O)  # O opened, and X is to move against a3 and b3
        self.assertEqual(words(position, "c3"), "X blocks on c3, threatening a1")
        self.assertEqual(words(position, "a1"), "X takes the lower left corner, threatening c3, leaving c3 to O")
        for text, cell, said in self.CASES:
            self.assertEqual(words(board(text.translate(SWAP), R.O), cell), said.translate(SWAP))


class Boards(unittest.TestCase):
    """Every board of every game, either mark first, as the engine lists it."""

    def test_every_open_cell_is_listed_in_what_the_kit_accepts(self):
        for first, listed in LISTED.items():
            for position, entries in listed.items():
                self.assertEqual([e["code"] for e in entries], R.legal(position))
                for e in entries:
                    with self.subTest(first=first, board=position.board, cell=e["code"]):
                        self.assertTrue(KIT_EMOJI.fullmatch(e["emoji"]))
                        self.assertTrue(KIT_TITLE.fullmatch(e["title"]) and len(e["title"]) <= 48)
                        self.assertTrue(KIT_WORDS.fullmatch(e["words"]) and len(e["words"]) <= 80)
                        self.assertEqual(e["notation"], R.notation(position, e["code"]))
                        for dash in DASHES:
                            self.assertNotIn(dash, e["title"] + e["words"])

    def test_no_two_moves_on_one_board_share_a_title(self):
        for first, listed in LISTED.items():
            for position, entries in listed.items():
                titles = [e["title"] for e in entries]
                self.assertEqual(len(set(titles)), len(titles), (first, position.board, titles))

    def test_mirror_twins_share_a_title_and_add_their_place(self):
        twins = 0
        for listed in LISTED.values():
            for position, entries in listed.items():
                keys = {e["code"]: made(position, e["code"]) for e in entries}
                repeats = collections.Counter(keys.values())
                for e in entries:
                    title = TITLES[keys[e["code"]]]["title"]
                    if repeats[keys[e["code"]]] > 1:
                        self.assertEqual(e["title"], f"{title[:-1]}, {PLACES[e['code']]}!")
                        twins += 1
                    else:
                        self.assertEqual(e["title"], title)
        self.assertGreater(twins, 1000)

    def test_o_first_reads_as_x_first_with_the_marks_swapped(self):
        for position, entries in LISTED[R.O].items():
            mirror = R.Position.from_board(position.board.translate(SWAP))
            for e, x in zip(entries, LISTED[R.X][mirror], strict=True):
                self.assertEqual((e["code"], e["emoji"], e["title"]), (x["code"], x["emoji"], x["title"]))
                self.assertEqual((e["notation"], e["words"]),
                                 (x["notation"].translate(SWAP), x["words"].translate(SWAP)))

    def test_a_move_is_named_the_same_in_every_game_and_at_every_move(self):
        position = board("X../.O./...")
        self.assertEqual(listing(position, 1, 3), listing(position, 7, 3))
        self.assertEqual(listing(position, 1, 3), listing(position, 2, 5))

    def test_every_emoji_says_what_its_move_does(self):
        """🏆 wins, 🛡️ blocks unless it wins or forks, ⚠️ loses by force, 🤝 draws on the last cell, ⚡ forks or wins
        as surely without a threat, 🎯 threatens, and a quiet move shows where its mark goes."""
        seen = collections.Counter()
        for listed in LISTED.values():
            for position, entries in listed.items():
                mover, them = position.turn, R.other(position.turn)
                menace = R.threats(position, them)
                for e in entries:
                    after = play(position, e["code"])
                    end, best = R.ending(after), outlook(after)
                    makes = [] if end else R.threats(after, mover)
                    if end and end.winner:
                        want = "🏆"
                    elif e["code"] in menace and not (best == mover and len(makes) != 1):
                        want = "🛡️"
                    elif best == them:
                        want = "⚠️"
                    elif end:
                        want = "🤝"
                    elif best == mover and len(makes) != 1:
                        want = "⚡"
                    elif makes:
                        want = "🎯"
                    else:
                        want = {"Centre": "⭐", "Corner": "📐", "Edge": "📏"}[kind(e["code"])]
                    self.assertEqual(e["emoji"], want, (position.board, e))
                    seen[want] += 1
        self.assertEqual(len(seen), 9, "every sign comes up")


if __name__ == "__main__":
    unittest.main()
