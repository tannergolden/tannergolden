# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Tic-Tac and Pentago, played offline through the same calls their workflow makes: every way a turn goes, the Ghost
Rule's ghosts and the Arbiter's draws among them.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

Each game is played at a table: turns come in as the intake sends them, from
the owner for the house and from made-up players for GitHub, at times the
test sets, so the Arbiter's week and a final board's two days pass in a line.
Each player keeps one mark or colour in every game, the house X and White,
GitHub O and Black. Under the Ghost Rule the Arbiter draws the side that
places the first ghost once a fresh board's start has come, and the side
that moves first as the second ghost goes down, each draw seeded by its
moment: a table is laid at the first minute whose draw gives the side the
test asks for, and its second ghost goes down at the first minute that draws
the opener it asks for, so a game's line can be written down. A turn's
number counts every turn, the ghosts the first two.

One test goes past the two games: it sets out every kind of board in all
four, to hold that none carries a banner over it.
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

import chess
import games
import hall
import page
from page import GITHUB, HOUSE, other

OWNER, OWNER_ID = "tannergolden", 24684994
OCTOCAT, OCTOCAT_ID = "octocat", 583231
HUBOT, HUBOT_ID = "hubot", 480938
T0 = page.parse("2026-10-12T16:00:00Z")
HOUR, MINUTE = dt.timedelta(hours=1), dt.timedelta(minutes=1)
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
PING = re.compile(r"(?<![\[\w])@[A-Za-z0-9][A-Za-z0-9-]*")  # a mention GitHub notifies: outside a link's text
LINKED = "[@tannergolden](https://github.com/tannergolden)"
BOARD = "[the board](https://github.com/tannergolden)"
SETTINGS = "elements:\n  other:\n    kind: placard\n\ntrophies:\n  style: trophy\n"

# What tannergolden/markdown accepts from the games (src/domain/elements/games/data.py, chess/game.py whose checks
# every game shares, and each game's game.py).
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,98}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_WHO = re.compile(r"@[A-Za-z0-9][A-Za-z0-9-]{0,38}|the Arbiter")
KIT_DAY = re.compile(r"(?:[1-9]|[12][0-9]|3[01]) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
KIT_MOMENT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(?::[0-9]{2})?(?:Z|[+-][0-9]{2}:[0-9]{2})")
KIT_LINE = re.compile(r"[^<>|\n\r]{1,400}")
KIT_BLOCK = re.compile(r"\s|```|~~~|#{1,6}(?:\s|$)|>|[-*+](?:\s|$)|[0-9]+[.)](?:\s|$)|\[[^\]]*\]:|[-=*_\s]+$")
KIT_HOW = re.compile(r"[a-z][a-z0-9 ,'-]{0,23}")
KIT_BOARD = {"tictac": re.compile(r"(?:[XOG.]{9}/){8}[XOG.]{9}"), "pentago": re.compile(r"(?:[WBG.]{6}/){5}[WBG.]{6}")}
KIT_MOVE = {"tictac": re.compile(r"[XO][a-i][1-9]#?|[a-i][1-9]"),  # a mark, or a ghost's square
            "pentago": re.compile(r"[a-f][1-6]-(?:ul|ur|ll|lr)-(?:cw|acw)#?|[a-f][1-6]#?")}  # or a hole alone
KIT_OFFER = {"tictac": re.compile(r"[XO][a-i][1-9]|[a-i][1-9]"), "pentago": re.compile(r"[a-f][1-6]")}
KIT_ALERTS = {"tictac": ("place a ghost", "any board", "upper left board", "top board", "upper right board",
                         "left board", "centre board", "right board", "lower left board", "bottom board",
                         "lower right board"),
              "pentago": ("set a ghost",)}
KIT_ENDS = {"tictac": {"three boards in a row": True, "no line left": False},
            "pentago": {"five in a row": True, "five for both": False, "a full board": False}}
KIT_LETTERS = {"tictac": {HOUSE: "X", GITHUB: "O"}, "pentago": {HOUSE: "W", GITHUB: "B"}}
NUMBER = r"[1-9][0-9]{0,8}"
CODES = {"tictac": r"[a-i][1-9]", "pentago": r"[a-f][1-6](?:-(?:ul|ur|ll|lr)-(?:cw|acw))?"}
KIT_LINK = {key: re.compile(r"https://github\.com/tannergolden/play/issues/new\?template=move\.yml&title=" + key
                            + rf"%3A%20{code}%20%C2%B7%20game%20{NUMBER}%20%C2%B7%20move%20{NUMBER}")
            for key, code in CODES.items()}
# What tannergolden/play's intake takes as a move's issue title, the move as `move`.
INTAKE = {key: re.compile(rf"{key}: (?P<move>{code}) · game (?P<game>{NUMBER}) · move (?P<ply>{NUMBER})")
          for key, code in CODES.items()}
TURNS = [["ul", "cw"], ["ul", "acw"], ["ur", "cw"], ["ur", "acw"], ["ll", "cw"], ["ll", "acw"], ["lr", "cw"],
         ["lr", "acw"]]  # a Pentago hole's eight links, in the order the kit takes them

# Lines of play after the ghosts, each checked move by move against the rules: Tic-Tac's and Pentago's full board found
# by a seeded search, the rest of Pentago's set out by hand. Each is named for the side that moved first, the opener,
# or the side that moved second, the reply: the opener's mark or colour is the house's or GitHub's as the Arbiter drew.
TT_GHOSTS = ("e5", "a1")
# The opener takes the upper left board's middle row, the top board's bottom row and the upper right board's diagonal,
# and with them the big board's top row: three boards in a row, at its ninth mark.
TT_FIRST_WINS = ["b8", "e6", "d7", "a3", "c8", "i6", "g7", "b3", "f7", "i3", "h8", "d6", "a8", "b6", "e7", "f3", "i9"]
# The opener's g3, a board's upper left corner, sends the reply to the upper left board, where the line above begins.
TT_SECOND_WINS = ["g3", *TT_FIRST_WINS]
# Eight boards won, four by each mark, the right board still open: no line of three boards is left for either mark.
TT_NO_LINE = ["b3", "f7", "i3", "g7", "b2", "e6", "e8", "e4", "e3", "d7", "b1", "e1", "e2", "f4", "i2", "h6", "e7",
              "f1", "i1", "d4", "e9", "d1", "c4", "a8", "b5", "h7", "a6", "c8", "g6", "b8", "h4", "i7"]
PG_GHOSTS = ("e5", "e2")  # on two quarters' centres, which never move
# The opener sets a1 to a5 up the a-file, turning the lower right quarter round its ghost: the fifth makes five
# unturned, `a5#`.
PG_UNTURNED = ["a1-lr-cw", "d6-lr-acw", "a2-lr-cw", "e6-lr-acw", "a3-lr-cw", "f6-lr-acw", "a4-lr-cw", "d5-lr-acw",
               "a5-lr-cw"]
# The opener's c4 completes the upper left quarter's bottom row, b4 and c4, and its turn stands them up the a-file.
PG_TURNED = ["a1-lr-cw", "d6-lr-acw", "a2-lr-cw", "e6-lr-acw", "a3-lr-cw", "f6-lr-acw", "b4-lr-cw", "d5-lr-acw",
             "c4-ul-cw"]
# The reply's turn stands the opener's b4 and c4 up the a-file: five for the opener alone, on the reply's move.
PG_FOR_THE_OTHER = ["a1-lr-cw", "d6-lr-acw", "a2-lr-cw", "e6-lr-acw", "a3-lr-cw", "f6-lr-acw", "b4-lr-cw",
                    "d5-lr-acw", "c4-lr-cw", "f5-ul-cw"]
# The opener's turn stands its b4 and c4 up the a-file and the reply's a6, b6 and c6 down the c-file: five for both.
PG_BOTH = ["a1-lr-cw", "a6-lr-acw", "a2-lr-cw", "b6-lr-acw", "a3-lr-cw", "c6-lr-acw", "b4-lr-cw", "c2-lr-acw",
           "c4-lr-cw", "c3-lr-acw", "f1-ul-cw"]
# Thirty-four marbles and no five for either colour at any point: the board fills.
PG_FULL = ["a6-ul-acw", "c2-ur-acw", "e4-ul-acw", "c6-ur-acw", "e3-ul-acw", "f3-ll-cw", "b5-ll-acw", "a3-ur-acw",
           "b3-ur-acw", "a1-ll-acw", "e1-lr-acw", "c5-ur-acw", "f5-ur-cw", "f4-ul-cw", "a6-ul-acw", "c2-ur-acw",
           "b1-ur-acw", "f1-lr-cw", "c4-lr-cw", "e3-ur-cw", "d6-lr-acw", "d4-lr-acw", "f3-lr-cw", "d5-ll-acw",
           "b6-ur-cw", "a5-ll-cw", "d3-lr-cw", "b2-ur-cw", "c3-ur-acw", "e1-lr-acw", "f5-lr-acw", "b4-lr-acw",
           "a3-ur-cw", "d6-ur-cw"]
GHOSTS = {"tictac": TT_GHOSTS, "pentago": PG_GHOSTS}
LINES = {"tictac": (TT_FIRST_WINS, TT_SECOND_WINS, TT_NO_LINE),
         "pentago": (PG_UNTURNED, PG_TURNED, PG_FOR_THE_OTHER, PG_BOTH, PG_FULL)}
KEYS = ("tictac", "pentago")
SIDES = ((HOUSE, HOUSE), (HOUSE, GITHUB), (GITHUB, HOUSE), (GITHUB, GITHUB))  # who places first, and who opens
FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]  # chess: the house opens, and GitHub mates on its second move
SIDE_WORDS = re.compile(r"\b(?:[Dd]ark|[Ll]ight)\b")  # the kit's materials, which nothing a reader sees says
WHY = re.compile(r"(?i)advantage|solved|force a win|wins more|far more often|first move's edge")


def drawn_at(seed: str, side: str, start: dt.datetime) -> dt.datetime:
    """The first minute from `start` at which the Arbiter's draw, seeded by `seed` and the minute's stamp after it,
    comes out `side`: `tictac:1:places:` for the side that places game 1's first ghost, `tictac:1:opens:` for the
    side that opens it."""
    moment = start
    while games.pick([HOUSE, GITHUB], seed + page.stamp(moment)) != side:
        moment += MINUTE
    return moment


class Table:
    """A game at the profile: the state between turns, and every reply so far. By the time the table is laid the
    Arbiter has drawn `places` to place game 1's first ghost; then `ghosts` go down, the first from that side and the
    second from the other, and the Arbiter draws `opens` as the second does. With no ghosts the table stops at the
    draw."""

    def __init__(self, key: str, places: str = HOUSE, opens: str = HOUSE, ghosts: tuple[str, ...] | None = None):
        self.key, self.mod = key, games.rules(key)
        self.game, self.hall, self.outcomes, self.texts, self.issue = None, [], [], [], 100
        self.clock = drawn_at(f"{key}:1:places:", places, T0)
        self.keep(games.tick(self.mod, None, [], OWNER, self.clock))
        self.lay(GHOSTS[key] if ghosts is None else ghosts, opens)

    def turn(self) -> int:
        return len(games.turns(self.game)) + 1

    def side(self) -> str:
        return games.side_of(self.mod, self.game, self.turn())

    def lay(self, ghosts: tuple[str, ...], opens: str = HOUSE) -> None:
        """Ghosts from the sides whose turn they are, an hour apart, but the second at the first minute from an hour
        on whose draw gives `opens` the first move."""
        for code in ghosts:
            after = HOUR
            if len(games.ghosts_of(self.game)) == 1:
                after = drawn_at(f"{self.key}:{self.game['game']}:opens:", opens, self.clock + HOUR) - self.clock
            outcome = self.move(code, after=after)
            assert outcome.changed, f"{code}: {outcome.comment}"

    def move(self, code: str, player: str | None = None, player_id: int | None = None, move: int | None = None,
             game: int | None = None, after: dt.timedelta = HOUR) -> games.Outcome:
        """A turn from whoever's turn it is, at the turn on the board, unless the test says otherwise."""
        player = player or (OWNER if self.side() == HOUSE else OCTOCAT)
        player_id = player_id or {OWNER: OWNER_ID, OCTOCAT: OCTOCAT_ID, HUBOT: HUBOT_ID}.get(player, 7)
        self.clock += after
        self.issue += 1
        request = games.Request(code, game or self.game["game"], move or self.turn(), self.issue, player, player_id)
        return self.keep(games.play(self.mod, self.game, self.hall, request, OWNER, OWNER_ID, self.clock))

    def again(self, code: str, move: int, issue: int, player: str = OCTOCAT, player_id: int = OCTOCAT_ID,
              game: int = 1) -> games.Outcome:
        """A turn sent again from its own issue, as a re-run of its job sends it, changing nothing at the table."""
        request = games.Request(code, game, move, issue, player, player_id)
        return games.play(self.mod, self.game, self.hall, request, OWNER, OWNER_ID, self.clock)

    def wait(self, span: dt.timedelta) -> games.Outcome:
        self.clock += span
        return self.keep(games.tick(self.mod, self.game, self.hall, OWNER, self.clock))

    def fresh(self) -> games.Outcome | None:
        """Waits out a finished game's two days, to the clock's run at the moment the fresh board comes."""
        if not games.turns(self.game) and page.parse(self.game["started"]) > self.clock:
            return self.wait(page.parse(self.game["started"]) - self.clock)
        return None

    def keep(self, outcome: games.Outcome) -> games.Outcome:
        if outcome.changed:
            self.game, self.hall = outcome.game, outcome.hall
        self.outcomes.append(outcome)
        self.texts += [outcome.comment, outcome.commit, *(outcome.record or ())]
        return outcome

    def play(self, codes: list[str]) -> games.Outcome:
        """A line of moves after the ghosts, each from the side whose turn it is."""
        outcome = None
        for code in codes:
            outcome = self.move(code)
            assert outcome.changed, f"{code}: {outcome.comment}"
        return outcome

    def board(self) -> dict:
        return games.board(self.mod, self.game, self.hall, OWNER, self.clock)


def tables(key: str):
    """A table of the game for every draw: each side placing first, and each side opening."""
    for places, opens in SIDES:
        yield places, opens, Table(key, places, opens)


def named(side: str) -> str:
    return "@tannergolden" if side == HOUSE else "GitHub"


def unsaid(text: str) -> str:
    """A reply or note without the move titles it quotes, which are names in each game's own words."""
    return re.sub(r"\*[^*\n]+\*(?= · )", "", text)


def links(entry: list) -> list[str]:
    """The links a listed move carries: one, or a Pentago hole's eight, one for each turn."""
    return [url for _, _, url in entry[4]] if isinstance(entry[4], list) else [entry[4]]


def title_of(url: str) -> str:
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["title"][0]


class GhostRule(unittest.TestCase):
    """Both games open under the Ghost Rule: once a fresh board's start has come the Arbiter draws the side that
    places the first ghost, the other side places the second, and as it goes down the Arbiter draws the side that
    moves first. Its draws count for nobody, and each side keeps its mark or colour whoever moves first."""

    def test_the_first_run_draws_the_side_that_places_the_first_ghost(self):
        for key in KEYS:
            for places in (HOUSE, GITHUB):
                table = Table(key, places, ghosts=())
                drawn = table.outcomes[0]
                with self.subTest(key=key, places=places):
                    self.assertTrue(drawn.changed)
                    self.assertEqual(table.game, {"game": 1, "started": page.stamp(table.clock), "places": places,
                                                  "ghosts": [], "moves": []})
                    self.assertEqual((drawn.issue, drawn.logbook, drawn.comment), (None, False, ""),
                                     "a draw answers no issue")
                    subject, body = drawn.commit.split("\n\n")
                    verb, does = table.mod.GHOSTS[:2]  # place and places, or set and sets: each game's own words
                    self.assertEqual(subject, f"chore({key}): 🎲 start game 1, {OWNER if places == HOUSE else 'GitHub'}"
                                              f" to {verb} the first ghost")
                    self.assertEqual(" ".join(body.split()), f"Under the Ghost Rule each side {does} one ghost before"
                                                             f" the first move of {table.mod.TITLE}, the Arbiter"
                                                             f" drawing the side that {does} first, and then the side"
                                                             " that moves first.")
                    self.assertEqual(drawn.log, f"the Arbiter drew {named(places)} to {verb} game 1's first ghost; the"
                                                f" side to move has until {page.stamp(table.clock + page.WEEK)}")
                    self.assertEqual(games.tick(table.mod, table.game, [], OWNER, table.clock + HOUR).changed, False,
                                     "and draws once")

    def test_the_draws_are_seeded_and_fair(self):
        for key in KEYS:
            mod = games.rules(key)
            places, opens = {HOUSE: 0, GITHUB: 0}, {HOUSE: 0, GITHUB: 0}
            mover = {"player": None, "player_id": None, "issue": None, "arbiter": True}
            for minute in range(400):
                moment = T0 + minute * MINUTE
                game, drawn = games.settle(mod, None, moment)
                self.assertEqual(games.settle(mod, None, moment), (game, drawn), "the same moment draws the same side")
                places[drawn] += 1
                first = games.place_ghost(mod, game, [], "a1", mover, moment)[0].game
                second, _, opener = games.place_ghost(mod, first, [], "b2", mover, moment + HOUR)
                self.assertEqual(second.game["opens"], opener)
                opens[opener] += 1
            with self.subTest(key=key):
                self.assertGreater(min(places.values()), 150, places)
                self.assertGreater(min(opens.values()), 150, opens)

    def test_each_side_places_one_ghost_and_the_second_draws_the_side_that_moves_first(self):
        for key in KEYS:
            for places, opens, table in tables(key):
                ghosts = table.game["ghosts"]
                with self.subTest(key=key, places=places, opens=opens):
                    self.assertEqual((table.game["places"], table.game["opens"], table.game["moves"]),
                                     (places, opens, []))
                    self.assertEqual([g["move"] for g in ghosts], list(GHOSTS[key]))
                    self.assertEqual([g["player"] for g in ghosts],
                                     [OWNER, OCTOCAT] if places == HOUSE else [OCTOCAT, OWNER])
                    self.assertEqual([games.side_of(table.mod, table.game, turn) for turn in range(1, 5)],
                                     [places, other(places), opens, other(opens)])
                    self.assertEqual(table.mod.WORDS, {"tictac": {HOUSE: "X", GITHUB: "O"},
                                                       "pentago": {HOUSE: "White", GITHUB: "Black"}}[key])
                    self.assertEqual((games.house_moves(table.mod, table.game),
                                      games.contributors(table.mod, table.game)),
                                     (1, [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 1}]),
                                     "a ghost is a turn of the side that placed it")
                    element = table.board()
                    self.assertEqual((element["places"], element["opens"], element["move"]), (places, opens, 1))
                    self.assertEqual(element["board"].count("G"), 2)
                    self.assertEqual(element["last"], {"move": GHOSTS[key][1], "words": element["last"]["words"],
                                                       "by": "@octocat" if places == HOUSE else "@tannergolden",
                                                       "when": page.day(table.clock)})

    def test_a_ghost_s_reply_names_it_and_says_whose_turn_comes_next(self):
        table = Table("tictac", HOUSE, HOUSE)
        first, second = table.outcomes[1:3]
        self.assertEqual(first.comment, "👻 **G. e5 is on the board.**\n👻 *Centre Ghost* · A"
                                        " ghost locks the centre of the centre board\nGitHub's turn to place a ghost:"
                                        f" anyone but {LINKED} can pick a square for it on {BOARD}.\n")
        self.assertEqual((first.issue, first.commit, first.log),
                         (101, "chore(tictac): 👻 place G. e5 for X in game 1\n\nMove 1, by tannergolden.",
                          "placed G. e5"))
        self.assertEqual(second.comment, "👻 **G... a1 is on the board.** Well played, @octocat.\n👻 *Corner"
                                         " Ghost* · A ghost locks the lower left corner"
                                         " of the lower left board\n🎲 Both ghosts are down, so the Arbiter drew the"
                                         " side that moves first: @tannergolden, as X.\n@tannergolden, it's your move,"
                                         " in any open board.\n")
        self.assertEqual((second.issue, second.commit, second.log),
                         (102, "chore(tictac): 👻 place G... a1 for O in game 1, drawing tannergolden to open\n\nMove"
                               " 2, by octocat.", "placed G... a1, the Arbiter drawing house to open"))
        table = Table("pentago", GITHUB, GITHUB)
        first, second = table.outcomes[1:3]
        self.assertEqual(first.comment, "👻 **G. e5 is on the board.** Well played, @octocat.\n👻 *Centre Ghost*"
                                        " · A ghost on e5, the centre of the upper right"
                                        " quarter\n@tannergolden, it's your turn to set a ghost.\n")
        self.assertEqual(first.commit, "chore(pentago): 👻 set G. e5 for Black in game 1\n\nMove 1, by octocat.")
        self.assertEqual(second.comment, "👻 **G... e2 is on the board.**\n👻 *Centre Ghost*"
                                         " · A ghost on e2, the centre of the lower right quarter\n🎲 Both"
                                         " ghosts are down, so the Arbiter drew the side that moves first: GitHub, as"
                                         f" Black.\nGitHub's turn: anyone but {LINKED} can pick Black's first move"
                                         f" on {BOARD}.\n")
        self.assertEqual(second.commit, "chore(pentago): 👻 set G... e2 for White in game 1, drawing GitHub to"
                                        " open\n\nMove 2, by tannergolden.")
        self.assertIsNone(PING.search(second.comment), "GitHub's turn pings nobody")

    def test_a_ghost_turn_is_the_side_s_whose_ghost_it_is(self):
        for key in KEYS:
            mod = games.rules(key)
            verb, spot = mod.GHOSTS[0], mod.SPOT
            house = (f"⏳ **It's {LINKED}'s turn to {verb} a ghost**, so `b2` wasn't played.\nOnce {LINKED}'s ghost is"
                     f" down, pick a {spot} for GitHub's on {BOARD}.\n")
            github = (f"⏳ **It's GitHub's turn to {verb} a ghost**, so `b2` wasn't played.\nGitHub's ghost is for"
                      " everyone but you. Your turn comes next.\n")
            for places, ghosts, player, said, log in ((HOUSE, (), OCTOCAT, house, "the house's ghost"),
                                                      (GITHUB, (), OWNER, github, "GitHub's ghost"),
                                                      (HOUSE, ("e5",), OWNER, github, "GitHub's ghost"),
                                                      (GITHUB, ("e5",), HUBOT, house, "the house's ghost")):
                table = Table(key, places, ghosts=ghosts)
                before = table.game
                outcome = table.move("b2", player=player)
                with self.subTest(key=key, places=places, ghosts=ghosts):
                    self.assertFalse(outcome.changed)
                    self.assertEqual((outcome.comment, outcome.log, outcome.issue), (said, log, table.issue))
                    self.assertIs(table.game, before)
                    self.assertIsNone(PING.search(outcome.comment), "a turn away pings nobody")
        self.assertEqual((games.rules("tictac").SPOT, games.rules("pentago").SPOT), ("square", "hole"))

    def test_a_ghost_goes_on_an_empty_square_alone(self):
        for key, code, free in (("tictac", "e5", "a9"), ("pentago", "e5", "a6"), ("pentago", "b2-ur-cw", "a6")):
            table = Table(key, HOUSE, ghosts=("e5",))
            outcome = table.move(code)
            spot = table.mod.SPOT  # a square of Tic-Tac's, a hole of Pentago's
            with self.subTest(key=key, code=code):
                self.assertFalse(outcome.changed)
                self.assertEqual(outcome.comment, f"🚫 **`{code}` isn't a {spot} a ghost can go on**: a ghost goes on an"
                                                  f" empty {spot} alone, such as `{free}`.\nNothing was played. Every"
                                                  f" {spot} listed under {BOARD} is open: pick one there.\n")
                self.assertEqual(outcome.log, "illegal ghost")

    def test_a_ghost_s_square_is_nobody_s_once_the_game_is_under_way(self):
        ghosts = {"tictac": {"Xe5", "Xa1"}, "pentago": {"e5", "e2"}}  # the ghosts' squares as a move would name them
        for key, code, why in (("tictac", "e5", "a ghost locks e5, so nobody can take it"),
                               ("tictac", "a1", "a ghost locks a1, so nobody can take it"),
                               ("pentago", "e5-ur-cw", "a ghost stands on e5"),
                               ("pentago", "e2-ul-acw", "a ghost stands on e2")):
            table = Table(key, HOUSE, HOUSE)
            outcome = table.move(code)
            with self.subTest(key=key, code=code):
                self.assertFalse(outcome.changed)
                self.assertEqual(outcome.comment, f"🚫 **`{code}` isn't a legal move here**: {why}.\nNothing was"
                                                  f" played. Every move listed under {BOARD} is legal: pick one"
                                                  " there.\n")
                listed = {entry[2] for entry in table.board()["moves"]}
                self.assertFalse(listed & ghosts[key], "no ghost's square is offered")

    def test_a_pentago_ghost_turns_with_its_quarter(self):
        table = Table("pentago", HOUSE, HOUSE, ghosts=("b6", "e2"))
        self.assertEqual(table.board()["board"], ".G..../....../....../....../....G./......")
        table.move("f1-ul-cw")  # the upper left quarter turns, and its top edge's ghost with it, to the right edge
        element = table.board()
        self.assertEqual(element["board"], "....../..G.../....../....../....G./.....W")
        refused = table.move("c5-lr-cw")
        self.assertEqual(refused.comment.splitlines()[0], "🚫 **`c5-lr-cw` isn't a legal move here**: a ghost stands"
                                                          " on c5.")
        self.assertIn("b6", [entry[2] for entry in element["moves"]], "the hole it left is free")
        self.assertTrue(table.move("b6-lr-cw").changed)

    def test_a_hole_alone_after_the_ghosts_is_turned_away(self):
        table = Table("pentago", HOUSE, HOUSE)
        before = table.game
        outcome = table.move("e4")
        self.assertFalse(outcome.changed)
        self.assertIs(table.game, before)
        self.assertEqual(outcome.comment, "🚫 **`e4` isn't a legal move here**: a move names its hole, then the quarter"
                                          " it turns and which way, such as `e4-ul-cw`.\nNothing was played. Every"
                                          f" move listed under {BOARD} is legal: pick one there.\n")
        self.assertEqual(outcome.log, "illegal")

    def test_a_turn_s_number_counts_the_ghosts(self):
        for key in KEYS:
            table = Table(key, GITHUB, GITHUB, ghosts=())
            line = [*GHOSTS[key], *LINES[key][0][:3]]
            for turn, code in enumerate(line, 1):
                element = table.board()
                plies = {INTAKE[key].fullmatch(title_of(url))["ply"] for entry in element["moves"]
                         for url in links(entry)}
                with self.subTest(key=key, turn=turn):
                    self.assertEqual(plies, {str(turn)}, "the issue title's move counts the ghosts")
                    self.assertEqual(element["move"], max(1, (turn - 1) // 2))
                if turn == 2:
                    table.lay((code,), GITHUB)
                else:
                    table.move(code)
            self.assertEqual(table.board()["move"], 2, "the fourth move is the reply's second, on the second row")

    def test_a_turn_sent_for_a_ghost_s_number_is_too_late(self):
        table = Table("tictac", HOUSE, GITHUB)  # the owner placed e5, octocat a1, and GitHub opens
        outcome = table.move("b8", player=HUBOT, move=2)
        self.assertEqual(outcome.comment, "⌛ **Too late: move 2 is already on the board**, so `b8` wasn't played.\n"
                                          "G... a1 got there first, played by [@octocat](https://github.com/octocat)."
                                          f" Pick a move from {BOARD} as it stands now.\n")
        self.assertIn("G. e5 got there first, played by you.", table.move("b8", player=OWNER, move=1).comment)
        self.assertEqual(table.move("b8", move=4).comment,
                         f"❓ **The board is on move 3, not move 4**, so `b8` wasn't played.\nPick a move from {BOARD}"
                         " as it stands now.\n")
        self.assertTrue(table.move("b8", move=3).changed)

    def test_the_score_sheet_opens_with_the_ghosts_row(self):
        table = Table("tictac", GITHUB, HOUSE, ghosts=())
        sheets = [table.board()["history"]]
        table.lay(TT_GHOSTS[:1])
        sheets.append(table.board()["history"])
        table.lay(TT_GHOSTS[1:], HOUSE)
        sheets.append(table.board()["history"])
        for code in TT_FIRST_WINS[:4]:
            table.move(code)
            sheets.append(table.board()["history"])
        ghosts = ["G", "e5", "a1", "@octocat"]
        self.assertEqual(sheets, [
            [["G", "", "", ""]], [["G", "e5", "", "@octocat"]], [ghosts, [1, "", "", ""]],
            [ghosts, [1, "Xb8", "", ""]], [ghosts, [1, "Xb8", "Oe6", "@octocat"], [2, "", "", ""]],
            [ghosts, [1, "Xb8", "Oe6", "@octocat"], [2, "Xd7", "", ""]],
            [[1, "Xb8", "Oe6", "@octocat"], [2, "Xd7", "Oa3", "@octocat"], [3, "", "", ""]]],
            "the ghosts' row first, then the moves, the latest three rows")


class Turns(unittest.TestCase):
    def test_a_mark_is_played_and_the_reply_says_whose_turn_it_is_and_where(self):
        table = Table("tictac", HOUSE, HOUSE)
        outcome = table.move("b8")  # a board's centre: O is sent to the centre board
        self.assertEqual(outcome.comment, "❌ **1. Xb8 is on the board.**\n🔳 *Centre Move*"
                                          " · X takes the centre of the upper left board\nGitHub's turn, in the centre"
                                          f" board: anyone but {LINKED} can pick O's reply on {BOARD}.\n")
        self.assertEqual(outcome.commit, "chore(tictac): ❌ play 1. Xb8 in game 1\n\nMove 3, by tannergolden.")
        self.assertIsNone(PING.search(outcome.comment), "the owner's own move pings nobody")
        self.assertEqual(table.board()["alert"], "centre board")
        outcome = table.move("e6")  # the top edge: X is sent to the top board
        self.assertEqual(outcome.comment, "⭕ **1... Oe6 is on the board.** Well played, @octocat.\n📏 *Edge Move*"
                                          " · O takes the top edge of the centre board\n"
                                          "@tannergolden, it's your move, in the top board.\n")
        self.assertEqual((outcome.issue, outcome.log), (table.issue, "played 1... Oe6"))
        self.assertEqual(table.board()["alert"], "top board")

    def test_a_pentago_reply_names_the_whole_move(self):
        table = Table("pentago", GITHUB, GITHUB)
        outcome = table.move("a1-lr-cw")
        self.assertEqual(outcome.comment, "⚫ **1. a1-lr-cw is on the board.** Well played, @octocat.\n⚫ *Corner Move*"
                                          " · A black marble on a1, then the"
                                          " lower right quarter turns clockwise\n@tannergolden, it's your move.\n")
        self.assertEqual(outcome.commit, "chore(pentago): ⚫ play 1. a1-lr-cw in game 1\n\nMove 3, by octocat.")
        outcome = table.move("d6-lr-acw")
        self.assertEqual(outcome.comment, "⚪ **1... d6-lr-acw is on the board.**\n⚪ *Corner Move*"
                                          " · A white marble on d6, then the lower right quarter"
                                          f" turns anticlockwise\nGitHub's turn: anyone but {LINKED} can pick Black's"
                                          f" reply on {BOARD}.\n")
        element = table.board()
        self.assertNotIn("alert", element, "once the ghosts are down a Pentago turn calls nothing out")
        self.assertEqual(element["last"], {"move": "d6-lr-acw", "words": "A white marble on d6, then the lower right"
                                                                         " quarter turns anticlockwise",
                                           "by": "@tannergolden", "when": page.day(table.clock)})

    def test_the_house_s_turn_is_the_owner_s_alone_whichever_side_opened(self):
        for key, house, github in (("tictac", "X", "O"), ("pentago", "White", "Black")):
            for opens in (HOUSE, GITHUB):
                table = Table(key, GITHUB, opens)
                if opens == GITHUB:
                    table.move(LINES[key][0][0])
                code = LINES[key][0][1 if opens == GITHUB else 0]
                outcome = table.move(code, player=OCTOCAT)
                with self.subTest(key=key, opens=opens):
                    self.assertFalse(outcome.changed)
                    self.assertEqual(outcome.comment, f"⏳ **It's {LINKED}'s turn as {house}**, so `{code}` wasn't"
                                                      f" played.\nGitHub plays {github}: once {house} moves, pick"
                                                      f" {github}'s reply on {BOARD}.\n")
                    self.assertEqual(outcome.log, f"{house}'s turn")
                    self.assertIsNone(PING.search(outcome.comment), "a turn away never pings the owner")

    def test_github_s_turn_is_for_everyone_but_the_owner_whichever_side_opened(self):
        for key, github in (("tictac", "O"), ("pentago", "Black")):
            for opens in (HOUSE, GITHUB):
                table = Table(key, HOUSE, opens)
                if opens == HOUSE:
                    table.move(LINES[key][0][0])
                code = LINES[key][0][1 if opens == HOUSE else 0]
                outcome = table.move(code, player=OWNER)
                with self.subTest(key=key, opens=opens):
                    self.assertFalse(outcome.changed)
                    self.assertEqual(outcome.comment, f"⏳ **It's GitHub's turn as {github}**, so `{code}` wasn't"
                                                      f" played.\n{github}'s moves are for everyone but you. Your turn"
                                                      " comes next.\n")

    def test_the_first_move_to_arrive_is_the_one_played_and_the_rest_are_too_late(self):
        table = Table("tictac", HOUSE, GITHUB)
        first = table.move("b8", move=3)
        late = table.move("c8", player=HUBOT, move=3)
        self.assertTrue(first.changed)
        self.assertEqual(late.comment, "⌛ **Too late: move 3 is already on the board**, so `c8` wasn't played.\n"
                                       "1. Ob8 got there first, played by [@octocat](https://github.com/octocat). Pick"
                                       f" a move from {BOARD} as it stands now.\n")
        self.assertIsNone(PING.search(late.comment), "a turn away pings nobody, not even the player it names")
        self.assertIn("1. Ob8 got there first, played by you.", table.move("c8", player=OCTOCAT, move=3).comment)
        table = Table("pentago", GITHUB, HOUSE)
        table.move("a1-lr-cw")
        self.assertIn("1. a1-lr-cw got there first, played by you.", table.move("a2-lr-cw", player=OWNER,
                                                                                move=3).comment)

    def test_a_move_for_another_game_or_move_is_turned_away(self):
        table = Table("pentago", HOUSE, HOUSE)
        self.assertEqual(table.move("a1-lr-cw", game=2, move=1).comment,
                         f"❓ **There's no game 2 yet**, so `a1-lr-cw` wasn't played.\nGame 1 is under way on {BOARD}:"
                         " pick a move there.\n")
        self.assertEqual(table.move("a1-lr-cw", move=7).comment,
                         f"❓ **The board is on move 3, not move 7**, so `a1-lr-cw` wasn't played.\nPick a move from"
                         f" {BOARD} as it stands now.\n")
        self.assertEqual(games.turns(table.game), [*table.game["ghosts"]])

    def test_an_illegal_move_changes_nothing_and_says_why(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.move("b8")  # O is sent to the centre board
        outcome = table.move("a9")
        self.assertFalse(outcome.changed)
        self.assertEqual(outcome.comment, "🚫 **`a9` isn't a legal move here**: the last mark sent O to the centre"
                                          " board, so it must go there.\nNothing was played. Every move listed under"
                                          f" {BOARD} is legal: pick one there.\n")
        table = Table("pentago", HOUSE, HOUSE)
        table.move("a1-lr-cw")
        self.assertIn("**`a1-ul-cw` isn't a legal move here**: there's already a white marble on a1.\n",
                      table.move("a1-ul-cw").comment)

    def test_a_turned_away_move_pings_nobody(self):
        table = Table("pentago", GITHUB, GITHUB)
        table.move("a1-lr-cw")
        refusals = [table.move("a2-lr-cw", player=OCTOCAT), table.move("a2-lr-cw", player=OWNER, move=3),
                    table.move("a2-lr-cw", move=9), table.move("a2-lr-cw", game=4), table.move("a1-lr-cw"),
                    table.move("a2", player=OWNER)]
        for outcome in refusals:
            self.assertFalse(outcome.changed, outcome.comment)
            self.assertIsNone(PING.search(outcome.comment), outcome.comment)


class Again(unittest.TestCase):
    """A run made over again, such as a re-run of its job, finds its own turn already played: it is told so on its
    issue, as it was the first time, and never that it wasn't played."""

    def test_the_last_turn_run_again_is_answered_as_it_was_and_the_page_drawn_again(self):
        for key in KEYS:
            table = Table(key, HOUSE, GITHUB)
            placed = table.outcomes[2]  # octocat's ghost, the second, and the Arbiter's draw of GitHub to open
            again = table.again(GHOSTS[key][1], 2, placed.issue)
            with self.subTest(key=key, turn="the second ghost"):
                self.assertEqual((again.changed, again.redraw), (False, True))
                self.assertEqual((again.comment, again.issue), (placed.comment, placed.issue))
            played = table.move(LINES[key][0][0])
            again = table.again(LINES[key][0][0], 3, played.issue)
            with self.subTest(key=key, turn="the first move"):
                self.assertEqual((again.changed, again.redraw), (False, True))
                self.assertEqual((again.comment, again.issue), (played.comment, played.issue))

    def test_an_older_turn_run_again_says_it_is_on_the_board(self):
        table = Table("tictac", GITHUB, HOUSE)  # octocat placed the first ghost, from issue 101
        table.move("b8")
        again = table.again("e5", 1, 101)
        self.assertEqual(again.comment, "✅ **G. e5 is already on the board**, played from this issue.\nThe game has"
                                        f" moved on since: pick a move from {BOARD} as it stands now.\n")
        self.assertFalse(again.changed or again.redraw)
        table.move("e6")
        again = table.again("e6", 4, table.issue)
        self.assertTrue(again.redraw)
        again = table.again("b8", 3, table.issue - 1, OWNER, OWNER_ID)
        self.assertEqual(again.comment.splitlines()[0], "✅ **1. Xb8 is already on the board**, played from this"
                                                        " issue.")

    def test_the_move_that_ended_a_game_run_again_says_so(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS)
        again = table.again("i9", 19, table.issue, OWNER, OWNER_ID)
        opens = page.day(page.parse(table.game["started"]))
        self.assertEqual(again.comment, "✅ **9. Xi9# already ended game 1**, played from this issue.\n"
                                        f"Game 2 opens {opens} on {BOARD}.\n")
        self.assertTrue(again.redraw)
        table.fresh()
        table.lay(TT_GHOSTS[:1])
        again = table.again("i9", 19, table.issue - 1, OWNER, OWNER_ID)
        self.assertEqual(again.comment.splitlines()[1], f"Game 2 is under way on {BOARD}.")
        self.assertFalse(again.redraw, "a ghost on the fresh board is the last thing to happen now")


class Endings(unittest.TestCase):
    def test_the_house_wins_tic_tac_and_the_game_is_recorded(self):
        table = Table("tictac", HOUSE, HOUSE)
        outcome = table.play(TT_FIRST_WINS)
        ended = table.clock
        opens = ended + page.DISPLAY
        self.assertEqual(outcome.comment, "🏆 **9. Xi9#: three boards in a row!** @tannergolden wins game 1.\n📐 *Corner Move*"
                                          " · X takes the upper right"
                                          " corner of the upper right board\nIts final board stays up for two days:"
                                          f" game 2 opens {page.day(opens)}, and the Arbiter draws the side that places"
                                          " its first ghost.\n")
        self.assertEqual(outcome.commit, "chore(tictac): 🏆 play 9. Xi9#, ending game 1: X wins\n\nMove 19, by"
                                         " tannergolden.")
        self.assertEqual(outcome.log, "played 9. Xi9#, three boards in a row")
        self.assertEqual(table.hall[-1], {
            "game": 1, "result": "1-0", "reason": "three boards in a row", "winner": OWNER, "plies": 19,
            "started": table.outcomes[0].game["started"], "ended": page.stamp(ended),
            "deciding": {"move": "9. Xi9#", "player": OWNER, "player_id": OWNER_ID, "arbiter": False,
                         "issue": table.issue},
            "players": [{"player": OCTOCAT, "player_id": OCTOCAT_ID, "moves": 9}], "house_moves": 10,
            "final": "........X/XXX....X./...XXXX../.O.OO...O/....G..../........./OO...O..O/........./G........",
            "line": ["a3", "b3", "c3"]})
        self.assertEqual(hall.winner(table.hall[-1], OWNER), HOUSE)
        self.assertEqual({key: value for key, value in table.game.items() if key != "ended"},
                         {"game": 2, "started": page.stamp(opens), "moves": []}, "its draw comes with its start")
        self.assertEqual([g["move"] for g in table.game["ended"]["ghosts"]], list(TT_GHOSTS))
        self.assertEqual([played["move"] for played in table.game["ended"]["moves"]], TT_FIRST_WINS)

    def test_github_wins_and_its_player_takes_a_place_in_the_hall_of_fame(self):
        table = Table("tictac", HOUSE, HOUSE)
        outcome = table.play(TT_SECOND_WINS)
        self.assertTrue(outcome.comment.startswith(
            "🏆 **9... Oi9#: three boards in a row!** GitHub wins game 1, and @octocat takes a place in the [Hall of"
            " Fame](https://github.com/tannergolden) for the winning move.\n"))
        record = table.hall[-1]
        self.assertEqual((record["winner"], record["result"], record["line"], record["plies"]),
                         ("GitHub", "0-1", ["a3", "b3", "c3"], 20))
        self.assertEqual(hall.winner(record, OWNER), OCTOCAT_ID)
        self.assertTrue(outcome.commit.startswith("chore(tictac): 🏆 play 9... Oi9#, ending game 1: O wins\n"))
        table = Table("pentago", HOUSE, GITHUB)
        outcome = table.play(PG_TURNED)
        self.assertTrue(outcome.comment.startswith("🏆 **5. c4-ul-cw#: five in a row!** GitHub wins game 1, and"
                                                   " @octocat takes a place in the [Hall of Fame]"))
        self.assertEqual((table.hall[-1]["winner"], table.hall[-1]["result"]), ("GitHub", "0-1"),
                         "the house's White score first, as chess writes it, whoever moved first")
        self.assertNotIn("own", table.hall[-1]["deciding"])

    def test_every_way_pentago_ends(self):
        cases = {  # the line, the side drawn to open, the deciding move, the result, how, the winner, and its own
            "unturned": (PG_UNTURNED, HOUSE, "5. a5#", "1-0", "five in a row", HOUSE, True),
            "turned": (PG_TURNED, GITHUB, "5. c4-ul-cw#", "0-1", "five in a row", GITHUB, True),
            "for the other": (PG_FOR_THE_OTHER, HOUSE, "5... f5-ul-cw#", "1-0", "five in a row", HOUSE, False),
            "for the other, the house's turn": (PG_FOR_THE_OTHER, GITHUB, "5... f5-ul-cw#", "0-1", "five in a row",
                                                GITHUB, False),
            "five for both": (PG_BOTH, HOUSE, "6. f1-ul-cw", "1/2-1/2", "five for both", None, True),
            "a full board": (PG_FULL, GITHUB, "17... d6-ur-cw", "1/2-1/2", "a full board", None, True),
        }
        for name, (line, opens, deciding, result, how, winner, own) in cases.items():
            table = Table("pentago", GITHUB, opens)
            table.play(line)
            record = table.hall[-1]
            element = table.board()
            with self.subTest(name):
                self.assertEqual((record["deciding"]["move"], record["result"], record["reason"]),
                                 (deciding, result, how))
                self.assertEqual(record["deciding"].get("own", True), own)
                self.assertEqual(record["plies"], len(line) + 2, "the ghosts are turns too")
                self.assertEqual(element["result"], {"winner": winner, "how": how})
                if winner:
                    self.assertEqual((record["line"], element["line"]), (["a1", "a2", "a3", "a4", "a5"],) * 2)
                else:
                    self.assertNotIn("line", record)
                    self.assertNotIn("line", element)
                self.assertEqual(element["last"]["move"], deciding.split()[-1])

    def test_a_win_the_other_side_s_turn_made_counts_for_nobody(self):
        table = Table("pentago", GITHUB, HOUSE)  # the house opens, and GitHub's turn stands White's five up
        outcome = table.play(PG_FOR_THE_OTHER)
        self.assertEqual(outcome.comment, "🏆 **5... f5-ul-cw#: five in a row!** @tannergolden wins game 1 on the other"
                                          " side's move, which counts for nobody.\n⚫ *Edge Move*"
                                          " · A black marble on f5, then the upper left quarter turns"
                                          " clockwise\nIts final board stays up for two days: game 2 opens"
                                          f" {page.day(table.clock + page.DISPLAY)}, and the Arbiter draws the side"
                                          " that sets its first ghost.\n")
        self.assertEqual(outcome.commit, "chore(pentago): 🏆 play 5... f5-ul-cw#, ending game 1: White wins\n\nMove"
                                         " 12, by octocat.")
        record = table.hall[-1]
        self.assertEqual((record["winner"], record["deciding"]["player"], record["deciding"]["own"]),
                         (OWNER, OCTOCAT, False))
        self.assertIsNone(hall.winner(record, OWNER), "nobody's win, though the scoreboard keeps it")
        states = {key: (None, []) for key in hall.GAMES} | {"pentago": (table.game, table.hall)}
        element = hall.element(states, OWNER, OWNER_ID)
        self.assertEqual((element["series"]["pentago"], element["people"]), ([1, 1, 0, 0], []))
        self.assertIn("The move that won it was the other side's, its turn making five for the winner alone, so the"
                      " win counts for nobody.", table.board()["note"])
        table = Table("pentago", HOUSE, GITHUB)  # GitHub opens, and the house's turn stands Black's five up
        outcome = table.play(PG_FOR_THE_OTHER)
        self.assertTrue(outcome.comment.startswith("🏆 **5... f5-ul-cw#: five in a row!** GitHub wins game 1 on the"
                                                   " other side's move, which counts for nobody.\n"))
        self.assertIsNone(hall.winner(table.hall[-1], OWNER))
        self.assertIn("counts for nobody", table.board()["note"])

    def test_tic_tac_is_drawn_once_no_line_of_three_boards_is_left(self):
        table = Table("tictac", HOUSE, GITHUB)
        outcome = table.play(TT_NO_LINE)
        self.assertTrue(outcome.comment.startswith("🤝 **16... Xi7: game 1 is drawn with no line of three boards left"
                                                   " for either side.**\n"))
        self.assertTrue(outcome.commit.startswith("chore(tictac): 🤝 play 16... Xi7, ending game 1: drawn\n"))
        record = table.hall[-1]
        self.assertEqual((record["winner"], record["result"], record["reason"], record["plies"]),
                         (None, "1/2-1/2", "no line left", 34))
        self.assertNotIn("line", record)
        self.assertIn(".", record["final"], "drawn with squares still open")
        self.assertIsNone(hall.winner(record, OWNER))

    def test_the_record_names_the_game_its_days_its_draws_and_who_played_each_turn(self):
        table = Table("tictac", HOUSE, HOUSE)
        name, text = table.play(TT_FIRST_WINS).record
        self.assertEqual(name, "game-1.txt")
        self.assertEqual(text.splitlines()[:4], [
            "Tic-Tac, game 1: @tannergolden against GitHub",
            f"Played from {page.date(T0)} to {page.date(table.clock)}, in EST.",
            "@tannergolden played X and GitHub played O; under the Ghost Rule the Arbiter drew @tannergolden to place"
            " the first ghost and @tannergolden to move first, as X.",
            "@tannergolden won with 9. Xi9#, three boards in a row."])
        self.assertEqual([" ".join(line.split()) for line in text.splitlines()[5:10]],
                         ["G. e5 @tannergolden", "G... a1 @octocat", "1. Xb8 @tannergolden", "1... Oe6 @octocat",
                          "2. Xd7 @tannergolden"])
        self.assertEqual(" ".join(text.splitlines()[-3].split()), "9. Xi9# @tannergolden")
        self.assertTrue(text.endswith("\n\nResult: 1-0, X's score first\n"))
        table = Table("pentago", GITHUB, HOUSE)
        text = table.play(PG_FULL).record[1]
        self.assertIn("@tannergolden played White and GitHub played Black; under the Ghost Rule the Arbiter drew GitHub"
                      " to set the first ghost and @tannergolden to move first, as White.", text)
        self.assertIn("Drawn with 17... d6-ur-cw, on a full board.", text)
        self.assertIn("G. e5 @octocat", [" ".join(line.split()) for line in text.splitlines()])
        self.assertTrue(text.endswith("\nResult: 1/2-1/2, White's score first\n"))
        for dash in DASHES:
            self.assertNotIn(dash, text)


class TwoDays(unittest.TestCase):
    """The owner's rule: a finished game's final board stays up for two days, and then the fresh board comes by
    itself, with the Arbiter's draw of the side that places its first ghost. Nothing can be played meanwhile."""

    def test_the_final_board_shows_how_the_game_ended_and_lists_nothing_to_play(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS)
        opens = page.parse(table.game["started"])
        element = table.board()
        self.assertEqual({key: element[key] for key in ("kind", "places", "opens", "game", "move", "players", "next",
                                                        "next_at")},
                         {"kind": "tictac", "places": HOUSE, "opens": HOUSE, "game": 1, "move": 9, "players": 1,
                          "next": page.day(opens), "next_at": page.stamp(opens)})
        self.assertEqual(element["next_at"], page.stamp(page.parse(table.game["started"])),
                         "the moment the fresh board comes, for the kit's countdown")
        self.assertEqual(list(element), ["kind", "board", "places", "opens", "game", "move", "players", "next",
                                         "next_at", "last", "result", "line", "history", "note"])
        self.assertEqual((element["result"], element["line"]), ({"winner": HOUSE, "how": "three boards in a row"},
                                                                ["a3", "b3", "c3"]))
        self.assertEqual(element["last"], {"move": "Xi9#", "words": "X takes the upper right corner of the upper right"
                                                                    " board", "by": "@tannergolden",
                                           "when": page.day(table.clock)})
        self.assertEqual(element["history"], [[7, "Xa8", "Ob6", "@octocat"], [8, "Xe7", "Of3", "@octocat"],
                                              [9, "Xi9#", "", ""]])
        for missing in ("moves", "due", "alert"):
            self.assertNotIn(missing, element)
        self.assertTrue(element["note"].startswith(f"Game 1 is over, and its final board stays up for two days: game 2"
                                                   f" opens {page.until(opens)}, and nothing can be played until"
                                                   " then."))
        table = Table("pentago", GITHUB, GITHUB)
        table.play(PG_FULL)
        element = table.board()
        self.assertEqual((element["result"], element["opens"], element["places"]),
                         ({"winner": None, "how": "a full board"}, GITHUB, GITHUB))
        self.assertEqual(element["next_at"], page.stamp(page.parse(table.game["started"])))
        self.assertNotIn("line", element)

    def test_a_move_meanwhile_is_told_the_day_the_next_game_opens(self):
        table = Table("pentago", HOUSE, HOUSE)
        table.play(PG_UNTURNED)
        day = page.day(page.parse(table.game["started"]))
        for game, move, code in ((2, 1, "a1"), (2, 3, "a1-lr-cw"), (1, 12, "a1-lr-cw"), (1, 3, "a1-lr-cw"),
                                 (3, 1, "a1")):
            with self.subTest(game=game, move=move):
                outcome = table.move(code, player=OCTOCAT, game=game, move=move)
                self.assertEqual(outcome.comment, f"⏳ **Game 2 opens {day}**, so `{code}` wasn't played.\nGame 1's"
                                                  f" final board stays up until then: pick a move from {BOARD} once"
                                                  " game 2 is on it.\n")
                self.assertFalse(outcome.changed)

    def test_the_fresh_board_comes_by_itself_with_the_arbiter_s_draw(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS)
        opens = page.parse(table.game["started"])
        before = table.wait(opens - table.clock - MINUTE)
        self.assertFalse(before.changed)
        self.assertEqual(before.log, f"game 1's final board is up until {page.stamp(opens)}")
        came = table.wait(MINUTE)
        places = games.pick([HOUSE, GITHUB], f"tictac:2:places:{page.stamp(opens)}")
        self.assertTrue(came.changed)
        self.assertEqual(table.game, {"game": 2, "started": page.stamp(opens), "places": places, "ghosts": [],
                                      "moves": []})
        placer = OWNER if places == HOUSE else "GitHub"
        self.assertEqual(came.commit.splitlines()[0], f"chore(tictac): 🎲 start game 2, {placer} to place the first"
                                                      " ghost")
        self.assertEqual(came.log, f"the Arbiter drew {named(places)} to place game 2's first ghost; the side to move"
                                   f" has until {page.stamp(opens + page.WEEK)}")
        self.assertEqual((came.comment, came.issue), ("", None), "a draw answers no issue")
        element = table.board()
        self.assertNotIn("result", element)
        self.assertEqual((element["game"], element["due"], element["alert"], element["places"]),
                         (2, page.day(opens + page.WEEK), "place a ghost", places))
        self.assertTrue(element["note"].startswith(f"@{OWNER} won game 1. {table.mod.OPENS_NOTE.format(owner=OWNER)}"),
                        element["note"])
        over = table.move("a1", player=OCTOCAT, game=1, move=20)
        self.assertEqual(over.comment, "⌛ **Game 1 is over**, so `a1` wasn't played.\nGame 2 is under way on"
                                       f" {BOARD}: pick a move there.\n", "once game 2 is on the board")
        self.assertFalse(over.changed)

    def test_a_ghost_after_the_start_finds_the_draw_made_before_the_clock_comes(self):
        for right in (True, False):
            table = Table("pentago", HOUSE, HOUSE)
            table.play(PG_UNTURNED)
            opens = page.parse(table.game["started"])
            places = games.pick([HOUSE, GITHUB], f"pentago:2:places:{page.stamp(opens)}")
            table.clock = opens  # the moment the board comes, before the clock's next run
            sender = places if right else other(places)
            player, player_id = (OWNER, OWNER_ID) if sender == HOUSE else (HUBOT, HUBOT_ID)
            outcome = table.move("b5", player=player, player_id=player_id, game=2, move=1, after=5 * MINUTE)
            with self.subTest(right=right):
                self.assertTrue(outcome.changed, "the draw is saved, whether or not the ghost is played")
                self.assertEqual((table.game["game"], table.game["places"]), (2, places))
                if right:
                    self.assertEqual([g["move"] for g in table.game["ghosts"]], ["b5"])
                    self.assertTrue(outcome.commit.endswith(f"\n\nMove 1, by {player}. The Arbiter drew"
                                                            f" {OWNER if places == HOUSE else 'GitHub'} to set the"
                                                            " first ghost."))
                else:
                    self.assertEqual(table.game["ghosts"], [])
                    self.assertTrue(outcome.comment.startswith("⏳ **It's "), outcome.comment)
                    self.assertTrue(outcome.commit.startswith("chore(pentago): 🎲 start game 2, "))

    def test_the_next_board_says_how_the_last_game_ended_until_its_first_move(self):
        # The sentence is said in full whenever it fits in the note's one line beside everything that must be said,
        # and in short where it doesn't, and the first move takes it away: GitHub's turns always leave it room, and
        # the house's leave a draw's how none in Pentago, nor in Tic-Tac's draw with no line left.
        short = "Game 1 was drawn."
        for key, line, opens, said in (("tictac", TT_FIRST_WINS, HOUSE, f"@{OWNER} won game 1."),
                                       ("tictac", TT_NO_LINE, HOUSE, "Game 1 was drawn with no line of three boards"
                                                                     " left for either side."),
                                       ("pentago", PG_BOTH, HOUSE, "Game 1 was drawn with five for both sides."),
                                       ("pentago", PG_FULL, GITHUB, "Game 1 was drawn on a full board."),
                                       ("pentago", PG_FOR_THE_OTHER, HOUSE, f"@{OWNER} won game 1.")):
            table = Table(key, HOUSE, opens)
            table.play(line)
            table.fresh()
            notes = []
            for ghost in GHOSTS[key]:
                notes.append((table.side(), table.board()["note"]))
                table.lay((ghost,))
            notes.append((table.side(), table.board()["note"]))
            table.move(LINES[key][0][0])
            with self.subTest(key=key, said=said):
                self.assertEqual(table.board()["game"], 2)
                for side, note in notes:
                    if note.startswith(f"{said} "):
                        continue
                    self.assertTrue(note.startswith(f"{short} "), note)
                    self.assertGreater(len(f"{said} {note[len(short) + 1:]}"), page.NOTE, note)
                    self.assertEqual(side, HOUSE, "GitHub's turns leave it room")
                self.assertTrue(any(side == GITHUB for side, _ in notes))
                self.assertNotIn(said, table.board()["note"], "the first move takes it away")
                self.assertFalse(table.board()["note"].startswith(short), "the first move takes it away")


class Clock(unittest.TestCase):
    def test_a_side_has_a_whole_week_then_the_arbiter_moves_for_it(self):
        table = Table("tictac", HOUSE, HOUSE)  # octocat's ghost, the second, went down from issue 102
        self.assertFalse(table.wait(page.WEEK - dt.timedelta(seconds=1)).changed)
        outcome = table.wait(dt.timedelta(seconds=1))
        self.assertTrue(outcome.changed)
        played = table.game["moves"][-1]
        self.assertEqual((played["arbiter"], played["player"], played["issue"]), (True, None, None))
        self.assertRegex(outcome.comment, r"^⏰ \*\*A week passed without a move from \[@tannergolden\]"
                                          r"\([^)]+\)\*\*, so the Arbiter played 1\. X[a-i][1-9] for X, at"
                                          r" random\.\n\S+ \*[^*]+\* · X takes [^\n]+\nGitHub's turn, in the [a-z ]+"
                                          r" board: anyone but")
        self.assertEqual((outcome.issue, outcome.logbook), (102, False), "told on the issue of the turn it answers")
        self.assertIsNone(PING.search(outcome.comment), "the owner's own lapse goes to GitHub's player, unpinged")
        self.assertTrue(outcome.commit.startswith("chore(tictac): ⏰ play 1. X"))
        self.assertIn("after a week without a move\n\nMove 3 of game 1, by the Arbiter.", outcome.commit)
        self.assertEqual(table.board()["history"][-1][1:], [played["shown"], "", ""])

    def test_a_week_without_a_ghost_brings_the_arbiter_s_at_random(self):
        for key in KEYS:
            mod = games.rules(key)
            table = Table(key, GITHUB, ghosts=())  # GitHub's ghost, the first: nobody's issue to tell
            outcome = table.wait(page.WEEK)
            ghost = table.game["ghosts"][0]
            code = ghost["move"]
            name = next(entry for entry in mod.ghost_listing(()) if entry["code"] == code)
            word = mod.WORDS[GITHUB]
            with self.subTest(key=key, ghost="the first"):
                self.assertEqual((ghost["arbiter"], ghost["at"]), (True, page.stamp(table.clock)))
                self.assertEqual(outcome.comment, f"⏰ **A week passed without a ghost from GitHub**, so the Arbiter"
                                                  f" {mod.GHOSTS[3]} G. {code} for {word}, at random.\n\n👻 **G."
                                                  f" {code} is on the board.**\n👻 *{name['title']}* ·"
                                                  f" {name['words']}\n"
                                                  f"@tannergolden, it's your turn to {mod.GHOSTS[0]} a ghost.\n")
                self.assertEqual((outcome.issue, outcome.logbook), (None, True))
                self.assertEqual(outcome.commit, f"chore({key}): 👻 {mod.GHOSTS[0]} G. {code} for {word} in game 1"
                                                 " after a week without one\n\nMove 1 of game 1, by the Arbiter.")
                self.assertEqual(table.board()["history"], [["G", code, "", "the Arbiter"]])
            table = Table(key, HOUSE, ghosts=GHOSTS[key][:1])  # the owner's ghost from issue 101, then GitHub's due
            outcome = table.wait(page.WEEK)
            code = table.game["ghosts"][1]["move"]
            opens = table.game["opens"]
            with self.subTest(key=key, ghost="the second"):
                self.assertNotEqual(code, GHOSTS[key][0])
                self.assertEqual((outcome.issue, outcome.logbook), (101, False))
                self.assertIn(f"\n🎲 Both ghosts are down, so the Arbiter drew the side that moves first:"
                              f" {named(opens)}, as {mod.WORDS[opens]}.\n", outcome.comment)
                self.assertTrue(outcome.commit.startswith(f"chore({key}): 👻 {mod.GHOSTS[0]} G... {code} for {word}"
                                                          " in game 1 after a week without one, drawing"
                                                          f" {OWNER if opens == HOUSE else 'GitHub'} to open\n\nMove 2"
                                                          " of game 1"))
                self.assertEqual(outcome.log, f"the Arbiter {mod.GHOSTS[3]} G... {code}, drawing {opens} to open")
                self.assertIn(code, mod.ghost_cells(GHOSTS[key][:1]))

    def test_a_fresh_board_left_a_week_gets_its_draw_and_the_arbiter_s_ghost_in_one_run(self):
        # Nobody ran the clock from the end of game 1 until a week after game 2's board came: the one run draws the
        # side that places first and places its ghost, and tells the issue of the move that ended game 1.
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS)
        ended_on = table.issue
        opens = page.parse(table.game["started"])
        outcome = table.wait(opens - table.clock + page.WEEK + HOUR)
        places, ghost = table.game["places"], table.game["ghosts"][0]
        self.assertEqual((table.game["game"], ghost["arbiter"], ghost["at"]), (2, True, page.stamp(table.clock)))
        self.assertEqual(places, games.pick([HOUSE, GITHUB], f"tictac:2:places:{page.stamp(opens)}"))
        self.assertEqual((outcome.issue, outcome.logbook), (ended_on, False))
        self.assertEqual(outcome.log, f"the Arbiter drew {named(places)} to place game 2's first ghost; the Arbiter"
                                      f" placed G. {ghost['move']}")
        self.assertIn("\n\nMove 1 of game 2, by the Arbiter. The Arbiter first drew ", outcome.commit)
        self.assertTrue(outcome.commit.endswith(" to place the first ghost."))
        self.assertTrue(outcome.comment.startswith("⏰ **A week passed without a ghost from "))

    def test_the_arbiter_after_itself_writes_in_the_logbook_and_pings_the_owner_on_their_turn(self):
        table = Table("pentago", HOUSE, GITHUB)  # the owner's ghost, then octocat's from issue 102, and GitHub opens
        first = table.wait(page.WEEK)  # GitHub's lapse, after a player's ghost: on that player's issue
        self.assertEqual((first.issue, first.logbook), (102, False))
        self.assertTrue(first.comment.endswith("\n@tannergolden, it's your move.\n"))
        second = table.wait(page.WEEK)  # the house's lapse, after the Arbiter's own move: the logbook
        self.assertEqual((second.issue, second.logbook), (None, True))
        self.assertIsNone(PING.search(second.comment), "GitHub's turn pings nobody, even in the logbook")
        third = table.wait(page.WEEK)
        self.assertEqual((third.issue, third.logbook), (None, True))
        self.assertTrue(third.comment.endswith("\n@tannergolden, it's your move.\n"))

    def test_the_arbiter_s_pick_is_the_same_however_often_it_is_asked(self):
        for key in KEYS:
            for ghosts in ((), GHOSTS[key]):
                table = Table(key, GITHUB, GITHUB, ghosts=ghosts)
                later = table.clock + dt.timedelta(days=9)
                first = games.tick(table.mod, table.game, table.hall, OWNER, later)
                second = games.tick(table.mod, table.game, table.hall, OWNER, later + HOUR)
                self.assertEqual(games.turns(first.game)[-1]["move"], games.turns(second.game)[-1]["move"])

    def test_a_win_the_arbiter_played_counts_for_nobody_and_the_final_board_says_so(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS[:-1])
        before = table.game
        positions = games.replay(table.mod, before)
        arbiter = {"player": None, "player_id": None, "issue": None, "arbiter": True}
        outcome, shown, end = games.apply(table.mod, before, table.hall, positions, "i9", arbiter, OWNER, table.clock)
        table.keep(outcome)
        ended = {**before, "moves": [*before["moves"], {"move": "i9"}]}
        text = games.ended_text(table.mod, ended, end, shown, arbiter, OWNER, "name", table.clock)
        self.assertTrue(text.startswith("🏆 **9. Xi9#: three boards in a row!** @tannergolden wins game 1 on the"
                                        " Arbiter's move."))
        self.assertIn("The winning move was the Arbiter's, played after a week without one, so the win counts for"
                      " nobody.", table.board()["note"])
        self.assertIsNone(hall.winner(table.hall[-1], OWNER))
        self.assertIn("\n9. Xi9#    the Arbiter, after a week\n", outcome.record[1])


class Replay(unittest.TestCase):
    """A game won by a person's own move gets a replay (replays.py): every turn, its ghosts first, with what it did,
    who played it and when, written beside the game's record for tannergolden/play's Replay workflow, and linked from
    the final board. A draw gets none, and nor does a win the Arbiter's move made or a Pentago turn that made five for
    the side that did not turn."""

    def test_a_person_s_win_gets_a_replay_of_every_turn_its_ghosts_first(self):
        for key, line, places, opens, winner in (("tictac", TT_FIRST_WINS, HOUSE, HOUSE, HOUSE),
                                                 ("tictac", TT_SECOND_WINS, GITHUB, HOUSE, GITHUB),
                                                 ("pentago", PG_TURNED, GITHUB, GITHUB, GITHUB),
                                                 ("pentago", PG_UNTURNED, HOUSE, GITHUB, GITHUB)):
            table = Table(key, places, opens)
            name, facts = table.play(line).replay
            game, record = table.game["ended"], table.hall[-1]
            turns = games.turns(game)
            sides = [games.side_of(table.mod, game, turn) for turn in range(1, len(turns) + 1)]
            plies = facts["plies"]
            with self.subTest(key=key, places=places, opens=opens):
                self.assertEqual(name, "game-1.replay.json")
                self.assertEqual({k: facts[k] for k in ("replay", "kind", "game", "winner", "by", "by_id", "issue",
                                                        "reason", "line", "started", "ended", "places", "opens",
                                                        "final", "players", "house_moves")},
                                 {"replay": 1, "kind": key, "game": 1, "winner": winner,
                                  "by": OWNER if winner == HOUSE else OCTOCAT,
                                  "by_id": OWNER_ID if winner == HOUSE else OCTOCAT_ID,
                                  "issue": record["deciding"]["issue"], "reason": record["reason"],
                                  "line": record["line"], "started": game["started"], "ended": record["ended"],
                                  "places": places, "opens": opens, "final": record["final"],
                                  "players": record["players"], "house_moves": record["house_moves"]})
                self.assertEqual([ply["side"] for ply in plies], sides, "every turn, the ghosts first")
                self.assertEqual([(ply["by"], ply["by_id"]) for ply in plies],
                                 [(turn["player"], turn["player_id"]) for turn in turns])
                self.assertEqual([ply["when"] for ply in plies], [page.day(page.parse(turn["at"])) for turn in turns])
                self.assertEqual([ply["notation"] for ply in plies[:2]], [f"G. {GHOSTS[key][0]}",
                                                                          f"G... {GHOSTS[key][1]}"])
                self.assertEqual(plies[-1]["notation"], record["deciding"]["move"])
                self.assertTrue(plies[-1]["move"].endswith("#") and plies[-1]["notation"].endswith("#"))
                self.assertEqual([ply["notation"] for ply in plies if "#" in ply["notation"]], [plies[-1]["notation"]])
                letters = {HOUSE: "X", GITHUB: "O"}
                for ply, turn, side in zip(plies, turns, sides):
                    ghost = ply["notation"].startswith("G")
                    if key == "tictac":
                        self.assertEqual((ply["cell"], ply["mark"]), (turn["move"], "G" if ghost else letters[side]))
                    elif ghost:
                        self.assertEqual((ply["cell"], ply["ghost"]), (turn["move"], True))
                    else:
                        self.assertEqual([ply["cell"], ply["quarter"], ply["way"]], turn["move"].split("-"))
                        self.assertEqual(ply["unturned"], ply is plies[-1] and line is PG_UNTURNED)
                self.assertIn(f" 🎬 [Watch the replay](https://github.com/tannergolden/play/blob/HEAD/replays/{key}/"
                              "game-1.md) of every move.", table.board()["note"])

    def test_the_final_board_s_note_links_the_replay_after_how_the_game_ended(self):
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS)
        note = table.board()["note"]
        opens = page.until(page.parse(table.game["started"]))
        self.assertEqual(note, f"Game 1 is over, and its final board stays up for two days: game 2 opens {opens}, and"
                               " nothing can be played until then. 🎬 [Watch the replay](https://github.com/"
                               "tannergolden/play/blob/HEAD/replays/tictac/game-1.md) of every move. Every finished"
                               " game is kept as a [record](https://github.com/tannergolden/tannergolden/tree/HEAD/"
                               ".github/tictac/games).")
        self.assertTrue(KIT_LINE.fullmatch(note) and not KIT_BLOCK.match(note), note)

    def test_a_draw_and_a_win_that_is_nobody_s_get_no_replay_and_no_link(self):
        for key, line, opens in (("tictac", TT_NO_LINE, GITHUB), ("pentago", PG_BOTH, HOUSE),
                                 ("pentago", PG_FULL, GITHUB), ("pentago", PG_FOR_THE_OTHER, HOUSE)):
            table = Table(key, HOUSE, opens)
            outcome = table.play(line)
            with self.subTest(key=key, how=table.hall[-1]["reason"], own=table.hall[-1]["deciding"].get("own")):
                self.assertIsNone(outcome.replay)
                self.assertNotIn("Watch the replay", table.board()["note"])
        table = Table("tictac", HOUSE, HOUSE)
        table.play(TT_FIRST_WINS[:-1])
        arbiter = {"player": None, "player_id": None, "issue": None, "arbiter": True}
        outcome, _, _ = games.apply(table.mod, table.game, table.hall, games.replay(table.mod, table.game), "i9",
                                    arbiter, OWNER, table.clock)
        table.keep(outcome)
        self.assertIsNone(outcome.replay, "a win the Arbiter's move made")
        self.assertNotIn("Watch the replay", table.board()["note"])
        with tempfile.TemporaryDirectory() as temp:
            games.save(Path(temp), outcome)
            self.assertEqual(sorted(path.name for path in (Path(temp) / "games").iterdir()), ["game-1.txt"])


class Board(unittest.TestCase):
    """What each game's element is given, all along its lines."""

    def boards(self):
        """Every board along every line of both games, every way round: its ghosts, each move, the final board and
        the fresh one, with the table it was set out from."""
        for key in KEYS:
            for line in LINES[key]:
                for places, opens in SIDES:
                    table = Table(key, places, opens, ghosts=())
                    yield table.board(), table
                    for ghost in GHOSTS[key]:
                        table.lay((ghost,), opens)
                        yield table.board(), table
                    for code in line:
                        table.move(code)
                        yield table.board(), table
                    table.fresh()
                    yield table.board(), table

    def every_kind(self):
        """A board of every kind in all four games, each with its game and its kind. The Arbiter plays this engine's
        three games alone, a turn a week, from the first run to the next game's fresh board; in chess the house opens
        and GitHub mates, and the Arbiter opens the next game after a week without a move."""
        for key in games.GAMES:
            mod, moment = games.rules(key), T0
            game, hall_ = games.tick(mod, None, [], OWNER, moment).game, []
            while not hall_:
                ghosts, moves = len(games.ghosts_of(game)), len(game["moves"])
                kind = ("a turn" if moves else "a fresh board" if not ghosts else "a ghost down" if ghosts == 1
                        else "both ghosts down")
                yield key, kind, games.board(mod, game, hall_, OWNER, moment)
                moment += page.WEEK
                outcome = games.tick(mod, game, hall_, OWNER, moment)
                game, hall_ = outcome.game, outcome.hall
            yield key, "a final board", games.board(mod, game, hall_, OWNER, moment)
            yield key, "a fresh board", games.board(mod, game, hall_, OWNER, moment + page.DISPLAY)
        game, hall_, moment = None, [], T0
        yield "chess", "a fresh board", chess.board(game, hall_, OWNER, moment)
        for ply, uci in enumerate(FOOLS_MATE, 1):
            player = (OWNER, OWNER_ID) if ply % 2 else (OCTOCAT, OCTOCAT_ID)
            moment += HOUR
            outcome = chess.play(game, hall_, chess.Request(uci, 1, ply, 100 + ply, *player), OWNER, OWNER_ID, moment)
            game, hall_ = outcome.game, outcome.hall
            yield "chess", "a final board" if hall_ else "a turn", chess.board(game, hall_, OWNER, moment)
        moment = page.parse(game["started"])
        yield "chess", "a fresh board", chess.board(game, hall_, OWNER, moment)
        moment += page.WEEK
        outcome = chess.tick(game, hall_, OWNER, moment)
        yield "chess", "a turn", chess.board(outcome.game, outcome.hall, OWNER, moment)

    def test_every_legal_move_is_listed_once_behind_a_link_that_plays_it(self):
        for key in KEYS:
            table = Table(key, GITHUB, GITHUB, ghosts=())
            for turn, code in enumerate([*GHOSTS[key], *LINES[key][0][:3]], 1):
                element = table.board()
                titles = [title_of(url) for entry in element["moves"] for url in links(entry)]
                found = [INTAKE[key].fullmatch(title) for title in titles]
                self.assertTrue(all(found), titles)
                if games.ghosting(table.mod, table.game):
                    want = table.mod.ghost_cells([g["move"] for g in table.game["ghosts"]])
                else:
                    want = table.mod.legal(games.replay(table.mod, table.game)[-1])
                self.assertEqual([link["move"] for link in found], want)
                self.assertEqual({(link["game"], link["ply"]) for link in found}, {("1", str(turn))})
                self.assertEqual(len({entry[2] for entry in element["moves"]}), len(element["moves"]),
                                 "each move once, by its own notation")
                if key == "pentago" and turn > 2:
                    self.assertTrue(all([[q, w] for q, w, _ in entry[4]] == TURNS for entry in element["moves"]))
                    self.assertEqual(len(titles), 8 * len(element["moves"]), "each hole once, with its eight turns")
                side = games.side_of(table.mod, table.game, turn)
                player, player_id = (OWNER, OWNER_ID) if side == HOUSE else (OCTOCAT, OCTOCAT_ID)
                for link in found:
                    request = games.Request(link["move"], 1, turn, 7, player, player_id)
                    played = games.play(table.mod, table.game, table.hall, request, OWNER, OWNER_ID, table.clock)
                    self.assertTrue(played.changed, (key, turn, link["move"], played.comment))
                if turn == 2:
                    table.lay((code,), GITHUB)
                else:
                    table.move(code)

    def test_what_the_readme_carries_is_text_the_kit_accepts(self):
        for element, table in self.boards():
            key = table.key
            with self.subTest(key=key, game=element["game"], move=element["move"], board=element["board"]):
                self.assertEqual(element["kind"], key)
                self.assertRegex(element["board"], KIT_BOARD[key])
                self.assertIn(element["places"], (HOUSE, GITHUB))
                for gone in ("x", "light", "dark", "threats", "outlook", "prompt"):
                    self.assertNotIn(gone, element)
                letters = KIT_LETTERS[key]
                counts = {side: element["board"].count(letter) for side, letter in letters.items()}
                ghosts = element["board"].count("G")
                if ghosts < 2:
                    self.assertEqual((sum(counts.values()), "opens" in element), (0, False), element)
                else:  # the opener's mark or colour has as many on the board as the other's, or one more
                    opens = element["opens"]
                    self.assertIn(counts[opens] - counts[other(opens)], (0, 1), element["board"])
                note = element["note"]
                self.assertTrue(KIT_LINE.fullmatch(note) and not KIT_BLOCK.match(note), note)
                self.assertNotIn("![", note)
                for i, row in enumerate(element["history"]):
                    self.assertTrue(len(row) == 4 and (row[0] == "G" and i == 0 or isinstance(row[0], int)
                                                       and row[0] >= 1), row)
                    self.assertTrue(all(cell == "" or KIT_MOVE[key].fullmatch(cell) for cell in row[1:3]), row)
                    self.assertTrue(row[3] == "" or KIT_WHO.fullmatch(row[3]), row)
                    self.assertFalse(row[2] and not row[1], row)
                if "last" in element:
                    self.assertRegex(element["last"]["move"], KIT_MOVE[key])
                    self.assertRegex(element["last"]["words"], KIT_WORDS)
                    self.assertRegex(element["last"]["by"], KIT_WHO)
                    self.assertRegex(element["last"]["when"], KIT_DAY)
                if "result" in element:
                    how = element["result"]["how"]
                    self.assertTrue(KIT_HOW.fullmatch(how) and how in KIT_ENDS[key], how)
                    self.assertEqual(element["result"]["winner"] is not None, KIT_ENDS[key][how])
                    self.assertRegex(element["next"], KIT_DAY)
                    self.assertRegex(element["next_at"], KIT_MOMENT)
                    for missing in ("moves", "due", "alert"):
                        self.assertNotIn(missing, element)
                else:
                    self.assertRegex(element["due"], KIT_DAY)
                    self.assertNotIn("next_at", element)
                    self.assertTrue(element["moves"])
                    if ghosts < 2 or key == "tictac":
                        self.assertIn(element["alert"], KIT_ALERTS[key])
                    else:
                        self.assertNotIn("alert", element, "a Pentago turn calls nothing out")
                for entry in element.get("moves", []):
                    emoji, title, notation, words, link = entry
                    self.assertRegex(emoji, KIT_EMOJI)
                    self.assertRegex(title, KIT_TITLE)
                    self.assertTrue(KIT_MOVE[key].fullmatch(notation) and KIT_OFFER[key].fullmatch(notation),
                                    notation)
                    self.assertRegex(words, KIT_WORDS)
                    if isinstance(link, list):
                        self.assertEqual([[q, w] for q, w, _ in link], TURNS)
                        for q, w, url in link:
                            self.assertRegex(url, KIT_LINK[key])
                            self.assertEqual(INTAKE[key].fullmatch(title_of(url))["move"], f"{notation}-{q}-{w}")
                    else:
                        self.assertRegex(link, KIT_LINK[key])

    def test_no_board_in_any_game_carries_a_banner(self):
        """A board's own picture says whose turn it is and by when, the last move, a check or a jump to take, and a
        finished game's result and the day the next one opens, so the README carries no banner over it: no game's
        element has a `prompt`, whatever kind of board it is."""
        seen = set()
        for key, kind, element in self.every_kind():
            seen.add((key, kind))
            with self.subTest(key=key, kind=kind, game=element["game"], move=element["move"]):
                self.assertNotIn("prompt", element)
        ghostly = ("a fresh board", "a ghost down", "both ghosts down", "a turn", "a final board")
        self.assertEqual(seen, {(key, kind) for key in KEYS for kind in ghostly}
                         | {(key, kind) for key in ("checkers", "chess")
                            for kind in ("a fresh board", "a turn", "a final board")})

    def test_the_score_sheet_names_who_chose_github_s_moves_whichever_side_opened(self):
        for opens, sheet in ((HOUSE, [["G", "e5", "a1", "@octocat"], [1, "Xb8", "Oe6", "@octocat"],
                                      [2, "Xd7", "", ""]]),
                             (GITHUB, [["G", "e5", "a1", "@octocat"], [1, "Ob8", "Xe6", "@octocat"],
                                       [2, "Od7", "", "@octocat"]])):
            table = Table("tictac", HOUSE, opens)
            table.play(TT_FIRST_WINS[:3])
            self.assertEqual(table.board()["history"], sheet)

    def test_no_board_says_who_wins_or_where_a_side_could_win_next(self):
        for key in KEYS:
            for line in LINES[key][:2]:
                table = Table(key, HOUSE, GITHUB)
                for code in line[:-1]:
                    table.move(code)
                    element = table.board()
                    with self.subTest(key=key, code=code):
                        for hint in ("threats", "outlook"):
                            self.assertNotIn(hint, element)
                        self.assertIn(element.get("alert", ""), (*KIT_ALERTS["tictac"][1:], "")
                                      if key == "tictac" else ("",))
                        self.assertNotRegex(element["note"], r"(?i)block|threat")
                        self.assertFalse([row for row in element["moves"] if row[2].endswith(("+", "#"))])
                        self.assertFalse([row for row in element["history"] if "+" in row[1] + row[2]])

    def test_the_move_that_won_keeps_its_hash_but_reads_as_any_other_while_it_is_still_to_play(self):
        # offered, the move that would win is written as any other move is; played, the sheet, the last move and the
        # reply write it with its `#`, as a score sheet writes a mate
        for key, line, offered, won in (("tictac", TT_FIRST_WINS, "Xi9", "Xi9#"), ("pentago", PG_UNTURNED, "a5", "a5#"),
                                        ("pentago", PG_TURNED, "c4", "c4-ul-cw#")):
            table = Table(key, HOUSE, HOUSE)
            table.play(line[:-1])
            listed = [row[2] for row in table.board()["moves"]]
            outcome = table.move(line[-1])
            element = table.board()
            with self.subTest(key=key, won=won):
                self.assertIn(offered, listed)
                self.assertFalse([code for code in listed if code.endswith(("+", "#"))])
                self.assertEqual(element["last"]["move"], won)
                self.assertEqual([cell for row in element["history"] for cell in row[1:3] if "#" in cell], [won])
                self.assertIn(won, outcome.comment)

    def test_no_reply_commit_record_or_note_has_a_long_dash_a_side_word_or_a_why(self):
        texts = []
        for element, table in self.boards():
            texts += [element["note"], *table.texts]
            table.texts = []  # each reply and commit once
        for dash in DASHES:
            self.assertNotIn(dash, "".join(texts))
        for text in texts:
            self.assertNotRegex(unsaid(text), SIDE_WORDS)
            self.assertNotRegex(text, WHY)


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

    def test_the_clock_draws_the_first_game_and_a_ghost_is_placed_and_answered(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "tictac"
            moment = drawn_at("tictac:1:places:", HOUSE, T0)
            code, out = self.run_script("tictac", folder, page.stamp(moment))
            self.assertEqual(code, 0)
            saved = json.loads((folder / "game.json").read_text(encoding="utf-8"))
            self.assertEqual(saved, {"game": 1, "started": page.stamp(moment), "places": HOUSE, "ghosts": [],
                                     "moves": []})
            self.assertTrue((out / "commit.txt").read_text(encoding="utf-8").startswith(
                "chore(tictac): 🎲 start game 1, tannergolden to place the first ghost\n\n"))
            self.assertEqual((out / "comment.md").read_text(encoding="utf-8"), "")
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=true\nissue=\nlogbook=false\nreplay=false\n")
            settings = (Path(temp) / "markdown.yaml").read_text(encoding="utf-8")
            empty = "/".join(["........."] * 9)
            self.assertIn(f'  # tictac:start\n  tictac:\n    kind: "tictac"\n    board: "{empty}"\n'
                          '    places: "house"\n    game: 1\n', settings)
            self.assertIn('    alert: "place a ghost"\n    history:\n      - ["G", "", "", ""]\n', settings)
            self.assertIn("  # hall:start\n  hall-of-fame:\n", settings)
            self.assertIn('    series: {"tictac": [0, 0, 0, 0], "pentago": [0, 0, 0, 0], "checkers": [0, 0, 0, 0],'
                          ' "chess": [0, 0, 0, 0]}\n', settings)
            self.assertTrue(settings.endswith("  # hall:end\n\ntrophies:\n  style: trophy\n"),
                            "the regions go at the end of elements:, before the next section")
            (Path(temp) / "output.txt").unlink()
            code, out = self.run_script("tictac", folder, page.stamp(moment + HOUR), MOVE="e5", GAME="1",
                                        MOVE_NUMBER="1", ISSUE="12", PLAYER=OWNER, PLAYER_ID=str(OWNER_ID))
            self.assertEqual(code, 0)
            self.assertIn("G. e5 is on the board", (out / "comment.md").read_text(encoding="utf-8"))
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=true\nissue=12\nlogbook=false\nreplay=false\n")
            self.assertTrue((out / "commit.txt").read_text(encoding="utf-8").endswith(
                "\n\nRun: https://github.com/tannergolden/tannergolden/actions/runs/1\n"))
            self.assertEqual(json.loads((folder / "game.json").read_text(encoding="utf-8"))["ghosts"][0]["move"],
                             "e5")

    def test_a_turned_away_ghost_saves_nothing_and_still_replies(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "pentago"
            moment = drawn_at("pentago:1:places:", HOUSE, T0)
            self.run_script("pentago", folder, page.stamp(moment))
            before = (folder / "game.json").read_text(encoding="utf-8")
            (Path(temp) / "output.txt").unlink()
            code, out = self.run_script("pentago", folder, page.stamp(moment + HOUR), MOVE="b5", GAME="1",
                                        MOVE_NUMBER="1", ISSUE="13", PLAYER=OCTOCAT, PLAYER_ID=str(OCTOCAT_ID))
            self.assertEqual(code, 0)
            self.assertEqual((folder / "game.json").read_text(encoding="utf-8"), before)
            self.assertEqual((out / "comment.md").read_text(encoding="utf-8"),
                             f"⏳ **It's {LINKED}'s turn to set a ghost**, so `b5` wasn't played.\nOnce {LINKED}'s"
                             f" ghost is down, pick a hole for GitHub's on {BOARD}.\n")
            self.assertEqual((Path(temp) / "output.txt").read_text(encoding="utf-8"),
                             "changed=false\nissue=13\nlogbook=false\nreplay=false\n")

    def test_a_game_won_by_a_person_s_move_saves_its_replay_beside_its_record_and_says_so(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "pentago"
            moment = drawn_at("pentago:1:places:", HOUSE, T0)
            self.run_script("pentago", folder, page.stamp(moment))
            for turn, code in enumerate([*PG_GHOSTS, *PG_UNTURNED], 1):
                game = json.loads((folder / "game.json").read_text(encoding="utf-8"))
                side = games.side_of(games.rules("pentago"), game, turn)
                moment = drawn_at("pentago:1:opens:", HOUSE, moment + HOUR) if turn == 2 else moment + HOUR
                player, player_id = (OWNER, OWNER_ID) if side == HOUSE else (OCTOCAT, OCTOCAT_ID)
                status, out = self.run_script("pentago", folder, page.stamp(moment), MOVE=code, GAME="1",
                                              MOVE_NUMBER=str(turn), ISSUE=str(30 + turn), PLAYER=player,
                                              PLAYER_ID=str(player_id))
                self.assertEqual(status, 0, (out / "comment.md").read_text(encoding="utf-8"))
            self.assertTrue((folder / "games" / "game-1.txt").exists())
            facts = json.loads((folder / "games" / "game-1.replay.json").read_text(encoding="utf-8"))
            self.assertEqual((facts["kind"], facts["game"], facts["winner"], facts["by"], facts["issue"]),
                             ("pentago", 1, HOUSE, OWNER, 41))
            self.assertEqual([ply["notation"] for ply in facts["plies"]][:3], ["G. e5", "G... e2", "1. a1-lr-cw"])
            self.assertEqual(facts["plies"][-1]["notation"], "5. a5#")
            outputs = (Path(temp) / "output.txt").read_text(encoding="utf-8").splitlines()
            self.assertEqual([line for line in outputs if line.startswith("replay=")],
                             ["replay=false"] * 11 + ["replay=true"], "the clock's draw, ten turns, and the win")
            region = (Path(temp) / "markdown.yaml").read_text(encoding="utf-8").split("# pentago:start")[1]
            self.assertIn("🎬 [Watch the replay](https://github.com/tannergolden/play/blob/HEAD/replays/pentago/"
                          "game-1.md) of every move.", region.split("# pentago:end")[0])

    def test_anything_malformed_is_turned_away_on_its_issue_and_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            for key, moves in (("tictac", ("j1", "a0", "e10", "e5; rm -rf", "4", "e4-ur-cw", "E5")),
                               ("pentago", ("g1", "a7", "a1-ul-up", "a1-xx-cw", "a1-ul", "a1 ul cw", "A1-UL-CW"))):
                folder = Path(temp) / key
                good = {"MOVE": "b2", "GAME": "1", "MOVE_NUMBER": "1", "ISSUE": "1", "PLAYER": OCTOCAT,
                        "PLAYER_ID": str(OCTOCAT_ID)}
                bad = [("MOVE", move) for move in moves] + [("GAME", "0"), ("MOVE_NUMBER", "x"),
                                                             ("GAME", "1234567890"), ("PLAYER", "bad name"),
                                                             ("PLAYER_ID", "12a")]
                for name, value in bad:
                    with self.subTest(key=key, name=name, value=value):
                        code, out = self.run_script(key, folder, "2026-10-12T16:00:00Z", **{**good, name: value})
                        self.assertEqual(code, 0)
                        reply = (out / "comment.md").read_text(encoding="utf-8")
                        self.assertTrue(reply.startswith("🚫 **This move can't be played as sent**, so nothing was"
                                                         " played."))
                        self.assertIn("issue=1\n", (Path(temp) / "output.txt").read_text(encoding="utf-8"))
                self.assertFalse(folder.exists())
                code, _ = self.run_script(key, folder, "2026-10-12T16:00:00Z", **{**good, "MOVE": "z9", "ISSUE": "x"})
                self.assertEqual(code, 1, "nowhere to say so: the run stops")
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(games.main([key, str(folder)], {"OWNER": OWNER}), 1)


if __name__ == "__main__":
    unittest.main()
