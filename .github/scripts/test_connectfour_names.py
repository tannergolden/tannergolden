# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named for what its drop does in Connect Four: each reading checked against brute force on the
rules, both ways round (Black dropping first and White dropping first), and every board's titles and words held to
what the kit takes.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import functools
import random
import re
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import connectfour_names as N
import connectfour_rules as R
from connectfour_names import LONGEST, TITLES, WORDS, calls, kind, listing, opener, read, words

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
FIRSTS = (R.DARK, R.LIGHT)  # Black drops first, then White drops first
SIDE = {R.DARK: "Black", R.LIGHT: "White"}
SWAP = str.maketrans("DL", "LD")  # a frame with the colours the other way round
COLOURS = re.compile(r"\b(black|white|Black|White)\b")


def drop(columns: str, first: str = R.DARK) -> R.Position:
    """The position after the drops, `first` the colour that dropped first."""
    position = R.opening(first)
    for col in columns:
        position = R.make(position, int(col))
    return position


def frame(text: str, first: str = R.DARK) -> R.Position:
    """The position a frame of D, L and dots describes, `first` the colour that dropped first."""
    return R.Position.from_board(text, first)


def games(n: int, seed: int) -> list[R.Position]:
    """Every position of `n` games of seeded random play with a drop left to make, every other game White first."""
    rng, out = random.Random(seed), []
    for game in range(n):
        position = R.opening(FIRSTS[game % 2])
        while R.legal(position):
            out.append(position)
            after = R.make(position, rng.choice(R.legal(position)))
            position = after if type(after) is type(position) else type(position)(after.cells, after.last)
    return out


NAMED = {position: listing(position, 1, 1) for position in games(60, 5)}  # every board's names, once for every test
SAMPLE = [position for i, (position, named) in enumerate(NAMED.items())  # a third of them, and every one with a key
          if i % 3 == 0 or any(m["emoji"] == "🔑" for m in named)]  # checked by brute force


# --- brute force on the rules, cell by cell, with nothing of the names module's ------------------------------------
def height(cells: tuple[str, ...], col: int) -> int:
    return sum(1 for row in range(1, R.ROWS + 1) if cells[(row - 1) * R.COLS + col - 1])


def put(cells: tuple[str, ...], col: int, colour: str) -> tuple[tuple[str, ...], int]:
    """The frame with a disc of `colour` dropped down the column, and the row it lands on."""
    row, out = height(cells, col) + 1, list(cells)
    out[(row - 1) * R.COLS + col - 1] = colour
    return tuple(out), row


def completes(cells: tuple[str, ...], col: int, row: int, colour: str) -> bool:
    """Whether a disc of `colour` on the cell, wherever it stood, would connect four."""
    out = list(cells)
    out[(row - 1) * R.COLS + col - 1] = colour
    return bool(R.four(out, col, row))


def wins(cells: tuple[str, ...], colour: str) -> set[tuple[int, int]]:
    """The cells `colour` could drop on now and connect four."""
    return {(col, height(cells, col) + 1) for col in R.threats(R.Position(cells), colour)}


def forced(cells: tuple[str, ...], mover: str) -> bool:
    """Whether `mover`, having just dropped, wins on its next drop whatever the other side drops now."""
    foe, open_ = R.other(mover), [col for col in range(1, R.COLS + 1) if height(cells, col) < R.ROWS]
    return bool(open_) and not wins(cells, foe) and all(wins(put(cells, col, foe)[0], mover) for col in open_)


@functools.cache
def truth(position: R.Position, col: int) -> dict:
    """What the drop does, found by brute force: the facts each reading claims."""
    mover = position.turn
    foe, cells = R.other(mover), position.cells
    after, row = put(cells, col, mover)
    if R.four(after, col, row):
        return {"win": True}
    full = all(after)
    theirs, theirs_after = wins(cells, foe), (set() if full else wins(after, foe))
    out = {"win": False, "fills": full, "missed": tuple(sorted(c for c, _ in wins(cells, mover) if c != col)),
           "blocks": (col, row) in theirs, "leaves": tuple(sorted(c for c, _ in theirs_after & theirs)),
           "opens": tuple(sorted(c for c, _ in theirs_after - theirs)),
           "makes": tuple(sorted(c for c, _ in wins(after, mover))) if not full else (),
           "spends": row < R.ROWS and completes(cells, col, row + 1, mover)}
    out["forces"] = not full and not theirs_after and forced(after, mover)
    out["doomed"] = tuple(reply for reply in range(1, R.COLS + 1) if not (full or theirs_after or out["forces"])
                          and height(after, reply) < R.ROWS and forced(put(after, reply, foe)[0], foe))
    out["plants"] = tuple(sorted(((c, r) for c in range(1, R.COLS + 1) for r in range(height(after, c) + 2, R.ROWS + 1)
                                  if completes(after, c, r, mover) and not completes(cells, c, r, mover)),
                                 key=lambda cell: (cell[1], cell[0])))
    lowest = [all(not completes(after, c, k, side) for side in FIRSTS for k in range(height(after, c) + 1, r))
              for c, r in out["plants"]]
    first = opener(position) == mover
    out["strong"] = tuple(cell for cell, low in zip(out["plants"], lowest) if low and (cell[1] % 2 == 1) == first)
    return out


def losing(fact: dict) -> bool:
    """Whether the drop passes up a win, or lets the other side win on its next drop or by a double threat after."""
    return not fact["win"] and bool(fact["missed"] or fact["leaves"] or fact["opens"] or fact["doomed"])


# --- one position for every call: its drops, the column, and the words, `{m}` the mover's discs ----------------------
CASES = {
    "win across": ("164425", 3, "A {m} disc down column 3 connects four across row 1"),
    "win up": ("727474", 7, "A {m} disc down column 7 connects four up column 7"),
    "win diagonal": ("6534344653", 3, "A {m} disc down column 3 connects four on a diagonal"),
    "win twice": ("24234623665431", 2, "A {m} disc down column 2 connects four up column 2 and on a diagonal"),
    "missed": ("727474", 1, "A {m} disc down column 1, to row 1, passing up the win in column 7"),
    "block across": ("73536", 4, "A {m} disc down column 4 blocks on row 1"),
    "block up": ("72747", 7, "A {m} disc down column 7 blocks on row 4"),
    "block diagonal": ("4544375566", 4, "A {m} disc down column 4 blocks on row 4"),
    "block twice": ("2423462366543", 2, "A {m} disc down column 2 blocks on row 4"),
    "strike": ("27153", 4, "A {m} disc down column 4 blocks on row 1, threatening column 6"),
    "block double": ("6152233351", 4, "A {m} disc down column 4 blocks on row 1, threatening columns 4 and 7"),
    "block stacked": ("62553663555", 4, ("A {m} disc down column 4 blocks on row 1, threatening column 4 on rows"
                                         " 2 and 3")),
    "block triple": ("2543641354224", 3, "A {m} disc down column 3 blocks on row 3, threatening columns 2, 3 and 5"),
    "block squeeze": ("336772351766652312626171252353717515", 4, ("A {m} disc down column 4 blocks on row 1,"
                                                                  " leaving {F} no safe drop")),
    "block plant": ("2644252", 2, "A {m} disc down column 2 blocks on row 4, threatening row 3 of column 3"),
    "block plant odd": ("6674767", 7, "A {m} disc down column 7 blocks on row 4, threatening row 2 of column 5"),
    "block lost two": ("31435", 2, "A {m} disc down column 2 blocks on row 1, leaving column 6 to {F}"),
    "block lost trap": ("21263756321", 4, "A {m} disc down column 4 blocks on row 1, opening column 4 to {F}"),
    "block doomed": ("3326272", 2, "A {m} disc down column 2 blocks on row 4, giving {F} a double threat"),
    "block draw": ("46322514114254632744122155365167537663737", 7, ("A {m} disc down column 7 blocks on row 6,"
                                                                     " filling the frame for a draw")),
    "draw": ("16324626147173444562435616551155333722277", 7, ("A {m} disc down column 7, to row 6, filling the"
                                                              " frame for a draw")),
    "double": ("4633", 2, "A {m} disc down column 2, to row 1, threatening columns 1 and 5"),
    "triple": ("7665525634", 4, "A {m} disc down column 4, to row 2, threatening columns 3, 6 and 7"),
    "stacked": ("4361416434", 7, "A {m} disc down column 7, to row 1, threatening column 5 on rows 1 and 2"),
    "squeeze": ("55127611317553721167337722336552266", 6, ("A {m} disc down column 6, to row 6, leaving {F} no"
                                                           " safe drop")),
    "ignore": ("73536", 1, "A {m} disc down column 1, to row 1, leaving column 4 to {F}"),
    "under": ("3231221", 4, "A {m} disc down column 4, to row 1, opening column 4 to {F}"),
    "spend": ("32312212", 4, "A {m} disc down column 4, to row 1, spending {M}'s threat on row 2"),
    "only": ("4612433114331", 4, "A {m} disc down column 4, to row 4, where every other drop loses"),
    "doomed": ("274", 2, "A {m} disc down column 2, to row 2, giving {F} a double threat in column 3"),
    "threat": ("5527", 3, "A {m} disc down column 3, to row 1, threatening column 4"),
    "plant": ("436556", 6, "A {m} disc down column 6, to row 3, threatening row 4 of column 7"),
    "plant odd": ("477557", 7, "A {m} disc down column 7, to row 4, threatening row 3 of column 6"),
    "plant two": ("565442", 6, "A {m} disc down column 6, to row 2, setting two threats"),
    "plant two odd": ("3455541", 3, "A {m} disc down column 3, to row 2, setting two threats"),
    "top": ("44444", 4, "A {m} disc down column 4, to row 6, filling the column"),
    "stack": ("25", 2, "A {m} disc down column 2, to row 2"),
    "cap": ("2", 2, "A {m} disc down column 2, to row 2"),
    "cap two": ("232", 2, "A {m} disc down column 2, to row 3"),
    "opening centre": ("", 4, "A {m} disc down column 4, to row 1"),
    "opening edge": ("", 1, "A {m} disc down column 1, to row 1"),
    "opening": ("", 2, "A {m} disc down column 2, to row 1"),
    "centre": ("2", 4, "A {m} disc down column 4, to row 1"),
    "edge": ("2", 1, "A {m} disc down column 1, to row 1"),
    "open": ("2", 6, "A {m} disc down column 6, to row 1"),
    "open near": ("2", 3, "A {m} disc down column 3, to row 1"),
}
THRICE = "....D../..L.DL./..D.LLL/.LLLDDD/.LDLDDL/LDDLDDD"  # Black first, and White's 4 connects four three ways
BLOCKS = "....D.D/....DLL/..L.LLL/..LLDDD/DLDLDLD/LDLLDDD"  # Black first, and Black's 4 blocks White's three fours


def spoken(text: str, position: R.Position) -> str:
    mover = position.turn
    return text.format(m=SIDE[mover].lower(), M=SIDE[mover], F=SIDE[R.other(mover)])


class Readings(unittest.TestCase):
    def test_every_call_has_a_drop_that_takes_it_and_says_so_both_ways_round(self):
        self.assertEqual(set(CASES) | {"win thrice", "block thrice"}, set(TITLES))
        for want, (line, col, text) in CASES.items():
            for first in FIRSTS:
                with self.subTest(call=want, first=SIDE[first]):
                    position = drop(line, first)
                    self.assertIn(col, R.legal(position))
                    self.assertEqual(calls(read(position, col)), want)
                    self.assertEqual(words(position, col), spoken(text, position))

    def test_a_drop_that_connects_or_blocks_four_three_ways_names_them_all(self):
        for first, text in ((R.DARK, THRICE), (R.LIGHT, THRICE.translate(SWAP))):
            position = frame(text, first)
            self.assertEqual(calls(read(position, 4)), "win thrice")
            self.assertEqual(words(position, 4), spoken("A {m} disc down column 4 connects four up, across row 4 and"
                                                        " on a diagonal", position))
        for first, text in ((R.DARK, BLOCKS), (R.LIGHT, BLOCKS.translate(SWAP))):
            position = frame(text, first)
            self.assertEqual((calls(read(position, 4)), read(position, 4).blocks), ("block thrice",
                                                                                   ("across", "up", "rising")))
            named = {m["code"]: m for m in listing(position, 1, 1)}
            self.assertEqual((named["4"]["emoji"], named["4"]["words"]),
                             ("🛡️", spoken("A {m} disc down column 4 blocks on row 4", position)))
            self.assertIn("Three", named["4"]["title"])

    def test_every_reading_has_calls_that_fit_whatever_it_holds(self):
        ways = [tuple(name for i, name in enumerate(N.LINES) if bits >> i & 1) for bits in range(1, 16)]
        base = N.Reading(R.LIGHT, 4, 2, opener=True)
        plants = [{"plants": ((6, 3),), "marked": (6, 3)},
                  {"plants": ((6, 3),), "strong": ((6, 3),), "parity": "odd", "marked": (6, 3)},
                  {"plants": ((6, 3), (5, 5)), "marked": (6, 3)},
                  {"plants": ((6, 3), (5, 5)), "strong": ((6, 3), (5, 5)), "parity": "odd", "marked": (6, 3)}]
        forced = [{"forces": "double", "makes": (2, 6), "aims": ((2, 1), (6, 2))},
                  {"forces": "double", "makes": (1, 2, 6), "aims": ((1, 1), (2, 1), (6, 2))},
                  {"forces": "stacked", "makes": (5,), "aims": ((5, 2),)}, {"forces": "squeeze"}]
        tails = [{}, {"fills": True}, {"leaves": (3,)}, {"opens": (4,)}, {"leaves": (3, 6), "opens": (4,)},
                 {"doomed": (3,)}, {"doomed": (1, 3, 6)}, {"only": True}, {"spends": True, "makes": (4,),
                                                                           "aims": ((4, 3),)},
                 {"makes": (5,), "aims": ((5, 1),), "aimed": ("across",)}, *forced, *plants]
        readings = [N.Reading(R.DARK, col, 1, first=True) for col in range(1, 8)]
        readings += [replace(base, wins=lines) for lines in ways]
        readings += [replace(base, missed=missed, **tail) for missed in ((3,), (3, 5)) for tail in tails]
        readings += [replace(base, blocks=lines, **tail) for lines in ways for tail in tails]
        readings += [replace(base, **tail) for tail in tails]
        readings += [replace(base, col=col, row=row, below=below, run=run) for col in range(1, 8) for row in (1, 3, 6)
                     for below, run in (("", 0), ("own", 1), ("theirs", 1), ("theirs", 2)) if (row == 1) == (not below)]
        for r in readings:
            with self.subTest(reading=r):
                self.assertIn(calls(r), TITLES)
                emoji, name, call = N.title(R.START, r, set())
                self.assertIn(call, TITLES[calls(r)])
                self.assertTrue(KIT_EMOJI.fullmatch(emoji) and KIT_TITLE.fullmatch(name), (emoji, name))
                self.assertTrue(KIT_WORDS.fullmatch(N.said(r)), N.said(r))

    def test_every_reading_is_true_by_brute_force_both_ways_round(self):
        checked = 0
        for position in SAMPLE:
            for col in R.legal(position):
                facts, r = truth(position, col), read(position, col)
                with self.subTest(board=position.board, first=SIDE[opener(position)], col=col):
                    self.assertEqual(r.colour, position.turn)
                    self.assertEqual(bool(r.wins), facts["win"])
                    if facts["win"]:
                        self.assertEqual(R.ending(R.make(position, col)).winner, position.turn)
                        continue
                    for name in ("fills", "missed", "leaves", "opens", "makes", "spends", "doomed", "plants",
                                 "strong"):
                        self.assertEqual(getattr(r, name), facts[name], name)
                    self.assertEqual(bool(r.blocks), facts["blocks"])
                    self.assertEqual(bool(r.forces), facts["forces"])
                    self.assertEqual(r.parity, ("odd" if r.opener else "even") if facts["strong"] else "")
                    checked += 1
        self.assertGreater(checked, 2000)

    def test_a_threat_is_called_odd_or_even_only_when_its_row_is_the_mover_s_kind(self):
        cases = {  # the drops, the column, the call, and the row of the threat it plants
            "477557": (7, "plant odd", "Odd", 3),  # the side that dropped first, on an odd row
            "24223": (3, "plant odd", "Even", 4),  # the other side, on an even row
            "233111": (2, "plant", "", 2),  # the side that dropped first, on an even row: the other side's kind
            "2442413": (4, "plant", "", 3),  # the other side, on an odd row: the first side's kind
            "431355143": (5, "plant", "", 4),  # the mover's kind, but over its own threat in that column
        }
        for line, (col, want, parity, row) in cases.items():
            for first in FIRSTS:
                with self.subTest(line=line, first=SIDE[first]):
                    position = drop(line, first)
                    r = read(position, col)
                    self.assertEqual((calls(r), r.parity.capitalize(), r.marked[1]), (want, parity, row))
                    name = next(m["title"] for m in listing(position, 1, 1) if m["code"] == str(col))
                    self.assertEqual(bool(re.search(r"\b(Odd|Even)\b", name)), bool(parity), name)
                    if parity:
                        self.assertIn(parity, name)

    def test_who_dropped_first_is_read_from_the_position(self):
        for first in FIRSTS:
            for line in ("", "4", "45", "453"):
                with self.subTest(first=SIDE[first], line=line):
                    position = drop(line, first)
                    self.assertEqual(opener(position), first)
                    self.assertEqual(read(position, 1).opener, position.turn == first)

    def test_a_drop_that_loses_is_warned_of_before_anything_else_it_does(self):
        position = drop("4612433114331")  # down 5 spends White's threat on row 2, and Black's block of it on row 2
        # sets a double threat
        r = read(position, 5)
        self.assertTrue(r.spends and r.doomed)
        self.assertEqual((kind(r), next(m["emoji"] for m in listing(position, 1, 1) if m["code"] == "5")),
                         ("doomed", "⚠️"))

    def test_a_block_that_cannot_save_the_game_says_so(self):
        position = drop("31435")  # Black's three across row 1 is open at both ends
        named = {int(m["code"]): m for m in listing(position, 1, 1)}
        for col in (2, 6):
            self.assertEqual((kind(read(position, col)), named[col]["emoji"]), ("block lost", "⚠️"))
            self.assertTrue(named[col]["words"].startswith(f"A white disc down column {col} blocks on row 1, leaving"))


class Titles(unittest.TestCase):
    def test_every_board_names_every_open_column_once_in_what_the_kit_accepts(self):
        for position, named in NAMED.items():
            self.assertEqual([m["code"] for m in named], [str(c) for c in R.legal(position)])
            self.assertEqual(len({m["title"] for m in named}), len(named), position.board)
            for m in named:
                self.assertTrue(KIT_EMOJI.fullmatch(m["emoji"]), m)
                self.assertTrue(KIT_TITLE.fullmatch(m["title"]), m)
                self.assertTrue(KIT_WORDS.fullmatch(m["words"]), m)
                self.assertLessEqual((len(m["title"]), len(m["words"])), (LONGEST, WORDS), m)
                self.assertEqual(m["notation"], R.notation(position, int(m["code"])))
                self.assertFalse(m["title"].startswith("Drop Down Column"), "a call stands in for every taken one")

    def test_a_title_is_a_call_and_the_words_say_white_and_black(self):
        for position, named in NAMED.items():
            mover = SIDE[position.turn].lower()
            for m in named:
                self.assertTrue(m["title"].endswith("!"), m["title"])
                self.assertRegex(m["words"], rf"^A {mover} disc down column {m['code']}( |,)")
                for text in (m["title"], m["words"]):
                    self.assertNotRegex(text.lower(), r"\b(dark|light)\b")
                    for dash in DASHES:
                        self.assertNotIn(dash, text)

    def test_the_same_position_and_drop_always_get_the_same_name(self):
        for position in list(NAMED)[::40]:
            once = listing(position, 1, 1)
            self.assertEqual(listing(position, 7, 30), once, "the game and the move number name nothing")
            N._listing.cache_clear()
            self.assertEqual(listing(position, 1, 1), once)
        pinned = {("", R.DARK): "Open Dead Centre!", ("", R.LIGHT): "Open Dead Centre!",
                  ("4633", R.DARK): "Strike Twice, Columns 1 and 5!",
                  ("274", R.LIGHT): "Open the Door to a Double Threat!"}
        for (line, first), title in pinned.items():
            position = drop(line, first)
            col = {"": 4, "4633": 2, "274": 2}[line]
            self.assertEqual(listing(position, 1, 1)[R.legal(position).index(col)]["title"], title)

    def test_the_same_drop_on_the_same_frame_is_called_the_same_whichever_colour_drops_it(self):
        for line in ("", "4", "4633", "274", "73536", "6152233351", "477557"):
            black, white = (listing(drop(line, first), 1, 1) for first in FIRSTS)
            for b, w in zip(black, white):
                self.assertEqual(b["emoji"], w["emoji"])
                for field in ("title", "words"):  # the same, but for the colours they name
                    self.assertEqual(COLOURS.sub("_", b[field]), COLOURS.sub("_", w[field]))

    def test_every_call_has_room_and_enough_others_to_stand_in_for_it(self):
        longest = {"row": 6, "col": 7, "column": "the Centre Column", "in_place": "on the Right Edge", "foe": "White",
                   "edge": "Right", "diagonal": "Falling Diagonal", "along": "Across Row 6 and on the Diagonal",
                   "won": "Columns 1, 2 and 3", "threat": "Columns 1, 2 and 3", "doom": "Columns 1, 2 and 3",
                   "aim": 7, "arow": 5, "atop": 6, "above": 6, "under": 5, "aims": "Columns 1, 2 and 3",
                   "aimed": "Across Row 6 and on the Diagonal", "ways": "Three", "parity": "Even", "prow": 6, "pcol": 7}
        for key, options in TITLES.items():
            fits = [option for option in options if len(option.format(**longest)) <= LONGEST]
            with self.subTest(call=key):
                self.assertGreaterEqual(len(fits), 1 if "draw" in key else 7, fits)
                self.assertEqual(len(set(options)), len(options))
                for option in fits:
                    self.assertTrue(KIT_TITLE.fullmatch(option.format(**longest)), option)
                    self.assertTrue(option.endswith("!"), option)

    def test_a_warning_marks_the_drops_that_lose_or_pass_up_the_win_and_a_key_the_only_one_that_does_not(self):
        warned = keys = 0
        for position in SAMPLE:
            facts = {int(m["code"]): truth(position, int(m["code"])) for m in NAMED[position]}
            holding = [col for col, fact in facts.items() if not losing(fact)]
            calm = not any(fact["win"] or fact["blocks"] for fact in facts.values())
            for m in NAMED[position]:
                col, fact = int(m["code"]), facts[int(m["code"])]
                bad = losing(fact)
                key = len(facts) > 1 and calm and holding == [col] and not (fact["forces"] or fact["fills"])
                with self.subTest(board=position.board, col=col):
                    self.assertEqual(m["emoji"] == "⚠️", bad, m)
                    self.assertEqual(m["emoji"] == "🔑", key, m)
                    if key:
                        self.assertTrue(m["words"].endswith(", where every other drop loses"), m)
                warned, keys = warned + bad, keys + key
        self.assertGreater(warned, 300)
        self.assertGreater(keys, 1)

    def test_a_win_is_named_for_its_line_and_marked_as_the_win(self):
        for position, named in NAMED.items():
            for m in named:
                r = read(position, int(m["code"]))
                self.assertEqual(bool(r.wins), m["notation"].endswith("#"), m)
                self.assertEqual(m["emoji"] == "🏆", bool(r.wins), m)
                if 0 < len(r.wins) < 3:  # three ways at once say how many, and the words name them
                    for line in r.wins:
                        self.assertIn({"across": f"Row {r.row}", "up": f"Column {r.col}", "rising": "Diagonal",
                                       "falling": "Diagonal"}[line], m["title"])

    def test_only_a_threat_planted_on_the_mover_s_kind_of_row_is_called_odd_or_even(self):
        for position, named in NAMED.items():
            for m in named:
                r = read(position, int(m["code"]))
                if re.search(r"\b(Odd|Even)\b", m["title"]):
                    self.assertTrue(r.strong, m)
                    self.assertIn("Odd" if r.opener else "Even", m["title"])


if __name__ == "__main__":
    unittest.main()
