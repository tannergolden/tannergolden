# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of checkers, held to the numbers everyone checks a move generator against.

  python3 -m unittest discover -s .github/scripts -p 'test_checkers*.py'

Perft counts every sequence of legal moves to a depth from the start, and the
counts below are the published ones for English draughts. They hold the men's
steps, jumps and multi-jumps, which the opening reaches, but no king; a second,
plainer reading of the rules, which lifts each piece it takes as it goes, holds
the kings to the same moves on positions drawn at random. Set
CHECKERS_PERFT_DEEP=1 to add the deepest counts, which take half a minute more.
"""
from __future__ import annotations

import copy
import dataclasses
import os
import pickle
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checkers_rules as rules
from checkers_rules import DARK, LIGHT, START, Ending, Move, Position, ending, find, legal_moves, make

PERFT = [7, 49, 302, 1469, 7361, 36768, 179740]
DEEPER = [845931, 3963680]
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
# Eighty-one plies of kings walking, nothing taken and no position three times (found by a seeded search).
KINGS = "B:WK29,K32:BK1,K4"
WALK = ["1-5", "29-25", "4-8", "25-29", "5-9", "32-28", "9-5", "28-32", "8-11", "29-25", "11-15", "25-21", "15-18",
        "21-25", "18-15", "32-28", "15-11", "28-32", "11-16", "25-29", "16-19", "32-27", "19-15", "27-23", "5-1",
        "23-27", "15-11", "27-31", "11-8", "31-26", "8-11", "26-23", "11-15", "23-26", "1-6", "26-23", "6-2", "23-26",
        "15-10", "26-23", "2-7", "29-25", "10-14", "23-27", "7-10", "27-32", "14-9", "32-28", "10-7", "28-24", "9-6",
        "25-22", "7-11", "22-25", "11-15", "25-29", "15-11", "24-28", "6-10", "28-32", "11-7", "32-27", "10-14",
        "29-25", "14-10", "27-32", "10-6", "25-29", "7-11", "32-27", "6-10", "27-31", "10-14", "31-27", "14-9", "27-32",
        "11-7", "32-27", "9-13", "27-31", "13-17"]
# The same, with a man moving at the forty-first ply, so the count starts again from there.
KINGS_AND_A_MAN = "B:WK29,K32:BK1,K4,12"
BROKEN = ["1-6", "32-27", "6-1", "27-32", "1-5", "32-27", "4-8", "27-23", "5-1", "23-26", "8-3", "26-23", "1-6",
          "23-19", "6-2", "19-24", "2-7", "24-27", "3-8", "27-31", "8-3", "29-25", "7-11", "31-27", "11-16", "25-21",
          "16-19", "27-32", "3-7", "32-28", "7-3", "28-32", "3-8", "32-27", "8-11", "27-32", "19-16", "32-28", "16-20",
          "21-17", "12-16", "17-21", "11-8", "21-25", "8-3", "25-29", "3-7", "28-32", "7-11", "32-28", "11-7", "29-25",
          "7-2", "25-22", "2-7", "28-32", "7-11", "32-28", "11-8", "22-26", "8-4", "26-22", "4-8", "22-18", "8-3",
          "28-32", "3-8", "18-14", "8-12", "14-18", "12-8", "32-27", "8-3", "18-15", "3-7", "27-32", "7-3", "32-28",
          "3-8", "28-32", "20-24", "15-10", "8-3", "10-6", "24-28", "6-1", "3-8", "32-27", "8-11", "27-32", "11-8",
          "1-5", "8-11", "5-1", "28-24", "1-5", "11-15", "5-9", "24-28", "9-5", "15-10", "32-27", "10-15", "27-31",
          "15-11", "31-26", "28-24", "5-9", "24-28", "26-31", "28-24", "9-5", "11-7", "5-1", "24-19", "31-26", "19-15",
          "26-23", "7-11", "23-27", "11-7"]
# Games from the design, the second ending on a man crowned by a double jump.
OPENING = ["11-15", "23-19", "8-11", "22-17", "10-14", "17x10", "7x14", "19x10", "6x15", "24-20", "15-18", "27-24",
           "12-16", "31-27", "3-8", "26-22", "1-6", "22x15", "11x18"]
CROWNED = ["11-15", "23-19", "8-11", "22-17", "10-14", "17x10", "7x14", "19x10", "6x15", "26-22", "3-7", "27-23",
           "4-8", "32-27", "9-13", "22-17", "13x22", "25x18x9", "5x14", "29-25", "1-5", "24-20", "15-18", "23-19",
           "7-10", "27-23", "18x27", "31x24", "11-15", "25-22", "14-18", "22-17", "2-6", "17-14", "10x17", "19x10x1"]
# The headers a game's record might carry.
HEADERS = {"Event": "@tannergolden vs. GitHub", "Site": "https://github.com/tannergolden", "Date": "2026.10.12",
           "Round": "6", "Black": "tannergolden", "White": "GitHub"}
# A dark king among four light men it can take all of, round and back to where it stood, either way round.
CIRCLE = "B:W9,10,17,18:BK6"


def position(fen: str = "") -> Position:
    return Position.from_fen(fen) if fen else START


def codes(fen: str) -> list[str]:
    return [move.code for move in legal_moves(position(fen))]


def play(*moves: str, fen: str = "") -> tuple[list[Position], list[Move]]:
    """The positions after each move, from the first, and the moves: every move must be legal."""
    positions, played = [position(fen)], []
    for code in moves:
        move = find(positions[-1], code)
        assert move is not None, f"{code} is not legal in {positions[-1].fen}"
        played.append(move)
        positions.append(make(positions[-1], move))
    return positions, played


def reference(pieces: dict[int, str], turn: str) -> list[str]:
    """Every legal move's code by a second, plainer reading of the rules: a board of rows and columns, where a
    jumping piece is moved along and each piece it takes is lifted off as it goes."""
    def headings(piece: str) -> tuple[tuple[int, int], ...]:
        rows = (1,) if piece == "d" else (-1,) if piece == "l" else (-1, 1)
        return tuple((dr, dc) for dr in rows for dc in (-1, 1))

    def number(cell: tuple[int, int]) -> int | None:
        return rules.square_at(*cell)

    def runs(board: dict, cell: tuple[int, int], piece: str, path: list[int]) -> list[list[int]]:
        out = []
        for dr, dc in headings(piece):
            over, land = (cell[0] + dr, cell[1] + dc), (cell[0] + 2 * dr, cell[1] + 2 * dc)
            if number(land) is None or land in board or board.get(over, turn).lower() == turn:
                continue
            after = dict(board)
            del after[over]
            after[land] = after.pop(cell)
            if piece.islower() and land[0] == (7 if piece == "d" else 0):
                out.append([*path, number(land)])  # crowned: the move ends here
            else:
                out += runs(after, land, piece, [*path, number(land)]) or [[*path, number(land)]]
        return out

    board = {rules.row_col(square): piece for square, piece in pieces.items()}
    mine = [(cell, piece) for cell, piece in board.items() if piece.lower() == turn]
    found = ["x".join(map(str, path)) for cell, piece in mine for path in runs(board, cell, piece, [number(cell)])]
    if not found:
        found = [f"{number(cell)}-{number((cell[0] + dr, cell[1] + dc))}" for cell, piece in mine
                 for dr, dc in headings(piece)
                 if number((cell[0] + dr, cell[1] + dc)) and (cell[0] + dr, cell[1] + dc) not in board]
    return sorted(found, key=lambda code: [int(n) for n in code.replace("x", "-").split("-")])


def scattered(n: int, seed: int = 1):
    """`n` positions with pieces scattered at random, kings among them."""
    rng = random.Random(seed)
    while n:
        squares = rng.sample(range(1, 33), rng.randint(2, 20))
        pieces = {}
        for i, square in enumerate(squares):
            side = DARK if i % 2 else LIGHT
            pieces[square] = side.upper() if rng.random() < 0.4 or square in rules.CROWN[side] else side
        try:
            yield Position(pieces, rng.choice((DARK, LIGHT)))
        except ValueError:  # more than twelve a side
            continue
        n -= 1


def games(n: int, seed: int = 7):
    """`n` games of random legal moves, each as its positions and moves, played to their end or two hundred plies."""
    rng = random.Random(seed)
    for _ in range(n):
        positions, moves = [START], []
        while len(moves) < 200 and not ending(positions, moves):
            move = rng.choice(legal_moves(positions[-1]))
            moves.append(move)
            positions.append(make(positions[-1], move))
        yield positions, moves


class Perft(unittest.TestCase):
    def test_the_start_counts_true(self):
        deep = os.environ.get("CHECKERS_PERFT_DEEP") == "1"
        for depth, count in enumerate(PERFT + (DEEPER if deep else []), 1):
            with self.subTest(depth=depth):
                self.assertEqual(rules.perft(START, depth), count)

    def test_kings_move_as_a_plainer_reading_of_the_rules_says(self):
        kings = jumps = 0
        for found in scattered(1500):
            with self.subTest(fen=found.fen):
                self.assertEqual(codes(found.fen), reference(dict(found.pieces), found.turn))
            kings += any(piece.isupper() for piece in found.pieces.values())
            jumps += any(len(move.captures) > 1 for move in legal_moves(found))
        self.assertGreater(kings, 1000)
        self.assertGreater(jumps, 150)


class Moves(unittest.TestCase):
    def test_the_opening_moves_are_the_seven_steps_in_order(self):
        self.assertEqual(codes(START.fen), ["9-13", "9-14", "10-14", "10-15", "11-15", "11-16", "12-16"])
        self.assertEqual(legal_moves(START), sorted(legal_moves(START)), "the list's order is Move's own")

    def test_a_code_writes_every_square_a_piece_stands_on(self):
        self.assertEqual(Move((11, 15)).code, "11-15")
        self.assertEqual(Move((22, 15), (18,)).code, "22x15")
        self.assertEqual(Move((22, 15, 8), (18, 11)).code, "22x15x8")

    def test_a_man_steps_forward_only_and_a_king_both_ways(self):
        self.assertEqual(codes("B:W32:B18"), ["18-22", "18-23"])
        self.assertEqual(codes("W:W18:B1"), ["18-14", "18-15"])
        self.assertEqual(codes("B:W32:BK18"), ["18-14", "18-15", "18-22", "18-23"])
        self.assertEqual(codes("B:W32:B12"), ["12-16"], "the side of the board leaves one way forward")

    def test_a_capture_is_compulsory_and_any_jump_may_be_chosen(self):
        self.assertEqual(codes("B:W18:B1,14"), ["14x23"], "no step while a jump is there to make")
        # One jump takes two, the other one; either may be chosen, not only the longer.
        self.assertEqual(codes("B:W14,15,22:B10"), ["10x17x26", "10x19"])
        self.assertEqual([len(move.captures) for move in legal_moves(position("B:W14,15,22:B10"))], [2, 1])

    def test_a_jump_goes_on_while_it_can_and_names_every_landing(self):
        move = legal_moves(position("B:W6,15,24,32:B1"))
        self.assertEqual(move, [Move((1, 10, 19, 28), (6, 15, 24), False)])

    def test_a_man_jumps_only_forward_and_a_king_both_ways(self):
        self.assertEqual(codes("B:W11:B15"), ["15-18", "15-19"])
        self.assertEqual(codes("B:W11:BK15"), ["15x8"])

    def test_a_man_crowned_in_the_middle_of_a_jump_stops_there(self):
        # The light man takes 7 and lands on 3, the far row: crowned, its move ends, though a king could take 8 next.
        self.assertEqual(legal_moves(position("W:W10:B7,8")), [Move((10, 3), (7,), True)])
        self.assertEqual(codes("W:WK10:B7,8"), ["10x3x12"], "a king that was one already goes on")
        after = make(position("W:W10:B7,8"), find(position("W:W10:B7,8"), "10x3"))
        self.assertEqual(after.fen, "B:WK3:B8")

    def test_a_man_crowned_by_a_double_jump(self):
        positions, moves = play(*CROWNED)
        self.assertEqual(moves[-1], Move((19, 10, 1), (15, 6), True))
        self.assertEqual(positions[-1].fen, "B:WK1,20,21,24,28,30:B5,8,12,17,18")
        self.assertEqual(codes(positions[-1].fen), ["5-9", "8-11", "12-16", "17-22", "18-22", "18-23"])

    def test_a_man_crowned_by_a_step(self):
        move = find(position("B:W30:B1,25"), "25-29")
        self.assertTrue(move.crowns)
        self.assertEqual(make(position("B:W30:B1,25"), move).fen, "W:W30:B1,K29")
        self.assertFalse(find(position("B:W30:BK25,1"), "25-29").crowns, "a king is crowned only once")

    def test_a_king_takes_many_and_may_come_round_to_where_it_stood(self):
        self.assertEqual(codes(CIRCLE), ["6x13x22x15x6", "6x15x22x13x6"])
        circle = find(position(CIRCLE), "6x15x22x13x6")
        self.assertEqual((circle.captures, circle.crowns), ((10, 18, 17, 9), False))
        self.assertEqual(make(position(CIRCLE), circle).fen, "W:W:BK6", "back where it stood, every light man gone")
        # Nine taken in one move, crossing two empty squares twice but no piece twice.
        long = legal_moves(position("B:W6,8,9,10,11,13,17,18,19,25,26,27:BK32"))
        self.assertIn("32x23x14x7x16x23x30x21x14x5", [move.code for move in long])
        self.assertEqual(max(len(move.captures) for move in long), 9)

    def test_the_design_s_game_plays_through(self):
        positions, _ = play(*OPENING)
        self.assertEqual(positions[-1].fen, "W:W20,21,24,25,27,28,29,30,32:B2,4,5,6,8,9,14,16,18")
        self.assertEqual(codes(positions[-1].fen), ["20x11"])
        self.assertTrue(rules.must_jump(positions[-1]))
        self.assertFalse(rules.must_jump(START))

    def test_make_takes_the_jumped_off_and_leaves_the_position_it_was_given(self):
        before = position("B:W14,15,22:B10")
        after = make(before, find(before, "10x17x26"))
        self.assertEqual(after.fen, "W:W15:B26")
        self.assertEqual(after.turn, LIGHT)
        self.assertEqual(before.fen, "B:W14,15,22:B10")

    def test_find_gives_the_legal_move_written_so_and_nothing_else(self):
        self.assertEqual(find(START, "11-15"), Move((11, 15), (), False))
        for code in ("15-11", "11x15", "11-15 ", "11\u201315", "", "0-4", "33-29", "11", None, 1115):
            with self.subTest(code=code):
                self.assertIsNone(find(START, code))


class Fen(unittest.TestCase):
    def test_writes_whose_turn_then_light_then_dark_kings_marked_squares_ascending(self):
        self.assertEqual(START.fen, "B:W21,22,23,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,6,7,8,9,10,11,12")
        self.assertEqual(Position({30: "L", 21: "l", 22: "l", 9: "D", 1: "d", 2: "d"}, DARK).fen,
                         "B:W21,22,K30:B1,2,K9")
        self.assertEqual(Position({5: "D"}, LIGHT).fen, "W:W:BK5", "a side with nothing left lists nothing")

    def test_round_trips_every_position_of_many_games(self):
        for positions, _ in games(20):
            for found in positions:
                self.assertEqual(Position.from_fen(found.fen), found)
                self.assertEqual(Position.from_fen(found.fen).fen, found.fen)

    def test_reads_a_list_in_any_order_and_writes_it_in_order(self):
        self.assertEqual(Position.from_fen("W:WK30,21:B9,1").fen, "W:W21,K30:B1,9")

    def test_refuses_what_is_not_a_position(self):
        for fen in ("", "B", "B:W21:B1:", "X:W21:B1", "b:W21:B1", "B:B1:W21", "B:W21", "B:W21;B1", "B:W21:B1.",
                    " B:W21:B1", "B:W21:B1 ", "B:W 21:B1", "B:W21,:B1", "B:W,21:B1", "B:W21,,22:B1", "B:WK:B1",
                    "B:Wk21:B1", "B:WKK21:B1", "B:W21K:B1", "B:W0:B1", "B:W33:B1", "B:W021:B1", "B:W1-12:B21",
                    "B:W\u0662\u0661:B1", "B:W21:B\uff11", None, 21):
            with self.subTest(fen=fen), self.assertRaises(rules.FenError):
                Position.from_fen(fen)

    def test_refuses_a_position_no_game_can_reach(self):
        for fen in ("B:W21,21:B1",  # one square twice
                    "B:W21:B21",  # a square on both sides
                    "B:W13,14,15,16,17,18,19,20,21,22,23,24,25:B1",  # thirteen light pieces
                    "B:W21:BK1,K2,K3,K4,K5,K6,K7,K8,K9,K10,K11,K12,K13",  # thirteen dark, kings among them
                    "B:W21:B29",  # a dark man on its far row, never crowned
                    "W:W1:B12",  # a light man on its far row
                    "B:W:B1",  # light made the last move with no piece to make it with
                    "W:W21:B",  # and dark
                    "B:W:B"):
            with self.subTest(fen=fen), self.assertRaises(rules.FenError):
                Position.from_fen(fen)
        self.assertEqual(Position.from_fen("W:W:B1").fen, "W:W:B1", "the side to move may have nothing left: it lost")
        self.assertEqual(Position.from_fen("B:WK1:BK32").fen, "B:WK1:BK32", "kings may stand on any square")


class Positions(unittest.TestCase):
    def test_a_position_is_checked_when_it_is_made(self):
        for pieces, turn in (({0: "d"}, DARK), ({33: "l"}, DARK), ({"1": "d", 21: "l"}, DARK),
                             ({True: "d", 21: "l"}, DARK), ({1: "x", 21: "l"}, DARK), ({1: "dd", 21: "l"}, DARK),
                             ({1: "d", 21: "l"}, "w"), ({1: "d", 21: "l"}, "D"), ([(1, "d")], DARK),
                             ({29: "d", 21: "l"}, DARK), ({1: "d"}, DARK)):
            with self.subTest(pieces=pieces, turn=turn), self.assertRaises((ValueError, TypeError)):
                Position(pieces, turn)
        with self.assertRaises(TypeError):
            Position([(1, "d"), (21, "l")], DARK)

    def test_a_position_never_changes_and_equal_ones_are_one(self):
        with self.assertRaises(TypeError):
            START.pieces[13] = "d"
        with self.assertRaises(TypeError):
            del START.pieces[1]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            START.turn = LIGHT
        same = Position(dict(reversed(list(START.pieces.items()))), DARK)
        self.assertEqual(same, START)
        self.assertEqual(len({same, START, make(START, find(START, "11-15"))}), 2)
        self.assertEqual(copy.deepcopy(START), START)
        self.assertEqual(pickle.loads(pickle.dumps(START)), START)
        self.assertEqual(dataclasses.replace(START, turn=LIGHT).fen, START.fen.replace("B:", "W:", 1))


class Endings(unittest.TestCase):
    def test_a_side_with_its_last_piece_taken_has_no_move_and_loses(self):
        positions, moves = play("6x15x22x13x6", fen=CIRCLE)
        self.assertEqual(ending(positions, moves), Ending(DARK, "no move left", "1-0"))

    def test_a_side_whose_pieces_are_all_shut_in_loses(self):
        # The light man on 5 has one way forward, to 1, and the dark king steps there.
        positions, moves = play("6-1", fen="B:W5:BK6")
        self.assertEqual(ending(positions, moves), Ending(DARK, "no move left", "1-0"))
        # The dark king on 32 could jump 27 to 23, until a light man steps there; the man on 28 is boxed in behind it.
        positions, moves = play("26-23", fen="W:W26,27:B28,K32")
        self.assertEqual(legal_moves(positions[-1]), [])
        self.assertEqual(ending(positions, moves), Ending(LIGHT, "no move left", "0-1"))

    def test_the_same_position_a_third_time_is_a_draw_but_not_a_second(self):
        there_and_back = ["1-6", "32-27", "6-1", "27-32"]
        positions, moves = play(*there_and_back, fen="B:WK32:BK1")
        self.assertIsNone(ending(positions, moves), "the first position a second time")
        positions, moves = play(*there_and_back * 2, fen="B:WK32:BK1")
        self.assertIsNone(ending(positions[:-1], moves[:-1]))
        self.assertEqual(ending(positions, moves), Ending(None, "repetition", "1/2-1/2"))

    def test_forty_moves_each_with_no_capture_and_no_man_moved_are_a_draw(self):
        positions, moves = play(*WALK[:79], fen=KINGS)
        self.assertEqual(rules.quiet_plies(positions, moves), 79)
        self.assertIsNone(ending(positions, moves))
        positions, moves = play(*WALK[:80], fen=KINGS)
        self.assertEqual(ending(positions, moves), Ending(None, "forty moves", "1/2-1/2"))

    def test_a_man_moved_starts_the_count_again(self):
        self.assertEqual(BROKEN[40], "12-16")
        positions, moves = play(*BROKEN[:81], fen=KINGS_AND_A_MAN)
        self.assertEqual(rules.quiet_plies(positions, moves), 40)
        positions, moves = play(*BROKEN[:120], fen=KINGS_AND_A_MAN)
        self.assertIsNone(ending(positions, moves))
        positions, moves = play(*BROKEN, fen=KINGS_AND_A_MAN)
        self.assertEqual(ending(positions, moves), Ending(None, "forty moves", "1/2-1/2"))

    def test_a_capture_starts_the_count_again_even_by_a_king(self):
        positions, moves = play("6x15x22x13x6", fen=CIRCLE)
        self.assertEqual(rules.quiet_plies(positions, moves), 0)
        self.assertEqual(rules.quiet_plies(*play("11-15")), 0)

    def test_every_random_game_ends_by_the_rules_and_only_at_its_end(self):
        reasons = set()
        for positions, moves in games(40):
            end = ending(positions, moves)
            if end:
                reasons.add(end.reason)
                self.assertIn(end.reason, rules.REASONS)
                self.assertEqual(end.result, rules.RESULTS[end.winner])
                self.assertTrue(all(ending(positions[:i], moves[:i - 1]) is None for i in range(1, len(positions))))
        self.assertIn("no move left", reasons)

    def test_the_positions_and_moves_must_match_in_number(self):
        for positions, moves in (([], []), ([START], [find(START, "11-15")]), ([START, START], [])):
            with self.assertRaises(ValueError):
                ending(positions, moves)


class WhyIllegal(unittest.TestCase):
    def assertWhy(self, fen: str, code, why: str):
        with self.subTest(fen=fen, code=code):
            said = rules.why_illegal(position(fen), code)
            self.assertEqual(said, why)
            self.assertFalse(any(dash in said for dash in DASHES))
            if why:
                self.assertIsNone(find(position(fen), code) if isinstance(code, str) else None)

    def test_a_legal_move_has_no_reason(self):
        self.assertWhy("", "11-15", "")
        self.assertWhy("B:W14,15,22:B10", "10x19", "")

    def test_a_code_out_of_shape_or_off_the_board(self):
        shape = "a move is written square to square, such as `11-15` for a step or `22x15x8` for a jump"
        for code in ("", "11", "11_15", "11-15-19", "11-x15", "x11", "11x", "a-b", " 11-15", "11-15 ", "11\u201315",
                     "\u0661\u0661-\u0661\u0665", None, 1115):
            self.assertWhy("", code, shape)
        self.assertWhy("", "0-4", "there's no square 0, as the squares are numbered 1 to 32")
        self.assertWhy("", "11-33", "there's no square 33, as the squares are numbered 1 to 32")
        self.assertWhy("", "09-13", "there's no square 09, as the squares are numbered 1 to 32")

    def test_whose_piece_it_is(self):
        self.assertWhy("", "14-18", "there is no man of yours on 14")
        self.assertWhy("", "22-18", "the man on 22 is Light's")
        self.assertWhy("B:WK22:B1", "22-18", "the king on 22 is Light's")

    def test_a_capture_is_compulsory(self):
        self.assertWhy("W:W22,24:B18,1", "24-19", "a capture is compulsory, so the man on 22 must jump")
        self.assertWhy("W:W22,23:B18,1", "22-17", "a capture is compulsory, so a man on 22 or 23 must jump")
        self.assertWhy("W:WK3,23:B7,18", "23-19", "a capture is compulsory, so the king on 3 or the man on 23 must jump")

    def test_a_jump_written_as_a_step_and_a_step_as_a_jump(self):
        self.assertWhy("W:W22:B18,1", "22-15", "a jump is written with an x, as `22x15`")
        self.assertWhy("", "11x15", "a step is written with a dash, as `11-15`")

    def test_a_jump_that_stops_short_or_leaves_out_a_landing(self):
        self.assertWhy("B:W6,15,24,32:B1", "1x10", "a jump goes on while it can take more, so this one carries on as"
                                                  " `1x10x19x28`")
        self.assertWhy("B:W6,15,24,32:B1", "1x28", "a jump names every square it lands on, so this one is `1x10x19x28`")
        self.assertWhy(CIRCLE, "6x6", "a jump names every square it lands on, so this one is `6x13x22x15x6` or"
                                      " `6x15x22x13x6`")

    def test_a_step_that_goes_nowhere_a_step_can(self):
        self.assertWhy("", "11-20", "a step goes to the next square along a diagonal, and 20 isn't next to 11")
        self.assertWhy("", "11-11", "a step goes to the next square along a diagonal, and 11 isn't next to 11")
        self.assertWhy("B:W32:B15", "15-11", "a man only moves forward, toward the far row, and only a king can move back")
        self.assertWhy("", "9-5", "a man only moves forward, toward the far row, and only a king can move back")
        self.assertWhy("", "5-9", "there's already a man on 9")

    def test_a_jump_that_goes_nowhere_a_jump_can(self):
        self.assertWhy("B:W32:B11", "11x18", "there's nothing on 15 to jump")
        self.assertWhy("B:W32:B11,15", "11x18", "the man on 15 is yours, and a jump only takes the other side's"
                                                " pieces")
        self.assertWhy("B:W15,18:B11", "11x18", "a jump lands on an empty square, and there's a man on 18")
        self.assertWhy("B:W15:B11", "11x19", "a jump goes over the next square on a diagonal to the one beyond it,"
                                             " and 19 isn't a jump from 11")
        self.assertWhy("B:W15:B11", "11x20", "there's nothing on 16 to jump")
        self.assertWhy("B:W11:B15,1", "15x8", "a man only jumps forward, toward the far row, and only a king can jump back")
        self.assertWhy(CIRCLE, "6x15x6", "the man on 10 is taken already, and no piece is taken twice")
        self.assertWhy("W:W10:B7,8", "10x3x12", "a man is crowned when it reaches the far row, and its move ends there,"
                                                " on 3")

    def test_a_game_over_has_no_move_at_all(self):
        self.assertWhy("W:W:B1", "21-17", "Light has no move left, so the game is over")


class Record(unittest.TestCase):
    def test_a_record_has_its_headers_its_numbered_moves_and_its_result(self):
        record = rules.pdn(OPENING[:4], HEADERS, "*")
        self.assertEqual(record, '[Event "@tannergolden vs. GitHub"]\n[Site "https://github.com/tannergolden"]\n'
                                 '[Date "2026.10.12"]\n[Round "6"]\n[Black "tannergolden"]\n[White "GitHub"]\n'
                                 '[Result "*"]\n[GameType "21"]\n\n1. 11-15 23-19 2. 8-11 22-17 *\n')

    def test_a_comment_after_a_move_brings_the_reply_its_number(self):
        moves = [f"{code} {{{'tannergolden' if i % 2 == 0 else 'octocat'}}}" for i, code in enumerate(CROWNED)]
        record = rules.pdn(moves, HEADERS, "0-1", note="Light crowned a king.")
        body = record.split("\n\n", 1)[1]
        self.assertTrue(body.startswith("1. 11-15 {tannergolden} 1... 23-19 {octocat} 2. 8-11 {tannergolden}"), body)
        self.assertTrue(" ".join(body.split()).endswith("18... 19x10x1 {octocat} {Light crowned a king.} 0-1"),
                        body)
        self.assertTrue(all(len(line) <= 79 for line in record.splitlines()))
        self.assertIn('[Result "0-1"]\n[GameType "21"]\n', record)
        self.assertFalse(any(dash in record for dash in DASHES))

    def test_a_game_from_a_position_with_light_to_move_opens_on_light_s_reply(self):
        record = rules.pdn(["27-23", "19x26"], {"FEN": "W:W27:B19,22,26"}, "1-0")
        self.assertEqual(record.split("\n\n")[1], "1... 27-23 2. 19x26 1-0\n")

    def test_header_values_are_escaped_and_the_record_is_refused_when_it_would_not_read_back(self):
        record = rules.pdn([], {"Event": 'The "Big" \\ Game'}, "1/2-1/2")
        self.assertIn('[Event "The \\"Big\\" \\\\ Game"]', record)
        for moves, headers, result in ((["11-15"], {}, "2-0"), (["11-15 23-19"], {}, "*"), (["11-15 {a}b}"], {}, "*"),
                                       (["11-33"], {}, "*"), ([], {"Result": "1-0"}, "0-1"),
                                       ([], {"GameType": "20"}, "*"), ([], {"Bad Name": "x"}, "*"),
                                       ([], {"Event": "two\nlines"}, "*"), ([], {"Event": 6}, "*"),
                                       ([], {"FEN": "nonsense"}, "*")):
            with self.subTest(moves=moves, headers=headers, result=result), self.assertRaises(ValueError):
                rules.pdn(moves, headers, result)
        with self.assertRaises(ValueError):
            rules.pdn([], {}, "*", note="a {brace}")


if __name__ == "__main__":
    unittest.main()
