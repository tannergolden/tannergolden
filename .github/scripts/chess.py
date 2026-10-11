#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The chess game on the profile: one move, or the Arbiter's after a week without one.

  python3 .github/scripts/chess.py .github/chess [--now 2026-10-11T16:30:00Z]

The owner of the profile always plays White, and so always opens; GitHub,
anyone else, plays Black, and the first of its moves to reach the game is the
one played. Each move arrives from tannergolden/play's Move Intake, which
starts .github/workflows/chess.yml with the move in UCI, the game and move it
was picked at, the issue it came from and who opened it; they arrive here as
UCI, GAME, MOVE_NUMBER, ISSUE, PLAYER and PLAYER_ID, and are checked again.
Moves count both sides', from 1 for White's first.

A move is played only when it is for the game and the move on the board, by
the side whose turn it is, and legal. Anything else is turned away with a
reply saying why, and nothing changes. With no UCI the run is the clock: when
the side to move has gone a week without moving, the Arbiter plays a legal
move for it at random, and says so on the issue of the last move that came
from one.

A game ends when the rules end it, never by resigning or agreeing a draw.
Its record goes into the Hall of Fame, its moves into a PGN, and the next game
starts at once, with the owner to open it.

  .github/chess/game.json           the game in progress: its number, start and moves
  .github/chess/hall-of-fame.json   every finished game: result, deciding move, players, the owner's moves
  .github/chess/games/game-N.pgn    each finished game, every move with who played it

After every run it sets the game out for the page as two elements. The board:
the position, the last move in words with who played it when, any check, whose
turn it is and until when, how many have played for GitHub, what each side has
taken, the score sheet's latest rows, the turn's banner, and every legal move
named by chess_names.py, with a link that opens its ready-made issue. The Hall
of Fame: the series between the owner and GitHub, and its leading winners, a
point to whoever made a mating move; and the leaderboard, the owner's own moves,
wins and games on top of GitHub's ten leading players', where nothing the
Arbiter played counts for anyone. They go between the `# chess:start` and
`# chess:end` lines of .github/markdown.yaml, and nothing else in that file,
for tannergolden/markdown to draw in the page's one theme.

It writes comment.md, the reply to post, and commit.txt into the run's
temporary folder (--out), and sets `changed` and `issue` as step outputs.
Stdlib only, with chess_rules.py and chess_names.py beside it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from chess_names import listing
from chess_names import words as move_words
from chess_rules import (START, Ending, Move, Position, ending, in_check, king, label, legal_moves, make, pseudo_moves,
                         san, side, square)

WEEK = dt.timedelta(days=7)
EST = dt.timezone(dt.timedelta(hours=-5), "EST")  # the page tells time in EST, as its settings say
GROUPS = {"k": "king", "q": "queen", "r": "rook", "b": "bishop", "n": "knight", "p": "pawn"}
ROWS, PODIUM, LEADERS = 3, 5, 10  # the score sheet's latest rows, the Hall of Fame's winners, its leaderboard
UCI = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?")
NUMBER = re.compile(r"[1-9][0-9]{0,8}")
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
REASONS = {
    "stalemate": "stalemate",
    "fivefold repetition": "fivefold repetition",
    "seventy-five-move rule": "the seventy-five-move rule",
    "insufficient material": "insufficient material",
}


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def stamp(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Request:
    """A move as the intake sent it."""
    uci: str
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
    pgn: tuple[str, str] | None = None  # a finished game's file name and text
    log: str = ""
    finished: dict | None = None  # the finished game's Hall of Fame record


def new_game(number: int, started: dt.datetime) -> dict:
    return {"game": number, "started": stamp(started), "fen": START, "moves": []}


def replay(game: dict) -> list[Position]:
    """Every position of the game, from the first to the one on the board."""
    positions = [Position.from_fen(START)]
    for index, played in enumerate(game["moves"], 1):
        position = positions[-1]
        moves = {move.uci: move for move in legal_moves(position)}
        if played["uci"] not in moves:
            raise ValueError(f"game {game['game']}, move {index}: {played['uci']} is not legal there")
        positions.append(make(position, moves[played["uci"]]))
    return positions


def numbered(position: Position, name: str) -> str:
    """A move with its number, as a score sheet writes it: `12. Nf3` for White, `12... Nf6` for Black."""
    return f"{position.fullmove}. {name}" if position.turn == "w" else f"{position.fullmove}... {name}"


def named(position: Position, game: int, ply: int, move: Move) -> str:
    """A move as its reply names it, as the board listed it: its emoji, its order and what it does."""
    entry = next(m for m in listing(position, game, ply) if m["uci"] == move.uci)
    return f"{entry['emoji']} *{entry['title']}* · {entry['words']}"


def next_turn(turn: str, owner: str, check: bool, board: str) -> str:
    """The line a reply ends on: whose turn it is now, and whether that side is in check. The owner is pinged when
    the move is theirs, and only then."""
    if turn == "w":
        return f"@{owner}, it's your move{', and you are in check' if check else ''}."
    return (f"GitHub's turn{', in check' if check else ''}: anyone but {handle(owner)} can pick Black's"
            f" {'way out' if check else 'reply'} on {board}.")


def who(played: dict) -> str:
    return "the Arbiter" if played.get("arbiter") else f"@{played['player']}"


def handle(login: str) -> str:
    """A player named without a ping: the @handle as a link to their profile, which GitHub never turns into a
    mention. A turned-away move pings nobody, so nobody can ping anyone by opening issues."""
    return f"[@{login}]({profile(login)})"


def why_illegal(position: Position, uci: str) -> str:
    """Why a move that is not legal is not, in a few words."""
    piece = position.board[square(uci[0:2])]
    if not piece:
        return f"there's no piece on {uci[0:2]}"
    if side(piece) != position.turn:
        return f"the {PIECES[piece.lower()]} on {uci[0:2]} is {'White' if side(piece) == 'w' else 'Black'}'s"
    legal = {move.uci for move in legal_moves(position)}
    if len(uci) == 4 and uci + "q" in legal:
        return f"a pawn reaching the last rank has to say what it becomes, such as `{uci}q` for a queen"
    if len(uci) == 5 and uci[:4] in legal:
        return f"only a pawn reaching the last rank names a piece to become, so the move is `{uci[:4]}`"
    if any(move.uci == uci for move in pseudo_moves(position)):
        return "it would leave your king in check"
    return f"the {PIECES[piece.lower()]} on {uci[0:2]} can't move to {uci[2:4]}"


def profile(owner: str) -> str:
    return f"https://github.com/{owner}"


def contributors(game: dict) -> list[dict]:
    """Everyone who played a move for GitHub in the game, most moves first."""
    counts: dict[int, dict] = {}
    for index, played in enumerate(game["moves"]):
        if index % 2 == 1 and not played.get("arbiter"):
            entry = counts.setdefault(played["player_id"], {"player": played["player"],
                                                            "player_id": played["player_id"], "moves": 0})
            entry["player"] = played["player"]  # the newest login, should it have changed
            entry["moves"] += 1
    return sorted(counts.values(), key=lambda entry: (-entry["moves"], entry["player"].casefold()))


def pgn(game: dict, positions: list[Position], end: Ending, owner: str, ended: dt.datetime) -> str:
    """The finished game in PGN, every move followed by who played it."""
    tags = [("Event", f"@{owner} vs. GitHub"), ("Site", profile(owner)),
            ("Date", parse(game["started"]).strftime("%Y.%m.%d")), ("Round", str(game["game"])),
            ("White", owner), ("Black", "GitHub"), ("Result", end.result), ("Termination", "normal"),
            ("PlyCount", str(len(game["moves"]))), ("EndDate", ended.strftime("%Y.%m.%d"))]
    words = []
    for position, played in zip(positions, game["moves"]):
        words += [numbered(position, played["san"]).split()[0], played["san"],
                  "{" + ("the Arbiter, after a week" if played.get("arbiter") else played["player"]) + "}"]
    closing = "Checkmate." if end.reason == "checkmate" else f"Drawn by {REASONS[end.reason]}."
    words += ["{" + closing + "}", end.result]
    lines, line = [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > 79:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    lines.append(line)
    header = "".join(f'[{name} "{value}"]\n' for name, value in tags)
    return header + "\n" + "\n".join(lines) + "\n"


def apply(game: dict, hall: list, positions: list[Position], move: Move, mover: dict, owner: str,
          moment: dt.datetime) -> tuple[Outcome, str, Ending | None]:
    """Plays a legal move into the game; when it ends the game, records it and starts the next one."""
    position = positions[-1]
    name = san(position, move)
    shown = numbered(position, name)
    game = {**game, "moves": [*game["moves"], {"uci": move.uci, "san": name, **mover, "at": stamp(moment)}]}
    positions = [*positions, make(position, move)]
    game["fen"] = positions[-1].fen
    end = ending(positions)
    outcome = Outcome(game=game, hall=hall, changed=True)
    if end:
        deciding = {"move": shown, **{key: mover.get(key) for key in ("player", "player_id", "arbiter", "issue")}}
        winner = {"w": owner, "b": "GitHub"}.get(end.winner or "")
        record = {"game": game["game"], "result": end.result, "reason": end.reason, "winner": winner,
                  "plies": len(game["moves"]), "started": game["started"], "ended": stamp(moment),
                  "deciding": deciding, "players": contributors(game), "house_moves": house_moves(game)}
        outcome.hall = [*hall, record]
        outcome.finished = record
        outcome.pgn = (f"game-{game['game']}.pgn", pgn(game, positions, end, owner, moment))
        outcome.game = new_game(game["game"] + 1, moment)
    return outcome, shown, end


def ended_text(end: Ending, shown: str, number: int, mover: dict, owner: str, name: str) -> str:
    """What the reply says when a move ends the game: how it ended, the move that did it, and that the next game has
    started."""
    if end.reason == "checkmate":
        winner = f"@{owner}" if end.winner == "w" else "GitHub"
        if mover.get("arbiter"):
            head = f"🏆 **{shown}: checkmate!** {winner} wins game {number} on the Arbiter's move."
        elif end.winner == "w":
            head = f"🏆 **{shown}: checkmate!** @{owner} wins game {number}."
        else:
            head = (f"🏆 **{shown}: checkmate!** GitHub wins game {number}, and @{mover['player']} takes a place in"
                    f" the [Hall of Fame]({profile(owner)}) for the winning move.")
    else:
        head = f"🤝 **{shown}: game {number} is drawn by {REASONS[end.reason]}.**"
    return f"{head}\n{name}\nGame {number + 1} starts now, and @{owner} opens it as White.\n"


def play(game: dict | None, hall: list, request: Request, owner: str, owner_id: int,
         moment: dt.datetime) -> Outcome:
    """One move from the intake: played, or turned away with the reason."""
    current = game or new_game(1, moment)
    number, board = current["game"], f"[the board]({profile(owner)})"
    outcome = Outcome(game=game, hall=hall, issue=request.issue)

    def refuse(text: str, log: str) -> Outcome:
        outcome.comment, outcome.log = text, log
        return outcome

    if request.game < number:
        return refuse(f"⌛ **Game {request.game} is over**, so `{request.uci}` wasn't played.\nGame {number} is under"
                      f" way on {board}: pick a move there.\n", "an earlier game")
    if request.game > number:
        return refuse(f"❓ **There's no game {request.game} yet**, so `{request.uci}` wasn't played.\nGame {number}"
                      f" is under way on {board}: pick a move there.\n", "a later game")
    positions = replay(current)
    position, ply = positions[-1], len(current["moves"]) + 1
    if request.move < ply:
        earlier = current["moves"][request.move - 1]
        shown = numbered(positions[request.move - 1], earlier["san"])
        by = ("you" if not earlier.get("arbiter") and earlier["player_id"] == request.player_id else
              "the Arbiter" if earlier.get("arbiter") else handle(earlier["player"]))
        return refuse(f"⌛ **Too late: move {request.move} is already on the board**, so `{request.uci}` wasn't"
                      f" played.\n{shown} got there first, played by {by}. Pick a move from {board} as it stands"
                      " now.\n", "stale")
    if request.move > ply:
        return refuse(f"❓ **The board is on move {ply}, not move {request.move}**, so `{request.uci}` wasn't"
                      f" played.\nPick a move from {board} as it stands now.\n", "a later move")
    is_owner = request.player_id == owner_id
    if position.turn == "w" and not is_owner:
        return refuse(f"⏳ **It's {handle(owner)}'s turn as White**, so `{request.uci}` wasn't played.\n"
                      f"GitHub plays Black: once White moves, pick Black's reply on {board}.\n", "White's turn")
    if position.turn == "b" and is_owner:
        return refuse(f"⏳ **It's GitHub's turn as Black**, so `{request.uci}` wasn't played.\nBlack's moves are"
                      " for everyone but you. Your turn comes next.\n", "Black's turn")
    moves = {move.uci: move for move in legal_moves(position)}
    if request.uci not in moves:
        return refuse(f"🚫 **`{request.uci}` isn't a legal move here**: {why_illegal(position, request.uci)}.\n"
                      f"Nothing was played. Every move listed under {board} is legal: pick one there.\n", "illegal")

    mover = {"player": request.player, "player_id": request.player_id, "issue": request.issue, "arbiter": False}
    name = named(position, number, ply, moves[request.uci])
    outcome, shown, end = apply(current, hall, positions, moves[request.uci], mover, owner, moment)
    outcome.issue = request.issue
    check = shown.endswith("+")
    if end:
        outcome.comment = ended_text(end, shown, number, mover, owner, name)
        outcome.commit = f"chore(chess): 🏆 play {shown}, ending game {number} {end.result}"
    elif position.turn == "w":
        outcome.comment = (f"♟️ **{shown} is on the board.{' Check!' if check else ''}**\n{name}\n"
                           f"{next_turn('b', owner, check, board)}\n")
        outcome.commit = f"chore(chess): ♟️ play {shown} in game {number}"
    else:
        outcome.comment = (f"♟️ **{shown} is on the board.{' Check!' if check else ''}** Well played,"
                           f" @{request.player}.\n{name}\n{next_turn('w', owner, check, board)}\n")
        outcome.commit = f"chore(chess): ♟️ play {shown} in game {number}"
    outcome.commit += f"\n\nMove {ply}, by {request.player}."
    outcome.log = f"played {shown}" + (f", {end.reason}" if end else "")
    return outcome


def tick(game: dict | None, hall: list, owner: str, moment: dt.datetime) -> Outcome:
    """The clock: after a week without a move, the Arbiter plays one at random for the side to move."""
    outcome = Outcome(game=game, hall=hall)
    if game is None:
        outcome.log = "no game has started"
        return outcome
    last = parse(game["moves"][-1]["at"] if game["moves"] else game["started"])
    if moment - last < WEEK:
        outcome.log = f"the side to move has until {stamp(last + WEEK)}"
        return outcome
    positions = replay(game)
    position, ply = positions[-1], len(game["moves"]) + 1
    legal = sorted(legal_moves(position), key=lambda move: move.uci)
    seed = hashlib.sha256(f"{game['game']}:{ply}:{stamp(last)}".encode()).digest()
    move = random.Random(int.from_bytes(seed, "big")).choice(legal)  # noqa: S311 - a fair pick, not a secret
    mover = {"player": None, "player_id": None, "issue": None, "arbiter": True}
    number = game["game"]
    name = named(position, number, ply, move)
    outcome, shown, end = apply(game, hall, positions, move, mover, owner, moment)
    # the reply goes on the issue of the game's last move, or, when the Arbiter opens a new game, of the move that
    # ended the one before
    issues = [earlier.get("issue") for earlier in game["moves"]]
    if not game["moves"] and hall:
        issues = [hall[-1].get("deciding", {}).get("issue")]
    outcome.issue = next((issue for issue in reversed(issues) if issue), None)
    board = f"[the board]({profile(owner)})"
    late = "GitHub" if position.turn == "b" else handle(owner)
    head = (f"⏰ **A week passed without a move from {late}**, so the Arbiter played {shown} for"
            f" {'Black' if position.turn == 'b' else 'White'}, at random.")
    if end:
        outcome.comment = f"{head}\n\n{ended_text(end, shown, number, mover, owner, name)}"
    else:
        turn = "w" if position.turn == "b" else "b"
        outcome.comment = f"{head}\n{name}\n{next_turn(turn, owner, shown.endswith('+'), board)}\n"
    outcome.commit = (f"chore(chess): ⏰ play {shown} for {'White' if position.turn == 'w' else 'Black'}"
                      f" after a week without a move\n\nMove {ply} of game {number}, by the Arbiter.")
    if end:
        outcome.commit += f" It ends the game {end.result}."
    outcome.log = f"the Arbiter played {shown}" + (f", {end.reason}" if end else "")
    return outcome


def link(owner: str, uci: str, game: int, ply: int) -> str:
    """The link that opens a move's ready-made issue in the intake, its title already written."""
    title = urllib.parse.quote(f"chess: {uci} \u00b7 game {game} \u00b7 move {ply}", safe="")
    return f"https://github.com/{owner}/play/issues/new?template=move.yml&title={title}"


def until(moment: dt.datetime) -> str:
    """A deadline as the page tells time: `18 Oct, 12:31 EST`."""
    local = moment.astimezone(EST)
    return f"{local.day} {local:%b}, {local:%H:%M} EST"


def day(moment: dt.datetime) -> str:
    """A day as the page's sheets letter it, in the page's time: `18 Oct`."""
    local = moment.astimezone(EST)
    return f"{local.day} {local:%b}"


def taken(game: dict, positions: list[Position]) -> dict:
    """What each side has taken so far, as piece letters: {"white": "pn", "black": "p"}."""
    took = {"white": "", "black": ""}
    for position, played in zip(positions, game["moves"]):
        move = Move.from_uci(played["uci"])
        piece = position.board[move.end]
        if not piece and position.board[move.start].lower() == "p" and move.end == position.ep:
            piece = "p"
        if piece:
            took["white" if position.turn == "w" else "black"] += piece.lower()
    return took


def score_sheet(game: dict, position: Position) -> list[list]:
    """The score sheet's latest rows: each move's number, White's move, Black's and who chose it, and the row the
    next move goes on."""
    moves, rows = game["moves"], []
    for i in range(0, len(moves), 2):
        black = moves[i + 1] if i + 1 < len(moves) else None
        rows.append([i // 2 + 1, moves[i]["san"], black["san"] if black else "", who(black) if black else ""])
    if position.turn == "w":
        rows.append([position.fullmove, "", "", ""])
    return rows[-ROWS:]


# The banner over the board stays on one line of the profile's README. Measured in the README's own type, a banner
# of up to this many characters, its markdown included, fits that line with room to spare.
BANNER = 91


def prompt(owner: str, white: bool, number: int, shown: str = "", arbiter: bool = False, check: bool = False,
           due: str = "", result: str = "") -> str:
    """The banner over the board, one line long (`BANNER`): whose turn it is, the move just played or how the last
    game ended, and the day the turn is due. The exact time and the rules go in the note under the moves."""
    by = f" by {due}" if due else ""
    alarm = "Check! " if check else ""
    if not white:
        mover = "The Arbiter" if arbiter else f"@{owner}"
        return f"🟢 **GitHub's turn!** {mover} played {shown}. {alarm}Pick a move below{by}."
    head = f"🛑 **@{owner}'s turn!**"
    if shown:
        return f"{head} {'The Arbiter' if arbiter else 'GitHub'} played {shown}. {alarm}Reply due{by}."
    if result:
        return f"{head} {result}. Game {number} opens{by}."
    return f"{head} @{owner} opens game {number} as White, and GitHub plays Black."


def board(game: dict | None, hall: list, owner: str) -> dict:
    """The page's chess element: what the board draws, and what the README carries round it."""
    current = game or {"game": 1, "started": None, "moves": []}  # a first game nobody has opened yet
    positions = replay(current)
    position, ply, number = positions[-1], len(current["moves"]) + 1, current["game"]
    groups: dict[str, list] = {}
    for entry in listing(position, number, ply):
        groups.setdefault(entry["piece"], []).append(
            [entry["emoji"], entry["title"], entry["san"], entry["words"], link(owner, entry["uci"], number, ply)])
    started = game is not None and (current["moves"] or current.get("started"))
    clock = parse(current["moves"][-1]["at"] if current["moves"] else current["started"]) + WEEK if started else None
    element = {"kind": "chess", "fen": position.fen, "game": number, "move": position.fullmove,
               "players": len(contributors(current))}
    if clock:
        element["due"] = day(clock)
    shown, arbiter = "", False
    if current["moves"]:
        played, before = current["moves"][-1], positions[-2]
        arbiter = bool(played.get("arbiter"))
        move = Move.from_uci(played["uci"])
        took = before.board[move.end] or ("p" if before.board[move.start].lower() == "p" and move.end == before.ep
                                          else "")
        shown = numbered(before, played["san"])
        element["last"] = {"san": played["san"], "from": label(move.start), "to": label(move.end),
                           "piece": PIECES[before.board[move.start].lower()], "captured": PIECES.get(took.lower(), ""),
                           "words": move_words(before, move), "by": who(played), "when": day(parse(played["at"]))}
    if in_check(position):
        element["check"] = label(king(position, position.turn))
    element["taken"] = taken(current, positions)
    element["history"] = score_sheet(current, position)
    due, checked = day(clock) if clock else "", in_check(position)
    if position.turn == "b":
        element["prompt"] = prompt(owner, False, number, shown, arbiter, checked, due)
        element["note"] = f"Anyone but @{owner} can play on this turn, and the first pick in is played."
    else:
        last = hall[-1] if hall and not shown else None  # the game that just ended, when this one has yet to start
        result = ""
        if last:
            result = (f"{'@' + owner if last['winner'] == owner else 'GitHub'} won game {last['game']}"
                      if last["winner"] else f"Game {last['game']} was drawn")
        element["prompt"] = prompt(owner, True, number, shown, arbiter, checked, due, result)
        element["note"] = (f"Only @{owner} can play on this turn: a pick from anyone else is turned away with a"
                           " comment on its issue.")
        if last and not last["winner"]:
            element["note"] = f"Game {last['game']} was drawn by {REASONS[last['reason']]}. {element['note']}"
    element["note"] += (f" The move is due by {until(clock)}, or the Arbiter plays a random legal move." if clock
                        else " A side that goes a week without moving gets a random legal move from the Arbiter.")
    if hall:
        element["note"] += (f" Every finished game is kept as a [PGN](https://github.com/{owner}/{owner}/tree/HEAD/"
                            ".github/chess/games).")
    element["moves"] = [{"piece": piece, "list": entries} for piece, entries in groups.items()]
    return element


def house_moves(game: dict) -> int:
    """How many of White's moves in the game the owner made: the Arbiter's are not theirs."""
    return sum(1 for index, played in enumerate(game["moves"]) if index % 2 == 0 and not played.get("arbiter"))


def leaders(hall: list, owner: str, game: dict | None = None) -> list[list]:
    """The leaderboard under the Hall of Fame: the owner's row on top, then GitHub's ten leading players, ranked by
    their wins and then by the moves they have played for GitHub. A row counts its player's moves, wins and games
    over every finished game and the one on the board, under the newest login they played as. A win is a mating
    move of one's own, and a move or a mate the Arbiter played counts for nobody, on either side. The owner's row
    stands from the start, at nought until they move."""
    house = {"login": owner, "moves": 0, "wins": 0, "games": 0}
    tally: dict[int, dict] = {}

    def player(player_id: int, login: str) -> dict:
        return tally.setdefault(player_id, {"login": login, "moves": 0, "wins": 0, "games": 0})

    games = [(record, record["house_moves"], record["players"]) for record in hall]
    games += [(None, house_moves(game), contributors(game))] if game else []
    for record, own, players in games:  # in the order they were played, so the last login seen is the newest
        house["moves"] += own
        house["games"] += 1 if own else 0
        for played in players:
            entry = player(played["player_id"], played["player"])
            entry["login"] = played["player"]
            entry["moves"] += played["moves"]
            entry["games"] += 1
        deciding = (record or {}).get("deciding", {})
        if record and record["reason"] == "checkmate" and not deciding.get("arbiter"):
            winner = house if record["winner"] == owner else player(deciding["player_id"], deciding["player"])
            winner["wins"] += 1  # a draw is nobody's win, and nor is the Arbiter's mate
    ranked = sorted(tally.values(), key=lambda e: (-e["wins"], -e["moves"], e["login"].casefold()))
    return [[e["login"], e["moves"], e["wins"], e["games"]] for e in (house, *ranked[:LEADERS])]


def hall_element(hall: list, owner: str, game: dict | None = None) -> dict:
    """The page's Hall of Fame: the series between the owner and GitHub, its leading winners, and the leaderboard
    under it. A win is a point for whoever made the mating move, the owner included; a draw
    scores nobody, and nor does the Arbiter's mate."""
    house = sum(1 for record in hall if record["winner"] == owner)
    world = sum(1 for record in hall if record["winner"] == "GitHub")
    wins: dict = {}
    for record in hall:
        deciding = record["deciding"]
        if record["reason"] != "checkmate" or deciding.get("arbiter"):
            continue
        key = owner if record["winner"] == owner else deciding["player_id"]
        entry = wins.setdefault(key, {"login": owner if key == owner else deciding["player"], "wins": 0})
        if key != owner:
            entry["login"] = deciding["player"]  # the newest login, should it have changed
        entry["wins"] += 1
        entry["last"] = record["ended"]
    for key, entry in wins.items():
        entry["games"] = len(hall) if key == owner else sum(
            1 for record in hall if any(p["player_id"] == key for p in record["players"]))
    ranked = sorted(wins.values(), key=lambda e: (-e["wins"], -parse(e["last"]).timestamp(), e["login"].casefold()))
    return {"kind": "chess-hall", "games": len(hall), "house": house, "world": world,
            "draws": len(hall) - house - world,
            "people": [[e["login"], e["wins"], day(parse(e["last"])), e["games"]] for e in ranked[:PODIUM]],
            "leaders": leaders(hall, owner, game), "measure": {}}


def flow(value) -> str:
    """A value as YAML's inline form, which JSON is: emoji and all written as themselves."""
    return json.dumps(value, ensure_ascii=False)


def element_yaml(eid: str, element: dict) -> str:
    """An element as an entry of the settings' `elements:` section: two spaces in, one field a line, each list's
    items one a line."""
    out = [f"  {eid}:"]
    for key, value in element.items():
        if key == "moves":
            out.append("    moves:")
            for group in value:
                out += [f"      - piece: {flow(group['piece'])}", "        list:"]
                out += [f"          - {flow(move)}" for move in group["list"]]
        elif key in ("history", "people", "leaders"):
            out.append(f"    {key}:" if value else f"    {key}: []")
            out += [f"      - {flow(row)}" for row in value]
        else:
            out.append(f"    {key}: {flow(value)}")
    return "".join(line + "\n" for line in out)


def set_out(settings: Path, elements: list[tuple[str, dict]]) -> bool:
    """Writes the elements between the settings' chess markers, when they changed. True when they did."""
    lines = settings.read_text(encoding="utf-8").splitlines(keepends=True)
    marks = [i for i, line in enumerate(lines) if line.strip() in ("# chess:start", "# chess:end")]
    if len(marks) != 2 or lines[marks[0]].strip() != "# chess:start":
        raise ValueError(f"{settings} needs one '# chess:start' line, then one '# chess:end' line, under elements:")
    a, b = marks
    new = "".join(lines[:a + 1]) + "".join(element_yaml(eid, el) for eid, el in elements) + "".join(lines[b:])
    if new == "".join(lines):
        return False
    settings.write_text(new, encoding="utf-8")
    return True


def load(folder: Path) -> tuple[dict | None, list]:
    path, hall = folder / "game.json", folder / "hall-of-fame.json"
    game = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return game, json.loads(hall.read_text(encoding="utf-8")) if hall.exists() else []


def dump(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def save(folder: Path, outcome: Outcome) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "game.json").write_text(dump(outcome.game), encoding="utf-8")
    if outcome.finished:
        (folder / "hall-of-fame.json").write_text(dump(outcome.hall), encoding="utf-8")
    if outcome.pgn:
        name, text = outcome.pgn
        (folder / "games").mkdir(exist_ok=True)
        (folder / "games" / name).write_text(text, encoding="utf-8")


def request_from(env: dict) -> Request | None:
    """The move the intake sent, checked again: None when there is none, an error when any part is malformed."""
    if not env.get("UCI"):
        return None
    checks = (("UCI", UCI), ("GAME", NUMBER), ("MOVE_NUMBER", NUMBER), ("PLAYER", LOGIN), ("PLAYER_ID", NUMBER))
    for name, shape in checks:
        if not shape.fullmatch(env.get(name, "")):
            raise ValueError(f"{name} is missing or malformed")
    issue = env.get("ISSUE", "")
    if issue and not NUMBER.fullmatch(issue):
        raise ValueError("ISSUE is malformed")
    return Request(env["UCI"], int(env["GAME"]), int(env["MOVE_NUMBER"]), int(issue) if issue else None,
                   env["PLAYER"], int(env["PLAYER_ID"]))


def main(argv: list[str] | None = None, env: dict | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path, help="where the game's state lives, .github/chess")
    parser.add_argument("--out", type=Path, help="where comment.md and commit.txt go (default: $RUNNER_TEMP)")
    parser.add_argument("--now", help="the time to play at, ISO 8601 (default: now)")
    parser.add_argument("--settings", type=Path, default=Path(".github/markdown.yaml"),
                        help="the page's settings, where the board is set out (default: .github/markdown.yaml)")
    args = parser.parse_args(argv)
    env = dict(os.environ) if env is None else env
    owner, owner_id = env.get("OWNER", ""), env.get("OWNER_ID", "")
    if not LOGIN.fullmatch(owner) or not NUMBER.fullmatch(owner_id):
        print("::error::OWNER and OWNER_ID name the player of White, and one is missing or malformed.")
        return 1
    try:
        request = request_from(env)
    except ValueError as exc:
        print(f"::error::The move was not played: {exc}.")
        return 1
    moment = parse(args.now) if args.now else now_utc()
    game, hall = load(args.folder)
    if request:
        outcome = play(game, hall, request, owner, int(owner_id), moment)
    else:
        outcome = tick(game, hall, owner, moment)
    if outcome.changed:
        save(args.folder, outcome)
    after = (outcome.game, outcome.hall) if outcome.changed else (game, hall)
    try:
        drawn = set_out(args.settings, [("chess", board(*after, owner)),
                                        ("chess-hall", hall_element(after[1], owner, after[0]))])
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    if drawn and not outcome.commit:
        outcome.commit = "chore(chess): 🖌️ set the board out for the page"
    out = args.out or Path(env.get("RUNNER_TEMP", "."))
    out.mkdir(parents=True, exist_ok=True)
    run = env.get("RUN_URL", "")
    (out / "comment.md").write_text(outcome.comment, encoding="utf-8")
    (out / "commit.txt").write_text(outcome.commit + (f"\n\nRun: {run}" if run and outcome.commit else "") + "\n",
                                    encoding="utf-8")
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if outcome.changed or drawn else 'false'}\n")
            handle.write(f"issue={outcome.issue or ''}\n")
    target = f" (game {request.game}, move {request.move}, @{request.player})" if request else ""
    print(f"{'Move ' + request.uci if request else 'Clock'}{target}: {outcome.log}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
