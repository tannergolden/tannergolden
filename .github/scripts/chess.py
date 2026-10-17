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
reply saying why, and nothing changes. With no UCI the run is the clock, as
.github/scripts/clock.py runs it for every game twice an hour: when the side
to move has gone a week without moving, the Arbiter plays a legal move for it
at random, and says so on the issue of the move it answers, once, and after
that in the owner's logbook.

A game ends when the rules end it, never by resigning or agreeing a draw.
Its record goes into the Hall of Fame and its moves into a PGN, and its final
board stays up for two days: until then nothing can be played, and a move
sent meanwhile is told the day the next game opens. Then the next game's
fresh board comes by itself, with the owner to open it, and the week for its
first move counts from then.

  .github/chess/game.json           the game on the board: its number, start and moves, and while a final board is
                                    up, the game that ended
  .github/chess/hall-of-fame.json   every finished game: result, deciding move, players, the owner's moves
  .github/chess/games/game-N.pgn    each finished game, every move with who played it
  .github/chess/games/game-N.replay.json
                                    a game a person's own move won: what each move did, for its replay (replays.py)

After every run it sets the board out for the page: the position, the last
move in words with who played it when, any check, whose turn it is and until
when, how many have played for GitHub, what each side has taken, the score
sheet's latest rows, and every legal move named by chess_names.py, with a
link that opens its ready-made issue; or, while a final board is up, the
final position, who won and how, and the day the next game opens, with
nothing to play. It goes between the `# chess:start` and `# chess:end` lines
of .github/markdown.yaml, and the Hall of Fame of all four games (hall.py)
between `# hall:start` and `# hall:end`, and nothing else in that file, for
tannergolden/markdown to draw in the page's one theme.

It writes comment.md, the reply to post, and commit.txt into the run's
temporary folder (--out), and sets `changed`, `issue`, `logbook`, `replay`,
`ruling` and `game` as step outputs: whether the page is to be drawn again,
the issue the reply goes on, whether it goes in the owner's logbook of the
Arbiter's moves instead, whether a person's own move won the game, for the
workflow to ask tannergolden/play for its replay, whose page the final board
links, the ruling on a player's move, `played` or `turned away`, by which the
workflow labels and closes its issue, and the game whose milestone that issue
joins: the one the move was sent for, or none for a game there never was.
Both are empty for the clock, and a move already on the board from its own
issue is `played`. A request that is not in the form the intake sends is
turned away on its issue like any move that can't be played.
Stdlib only, with chess_rules.py, chess_names.py, hall.py and page.py beside it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import random
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import hall as halls
import replays
from chess_names import listing
from chess_names import words as move_words
from chess_rules import (
    START,
    Ending,
    Move,
    Position,
    attacked,
    ending,
    in_check,
    king,
    label,
    legal_moves,
    make,
    other,
    pseudo_moves,
    san,
    side,
    square,
)
from page import (
    DISPLAY,
    EST,
    WEEK,
    day,
    dump,
    handle,
    load,
    now_utc,
    parse,
    profile,
    sentences,
    set_out,
    stamp,
    until,
)

__all__ = ["EST", "WEEK", "dump", "load", "now_utc", "stamp", "until"]

GROUPS = {"k": "king", "q": "queen", "r": "rook", "b": "bishop", "n": "knight", "p": "pawn"}
ROWS = 3  # the score sheet's latest rows
UCI = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?")
COUNT = re.compile(r"[1-9][0-9]{0,8}")  # a game or a move: up to 999,999,999, as the page's links carry
ID = re.compile(r"[1-9][0-9]{0,15}")  # an issue or an account: up to 16 digits, as the intake passes on
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
REASONS = {
    "stalemate": "stalemate",
    "fivefold repetition": "fivefold repetition",
    "seventy-five-move rule": "the seventy-five-move rule",
    "insufficient material": "insufficient material",
    "dead position": "a dead position",
}
# How a finished board says a game ended, as the page's plate takes it (`result.how`).
HOW = {"checkmate": "checkmate", "stalemate": "stalemate", "fivefold repetition": "fivefold repetition",
       "seventy-five-move rule": "seventy-five moves", "insufficient material": "insufficient material",
       "dead position": "dead position"}
OPENS = ("⏳ **Game {number} opens {day}**, so `{uci}` wasn't played.\n"
         "Game {ended}'s final board stays up until then: pick a move from {board} once game {number} is on it.\n")


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
    replay: tuple[str, dict] | None = None  # a won game's replay facts, and their file's name
    log: str = ""
    finished: dict | None = None  # the finished game's Hall of Fame record
    redraw: bool = False  # nothing to save, but the page is drawn again: a run of the last move over again
    logbook: bool = False  # the comment goes in the owner's logbook of the Arbiter's moves, not on a player's issue
    ruling: str = ""  # on a player's move, "played" or "turned away": how its issue is labelled and closed
    filed: int | None = None  # the game whose milestone that issue joins: the one it was sent for, if there is one


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
    start, end = square(uci[0:2]), square(uci[2:4])
    if piece.lower() == "k" and start in (4, 60) and abs(end - start) == 2:
        return why_not_castle(position, start, end)
    if uci[:4] in {move.uci[:4] for move in pseudo_moves(position)}:
        if piece.lower() == "k":
            return f"the king can't step into check on {uci[2:4]}"
        if in_check(position):
            return "your king is in check, and this move doesn't get it out"
        bare = list(position.board)
        bare[start] = ""
        if attacked(tuple(bare), king(position, position.turn), other(position.turn)):
            return f"the {PIECES[piece.lower()]} on {uci[0:2]} is pinned to your king"
        return "it would leave your king in check"
    return f"the {PIECES[piece.lower()]} on {uci[0:2]} can't move to {uci[2:4]}"


def why_not_castle(position: Position, start: int, end: int) -> str:
    """Why the king can't castle where it was sent: the right gone, a piece in the way, or check on its path."""
    kingside = end > start
    wing = "kingside" if kingside else "queenside"
    right = ("K" if kingside else "Q") if position.turn == "w" else ("k" if kingside else "q")
    if right not in position.castling:
        return f"the right to castle {wing} is gone: the king or that rook has moved, or the rook was taken"
    rook = start + 3 if kingside else start - 4
    if any(position.board[i] for i in range(min(start, rook) + 1, max(start, rook))):
        return f"the squares between the king and the rook must be empty to castle {wing}"
    enemy = other(position.turn)
    if attacked(position.board, start, enemy):
        return "the king can't castle out of check"
    crossed = start + 1 if kingside else start - 1
    if attacked(position.board, crossed, enemy):
        return f"the king can't castle across {label(crossed)}, which is under attack"
    return "the king can't castle into check"


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
    """Plays a legal move into the game; when it ends the game, records it, and sets the next game to come two days
    on, its board showing the one that ended until then."""
    position = positions[-1]
    name = san(position, move)
    shown = numbered(position, name)
    game = {**{key: value for key, value in game.items() if key != "ended"},
            "moves": [*game["moves"], {"uci": move.uci, "san": name, **mover, "at": stamp(moment)}]}
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
        if replays.due(record):
            outcome.replay = (replays.name(game["game"]), replays.chess_facts(game, positions, record, owner))
        outcome.game = {**new_game(game["game"] + 1, moment + DISPLAY), "ended": game}
    return outcome, shown, end


def ended_text(end: Ending, shown: str, number: int, mover: dict, owner: str, name: str, opens: dt.datetime) -> str:
    """What the reply says when a move ends the game: how it ended, the move that did it, and when the next game
    opens, once the final board's two days are up."""
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
    return (f"{head}\n{name}\nIts final board stays up for two days: game {number + 1} opens {day(opens)}, and"
            f" @{owner} opens it as White.\n")


def played_text(shown: str, white: bool, player: str, name: str, owner: str, board: str) -> str:
    """The reply to a move that is played and leaves the game going: the move, its name, and whose turn it is."""
    check = shown.endswith("+")
    alarm = " Check!" if check else ""
    if white:
        return f"♟️ **{shown} is on the board.{alarm}**\n{name}\n{next_turn('b', owner, check, board)}\n"
    return (f"♟️ **{shown} is on the board.{alarm}** Well played, @{player}.\n{name}\n"
            f"{next_turn('w', owner, check, board)}\n")


def same(played: dict, request: Request) -> bool:
    """Whether a move on record came from this very request: the same issue, the same move and the same player. A
    run made over again, such as a re-run of its job, finds its own move already played."""
    return (request.issue is not None and played.get("issue") == request.issue and not played.get("arbiter")
            and played.get("player_id") == request.player_id)


def play(game: dict | None, hall: list, request: Request, owner: str, owner_id: int,
         moment: dt.datetime) -> Outcome:
    """One move from the intake: played, or turned away with the reason."""
    current = game or new_game(1, moment)
    number, board = current["game"], f"[the board]({profile(owner)})"
    # A move for a game that never was joins no milestone, so a title can't make one up.
    outcome = Outcome(game=game, hall=hall, issue=request.issue, filed=request.game if request.game <= number else None)

    def refuse(text: str, log: str, ruling: str = "turned away") -> Outcome:
        outcome.comment, outcome.log, outcome.ruling = text, log, ruling
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
                          f" issue.\n{later}\n", "already played from this issue", "played")
    if waiting:
        return refuse(OPENS.format(number=number, day=day(parse(current["started"])), uci=request.uci,
                                   ended=number - 1, board=board), "the last game's final board is up")
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
        if earlier["uci"] == request.uci and same(earlier, request):
            if request.move == ply - 1:  # the last move on the board: answer as when it was played, and draw again
                before = positions[-2]
                outcome.redraw = True
                name = named(before, number, request.move, Move.from_uci(earlier["uci"]))
                return refuse(played_text(shown, before.turn == "w", request.player, name, owner, board),
                              "already played from this issue", "played")
            return refuse(f"✅ **{shown} is already on the board**, played from this issue.\nThe game has moved on"
                          f" since: pick a move from {board} as it stands now.\n", "already played from this issue",
                          "played")
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
    outcome.issue, outcome.ruling, outcome.filed = request.issue, "played", number
    if end:
        outcome.comment = ended_text(end, shown, number, mover, owner, name, moment + DISPLAY)
        outcome.commit = f"chore(chess): 🏆 play {shown}, ending game {number} {end.result}"
    else:
        outcome.comment = played_text(shown, position.turn == "w", request.player, name, owner, board)
        outcome.commit = f"chore(chess): ♟️ play {shown} in game {number}"
    outcome.commit += f"\n\nMove {ply}, by {request.player}."
    outcome.log = f"played {shown}" + (f", {end.reason}" if end else "")
    return outcome


def tick(game: dict | None, hall: list, owner: str, moment: dt.datetime) -> Outcome:
    """The clock: after a week without a move, the Arbiter plays one at random for the side to move. The week of a
    game's first move counts from the moment its fresh board came."""
    outcome = Outcome(game=game, hall=hall)
    if game is None:
        outcome.log = "no game has started"
        return outcome
    if not game["moves"] and parse(game["started"]) > moment:
        outcome.log = f"game {game['game'] - 1}'s final board is up until {game['started']}"
        return outcome
    last = parse(game["moves"][-1]["at"] if game["moves"] else game["started"])
    if moment - last < WEEK:
        outcome.log = f"the side to move has until {stamp(last + WEEK)}"
        return outcome
    positions = replay(game)
    position, ply = positions[-1], len(game["moves"]) + 1
    legal = sorted(legal_moves(position), key=lambda move: move.uci)
    seed = hashlib.sha256(f"{game['game']}:{ply}:{stamp(last)}".encode()).digest()
    move = random.Random(int.from_bytes(seed, "big")).choice(legal)  # a fair pick, not a secret
    mover = {"player": None, "player_id": None, "issue": None, "arbiter": True}
    number = game["game"]
    name = named(position, number, ply, move)
    outcome, shown, end = apply(game, hall, positions, move, mover, owner, moment)
    # The notice goes on the issue of the move the Arbiter answers, once: its first move after a player's (the move
    # that ended the last game, when it opens the next) is told there, and a move after another of its own goes in
    # the owner's logbook, so no player's issue collects a notice a week and none is lost.
    before = game["moves"][-1] if game["moves"] else (hall[-1]["deciding"] if hall else None)
    if before and not before.get("arbiter") and before.get("issue"):
        outcome.issue = before["issue"]
    else:
        outcome.logbook = True
    board = f"[the board]({profile(owner)})"
    late = "GitHub" if position.turn == "b" else handle(owner)
    head = (f"⏰ **A week passed without a move from {late}**, so the Arbiter played {shown} for"
            f" {'Black' if position.turn == 'b' else 'White'}, at random.")
    if end:
        outcome.comment = f"{head}\n\n{ended_text(end, shown, number, mover, owner, name, moment + DISPLAY)}"
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
    title = urllib.parse.quote(f"chess: {uci} · game {game} · move {ply}", safe="")
    return f"https://github.com/{owner}/play/issues/new?template=move.yml&title={title}"


def taken(game: dict, positions: list[Position]) -> dict:
    """What each side has taken so far, as piece letters: {"white": "bp", "black": "p"}."""
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


def last_move(game: dict, positions: list[Position]) -> dict:
    """The last move as the board shows it: its notation, its squares and pieces, its words, who played it, the day."""
    played, before = game["moves"][-1], positions[-2]
    move = Move.from_uci(played["uci"])
    took = before.board[move.end] or ("p" if before.board[move.start].lower() == "p" and move.end == before.ep
                                      else "")
    return {"san": played["san"], "from": label(move.start), "to": label(move.end),
            "piece": PIECES[before.board[move.start].lower()], "captured": PIECES.get(took.lower(), ""),
            "words": move_words(before, move), "by": who(played), "when": day(parse(played["at"]))}


def kept(owner: str) -> str:
    return f"Every finished game is kept as a [PGN](https://github.com/{owner}/{owner}/tree/HEAD/.github/chess/games)."


def board(game: dict | None, hall: list, owner: str, moment: dt.datetime) -> dict:
    """The page's chess element: what the board draws, and what the README carries round it."""
    current = game or {"game": 1, "started": None, "moves": []}  # a first game nobody has opened yet
    if current.get("ended") and not current["moves"] and parse(current["started"]) > moment:
        return finished(current, hall, owner)
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
    if current["moves"]:
        element["last"] = last_move(current, positions)
    if in_check(position):
        element["check"] = label(king(position, position.turn))
    element["taken"] = taken(current, positions)
    element["history"] = score_sheet(current, position)
    if position.turn == "b":
        element["note"] = f"Anyone but @{owner} can play on this turn, and the first pick in is played."
    else:
        last = hall[-1] if hall and not current["moves"] else None  # the game that ended, this one yet to start
        element["note"] = (f"Only @{owner} can play on this turn: a pick from anyone else is turned away with a"
                           " comment on its issue.")
        if last:
            ended = (f"{'@' + owner if last['winner'] == owner else 'GitHub'} won game {last['game']}."
                     if last["winner"] else f"Game {last['game']} was drawn by {REASONS[last['reason']]}.")
            element["note"] = f"{ended} {element['note']}"
    element["note"] += (f" The move is due by {until(clock)}, or the Arbiter plays a random legal move." if clock
                        else " A side that goes a week without moving gets a random legal move from the Arbiter.")
    if hall:
        element["note"] += f" {kept(owner)}"
    element["moves"] = [{"piece": piece, "list": entries} for piece, entries in groups.items()]
    return element


def finished(game: dict, hall: list, owner: str) -> dict:
    """The board while a finished game's final board is up: the final position, who won and how, its last move and
    score sheet, and the day the next game opens, with nothing left to play."""
    ended, opens = game["ended"], parse(game["started"])
    record = next((r for r in reversed(hall) if r["game"] == ended["game"]), None) or {}
    positions = replay(ended)
    position, number = positions[-1], ended["game"]
    end = ending(positions)
    winner = {"w": "house", "b": "github"}.get(end.winner or "") if end else None
    element = {"kind": "chess", "fen": position.fen, "game": number, "move": position.fullmove,
               "players": len(contributors(ended)), "next": day(opens), "next_at": stamp(opens)}
    if ended["moves"]:
        element["last"] = last_move(ended, positions)
    if in_check(position):
        element["check"] = label(king(position, position.turn))
    if end:
        element["result"] = {"winner": winner, "how": HOW[end.reason]}
    element["taken"] = taken(ended, positions)
    element["history"] = score_sheet(ended, position)
    deciding = record.get("deciding") or {}
    over = (f"Game {number} is over, and its final board stays up for two days: game {number + 1} opens"
            f" {until(opens)}, and nothing can be played until then.")
    nobody = ("The winning move was the Arbiter's, played after a week without one, so the win counts for nobody."
              if winner and deciding.get("arbiter") else "")
    watch = (f"🎬 [Watch the replay]({replays.page(owner, 'chess', number)}) of every move."
             if replays.due(record) else "")
    element["note"] = sentences([(over, True), (nobody, True), (watch, True), (kept(owner), False)])
    return element


def house_moves(game: dict) -> int:
    """How many of White's moves in the game the owner made: the Arbiter's are not theirs."""
    return sum(1 for index, played in enumerate(game["moves"]) if index % 2 == 0 and not played.get("arbiter"))


def save(folder: Path, outcome: Outcome) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "game.json").write_text(dump(outcome.game), encoding="utf-8")
    if outcome.finished:
        (folder / "hall-of-fame.json").write_text(dump(outcome.hall), encoding="utf-8")
    if outcome.pgn:
        name, text = outcome.pgn
        (folder / "games").mkdir(exist_ok=True)
        (folder / "games" / name).write_text(text, encoding="utf-8")
    if outcome.replay:
        name, facts = outcome.replay
        (folder / "games").mkdir(exist_ok=True)
        (folder / "games" / name).write_text(dump(facts), encoding="utf-8")


def request_from(env: dict) -> Request | None:
    """The move the intake sent, checked again: None when there is none, an error when any part is malformed."""
    if not env.get("UCI"):
        return None
    checks = (("UCI", UCI), ("GAME", COUNT), ("MOVE_NUMBER", COUNT), ("PLAYER", LOGIN), ("PLAYER_ID", ID))
    for name, shape in checks:
        if not shape.fullmatch(env.get(name, "")):
            raise ValueError(f"{name} is missing or malformed")
    issue = env.get("ISSUE", "")
    if issue and not ID.fullmatch(issue):
        raise ValueError("ISSUE is malformed")
    return Request(env["UCI"], int(env["GAME"]), int(env["MOVE_NUMBER"]), int(issue) if issue else None,
                   env["PLAYER"], int(env["PLAYER_ID"]))


def regions(root: Path, owner: str, owner_id: int, moment: dt.datetime) -> dict:
    """The settings' regions a chess run writes: its board, and the Hall of Fame of all four games, from the state
    in the checkout."""
    states = halls.load(root)
    return {"chess": [("chess", board(*states["chess"], owner, moment))],
            "hall": [("hall-of-fame", halls.element(states, owner, owner_id))]}


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
    if not LOGIN.fullmatch(owner) or not ID.fullmatch(owner_id):
        print("::error::OWNER and OWNER_ID name the player of White, and one is missing or malformed.")
        return 1
    malformed = ""
    try:
        request = request_from(env)
    except ValueError as exc:
        if not ID.fullmatch(env.get("ISSUE", "")):  # nowhere to say so
            print(f"::error::The move was not played: {exc}.")
            return 1
        request, malformed = None, str(exc)
    moment = parse(args.now) if args.now else now_utc()
    game, hall = load(args.folder)
    if malformed:
        outcome = Outcome(game=game, hall=hall, issue=int(env["ISSUE"]), log=f"turned away, {malformed}",
                          ruling="turned away",
                          comment=f"🚫 **This move can't be played as sent**, so nothing was played.\nEvery move listed"
                                  f" under [the board]({profile(owner)}) opens its issue ready-made: pick one there"
                                  " and send it unchanged.\n")
    elif request:
        outcome = play(game, hall, request, owner, int(owner_id), moment)
    else:
        outcome = tick(game, hall, owner, moment)
    if outcome.changed:
        save(args.folder, outcome)
    try:
        drawn = set_out(args.settings, regions(args.folder.parent, owner, int(owner_id), moment))
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
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle_:
            handle_.write(f"changed={'true' if outcome.changed or drawn or outcome.redraw else 'false'}\n")
            handle_.write(f"issue={outcome.issue or ''}\n")
            handle_.write(f"logbook={'true' if outcome.logbook else 'false'}\n")
            handle_.write(f"replay={'true' if outcome.replay else 'false'}\n")
            handle_.write(f"ruling={outcome.ruling}\n")
            handle_.write(f"game={outcome.filed or ''}\n")
    target = f" (game {request.game}, move {request.move}, @{request.player})" if request else ""
    print(f"{'Move ' + request.uci if request else 'Move' if malformed else 'Clock'}{target}: {outcome.log}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
