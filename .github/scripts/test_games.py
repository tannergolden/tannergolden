# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac-Toe and Connect Four, played offline through the same calls their workflow makes: every way a move goes.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

Each game is played at a table: moves come in as the intake sends them, from
the owner for the house and from made-up players for GitHub, at times the
test sets, so the Arbiter's week and a final board's two days pass in a line.
The Arbiter opens every game of both, for a side it draws at random, with a
random move; a table starts at the first minute whose draw gives the side and
the opening move the test asks for, so a game's line can be written down.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import re
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import games
import page
from page import GITHUB, HOUSE, other

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
HUBOT, HUBOT_ID = "hubot", 480938
T0 = page.parse("2026-10-12T16:00:00Z")
HOUR = dt.timedelta(hours=1)
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
PING = re.compile(r"(?<![\[\w])@[A-Za-z0-9][A-Za-z0-9-]*")  # a mention GitHub notifies: outside a link's text
LINKED = "[@tannergolden](https://github.com/tannergolden)"
BOARD = "[the board](https://github.com/tannergolden)"
SETTINGS = "elements:\n  other:\n    kind: placard\n\ntrophies:\n  style: trophy\n"

# What tannergolden/markdown accepts from the games (src/domain/elements/games/data.py and each game's game.py).
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_WHO = re.compile(r"@[A-Za-z0-9][A-Za-z0-9-]{0,38}|the Arbiter")
KIT_DAY = re.compile(r"(?:[1-9]|[12][0-9]|3[01]) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
KIT_LINE = re.compile(r"[^<>|\n\r]{1,400}")
KIT_BLOCK = re.compile(r"\s|```|~~~|#{1,6}(?:\s|$)|>|[-*+](?:\s|$)|[0-9]+[.)](?:\s|$)|\[[^\]]*\]:|[-=*_\s]+$")
KIT_HOW = re.compile(r"[a-z][a-z0-9 ,'-]{0,23}")
KIT_MOVE = {"tictactoe": re.compile(r"[XO][a-c][1-3][+#]?"), "connectfour": re.compile(r"[1-7][+#]?")}
KIT_BOARD = {"tictactoe": re.compile(r"[XO.]{3}/[XO.]{3}/[XO.]{3}"),
             "connectfour": re.compile(r"(?:[LD.]{7}/){5}[LD.]{7}")}
NUMBER = r"[1-9][0-9]{0,8}"
# What tannergolden/play's intake takes as a move's issue title, the move as `move`.
INTAKE = {"tictactoe": re.compile(rf"tictactoe: (?P<move>[a-c][1-3]) · game (?P<game>{NUMBER})"
                                  rf" · move (?P<ply>{NUMBER})"),
          "connectfour": re.compile(rf"connectfour: (?P<move>[1-7]) · game (?P<game>{NUMBER})"
                                    rf" · move (?P<ply>{NUMBER})")}

# Lines of play, the Arbiter's opening first.
TTT_X_WINS = ["b2", "a2", "a1", "c3", "c1", "b1", "a3"]  # X forks a3 and b1, and wins on a3
TTT_O_WINS = ["b2", "a3", "b3", "a2", "c3", "a1"]  # O blocks b1, then wins up the a-file
TTT_DRAW = ["b2", "a1", "c1", "a3", "a2", "c2", "b3", "b1", "c3"]
C4_DARK_UP = list("4141424")  # Dark stacks column 4; Light lets the third disc through
C4_LIGHT_UP = list("42157234251535")  # Light connects four up column 5
C4_DARK_DIAGONAL = list("446314325141273")  # Dark connects from 1,1 to 4,4
C4_DARK_ACROSS = list("4113317237274")  # Dark connects across row 2
C4_DRAW = list("467516245217422716242761435431776133653535")  # forty-two discs and no four in a row
LINES = {"tictactoe": (TTT_X_WINS, TTT_O_WINS, TTT_DRAW),
         "connectfour": (C4_DARK_UP, C4_LIGHT_UP, C4_DARK_DIAGONAL, C4_DARK_ACROSS, C4_DRAW)}
KEYS = ("tictactoe", "connectfour")


def opening_at(key: str, side: str, code: str, number: int = 1, start: dt.datetime = T0) -> dt.datetime:
    """The first minute from `start` at which the Arbiter, opening game `number`, draws `side` and plays `code`."""
    moment = start
    mod = games.rules(key)
    while True:
        stamped = page.stamp(moment)
        if (games.pick([HOUSE, GITHUB], f"{key}:{number}:opens:{stamped}") == side
                and games.pick(sorted(mod.legal(mod.start())), f"{key}:{number}:1:{stamped}") == code):
            return moment
        moment += dt.timedelta(minutes=1)


class Table:
    """A game at the profile: the state between moves, and every reply so far. The Arbiter has opened game 1 for
    `opens` with `first` by the time the table is laid."""

    def __init__(self, key: str, opens: str = HOUSE, first: str | None = None):
        self.key, self.mod = key, games.rules(key)
        self.game, self.hall, self.outcomes, self.texts, self.issue = None, [], [], [], 100
        self.clock = opening_at(key, opens, first or {"tictactoe": "b2", "connectfour": "4"}[key])
        self.keep(games.tick(self.mod, None, [], OWNER, self.clock))

    def side(self) -> str:
        return games.side_of(self.game, len(self.game["moves"]) + 1)

    def move(self, code: str, player: str | None = None, player_id: int | None = None, move: int | None = None,
             game: int | None = None, after: dt.timedelta = HOUR) -> games.Outcome:
        """A move from whoever's turn it is, at the move on the board, unless the test says otherwise."""
        player = player or (OWNER if self.side() == HOUSE else OCTOCAT)
        player_id = player_id or {OWNER: OWNER_ID, OCTOCAT: OCTOCAT_ID, HUBOT: HUBOT_ID}.get(player, 7)
        self.clock += after
        self.issue += 1
        request = games.Request(code, game or self.game["game"], move or len(self.game["moves"]) + 1, self.issue,
                                player, player_id)
        return self.keep(games.play(self.mod, self.game, self.hall, request, OWNER, OWNER_ID, self.clock))

    def wait(self, span: dt.timedelta) -> games.Outcome:
        self.clock += span
        return self.keep(games.tick(self.mod, self.game, self.hall, OWNER, self.clock))

    def fresh(self) -> games.Outcome | None:
        """Waits out a finished game's two days, to the clock's run at the moment the fresh board comes."""
        if not self.game["moves"] and page.parse(self.game["started"]) > self.clock:
            return self.wait(page.parse(self.game["started"]) - self.clock)
        return None

    def keep(self, outcome: games.Outcome) -> games.Outcome:
        if outcome.changed:
            self.game, self.hall = outcome.game, outcome.hall
        self.outcomes.append(outcome)
        self.texts += [outcome.comment, outcome.commit]
        return outcome

    def play(self, codes: list[str]) -> games.Outcome:
        """The line after the Arbiter's opening, which must be its first code."""
        assert self.game["moves"][0]["move"] == codes[0], (self.game["moves"][0], codes[0])
        outcome = None
        for code in codes[1:]:
            outcome = self.move(code)
            assert outcome.changed, f"{code}: {outcome.comment}"
        return outcome

    def board(self) -> dict:
        return games.board(self.mod, self.game, self.hall, OWNER, self.clock)


def tables(line: list[str] | None = None):
    """A table of each game, opened for each side, each with the line's first move or the centre."""
    for key in KEYS:
        for opens in (HOUSE, GITHUB):
            yield key, opens, Table(key, opens)


class Opening(unittest.TestCase):
    """The Arbiter opens every game of both, for a side drawn at random, with a random legal move that counts for
    nobody and answers no issue; that side plays X, or the dark discs, and the other O, or the light ones."""

    def test_the_first_game_is_opened_on_the_clock_for_the_side_drawn(self):
        for key, opens, table in tables():
            with self.subTest(key=key, opens=opens):
                opened = table.outcomes[0]
                self.assertTrue(opened.changed)
                self.assertEqual((table.game["game"], table.game["started"], table.game["opens"]),
                                 (1, page.stamp(table.clock), opens))
                first = table.game["moves"][0]
                self.assertEqual(first, {"move": first["move"], "shown": first["shown"], "player": None,
                                         "player_id": None, "issue": None, "arbiter": True,
                                         "at": table.game["started"]})
                self.assertEqual((games.contributors(table.game), games.house_moves(table.game)), ([], 0),
                                 "the opening counts for nobody")
                self.assertEqual((opened.issue, opened.logbook, opened.comment), (None, False, ""),
                                 "and answers no issue")
                side = "tannergolden" if opens == HOUSE else "GitHub"
                self.assertTrue(opened.commit.startswith(f"chore({key}): 🎲 open game 1 for {side} with 1. "))

    def test_the_draws_are_seeded_and_fair(self):
        for key in KEYS:
            mod = games.rules(key)
            sides, firsts = {HOUSE: 0, GITHUB: 0}, set()
            for minute in range(400):
                moment = T0 + dt.timedelta(minutes=minute)
                game, opening = games.settle(mod, None, moment)
                again, _ = games.settle(mod, None, moment)
                self.assertEqual(game, again, "the same moment draws the same side and move")
                sides[game["opens"]] += 1
                firsts.add(opening["move"])
            with self.subTest(key=key):
                self.assertGreater(min(sides.values()), 150, sides)
                self.assertEqual(firsts, set(mod.legal(mod.start())), "every opening move comes up")

    def test_the_opener_plays_x_or_dark_and_the_other_side_o_or_light(self):
        for key, opens, table in tables():
            element = table.board()
            with self.subTest(key=key, opens=opens):
                if key == "tictactoe":
                    self.assertEqual(element["x"], opens)
                    self.assertEqual(table.game["moves"][0]["shown"], "Xb2")
                else:
                    self.assertEqual((element["opens"], element["light"]), (opens, other(opens)))
                    self.assertEqual(table.game["moves"][0]["shown"], "⚫4")
                self.assertEqual(games.word(table.mod, table.game, opens), table.mod.FIRST)
                self.assertEqual(games.word(table.mod, table.game, other(opens)), table.mod.SECOND)

    def test_the_fresh_board_names_the_side_and_the_move_and_says_why_the_arbiter_opens(self):
        said = {
            ("tictactoe", HOUSE): "🟢 **GitHub's turn!** The Arbiter opened game 1 for @tannergolden with X on b2, at"
                                  " random.",
            ("tictactoe", GITHUB): "🛑 **@tannergolden's turn!** The Arbiter opened game 1 for GitHub with X on b2, at"
                                   " random.",
            ("connectfour", HOUSE): "🟢 **GitHub's turn!** The Arbiter opened game 1 for @tannergolden with ⚫4, at"
                                    " random.",
            ("connectfour", GITHUB): "🛑 **@tannergolden's turn!** The Arbiter opened game 1 for GitHub with ⚫4, at"
                                     " random.",
        }
        for key, opens, table in tables():
            element = table.board()
            with self.subTest(key=key, opens=opens):
                self.assertEqual(element["prompt"], said[key, opens])
                self.assertTrue(element["note"].startswith(table.mod.WHY))
                self.assertIn(games.who_plays(other(opens), OWNER), element["note"])
                self.assertIn(f"The move is due by {page.until(table.clock + page.WEEK)}, or the Arbiter plays a random"
                              " legal move.", element["note"])
                self.assertEqual(element["last"]["by"], "the Arbiter")
                self.assertEqual(element["history"][0][3], "the Arbiter" if opens == GITHUB else "",
                                 "who chose GitHub's move, when the Arbiter chose it for GitHub")
        self.assertIn("of the 255,168 possible games, X wins 131,184, O wins 77,904 and 46,080 are drawn",
                      games.rules("tictactoe").WHY)
        self.assertIn("James D. Allen and Victor Allis, independently, in 1988", games.rules("connectfour").WHY)

    def test_the_week_for_the_reply_counts_from_the_start(self):
        table = Table("tictactoe", GITHUB)
        self.assertEqual(table.wait(page.WEEK - dt.timedelta(minutes=1)).log,
                         f"the side to move has until {page.stamp(page.parse(table.game['started']) + page.WEEK)}")
        outcome = table.wait(dt.timedelta(minutes=1))
        self.assertTrue(outcome.changed)
        self.assertTrue(outcome.logbook, "the move it answers is its own opening, so the owner's logbook has it")


class Turns(unittest.TestCase):
    def test_a_move_is_played_and_the_reply_says_whose_turn_it_is(self):
        table = Table("tictactoe", HOUSE)  # the house plays X, so GitHub replies first
        outcome = table.move("a2")
        entry = next(e for e in table.mod.listing(games.replay(table.mod, table.outcomes[0].game)[-1], 1, 2)
                     if e["code"] == "a2")
        self.assertEqual(outcome.comment, f"⭕ **1... Oa2 is on the board.** Well played, @octocat.\n{entry['emoji']}"
                                          f" *{entry['title']}* · O takes the left edge\n@tannergolden, it's your"
                                          " move.\n")
        self.assertEqual(outcome.issue, 101)
        self.assertEqual(outcome.commit, "chore(tictactoe): ⭕ play 1... Oa2 in game 1\n\nMove 2, by octocat.")
        outcome = table.move("a1")
        self.assertRegex(outcome.comment, r"^❌ \*\*2\. Xa1\+ is on the board\. Block it!\*\*\n\S+ \*[^*]+!\* · X takes"
                                          r" the lower left corner, threatening c3\nGitHub's turn, with X threatening"
                                          r" c3: anyone but \[@tannergolden\]\([^)]+\) can pick O's reply on"
                                          r" \[the board\]\([^)]+\)\.\n$")
        self.assertIsNone(PING.search(outcome.comment), "the owner's own move pings nobody")

    def test_connect_four_s_reply_names_the_disc(self):
        table = Table("connectfour", GITHUB)  # GitHub drops the dark discs, so the house replies with a light one
        outcome = table.move("3")
        self.assertRegex(outcome.comment, r"^🪂 \*\*1\.\.\. ⚪3 is on the board\.\*\*\n\S+ \*[^*]+!\* · A light disc"
                                          r" down column 3, to row 1\nGitHub's turn: anyone but \[@tannergolden\]"
                                          r"\([^)]+\) can pick Dark's reply on \[the board\]")
        outcome = table.move("4", player=HUBOT)
        self.assertTrue(outcome.comment.startswith("🪂 **2. ⚫4 is on the board.** Well played, @hubot.\n"))
        self.assertTrue(outcome.comment.endswith("\n@tannergolden, it's your move.\n"))

    def test_the_house_s_turn_is_the_owner_s_alone_whichever_mark_it_plays(self):
        cases = {("tictactoe", GITHUB): ("O", "X"), ("connectfour", GITHUB): ("Light", "Dark")}
        for (key, opens), (house, github) in cases.items():
            table = Table(key, opens)
            code = table.mod.legal(games.replay(table.mod, table.game)[-1])[0]
            outcome = table.move(code, player=OCTOCAT)
            with self.subTest(key=key):
                self.assertFalse(outcome.changed)
                self.assertEqual(outcome.comment, f"⏳ **It's {LINKED}'s turn as {house}**, so `{code}` wasn't"
                                                  " played.\n"
                                                  f"GitHub plays {github}: once {house} moves, pick {github}'s reply on"
                                                  f" {BOARD}.\n")
                self.assertIsNone(PING.search(outcome.comment), "a turn away never pings the owner")

    def test_github_s_turn_is_for_everyone_but_the_owner_whichever_mark_it_plays(self):
        cases = {("tictactoe", HOUSE): "O", ("tictactoe", GITHUB): "X", ("connectfour", HOUSE): "Light",
                 ("connectfour", GITHUB): "Dark"}
        for (key, opens), github in cases.items():
            table = Table(key, opens)
            if opens == GITHUB:  # the house replies to the Arbiter's opening first
                table.move(table.mod.legal(games.replay(table.mod, table.game)[-1])[0])
            code = table.mod.legal(games.replay(table.mod, table.game)[-1])[0]
            outcome = table.move(code, player=OWNER)
            with self.subTest(key=key, opens=opens):
                self.assertFalse(outcome.changed)
                self.assertEqual(outcome.comment, f"⏳ **It's GitHub's turn as {github}**, so `{code}` wasn't played.\n"
                                                  f"{github}'s moves are for everyone but you. Your turn comes next.\n")

    def test_the_first_move_to_arrive_is_the_one_played_and_the_rest_are_too_late(self):
        table = Table("tictactoe", HOUSE)
        first = table.move("a2", move=2)
        late = table.move("c1", player=HUBOT, move=2)
        self.assertTrue(first.changed)
        self.assertEqual(late.comment, "⌛ **Too late: move 2 is already on the board**, so `c1` wasn't played.\n"
                                       f"1... Oa2 got there first, played by [@octocat](https://github.com/octocat)."
                                       f" Pick a move from {BOARD} as it stands now.\n")
        self.assertIsNone(PING.search(late.comment), "a turn away pings nobody, not even the player it names")
        self.assertIn("1... Oa2 got there first, played by you.", table.move("c1", player=OCTOCAT, move=2).comment)
        self.assertIn("1. Xb2 got there first, played by the Arbiter.", table.move("c1", move=1).comment)
        table = Table("connectfour", GITHUB)
        table.move("3")
        late = table.move("5", player=OWNER, move=2)
        self.assertIn("1... ⚪3 got there first, played by you.", late.comment)

    def test_a_move_for_another_game_or_move_is_turned_away(self):
        table = Table("connectfour", HOUSE)
        self.assertEqual(table.move("3", game=2, move=1).comment,
                         f"❓ **There's no game 2 yet**, so `3` wasn't played.\nGame 1 is under way on {BOARD}: pick a"
                         " move there.\n")
        self.assertEqual(table.move("3", move=7).comment,
                         f"❓ **The board is on move 2, not move 7**, so `3` wasn't played.\nPick a move from"
                         f" {BOARD} as it stands now.\n")
        self.assertEqual(len(table.game["moves"]), 1)

    def test_an_illegal_move_changes_nothing_and_says_why(self):
        table = Table("tictactoe", HOUSE)
        outcome = table.move("b2")
        self.assertFalse(outcome.changed)
        self.assertEqual(outcome.comment, "🚫 **`b2` isn't a legal move here**: there's already an X on b2.\nNothing"
                                          f" was played. Every move listed under {BOARD} is legal: pick one there.\n")
        table = Table("connectfour", HOUSE)
        for code in "44444":
            table.move(code)
        self.assertIn("**`4` isn't a legal move here**: column 4 is full.\n", table.move("4").comment)

    def test_a_threat_is_called_out_and_the_board_asks_for_the_block(self):
        table = Table("tictactoe", HOUSE)
        table.move("a2")
        table.move("a1")  # X has b2 and a1: c3 wins next
        element = table.board()
        self.assertEqual((element["alert"], element["threats"]), ("must block", {HOUSE: ["c3"], GITHUB: []}))
        self.assertEqual(element["prompt"], "🟢 **GitHub's turn!** @tannergolden played 2. Xa1+. Block c3! Pick a move"
                                            f" below by {page.day(table.clock + page.WEEK)}.")
        blunders = [entry for entry in element["moves"] if entry[0] == "⚠️"]
        self.assertEqual(len(blunders), len(element["moves"]) - 1, "every cell but the block is a blunder")
        block = next(entry for entry in element["moves"] if entry[2].startswith("Oc3"))
        self.assertEqual((block[0], block[3]), ("🛡️", "O blocks on c3"))
        self.assertTrue(all(entry[3].endswith("leaving c3 to X") for entry in blunders))

    def test_a_turned_away_move_pings_nobody(self):
        table = Table("connectfour", GITHUB)
        table.move("3")
        refusals = [table.move("3", player=OWNER), table.move("3", player=OCTOCAT, move=1),
                    table.move("3", move=9), table.move("3", game=4), table.move("3", game=1, move=2)]
        for outcome in refusals:
            self.assertFalse(outcome.changed, outcome.comment)
            self.assertIsNone(PING.search(outcome.comment), outcome.comment)


class Again(unittest.TestCase):
    """A run made over again, such as a re-run of its job, finds its own move already played: it is told so on its
    issue, as it was the first time, and never that it wasn't played."""

    def test_the_last_move_run_again_is_answered_as_it_was_and_the_page_drawn_again(self):
        table = Table("tictactoe", HOUSE)
        first = table.move("a2")
        again = games.play(table.mod, table.game, table.hall, games.Request("a2", 1, 2, table.issue, OCTOCAT,
                                                                            OCTOCAT_ID), OWNER, OWNER_ID, table.clock)
        self.assertFalse(again.changed)
        self.assertTrue(again.redraw)
        self.assertEqual((again.comment, again.issue), (first.comment, first.issue))

    def test_an_older_move_run_again_says_it_is_on_the_board(self):
        table = Table("connectfour", HOUSE)
        table.move("3")
        mine = table.issue
        table.move("4")
        again = games.play(table.mod, table.game, table.hall, games.Request("3", 1, 2, mine, OCTOCAT, OCTOCAT_ID),
                           OWNER, OWNER_ID, table.clock)
        self.assertEqual(again.comment, "✅ **1... ⚪3 is already on the board**, played from this issue.\nThe game has"
                                        f" moved on since: pick a move from {BOARD} as it stands now.\n")
        self.assertFalse(again.changed or again.redraw)

    def test_the_move_that_ended_a_game_run_again_says_so(self):
        table = Table("tictactoe", HOUSE)
        table.play(TTT_X_WINS)
        again = games.play(table.mod, table.game, table.hall, games.Request("a3", 1, 7, table.issue, OWNER, OWNER_ID),
                           OWNER, OWNER_ID, table.clock)
        opens = page.day(page.parse(table.game["started"]))
        self.assertEqual(again.comment, "✅ **4. Xa3# already ended game 1**, played from this issue.\n"
                                        f"Game 2 opens {opens} on {BOARD}.\n")
        self.assertTrue(again.redraw)
        table.fresh()
        again = games.play(table.mod, table.game, table.hall, games.Request("a3", 1, 7, table.issue, OWNER, OWNER_ID),
                           OWNER, OWNER_ID, table.clock)
        self.assertEqual(again.comment.splitlines()[1], f"Game 2 is under way on {BOARD}.")
        self.assertFalse(again.redraw, "the fresh board's opening is the last thing to happen now")


class Endings(unittest.TestCase):
    def test_the_house_wins_and_the_game_is_recorded(self):
        table = Table("tictactoe", HOUSE)
        outcome = table.play(TTT_X_WINS)
        ended = table.clock
        opens = ended + page.DISPLAY
        self.assertRegex(outcome.comment, r"^🏆 \*\*4\. Xa3#: three in a row!\*\* @tannergolden wins game 1\."
                                          r"\n\S+ \*[^*]+!\* · X takes a3, three in a row from a3 to c1\nIts final"
                                          rf" board stays up for two days: game 2 opens {page.day(opens)}, and the"
                                          r" Arbiter opens it for a side drawn at random\.\n$")
        self.assertTrue(outcome.commit.startswith("chore(tictactoe): 🏆 play 4. Xa3#, ending game 1 1-0\n\nMove 7, by"
                                                  " tannergolden."))
        record = table.hall[-1]
        self.assertEqual(record, {
            "game": 1, "result": "1-0", "reason": "three in a row", "winner": OWNER, "plies": 7,
            "started": table.outcomes[0].game["started"], "ended": page.stamp(ended),
            "deciding": {"move": "4. Xa3#", "player": OWNER, "player_id": OWNER_ID, "arbiter": False,
                         "issue": table.issue},
            "players": [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 3}], "house_moves": 3,
            "final": "X.O/OX./XOX", "line": ["a3", "b2", "c1"]})
        self.assertEqual({key: value for key, value in table.game.items() if key != "ended"},
                         {"game": 2, "started": page.stamp(opens), "moves": []})
        self.assertEqual([played["move"] for played in table.game["ended"]["moves"]], TTT_X_WINS)

    def test_github_wins_and_its_player_takes_a_place_in_the_hall_of_fame(self):
        table = Table("tictactoe", HOUSE)
        outcome = table.play(TTT_O_WINS)
        self.assertTrue(outcome.comment.startswith(
            "🏆 **3... Oa1#: three in a row!** GitHub wins game 1, and @octocat takes a place in the [Hall of Fame]"
            "(https://github.com/tannergolden) for the winning move.\n"))
        self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["result"], table.hall[-1]["line"]),
                         ("GitHub", "0-1", ["a1", "a2", "a3"]))
        table = Table("connectfour", GITHUB)
        outcome = table.play(C4_DARK_UP)
        self.assertTrue(outcome.comment.startswith("🏆 **4. ⚫4#: four in a row!** GitHub wins game 1, and @octocat"))
        self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["result"]), ("GitHub", "1-0"),
                         "Dark, which GitHub played, moved first")
        self.assertEqual(table.hall[-1]["line"], [[4, 1], [4, 2], [4, 3], [4, 4]])

    def test_every_way_connect_four_is_won_and_a_full_frame_drawn(self):
        cases = {
            "up": (C4_DARK_UP, HOUSE, "4. ⚫4#", "1-0", [[4, 1], [4, 2], [4, 3], [4, 4]],
                   "Four dark discs up column 4"),
            "light": (C4_LIGHT_UP, HOUSE, "7... ⚪5#", "0-1", [[5, 1], [5, 2], [5, 3], [5, 4]],
                      "Four light discs up column 5"),
            "diagonal": (C4_DARK_DIAGONAL, HOUSE, "8. ⚫3#", "1-0", [[1, 1], [2, 2], [3, 3], [4, 4]],
                         "Four dark discs on a diagonal"),
            "across": (C4_DARK_ACROSS, GITHUB, "7. ⚫4#", "1-0", [[1, 2], [2, 2], [3, 2], [4, 2]],
                       "Four dark discs across row 2"),
        }
        for name, (line, opens, deciding, result, cells, summary) in cases.items():
            table = Table("connectfour", opens)
            table.play(line)
            record = table.hall[-1]
            with self.subTest(name):
                self.assertEqual((record["deciding"]["move"], record["result"], record["reason"], record["line"]),
                                 (deciding, result, "four in a row", cells))
                self.assertIn(summary, table.board()["prompt"])
        table = Table("connectfour", HOUSE)
        outcome = table.play(C4_DRAW)
        self.assertTrue(outcome.comment.startswith("🤝 **21... ⚪5: game 1 is drawn on a full frame.**\n"))
        record = table.hall[-1]
        self.assertEqual((record["winner"], record["result"], record["reason"], record["plies"]),
                         (None, "1/2-1/2", "a full frame", 42))
        self.assertNotIn("line", record)
        self.assertNotIn(".", record["final"])

    def test_a_full_board_is_drawn(self):
        table = Table("tictactoe", GITHUB)
        outcome = table.play(TTT_DRAW)
        self.assertTrue(outcome.comment.startswith("🤝 **5. Xc3: game 1 is drawn on a full board.**\n"))
        self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["reason"], table.hall[-1]["final"]),
                         (None, "a full board", "OXX/XXO/OOX"))
        self.assertEqual(table.hall[-1]["house_moves"], 4, "the house played O, the four moves after X's")

    def test_the_record_names_the_game_its_days_its_result_and_who_played_each_move(self):
        table = Table("tictactoe", HOUSE)
        outcome = table.play(TTT_X_WINS)
        name, text = outcome.record
        self.assertEqual(name, "game-1.txt")
        self.assertEqual(text.splitlines()[:4], [
            "Tic-Tac-Toe, game 1: @tannergolden against GitHub",
            f"Played from {page.day(T0)} 2026 to {page.day(table.clock)} 2026, in EST.",
            "The Arbiter opened for @tannergolden, who played X; GitHub played O.",
            "@tannergolden won with 4. Xa3#, three in a row."])
        self.assertEqual([" ".join(line.split()) for line in text.splitlines()[5:12]],
                         ["1. Xb2 the Arbiter, opening the game", "1... Oa2 @octocat", "2. Xa1+ @tannergolden",
                          "2... Oc3 @octocat", "3. Xc1+ @tannergolden", "3... Ob1 @octocat", "4. Xa3# @tannergolden"])
        self.assertTrue(text.endswith("\nResult: 1-0\n"))
        table = Table("connectfour", HOUSE)
        text = table.play(C4_DRAW).record[1]
        self.assertIn("Drawn with 21... ⚪5, on a full frame.", text)


class TwoDays(unittest.TestCase):
    """The owner's rule: a finished game's final board stays up for two days, and then the fresh board comes by
    itself, the Arbiter's opening already on it. Nothing can be played meanwhile."""

    def test_the_final_board_shows_how_the_game_ended_and_lists_nothing_to_play(self):
        table = Table("tictactoe", HOUSE)
        table.play(TTT_X_WINS)
        opens = page.parse(table.game["started"])
        element = table.board()
        self.assertEqual({key: element[key] for key in ("kind", "board", "x", "game", "move", "players", "next")},
                         {"kind": "tictactoe", "board": "X.O/OX./XOX", "x": HOUSE, "game": 1, "move": 4, "players": 1,
                          "next": page.day(opens)})
        self.assertEqual(element["result"], {"winner": HOUSE, "how": "three in a row"})
        self.assertEqual(element["line"], ["a3", "b2", "c1"])
        self.assertEqual(element["last"], {"move": "Xa3#", "words": "X takes a3, three in a row from a3 to c1",
                                           "by": "@tannergolden", "when": page.day(table.clock)})
        self.assertEqual(element["history"], [[2, "Xa1+", "Oc3", "@octocat"], [3, "Xc1+", "Ob1", "@octocat"],
                                              [4, "Xa3#", "", ""]])
        for missing in ("moves", "due", "threats", "outlook", "alert"):
            self.assertNotIn(missing, element)
        self.assertEqual(element["prompt"],
                         f"🏆 **@tannergolden wins game 1!** X struck a3, b2 and c1. Game 2 opens {page.day(opens)}.")
        self.assertTrue(element["note"].startswith(f"Game 1 is over, and its final board stays up for two days:"
                                                   f" game 2 opens {page.until(opens)}, and nothing can be played until"
                                                   " then."))
        table = Table("connectfour", GITHUB)
        table.play(C4_DRAW)
        element = table.board()
        self.assertEqual((element["result"], element["opens"], element["light"]),
                         ({"winner": None, "how": "a full frame"}, GITHUB, HOUSE))
        self.assertTrue(element["prompt"].startswith("🤝 **Game 1 is drawn!** A full frame, and no four in a row."))
        self.assertNotIn("line", element)

    def test_a_move_meanwhile_is_told_the_day_the_next_game_opens(self):
        table = Table("connectfour", HOUSE)
        table.play(C4_DARK_UP)
        day = page.day(page.parse(table.game["started"]))
        said = (f"⏳ **Game 2 opens {day}**, so `3` wasn't played.\nGame 1's final board stays up until then: pick a"
                f" move from {BOARD} once game 2 is on it.\n")
        for game, move in ((2, 1), (2, 2), (1, 8), (1, 2), (3, 1)):
            with self.subTest(game=game, move=move):
                outcome = table.move("3", player=OCTOCAT, game=game, move=move)
                self.assertEqual(outcome.comment, said)
                self.assertFalse(outcome.changed)

    def test_the_fresh_board_comes_by_itself_with_the_arbiter_s_opening(self):
        table = Table("tictactoe", HOUSE)
        table.play(TTT_X_WINS)
        opens = page.parse(table.game["started"])
        before = table.wait(opens - table.clock - dt.timedelta(minutes=1))
        self.assertFalse(before.changed)
        self.assertEqual(before.log, f"game 1's final board is up until {page.stamp(opens)}")
        came = table.wait(dt.timedelta(minutes=1))
        self.assertTrue(came.changed)
        self.assertEqual((table.game["game"], len(table.game["moves"]), table.game["moves"][0]["at"]),
                         (2, 1, page.stamp(opens)), "the opening stands at the moment the board came")
        self.assertNotIn("ended", table.game)
        self.assertTrue(came.commit.startswith("chore(tictactoe): 🎲 open game 2 for "))
        element = table.board()
        self.assertNotIn("result", element)
        self.assertEqual((element["game"], element["due"]), (2, page.day(opens + page.WEEK)))
        self.assertRegex(element["prompt"], r"The Arbiter opened game 2 for (GitHub|@tannergolden) with X on"
                                            r" [a-c][1-3], at random\.$")
        over = table.move("a1", player=OCTOCAT, game=1, move=8)
        self.assertEqual(over.comment, "⌛ **Game 1 is over**, so `a1` wasn't played.\nGame 2 is under way on"
                                       f" {BOARD}: pick a move there.\n", "once game 2 is on the board")
        self.assertFalse(over.changed)

    def test_a_move_after_the_start_finds_the_opening_on_the_board_before_the_clock_comes(self):
        table = Table("connectfour", HOUSE)
        table.play(C4_DARK_UP)
        opens = page.parse(table.game["started"])
        table.clock = opens  # the moment the board comes, before the clock's run on the hour
        outcome = table.move("3", player=OCTOCAT, game=2, move=1, after=dt.timedelta(minutes=5))
        self.assertTrue(outcome.changed, "the opening is played and saved")
        self.assertIn("got there first, played by the Arbiter.", outcome.comment)
        self.assertEqual(len(table.game["moves"]), 1)
        self.assertTrue(outcome.commit.startswith("chore(connectfour): 🎲 open game 2 for "))


class Clock(unittest.TestCase):
    def test_a_side_has_a_whole_week_then_the_arbiter_moves_for_it(self):
        table = Table("tictactoe", HOUSE)
        table.move("a2")
        self.assertFalse(table.wait(page.WEEK - dt.timedelta(seconds=1)).changed)
        outcome = table.wait(dt.timedelta(seconds=1))
        self.assertTrue(outcome.changed)
        played = table.game["moves"][-1]
        self.assertEqual((played["arbiter"], played["player"], played["issue"]), (True, None, None))
        self.assertRegex(outcome.comment, r"^⏰ \*\*A week passed without a move from \[@tannergolden\]"
                                          r"\([^)]+\)\*\*, so the Arbiter played 2\. X[a-c][1-3]\+? for X, at"
                                          r" random\.\n\S+ \*[^*]+!\* · [^\n]+\nGitHub's turn")
        self.assertEqual((outcome.issue, outcome.logbook), (101, False), "told on the issue of the move it answers")
        self.assertIsNone(PING.search(outcome.comment), "the owner's own lapse goes to GitHub's player, unpinged")
        self.assertTrue(outcome.commit.startswith("chore(tictactoe): ⏰ play 2. X"))
        self.assertIn("after a week without a move\n\nMove 3 of game 1, by the Arbiter.", outcome.commit)

    def test_the_arbiter_after_itself_writes_in_the_logbook_and_pings_the_owner_on_their_turn(self):
        table = Table("connectfour", HOUSE)
        table.move("3")
        first = table.wait(page.WEEK)  # the house's lapse: on GitHub's player's issue
        self.assertEqual((first.issue, first.logbook), (101, False))
        second = table.wait(page.WEEK)  # GitHub's lapse, after the Arbiter's own move: the logbook
        self.assertEqual((second.issue, second.logbook), (None, True))
        self.assertTrue(second.comment.endswith("\n@tannergolden, it's your move.\n"))
        third = table.wait(page.WEEK)
        self.assertEqual((third.issue, third.logbook), (None, True))
        self.assertIsNone(PING.search(third.comment), "GitHub's turn pings nobody, even in the logbook")

    def test_the_arbiter_s_pick_is_the_same_however_often_it_is_asked(self):
        table = Table("tictactoe", GITHUB)
        later = table.clock + dt.timedelta(days=9)
        first = games.tick(table.mod, table.game, table.hall, OWNER, later)
        second = games.tick(table.mod, table.game, table.hall, OWNER, later + HOUR)
        self.assertEqual(first.game["moves"][-1]["move"], second.game["moves"][-1]["move"])

    def test_a_win_the_arbiter_played_counts_for_nobody_and_the_final_board_says_so(self):
        table = Table("tictactoe", HOUSE)
        table.play(TTT_X_WINS[:-1])
        before = table.game
        positions = games.replay(table.mod, before)
        arbiter = {"player": None, "player_id": None, "issue": None, "arbiter": True}
        outcome, shown, end = games.apply(table.mod, before, table.hall, positions, "a3", arbiter, OWNER, table.clock)
        table.keep(outcome)
        text = games.ended_text(table.mod, before, end, shown, arbiter, OWNER, "name", table.clock)
        self.assertTrue(text.startswith("🏆 **4. Xa3#: three in a row!** @tannergolden wins game 1 on the Arbiter's"
                                        " move."))
        self.assertIn("The winning move was the Arbiter's, played after a week without one, so the win counts for"
                      " nobody.", table.board()["note"])


class Board(unittest.TestCase):
    """What each game's element is given, all along its lines."""

    def boards(self):
        """Every board along every line of both games, both ways round: each one, its game and the table."""
        for key in KEYS:
            for line in LINES[key]:
                for opens in (HOUSE, GITHUB):
                    table = Table(key, opens, line[0])
                    yield table.board(), table
                    for code in line[1:]:
                        table.move(code)
                        yield table.board(), table
                    table.fresh()
                    yield table.board(), table

    def test_every_legal_move_is_listed_once_behind_a_link_that_plays_it(self):
        for key in KEYS:
            table = Table(key, GITHUB)
            for code in LINES[key][0][1:]:
                element = table.board()
                position = games.replay(table.mod, table.game)[-1]
                ply = len(table.game["moves"]) + 1
                titles = [urllib.parse.parse_qs(urllib.parse.urlparse(entry[4]).query)["title"][0]
                          for entry in element["moves"]]
                links = [INTAKE[key].fullmatch(title) for title in titles]
                self.assertTrue(all(links), titles)
                self.assertEqual([link["move"] for link in links], table.mod.legal(position))
                self.assertEqual({(link["game"], link["ply"]) for link in links}, {("1", str(ply))})
                self.assertEqual(len({entry[1] for entry in element["moves"]}), len(element["moves"]),
                                 "no two moves on a board share a title")
                side = games.side_of(table.game, ply)
                player, player_id = (OWNER, OWNER_ID) if side == HOUSE else (OCTOCAT, OCTOCAT_ID)
                for link in links:
                    request = games.Request(link["move"], 1, ply, 7, player, player_id)
                    played = games.play(table.mod, table.game, table.hall, request, OWNER, OWNER_ID, table.clock)
                    self.assertTrue(played.changed, (key, ply, link["move"], played.comment))
                table.move(code)

    def test_what_the_readme_carries_is_text_the_kit_accepts(self):
        for element, table in self.boards():
            key = table.key
            with self.subTest(key=key, game=element["game"], move=element["move"]):
                self.assertRegex(element[{"tictactoe": "board", "connectfour": "board"}[key]], KIT_BOARD[key])
                for field in ("prompt", "note"):
                    self.assertTrue(KIT_LINE.fullmatch(element[field]) and not KIT_BLOCK.match(element[field]),
                                    element[field])
                    self.assertNotIn("![", element[field])
                    for dash in DASHES:
                        self.assertNotIn(dash, element[field])
                self.assertLessEqual(len(element["prompt"]), page.BANNER, element["prompt"])
                for row in element["history"]:
                    self.assertTrue(len(row) == 4 and isinstance(row[0], int) and row[0] >= 1, row)
                    self.assertTrue(all(cell == "" or KIT_MOVE[key].fullmatch(cell) for cell in row[1:3]), row)
                    self.assertTrue(row[3] == "" or KIT_WHO.fullmatch(row[3]), row)
                if "last" in element:
                    self.assertRegex(element["last"]["move"], KIT_MOVE[key])
                    self.assertRegex(element["last"]["words"], KIT_WORDS)
                    self.assertRegex(element["last"]["by"], KIT_WHO)
                    self.assertRegex(element["last"]["when"], KIT_DAY)
                if "result" in element:
                    self.assertRegex(element["result"]["how"], KIT_HOW)
                    self.assertRegex(element["next"], KIT_DAY)
                    self.assertNotIn("moves", element)
                else:
                    self.assertRegex(element["due"], KIT_DAY)
                    self.assertTrue(element["moves"])
                for emoji, title, notation, words, url in element.get("moves", []):
                    self.assertRegex(emoji, KIT_EMOJI)
                    self.assertRegex(title, KIT_TITLE)
                    self.assertRegex(notation, KIT_MOVE[key])
                    self.assertRegex(words, KIT_WORDS)
                    self.assertTrue(url.startswith(f"https://github.com/tannergolden/play/issues/new?template=move.yml"
                                                   f"&title={key}%3A%20"), url)

    def test_the_score_sheet_names_who_chose_github_s_moves_whichever_side_opened(self):
        for opens, who in ((HOUSE, [[1, "Xb2", "Oa2", "@octocat"], [2, "Xa1+", "", ""]]),
                           (GITHUB, [[1, "Xb2", "Oa2", "the Arbiter"], [2, "Xa1+", "", "@octocat"]])):
            table = Table("tictactoe", opens)
            table.move("a2")
            table.move("a1")
            self.assertEqual(table.board()["history"], who)

    def test_the_outlook_says_who_wins_with_perfect_play(self):
        table = Table("tictactoe", GITHUB)  # GitHub plays X
        self.assertEqual(table.board()["outlook"], "draw")
        table.move("a2")  # the house's O on an edge loses to perfect play
        self.assertEqual(table.board()["outlook"], GITHUB)
        table = Table("tictactoe", HOUSE)
        table.move("a2")
        self.assertEqual(table.board()["outlook"], HOUSE)

    def test_every_banner_fits_one_line_however_long_the_game(self):
        for key in KEYS:
            mod = games.rules(key)
            for number in (1, 9_999, 999_999_999):
                for opens in (HOUSE, GITHUB):
                    game, _ = games.settle(mod, {"game": number, "started": page.stamp(T0), "moves": []}, T0)
                    game["opens"] = opens
                    banner = games.opening_banner(mod, game, OWNER)
                    with self.subTest(key=key, number=number, opens=opens):
                        self.assertLessEqual(len(banner), page.BANNER, banner)
            for shown in ("99999. Xa1+", "99999... Oa1#", "99999. ⚫4+", "99999... ⚪4+"):
                for side in (HOUSE, GITHUB):
                    for mover in ("The Arbiter", "@tannergolden", "GitHub"):
                        for calls in (["Block column 7! ", "Block it! "], ["Two threats! "], []):
                            banner = games.turn_banner(side, OWNER, mover, shown, calls, "28 Sep")
                            self.assertLessEqual(len(banner), page.BANNER, banner)

    def test_no_reply_or_commit_has_a_long_dash(self):
        texts = []
        for _, table in self.boards():
            texts += table.texts
        for dash in DASHES:
            self.assertNotIn(dash, "".join(texts))


class Script(unittest.TestCase):
    """The whole script, as the workflow runs it: the environment in, files and step outputs out."""

    def run_script(self, key: str, folder: Path, now: str, **values) -> tuple[int, Path]:
        out, output, settings = folder.parent / "out", folder.parent / "output.txt", folder.parent / "markdown.yaml"
        if not settings.exists():
            settings.write_text(SETTINGS, encoding="utf-8")
        env = {"OWNER": OWNER, "OWNER_ID": str(OWNER_ID), "GITHUB_OUTPUT": str(output),
               "RUN_URL": "https://github.com/tannergolden/tannergolden/actions/runs/1", **values}
        with contextlib.redirect_stdout(io.StringIO()):
            code = games.main([key, str(folder), "--out", str(out), "--now", now, "--settings", str(settings)], env)
        return code, out

    def test_the_clock_opens_the_first_game_and_a_move_is_played_and_answered(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "tictactoe"
            moment = opening_at("tictactoe", HOUSE, "b2")
            code, out = self.run_script("tictactoe", folder, page.stamp(moment))
            self.assertEqual(code, 0)
            saved = json.loads((folder / "game.json").read_text(encoding="utf-8"))
            self.assertEqual((saved["opens"], saved["moves"][0]["move"]), (HOUSE, "b2"))
            self.assertTrue((out / "commit.txt").read_text(encoding="utf-8").startswith(
                "chore(tictactoe): 🎲 open game 1 for tannergolden with 1. Xb2"))
            settings = (Path(temp) / "markdown.yaml").read_text(encoding="utf-8")
            self.assertIn('  # tictactoe:start\n  tictactoe:\n    kind: "tictactoe"\n    board: ".../.X./..."\n',
                          settings)
            self.assertIn("  # hall:start\n  hall-of-fame:\n", settings)
            self.assertTrue(settings.endswith("  # hall:end\n\ntrophies:\n  style: trophy\n"),
                            "the regions go at the end of elements:, before the next section")
            (Path(temp) / "output.txt").unlink()
            code, out = self.run_script("tictactoe", folder, page.stamp(moment + HOUR), MOVE="a2", GAME="1",
                                        MOVE_NUMBER="2", ISSUE="12", PLAYER=OCTOCAT, PLAYER_ID=str(OCTOCAT_ID))
            self.assertEqual(code, 0)
            self.assertIn("1... Oa2 is on the board", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=true\nissue=12\nlogbook=false\n")
            self.assertTrue((out / "commit.txt").read_text(encoding="utf-8").endswith(
                "\n\nRun: https://github.com/tannergolden/tannergolden/actions/runs/1\n"))

    def test_a_turned_away_move_saves_nothing_and_still_replies(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "connectfour"
            moment = opening_at("connectfour", GITHUB, "4")
            self.run_script("connectfour", folder, page.stamp(moment))
            before = (folder / "game.json").read_text(encoding="utf-8")
            (Path(temp) / "output.txt").unlink()
            code, out = self.run_script("connectfour", folder, page.stamp(moment + HOUR), MOVE="3", GAME="1",
                                        MOVE_NUMBER="2", ISSUE="13", PLAYER=OCTOCAT, PLAYER_ID=str(OCTOCAT_ID))
            self.assertEqual(code, 0)
            self.assertEqual((folder / "game.json").read_text(encoding="utf-8"), before)
            self.assertIn(f"It's {LINKED}'s turn as Light", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=false\nissue=13\nlogbook=false\n")

    def test_anything_malformed_is_turned_away_on_its_issue_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "tictactoe"
            good = {"MOVE": "a2", "GAME": "1", "MOVE_NUMBER": "2", "ISSUE": "1", "PLAYER": OCTOCAT,
                    "PLAYER_ID": str(OCTOCAT_ID)}
            for name, bad in (("MOVE", "d4"), ("MOVE", "a2; rm -rf"), ("MOVE", "4"), ("GAME", "0"),
                              ("MOVE_NUMBER", "x"), ("GAME", "1234567890"), ("PLAYER", "bad name"),
                              ("PLAYER_ID", "12a")):
                with self.subTest(name=name, bad=bad):
                    code, out = self.run_script("tictactoe", folder, "2026-10-12T16:00:00Z", **{**good, name: bad})
                    self.assertEqual(code, 0)
                    reply = (out / "comment.md").read_text(encoding="utf-8")
                    self.assertTrue(reply.startswith("🚫 **This move can't be played as sent**, so nothing was"
                                                     " played."))
                    self.assertIn("issue=1\n", (Path(temp) / "output.txt").read_text(encoding="utf-8"))
            self.assertFalse(folder.exists())
            code, _ = self.run_script("tictactoe", folder, "2026-10-12T16:00:00Z", **{**good, "MOVE": "z9",
                                                                                      "ISSUE": "x"})
            self.assertEqual(code, 1, "nowhere to say so: the run stops")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(games.main(["tictactoe", str(folder)], {"OWNER": OWNER}), 1)


if __name__ == "__main__":
    unittest.main()
