#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Build tictactoe_names.json: a title for every Tic-Tac-Toe move, from where its mark goes and nothing else.

  python3 .github/scripts/tictactoe_names_table.py          write the table
  python3 .github/scripts/tictactoe_names_table.py --check  fail if the table is not what this script makes

A move is read from the mover's side, the mark that moved first written X, and
taken up to the board's eight turns and mirrors: 2,096 moves from 627 boards,
making the 764 positions the game can reach once a mark goes down. A title is
built in three steps:

1. The facts. Only what the board plainly shows about the cell the mark
   takes: its kind (the centre, a corner or an edge); the marks touching it,
   by a side or at a corner, each side's named by kind or counted; the mark
   across the centre from it; for a corner, the two corners a cell along from
   it; the marks that do none of these; the mover's count of marks, and of
   cells of this kind; and, for the few boards nothing else will do, a mark
   that touches the cell and sits beside one of the other side's, or a distant
   one that touches one of theirs. Nothing about a row, a column or a diagonal
   and what it holds, nothing about who wins, and nothing a move ahead.
2. The details. Each move takes the cheapest words that fit and are true of
   its own cell and of no other on its board (its mirror twins aside: they
   share a title, and the listing adds their place), and says "the corner" of
   it where that fits. On a few boards a cell can be told apart only by words
   too long to fit: it takes true words no other title there claims, says "a
   corner", and every cell they are also true of has a title true of that cell
   alone, so the two still read apart.
3. The lead. Every move on one board opens alike, by a hash of the board among
   the leads that fit all its titles: "Take the Corner", "Mark an Edge",
   "Take Your Second Corner", "Lay Your Third Mark in the Corner".

The table keeps each move's title and the facts it claims, so a title can be
read against its board. Stdlib only, with tictactoe_rules.py and
tictactoe_names.py beside it.
"""
from __future__ import annotations

import argparse
import collections
import functools
import itertools
import json
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
LONGEST = 48  # the longest title tannergolden/markdown takes
ROOM = {"corner": len("Upper Right"), "edge": len("Bottom")}  # the longest place a twin of each kind can carry

# --- the words titles are made of ----------------------------------------------------------------------------------
CELL = {"centre": "Centre", "corner": "Corner", "edge": "Edge"}
ORDINAL = ("", "First", "Second", "Third", "Fourth", "Fifth")
NUMBER = ("No", "One", "Two", "Three", "Four")
OWNER = {"your": "Your", "their": "Their"}
OWNS = {"your": "Yours", "their": "Theirs"}
# The leads a board's titles open with. A board's hash picks one among those that fit every title on it ("take" and
# "mark" always do), so every move on one board opens alike.
LEADS = ("take", "mark", "lay", "count", "set", "plant", "put", "send")
# What each kind of detail costs a title: the marks touching the cell come first, the plainest words cheapest.
COST = {"by": 0.0, "count": 0.6, "none": 2.4, "across": 1.0, "along": 1.2, "away": 2.0, "nest-by": 4.0}


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
        if self.kind != "centre":
            facing = self.owner(8 - new)
            if facing:
                out.add(("across", facing))
        return frozenset(out)


def details(m: Move) -> list[tuple[str, frozenset, float, str]]:
    """Every detail a title can give the move, as (words, facts, cost, family): one phrase each."""
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
            out.append((f"by {text}", claims, cost + 0.3 * bool(other), "by"))
            if by[side] and not other and has[flip(side)]:
                out.append((f"by {text} Alone", claims | {("by", flip(side), ())}, cost + 0.1, "by"))
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
    for fact in sorted(f for f in facts if f[0] == "across"):
        out.append((f"Across From {OWNS[fact[1]]}", {fact}, COST["across"], "across"))
    if m.kind == "corner":
        alongs = {side: next(f[2] for f in facts if f[:2] == ("along", side)) for side in OWNER}
        if alongs["your"] == alongs["their"] == 1:
            out.append(("Along From Your Corner and Theirs", {("along", "your", 1), ("along", "their", 1)},
                        COST["along"], "along"))
        for side, count in alongs.items():
            if count:
                whose = OWNS[side] if count == 1 else f"{OWNER[side]} Two Corners"
                out.append((f"Along From {whose}", {("along", side, count)}, COST["along"] + 0.2, "along"))
    away = {f[1]: f for f in facts if f[0] == "away"}
    if len(away) == 2:
        mine, theirs = away["your"][2], away["their"][2]
        whose = "Theirs" if mine == theirs and len(set(mine)) == 1 else f"Their {kinds(theirs)}"
        out.append((f"Away From Your {kinds(mine)} and {whose}", {away["your"], away["their"]}, COST["away"], "away"))
    for side, fact in sorted(away.items()):
        out.append((f"Away From {OWNER[side]} {kinds(fact[2])}", {fact}, COST["away"] + 0.2, "away"))
    for fact in sorted(f for f in facts if f[0] == "nest-by"):
        side, kind, other = fact[1:4]
        whose = f"{OWNER[other]} {CELL[fact[4]]}" if len(fact) > 4 else OWNS[other]
        out.append((f"by {OWNER[side]} {CELL[kind]} Beside {whose}", {fact}, COST["nest-by"] + 0.1 * (len(fact) > 4),
                    "nest-by"))
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
    if form in ("take", "mark"):
        return f"{form.title()} {cell}", plain
    if form == "count":
        if m.kind == "centre":
            return f"Take {cell}", plain
        return f"Take Your {ORDINAL[m.count]} {CELL[m.kind]}", plain | {("count", m.count)}
    if form == "send":
        return f"Send Your {ORDINAL[m.marks]} Mark to {cell}", plain | {("mark", m.marks)}
    return f"{form.title()} Your {ORDINAL[m.marks]} Mark {where} {cell}", plain | {("mark", m.marks)}


def room(m: Move, twin: bool) -> int:
    """The longest title the move can have, its "!" included, leaving room for a twin's place."""
    return LONGEST - (len(", ") + ROOM[m.kind] if twin else 0)


def options(m: Move) -> list[tuple[tuple[str, ...], frozenset, float]]:
    """Every set of details a title can give the move: none, one, or two of different kinds, cheapest first."""
    found = details(m)
    out = [((), frozenset(), 0.0 if m.n == 1 else 2.0 if m.kind == "centre" else 5.0)]
    out += [((text,), facts, cost) for text, facts, cost, _ in found]
    for (t1, f1, c1, k1), (t2, f2, c2, k2) in itertools.combinations(found, 2):
        if k1 == k2 or {k1, k2} == {"by", "nest-by"} or t1[:4] == t2[:4] == "Away":
            continue
        out.append(((t1, t2), f1 | f2, c1 + c2 + 2.0))
    return sorted(out, key=lambda o: (o[2] + sum(map(len, o[0])) / 100, o[0]))


def title(words: str, phrases: tuple[str, ...]) -> str:
    """A title from its lead and its details: `Take the Corner by Their Edge, Along From Yours!`."""
    return (" ".join([words] + list(phrases[:1])) + "".join(f", {text}" for text in phrases[1:])) + "!"


def pick(moves: dict[str, Move], twins: collections.Counter) -> dict[str, tuple]:
    """Each move's details on one board, the facts its title claims, whether the title is true of its own cell alone,
    and whether it says "the" of it. A move takes the cheapest details that fit and are true of its cell and of no
    other cell on the board (its twins aside), saying "the corner" where that fits and "a corner" where only that does.
    A move no such details fit takes the cheapest true ones that claim what no other move's title claims, so long as
    every cell they are true of has a title that is true of that cell alone: the two read apart all the same."""
    picked = {}
    for k, m in moves.items():
        for phrases, facts, _ in options(m):
            claims = facts | {("cell", m.kind)}
            if any(holds(o, claims) for o in moves.values() if o is not m):
                continue
            sure = [True, False] if twins[k] == 1 and m.kind != "centre" else [False]
            fit = [s for s in sure if len(title(lead("take", m, s)[0], phrases)) <= room(m, twins[k] > 1)]
            if fit:
                picked[k] = (phrases, claims, True, fit[0] or m.kind == "centre")
                break
    for k, m in moves.items():
        if k in picked:
            continue
        for phrases, facts, _ in options(m):
            claims = facts | {("cell", m.kind)}
            if len(title(lead("take", m, False)[0], phrases)) > room(m, twins[k] > 1):
                continue
            if any(claims == p[1] for p in picked.values()):
                continue
            shared = [o for o in moves.values() if o is not m and holds(o, claims)]
            if all(o.key in picked and picked[o.key][2] for o in shared):
                picked[k] = (phrases, claims, False, m.kind == "centre")
                break
        else:
            raise ValueError(f"no title tells {k} apart from the other moves on its board")
    return picked


def choose() -> dict[str, tuple[str, frozenset]]:
    """Every move's title and the facts it claims, board by board: the details that tell it apart, opened by the lead
    the board's hash picks among those that fit every title on the board."""
    out = {}
    for board in BOARDS:
        keys = {i: key(board, i) for i in range(9) if board[i] == "."}
        twins = collections.Counter(keys.values())
        moves = {k: Move(k) for k in sorted(set(keys.values()))}
        picked = pick(moves, twins)
        spoken = " ".join(text for k in moves for text in picked[k][0])
        fits = []
        for form in LEADS:
            opened = {k: lead(form, m, picked[k][3]) for k, m in moves.items()}
            if "Mark" in spoken and any("Mark" in words for words, _ in opened.values()):
                continue  # never "Mark the Corner by No Mark"
            if all(len(title(opened[k][0], picked[k][0])) <= room(m, twins[k] > 1) for k, m in moves.items()):
                fits.append(form)
        form = fits[zlib.crc32(board.encode()) % len(fits)]
        opened = {k: lead(form, m, picked[k][3]) for k, m in moves.items()}
        for k in moves:
            words, claims = opened[k]
            out[k] = (title(words, picked[k][0]), claims | picked[k][1])
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
        other = rest[2] + (f"={rest[3]}" if len(rest) > 3 else "")
        return f"nest-by:{rest[0]}={rest[1]}:beside={other}"
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
