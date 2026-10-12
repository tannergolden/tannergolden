# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of chess, held to the numbers everyone checks a move generator against.

  python3 -m unittest discover -s .github/scripts -p 'test_chess*.py'

Perft counts every sequence of legal moves to a depth from a position; the
positions below are the standard ones, chosen because they hold every
awkward rule: castling through and out of check, en passant that uncovers a
check, promotions with and without capture, pins. Set CHESS_PERFT_DEEP=1 to
add the deepest counts, which take a few seconds more.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("chess_rules", HERE / "chess_rules.py")
rules = importlib.util.module_from_spec(spec)
sys.modules["chess_rules"] = rules  # dataclasses look their module up while the class is built
spec.loader.exec_module(rules)

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PERFT = [
    (rules.START, [20, 400, 8902], [197281]),
    (KIWIPETE, [48, 2039], [97862]),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [14, 191, 2812, 43238], []),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [6, 264, 9467], []),
    ("r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1", [6, 264, 9467], []),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [44, 1486], [62379]),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", [46, 2079], [89890]),
]


def position(fen: str = rules.START):
    return rules.Position.from_fen(fen)


def play(*ucis: str, fen: str = rules.START):
    """The positions after each move, from the first: every move must be legal."""
    positions = [position(fen)]
    for uci in ucis:
        legal = {move.uci: move for move in rules.legal_moves(positions[-1])}
        assert uci in legal, f"{uci} is not legal in {positions[-1].fen}"
        positions.append(rules.make(positions[-1], legal[uci]))
    return positions


def names(fen: str, *ucis: str) -> list[str]:
    """Each move's SAN, played one after another from the FEN."""
    positions, out = [position(fen)], []
    for uci in ucis:
        move = rules.Move.from_uci(uci)
        out.append(rules.san(positions[-1], move))
        positions.append(rules.make(positions[-1], move))
    return out


class Perft(unittest.TestCase):
    def test_every_standard_position_counts_true(self):
        deep = os.environ.get("CHESS_PERFT_DEEP") == "1"
        for fen, counts, deeper in PERFT:
            for depth, count in enumerate(counts + (deeper if deep else []), 1):
                with self.subTest(fen=fen, depth=depth):
                    self.assertEqual(rules.perft(position(fen), depth), count)


class Fen(unittest.TestCase):
    def test_round_trips(self):
        for fen, _, _ in PERFT:
            self.assertEqual(position(fen).fen, fen)

    def test_after_a_double_step_names_the_square_passed(self):
        self.assertEqual(play("e2e4")[-1].fen, "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

    def test_refuses_what_is_not_a_position(self):
        for fen in ("8/8/8/8/8/8/8/8 w - - 0 1",  # no kings
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1",
                    "rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1",  # e3 with White to move
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KKq - 0 1",
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP w KQkq - 0 1"):
            with self.subTest(fen=fen), self.assertRaises(rules.FenError):
                position(fen)

    def test_refuses_a_position_no_game_can_reach(self):
        for fen in ("4k2R/8/8/8/8/8/8/4K3 w - - 0 1",  # Black in check with White to move
                    "8/8/8/8/8/8/8/Kk6 w - - 0 1",  # kings side by side
                    "4k3/8/8/3PN3/8/8/8/4K3 w - e6 0 1",  # no pawn passed e6: a knight stands on e5
                    "4k3/8/4N3/3P4/8/8/8/4K3 w - e6 0 1",  # nor with a knight on e6 itself
                    "rnbqkbnr/pppp0ppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "rnbqkbnr/pppppppp/44/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "rnbqkbnr/pppppppp/\uff18/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - \u00b2 1",
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0",
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 1234567 1"):
            with self.subTest(fen=fen), self.assertRaises(rules.FenError):
                position(fen)

    def test_keeps_only_the_castling_rights_its_pieces_still_hold_in_order(self):
        self.assertEqual(position("4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1").castling, "")
        self.assertEqual(position("r3k2r/8/8/8/8/8/8/R3K2R w kqKQ - 0 1").castling, "KQkq")
        self.assertEqual(position("r3k3/8/8/8/8/8/8/4K2R w KQkq - 0 1").castling, "Kq")
        shuffle = ["a1b3", "e8f8", "b3a1", "f8e8"] * 4  # a knight's walk: a rook was never there to castle with
        positions = play(*shuffle, fen="4k3/8/8/8/3R4/8/8/N3K3 w Q - 0 1")
        self.assertEqual([i for i in range(1, len(positions) + 1) if rules.ending(positions[:i])][:1], [17])

    def test_a_move_or_a_square_out_of_shape_is_refused(self):
        for text in ("", "e2", "i2e4", "E2E4", "0000", "e0e4", "h0h1", "e9e4", "e\u0662e\u0664", "e7e8Q", "e7e8k"):
            with self.subTest(uci=text), self.assertRaises(ValueError):
                rules.Move.from_uci(text)
        for text in ("", "e", "e0", "i1", "e10", "E2"):
            with self.subTest(square=text), self.assertRaises(ValueError):
                rules.square(text)


class SpecialMoves(unittest.TestCase):
    def ucis(self, fen: str) -> set[str]:
        return {move.uci for move in rules.legal_moves(position(fen))}

    def test_each_side_castles_only_on_its_own_rights(self):
        both = "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"
        self.assertLessEqual({"e8g8", "e8c8"}, self.ucis(both))
        whites_only = "r3k2r/8/8/8/8/8/8/R3K2R b KQ - 0 1"
        self.assertFalse({"e8g8", "e8c8"} & self.ucis(whites_only))
        self.assertFalse({"e1g1", "e1c1"} & self.ucis("r3k2r/8/8/8/8/8/8/R3K2R w kq - 0 1"))

    def test_never_castles_out_of_through_or_into_check(self):
        self.assertNotIn("e1g1", self.ucis("4r1k1/8/8/8/8/8/8/4K2R w K - 0 1"))  # out of check
        self.assertNotIn("e1g1", self.ucis("5rk1/8/8/8/8/8/8/4K2R w K - 0 1"))  # through f1
        self.assertNotIn("e1g1", self.ucis("k5r1/8/8/8/8/8/8/4K2R w K - 0 1"))  # into g1
        self.assertIn("e1c1", self.ucis("1r2k3/8/8/8/8/8/8/R3K3 w Q - 0 1"))  # b1 attacked is fine

    def test_castling_moves_the_rook_and_spends_the_rights(self):
        after = play("e1g1", fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")[-1]
        self.assertEqual(after.fen, "r3k2r/8/8/8/8/8/8/R4RK1 b kq - 1 1")
        after = play("e8c8", fen="r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")[-1]
        self.assertEqual(after.fen, "2kr3r/8/8/8/8/8/8/R3K2R w KQ - 1 2")

    def test_a_rook_taken_in_its_corner_takes_its_right_with_it(self):
        after = play("a1a8", fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")[-1]
        self.assertEqual(after.castling, "Kk")

    def test_en_passant_takes_the_pawn_beside_and_lasts_one_move(self):
        positions = play("e2e4", "a7a6", "e4e5", "d7d5")
        self.assertIn("e5d6", {move.uci for move in rules.legal_moves(positions[-1])})
        after = play("e5d6", fen=positions[-1].fen)[-1]
        self.assertEqual(after.board[rules.square("d5")], "")
        self.assertEqual(after.board[rules.square("d6")], "P")
        later = play("a2a3", "a6a5", fen=positions[-1].fen)[-1]
        self.assertNotIn("e5d6", {move.uci for move in rules.legal_moves(later)})

    def test_en_passant_that_uncovers_the_king_is_illegal(self):
        self.assertNotIn("e5d6", self.ucis("8/8/8/K2pP2r/8/8/8/7k w - d6 0 1"))

    def test_a_pawn_on_the_last_rank_becomes_any_of_four(self):
        self.assertLessEqual({"a7a8q", "a7a8r", "a7a8b", "a7a8n"}, self.ucis("7k/P7/8/8/8/8/8/K7 w - - 0 1"))
        self.assertNotIn("a7a8", self.ucis("7k/P7/8/8/8/8/8/K7 w - - 0 1"))


class Notation(unittest.TestCase):
    def test_names_moves_as_a_score_sheet_does(self):
        self.assertEqual(names(rules.START, "e2e4", "d7d5", "e4d5", "g8f6", "g1f3"),
                         ["e4", "d5", "exd5", "Nf6", "Nf3"])

    def test_names_castling_promotion_check_and_mate(self):
        self.assertEqual(names("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1", "e8c8"), ["O-O", "O-O-O"])
        self.assertEqual(names("3r3k/2P5/8/8/8/8/8/K7 w - - 0 1", "c7d8n"), ["cxd8=N"])
        self.assertEqual(names("7k/P7/8/8/8/8/8/K7 w - - 0 1", "a7a8q"), ["a8=Q+"])
        self.assertEqual(names(rules.START, "f2f3", "e7e5", "g2g4", "d8h4"), ["f3", "e5", "g4", "Qh4#"])

    def test_tells_twin_pieces_apart_by_file_then_rank_then_both(self):
        self.assertEqual(names("4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1", "b1d2"), ["Nbd2"])
        self.assertEqual(names("4k3/R7/8/8/8/8/8/R3K3 w - - 0 1", "a1a3"), ["R1a3"])
        # Queens on e4, h4 and h1 can all reach e1: h4's file is shared with h1, its rank with e4.
        self.assertEqual(names("1k6/8/8/8/4Q2Q/8/8/K6Q w - - 0 1", "h4e1"), ["Qh4e1"])


class Endings(unittest.TestCase):
    def test_checkmate_names_the_winner(self):
        end = rules.ending(play("f2f3", "e7e5", "g2g4", "d8h4"))
        self.assertEqual((end.reason, end.winner, end.result), ("checkmate", "b", "0-1"))

    def test_stalemate_is_a_draw(self):
        end = rules.ending([position("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")])
        self.assertEqual((end.reason, end.winner, end.result), ("stalemate", None, "1/2-1/2"))

    def test_too_little_material_is_a_draw(self):
        for fen in ("8/8/8/4k3/8/8/8/4K3 w - - 0 1", "8/8/8/4k3/8/8/8/4KB2 w - - 0 1",
                    "8/8/8/4k3/8/8/8/4KN2 w - - 0 1", "2b5/8/8/4k3/8/8/8/4KB2 w - - 0 1"):
            with self.subTest(fen=fen):
                self.assertEqual(rules.ending([position(fen)]).reason, "insufficient material")
        for fen in ("1b6/8/8/4k3/8/8/8/4KB2 w - - 0 1", "8/8/8/4k3/8/8/8/3NKN2 w - - 0 1",
                    "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1", "n7/8/8/4k3/8/8/8/4KB2 w - - 0 1"):
            with self.subTest(fen=fen):
                self.assertIsNone(rules.ending([position(fen)]))

    def test_kings_shut_out_behind_locked_pawns_are_a_dead_draw(self):
        for fen in ("8/8/8/1k6/p1p1p1p1/P1P1P1P1/8/7K w - - 0 1", "8/8/8/1k6/p1p1p1p1/P1P1P1P1/8/7K b - - 0 1"):
            with self.subTest(fen=fen):
                self.assertEqual(rules.ending([position(fen)]).reason, "dead position")
        for fen in ("8/8/8/1k6/p1p1p1p1/P1P1P3/8/7K w - - 0 1",  # a gap: g4 can push
                    "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1",  # a free pawn
                    "8/8/8/1k6/p1p1p1p1/P1P1P1P1/7N/7K w - - 0 1"):  # a knight can break in
            with self.subTest(fen=fen):
                self.assertIsNone(rules.ending([position(fen)]))
        self.assertTrue(rules.dead(position("8/8/8/4k3/8/8/8/4K3 w - - 0 1")), "kings alone are dead too")

    def test_seventy_five_quiet_moves_each_are_a_draw_but_not_seventy_four(self):
        self.assertIsNone(rules.ending([position("4k3/8/8/8/8/8/R7/4K3 w - - 149 90")]))
        self.assertEqual(rules.ending([position("4k3/8/8/8/8/8/R7/4K3 w - - 150 90")]).reason,
                         "seventy-five-move rule")

    def test_a_fifth_repetition_is_a_draw_but_not_a_fourth(self):
        shuffle = ["g1f3", "g8f6", "f3g1", "f6g8"]
        positions = play(*shuffle * 3)  # the start position, a fourth time
        self.assertIsNone(rules.ending(positions))
        positions = play(*shuffle * 4)  # and a fifth
        self.assertEqual(rules.ending(positions).reason, "fivefold repetition")

    def test_an_en_passant_nobody_can_take_does_not_tell_positions_apart(self):
        after_double = play("e2e4")[-1]
        same = rules.Position(after_double.board, "b", after_double.castling, None, 0, 1)
        self.assertEqual(rules.repetition_key(after_double), rules.repetition_key(same))


if __name__ == "__main__":
    unittest.main()
