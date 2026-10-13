# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""A finished game as its replay draws it: every turn, with what it did on the board, who played it and when.

  from replays import due, facts, chess_facts, PAGE

A game won by a person's own move gets a replay: tannergolden/play's Replay
workflow hands these facts to the kit (tannergolden/markdown's `replay`
command), which plays the game again on its own board, move by move, and
loops. A draw gets none, and neither does a win the Arbiter's move made or a
Pentago turn that made five for the side that did not turn.

The engine knows the rules, so it writes what each turn did, and the kit only
draws it: for every turn its side, its notation as the score sheet numbers
it, its words, who played it (none for the Arbiter) and the day; and what it
did, in each game's own terms. Chess: the squares it went from and to, the
piece, the square of what it took, a castling rook's squares, a promotion and
the king it put in check. Checkers: every square the piece passed, the men
it took and whether it was crowned. Pentago: the hole, the quarter turned and
which way, whether the marble made five before any turn, and a ghost's hole.
Tic-Tac: the square, and the mark or a ghost. The facts go beside the game's
record, as games/game-<N>.replay.json. Stdlib only.
"""
from __future__ import annotations

from types import ModuleType

import chess_rules as CR
import checkers_rules as KR
import pentago_rules as PR
from page import GITHUB, HOUSE, day, parse

VERSION = 1  # the facts' shape, as the kit's replay command reads it
PAGE = "https://github.com/{owner}/play/blob/HEAD/replays/{key}/game-{game}.md"  # a replay's page in play


def due(record: dict) -> bool:
    """Whether a finished game gets a replay: a win, by a person's own move."""
    deciding = record.get("deciding") or {}
    return bool(record.get("winner")) and not deciding.get("arbiter") and deciding.get("own") is not False


def page(owner: str, key: str, game: int) -> str:
    return PAGE.format(owner=owner, key=key, game=game)


def name(game: int) -> str:
    return f"game-{game}.replay.json"


def who(played: dict) -> tuple[str | None, int | None]:
    """Who played a turn, by login and account ID: nobody for the Arbiter."""
    if played.get("arbiter"):
        return None, None
    return played["player"], played["player_id"]


def summary(key: str, game: dict, record: dict, owner: str, plies: list[dict], **more) -> dict:
    deciding = record["deciding"]
    return {"replay": VERSION, "kind": key, "game": game["game"],
            "winner": HOUSE if record["winner"] == owner else GITHUB, "by": deciding["player"],
            "by_id": deciding["player_id"], "issue": deciding.get("issue"), "reason": record["reason"],
            "line": record.get("line"), "started": game["started"], "ended": record["ended"], **more,
            "players": record["players"], "house_moves": record["house_moves"], "plies": plies}


# --- tic-tac, pentago and checkers --------------------------------------------------------------------------------
def what(key: str, before, code: str, side: str, ghost: bool) -> dict:
    """What one turn did on the board, in its game's own terms."""
    if key == "tictac":
        return {"cell": code, "mark": "G" if ghost else {HOUSE: "X", GITHUB: "O"}[side]}
    if key == "pentago":
        if ghost:
            return {"cell": code, "ghost": True}
        cell, quarter, way = PR.parse(code)
        return {"cell": cell, "quarter": quarter, "way": way, "unturned": PR.won_unturned(before, code)}
    move = KR.find(before, code)
    return {"path": list(move.path), "captures": list(move.captures), "crowns": move.crowns,
            "piece": before.pieces[move.path[0]]}


def facts(mod: ModuleType, game: dict, positions: list, record: dict, owner: str) -> dict:
    """A finished game of Tic-Tac, Pentago or Checkers as its replay draws it: every turn, its ghosts first.
    `positions` are the game's from its first to its last, as `games.replay` gives them."""
    import games  # the engine's own: imported here, as it imports this module

    plies, ghosts = [], games.ghosts_of(game)
    for turn, played in enumerate(games.turns(game), 1):
        side, ghost = games.side_of(mod, game, turn), turn <= len(ghosts)
        index = turn - len(ghosts)  # a move's place among the moves, from 1
        if ghost:
            last = games.last_move(mod, {**game, "ghosts": ghosts[:turn], "moves": []}, [])
            before = None
        else:
            last = games.last_move(mod, {**game, "moves": game["moves"][:index]}, positions[:index + 1])
            before = positions[index - 1]
        by, by_id = who(played)
        plies.append({"side": side, "notation": games.turn_named(mod, turn, last["move"]), "move": last["move"],
                      "words": last["words"], "by": by, "by_id": by_id, "when": day(parse(played["at"])),
                      **what(mod.KEY, before, played["move"], side, ghost)})
    more = {"places": game.get("places"), "opens": games.opener(mod, game)} if games.ghostly(mod) else {}
    return summary(mod.KEY, game, record, owner, plies, **more, final=record["final"])


# --- chess --------------------------------------------------------------------------------------------------------
def chess_facts(game: dict, positions: list, record: dict, owner: str) -> dict:
    """A finished game of Chess as its replay draws it: every move with its squares, what it took, a castling
    rook, a promotion and a king it put in check."""
    import chess  # the engine's own: imported here, as it imports this module

    plies = []
    for index, played in enumerate(game["moves"], 1):
        before, after = positions[index - 1], positions[index]
        last = chess.last_move({**game, "moves": game["moves"][:index]}, positions[:index + 1])
        move = CR.Move.from_uci(played["uci"])
        piece, took = before.board[move.start], before.board[move.end]
        taken_at = CR.label(move.end) if took else None
        if piece.lower() == "p" and move.end == before.ep:
            taken_at = CR.label(move.end - 8 if piece == "P" else move.end + 8)
        rook = None
        if piece.lower() == "k" and abs(move.end - move.start) == 2:
            rank = CR.label(move.start)[1]
            rook = [f"h{rank}", f"f{rank}"] if move.end > move.start else [f"a{rank}", f"d{rank}"]
        by, by_id = who(played)
        plies.append({"side": HOUSE if index % 2 else GITHUB, "notation": chess.numbered(before, played["san"]),
                      "move": played["san"], "words": last["words"], "by": by, "by_id": by_id,
                      "when": day(parse(played["at"])), "from": CR.label(move.start), "to": CR.label(move.end),
                      "piece": piece, "taken_at": taken_at, "rook": rook, "promotion": move.promotion or None,
                      "check": CR.label(CR.king(after, after.turn)) if CR.in_check(after) else None})
    return summary("chess", game, record, owner, plies, final=positions[-1].fen)
