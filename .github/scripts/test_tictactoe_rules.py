# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Tic-Tac-Toe, held to the game's known numbers and to a plain search of every line of play, whichever
mark moves first.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

The game is small enough to count whole: 5,478 positions, 765 once the
board's turns and mirrors are set aside, and 255,168 games, of which the
mark that moves first wins 131,184, the other 77,904, and 46,080 are drawn.
On the profile either mark can move first, so every count is made both ways
round. Perfect play is checked against a search that shares nothing with the
rules but the board.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tictactoe_rules as R


def walk(position: R.Position, seen: dict, games: dict) -> None:
    """Every game from the position, each position met kept with how its game ended, if it did."""
    end = R.ending(position)
    seen[position.marks] = end
    if end:
        games[end.winner] += 1
        return
    for cell in R.legal(position):
        walk(R.make(position, cell), seen, games)


SEEN: dict = {}
GAMES = {"X": 0, "O": 0, None: 0}
walk(R.START, SEEN, GAMES)  # the whole game, X first, once for every test here
O_SEEN: dict = {}
O_GAMES = {"X": 0, "O": 0, None: 0}
walk(R.opening(R.O), O_SEEN, O_GAMES)  # and O first


def plain(board: list[str], mover: str) -> int:
    """Perfect play's value by a search of its own: 1 when X wins, -1 when O does, 0 for a draw."""
    lines = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return 1 if board[a] == "X" else -1
    open_ = [i for i, mark in enumerate(board) if not mark]
    if not open_:
        return 0
    values = []
    for i in open_:
        board[i] = mover
        values.append(plain(board, "O" if mover == "X" else "X"))
        board[i] = ""
    return max(values) if mover == "X" else min(values)


def boards(first: str = R.X) -> list[R.Position]:
    return [R.Position(marks, first) for marks in sorted(SEEN if first == R.X else O_SEEN)]


class Counts(unittest.TestCase):
    def test_every_position_and_every_game_is_counted_true(self):
        self.assertEqual(len(SEEN), 5478)
        self.assertEqual(GAMES, {"X": 131184, "O": 77904, None: 46080})
        self.assertEqual(sum(GAMES.values()), 255168)

    def test_o_first_is_the_same_game_with_the_marks_swapped(self):
        swapped = {"X": "O", "O": "X", "": ""}
        self.assertEqual(len(O_SEEN), 5478)
        self.assertEqual(O_GAMES, {"O": 131184, "X": 77904, None: 46080})
        self.assertEqual(set(O_SEEN), {tuple(swapped[mark] for mark in marks) for marks in SEEN})

    def test_765_positions_once_turns_and_mirrors_are_set_aside(self):
        def turned(marks: tuple) -> tuple:  # a quarter turn of the board
            grid = [marks[r * 3:r * 3 + 3] for r in range(3)]
            return tuple(grid[2 - c][r] for r in range(3) for c in range(3))

        def mirrored(marks: tuple) -> tuple:
            return tuple(marks[r * 3 + 2 - c] for r in range(3) for c in range(3))

        unique = set()
        for position in boards():
            forms, marks = [], position.marks
            for _ in range(4):
                marks = turned(marks)
                forms += [marks, mirrored(marks)]
            unique.add(min(forms))
        self.assertEqual(len(unique), 765)


class Lines(unittest.TestCase):
    def test_every_line_wins_for_either_mark_and_names_its_cells(self):
        won = {(end.winner, end.line): R.Position(marks) for marks, end in SEEN.items() if end and end.winner}
        self.assertEqual(set(won), {(mark, line) for mark in (R.X, R.O) for line in R.LINES},
                         "every line is won by each mark in some game")
        for (mark, line), position in won.items():
            with self.subTest(line=line, mark=mark):
                self.assertTrue(all(position.at(cell) == mark for cell in line))
                self.assertEqual(R.ending(position).result, "1-0" if mark == R.X else "0-1")
                self.assertEqual(R.legal(position), [], "a won game has no move left")

    def test_a_full_board_without_a_line_is_a_draw(self):
        position = R.Position.from_board("XOX/XOO/OXX")
        self.assertEqual(R.ending(position), R.Ending(None, "a full board"))
        self.assertEqual(R.ending(position).result, "1/2-1/2")

    def test_a_board_still_open_has_no_ending(self):
        self.assertIsNone(R.ending(R.Position.from_board("XO./.X./..O")))


class Moves(unittest.TestCase):
    def test_x_opens_and_the_marks_take_turns(self):
        position = R.START
        self.assertEqual(position.turn, R.X)
        self.assertEqual(R.legal(position), list(R.READING))
        position = R.make(position, "b2")
        self.assertEqual((position.turn, position.board), (R.O, ".../.X./..."))
        self.assertNotIn("b2", R.legal(position))

    def test_o_opens_when_the_game_says_so_and_the_marks_still_take_turns(self):
        position = R.opening(R.O)
        self.assertEqual((position.turn, position.first, R.legal(position)), (R.O, R.O, list(R.READING)))
        position = R.make(position, "a1")
        self.assertEqual((position.turn, position.board, position.first), (R.X, ".../.../O..", R.O))
        position = R.make(position, "b2")
        self.assertEqual((position.turn, position.board), (R.O, ".../.X./O.."))
        self.assertNotEqual(R.Position(position.marks), position, "the same marks with X first is another position")
        self.assertEqual(R.Position.from_board(".../.X./O..", R.O), position)

    def test_a_board_is_read_and_written_top_row_first(self):
        position = R.Position.from_board("O../XX./O.X")
        self.assertEqual((position.at("a3"), position.at("a1"), position.at("c1"), position.at("b2")),
                         ("O", "O", "X", "X"))
        self.assertEqual(position.board, "O../XX./O.X")
        for bad in ("O../XX./O.", "OOO/.../...", "XXX/X../...", "X../.../..?"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                R.Position.from_board(bad)
        self.assertEqual(R.Position.from_board("O../.../...", R.O).turn, R.X)
        for bad, first in (("X../.../...", R.O), ("XX./O../...", R.O), ("O../.../...", R.X), (".../.../...", "Y")):
            with self.subTest(bad=bad, first=first), self.assertRaises(ValueError):
                R.Position.from_board(bad, first)

    def test_threats_are_the_cells_a_mark_would_win_on(self):
        position = R.Position.from_board("O../XX./O.X")
        self.assertEqual(R.threats(position, R.X), ["c2"])
        self.assertEqual(R.threats(position, R.O), [], "O's a1 and a3 are cut off by X on a2")
        self.assertEqual(R.threats(R.Position.from_board("X../.X./O.."), R.X), ["c1"])
        self.assertEqual(R.threats(R.Position.from_board("XX./.../OO."), R.X), ["c3"])
        self.assertEqual(R.threats(R.Position.from_board("X.X/.O./X.O"), R.X), ["b3", "a2"],
                         "every cell a mark would win on, as the board is read")

    def test_a_move_is_written_with_a_threat_or_a_win(self):
        self.assertEqual(R.notation(R.START, "b2"), "Xb2")
        self.assertEqual(R.notation(R.Position.from_board(".../.X./..."), "a1"), "Oa1")
        self.assertEqual(R.notation(R.Position.from_board(".../.X./O.."), "c1"), "Xc1+",
                         "X on c1 could win on a3 next")
        self.assertEqual(R.notation(R.Position.from_board("O../XX./O.X"), "c2"), "Oc2", "a block, and no threat")
        self.assertEqual(R.notation(R.Position.from_board("O../.XX/O.X"), "a2"), "Oa2#")
        self.assertEqual(R.notation(R.Position.from_board("X../.X./O.."), "c1"), "Oc1+",
                         "O blocks c1 and could win on b1 next")
        self.assertEqual(R.notation(R.opening(R.O), "b2"), "Ob2", "O's mark goes down first when O opens")
        self.assertEqual(R.notation(R.Position.from_board(".../.O./X..", R.O), "c1"), "Oc1+")
        self.assertEqual(R.notation(R.Position.from_board("O../.O./XX.", R.O), "c1"), "Oc1#")

    def test_why_a_cell_cannot_be_marked(self):
        position = R.Position.from_board("O../XX./O.X")
        self.assertEqual(R.why_illegal(position, "b2"), "there's already an X on b2")
        self.assertEqual(R.why_illegal(position, "a1"), "there's already an O on a1")


class Outlook(unittest.TestCase):
    def test_perfect_play_agrees_with_a_plain_search_of_every_line_either_mark_first(self):
        for first in (R.X, R.O):
            checked = 0
            for position in boards(first):
                if R.ending(position) or sum(1 for mark in position.marks if mark) < 3:
                    continue
                board = [position.at(cell) for cell in ("a3", "b3", "c3", "a2", "b2", "c2", "a1", "b1", "c1")]
                want = {1: R.X, -1: R.O, 0: "draw"}[plain(board, position.turn)]
                self.assertEqual(R.outlook(position), want, (first, position.board))
                checked += 1
            self.assertGreater(checked, 4000)

    def test_the_game_is_a_draw_from_the_start_and_lost_by_a_slip(self):
        self.assertEqual(R.outlook(R.START), "draw")
        for cell in R.CELLS:
            self.assertEqual(R.outlook(R.make(R.START, cell)), "draw", f"X on {cell} still draws")
        self.assertEqual(R.outlook(R.Position.from_board(".../OX./...")), R.X, "O on an edge beside X's centre loses")
        self.assertEqual(R.outlook(R.Position.from_board("X../.O./...")), "draw")
        self.assertEqual(R.outlook(R.opening(R.O)), "draw", "and from the start with O first")
        self.assertEqual(R.outlook(R.Position.from_board(".../XO./...", R.O)), R.O,
                         "X on an edge beside O's centre loses, when O moved first")


if __name__ == "__main__":
    unittest.main()
