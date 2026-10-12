# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Connect Four: discs fall, the two sides take turns, whichever colour drops first, four in a row wins
every way, and a full frame draws.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import connectfour_rules as R

DRAW = [int(c) for c in "467516245217422716242761435431776133653535"]  # forty-two discs and no four in a row


def drop(*columns: int, start: R.Position = R.START) -> R.Position:
    position = start
    for col in columns:
        assert col in R.legal(position), (col, position.board)
        position = R.make(position, col)
    return position


class Frame(unittest.TestCase):
    def test_dark_drops_first_and_a_disc_falls_to_the_foot(self):
        position = drop(4)
        self.assertEqual((position.at(4, 1), position.turn, position.last), (R.DARK, R.LIGHT, (4, 1)))
        position = drop(4, 4)
        self.assertEqual((position.at(4, 2), position.height(4), position.turn), (R.LIGHT, 2, R.DARK))
        self.assertEqual(position.board, "......./......./......./......./...L.../...D...")

    def test_light_drops_first_when_the_game_says_so(self):
        position = drop(4, start=R.opening(R.LIGHT))
        self.assertEqual((position.at(4, 1), position.turn, position.first), (R.LIGHT, R.DARK, R.LIGHT))
        position = drop(4, 3, start=R.opening(R.LIGHT))
        self.assertEqual((position.at(3, 1), position.turn), (R.DARK, R.LIGHT))
        self.assertEqual(position.board, "......./......./......./......./......./..DL...")
        self.assertEqual(R.Position.from_board(position.board, R.LIGHT), position)
        self.assertNotEqual(R.Position(position.cells), position, "the same discs with dark first is another position")

    def test_a_frame_is_read_and_written_top_row_first(self):
        text = "......./..D..../..LD.../..DD.../D.DLLL./L.DLDLL"
        self.assertEqual(R.Position.from_board(text).board, text)
        self.assertEqual((R.Position.from_board(text).at(3, 4), R.Position.from_board(text).at(1, 1)),
                         (R.LIGHT, R.LIGHT))
        short = "/".join(["......."] * 5 + ["......"])
        floating = "/".join(["...D..."] + ["......."] * 4 + ["......D"])
        doubled = "/".join(["......."] * 5 + ["DD....."])
        light_first = "/".join(["......."] * 5 + ["LL....."])
        for bad in (short, floating, doubled, light_first):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                R.Position.from_board(bad)
        one_light, one_dark = "/".join(["......."] * 5 + ["L......"]), "/".join(["......."] * 5 + ["D......"])
        self.assertEqual(R.Position.from_board(one_light, R.LIGHT).turn, R.DARK)
        for bad, first in ((one_dark, R.LIGHT), (one_light, R.DARK), (one_light, "X")):
            with self.subTest(bad=bad, first=first), self.assertRaises(ValueError):
                R.Position.from_board(bad, first)

    def test_a_full_column_takes_no_more(self):
        position = drop(4, 4, 4, 4, 4, 4)
        self.assertNotIn(4, R.legal(position))
        self.assertEqual(R.why_illegal(position, 4), "column 4 is full")
        self.assertEqual(R.legal(position), [1, 2, 3, 5, 6, 7])


class FourInARow(unittest.TestCase):
    def test_four_wins_up_across_and_on_both_diagonals(self):
        cases = {
            "up": ([4, 1, 4, 1, 4, 2, 4], ((4, 1), (4, 2), (4, 3), (4, 4))),
            "across": ([1, 1, 2, 2, 3, 3, 4], ((1, 1), (2, 1), (3, 1), (4, 1))),
            "rising": ([1, 2, 2, 3, 3, 4, 3, 4, 4, 7, 4], ((1, 1), (2, 2), (3, 3), (4, 4))),
            "falling": ([7, 6, 6, 5, 5, 4, 5, 4, 4, 1, 4], ((4, 4), (5, 3), (6, 2), (7, 1))),
        }
        for way, (columns, line) in cases.items():
            position = drop(*columns)
            end = R.ending(position)
            with self.subTest(way=way):
                self.assertEqual((end.winner, end.reason, end.line, end.result), (R.DARK, "four in a row", line, "0-1"))
                self.assertEqual(R.legal(position), [], "a won game has no move left")

    def test_light_wins_too_and_scores_first_as_white(self):
        end = R.ending(drop(1, 4, 1, 4, 2, 4, 7, 4))
        self.assertEqual((end.winner, end.line, end.result), (R.LIGHT, ((4, 1), (4, 2), (4, 3), (4, 4)), "1-0"))
        end = R.ending(drop(4, 1, 4, 1, 4, 2, 4, start=R.opening(R.LIGHT)))
        self.assertEqual((end.winner, end.line), (R.LIGHT, ((4, 1), (4, 2), (4, 3), (4, 4))),
                         "and when it dropped first")

    def test_five_in_a_row_names_four_with_the_last_disc(self):
        position = drop(1, 1, 2, 2, 4, 4, 5, 5, 3)  # the third disc joins two on each side: five across
        end = R.ending(position)
        self.assertEqual(len(end.line), 4)
        self.assertIn((3, 1), end.line)
        self.assertEqual(end.line, ((1, 1), (2, 1), (3, 1), (4, 1)))

    def test_a_full_frame_without_four_is_a_draw(self):
        position = drop(*DRAW)
        self.assertTrue(all(position.cells))
        self.assertEqual(R.ending(position), R.Ending(None, "a full frame"))
        self.assertEqual(R.ending(position).result, "1/2-1/2")
        for n in range(len(DRAW)):
            self.assertIsNone(R.ending(drop(*DRAW[:n])), "and nothing ended it sooner")

    def test_every_random_game_ends_at_its_first_four_or_its_full_frame(self):
        rng = random.Random(4)
        for n in range(200):
            position = R.opening(R.LIGHT if n % 2 else R.DARK)
            while not R.ending(position):
                position = R.make(position, rng.choice(R.legal(position)))
            end = R.ending(position)
            if end.winner:
                self.assertTrue(all(position.at(*cell) == end.winner for cell in end.line))
                self.assertIn(position.last, end.line, "the four hold the disc that made them")
            else:
                self.assertTrue(all(position.cells))


class Threats(unittest.TestCase):
    def test_a_threat_is_a_column_a_side_could_win_down_at_once(self):
        position = drop(4, 1, 4, 1, 4)
        self.assertEqual(R.threats(position, R.DARK), [4])
        self.assertEqual(R.threats(position, R.LIGHT), [])
        position = drop(1, 7, 2, 7, 3)  # three across the foot, open at 4
        self.assertEqual(R.threats(position, R.DARK), [4])

    def test_a_win_out_of_reach_is_not_a_threat_yet(self):
        # Dark has three rising from 1,1, and the fourth cell, 4,4, stands over an empty 4,3
        position = drop(1, 2, 2, 3, 3, 7, 3, 6)
        self.assertEqual(position.height(4), 0)
        self.assertNotIn(4, R.threats(position, R.DARK))

    def test_a_move_is_written_with_its_win_and_never_a_threat(self):
        self.assertEqual(R.notation(R.START, 4), "4")
        self.assertEqual(R.notation(drop(4, 1, 4, 1), 4), "4", "three up column 4, and the sheet doesn't say so")
        self.assertEqual(R.notation(drop(4, 1, 4, 1, 4, 2), 4), "4#")
        self.assertEqual(R.notation(drop(4, 1, 4, 1, 4), 4), "4")
        self.assertEqual(R.notation(drop(4, 1, 4, 1, start=R.opening(R.LIGHT)), 4), "4", "light first, the same")
        self.assertEqual(R.notation(drop(4, 1, 4, 1, 4, 2, start=R.opening(R.LIGHT)), 4), "4#")

    def test_every_drop_of_random_games_is_its_column_and_a_win_its_hash_alone(self):
        rng = random.Random(7)
        for game in range(300):
            position = R.opening(R.LIGHT) if game % 2 else R.START
            while not R.ending(position):
                for col in R.legal(position):
                    won = R.ending(R.make(position, col))
                    want = f"{col}{'#' if won and won.winner == position.turn else ''}"
                    self.assertEqual(R.notation(position, col), want, (position.board, col))
                position = R.make(position, rng.choice(R.legal(position)))


if __name__ == "__main__":
    unittest.main()
