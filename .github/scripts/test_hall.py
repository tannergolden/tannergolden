# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The Hall of Fame of all four games: each game's series, the leading winners and the leaderboard, as the kit's
`hall-of-fame` kind takes them, from every game's finished games and the game on each board.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hall
import page

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
HUBOT, HUBOT_ID = "hubot", 480938
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
DAY = re.compile(r"(?:[1-9]|[12][0-9]|3[01]) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")


def record(game: int, winner: str | None, ended: str, deciding: tuple[str | None, int | None] = (None, None),
           players: list[tuple[str, int, int]] = (), house_moves: int = 1, arbiter: bool = False) -> dict:
    """A finished game as a Hall of Fame keeps it: who won, when, the deciding move's player, everyone who played
    for GitHub and the house's own moves."""
    player, player_id = deciding
    return {"game": game, "result": "1-0", "reason": "three in a row", "winner": winner, "plies": 5,
            "started": "2026-10-01T12:00:00Z", "ended": ended,
            "deciding": {"move": "3. Xa3#", "player": player, "player_id": player_id, "arbiter": arbiter,
                         "issue": None if arbiter else 9},
            "players": [{"player": login, "player_id": account, "moves": moves} for login, account, moves in players],
            "house_moves": house_moves}


def states(**games) -> dict:
    """Every game's state, empty but for the ones given: each a game on its board (or None) and its records."""
    out = {key: (None, []) for key in hall.GAMES}
    out.update(games)
    return out


def board(*moves: tuple[str | None, int | None, bool], opens: str = "house") -> dict:
    """A game on its board: each move's player, account and whether the Arbiter played it, in turn."""
    return {"game": 2, "started": "2026-10-12T16:00:00Z", "opens": opens,
            "moves": [{"move": "x", "shown": "x", "player": login, "player_id": account, "issue": None,
                       "arbiter": arbiter, "at": f"2026-10-12T{17 + i:02}:00:00Z"}
                      for i, (login, account, arbiter) in enumerate(moves)]}


class Shape(unittest.TestCase):
    """The element is what the kit's `hall-of-fame` kind takes."""

    def assertShaped(self, element: dict) -> None:
        self.assertEqual(list(element), ["kind", "series", "people", "leaders", "measure"])
        self.assertEqual((element["kind"], element["measure"]), ("hall-of-fame", {}))
        self.assertEqual(list(element["series"]), list(hall.GAMES))
        for n, house, world, draws in element["series"].values():
            self.assertEqual(house + world + draws, n)
        self.assertLessEqual(len(element["people"]), 10)
        for row in element["people"]:
            self.assertTrue(len(row) in (4, 5) and LOGIN.fullmatch(row[0]) and len(row[1]) == 4
                            and sum(row[1]) >= 1 and DAY.fullmatch(row[2]) and row[3] >= 0, row)
        self.assertEqual(element["leaders"][0][0], OWNER)
        self.assertLessEqual(len(element["leaders"]), 21)
        for i, row in enumerate(element["leaders"]):
            self.assertTrue(len(row) in (4, 5) and LOGIN.fullmatch(row[0]) and len(row[3]) == 4, row)
            self.assertTrue(i == 0 or row[1] >= 1, "a player without a move is not on it")
        ranks = [(-sum(row[3]), -row[1], row[0].casefold()) for row in element["leaders"][1:]]
        self.assertEqual(ranks, sorted(ranks))

    def test_the_owner_s_row_stands_from_the_start(self):
        element = hall.element(states(), OWNER, OWNER_ID)
        self.assertShaped(element)
        self.assertEqual(element["series"], {key: [0, 0, 0, 0] for key in hall.GAMES})
        self.assertEqual((element["people"], element["leaders"]), ([], [[OWNER, 0, 0, [0, 0, 0, 0], OWNER_ID]]))
        self.assertEqual(hall.element(states(), OWNER)["leaders"], [[OWNER, 0, 0, [0, 0, 0, 0]]],
                         "an account's ID ends a row only when it is known")


class Series(unittest.TestCase):
    def test_each_game_counts_its_own_finished_games_the_arbiter_s_wins_included(self):
        element = hall.element(states(
            tictactoe=(None, [record(1, OWNER, "2026-10-01T12:00:00Z"), record(2, "GitHub", "2026-10-02T12:00:00Z",
                                                                         (OCTOCAT, OCTOCAT_ID)),
                              record(3, None, "2026-10-03T12:00:00Z")]),
            chess=(None, [record(1, "GitHub", "2026-10-04T12:00:00Z", arbiter=True)])), OWNER, OWNER_ID)
        self.assertEqual(element["series"], {"tictactoe": [3, 1, 1, 1], "connectfour": [0, 0, 0, 0],
                                             "checkers": [0, 0, 0, 0], "chess": [1, 0, 1, 0]})


class People(unittest.TestCase):
    def test_winners_rank_by_wins_in_all_four_then_the_latest_win_then_login(self):
        element = hall.element(states(
            tictactoe=(None, [record(1, "GitHub", "2026-10-01T12:00:00Z", (OCTOCAT, OCTOCAT_ID),
                                     [(OCTOCAT, OCTOCAT_ID, 3)]),
                              record(2, OWNER, "2026-10-05T12:00:00Z", players=[(HUBOT, HUBOT_ID, 2)])]),
            checkers=(None, [record(1, "GitHub", "2026-10-03T12:00:00Z", (HUBOT, HUBOT_ID), [(HUBOT, HUBOT_ID, 9)])]),
            chess=(None, [record(1, "GitHub", "2026-10-02T12:00:00Z", (OCTOCAT, OCTOCAT_ID),
                                 [(OCTOCAT, OCTOCAT_ID, 20)])])), OWNER, OWNER_ID)
        self.assertEqual(element["people"], [
            ["octocat", [1, 0, 0, 1], "2 Oct", 2, OCTOCAT_ID],
            ["tannergolden", [1, 0, 0, 0], "5 Oct", 4, OWNER_ID],
            ["hubot", [0, 0, 1, 0], "3 Oct", 2, HUBOT_ID],
        ], "two wins first; then of one win each, the latest first; the house counts every finished game it played")

    def test_a_win_by_the_arbiter_s_move_is_nobody_s_and_a_draw_is_nobody_s(self):
        element = hall.element(states(
            connectfour=(None, [record(1, "GitHub", "2026-10-01T12:00:00Z", arbiter=True),
                                record(2, OWNER, "2026-10-02T12:00:00Z", arbiter=True),
                                record(3, None, "2026-10-03T12:00:00Z")])), OWNER, OWNER_ID)
        self.assertEqual(element["people"], [])
        self.assertEqual(element["series"]["connectfour"], [3, 1, 1, 1], "though the scoreboard keeps them")
        self.assertEqual(element["leaders"][0][3], [0, 0, 0, 0])

    def test_the_podium_hands_the_page_ten_winners_for_its_five_places(self):
        won = [record(i, "GitHub", f"2026-10-{i:02}T20:00:00Z", (f"w{i:02}", 2000 + i), [(f"w{i:02}", 2000 + i, 2)])
               for i in range(1, 13)]
        people = hall.element(states(chess=(None, won)), OWNER)["people"]
        self.assertEqual(people, [[f"w{i:02}", [0, 0, 0, 1], f"{i} Oct", 1, 2000 + i] for i in range(12, 2, -1)],
                         "a win each, the latest first, twice the five the page shows")


class Leaders(unittest.TestCase):
    def test_the_leaderboard_counts_moves_and_games_in_all_four_and_on_every_board(self):
        element = hall.element(states(
            tictactoe=(board((None, None, True), (OCTOCAT, OCTOCAT_ID, False), (OWNER, OWNER_ID, False)),
                       [record(1, "GitHub", "2026-10-01T12:00:00Z", (OCTOCAT, OCTOCAT_ID),
                               [(OCTOCAT, OCTOCAT_ID, 3)], house_moves=2)]),
            chess=(board((OWNER, OWNER_ID, False), (HUBOT, HUBOT_ID, False), (OWNER, OWNER_ID, False),
                         (OCTOCAT, OCTOCAT_ID, False)), [])), OWNER, OWNER_ID)
        self.assertEqual(element["leaders"], [
            [OWNER, 2 + 1 + 2, 3, [0, 0, 0, 0], OWNER_ID],
            ["octocat", 3 + 1 + 1, 3, [1, 0, 0, 0], OCTOCAT_ID],
            ["hubot", 1, 1, [0, 0, 0, 0], HUBOT_ID],
        ], "the owner on top; then wins first and moves next, with every game on a board as it goes")

    def test_the_arbiter_s_opening_and_week_moves_count_for_nobody_whichever_side_it_moved_for(self):
        opened_for_github = board((None, None, True), (OWNER, OWNER_ID, False), (OCTOCAT, OCTOCAT_ID, False),
                                  (None, None, True), opens="github")
        self.assertEqual(hall.tally(opened_for_github),
                         (1, [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 1}]))
        opened_for_the_house = board((None, None, True), (OCTOCAT, OCTOCAT_ID, False), (None, None, True))
        self.assertEqual(hall.tally(opened_for_the_house),
                         (0, [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 1}]))
        self.assertEqual(hall.tally(None), (0, []))

    def test_twenty_of_github_follow_the_house(self):
        crowd = record(1, OWNER, "2026-10-01T12:00:00Z", players=[(f"p{i:02}", 1000 + i, i) for i in range(1, 26)])
        leaders = hall.element(states(checkers=(None, [crowd])), OWNER)["leaders"]
        self.assertEqual([row[0] for row in leaders], [OWNER, *(f"p{i:02}" for i in range(25, 5, -1))],
                         "twice the ten the page shows, so it can fill the place of a player whose account is gone")
        self.assertEqual(leaders[0], [OWNER, 1, 1, [0, 0, 1, 0]])

    def test_a_player_is_named_by_the_newest_login_they_played_as_in_any_game(self):
        element = hall.element(states(
            chess=(None, [record(1, "GitHub", "2026-10-01T12:00:00Z", ("octo-old", OCTOCAT_ID),
                                 [("octo-old", OCTOCAT_ID, 2)])]),
            tictactoe=(board((None, None, True), ("octo-new", OCTOCAT_ID, False)), [])), OWNER, OWNER_ID)
        self.assertEqual(element["leaders"][1], ["octo-new", 3, 2, [0, 0, 0, 1], OCTOCAT_ID])
        self.assertEqual(element["people"][0], ["octo-new", [0, 0, 0, 1], "1 Oct", 1, OCTOCAT_ID],
                         "the podium names a winner by the newest login they played as, too")

    def test_every_count_keeps_to_the_page_s_ceilings(self):
        huge = record(1, OWNER, "2026-10-01T12:00:00Z", players=[(OCTOCAT, OCTOCAT_ID, 2_000_000_000)],
                      house_moves=3_000_000_000)
        element = hall.element(states(chess=(None, [huge])), OWNER, OWNER_ID)
        self.assertEqual(element["leaders"][0][1], 999_999_999)
        self.assertEqual(element["leaders"][1][1], 999_999_999)


class Files(unittest.TestCase):
    def test_every_game_s_state_is_read_from_its_own_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "connectfour").mkdir()
            (root / "connectfour" / "hall-of-fame.json").write_text(
                json.dumps([record(1, OWNER, "2026-10-01T12:00:00Z")]), encoding="utf-8")
            (root / "connectfour" / "game.json").write_text(json.dumps(board((None, None, True))), encoding="utf-8")
            found = hall.load(root)
            self.assertEqual(list(found), list(hall.GAMES))
            self.assertEqual(found["chess"], (None, []))
            self.assertEqual((found["connectfour"][0]["game"], len(found["connectfour"][1])), (2, 1))
            self.assertEqual(hall.element(found, OWNER)["series"]["connectfour"], [1, 1, 0, 0])
            self.assertEqual(page.load(root / "nowhere"), (None, []))


if __name__ == "__main__":
    unittest.main()
