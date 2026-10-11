#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: an emoji, a title, and what the move does in plain English.

  from chess_names import listing, words

`read` takes a move apart for what it does: which piece moves and from where,
what it takes, whether it checks, discovers a check, mates or stalemates,
castles or promotes, whether it forks, leaves its home square, takes the
center, runs for the last rank, retreats, or steps where it can be taken for
nothing. The most telling of those picks the move's theme, and the theme
builds its title from phrases of its own and from words kept for each piece,
each piece taken and each part of the board: a knight's move reads as
cavalry's and a pawn's as a footsoldier's, a capture names what fell, and a
place names where it happened. The phrases and words between them make
millions of titles, so two boards seldom share one.

The choice is seeded by the game, the move number and the position, so a board
names its moves the same way however often it is drawn, and differently in
another game, and no two moves on one board share a title. Stdlib only, with
chess_rules.py beside it.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import random
from dataclasses import dataclass

from chess_rules import (DIAGONAL, FILES, KING, KNIGHT, ORTHOGONAL, Move, Position, attacked, in_check, legal_moves,
                         make, other, san, side, step)

PIECES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100}
ORDER = "kqrbnp"  # the list's order: the king's moves first, the pawns' last
CENTER = {27, 28, 35, 36}  # d4, e4, d5 and e5
HOME = {"w": {1: "n", 6: "n", 2: "b", 5: "b", 3: "q", 0: "r", 7: "r", 4: "k"},
        "b": {57: "n", 62: "n", 58: "b", 61: "b", 59: "q", 56: "r", 63: "r", 60: "k"}}
FIANCHETTO = {"w": {9, 14}, "b": {49, 54}}  # b2 and g2, b7 and g7

# --- the words each piece is made of ---------------------------------------------------------------------------
ADJ = {
    "n": ("Galloping", "Midnight", "Crooked", "Restless", "Thundering", "Wild", "Wandering", "Silver", "Hooded",
          "Daring", "Phantom", "Nimble", "Moonlit", "Sudden", "Reckless", "Feral", "Errant", "Swift"),
    "b": ("Holy", "Silent", "Slanted", "Hallowed", "Solemn", "Shadowed", "Gilded", "Oblique", "Pious", "Sacred",
          "Candlelit", "Cloistered", "Devout", "Veiled", "Distant", "Patient"),
    "r": ("Stone", "Iron", "Granite", "Unyielding", "Towering", "Grim", "Steadfast", "Heavy", "Rumbling",
          "Fortified", "Thunderous", "Relentless", "Ironbound", "Weathered", "Mighty"),
    "q": ("Royal", "Imperial", "Sovereign", "Radiant", "Fearless", "Relentless", "Starlit", "Regal", "Gilded",
          "Majestic", "Tempestuous", "Glittering", "Unbowed", "Peerless"),
    "k": ("Royal", "Weary", "Careful", "Stately", "Solemn", "Measured", "Defiant", "Cautious", "Ancient",
          "Unhurried", "Crowned", "Lonely"),
    "p": ("Humble", "Steady", "Brave", "Muddy", "Stubborn", "Patient", "Lowly", "Dauntless", "Weathered", "Loyal",
          "Unsung", "Faithful", "Gritty", "Plucky"),
}
NOUN = {
    "n": ("Charge", "Gallop", "Leap", "Canter", "Raid", "Sortie", "Foray", "Ride", "Pounce", "Stride", "Hoofbeat",
          "Vanguard", "Outrider", "Errand", "Hop", "Joust"),
    "b": ("Blessing", "Sermon", "Pilgrimage", "Diagonal", "Vigil", "Benediction", "Procession", "Prayer", "Psalm",
          "Vespers", "Litany", "Crusade", "Homily", "Absolution"),
    "r": ("Siege", "Rampart", "Tower", "Bulwark", "Barbican", "Watchtower", "Parapet", "Portcullis", "Citadel",
          "Battering Ram", "Wall", "Keep", "Bastion", "Advance"),
    "q": ("Tempest", "Decree", "Reach", "Command", "Edict", "Storm", "Wrath", "Grace", "Sovereignty", "Procession",
          "Audience", "Proclamation", "Sweep", "Verdict"),
    "k": ("Stroll", "Step", "Walk", "March", "Procession", "Vigil", "Refuge", "Progress", "Pilgrimage", "Promenade",
          "Passage"),
    "p": ("March", "Advance", "Stride", "Footfall", "Muster", "Trudge", "Vanguard", "Shield Wall", "Pike Line",
          "Sally"),
}
# How each piece goes somewhere: the patterns that take it to a place use these.
MOVE = {
    "n": ("Gallop", "Ride", "Charge", "Leap", "Canter", "Raid", "Sortie", "Foray", "Hop", "Pounce"),
    "b": ("Procession", "Pilgrimage", "Passage", "Crossing", "Glide", "Journey", "Progress"),
    "r": ("Advance", "Roll", "March", "Lift", "Rumble", "Sweep", "Drive"),
    "q": ("Sweep", "Procession", "Flight", "Advance", "Progress", "Glide", "Surge"),
    "k": ("Stroll", "Walk", "Progress", "Step", "Promenade", "Passage"),
    "p": ("March", "Advance", "Stride", "Trudge", "Muster", "Sally", "Step"),
}
# What each piece does when it takes something.
STRIKE = {
    "n": ("Ambush", "Raid", "Charge", "Trampling", "Onslaught"),
    "b": ("Judgement", "Smiting", "Verdict", "Reckoning", "Penance"),
    "r": ("Onslaught", "Siege", "Breach", "Battering", "Avalanche"),
    "q": ("Wrath", "Justice", "Fury", "Vengeance", "Decree"),
    "k": ("Blade", "Reprisal", "Justice"),
    "p": ("Ambush", "Uprising", "Revolt", "Skirmish", "Pitchfork"),
}
FIERCE = ("Ruthless", "Merciless", "Savage", "Grim", "Bloody", "Brutal", "Pitiless", "Cold", "Swift", "Fearsome")
EMOJI = {
    "n": ("🐴", "🐎", "🏇", "🦄", "🌙"), "b": ("⛪", "🕯️", "📿", "🕊️", "📜", "🔔"),
    "r": ("🏰", "🗼", "🧱", "🛡️", "🪨", "⛓️"), "q": ("👸", "👑", "💎", "🌪️", "🌟", "⚜️"),
    "k": ("🤴", "👑", "🚶", "🛡️", "🏰"), "p": ("🥾", "🛡️", "🚩", "🌱", "👣", "🪖"),
}

# --- the themes: each a list of title patterns, and the emoji it is drawn from ------------------------------------
# A pattern's fields: {P} the piece that moves, {T} the piece it takes, {sq} where it lands, {place} a name for that
# part of the board, {adj}, {noun} and {move} from the moving piece's words, {fierce} and {strike} for a capture,
# {file} the file it lands on.
THEMES = {
    "mate": (("💀", "☠️", "🏁", "👑"), (
        "The Final Word", "Long Live the Board", "Checkmate on {sq}", "The Last Bell", "The Crown Falls", "Game Over",
        "The Throne Is Taken", "The End of the Road", "The {P}'s Final Word", "Mate at {place}")),
    "smothered": (("💀", "🐴"), ("The Smothered Mate", "Smothered", "No Room to Breathe")),
    "back-rank": (("💀", "🏁"), ("The Back-Rank Mate", "Trapped on the Back Rank", "No Way Out")),
    "stalemate": (("🧊", "🤝"), (
        "The Frozen Throne", "Nowhere to Run", "Peace by Default", "The Stalemate Trap", "A Draw from Nowhere")),
    "crown": (("👑", "⭐", "✨"), (
        "A Crown for a Footsoldier", "Rise Through the Ranks", "From Pawn to Queen", "The Coronation",
        "Long Live the New Queen", "The Long Road Ends", "A Queen Is Born on {sq}")),
    "crown-taking": (("👑", "🩸"), ("Crowned in Blood", "A Crown Taken by Force", "The Bloody Coronation")),
    "underpromote": (("🎖️", "✨"), ("Knighted in the Field", "A Humbler Crown", "The Unexpected {P}", "Raised to {P}")),
    "castle-king": (("🏰", "🏯"), (
        "Raise the Drawbridge", "Into the Keep", "The Kingside Fortress", "Close the Gates", "Safe Behind the Walls",
        "The King Takes Shelter")),
    "castle-queen": (("🏰", "🏯"), (
        "The Long Castle", "The Queenside Citadel", "Across the Great Hall", "The Grand Retreat", "Castle Long")),
    "double": (("🌩️", "⚡"), (
        "Twin Thunder", "The Pincer", "Two Swords Drawn", "Double Jeopardy", "The Crossfire", "Nowhere to Hide")),
    "discovery": (("🎭", "🪞"), (
        "The Veil Lifts", "Unmasked", "Out of the Shadows", "The Hidden Blade", "Behind the Curtain", "Revealed")),
    "royal-fork": (("🍴", "🔱"), ("The Royal Fork", "Crown and Queen", "The Grand Fork", "A Fork for the Family")),
    "fork": (("🍴", "🔱"), (
        "Two Birds, One Stone", "The Fork in the Road", "The Trident", "Double Trouble", "Two Targets, One {P}",
        "The {adj} Fork")),
    "queen-taken": (("💔", "⚰️", "👑"), (
        "The Queen Is Fallen", "Dethroned", "The Crown Topples", "Fall of the Queen", "The Queen's Last Stand",
        "Queenslayer", "No Queen Survives {place}")),
    "strike": (("🌩️", "⚡"), (
        "Blood and Thunder", "Strike and Warn", "{T} Down, King Next", "Take and Threaten", "A Blow and a Warning",
        "The {fierce} {strike}")),
    "passing": (("👻",), ("En Passant", "In Passing", "The Ghost Capture", "Caught in Passing", "The Phantom Strike")),
    "first-blood": (("🩸", "🗡️"), ("First Blood", "First Blood on {sq}", "The First to Fall", "Opening Blood",
                                  "The First {strike}", "First Blood at {place}", "The {T} Falls First")),
    "giant": (("🪨", "⚔️"), ("Giant Slayer", "David and Goliath", "The Peasant's Revenge", "Pitchforks Raised",
                            "A Pawn Fells the {T}", "The {T} Felled at {sq}")),
    "capture": (("⚔️", "🗡️", "🩸", "💥", "🪓", "🏹"), (
        "Blood for Blood", "The Fall of the {T}", "Down Goes the {T}", "{T}slayer", "No Quarter for the {T}",
        "Spoils of {sq}", "The {fierce} {strike}", "{fierce} Harvest on {sq}", "The {T} Falls at {place}",
        "A {T} for the Taking", "Cut Down on {sq}", "The Reckoning", "Break Their Ranks")),
    "check": (("⚡", "🔔", "🎯", "📯", "🚨"), (
        "Sound the Alarm", "The King Trembles", "A Knock at the Gate", "The Bell Tolls", "Check from {place}",
        "The {adj} Warning", "Eyes on the Crown", "Target the King", "The Throne Shakes", "Royal Summons")),
    "offering": (("🎲", "🎁", "🦁"), (
        "The Bold Offering", "A Gift for the Enemy", "Into the Lion's Den", "Fortune Favors the Bold", "Bait on {sq}",
        "The Daring Sacrifice", "Come and Take It", "The {adj} Gamble", "A {adj} {move} into Danger",
        "A {P} for the Taking", "The {P} Stands Alone", "Alone at {place}", "Unguarded on {sq}",
        "Daring Them to Take {sq}")),
    "doorstep": (("🌠", "✨"), (
        "Within Sight of the Crown", "One Step from Glory", "The Crown Beckons", "Knocking at the Palace Door",
        "Almost Crowned", "The Last Step but One", "The {adj} {move} to {sq}")),
    "runner": (("🏃", "💨"), (
        "The Runaway", "Nothing in the Way", "The Open Road Home", "Freedom March", "The Lone Runner",
        "Chasing the Crown", "The {adj} Runaway", "A Clear Road from {sq}")),
    "stride": (("👣", "🥾"), (
        "Two Steps Forward", "The Long Stride", "The Bold Advance", "Double Time", "Two Squares to {sq}",
        "The {adj} Double Step")),
    "center": (("🎯", "🏛️", "🧭"), (
        "Take the Center", "Heart of the Board", "Claim the Crossroads", "Stake a Claim at {sq}",
        "The {adj} {move} to the Center", "Hold the High Ground", "The {adj} Claim on {sq}", "Center Stage at {sq}")),
    "develop": (("🌅", "🚪"), (
        "Into the Fray", "First Light", "Off the Back Rank", "The {adj} Debut", "The First {move}",
        "The {adj} {move} Begins", "A {adj} Debut at {sq}", "The {P} Enters the Fray", "A {adj} Start on {sq}")),
    "fianchetto": (("🔭", "🎯"), (
        "The Fianchetto", "The Long Watch", "Eye on the Long Diagonal", "The Hidden Sniper", "The {adj} Watch")),
    "seventh": (("🐗", "🔥"), (
        "Pig on the Seventh", "Behind Enemy Lines", "The Raid on the Seventh", "The {adj} {move} to the Seventh")),
    "open-file": (("🛣️",), (
        "The Open Road", "Command of the {file}-File", "Down the {file}-File", "Master of the {file}-File",
        "The Open File")),
    "sortie": (("👸",), (
        "Her Majesty's Early Outing", "The Queen Rides Out", "An Early Audience", "The Queen Will Not Wait",
        "The Queen's Early {move} to {sq}", "Her Majesty Rides to {place}", "An Early {move} for the Queen")),
    "royal-walk": (("🚶", "🤴"), (
        "The King's Walk", "A Royal Stroll", "The King Takes the Field", "The Wandering Monarch",
        "One Small Step for the Crown", "The {adj} {move}", "The Royal Progress", "The Monarch Moves",
        "The Crown on the Move", "A Royal Visit to {place}", "The King Surveys {place}", "The {adj} King")),
    "rim": (("🌑", "🌲"), ("Dim on the Rim", "The Edge of the Map", "Lost in the Woods", "The Lonely Outpost",
                          "A {adj} {move} to the Rim", "Dim on {sq}", "The Lonely Ride to {sq}")),
    "retreat": (("↩️", "🔙", "🧭"), (
        "Strategic Withdrawal", "Fall Back to {place}", "Regroup", "The Long Way Home", "A Tactical Retreat",
        "The {adj} Retreat", "Back to {place}", "The {move} Home", "A {adj} {move} Back to {sq}",
        "The {P} Withdraws to {sq}", "Regroup at {place}")),
    "long": (("🏹", "🌠"), ("Across the Board", "The Long {move}", "From Edge to Edge", "The Far Reach",
                           "The {adj} Sweep")),
    "quiet": ((), (
        "The {adj} {noun}", "{adj} {noun}", "The {move} to {place}", "A {adj} {move} to {sq}", "The {P}'s {move}",
        "{move} toward {place}")),
}
# Each piece adds phrases of its own to a theme.
OWN = {
    ("develop", "n"): ("Saddle Up", "Out of the Stables", "The Cavalry Rides Out"),
    ("develop", "b"): ("Out of the Cloister", "The Bishop Takes Up Office", "The First Sermon"),
    ("capture", "n"): ("The Ambush on {sq}", "Trampled Underhoof", "The Cavalry Strikes", "Hooves over the {T}"),
    ("capture", "b"): ("Judgement on {sq}", "The Bishop's Verdict", "Excommunicated", "Smite the {T}"),
    ("capture", "r"): ("The Ram Breaks Through", "Crushed Under Stone", "The Siege of {sq}", "The Walls Close In"),
    ("capture", "q"): ("The Queen's Justice", "Royal Wrath on {sq}", "By Royal Decree", "Her Majesty Collects"),
    ("capture", "k"): ("The King's Own Blade", "The King Draws His Sword", "The Crown Bares Its Teeth"),
    ("capture", "p"): ("The Footsoldier's Prize", "Pitchforks Raised"),
    ("check", "n"): ("Hooves at the Throne", "The Knight's Challenge"),
    ("check", "b"): ("The Bishop's Accusation", "A Slanted Threat"),
    ("check", "r"): ("The Ram at the Door", "Siege of the King"),
    ("check", "q"): ("The Queen's Ultimatum", "Her Majesty Demands"),
    ("check", "p"): ("The Footsoldier's Challenge", "A Pitchfork at the Throne"),
    ("fork", "n"): ("The Knight's Fork", "The Cavalry Splits Them"),
    ("fork", "p"): ("The Pitchfork", "The Peasant's Fork"),
    ("mate", "p"): ("The Peasant's Revenge", "Mate by a Footsoldier"),
    ("mate", "q"): ("The Queen's Final Word", "Long Live the Queen"),
    ("quiet", "p"): ("Forward March", "One Step Closer", "Shield Wall", "Plant the Flag", "Boots on the Ground",
                     "The Infantry Advances", "Small Beginnings", "Taking Root", "Hold the Field", "Brick by Brick"),
    ("quiet", "n"): ("The Cavalry Charge", "Flanking Maneuver", "Knight Errant", "The Unexpected Leap", "Over the Wall",
                     "Hoofbeats", "The Wild Hop", "Night Ride", "Across the Field"),
    ("quiet", "b"): ("The Bishop's Blessing", "The Long Diagonal", "Holy Fire", "A Divine Angle", "The Cathedral Path",
                     "Eclipse", "Wings of the Church"),
    ("quiet", "r"): ("Hold the Line", "Siege Tower", "The Watchtower", "Fortress Wall", "Raise the Ramparts",
                     "Man the Walls", "The Iron Gate", "Stone by Stone", "Hold the Bridge", "Drop Anchor"),
    ("quiet", "q"): ("Her Majesty Advances", "The Queen's Tempest", "The Royal Hunt", "Crown Jewel",
                     "Star of the Court", "Royal Decree", "Her Royal Reach", "The Queen's Sight", "Shooting Star"),
    ("quiet", "k"): ("A Royal Stroll", "The Last Stand", "The King Steps Aside", "Close the Gates",
                     "The Royal Retreat"),
}
# What a part of the board is called, from the side of the piece that lands there.
PLACES = {
    "center": ("the Crossroads", "the Heart of the Board", "the Center", "the Market Square", "the High Ground"),
    "throne": ("the Enemy Throne Room", "the Enemy Gates", "the Last Rank", "the Far Shore"),
    "deep": ("Enemy Lines", "the Enemy's Doorstep", "the Far Bank", "Hostile Ground"),
    "middle": ("No Man's Land", "the Front", "the Middle Ground", "the Border"),
    "home": ("Home Ground", "the Near Fields", "the Home Front", "Friendly Soil"),
    "queenside": ("the Queen's Wing", "the Queenside", "the Western Marches"),
    "kingside": ("the King's Wing", "the Kingside", "the Eastern Woods"),
    "rim": ("the Edge of the Map", "the Rim", "the Board's Edge"),
}


@dataclass(frozen=True)
class Reading:
    """What one move does, as a name reads it."""
    kind: str  # the piece that moves: p, n, b, r, q or k
    start: int
    end: int
    turn: str  # w or b
    taken: str = ""  # the kind it takes
    passing: bool = False  # it takes en passant
    castle: str = ""  # "king" or "queen", the side it castles to
    crown: str = ""  # what a pawn becomes on the last rank
    check: bool = False
    double: bool = False  # two pieces give check at once
    discovered: bool = False  # the check comes from a piece the move uncovered
    mate: bool = False
    stalemate: bool = False
    fork: tuple[str, ...] = ()  # what the moved piece attacks at once, when two or more are worth having
    first: bool = False  # the piece leaves its starting square
    exposed: bool = False  # it lands where it can be taken and nothing of its own defends it
    advance: int = 0  # ranks gained toward the other side, negative for a retreat
    distance: int = 0  # squares travelled, the longer way
    first_blood: bool = False  # the game's first capture
    passed: bool = False  # a pawn with no pawn of the other side ahead of it, on its file or beside it
    smothered: bool = False  # a knight's mate on a king boxed in by its own pieces
    back_rank: bool = False  # a mate on the back rank the king never left
    open_file: bool = False  # a rook on a file with no pawns


def rank_of(index: int, turn: str) -> int:
    """The square's rank as the side to move counts it, from 0 for its own back rank to 7 for the other's."""
    return index // 8 if turn == "w" else 7 - index // 8


def reach(board: tuple[str, ...], index: int) -> list[int]:
    """The squares the piece on `index` attacks."""
    piece = board[index]
    kind, forward = piece.lower(), 1 if side(piece) == "w" else -1
    if kind == "p":
        return [t for t in (step(index, -1, forward), step(index, 1, forward)) if t is not None]
    if kind in "nk":
        return [t for df, dr in (KNIGHT if kind == "n" else KING) if (t := step(index, df, dr)) is not None]
    out = []
    for df, dr in {"b": DIAGONAL, "r": ORTHOGONAL, "q": ORTHOGONAL + DIAGONAL}[kind]:
        target = step(index, df, dr)
        while target is not None:
            out.append(target)
            if board[target]:
                break
            target = step(target, df, dr)
    return out


def read(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> Reading:
    """What the move does: every trait a name can be made from. `after` and `replies`, the position the move makes
    and the other side's legal moves there, save working them out again when they are known."""
    board, turn = position.board, position.turn
    kind = board[move.start].lower()
    enemy = other(turn)
    passing = kind == "p" and move.end == position.ep and not board[move.end]
    taken = "p" if passing else board[move.end].lower()
    castle = "" if kind != "k" or abs(move.end - move.start) != 2 else ("king" if move.end > move.start else "queen")
    after = make(position, move) if after is None else after
    check = in_check(after)
    replies = legal_moves(after) if replies is None else replies
    enemy_king = after.board.index("K" if enemy == "w" else "k")
    checkers = [i for i, piece in enumerate(after.board)
                if piece and side(piece) == turn and enemy_king in reach(after.board, i)]
    direct = enemy_king in reach(after.board, move.end)
    targets = []
    for target in reach(after.board, move.end):
        piece = after.board[target]
        if not piece or side(piece) != enemy or piece.lower() == "p":
            continue
        worth = piece.lower() == "k" or VALUE[piece.lower()] > VALUE[after.board[move.end].lower()] \
            or not attacked(after.board, target, enemy)
        if worth:
            targets.append(piece.lower())
    mover = after.board[move.end].lower()
    exposed = (mover != "k" and attacked(after.board, move.end, enemy) and not attacked(after.board, move.end, turn)
               and VALUE.get(taken, 0) < VALUE[mover])
    ahead = range(rank_of(move.end, turn) + 1, 8)
    files = {f for f in (move.end % 8 - 1, move.end % 8, move.end % 8 + 1) if 0 <= f < 8}
    passed = kind == "p" and not any(after.board[f + 8 * (r if turn == "w" else 7 - r)] == ("p" if turn == "w" else "P")
                                     for f in files for r in ahead)
    mate = check and not replies
    boxed = all(after.board[t] and side(after.board[t]) == enemy for t in reach(after.board, enemy_king)
                if not (after.board[t] and side(after.board[t]) == turn))
    return Reading(
        kind=kind, start=move.start, end=move.end, turn=turn, taken=taken, passing=passing, castle=castle,
        crown=move.promotion, check=check, double=len(checkers) > 1, discovered=check and not direct, mate=mate,
        stalemate=not check and not replies, fork=tuple(sorted(targets, key=ORDER.index)) if len(targets) > 1 else (),
        first=HOME[turn].get(move.start) == kind, exposed=exposed,
        advance=rank_of(move.end, turn) - rank_of(move.start, turn),
        distance=max(abs(move.end % 8 - move.start % 8), abs(move.end // 8 - move.start // 8)),
        first_blood=bool(taken) and sum(1 for piece in board if piece) == 32, passed=passed,
        smothered=mate and kind == "n" and boxed,
        back_rank=mate and kind in "rq" and rank_of(enemy_king, turn) == 7 and move.end // 8 == enemy_king // 8,
        open_file=kind == "r" and not any(after.board[move.end % 8 + 8 * r].lower() == "p" for r in range(8)))


def theme(r: Reading) -> str:
    """The most telling thing the move does, which its title is about."""
    if r.mate:
        return "smothered" if r.smothered else "back-rank" if r.back_rank else "mate"
    if r.stalemate:
        return "stalemate"
    if r.crown:
        return "crown-taking" if r.taken and r.crown == "q" else "crown" if r.crown == "q" else "underpromote"
    if r.castle:
        return f"castle-{r.castle}"
    if r.double:
        return "double"
    if r.discovered:
        return "discovery"
    if "k" in r.fork and "q" in r.fork:
        return "royal-fork"
    if r.taken == "q":
        return "queen-taken"
    if r.fork and (r.check or len(r.fork) > 2):
        return "fork"
    if r.taken and r.check:
        return "strike"
    if r.passing:
        return "passing"
    if r.taken:
        if r.first_blood:
            return "first-blood"
        return "giant" if r.kind == "p" and VALUE[r.taken] >= 3 else "capture"
    if r.check:
        return "check"
    if r.fork:
        return "fork"
    if r.exposed:
        return "offering"
    if r.kind == "p":
        if rank_of(r.end, r.turn) == 6:
            return "doorstep"
        if r.passed and rank_of(r.end, r.turn) >= 4:
            return "runner"
        if r.end in CENTER:
            return "center"
        return "stride" if r.distance == 2 else "quiet"
    if r.kind in "nb" and r.first:
        return "fianchetto" if r.kind == "b" and r.end in FIANCHETTO[r.turn] else "develop"
    if r.kind in "rq" and rank_of(r.end, r.turn) == 6:
        return "seventh"
    if r.open_file and r.advance >= 0 and r.distance > 1:
        return "open-file"
    if r.kind == "q" and r.first:
        return "sortie"
    if r.kind == "k":
        return "royal-walk"
    if r.end in CENTER:
        return "center"
    if r.kind == "n" and r.end % 8 in (0, 7):
        return "rim"
    if r.advance < 0:
        return "retreat"
    if r.kind in "brq" and r.distance >= 5:
        return "long"
    return "quiet"


def places(r: Reading) -> tuple[str, ...]:
    """What the square it lands on can be called."""
    out = []
    rank = rank_of(r.end, r.turn)
    if r.end in CENTER:
        out += PLACES["center"]
    out += PLACES["throne" if rank == 7 else "deep" if rank >= 5 else "middle" if rank >= 3 else "home"]
    f = r.end % 8
    if f in (0, 7):
        out += PLACES["rim"]
    if f <= 2:
        out += PLACES["queenside"]
    elif f >= 5:
        out += PLACES["kingside"]
    return tuple(out)


def title(r: Reading, rng: random.Random, used: set[str] = frozenset()) -> tuple[str, str, str]:
    """One emoji, title and the pattern it came from, drawn from the move's theme with `rng`: a pattern and an emoji
    the board has not `used` yet when its theme has one left."""
    key = theme(r)
    emoji, patterns = THEMES[key]
    # a pattern with fields to fill comes up twice as often as a fixed phrase, so the titles keep surprising
    patterns = [p for p in patterns + OWN.get((key, r.kind), ()) for _ in range(2 if "{" in p else 1)]
    pattern = rng.choice([p for p in patterns if p not in used] or patterns)
    name = pattern.format(
        P=PIECES[r.crown or r.kind].capitalize(), T=PIECES.get(r.taken, "").capitalize(), sq=FILES[r.end % 8] +
        str(r.end // 8 + 1), place=rng.choice(places(r)), adj=rng.choice(ADJ[r.kind]), noun=rng.choice(NOUN[r.kind]),
        move=rng.choice(MOVE[r.kind]), fierce=rng.choice(FIERCE), strike=rng.choice(STRIKE[r.kind]),
        file=FILES[r.end % 8])
    emoji = emoji or EMOJI[r.kind]
    return rng.choice([e for e in emoji if e not in used] or emoji), name, pattern


def words(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> str:
    """The move in plain English: `Knight from g1 to f3`, `Pawn from c7 takes the knight on d6, check`."""
    board = position.board
    kind = board[move.start].lower()
    start, end = FILES[move.start % 8] + str(move.start // 8 + 1), FILES[move.end % 8] + str(move.end // 8 + 1)
    if kind == "k" and abs(move.end - move.start) == 2:
        text = "Castle kingside" if move.end > move.start else "Castle queenside"
    elif kind == "p" and move.end == position.ep and not board[move.end]:
        text = f"Pawn from {start} takes the pawn on {end[0]}{start[1]}, en passant"
    elif board[move.end]:
        text = f"{PIECES[kind].capitalize()} from {start} takes the {PIECES[board[move.end].lower()]} on {end}"
    elif kind == "p" and abs(move.end - move.start) == 16:
        text = f"Pawn from {start} to {end}, two squares"
    else:
        text = f"{PIECES[kind].capitalize()} from {start} to {end}"
    if move.promotion:
        text += f", becoming a {PIECES[move.promotion]}"
    after = make(position, move) if after is None else after
    replies = legal_moves(after) if replies is None else replies
    if in_check(after):
        text += ", checkmate" if not replies else ", check"
    elif not replies:
        text += ", stalemate"
    return text


def seed(position: Position, game: int, ply: int) -> int:
    """The board's seed: the same game, move and position always give the same names."""
    return int.from_bytes(hashlib.sha256(f"{game}:{ply}:{position.fen}".encode()).digest()[:8], "big")


def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every legal move in the list's order, each with its SAN, its words and a title no other move here has."""
    return copy.deepcopy(_listing(position.fen, game, ply))


@functools.lru_cache(maxsize=64)
def _listing(fen: str, game: int, ply: int) -> list[dict]:
    position = Position.from_fen(fen)
    legal = legal_moves(position)
    order = {"q": 0, "r": 1, "b": 2, "n": 3, "": 4}
    moves = sorted(legal, key=lambda m: (ORDER.index(position.board[m.start].lower()), m.end % 8, -(m.end // 8),
                                         m.start, order[m.promotion]))
    base, seen, out = seed(position, game, ply), set(), []
    for move in moves:
        rng = random.Random(base ^ int.from_bytes(hashlib.sha256(move.uci.encode()).digest()[:8], "big"))
        after = make(position, move)
        replies = legal_moves(after)
        reading = read(position, move, after, replies)
        for _ in range(64):
            emoji, name, pattern = title(reading, rng, seen)
            if name not in seen:
                break
        else:  # a theme with too few titles for a board this busy: the square makes it its own
            name = f"{name} on {FILES[move.end % 8]}{move.end // 8 + 1}"
        seen |= {name, pattern, emoji}
        out.append({"uci": move.uci, "san": san(position, move, legal, replies),
                    "piece": PIECES[position.board[move.start].lower()], "emoji": emoji, "title": name,
                    "words": words(position, move, after, replies)})
    return out
