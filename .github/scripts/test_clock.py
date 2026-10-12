# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The one clock for all four games, run as its workflow runs it: every game ticked, saved, set out and noticed in
one run, with one commit.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chess
import clock
import games
import page

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
T0 = page.parse("2026-10-12T16:00:00Z")
SETTINGS = "elements:\n  other:\n    kind: placard\n\ntrophies:\n  style: trophy\n"
FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]


class Run(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / ".github"
        self.root.mkdir()
        self.settings = self.root / "markdown.yaml"
        self.settings.write_text(SETTINGS, encoding="utf-8")
        self.out = Path(self.temp.name) / "out"

    def tearDown(self):
        self.temp.cleanup()

    def run_clock(self, moment: dt.datetime, **values) -> tuple[int, dict]:
        output = Path(self.temp.name) / "output.txt"
        output.unlink(missing_ok=True)
        env = {"OWNER": OWNER, "OWNER_ID": str(OWNER_ID), "GITHUB_OUTPUT": str(output),
               "RUN_URL": "https://github.com/tannergolden/tannergolden/actions/runs/1", **values}
        with contextlib.redirect_stdout(io.StringIO()):
            code = clock.main([str(self.root), "--out", str(self.out), "--now", page.stamp(moment), "--settings",
                               str(self.settings)], env)
        said = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines()) if code == 0 else {}
        return code, said

    def state(self, key: str) -> tuple[dict | None, list]:
        return page.load(self.root / key)

    def commit(self) -> str:
        return (self.out / "commit.txt").read_text(encoding="utf-8")

    def said(self) -> str:
        """The commit's message on one line, however its body wraps."""
        return " ".join(self.commit().split())

    def stale(self, key: str) -> None:
        """Sets `key`'s board out as an older engine would have: its note in other words, and no game moved."""
        text = self.settings.read_text(encoding="utf-8")
        start, end = text.index(f"# {key}:start"), text.index(f"# {key}:end")
        region = re.sub(r"(?m)^(    note: ).*$", r'\1"An older note."', text[start:end], count=1)
        self.assertNotEqual(region, text[start:end])
        self.settings.write_text(text[:start] + region + text[end:], encoding="utf-8")

    def notices(self) -> list[str]:
        return (self.out / "notices.txt").read_text(encoding="utf-8").splitlines()

    def test_the_first_run_opens_the_arbiter_s_games_starts_checkers_and_sets_every_board_and_the_hall_out(self):
        code, said = self.run_clock(T0)
        self.assertEqual((code, said), (0, {"changed": "true", "notices": "0"}))
        for key in ("tictactoe", "connectfour"):
            game, _ = self.state(key)
            self.assertEqual((game["game"], len(game["moves"]), game["moves"][0]["arbiter"]), (1, 1, True))
        self.assertEqual(self.state("checkers"), ({"game": 1, "started": page.stamp(T0), "moves": []}, []),
                         "checkers starts at once, with GitHub to open as Black")
        self.assertEqual(self.state("chess"), (None, []), "the house opens chess itself, with its first move")
        text = self.settings.read_text(encoding="utf-8")
        found = [text.index(f"  # {region}:start\n") for region in page.REGIONS]
        self.assertEqual(found, sorted(found), "every region, in the page's order")
        self.assertTrue(text.endswith("  # hall:end\n\ntrophies:\n  style: trophy\n"))
        self.assertTrue(self.commit().startswith("chore(games): ⏰ run the clock for tictactoe, connectfour and"
                                                 " checkers\n\nchore(tictactoe): 🎲 open game 1 for "))
        self.assertIn("\n\nchore(connectfour): 🎲 open game 1 for ", self.commit())
        self.assertIn("\n\nchore(checkers): 🏁 start game 1, GitHub to open as Black\n\n", self.commit())
        self.assertIn('  checkers:\n    kind: "checkers"\n', text)
        self.assertIn(f'    due: "{page.day(T0 + page.WEEK)}"\n', text.split("# checkers:start")[1])
        self.assertTrue(self.commit().endswith("\n\nRun: https://github.com/tannergolden/tannergolden/actions/runs/1\n"))
        self.assertEqual(self.notices(), [], "an opening answers no issue")

    def test_a_tick_with_nothing_to_do_changes_nothing(self):
        self.run_clock(T0)
        before = self.settings.read_text(encoding="utf-8")
        code, said = self.run_clock(T0 + dt.timedelta(hours=1))
        self.assertEqual((code, said), (0, {"changed": "false", "notices": "0"}))
        self.assertEqual(self.settings.read_text(encoding="utf-8"), before)
        self.assertEqual(self.commit(), "\n")

    def test_the_arbiter_s_week_runs_out_in_several_games_at_once_and_each_is_noticed(self):
        self.run_clock(T0)
        chess_game = chess.play(None, [], chess.Request("e2e4", 1, 1, 41, OWNER, OWNER_ID), OWNER, OWNER_ID,
                                T0 + dt.timedelta(minutes=30))
        chess.save(self.root / "chess", chess_game)
        code, said = self.run_clock(T0 + page.WEEK + dt.timedelta(hours=1))
        self.assertEqual((code, said), (0, {"changed": "true", "notices": "4"}))
        self.assertEqual(self.notices(), ["logbook tictactoe.md", "logbook connectfour.md", "logbook checkers.md",
                                          "41 chess.md"],
                         "after its own opening, or a start nobody moved from, the Arbiter writes in the logbook; after"
                         " the owner's move, on its issue")
        for key, arbiter in (("tictactoe", [True, True]), ("connectfour", [True, True]), ("checkers", [True])):
            game, _ = self.state(key)
            self.assertEqual([played["arbiter"] for played in game["moves"]], arbiter)
            self.assertTrue((self.out / f"{key}.md").read_text(encoding="utf-8").startswith(
                "⏰ **A week passed without a move from "))
        self.assertIn("so the Arbiter played 1. ", (self.out / "checkers.md").read_text(encoding="utf-8"))
        self.assertIn(" for Black, at random.", (self.out / "checkers.md").read_text(encoding="utf-8"))
        self.assertTrue(self.commit().startswith("chore(games): ⏰ run the clock for tictactoe, connectfour, checkers"
                                                 " and chess\n\n"))
        self.assertTrue(self.state("chess")[0]["moves"][-1]["arbiter"])

    def test_a_finished_game_s_fresh_board_comes_on_the_first_tick_after_its_two_days(self):
        game, hall = None, []
        for ply, uci in enumerate(FOOLS_MATE, 1):
            player = (OWNER, OWNER_ID) if ply % 2 else (OCTOCAT, OCTOCAT_ID)
            outcome = chess.play(game, hall, chess.Request(uci, 1, ply, 50 + ply, *player), OWNER, OWNER_ID,
                                 T0 + dt.timedelta(minutes=ply))
            chess.save(self.root / "chess", outcome)
            game, hall = outcome.game, outcome.hall
        opens = page.parse(game["started"])
        self.run_clock(opens - dt.timedelta(minutes=1))
        settings = self.settings.read_text(encoding="utf-8")
        self.assertIn('    result: {"winner": "github", "how": "checkmate"}\n', settings)
        before = (self.root / "chess" / "game.json").read_text(encoding="utf-8")
        code, said = self.run_clock(opens + dt.timedelta(minutes=59))
        self.assertEqual((code, said["changed"], said["notices"]), (0, "true", "0"))
        self.assertEqual((self.root / "chess" / "game.json").read_text(encoding="utf-8"), before,
                         "the fresh board needs no new state, only the page drawn again")
        self.assertNotIn("result:", self.settings.read_text(encoding="utf-8").split("# chess:start")[1])
        self.assertEqual(self.commit().splitlines()[0], "chore(games): 🖌️ set the boards out for the page")
        self.assertIn("The clock set out chess again: a final board's two days are up, and the fresh board has"
                      " come.", self.said())
        self.assertNotIn("as the engine sets", self.said())

    def test_a_board_set_out_anew_with_no_move_says_the_engine_sets_it_out_differently(self):
        self.run_clock(T0)
        self.stale("tictactoe")
        code, said = self.run_clock(T0 + dt.timedelta(minutes=1))
        self.assertEqual((code, said["changed"], said["notices"]), (0, "true", "0"))
        self.assertEqual(self.commit().splitlines()[0], "chore(games): 🖌️ set the boards out for the page")
        self.assertIn("The clock set out tictactoe again, as the engine sets it out now: no game moved.", self.said())
        self.assertNotIn("two days", self.said(), "no final board came down")
        self.stale("connectfour")
        self.stale("checkers")
        self.run_clock(T0 + dt.timedelta(minutes=2))
        self.assertIn("The clock set out connectfour and checkers again, as the engine sets them out now", self.said())

    def test_a_fresh_board_and_a_board_set_out_anew_are_each_told_for_what_they_are(self):
        game, hall = None, []
        for ply, uci in enumerate(FOOLS_MATE, 1):
            player = (OWNER, OWNER_ID) if ply % 2 else (OCTOCAT, OCTOCAT_ID)
            outcome = chess.play(game, hall, chess.Request(uci, 1, ply, 50 + ply, *player), OWNER, OWNER_ID,
                                 T0 + dt.timedelta(minutes=ply))
            chess.save(self.root / "chess", outcome)
            game, hall = outcome.game, outcome.hall
        opens = page.parse(game["started"])
        self.run_clock(opens - dt.timedelta(minutes=1))
        self.stale("tictactoe")
        code, said = self.run_clock(opens + dt.timedelta(minutes=59))
        self.assertEqual((code, said["changed"]), (0, "true"))
        self.assertIn("The clock set out chess again: a final board's two days are up, and the fresh board has come."
                      " It also set out tictactoe again, as the engine sets it out now: no game moved.", self.said())

    def test_one_game_s_own_commit_stands_when_it_alone_moved_on(self):
        self.run_clock(T0)
        for key in ("tictactoe", "checkers"):  # a move three days in, so only Connect Four's week runs out
            mod = games.rules(key)
            game, hall = self.state(key)
            ply = len(game["moves"]) + 1
            player = (OWNER, OWNER_ID) if games.side_of(mod, game, ply) == "house" else (OCTOCAT, OCTOCAT_ID)
            code = mod.legal(games.replay(mod, game)[-1])[0]
            moved = games.play(mod, game, hall, games.Request(code, 1, ply, 60, *player), OWNER, OWNER_ID,
                               T0 + dt.timedelta(days=3))
            self.assertTrue(moved.changed, moved.comment)
            games.save(self.root / key, moved)
        code, said = self.run_clock(T0 + page.WEEK + dt.timedelta(minutes=1))
        self.assertEqual((code, said["notices"]), (0, "1"))
        self.assertTrue(self.commit().startswith("chore(connectfour): ⏰ play 1... "), self.commit())

    def test_a_run_without_its_owner_or_its_settings_stops(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(clock.main([str(self.root), "--now", page.stamp(T0)], {"OWNER": OWNER}), 1)
        self.settings.write_text("trophies:\n  style: trophy\n", encoding="utf-8")
        code, _ = self.run_clock(T0)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
