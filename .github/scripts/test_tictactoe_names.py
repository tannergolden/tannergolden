# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named for where its mark goes: every title read phrase by phrase against its board, every board
of every game listed as the engine shows it, whichever mark moved first, and nothing in any of it a verdict.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

A title's truth is read here from tictactoe_rules.py alone, by code that shares nothing with the script that builds
the table: every word of a title belongs to a phrase this file knows, every phrase is true of its move, on every
board the titles tell the cells apart, and no two moves in the whole game share a title or say the same thing in
other words (mirror twins aside, which share one and add their place). Neutrality is held to the owner's rule, that
no name helps a player choose: no judgement, consequence or line word, no judging emoji, no `+` or `#`, and a move
that wins on the spot reads like one that does nothing.
"""
from __future__ import annotations

import collections
import functools
import itertools
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tictactoe_names_table as T
import tictactoe_rules as R
from tictactoe_names import PLACES, TABLE, canonical, listing, made, names

HERE = Path(__file__).resolve().parent
# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,98}[A-Za-z0-9,.'!-])?")  # no space at either end
LONGEST = 100  # the longest title the kit takes for Tic-Tac-Toe, a twin's place included
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
SMALL = {"a", "an", "the", "and", "to", "of", "on", "at", "for", "in", "by"}  # the words Title Case leaves small
SWAP = str.maketrans("XO", "OX")
TITLES = names()
SIGN = {"Centre": "\U0001f533", "Corner": "📐", "Edge": "📏"}  # a framed square for the middle cell, no star
EDGES = {(1, 2): "top", (1, 0): "bottom", (0, 1): "left", (2, 1): "right"}  # each edge by its file and rank

# The owner's rule: no judgement, no consequence or tactic, no strategy verdict, no named opening, and in Tic-Tac-Toe
# no phrase about a row, a column or a diagonal and what it holds. Each is a whole word, in any case.
BANNED = (
    "good", "bad", "safe", "sound", "strong", "weak", "win", "wins", "winning", "won", "lose", "loses", "losing",
    "lost", "draw", "draws", "drawn", "save", "saves", "hold", "holds", "slip", "slips", "only", "best", "forced",
    "blunder", "mistake", "check", "checks", "mate", "stalemate", "threat", "threats", "threaten", "threatens",
    "threatening", "block", "blocks", "blocked", "blocking", "fork", "forks", "pin", "pins", "skewer", "discovered",
    "double", "trap", "traps", "shot", "sacrifice", "gambit", "exchange", "trade", "attack", "attacks", "defend",
    "defends", "guard", "guards", "guarding", "escape", "hang", "hangs", "material", "next", "leaves", "lets", "leave",
    "let", "rim", "outpost", "open", "battery", "seventh", "passed", "luft", "fianchetto", "seize", "command",
    "control", "bridge", "row", "rows", "column", "columns", "diagonal", "diagonals", "line", "lines", "middle", "side",
    "sides", "between", "end", "ends", "complete", "completes", "race", "chase", "hand", "book", "opening",
)
BANNED_RE = re.compile(r"\b(?:" + "|".join(BANNED) + r")\b|two-for-one|in a row", re.IGNORECASE)
BANNED_EMOJI = ("⚠", "🏆", "🔑", "🛡", "⚡", "🎯", "💥", "💸", "📌", "🍴", "🎁", "💰", "🔄", "☠", "🤝", "📖", "⭐")


# --- boards either mark opened -----------------------------------------------------------------------------------
def board(text: str, first: str = R.X) -> R.Position:
    """A position from three rows of marks, `first` the mark that opened."""
    return R.Position.from_board(text, first)


def reach(first: str) -> list[R.Position]:
    """Every position the game can reach, `first` to move first, that has a move to make."""
    seen, todo = {}, [R.opening(first)]
    while todo:
        position = todo.pop()
        if position.marks not in seen:
            seen[position.marks] = position
            todo += [R.make(position, cell) for cell in R.legal(position)]
    return [seen[marks] for marks in sorted(seen) if R.legal(seen[marks])]


REACHED = {first: reach(first) for first in (R.X, R.O)}
LISTED = {first: {position: listing(position, 1, 1) for position in found}
          for first, found in REACHED.items()}  # every board's listing, once for every test here


# --- the board's geometry, from the cells' names -------------------------------------------------------------------
def spot(cell: str) -> tuple[int, int]:
    return "abc".index(cell[0]), int(cell[1]) - 1


def kind(cell: str) -> str:
    return "Centre" if cell == R.CENTRE else "Corner" if cell in R.CORNERS else "Edge"


def touching(a: str, b: str) -> bool:
    """Two cells that share a side or a corner."""
    (fa, ra), (fb, rb) = spot(a), spot(b)
    return a != b and max(abs(fa - fb), abs(ra - rb)) == 1


def beside(a: str, b: str) -> bool:
    """Two cells that share a side."""
    (fa, ra), (fb, rb) = spot(a), spot(b)
    return abs(fa - fb) + abs(ra - rb) == 1


def facing(a: str, b: str) -> bool:
    """Two cells on either side of the centre."""
    (fa, ra), (fb, rb) = spot(a), spot(b)
    return a != R.CENTRE and (fa + fb, ra + rb) == (2, 2)


def along(a: str, b: str) -> bool:
    """Two corners a cell apart along the edge of the board."""
    (fa, ra), (fb, rb) = spot(a), spot(b)
    return a != b and a in R.CORNERS and b in R.CORNERS and (fa == fb or ra == rb)


def turns(cell: str, n: int) -> str:
    """The cell under the n-th of the board's eight turns and mirrors."""
    f, r = spot(cell)
    for _ in range(n // 2):
        f, r = r, 2 - f
    if n % 2:
        f = 2 - f
    return f"{'abc'[f]}{r + 1}"


def twins(position: R.Position) -> dict[str, set[str]]:
    """Each open cell with the cells a turn or mirror of the board, marks and all, carries it to."""
    keep = [n for n in range(8) if all(position.at(turns(c, n)) == position.at(c) for c in R.READING)]
    return {c: {turns(c, n) for n in keep} for c in R.legal(position)}


class Look:
    """A move as the board shows it, from the side that moves: the cell, its kind, and every other mark."""

    def __init__(self, position: R.Position, cell: str):
        self.position, self.cell, self.kind = position, cell, kind(cell)
        self.mover = position.turn
        marks = {c: position.at(c) for c in R.READING if position.at(c)}
        self.side = {"Your": [c for c, m in marks.items() if m == self.mover],
                     "Their": [c for c, m in marks.items() if m != self.mover]}
        self.after = R.make(position, cell)

    def near(self, side: str) -> list[str]:
        return sorted(kind(c) for c in self.side[side] if touching(c, self.cell))

    def far(self, side: str) -> list[str]:
        return sorted(kind(c) for c in self.side[side]
                      if not touching(c, self.cell) and not facing(c, self.cell) and not along(c, self.cell))

    def wins(self) -> bool:
        end = R.ending(self.after)
        return bool(end and end.winner == self.mover)

    def gives(self) -> bool:
        """Whether the other side could win with its next mark: the move loses on the spot."""
        return not R.ending(self.after) and bool(R.threats(self.after, R.other(self.mover)))


# --- every phrase a title can hold, with what makes it true --------------------------------------------------------
NUMBER = {"One": 1, "Two": 2, "Three": 3, "Four": 4}
ORDINAL = {"First": 1, "Second": 2, "Third": 3, "Fourth": 4, "Fifth": 5}
KIND = r"(?:(?:Two|Three|Four) )?(?:Centre|Corners?|Edges?)"  # one kind of cell, or a count of them
KINDS = rf"{KIND}(?:(?:, | and ){KIND})*"
ONE = r"(?:Centre|Corner|Edge)"
SIDE = {"Your": "Your", "Their": "Their", "Yours": "Your", "Theirs": "Their"}
OTHER = {"Your": "Their", "Their": "Your"}


def said(kinds: list[str]) -> str:
    """Kinds as a title says them: `Edge`, `Two Corners`, `Centre and Edge`, `Centre, Corner and Edge`."""
    count = collections.Counter(kinds)
    parts = [k if count[k] == 1 else f"{['', '', 'Two', 'Three', 'Four'][count[k]]} {k}s"
             for k in ("Centre", "Corner", "Edge") if count[k]]
    if len(parts) < 2:
        return "".join(parts)  # no marks at all says nothing a title could match
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def nest(look: Look, side: str, k: str, other: str, other_kind: str | None, how=beside) -> bool:
    """Whether a mark of `side` of kind `k` touches the cell and shares a side with one of `other`'s (of kind
    `other_kind`, when it is named), or faces it over the centre (`how`)."""
    return any(touching(c, look.cell) and how(c, d) and other_kind in (None, kind(d))
               for c in look.side[side] if kind(c) == k for d in look.side[other])


def distant(look: Look, side: str, k: str, other: str, other_kind: str | None, also: bool) -> bool:
    """Whether a mark of `side` of kind `k` neither touches the cell, nor faces it, nor sits a corner along from it,
    and touches one of `other`'s (of kind `other_kind`, when it is named); and whether another of that side and kind
    touches the cell (`also`: "Away From Their Other Edge") or none does."""
    if any(touching(c, look.cell) for c in look.side[side] if kind(c) == k) != also:
        return False
    return any(not touching(c, look.cell) and not facing(c, look.cell) and not along(c, look.cell)
               and touching(c, d) and other_kind in (None, kind(d))
               for c in look.side[side] if kind(c) == k for d in look.side[other])


# (name, pattern, truth): every detail a title can give, and what must be true of its move when it does.
PHRASES = [
    ("none", r"by No Mark", lambda v, m: not v.near("Your") and not v.near("Their")),
    ("both same", rf"by Your ({KINDS}) and Theirs",
     lambda v, m: said(v.near("Your")) == said(v.near("Their")) == m[1] and len(set(v.near("Your"))) == 1),
    ("both", rf"by Your ({KINDS}) and Their ({KINDS})",
     lambda v, m: said(v.near("Your")) == m[1] and said(v.near("Their")) == m[2]),
    ("both mixed", rf"by Your ({KINDS}) and (One|Two|Three|Four) of Theirs",
     lambda v, m: said(v.near("Your")) == m[1] and len(v.near("Their")) == NUMBER[m[2]]),
    ("both mixed", rf"by (One|Two|Three|Four) of Yours and Their ({KINDS})",
     lambda v, m: len(v.near("Your")) == NUMBER[m[1]] and said(v.near("Their")) == m[2]),
    ("nest by", rf"by (Your|Their) ({ONE}) Beside (?:(Yours|Theirs)|(Your|Their) ({ONE}))",
     lambda v, m: nest(v, m[1], m[2], SIDE[m[3] or m[4]], m[5])),
    ("nest across", rf"by (Your|Their) ({ONE}) Across From (Your|Their) ({ONE})",
     lambda v, m: nest(v, m[1], m[2], m[3], m[4], facing)),
    ("by", rf"by (Your|Their) ({KINDS})( Alone)?",
     lambda v, m: said(v.near(m[1])) == m[2] and (not m[3] or not v.near(OTHER[m[1]]))),
    ("by counted", r"by (One|Two|Three|Four) of (Yours|Theirs)( Alone)?",
     lambda v, m: len(v.near(SIDE[m[2]])) == NUMBER[m[1]] and (not m[3] or not v.near(OTHER[SIDE[m[2]]]))),
    ("across", r"Across From (Yours|Theirs)",
     lambda v, m: any(facing(v.cell, c) for c in v.side[SIDE[m[1]]])),
    ("along", r"Along From (Yours|Theirs)", lambda v, m: v.kind == "Corner"
     and sum(along(v.cell, c) for c in v.side[SIDE[m[1]]]) == 1),
    ("along", r"Along From (Your|Their) Two Corners", lambda v, m: v.kind == "Corner"
     and sum(along(v.cell, c) for c in v.side[m[1]]) == 2),
    ("along", r"Along From Your Corner and Theirs", lambda v, m: v.kind == "Corner"
     and sum(along(v.cell, c) for c in v.side["Your"]) == sum(along(v.cell, c) for c in v.side["Their"]) == 1),
    ("nest away", rf"Away From (Your|Their) (Other )?({ONE}) by (?:(Yours|Theirs)|(Your|Their) ({ONE}))",
     lambda v, m: distant(v, m[1], m[3], SIDE[m[4] or m[5]], m[6], bool(m[2]))),
    ("away both", rf"Away From Your ({KINDS}) and (?:Theirs|Their ({KINDS}))",
     lambda v, m: away(v, "Your", m[1]) and away(v, "Their", m[2] or m[1])),
    ("away", rf"Away From (Your|Their) ({KINDS})", lambda v, m: away(v, m[1], m[2])),
    ("against", rf"Against Their ({KINDS})", lambda v, m: v.kind != "Centre"
     and said(sorted(kind(c) for c in v.side["Their"])) == m[1]),
    ("mark", r"With Your (First|Second|Third|Fourth|Fifth) Mark",
     lambda v, m: len(v.side["Your"]) + 1 == ORDINAL[m[1]]),
]
PHRASES = [(name, re.compile(pattern), truth) for name, pattern, truth in PHRASES]


def away(look: Look, side: str, text: str) -> bool:
    """Whether a side's marks that neither touch the cell, nor face it, nor sit a corner along from it are `text`, and
    none of that side's marks of those kinds touches the cell."""
    return said(look.far(side)) == text and not set(look.far(side)) & set(look.near(side))


LEAD = re.compile(
    r"(?P<verb>Take|Mark) (?P<the>the|an?) (?P<kind>Centre|Corner|Edge)"
    r"|(?P<start>Start) (?P<at0>in|on) (?P<the0>the|an?) (?P<kind0>Centre|Corner|Edge)"
    r"|Take Your (?P<nth>First|Second|Third|Fourth) (?P<kind2>Corner|Edge)"
    r"|(?P<lay>Lay|Set) Your (?P<ord>First|Second|Third|Fourth|Fifth) Mark (?P<at>in|on) "
    r"(?P<the3>the|an?) (?P<kind3>Centre|Corner|Edge)")
DETAIL = re.compile(r", (?=(?:by|Across From|Along From|Away From|Against|With Your) )")


class Reading:
    """A title taken apart: its lead's form, the cell's kind, the article, what the lead counts, and each detail."""

    def __init__(self, title: str):
        self.title = title
        text = title.removesuffix("!")
        m = LEAD.match(text)
        if not m:
            raise ValueError(f"{title!r} opens with no lead this file knows")
        self.kind = m["kind"] or m["kind0"] or m["kind2"] or m["kind3"]
        self.article = m["the"] or m["the0"] or m["the3"]  # None for "Take Your Second Corner"
        self.form = (m["verb"] or m["start"] or ("Take Your" if m["nth"] else m["lay"])).lower()
        self.count = ORDINAL.get(m["nth"] or "")
        self.marks = ORDINAL.get(m["ord"] or "")
        self.at = m["at"] or m["at0"]
        self.start = bool(m["start"])
        rest = text[m.end():]
        if rest and not rest.startswith(" "):
            raise ValueError(f"{title!r} runs its lead into what follows")
        self.details = DETAIL.split(rest[1:]) if rest else []
        self.read = []
        for detail in self.details:
            found = next(((name, p.fullmatch(detail), truth) for name, p, truth in PHRASES if p.fullmatch(detail)),
                         None)
            if found is None:
                raise ValueError(f"{detail!r} in {title!r} is no phrase this file knows")
            self.read.append(found)

    def true(self, look: Look) -> bool:
        """Whether every claim the title makes holds of the move."""
        mine = self.marks is None or len(look.side["Your"]) + 1 == self.marks
        counted = self.count is None or sum(kind(c) == self.kind for c in look.side["Your"]) + 1 == self.count
        started = self.start == (not look.side["Your"] and not look.side["Their"])  # the game's first mark alone
        return (look.kind == self.kind and mine and counted and started
                and all(truth(look, m) for _, m, truth in self.read))

    def says(self) -> frozenset:
        """What the title claims, in whatever words and order: its cell's kind, whether the game starts there, the
        count its lead or a detail makes, and every other detail. `Lay Your Third Mark in a Corner, by Their Edge` and
        `Take the Corner by Their Edge, With Your Third Mark` say one thing."""
        marks = {self.marks} | {ORDINAL[m[1]] for name, m, _ in self.read if name == "mark"}
        return frozenset({("cell", self.kind), ("start", self.start), ("count", self.count)}
                         | {("mark", n) for n in marks if n}
                         | {("detail", m[0]) for name, m, _ in self.read if name != "mark"})

    def shapes(self) -> list[str]:
        """The lead's form and each detail's phrase, for comparing moves that do different things."""
        return [f"lead {self.form}"] + [name for name, _, _ in self.read]


@functools.cache
def reading(title: str) -> Reading:
    return Reading(title)


def bare(entry: dict, double: set[str]) -> str:
    """A listed title without the place a twin adds."""
    if len(double) > 1:
        place = f", {PLACES[entry['code']]}!"
        assert entry["title"].endswith(place), entry
        return entry["title"][:-len(place)] + "!"
    return entry["title"]


def boards():
    """Every board of every game, either mark first, with its listing and each open cell's twins."""
    for first, listed in LISTED.items():
        for position, entries in listed.items():
            yield first, position, entries, twins(position)


# --- the tests ---------------------------------------------------------------------------------------------------
class Counts(unittest.TestCase):
    """The game counted whole, as the table counts it, either mark first."""

    def test_every_move_of_every_game_is_named(self):
        for first in (R.X, R.O):
            self.assertEqual(len(REACHED[first]), 4520, f"every position with a move to make, {first} first")
            keys = {made(p, c) for p in REACHED[first] for c in R.legal(p)}
            self.assertEqual(keys, set(TITLES), f"{first} first: every move the game has is in the table, no more")
        self.assertEqual(len(TITLES), 2096, "2,096 moves once the board's turns and mirrors are set aside")

    def test_the_moves_make_the_764_positions(self):
        positions = {canonical(k.replace("/", "").upper()) for k in TITLES}
        self.assertEqual(len(positions), 764)
        boards = {canonical(k.replace("/", "").replace("x", ".").replace("o", ".")) for k in TITLES}
        self.assertEqual(len(boards), 627, "made on 627 boards")


class Table(unittest.TestCase):
    def test_the_table_is_what_the_script_makes(self):
        self.assertEqual(T.render(T.table()), TABLE.read_text(encoding="utf-8"),
                         "run tictactoe_names_table.py to build tictactoe_names.json again")

    def test_the_script_makes_the_same_table_whatever_the_hash_seed(self):
        """The table above was made under this run's hash seed; the script makes it again under another."""
        seed = "4242" if os.environ.get("PYTHONHASHSEED") == "0" else "0"
        env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN", "MARKDOWN_TOKEN")}
        done = subprocess.run([sys.executable, str(HERE / "tictactoe_names_table.py"), "--check"],
                              env={**env, "PYTHONHASHSEED": seed}, capture_output=True, text=True, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_table_keeps_no_judgement(self):
        for key, entry in TITLES.items():
            self.assertEqual(set(entry), {"title", "facts"}, key)

    def test_every_stored_fact_is_true_of_its_move(self):
        """The facts a title claims, as the table keeps them, read against the move the key describes."""
        for key, entry in TITLES.items():
            marks = key.replace("/", "")
            cell = R.READING[next(i for i, m in enumerate(marks) if m.islower())]
            before = "".join("." if m.islower() else m for m in marks)
            position = board("/".join(before[r:r + 3] for r in (0, 3, 6)))
            look = Look(position, cell)
            with self.subTest(key=key, title=entry["title"]):
                for fact in entry["facts"]:
                    self.assertTrue(stored(look, fact), fact)

    def test_every_title_is_an_order_in_title_case(self):
        for key, entry in TITLES.items():
            title = entry["title"]
            with self.subTest(key=key, title=title):
                self.assertTrue(KIT_TITLE.fullmatch(title))
                self.assertTrue(title.endswith("!") and title.count("!") == 1)
                self.assertLessEqual(len(title), LONGEST)
                self.assertNotRegex(title, r"\b[a-c][1-3]\b|\b[XO]\b|\d", "a title names no cell, mark or digit")
                self.assertLessEqual(title.count("Mark"), 1, "never Mark the Corner by No Mark")
                self.assertEqual(title.startswith("Start "), key.count(".") == 8, "the first mark alone starts")
                self.assertNotIn("Start", title.removeprefix("Start "))
                self.assertNotRegex(title, r"Your First (?:Corner|Edge).*First Mark", "one count, said once")
                for word in title.rstrip("!").split()[1:]:
                    self.assertTrue(word in SMALL or word[0].isupper(), word)
                for dash in DASHES:
                    self.assertNotIn(dash, title)


def stored(look: Look, fact: str) -> bool:
    """Whether a fact the table keeps is true of the move: `by:their=centre+edge`, `across:your`, `mark:3`."""
    name, _, rest = fact.partition(":")
    parts = rest.split(":")
    side, _, value = parts[0].partition("=")
    side = {"your": "Your", "their": "Their"}.get(side, side)
    kinds = sorted(k.title() for k in value.split("+")) if value not in ("none", "") else []
    if name == "cell":
        return look.kind == rest.title()
    if name == "mark":
        return len(look.side["Your"]) + 1 == int(rest)
    if name == "count":
        return sum(kind(c) == look.kind for c in look.side["Your"]) + 1 == int(rest)
    if name == "by":
        return look.near(side) == kinds
    if name == "by-count":
        return len(look.near(side)) == int(value)
    if name == "across":
        return any(facing(look.cell, c) for c in look.side[side])
    if name == "along":
        return look.kind == "Corner" and sum(along(look.cell, c) for c in look.side[side]) == int(value)
    if name == "away":
        return look.far(side) == kinds and not set(kinds) & set(look.near(side))
    if name == "start":
        return not look.side["Your"] and not look.side["Their"]
    if name == "against":
        return look.kind != "Centre" and sorted(kind(c) for c in look.side["Their"]) == kinds
    if name in ("nest-by", "nest-across", "nest-away", "nest-away-other"):
        other, _, other_kind = parts[1].partition("=")[2].partition("=")
        other = {"your": "Your", "their": "Their"}[other]
        if name == "nest-by":
            return nest(look, side, value.title(), other, other_kind.title() or None)
        if name == "nest-across":
            return nest(look, side, value.title(), other, other_kind.title(), facing)
        return distant(look, side, value.title(), other, other_kind.title() or None, name == "nest-away-other")
    raise AssertionError(f"{fact!r} is no fact this file knows")


class Titles(unittest.TestCase):
    """Every title on every board, read phrase by phrase."""

    def test_every_title_is_true_of_its_move_phrase_by_phrase(self):
        used = collections.Counter()
        for first, position, entries, double in boards():
            for entry in entries:
                title = bare(entry, double[entry["code"]])
                with self.subTest(first=first, board=position.board, cell=entry["code"], title=title):
                    read = reading(title)
                    self.assertTrue(read.true(Look(position, entry["code"])))
                    if read.at:
                        self.assertEqual(read.at, "on" if read.kind == "Edge" else "in")
                    used.update(read.shapes())
        families = {"by", "by counted", "none", "both", "both same", "both mixed", "nest by", "nest across", "across",
                    "along", "away", "away both", "nest away", "against", "mark"}
        leads = {f"lead {form}" for form in ("start", "take", "mark", "take your", "lay", "set")}
        self.assertEqual(set(used), families | leads, "every phrase the generator has is used, and no other")

    def test_every_board_tells_its_cells_apart(self):
        """No two cells on a board share a title, and of any two that are not mirror images, at least one has a title
        that is not true of the other. Nearly every title is true of its own cell alone."""
        alone = total = 0
        for first, position, entries, double in boards():
            titles = [e["title"] for e in entries]
            self.assertEqual(len(set(titles)), len(titles), (first, position.board, titles))
            looks = {e["code"]: Look(position, e["code"]) for e in entries}
            read = {e["code"]: reading(bare(e, double[e["code"]])) for e in entries}
            for a, b in itertools.combinations(looks, 2):
                if b in double[a]:
                    continue
                with self.subTest(first=first, board=position.board, cells=(a, b)):
                    self.assertFalse(read[a].true(looks[b]) and read[b].true(looks[a]),
                                     (read[a].title, read[b].title))
            for cell in looks:
                total += 1
                alone += not any(read[cell].true(looks[c]) for c in looks if c not in double[cell])
        self.assertGreater(alone / total, 0.99, "nearly every title is true of its own cell alone")

    def test_the_says_its_cell_is_the_only_one(self):
        """`the corner` is the one corner on the board the title is true of; a twin, or a cell its title does not
        single out, is `a corner` or `an edge`."""
        for first, position, entries, double in boards():
            looks = {e["code"]: Look(position, e["code"]) for e in entries}
            for e in entries:
                read = reading(bare(e, double[e["code"]]))
                if read.article is None or read.kind == "Centre":
                    continue
                alone = not any(read.true(looks[c]) for c in looks if c not in double[e["code"]])
                with self.subTest(first=first, board=position.board, title=e["title"]):
                    if read.article == "the":
                        self.assertTrue(alone and len(double[e["code"]]) == 1)
                    else:
                        self.assertEqual(read.article, "an" if read.kind == "Edge" else "a")
                    if len(double[e["code"]]) > 1:
                        self.assertNotEqual(read.article, "the")

    def test_mirror_twins_share_a_title_and_add_their_place(self):
        count = 0
        for _, position, entries, double in boards():
            by_cell = {e["code"]: e for e in entries}
            for cell, group in double.items():
                if len(group) > 1:
                    count += 1
                    titles = {bare(by_cell[c], group) for c in group}
                    self.assertEqual(len(titles), 1, (position.board, group))
                    self.assertTrue(by_cell[cell]["title"].endswith(f", {PLACES[cell]}!"))
                else:
                    self.assertFalse(any(by_cell[cell]["title"].endswith(f", {p}!") for p in PLACES.values()))
        self.assertGreater(count, 1000)

    def test_every_move_on_a_board_opens_alike(self):
        for first, position, entries, double in boards():
            forms = {reading(bare(e, double[e["code"]])).form for e in entries if e["code"] != R.CENTRE}
            centre = [reading(e["title"]).form for e in entries if e["code"] == R.CENTRE]
            with self.subTest(first=first, board=position.board):
                self.assertLessEqual(len(forms), 1, [e["title"] for e in entries])
                if centre and forms:
                    self.assertIn(centre[0], forms | ({"take"} if forms == {"take your"} else set()))


class Unique(unittest.TestCase):
    """The owner's rule for the whole game: no two moves share a title, on one board or on any two."""

    def test_no_title_is_given_to_two_moves(self):
        titles = collections.Counter(entry["title"] for entry in TITLES.values())
        self.assertEqual([t for t, n in titles.items() if n > 1], [])
        facts = collections.Counter(frozenset(entry["facts"]) for entry in TITLES.values())
        self.assertEqual(len(facts), len(TITLES), "no two titles claim the same facts")

    def test_no_two_titles_say_the_same_thing_in_other_words(self):
        said = collections.defaultdict(list)
        for entry in TITLES.values():
            said[reading(entry["title"]).says()].append(entry["title"])
        self.assertEqual([titles for titles in said.values() if len(titles) > 1], [])

    def test_a_title_shown_anywhere_names_one_move(self):
        """Every title the listings show, its twin's place aside, belongs to one move, whichever mark opened and
        however the board is turned; a move's mirror twins are the only cells that share one."""
        moves = collections.defaultdict(set)
        for _, position, entries, double in boards():
            for e in entries:
                moves[bare(e, double[e["code"]])].add(made(position, e["code"]))
        self.assertEqual(len(moves), len(TITLES))
        self.assertEqual({t: keys for t, keys in moves.items() if len(keys) > 1}, {})


class Neutral(unittest.TestCase):
    """The owner's rule: a title says what the move is, never what it does to the game."""

    def test_nothing_listed_judges_the_move(self):
        for first, position, entries, _ in boards():
            for e in entries:
                with self.subTest(first=first, board=position.board, cell=e["code"]):
                    for text in (e["title"], e["words"], e["notation"], e["emoji"]):
                        self.assertIsNone(BANNED_RE.search(text), text)
                        self.assertFalse(any(sign in text for sign in BANNED_EMOJI), text)
                    self.assertEqual(e["emoji"], SIGN[kind(e["code"])], "the emoji names the cell and nothing more")
                    self.assertEqual(e["notation"], f"{position.turn}{e['code']}", "no + and no #")

    def test_the_words_say_where_the_mark_goes_and_nothing_more(self):
        for _, position, entries, _ in boards():
            last = len(entries) == 1
            for e in entries:
                where = {"Centre": "the centre"}.get(kind(e["code"]), "")
                if not where:
                    f, r = spot(e["code"])
                    if kind(e["code"]) == "Corner":
                        where = f"the {'upper' if r == 2 else 'lower'} {'left' if f == 0 else 'right'} corner"
                    else:
                        where = f"the {EDGES[(f, r)]} edge"
                self.assertEqual(e["words"], f"{position.turn} takes {where}" + (", the last cell" if last else ""))

    def test_a_win_and_a_quiet_move_of_one_kind_read_alike(self):
        """On every board where a mark of one kind wins on the spot and another of that kind does not, the two open
        alike, show one emoji, and say their words the same way; and no detail is kept for moves that win, nor for
        moves that hand the other side a win. (The lead is the board's: every move on it opens alike.)"""
        seen = {"wins": collections.Counter(), "gives": collections.Counter(), "quiet": collections.Counter()}
        pairs = 0
        for first, position, entries, double in boards():
            looks = {e["code"]: Look(position, e["code"]) for e in entries}
            read = {e["code"]: reading(bare(e, double[e["code"]])) for e in entries}
            for e in entries:
                look = looks[e["code"]]
                how = "wins" if look.wins() else "gives" if look.gives() else "quiet"
                seen[how].update(read[e["code"]].shapes()[1:])
            by_kind = collections.defaultdict(list)
            for e in entries:
                by_kind[kind(e["code"])].append(e)
            for same in by_kind.values():
                for a, b in itertools.combinations(same, 2):
                    if looks[a["code"]].wins() == looks[b["code"]].wins():
                        continue
                    pairs += 1
                    with self.subTest(first=first, board=position.board, cells=(a["code"], b["code"])):
                        self.assertEqual(read[a["code"]].form, read[b["code"]].form)
                        self.assertEqual(a["emoji"], b["emoji"])
                        self.assertEqual(a["words"].split(" takes ")[0], b["words"].split(" takes ")[0])
        self.assertGreater(pairs, 1000)
        for how in ("wins", "gives"):
            self.assertLessEqual(set(seen[how]), set(seen["quiet"]), f"a detail only moves that {how} use")

    def test_a_win_reads_like_the_quiet_corner_beside_it(self):
        named = {e["code"]: e for e in listing(board("XX./OO./..."), 1, 1)}  # c3 wins for X; a1 and c1 do nothing
        self.assertEqual([named[c]["emoji"] for c in ("c3", "a1", "c1")], ["📐"] * 3)
        forms = {reading(named[c]["title"]).form for c in ("c3", "a1", "c1")}
        self.assertEqual(len(forms), 1)
        self.assertEqual(named["c3"]["notation"], "Xc3")
        self.assertEqual(named["c3"]["words"], "X takes the upper right corner")
        self.assertEqual(named["a1"]["words"], "X takes the lower left corner")


class Boards(unittest.TestCase):
    """Every board of every game, either mark first, as the engine lists it."""

    def test_every_open_cell_is_listed_in_what_the_kit_accepts(self):
        for first, listed in LISTED.items():
            for position, entries in listed.items():
                self.assertEqual([e["code"] for e in entries], R.legal(position))
                for e in entries:
                    with self.subTest(first=first, board=position.board, cell=e["code"]):
                        self.assertEqual(set(e), {"code", "notation", "emoji", "title", "words"})
                        self.assertTrue(KIT_EMOJI.fullmatch(e["emoji"]))
                        self.assertTrue(KIT_TITLE.fullmatch(e["title"]) and len(e["title"]) <= LONGEST)
                        self.assertTrue(KIT_WORDS.fullmatch(e["words"]) and len(e["words"]) <= 80)
                        for dash in DASHES:
                            self.assertNotIn(dash, e["title"] + e["words"])

    def test_o_first_reads_as_x_first_with_the_marks_swapped(self):
        for position, entries in LISTED[R.O].items():
            mirror = R.Position.from_board(position.board.translate(SWAP))
            for e, x in zip(entries, LISTED[R.X][mirror], strict=True):
                self.assertEqual((e["code"], e["emoji"], e["title"]), (x["code"], x["emoji"], x["title"]))
                self.assertEqual((e["notation"], e["words"]),
                                 (x["notation"].translate(SWAP), x["words"].translate(SWAP)))

    def test_a_move_is_named_the_same_in_every_game_and_at_every_move(self):
        for text, first in (("X../.O./...", R.X), (".../.../O..", R.O), ("XO./.X./..O", R.X)):
            position = board(text, first)
            self.assertEqual(listing(position, 1, 3), listing(position, 7, 3))
            self.assertEqual(listing(position, 1, 3), listing(position, 2, 5))
            self.assertEqual(listing(position, 1, 3), listing(board(text, first), 9, 1))


class Examples(unittest.TestCase):
    """Boards as the profile shows them."""

    def entries(self, text: str, first: str = R.X) -> dict[str, dict]:
        return {e["code"]: e for e in listing(board(text, first), 1, 1)}

    def test_the_live_board_names_every_cell_for_where_it_is(self):
        named = self.entries(".../.../O..", R.O)  # the Arbiter opened for GitHub with O on a1: X to move
        self.assertEqual({c: (e["emoji"], e["title"]) for c, e in named.items()}, {
            "a3": ("📐", "Take a Corner Along From Theirs, Upper Left!"),
            "b3": ("📏", "Take an Edge by No Mark, Top!"),
            "c3": ("📐", "Take the Corner Across From Theirs!"),
            "a2": ("📏", "Take an Edge by Their Corner, Left!"),
            "b2": ("\U0001f533", "Take the Centre!"),
            "c2": ("📏", "Take an Edge by No Mark, Right!"),
            "b1": ("📏", "Take an Edge by Their Corner, Bottom!"),
            "c1": ("📐", "Take a Corner Along From Theirs, Lower Right!"),
        })
        self.assertEqual(named["b2"]["words"], "X takes the centre")
        self.assertEqual(named["c3"]["notation"], "Xc3")

    def test_the_first_mark_starts_the_game_and_says_no_more(self):
        for first in (R.X, R.O):
            named = self.entries(".../.../...", first)
            self.assertEqual(named["b2"]["title"], "Start in the Centre!")
            self.assertEqual(named["a3"]["title"], "Start in a Corner, Upper Left!")
            self.assertEqual(named["c1"]["title"], "Start in a Corner, Lower Right!")
            self.assertEqual(named["b1"]["title"], "Start on an Edge, Bottom!")
            self.assertEqual(named["c2"]["title"], "Start on an Edge, Right!")
            self.assertEqual(named["b2"]["words"], f"{first} takes the centre")

    def test_the_last_cell_says_so_and_no_more(self):
        named = self.entries("XOX/XOO/OX.")
        self.assertEqual(named["c1"]["words"], "X takes the lower right corner, the last cell")
        self.assertEqual(named["c1"]["emoji"], "📐")
        self.assertNotIn("draw", named["c1"]["title"].lower())


if __name__ == "__main__":
    unittest.main()
