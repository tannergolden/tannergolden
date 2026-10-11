#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: an emoji, a title, and what the move does in plain English.

  from chess_names import listing, words

Every title is an order, as if the player commanded an army: "Send In the
Cavalry!", "Trample Their Pikemen!", "Raise the Drawbridge!". It opens with a
word of command and ends with "!", and it never names a square, since the
notation beside it in the list already does.

`read` takes a move apart for what it does: which piece moves and from where,
what it takes, whether it checks, discovers a check, mates or stalemates,
castles or promotes, whether it forks, leaves its home square, takes the
center, runs for the last rank, retreats, or steps where it can be taken for
nothing. The most telling of those picks the move's theme, and the theme
builds its order from orders of its own and from the words kept for each
piece as a unit of the army: the pawns are its pikemen and the knights its
cavalry, a capture names what fell and the unit it fell from, and a place
names where it happened. Between them they make millions of orders, so two
boards seldom share one.

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
import re
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

# --- the army: each piece a unit, and the orders it takes ---------------------------------------------------------
# Every title is an order shouted down the line: it opens with one of COMMANDS and ends with "!". Each piece is a
# unit of the army (the pawns its pikemen, the knights its cavalry, the rooks its siege towers), so a move reads as
# the order that sent it, and no title ever names a square: the notation beside it does that.
TROOP = {  # the unit an order sends: "Advance the Pikemen!"
    "p": ("Pikemen", "Footmen", "Infantry", "Spearmen", "Vanguard", "Militia", "Shield Wall", "Front Line", "Levies",
          "Skirmishers", "Yeomen", "Halberdiers"),
    "n": ("Cavalry", "Horsemen", "Riders", "Lancers", "Dragoons", "Hussars", "Outriders", "Light Horse",
          "Heavy Horse", "Knights"),
    "b": ("Bishops", "Templars", "Crusaders", "Clergy", "Zealots", "Holy Order", "Paladins", "Battle Priests",
          "Inquisitors", "Abbots"),
    "r": ("Siege Towers", "Rams", "Garrison", "Towers", "Catapults", "Trebuchets", "Engineers", "Siege Engines",
          "Battlements", "War Wagons"),
    "q": ("Queen", "Warrior Queen", "War Queen", "Iron Queen", "Queen of Blades", "Crown's Champion"),
    "k": ("King", "Crown", "Old King", "Sovereign", "Royal Court"),
}
ONE = {  # one soldier of it: "Crown the Pikeman!"
    "p": ("Pikeman", "Footman", "Spearman", "Foot Soldier", "Militiaman", "Yeoman", "Halberdier", "Conscript"),
    "n": ("Rider", "Horseman", "Lancer", "Dragoon", "Hussar", "Outrider", "Knight"),
    "b": ("Bishop", "Templar", "Crusader", "Zealot", "Paladin", "Inquisitor"),
    "r": ("Siege Tower", "Ram", "Catapult", "Trebuchet", "War Wagon", "Tower"),
    "q": ("Queen", "Warrior Queen", "War Queen", "Iron Queen"),
    "k": ("King", "Old King", "Sovereign"),
}
CALL = {  # the unit called to at the end of an order: "Charge, Cavalry!"
    "p": ("Footmen", "Pikemen", "Infantry", "Spearmen", "Soldiers", "Militia", "Vanguard", "Lads"),
    "n": ("Cavalry", "Riders", "Horsemen", "Lancers", "Knights", "Hussars"),
    "b": ("Templars", "Crusaders", "Brothers", "Zealots", "Paladins", "Father"),
    "r": ("Garrison", "Engineers", "Towers", "Siege Crews", "Sappers"),
    "q": ("My Queen", "Majesty", "Your Majesty", "My Lady"),
    "k": ("Sire", "Majesty", "My King", "Your Majesty"),
}
SEND = {  # the orders that move the unit: "{send} the {troop}!"
    "p": ("Advance", "March", "Push Up", "Move Up", "Send Forward", "Rally", "Muster", "Drive", "Lead Out"),
    "n": ("Send In", "Spur On", "Unleash", "Loose", "Wheel In", "Swing Out", "Rally", "Lead Out", "Turn Loose"),
    "b": ("Send Forth", "Rally", "Loose", "Unleash", "Dispatch", "Station", "Post", "Lead Out", "Summon"),
    "r": ("Roll Up", "Wheel In", "Bring Up", "Haul Up", "Move Up", "Raise", "Station", "Roll Out", "Post"),
    "q": ("Unleash", "Send In", "Dispatch", "Loose", "Deploy", "Summon", "Turn Loose"),
    "k": ("Shelter", "Move", "Guard", "Escort", "Shield", "Lead Out"),
}
CRY = {  # the orders shouted to it: "{cry}, {call}!"
    "p": ("Advance", "Forward", "March", "Hold Fast", "Press On", "Step Up", "Dig In", "Push On", "Quick March",
          "Close Ranks"),
    "n": ("Charge", "Ride", "Ride Hard", "Ride Out", "Leap", "Gallop", "Wheel About", "Hit Them Hard",
          "Run Them Down"),
    "b": ("Strike", "Sweep In", "Advance", "Cut Across", "Slip Through", "Go Forth", "Move Out", "Strike True"),
    "r": ("Roll Forward", "Advance", "Hold Fast", "Push On", "Fire", "Move Up", "Grind On", "Batter On"),
    "q": ("Ride", "Strike", "Sweep In", "Go Forth", "Show No Mercy", "Rule the Field", "Lead Us"),
    "k": ("Step Back", "Stand Fast", "Step Lively", "Hold Firm", "Move Out", "Take Cover", "Mind Your Step"),
}
TOWARD = {  # the orders that take it toward the fight: "March on the Crossroads!"
    "p": ("March on", "Push toward", "Press toward", "Advance on", "Close on", "Move on"),
    "n": ("Ride for", "Gallop toward", "Charge toward", "Ride on", "Make for", "Wheel toward"),
    "b": ("Slip toward", "Sweep toward", "Strike toward", "Make for", "Cut toward"),
    "r": ("Roll toward", "Drive on", "Bear Down on", "Advance on", "Grind toward"),
    "q": ("Sweep toward", "Bear Down on", "Ride for", "Strike toward", "Make for", "Fly toward"),
    "k": ("Walk toward", "Step toward", "Make for", "Retire toward", "Head for"),
}
FORM = ("Form Up", "Hold Position", "Take Position", "Stand Guard", "Make Camp", "Close Ranks")  # on its own ground
STRIKE = {  # how each unit takes what it takes: "{strike} the {T}!"
    "p": ("Stab", "Spear", "Skewer", "Pitchfork", "Overrun", "Mob", "Bring Down", "Swarm"),
    "n": ("Trample", "Ride Down", "Run Down", "Ambush", "Overrun", "Hack Down", "Cut Down"),
    "b": ("Smite", "Condemn", "Judge", "Banish", "Excommunicate", "Strike Down", "Purge"),
    "r": ("Crush", "Batter", "Flatten", "Bury", "Grind Down", "Demolish", "Pound"),
    "q": ("Destroy", "Annihilate", "Sweep Away", "Erase", "Obliterate", "Cut Down"),
    "k": ("Slay", "Strike Down", "Cut Down", "Dispatch", "Behead"),
}
FIERCE = ("without Mercy", "Where It Stands", "at Once", "Swiftly", "Now")  # how hard: "Crush the Knight at Once!"
EMOJI = {
    "n": ("🐴", "🐎", "🏇", "🦄", "🌙"), "b": ("⛪", "🕯️", "📿", "🕊️", "📜", "🔔"),
    "r": ("🏰", "🗼", "🧱", "🛡️", "🪨", "⛓️"), "q": ("👸", "👑", "💎", "🌪️", "🌟", "⚜️"),
    "k": ("🤴", "👑", "🚶", "🛡️", "🏰"), "p": ("🥾", "🛡️", "🚩", "🌱", "👣", "🪖"),
}
# The words of command every title opens with, the drill the whole army knows.
COMMANDS = frozenset("""
    Accuse Advance Aim Ambush Annihilate Answer Back Bait Banish Bare Batter Bear Behead Bless Brace Break Bring
    Bury Call Castle Catch Charge Check Checkmate Circle Claim Clear Close Collect Condemn Corner Cross Crown Crush
    Cut Dare Deliver Demand Demolish Deploy Destroy Dethrone Dig Dispatch Divide Double Drag Draw Drive Drop End
    Erase Escort Excommunicate Fall Finish Fire Flank Flatten Fly Fork Form Fortify Forward Freeze Gallop Garrison
    Get Give Go Grind Guard Hack Hail Haul Head Hit Hold Hound Hunt Jab Join Judge Jump Keep Knock Lead Leap Leave
    Lengthen Let Light Lock Loose Make Man March Mind Mob Move Muster Obliterate Offer Open Overrun Own Pass Patrol
    Pin Pitchfork Plant Post Pound Press Prod Promote Pull Purge Push Put Quick Race Raid Raise Rally Ram Rattle
    Ravage Reach Regroup Reign Reinforce Retire Retreat Reveal Ride Ring Roll Rule Run Saddle Scout Seal Seize Send
    Set Shelter Shield Shift Shore Show Skewer Slay Slip Smite Smother Snatch Sound Spear Spill Split Spur Stab
    Stand Station Step Storm Stride Strike Summon Swarm Sweep Swing Take Tempt Threaten Topple Trample Trap Turn
    Unleash Unmask Walk Watch Wheel Withdraw
""".split())

# --- the themes: each a list of title patterns, and the emoji it is drawn from ------------------------------------
# A pattern's fields: {troop}, {one} and {call} the unit that moves, as an order sends it, as one soldier and as
# called to; {send}, {cry} and {strike} the orders it takes, and {go} one that takes it to where it lands; {P} the
# piece it is or becomes, {T} the piece it takes and {foe} that piece's unit; {fierce} how hard it strikes; {place}
# and {at} where it lands, the second with the word that puts it there; {pair} the two pieces a fork catches.
THEMES = {
    "mate": (("💀", "☠️", "🏁", "👑"), (
        "Topple the King!", "Seize the Throne!", "Finish It!", "End It Here!", "Take the Crown!", "Claim the Throne!",
        "Bring Down the King!", "Checkmate Them!", "Leave the King No Escape!", "Corner the King {at}!",
        "Trap the King {at}!", "End the War {at}!")),
    "smothered": (("💀", "🐴"), ("Smother the King!", "Bury Him in His Own Court!", "Leave Him No Room!",
                                "Seal the King In!")),
    "back-rank": (("💀", "🏁"), ("Strike the Back Rank!", "Seal the Back Rank!", "Trap Him Behind His Walls!",
                                "Pin Him to His Own Wall!")),
    "stalemate": (("🧊", "🤝"), ("Freeze the Field!", "Leave Them No Move!", "Call the Truce!", "Lock the Board!",
                                "Hold Them Frozen!")),
    "crown": (("👑", "⭐", "✨"), (
        "Crown the {one}!", "Raise a New Queen!", "Crown a Queen in the Field!", "Promote the {one}!",
        "Make Way for the New Queen!", "Hail the New Queen!")),
    "crown-taking": (("👑", "🩸"), ("Cut Through and Take the Crown!", "Crown the {one} in Blood!",
                                   "Take It and Be Crowned!")),
    "underpromote": (("🎖️", "✨"), ("Make the {one} a {P}!", "Raise a {P} from the Ranks!",
                                   "Promote the {one} to {P}!")),
    "castle-king": (("🏰", "🏯"), (
        "Raise the Drawbridge!", "Retreat to the Keep!", "Close the Gates!", "Garrison the King!",
        "Shelter the Crown!", "Man the Kingside Walls!")),
    "castle-queen": (("🏰", "🏯"), (
        "Castle Long!", "Fortify the Queenside!", "Move the Court West!", "Shelter the King in the Great Hall!",
        "Bring the Rook to the Center!")),
    "double": (("🌩️", "⚡"), (
        "Close the Pincer!", "Strike from Both Flanks!", "Double the Assault!", "Hit the King Twice!",
        "Draw Both Blades!", "Catch Him in the Crossfire!")),
    "discovery": (("🎭", "🪞"), (
        "Unmask the Battery!", "Open the Line of Fire!", "Pull Back the Curtain!", "Step Aside and Let Them Strike!",
        "Reveal the Hidden Blade!", "Clear the Way for the Strike!")),
    "royal-fork": (("🍴", "🔱"), ("Fork the King and Queen!", "Split the Royal Family!", "Strike at Crown and Queen!",
                                 "Hit the King, Take the Queen!")),
    "fork": (("🍴", "🔱"), (
        "Strike Two at Once!", "Split Their Ranks!", "Divide and Conquer!", "Hit Them Both!", "Fork the {pair}!",
        "Catch the {pair} Together!")),
    "queen-taken": (("💔", "⚰️", "👑"), (
        "Take Down the Queen!", "Dethrone Her!", "Cut Down the Queen!", "Bring the Queen to Her Knees!",
        "Show the Queen No Mercy!", "{strike} the Queen!", "End the Queen's Reign!")),
    "strike": (("🌩️", "⚡"), (
        "Take the {T} and Warn the King!", "Cut Down the {T}, Then the King!", "Strike and Threaten!",
        "Take It with Check!", "{strike} the {T}, Check the King!")),
    "passing": (("👻",), ("Strike in Passing!", "Catch Them Crossing!", "Take the Passing Pawn!", "Ambush the Runner!",
                         "Snatch It en Passant!")),
    "first-blood": (("🩸", "🗡️"), ("Draw First Blood!", "Strike First!", "Open the Killing!", "Take the First {T}!",
                                  "Spill First Blood {at}!", "{strike} Their {foe} First!")),
    "giant": (("🪨", "⚔️"), ("Bring Down the {T}!", "Topple the {T}!", "Raise Pitchforks, Take the {T}!",
                            "Let the Footmen Fell the {T}!", "Drag Down Their {foe}!")),
    "capture": (("⚔️", "🗡️", "🩸", "💥", "🪓", "🏹"), (
        "Take the {T}!", "Cut Down the {T}!", "Seize Their {T}!", "Give the {T} No Quarter!", "{strike} the {T}!",
        "{strike} Their {foe}!", "{strike} the {T} {fierce}!", "{strike} Their {foe} {at}!", "Break Their {foe}!",
        "Claim the {T} {at}!")),
    "check": (("⚡", "🔔", "🎯", "📯", "🚨"), (
        "Check the King!", "Sound the Alarm!", "Threaten the Crown!", "Knock on the King's Door!",
        "Put the King on Notice!", "Hound the King!", "Strike at the Throne!", "Rattle the Throne!",
        "Give Check from {place}!", "Call Out the King!")),
    "offering": (("🎲", "🎁", "🦁"), (
        "Bait the Trap!", "Dare Them to Take It!", "Offer Them the {one}!", "Leave the {one} as Bait!",
        "Stand Firm and Tempt Them!", "Hold Your Ground, {call}!", "Tempt Them {at}!")),
    "doorstep": (("🌠", "✨"), (
        "Push for the Crown!", "Reach for the Crown!", "Storm the Palace Door!", "Take One More Step!",
        "Knock on the Palace Gate!", "Press On, the Crown Awaits!")),
    "runner": (("🏃", "💨"), (
        "Run for the Crown!", "Break for the Last Rank!", "Clear the Road Ahead!", "Run, {call}, Run!",
        "Race for the Far Shore!", "Make for the Last Rank!")),
    "stride": (("👣", "🥾"), (
        "Quick March!", "Lengthen Your Stride!", "Take Two Steps, {call}!", "Double the Pace!", "Step Out Smartly!",
        "Stride Forward, {call}!")),
    "center": (("🎯", "🏛️", "🧭"), (
        "Seize the Center!", "Take the Crossroads!", "Hold the High Ground!", "Plant the Flag {at}!",
        "Claim the Heart of the Board!", "{send} the {troop} to the Center!", "Hold the Center, {call}!")),
    "develop": (("🌅", "🚪"), (
        "Deploy the {troop}!", "Send Out the {troop}!", "Muster the {troop}!", "Join the Fray, {call}!",
        "Take the Field, {call}!", "Leave the Barracks!", "Answer the Call, {call}!")),
    "fianchetto": (("🔭", "🎯"), (
        "Post the Sniper!", "Watch the Long Diagonal!", "Set the Bishop on Watch!", "Aim Down the Long Diagonal!",
        "Guard the Long Road!")),
    "seventh": (("🐗", "🔥"), (
        "Raid Their Back Lines!", "Storm the Seventh!", "Get Behind Their Lines!", "Ravage the Seventh Rank!",
        "{send} the {troop} Behind Their Lines!")),
    "open-file": (("🛣️",), (
        "Take the Open Road!", "Seize the Open File!", "Charge Down the Open File!", "Own the Open File!",
        "Roll Down the Open Road!")),
    "sortie": (("👸",), (
        "Send Out the Queen!", "Unleash Her Majesty!", "Let the Queen Ride!", "Ride Out, My Queen!",
        "Show Them the Queen!", "Send the Queen to {place}!")),
    "royal-walk": (("🚶", "🤴"), (
        "Walk the King Forward!", "Move the Crown!", "Step Aside, Your Majesty!", "Lead from the Front, Sire!",
        "Shift the Royal Court!", "Escort the King to {place}!", "Guard the King's Steps!", "{cry}, {call}!")),
    "rim": (("🌑", "🌲"), (
        "Ride for the Rim!", "Scout the Edge!", "Guard the Flank!", "Patrol the Border!", "Hold the Edge of the Map!",
        "Watch the Woods, {call}!")),
    "retreat": (("↩️", "🔙", "🧭"), (
        "Fall Back!", "Regroup {at}!", "Pull Back to {place}!", "Withdraw and Regroup!", "Retreat in Good Order!",
        "Back to the Lines!", "Fall Back, {call}!", "Draw Back to {place}!")),
    "long": (("🏹", "🌠"), (
        "Sweep the Board!", "Strike from Afar!", "Cross the Whole Field!", "Sweep from Edge to Edge!",
        "Sweep Across the Board, {call}!")),
    "quiet": ((), (
        "{send} the {troop}!", "{send} the {troop} {at}!", "{cry}, {call}!", "{go}!", "{go}, {call}!",
        "{send} the {troop} to {place}!")),
}
# Each piece adds orders of its own to a theme.
OWN = {
    ("develop", "n"): ("Saddle Up!", "Open the Stables!", "Ride Out, {call}!"),
    ("develop", "b"): ("Ring the Bells!", "Open the Cathedral Doors!", "Bless the Troops!"),
    ("capture", "n"): ("Ride Them Down!", "Trample Them Underhoof!", "Hit Them from the Flank!"),
    ("capture", "b"): ("Pass Judgement on the {T}!", "Excommunicate the {T}!", "Bring Holy Wrath!"),
    ("capture", "r"): ("Break Through the Wall!", "Crush Them Under Stone!", "Bring the Walls Down!"),
    ("capture", "q"): ("Deliver the Queen's Justice!", "Collect Their {T}, Majesty!", "Strike by Royal Decree!"),
    ("capture", "k"): ("Draw the King's Sword!", "Bare the Crown's Teeth!", "Strike, Sire!"),
    ("capture", "p"): ("Raise the Pitchforks!", "Claim the Footman's Prize!"),
    ("check", "n"): ("Ride at the King!", "Jump the King's Guard!"),
    ("check", "b"): ("Strike the King on the Slant!", "Accuse the King!"),
    ("check", "r"): ("Batter the King's Gate!", "Ram the Royal Door!"),
    ("check", "q"): ("Demand His Surrender!", "Hunt the King, My Queen!"),
    ("check", "p"): ("Prod the King!", "Jab at the Crown!"),
    ("fork", "n"): ("Split Them with the Cavalry!", "Ride Between Them!"),
    ("fork", "p"): ("Raise the Pitchfork!", "Stab Two at Once!"),
    ("mate", "p"): ("Let the Footmen Take the Crown!", "Topple the King with a Pike!"),
    ("mate", "q"): ("Let the Queen End It!", "Finish It, My Queen!"),
    ("quiet", "p"): ("Hold the Line!", "Dig In!", "Plant the Flag!", "Raise the Shields!", "Close Ranks!",
                     "Brace for the Charge!", "Keep Formation!", "Hold the Field!", "Shore Up the Line!",
                     "Forward March!"),
    ("quiet", "n"): ("Flank Them!", "Leap the Wall!", "Ride Through the Night!", "Wheel and Strike!",
                     "Circle Behind Them!", "Scout Ahead!", "Jump the Line!"),
    ("quiet", "b"): ("Bless the Advance!", "Light the Long Road!", "Guard the Diagonal!", "Slip Through the Gap!",
                     "Watch from Afar!", "Hold the Holy Ground!"),
    ("quiet", "r"): ("Raise the Ramparts!", "Man the Walls!", "Hold the Bridge!", "Drop Anchor!",
                     "Reinforce the Line!", "Shore Up the Walls!"),
    ("quiet", "q"): ("Sweep the Field, My Queen!", "Reign over the Board!", "Watch over Them, Majesty!",
                     "Rule the Field!", "Hunt Them Down!"),
    ("quiet", "k"): ("Hold Court!", "Stand Fast, Sire!", "Take Cover, Majesty!", "Guard the Throne!",
                     "Mind the King!"),
}
# What a busy board puts on the end of an order its theme has already given, so no two moves share a title.
URGE = (", Now!", ", Again!", ", Together!", ", at Once!", ", All of You!", ", to a Man!")
LONGEST = 48  # the longest title tannergolden/markdown draws in the list

# What a part of the board is called, from the side of the piece that lands there.
# Each place with the word that puts a move there: at the Crossroads, behind Enemy Lines, in the Eastern Woods.
PLACES = {
    "center": (("at", "the Crossroads"), ("at", "the Heart of the Board"), ("in", "the Center"),
               ("in", "the Market Square"), ("on", "the High Ground")),
    "throne": (("in", "the Enemy Throne Room"), ("at", "the Enemy Gates"), ("on", "the Last Rank"),
               ("on", "the Far Shore")),
    "deep": (("behind", "Enemy Lines"), ("on", "the Enemy's Doorstep"), ("on", "the Far Bank"),
             ("on", "Hostile Ground")),
    "middle": (("in", "No Man's Land"), ("at", "the Front"), ("on", "the Middle Ground"), ("at", "the Border")),
    "home": (("on", "Home Ground"), ("in", "the Near Fields"), ("on", "the Home Front"), ("on", "Friendly Soil")),
    "queenside": (("on", "the Queen's Wing"), ("on", "the Queenside"), ("in", "the Western Marches")),
    "kingside": (("on", "the King's Wing"), ("on", "the Kingside"), ("in", "the Eastern Woods")),
    "rim": (("at", "the Edge of the Map"), ("on", "the Rim"), ("at", "the Board's Edge")),
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


def places(r: Reading) -> tuple[tuple[str, str], ...]:
    """What the square it lands on can be called, each with the word that puts a move there."""
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


def title(r: Reading, rng: random.Random, used: set[str] = frozenset(), key: str = "") -> tuple[str, str, str]:
    """One emoji, title and the pattern it came from, drawn with `rng` from the move's theme, or from `key`'s: a
    pattern and an emoji the board has not `used` yet when the theme has one left, and a title short enough to draw."""
    key = key or theme(r)
    emoji, patterns = THEMES[key]
    # a pattern with fields to fill comes up twice as often as a fixed order, so the titles keep surprising
    patterns = [p for p in patterns + OWN.get((key, r.kind), ()) for _ in range(2 if "{" in p else 1)]
    fresh = [p for p in patterns if p not in used] or patterns
    for _ in range(16):
        pattern = rng.choice(fresh)
        at, place = rng.choice(places(r))
        name = pattern.format(
            P=PIECES[r.crown or r.kind].capitalize(), T=PIECES.get(r.taken, "").capitalize(),
            troop=rng.choice(TROOP[r.kind]), one=rng.choice(ONE[r.kind]), call=rng.choice(CALL[r.kind]),
            send=rng.choice(SEND[r.kind]), cry=rng.choice(CRY[r.kind]),
            go=f"{rng.choice(FORM)} {at} {place}" if (at, place) in PLACES["home"] else
            f"{rng.choice(TOWARD[r.kind])} {place}",
            strike=rng.choice(STRIKE[r.kind]), foe=rng.choice(TROOP.get(r.taken) or ("",)), fierce=rng.choice(FIERCE),
            place=place, at=f"{at} {place}", pair=" and ".join(PIECES[k].capitalize() for k in r.fork[:2]))
        name = re.sub(r"\bA (?=[AEIOU])", "An ", name)  # the article goes with the word filled in after it
        if len(name) <= LONGEST:
            break
    else:  # sixteen orders too long to draw: the theme's shortest fixed one
        pattern = name = min((p for p in patterns if "{" not in p), key=len)
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
        for key in ("", "quiet"):  # the move's own theme, then, on a board too busy for it, the piece's plain orders
            for _ in range(64):
                emoji, name, pattern = title(reading, rng, seen, key)
                if name not in seen:
                    break
            else:
                continue
            break
        else:  # every order already given here: the last one, urged on
            name = next((name[:-1] + urge for urge in URGE
                         if name[:-1] + urge not in seen and len(name[:-1] + urge) <= LONGEST), name)
        seen |= {name, pattern, emoji}
        out.append({"uci": move.uci, "san": san(position, move, legal, replies),
                    "piece": PIECES[position.board[move.start].lower()], "emoji": emoji, "title": name,
                    "words": words(position, move, after, replies)})
    return out
