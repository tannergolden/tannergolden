# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The Hall of Fame of all four games on the profile: each game's series, the leading winners, and the leaderboard.

  from hall import element, load

Every game keeps its finished games in .github/<game>/hall-of-fame.json and
the game on its board in game.json. The Hall reads all four, in tier order
(Tic-Tac, Pentago, Checkers, Chess), and sets them out for the page
as one element, `hall-of-fame`:

  series   each game's games finished, the house's wins, GitHub's wins and
           the draws: a side has won every game it won, the Arbiter's
           winning moves included, as a scoreboard keeps it
  people   the leading winners across all four games, the house included:
           each one's login, wins by game, the day of the last win, the
           games played and the account's ID; ranked by wins, then the
           latest win, then login; twice the page's five places
  leaders  the house's own row, then GitHub's leading players: each one's
           login, moves, games, wins by game and account ID; ranked by wins,
           then moves, then login; twice the page's ten places

A win is a person's when the game was won and its deciding move was not the
Arbiter's: the owner's when the house won, else the deciding move's player's.
A draw is nobody's win, and nor is anything the Arbiter plays: its moves,
its openings and its winning moves count for nobody. Moves and games count
over every finished game and the game on each board. Each player is named by
the newest login they played as, in any game, with their account's ID, so
the page can name them as they are now and leave out anyone whose account is
gone; the lists run to twice the places the page shows, so the next player
fills a place left that way. Stdlib only.
"""
from __future__ import annotations

from pathlib import Path

from page import GITHUB, HOUSE, day, other, parse
from page import load as load_game

GAMES = ("tictac", "pentago", "checkers", "chess")  # tier order, for every list of the four games
OPENERS = {"checkers": GITHUB, "chess": HOUSE}  # who always opens these; the Arbiter's games say whom it opened for
PEOPLE, LEADERS = 5, 10  # the page's places: the podium's winners, and GitHub's players under the house's row
DEPTH = 2  # the lists run to twice the page's places, so a player whose account is gone leaves no gap
TALLY, MOST = 999_999, 999_999_999  # the most a count of games or wins, and of moves, may be on the page


def load(root: Path) -> dict[str, tuple[dict | None, list]]:
    """Every game's state from the folder that holds them, .github: the game on its board and its finished games."""
    return {key: load_game(root / key) for key in GAMES}


def opener(key: str, game: dict) -> str:
    """The side that moved first in a game: the side the Arbiter drew to open it, or the side that always opens it."""
    return game.get("opens") or OPENERS.get(key, HOUSE)


def turns(key: str, game: dict) -> list[tuple[str, dict]]:
    """Every turn played in a game, with the side that played it: under the Ghost Rule its two ghosts first, the side
    the Arbiter drew placing the first, then its moves, from the side that opened (`opener`)."""
    out = [(game["places"] if i == 0 else other(game["places"]), played)
           for i, played in enumerate(game.get("ghosts", []))]
    first = opener(key, game)
    return out + [(first if ply % 2 else other(first), played) for ply, played in enumerate(game.get("moves", []), 1)]


def tally(key: str, game: dict | None) -> tuple[int, list[dict]]:
    """The game on a board, counted: the house's turns in it, and everyone who has played a turn for GitHub, most
    first, a ghost a turn like any move; the Arbiter's count for nobody."""
    if not game:
        return 0, []
    house, counts = 0, {}
    for side, played in turns(key, game):
        if played.get("arbiter"):
            continue
        if side == HOUSE:
            house += 1
            continue
        entry = counts.setdefault(played["player_id"], {"player": played["player"], "player_id": played["player_id"],
                                                        "moves": 0})
        entry["player"] = played["player"]
        entry["moves"] += 1
    return house, sorted(counts.values(), key=lambda e: (-e["moves"], e["player"].casefold()))


def winner(record: dict, owner: str):
    """Whose win a finished game is: the house's, a player's account ID, or None for a draw, the Arbiter's win, or a
    win the other side's move made, as a Pentago turn can make five for the side that did not turn."""
    deciding = record.get("deciding") or {}
    if not record.get("winner") or deciding.get("arbiter") or deciding.get("own") is False:
        return None
    return HOUSE if record["winner"] == owner else deciding.get("player_id")


def logins(states: dict) -> dict[int, str]:
    """Every player's newest login, by account: the last one they played as, in any of the four games."""
    seen = []
    for key, (game, hall) in states.items():
        for record in hall:
            seen += [(parse(record["ended"]), p["player_id"], p["player"]) for p in record.get("players", [])]
        if game:
            seen += [(parse(played["at"]), played["player_id"], played["player"])
                     for side, played in turns(key, game) if not played.get("arbiter") and side == GITHUB]
    newest: dict[int, str] = {}
    for _, account, login in sorted(seen, key=lambda event: event[0]):
        newest[account] = login
    return newest


def row(login: str, cells: list, account: int | None) -> list:
    """A row for the page: its login, its counts, and the account's ID when it is known."""
    return [login, *cells] + ([account] if account else [])


def series(states: dict, owner: str) -> dict[str, list[int]]:
    """Each game's games finished, the house's wins, GitHub's wins and the draws."""
    out = {}
    for key in GAMES:
        hall = states[key][1]
        house = sum(1 for record in hall if record.get("winner") == owner)
        world = sum(1 for record in hall if record.get("winner") == "GitHub")
        out[key] = [min(n, TALLY) for n in (len(hall), house, world, len(hall) - house - world)]
    return out


def people(states: dict, owner: str, owner_id: int | None, newest: dict[int, str]) -> list[list]:
    """The leading winners across all four games, the house included: twice the five the page shows."""
    wins: dict = {}
    for index, key in enumerate(GAMES):
        for record in states[key][1]:
            who = winner(record, owner)
            if who is None:
                continue
            entry = wins.setdefault(who, {"wins": [0] * len(GAMES), "last": record["ended"]})
            entry["wins"][index] += 1
            if parse(record["ended"]) >= parse(entry["last"]):
                entry["last"] = record["ended"]
    finished = [record for key in GAMES for record in states[key][1]]
    rows = []
    for who, entry in wins.items():
        house = who == HOUSE
        login = owner if house else newest.get(who) or next(
            r["deciding"]["player"] for r in finished if (r.get("deciding") or {}).get("player_id") == who)
        games = len(finished) if house else sum(1 for r in finished if any(p["player_id"] == who
                                                                          for p in r.get("players", [])))
        rows.append((login, entry, games, owner_id if house else who))
    rows.sort(key=lambda r: (-sum(r[1]["wins"]), -parse(r[1]["last"]).timestamp(), r[0].casefold()))
    return [row(login, [[min(n, TALLY) for n in entry["wins"]], day(parse(entry["last"])), min(games, TALLY)],
                account) for login, entry, games, account in rows[:PEOPLE * DEPTH]]


def leaders(states: dict, owner: str, owner_id: int | None, newest: dict[int, str]) -> list[list]:
    """The leaderboard: the house's own row on top, at nought until it moves, then GitHub's leading players, twice
    the ten the page shows, each with the moves and games they played in all four games and their wins in each."""
    house = {"moves": 0, "games": 0, "wins": [0] * len(GAMES)}
    tallies: dict[int, dict] = {}

    def player(account: int, login: str) -> dict:
        return tallies.setdefault(account, {"login": login, "moves": 0, "games": 0, "wins": [0] * len(GAMES)})

    for index, key in enumerate(GAMES):
        game, hall = states[key]
        played = [(record, record.get("house_moves", 0), record.get("players", [])) for record in hall]
        played += [(None, *tally(key, game))] if game else []
        for record, own, players in played:
            house["moves"] += own
            house["games"] += 1 if own else 0
            for p in players:
                entry = player(p["player_id"], p["player"])
                entry["moves"] += p["moves"]
                entry["games"] += 1
            who = winner(record, owner) if record else None
            if who == HOUSE:
                house["wins"][index] += 1
            elif who is not None:
                player(who, record["deciding"]["player"])["wins"][index] += 1
    for account, entry in tallies.items():
        entry["login"] = newest.get(account, entry["login"])
    moved = [(account, entry) for account, entry in tallies.items() if entry["moves"]]  # no move, no place
    ranked = sorted(moved, key=lambda item: (-sum(item[1]["wins"]), -item[1]["moves"], item[1]["login"].casefold()))
    rows = [(owner, house, owner_id)] + [(e["login"], e, account) for account, e in ranked[:LEADERS * DEPTH]]
    return [row(login, [min(e["moves"], MOST), min(e["games"], TALLY), [min(n, TALLY) for n in e["wins"]]], account)
            for login, e, account in rows]


def element(states: dict, owner: str, owner_id: int | None = None) -> dict:
    """The page's Hall of Fame of all four games: each game's series, its leading winners and its leaderboard."""
    newest = logins(states)
    return {"kind": "hall-of-fame", "series": series(states, owner),
            "people": people(states, owner, owner_id, newest), "leaders": leaders(states, owner, owner_id, newest),
            "measure": {}}
