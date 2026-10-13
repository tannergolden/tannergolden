# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every empty hole named for where its marble goes and for nothing the move would do: each hole listed once, its eight
turns after it, the title and words from the hole and its quarter, each of the 36 titles its own, and a whole move
named once it is made, its turn said in full. A ghost's hole is named the same way, for the hole it stands in.

  python3 -m unittest discover -s .github/scripts -p 'test_pentago*.py'

The names are worked out here a second way, from the hole's file and rank
alone, and held to what tannergolden/markdown takes for a move's emoji, title
and words.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pentago
import pentago_rules as R
from pentago_names import entry, ghost_listing, listing

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py,
# whose checks every game's moves share).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,98}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
# Each hole's place in its quarter, read top row first, and each quarter's on the board.
SPOTS = ("upper left corner", "top edge", "upper right corner", "left edge", "centre", "right edge",
         "lower left corner", "bottom edge", "lower right corner")
QUARTERS = ("upper left", "upper right", "lower left", "lower right")
# The order every hole's eight turns come in: each quarter, the upper left first, clockwise then anticlockwise.
ORDER = [("ul", "cw"), ("ul", "acw"), ("ur", "cw"), ("ur", "acw"), ("ll", "cw"), ("ll", "acw"), ("lr", "cw"),
         ("lr", "acw")]
SMALL = {"the", "of"}  # the words a title keeps in lower case
# What no name may say: a verdict, or what the move does to the game.
JUDGED = ("good", "bad", "safe", "strong", "weak", "best", "only", "win", "wins", "winning", "won", "lose", "loses",
          "lost", "draw", "draws", "drawn", "save", "saves", "block", "blocks", "threat", "threatens", "fork", "trap",
          "force", "forced", "blunder", "mistake", "attack", "defend", "guard", "next", "leaves", "lets", "five",
          "four", "row", "line", "both", "full", "must")
BANNED = re.compile(rf"\b(?:{'|'.join(JUDGED)})\b", re.IGNORECASE)


def place(cell: str) -> tuple[str, str]:
    """A hole's place in its quarter and its quarter's on the board, in words, from its file and rank alone."""
    x, y = "abcdef".index(cell[0]), int(cell[1]) - 1
    return SPOTS[(2 - y % 3) * 3 + x % 3], QUARTERS[(1 - y // 3) * 2 + x // 3]


def capitals(text: str) -> str:
    return " ".join(word if word in SMALL else word[0].upper() + word[1:] for word in text.split())


def expected(colour: str, cell: str) -> dict:
    """What the listing names a hole for the colour to move, worked out from the hole alone."""
    spot, quarter = place(cell)
    return {"code": cell, "notation": cell, "emoji": {R.W: "⚪", R.B: "⚫"}[colour],
            "title": capitals(f"take the {spot} of the {quarter} quarter!"),
            "words": f"A {'white' if colour == R.W else 'black'} marble on {cell}, then a quarter turns",
            "turns": [(q, w, f"{cell}-{q}-{w}") for q, w in ORDER]}


def boards(n: int, seed: int) -> list[R.Position]:
    """Every position with a move to make in `n` games of seeded random play, either colour first, under two ghosts."""
    rng, out = random.Random(seed), []
    for game in range(n):
        position = R.opening(R.B if game % 2 else R.W, rng.sample(R.CELLS, 2))
        while R.legal(position):
            out.append(position)
            position = R.make(position, rng.choice(R.legal(position)))
    return out


BOARDS = boards(60, 5)


class Listing(unittest.TestCase):
    def test_every_empty_hole_is_listed_once_as_the_board_is_read_with_its_eight_turns(self):
        for position in BOARDS:
            listed = listing(position, 1, 3)
            self.assertEqual([row["code"] for row in listed], R.empty(position))
            self.assertEqual([code for row in listed for _, _, code in row["turns"]], R.legal(position),
                             "every legal move once, in the order the rules list them")
            for row in listed:
                self.assertEqual([(q, w) for q, w, _ in row["turns"]], ORDER)

    def test_a_hole_is_named_for_its_place_in_its_quarter(self):
        named = {row["code"]: row for row in listing(R.opening(R.W, ("e5", "e2")), 1, 3)}
        self.assertEqual(named["b5"], {"code": "b5", "notation": "b5", "emoji": "⚪",
                                       "title": "Take the Centre of the Upper Left Quarter!",
                                       "words": "A white marble on b5, then a quarter turns",
                                       "turns": [(q, w, f"b5-{q}-{w}") for q, w in ORDER]})
        self.assertEqual(named["e4"]["title"], "Take the Bottom Edge of the Upper Right Quarter!")
        self.assertEqual(named["a1"]["title"], "Take the Lower Left Corner of the Lower Left Quarter!")
        self.assertEqual(named["f3"]["title"], "Take the Upper Right Corner of the Lower Right Quarter!")
        black = listing(R.opening(R.B, ()), 1, 3)[0]
        self.assertEqual((black["emoji"], black["words"]), ("⚫", "A black marble on a6, then a quarter turns"))

    def test_every_name_on_many_boards_is_the_hole_s_own_and_no_more(self):
        for position in BOARDS:
            for row in listing(position, 1, 3):
                self.assertEqual(row, expected(position.turn, row["code"]), position.board)

    def test_each_of_the_36_holes_has_a_title_of_its_own_in_what_the_kit_takes(self):
        named = listing(R.opening(R.W), 1, 1)
        self.assertEqual(len({row["title"] for row in named}), 36)
        for row in named:
            with self.subTest(code=row["code"]):
                self.assertRegex(row["emoji"], KIT_EMOJI)
                self.assertTrue(KIT_TITLE.fullmatch(row["title"]) and row["title"].endswith("!"), row)
                self.assertTrue(KIT_WORDS.fullmatch(row["words"]), row)
                self.assertEqual(capitals(row["title"]), row["title"], "every word capitalized but the and of")
                for dash in DASHES:
                    self.assertNotIn(dash, row["title"] + row["words"])

    def test_the_game_and_the_move_number_change_nothing(self):
        for position in BOARDS[:100]:
            self.assertEqual(listing(position, 1, 3), listing(position, 52, 31))

    def test_a_hole_whose_move_would_win_reads_as_any_other(self):
        # White's a5 would make five on its own: the hole is listed as it is on an empty board.
        position = R.Position(tuple(R.W if cell in ("a1", "a2", "a3", "a4") else
                                    R.B if cell in ("d6", "e6", "f6", "d5") else "" for cell in R.CELLS))
        self.assertTrue(R.won_unturned(position, "a5-lr-cw"))
        self.assertEqual(next(row for row in listing(position, 1, 11) if row["code"] == "a5"), expected(R.W, "a5"))

    def test_no_name_judges_or_says_what_the_move_would_do(self):
        for position in BOARDS[::9]:
            for row in listing(position, 1, 3):
                for field in ("emoji", "title", "notation", "words"):
                    self.assertNotRegex(row[field], BANNED, row)
                self.assertFalse(row["notation"].endswith(("+", "#")), row)

    def test_a_finished_game_lists_nothing(self):
        won = R.Position(tuple(R.W if cell in ("a1", "a2", "a3", "a4", "a5") else "" for cell in R.CELLS))
        self.assertTrue(R.ending(won))
        self.assertEqual(listing(won, 1, 11), [])

    def test_the_engine_lists_the_names_module_s_own(self):
        self.assertEqual(pentago.listing(BOARDS[40], 1, 3), listing(BOARDS[40], 1, 3))


class Entry(unittest.TestCase):
    def test_a_move_made_is_named_with_its_turn_in_full(self):
        start = R.opening(R.W, ("e5", "e2"))
        self.assertEqual(entry(start, "e4-ur-cw"), {"code": "e4-ur-cw", "notation": "e4-ur-cw", "emoji": "⚪",
                                                    "title": "Take the Bottom Edge of the Upper Right Quarter!",
                                                    "words": "A white marble on e4, then the upper right quarter"
                                                             " turns clockwise"})
        self.assertEqual(entry(R.opening(R.B), "a1-ll-acw")["words"],
                         "A black marble on a1, then the lower left quarter turns anticlockwise")

    def test_a_marble_that_made_five_on_its_own_is_named_with_no_turn(self):
        position = R.Position(tuple(R.W if cell in ("a1", "a2", "a3", "a4") else
                                    R.B if cell in ("d6", "e6", "f6", "d5") else "" for cell in R.CELLS))
        named = entry(position, "a5-lr-cw")
        self.assertEqual((named["words"], named["title"], named["emoji"]),
                         ("A white marble on a5", "Take the Left Edge of the Upper Left Quarter!", "⚪"))

    def test_every_move_named_on_many_boards_is_in_what_the_kit_takes(self):
        for position in BOARDS[::5]:
            for code in R.legal(position)[::7]:
                named = entry(position, code)
                hole, quarter, way = code.split("-")
                spot, _ = place(hole)
                words = f"A {'white' if position.turn == R.W else 'black'} marble on {hole}"
                if not R.won_unturned(position, code):
                    words += f", then the {dict(zip(('ul', 'ur', 'll', 'lr'), QUARTERS))[quarter]} quarter turns"
                    words += " clockwise" if way == "cw" else " anticlockwise"
                self.assertEqual(named["words"], words)
                self.assertEqual(named["title"], expected(position.turn, hole)["title"])
                self.assertTrue(KIT_WORDS.fullmatch(named["words"]) and KIT_TITLE.fullmatch(named["title"]), named)


class Ghosts(unittest.TestCase):
    def test_a_ghost_is_named_for_the_hole_it_would_stand_in(self):
        named = {row["code"]: row for row in ghost_listing(())}
        self.assertEqual(named["b5"], {"code": "b5", "notation": "b5", "emoji": "👻",
                                       "title": "Ghost the Centre of the Upper Left Quarter!",
                                       "words": "A ghost on b5, the centre of the upper left quarter"})
        self.assertEqual(named["f1"]["words"], "A ghost on f1, the lower right corner of the lower right quarter")

    def test_every_hole_is_listed_once_as_the_board_is_read_but_a_ghost_s(self):
        self.assertEqual([row["code"] for row in ghost_listing(())], list(R.READING))
        self.assertEqual([row["code"] for row in ghost_listing(("b5",))], [cell for cell in R.READING if cell != "b5"])
        self.assertEqual(pentago.ghost_cells(["b5"]), [cell for cell in R.READING if cell != "b5"])
        self.assertNotIn("turns", ghost_listing(())[0], "a ghost is one choice, with no turn")

    def test_every_ghost_s_name_is_its_own_and_in_what_the_kit_takes(self):
        named = ghost_listing(())
        self.assertEqual(len({row["title"] for row in named}), 36)
        for row in named:
            spot, quarter = place(row["code"])
            with self.subTest(code=row["code"]):
                self.assertEqual(row["title"], capitals(f"ghost the {spot} of the {quarter} quarter!"))
                self.assertEqual(row["words"], f"A ghost on {row['code']}, the {spot} of the {quarter} quarter")
                self.assertTrue(KIT_TITLE.fullmatch(row["title"]) and KIT_WORDS.fullmatch(row["words"]), row)
                self.assertNotRegex(row["title"] + " " + row["words"], BANNED)


if __name__ == "__main__":
    unittest.main()
