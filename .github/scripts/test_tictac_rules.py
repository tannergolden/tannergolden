# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The rules of Tic-Tac, Tic-Tac-Toe on nine boards at once, held to a second, plainer reading of them over many random
games, and to positions set out by hand for every way a mark sends, a board closes and a game ends.

  python3 -m unittest discover -s .github/scripts -p 'test_tictac*.py'

The plainer reading shares nothing with the rules but the squares' names: it
reads the big board as nine grids of three by three, works out each board's
state, where the last mark sends the side to move, every square it may take
and how the game ends, and both readings must agree on every position of a
hundred and twenty seeded random games, either mark first, each under the
Ghost Rule's two locked squares. Positions set out by hand hold the rest: the
board a mark sends the other side to, a board closed by a win, by its last
open square or by a ghost, three boards in a row, and the draw that comes as
soon as neither mark can still make a line of three boards.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tictac_rules as R
from tictac_rules import O, X

DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
CENTRE = ("d6", "e6", "f6", "d5", "e5", "f5", "d4", "e4", "f4")  # the centre board, as it is read
# The centre board full round a ghost on its centre, with no line in it: X X O, O and the ghost and X, X O O.
ROUND_XS, ROUND_OS = "d6 e6 f5 d4", "f6 d5 e4 f4"


def setup(xs: str = "", os: str = "", ghosts: str = "", first: str = X, last: str = "") -> R.Position:
    """A position with X on the squares `xs` names, O on those `os` names and a ghost on each of `ghosts`, every list
    split by spaces; `first` the mark that moved first and `last` the square of the last mark."""
    marks = {**dict.fromkeys(xs.split(), X), **dict.fromkeys(os.split(), O)}
    return R.Position(tuple(marks.get(cell, "") for cell in R.CELLS), first, frozenset(ghosts.split()), last)


def top_rows(*boards: tuple[int, int]) -> str:
    """The squares of each board's top row, as `setup` takes them: three in a row in each board."""
    return " ".join(cell for board in boards for cell in R.squares_of(board)[:3])


def plain(marks: dict[str, str], ghosts: frozenset, last: str) -> tuple[dict, list[str], tuple | None]:
    """The rules read a second, plainer way, on a grid of nine by nine: each board's state, every square the side to
    move may take as the board is read, and how the game ends (its winner, how, and the boards of every line it was
    won on), from the marks by square, the ghosts and the square of the last mark."""
    def square(x: int, y: int) -> str:
        return "abcdefghi"[x] + str(y + 1)

    def lines(grid: list[list]) -> list[list]:
        """A grid's rows, columns and both diagonals."""
        return [*grid, *map(list, zip(*grid)), [grid[i][i] for i in range(3)], [grid[i][2 - i] for i in range(3)]]

    state = {}
    for bx in range(3):
        for by in range(3):
            cells = [[square(bx * 3 + i, by * 3 + j) for i in range(3)] for j in range(3)]
            grid = [[marks.get(cell, "") for cell in row] for row in cells]
            won = [mark for mark in (X, O) if any(all(v == mark for v in line) for line in lines(grid))]
            full = all(cell in marks or cell in ghosts for row in cells for cell in row)
            state[bx, by] = won[0] if won else "draw" if full else None
    big = lines([[(bx, by) for bx in range(3)] for by in range(3)])
    end = None
    for mark in (X, O):
        won = [line for line in big if all(state[b] == mark for b in line)]
        if won:
            end = (mark, "three boards in a row", [{"abc"[bx] + str(by + 1) for bx, by in line} for line in won])
    if end is None and not any(all(state[b] in (None, mark) for b in line) for line in big for mark in (X, O)):
        end = (None, "no line left", [])
    if end:
        return state, [], end
    sent = None
    if last:
        x, y = "abcdefghi".index(last[0]), int(last[1]) - 1
        sent = (x % 3, y % 3) if state[x % 3, y % 3] is None else None
    boards = [sent] if sent else [b for b, held in state.items() if held is None]
    legal = [square(x, y) for y in range(8, -1, -1) for x in range(9)
             if (x // 3, y // 3) in boards and square(x, y) not in marks and square(x, y) not in ghosts]
    return state, legal, None


def games(n: int, seed: int):
    """`n` games of seeded random play, every other one O first, each under two ghosts dropped at random: every
    position of each, the last its end."""
    rng = random.Random(seed)
    for game in range(n):
        ghosts = rng.sample(R.CELLS, 2)
        if game % 3 == 0:  # both in one board now and then, so a board fills round two ghosts
            board = R.squares_of(rng.choice(R.BOARDS))
            ghosts = rng.sample(board, 2)
        position, out = R.opening(O if game % 2 else X, ghosts), []
        while True:
            out.append(position)
            if R.ending(position):
                break
            position = R.make(position, rng.choice(R.legal(position)))
        yield out


class Squares(unittest.TestCase):
    def test_the_squares_are_named_as_chess_names_them_and_read_top_row_first(self):
        self.assertEqual((len(R.CELLS), R.CELLS[:3], R.CELLS[-1]), (81, ("a1", "b1", "c1"), "i9"))
        self.assertEqual((R.READING[:3], R.READING[-1]), (("a9", "b9", "c9"), "i1"))
        self.assertEqual(sorted(R.READING), sorted(R.CELLS))

    def test_a_square_stands_in_a_board_and_in_a_place_inside_it(self):
        self.assertEqual([R.board_of(cell) for cell in ("a1", "e5", "i9", "c7", "g3")],
                         [(0, 0), (1, 1), (2, 2), (0, 2), (2, 0)])
        self.assertEqual([R.spot_of(cell) for cell in ("a1", "e5", "f6", "d4", "i9", "b8")],
                         [(0, 0), (1, 1), (2, 2), (0, 0), (2, 2), (1, 1)])
        self.assertEqual([R.board_name(b) for b in R.BOARDS],
                         ["a3", "b3", "c3", "a2", "b2", "c2", "a1", "b1", "c1"], "as Tic-Tac-Toe names its cells")
        self.assertEqual(R.squares_of((1, 1)), CENTRE)
        self.assertEqual(R.squares_of((0, 0)), ("a3", "b3", "c3", "a2", "b2", "c2", "a1", "b1", "c1"))
        self.assertEqual(len({line for b in R.BOARDS for line in R.lines_of(b)}), 72, "eight lines in each board")

    def test_a_position_is_written_as_nine_rows_top_first_its_ghosts_as_g(self):
        position = setup(xs="a9 e5", os="i1", ghosts="a1 i9")
        self.assertEqual(position.board, "X.......G/........./........./........./....X..../........./........./"
                                         "........./G.......O")
        self.assertEqual(R.opening(X, ("e5",)).board.count("G"), 1)
        for dash in DASHES:
            self.assertNotIn(dash, position.board)


class Opening(unittest.TestCase):
    def test_the_first_mark_goes_on_any_square_but_a_ghost_s(self):
        position = R.opening(X, ("e5", "a1"))
        self.assertEqual((position.turn, position.target, position.last), (X, None, ""))
        self.assertEqual(R.legal(position), [cell for cell in R.READING if cell not in ("e5", "a1")])
        self.assertEqual(position.ghosts, frozenset({"e5", "a1"}))

    def test_either_mark_can_go_first_and_then_the_marks_take_turns(self):
        for first in (X, O):
            position = R.opening(first, ("e5", "a1"))
            seen = []
            for cell in ("b8", "e6", "d7", "a3"):
                seen.append(position.turn)
                position = R.make(position, cell)
            with self.subTest(first=first):
                self.assertEqual(seen, [first, R.other(first)] * 2)
                self.assertEqual((position.first, position.last), (first, "a3"))

    def test_make_leaves_the_position_it_was_given(self):
        before = R.opening(X, ("e5",))
        after = R.make(before, "f6")
        self.assertEqual((before.at("f6"), before.last, after.at("f6"), after.last), ("", "", X, "f6"))
        self.assertEqual(after.ghosts, before.ghosts)


class Sending(unittest.TestCase):
    """Where a mark goes inside its board sends the other side to the board in that place on the big board."""

    def test_every_square_sends_the_other_side_to_the_board_in_its_place(self):
        start = R.opening(X)
        for cell in R.CELLS:
            after = R.make(start, cell)
            with self.subTest(cell=cell):
                self.assertEqual(after.target, R.spot_of(cell))
                self.assertEqual(R.legal(after), [c for c in R.READING if R.board_of(c) == R.spot_of(cell)
                                                  and c != cell])

    def test_the_upper_right_corner_of_the_centre_board_sends_to_the_upper_right_board(self):
        after = R.make(R.opening(X, ("e5", "a1")), "f6")
        self.assertEqual(after.target, (2, 2))
        self.assertEqual(R.legal(after), ["g9", "h9", "i9", "g8", "h8", "i8", "g7", "h7", "i7"])
        self.assertEqual(R.legal(R.make(after, "g9")), ["a9", "b9", "c9", "a8", "b8", "c8", "a7", "b7", "c7"],
                         "the upper left corner of any board sends to the upper left board")

    def test_a_ghost_is_never_a_square_to_take_in_the_board_sent_to(self):
        after = R.make(R.opening(X, ("e5", "a1")), "b8")  # the centre of its board sends to the centre board
        self.assertEqual(R.legal(after), [cell for cell in CENTRE if cell != "e5"])

    def test_a_side_sent_to_a_won_board_plays_any_open_square_of_any_open_board(self):
        # X has won the upper right board on its top row, and O's last mark, in its own board's upper right corner,
        # sends X there: it is closed, so X may take any open square of any open board.
        position = setup(xs="g9 h9 i9", os="c9 f4 a1", last="c9")
        self.assertEqual((position.turn, position.closed[2, 2]), (X, X))
        self.assertIsNone(position.target)
        legal = R.legal(position)
        self.assertEqual(legal, [cell for cell in R.READING if R.board_of(cell) != (2, 2)
                                 and cell not in ("c9", "f4", "a1")])
        self.assertFalse({"g8", "h8", "i8", "g7"} & set(legal), "a won board closes with squares still open")

    def test_a_board_full_without_a_line_is_drawn_and_closes(self):
        # The centre board filled X O X / X O O / O X X, no line in it, and X's last mark, the centre of the upper
        # left board, sends O there.
        position = setup(xs="d6 f6 d5 e4 f4 b8", os="e6 e5 f5 d4 h2", last="b8")
        self.assertEqual((position.turn, position.closed[1, 1]), (O, R.DRAWN))
        self.assertIsNone(position.target)
        self.assertNotIn((1, 1), {R.board_of(cell) for cell in R.legal(position)})

    def test_a_board_with_a_ghost_is_full_once_its_other_squares_are_taken(self):
        position = setup(xs=f"{ROUND_XS} b8", os=f"{ROUND_OS} h2", ghosts="e5", last="h2")
        self.assertEqual(position.closed[1, 1], R.DRAWN)
        self.assertIsNone(position.target, "O's h2, a board's centre, sends X to the full board, so X goes anywhere")
        self.assertEqual(len(R.legal(position)), 81 - 9 - 2)
        self.assertIsNone(setup(xs=ROUND_XS, os="f6 d5 e4", ghosts="e5").closed[1, 1], "with f4 open it is open")

    def test_no_line_runs_through_a_ghost(self):
        # X holds both ends of the centre board's middle row, its column and a diagonal: the ghost on e5 stands in each
        # of them, so none of them is a line, and nobody can take e5.
        position = setup(xs="d5 f5 e6 e4 d4 f6", os="a9 c8 a7 h2 g1 i2", ghosts="e5")
        self.assertIsNone(position.closed[1, 1])
        self.assertNotIn("e5", R.legal(position))
        self.assertEqual(R.make(position, "d6").closed[1, 1], X, "a line round the ghost wins it: d6, e6 and f6")


class Endings(unittest.TestCase):
    def test_three_boards_in_a_row_win_the_game_and_name_their_boards(self):
        for line in R.LINES:
            for mark in (X, O):
                position = setup(**{"xs" if mark == X else "os": top_rows(*line)})
                end = R.ending(position)
                with self.subTest(line=line, mark=mark):
                    self.assertEqual(end, R.Ending(mark, "three boards in a row",
                                                   tuple(R.board_name(b) for b in line)))
                    self.assertEqual(end.result, "1-0" if mark == X else "0-1")
                    self.assertEqual(R.legal(position), [], "a won game has no move left")

    def test_two_boards_in_a_row_are_not_yet_a_win(self):
        position = setup(xs=top_rows((0, 2), (1, 2)), os=top_rows((2, 1)))
        self.assertIsNone(R.ending(position))
        self.assertEqual((position.closed[0, 2], position.closed[1, 2], position.closed[2, 1]), (X, X, O))

    def test_the_game_is_drawn_once_neither_mark_can_make_a_line_of_three_boards(self):
        # The centre board drawn round its ghost, which spoils its row, its column and both diagonals; X holds the
        # upper left and lower right boards, O the other two corners, which spoils every line round the edge. The
        # four edge boards are still open, and nothing left on them can make three in a row.
        corners = {"xs": top_rows((0, 2), (2, 0)), "os": top_rows((2, 2), (0, 0))}
        position = setup(xs=f"{ROUND_XS} {corners['xs']}", os=f"{ROUND_OS} {corners['os']}", ghosts="e5")
        self.assertEqual(sum(1 for held in position.closed.values() if held is None), 4)
        end = R.ending(position)
        self.assertEqual(end, R.Ending(None, "no line left"))
        self.assertEqual((end.result, end.line, R.legal(position)), ("1/2-1/2", (), []))
        # With the lower right board still open, O could yet win the bottom row: no draw.
        position = setup(xs=f"{ROUND_XS} {top_rows((0, 2))}", os=f"{ROUND_OS} {corners['os']}", ghosts="e5")
        self.assertIsNone(R.ending(position))

    def test_a_game_with_a_line_still_open_has_no_ending(self):
        self.assertIsNone(R.ending(R.opening(X, ("e5", "a1"))))
        self.assertIsNone(R.ending(setup(xs=top_rows((1, 1)), os=top_rows((0, 0)))))


class Notation(unittest.TestCase):
    def test_a_move_is_its_mark_and_its_square(self):
        self.assertEqual(R.notation(R.opening(X), "e5"), "Xe5")
        self.assertEqual(R.notation(R.opening(O), "e5"), "Oe5")
        self.assertEqual(R.notation(R.make(R.opening(X), "f6"), "g9"), "Og9")

    def test_only_the_mark_that_wins_the_game_has_a_hash(self):
        # X has the top rows of the upper left and top boards, and two of the upper right board's: g9 wins its board
        # and the game. A mark that wins a board alone is written as any other.
        position = setup(xs=f"{top_rows((0, 2), (1, 2))} h9 i9", os="a1 c1 b2 e1 d3 g2 i1 h3")
        self.assertEqual(R.notation(position, "g9"), "Xg9#")
        board_only = setup(xs="h9 i9", os="a1 c1")
        self.assertEqual(R.make(board_only, "g9").closed[2, 2], X)
        self.assertEqual(R.notation(board_only, "g9"), "Xg9")

    def test_every_move_of_many_games_is_its_mark_and_square_and_only_the_win_has_a_hash(self):
        for positions in games(80, 11):
            for before, after in zip(positions, positions[1:]):
                cell = after.last
                won = R.ending(after)
                want = before.turn + cell + ("#" if won and won.winner == before.turn else "")
                self.assertEqual(R.notation(before, cell), want, (before.board, cell))
                self.assertNotIn("+", R.notation(before, cell), "nothing marks a threat")


class WhyIllegal(unittest.TestCase):
    def test_a_ghost_s_square_a_mark_s_and_the_board_the_rules_send_to(self):
        position = R.make(R.make(R.opening(X, ("e5", "a1")), "b8"), "f6")  # O's f6 sends X to the upper right board
        self.assertEqual(R.why_illegal(position, "e5"), "a ghost locks e5, so nobody can take it")
        self.assertEqual(R.why_illegal(position, "b8"), "there's already an X on b8")
        self.assertEqual(R.why_illegal(position, "f6"), "there's already an O on f6")
        self.assertEqual(R.why_illegal(position, "a9"), "the last mark sent X to the upper right board, so it must go"
                                                        " there")

    def test_a_closed_board_and_a_game_that_is_over(self):
        position = setup(xs="g9 h9 i9", os="c9 f4 a1", last="c9")
        self.assertEqual(R.why_illegal(position, "g7"), "the upper right board is closed")
        won = setup(xs=top_rows((0, 0), (1, 1), (2, 2)))
        self.assertEqual(R.why_illegal(won, "a9"), "the game is over")

    def test_no_reason_has_a_long_dash(self):
        for positions in games(6, 3):
            for position in positions[:-1]:
                for cell in R.CELLS:
                    if cell not in R.legal(position):
                        said = R.why_illegal(position, cell)
                        self.assertTrue(said and not any(dash in said for dash in DASHES), said)


class PlainReading(unittest.TestCase):
    def test_every_position_of_many_random_games_agrees_with_a_plainer_reading(self):
        seen = {"X wins": 0, "O wins": 0, "no line left": 0, "a drawn board": 0, "a board drawn round a ghost": 0,
                "sent to a closed board": 0}
        for positions in games(120, 7):
            for position in positions:
                marks = {cell: position.at(cell) for cell in R.CELLS if position.at(cell)}
                state, legal, end = plain(marks, position.ghosts, position.last)
                self.assertEqual(position.closed, state, position.board)
                self.assertEqual(R.legal(position), legal, position.board)
                found = R.ending(position)
                if end is None:
                    self.assertIsNone(found, position.board)
                    sent = R.spot_of(position.last) if position.last else None
                    self.assertEqual(position.target, sent if sent and state[sent] is None else None)
                    seen["sent to a closed board"] += bool(sent and state[sent] is not None)
                else:
                    self.assertEqual((found.winner, found.reason), end[:2], position.board)
                    if found.winner:
                        self.assertIn(set(found.line), end[2])
                drawn = [b for b, held in state.items() if held == "draw"]
                seen["a drawn board"] += bool(drawn)
                seen["a board drawn round a ghost"] += any(set(R.squares_of(b)) & position.ghosts for b in drawn)
            end = R.ending(positions[-1])
            seen[f"{end.winner} wins" if end.winner else end.reason] += 1
        self.assertTrue(all(seen.values()), seen)


if __name__ == "__main__":
    unittest.main()
