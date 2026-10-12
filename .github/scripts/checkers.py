# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Checkers on the profile, the third tier of its four games, played by games.py as chess.py plays chess.

  python3 .github/scripts/games.py checkers .github/checkers

What the shared engine asks of the game: how a move is written, in an issue's
title, on the sheet and in a reply alike (`11-15` for a step, `22x15` for a
jump and `22x15x8` for a jump of two, a square for every landing), how a game
ends, what its board sets out for the page beside the fields every game
shares, and what it calls things.

American checkers on the 32 dark squares. The house opens every game, as
Dark, which moves first, and GitHub plays Light. A jump must be taken when
there is one, and goes on while it can; a man that reaches the far row is
crowned. A side left without a legal move on its turn loses, and the game is
drawn when the same position comes round a third time with the same side to
move, or after forty moves each with no jump and no man moved. The board
sets out the position as a PDN FEN (`fen`), the side that plays the dark men
(`dark`, the house), the kings each side has made (`kings`), that the side to
move must jump (`alert`), and whether the last move crowned its man. The
rules are checkers_rules.py's, the names checkers_names.py's, and a finished
game is kept as PDN. Stdlib only.
"""
from __future__ import annotations

import re

import checkers_names as N
import checkers_rules as R
from page import GITHUB, HOUSE, parse, profile

KEY, TITLE = "checkers", "Checkers"
EXT, RECORD = "pdn", "PDN"  # a finished game's file, and what the note's link calls it
ARBITER_OPENS = False  # the house opens every game, as Dark
SQ = r"(?:3[0-2]|[12][0-9]|[1-9])"
CODE = re.compile(rf"{SQ}(?:-{SQ}|(?:x{SQ})+)")  # a move as an issue's title carries it
FIRST, SECOND = "Dark", "Light"  # what each side is called: Dark moves first, and the house plays it
COLOUR = {R.DARK: FIRST, R.LIGHT: SECOND}
SIGN = {FIRST: "⛂", SECOND: "⛀"}
LEAD = SIGN  # what a reply and a commit lead with: the mover's man
RULE = "A jump must be taken whenever there is one, and a man that reaches the far row is crowned."
DRAWN = {"repetition": "by repetition", "forty moves": "by the forty-move rule"}


def start() -> R.Position:
    return R.START


def moves(position: R.Position) -> list:
    """Every legal move, by the squares it passes, from the dark side's back row."""
    return sorted(R.legal_moves(position), key=lambda move: tuple(move.path))


def legal(position: R.Position) -> list[str]:
    return [move.code for move in moves(position)]


def found(position: R.Position, code: str):
    move = R.find(position, code)
    if move is None:
        raise ValueError(f"{code} is not a legal move in {position.fen}")
    return move


def make(position: R.Position, code: str) -> R.Position:
    return R.make(position, found(position, code))


def notation(position: R.Position, code: str) -> str:
    return code


def shown(position: R.Position, code: str) -> str:
    return code


def why_illegal(position: R.Position, code: str) -> str:
    return R.why_illegal(position, code)


def final(position: R.Position) -> str:
    return position.fen


def ending(positions: list[R.Position], codes: list[str]) -> tuple[bool | None, str, None] | None:
    """How the game ends, if it does: whether Dark, the opener, won, and how."""
    played = [found(position, code) for position, code in zip(positions, codes)]
    end = R.ending(positions, played)
    if end is None:
        return None
    return (None if end.winner is None else end.winner == R.DARK), end.reason, None


def listing(position: R.Position, game: int, ply: int) -> list[dict]:
    """Every legal move, by the squares it passes, each with its notation, its words, an emoji and a title no other
    move here has."""
    named = sorted(N.named(position), key=lambda entry: tuple(entry[0].path))
    return [{"code": move.code, "notation": move.code, "emoji": emoji, "title": title, "words": words}
            for move, emoji, title, words in named]


def jumps(position: R.Position) -> bool:
    """Whether the side to move has a jump to take, which it must."""
    return R.must_jump(position)


def pressure(position: R.Position) -> tuple[str, str]:
    """What the side to move faces, as a reply's last line says it to the house, and of GitHub."""
    return ("and a jump must be taken", "with a jump to take") if jumps(position) else ("", "")


def alarm(position: R.Position) -> str:
    """What a reply's first line calls out after the move, as chess's calls a check."""
    return " A jump must be taken!" if jumps(position) else ""


def calls(position: R.Position) -> list[str]:
    """What the banner tells the side to move, longest first."""
    return ["A jump must be taken! ", "Must jump! "] if jumps(position) else []


def kings(game: dict, positions: list[R.Position]) -> dict[str, int]:
    """The kings each side has made: every man of theirs crowned, the house's Dark and GitHub's Light."""
    made = {HOUSE: 0, GITHUB: 0}
    for index, played in enumerate(game["moves"]):
        if found(positions[index], played["move"]).crowns:
            made[HOUSE if index % 2 == 0 else GITHUB] += 1
    return made


def fields(game: dict, positions: list[R.Position], over: bool) -> dict:
    """The board's own fields: the position, the side with the dark men, the kings each side has made, and while
    the game goes on, a jump the side to move must take."""
    out: dict = {"fen": positions[-1].fen, "dark": HOUSE, "kings": kings(game, positions)}
    if not over and jumps(positions[-1]):
        out["alert"] = "must jump"
    return out


def marked(before: R.Position, code: str) -> dict:
    """Anything more the last move tells the board: that it crowned its man."""
    return {"crowned": True} if found(before, code).crowns else {}


def cry(end, loser: str) -> str:
    """The winning reply's call."""
    return f"{loser} has no move left!"


def summary(end, positions: list[R.Position]) -> str:
    """How the game ended, as the final board's banner says it."""
    if end.first is not None:
        return f"{SECOND if end.first else FIRST} has no move left"
    if end.reason == "repetition":
        return "The same position came round a third time"
    return "Forty moves each without a jump or a man moved"


def opening(code: str) -> list[str]:
    """The house opens every game itself, so the Arbiter never names an opening here."""
    return [code]


def record(game: dict, positions: list[R.Position], kept: dict, owner: str) -> str:
    """The finished game as PDN: the house as Black, PDN's name for the side that moves first, GitHub as White, the
    result, and every move followed by who played it, as the chess game's PGN has it."""
    started, ended = parse(game["started"]), parse(kept["ended"])
    headers = {"Event": f"@{owner} vs. GitHub", "Site": profile(owner), "Date": started.strftime("%Y.%m.%d"),
               "Round": str(game["game"]), "Black": owner, "White": "GitHub", "Result": kept["result"],
               "PlyCount": str(len(game["moves"])), "EndDate": ended.strftime("%Y.%m.%d")}
    texts = [f"{played['move']} {{{'the Arbiter, after a week' if played.get('arbiter') else played['player']}}}"
             for played in game["moves"]]
    if kept["winner"]:
        note = f"{SECOND if kept['winner'] == owner else FIRST} has no move left."
    else:
        note = f"Drawn {DRAWN[kept['reason']]}."
    return R.pdn(texts, headers, kept["result"], note=note)
