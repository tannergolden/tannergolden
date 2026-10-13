# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Pentago, held to a second, plainer reading of them over many random games, and to positions set out by
hand for every way a quarter turns and a game ends.

  python3 -m unittest discover -s .github/scripts -p 'test_pentago*.py'

The plainer reading shares nothing with the rules but the holes' names: it
keeps the board as six rows of six, the top row first, sets a marble, looks
for five, turns a quarter as a picture of three rows of three is turned, and
looks again, and both readings must agree on every move of two hundred seeded
random games, either colour first, each under two ghosts set at random, which
turn with their quarters. Positions set out by hand hold the rest: five set in
a row before any quarter turns, five made by the turn for the mover, for the
other side alone and for both, and a full board.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pentago_rules as R
from pentago_rules import B, W

DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
WAYS = ("cw", "acw")
# Thirty-four marbles in, two ghosts on quarters' centres, and no five for either colour at any point: the board fills
# (found by a seeded search).
FULL = ["a6-ul-acw", "c2-ur-acw", "e4-ul-acw", "c6-ur-acw", "e3-ul-acw", "f3-ll-cw", "b5-ll-acw", "a3-ur-acw",
        "b3-ur-acw", "a1-ll-acw", "e1-lr-acw", "c5-ur-acw", "f5-ur-cw", "f4-ul-cw", "a6-ul-acw", "c2-ur-acw",
        "b1-ur-acw", "f1-lr-cw", "c4-lr-cw", "e3-ur-cw", "d6-lr-acw", "d4-lr-acw", "f3-lr-cw", "d5-ll-acw",
        "b6-ur-cw", "a5-ll-cw", "d3-lr-cw", "b2-ur-cw", "c3-ur-acw", "e1-lr-acw", "f5-lr-acw", "b4-lr-acw",
        "a3-ur-cw", "d6-ur-cw"]
CENTRES = ("e5", "e2")  # the ghosts of FULL, on the upper right and lower right quarters' centres


def setup(ws: str = "", bs: str = "", ghosts: str = "", first: str = W) -> R.Position:
    """A position with white marbles in the holes `ws` names, black ones in those `bs` names and a ghost in each of
    `ghosts`, every list split by spaces; `first` the colour that set the first marble."""
    holes = {**dict.fromkeys(ws.split(), W), **dict.fromkeys(bs.split(), B), **dict.fromkeys(ghosts.split(), R.GHOST)}
    return R.Position(tuple(holes.get(cell, "") for cell in R.CELLS), first)


def play(codes: list[str], first: str = W, ghosts=CENTRES) -> list[R.Position]:
    """Every position of a line from the opening, each move legal where it is made."""
    positions = [R.opening(first, ghosts)]
    for code in codes:
        assert code in R.legal(positions[-1]), (code, positions[-1].board)
        positions.append(R.make(positions[-1], code))
    return positions


# --- the plainer reading -------------------------------------------------------------------------------------------
def rows_of(position: R.Position) -> list[list[str]]:
    return [list(row) for row in position.board.split("/")]


def at(cell: str) -> tuple[int, int]:
    """A hole's row from the top and column from the left."""
    return 6 - int(cell[1]), "abcdef".index(cell[0])


# Every run of five holes in a row on six rows of six, as (row, column) pairs: across, down and both diagonals.
RUNS = [[(r + k * dr, c + k * dc) for k in range(5)] for r in range(6) for c in range(6)
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)) if 0 <= r + 4 * dr < 6 and 0 <= c + 4 * dc < 6]


def five(rows: list[list[str]], colour: str) -> list[set[str]]:
    """Every five in a row of `colour`, each as its holes."""
    return [{"abcdef"[c] + str(6 - r) for r, c in run} for run in RUNS if all(rows[r][c] == colour for r, c in run)]


def plain_make(rows: list[list[str]], colour: str, code: str) -> tuple[list[list[str]], bool]:
    """A move read plainly: the marble goes in, and unless it made five on its own, the quarter turns as a picture of
    three rows of three turns, clockwise or anticlockwise. Returns the rows after it, and whether the quarter turned."""
    cell, quarter, way = code.split("-")
    rows = [list(row) for row in rows]
    r, c = at(cell)
    rows[r][c] = colour
    if five(rows, colour):
        return rows, False
    top, left = {"ul": (0, 0), "ur": (0, 3), "ll": (3, 0), "lr": (3, 3)}[quarter]
    picture = [rows[top + i][left:left + 3] for i in range(3)]
    picture = [list(row) for row in zip(*picture[::-1])] if way == "cw" else [list(row) for row in zip(*picture)][::-1]
    for i in range(3):
        rows[top + i][left:left + 3] = picture[i]
    return rows, True


def plain_ending(rows: list[list[str]]) -> tuple[str | None, str, list[set[str]]] | None:
    white, black = five(rows, W), five(rows, B)
    if white and black:
        return None, "five for both", []
    if white or black:
        return (W, "five in a row", white) if white else (B, "five in a row", black)
    if all(hole != "." for row in rows for hole in row):
        return None, "a full board", []
    return None


def games(n: int, seed: int):
    """`n` games of seeded random play, every other one Black first, each under two ghosts set at random: every
    position of each, and the move made from it."""
    rng = random.Random(seed)
    for game in range(n):
        position = R.opening(B if game % 2 else W, rng.sample(R.CELLS, 2))
        while not R.ending(position):
            code = rng.choice(R.legal(position))
            yield position, code
            position = R.make(position, code)


class Board(unittest.TestCase):
    def test_the_holes_are_named_as_chess_names_squares_and_read_top_row_first(self):
        self.assertEqual((len(R.CELLS), R.CELLS[:2], R.CELLS[-1]), (36, ("a1", "b1"), "f6"))
        self.assertEqual((R.READING[:2], R.READING[-1]), (("a6", "b6"), "f1"))

    def test_the_four_quarters_and_a_hole_s_place_in_its_quarter(self):
        self.assertEqual([R.quarter_of(cell) for cell in ("a4", "c6", "d4", "f6", "a1", "c3", "d1", "f3")],
                         ["ul", "ul", "ur", "ur", "ll", "ll", "lr", "lr"])
        self.assertEqual([R.spot_of(cell) for cell in ("b5", "e5", "b2", "e2")], [(1, 1)] * 4, "each quarter's centre")
        self.assertEqual([R.spot_of(cell) for cell in ("a6", "f4", "d1", "c3")], [(0, 2), (2, 0), (0, 0), (2, 2)])

    def test_there_are_thirty_two_lines_of_five(self):
        self.assertEqual((len(R.LINES), len(set(R.LINES)), len(RUNS)), (32, 32, 32), "and as the plainer reading finds")
        self.assertEqual(sum(1 for line in R.LINES if R.INDEX["c3"] in line), 7, "a middle hole stands in seven")
        self.assertEqual(sum(1 for line in R.LINES if R.INDEX["a1"] in line), 3, "a corner in three")

    def test_a_position_is_written_as_six_rows_top_first_its_ghosts_as_g(self):
        position = setup(ws="a6", bs="f1", ghosts="b5 e2")
        self.assertEqual(position.board, "W...../.G..../....../....../....G./.....B")
        self.assertEqual(position.ghosts, ["b5", "e2"])
        self.assertEqual(R.opening(W, ("b5", "e2")).board, "....../.G..../....../....../....G./......")


class Turning(unittest.TestCase):
    def test_a_quarter_turns_clockwise_or_anticlockwise_as_the_board_is_seen(self):
        # The upper left quarter's ring, clockwise: each corner to the next, each edge to the next.
        ring = ["a6", "b6", "c6", "c5", "c4", "b4", "a4", "a5"]
        for i, cell in enumerate(ring):
            with self.subTest(cell=cell):
                self.assertEqual(R.landed(cell, "ul", "cw"), ring[(i + 2) % 8])
                self.assertEqual(R.landed(cell, "ul", "acw"), ring[(i - 2) % 8])
        corners = {"ur": ("d6", "f6", "f4", "d4"), "ll": ("a3", "c3", "c1", "a1"), "lr": ("d3", "f3", "f1", "d1")}
        for quarter, (upper_left, upper_right, lower_right, lower_left) in corners.items():
            with self.subTest(quarter=quarter):
                self.assertEqual([R.landed(cell, quarter, "cw") for cell in (upper_left, upper_right, lower_right,
                                                                             lower_left)],
                                 [upper_right, lower_right, lower_left, upper_left])

    def test_a_quarter_s_centre_never_moves_and_the_other_quarters_stand_still(self):
        for quarter in R.QUARTERS:
            for way in WAYS:
                for cell in R.CELLS:
                    landed = R.landed(cell, quarter, way)
                    if R.quarter_of(cell) != quarter or R.spot_of(cell) == (1, 1):
                        self.assertEqual(landed, cell, (cell, quarter, way))
                    else:
                        self.assertNotEqual(landed, cell, (cell, quarter, way))
                        self.assertEqual(R.quarter_of(landed), quarter)

    def test_four_turns_one_way_bring_a_quarter_back_and_a_turn_back_undoes_one(self):
        rng = random.Random(3)
        for _ in range(50):
            holes = tuple(rng.choice((W, B, R.GHOST, "")) for _ in R.CELLS)
            for quarter in R.QUARTERS:
                turned = holes
                for _ in range(4):
                    turned = R.turned(turned, quarter, "cw")
                self.assertEqual(turned, holes)
                self.assertEqual(R.turned(R.turned(holes, quarter, "cw"), quarter, "acw"), holes)

    def test_the_marble_set_turns_with_its_quarter(self):
        after = R.make(R.opening(W, CENTRES), "a6-ul-cw")
        self.assertEqual((after.at("a6"), after.at("c6")), ("", W))
        after = R.make(R.opening(W, CENTRES), "a6-ur-cw")
        self.assertEqual(after.at("a6"), W, "a turn of another quarter leaves it where it was set")

    def test_a_ghost_turns_with_its_quarter_and_leaves_its_hole_free(self):
        position = R.opening(W, ("b6", "e2"))
        after = R.make(position, "f1-ul-cw")
        self.assertEqual(after.ghosts, ["c5", "e2"], "the top edge's ghost goes to the right edge")
        self.assertIn("b6-ur-cw", R.legal(after))
        self.assertNotIn("c5-ur-cw", R.legal(after))
        self.assertEqual(R.make(after, "a1-ul-acw").ghosts, ["b6", "e2"], "and back, turned the other way")
        self.assertEqual(R.make(position, "f1-lr-cw").ghosts, ["b6", "e2"], "a quarter's centre never moves")


class Moves(unittest.TestCase):
    def test_every_empty_hole_with_each_of_its_eight_turns_as_the_board_is_read(self):
        self.assertEqual(R.TURNS, (("ul", "cw"), ("ul", "acw"), ("ur", "cw"), ("ur", "acw"), ("ll", "cw"),
                                   ("ll", "acw"), ("lr", "cw"), ("lr", "acw")))
        legal = R.legal(R.opening(W, CENTRES))
        self.assertEqual(len(legal), 34 * 8)
        self.assertEqual(legal[:9], ["a6-ul-cw", "a6-ul-acw", "a6-ur-cw", "a6-ur-acw", "a6-ll-cw", "a6-ll-acw",
                                     "a6-lr-cw", "a6-lr-acw", "b6-ul-cw"])
        self.assertEqual(legal, [f"{cell}-{q}-{w}" for cell in R.READING if cell not in CENTRES for q, w in R.TURNS])
        self.assertEqual(R.empty(R.opening(W, CENTRES)), [cell for cell in R.READING if cell not in CENTRES])

    def test_the_colours_take_turns_and_each_sets_seventeen_marbles(self):
        for first in (W, B):
            positions = play(FULL, first)
            with self.subTest(first=first):
                self.assertEqual([p.turn for p in positions[:4]], [first, R.other(first)] * 2)
                self.assertEqual((positions[-1].holes.count(W), positions[-1].holes.count(B)), (17, 17))
                self.assertEqual(positions[-1].first, first)

    def test_make_leaves_the_position_it_was_given(self):
        before = R.opening(W, CENTRES)
        after = R.make(before, "a6-ul-cw")
        self.assertEqual((before.at("a6"), before.at("c6"), after.at("c6")), ("", "", W))


class Endings(unittest.TestCase):
    def test_five_set_in_a_row_wins_before_any_quarter_turns(self):
        # White's a5 makes a1 to a5 on its own, so the lower left quarter, which would have broken it, never turns.
        position = setup(ws="a1 a2 a3 a4", bs="d6 e6 f6 d5", ghosts="e5 e2")
        self.assertEqual(position.turn, W)
        self.assertTrue(R.won_unturned(position, "a5-ll-cw"))
        after = R.make(position, "a5-ll-cw")
        self.assertEqual([after.at(cell) for cell in ("a1", "a2", "a3", "a4", "a5")], [W] * 5)
        self.assertEqual(R.ending(after), R.Ending(W, "five in a row", ("a1", "a2", "a3", "a4", "a5")))
        self.assertEqual(R.notation(position, "a5-ll-cw"), "a5#", "its hole alone, with the win")

    def test_five_made_by_the_turn_wins_for_the_mover(self):
        # White's c4 completes the upper left quarter's bottom row, which the turn stands up along the a-file.
        position = setup(ws="a1 a2 a3 b4", bs="d6 e6 f6 d5", ghosts="e5 e2")
        self.assertFalse(R.won_unturned(position, "c4-ul-cw"))
        after = R.make(position, "c4-ul-cw")
        self.assertEqual(R.ending(after), R.Ending(W, "five in a row", ("a1", "a2", "a3", "a4", "a5")))
        self.assertEqual(R.ending(after).result, "1-0")
        self.assertEqual(R.notation(position, "c4-ul-cw"), "c4-ul-cw#")
        self.assertEqual(R.notation(position, "c4-ul-acw"), "c4-ul-acw", "turned the other way, no five")

    def test_five_made_by_the_turn_for_the_other_side_alone_wins_it_for_them(self):
        # Black sets f5 and turns the upper left quarter, standing White's b4 and c4 up beside a1, a2 and a3.
        position = setup(ws="a1 a2 a3 b4 c4", bs="d6 e6 f6 d5", ghosts="e5 e2")
        self.assertEqual(position.turn, B)
        after = R.make(position, "f5-ul-cw")
        end = R.ending(after)
        self.assertEqual(end, R.Ending(W, "five in a row", ("a1", "a2", "a3", "a4", "a5")))
        self.assertEqual(end.result, "1-0")
        self.assertEqual(R.notation(position, "f5-ul-cw"), "f5-ul-cw#", "a # on the move that won, whoever it won for")

    def test_five_made_by_the_turn_for_both_is_a_draw(self):
        # The turn stands White's b4 and c4 up the a-file and Black's top row a6, b6 and c6 down the c-file.
        position = setup(ws="a1 a2 a3 b4 c4", bs="a6 b6 c6 c2 c3", ghosts="e5 e2")
        after = R.make(position, "f1-ul-cw")
        self.assertEqual((len(R.fives(after.holes, W)), len(R.fives(after.holes, B))), (1, 1))
        self.assertEqual(R.ending(after), R.Ending(None, "five for both"))
        self.assertEqual(R.ending(after).result, "1/2-1/2")
        self.assertEqual(R.notation(position, "f1-ul-cw"), "f1-ul-cw", "a draw has no #")

    def test_a_full_board_without_five_is_a_draw(self):
        for first in (W, B):
            positions = play(FULL, first)
            with self.subTest(first=first):
                self.assertTrue(all(R.ending(p) is None for p in positions[:-1]))
                self.assertEqual(R.ending(positions[-1]), R.Ending(None, "a full board"))
                self.assertEqual(R.notation(positions[-2], FULL[-1]), FULL[-1])
                self.assertNotIn(".", positions[-1].board)

    def test_a_game_that_is_over_has_no_move_left(self):
        won = setup(ws="a1 a2 a3 a4 a5", bs="d6 e6 f6 d5")
        self.assertEqual((R.legal(won), R.why_illegal(won, "f1-lr-cw")), ([], "the game is over"))
        self.assertIsNone(R.ending(R.opening(W, CENTRES)))


class Notation(unittest.TestCase):
    def test_every_move_of_many_games_is_its_code_or_its_hole_alone_and_a_win_has_a_hash(self):
        for position, code in games(60, 9):
            after = R.make(position, code)
            end = R.ending(after)
            hole = code.split("-")[0]
            want = (hole + "#") if R.won_unturned(position, code) else code + ("#" if end and end.winner else "")
            self.assertEqual(R.notation(position, code), want, (position.board, code))
            self.assertNotIn("+", R.notation(position, code), "nothing marks a threat")


class WhyIllegal(unittest.TestCase):
    def test_a_ghost_s_hole_and_a_marble_s(self):
        position = setup(ws="a1", bs="f6", ghosts="e5 b6")
        self.assertEqual(R.why_illegal(position, "e5-ur-cw"), "a ghost stands on e5")
        self.assertEqual(R.why_illegal(position, "b6-lr-acw"), "a ghost stands on b6")
        self.assertEqual(R.why_illegal(position, "a1-ul-cw"), "there's already a white marble on a1")
        self.assertEqual(R.why_illegal(position, "f6-ll-acw"), "there's already a black marble on f6")

    def test_a_hole_alone_with_no_turn(self):
        position = setup(ws="a1", bs="f6", ghosts="e5 b6")
        self.assertEqual(R.why_illegal(position, "e4"), "a move names its hole, then the quarter it turns and which"
                                                        " way, such as `e4-ul-cw`")
        self.assertEqual(R.why_illegal(position, "a1"), "there's already a white marble on a1")
        self.assertEqual(R.why_illegal(position, "e5"), "a ghost stands on e5")

    def test_no_reason_has_a_long_dash(self):
        position = setup(ws="a1", bs="f6", ghosts="e5 b6")
        for cell in R.CELLS:
            for code in (cell, f"{cell}-ur-acw"):
                if code not in R.legal(position):
                    said = R.why_illegal(position, code)
                    self.assertTrue(said and not any(dash in said for dash in DASHES), said)


class PlainReading(unittest.TestCase):
    def test_every_move_of_many_random_games_agrees_with_a_plainer_reading(self):
        seen = {"White wins": 0, "Black wins": 0, "a win for the side that turned": 0,
                "a win for the side that did not": 0, "a win before any turn": 0, "five for both": 0,
                "a full board": 0, "a ghost turned": 0}
        for position, code in games(200, 13):
            rows, turned = plain_make(rows_of(position), position.turn, code)
            after = R.make(position, code)
            self.assertEqual(after.board, "/".join("".join(row) for row in rows), (position.board, code))
            self.assertEqual(R.legal(position), [f"{c}-{q}-{w}" for c in R.READING if not position.at(c)
                                                 for q in ("ul", "ur", "ll", "lr") for w in WAYS])
            self.assertEqual(R.won_unturned(position, code), not turned)
            end, found = plain_ending(rows), R.ending(after)
            if end is None:
                self.assertIsNone(found, after.board)
            else:
                self.assertEqual((found.winner, found.reason), end[:2], after.board)
                seen[found.reason] = seen.get(found.reason, 0) + 1
                if found.winner:
                    self.assertIn(set(found.line), end[2])
                    seen["White wins" if found.winner == W else "Black wins"] += 1
                    seen["a win before any turn" if not turned else "a win for the side that turned"
                         if found.winner == position.turn else "a win for the side that did not"] += 1
            seen["a ghost turned"] += position.ghosts != after.ghosts
        self.assertTrue(all(seen.values()), seen)


if __name__ == "__main__":
    unittest.main()
