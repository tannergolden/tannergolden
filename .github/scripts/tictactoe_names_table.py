#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Build tictactoe_names.json: one title for each of the 764 positions a Tic-Tac-Toe move can make.

  python3 .github/scripts/tictactoe_names_table.py          write the table
  python3 .github/scripts/tictactoe_names_table.py --check  fail if the table is not what this script makes

A move is named for the position it makes, taken up to the board's eight
turns and mirrors and read from the mover's side: the mark that moved first is
written X, so a game O opened reads as one X opened. Of the 765 positions the
game can reach that way, 764 are made by a move, the empty board being the
other. A title is built in five steps:

1. Perfect play. The whole game is solved: what each position is worth to the
   side that just moved (a win, a draw or a loss, and how soon with best
   play), and what the move was worth from every board that can make it.
2. The facts. What is true of the position from the mover's side: the line it
   completes, the lines it threatens, the lines of theirs it guards, the
   threats they hold, where its marks stand against theirs ("Box In Their
   Corner" is two of your edges around a corner of theirs), how far into the
   game it is, and what perfect play makes of it. A title claims only facts of
   the position, so it holds however the move reached it; a fact about the move
   itself (the slip, the only hold) is claimed only when every board that makes
   the position agrees on it.
3. The candidates. Every title the phrasebook below can truly say of the
   position: a lead in the game's own words, a detail, the ending that carries
   perfect play's judgement, and how far into the game it is. A detail must
   tell something its lead does not (some other position with that lead lacks
   it), and a title must leave room for a mirror twin's place where the
   position can have one (48 characters in all).
4. The choice. Each position takes the cheapest candidate that no other
   position's title says, in its words or in the facts it claims (the same
   facts in another order would be one name twice): the most telling, shortest
   title, unless another position needs it more, the early positions choosing
   most carefully. Two moves on one board never read as one title and the same
   title with more said that is true of both.
5. The table: each position's title, emoji, judgement and the facts its title
   claims, so every title can be read against its board and audited.

Stdlib only, with tictactoe_rules.py and tictactoe_names.py beside it.
"""
from __future__ import annotations

import argparse
import collections
import functools
import heapq
import itertools
import json
import sys
from pathlib import Path

import tictactoe_rules as R
from tictactoe_names import TABLE, canonical, forms

# --- the board as a string: nine marks in the order the board is read, a3 b3 c3 a2 b2 c2 a1 b1 c1 ---------------
AT = {cell: i for i, cell in enumerate(R.READING)}
LINES = tuple(tuple(AT[cell] for cell in line) for line in R.LINES)
KIND = tuple("centre" if cell == R.CENTRE else "corner" if cell in R.CORNERS else "edge" for cell in R.READING)
ACROSS = {i: 8 - i for i in range(9) if i != 4}  # the cell across the centre from each other cell
NEAR = {0: (1, 3), 2: (1, 5), 6: (3, 7), 8: (5, 7)}  # each corner's two edges
EMPTY = "." * 9
LONGEST = 48  # the longest title tannergolden/markdown takes
PLACES = {"a3": "Upper Left", "b3": "Top", "c3": "Upper Right", "a2": "Left", "c2": "Right", "a1": "Lower Left",
          "b1": "Bottom", "c1": "Lower Right"}

# --- the words titles are made of --------------------------------------------------------------------------------
NUM = ("No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine")
WORD = {"diagonal": "Diagonal", "middle": "Middle", "side": "Side"}  # a line: corner to corner through the centre,
# edge to edge through it, or along the side of the board
CELL = {"centre": "Centre", "corner": "Corner", "edge": "Edge"}
BOTH = {"Diagonal": "Both Diagonals", "Middle": "Both Middles", "Side": "Two Sides", "Edge": "Two Edges",
        "Centre": "the Centre Twice"}
ORDER = ("Centre", "Diagonal", "Middle", "Side", "Edge")
EMOJI = {"win": "🏆", "draw": "🤝", "fork": "⚡", "threat": "🎯", "centre": "⭐", "corner": "📐", "edge": "📏",
         "blunder": "⚠️"}


def other(mark: str) -> str:
    return "O" if mark == "X" else "X"


def turn(board: str) -> str:
    """Whose mark goes down next, X having moved first."""
    return "X" if board.count("X") == board.count("O") else "O"


def won(board: str) -> str | None:
    for a, b, c in LINES:
        if board[a] != "." and board[a] == board[b] == board[c]:
            return board[a]
    return None


def put(board: str, i: int, mark: str) -> str:
    return board[:i] + mark + board[i + 1:]


@functools.cache
def solve(board: str) -> tuple[int, int]:
    """Perfect play from a board, X first: 1 when X wins, -1 when O does and 0 for a draw, and how many marks the
    game has left with best play (the winner hurrying, the loser holding on as long as it can)."""
    if won(board):
        return (1 if won(board) == "X" else -1), 0
    if "." not in board:
        return 0, 0
    mark = turn(board)
    outcomes = [solve(put(board, i, mark)) for i in range(9) if board[i] == "."]
    best = max(v for v, _ in outcomes) if mark == "X" else min(v for v, _ in outcomes)
    lengths = [n + 1 for v, n in outcomes if v == best]
    hurry = (best == 1) == (mark == "X") and best != 0
    return best, (min(lengths) if hurry else max(lengths))


def worth(board: str, mark: str) -> int:
    """What perfect play makes of the board for `mark`: 1 a win, 0 a draw, -1 a loss."""
    value = solve(board)[0]
    return value if mark == "X" else -value


def reachable() -> set[str]:
    seen, todo = set(), [EMPTY]
    while todo:
        board = todo.pop()
        if board in seen:
            continue
        seen.add(board)
        if not won(board) and "." in board:
            todo += [put(board, i, turn(board)) for i in range(9) if board[i] == "."]
    return seen


SEEN = reachable()
SHAPES = {canonical(board) for board in SEEN}
POSITIONS = sorted((s for s in SHAPES if s != EMPTY), key=lambda s: (9 - s.count("."), s))


def threats(board: str, mark: str) -> list[int]:
    """The open cells where `mark` would complete three in a row."""
    return [i for i in range(9) if board[i] == "." and any(
        i in line and all(board[j] == mark for j in line if j != i) for line in LINES)]


def kind_of_line(line: tuple[int, ...]) -> str:
    return ("diagonal" if any(KIND[i] == "corner" for i in line) else "middle") if 4 in line else "side"


def threat_word(board: str, cell: int, mark: str) -> str:
    """A threat named by where it wins: the Centre, or the line it completes on a corner, or an Edge between corners
    along a side."""
    if KIND[cell] == "centre":
        return "Centre"
    lines = [kind_of_line(line) for line in LINES if cell in line and all(board[j] == mark for j in line if j != cell)]
    if lines[0] == "side":
        return "Side" if KIND[cell] == "corner" else "Edge"
    return WORD[lines[0]]


def line_word(board: str, cell: int, mark: str) -> str:
    """A threat named by its line alone, or Fork when the cell would complete two kinds of line."""
    lines = {kind_of_line(line) for line in LINES if cell in line and all(board[j] == mark for j in line if j != cell)}
    return WORD[lines.pop()] if len(lines) == 1 else "Fork"


def two(words: list[str]) -> str:
    a, b = sorted(words, key=ORDER.index)[:2]
    return BOTH[a] if a == b else f"the {a} and the {b}"


def line_of(a: int, b: int) -> tuple[int, ...] | None:
    return next((line for line in LINES if a in line and b in line), None)


def formation(cells: list[int]) -> str | None:
    """Two or three marks as one shape, in the game's words: Opposite Corners, a Corner and Its Edge, the Centre and
    Two Edges. Four or more have no one shape."""
    cells = sorted(cells)
    if len(cells) == 2:
        a, b = cells
        if 4 in cells:
            kind = KIND[b if a == 4 else a]
            return f"the Centre and {'a' if kind == 'corner' else 'an'} {CELL[kind]}"
        if KIND[a] == KIND[b]:
            return f"{'Opposite' if ACROSS[a] == b else 'Adjacent'} {CELL[KIND[a]]}s"
        corner, edge = (a, b) if KIND[a] == "corner" else (b, a)
        return "a Corner and Its Edge" if edge in NEAR[corner] else "a Corner and a Far Edge"
    if len(cells) == 3:
        count = collections.Counter(KIND[i] for i in cells)
        parts = ["the Centre"] if count["centre"] else []
        parts += [(("a " if k == "corner" else "an ") + CELL[k]) if count[k] == 1 else f"{NUM[count[k]]} {CELL[k]}s"
                  for k in ("corner", "edge") if count[k]]
        return " and ".join(parts) if len(parts) > 1 else None
    return None


# --- the facts -----------------------------------------------------------------------------------------------------
class Facts:
    """What is true of a position a move makes, read from the side that made it (the mover)."""

    def __init__(self, board: str):
        self.board = board
        self.n = 9 - board.count(".")
        self.mover = "X" if self.n % 2 else "O"
        self.them = other(self.mover)
        self.mine = [i for i in range(9) if board[i] == self.mover]
        self.theirs = [i for i in range(9) if board[i] == self.them]
        self.won = sorted(kind_of_line(line) for line in LINES if all(board[i] == self.mover for i in line))
        self.full = "." not in board and not self.won
        self.worth = worth(board, self.mover)
        self.length = solve(board)[1]
        self.threats = threats(board, self.mover)  # where the mover could win next
        self.menace = threats(board, self.them)  # where they could win next
        lines = [(line, sum(board[i] == self.mover for i in line), sum(board[i] == self.them for i in line))
                 for line in LINES]
        self.guards = sorted(WORD[kind_of_line(line)] for line, m, t in lines if t == 2 and m == 1)
        self.live = sum(1 for _, _, t in lines if t == 0)  # lines the mover can still complete
        self.centre = "you" if board[4] == self.mover else "them" if board[4] == self.them else "open"
        self.boards = self.made_from()
        self.before = sorted({worth_before for _, _, worth_before, _ in self.boards})
        self.only = bool(self.boards) and all(only for _, _, _, only in self.boards)
        self.forks = self.their_forks()
        self.counter = self.block_counter()
        self.category = self.categorise()

    def made_from(self) -> list[tuple[str, int, int, bool]]:
        """Every board, up to its turns and mirrors, from which a move makes this position: the board, the cell, what
        the board was worth to the mover, and whether this was the only position (up to mirrors) that kept it."""
        out = {}
        for i in self.mine:
            board = put(self.board, i, ".")
            if won(board) or canonical(board) not in SHAPES:
                continue
            tagged = put(board, i, "*")
            out.setdefault(max(forms(tagged)), (board, i))
        found = []
        for board, i in out.values():
            results = {}
            for j in range(9):
                if board[j] == ".":
                    after = put(board, j, self.mover)
                    results.setdefault(canonical(after), worth(after, self.mover))
            best = max(results.values())
            keeps = [shape for shape, value in results.items() if value == best]
            found.append((board, i, worth(board, self.mover), self.worth == best and len(keeps) == 1))
        return found

    def their_forks(self) -> list[int]:
        """Cells where they could make two threats at once with their next mark."""
        board, out = self.board, []
        for i in range(9):
            if board[i] == ".":
                after = put(board, i, self.them)
                if not won(after) and len(threats(after, self.them)) >= 2:
                    out.append(i)
        return out

    def block_counter(self) -> list[int]:
        """When the mover threatens one cell: the threats their forced block there makes of its own."""
        if len(self.threats) != 1 or self.won or self.full:
            return []
        return threats(put(self.board, self.threats[0], self.them), self.them)

    def categorise(self) -> str:
        if self.won:
            return "win"
        if self.full:
            return "full"
        if self.worth == -1:
            return "loss-now" if self.menace else "loss-fork" if self.length == 3 else "loss-trap"
        if self.worth == 1:
            return "win-fork" if len(self.threats) >= 2 else "win-threat" if self.threats else "win-quiet"
        return "draw-threat" if self.threats else "draw-quiet"

    def judge(self) -> str:
        """How a drawn position's title judges the move: the slip, the only hold, the hold, or neither when the boards
        that make it disagree."""
        if self.before == [1]:
            return "slip"
        if self.before == [0]:
            return "only" if self.only else "hold"
        return "draw"


# --- the phrasebook --------------------------------------------------------------------------------------------------
def states(f: Facts) -> dict:
    """The position's standing from the mover's side, each as {fact: (verb, detail, cost, joins)}: the verb leads a
    title ("Box In Their Corner"), the detail follows one ("Boxing In Their Corner"), and `joins` says whether the
    verb can take an ending that starts with "and" without reading as a list. A standing their own mark made (your
    line blocked, your corners split, your corner boxed in) has no verb: no move of yours makes it, so no order can
    say it, and it is only ever a detail ("With Your Corners Split")."""
    board = f.board
    out: dict = {}

    def add(fact, verb, detail, cost, joins=True):
        out.setdefault(fact, (verb, detail, cost, joins))
    mc = [i for i in f.mine if KIND[i] == "corner"]
    me = [i for i in f.mine if KIND[i] == "edge"]
    tc = [i for i in f.theirs if KIND[i] == "corner"]
    te = [i for i in f.theirs if KIND[i] == "edge"]
    if f.guards:
        g = f.guards
        if len(g) == 1:
            add(("guard", tuple(g)), f"Guard the {g[0]}", f"Guarding the {g[0]}", 1)
        elif len(g) == 2:
            said = BOTH[g[0]] if g[0] == g[1] else two(g)
            add(("guard", tuple(g)), f"Guard {said}", f"Guarding {said}", 1, g[0] == g[1])
        else:
            add(("guard", tuple(g)), f"Guard {NUM[len(g)]} Lines", f"Guarding {NUM[len(g)]} Lines", 1)
    for a, b in itertools.combinations(f.mine, 2):
        line = line_of(a, b)
        third = line and next(i for i in line if i not in (a, b))
        if not line or board[third] != f.them:
            continue
        if third == 4:
            add(("flank", KIND[a]), f"Flank Their Centre From the {CELL[KIND[a]]}s", "Flanking Their Centre", 1)
        elif KIND[a] == KIND[b] == "corner":
            add(("split",), None, "With Your Corners Split", 1.5)
        else:
            w = WORD[kind_of_line(line)]
            add(("blocked", w), None, f"With Your {w} Blocked", 1.5)
    for corner, edges in NEAR.items():
        if all(e in me for e in edges):
            if board[corner] == f.them:
                add(("box",), "Box In Their Corner", "Boxing In Their Corner", 1)
            elif board[corner] == ".":
                add(("ring",), "Surround an Open Corner", "Surrounding an Open Corner", 2)
            else:
                add(("wall",), "Wall In Your Own Corner", "Walling In Your Corner", 2.5)
        if corner in mc and all(e in te for e in edges):
            add(("boxed",), None, "With Your Corner Boxed In", 2)
    if any(ACROSS[i] in tc for i in mc):
        add(("face", "corner"), "Face Their Corner", "Facing Their Corner", 2)
    if any(ACROSS[i] in te for i in me):
        add(("face", "edge"), "Face Their Edge", "Facing Their Edge", 2)
    if any(e in NEAR[c] for e in me for c in tc):
        add(("crowd",), "Crowd Their Corner", "Crowding Their Corner", 3)
    if len(f.mine) >= 2 and not any(line_of(a, b) for a, b in itertools.combinations(f.mine, 2)):
        add(("scatter",), "Scatter Your Marks", "With Your Marks Scattered", 1.5)
    add(("centre", f.centre), {"you": "Keep the Centre", "open": "Leave the Centre Open",
                               "them": "Play Round Their Centre"}[f.centre],
        {"you": "Holding the Centre", "open": "With the Centre Open", "them": "Against Their Centre"}[f.centre], 2.5)
    shape = formation(f.mine)
    if shape:
        add(("shape", shape), f"Keep {shape}", f"With {shape}", 2.5, " and " not in shape)
    if len(mc) >= 2 and not shape:
        add(("corners", len(mc)), f"Keep {NUM[len(mc)]} Corners" if len(mc) < 4 else "Keep Every Corner",
            f"With {NUM[len(mc)]} Corners" if len(mc) < 4 else "With Every Corner", 3)
    if not mc and me:
        add(("corners", 0), "Stick to the Edges" if f.centre != "you" else "Stay Off the Corners", "With No Corner",
            2.5)
    if len(me) >= 2 and not shape:
        add(("edges", len(me)), f"Keep {NUM[len(me)]} Edges" if len(me) < 4 else "Keep Every Edge",
            f"With {NUM[len(me)]} Edges" if len(me) < 4 else "With Every Edge", 3)
    if not me and mc and f.n >= 3:
        add(("edges", 0), "Keep Off the Edges", "With No Edge", 3)
    if f.live == 0:
        add(("live", 0), "Run Out of Lines", "With No Line Left", 2)
    elif f.live == 1:
        add(("live", 1), "Keep One Line Alive", "With One Line Left", 3)
    return out


def their_shape(f: Facts) -> tuple | None:
    """Their marks as a winning title passes them, as (fact, detail, cost): "Past Their Opposite Edges", "Past Their
    Corner and Far Edge", "Past Their Centre and Two Edges". Marks of all three kinds make no one phrase."""
    count = collections.Counter(KIND[i] for i in f.theirs)
    if len(f.theirs) == 2:
        shape = formation(f.theirs)
        shape = {"the Centre and a Corner": "Centre and Corner", "the Centre and an Edge": "Centre and Edge",
                 "a Corner and Its Edge": "Corner and Its Edge", "a Corner and a Far Edge": "Corner and Far Edge"}.get(
            shape, shape)
        return ("their shape", shape), f"Past Their {shape}", 2
    parts = [(CELL[k] if count[k] == 1 else f"{NUM[count[k]]} {CELL[k]}s") for k in ("centre", "corner", "edge")
             if count[k]]
    if len(parts) > 2:
        return None
    return ("their marks", tuple(sorted(count.items()))), "Past Their " + " and ".join(parts), 2.5


def clashes(lead: str, detail: str) -> bool:
    """Whether a detail would seem to deny or muddle its lead: "Fork the Centre and the Edge With No Edge", or one
    line named twice for two lines ("Hand Them the Middle Guarding the Middle"), a cell's kind named twice for two
    cells ("Threaten the Edge Facing Their Edge"), or theirs said twice over ("Win Your Side Before Theirs Against
    Their Centre")."""
    return (any(f"No {word}" in detail and word in lead for word in ("Edge", "Corner", "Centre", "Line"))
            or any(word in detail and word in lead for word in ("Diagonal", "Middle", "Side"))
            or any(word in detail and word in lead for word in ("Edge", "Corner"))
            or (lead.endswith("Theirs") and "Their" in detail))


def candidates(f: Facts) -> list[tuple]:
    """Every true title of the position, as (text, facts, cost, lead text, lead facts), each set of facts said one
    way: a verb, a detail, the ending that carries the judgement, and how far into the game it is."""
    out: list = []
    st = states(f)
    timing = (("mark", f.n), f"{NUM[f.n]} Marks In", 4.5)
    details = [(fact, detail, cost + 1) for fact, (_, detail, cost, _) in st.items()]
    plain = [("", set(), 0)]

    def compose(verbs, ends, extras, pairs=False, timed=True, alone=True):
        for verb, verb_facts, verb_cost in verbs:
            for end, end_facts, end_cost in ends:
                if " and " in verb and end.startswith("and "):
                    continue
                lead_facts = frozenset(verb_facts) | frozenset(end_facts)
                lead = " ".join(x for x in (verb, end) if x)
                usable = [d for d in extras if d[0] not in lead_facts and not clashes(lead, d[1])]
                options = [((), "", 0)] * alone + [((k,), text, cost) for k, text, cost in usable]
                if pairs:
                    options += [((k1, k2), f"{t1} {t2}", c1 + c2 + 1)
                                for (k1, t1, c1), (k2, t2, c2) in itertools.combinations(usable, 2)]
                for facts, text, cost in options:
                    if verb.startswith("Let Them") and text and "Your" not in text and text != "With the Centre Open":
                        continue  # "Let Them Fork Guarding the Side" would seem to say who guards it
                    when_ok = timed and len(facts) < 2 and timing[0] not in lead_facts and not lead.endswith(
                        ("Another", "the Other", "Theirs"))  # no "Lose to Another Six Marks In"
                    for when in ((False, True) if when_ok else (False,)):
                        late = timing[2] + 2 * len(facts) if when else 0  # the time alone, or a last resort
                        out.append((" ".join(x for x in (verb, text, end, timing[1] if when else "") if x),
                                    lead_facts | set(facts) | ({timing[0]} if when else set()),
                                    verb_cost + end_cost + cost + late, lead, lead_facts))

    def verbs_for(end, cost=0.0):
        """The states that can lead a title with this ending, without saying one verb twice ("Let Them ... and Let
        Them Fork") or reading as a list ("Keep Two Corners and an Edge and Hold")."""
        follow = end.split()[1] if end.startswith("and ") else None
        return [(verb, {fact}, c + cost) for fact, (verb, _, c, joins) in st.items()
                if verb and joins and verb.split()[0] != follow]
    mine = [threat_word(f.board, i, f.mover) for i in f.threats]
    theirs = [threat_word(f.board, i, f.them) for i in f.menace]
    cat = f.category
    if cat in ("win", "full", "win-fork", "win-threat", "win-quiet"):
        passing = [(k, d, c) for k, (_, d, c, _) in st.items() if k[0] not in ("scatter", "wall", "live")
                   and not (k[0] == "shape" and cat == "win")]
        shape = their_shape(f)
        passing += [shape] if shape else []
        if cat == "win":
            if len(f.won) == 2:
                compose([(f"Win {two([WORD[x] for x in f.won])} at Once", {("won", tuple(f.won))}, 0)], plain, [],
                        timed=False)
                return out
            line = WORD[f.won[0]]
            if f.n == 9:
                compose([(f"Win the {line} on the Last Cell", {("won", line), ("mark", 9)}, 0),
                         ("Win on the Last Cell", {("won",), ("mark", 9)}, 1)], plain, passing, True, False)
                return out
            verbs = [(f"Win the {line}", {("won", line)}, 1.5 if f.menace or f.threats else 0)]
            if f.menace:  # they had a win of their own waiting: a fork, or one line (one cell can't win two)
                race = line_word(f.board, f.menace[0], f.them) if len(f.menace) == 1 else "Fork"
                if len(f.menace) > 1 or race != "Fork":
                    verbs.append((f"Win Your {line} Before Theirs" if race == line else
                                  f"Win the {line} Before Their {race}", {("won", line), ("race", race)}, 0))
                verbs.append((f"Win the Race Down the {line}", {("won", line), ("race",)}, 1))
            spare = line_word(f.board, f.threats[0], f.mover) if len(f.threats) == 1 else NUM[len(f.threats)]
            if len(f.threats) > 1:  # the other wins it had waiting
                verbs.append((f"Take the {line} Over {spare} More", {("won", line), ("spare", spare)}, 0))
            elif f.threats and spare != "Fork":
                verbs.append((f"Take One {line} Over the Other" if spare == line and line != "Side" else
                              "Take One Side Over Another" if spare == line else
                              f"Take the {line} Over the {spare}", {("won", line), ("spare", spare)}, 0))
            compose(verbs, plain, passing, True)
            return out
        if cat == "full":
            compose([("Draw on the Last Cell", {("full",)}, 0)], plain, passing, True, False)
            return out
        if cat == "win-fork":
            said = two(mine) if len(mine) == 2 else "Three Ways"
            compose([(f"Fork {said}", {("fork", said)}, 0)], plain, passing, True)
            compose(verbs_for("and Fork", 5), [("and Fork", {("fork",)}, 0)], [])
            compose([("Fork", {("fork",)}, 6)], plain, passing, alone=False)  # "Fork With Your Side Blocked"
            return out
        if cat == "win-threat":
            compose([(f"Threaten the {mine[0]} and Fork Next", {("forks next", mine[0])}, 0)], plain, passing, True)
            compose(verbs_for("and Fork Next", 5), [("and Fork Next", {("forks next",)}, 0)], [])
            return out
        compose([("Leave Them No Safe Reply", {("no safe reply",)}, 0)], plain, passing, True)
        return out
    if cat == "loss-now":
        lose = {("loses",)}
        race = mine[0] if len(mine) == 1 else None
        if len(theirs) >= 2:
            count = "Two Wins" if len(theirs) == 2 else "Three Wins"
            said = two(theirs) if len(theirs) == 2 else "Three Wins"
            end = f"and Leave Them {count}"
            compose([(f"Leave Them {said}", {("theirs", said), ("theirs", len(theirs))}, 0),
                     (f"Leave Them {count}", {("theirs", len(theirs))}, 0.5)], plain, details)
            compose(verbs_for(end, 0.3), [(end, {("theirs", len(theirs))}, 0)], [])
            if race:
                compose([(f"Chase the {race}", {("chase", race)}, -3)], [(end, {("theirs", len(theirs))}, 0)], details)
            return out
        gift = theirs[0]
        if f.n == 8:
            end = "and Hand Them the Last Cell"
            compose([("Hand Them the Last Cell", {("last cell",)}, 0),
                     (f"Hand Them the {gift} on the Last Cell", {("last cell",), ("theirs", gift)}, 0.5)],
                    plain, details)
            compose(verbs_for(end), [(end, {("last cell",)}, 0)], [])
            if race:
                compose([(f"Chase the {race}", {("chase", race)}, -3)], [(end, {("last cell",)}, 0)], details)
        ends = [("and Lose", lose, 0), (f"and Lose to the {gift}", lose | {("theirs", gift)}, 0.5)]
        compose([(f"Hand Them the {gift}", lose | {("theirs", gift)}, 3 if mine else 0)], plain, details)
        same = [k for k in st if k[0] == "guard" and k[1] == (gift,)]
        for fact in same:
            rest = "the Other" if gift in ("Diagonal", "Middle") else "Another"
            compose([(f"Guard One {gift} and Lose to {rest}", {fact, ("loses",), ("theirs", gift)}, 1)], plain, details)
        for end in ends:
            compose([v for v in verbs_for(end[0], 3 if mine else 0) if next(iter(v[1])) not in same], [end], [])
        if race:
            to = "and Lose to Theirs" if race == gift else f"and Lose to the {gift}"
            compose([(f"Chase the {race}", {("chase", race)}, -3)],
                    [("and Lose", lose, 0), (to, lose | {("theirs", gift)}, 0.5)], details)
        if len(mine) > 1:
            compose([("Fork Too Late", {("fork too late",), ("loses",)}, -3),
                     (f"Fork Too Late for the {gift}", {("fork too late",), ("loses",), ("theirs", gift)}, -2.5)],
                    plain, details)
        return out
    if cat == "loss-fork":
        if mine:
            compose([("Force a Block That Forks You", {("forked by the block",)}, 0),
                     (f"Chase the {mine[0]} Into a Fork", {("forked by the block",), ("chase", mine[0])}, 0)], plain,
                    details)
            compose(verbs_for("and Let Them Fork", 4), [("and Let Them Fork", {("they fork",)}, 0)], [])
            return out
        verbs = [("Let Them Fork", {("they fork",)}, 0.5)]
        kinds = sorted({KIND[i] for i in f.forks})
        if len(kinds) == 1:
            where = "the Centre" if kinds[0] == "centre" else ("an " if kinds[0] == "edge" else "a ") + CELL[kinds[0]]
            verbs.append((f"Let Them Fork From {where}", {("they fork",), ("fork from", kinds[0])}, 0))
        if len(f.forks) > 1:
            verbs.append((f"Leave Them {NUM[len(f.forks)]} Ways to Fork", {("they fork",), ("forks", len(f.forks))},
                          0))
        compose(verbs, plain, details)
        compose(verbs_for("and Let Them Fork", 0.3), [("and Let Them Fork", {("they fork",)}, 0)], [])
        return out
    if cat == "loss-trap":
        if len(mine) == 1:
            compose([(f"Chase the {mine[0]} Into Their Trap", {("trap",), ("chase", mine[0])}, 0)], plain, details)
        compose([("Walk Into Their Trap", {("trap",)}, 0.5)], plain, details)
        compose(verbs_for("and Walk Into Their Trap", 0.8), [("and Walk Into Their Trap", {("trap",)}, 0)], [])
        return out
    judge = f.judge()
    ends = [({"slip": "and Let the Win Slip", "hold": "and Hold", "only": "to Save the Draw", "draw": ""}[judge],
             {("judge", judge)}, 0)]
    if judge == "only":
        ends.append(("and Hold", {("judge", "hold")}, 6))  # the only hold says so wherever a title has room
    if cat == "draw-threat":
        verbs = [(f"Threaten the {mine[0]}", {("chase", mine[0])}, 0)]
        for fact, (verb, _, cost, joins) in st.items():
            if fact[0] == "guard" and joins:
                verbs.append((f"{verb} and Threaten the {mine[0]}", {fact, ("chase", mine[0])}, -0.5))
        if f.counter:
            verbs.append(("Force a Block That Threatens Back", {("chase", mine[0]), ("threatens back",)}, 0.5))
        compose(verbs, ends, details)
        for end in ends:
            compose(verbs_for(end[0], 2.5 if judge == "only" and end == ends[0] else 6), [end], [])
        if judge == "slip":
            compose([("Let the Win Slip", {("judge", judge)}, 6)], plain, details)
        return out
    if judge == "slip":
        compose([("Let the Win Slip", {("judge", judge)}, 0.5)], plain, details)
    elif judge == "hold":
        compose([("Hold the Draw", {("judge", judge)}, 0.5)], plain, details)
    traps = []
    replies = {i: worth(put(f.board, i, f.them), f.them) for i in range(9) if f.board[i] == "."}
    best = max(replies.values())
    bad = [i for i, v in replies.items() if v < best]
    safe = [i for i, v in replies.items() if v == best]
    if bad:
        if len(safe) == 1:
            traps.append(("Leave Them One Safe Reply", {("safe replies", 1)}, 0.5))
        elif all(KIND[i] != "corner" for i in safe) and any(KIND[i] == "corner" for i in bad):
            traps.append(("Leave Them No Safe Corner", {("no safe", "corner")}, 0.5))
        elif all(KIND[i] != "edge" for i in safe) and any(KIND[i] == "edge" for i in bad):
            traps.append(("Leave Them No Safe Edge", {("no safe", "edge")}, 0.5))
        else:
            traps.append(("Set a Trap", {("trap set",)}, 1))
    for end in ends:
        compose(verbs_for(end[0]), [end], [])
        compose(traps, [end], details)
    return out


def opening(f: Facts) -> str:
    """The first two marks, named for where they stand, and the second judged: an edge against the centre and every
    reply to a corner but the centre lose by force."""
    x = f.board.index("X")
    if f.n == 1:
        return {"centre": "Seize the Centre", "corner": "Claim a Corner", "edge": "Open on an Edge"}[KIND[x]]
    o = f.board.index("O")
    if KIND[x] == "centre":
        return "Save the Draw From a Corner" if KIND[o] == "corner" else "Take an Edge and Lose to the Centre"
    if KIND[x] == "corner":
        if KIND[o] == "centre":
            return "Save the Draw From the Centre"
        if KIND[o] == "corner":
            return "Take the Opposite Corner and Lose" if ACROSS[x] == o else "Take an Adjacent Corner and Lose"
        return "Take an Adjacent Edge and Lose" if o in NEAR[x] else "Take a Far Edge and Lose"
    if KIND[o] == "centre":
        return "Hold the Centre Against Their Edge"
    if KIND[o] == "edge":
        return "Hold the Edge Across From Theirs" if ACROSS[x] == o else "Take the Edge Beside Theirs and Lose"
    return "Hold the Corner Beside Their Edge" if x in NEAR[o] else "Take a Far Corner and Lose"


# --- the choice ------------------------------------------------------------------------------------------------------
def neighbours() -> dict[str, set[str]]:
    """Each position's siblings: the other positions a move can make from a board that can make it."""
    out = collections.defaultdict(set)
    for board in SEEN:
        if won(board) or "." not in board:
            continue
        made = {canonical(put(board, i, turn(board))) for i in range(9) if board[i] == "."}
        for shape in made:
            out[shape] |= made - {shape}
    return out


def room(siblings_places: dict[str, int], shape: str) -> int:
    """The longest title the position can have and still take a twin's place after it."""
    place = siblings_places.get(shape, 0)
    return LONGEST - (place + 2 if place else 0)


def twin_places() -> dict[str, int]:
    """For each position two moves on one board can make: the longest place a title of it may have to carry."""
    out: dict = {}
    for board in SEEN:
        if won(board) or "." not in board:
            continue
        made = collections.defaultdict(list)
        for i in range(9):
            if board[i] == ".":
                made[canonical(put(board, i, turn(board)))].append(R.READING[i])
        for shape, cells in made.items():
            if len(cells) > 1:
                out[shape] = max(out.get(shape, 0), max(len(PLACES[c]) for c in cells))
    return out


def choose(facts: dict[str, Facts], reserved: set[str]) -> dict[str, tuple]:
    """Each position's title: its cheapest true candidate that no other position's title says, in its words or in
    what it claims (two titles that claimed the same facts in another order would be one name twice), nor an opening's
    title (`reserved`). Titles are given out by regret (the position that would lose most by waiting chooses first),
    then bettered along chains of moves, and two titles on one board never read as one and the same title with more
    said that is true of both."""
    places, siblings = twin_places(), neighbours()
    named = {s: candidates(f) for s, f in facts.items() if f.n > 2}
    held = {s: frozenset().union(*(c[1] for c in cs)) for s, cs in named.items()}  # every fact a position has
    family = collections.defaultdict(list)
    for s in named:
        family[facts[s].category].append(s)

    def keys(c):
        """What a title says: its words, and the facts it claims."""
        return c[0], frozenset(c[1])

    def telling(s, c):
        """Whether each detail says something its lead does not: some position of the family has the lead without
        it."""
        for detail in c[1] - c[4]:
            if not any(c[4] <= held[p] and detail not in held[p] for p in family[facts[s].category] if p != s):
                return False
        return True
    cands = {}
    for s, cs in named.items():
        kept, said = {}, set()
        weight = 1 + 0.15 * max(0, 7 - facts[s].n)  # the early positions come up most: they choose most carefully
        for c in sorted(cs, key=lambda c: (c[2], c[0])):
            if len(c[0]) + 1 > room(places, s) or said & set(keys(c)) or c[0] in reserved or not telling(s, c):
                continue
            said |= set(keys(c))
            shared = sum(1 for o in siblings[s] if o in held and c[1] <= held[o])  # true of a move beside it too
            kept[c[0]] = (c[0], c[1], (c[2] + 0.6 * shared + len(c[0]) / 40) * weight, c[3], c[4])
        cands[s] = sorted(kept.values(), key=lambda c: (c[2], c[0]))
    got: dict = {}
    holder: dict = {}  # each title's words and each set of facts a title claims, with the position whose title it is

    def occupants(c, s):
        return {holder[k] for k in keys(c) if k in holder} - {s}

    def echoes(c, o, s_o):
        """Whether `c` would read as o's title with more said that is true of o's position too ("Guard the Side and
        Lose to the Centre" beside "Guard the Side and Lose", when both lose to the centre)."""
        return o[1] < c[1] and c[1] - o[1] <= held.get(s_o, frozenset())

    def fits(s, c):
        return not any(o in got and (echoes(c, got[o], o) or echoes(got[o], c, s)) for o in siblings[s])

    def free(s, c):
        return not occupants(c, s) and fits(s, c)

    def assign(pairs):
        """Give each position its title at once."""
        for s, _ in pairs:
            for k in keys(got[s]) if s in got else ():
                if holder.get(k) == s:
                    del holder[k]
        for s, c in pairs:
            got[s] = c
            for k in keys(c):
                holder[k] = s

    def move(s, c):
        assign([(s, c)])

    def best_two(s):
        cs = cands[s]
        i = next((k for k, c in enumerate(cs) if free(s, c)), len(cs))
        j = next((k for k, c in enumerate(cs) if k > i and free(s, c)), len(cs))
        costs = [c[2] for c in cs] + [50, 50]  # no title left costs most
        return i, costs[j] - costs[i]
    heap = []
    for s in sorted(cands):
        i, regret = best_two(s)
        heapq.heappush(heap, (-regret, s, i))
    while heap:
        regret, s, i = heapq.heappop(heap)
        if s in got:
            continue
        now = best_two(s)
        if now != (i, -regret):
            heapq.heappush(heap, (-now[1], s, now[0]))
            continue
        if i < len(cands[s]):
            move(s, cands[s][i])

    def augment(s, seen, fixed=frozenset()):
        """A title for s, freed along chains of positions that each move to another title of theirs (none of them
        `fixed`)."""
        for c in cands[s]:
            if seen & set(keys(c)) or not fits(s, c):
                continue
            seen |= set(keys(c))
            for o in sorted(occupants(c, s)):
                if o not in got or o in fixed or not augment(o, seen, fixed):
                    break
            if not occupants(c, s) and fits(s, c):
                move(s, c)
                return True
        return False
    for s in sorted(cands):
        if s not in got and not augment(s, set()):
            if __import__("os").environ.get("TTT_DEBUG"):
                for c in cands[s]:
                    print("   ", c[0], "| held by", [(o, got[o][0]) for o in occupants(c, s)], "| fits", fits(s, c))
            raise ValueError(f"no title is left for {s}")

    def chain(s, allowance, seen, depth):
        """Moves that free a title for whoever wants s's: s takes another title, perhaps from someone who moves
        on in turn, for a rise in cost under `allowance`."""
        for c in cands[s]:
            rise = c[2] - got[s][2]
            if rise >= allowance or seen & set(keys(c)) or c[0] == got[s][0] or not fits(s, c):
                continue
            others = occupants(c, s)
            if not others:
                return [(s, c)]
            if depth and len(others) == 1 and next(iter(others)) in got:
                rest = chain(next(iter(others)), allowance - rise, seen | set(keys(c)), depth - 1)
                if rest is not None:
                    return [(s, c)] + rest
        return None
    for _ in range(8):
        better = False
        for s in sorted(cands, key=lambda s: (-got[s][2], s)):
            for c in cands[s]:
                gain = got[s][2] - c[2]
                if gain <= 0.5:
                    break
                if not fits(s, c):
                    continue
                others = occupants(c, s)
                moves = None if others else [(s, c)]
                if len(others) == 1 and next(iter(others)) in got:
                    rest = chain(next(iter(others)), gain, set(keys(c)) | set(keys(got[s])), 2)
                    moves = rest and [(s, c)] + rest
                if moves:
                    before = [(p, got[p]) for p, _ in moves]
                    for p, d in reversed(moves):
                        move(p, d)
                    if all(fits(p, got[p]) for p, _ in moves):  # each move fitted the board as it stood: all together?
                        better = True
                        break
                    assign(before)
        if not better:
            break
    for _ in range(8):  # a chain of moves can leave two titles on one board reading as one: give one another title
        for s in [s for s in sorted(got) if not fits(s, got[s])]:
            pair = [s] + sorted(o for o in siblings[s] if o in got and (echoes(got[s], got[o], o)
                                                                        or echoes(got[o], got[s], s)))
            for t in pair:
                if fits(s, got[s]):
                    break
                old = got.pop(t)
                for k in keys(old):
                    if holder.get(k) == t:
                        del holder[k]
                if not augment(t, set(), siblings[t] | {t}):  # moving a title beside it would only swap the two
                    move(t, old)
    clashing = [s for s in sorted(got) if not fits(s, got[s])]
    if clashing:
        raise ValueError(f"titles that read as each other's on one board: {[(s, got[s][0]) for s in clashing]}")
    said = collections.Counter(k for c in got.values() for k in keys(c))
    if max(said.values()) > 1:
        raise ValueError(f"titles said twice: {[k for k, n in said.items() if n > 1]}")
    return got


# --- the table -------------------------------------------------------------------------------------------------------
def emoji(f: Facts) -> str:
    """One emoji for what the move does: the win, the drawn last cell, a blunder, a fork (or the quiet move that wins
    as surely), a threat, or for a quiet move where its mark went, when every board that makes the position agrees,
    and the draw it keeps otherwise. A board's listing shows a quiet move's own cell, and a block as the block it is
    (tictactoe_names.py)."""
    if f.category == "win":
        return EMOJI["win"]
    if f.worth == -1:
        return EMOJI["blunder"]
    if f.full:
        return EMOJI["draw"]
    if len(f.threats) >= 2 or f.worth == 1 and not f.threats:
        return EMOJI["fork"]
    if f.threats:
        return EMOJI["threat"]
    kinds = {KIND[i] for _, i, _, _ in f.boards}
    return EMOJI[kinds.pop()] if len(kinds) == 1 else EMOJI["draw"]


def judgement(f: Facts) -> str:
    """What perfect play makes of the move, from the mover's side."""
    if f.category == "win":
        return "wins: three in a row" + (", two lines at once" if len(f.won) == 2 else "")
    if f.full:
        return "draws: the last cell"
    if f.worth == 1:
        how = {"win-fork": "a fork they cannot block both ways", "win-threat": "the block it forces leaves a fork",
               "win-quiet": "every reply loses"}[f.category]
        return f"wins by force: {how}"
    if f.worth == -1:
        how = {"loss-now": "they win next move", "loss-fork": "they fork next move",
               "loss-trap": "they force a fork"}[f.category]
        lead = ("throws away a won game and loses by force" if f.before == [1] else
                "loses by force, as every move from there does" if f.before == [-1] else "loses by force")
        return f"{lead}: {how}"
    return {"slip": "throws away a won game: draws", "hold": "holds the draw",
            "only": "holds the draw: the only move that does, from every board that makes it",
            "draw": "draws: a hold from some boards, a slip from others"}[f.judge()]


def said(fact: tuple) -> str:
    return ":".join(str(x) if not isinstance(x, tuple) else "+".join(map(str, x)) for x in fact)


def table() -> dict:
    """Every position a move can make, with its title, emoji, judgement and the facts its title claims."""
    facts = {s: Facts(s) for s in POSITIONS}
    got = choose(facts, {opening(f) for f in facts.values() if f.n <= 2})
    out = {}
    for s in POSITIONS:
        f = facts[s]
        if f.n <= 2:
            title, claims = opening(f), [("opening",)]
        else:
            title, claims = got[s][0], sorted(got[s][1], key=said)
        key = "/".join(s[r * 3:r * 3 + 3] for r in range(3))
        out[key] = {"title": title + "!", "emoji": emoji(f), "judgement": judgement(f),
                    "facts": [said(c) for c in claims]}
    return out


def render(positions: dict) -> str:
    """The table as its file keeps it: one position to a line, by the marks down and then the board."""
    lines = [json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
             for key, value in positions.items()]
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
