# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named as a call across a duel: what a move is read as, its title and words, and that a board
keeps them, in every position the game can reach.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tictactoe_rules as R
from tictactoe_names import THEMES, listing, read, theme, words

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]


def positions() -> list[R.Position]:
    """Every position the game can reach with a move left to make."""
    seen, todo = set(), [R.START]
    while todo:
        position = todo.pop()
        if position.marks in seen:
            continue
        seen.add(position.marks)
        todo += [R.make(position, cell) for cell in R.legal(position)]
    return [R.Position(marks) for marks in sorted(seen) if R.legal(R.Position(marks))]


EVERY = positions()
NAMED = {position: listing(position, 1, 1) for position in EVERY}  # every board's names, once for every test here


# A board for each theme, with the cell whose move has it, and its words.
CASES = {
    "win": ("OOX/..X/...", "c1", "X takes c1, three in a row from c1 to c3"),
    "riposte": ("XX./..O/...", "c3", "O blocks on c3, threatening c1"),
    "block": (".XX/..O/...", "a3", "O blocks on a3"),
    "blunder": (".XX/..O/...", "a2", "O takes the left edge, threatening b2, leaving a3 to X"),
    "fork": ("OXX/..O/...", "b2", "X takes the centre, threatening a1 and b1"),
    "threat": (".OX/.../...", "b2", "X takes the centre, threatening a1"),
    "centre": (".../.../...", "b2", "X takes the centre"),
    "corner": (".../.../...", "a3", "X takes the upper left corner"),
    "edge": (".../.../...", "b3", "X takes the head of the board"),
}


class Reading(unittest.TestCase):
    def test_a_move_is_named_for_the_most_telling_thing_it_does(self):
        for want, (board, cell, _) in CASES.items():
            with self.subTest(theme=want):
                position = R.Position.from_board(board)
                self.assertIn(cell, R.legal(position))
                self.assertEqual(theme(read(position, cell)), want)

    def test_its_words_say_what_it_does(self):
        for want, (board, cell, said) in CASES.items():
            with self.subTest(theme=want):
                self.assertEqual(words(R.Position.from_board(board), cell), said)
        self.assertEqual(words(R.Position.from_board("X.X/.O./X.O"), "b1"),
                         "O takes the foot of the board, threatening b3, leaving b3 and a2 to X",
                         "a fork it can't stop, and a threat of its own on one of the two")


class Titles(unittest.TestCase):
    def test_every_board_names_every_open_cell_once_in_what_the_kit_accepts(self):
        for position, named in NAMED.items():
            self.assertEqual([m["code"] for m in named], R.legal(position))
            self.assertEqual(len({m["title"] for m in named}), len(named), position.board)
            for m in named:
                self.assertTrue(KIT_EMOJI.fullmatch(m["emoji"]), m)
                self.assertTrue(KIT_TITLE.fullmatch(m["title"]), m)
                self.assertTrue(KIT_WORDS.fullmatch(m["words"]), m)
                self.assertEqual(m["notation"], R.notation(position, m["code"]))

    def test_every_title_is_a_call_that_never_names_a_cell(self):
        for named in NAMED.values():
            for m in named:
                self.assertTrue(m["title"].endswith("!"), m["title"])
                self.assertNotRegex(m["title"], r"\b[a-c][1-3]\b")
                for dash in DASHES:
                    self.assertNotIn(dash, m["title"] + m["words"])

    def test_a_blunder_is_named_as_one_and_only_a_blunder_is(self):
        blunders = 0
        for position, named in NAMED.items():
            threatened = R.threats(position, R.other(position.turn))
            for m in named:
                after = R.make(position, m["code"])
                won = R.ending(after) and R.ending(after).winner
                leaves = not won and m["code"] not in threatened and R.threats(after, R.other(position.turn))
                self.assertEqual(m["emoji"] == "⚠️", bool(leaves), (position.board, m))
                blunders += bool(leaves)
                if won:
                    self.assertEqual(m["emoji"], "🏆")
                    self.assertTrue(m["notation"].endswith("#"))
        self.assertGreater(blunders, 1000)

    def test_a_board_is_named_the_same_every_time_and_another_game_differently(self):
        position = R.Position.from_board(".../.X./...")
        self.assertEqual(listing(position, 1, 2), listing(position, 1, 2))
        first = [m["title"] for m in listing(position, 1, 2)]
        later = [m["title"] for m in listing(position, 2, 2)]
        self.assertGreater(sum(a != b for a, b in zip(first, later)), len(first) // 3)

    def test_the_calls_run_wide(self):
        seen = {m["title"] for named in NAMED.values() for m in named}
        fixed = {call for _, calls in THEMES.values() for call in calls}
        self.assertGreater(len(seen), len(fixed), "the duelist's name makes more calls than the fixed ones")


if __name__ == "__main__":
    unittest.main()
