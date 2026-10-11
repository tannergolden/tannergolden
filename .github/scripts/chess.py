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
  .github/chess/hall-of-fame.json   every finished game: result, deciding move, players
  .github/chess/games/game-N.pgn    each finished game, every move with who played it

It writes comment.md, the reply to post, and commit.txt into the run's
temporary folder (--out), and sets `changed` and `issue` as step outputs.
Stdlib only, with chess_rules.py beside it.
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
from dataclasses import dataclass
from pathlib import Path

from chess_rules import START, Ending, Move, Position, ending, legal_moves, make, pseudo_moves, san, side, square

WEEK = dt.timedelta(days=7)
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


def who(played: dict) -> str:
    return "the Arbiter" if played.get("arbiter") else f"@{played['player']}"


def why_illegal(position: Position, uci: str) -> str:
    """Why a move that is not legal is not, in a few words."""
    piece = position.board[square(uci[0:2])]
    if not piece:
        return f"there is no piece on {uci[0:2]}"
    if side(piece) != position.turn:
        return f"the {PIECES[piece.lower()]} on {uci[0:2]} is {'White' if side(piece) == 'w' else 'Black'}'s"
    legal = {move.uci for move in legal_moves(position)}
    if len(uci) == 4 and uci + "q" in legal:
        return f"a pawn reaching the last rank has to say what it becomes, such as {uci}q"
    if len(uci) == 5 and uci[:4] in legal:
        return f"only a pawn reaching the last rank names a piece to become, so it is {uci[:4]}"
    if any(move.uci == uci for move in pseudo_moves(position)):
        return "it would leave the king in check"
    return f"the {PIECES[piece.lower()]} on {uci[0:2]} cannot move to {uci[2:4]}"


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
        deciding = {"move": shown, **{key: mover[key] for key in ("player", "player_id", "arbiter")}}
        winner = {"w": owner, "b": "GitHub"}.get(end.winner or "")
        record = {"game": game["game"], "result": end.result, "reason": end.reason, "winner": winner,
                  "plies": len(game["moves"]), "started": game["started"], "ended": stamp(moment),
                  "deciding": deciding, "players": contributors(game)}
        outcome.hall = [*hall, record]
        outcome.finished = record
        outcome.pgn = (f"game-{game['game']}.pgn", pgn(game, positions, end, owner, moment))
        outcome.game = new_game(game["game"] + 1, moment)
    return outcome, shown, end


def ended_text(end: Ending, shown: str, number: int, mover: dict, owner: str) -> str:
    """What the reply says when a move ends the game, and that the next one has started."""
    if end.reason == "checkmate":
        if end.winner == "w":
            head = f"🏆 **{shown}: checkmate.** @{owner} wins game {number}" + (
                ", with the Arbiter's move." if mover.get("arbiter") else ".")
        elif mover.get("arbiter"):
            head = f"🏆 **{shown}: checkmate.** GitHub wins game {number}, with the Arbiter's move."
        else:
            head = (f"🏆 **{shown}: checkmate.** GitHub wins game {number}, and @{mover['player']} goes into"
                    " the Hall of Fame for the winning move.")
    else:
        head = f"🤝 **{shown}: game {number} is drawn by {REASONS[end.reason]}.**"
    return f"{head} Game {number + 1} starts now, and @{owner} opens it as White.\n"


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
        return refuse(f"⌛ **Game {request.game} is over**, so {request.uci} was not played. Game {number} is on"
                      f" {board} now: pick a move there.\n", "an earlier game")
    if request.game > number:
        return refuse(f"❓ **There is no game {request.game} yet**, so {request.uci} was not played. Game {number}"
                      f" is on {board}: pick a move there.\n", "a later game")
    positions = replay(current)
    position, ply = positions[-1], len(current["moves"]) + 1
    if request.move < ply:
        earlier = current["moves"][request.move - 1]
        shown = numbered(positions[request.move - 1], earlier["san"])
        by = "you" if not earlier.get("arbiter") and earlier["player_id"] == request.player_id else who(earlier)
        return refuse(f"⌛ **The board moved on**, so {request.uci} was not played: move {request.move} is"
                      f" already on it, {shown}, by {by}. Pick a move from {board} as it stands now.\n", "stale")
    if request.move > ply:
        return refuse(f"❓ **The board is on move {ply}**, not move {request.move}, so {request.uci} was not"
                      f" played. Pick a move from {board}.\n", "a later move")
    is_owner = request.player_id == owner_id
    if position.turn == "w" and not is_owner:
        return refuse(f"⏳ **It is {owner}'s turn as White**, so {request.uci} was not played. GitHub plays Black,"
                      f" and its turn comes next, on {board}.\n", "White's turn")
    if position.turn == "b" and is_owner:
        return refuse(f"⏳ **It is GitHub's turn as Black**, so {request.uci} was not played: anyone but you plays"
                      " Black's moves. Your turn comes next.\n", "Black's turn")
    moves = {move.uci: move for move in legal_moves(position)}
    if request.uci not in moves:
        return refuse(f"🚫 **{request.uci} is not a legal move here**: {why_illegal(position, request.uci)}."
                      f" Nothing was played. Pick a move from {board}.\n", "illegal")

    mover = {"player": request.player, "player_id": request.player_id, "issue": request.issue, "arbiter": False}
    outcome, shown, end = apply(current, hall, positions, moves[request.uci], mover, owner, moment)
    outcome.issue = request.issue
    if end:
        outcome.comment = ended_text(end, shown, number, mover, owner)
        outcome.commit = f"chore(chess): 🏆 play {shown}, ending game {number} {end.result}"
    elif position.turn == "w":
        outcome.comment = (f"♟️ **{shown} is on the board.** It is GitHub's turn: anyone but @{owner} can play"
                           f" the next move, from {board}.\n")
        outcome.commit = f"chore(chess): ♟️ play {shown} in game {number}"
    else:
        outcome.comment = f"♟️ **{shown} is on the board**, played by @{request.player}. @{owner}, it is your move.\n"
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
    outcome, shown, end = apply(game, hall, positions, move, mover, owner, moment)
    for earlier in reversed(game["moves"]):
        if earlier.get("issue"):
            outcome.issue = earlier["issue"]
            break
    board = f"[the board]({profile(owner)})"
    if position.turn == "b":
        text = (f"⏰ **A week went by without a move from GitHub**, so the Arbiter played {shown} at random"
                f" for Black.")
        follow = f" @{owner}, it is your move.\n"
    else:
        text = (f"⏰ **A week went by without a move from {owner}**, so the Arbiter played {shown} at random"
                f" for White.")
        follow = f" It is GitHub's turn: anyone but {owner} can play the next move, from {board}.\n"
    outcome.comment = text + (" " + ended_text(end, shown, number, mover, owner) if end else follow)
    outcome.commit = (f"chore(chess): ⏰ play {shown} for {'White' if position.turn == 'w' else 'Black'}"
                      f" after a week without a move\n\nMove {ply} of game {number}, by the Arbiter.")
    if end:
        outcome.commit += f" It ends the game {end.result}."
    outcome.log = f"the Arbiter played {shown}" + (f", {end.reason}" if end else "")
    return outcome


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
    out = args.out or Path(env.get("RUNNER_TEMP", "."))
    out.mkdir(parents=True, exist_ok=True)
    run = env.get("RUN_URL", "")
    (out / "comment.md").write_text(outcome.comment, encoding="utf-8")
    (out / "commit.txt").write_text(outcome.commit + (f"\n\nRun: {run}" if run and outcome.commit else "") + "\n",
                                    encoding="utf-8")
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if outcome.changed else 'false'}\n")
            handle.write(f"issue={outcome.issue or ''}\n")
    target = f" (game {request.game}, move {request.move}, @{request.player})" if request else ""
    print(f"{'Move ' + request.uci if request else 'Clock'}{target}: {outcome.log}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
