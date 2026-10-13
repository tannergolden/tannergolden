# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every square named as tic-tac-toe players name it and for nothing the mark does: the Centre, a Corner or an Edge of
its board, with no square or board in the name, the emoji by the same kind, the words from the square's place and its
board's, and a square named alike whatever the game, the move or the marks round it, so a mark that wins the game reads
as any other. A ghost's square is named the same way, for the square it locks.

  python3 -m unittest discover -s .github/scripts -p 'test_tictac*.py'

The names are worked out here a second way, from the square's file and rank
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

import tictac
import tictac_rules as R
from tictac_names import ghost_listing, listing

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py,
# whose checks every game's moves share).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,98}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
# The nine places of three by three, read top row first: a board's on the big board, and a square's in its board.
BOARDS = ("upper left", "top", "upper right", "left", "centre", "right", "lower left", "bottom", "lower right")
SPOTS = ("upper left corner", "top edge", "upper right corner", "left edge", "centre", "right edge",
         "lower left corner", "bottom edge", "lower right corner")
KINDS = {"centre": "Centre", "corner": "Corner", "edge": "Edge"}  # a square's kind in its board, as the game names it
WHERE = re.compile(r"[a-i][1-9]|\b(?:upper|lower|top|bottom|left|right|board|of|the)\b", re.IGNORECASE)
# What no name may say: a verdict, what the mark does to the game or its board, or where it sends the other side.
JUDGED = ("good", "bad", "safe", "strong", "weak", "best", "only", "win", "wins", "winning", "won", "lose", "loses",
          "lost", "draw", "draws", "drawn", "save", "saves", "block", "blocks", "threat", "threatens", "fork", "trap",
          "force", "forced", "blunder", "mistake", "attack", "defend", "guard", "next", "leaves", "lets", "line",
          "row", "three", "claim", "claims", "seize", "control", "send", "sends", "close", "closes", "closed", "full",
          "open", "free", "anywhere", "must")
BANNED = re.compile(rf"\b(?:{'|'.join(JUDGED)})\b", re.IGNORECASE)


def place(cell: str) -> tuple[str, str]:
    """A square's place in its board and its board's on the big board, in words, from its file and rank alone."""
    x, y = "abcdefghi".index(cell[0]), int(cell[1]) - 1
    return SPOTS[(2 - y % 3) * 3 + x % 3], BOARDS[(2 - y // 3) * 3 + x // 3]


def kind(cell: str) -> str:
    """A square's kind in its board, worked out from its place: `Centre`, `Corner` or `Edge`."""
    return KINDS[place(cell)[0].split()[-1]]


def expected(mark: str, cell: str) -> dict:
    """What the listing names a square for `mark`, worked out from the square alone."""
    spot, board = place(cell)
    emoji = {"Centre": "🔳", "Corner": "📐", "Edge": "📏"}[kind(cell)]
    return {"code": cell, "notation": f"{mark}{cell}", "emoji": emoji, "title": kind(cell),
            "words": f"{mark} takes the {spot} of the {board} board"}


def boards(n: int, seed: int) -> list[R.Position]:
    """Every position with a move to make in `n` games of seeded random play, either mark first, under two ghosts."""
    rng, out = random.Random(seed), []
    for game in range(n):
        position = R.opening(R.O if game % 2 else R.X, rng.sample(R.CELLS, 2))
        while R.legal(position):
            out.append(position)
            position = R.make(position, rng.choice(R.legal(position)))
    return out


BOARDS_SEEN = boards(40, 5)


class Listing(unittest.TestCase):
    def test_every_square_the_side_to_move_may_take_is_listed_once_as_the_board_is_read(self):
        for position in BOARDS_SEEN:
            self.assertEqual([entry["code"] for entry in listing(position, 1, 3)], R.legal(position), position.board)

    def test_a_square_is_named_for_its_kind_and_its_words_say_where_it_is(self):
        start = R.opening(R.X, ("a1", "i9"))
        named = {entry["code"]: entry for entry in listing(start, 1, 3)}
        self.assertEqual(named["e5"], {"code": "e5", "notation": "Xe5", "emoji": "🔳", "title": "Centre",
                                       "words": "X takes the centre of the centre board"})
        self.assertEqual(named["f6"], {"code": "f6", "notation": "Xf6", "emoji": "📐", "title": "Corner",
                                       "words": "X takes the upper right corner of the centre board"})
        self.assertEqual((named["a8"]["emoji"], named["a8"]["title"]), ("📏", "Edge"))
        self.assertEqual(named["h1"]["title"], "Edge")
        self.assertEqual((named["b2"]["title"], named["b2"]["words"]),
                         ("Centre", "X takes the centre of the lower left board"))
        o_first = {entry["code"]: entry for entry in listing(R.opening(R.O, ()), 1, 3)}
        self.assertEqual((o_first["e5"]["notation"], o_first["e5"]["words"]),
                         ("Oe5", "O takes the centre of the centre board"), "the mark to go down leads both")

    def test_every_name_on_many_boards_is_the_square_s_own_and_no_more(self):
        for position in BOARDS_SEEN:
            for entry in listing(position, 1, 3):
                self.assertEqual(entry, expected(position.turn, entry["code"]), position.board)

    def test_every_square_is_a_centre_a_corner_or_an_edge_in_what_the_kit_takes(self):
        named = listing(R.opening(R.X), 1, 1)
        self.assertEqual(len(named), 81)
        titles = [entry["title"] for entry in named]
        self.assertEqual({title: titles.count(title) for title in set(titles)}, {"Centre": 9, "Corner": 36, "Edge": 36})
        for entry in named:
            with self.subTest(code=entry["code"]):
                self.assertRegex(entry["emoji"], KIT_EMOJI)
                self.assertTrue(KIT_TITLE.fullmatch(entry["title"]), entry)
                self.assertTrue(KIT_WORDS.fullmatch(entry["words"]), entry)
                self.assertIsNone(WHERE.search(entry["title"]), "a name holds no square and no board")
                for dash in DASHES:
                    self.assertNotIn(dash, entry["title"] + entry["words"])
        emoji = [entry["emoji"] for entry in named]
        self.assertEqual((emoji.count("🔳"), emoji.count("📐"), emoji.count("📏")), (9, 36, 36))

    def test_the_game_and_the_move_number_change_nothing(self):
        for position in BOARDS_SEEN[:200]:
            self.assertEqual(listing(position, 1, 3), listing(position, 41, 77))

    def test_a_mark_that_wins_the_game_reads_as_any_other(self):
        # X has won the upper left and top boards and holds two of the upper right board's top row, and O's last mark
        # sends X there: g9 wins the game, and its name is the one it has on an empty board.
        xs, os = "a9 b9 c9 d9 e9 f9 h9 i9", "a1 c1 b2 e1 d3 g2 i1 g3"
        marks = {**dict.fromkeys(xs.split(), R.X), **dict.fromkeys(os.split(), R.O)}
        position = R.Position(tuple(marks.get(cell, "") for cell in R.CELLS), R.X, frozenset(), "g3")
        self.assertEqual(R.notation(position, "g9"), "Xg9#")
        winning = next(entry for entry in listing(position, 1, 17) if entry["code"] == "g9")
        self.assertEqual(winning, expected(R.X, "g9"))
        self.assertNotIn("#", winning["notation"])

    def test_no_name_judges_or_says_what_the_mark_does(self):
        for position in BOARDS_SEEN[::7]:
            for entry in listing(position, 1, 3):
                for field in ("emoji", "title", "notation", "words"):
                    self.assertNotRegex(entry[field], BANNED, entry)
                self.assertFalse(entry["notation"].endswith(("+", "#")), entry)

    def test_a_listing_handed_out_can_be_changed_without_changing_the_next(self):
        position = R.opening(R.X, ("e5",))
        first = listing(position, 1, 3)
        first[0]["title"] = "Changed"
        first.pop()
        self.assertEqual(listing(position, 1, 3), [expected(R.X, cell) for cell in R.legal(position)])

    def test_a_finished_game_lists_nothing(self):
        xs = " ".join(cell for b in ((0, 0), (1, 1), (2, 2)) for cell in R.squares_of(b)[:3])
        position = R.Position(tuple(R.X if cell in xs.split() else "" for cell in R.CELLS))
        self.assertTrue(R.ending(position))
        self.assertEqual(listing(position, 1, 19), [])

    def test_the_engine_lists_the_names_module_s_own(self):
        position = BOARDS_SEEN[33]
        self.assertEqual(tictac.listing(position, 1, 3), listing(position, 1, 3))


class Ghosts(unittest.TestCase):
    def test_a_ghost_is_named_for_the_kind_of_square_it_would_lock(self):
        named = {entry["code"]: entry for entry in ghost_listing(())}
        self.assertEqual(named["e5"], {"code": "e5", "notation": "e5", "emoji": "👻", "title": "Centre Ghost",
                                       "words": "A ghost locks the centre of the centre board"})
        self.assertEqual(named["a1"]["title"], "Corner Ghost")
        self.assertEqual(named["d9"]["words"], "A ghost locks the upper left corner of the top board")

    def test_every_open_square_is_listed_once_as_the_board_is_read(self):
        self.assertEqual([entry["code"] for entry in ghost_listing(())], list(R.READING))
        self.assertEqual([entry["code"] for entry in ghost_listing(("e5",))],
                         [cell for cell in R.READING if cell != "e5"], "the second ghost goes anywhere but the first's")
        self.assertEqual(tictac.ghost_cells(["e5"]), [cell for cell in R.READING if cell != "e5"])

    def test_every_ghost_s_name_is_its_square_s_kind_and_in_what_the_kit_takes(self):
        named = ghost_listing(())
        self.assertEqual({entry["title"] for entry in named}, {"Centre Ghost", "Corner Ghost", "Edge Ghost"})
        for entry in named:
            spot, board = place(entry["code"])
            with self.subTest(code=entry["code"]):
                self.assertEqual(entry["title"], f"{kind(entry['code'])} Ghost")
                self.assertIsNone(WHERE.search(entry["title"]), "a name holds no square and no board")
                self.assertEqual(entry["words"], f"A ghost locks the {spot} of the {board} board")
                self.assertEqual((entry["emoji"], entry["notation"]), ("👻", entry["code"]))
                self.assertTrue(KIT_TITLE.fullmatch(entry["title"]) and KIT_WORDS.fullmatch(entry["words"]), entry)
                self.assertNotRegex(entry["title"] + " " + entry["words"], BANNED)


if __name__ == "__main__":
    unittest.main()
