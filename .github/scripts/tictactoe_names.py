# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open cell named as a call across a duel: an emoji, a title, and what the move does in plain words.

  from tictactoe_names import listing

Chess names its moves as orders to an army; Tic-Tac-Toe is a duel, and every
title is a call across it: "Strike the Heart!" for the centre, "Parry the
Thrust!" for a block, "Strike the Final Blow!" for the win. Every title ends
with "!" and never names a cell, since the notation beside it does.

`read` takes a move apart for what it does: whether it wins, blocks a line
the other side would win on, leaves such a line open, or makes threats of
its own, and which cell it takes. The most telling of those is its theme. A
move that leaves the other side free to win next is named as the blunder it
is, under a warning sign: "Drop Your Guard!", "Look Away!".

The choice is seeded by the game, the move number and the position, so a
board names its moves the same way however often it is drawn, and no two
moves on one board share a title. Stdlib only, with tictactoe_rules.py beside
it.
"""
from __future__ import annotations

import functools
import hashlib
import random
from dataclasses import dataclass

from tictactoe_rules import CENTRE, CORNERS, Position, ending, legal, make, notation, other, threats

# What each cell is called in a move's words: the centre, a corner, or the middle of an edge.
CELL_WORDS = {"b2": "the centre", "a1": "the lower left corner", "c1": "the lower right corner",
              "a3": "the upper left corner", "c3": "the upper right corner", "b1": "the foot of the board",
              "b3": "the head of the board", "a2": "the left edge", "c2": "the right edge"}
CALL = ("Duelist", "Swordsman", "Fencer", "Champion", "Challenger", "Master")  # the one a call is shouted to
# Each theme: the emoji it is drawn with, and its calls. A `{call}` is filled with one of CALL.
THEMES = {
    "win": (("🏆",), (
        "Strike the Final Blow!", "Finish the Duel!", "Land the Killing Thrust!", "End It in One Stroke!",
        "Run Them Through!", "Win the Bout!", "Claim the Duel!", "Take the Match, {call}!", "Seal It With Steel!")),
    "riposte": (("🤺",), (
        "Parry and Riposte!", "Block and Strike Back!", "Turn Their Blade and Answer!", "Parry, Then Thrust!",
        "Answer Steel With Steel!", "Turn the Tables, {call}!")),
    "block": (("🛡️",), (
        "Parry the Thrust!", "Block the Blade!", "Turn Their Point Aside!", "Catch Their Steel!",
        "Deflect the Strike!", "Meet Their Blade!", "Stop the Lunge!", "Guard the Gap, {call}!")),
    "blunder": (("⚠️",), (
        "Drop Your Guard!", "Turn Your Back on the Blade!", "Lower Your Shield!", "Look Away!",
        "Step Into the Thrust!", "Leave Your Flank Open!", "Ignore the Blade!", "Bare Your Chest!",
        "Forget the Point at Your Throat!")),
    "fork": (("🤺", "⚡"), (
        "Feint Left, Strike Right!", "Two Blades at Once!", "Strike From Both Sides!", "Double the Attack!",
        "Split Their Guard!", "Threaten Twice, {call}!")),
    "threat": (("⚔️", "🎯"), (
        "Lunge!", "Press the Attack!", "Close the Distance!", "Thrust at the Gap!", "Force Their Hand!",
        "Go on the Attack!", "Point Your Blade, {call}!", "Advance, {call}!")),
    "centre": (("🎯",), (
        "Strike the Heart!", "Take the Centre Ground!", "Hold the Centre!", "Seize the Middle of the Ring!",
        "Plant Your Feet!", "Own the Ring, {call}!")),
    "corner": (("🗡️", "📐"), (
        "Take the High Ground!", "Corner Them!", "Hold the Corner!", "Back Them Into a Corner!", "Seize the Angle!",
        "Cut the Angle!", "Take the Edge of the Ring!")),
    "edge": (("🪶", "👣"), (
        "Circle the Flank!", "Side-Step!", "Test Their Guard!", "Feel Out Their Defence!", "Probe the Line!",
        "Measure the Distance!", "Dance Along the Edge, {call}!")),
}
URGE = (", Again!", ", Now!", ", at Once!")  # what a busy board puts on the end of a title already given
LONGEST = 48  # the longest title tannergolden/markdown takes


@dataclass(frozen=True)
class Reading:
    """What one move does, as a name reads it."""
    mark: str
    cell: str
    wins: tuple[str, ...] = ()  # the line it completes
    blocks: bool = False  # it takes a cell the other side would win on
    leaves: tuple[str, ...] = ()  # the cells the other side can still win on, after it
    makes: tuple[str, ...] = ()  # the cells it can win on next, after it


def read(position: Position, cell: str) -> Reading:
    mark = position.turn
    after = make(position, cell)
    end = ending(after)
    if end and end.winner:
        return Reading(mark, cell, wins=end.line)
    return Reading(mark, cell, blocks=cell in threats(position, other(mark)),
                   leaves=tuple(threats(after, other(mark))), makes=tuple(threats(after, mark)) if not end else ())


def theme(r: Reading) -> str:
    """The most telling thing the move does, which its title is about."""
    if r.wins:
        return "win"
    if r.blocks:
        return "riposte" if r.makes else "block"
    if r.leaves:
        return "blunder"
    if r.makes:
        return "fork" if len(r.makes) > 1 else "threat"
    return "centre" if r.cell == CENTRE else "corner" if r.cell in CORNERS else "edge"


def cells(found: tuple[str, ...]) -> str:
    return " and ".join(found)


def words(position: Position, cell: str) -> str:
    """The move in plain words: `X takes the centre`, `O blocks on c2, threatening a3`, `X takes a3, three in a row
    from a3 to c1`."""
    r = read(position, cell)
    if r.wins:
        return f"{r.mark} takes {cell}, three in a row from {r.wins[0]} to {r.wins[-1]}"
    text = f"{r.mark} blocks on {cell}" if r.blocks else f"{r.mark} takes {CELL_WORDS[cell]}"
    if r.makes:
        text += f", threatening {cells(r.makes)}"
    if r.leaves:
        text += f", leaving {cells(r.leaves)} to {other(r.mark)}"
    return text


def title(r: Reading, rng: random.Random, used: set[str]) -> tuple[str, str, str]:
    """One emoji and title for the move, and the call it came from, drawn with `rng` from its theme: a call the
    board has not used yet, while the theme has one left."""
    emoji, calls = THEMES[theme(r)]
    pattern = rng.choice([call for call in calls if call not in used] or list(calls))
    name = pattern.format(call=rng.choice(CALL))
    if len(name) > LONGEST:
        name = pattern.replace(", {call}", "")
    return rng.choice([e for e in emoji if e not in used] or list(emoji)), name, pattern


def seed(position: Position, game: int, ply: int) -> int:
    """The board's seed: the same game, move and position always give the same names."""
    return int.from_bytes(hashlib.sha256(f"tictactoe:{game}:{ply}:{position.board}".encode()).digest()[:8], "big")


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open cell as the board is read, each with its notation, its words, an emoji and a title no other move
    here has."""
    return [dict(entry) for entry in _listing(position, game, ply)]


@functools.lru_cache(maxsize=64)
def _listing(position: Position, game: int, ply: int) -> tuple[dict, ...]:
    base, seen, out = seed(position, game, ply), set(), []
    for cell in legal(position):
        rng = random.Random(base ^ int.from_bytes(hashlib.sha256(cell.encode()).digest()[:8], "big"))
        emoji, name, pattern = title(read(position, cell), rng, seen)
        if name in seen:  # every call of the theme already given here: the last one, urged on
            name = next((name[:-1] + urge for urge in URGE if name[:-1] + urge not in seen), name)
        seen |= {name, pattern, emoji}
        out.append({"code": cell, "notation": notation(position, cell), "emoji": emoji, "title": name,
                    "words": words(position, cell)})
    return tuple(out)
