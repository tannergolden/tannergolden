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
import re
import tempfile
import unittest
import urllib.parse
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
# What tannergolden/markdown accepts from the game (src/domain/elements/chess/game.py): a move in SAN, its link to a
# ready-made issue, its emoji, title and words, a line of the README, who played a move, and a day.
KIT_SAN = re.compile(r"(?:O-O(?:-O)?|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h](?:x[a-h])?[1-8](?:=[QRBN])?)[+#]?")
KIT_LINK = re.compile(r"https://github\.com/tannergolden/play/issues/new\?template=move\.yml&title=chess%3A%20"
                      r"[a-h][1-8][a-h][1-8][qrbn]?%20%C2%B7%20game%20[1-9][0-9]{0,8}%20%C2%B7%20move%20[1-9][0-9]{0,8}")
KIT_LINE = re.compile(r"[^<>|\n\r]{1,400}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
KIT_EMOJI = re.compile("[\u2190-\u2bff\U0001f000-\U0001faff\u200d\ufe0f]{1,8}")
KIT_WHO = re.compile(r"@[A-Za-z0-9][A-Za-z0-9-]{0,38}|the Arbiter")
KIT_DAY = re.compile(r"(?:[1-9]|[12][0-9]|3[01]) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
# Nothing that would open a block of its own in the README where a prompt or note is set.
KIT_BLOCK = re.compile(r"\s|```|~~~|#{1,6}(?:\s|$)|>|[-*+](?:\s|$)|[0-9]+[.)](?:\s|$)|\[[^\]]*\]:|[-=*_\s]+$")
# A mention GitHub notifies: an @handle outside the text of a link.
# What tannergolden/play's intake takes as a move link's title (its intake/routes.json): any move, game and move
# number up to nine digits each, the same as the game's own.
INTAKE = re.compile(r"chess: (?P<uci>[a-h][1-8][a-h][1-8][qrbn]?) \u00b7 game (?P<game>[1-9][0-9]{0,8})"
                    r" \u00b7 move (?P<move>[1-9][0-9]{0,8})")
# Games that reach every kind of move there is, each line checked against python-chess when it was written.
SPECIAL = {
    "White castles kingside, Black queenside": "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 e1g1 f8c5 d2d3 d7d6 c1g5 c8g4 b1c3 d8d7 "
                                               "d1d2 e8c8",
    "White castles queenside, Black kingside": "d2d4 d7d5 b1c3 g8f6 c1f4 e7e6 d1d2 f8e7 e1c1 e8g8",
    "White takes en passant": "e2e4 a7a6 e4e5 d7d5 e5d6",
    "Black takes en passant": "a2a3 e7e5 a3a4 e5e4 d2d4 e4d3",
    "White promotes, by push and by capture": "a2a4 b7b5 a4b5 a7a6 b5a6 c8b7 a6b7 b8c6 b7a8q",
    "Black promotes, by push and by capture": "h2h3 g7g5 h3h4 g5h4 g2g3 h4g3 g1f3 g3g2 f3g5 g2h1q",
}
PING = re.compile(r"(?<![\[\w])@[A-Za-z0-9][A-Za-z0-9-]*")
LINKED = "[@tannergolden](https://github.com/tannergolden)"
SETTINGS = "elements:\n  # chess:start\n  # chess:end\n  other:\n    kind: placard\n"
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
        self.assertRegex(outcome.comment, r"^♟️ \*\*1\. e4 is on the board\.\*\*\n\S+ \*[^*]+!\* · Pawn from e2 to e4,"
                                          r" two squares\nGitHub's turn: anyone but \[@tannergolden\]\([^)]+\) can pick"
                                          r" Black's reply on \[the board\]")
        self.assertTrue(outcome.commit.startswith("chore(chess): ♟️ play 1. e4 in game 1\n\nMove 1, by tannergolden."))

    def test_nobody_else_can_open_it(self):
        outcome = Table().move("e2e4", player=OCTOCAT)
        self.assertFalse(outcome.changed)
        self.assertIsNone(outcome.game)
        self.assertIn(f"⏳ **It's {LINKED}'s turn as White**, so `e2e4` wasn't played.", outcome.comment)
        self.assertIsNone(PING.search(outcome.comment), "a turn away never pings the owner")

    def test_a_move_for_github_hands_the_turn_to_the_owner(self):
        table = Table()
        table.move("e2e4")
        outcome = table.move("c7c5")
        self.assertRegex(outcome.comment, r"\*\*1\.\.\. c5 is on the board\.\*\* Well played, @octocat\.\n"
                                          r"\S+ \*[^*]+!\* · Pawn from c7 to c5, two squares\n@tannergolden, it's your"
                                          r" move\.\n$")

    def test_the_owner_cannot_play_for_github(self):
        table = Table()
        table.move("e2e4")
        outcome = table.move("e7e5", player=OWNER)
        self.assertFalse(outcome.changed)
        self.assertIn("⏳ **It's GitHub's turn as Black**, so `e7e5` wasn't played.\nBlack's moves are for everyone"
                      " but you.", outcome.comment)

    def test_the_first_move_to_arrive_is_the_one_played(self):
        table = Table()
        table.move("e2e4")
        first = table.move("c7c5", move=2)
        late = table.move("e7e5", player=HUBOT, player_id=HUBOT_ID, move=2)
        self.assertTrue(first.changed)
        self.assertFalse(late.changed)
        self.assertIn("**Too late: move 2 is already on the board**, so `e7e5` wasn't played.\n1... c5 got there first,"
                      " played by [@octocat](https://github.com/octocat).", late.comment)
        self.assertIsNone(PING.search(late.comment), "a turn away pings nobody, not even the player it names")

    def test_a_move_sent_twice_is_told_it_was_its_own(self):
        table = Table()
        table.move("e2e4")
        table.move("c7c5", move=2)
        again = table.move("c7c5", player=OCTOCAT, move=2)
        self.assertIn("1... c5 got there first, played by you.", again.comment)

    def test_a_move_for_another_game_or_move_is_turned_away(self):
        table = Table()
        table.move("e2e4")
        self.assertIn("There's no game 2 yet", table.move("e7e5", game=2, move=1).comment)
        self.assertIn("The board is on move 2, not move 5**", table.move("e7e5", move=5).comment)
        self.assertEqual(len(table.game["moves"]), 1)


class Again(unittest.TestCase):
    """A run made over again, such as a re-run of its job, finds its own move already played: it is told so on its
    issue, as it was the first time, and never that it wasn't played."""

    def test_the_last_move_run_again_is_answered_as_it_was_and_the_page_drawn_again(self):
        table = Table()
        table.move("e2e4")
        first = table.move("e7e5")
        again = chess.play(table.game, table.hall, request("e7e5", 2, issue=table.issue), OWNER, OWNER_ID,
                           table.clock + dt.timedelta(minutes=5))
        self.assertFalse(again.changed, "nothing new to save")
        self.assertTrue(again.redraw, "but the page is drawn again, in case the first run's drawing never happened")
        self.assertEqual((again.comment, again.issue), (first.comment, first.issue))
        self.assertNotIn("wasn't played", again.comment)

    def test_an_older_move_run_again_says_it_is_on_the_board_and_pings_nobody(self):
        table = Table()
        table.move("e2e4")
        table.move("e7e5")
        mine = table.issue
        table.move("g1f3")
        again = chess.play(table.game, table.hall, request("e7e5", 2, issue=mine), OWNER, OWNER_ID, table.clock)
        self.assertEqual(again.comment, "✅ **1... e5 is already on the board**, played from this issue.\nThe game has"
                                        " moved on since: pick a move from [the board](https://github.com/tannergolden)"
                                        " as it stands now.\n")
        self.assertFalse(again.changed or again.redraw)
        self.assertIsNone(PING.search(again.comment))

    def test_someone_else_s_move_is_still_too_late(self):
        table = Table()
        table.move("e2e4")
        table.move("e7e5")
        late = chess.play(table.game, table.hall, request("e7e5", 2, issue=999, player=HUBOT, player_id=HUBOT_ID),
                          OWNER, OWNER_ID, table.clock)
        self.assertIn("⌛ **Too late: move 2 is already on the board**", late.comment)
        self.assertFalse(late.redraw)

    def test_the_move_that_ended_a_game_run_again_says_so(self):
        table = Table()
        table.play(FOOLS_MATE)
        again = chess.play(table.game, table.hall, request("d8h4", 4, issue=table.issue), OWNER, OWNER_ID, table.clock)
        self.assertEqual(again.comment, "✅ **2... Qh4# already ended game 1**, played from this issue.\n"
                                        "Game 2 is under way on [the board](https://github.com/tannergolden).\n")
        self.assertTrue(again.redraw, "game 2 has no move yet, so the ending is still the last thing to happen")
        table.move("e2e4")
        again = chess.play(table.game, table.hall, request("d8h4", 4, issue=table.issue - 1), OWNER, OWNER_ID,
                           table.clock)
        self.assertFalse(again.redraw)


class Legality(unittest.TestCase):
    def reason(self, fen: str, uci: str) -> str:
        return chess.why_illegal(rules.Position.from_fen(fen), uci)

    def test_says_why_a_move_is_not_legal(self):
        self.assertEqual(self.reason(rules.START, "e3e4"), "there's no piece on e3")
        self.assertEqual(self.reason(rules.START, "e7e5"), "the pawn on e7 is Black's")
        self.assertEqual(self.reason(rules.START, "e2e5"), "the pawn on e2 can't move to e5")
        self.assertEqual(self.reason(rules.START, "e2e4q"),
                         "only a pawn reaching the last rank names a piece to become, so the move is `e2e4`")
        self.assertEqual(self.reason("7k/P7/8/8/8/8/8/K7 w - - 0 1", "a7a8"),
                         "a pawn reaching the last rank has to say what it becomes, such as `a7a8q` for a queen")
        # The bishop on e2 is pinned to its king by the rook on e7.
        self.assertEqual(self.reason("4k3/4r3/8/8/8/8/4B3/4K3 w - - 0 1", "e2d3"),
                         "the bishop on e2 is pinned to your king")
        self.assertEqual(self.reason("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1c2"), "the king on e1 can't move to c2")

    def test_says_what_check_does_to_a_move(self):
        cases = {
            # the rook on a1 checks along the first rank, and a pawn step doesn't block it
            ("4k3/8/8/8/8/8/3P4/r3K3 w - - 0 1", "d2d3"): "your king is in check, and this move doesn't get it out",
            ("7k/4P3/8/8/8/8/8/2r1K3 w - - 0 1", "e7e8"): "your king is in check, and this move doesn't get it out",
            # the rook on f2 guards e2; the queen on c3 guards d2, checking or not
            ("4k3/8/8/8/8/8/5r2/4K3 w - - 0 1", "e1e2"): "the king can't step into check on e2",
            ("6k1/8/8/8/8/2q5/8/4K3 w - - 0 1", "e1d2"): "the king can't step into check on d2",
            # pinned to the king: a pawn by the queen on c3, and one on its way to the last rank by the rook on a7
            ("6k1/8/8/8/8/2q5/3P4/4K3 w - - 0 1", "d2d4"): "the pawn on d2 is pinned to your king",
            ("8/r2P3K/8/8/8/8/8/1k6 w - - 0 1", "d7d8"): "the pawn on d7 is pinned to your king",
            ("8/r2P3K/8/8/8/8/8/1k6 w - - 0 1", "d7d8q"): "the pawn on d7 is pinned to your king",
            # a free pawn on the last rank is only asked what it becomes; a blocked one can't go
            ("6k1/3P4/8/8/b7/8/8/K7 w - - 0 1", "d7d8"):
                "a pawn reaching the last rank has to say what it becomes, such as `d7d8q` for a queen",
            ("1r6/1P6/8/8/8/8/8/1K5k w - - 0 1", "b7b8"): "the pawn on b7 can't move to b8",
            ("4k3/q7/8/8/8/8/8/7K b - - 0 1", "a7b5"): "the queen on a7 can't move to b5",
        }
        for (fen, uci), said in cases.items():
            with self.subTest(fen=fen, uci=uci):
                self.assertEqual(self.reason(fen, uci), said)

    def test_says_why_the_king_can_t_castle(self):
        cases = {
            ("4k3/8/8/8/8/8/8/4K2R w Q - 0 1", "e1g1"):
                "the right to castle kingside is gone: the king or that rook has moved, or the rook was taken",
            ("4k3/8/8/8/8/8/8/R2QK3 w Q - 0 1", "e1c1"):
                "the squares between the king and the rook must be empty to castle queenside",
            ("4r1k1/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"): "the king can't castle out of check",
            ("5rk1/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"): "the king can't castle across f1, which is under attack",
            ("k5r1/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"): "the king can't castle into check",
            ("r3k3/8/8/8/8/8/8/3RK3 b q - 0 1", "e8c8"): "the king can't castle across d8, which is under attack",
        }
        for (fen, uci), said in cases.items():
            with self.subTest(fen=fen, uci=uci):
                self.assertEqual(self.reason(fen, uci), said)

    def test_an_illegal_move_changes_nothing_and_says_why(self):
        table = Table()
        outcome = table.move("e2e5")
        self.assertFalse(outcome.changed)
        self.assertIn("🚫 **`e2e5` isn't a legal move here**: the pawn on e2 can't move to e5.\nNothing was played.",
                      outcome.comment)


class Endings(unittest.TestCase):
    def test_a_checkmate_for_github_puts_its_player_in_the_hall_of_fame(self):
        table = Table()
        outcome = table.play(FOOLS_MATE)
        self.assertIn("🏆 **2... Qh4#: checkmate!** GitHub wins game 1, and @octocat takes a place in the [Hall of Fame]"
                      "(https://github.com/tannergolden) for the winning move.\n", outcome.comment)
        self.assertRegex(outcome.comment, r"\n\S+ \*[^*]+!\* · Queen from d8 to h4, checkmate\n")
        self.assertIn("Game 2 starts now, and @tannergolden opens it as White.", outcome.comment)
        record = table.hall[-1]
        self.assertEqual((record["game"], record["result"], record["reason"], record["winner"], record["plies"]),
                         (1, "0-1", "checkmate", "GitHub", 4))
        self.assertEqual(record["deciding"], {"move": "2... Qh4#", "player": OCTOCAT, "player_id": OCTOCAT_ID,
                                              "arbiter": False, "issue": 104})
        self.assertEqual(record["players"], [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 2}])
        self.assertEqual(table.game, {"game": 2, "started": record["ended"], "fen": rules.START, "moves": []})
        self.assertEqual(outcome.pgn[0], "game-1.pgn")
        self.assertTrue(outcome.commit.startswith("chore(chess): 🏆 play 2... Qh4#, ending game 1 0-1"))

    def test_a_checkmate_for_the_owner_says_so(self):
        outcome = Table().play(SCHOLARS_MATE)
        self.assertIn("🏆 **4. Qxf7#: checkmate!** @tannergolden wins game 1.\n", outcome.comment)
        self.assertTrue(outcome.comment.endswith("\nGame 2 starts now, and @tannergolden opens it as White.\n"))

    def test_a_stalemate_is_drawn_and_the_next_game_starts(self):
        table = Table()
        outcome = table.play(LOYDS_STALEMATE)
        self.assertIn("🤝 **10. Qe6: game 1 is drawn by stalemate.**\n", outcome.comment)
        self.assertIn("· Queen from c8 to e6, stalemate\nGame 2 starts now", outcome.comment)
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
        self.assertIn("⏰ **A week passed without a move from GitHub**, so the Arbiter played 1... ", outcome.comment)
        self.assertTrue(outcome.comment.endswith("\n@tannergolden, it's your move.\n"))
        self.assertIn("after a week without a move\n\nMove 2 of game 1, by the Arbiter.", outcome.commit)

    def test_after_a_week_the_arbiter_moves_for_the_owner_and_tells_github(self):
        table = Table()
        table.move("e2e4")
        table.move("c7c5")
        outcome = table.wait(dt.timedelta(days=8))
        self.assertEqual(outcome.issue, 102)  # the last move GitHub played
        self.assertIn(f"⏰ **A week passed without a move from {LINKED}**, so the Arbiter played 2. ", outcome.comment)
        self.assertRegex(outcome.comment, r"for White, at random\.\n\S+ \*[^*]+!\* · [^\n]+\nGitHub's turn")
        self.assertIsNone(PING.search(outcome.comment), "the owner's own lapse goes to GitHub's player, unpinged")

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

    def test_an_opening_left_a_week_is_told_on_the_move_that_ended_the_last_game(self):
        table = Table()
        table.play(FOOLS_MATE)
        outcome = table.wait(dt.timedelta(days=7))
        self.assertTrue(outcome.changed)
        self.assertEqual((table.game["game"], len(table.game["moves"])), (2, 1))
        self.assertEqual(outcome.issue, 104, "the issue of the mate that ended game 1")
        self.assertIn(f"without a move from {LINKED}**, so the Arbiter played 1. ", outcome.comment)

    def test_a_check_is_announced_and_the_side_in_it_told(self):
        table = Table()
        table.play(["e2e4", "f7f6"])
        outcome = table.move("d1h5")
        self.assertIn("♟️ **2. Qh5+ is on the board. Check!**\n", outcome.comment)
        self.assertIn("GitHub's turn, in check: anyone but [@tannergolden]", outcome.comment)
        self.assertIn("can pick Black's way out on [the board]", outcome.comment)
        table = Table()
        table.play(["f2f3", "e7e5"])
        outcome = table.move("e1f2")
        outcome = table.move("d8h4")
        self.assertIn("♟️ **2... Qh4+ is on the board. Check!** Well played, @octocat.\n", outcome.comment)
        self.assertIn("@tannergolden, it's your move, and you are in check.", outcome.comment)

    def test_a_turned_away_move_pings_nobody(self):
        table = Table()
        table.play(["e2e4", "c7c5"])
        refusals = [table.move("d2d4", player=OCTOCAT), table.move("e7e5", player=OWNER, move=3),
                    table.move("d2d4", move=1), table.move("d2d4", move=9), table.move("d2d4", game=4),
                    table.move("e2e5"), table.move("e3e4"), table.move("e7e6")]
        for outcome in refusals:
            self.assertFalse(outcome.changed, outcome.comment)
            self.assertIsNone(PING.search(outcome.comment), outcome.comment)


class Notices(unittest.TestCase):
    """The Arbiter tells a player once, on the issue of the move it answers; a move after another of its own goes in
    the owner's logbook, so no player's issue collects a notice a week, and none is lost."""

    def test_a_player_is_told_once_and_the_owner_s_logbook_takes_the_rest(self):
        table = Table()
        table.move("e2e4")
        table.move("e7e5")
        mine = table.issue
        first = table.wait(chess.WEEK)  # the owner's lapse, answered on GitHub's player's issue
        self.assertEqual((first.issue, first.logbook), (mine, False))
        second = table.wait(chess.WEEK)  # GitHub's lapse: the Arbiter answers itself, so into the logbook
        self.assertEqual((second.issue, second.logbook), (None, True))
        self.assertTrue(second.comment.endswith("\n@tannergolden, it's your move.\n"), "the owner is pinged there")
        third = table.wait(chess.WEEK)
        self.assertEqual((third.issue, third.logbook), (None, True))
        self.assertIsNone(PING.search(third.comment), "GitHub's turn pings nobody, even in the logbook")

    def test_a_game_the_arbiter_ended_opens_the_next_in_the_logbook(self):
        table = Table()
        table.play(FOOLS_MATE[:-1])
        arbiter = {"player": None, "player_id": None, "issue": None, "arbiter": True}
        positions = chess.replay(table.game)
        mate = next(move for move in rules.legal_moves(positions[-1]) if move.uci == FOOLS_MATE[-1])
        outcome, _, _ = chess.apply(table.game, table.hall, positions, mate, arbiter, OWNER, table.clock)
        table.game, table.hall = outcome.game, outcome.hall
        opening = table.wait(chess.WEEK)
        self.assertEqual((opening.issue, opening.logbook), (None, True), "the move before it was the Arbiter's own")

    def test_a_game_a_player_ended_opens_the_next_on_their_issue(self):
        table = Table()
        table.play(FOOLS_MATE)
        opening = table.wait(chess.WEEK)
        self.assertEqual((opening.issue, opening.logbook), (table.hall[-1]["deciding"]["issue"], False))


class Board(unittest.TestCase):
    """What the page's chess elements are given, after each turn of a game."""

    def entries(self, element: dict) -> list:
        return [entry for group in element["moves"] for entry in group["list"]]

    def test_a_game_nobody_has_opened_waits_for_the_owner(self):
        element = chess.board(None, [], OWNER)
        self.assertEqual((element["fen"], element["game"], element["move"], element["players"]), (rules.START, 1, 1, 0))
        self.assertEqual(element["prompt"],
                         "🛑 **@tannergolden's turn!** @tannergolden opens game 1 as White, and GitHub plays Black.")
        self.assertNotIn("last", element)
        self.assertNotIn("due", element, "the clock starts with the first move")
        self.assertEqual(element["history"], [[1, "", "", ""]])
        self.assertEqual(len(self.entries(element)), 20)
        self.assertEqual([group["piece"] for group in element["moves"]], ["knight", "pawn"])
        self.assertNotIn("PGN", element["note"])

    def test_every_move_is_named_and_links_to_its_own_ready_made_issue(self):
        table = Table()
        table.move("e2e4")
        element = chess.board(table.game, table.hall, OWNER)
        entries = self.entries(element)
        for emoji, title, name, words, url in entries:
            self.assertRegex(emoji, KIT_EMOJI)
            self.assertRegex(title, KIT_TITLE)
            self.assertRegex(name, KIT_SAN)
            self.assertRegex(words, KIT_WORDS)
            self.assertRegex(url, KIT_LINK)
            issue = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["title"][0]
            self.assertRegex(issue, r"^chess: [a-h][1-8][a-h][1-8][qrbn]? \u00b7 game 1 \u00b7 move 2$")
        self.assertEqual(len({entry[1] for entry in entries}), len(entries), "no two moves on a board share a title")
        e5 = next(entry for entry in entries if entry[2] == "e5")
        self.assertEqual((e5[3], e5[4]), ("Pawn from e7 to e5, two squares", chess.link(OWNER, "e7e5", 1, 2)))
        self.assertEqual(chess.board(table.game, table.hall, OWNER), element, "the same board, the same names")

    def test_the_last_move_the_turn_and_the_score_sheet(self):
        table = Table()
        table.move("e2e4")  # at 17:00 UTC, so GitHub has until noon EST a week on
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["last"], {"san": "e4", "from": "e2", "to": "e4", "piece": "pawn", "captured": "",
                                           "words": "Pawn from e2 to e4, two squares", "by": "@tannergolden",
                                           "when": "11 Oct"})
        self.assertEqual(element["due"], "18 Oct")
        self.assertEqual(element["prompt"],
                         "🟢 **GitHub's turn!** @tannergolden played 1. e4. Pick a move below by 18 Oct.")
        self.assertIn("The move is due by 18 Oct, 12:00 EST, or the Arbiter plays a random legal move.",
                      element["note"])
        self.assertEqual(element["history"], [[1, "e4", "", ""]])
        table.move("c7c5")
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["history"], [[1, "e4", "c5", "@octocat"], [2, "", "", ""]])
        self.assertEqual(element["prompt"], "🛑 **@tannergolden's turn!** GitHub played 1... c5. Reply due by 18 Oct.")
        self.assertIn("The move is due by 18 Oct, 13:00 EST", element["note"])
        self.assertEqual((element["players"], element["move"]), (1, 2))

    def test_a_check_marks_the_king_and_the_arbiter_is_named(self):
        table = Table()
        table.play(["e2e4", "f7f6", "d2d4"])
        table.wait(dt.timedelta(days=7))
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["last"]["by"], "the Arbiter")
        self.assertIn("The Arbiter played", element["prompt"])
        table = Table()
        table.play(["e2e4", "f7f6", "d1h5"])
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["check"], "e8")
        self.assertIn("played 2. Qh5+. Check! Pick a move below by", element["prompt"])

    def test_what_each_side_took_is_counted_from_the_game(self):
        table = Table()
        table.play(["e2e4", "d7d5", "e4d5", "g8f6", "d5d6", "e7e5", "d6c7", "d8c7"])
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["taken"], {"white": "pp", "black": "p"})
        self.assertEqual(element["last"]["captured"], "pawn")
        table = Table()
        table.play(["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"])  # en passant
        self.assertEqual(chess.board(table.game, table.hall, OWNER)["taken"], {"white": "p", "black": ""})

    def test_the_hall_of_fame_ranks_whoever_mated(self):
        table = Table()
        table.play(FOOLS_MATE)
        table.play(LOYDS_STALEMATE)
        table.play(SCHOLARS_MATE)
        hall = chess.hall_element(table.hall, OWNER)
        self.assertEqual({k: hall[k] for k in ("games", "house", "world", "draws")},
                         {"games": 3, "house": 1, "world": 1, "draws": 1})
        self.assertEqual(hall["people"], [["tannergolden", 1, "12 Oct", 3], ["octocat", 1, "11 Oct", 3, OCTOCAT_ID]],
                         "the newest win first; @octocat played Black in all three games")
        self.assertEqual(chess.hall_element(table.hall, OWNER, owner_id=OWNER_ID)["people"][0],
                         ["tannergolden", 1, "12 Oct", 3, OWNER_ID], "each row ends with the account's ID")
        self.assertEqual(hall["measure"], {}, "the kit reads each winner's name from their profile")
        element = chess.board(table.game, table.hall, OWNER)
        self.assertEqual(element["prompt"],
                         "🛑 **@tannergolden's turn!** @tannergolden won game 3. Game 4 opens by 19 Oct.")
        self.assertIn("[PGN](https://github.com/tannergolden/tannergolden/tree/HEAD/.github/chess/games)",
                      element["note"])

    def test_a_new_game_s_banner_says_how_the_last_one_ended(self):
        table = Table()
        table.play(FOOLS_MATE)
        element = chess.board(table.game, table.hall, OWNER)
        self.assertRegex(element["prompt"],
                         r"^🛑 \*\*@tannergolden's turn!\*\* GitHub won game 1\. Game 2 opens by \d+ Oct\.$")
        table.play(LOYDS_STALEMATE)
        element = chess.board(table.game, table.hall, OWNER)
        self.assertRegex(element["prompt"],
                         r"^🛑 \*\*@tannergolden's turn!\*\* Game 2 was drawn\. Game 3 opens by \d+ Oct\.$")
        self.assertTrue(element["note"].startswith("Game 2 was drawn by stalemate. Only @tannergolden can play"))

    def test_every_banner_fits_one_line_of_the_readme(self):
        """The longest banner each turn can have, at game 123 and move 123, fits the line (`BANNER`); and every note,
        the longest draw's too, fits the kit's 400 characters."""
        late = ("123. Qh4xe1+", "123... Qh4xe1+")
        banners = [chess.prompt(OWNER, False, 123, late[0], arbiter, check, "28 Sep")
                   for arbiter in (False, True) for check in (False, True)]
        banners += [chess.prompt(OWNER, True, 123, late[1], arbiter, check, "28 Sep")
                    for arbiter in (False, True) for check in (False, True)]
        banners += [chess.prompt(OWNER, True, 124, result=result, due="28 Sep")
                    for result in ("GitHub won game 123", "@tannergolden won game 123", "Game 123 was drawn")]
        banners.append(chess.prompt(OWNER, True, 1))
        for line in banners:
            self.assertLessEqual(len(line), chess.BANNER, line)
        wrapped = ("🛑 **@tannergolden's turn!** @tannergolden opens game 1 as White, and GitHub plays Black from the"
                   " next move on.")
        self.assertGreater(len(wrapped), chess.BANNER, "the banner that wrapped would not pass")
        ended = {"game": 123, "result": "1/2-1/2", "reason": "seventy-five-move rule", "winner": None}
        element = chess.board(chess.new_game(124, T0), [ended], OWNER)
        self.assertTrue(KIT_LINE.fullmatch(element["note"]) and not KIT_BLOCK.match(element["note"]),
                        element["note"])
        self.assertLessEqual(len(element["prompt"]), chess.BANNER)

    def test_the_leaderboard_puts_the_owner_on_top_and_counts_the_game_on_the_board(self):
        table = Table()
        self.assertEqual(chess.hall_element([], OWNER)["leaders"], [[OWNER, 0, 0, 0]], "the owner's row from the start")
        self.assertEqual(chess.hall_element([], OWNER, chess.new_game(1, T0))["leaders"], [[OWNER, 0, 0, 0]])
        table.play(FOOLS_MATE)  # the owner plays f3 and g4; @octocat plays both of Black's moves and mates
        table.move("e2e4")
        table.move("e7e5", player=HUBOT, player_id=HUBOT_ID)
        table.move("d2d4")
        table.move("d7d6", player=HUBOT, player_id=HUBOT_ID)
        hall = chess.hall_element(table.hall, OWNER, table.game)
        self.assertEqual(hall["leaders"],
                         [[OWNER, 4, 0, 2], ["octocat", 2, 1, 1, OCTOCAT_ID], ["hubot", 2, 0, 1, HUBOT_ID]],
                         "the owner on top, then wins first and moves next, with the game on the board as it goes")
        self.assertEqual(chess.hall_element(table.hall, OWNER)["leaders"],
                         [[OWNER, 2, 0, 1], ["octocat", 2, 1, 1, OCTOCAT_ID]])
        self.assertEqual(chess.hall_element(table.hall, OWNER, owner_id=OWNER_ID)["leaders"][0],
                         [OWNER, 2, 0, 1, OWNER_ID], "each row ends with its account's ID, the owner's too")

    def test_the_owner_s_own_mate_is_their_win_and_ten_of_github_follow(self):
        table = Table()
        table.play(SCHOLARS_MATE)  # the owner mates with their fourth move; @octocat played Black's three
        self.assertEqual(chess.hall_element(table.hall, OWNER)["leaders"],
                         [[OWNER, 4, 1, 1], ["octocat", 3, 0, 1, OCTOCAT_ID]])
        crowd = dict(table.hall[0], players=[{"player": f"p{i:02}", "player_id": 1000 + i, "moves": i}
                                             for i in range(1, 13)])
        leaders = chess.hall_element([crowd], OWNER)["leaders"]
        self.assertEqual([row[0] for row in leaders], [OWNER, *(f"p{i:02}" for i in range(12, 2, -1))])

    def test_a_move_or_a_mate_the_arbiter_played_counts_for_nobody_on_either_side(self):
        arbiter = {"player": None, "player_id": None, "issue": None, "arbiter": True}
        table = Table()
        for moves in (FOOLS_MATE, SCHOLARS_MATE):  # the Arbiter plays the mate: for GitHub, then for the owner
            table.play(moves[:-1])
            positions = chess.replay(table.game)
            mate = next(move for move in rules.legal_moves(positions[-1]) if move.uci == moves[-1])
            outcome, _, end = chess.apply(table.game, table.hall, positions, mate, arbiter, OWNER, table.clock)
            self.assertEqual(end.reason, "checkmate")
            table.game, table.hall = outcome.game, outcome.hall
        table.move("e2e4")
        table.wait(chess.WEEK)  # the Arbiter plays for GitHub
        table.wait(chess.WEEK)  # and for the owner
        self.assertEqual(sum(1 for played in table.game["moves"] if played["arbiter"]), 2)
        hall = chess.hall_element(table.hall, OWNER, table.game)
        self.assertEqual(hall["leaders"], [[OWNER, 2 + 3 + 1, 0, 3], ["octocat", 1 + 3, 0, 2, OCTOCAT_ID]])
        self.assertEqual(hall["people"], [], "and nobody is on the podium")

    def test_the_hall_names_a_player_by_the_newest_login_they_played_as(self):
        table = Table()
        table.play(FOOLS_MATE)  # @octocat mates
        table.move("e2e4")
        table.move("e7e5", player="octocat-renamed")
        hall = chess.hall_element(table.hall, OWNER, table.game)
        self.assertEqual(hall["leaders"], [[OWNER, 3, 0, 2], ["octocat-renamed", 3, 1, 2, OCTOCAT_ID]])
        self.assertEqual(hall["people"], [["octocat-renamed", 1, "11 Oct", 1, OCTOCAT_ID]],
                         "the podium names a winner by the newest login they played as, too")

    def test_a_mate_the_arbiter_played_scores_nobody(self):
        table = Table()
        table.play(FOOLS_MATE)
        record = table.hall[0]
        by_the_clock = {**record, "deciding": {**record["deciding"], "player": None, "player_id": None, "arbiter": True}}
        hall = chess.hall_element([by_the_clock], OWNER)
        self.assertEqual((hall["world"], hall["people"]), (1, []), "GitHub wins the game, and nobody the point")

    def test_the_banner_stays_one_line_however_long_the_move_number(self):
        for digits in range(1, 6):  # up to move 99,999, the furthest the page draws
            n = int("9" * digits)
            for white in (False, True):
                for arbiter in (False, True):
                    for check in (False, True):
                        shown = f"{n}... exd8=Q+" if white else f"{n}. exd8=Q+"
                        banner = chess.prompt(OWNER, white, 123, shown, arbiter, check, "28 Sep")
                        with self.subTest(digits=digits, white=white, arbiter=arbiter, check=check):
                            self.assertLessEqual(len(banner), chess.BANNER, banner)
        self.assertTrue(chess.prompt(OWNER, False, 1, "1. e4", due="18 Oct").endswith("Pick a move below by 18 Oct."),
                        "the full wording whenever it fits")

    def test_a_dead_position_is_named_wherever_a_draw_is(self):
        end = rules.Ending("dead position", None)
        mover = {"player": OCTOCAT, "player_id": OCTOCAT_ID, "issue": 7, "arbiter": False}
        self.assertIn("game 3 is drawn by a dead position.", chess.ended_text(end, "40. g4", 3, mover, OWNER, "name"))
        table = Table()
        table.play(FOOLS_MATE)
        table.hall[-1].update(reason="dead position", winner=None, result="1/2-1/2")
        self.assertTrue(chess.board(table.game, table.hall, OWNER)["note"].startswith(
            "Game 1 was drawn by a dead position."))

    def test_what_the_readme_carries_is_text_the_kit_accepts(self):
        for moves in ([], ["e2e4"], ["e2e4", "c7c5"], FOOLS_MATE):
            table = Table()
            table.play(moves) if moves else None
            element = chess.board(table.game, table.hall, OWNER)
            for key in ("prompt", "note"):
                self.assertTrue(KIT_LINE.fullmatch(element[key]) and not KIT_BLOCK.match(element[key]), element[key])
                self.assertNotIn("![", element[key])
                for dash in DASHES:
                    self.assertNotIn(dash, element[key])
            for row in element["history"]:
                self.assertTrue(row[3] == "" or KIT_WHO.fullmatch(row[3]), row)
            if "last" in element:
                self.assertRegex(element["last"]["by"], KIT_WHO)
                self.assertRegex(element["last"]["when"], KIT_DAY)
                self.assertRegex(element["last"]["words"], KIT_WORDS)
            for row in chess.hall_element(table.hall, OWNER)["people"]:
                self.assertRegex(row[2], KIT_DAY)

    def test_a_reply_names_the_move_as_the_board_listed_it(self):
        table = Table()
        listed = {entry[2]: entry for entry in self.entries(chess.board(None, [], OWNER))}
        outcome = table.move("g1f3")
        emoji, title = listed["Nf3"][0], listed["Nf3"][1]
        self.assertIn(f"**1. Nf3 is on the board.**\n{emoji} *{title}* · Knight from g1 to f3\n", outcome.comment)


class EveryMove(unittest.TestCase):
    """Every legal move on the board, of every piece and in every kind of position, is listed once, behind a link
    the intake takes for that move, game and move number, and is played when its issue comes back."""

    def test_every_legal_move_is_listed_once_and_its_link_plays_it(self):
        kinds = set()
        for label, line in SPECIAL.items():
            table = Table()
            for ply, uci in enumerate(line.split(), 1):
                position = chess.replay(table.game)[-1] if table.game else rules.Position.from_fen(rules.START)
                legal = {move.uci: move for move in rules.legal_moves(position)}
                element = chess.board(table.game, table.hall, OWNER)
                entries = [entry for group in element["moves"] for entry in group["list"]]
                titles = [urllib.parse.parse_qs(urllib.parse.urlparse(entry[4]).query)["title"][0] for entry in entries]
                links = [INTAKE.fullmatch(title) for title in titles]
                self.assertTrue(all(links), (label, ply, titles))
                self.assertEqual(sorted(link["uci"] for link in links), sorted(legal), (label, ply))
                self.assertEqual({(link["game"], link["move"]) for link in links}, {(str(element["game"]), str(ply))})
                for entry in entries:
                    self.assertTrue(KIT_EMOJI.fullmatch(entry[0]) and KIT_TITLE.fullmatch(entry[1])
                                    and KIT_SAN.fullmatch(entry[2]) and KIT_WORDS.fullmatch(entry[3])
                                    and KIT_LINK.fullmatch(entry[4]), (label, ply, entry))
                found = {link["uci"]: self.kind(position, legal[link["uci"]]) for link in links}
                kinds |= set(found.values())
                # every link is played back, wherever a castle, an en passant or a promotion is on the board
                if ply == 1 or set(found.values()) - {"move", "capture"}:
                    player = (OWNER, OWNER_ID) if position.turn == "w" else (OCTOCAT, OCTOCAT_ID)
                    for each in found:
                        outcome = chess.play(table.game, table.hall, request(each, ply, element["game"], 7, *player),
                                             OWNER, OWNER_ID, table.clock)
                        self.assertTrue(outcome.changed, (label, ply, each, outcome.comment))
                self.assertTrue(table.move(uci).changed, (label, ply, uci))
        self.assertEqual(kinds, {"castle", "en passant", "promotion", "capture", "move"})

    @staticmethod
    def kind(position, move) -> str:
        piece = position.board[move.start].lower()
        if piece == "k" and abs(move.end - move.start) == 2:
            return "castle"
        if piece == "p" and move.end == position.ep:
            return "en passant"
        return "promotion" if move.promotion else "capture" if position.board[move.end] else "move"

    def test_a_link_reaches_any_game_and_move_the_rules_allow(self):
        # A game can run past 17,000 moves before the seventy-five-move rule and fivefold repetition end it.
        for game, ply in ((1, 1), (1, 999), (1, 1000), (10000, 17697), (999999999, 999999999)):
            url = chess.link(OWNER, "e7e8q", game, ply)
            title = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["title"][0]
            link = INTAKE.fullmatch(title)
            self.assertTrue(link and KIT_LINK.fullmatch(url), (game, ply))
            self.assertEqual((link["game"], link["move"]), (str(game), str(ply)))


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
        settings = folder.parent / "markdown.yaml"
        if not settings.exists():
            settings.write_text(SETTINGS, encoding="utf-8")
        env = {"OWNER": OWNER, "OWNER_ID": str(OWNER_ID), "GITHUB_OUTPUT": str(output),
               "RUN_URL": "https://github.com/tannergolden/tannergolden/actions/runs/1", **values}
        with contextlib.redirect_stdout(io.StringIO()):  # the run's log line
            code = chess.main([str(folder), "--out", str(out), "--now", now, "--settings", str(settings)], env)
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
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=true\nissue=12\nlogbook=false\n")

    def test_a_turned_away_move_saves_nothing_and_still_replies(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            self.run_script(folder, "2026-10-11T15:00:00Z")  # the clock, which sets the opening board out
            (Path(temp) / "output.txt").unlink()
            code, out = self.run_script(folder, "2026-10-11T16:00:00Z", UCI="e7e5", GAME="1", MOVE_NUMBER="1",
                                        ISSUE="13", PLAYER=OCTOCAT, PLAYER_ID=str(OCTOCAT_ID))
            self.assertEqual(code, 0)
            self.assertFalse(folder.exists())
            self.assertIn(f"It's {LINKED}'s turn", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=false\nissue=13\nlogbook=false\n")

    def test_every_run_sets_the_board_out_between_its_markers_and_nowhere_else(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            code, out = self.run_script(folder, "2026-10-11T16:00:00Z")
            self.assertEqual(code, 0)
            text = (Path(temp) / "markdown.yaml").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("elements:\n  # chess:start\n  chess:\n    kind: \"chess\"\n"))
            self.assertIn("\n  chess-hall:\n    kind: \"chess-hall\"\n    games: 0\n", text)
            self.assertTrue(text.endswith("  # chess:end\n  other:\n    kind: placard\n"))
            self.assertEqual((out / "commit.txt").read_text(encoding="utf-8").splitlines()[0],
                             "chore(chess): 🖌️ set the board out for the page")
            self.assertIn("changed=true", (Path(temp) / "output.txt").read_text(encoding="utf-8"))
            (Path(temp) / "output.txt").unlink()
            self.run_script(folder, "2026-10-11T17:00:00Z")
            self.assertIn("changed=false", (Path(temp) / "output.txt").read_text(encoding="utf-8"))

    def test_settings_without_the_markers_stop_the_run(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "markdown.yaml").write_text("elements:\n", encoding="utf-8")
            code, _ = self.run_script(Path(temp) / "chess", "2026-10-11T16:00:00Z")
            self.assertEqual(code, 1)

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

    def test_a_notice_for_the_owner_s_logbook_says_so_in_the_step_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            self.run_script(folder, "2026-10-01T09:00:00Z", UCI="d2d4", GAME="1", MOVE_NUMBER="1", ISSUE="5",
                            PLAYER=OWNER, PLAYER_ID=str(OWNER_ID))
            self.run_script(folder, "2026-10-08T09:00:00Z")  # told on the owner's issue 5
            self.run_script(folder, "2026-10-15T09:00:00Z")  # the Arbiter after itself: the logbook
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8").splitlines()[-6:],
                             ["changed=true", "issue=5", "logbook=false", "changed=true", "issue=", "logbook=true"])

    def test_anything_malformed_is_turned_away_on_its_issue_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "chess"
            good = {"UCI": "e2e4", "GAME": "1", "MOVE_NUMBER": "1", "ISSUE": "1", "PLAYER": OWNER,
                    "PLAYER_ID": str(OWNER_ID)}
            for name, bad in (("UCI", "e2e9"), ("UCI", "e2e4; rm -rf"), ("GAME", "0"), ("MOVE_NUMBER", "x"),
                              ("GAME", "1234567890"), ("PLAYER", "bad name"), ("PLAYER", "x[bot]"),
                              ("PLAYER_ID", "12a"), ("PLAYER_ID", "12345678901234567")):
                with self.subTest(name=name, bad=bad):
                    code, out = self.run_script(folder, "2026-10-11T16:00:00Z", **{**good, name: bad})
                    self.assertEqual(code, 0)
                    reply = (out / "comment.md").read_text(encoding="utf-8")
                    self.assertTrue(reply.startswith(
                        "🚫 **This move can't be played as sent**, so nothing was played."))
                    self.assertIsNone(PING.search(reply), "a turned-away request pings nobody")
                    self.assertIn("issue=1\n", (Path(temp) / "output.txt").read_text(encoding="utf-8"))
            self.assertFalse(folder.exists())
            for bad in ("-1", "0", "12345678901234567", "x"):  # nowhere to say so: the run stops
                with self.subTest(issue=bad):
                    code, _ = self.run_script(folder, "2026-10-11T16:00:00Z", **{**good, "UCI": "e2e9", "ISSUE": bad})
                    self.assertEqual(code, 1)
            code, _ = self.run_script(folder, "2026-10-11T16:00:00Z", **{**good, "ISSUE": "1234567890123456",
                                                                          "PLAYER_ID": "1234567890123456"})
            self.assertEqual(code, 0, "issues and accounts run to 16 digits, as the intake passes them on")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(chess.main([str(folder), "--now", "2026-10-11T16:00:00Z"], {"OWNER": OWNER}), 1)

    def test_a_game_with_an_impossible_move_is_never_replayed_quietly(self):
        with self.assertRaises(ValueError):
            chess.replay({"game": 1, "started": "2026-10-11T16:00:00Z", "moves": [{"uci": "e2e5"}]})


if __name__ == "__main__":
    unittest.main()
