# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: what a move is read as, the title and words it is given, and that a board keeps them.

  python3 -m unittest discover -s .github/scripts -p 'test_chess*.py'
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chess_names import COMMANDS, OWN, PLACES, SHORT, listing, read, theme, words  # noqa: E402
from chess_names import THEMES as THEME_PATTERNS  # noqa: E402
from chess_rules import START, Move, Position, legal_moves, make  # noqa: E402

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
# A position for each theme a move can have, with the move that has it.
THEMES = {
    "mate": ("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2", "d8h4"),
    "smothered": ("6rk/6pp/8/6N1/8/8/8/K7 w - - 0 1", "g5f7"),
    "back-rank": ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "d1d8"),
    "stalemate": ("7k/5Q2/8/8/8/8/8/K7 w - - 0 1", "f7g6"),
    "crown": ("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8q"),
    "underpromote": ("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8n"),
    "castle-king": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "e1g1"),
    "castle-queen": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "e1c1"),
    "passing": ("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3", "e5f6"),
    "first-blood": ("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2", "e4d5"),
    "royal-fork": ("q3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5c7"),
    "discovery": ("4k3/8/8/8/8/8/4N3/K3R3 w - - 0 1", "e2c3"),
    "double": ("4k3/8/8/8/4N3/8/8/K3R3 w - - 0 1", "e4d6"),
    "develop": (START, "g1f3"),
    "center": (START, "e2e4"),
    "stride": (START, "a2a4"),
    "fianchetto": ("rnbqkbnr/pppppppp/8/8/8/6P1/PPPPPP1P/RNBQKBNR w KQkq - 0 1", "f1g2"),
    "pin": ("4k3/8/2n5/8/8/8/8/4KB2 w - - 0 1", "f1b5"),  # the knight held to its king
    "threat": ("4k3/8/8/3q4/8/8/8/1N2K3 w - - 0 1", "b1c3"),  # the queen, alone
    "escape": ("4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1", "e5f3"),  # out of the pawn's reach
    "guard": ("4k3/8/8/b7/8/2N5/8/4K3 w - - 0 1", "e1d2"),  # the king covers the knight the bishop eyes
}
# Orders that send a unit forward, which a move along its own rank never gets.
FORWARD = tuple(f"{order} the " for order in ("Advance", "March", "Push Up", "Move Up", "Send Forward", "Drive",
                                              "Send In", "Spur On"))


def boards(n: int, seed: int = 7):
    """`n` positions from random games, each with a move to make."""
    rng = random.Random(seed)
    for game in range(n):
        position = Position.from_fen(START)
        for _ in range(rng.randint(0, 80)):
            moves = legal_moves(position)
            if not moves:
                break
            position = make(position, rng.choice(moves))
        if legal_moves(position):
            yield game, position


class Reading(unittest.TestCase):
    def test_a_move_is_named_for_the_most_telling_thing_it_does(self):
        for want, (fen, uci) in THEMES.items():
            with self.subTest(theme=want):
                position, move = Position.from_fen(fen), Move.from_uci(uci)
                self.assertIn(move, legal_moves(position))
                self.assertEqual(theme(read(position, move)), want)

    def test_its_words_say_what_it_does(self):
        said = {uci: words(Position.from_fen(fen), Move.from_uci(uci)) for fen, uci in THEMES.values()}
        self.assertEqual(said["d8h4"], "Queen from d8 to h4, checkmate")
        self.assertEqual(said["f7g6"], "Queen from f7 to g6, stalemate")
        self.assertEqual(said["e7e8n"], "Pawn from e7 to e8, becoming a knight")
        self.assertEqual(said["e1c1"], "Castle queenside")
        self.assertEqual(said["e5f6"], "Pawn from e5 takes the pawn on f5, en passant")
        self.assertEqual(said["e4d6"], "Knight from e4 to d6, check")
        self.assertEqual(said["a2a4"], "Pawn from a2 to a4, two squares")


class Titles(unittest.TestCase):
    def test_every_board_names_every_move_once_in_what_the_kit_accepts(self):
        for game, position in boards(60):
            named = listing(position, game, 1)
            self.assertEqual(len(named), len(legal_moves(position)))
            self.assertEqual(len({m["title"] for m in named}), len(named), position.fen)
            for m in named:
                self.assertTrue(KIT_EMOJI.fullmatch(m["emoji"]), m["emoji"])
                self.assertTrue(KIT_TITLE.fullmatch(m["title"]), m["title"])
                self.assertTrue(KIT_WORDS.fullmatch(m["words"]), m["words"])

    def test_every_title_is_an_order_and_never_names_a_square(self):
        short = total = 0
        for game, position in boards(60):
            for m in listing(position, game, 1):
                self.assertIn(m["title"].split()[0].rstrip(",!"), COMMANDS, m["title"])
                self.assertTrue(m["title"].endswith("!"), m["title"])
                self.assertNotRegex(m["title"], r"\b[a-h][1-8]\b|\b[a-h]-[Ff]ile\b")
                reading = read(position, Move.from_uci(m["uci"]))
                if reading.advance == 0 and reading.kind in "rqk" and theme(reading) == "quiet":
                    self.assertFalse(m["title"].startswith(FORWARD), f"{m['title']} sends sideways forward")
                short, total = short + (len(m["title"]) <= SHORT), total + 1
        self.assertGreater(short / total, 0.85, "most orders read at a glance")
        opening = [m["title"] for m in listing(Position.from_fen(START), 1, 1)]
        self.assertEqual(opening[:4], ["Leave the Barracks!", "Deploy the Outriders!", "Muster the Knights!",
                                       "Join the Fray, Cavalry!"])

    def test_a_board_is_named_the_same_every_time_and_another_game_differently(self):
        position = Position.from_fen(START)
        self.assertEqual(listing(position, 1, 1), listing(position, 1, 1))
        first = [m["title"] for m in listing(position, 1, 1)]
        later = [m["title"] for m in listing(position, 2, 1)]
        self.assertGreater(sum(a != b for a, b in zip(first, later)), len(first) // 2)

    def test_the_titles_run_far_past_any_fixed_list(self):
        fixed = {p for _, patterns in THEME_PATTERNS.values() for p in patterns if "{" not in p}
        fixed |= {p for patterns in OWN.values() for p in patterns if "{" not in p}
        seen = {m["title"] for game, position in boards(60) for m in listing(position, game, 1)}
        self.assertGreater(len(seen - fixed), len(fixed), "more titles made than every fixed phrase put together")

    def test_a_title_s_article_fits_and_a_place_brings_its_own_preposition(self):
        for game, position in boards(60):
            for m in listing(position, game, 1):
                self.assertNotRegex(m["title"], r"\bA [AEIOU]|\bAn [^AEIOU]")
        patterns = [p for _, ps in THEME_PATTERNS.values() for p in ps] + [p for ps in OWN.values() for p in ps]
        for pattern in patterns:
            self.assertNotRegex(pattern, r"\b(?:at|in|on|behind) \{place\}", "a place's own word comes with {at}")
        self.assertTrue(all(at in ("at", "in", "on", "behind") for options in PLACES.values() for at, _ in options))

    def test_the_list_runs_from_the_king_to_the_pawns(self):
        pieces = [m["piece"] for m in listing(Position.from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
                                               1, 1)]
        order = ["king", "queen", "rook", "bishop", "knight", "pawn"]
        self.assertEqual(pieces, sorted(pieces, key=order.index))


if __name__ == "__main__":
    unittest.main()
