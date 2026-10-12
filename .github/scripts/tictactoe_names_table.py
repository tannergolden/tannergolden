#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Build tictactoe_names.json: a title for every Tic-Tac-Toe move, from where its mark goes and nothing else.

  python3 .github/scripts/tictactoe_names_table.py          write the table
  python3 .github/scripts/tictactoe_names_table.py --check  fail if the table is not what this script makes

A move is read from the mover's side, the mark that moved first written X, and
taken up to the board's eight turns and mirrors: 2,096 moves from 627 boards,
making the 764 positions the game can reach once a mark goes down. No two moves
share a title, nor claim the same facts in other words; a move's mirror twins
share its title, and the listing adds their place. A title is built in three
steps:

1. The facts. Only what the board plainly shows about the cell the mark
   takes: its kind (the centre, a corner or an edge); the marks touching it,
   by a side or at a corner, each side's named by kind or counted; the mark
   across the centre from it; for a corner, the two corners a cell along from
   it; the marks that do none of these; every mark the other side has; the
   mover's count of marks, and of cells of this kind; and, where nothing
   plainer is left, how a mark touching the cell sits by one of the other
   side's (beside it, or across the centre from it), or a distant mark that
   touches one. Nothing about a row, a column or a diagonal and what it holds,
   nothing about who wins, and nothing a move ahead. The game's first mark
   has a fact of its own: it starts the game.
2. The details. Each move may take any words that fit in 100 characters and
   are true of its own cell and of no other on its board (its mirror twins
   aside); on a few crowded boards, where a cell can be told apart only by
   words too long, it may take true words that also fit a neighbour whose own
   title is true of it alone, and says "a corner". Every move then takes a
   different set of facts, the whole game at once, by an exact assignment over
   each move's cheapest titles at the least total cost: each title's length
   and a little more for the less plain words, weighed so the boards that come
   up most, early in a game, keep the shortest titles.
3. The lead. Every move on one board opens alike, by a hash of the board among
   the leads that fit all its titles: "Take the Corner", "Mark an Edge",
   "Take Your Second Corner", "Lay Your Third Mark in the Corner". A lead that
   counts goes only where every title on its board stays short and its count
   makes no title claim what another does; the empty board's lead is "Start".

The table keeps each move's title and the facts it claims, so a title can be
read against its board. Stdlib only, with tictactoe_rules.py and
tictactoe_names.py beside it.
"""
from __future__ import annotations

import argparse
import collections
import functools
import heapq
import itertools
import json
import math
import sys
import zlib
from pathlib import Path

import tictactoe_rules as R
from tictactoe_names import TABLE, canonical

# --- the board as a string: nine marks in the order the board is read, a3 b3 c3 a2 b2 c2 a1 b1 c1 ---------------
KIND = tuple("centre" if cell == R.CENTRE else "corner" if cell in R.CORNERS else "edge" for cell in R.READING)
SPOT = tuple(divmod(i, 3) for i in range(9))  # each cell's row and column
LINES = tuple(tuple(R.READING.index(cell) for cell in line) for line in R.LINES)
EMPTY = "." * 9
LONGEST = 100  # the longest title, a twin's place and its "!" included, tannergolden/markdown takes
ROOM = {"corner": len("Upper Right"), "edge": len("Bottom")}  # the longest place a twin of each kind can carry

# --- the words titles are made of ----------------------------------------------------------------------------------
CELL = {"centre": "Centre", "corner": "Corner", "edge": "Edge"}
ORDINAL = ("", "First", "Second", "Third", "Fourth", "Fifth")
NUMBER = ("No", "One", "Two", "Three", "Four")
OWNER = {"your": "Your", "their": "Their"}
OWNS = {"your": "Yours", "their": "Theirs"}
# The leads a board's titles open with. A board's hash picks one among those that fit every title on it ("take" and
# "mark" always do), so every move on one board opens alike.
LEADS = ("take", "mark", "lay", "count", "set")
# What each kind of detail costs a title beyond its length: the plainest words come cheapest.
COST = {"by": 0, "count": 3, "none": 4, "across": 0, "along": 1, "away": 2, "nest-by": 6, "nest-away": 7, "against": 2,
        "mark": 2, "shared": 30}
FEW = 4  # a move with fewer titles true of its cell alone may take one that is true of a neighbour too
CHOICES = 80  # the cheapest titles of each move the assignment weighs: more change nothing
SHORT = 60  # a lead that counts ("Lay Your Third Mark in the Corner") only where every title on its board stays short
FAMILIES = ("by", "nest-by", "nest-across", "across", "along", "away", "nest-away", "against", "mark")  # in order


def flip(side: str) -> str:
    """The other side: "your" for "their", and "their" for "your"."""
    return "their" if side == "your" else "your"


def touching(a: int, b: int) -> bool:
    """Whether two cells touch, by a side or at a corner."""
    return a != b and abs(SPOT[a][0] - SPOT[b][0]) <= 1 and abs(SPOT[a][1] - SPOT[b][1]) <= 1


def beside(a: int, b: int) -> bool:
    """Whether two cells share a side."""
    return abs(SPOT[a][0] - SPOT[b][0]) + abs(SPOT[a][1] - SPOT[b][1]) == 1


def across(a: int, b: int) -> bool:
    """Whether two cells face each other over the centre."""
    return a + b == 8 and a != 4


def along(a: int, b: int) -> bool:
    """Whether two corners are a cell apart along the edge of the board."""
    return a != b and KIND[a] == KIND[b] == "corner" and (SPOT[a][0] == SPOT[b][0] or SPOT[a][1] == SPOT[b][1])


def kinds(cells: list[str]) -> str:
    """Kinds of cell in a title's words: `Edge`, `Two Corners`, `Centre and Edge`, `Centre, Corner and Edge`."""
    count = collections.Counter(cells)
    parts = [CELL[k] if count[k] == 1 else f"{NUMBER[count[k]]} {CELL[k]}s" for k in CELL if count[k]]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def won(board: str) -> bool:
    return any(board[a] != "." and board[a] == board[b] == board[c] for a, b, c in LINES)


def turn(board: str) -> str:
    """Whose mark goes down next, X having moved first."""
    return "X" if board.count("X") == board.count("O") else "O"


def reachable() -> set[str]:
    """Every board the game can reach, X first."""
    seen, todo = set(), [EMPTY]
    while todo:
        board = todo.pop()
        if board in seen:
            continue
        seen.add(board)
        if not won(board) and "." in board:
            todo += [board[:i] + turn(board) + board[i + 1:] for i in range(9) if board[i] == "."]
    return seen


SEEN = reachable()
BOARDS = sorted({canonical(board) for board in SEEN if not won(board) and "." in board})  # the boards a move is made on


def key(board: str, i: int) -> str:
    """A move's key: the marks after it, the new one in lower case, taken up to the board's turns and mirrors."""
    marks = canonical(board[:i] + turn(board).lower() + board[i + 1:])
    return "/".join(marks[r:r + 3] for r in (0, 3, 6))


# --- the facts -----------------------------------------------------------------------------------------------------
class Move:
    """A move, from its key: the cell its mark takes and where every other mark stands from there."""

    def __init__(self, text: str):
        self.key = text
        marks = text.replace("/", "")
        self.new = next(i for i, mark in enumerate(marks) if mark.islower())
        self.board = marks.upper()
        self.mover = self.board[self.new]
        self.kind = KIND[self.new]
        self.mine = [i for i, mark in enumerate(self.board) if mark == self.mover and i != self.new]
        self.theirs = [i for i, mark in enumerate(self.board) if mark not in (".", self.mover)]
        self.marks = len(self.mine) + 1  # which of the mover's marks this is
        self.count = 1 + sum(1 for i in self.mine if KIND[i] == self.kind)  # and which of its cells of this kind
        self.n = len(self.mine) + 1 + len(self.theirs)

    def owner(self, i: int) -> str | None:
        return "your" if i in self.mine or i == self.new else "their" if i in self.theirs else None

    def far(self, i: int) -> bool:
        """Whether a cell neither touches the move's cell, nor faces it, nor is a corner along from it."""
        return i != self.new and not touching(i, self.new) and not across(i, self.new) and not along(i, self.new)

    @functools.cached_property
    def facts(self) -> frozenset:
        """Every fact a title can claim of the move, each of one side's marks ("your" or "their") and exact."""
        new, out = self.new, {("cell", self.kind), ("mark", self.marks), ("count", self.count)}
        if self.theirs and self.kind != "centre":  # every mark touches the centre, where "by" says it all
            out.add(("against", tuple(sorted(KIND[i] for i in self.theirs))))
        if self.n == 1:
            out.add(("start",))
        for side, cells in (("your", self.mine), ("their", self.theirs)):
            near = tuple(sorted(KIND[i] for i in cells if touching(i, new)))
            out.add(("by", side, near))
            out.add(("by-count", side, len(near)))
            if self.kind == "corner":
                out.add(("along", side, sum(1 for i in cells if along(i, new))))
            away = tuple(sorted(KIND[i] for i in cells if self.far(i)))
            if away and not set(away) & set(near):  # away from their edge, and no edge of theirs touches it
                out.add(("away", side, away))
            for i in cells:
                for j in self.mine + self.theirs:
                    if self.owner(j) == side:
                        continue
                    if touching(i, new) and beside(i, j):
                        out.add(("nest-by", side, KIND[i], self.owner(j)))
                        out.add(("nest-by", side, KIND[i], self.owner(j), KIND[j]))
                    if touching(i, new) and across(i, j):
                        out.add(("nest-across", side, KIND[i], self.owner(j), KIND[j]))
                    if self.far(i) and touching(i, j):  # their edge away from it by yours, or their other edge
                        name = "nest-away" if KIND[i] not in near else "nest-away-other"
                        out.add((name, side, KIND[i], self.owner(j)))
                        out.add((name, side, KIND[i], self.owner(j), KIND[j]))
        if self.kind != "centre":
            facing = self.owner(8 - new)
            if facing:
                out.add(("across", facing))
        return frozenset(out)


def details(m: Move) -> list[tuple[str, frozenset, float, str]]:
    """Every detail a title can give the move, as (words, facts, cost beyond its length, family): one phrase each."""
    facts, out = m.facts, []
    by = {side: next(f[2] for f in facts if f[:2] == ("by", side)) for side in OWNER}
    has = {"your": bool(m.mine), "their": bool(m.theirs)}

    def says(side: str) -> list[tuple[str, set, float]]:
        """The ways to say one side's marks touching the cell: their kinds, or how many there are."""
        near = by[side]
        if not near:
            return []
        return [(f"{OWNER[side]} {kinds(near)}", {("by", side, near)}, COST["by"]),
                (f"{NUMBER[len(near)]} of {OWNS[side]}", {("by-count", side, len(near))}, COST["count"])]
    yours, theirs = says("your"), says("their")
    if not by["your"] and not by["their"]:
        out.append(("by No Mark", {("by", "your", ()), ("by", "their", ())}, COST["none"], "by"))
    for side, ways in (("your", yours), ("their", theirs)):
        other = by[flip(side)]
        for text, claims, cost in ways:
            out.append((f"by {text}", claims, cost, "by"))
            if by[side] and not other and has[flip(side)] and " of " not in text:
                out.append((f"by {text} Alone", claims | {("by", flip(side), ())}, cost + 1, "by"))
    if by["your"] and by["their"]:
        for (t1, f1, c1), (t2, f2, c2) in itertools.product(yours, theirs):
            if " of " in t1 and " of " in t2:
                continue  # "by Two of Yours and One of Theirs" says too little to be worth its length
            if t1.startswith("Your") and t2.startswith("Their") and by["your"] == by["their"] and len(
                    set(by["your"])) == 1:
                text = f"{t1} and Theirs"  # "by Your Edge and Theirs", but never "by Your Corner and Edge and Theirs"
            else:
                text = f"{t1} and {t2}"
            out.append((f"by {text}", f1 | f2, c1 + c2, "by"))
    out.extend((f"Across From {OWNS[fact[1]]}", {fact}, COST["across"], "across")
               for fact in sorted(f for f in facts if f[0] == "across"))
    if m.kind == "corner":
        alongs = {side: next(f[2] for f in facts if f[:2] == ("along", side)) for side in OWNER}
        if alongs["your"] == alongs["their"] == 1:
            out.append(("Along From Your Corner and Theirs", {("along", "your", 1), ("along", "their", 1)},
                        COST["along"], "along"))
        for side, count in alongs.items():
            if count:
                whose = OWNS[side] if count == 1 else f"{OWNER[side]} Two Corners"
                out.append((f"Along From {whose}", {("along", side, count)}, COST["along"], "along"))
    away = {f[1]: f for f in facts if f[0] == "away"}
    if len(away) == 2:
        mine, theirs = away["your"][2], away["their"][2]
        whose = "Theirs" if mine == theirs and len(set(mine)) == 1 else f"Their {kinds(theirs)}"
        out.append((f"Away From Your {kinds(mine)} and {whose}", {away["your"], away["their"]}, COST["away"], "away"))
    for side, fact in sorted(away.items()):
        out.append((f"Away From {OWNER[side]} {kinds(fact[2])}", {fact}, COST["away"], "away"))
    for fact in sorted(f for f in facts if f[0] == "nest-by"):
        side, kind, other = fact[1:4]
        whose = f"{OWNER[other]} {CELL[fact[4]]}" if len(fact) > 4 else OWNS[other]
        out.append((f"by {OWNER[side]} {CELL[kind]} Beside {whose}", {fact}, COST["nest-by"], "nest-by"))
    for fact in sorted(f for f in facts if f[0] == "nest-across"):
        _, side, kind, other, far = fact
        out.append((f"by {OWNER[side]} {CELL[kind]} Across From {OWNER[other]} {CELL[far]}", {fact},
                    COST["nest-by"], "nest-across"))
    for fact in sorted(f for f in facts if f[0] in ("nest-away", "nest-away-other")):
        name, side, kind, other = fact[:4]
        whose = f"{OWNER[side]} Other {CELL[kind]}" if name == "nest-away-other" else f"{OWNER[side]} {CELL[kind]}"
        near = f"{OWNER[other]} {CELL[fact[4]]}" if len(fact) > 4 else OWNS[other]
        out.append((f"Away From {whose} by {near}", {fact}, COST["nest-away"], "nest-away"))
    out.extend((f"Against Their {kinds(fact[1])}", {fact}, COST["against"], "against")
               for fact in sorted(f for f in facts if f[0] == "against"))
    if m.n > 1:  # the game's first mark has a title of its own: "Start in the Centre!"
        out.append((f"With Your {ORDINAL[m.marks]} Mark", {("mark", m.marks)}, COST["mark"], "mark"))
    return [(text, frozenset(f), cost, family) for text, f, cost, family in out]


def holds(m: Move, claims: frozenset) -> bool:
    """Whether every fact a title claims is true of the move."""
    return claims <= m.facts


# --- the leads -----------------------------------------------------------------------------------------------------
def lead(form: str, m: Move, sure: bool) -> tuple[str, frozenset]:
    """A title's opening words for the move, and the facts they claim. `sure` gives the cell "the": its title is true
    of it and of no other cell on its board; otherwise it is "a corner" or "an edge"."""
    article = "the" if m.kind == "centre" or sure else "an" if m.kind == "edge" else "a"
    cell = f"{article} {CELL[m.kind]}"
    where = "on" if m.kind == "edge" else "in"
    plain = frozenset({("cell", m.kind)})
    if form == "start":
        return f"Start {where} {cell}", plain | {("start",)}
    if form in ("take", "mark"):
        return f"{form.title()} {cell}", plain
    if form == "count":
        if m.kind == "centre":
            return f"Take {cell}", plain
        return f"Take Your {ORDINAL[m.count]} {CELL[m.kind]}", plain | {("count", m.count)}
    return f"{form.title()} Your {ORDINAL[m.marks]} Mark {where} {cell}", plain | {("mark", m.marks)}


def room(m: Move, twin: bool) -> int:
    """The longest title the move can have, its "!" included, leaving room for a twin's place."""
    return LONGEST - (len(", ") + ROOM[m.kind] if twin else 0)


def title(words: str, phrases: tuple[str, ...]) -> str:
    """A title from its lead and its details: `Take the Corner by Their Edge, Along From Yours!`."""
    return " ".join([words, *phrases[:1]]) + "".join(f", {text}" for text in phrases[1:]) + "!"


def options(m: Move, others: list[Move], twin: bool, safe: int | None = None) -> list[tuple]:
    """The titles the move can have, cheapest first, each as (cost, details, the facts it claims, whether it is true
    of the move's cell alone): at most three details, of different kinds, in a fixed order, that fit. Without `safe`,
    a title must be true of the move's cell and of no other cell on its board (`others`); with it, a title may also be
    true of the cells `safe` marks, whose own titles will be true of them alone, and costs more. A title's cost is its
    length, and a little more for the plainest words' rivals."""
    if m.n == 1:  # nothing else on the board: the move starts the game
        start = frozenset({("cell", m.kind), ("start",)})
        return [(len(title(lead("start", m, not twin)[0], ())), (), start, True)]
    found = sorted(details(m), key=lambda d: (FAMILIES.index(d[3]), d[0]))
    full = (1 << len(others)) - 1
    plain = frozenset({("cell", m.kind)})
    kind = sum(1 << j for j, o in enumerate(others) if o.kind != m.kind)  # the cells the kind alone rules out
    rules = [sum(1 << j for j, o in enumerate(others) if not holds(o, facts)) for _, facts, _, _ in found]
    words = lead("take", m, not twin and safe is None)[0]
    best: dict[frozenset, tuple] = {}
    for size in range(4):
        for picked in itertools.combinations(range(len(found)), size):
            families = [found[i][3] for i in picked]
            if len(set(families)) < size or {"by", "nest-by"} <= set(families) or {"away", "nest-away"} <= set(
                    families) or {"by", "nest-across"} <= set(families):
                continue
            ruled = kind
            for i in picked:
                ruled |= rules[i]
            alone = ruled == full
            if (not alone and (safe is None or ruled | safe != full)) or not named_first(picked, found):
                continue
            phrases = tuple(found[i][0] for i in picked)
            if sum(phrase.count("Mark") for phrase in phrases) > 1:
                continue  # never "by No Mark, With Your Second Mark"
            text = title(words, phrases)
            if len(text) > room(m, twin):
                continue
            claims = plain.union(*(found[i][1] for i in picked))
            cost = len(text) + sum(found[i][2] for i in picked) + (0 if alone else COST["shared"])
            if claims not in best or (cost, phrases) < best[claims][:2]:
                best[claims] = (cost, phrases, claims, alone)
    return sorted(best.values(), key=lambda o: (o[0], o[1]))


def named_first(picked: tuple[int, ...], found: list) -> bool:
    """Whether a title that says "their other edge" first names the edge of theirs that touches the cell."""
    claims = set().union(*(found[i][1] for i in picked)) if picked else set()
    return all(any(f[0] == "by" and f[1] == fact[1] and fact[2] in f[2] for f in claims)
               for fact in claims if fact[0] == "nest-away-other")


STAGE = collections.Counter(9 - board.count(".") for board in BOARDS)  # the boards with each number of marks down


def early(k: str) -> int:
    """How much a move's title length weighs: a game passes one board of each stage, so a board comes up as often as
    its stage has few boards, and the boards players meet most keep the shortest titles."""
    return round(100 / math.sqrt(STAGE[8 - k.count(".")]))


def assign(cands: dict[str, list]) -> dict[str, int]:
    """Each move's title, as an index into its options, so that no two moves claim the same facts and the titles'
    total cost, each weighed by how early its move comes, is the least it can be: each move in turn takes the
    cheapest path of moves that frees a title for it (an exact assignment by shortest augmenting paths, with a
    price on each set of facts)."""
    keys = sorted(cands)
    ids: dict[frozenset, int] = {}
    edges = [[(ids.setdefault(o[2], len(ids)), o[0] * early(k), i) for i, o in enumerate(cands[k][:CHOICES])]
             for k in keys]
    price, owner, match = [0] * len(ids), [-1] * len(ids), [-1] * len(keys)
    cost = [{o: c for o, c, _ in row} for row in edges]
    for s, row in enumerate(edges):
        least = min(c - price[o] for o, c, _ in row)
        dist = {o: c - price[o] - least for o, c, _ in row}
        before = {o: s for o, _, _ in row}
        heap = sorted((d, o) for o, d in dist.items())
        scanned, done, end = set(), [], None
        while heap:
            d, o = heapq.heappop(heap)
            if o in scanned or d > dist[o]:
                continue
            scanned.add(o)
            if owner[o] < 0:
                end = o
                break
            done.append(o)
            holder = owner[o]
            tight = cost[holder][o] - price[o]
            for o2, c2, _ in edges[holder]:
                step = d + c2 - price[o2] - tight
                if o2 not in scanned and step < dist.get(o2, step + 1):
                    dist[o2], before[o2] = step, holder
                    heapq.heappush(heap, (step, o2))
        if end is None:
            raise ValueError(f"no title is left for {keys[s]}")
        for o in done:
            price[o] -= dist[end] - dist[o]
        o = end
        while True:  # each move along the path takes the next one's title, the first a free one
            holder = before[o]
            match[holder], owner[o], o = o, holder, match[holder]
            if holder == s:
                break
    return {k: next(i for o, _, i in edges[n] if o == match[n]) for n, k in enumerate(keys)}


def choose() -> dict[str, tuple[str, frozenset]]:
    """Every move's title and the facts it claims: the cheapest details, true of its cell alone on its board, that no
    other move's title claims, opened by the lead the board's hash picks among those that fit every title on it."""
    boards, cands = {}, {}
    for board in BOARDS:
        keys = {i: key(board, i) for i in range(9) if board[i] == "."}
        twins = collections.Counter(keys.values())
        moves = {k: Move(k) for k in sorted(set(keys.values()))}
        boards[board] = (moves, twins)
        for k, m in moves.items():
            cands[k] = options(m, [o for o in moves.values() if o is not m], twins[k] > 1)
        few = {k for k in moves if len(cands[k]) < FEW}  # moves that may have to share a little of their truth
        for k in sorted(few):
            others = [o for o in moves.values() if o.key != k]
            safe = sum(1 << j for j, o in enumerate(others) if o.key not in few)
            cands[k] = sorted(cands[k] + options(moves[k], others, twins[k] > 1, safe), key=lambda o: (o[0], o[1]))
            if not cands[k]:
                raise ValueError(f"no title tells {k} apart from the other moves on its board")
    got = assign(cands)
    cores = {cands[k][got[k]][2] for k in cands}  # what each title says without its lead: all different
    out, claimed = {}, set()
    for board, (moves, twins) in boards.items():
        said = {k: cands[k][got[k]] for k in moves}
        spoken = " ".join(text for k in moves for text in said[k][1])
        fits = []
        for form in ("start",) if board == EMPTY else LEADS:
            opened = {k: lead(form, m, twins[k] == 1 and said[k][3]) for k, m in moves.items()}
            texts = [title(opened[k][0], said[k][1]) for k in moves]
            if "Mark" in spoken and any("Mark" in words for words, _ in opened.values()):
                continue  # never "Mark the Corner by No Mark", nor "Lay Your Third Mark ..., With Your Third Mark"
            if any(len(text) > room(m, twins[k] > 1) for text, (k, m) in zip(texts, moves.items(), strict=True)):
                continue
            if form not in ("take", "mark", "start") and max(map(len, texts)) > SHORT:
                continue  # a lead that counts only where it keeps every title short
            if any("Your First" in words and "First Mark" in text
                   for (words, _), text in zip(opened.values(), texts, strict=True)):
                continue  # "Take Your First Corner ..., With Your First Mark" says one thing twice
            fuller = [opened[k][1] | said[k][2] for k in moves]
            if any(f != said[k][2] and (f in cores or f in claimed) for f, k in zip(fuller, moves, strict=True)):
                continue  # a lead's count never makes a title say what another title says
            fits.append(form)
        form = fits[zlib.crc32(board.encode()) % len(fits)]
        for k, m in moves.items():
            words, claims = lead(form, m, twins[k] == 1 and said[k][3])
            out[k] = (title(words, said[k][1]), claims | said[k][2])
            claimed.add(claims | said[k][2])
    return out


# --- the table -------------------------------------------------------------------------------------------------------
def said(fact: tuple) -> str:
    """A fact as the table writes it: `by:their=centre+edge`, `across:your`, `along:their=1`, `mark:3`."""
    name, rest = fact[0], fact[1:]
    if name in ("by", "away"):
        return f"{name}:{rest[0]}={'+'.join(rest[1]) or 'none'}"
    if name in ("along", "by-count"):
        return f"{name}:{rest[0]}={rest[1]}"
    if name == "nest-by":
        whose = rest[2] + (f"={rest[3]}" if len(rest) > 3 else "")
        return f"nest-by:{rest[0]}={rest[1]}:beside={whose}"
    if name in ("nest-away", "nest-away-other"):
        whose = rest[2] + (f"={rest[3]}" if len(rest) > 3 else "")
        return f"{name}:{rest[0]}={rest[1]}:by={whose}"
    if name == "against":
        return f"against:their={'+'.join(rest[0])}"
    if name == "nest-across":
        return f"nest-across:{rest[0]}={rest[1]}:facing={rest[2]}={rest[3]}"
    if name == "start":
        return "start"
    return f"{name}:{rest[0]}"


def table() -> dict:
    """Every move, by its key, with its title and the facts its title claims."""
    got = choose()
    order = sorted(got, key=lambda k: (9 - k.count("."), k))
    return {k: {"title": got[k][0], "facts": sorted(said(f) for f in got[k][1])} for k in order}


def render(moves: dict) -> str:
    """The table as its file keeps it: one move to a line, by the marks down and then the board."""
    lines = [json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False) for k, v in moves.items()]
    return "{\n" + ",\n".join(lines) + "\n}\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the table is not what this script makes")
    args = parser.parse_args(argv)
    text = render(table())
    if args.check:
        if not TABLE.exists() or TABLE.read_text(encoding="utf-8") != text:
            print(f"{TABLE.name} is not what {Path(__file__).name} makes: run it to rebuild", file=sys.stderr)
            return 1
        return 0
    TABLE.write_text(text, encoding="utf-8")
    print(f"wrote {len(json.loads(text))} titles to {TABLE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
