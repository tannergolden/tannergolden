# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every board the four games write, and the Hall of Fame of all four, held to tannergolden/markdown's own checks: the
kit is the judge.

  KIT_SRC=../markdown/src python3 -m unittest discover -s .github/scripts -p 'test_kit.py'

The kit draws each board from the element the engines write, and turns away
any field it can't draw. With KIT_SRC naming a checkout of the kit's `src`,
this plays every line the games' own tests play, every way round the Arbiter
can draw, from the Ghost Rule's ghosts through to the final board and the
fresh one, and many random games besides, and hands every board the kit's
`check` for its kind, which must find nothing, then its `state`, its
description and its README block, which must draw from it. The Hall of Fame
goes the same way, along scores of games of all four played by more players
than the page has places for, the Arbiter's week turns among them, and a few
of its sheets are drawn; and so do the facts of every game a person's own move
won, which the kit's replay reads. A kind the checkout doesn't have yet is
skipped, and without KIT_SRC all of it is: the games' own tests hold the same
shapes.
"""
from __future__ import annotations

import datetime as dt
import importlib
import itertools
import os
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import games
import hall
import page
import replays
import test_checkers
import test_chess
import test_games
from page import HOUSE

KIT = os.environ.get("KIT_SRC", "")
OWNER, OWNER_ID = test_games.OWNER, test_games.OWNER_ID
HOUR = dt.timedelta(hours=1)
POOL = [(f"player-{n}", 1000 + n) for n in range(1, 31)]  # more of GitHub's players than the leaderboard has rows


def has(kind: str) -> bool:
    """Whether KIT_SRC names a checkout of the kit's `src` that draws `kind` (its folder under domain/elements)."""
    return bool(KIT) and Path(KIT, "domain", "elements", kind).is_dir()


def kit(module: str):
    """One of the kit's own modules, from the checkout KIT_SRC names."""
    sys.path.insert(0, KIT)
    try:
        return importlib.import_module(module)
    finally:
        sys.path.remove(KIT)


def lines_of_play():
    """Every board of Tic-Tac and Pentago along every line, every way round the Arbiter can draw: before the
    ghosts, after each, along the line, and the final and the fresh board; and every board of seeded random games
    under ghosts set at random, now and then a week left to the Arbiter."""
    for key in test_games.KEYS:
        for line in test_games.LINES[key]:
            for places, opens in test_games.SIDES:
                table = test_games.Table(key, places, opens, ghosts=())
                yield table.board()
                for ghost in test_games.GHOSTS[key]:
                    table.lay((ghost,), opens)
                    yield table.board()
                for code in line:
                    table.move(code)
                    yield table.board()
                table.fresh()
                yield table.board()
        mod, rng = games.rules(key), random.Random(key)
        for places, opens in test_games.SIDES:
            for _ in range(3):
                table = test_games.Table(key, places, opens, ghosts=tuple(rng.sample(mod.ghost_cells(()), 2)))
                while "moves" in table.board():
                    if rng.random() < 0.05:
                        table.wait(page.WEEK)
                    else:
                        table.move(rng.choice(mod.legal(games.replay(mod, table.game)[-1])))
                    yield table.board()


def checkers_boards():
    yield games.board(games.rules("checkers"), None, [], OWNER, test_checkers.T0)
    for codes in (test_checkers.DARK_WINS, test_checkers.LIGHT_WINS, test_checkers.REPEATED):
        table = test_checkers.Table()
        for code in codes:
            table.move(code)
            yield table.board()
        table.clock = page.parse(table.game["started"])
        yield table.board()


def chess_boards():
    yield test_chess.chess.board(None, [], OWNER, test_chess.T0)
    lines = [line.split() for line in test_chess.SPECIAL.values()]
    lines += [test_chess.FOOLS_MATE, test_chess.SCHOLARS_MATE, test_chess.LOYDS_STALEMATE]
    for line in lines:
        table = test_chess.Table()
        for uci in line:
            table.move(uci)
            yield table.board()
        if table.game["moves"]:
            continue
        table.fresh()
        yield table.board()
        table.clock += dt.timedelta(days=8)
        table.wait(dt.timedelta(0))
        yield table.board()


# --- the Hall of Fame along hundreds of games ----------------------------------------------------------------------
def player(rng: random.Random, moves: int) -> tuple[str, int]:
    """One of GitHub's players from the pool, now and then under a new login after enough moves, as on GitHub."""
    login, account = rng.choice(POOL)
    return (f"{login}-renamed" if moves > 400 and account % 3 == 0 else login), account


def random_games(key: str, rng: random.Random, count: int):
    """`count` finished games of one of the three at random, GitHub's turns, ghosts among them, picked by the pool's
    players and now and then a week left to the Arbiter: the game's state after every step."""
    mod, clock, issue, moves = games.rules(key), test_games.T0, 100, 0
    game, records = None, []

    def keep(outcome: games.Outcome) -> None:
        nonlocal game, records
        if outcome.changed:
            game, records = outcome.game, outcome.hall

    keep(games.tick(mod, None, [], OWNER, clock))  # the first game: its start, and the Arbiter's draw where it draws
    while len(records) < count:
        if not games.turns(game) and page.parse(game["started"]) > clock:  # a final board is up
            clock = page.parse(game["started"])
            keep(games.tick(mod, game, records, OWNER, clock))
        elif rng.random() < 0.08:
            clock += page.WEEK + HOUR
            keep(games.tick(mod, game, records, OWNER, clock))
        else:
            turn = len(games.turns(game)) + 1
            login, account = ((OWNER, OWNER_ID) if games.side_of(mod, game, turn) == HOUSE else player(rng, moves))
            if games.ghosting(mod, game):
                code = rng.choice(mod.ghost_cells([ghost["move"] for ghost in game["ghosts"]]))
            else:
                code = rng.choice(sorted(mod.legal(games.replay(mod, game)[-1])))
            clock, issue, moves = clock + HOUR, issue + 1, moves + 1
            keep(games.play(mod, game, records, games.Request(code, game["game"], turn, issue, login, account),
                            OWNER, OWNER_ID, clock))
        yield game, records


def chess_games(rng: random.Random, count: int):
    """`count` finished games of chess, its mates and stalemate over and over, GitHub's moves picked by the pool's
    players: the game's state after every move."""
    table, lines = test_chess.Table(), itertools.cycle([test_chess.FOOLS_MATE, test_chess.SCHOLARS_MATE,
                                                        test_chess.LOYDS_STALEMATE])
    for line in itertools.islice(lines, count):
        for ply, uci in enumerate(line, 1):
            login, account = (OWNER, OWNER_ID) if ply % 2 else player(rng, 0)
            table.move(uci, player=login, player_id=account)
            yield table.game, table.hall
        table.fresh()


def hall_elements():
    """The Hall of Fame after every step of scores of games of all four, played round and round, one step of each
    game in turn."""
    rng = random.Random("hall-of-fame")
    walks = {"tictac": random_games("tictac", rng, 12), "pentago": random_games("pentago", rng, 20),
             "checkers": random_games("checkers", rng, 4), "chess": chess_games(rng, 12)}
    states = {key: (None, []) for key in hall.GAMES}
    while walks:
        for key in list(walks):
            try:
                states[key] = next(walks[key])
            except StopIteration:
                del walks[key]
                continue
            yield hall.element(states, OWNER, OWNER_ID)


def replay_facts():
    """The replay facts of every game a person's own move won along the games' own lines, every way round the Arbiter
    can draw, of seeded random games of the three this engine plays, and of chess's mates."""
    for key in test_games.KEYS:
        for line in test_games.LINES[key]:
            for places, opens in test_games.SIDES:
                outcome = test_games.Table(key, places, opens).play(line)
                if outcome.replay:
                    yield outcome.replay[1]
    for key, count in (("tictac", 6), ("pentago", 10), ("checkers", 3)):
        mod, seen = games.rules(key), set()
        for game, records in random_games(key, random.Random(f"replays of {key}"), count):
            ended, record = game.get("ended"), records[-1] if records else None
            if ended and record and record["game"] not in seen and replays.due(record):
                seen.add(record["game"])
                yield replays.facts(mod, ended, games.replay(mod, ended), record, OWNER)
    for codes in (test_checkers.DARK_WINS, test_checkers.LIGHT_WINS):
        yield test_checkers.Table().play(codes).replay[1]
    for line in (test_chess.FOOLS_MATE, test_chess.SCHOLARS_MATE):
        yield test_chess.Table().play(line).replay[1]


class Kit(unittest.TestCase):
    def judge(self, kind: str, boards) -> int:
        game, readme = kit(f"domain.elements.{kind}.game"), kit(f"domain.elements.{kind}.readme")
        count = 0
        for element in boards:
            with self.subTest(kind=kind, game=element.get("game"), move=element.get("move")):
                self.assertEqual(element["kind"], kind)
                self.assertEqual(game.check(element), [], element)
                (game.board_state if kind == "chess" else game.state)(element)
                described = game.describe(element)
                self.assertTrue(described["title"] and described["desc"])
                below = readme.text(element)
                self.assertNotIn("[!", below, "no banner: the board's own sheet says whose turn it is")
                if "result" in element:
                    self.assertNotIn("<details>", below, "a finished board lists nothing to play")
            count += 1
        return count

    @unittest.skipUnless(has("tictac") and has("pentago"), "KIT_SRC names no kit that draws the two games")
    def test_tic_tac_and_pentago(self):
        boards = list(lines_of_play())
        for kind in test_games.KEYS:
            self.assertGreater(self.judge(kind, [b for b in boards if b["kind"] == kind]), 100)

    @unittest.skipUnless(has("checkers"), "KIT_SRC names no kit that draws checkers")
    def test_checkers(self):
        self.assertGreater(self.judge("checkers", checkers_boards()), 100)

    @unittest.skipUnless(has("chess"), "KIT_SRC names no kit that draws chess")
    def test_chess_unfinished_finished_and_fresh(self):
        self.assertGreater(self.judge("chess", chess_boards()), 50)

    @unittest.skipUnless(has("replay"), "KIT_SRC names no kit that draws replays")
    def test_replays(self):
        replay, kinds = kit("domain.elements.replay"), set()
        for facts in replay_facts():
            with self.subTest(kind=facts["kind"], game=facts["game"], winner=facts["winner"]):
                self.assertEqual(replay.check(facts), [], facts)
                self.assertTrue(replay.prepared(facts)["span"])
            kinds.add(facts["kind"])
        self.assertEqual(kinds, {"tictac", "pentago", "checkers", "chess"})

    @unittest.skipUnless(has("hall"), "KIT_SRC names no kit that draws the Hall of Fame of all four games")
    def test_hall_of_fame(self):
        drawn, prints = kit("domain.elements.hall"), kit("domain.prints")
        kit("infra.resources").install()  # the kit's lettering, prints and calibration, which its sheets draw with
        count, last, full = 0, None, None
        for element in hall_elements():
            with self.subTest(step=count):
                self.assertEqual(drawn.check(element), [], element)
                state = drawn.state(element)
                self.assertTrue(drawn.describe(element)["desc"])
                self.assertTrue(drawn.leaderboard(element).startswith("<details>"))
                drawn.badges("hall-of-fame", element, ".")
                if len(element["leaders"]) == 21 and len(element["people"]) == 10 and full is None:
                    full = element
            count, last = count + 1, (element, state)
        element, state = last
        self.assertGreater(count, 1000)
        self.assertIsNotNone(full, "the lists reach their ceilings: ten winners and twenty of GitHub's players")
        self.assertEqual(sum(state["totals"][key] for key in ("house", "github", "draws")), state["totals"]["games"])
        self.assertEqual(state["totals"]["games"], 12 + 20 + 4 + 12)
        for sheet in (element, full):
            for variant in drawn.variants("hall-of-fame", sheet):
                for theme in ("day", "dark"):
                    self.assertTrue(drawn.draw("hall-of-fame", sheet, prints.STANDARD, theme, variant)
                                    .lstrip().startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
