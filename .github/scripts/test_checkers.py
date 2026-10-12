# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Checkers on the profile, played offline through the shared engine, as the workflow plays it: every way a move goes.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

GitHub plays Black and opens every game, as American checkers has Black move
first, and the house plays White. Whole games are drawn from seeded random
play over the rules' own legal moves, one for each way a game ends, and
played through the engine move by move, from made-up players for GitHub and
from the owner for the house, at times the test sets.
"""
from __future__ import annotations

import datetime as dt
import random
import re
import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checkers_rules as R
import games
import page
from page import GITHUB, HOUSE

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
T0 = page.parse("2026-10-12T16:00:00Z")
HOUR = dt.timedelta(hours=1)
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
PING = re.compile(r"(?<![\[\w])@[A-Za-z0-9][A-Za-z0-9-]*")
LINKED = "[@tannergolden](https://github.com/tannergolden)"
BOARD = "[the board](https://github.com/tannergolden)"
SQ = r"(?:3[0-2]|[12][0-9]|[1-9])"
# What tannergolden/markdown's checkers kind accepts (src/domain/elements/checkers/game.py), and what
# tannergolden/play's intake takes as a move's issue title.
_LIST = r"(?:K?(?:3[0-2]|[12]?[0-9])(?:,K?(?:3[0-2]|[12]?[0-9]))*)?"
KIT_FEN = re.compile(rf"[BW]:W{_LIST}:B{_LIST}")
KIT_MOVE = re.compile(rf"{SQ}(?:-{SQ}|(?:x{SQ})+)")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_WHO = re.compile(r"@[A-Za-z0-9][A-Za-z0-9-]{0,38}|the Arbiter")
KIT_DAY = re.compile(r"(?:[1-9]|[12][0-9]|3[01]) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
KIT_LINE = re.compile(r"[^<>|\n\r]{1,400}")
KIT_BLOCK = re.compile(r"\s|```|~~~|#{1,6}(?:\s|$)|>|[-*+](?:\s|$)|[0-9]+[.)](?:\s|$)|\[[^\]]*\]:|[-=*_\s]+$")
INTAKE = re.compile(rf"checkers: (?P<move>{SQ}(?:-{SQ}|(?:x{SQ})+)) · game (?P<game>[1-9][0-9]{{0,8}})"
                    rf" · move (?P<ply>[1-9][0-9]{{0,8}})")


def line(seed: int) -> list[str]:
    """A whole game of seeded random play, as its moves' codes."""
    rng, positions, moves = random.Random(seed), [R.START], []
    while not R.ending(positions, moves):
        move = rng.choice(R.legal_moves(positions[-1]))
        moves.append(move)
        positions.append(R.make(positions[-1], move))
    return [move.code for move in moves]


DARK_WINS, LIGHT_WINS, REPEATED, FORTY = line(1988), line(1805), line(1989), line(649)  # Black's win, White's, draws
SIDE_WORDS = re.compile(r"\b(?:[Dd]ark|[Ll]ight)\b")  # the old side words, which nothing a reader sees says now


class Table:
    """A game of checkers at the profile: the state between moves, and every reply so far."""

    def __init__(self):
        self.mod = games.rules("checkers")
        self.game, self.hall, self.outcomes, self.texts, self.issue, self.clock = None, [], [], [], 100, T0

    def current(self) -> dict:
        return self.game or {"game": 1, "started": page.stamp(self.clock), "moves": []}

    def move(self, code: str, player: str | None = None, player_id: int | None = None, move: int | None = None,
             game: int | None = None, after: dt.timedelta = HOUR) -> games.Outcome:
        current = self.current()
        side = games.side_of(self.mod, current, len(current["moves"]) + 1)
        player = player or (OWNER if side == HOUSE else OCTOCAT)
        player_id = player_id or (OWNER_ID if player == OWNER else OCTOCAT_ID)
        self.clock += after
        self.issue += 1
        request = games.Request(code, game or current["game"], move or len(current["moves"]) + 1, self.issue,
                                player, player_id)
        return self.keep(games.play(self.mod, self.game, self.hall, request, OWNER, OWNER_ID, self.clock))

    def wait(self, span: dt.timedelta) -> games.Outcome:
        self.clock += span
        return self.keep(games.tick(self.mod, self.game, self.hall, OWNER, self.clock))

    def keep(self, outcome: games.Outcome) -> games.Outcome:
        if outcome.changed:
            self.game, self.hall = outcome.game, outcome.hall
        self.outcomes.append(outcome)
        self.texts += [outcome.comment, outcome.commit]
        return outcome

    def play(self, codes: list[str]) -> games.Outcome:
        outcome = None
        for code in codes:
            outcome = self.move(code)
            assert outcome.changed, f"{code}: {outcome.comment}"
        return outcome

    def board(self) -> dict:
        return games.board(self.mod, self.game, self.hall, OWNER, self.clock)


def first_jump(codes: list[str]) -> int:
    """How many moves of the line come before the first position where a jump must be taken."""
    position = R.START
    for index, code in enumerate(codes):
        if R.must_jump(position):
            return index
        position = R.make(position, R.find(position, code))
    raise AssertionError("the line never forces a jump")


class Opening(unittest.TestCase):
    """American checkers: Black moves first, and GitHub plays Black, so GitHub opens every game; the house plays
    White. The first game starts on the first run that reaches it, and its week counts from then."""

    def test_the_first_run_starts_game_1_with_github_to_open_as_black(self):
        mod = games.rules("checkers")
        started = games.tick(mod, None, [], OWNER, T0)
        self.assertTrue(started.changed, "its start is written")
        self.assertEqual(started.game, {"game": 1, "started": page.stamp(T0), "moves": []})
        self.assertEqual((started.comment, started.issue, started.logbook), ("", None, False))
        self.assertEqual(started.commit, "chore(checkers): 🏁 start game 1, GitHub to open as Black\n\nGitHub opens"
                                         " every game of Checkers as Black, and the week for the first\nmove of game 1"
                                         " counts from now.")
        self.assertEqual(started.log, f"game 1 started, GitHub to open; the side to move has until"
                                      f" {page.stamp(T0 + page.WEEK)}")
        self.assertFalse(games.tick(mod, started.game, [], OWNER, T0 + HOUR).changed, "and only once")
        element = games.board(mod, started.game, [], OWNER, T0 + HOUR)
        due = page.day(T0 + page.WEEK)
        self.assertEqual((element["game"], element["fen"], element["kings"], element["due"]),
                         (1, R.START.fen, {HOUSE: 0, GITHUB: 0}, due))
        self.assertNotIn("dark", element)
        self.assertEqual([entry[2] for entry in element["moves"]],
                         ["9-13", "9-14", "10-14", "10-15", "11-15", "11-16", "12-16"])
        self.assertTrue(element["note"].startswith(
            "GitHub plays Black, which moves first in American checkers, so GitHub opens every game, and @tannergolden"
            " plays White. Anyone but @tannergolden can play on this turn, and the first pick in is played."))
        self.assertIn(f"The move is due by {page.until(T0 + page.WEEK)}, or the Arbiter plays a random legal move.",
                      element["note"])

    def test_a_board_drawn_before_any_run_reached_the_game_is_github_s_turn_too(self):
        element = games.board(games.rules("checkers"), None, [], OWNER, T0)
        self.assertEqual((element["game"], element["fen"], element["due"]), (1, R.START.fen, page.day(T0 + page.WEEK)))
        self.assertIn(games.who_plays(GITHUB, OWNER), element["note"])

    def test_the_owner_cannot_open_for_github_and_nobody_else_can_reply_for_the_house(self):
        table = Table()
        outcome = table.move("11-15", player=OWNER)
        self.assertTrue(outcome.changed, "the first run to reach the game writes its start, whatever it brings")
        self.assertEqual(outcome.game["moves"], [])
        self.assertEqual(outcome.comment, "⏳ **It's GitHub's turn as Black**, so `11-15` wasn't played.\nBlack's moves"
                                          " are for everyone but you. Your turn comes next.\n")
        opened = table.move("11-15")
        self.assertRegex(opened.comment, r"^⛂ \*\*1\. 11-15 is on the board\.\*\* Well played, @octocat\.\n\S+"
                                         r" \*[^*]+!\* · Man from 11 to 15\n@tannergolden, it's your move\.\n$")
        self.assertEqual(opened.commit, "chore(checkers): ⛂ play 1. 11-15 in game 1\n\nMove 1, by octocat.")
        outcome = table.move("23-19", player=OCTOCAT)
        self.assertEqual(outcome.comment, f"⏳ **It's {LINKED}'s turn as White**, so `23-19` wasn't played.\nGitHub"
                                          f" plays Black: once White moves, pick Black's reply on {BOARD}.\n")
        reply = table.move("23-19")
        self.assertRegex(reply.comment, r"^⛀ \*\*1\.\.\. 23-19 is on the board\.\*\*\n\S+ \*[^*]+!\* · Man from 23 to"
                                        r" 19\nGitHub's turn: anyone but \[@tannergolden\]\([^)]+\) can pick Black's"
                                        r" reply on \[the board\]")
        self.assertEqual(reply.commit, "chore(checkers): ⛀ play 1... 23-19 in game 1\n\nMove 2, by tannergolden.")

    def test_github_s_opening_can_start_the_game_itself(self):
        table = Table()
        opened = table.move("11-15")
        self.assertTrue(opened.changed)
        self.assertEqual((opened.game["started"], opened.game["moves"][0]["at"]), (page.stamp(table.clock),) * 2)
        self.assertEqual(opened.commit, "chore(checkers): ⛂ play 1. 11-15 in game 1\n\nMove 1, by octocat. Game 1"
                                        " starts with it.")


class Jumps(unittest.TestCase):
    def test_a_jump_that_must_be_taken_is_called_out_everywhere(self):
        table = Table()
        before = first_jump(DARK_WINS)
        table.play(DARK_WINS[:before])
        element = table.board()
        self.assertEqual(element["alert"], "must jump")
        self.assertTrue(all("x" in entry[2] for entry in element["moves"]), "only the jumps are listed")
        reply = table.outcomes[-1].comment
        self.assertIn(" A jump must be taken!**", reply)
        self.assertRegex(reply, r"(GitHub's turn, with a jump to take: |@tannergolden, it's your move, and a jump"
                                r" must be taken\.)")
        position = games.replay(table.mod, table.game)[-1]
        step = next(f"{a}-{b}" for a in range(1, 33) for b in range(1, 33)
                    if R.why_illegal(position, f"{a}-{b}") and "jump" in R.why_illegal(position, f"{a}-{b}"))
        refused = table.move(step)
        self.assertFalse(refused.changed)
        self.assertEqual(refused.comment, f"🚫 **`{step}` isn't a legal move here**: {R.why_illegal(position, step)}.\n"
                                          f"Nothing was played. Every move listed under {BOARD} is legal: pick one"
                                          " there.\n")

    def test_a_crowned_man_is_marked_and_every_king_made_is_counted(self):
        table = Table()
        positions, kings = [R.START], {HOUSE: 0, GITHUB: 0}
        for index, code in enumerate(DARK_WINS[:-1]):
            move = R.find(positions[-1], code)
            table.move(code)
            positions.append(R.make(positions[-1], move))
            if move.crowns:
                kings[GITHUB if index % 2 == 0 else HOUSE] += 1  # Black's men, GitHub's, move on the even indexes
                element = table.board()
                self.assertEqual(element["last"]["crowned"], True)
                self.assertIn("crowned", element["last"]["words"])
                self.assertEqual(element["kings"], kings)
            else:
                self.assertNotIn("crowned", table.board()["last"])
        self.assertGreater(sum(kings.values()), 0, "the line crowns a man")


class Endings(unittest.TestCase):
    def test_github_wins_when_white_has_no_move_left(self):
        table = Table()
        outcome = table.play(DARK_WINS)
        shown = games.numbered(len(DARK_WINS), DARK_WINS[-1])
        self.assertTrue(outcome.comment.startswith(f"🏆 **{shown}: White has no move left!** GitHub wins game 1, and"
                                                   " @octocat takes a place in the [Hall of Fame]"))
        self.assertIn("and GitHub opens it as Black.\n", outcome.comment)
        self.assertTrue(outcome.commit.startswith(f"chore(checkers): 🏆 play {shown}, ending game 1: Black wins\n"))
        record = table.hall[-1]
        self.assertEqual((record["result"], record["reason"], record["winner"], record["plies"]),
                         ("1-0", "no move left", "GitHub", len(DARK_WINS)), "PDN writes Black's score first")
        self.assertEqual(record["final"], games.replay(table.mod, table.game["ended"])[-1].fen)
        self.assertNotIn("line", record)
        name, text = outcome.record
        self.assertEqual(name, "game-1.pdn")
        for header in ('[Event "@tannergolden vs. GitHub"]', '[Round "1"]', '[Black "GitHub"]',
                       '[White "tannergolden"]', '[Result "1-0"]', '[GameType "21"]'):
            self.assertIn(header, text)
        movetext = " ".join(text.split("\n\n", 1)[1].split())
        self.assertTrue(movetext.startswith(f"1. {DARK_WINS[0]} {{octocat}} 1... {DARK_WINS[1]} {{tannergolden}}"))
        self.assertTrue(movetext.endswith("{White has no move left.} 1-0"))

    def test_the_house_wins_when_black_has_no_move_left(self):
        table = Table()
        outcome = table.play(LIGHT_WINS)
        shown = games.numbered(len(LIGHT_WINS), LIGHT_WINS[-1])
        self.assertTrue(outcome.comment.startswith(f"🏆 **{shown}: Black has no move left!** @tannergolden wins game"
                                                   " 1.\n"))
        self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["result"]), (OWNER, "0-1"))
        self.assertTrue(outcome.record[1].rstrip().endswith("{Black has no move left.} 0-1"))

    def test_a_game_is_drawn_by_repetition_and_by_forty_moves(self):
        for codes, reason, said in ((REPEATED, "repetition", "by repetition"),
                                    (FORTY, "forty moves", "by the forty-move rule")):
            table = Table()
            outcome = table.play(codes)
            with self.subTest(reason):
                self.assertTrue(outcome.comment.startswith(
                    f"🤝 **{games.numbered(len(codes), codes[-1])}: game 1 is drawn {said}.**\n"))
                self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["reason"], table.hall[-1]["result"]),
                                 (None, reason, "1/2-1/2"))
                element = table.board()
                self.assertEqual((element["game"], element["result"]), (1, {"winner": None, "how": reason}))
                self.assertIn(f"Drawn {said}.", outcome.record[1])


class TwoDays(unittest.TestCase):
    def test_the_final_board_then_the_fresh_board_with_github_to_open(self):
        table = Table()
        table.play(LIGHT_WINS)
        opens = page.parse(table.game["started"])
        element = table.board()
        self.assertEqual((element["game"], element["result"], element["next"]),
                         (1, {"winner": HOUSE, "how": "no move left"}, page.day(opens)))
        for missing in ("moves", "due", "alert", "dark"):
            self.assertNotIn(missing, element)
        refused = table.move("11-15", game=2, move=1)
        self.assertEqual(refused.comment, f"⏳ **Game 2 opens {page.day(opens)}**, so `11-15` wasn't played.\nGame 1's"
                                          f" final board stays up until then: pick a move from {BOARD} once game 2 is"
                                          " on it.\n")
        self.assertFalse(table.wait(opens - table.clock - dt.timedelta(minutes=1)).changed)
        table.clock = opens
        element = table.board()
        self.assertEqual((element["game"], element["due"], element["fen"]), (2, page.day(opens + page.WEEK),
                                                                              R.START.fen))
        self.assertTrue(element["note"].startswith("@tannergolden won game 1. GitHub plays Black, which moves first in"
                                                   " American checkers"), element["note"])
        self.assertIn(games.who_plays(GITHUB, OWNER), element["note"])
        late = table.wait(page.WEEK)
        self.assertTrue(late.changed, "a week after the fresh board came, the Arbiter opens for GitHub")
        self.assertEqual(late.issue, table.hall[-1]["deciding"]["issue"], "told on the issue of the game's last move")
        self.assertIn("⏰ **A week passed without a move from GitHub**, so the Arbiter played 1. ", late.comment)
        self.assertIn(" for Black, at random.", late.comment)
        self.assertTrue(late.comment.endswith("\n@tannergolden, it's your move.\n"))


class Board(unittest.TestCase):
    def boards(self):
        for codes in (DARK_WINS, LIGHT_WINS):
            table = Table()
            yield table.board(), table
            for code in codes:
                table.move(code)
                yield table.board(), table
            table.clock = page.parse(table.game["started"])
            yield table.board(), table

    def test_every_legal_move_is_listed_once_behind_a_link_that_plays_it(self):
        table = Table()
        for code in DARK_WINS[:-1]:
            element = table.board()
            position = games.replay(table.mod, table.game)[-1] if table.game else R.START
            ply = len(table.current()["moves"]) + 1
            titles = [urllib.parse.parse_qs(urllib.parse.urlparse(entry[4]).query)["title"][0]
                      for entry in element["moves"]]
            links = [INTAKE.fullmatch(title) for title in titles]
            self.assertTrue(all(links), titles)
            self.assertEqual([link["move"] for link in links], [move.code for move in R.legal_moves(position)])
            self.assertEqual({(link["game"], link["ply"]) for link in links}, {("1", str(ply))})
            self.assertEqual(len({entry[1] for entry in element["moves"]}), len(element["moves"]))
            side = games.side_of(table.mod, table.current(), ply)
            player, player_id = (OWNER, OWNER_ID) if side == HOUSE else (OCTOCAT, OCTOCAT_ID)
            for link in links:
                request = games.Request(link["move"], 1, ply, 7, player, player_id)
                played = games.play(table.mod, table.game, table.hall, request, OWNER, OWNER_ID, table.clock)
                self.assertTrue(played.changed, (ply, link["move"], played.comment))
            table.move(code)

    def test_what_the_readme_carries_is_text_the_kit_accepts(self):
        for element, _ in self.boards():
            with self.subTest(game=element["game"], move=element["move"]):
                self.assertRegex(element["fen"], KIT_FEN)
                self.assertTrue(all(0 <= n <= 12 for n in element["kings"].values()))
                note = element["note"]
                self.assertTrue(KIT_LINE.fullmatch(note) and not KIT_BLOCK.match(note), note)
                for dash in DASHES:
                    self.assertNotIn(dash, note)
                for row in element["history"]:
                    self.assertTrue(all(cell == "" or KIT_MOVE.fullmatch(cell) for cell in row[1:3]), row)
                    self.assertTrue(row[3] == "" or KIT_WHO.fullmatch(row[3]), row)
                if "last" in element:
                    self.assertRegex(element["last"]["move"], KIT_MOVE)
                    self.assertRegex(element["last"]["words"], KIT_WORDS)
                    self.assertRegex(element["last"]["by"], KIT_WHO)
                    self.assertRegex(element["last"]["when"], KIT_DAY)
                for emoji, title, notation, words, _ in element.get("moves", []):
                    self.assertRegex(emoji, KIT_EMOJI)
                    self.assertRegex(title, KIT_TITLE)
                    self.assertRegex(notation, KIT_MOVE)
                    self.assertRegex(words, KIT_WORDS)

    def test_no_reply_or_commit_has_a_long_dash_or_an_old_side_word_and_no_refusal_pings(self):
        texts = []
        for element, table in self.boards():
            texts += [*table.texts, element["note"]]
            texts += [outcome.record[1] for outcome in table.outcomes if outcome.record]
        for dash in DASHES:
            self.assertNotIn(dash, "".join(texts))
        for text in texts:
            self.assertNotRegex(re.sub(r"\*[^*\n]+!\*", "", text), SIDE_WORDS)
        table = Table()
        for outcome in (table.move("22-18"), table.move("11-15", game=3), table.move("11-15", move=4)):
            self.assertIsNone(PING.search(outcome.comment), outcome.comment)


if __name__ == "__main__":
    unittest.main()
