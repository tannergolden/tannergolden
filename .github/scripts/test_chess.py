# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The game on the profile, played offline: whole games through the same calls the workflow makes.

  python3 -m unittest discover -s .github/scripts -p 'test_chess*.py'

Moves come in as the intake sends them, from the owner as White and from
made-up players as Black, at times set by the test, so the Arbiter's week
passes in a line.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # chess.py imports chess_rules.py beside it
spec = importlib.util.spec_from_file_location("chess", HERE / "chess.py")
chess = importlib.util.module_from_spec(spec)
sys.modules["chess"] = chess  # dataclasses look their module up while the class is built
spec.loader.exec_module(chess)
rules = sys.modules["chess_rules"]
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
HUBOT, HUBOT_ID = "hubot", 480938
T0 = chess.parse("2026-10-11T16:00:00Z")
FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]
SCHOLARS_MATE = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]
LOYDS_STALEMATE = ("e2e3 a7a5 d1h5 a8a6 h5a5 h7h5 h2h4 a6h6 a5c7 f7f6 c7d7 e8f7 d7b7 d8d3 b7b8 d3h7 b8c8 f7g6 "
                   "c8e6").split()


def request(uci: str, move: int, game: int = 1, issue: int = 100, player: str = OCTOCAT,
            player_id: int = OCTOCAT_ID) -> chess.Request:
    return chess.Request(uci, game, move, issue, player, player_id)


class Table:
    """A game at the profile: the state between moves, and every reply so far."""

    def __init__(self):
        self.game, self.hall, self.outcomes, self.texts = None, [], [], []
        self.clock, self.issue = T0, 100

    def move(self, uci: str, player: str | None = None, player_id: int | None = None, move: int | None = None,
             game: int | None = None, after: dt.timedelta = dt.timedelta(hours=1)) -> chess.Outcome:
        """A move from whoever's turn it is, at the move on the board, unless the test says otherwise."""
        current = self.game or chess.new_game(1, self.clock)
        white = len(current["moves"]) % 2 == 0
        player = player or (OWNER if white else OCTOCAT)
        player_id = player_id or (OWNER_ID if player == OWNER else OCTOCAT_ID)
        self.clock += after
        self.issue += 1
        outcome = chess.play(self.game, self.hall, request(uci, move or len(current["moves"]) + 1,
                                                            game or current["game"], self.issue, player, player_id),
                             OWNER, OWNER_ID, self.clock)
        return self.keep(outcome)

    def wait(self, span: dt.timedelta) -> chess.Outcome:
        self.clock += span
        return self.keep(chess.tick(self.game, self.hall, OWNER, self.clock))

    def keep(self, outcome: chess.Outcome) -> chess.Outcome:
        if outcome.changed:
            self.game, self.hall = outcome.game, outcome.hall
        self.outcomes.append(outcome)
        self.texts += [outcome.comment, outcome.commit]
        return outcome

    def play(self, ucis: list[str]) -> chess.Outcome:
        outcome = None
        for uci in ucis:
            outcome = self.move(uci)
            assert outcome.changed, f"{uci}: {outcome.comment}"
        return outcome


class Turns(unittest.TestCase):
    def test_the_owner_opens_the_first_game(self):
        table = Table()
        outcome = table.move("e2e4")
        self.assertTrue(outcome.changed)
        self.assertEqual(outcome.game["game"], 1)
        self.assertEqual(outcome.game["moves"][0]["san"], "e4")
        self.assertEqual(outcome.game["started"], "2026-10-11T17:00:00Z")
        self.assertEqual(outcome.issue, 101)
        self.assertIn("**1. e4 is on the board.** It is GitHub's turn", outcome.comment)
        self.assertTrue(outcome.commit.startswith("chore(chess): ♟️ play 1. e4 in game 1\n\nMove 1, by tannergolden."))

    def test_nobody_else_can_open_it(self):
        outcome = Table().move("e2e4", player=OCTOCAT)
        self.assertFalse(outcome.changed)
        self.assertIsNone(outcome.game)
        self.assertIn("It is tannergolden's turn as White", outcome.comment)
        self.assertNotIn("@tannergolden", outcome.comment)  # a turn away never pings the owner

    def test_a_move_for_github_hands_the_turn_to_the_owner(self):
        table = Table()
        table.move("e2e4")
        outcome = table.move("c7c5")
        self.assertIn("**1... c5 is on the board**, played by @octocat. @tannergolden, it is your move.",
                      outcome.comment)

    def test_the_owner_cannot_play_for_github(self):
        table = Table()
        table.move("e2e4")
        outcome = table.move("e7e5", player=OWNER)
        self.assertFalse(outcome.changed)
        self.assertIn("It is GitHub's turn as Black", outcome.comment)

    def test_the_first_move_to_arrive_is_the_one_played(self):
        table = Table()
        table.move("e2e4")
        first = table.move("c7c5", move=2)
        late = table.move("e7e5", player=HUBOT, player_id=HUBOT_ID, move=2)
        self.assertTrue(first.changed)
        self.assertFalse(late.changed)
        self.assertIn("**The board moved on**, so e7e5 was not played: move 2 is already on it, 1... c5,"
                      " by @octocat.", late.comment)

    def test_a_move_sent_twice_is_told_it_was_its_own(self):
        table = Table()
        table.move("e2e4")
        table.move("c7c5", move=2)
        again = table.move("c7c5", player=OCTOCAT, move=2)
        self.assertIn("1... c5, by you.", again.comment)

    def test_a_move_for_another_game_or_move_is_turned_away(self):
        table = Table()
        table.move("e2e4")
        self.assertIn("There is no game 2 yet", table.move("e7e5", game=2, move=1).comment)
        self.assertIn("The board is on move 2**, not move 5", table.move("e7e5", move=5).comment)
        self.assertEqual(len(table.game["moves"]), 1)


class Legality(unittest.TestCase):
    def reason(self, fen: str, uci: str) -> str:
        return chess.why_illegal(rules.Position.from_fen(fen), uci)

    def test_says_why_a_move_is_not_legal(self):
        self.assertEqual(self.reason(rules.START, "e3e4"), "there is no piece on e3")
        self.assertEqual(self.reason(rules.START, "e7e5"), "the pawn on e7 is Black's")
        self.assertEqual(self.reason(rules.START, "e2e5"), "the pawn on e2 cannot move to e5")
        self.assertEqual(self.reason(rules.START, "e2e4q"),
                         "only a pawn reaching the last rank names a piece to become, so it is e2e4")
        self.assertEqual(self.reason("7k/P7/8/8/8/8/8/K7 w - - 0 1", "a7a8"),
                         "a pawn reaching the last rank has to say what it becomes, such as a7a8q")
        # The bishop on e2 is pinned to its king by the rook on e7.
        self.assertEqual(self.reason("4k3/4r3/8/8/8/8/4B3/4K3 w - - 0 1", "e2d3"), "it would leave the king in check")
        self.assertEqual(self.reason("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c2"), "the king on e1 cannot move to c2")

    def test_an_illegal_move_changes_nothing_and_says_why(self):
        table = Table()
        outcome = table.move("e2e5")
        self.assertFalse(outcome.changed)
        self.assertIn("🚫 **e2e5 is not a legal move here**: the pawn on e2 cannot move to e5. Nothing was played.",
                      outcome.comment)


class Endings(unittest.TestCase):
    def test_a_checkmate_for_github_puts_its_player_in_the_hall_of_fame(self):
        table = Table()
        outcome = table.play(FOOLS_MATE)
        self.assertIn("🏆 **2... Qh4#: checkmate.** GitHub wins game 1, and @octocat goes into the Hall of Fame",
                      outcome.comment)
        self.assertIn("Game 2 starts now, and @tannergolden opens it as White.", outcome.comment)
        record = table.hall[-1]
        self.assertEqual((record["game"], record["result"], record["reason"], record["winner"], record["plies"]),
                         (1, "0-1", "checkmate", "GitHub", 4))
        self.assertEqual(record["deciding"], {"move": "2... Qh4#", "player": OCTOCAT, "player_id": OCTOCAT_ID,
                                              "arbiter": False})
        self.assertEqual(record["players"], [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 2}])
        self.assertEqual(table.game, {"game": 2, "started": record["ended"], "fen": rules.START, "moves": []})
        self.assertEqual(outcome.pgn[0], "game-1.pgn")
        self.assertTrue(outcome.commit.startswith("chore(chess): 🏆 play 2... Qh4#, ending game 1 0-1"))

    def test_a_checkmate_for_the_owner_says_so(self):
        outcome = Table().play(SCHOLARS_MATE)
        self.assertIn("🏆 **4. Qxf7#: checkmate.** @tannergolden wins game 1. Game 2 starts now", outcome.comment)

    def test_a_stalemate_is_drawn_and_the_next_game_starts(self):
        table = Table()
        outcome = table.play(LOYDS_STALEMATE)
        self.assertIn("🤝 **10. Qe6: game 1 is drawn by stalemate.** Game 2 starts now", outcome.comment)
        self.assertEqual((table.hall[-1]["result"], table.hall[-1]["winner"]), ("1/2-1/2", None))
        self.assertIn("Game 1 is over", table.move("e2e4", game=1, move=20).comment)
        self.assertTrue(table.move("d2d4").changed)
        self.assertEqual((table.game["game"], table.game["moves"][0]["san"]), (2, "d4"))

    def test_the_finished_game_is_written_as_pgn_with_every_player(self):
        table = Table()
        table.move("f2f3")
        table.move("e7e5", player=HUBOT, player_id=HUBOT_ID)
        table.move("g2g4")
        text = table.move("d8h4").pgn[1]
        self.assertIn('[Event "@tannergolden vs. GitHub"]\n[Site "https://github.com/tannergolden"]\n', text)
        self.assertIn('[Round "1"]\n[White "tannergolden"]\n[Black "GitHub"]\n[Result "0-1"]\n', text)
        movetext = " ".join(text.split("\n\n", 1)[1].split())
        self.assertEqual(movetext, "1. f3 {tannergolden} 1... e5 {hubot} 2. g4 {tannergolden} 2... Qh4# {octocat}"
                                   " {Checkmate.} 0-1")
        self.assertTrue(all(len(line) <= 79 for line in text.splitlines()))

    def test_players_are_counted_by_account_under_their_newest_login(self):
        table = Table()
        table.move("f2f3")
        table.move("e7e5", player="octo-old", player_id=OCTOCAT_ID)
        table.move("g2g4")
        table.move("d8h4", player=OCTOCAT, player_id=OCTOCAT_ID)
        self.assertEqual(table.hall[-1]["players"], [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 2}])


class Clock(unittest.TestCase):
    def test_nothing_happens_before_the_first_game(self):
        outcome = Table().wait(dt.timedelta(days=30))
        self.assertFalse(outcome.changed)
        self.assertEqual(outcome.log, "no game has started")

    def test_a_side_has_a_whole_week(self):
        table = Table()
        table.move("e2e4")
        outcome = table.wait(dt.timedelta(days=7) - dt.timedelta(seconds=1))
        self.assertFalse(outcome.changed)
        self.assertEqual(outcome.log, "the side to move has until 2026-10-18T17:00:00Z")

    def test_after_a_week_the_arbiter_moves_for_github_and_tells_the_owner(self):
        table = Table()
        table.move("e2e4")
        outcome = table.wait(dt.timedelta(days=7))
        self.assertTrue(outcome.changed)
        played = outcome.game["moves"][-1]
        self.assertEqual((played["arbiter"], played["player"], played["issue"]), (True, None, None))
        self.assertIn(played["uci"], {move.uci for move in rules.legal_moves(chess.replay(table.game)[1])})
        self.assertEqual(outcome.issue, 101)  # the owner's own move, so the notice reaches them
        self.assertIn("⏰ **A week went by without a move from GitHub**, so the Arbiter played 1... ", outcome.comment)
        self.assertIn("@tannergolden, it is your move.", outcome.comment)
        self.assertIn("after a week without a move\n\nMove 2 of game 1, by the Arbiter.", outcome.commit)

    def test_after_a_week_the_arbiter_moves_for_the_owner_and_tells_github(self):
        table = Table()
        table.move("e2e4")
        table.move("c7c5")
        outcome = table.wait(dt.timedelta(days=8))
        self.assertEqual(outcome.issue, 102)  # the last move GitHub played
        self.assertIn("A week went by without a move from tannergolden", outcome.comment)
        self.assertIn("at random for White. It is GitHub's turn", outcome.comment)
        self.assertNotIn("@tannergolden", outcome.comment)

    def test_the_arbiters_pick_is_the_same_however_often_it_is_asked(self):
        table = Table()
        table.move("e2e4")
        later = table.clock + dt.timedelta(days=9)
        first = chess.tick(table.game, table.hall, OWNER, later)
        second = chess.tick(table.game, table.hall, OWNER, later + dt.timedelta(hours=1))
        self.assertEqual(first.game["moves"][-1]["uci"], second.game["moves"][-1]["uci"])

    def test_the_clock_starts_again_after_the_arbiter_moves(self):
        table = Table()
        table.move("e2e4")
        table.wait(dt.timedelta(days=7))
        self.assertFalse(table.wait(dt.timedelta(days=6)).changed)
        self.assertTrue(table.wait(dt.timedelta(days=1)).changed)
        self.assertEqual(len(table.game["moves"]), 3)

    def test_an_opening_left_a_week_is_played_with_nobody_to_tell(self):
        table = Table()
        table.play(FOOLS_MATE)
        outcome = table.wait(dt.timedelta(days=7))
        self.assertTrue(outcome.changed)
        self.assertEqual((table.game["game"], len(table.game["moves"])), (2, 1))
        self.assertIsNone(outcome.issue)


class Words(unittest.TestCase):
    def test_no_reply_or_commit_has_a_long_dash(self):
        table = Table()
        table.play(FOOLS_MATE)
        table.play(LOYDS_STALEMATE)
        table.move("e2e5")
        table.move("e2e4", player=OCTOCAT)
        table.wait(dt.timedelta(days=8))
        table.wait(dt.timedelta(days=8))
        table.move("a2a3", move=1)
        text = "".join(table.texts)
        for dash in DASHES:
            self.assertNotIn(dash, text)


class Script(unittest.TestCase):
    """The whole script, as the workflow runs it: the environment in, files and step outputs out."""

    def run_script(self, folder: Path, now: str, **values) -> tuple[int, Path]:
        out = folder.parent / "out"
        output = folder.parent / "output.txt"
        env = {"OWNER": OWNER, "OWNER_ID": str(OWNER_ID), "GITHUB_OUTPUT": str(output),
               "RUN_URL": "https://github.com/tannergolden/tannergolden/actions/runs/1", **values}
        with contextlib.redirect_stdout(io.StringIO()):  # the run's log line
            code = chess.main([str(folder), "--out", str(out), "--now", now], env)
        return code, out

    def test_a_move_is_saved_and_its_reply_written(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            code, out = self.run_script(folder, "2026-10-11T16:00:00Z", UCI="e2e4", GAME="1", MOVE_NUMBER="1",
                                        ISSUE="12", PLAYER=OWNER, PLAYER_ID=str(OWNER_ID))
            self.assertEqual(code, 0)
            saved = json.loads((folder / "game.json").read_text(encoding="utf-8"))
            self.assertEqual([played["uci"] for played in saved["moves"]], ["e2e4"])
            self.assertEqual(saved["fen"], "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
            self.assertIn("1. e4 is on the board", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertTrue((out / "commit.txt").read_text(encoding="utf-8").endswith(
                "Run: https://github.com/tannergolden/tannergolden/actions/runs/1\n"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"), "changed=true\nissue=12\n")

    def test_a_turned_away_move_saves_nothing_and_still_replies(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            code, out = self.run_script(folder, "2026-10-11T16:00:00Z", UCI="e7e5", GAME="1", MOVE_NUMBER="1",
                                        ISSUE="13", PLAYER=OCTOCAT, PLAYER_ID=str(OCTOCAT_ID))
            self.assertEqual(code, 0)
            self.assertFalse(folder.exists())
            self.assertIn("It is tannergolden's turn", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"), "changed=false\nissue=13\n")

    def test_a_whole_game_ends_in_the_hall_of_fame_and_a_pgn(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            for number, uci in enumerate(FOOLS_MATE, 1):
                player, player_id = (OWNER, OWNER_ID) if number % 2 else (OCTOCAT, OCTOCAT_ID)
                code, _ = self.run_script(folder, f"2026-10-11T1{number}:00:00Z", UCI=uci, GAME="1",
                                          MOVE_NUMBER=str(number), ISSUE=str(20 + number), PLAYER=player,
                                          PLAYER_ID=str(player_id))
                self.assertEqual(code, 0)
            hall = json.loads((folder / "hall-of-fame.json").read_text(encoding="utf-8"))
            self.assertEqual(hall[0]["deciding"]["player"], OCTOCAT)
            self.assertTrue((folder / "games" / "game-1.pgn").exists())
            self.assertEqual(json.loads((folder / "game.json").read_text(encoding="utf-8"))["game"], 2)

    def test_the_clock_run_takes_no_move(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            self.run_script(folder, "2026-10-01T09:00:00Z", UCI="d2d4", GAME="1", MOVE_NUMBER="1", ISSUE="5",
                            PLAYER=OWNER, PLAYER_ID=str(OWNER_ID))
            code, out = self.run_script(folder, "2026-10-09T09:00:00Z")
            self.assertEqual(code, 0)
            saved = json.loads((folder / "game.json").read_text(encoding="utf-8"))
            self.assertTrue(saved["moves"][-1]["arbiter"])
            self.assertIn("issue=5\n", (Path(temp) / "output.txt").read_text(encoding="utf-8"))

    def test_anything_malformed_stops_the_run(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            good = {"UCI": "e2e4", "GAME": "1", "MOVE_NUMBER": "1", "ISSUE": "1", "PLAYER": OWNER,
                    "PLAYER_ID": str(OWNER_ID)}
            for name, bad in (("UCI", "e2e9"), ("UCI", "e2e4; rm -rf"), ("GAME", "0"), ("MOVE_NUMBER", "x"),
                              ("ISSUE", "-1"), ("PLAYER", "bad name"), ("PLAYER_ID", "12a")):
                with self.subTest(name=name, bad=bad):
                    code, _ = self.run_script(folder, "2026-10-11T16:00:00Z", **{**good, name: bad})
                    self.assertEqual(code, 1)
            self.assertFalse(folder.exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chess.main([str(folder), "--now", "2026-10-11T16:00:00Z"], {"OWNER": OWNER}), 1)

    def test_a_game_with_an_impossible_move_is_never_replayed_quietly(self):
        with self.assertRaises(ValueError):
            chess.replay({"game": 1, "started": "2026-10-11T16:00:00Z", "moves": [{"uci": "e2e5"}]})


if __name__ == "__main__":
    unittest.main()
