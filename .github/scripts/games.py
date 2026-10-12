#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The three games beside chess on the profile, Tic-Tac-Toe, Connect Four and Checkers: one engine for all three.

  python3 .github/scripts/games.py tictactoe .github/tictactoe [--now 2026-10-12T16:00:00Z]

Each plays as chess.py plays chess, and says what it says the way chess says
it. The owner of the profile is the house, and GitHub, anyone else, the
other side; the first of GitHub's moves to reach the game is the one played.
Each move arrives from tannergolden/play's Move Intake, which starts the
game's workflow with the move as its issue title carries it (a cell, `b2`; a
column, `4`; or a checkers move, `11-15` or `22x15x8`), the game and move it
was picked at, the issue it came from and who opened it; they arrive here as
MOVE, GAME, MOVE_NUMBER, ISSUE, PLAYER and PLAYER_ID, and are checked again.
Moves count both sides', from 1 for the first.

Sides: each player keeps one colour in every game. The house plays X in
Tic-Tac-Toe and White in Connect Four and Checkers, as it plays White in
chess; GitHub plays O, or Black. Only who moves first can change. Checkers
is American checkers, where Black moves first, so GitHub opens every game of
it; the first starts as soon as a run first meets the game, and a fresh
board's week counts from its start like any turn's. In Tic-Tac-Toe and
Connect Four the Arbiter opens every game itself, for a side drawn at
random, with a random legal move, so that side's mark or disc goes first: O
opens a game of Tic-Tac-Toe the Arbiter opened for GitHub, and a white disc
a game of Connect Four it opened for the house. Both picks are seeded as the
Arbiter's week moves are, and the opening counts for nobody and answers no
issue. `game.json` records the side it opened for as `opens`.

A move is played only when it is for the game and the move on the board, by
the side whose turn it is, and legal. Anything else is turned away with a
reply saying why, in the very words the intake uses, and nothing changes.
With no MOVE the run is the clock (clock.py runs every game's in one run):
when the side to move has gone a week without moving, the Arbiter plays a
legal move for it at random, and says so on the issue of the move it
answers, once, and after that in the owner's logbook.

A game ends when the rules end it, never by resigning or agreeing a draw.
Its record goes into the Hall of Fame and its moves into a file of their own,
and its final board stays up for two days: until then nothing can be played,
and then the next game's fresh board comes by itself, the Arbiter's opening
already on it where the Arbiter opens. The week for its next move counts
from the moment it came.

  .github/<game>/game.json           the game on the board: its number, start, the side the Arbiter opened for where
                                     it opens, its moves, and while a final board is up, the game that ended
  .github/<game>/hall-of-fame.json   every finished game: result, deciding move, players, the house's moves, the
                                     final board and the winning line
  .github/<game>/games/game-N.txt    each finished game, every move with who played it (game-N.pdn for checkers)

After every run it sets the game's board out for the page between its own
markers in .github/markdown.yaml (`# tictactoe:start` and `# tictactoe:end`,
and so on), with every legal move named by the game's names module and a
link that opens its ready-made issue, and the Hall of Fame of all four games
between `# hall:start` and `# hall:end` (hall.py). It writes comment.md and
commit.txt into --out, and sets `changed`, `issue` and `logbook` as step
outputs, as chess.py does. Stdlib only, with each game's module beside it:
tictactoe.py, connectfour.py and checkers.py, and their rules and names.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import os
import random
import re
import sys
import textwrap
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import hall as halls
from page import (
    DISPLAY,
    GITHUB,
    HOUSE,
    WEEK,
    date,
    day,
    dump,
    handle,
    load,
    now_utc,
    other,
    parse,
    profile,
    sentences,
    set_out,
    stamp,
    until,
)

GAMES = ("tictactoe", "connectfour", "checkers")
ROWS = 3  # the score sheet's latest rows
COUNT = re.compile(r"[1-9][0-9]{0,8}")  # a game or a move: up to 999,999,999, as the page's links carry
ID = re.compile(r"[1-9][0-9]{0,15}")  # an issue or an account: up to 16 digits, as the intake passes on
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
ORDER = ("kind", "board", "fen", "opens", "game", "move", "players", "due", "next", "last", "result", "line",
         "kings", "alert", "history", "note", "moves")

# The refusals, word for word as the intake's (tannergolden/play), which turns the same moves away before they come.
OVER = ("⌛ **Game {game} is over**, so `{code}` wasn't played.\n"
        "Game {number} is under way on {board}: pick a move there.\n")
TOO_LATE = ("⌛ **Too late: move {ply} is already on the board**, so `{code}` wasn't played.\n"
            "{numbered} got there first, played by {by}. Pick a move from {board} as it stands now.\n")
HOUSE_TURN = ("⏳ **It's {owner}'s turn as {house}**, so `{code}` wasn't played.\n"
              "GitHub plays {github}: once {house} moves, pick {github}'s reply on {board}.\n")
GITHUB_TURN = ("⏳ **It's GitHub's turn as {github}**, so `{code}` wasn't played.\n"
               "{github}'s moves are for everyone but you. Your turn comes next.\n")
OPENS = ("⏳ **Game {number} opens {day}**, so `{code}` wasn't played.\n"
         "Game {ended}'s final board stays up until then: pick a move from {board} once game {number} is on it.\n")


def rules(key: str) -> ModuleType:
    """A game's module, beside this one: what the engine asks of its rules, names and board."""
    if key not in GAMES:
        raise ValueError(f"{key!r} is not one of the games: {', '.join(GAMES)}")
    return importlib.import_module(key)


@dataclass(frozen=True)
class Request:
    """A move as the intake sent it."""
    code: str
    game: int
    move: int
    issue: int | None
    player: str
    player_id: int


@dataclass
class Outcome:
    """What one run decided: the state to save, if it changed, and what to say where."""
    game: dict | None
    hall: list
    changed: bool = False
    comment: str = ""
    issue: int | None = None  # the issue the comment goes on
    commit: str = ""
    record: tuple[str, str] | None = None  # a finished game's file name and text
    log: str = ""
    finished: dict | None = None  # the finished game's Hall of Fame record
    redraw: bool = False  # nothing to save, but the page is drawn again: a run of the last move over again
    logbook: bool = False  # the comment goes in the owner's logbook of the Arbiter's moves, not on a player's issue


@dataclass(frozen=True)
class End:
    """How a game ended: the side that won it, if one did, how, and the cells it was won on."""
    winner: str | None  # HOUSE or GITHUB, or None for a draw
    reason: str
    line: list | None = None  # the winning cells as the board's own field takes them


# --- the sides ---------------------------------------------------------------------------------------------------
def opener(mod: ModuleType, game: dict) -> str:
    """The side that moves first: the side the game always opens with, or the side the Arbiter opened for."""
    return mod.OPENER or game.get("opens", HOUSE)


def side_of(mod: ModuleType, game: dict, ply: int) -> str:
    """Whose move a ply is, counting from 1: the opener's odd ones, the other side's even ones."""
    first = opener(mod, game)
    return first if ply % 2 else other(first)


def named_side(side: str, owner: str) -> str:
    return f"@{owner}" if side == HOUSE else "GitHub"


def numbered(ply: int, shown: str) -> str:
    """A move with its number, as a score sheet writes it: `3. Xa2` for the opener's, `3... Oc2` for the reply."""
    return f"{(ply + 1) // 2}. {shown}" if ply % 2 else f"{ply // 2}... {shown}"


def who(played: dict) -> str:
    return "the Arbiter" if played.get("arbiter") else f"@{played['player']}"


def link(owner: str, key: str, code: str, game: int, ply: int) -> str:
    """The link that opens a move's ready-made issue in the intake, its title already written."""
    title = urllib.parse.quote(f"{key}: {code} · game {game} · move {ply}", safe="")
    return f"https://github.com/{owner}/play/issues/new?template=move.yml&title={title}"


def pick(options: list, text: str):
    """A fair pick among the options, seeded by the text, so the same question always gets the same answer."""
    seed = hashlib.sha256(text.encode()).digest()
    return random.Random(int.from_bytes(seed, "big")).choice(options)  # a fair pick, not a secret


# --- the game ----------------------------------------------------------------------------------------------------
def replay(mod: ModuleType, game: dict) -> list:
    """Every position of the game, from the first to the one on the board."""
    positions = [mod.start(opener(mod, game))]
    for index, played in enumerate(game["moves"], 1):
        if played["move"] not in mod.legal(positions[-1]):
            raise ValueError(f"game {game['game']}, move {index}: {played['move']} is not legal there")
        positions.append(mod.make(positions[-1], played["move"]))
    return positions


def settle(mod: ModuleType, game: dict | None, moment: dt.datetime) -> tuple[dict, dict | None]:
    """The game brought up to the moment. The first game begins at once, its start the moment, and where the
    Arbiter opens, a fresh board's opening is played as soon as its start has come: a side drawn at random, then a
    random legal move for it, stamped at the start itself so the week for the reply counts from there. Returns the
    game, and the opening when this is the moment it was played."""
    if game is None:
        game = {"game": 1, "started": stamp(moment), "moves": []}
    if not mod.ARBITER_OPENS or game["moves"] or parse(game["started"]) > moment:
        return game, None
    number, started = game["game"], game["started"]
    opens = pick([HOUSE, GITHUB], f"{mod.KEY}:{number}:opens:{started}")
    position = mod.start(opens)
    code = pick(sorted(mod.legal(position)), f"{mod.KEY}:{number}:1:{started}")
    opening = {"move": code, "shown": mod.shown(position, code), "player": None, "player_id": None, "issue": None,
               "arbiter": True, "at": started}
    return {"game": number, "started": started, "opens": opens, "moves": [opening]}, opening


def contributors(mod: ModuleType, game: dict) -> list[dict]:
    """Everyone who played a move for GitHub in the game, most moves first: the Arbiter's count for nobody."""
    counts: dict[int, dict] = {}
    for ply, played in enumerate(game["moves"], 1):
        if side_of(mod, game, ply) == GITHUB and not played.get("arbiter"):
            entry = counts.setdefault(played["player_id"], {"player": played["player"],
                                                            "player_id": played["player_id"], "moves": 0})
            entry["player"] = played["player"]  # the newest login, should it have changed
            entry["moves"] += 1
    return sorted(counts.values(), key=lambda entry: (-entry["moves"], entry["player"].casefold()))


def house_moves(mod: ModuleType, game: dict) -> int:
    """How many of the house's moves in the game the owner made: the Arbiter's are not theirs."""
    return sum(1 for ply, played in enumerate(game["moves"], 1)
               if side_of(mod, game, ply) == HOUSE and not played.get("arbiter"))


def same(played: dict, request: Request) -> bool:
    """Whether a move on record came from this very request: the same issue, the same move and the same player. A
    run made over again, such as a re-run of its job, finds its own move already played."""
    return (request.issue is not None and played.get("issue") == request.issue and not played.get("arbiter")
            and played.get("player_id") == request.player_id)


def ending_of(mod: ModuleType, positions: list, codes: list[str]) -> End | None:
    """How the game ends after its last move, if it does: `positions` from the first to the last, and the moves
    between them."""
    found = mod.ending(positions, codes)
    return End(*found) if found else None


# --- what the replies say ----------------------------------------------------------------------------------------
def entry_of(mod: ModuleType, position, game: int, ply: int, code: str) -> dict:
    """A move as the board listed it: its notation, words, emoji and title."""
    return next(entry for entry in mod.listing(position, game, ply) if entry["code"] == code)


def named(mod: ModuleType, position, game: int, ply: int, code: str) -> str:
    """A move as its reply names it, as the board listed it: its emoji, its title and what it does."""
    entry = entry_of(mod, position, game, ply, code)
    return f"{entry['emoji']} *{entry['title']}* · {entry['words']}"


def turn_line(mod: ModuleType, game: dict, side: str, position, owner: str, board: str) -> str:
    """The line a reply ends on: whose turn it is now, and what that side faces. The owner is pinged when the move
    is theirs, and only then."""
    faces, facing = mod.pressure(position)
    if side == HOUSE:
        return f"@{owner}, it's your move{', ' + faces if faces else ''}."
    return (f"GitHub's turn{', ' + facing if facing else ''}: anyone but {handle(owner)} can pick"
            f" {mod.WORDS[GITHUB]}'s reply on {board}.")


def played_text(mod: ModuleType, game: dict, shown: str, side: str, player: str, name: str, after, owner: str,
                board: str) -> str:
    """The reply to a move that is played and leaves the game going: the move, its name, and whose turn it is."""
    sign = mod.LEAD[mod.WORDS[side]]
    alarm = mod.alarm(after)
    turn = turn_line(mod, game, other(side), after, owner, board)
    if side == HOUSE:
        return f"{sign} **{shown} is on the board.{alarm}**\n{name}\n{turn}\n"
    return f"{sign} **{shown} is on the board.{alarm}** Well played, @{player}.\n{name}\n{turn}\n"


def ended_text(mod: ModuleType, game: dict, end: End, shown: str, mover: dict, owner: str, name: str,
               opens: dt.datetime) -> str:
    """What the reply says when a move ends the game: how it ended, the move that did it, and when the next game's
    fresh board comes."""
    number, winner = game["game"], end.winner
    if winner is not None:
        cry = mod.cry(end, mod.WORDS[other(winner)])
        if mover.get("arbiter"):
            head = f"🏆 **{shown}: {cry}** {named_side(winner, owner)} wins game {number} on the Arbiter's move."
        elif winner == HOUSE:
            head = f"🏆 **{shown}: {cry}** @{owner} wins game {number}."
        else:
            head = (f"🏆 **{shown}: {cry}** GitHub wins game {number}, and @{mover['player']} takes a place in the"
                    f" [Hall of Fame]({profile(owner)}) for the winning move.")
    else:
        head = f"🤝 **{shown}: game {number} is drawn {mod.DRAWN[end.reason]}.**"
    nxt = ("the Arbiter opens it for a side drawn at random" if mod.ARBITER_OPENS
           else f"{named_side(mod.OPENER, owner)} opens it as {mod.WORDS[mod.OPENER]}")
    return (f"{head}\n{name}\nIts final board stays up for two days: game {number + 1} opens {day(opens)}, and"
            f" {nxt}.\n")


# --- moves ---------------------------------------------------------------------------------------------------------
def apply(mod: ModuleType, game: dict, hall: list, positions: list, code: str, mover: dict, owner: str,
          moment: dt.datetime) -> tuple[Outcome, str, End | None]:
    """Plays a legal move into the game; when it ends the game, records it, and sets the next game to come two days
    on, its board showing the one that ended until then."""
    position = positions[-1]
    ply = len(game["moves"]) + 1
    text = mod.shown(position, code)
    shown = numbered(ply, text)
    game = {**{key: value for key, value in game.items() if key not in ("moves", "ended")},
            "moves": [*game["moves"], {"move": code, "shown": text, **mover, "at": stamp(moment)}]}
    positions = [*positions, mod.make(position, code)]
    end = ending_of(mod, positions, [played["move"] for played in game["moves"]])
    outcome = Outcome(game=game, hall=hall, changed=True)
    if end:
        deciding = {"move": shown, **{key: mover.get(key) for key in ("player", "player_id", "arbiter", "issue")}}
        record = {"game": game["game"], "result": mod.RESULTS[end.winner], "reason": end.reason,
                  "winner": {HOUSE: owner, GITHUB: "GitHub"}.get(end.winner or ""), "plies": len(game["moves"]),
                  "started": game["started"], "ended": stamp(moment), "deciding": deciding,
                  "players": contributors(mod, game), "house_moves": house_moves(mod, game),
                  "final": mod.final(positions[-1])}
        if end.line:
            record["line"] = end.line
        outcome.hall = [*hall, record]
        outcome.finished = record
        write = getattr(mod, "record", None) or (lambda *args: text_record(mod, *args))
        outcome.record = (f"game-{game['game']}.{mod.EXT}", write(game, positions, record, owner))
        outcome.game = {"game": game["game"] + 1, "started": stamp(moment + DISPLAY), "moves": [], "ended": game}
    return outcome, shown, end


def opened_commit(mod: ModuleType, game: dict, owner: str) -> str:
    """The commit for the Arbiter's opening of a fresh board."""
    side = opener(mod, game)
    body = (f"The Arbiter opens every game of {mod.TITLE} for a side drawn at random, with a random move that counts"
            " for nobody.")
    return (f"chore({mod.KEY}): 🎲 open game {game['game']} for {owner if side == HOUSE else 'GitHub'} with"
            f" {numbered(1, game['moves'][0]['shown'])}\n\n{textwrap.fill(body, 72)}")


def started_commit(mod: ModuleType, game: dict, owner: str) -> str:
    """The commit for a first game that begins without an opening of the Arbiter's: its start, and who opens it."""
    side = opener(mod, game)
    named, said = (owner if side == HOUSE else "GitHub"), mod.WORDS[side]
    body = (f"{named} opens every game of {mod.TITLE} as {said}, and the week for the first move of game"
            f" {game['game']} counts from now.")
    return f"chore({mod.KEY}): 🏁 start game {game['game']}, {named} to open as {said}\n\n{textwrap.fill(body, 72)}"


def verdict(mod: ModuleType, end: End) -> str:
    """How a finished game came out, as a commit says it: the winner's colour or mark, or a draw."""
    return f"{mod.WORDS[end.winner]} wins" if end.winner else "drawn"


def play(mod: ModuleType, game: dict | None, hall: list, request: Request, owner: str, owner_id: int,
         moment: dt.datetime) -> Outcome:
    """One move from the intake: played, or turned away with the reason."""
    current, opening = settle(mod, game, moment)
    number, board = current["game"], f"[the board]({profile(owner)})"
    outcome = Outcome(game=current, hall=hall, issue=request.issue, changed=game is None or opening is not None)
    if opening:
        outcome.commit = opened_commit(mod, current, owner)
    elif game is None:
        outcome.commit = started_commit(mod, current, owner)

    def refuse(text: str, log: str) -> Outcome:
        outcome.comment, outcome.log = text, log
        return outcome

    # While the last game's final board is up, nothing can be played: a move for any game is told when the next
    # one opens, in the intake's words, which never say a game is under way before it is.
    waiting = number > 1 and not current["moves"] and parse(current["started"]) > moment
    if request.game < number:
        ended = next((record for record in hall if record["game"] == request.game), None)
        if ended and ended["plies"] == request.move and same(ended["deciding"], request):
            outcome.redraw = not current["moves"]  # its ending is still the last thing to happen
            later = (f"Game {number} opens {day(parse(current['started']))} on {board}." if waiting
                     else f"Game {number} is under way on {board}.")
            return refuse(f"✅ **{ended['deciding']['move']} already ended game {request.game}**, played from this"
                          f" issue.\n{later}\n", "already played from this issue")
    if waiting:
        return refuse(OPENS.format(number=number, day=day(parse(current["started"])), code=request.code,
                                   ended=number - 1, board=board), "the last game's final board is up")
    if request.game < number:
        return refuse(OVER.format(game=request.game, code=request.code, number=number, board=board), "an earlier game")
    if request.game > number:
        return refuse(f"❓ **There's no game {request.game} yet**, so `{request.code}` wasn't played.\nGame {number}"
                      f" is under way on {board}: pick a move there.\n", "a later game")
    positions = replay(mod, current)
    position, ply = positions[-1], len(current["moves"]) + 1
    if request.move < ply:
        earlier = current["moves"][request.move - 1]
        shown = numbered(request.move, earlier["shown"])
        if earlier["move"] == request.code and same(earlier, request):
            if request.move == ply - 1:  # the last move on the board: answer as when it was played, and draw again
                outcome.redraw = True
                name = named(mod, positions[-2], number, request.move, earlier["move"])
                return refuse(played_text(mod, current, shown, side_of(mod, current, request.move), request.player,
                                          name, position, owner, board), "already played from this issue")
            return refuse(f"✅ **{shown} is already on the board**, played from this issue.\nThe game has moved on"
                          f" since: pick a move from {board} as it stands now.\n", "already played from this issue")
        by = ("you" if not earlier.get("arbiter") and earlier["player_id"] == request.player_id else
              "the Arbiter" if earlier.get("arbiter") else handle(earlier["player"]))
        return refuse(TOO_LATE.format(ply=request.move, code=request.code, numbered=shown, by=by, board=board),
                      "stale")
    if request.move > ply:
        return refuse(f"❓ **The board is on move {ply}, not move {request.move}**, so `{request.code}` wasn't"
                      f" played.\nPick a move from {board} as it stands now.\n", "a later move")
    side, is_owner = side_of(mod, current, ply), request.player_id == owner_id
    words = {"house": mod.WORDS[HOUSE], "github": mod.WORDS[GITHUB]}
    if side == HOUSE and not is_owner:
        return refuse(HOUSE_TURN.format(owner=handle(owner), code=request.code, board=board, **words),
                      f"{words['house']}'s turn")
    if side == GITHUB and is_owner:
        return refuse(GITHUB_TURN.format(code=request.code, **words), f"{words['github']}'s turn")
    if request.code not in mod.legal(position):
        return refuse(f"🚫 **`{request.code}` isn't a legal move here**: {mod.why_illegal(position, request.code)}.\n"
                      f"Nothing was played. Every move listed under {board} is legal: pick one there.\n", "illegal")

    mover = {"player": request.player, "player_id": request.player_id, "issue": request.issue, "arbiter": False}
    name = named(mod, position, number, ply, request.code)
    result, shown, end = apply(mod, current, hall, positions, request.code, mover, owner, moment)
    result.issue = request.issue
    if end:
        result.comment = ended_text(mod, current, end, shown, mover, owner, name, moment + DISPLAY)
        sign = "🏆" if end.winner else "🤝"
        result.commit = f"chore({mod.KEY}): {sign} play {shown}, ending game {number}: {verdict(mod, end)}"
    else:
        after = mod.make(position, request.code)
        result.comment = played_text(mod, current, shown, side, request.player, name, after, owner, board)
        result.commit = f"chore({mod.KEY}): {mod.LEAD[mod.WORDS[side]]} play {shown} in game {number}"
    result.commit += f"\n\nMove {ply}, by {request.player}."
    if opening:
        result.commit += f" The Arbiter opened game {number} first, with {numbered(1, opening['shown'])}."
    elif game is None:
        result.commit += f" Game {number} starts with it."
    result.log = f"played {shown}" + (f", {end.reason}" if end else "")
    return result


def tick(mod: ModuleType, game: dict | None, hall: list, owner: str, moment: dt.datetime) -> Outcome:
    """The clock: a fresh board's opening once its start has come, where the Arbiter opens, and after a week without
    a move, the Arbiter's random move for the side to move."""
    settled, opening = settle(mod, game, moment)
    outcome = Outcome(game=settled, hall=hall, changed=game is None or opening is not None)
    said = []
    if opening:
        outcome.commit = opened_commit(mod, settled, owner)
        said.append(f"the Arbiter opened game {settled['game']} with {numbered(1, opening['shown'])}")
    elif game is None:
        outcome.commit = started_commit(mod, settled, owner)
        said.append(f"game {settled['game']} started, {named_side(opener(mod, settled), owner)} to open")
    if not settled["moves"] and parse(settled["started"]) > moment:
        outcome.log = f"game {settled['game'] - 1}'s final board is up until {settled['started']}"
        return outcome
    last = parse(settled["moves"][-1]["at"] if settled["moves"] else settled["started"])
    if moment - last < WEEK:
        outcome.log = "; ".join([*said, f"the side to move has until {stamp(last + WEEK)}"])
        return outcome
    positions = replay(mod, settled)
    position, ply, number = positions[-1], len(settled["moves"]) + 1, settled["game"]
    code = pick(sorted(mod.legal(position)), f"{mod.KEY}:{number}:{ply}:{stamp(last)}")
    mover = {"player": None, "player_id": None, "issue": None, "arbiter": True}
    side = side_of(mod, settled, ply)
    name = named(mod, position, number, ply, code)
    result, shown, end = apply(mod, settled, hall, positions, code, mover, owner, moment)
    # The notice goes on the issue of the move the Arbiter answers, once: its first move after a player's (the move
    # that ended the last game, when it opens the next) is told there, and a move after another of its own, its
    # opening included, goes in the owner's logbook, so no player's issue collects a notice a week and none is lost.
    before = settled["moves"][-1] if settled["moves"] else (hall[-1]["deciding"] if hall else None)
    if before and not before.get("arbiter") and before.get("issue"):
        result.issue = before["issue"]
    else:
        result.logbook = True
    board = f"[the board]({profile(owner)})"
    late = "GitHub" if side == GITHUB else handle(owner)
    head = (f"⏰ **A week passed without a move from {late}**, so the Arbiter played {shown} for"
            f" {mod.WORDS[side]}, at random.")
    if end:
        result.comment = f"{head}\n\n{ended_text(mod, settled, end, shown, mover, owner, name, moment + DISPLAY)}"
    else:
        after = mod.make(position, code)
        result.comment = f"{head}\n{name}\n{turn_line(mod, settled, other(side), after, owner, board)}\n"
    result.commit = (f"chore({mod.KEY}): ⏰ play {shown} for {mod.WORDS[side]} after a week without a move"
                     f"\n\nMove {ply} of game {number}, by the Arbiter.")
    if end:
        result.commit += f" It ends the game: {verdict(mod, end)}."
    if opening:
        result.commit += f" It opened the game first, with {numbered(1, opening['shown'])}."
    result.log = "; ".join([*said, f"the Arbiter played {shown}" + (f", {end.reason}" if end else "")])
    return result


# --- the board -----------------------------------------------------------------------------------------------------
def score_sheet(mod: ModuleType, game: dict, positions: list) -> list[list]:
    """The score sheet's latest rows: each move's number, the opener's move, the reply and who chose GitHub's, and
    the row the next move goes on."""
    moves, rows = game["moves"], []
    for i in range(0, len(moves), 2):
        first = moves[i]
        reply = moves[i + 1] if i + 1 < len(moves) else None
        github = first if opener(mod, game) == GITHUB else reply
        rows.append([i // 2 + 1, mod.notation(positions[i], first["move"]),
                     mod.notation(positions[i + 1], reply["move"]) if reply else "", who(github) if github else ""])
    if len(moves) % 2 == 0:
        rows.append([len(moves) // 2 + 1, "", "", ""])
    return rows[-ROWS:]


def last_move(mod: ModuleType, game: dict, positions: list) -> dict:
    """The last move as the board shows it: its notation as the score sheet writes it, a won game's last move with
    its `#`, its words, who played it, and the day."""
    played, before, ply = game["moves"][-1], positions[-2], len(game["moves"])
    entry = entry_of(mod, before, game["game"], ply, played["move"])
    return {"move": mod.notation(before, played["move"]), "words": entry["words"], "by": who(played),
            "when": day(parse(played["at"])), **mod.marked(before, played["move"])}


def ordered(element: dict) -> dict:
    return {key: element[key] for key in ORDER if key in element}


def kept(mod: ModuleType, owner: str) -> str:
    return (f"Every finished game is kept as a [{mod.RECORD}](https://github.com/{owner}/{owner}/tree/HEAD/.github/"
            f"{mod.KEY}/games).")


def who_plays(side: str, owner: str) -> str:
    if side == GITHUB:
        return f"Anyone but @{owner} can play on this turn, and the first pick in is played."
    return f"Only @{owner} can play on this turn: a pick from anyone else is turned away with a comment on its issue."


def board(mod: ModuleType, game: dict | None, hall: list, owner: str, moment: dt.datetime) -> dict:
    """The game's element for the page: what its board draws, and what the README carries round it."""
    current, _ = settle(mod, game, moment)
    if not current["moves"] and parse(current["started"]) > moment:
        if current.get("ended"):
            return finished(mod, current, hall, owner)
        current, _ = settle(mod, current, parse(current["started"]))  # its record is gone: the fresh board early
    positions = replay(mod, current)
    position, ply, number = positions[-1], len(current["moves"]) + 1, current["game"]
    side = side_of(mod, current, ply)
    element = {"kind": mod.KEY, **mod.fields(current, positions, over=False), "game": number, "move": (ply + 1) // 2,
               "players": len(contributors(mod, current))}
    clock = parse(current["moves"][-1]["at"] if current["moves"] else current["started"]) + WEEK
    element["due"] = day(clock)
    if current["moves"]:
        element["last"] = last_move(mod, current, positions)
    element["history"] = score_sheet(mod, current, positions)
    record = hall[-1] if hall and not current["moves"] else None  # the game that ended, when this one is yet to open
    opens = mod.OPENS_NOTE.format(owner=owner)
    if mod.ARBITER_OPENS and len(current["moves"]) == 1:
        parts = [(opens, True), (who_plays(side, owner), True)]
    elif current["moves"]:
        parts = [(who_plays(side, owner), True)]
    else:  # a fresh board, its opener to make the first move
        parts = [(f"Game {record['game']} was drawn {mod.DRAWN[record['reason']]}." if record and not record["winner"]
                  else "", False), (opens, True), (who_plays(side, owner), True)]
    parts.append((f"The move is due by {until(clock)}, or the Arbiter plays a random legal move.", True))
    parts += [(mod.RULE, False), (kept(mod, owner) if hall else "", False)]
    element["note"] = sentences(parts)
    element["moves"] = [[entry["emoji"], entry["title"], entry["notation"], entry["words"],
                         link(owner, mod.KEY, entry["code"], number, ply)]
                        for entry in mod.listing(position, number, ply)]
    return ordered(element)


def finished(mod: ModuleType, game: dict, hall: list, owner: str) -> dict:
    """The board while a finished game's final board is up: the final position, who won and how, the winning line,
    the last move and score sheet, and the day the fresh board comes, with nothing left to play."""
    ended, opens = game["ended"], parse(game["started"])
    record = next((r for r in reversed(hall) if r["game"] == ended["game"]), None) or {}
    positions = replay(mod, ended)
    end = ending_of(mod, positions, [played["move"] for played in ended["moves"]])
    number, ply = ended["game"], len(ended["moves"])
    won = end.winner if end else None
    element = {"kind": mod.KEY, **mod.fields(ended, positions, over=True), "game": number, "move": ply // 2 + 1,
               "players": len(contributors(mod, ended)), "next": day(opens)}
    if ended["moves"]:
        element["last"] = last_move(mod, ended, positions)
    if end:
        element["result"] = {"winner": won, "how": end.reason}
        if end.line:
            element["line"] = end.line
    element["history"] = score_sheet(mod, ended, positions)
    deciding = record.get("deciding") or {}
    over = (f"Game {number} is over, and its final board stays up for two days: game {number + 1} opens"
            f" {until(opens)}, and nothing can be played until then.")
    nobody = ("The winning move was the Arbiter's, played after a week without one, so the win counts for nobody."
              if won and deciding.get("arbiter") else "")
    element["note"] = sentences([(over, True), (nobody, True), (kept(mod, owner), False)])
    return ordered(element)


# --- a finished game's record ------------------------------------------------------------------------------------
def text_record(mod: ModuleType, game: dict, positions: list, record: dict, owner: str) -> str:
    """A finished game as plain text: a header naming the game, its days and its result, then every move, numbered,
    with who played it."""
    first = opener(mod, game)
    sides = f"@{owner} played {mod.WORDS[HOUSE]} and GitHub played {mod.WORDS[GITHUB]}; "
    sides += (f"the Arbiter opened for {named_side(first, owner)}, so {mod.WORDS[first]} moved first."
              if mod.ARBITER_OPENS else f"{mod.WORDS[first]} moves first.")
    deciding = record["deciding"]["move"]
    if record["winner"]:
        result = f"{'@' + owner if record['winner'] == owner else 'GitHub'} won with {deciding}, {record['reason']}."
    else:
        result = f"Drawn with {deciding}, {mod.DRAWN[record['reason']]}."
    lines = [f"{mod.TITLE}, game {game['game']}: @{owner} against GitHub",
             f"Played from {date(parse(game['started']))} to {date(parse(record['ended']))}, in EST.", sides, result,
             ""]
    width = max(len(numbered(ply, played["shown"])) for ply, played in enumerate(game["moves"], 1)) + 3
    for ply, played in enumerate(game["moves"], 1):
        by = ("the Arbiter, opening the game" if played.get("arbiter") and ply == 1 and mod.ARBITER_OPENS else
              "the Arbiter, after a week" if played.get("arbiter") else f"@{played['player']}")
        lines.append(f"{numbered(ply, played['shown']).ljust(width)}{by}")
    lines += ["", f"Result: {record['result']}, {mod.WORDS[HOUSE]}'s score first"]
    return "\n".join(lines) + "\n"


def save(folder: Path, outcome: Outcome) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "game.json").write_text(dump(outcome.game), encoding="utf-8")
    if outcome.finished:
        (folder / "hall-of-fame.json").write_text(dump(outcome.hall), encoding="utf-8")
    if outcome.record:
        name, text = outcome.record
        (folder / "games").mkdir(exist_ok=True)
        (folder / "games" / name).write_text(text, encoding="utf-8")


def request_from(mod: ModuleType, env: dict) -> Request | None:
    """The move the intake sent, checked again: None when there is none, an error when any part is malformed."""
    if not env.get("MOVE"):
        return None
    checks = (("MOVE", mod.CODE), ("GAME", COUNT), ("MOVE_NUMBER", COUNT), ("PLAYER", LOGIN), ("PLAYER_ID", ID))
    for name, shape in checks:
        if not shape.fullmatch(env.get(name, "")):
            raise ValueError(f"{name} is missing or malformed")
    issue = env.get("ISSUE", "")
    if issue and not ID.fullmatch(issue):
        raise ValueError("ISSUE is malformed")
    return Request(env["MOVE"], int(env["GAME"]), int(env["MOVE_NUMBER"]), int(issue) if issue else None,
                   env["PLAYER"], int(env["PLAYER_ID"]))


def regions(root: Path, owner: str, owner_id: int, moment: dt.datetime, keys: tuple[str, ...]) -> dict:
    """The settings' regions a run writes: each named game's board, and the Hall of Fame of all four, from the
    state in the checkout."""
    states = halls.load(root)
    out = {key: [(key, board(rules(key), *states[key], owner, moment))] for key in keys}
    out["hall"] = [("hall-of-fame", halls.element(states, owner, owner_id))]
    return out


def main(argv: list[str] | None = None, env: dict | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("key", choices=GAMES, help="the game: tictactoe, connectfour or checkers")
    parser.add_argument("folder", type=Path, help="where the game's state lives, such as .github/tictactoe")
    parser.add_argument("--out", type=Path, help="where comment.md and commit.txt go (default: $RUNNER_TEMP)")
    parser.add_argument("--now", help="the time to play at, ISO 8601 (default: now)")
    parser.add_argument("--settings", type=Path, default=Path(".github/markdown.yaml"),
                        help="the page's settings, where the board is set out (default: .github/markdown.yaml)")
    args = parser.parse_args(argv)
    env = dict(os.environ) if env is None else env
    mod = rules(args.key)
    owner, owner_id = env.get("OWNER", ""), env.get("OWNER_ID", "")
    if not LOGIN.fullmatch(owner) or not ID.fullmatch(owner_id):
        print("::error::OWNER and OWNER_ID name the house, and one is missing or malformed.")
        return 1
    malformed = ""
    try:
        request = request_from(mod, env)
    except ValueError as exc:
        if not ID.fullmatch(env.get("ISSUE", "")):  # nowhere to say so
            print(f"::error::The move was not played: {exc}.")
            return 1
        request, malformed = None, str(exc)
    moment = parse(args.now) if args.now else now_utc()
    game, hall = load(args.folder)
    if malformed:
        outcome = Outcome(game=game, hall=hall, issue=int(env["ISSUE"]), log=f"turned away, {malformed}",
                          comment=f"🚫 **This move can't be played as sent**, so nothing was played.\nEvery move listed"
                                  f" under [the board]({profile(owner)}) opens its issue ready-made: pick one there"
                                  " and send it unchanged.\n")
    elif request:
        outcome = play(mod, game, hall, request, owner, int(owner_id), moment)
    else:
        outcome = tick(mod, game, hall, owner, moment)
    if outcome.changed:
        save(args.folder, outcome)
    try:
        drawn = set_out(args.settings, regions(args.folder.parent, owner, int(owner_id), moment, (args.key,)))
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    if drawn and not outcome.commit:
        outcome.commit = f"chore({args.key}): 🖌️ set the board out for the page"
    out = args.out or Path(env.get("RUNNER_TEMP", "."))
    out.mkdir(parents=True, exist_ok=True)
    run = env.get("RUN_URL", "")
    (out / "comment.md").write_text(outcome.comment, encoding="utf-8")
    (out / "commit.txt").write_text(outcome.commit + (f"\n\nRun: {run}" if run and outcome.commit else "") + "\n",
                                    encoding="utf-8")
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle_:
            handle_.write(f"changed={'true' if outcome.changed or drawn or outcome.redraw else 'false'}\n")
            handle_.write(f"issue={outcome.issue or ''}\n")
            handle_.write(f"logbook={'true' if outcome.logbook else 'false'}\n")
    target = f" (game {request.game}, move {request.move}, @{request.player})" if request else ""
    print(f"{args.key}: {'Move ' + request.code if request else 'Move' if malformed else 'Clock'}{target}:"
          f" {outcome.log}.")
    return 0


if __name__ == "__main__":
    sys.exit(importlib.import_module("games").main())  # as the module the games' own modules import, not a copy
