# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named as an order to the airborne: an emoji, a title, and what the drop does in plain words.

  from connectfour_names import listing

Chess names its moves as orders to an army on the ground; Connect Four's come
from the sky, every disc a paratrooper dropped down a column: "Green Light,
Go!" for the first, "Hold the Drop Zone!" for the centre, "Plug the Gap!" for
a block, "Link Up, All Four!" for the win. Every title ends with "!" and
never names a column, since the notation beside it does.

`read` takes a drop apart for what it does: whether it connects four, blocks
a column the other side would win down, leaves such a column open, opens one
for them by filling the cell under it, or makes threats of its own, and where
it lands. The most telling of those is its theme. A drop that leaves the
other side free to win next is named as the blunder it is, under a warning
sign: "Leave the Gap Open!", "Into the Crossfire!".

The choice is seeded by the game, the move number and the position, so a
board names its moves the same way however often it is drawn, and no two
moves on one board share a title. Stdlib only, with connectfour_rules.py
beside it.
"""
from __future__ import annotations

import functools
import hashlib
import random
from dataclasses import dataclass

from connectfour_rules import COLOUR, Position, ending, legal, make, notation, other, threats

CALL = ("Troopers", "Jumpers", "Pathfinders", "Rangers", "Sky Troops", "Paratroopers")  # the ones an order calls to
# Each theme: the emoji it is drawn with, and its orders. A `{call}` is filled with one of CALL.
THEMES = {
    "win": (("🏆",), (
        "Link Up, All Four!", "Victory From the Sky!", "Four Down, Mission Done!", "Take the Objective!",
        "Mission Accomplished!", "Plant the Flag!", "Close the Ring, {call}!")),
    "counter": (("🪖",), (
        "Block and Counter!", "Hold and Hit Back!", "Stop Them, Then Strike!", "Seal the Gap and Push!")),
    "block": (("🛡️",), (
        "Plug the Gap!", "Seal the Breach!", "Cut Off Their Advance!", "Hold the Line!", "Close the Gap!",
        "Deny the Landing!", "Block the Drop!", "Stand Your Ground, {call}!")),
    "blunder": (("⚠️",), (
        "Leave the Gap Open!", "Abandon the Drop Zone!", "Miss the Landing!", "Drift Off Course!",
        "Jump Into the Wind!", "Look the Wrong Way!", "Land Behind Your Own Lines!", "Miss the Drop!")),
    "crossfire": (("⚠️",), (
        "Into the Crossfire!", "Land Under Their Guns!", "Open the Way for Them!", "Drop Into Their Sights!",
        "Build Their Ladder!", "Hand Them the High Ground!")),
    "fork": (("💥",), (
        "Pincer Them!", "Two Drop Zones at Once!", "Hit Them From Both Sides!", "Split Their Defence!",
        "Double Envelopment!")),
    "threat": (("🎯",), (
        "Set Up the Ambush!", "Dig In for the Win!", "Mark the Landing Zone!", "Line Up the Strike!",
        "Light the Beacon!", "Paint the Target, {call}!")),
    "first": (("🚦",), (
        "Green Light, Go!", "Hit the Silk!", "Jump, Jump, Jump!", "First Out the Door!", "Go, Go, Go!",
        "Lead the Stick!", "Out the Door, {call}!")),
    "centre": (("🪂",), (
        "Hold the Drop Zone!", "Seize the Centre!", "Drop Into the Heart of It!", "Take the Middle Ground!",
        "Own the Centre, {call}!")),
    "edge": (("🏔️",), (
        "Drop on the Flank!", "Hit the Far Ridge!", "Secure the Flank!", "Take the Ridge!",
        "Guard the Edge, {call}!")),
    "stack": (("🧗",), (
        "Stack the Squad!", "Reinforce From Above!", "Climb the Ladder!", "Build the Tower!", "Pile In, {call}!")),
    "drop": (("🪂",), (
        "Hit the Silk!", "Jump, Jump, Jump!", "Stick the Landing!", "Drop Behind Their Lines!", "Steady on the Drop!",
        "Boots on the Ground!", "Go Airborne, {call}!")),
}
URGE = (", Again!", ", Now!", ", at Once!")  # what a busy board puts on the end of a title already given
LONGEST = 48  # the longest title tannergolden/markdown takes
WORDS = 80  # the longest words tannergolden/markdown takes


@dataclass(frozen=True)
class Reading:
    """What one drop does, as a name reads it."""
    colour: str
    col: int
    row: int  # where the disc lands
    wins: tuple[tuple[int, int], ...] = ()  # the four it connects
    blocks: bool = False  # it drops down a column the other side would win down
    leaves: tuple[int, ...] = ()  # the columns the other side could already win down, still open after it
    opens: tuple[int, ...] = ()  # the columns it opens for the other side, by filling the cell under their win
    makes: tuple[int, ...] = ()  # the columns it can win down next, after it
    first: bool = False  # the first disc of the game
    stacks: bool = False  # it lands on a disc of its own


def read(position: Position, col: int) -> Reading:
    colour, row = position.turn, position.height(col) + 1
    after = make(position, col)
    end = ending(after)
    if end and end.winner:
        return Reading(colour, col, row, wins=end.line)
    before, now = threats(position, other(colour)), threats(after, other(colour))
    makes = tuple(threats(after, colour)) if not end else ()
    return Reading(colour, col, row, blocks=col in before, leaves=tuple(c for c in now if c in before),
                   opens=tuple(c for c in now if c not in before), makes=makes, first=not any(position.cells),
                   stacks=row > 1 and position.at(col, row - 1) == colour)


def theme(r: Reading) -> str:
    """The most telling thing the drop does, which its title is about."""
    if r.wins:
        return "win"
    if r.blocks:
        return "counter" if r.makes and not (r.leaves or r.opens) else "block"
    if r.leaves:
        return "blunder"
    if r.opens:
        return "crossfire"
    if r.makes:
        return "fork" if len(r.makes) > 1 else "threat"
    if r.first:
        return "first"
    if r.col == 4:
        return "centre"
    if r.col in (1, 7):
        return "edge"
    return "stack" if r.stacks else "drop"


def columns(found: tuple[int, ...]) -> str:
    """Columns as a sentence says them: `column 3`, `columns 3 and 6`, `columns 1, 3 and 6`."""
    names = [str(c) for c in found]
    said = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"column{'s' if len(names) > 1 else ''} {said}"


def words(position: Position, col: int) -> str:
    """The drop in plain words: `A black disc down column 4, to row 1`, `A white disc down column 7 blocks on row 2`,
    `A black disc down column 2 connects four on a diagonal`."""
    r = read(position, col)
    disc = f"A {COLOUR[r.colour]} disc down column {col}"
    if r.wins:
        (c0, r0), (c1, r1) = r.wins[0], r.wins[-1]
        where = f"across row {r0}" if r0 == r1 else f"up column {c0}" if c0 == c1 else "on a diagonal"
        return f"{disc} connects four {where}"
    text = f"{disc} blocks on row {r.row}" if r.blocks else f"{disc}, to row {r.row}"
    foe = COLOUR[other(r.colour)].capitalize()
    warning = (f", leaving {columns(r.leaves)} to {foe}" if r.leaves else
               f", opening {columns(r.opens)} to {foe}" if r.opens else "")
    threat = f", threatening {columns(r.makes)}" if r.makes else ""
    for said in (text + threat + warning, text + warning, text + threat, text):
        if len(said) <= WORDS:
            return said
    return text


def title(r: Reading, rng: random.Random, used: set[str]) -> tuple[str, str, str]:
    """One emoji and title for the drop, and the order it came from, drawn with `rng` from its theme: an order the
    board has not used yet, while the theme has one left."""
    emoji, orders = THEMES[theme(r)]
    pattern = rng.choice([order for order in orders if order not in used] or list(orders))
    name = pattern.format(call=rng.choice(CALL))
    if len(name) > LONGEST:
        name = pattern.replace(", {call}", "")
    return rng.choice([e for e in emoji if e not in used] or list(emoji)), name, pattern


def seed(position: Position, game: int, ply: int) -> int:
    """The board's seed: the same game, move and position always give the same names."""
    return int.from_bytes(hashlib.sha256(f"connectfour:{game}:{ply}:{position.board}".encode()).digest()[:8], "big")


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open column from the left, each with its notation, its words, an emoji and a title no other drop here
    has."""
    return [dict(entry) for entry in _listing(position, game, ply)]


@functools.lru_cache(maxsize=64)
def _listing(position: Position, game: int, ply: int) -> tuple[dict, ...]:
    base, seen, out = seed(position, game, ply), set(), []
    for col in legal(position):
        rng = random.Random(base ^ int.from_bytes(hashlib.sha256(str(col).encode()).digest()[:8], "big"))
        emoji, name, pattern = title(read(position, col), rng, seen)
        if name in seen:  # every order of the theme already given here: the last one, urged on
            name = next((name[:-1] + urge for urge in URGE if name[:-1] + urge not in seen), name)
        seen |= {name, pattern, emoji}
        out.append({"code": str(col), "notation": notation(position, col), "emoji": emoji, "title": name,
                    "words": words(position, col)})
    return tuple(out)
