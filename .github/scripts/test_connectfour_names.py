# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named as an order to the airborne: what a drop is read as, its title and words, and that a
board keeps them, in every position of many games.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import connectfour_rules as R
from connectfour_names import THEMES, listing, read, theme, words

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]


def drop(columns: str) -> R.Position:
    position = R.START
    for col in columns:
        position = R.make(position, int(col))
    return position


def frames(n: int = 60, seed: int = 5) -> list[R.Position]:
    """Every position of `n` games of seeded random play, with a drop left to make."""
    rng, out = random.Random(seed), []
    for _ in range(n):
        position = R.START
        while R.legal(position):
            out.append(position)
            position = R.make(position, rng.choice(R.legal(position)))
    return out


NAMED = {position: listing(position, 1, 1) for position in frames()}  # every board's names, once for every test


# A line for each theme, the column whose drop has it, and the drop's words.
CASES = {
    "win": ("536376", 4, "A dark disc down column 4 connects four across row 1"),
    "counter": ("16253", 4, "A light disc down column 4 blocks on row 1, threatening column 7"),
    "block": ("53637", 4, "A light disc down column 4 blocks on row 1"),
    "blunder": ("53637", 1, "A light disc down column 1, to row 1, leaving column 4 to Dark"),
    "crossfire": ("77444676", 5, "A dark disc down column 5, to row 1, opening column 5 to Light"),
    "fork": ("4436", 2, "A dark disc down column 2, to row 1, threatening columns 1 and 5"),
    "threat": ("5363", 4, "A dark disc down column 4, to row 1, threatening column 7"),
    "first": ("", 1, "A dark disc down column 1, to row 1"),
    "centre": ("5", 4, "A light disc down column 4, to row 1"),
    "edge": ("5", 1, "A light disc down column 1, to row 1"),
    "stack": ("53", 5, "A dark disc down column 5, to row 2"),
    "drop": ("5", 2, "A light disc down column 2, to row 1"),
}


class Reading(unittest.TestCase):
    def test_a_drop_is_named_for_the_most_telling_thing_it_does(self):
        for want, (line, col, _) in CASES.items():
            with self.subTest(theme=want):
                position = drop(line)
                self.assertIn(col, R.legal(position))
                self.assertEqual(theme(read(position, col)), want)

    def test_its_words_say_what_it_does(self):
        for want, (line, col, said) in CASES.items():
            with self.subTest(theme=want):
                self.assertEqual(words(drop(line), col), said)
        self.assertEqual(words(drop("4141"), 4), "A dark disc down column 4, to row 3, threatening column 4")

    def test_words_too_long_for_the_kit_keep_the_warning(self):
        for position, named in NAMED.items():
            for m in named:
                self.assertLessEqual(len(m["words"]), 80)
                r = read(position, int(m["code"]))
                if (r.leaves or r.opens) and not r.blocks and not r.wins:
                    self.assertRegex(m["words"], r", (leaving|opening) columns? ")


class Titles(unittest.TestCase):
    def test_every_board_names_every_open_column_once_in_what_the_kit_accepts(self):
        for position, named in NAMED.items():
            self.assertEqual([m["code"] for m in named], [str(c) for c in R.legal(position)])
            self.assertEqual(len({m["title"] for m in named}), len(named), position.board)
            for m in named:
                self.assertTrue(KIT_EMOJI.fullmatch(m["emoji"]), m)
                self.assertTrue(KIT_TITLE.fullmatch(m["title"]), m)
                self.assertTrue(KIT_WORDS.fullmatch(m["words"]), m)
                self.assertEqual(m["notation"], R.notation(position, int(m["code"])))

    def test_every_title_is_an_order_that_never_names_a_column(self):
        for named in NAMED.values():
            for m in named:
                self.assertTrue(m["title"].endswith("!"), m["title"])
                self.assertNotRegex(m["title"], r"[0-9]")
                for dash in DASHES:
                    self.assertNotIn(dash, m["title"] + m["words"])

    def test_a_blunder_is_named_as_one_and_only_a_blunder_is(self):
        blunders = 0
        for position, named in NAMED.items():
            foe = R.other(position.turn)
            before = R.threats(position, foe)
            for m in named:
                col = int(m["code"])
                after = R.make(position, col)
                won = R.ending(after) and R.ending(after).winner
                bad = not won and col not in before and bool(R.threats(after, foe))
                self.assertEqual(m["emoji"] == "⚠️", bad, (position.board, m))
                blunders += bad
                if won:
                    self.assertEqual((m["emoji"], m["notation"][-1]), ("🏆", "#"))
        self.assertGreater(blunders, 200)

    def test_a_board_is_named_the_same_every_time_and_another_game_differently(self):
        position = drop("4")
        self.assertEqual(listing(position, 1, 2), listing(position, 1, 2))
        first = [m["title"] for m in listing(position, 1, 2)]
        later = [m["title"] for m in listing(position, 2, 2)]
        self.assertGreater(sum(a != b for a, b in zip(first, later)), len(first) // 3)

    def test_the_orders_run_wide(self):
        seen = {m["title"] for named in NAMED.values() for m in named}
        fixed = {order for _, orders in THEMES.values() for order in orders}
        self.assertGreater(len(seen), len(fixed), "the troops called by name make more orders than the fixed ones")


if __name__ == "__main__":
    unittest.main()
