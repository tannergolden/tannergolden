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

from chess_names import (  # noqa: E402
    BOOK_LINES,
    COMMANDS,
    EMOJI,
    LONGEST,
    WORDS_LONGEST,
    fen4,
    gives_check,
    listing,
    read,
    see,
    survey,
    theme,
    tiers,
    words,
)
from chess_rules import START, Move, Position, in_check, legal_moves, make  # noqa: E402

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
WARNING = "⚠️"
# A position for each theme a move can have, with the move that has it.
THEMES = {
    "fool": ("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2", "d8h4"),
    "scholar": ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7"),
    "smothered": ("6rk/6pp/8/6N1/8/8/8/K7 w - - 0 1", "g5f7"),
    "back-rank": ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "d1d8"),
    "mate": ("7k/8/6K1/8/8/8/8/1Q6 w - - 0 1", "b1b8"),
    "stalemate": ("7k/5Q2/8/8/8/8/8/K7 w - - 0 1", "f7g6"),  # a queen up, so a draw thrown away
    "only": ("4k3/8/8/8/8/5q2/8/4K3 w - - 0 1", "e1d2"),
    "allows": ("rnbqkbnr/pppp1ppp/8/4p3/8/5P2/PPPPP1PP/RNBQKBNR w KQkq - 0 2", "g2g4"),  # into Fool's Mate
    "blunder": ("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "d8g5"),  # the knight takes it
    "only-stop": ("r1q3r1/2p5/n1b1kBp1/p5p1/2P5/QP2p2N/P3P1BP/3RKR2 b - - 3 27", "c6f3"),
    "book": ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "c7c5"),  # the Sicilian
    "dead": ("4k3/8/8/8/8/8/3q4/4K3 w - - 0 1", "e1d2"),  # king against king: drawn
    "crown": ("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8q"),
    "underpromote": ("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8n"),
    "castle": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "e1g1"),
    "evade": ("rnbqk1nr/pppp1ppp/8/4p3/1b1PP3/8/PPP2PPP/RNBQKBNR w KQkq - 1 3", "c2c3"),  # blocks the bishop's check
    "double": ("4k3/8/8/8/4N3/8/8/K3R3 w - - 0 1", "e4d6"),
    "discovery": ("4k3/8/8/8/8/8/4N3/K3R3 w - - 0 1", "e2c3"),
    "royal-fork": ("q3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5c7"),
    "sacrifice": ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5e5"),  # Nxe5 takes it
    "greek": ("rnbq1rk1/pppn1ppp/4p3/3pP3/1b1P4/2NB1N2/PPP2PPP/R2QK2R w KQ - 0 1", "d3h7"),
    "queen": ("3qk3/8/8/8/8/8/8/3QK3 w - - 0 1", "d1d8"),
    "fork": ("r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5c7"),
    "skewer": ("6q1/8/8/3k4/8/8/8/K2B4 w - - 0 1", "d1b3"),
    "strike": ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "c4f7"),  # the queen guards f7
    "passing": ("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3", "e5f6"),
    "level": ("4k2n/8/8/3b4/8/2N5/8/4K3 w - - 0 1", "c3d5"),  # a piece down, and a piece back
    "free": ("4k3/p7/8/3n4/8/2N5/P7/4K3 w - - 0 1", "c3d5"),
    "win": ("4k3/8/4p3/3r4/8/2N5/8/4K3 w - - 0 1", "c3d5"),  # the exchange
    "trade": ("4k3/8/4p3/3n4/8/2N5/8/4K3 w - - 0 1", "c3d5"),
    "capture": ("1rb3n1/pB2k3/2P1p3/P1p2pb1/6Qr/2B5/2PP4/RN2K1N1 b - - 1 20", "b8b7"),
    "stop": ("5rk1/5ppp/8/6NQ/8/8/5PPP/6K1 b - - 1 1", "h7h6"),  # Qxh7 was mate
    "check": ("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1a8"),
    "mate-threat": ("5rk1/5ppp/8/6N1/8/8/5PPP/3Q2K1 w - - 0 1", "d1h5"),
    "pin": ("4k3/8/2n5/8/8/8/8/4KB2 w - - 0 1", "f1b5"),  # the knight held to its king
    "unmask": ("4k3/4q3/8/8/8/8/4N3/K3R3 w - - 0 1", "e2c3"),  # the rook now hits the queen
    "threat": ("4k3/8/8/3q4/8/8/8/1N2K3 w - - 0 1", "b1c3"),  # the queen, alone
    "escape": ("4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1", "e5f3"),  # out of the pawn's reach
    "guard": ("4k3/8/8/b7/8/2N5/8/4K3 w - - 0 1", "e1d2"),  # the king covers the knight the bishop eyes
    "offer": ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "b7b5"),
    "outpost": ("4k3/pp3ppp/3p4/4p3/4P3/2N5/PPP2PPP/4K3 w - - 0 1", "c3d5"),
    "passed": ("8/8/4k3/8/8/4P3/8/4K3 w - - 0 1", "e3e4"),
    "centre": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "e2e4"),
    "luft": ("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", "h2h3"),
    "prepare": (START, "g2g3"),
    "free-bishop": (START, "e2e3"),
    "cover": (START, "c2c3"),
    "free-queen": ("r1b1qr2/b2p3p/3k3n/p1p2p2/1P1PPp2/PP1B3Q/3B1PP1/R3K2R w Q - 1 21", "g2g3"),
    "space": ("rnbqkbnr/pppppppp/8/8/7P/8/PPPPPPP1/RNBQKBNR w KQkq - 0 1", "h4h5"),
    "stride": (START, "a2a4"),
    "push": (START, "a2a3"),
    "rim-develop": (START, "g1h3"),
    "fianchetto": ("rnbqkbnr/pppppppp/8/8/8/6P1/PPPPPP1P/RNBQKBNR w KQkq - 0 1", "f1g2"),
    "aim-f7": ("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "f1c4"),
    "develop": (START, "g1f3"),
    "forfeit": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "e1f1"),
    "activate": ("8/8/4k3/8/8/4P3/8/4K3 w - - 0 1", "e1d2"),
    "tuck": ("5rk1/5ppp/8/6N1/8/8/5PPP/3Q2K1 w - - 0 1", "g1h1"),
    "opposition": ("8/8/4k3/8/8/4K3/4P3/8 w - - 0 1", "e3e4"),  # the kings face off, Black to move
    "behind-passer": ("1K6/1P1k4/8/8/8/8/r7/2R5 w - - 0 1", "c1b1"),  # the Lucena's rook, behind its pawn
    "king": ("5rk1/5ppp/8/6N1/8/8/5PPP/3Q2K1 w - - 0 1", "g1f1"),
    "seventh": ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "d1d7"),
    "battery": ("r4rk1/5ppp/8/8/8/3B4/5PPP/3Q1RK1 w - - 0 1", "d1c2"),  # queen behind bishop, at h7
    "open-file": ("6k1/ppp2pp1/7p/8/8/8/PP3PPP/R5K1 w - - 0 1", "a1d1"),
    "rook-forfeit": ("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "a1b1"),
    "connect": ("r3k3/pppppppp/8/8/8/8/PPP1PPPP/R2Q1RK1 w - - 0 1", "d1d2"),
    "lift": ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "d1d3"),
    "sortie": ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "d1f3"),
    "centralise": ("r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5d4"),
    "diagonal": ("4k3/8/8/8/8/8/3B4/4K3 w - - 0 1", "d2c3"),
    "aim": ("5rk1/5ppp/8/6N1/8/8/5PPP/3Q2K1 w - - 0 1", "d1b3"),
    "rim": ("r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1BP2N1P/PP1P1PP1/RNBQR1K1 b - - 0 9", "c6a5"),
    "retreat": ("r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5c3"),
    "invade": ("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "c6b4"),
    "long": ("4k3/8/8/8/8/Q7/8/4K3 w - - 0 1", "a3h3"),
    "quiet": ("4k3/8/8/8/8/Q7/8/4K3 w - - 0 1", "a3b3"),
}
# What each theme's title says, whichever synonym the board picks: the chess idea, in the game's own words.
SAYS = {
    "fool": "Fool's Mate", "scholar": "Scholar's Mate", "smothered": "Smother", "back-rank": "Back",
    "mate": "Checkmate", "stalemate": "Stalemate", "only": "Only", "allows": "Fool's Mate", "blunder": "Queen",
    "only-stop": "Only Move That Stops Mate", "book": "Sicilian", "dead": "Draw", "crown": "Queen",
    "underpromote": "Knight", "castle": "Castle", "evade": "Check", "double": "Double Check",
    "discovery": "Discover", "royal-fork": "Fork", "sacrifice": "Give Up the Queen for a Pawn", "greek": "h7",
    "queen": "Queens", "fork": "King and Rook", "skewer": "King and Queen", "strike": "With Check",
    "passing": "en Passant", "level": "Back", "free": "Knight", "win": "Exchange", "trade": "Knights",
    "capture": "Bishop", "stop": "Mate", "check": "King", "mate-threat": "Mate", "pin": "Knight to the King",
    "unmask": "Queen", "threat": "Queen", "escape": "Knight", "guard": "Knight", "offer": "b-Pawn",
    "outpost": "Outpost", "passed": "Passed Pawn", "centre": "Centre", "luft": "Luft", "prepare": "Fianchetto",
    "free-bishop": "King's Bishop", "cover": "d4", "free-queen": "Queen", "space": "h-Pawn", "stride": "Two Squares",
    "push": "a-Pawn", "rim-develop": "Rim", "fianchetto": "Fianchetto", "aim-f7": "f7", "develop": "King's Knight",
    "forfeit": "Castl", "activate": "King", "tuck": "Corner", "king": "King", "seventh": "Seventh",
    "opposition": "Opposition", "behind-passer": "Passed Pawn",
    "battery": "Queen and Bishop", "open-file": "Open", "rook-forfeit": "Castling Long", "connect": "Connect",
    "lift": "Lift", "sortie": "Queen", "centralise": "Knight", "diagonal": "Long Diagonal", "aim": "Queen",
    "rim": "Rim", "retreat": "Knight", "invade": "Knight", "long": "Queen", "quiet": "Queen",
}
SQUARE = re.compile(r"\b[a-h][1-8]\b")
PIECE = re.compile(r"\b(?:King|Queen|Rook|Bishop|Knight|Pawn|[a-h]-Pawn)s?\b")


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


def entry(fen: str, uci: str) -> dict:
    """The listed move, as the board names it."""
    return next(m for m in listing(Position.from_fen(fen)) if m["uci"] == uci)


def titled(fen: str) -> dict[str, str]:
    """Each move's title on the board, by its SAN."""
    return {m["san"]: m["title"] for m in listing(Position.from_fen(fen))}


class Reading(unittest.TestCase):
    def test_a_move_is_named_for_the_most_telling_thing_it_does(self):
        for want, (fen, uci) in THEMES.items():
            with self.subTest(theme=want):
                position, move = Position.from_fen(fen), Move.from_uci(uci)
                self.assertIn(move, legal_moves(position))
                self.assertEqual(theme(read(position, move)), want)
                named = entry(fen, uci)
                self.assertIn(SAYS[want], named["title"])
                self.assertEqual(named["emoji"], WARNING if want in ("allows", "blunder", "stalemate") else EMOJI[want])

    def test_every_theme_has_a_position_that_shows_it(self):
        self.assertEqual(set(THEMES), set(EMOJI))
        self.assertEqual(set(THEMES), set(SAYS))

    def test_its_words_say_what_it_does(self):
        said = {uci: words(Position.from_fen(fen), Move.from_uci(uci)) for fen, uci in THEMES.values()}
        self.assertEqual(said["d8h4"], "Queen from d8 to h4, checkmate")
        self.assertEqual(said["f7g6"], "Queen from f7 to g6, stalemate")
        self.assertEqual(said["e7e8n"], "Pawn from e7 to e8, becoming a knight")
        self.assertEqual(said["e5f6"], "Pawn from e5 takes the pawn on f5, en passant")
        self.assertEqual(said["e4d6"], "Knight from e4 to d6, check")
        self.assertEqual(said["a2a4"], "Pawn from a2 to a4, two squares")
        self.assertEqual(words(Position.from_fen(THEMES["castle"][0]), Move.from_uci("e1c1")), "Castle queenside")

    def test_a_check_is_seen_from_the_lines_a_move_opens(self):
        for _, position in boards(30, seed=3):
            for move in legal_moves(position):
                self.assertEqual(gives_check(position, move), in_check(make(position, move)), (position.fen, move))

    def test_the_static_exchange_counts_both_sides_taking_in_turn(self):
        board = Position.from_fen("4k3/8/4p3/3n4/8/2N5/8/4K3 w - - 0 1").board
        self.assertEqual(see(board, 18, 35), 0, "a knight for a knight")
        board = Position.from_fen("4k3/8/4p3/3r4/8/2N5/8/4K3 w - - 0 1").board
        self.assertEqual(see(board, 18, 35), 2, "a rook for a knight")
        board = Position.from_fen("4k3/8/4p3/3p4/8/2N5/8/4K3 w - - 0 1").board
        self.assertEqual(see(board, 18, 35), -2, "a knight for a pawn")
        board = Position.from_fen("4k3/8/8/3p4/8/2N5/8/4K3 w - - 0 1").board
        self.assertEqual(see(board, 18, 35), 1, "a pawn for nothing")


class Truth(unittest.TestCase):
    """A title says what the move does on the board, and never what it does not."""

    def test_the_twenty_opening_moves(self):
        title = titled(START)
        self.assertEqual(len(title), 20)
        for knight, which in (("Na3", "Queen's Knight"), ("Nh3", "King's Knight")):
            self.assertIn("Rim", title[knight], "a knight sent to the rim says so")
            self.assertIn(which, title[knight])
        self.assertRegex(title["Nf3"], r"^(Develop|Bring Out) the King's Knight!$")
        self.assertRegex(title["Nc3"], r"^(Develop|Bring Out) the Queen's Knight!$")
        self.assertIn("King's Pawn", title["e4"])
        self.assertIn("Queen's Pawn", title["d4"])
        self.assertEqual((title["c4"], title["f4"]), ("Play the English!", "Play Bird's Opening!"))
        self.assertIn("Grob's Attack", title["g4"])
        self.assertIn("Polish", title["b4"])
        self.assertIn("Nimzo-Larsen", title["b3"])
        self.assertIn("King's Bishop", title["e3"])
        self.assertIn("Queen's Bishop", title["d3"])
        self.assertRegex(title["g3"], r"Kingside Fianchetto|Fianchetto the King's Bishop")
        for pawn, covered in (("a3", "b4"), ("c3", "d4"), ("f3", "e4"), ("h3", "g4")):
            self.assertIn(covered, title[pawn])
        for pawn in ("a4", "h4"):
            self.assertIn("Two Squares", title[pawn])
        self.assertTrue(all(m["emoji"] != WARNING for m in listing(Position.from_fen(START))), "no first move loses")

    def test_a_knight_sent_to_the_rim_says_so(self):
        for _, position in boards(40):
            for m in listing(position):
                reading = read(position, Move.from_uci(m["uci"]))
                if theme(reading) in ("rim", "rim-develop"):
                    self.assertTrue(reading.end % 8 in (0, 7) and reading.kind == "n")
                    self.assertRegex(m["title"], r"\b(Rim|Edge)\b")
                if theme(reading) in ("develop", "centralise", "outpost"):
                    self.assertNotIn(reading.end % 8, (0, 7) if reading.kind == "n" else (), m["title"])

    def test_tactics_name_what_they_catch(self):
        self.assertIn("King and Rook", entry(*THEMES["fork"])["title"])
        self.assertIn("King and Queen", entry(*THEMES["royal-fork"])["title"])
        self.assertIn("King and Queen", entry(*THEMES["skewer"])["title"])
        self.assertRegex(entry(*THEMES["pin"])["title"], r"^(Pin|Nail) the Knight to the King!$")
        self.assertRegex(entry("4k3/8/2n5/8/8/8/8/4KB2 w - - 0 1", "f1g2")["title"], r"Knight")  # a threat, not a pin
        self.assertIn("Knight to the Queen", entry("r2qkb1r/ppp2ppp/2n2n2/3pp3/8/2NP1N2/PPP1PPPP/R1BQKB1R w KQkq - 0 1",
                                                   "c1g5")["title"])

    def test_positional_moves_name_the_idea(self):
        self.assertIn("Outpost", entry(*THEMES["outpost"])["title"])
        self.assertRegex(entry(*THEMES["open-file"])["title"], r"Open (d-)?File")
        self.assertRegex(entry("6k1/pp3pp1/2p4p/8/8/8/PP3PPP/R5K1 w - - 0 1", "a1c1")["title"], r"Half-Open")
        self.assertIn("Queen and Bishop", entry(*THEMES["battery"])["title"])
        self.assertIn("Double", entry("3r2k1/1q3ppp/8/8/8/8/R4PPP/3RK3 w - - 0 1", "a2d2")["title"])
        self.assertRegex(entry(*THEMES["luft"])["title"], r"Luft|Air|Escape Square")
        self.assertIn("Seventh", entry(*THEMES["seventh"])["title"])
        self.assertRegex(entry(*THEMES["passed"])["title"], r"Passed Pawn")
        self.assertRegex(entry(*THEMES["activate"])["title"], r"King")
        self.assertIn("Connect", titled(THEMES["connect"][0])["Qd2"] + titled(THEMES["connect"][0])["Qd3"])

    def test_captures_say_what_they_win_trade_or_give_up(self):
        self.assertRegex(entry(*THEMES["trade"])["title"], r"^(Trade|Swap|Exchange) Knights!$")
        self.assertRegex(entry(*THEMES["level"])["title"], r"Win Back the Piece|Material")
        self.assertRegex(entry(*THEMES["free"])["title"], r"Free|Undefended|Loose")
        self.assertIn("Exchange", entry(*THEMES["win"])["title"])
        self.assertEqual(entry(*THEMES["sacrifice"])["title"], "Give Up the Queen for a Pawn!")
        self.assertEqual(entry("4k3/8/8/3q4/8/8/8/3QK3 w - - 0 1", "d1d5")["emoji"], EMOJI["queen"])

    def test_a_blunder_is_named_as_a_blunder(self):
        fool = entry(*THEMES["allows"])
        self.assertEqual((fool["emoji"], fool["title"]), (WARNING, "Push the g-Pawn Into Fool's Mate!"))
        self.assertEqual(entry(*THEMES["blunder"])["emoji"], WARNING)
        dropped = entry("rnbq1rk1/pppn1ppp/4p3/3pP3/1b1P4/2NB1N2/PPP2PPP/R2QK2R w KQ - 0 1", "b2b3")
        self.assertEqual((dropped["emoji"], dropped["title"]), (WARNING, "Push the b-Pawn, Drop the Knight!"))
        self.assertIn("Stalemate", entry(*THEMES["stalemate"])["title"])
        thrown = entry("r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1", "b7a8b")
        self.assertEqual(thrown["emoji"], WARNING, "a bishop where a queen wins draws on the spot")
        for _, position in boards(30):
            for m in listing(position):
                if m["emoji"] == WARNING:
                    self.assertRegex(m["title"], r"Mate|Hang|Lose|Drop|Throw Away|Let Th|Stalemate|Draw")

    def test_the_only_move_and_the_only_defence_are_named_as_such(self):
        self.assertIn("Only", entry(*THEMES["only"])["title"])
        self.assertIn("Only Move That Stops Mate", entry(*THEMES["only-stop"])["title"])
        board = titled(THEMES["stop"][0])
        self.assertTrue(all("Mate" in board[san] for san in ("h6", "Re8", "Rd8")))
        self.assertTrue(all(entry(THEMES["stop"][0], uci)["emoji"] == WARNING for uci in ("g8h8", "f7f6", "g7g6")))

    def test_a_check_is_answered_by_how_it_is_met(self):
        board = titled(THEMES["evade"][0])
        self.assertTrue(all(re.search(r"Check|Shield the King", board[san]) for san in ("c3", "Nc3", "Bd2")))
        self.assertEqual(entry(THEMES["evade"][0], "d1d2")["emoji"], WARNING, "a queen blocking there is lost")
        self.assertRegex(titled("4k3/8/8/8/8/8/3q4/2K5 w - - 0 1")["Kb1"], r"Check|b1")
        self.assertIn("Draw", titled("4k3/8/8/8/8/8/3q4/2K5 w - - 0 1")["Kxd2"], "the last piece taken, a draw")

    def test_the_named_openings_are_the_ones_the_moves_reach(self):
        for line, titles in BOOK_LINES:
            with self.subTest(line=line):
                position = Position.from_fen(START)
                ucis = line.split()
                for uci in ucis[:-1]:
                    self.assertIn(Move.from_uci(uci), legal_moves(position))
                    position = make(position, Move.from_uci(uci))
                self.assertIn(Move.from_uci(ucis[-1]), legal_moves(position))
                self.assertIn(entry(position.fen, ucis[-1])["title"], titles)
        ruy = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        self.assertIn(titled(ruy)["Bb5"], ("Play the Ruy Lopez!", "Play the Spanish Game!"))
        english = "rnbqkbnr/ppp1pppp/8/3p4/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 0 2"  # 1.c4 d5, and 2.d4 transposes
        self.assertIn(titled(english)["d4"], ("Offer the Queen's Gambit!", "Play the Queen's Gambit!"))


class Titles(unittest.TestCase):
    def test_every_board_names_every_move_once_in_what_the_kit_accepts(self):
        for game, position in boards(60):
            named = listing(position, game, 1)
            self.assertEqual(len(named), len(legal_moves(position)))
            self.assertEqual(len({m["title"] for m in named}), len(named), position.fen)
            for m in named:
                self.assertTrue(KIT_EMOJI.fullmatch(m["emoji"]), m["emoji"])
                self.assertTrue(KIT_TITLE.fullmatch(m["title"]) and len(m["title"]) <= LONGEST, m["title"])
                self.assertTrue(KIT_WORDS.fullmatch(m["words"]) and len(m["words"]) <= WORDS_LONGEST, m["words"])
                self.assertFalse(any(dash in m["title"] + m["words"] for dash in DASHES))

    def test_every_title_is_an_order(self):
        for game, position in boards(60):
            for m in listing(position, game, 1):
                self.assertIn(m["title"].split()[0].rstrip(",!"), COMMANDS, m["title"])
                self.assertTrue(m["title"].endswith("!"), m["title"])

    def test_every_title_in_a_tier_names_the_same_details(self):
        for _, position in boards(30):
            board = survey(fen4(position))
            for move in legal_moves(position):
                for tier in tiers(read(position, move), board)[1:]:
                    details = {(frozenset(SQUARE.findall(t)), frozenset(PIECE.findall(t))) for t in tier}
                    self.assertEqual(len(details), 1, tier)
                for tier in tiers(read(position, move), board):
                    for title in tier:
                        self.assertIn(title.split()[0].rstrip(",!"), COMMANDS, title)
                        self.assertLessEqual(len(title), LONGEST, title)

    def test_the_same_position_always_names_its_moves_the_same_way(self):
        position = Position.from_fen(START)
        self.assertEqual(listing(position, 1, 1), listing(position, 2, 41), "whatever the game and move number")
        later = Position.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 6 4")  # the knights went back
        self.assertEqual(listing(position, 1, 1), listing(later, 1, 7), "or the clocks")
        stepped = Position.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        again = Position.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 2 3")
        self.assertEqual(listing(stepped, 1, 2), listing(again, 1, 6), "an en passant square nobody can use is none")
        other = [m["title"] for m in listing(Position.from_fen(THEMES["castle"][0]), 1, 1)]
        self.assertNotEqual([m["title"] for m in listing(position, 1, 1)], other)

    def test_the_plain_fallback_is_rare(self):
        plain = total = 0
        for game, position in boards(60):
            for m in listing(position, game, 1):
                plain += bool(re.fullmatch(r"(Move the \w+|Promote on [a-h][1-8]) from [a-h][1-8] to .*", m["title"]))
                total += 1
        self.assertLess(plain / total, 0.01, "almost every move keeps the voice of its theme")

    def test_the_list_runs_from_the_king_to_the_pawns(self):
        pieces = [m["piece"] for m in listing(Position.from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
                                               1, 1)]
        order = ["king", "queen", "rook", "bishop", "knight", "pawn"]
        self.assertEqual(pieces, sorted(pieces, key=order.index))


if __name__ == "__main__":
    unittest.main()
