# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: an emoji, a title, and what the move does in plain English.

  from checkers_names import name, named

Chess names its moves as orders to an army on land. Checkers is a fleet at
sea, and every title is an order to it: "Full Sail Ahead!" for a man under
way, "Board Them!" for a jump, "Rake Their Whole Line!" for a jump of two or
more, "Make Him Admiral!" for a man crowned, "Come About!" for a king turning
for home. A title ends with "!" and never names a square, since the code
beside it in the list already does. The words say the move exactly, as a
score sheet would: "Man from 11 to 15", "Man from 20 jumps 16, landing on
11", "Man from 19 jumps 15 and 6, landing on 1, crowned".

`read` takes a move apart for what it does: which piece moves and what it
takes; whether it is crowned, or leaves the other side no move at all;
whether it lands where it can be jumped, and whether that is a fire ship that
wins more back than it gives; whether it threatens a jump, slips one, or
covers a piece of its own from one; and where it goes, out of port, along the
coast, into the channel, within sight of the crown, back toward home or into
a double corner. The most telling of those is the move's theme. The theme
gives the emoji, one to a theme, so the emoji down the list read as a key to
the moves, and its orders: fixed ones, and ones built from the fleet's own
words, where every man is a ship of the line and every king an admiral, so
that a board with a crowd of moves still gives each an order of its own.

The choice is seeded by the position and the move, so a board names its
moves the same way however often it is drawn, and no two moves on one board
share a title. Stdlib only, with checkers_rules.py beside it.
"""
from __future__ import annotations

import functools
import hashlib
import itertools
import random
import string
from dataclasses import dataclass

from checkers_rules import DARK, HOME, OWN, Move, Position, jumps_from, legal_moves, make, other, row_col

CENTRE = frozenset((14, 15, 18, 19))  # the four squares in the middle of the board
DOUBLE_CORNERS = frozenset((1, 5, 28, 32))  # each side's corner of two squares, a lone king's refuge
LONGEST = 48  # the longest title tannergolden/markdown draws in the list
SHORT = 34  # an order this long or shorter reads at a glance, so the namer tries for one first
WORDS_LONGEST = 80  # the longest words tannergolden/markdown takes
NUMBERS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve")

# --- the fleet: each piece a ship, and the orders it takes -------------------------------------------------------
# Every man is a ship of the line and every king an admiral, so a move reads as the order that sent it. A field in
# braces is filled from these words: {ship} is the one that moves and {call} whoever the order is shouted to, by
# whether it is a man or a king; {foe} is what it takes or {target} what it threatens, and {guarded} the ship of its
# own it covers; {strike} is how it takes, {fierce} how hard, and {volley} and {count} how many.
SHIPS = {
    "man": ("Ship", "Sloop", "Frigate", "Brig", "Cutter", "Schooner", "Corvette", "Galleon", "Gunboat", "Clipper",
            "Ketch", "Man-of-War"),
    "king": ("Flagship", "Admiral", "Commodore"),
}
CALL = {
    "man": ("Lads", "Men", "Crew", "Sailors", "Shipmates", "Bosun", "Helmsman", "Hearties"),
    "king": ("Admiral", "Commodore", "Sir", "Flag Captain"),
}
FOES = {
    "man": ("Ship", "Sloop", "Frigate", "Brig", "Cutter", "Schooner", "Corvette", "Galleon", "Gunboat", "Raider",
            "Privateer", "Merchantman"),
    "king": ("Flagship", "Admiral's Ship", "Commodore's Ship"),
}
STRIKE = ("Board", "Sink", "Ram", "Rake", "Scuttle", "Take", "Capture", "Seize", "Burn", "Cripple", "Dismast", "Torch")
FIERCE = ("at Once", "Now", "Where She Lies", "Without Mercy", "in the Smoke")
VOLLEY = {2: "Double", 3: "Triple", 4: "Quadruple"}  # and "Grand" past four
SAIL = ("Make Way", "Full Sail", "Steady On", "Ahead Full", "Hold Course", "Make Sail", "Press On", "Carry On",
        "Forward")
SEND = ("Send Out", "Bring Up", "Sail", "Advance", "Move Up", "Ease Out", "Send Forward", "Steer", "Pilot", "Signal")
TURN = ("Bear", "Steer", "Swing", "Veer", "Turn", "Come", "Hard")
GO = ("Make for", "Steer for", "Sail for", "Head for", "Run for", "Stand for")
# The waters a move can land in, each with the word that sends a ship there: into the Narrows, along the Coast.
PLACES = {
    "centre": (("into", "the Channel"), ("into", "the Narrows"), ("through", "the Strait"), ("to", "Midchannel")),
    "edge": (("along", "the Coast"), ("into", "the Shallows"), ("under", "the Cliffs"), ("along", "the Shore"),
             ("to", "the Harbour Wall")),
    "corner": (("into", "the Double Corner"),),
    "home": (("into", "Home Waters"), ("into", "the Roads"), ("into", "Friendly Waters")),
    "own": (("into", "Open Water"), ("into", "the Offing"), ("into", "Blue Water"), ("into", "the Sea Lanes")),
    "enemy": (("into", "Enemy Waters"), ("into", "Their Waters"), ("into", "Hostile Waters"),
              ("into", "Contested Waters")),
    "far": (("off", "Their Coast"), ("into", "Their Home Waters"), ("toward", "the Far Shore"),
            ("into", "Their Harbour")),
}

# --- the themes: each an emoji and the orders it is named from ---------------------------------------------------
# One emoji to a theme, so the list's column reads as a key: ⛵ under way, ⚓ the coast, 🌊 leaving port, 🔭 within
# sight of the crown, 🧭 a king, ⚔️ a jump, 💥 two or more, 👑 crowned, 🎣 bait, 🔥 a fire ship, 🎯 a threat, 💨 an
# escape, 🛡️ a guard, 🏆 the winning move.
THEMES = {
    "victory": ("🏆", (  # takes the last piece they have
        "Rule the Waves!", "Sweep the Seas!", "Sink the Last of Them!", "Send Them to the Bottom!", "Win the Day!",
        "Splice the Mainbrace!", "Take the Last Prize!", "Hoist the Victory Signal!", "Make Them Strike Their Colours!",
        "Sink Their Last {foe}!", "Finish Them, {call}!", "Clear the Seas, {call}!")),
    "blockade": ("🏆", (  # leaves the pieces they have no move
        "Leave Them No Sea Room!", "Blockade Them!", "Bottle Them Up!", "Seal the Harbour!", "Close the Blockade!",
        "Hem Them In!", "Leave Them Dead in the Water!", "Shut Them In Port!", "Pin Them to the Shore!",
        "Chain the Harbour Mouth!", "Close the Net, {call}!")),
    "crown": ("👑", (
        "Make Him Admiral!", "Raise the Crown!", "Crown the Captain!", "Pipe the Admiral Aboard!",
        "Hoist the Admiral's Flag!", "Raise His Pennant!", "Fly the Admiral's Flag!", "All Hail the New Admiral!",
        "Crown the {ship}!", "Make the {ship} a Flagship!", "Promote the {ship}!", "Raise the Flag, {call}!")),
    "sweep": ("💥", (  # three or more taken
        "Sweep Their Whole Fleet!", "Rake Them from Stem to Stern!", "Break Their Whole Line!", "Fire Every Gun!",
        "Broadside After Broadside!", "Clear the Seas!", "Sink Them One by One!", "Rake Their Whole Line!",
        "{volley} Broadside!", "Take {count} Prizes!", "Sink {count} at a Blow!")),
    "double": ("💥", (
        "Rake Their Whole Line!", "Double Broadside!", "Clear Their Decks!", "Two Ships in One Pass!",
        "Fire Both Broadsides!", "Take Two Prizes!", "Sink Two at a Blow!", "Rake Them Twice!",
        "Board One, Then the Next!", "{strike} Them Both!", "Rake Them Both, {call}!")),
    "flagship": ("⚔️", (  # one taken, and a king
        "Sink Their Flagship!", "Take Their Admiral!", "Strike Down Their Admiral!", "Shoot Away Their Colours!",
        "Board Their Flagship!", "Bring Down Their Flag!", "Capture Their Admiral!", "{strike} Their {foe}!",
        "{strike} the {foe} {fierce}!")),
    "board": ("⚔️", (
        "Board Them!", "Take Their Ship!", "Ram Them Amidships!", "Grapple and Board!", "Away Boarders!",
        "Take Her as a Prize!", "Sink Her!", "Give Them a Broadside!", "Cut Her Out!", "Lay Alongside and Board!",
        "{strike} the {foe}!", "{strike} Their {foe}!", "{strike} the {foe} {fierce}!", "Take the {foe} as a Prize!",
        "Board the {foe}, {call}!")),
    "trap": ("🔥", (  # it can be jumped, and whatever they take, a jump takes back more
        "Send In the Fire Ship!", "Spring the Trap!", "Light the Fire Ship!", "Lure Them Onto the Rocks!",
        "Set the Trap!", "Lose a Ship, Win the Battle!", "Spring the Ambush!", "Sacrifice the {ship}!",
        "Send the {ship} In Burning!")),
    "bait": ("🎣", (  # it can be jumped where it lands
        "Bait the Hook!", "Sail Into Their Guns!", "Offer Them a Prize!", "Draw Their Fire!", "Trail Our Coat!",
        "Dangle the Bait!", "Tempt Them Out!", "Dare Them to Board!", "Run Under Their Guns!", "Stand Into Danger!",
        "Offer Them the {ship}!", "Risk the {ship}!", "Hold Fast Under Fire, {call}!")),
    "threat": ("🎯", (  # from where it lands it could jump next, left alone
        "Run Out the Guns!", "Beat to Quarters!", "Bring Her Guns to Bear!", "Clear for Action!", "Lay Her Alongside!",
        "Close to Boarding Range!", "Prepare to Board!", "Stand By to Fire!", "Train the Guns on Their {target}!",
        "Bear Down on the {target}!", "Run Down the {target}!", "Hunt Their {target}!",
        "Guns on the {target}, {call}!")),
    "escape": ("💨", (  # it could be jumped where it stood, and can't where it lands
        "Slip Their Guns!", "Run Out of Range!", "Break Away!", "Outrun Them!", "Crowd On Sail and Run!", "Get Clear!",
        "Slip the Net!", "Run for It!", "Haul Off!", "Steer Clear!", "Get the {ship} Clear!", "Save the {ship}!",
        "Run for It, {call}!")),
    "guard": ("🛡️", (  # a ship of its own could be jumped, and no longer can
        "Close the Gap!", "Guard the Convoy!", "Close Up the Line!", "Plug the Gap!", "Form Line of Battle!",
        "Keep Station!", "Protect the Convoy!", "Leave No Ship Behind!", "Cover the {guarded}!",
        "Shield the {guarded}!", "Stand By the {guarded}!", "Screen the {guarded}!")),
    "corner": ("🧭", (  # a king into a double corner
        "Make for the Double Corner!", "Run for the Double Corner!", "Shelter in the Double Corner!",
        "Ride Out the Storm!", "Hold the Double Corner!", "Anchor in the Double Corner!", "Find a Safe Harbour!",
        "Take Shelter, {call}!", "Shelter the {ship}!", "Anchor the {ship} in the Corner!")),
    "come-about": ("🧭", (  # a king back toward its own side
        "Come About!", "Wear Ship!", "Fall Back to Port!", "Bring Her About!", "Head for Home Waters!", "Put About!",
        "Back to the Roads!", "Return to Station!", "Come About, {call}!", "Bring the {ship} About!",
        "Fall Back, {call}!", "Head for Port, {call}!", "Recall the {ship}!", "Bring the {ship} Home!")),
    "cruise": ("🧭", (  # a king on patrol
        "The Admiral Sails!", "Patrol the Waters!", "Hunt Them Down!", "Take the Weather Gauge!", "Shadow Them!",
        "Show the Flag!", "Make Sail, {call}!", "Lead the Line, {call}!", "Bring Up the {ship}!", "Patrol {place}!",
        "Cruise {place}!", "{go} {place}!", "{send} the {ship}!", "{send} the {ship} {at}!", "{sail}, {call}!")),
    "landfall": ("🔭", (  # a man one row short of the crown
        "Land Ho!", "Raise the Far Shore!", "Make Landfall!", "Close on the Far Shore!", "Sight the Crown!",
        "One Last Leg!", "Make for Their Harbour!", "Run In for the Crown!", "Stand In for the Shore!",
        "Run In, {call}!", "Bring the {ship} Inshore!")),
    "port": ("🌊", (  # a man off its own back row
        "Leave Port!", "Weigh Anchor!", "Cast Off!", "Slip the Moorings!", "Put to Sea!", "Clear the Harbour!",
        "Sail on the Tide!", "Stand Out to Sea!", "Leave the Roads!", "Cast Off, {call}!", "Weigh Anchor, {call}!",
        "Send the {ship} to Sea!", "Take the {ship} Out!")),
    "coast": ("⚓", (  # a man to the side of the board
        "Hug the Coast!", "Hold the Harbour Wall!", "Drop Anchor!", "Hug the Shore!", "Keep to the Shallows!",
        "Run Along the Coast!", "Hold the Flank!", "Guard the Coast!", "Anchor the Flank!", "Ride at Anchor!",
        "Keep Inshore!", "Hug the Coast, {call}!", "Anchor the {ship} Inshore!")),
    "channel": ("⛵", (  # a man into the middle of the board
        "Hold the Channel!", "Take the Narrows!", "Seize the Strait!", "Command the Channel!", "Hold the Narrows!",
        "Run the Strait!", "Make for Midchannel!", "Take the Channel, {call}!", "Send the {ship} {at}!",
        "{go} {place}!")),
    "sail": ("⛵", (
        "Full Sail Ahead!", "Steady As She Goes!", "Make Way!", "Take the Wind!", "Trim the Sails!",
        "Run Before the Wind!", "Into Open Water!", "Ahead Two Thirds!", "Ahead Full!", "Hoist the Mainsail!",
        "Set the Topsails!", "Crowd On Sail!", "Shake Out the Reefs!", "Ease the Sheets!", "All Hands on Deck!",
        "{send} the {ship}!", "{send} the {ship} {at}!", "{sail}, {call}!", "{turn} to {side}!",
        "{turn} to {side}, {call}!", "{go} {place}!")),
}
# Orders a theme gives only some moves: a king's own, and a crowning won by a jump.
OWN_ORDERS = {
    ("board", "king"): ("Let the Admiral Board Them!", "Lead the Boarders, {call}!"),
    ("double", "king"): ("The Admiral Rakes Them!", "Rake Them, {call}!"),
    ("sweep", "king"): ("The Admiral Sweeps the Seas!",),
    ("crown", "taking"): ("Board Them and Take the Crown!", "Fight Through to the Crown!", "Take Them and Be Crowned!",
                          "Win the Crown in Battle!", "Make Admiral Under Fire!", "Board and Be Crowned!",
                          "Crown the {ship} in Battle!", "{strike} the {foe}, Make Admiral!"),
}
# Where a theme's places are drawn from, when not from wherever the move lands.
WATERS = {"channel": ("centre",), "coast": ("edge",), "corner": ("corner",)}
# A crowded board puts these on the end of an order already given, so no two moves share a title.
URGE = (", Now!", ", Again!", ", Together!", ", at Once!", ", All Hands!", ", Smartly!", ", With a Will!")
FIELDS = string.Formatter()


@dataclass(frozen=True)
class Reading:
    """What one move does, as a name reads it."""
    piece: str  # the piece that moves: d or l for a man, D or L for a king
    start: int
    end: int
    taken: tuple[str, ...] = ()  # the pieces it takes, in order
    crowned: bool = False
    wins: bool = False  # it leaves the other side no move
    left: bool = True  # the other side still has a piece after it
    exposed: bool = False  # it can be jumped at once where it lands
    trap: bool = False  # it can be jumped, and whatever they take, a jump takes back more
    threat: str = ""  # what of theirs it could jump from where it lands, were it to move again: man or king
    escaped: bool = False  # it could have been jumped where it stood, and can't be where it lands
    guarded: str = ""  # a piece of its own that could have been jumped before the move, and can't after: man or king
    side: str = ""  # Port or Starboard: which way a man's step turns, from its own heading

    @property
    def turn(self) -> str:
        return self.piece.lower()

    @property
    def kind(self) -> str:
        return "king" if self.piece.isupper() else "man"

    @property
    def rank(self) -> int:
        """How far up the board it lands, from 0 on its own back row to 7 on the far row."""
        return depth(self.end, self.turn)

    @property
    def advance(self) -> int:
        """Rows gained toward the far row: negative for a king heading home."""
        return self.rank - depth(self.start, self.turn)


def depth(square: int, turn: str) -> int:
    """The square's row as `turn` counts it, from 0 for its own back row to 7 for the far row."""
    row = row_col(square)[0]
    return row if turn == DARK else 7 - row


@functools.lru_cache(maxsize=256)
def in_reach(position: Position) -> frozenset[int]:
    """The squares of the side to move's pieces the other side could jump, were it the other side's move."""
    rival = OWN[other(position.turn)]
    pieces = position.pieces
    return frozenset(square for start, piece in pieces.items() if piece in rival
                     for move in jumps_from(pieces, start, piece) for square in move.captures)


def _gain(position: Position) -> int:
    """The most pieces the side to move can take in one jump: none when it has no jump."""
    return max((len(move.captures) for move in legal_moves(position)), default=0)


def read(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> Reading:
    """What the move does: every trait a name can be made from. `after` and `replies`, the position the move makes
    and the other side's legal moves there, save working them out again when they are known."""
    pieces, turn = position.pieces, position.turn
    start, end = move.path[0], move.path[-1]
    piece = pieces[start]
    after = make(position, move) if after is None else after
    replies = legal_moves(after) if replies is None else replies
    hit = {square for reply in replies for square in reply.captures}  # what of ours they can take now
    exposed = end in hit
    # A fire ship: whatever they take, a jump takes back more.
    trap = exposed and all(_gain(make(after, reply)) > len(reply.captures) for reply in replies)
    threat = guarded = side = ""
    escaped = False
    if not move.captures:
        landed = after.pieces[end]
        if not exposed:
            chances = [square for chance in jumps_from(after.pieces, end, landed) for square in chance.captures[:1]]
            threat = ("king" if any(after.pieces[square].isupper() for square in chances) else "man") if chances else ""
        reach = in_reach(position)
        escaped = start in reach and not exposed
        saved = [pieces[square] for square in reach if square != start and square not in hit]
        guarded = ("king" if any(p.isupper() for p in saved) else "man") if saved else ""
        if piece.islower():
            heading = row_col(end)[1] - row_col(start)[1]
            side = "Port" if (heading > 0) == (turn == DARK) else "Starboard"
    left = any(p in OWN[other(turn)] for p in after.pieces.values())
    return Reading(piece=piece, start=start, end=end, taken=tuple(pieces[square] for square in move.captures),
                   crowned=move.crowns, wins=not replies, left=left, exposed=exposed, trap=trap, threat=threat,
                   escaped=escaped, guarded=guarded, side=side)


def theme(r: Reading) -> str:
    """The most telling thing the move does, which its title is about."""
    if r.wins:
        return "blockade" if r.left else "victory"
    if r.crowned:
        return "crown"
    if len(r.taken) >= 3:
        return "sweep"
    if len(r.taken) == 2:
        return "double"
    if r.taken:
        return "flagship" if r.taken[0].isupper() else "board"
    if r.trap:
        return "trap"
    if r.exposed:
        return "bait"
    if r.threat:
        return "threat"
    if r.escaped:
        return "escape"
    if r.guarded:
        return "guard"
    if r.kind == "king":
        if r.end in DOUBLE_CORNERS:
            return "corner"
        return "come-about" if r.advance < 0 else "cruise"
    if r.rank == 6:
        return "landfall"
    if r.start in HOME[r.turn]:
        return "port"
    if row_col(r.end)[1] in (0, 7):
        return "coast"
    return "channel" if r.end in CENTRE else "sail"


def waters(r: Reading, key: str) -> tuple[tuple[str, str], ...]:
    """The waters the move lands in, each with the word that sends a ship there."""
    if key in WATERS:
        return tuple(place for region in WATERS[key] for place in PLACES[region])
    regions = [region for region, holds in (("centre", r.end in CENTRE), ("edge", row_col(r.end)[1] in (0, 7)),
                                            ("corner", r.end in DOUBLE_CORNERS)) if holds]
    regions.append("home" if r.rank <= 1 else "own" if r.rank <= 3 else "enemy" if r.rank <= 5 else "far")
    return tuple(place for region in regions for place in PLACES[region])


def choices(r: Reading, key: str) -> dict[str, tuple[str, ...]]:
    """What each field of an order can be filled with for this move: an order with a field left empty is not used."""
    taken = len(r.taken)
    foe = "king" if any(p.isupper() for p in r.taken) else "man"
    places = waters(r, key)
    return {
        "ship": SHIPS[r.kind], "call": CALL[r.kind], "foe": FOES[foe] if taken else (), "strike": STRIKE,
        "fierce": FIERCE, "volley": (VOLLEY.get(taken, "Grand"),) if taken > 1 else (),
        "count": (NUMBERS[taken].capitalize(),) if taken > 1 else (), "target": FOES[r.threat] if r.threat else (),
        "guarded": SHIPS[r.guarded] if r.guarded else (), "sail": SAIL, "send": SEND, "turn": TURN,
        "side": (r.side,) if r.side else (), "go": GO, "place": tuple(place for _, place in places),
        "at": tuple(f"{word} {place}" for word, place in places),
    }


def orders(r: Reading, key: str) -> tuple[str, ...]:
    """The theme's orders this move can take: its own, a king's or a jump's where the move is one, and none with a
    field the move has nothing to fill with."""
    found = choices(r, key)
    patterns = THEMES[key][1] + OWN_ORDERS.get((key, r.kind), ()) + (OWN_ORDERS[(key, "taking")]
                                                                      if key == "crown" and r.taken else ())
    return tuple(p for p in patterns if all(found[field] for _, field, _, _ in FIELDS.parse(p) if field))


def fill(pattern: str, found: dict[str, tuple[str, ...]], pick) -> str:
    """The order with each field filled by `pick`, which chooses one of a field's words."""
    return pattern.format(**{field: pick(found[field]) for _, field, _, _ in FIELDS.parse(pattern) if field})


def title(r: Reading, rng: random.Random, used: set[str] = frozenset(), key: str = "") -> tuple[str, str] | None:
    """One title and the order it came from, drawn with `rng` from the move's theme, or from `key`'s: an order the
    board has not given yet when the theme has one left, short enough to draw and not already a title here. None
    when the draws find none."""
    key = key or theme(r)
    patterns = orders(r, key)
    fresh = [p for p in patterns if p not in used] or list(patterns)
    found = choices(r, key)
    for attempt in range(40):
        pattern = rng.choice(fresh)
        name = fill(pattern, found, rng.choice)
        if len(name) <= (SHORT if attempt < 16 else LONGEST) and name not in used:
            return name, pattern
    return None


def every_title(r: Reading, key: str):
    """Every title the theme can give the move, in a fixed order: the last resort of a crowded board."""
    found = choices(r, key)
    for pattern in orders(r, key):
        fields = [field for _, field, _, _ in FIELDS.parse(pattern) if field]
        for words in itertools.product(*(found[field] for field in fields)):
            name = pattern.format(**dict(zip(fields, words, strict=True)))
            if len(name) <= LONGEST:
                yield name


def listed(squares: tuple[int, ...]) -> str:
    """`6`, `15 and 6`, `6, 15 and 24`."""
    numbers = [str(square) for square in squares]
    return numbers[0] if len(numbers) == 1 else ", ".join(numbers[:-1]) + " and " + numbers[-1]


def words(position: Position, move: Move, after: Position | None = None, replies: list[Move] | None = None) -> str:
    """The move in plain English: `Man from 11 to 15`, `Man from 20 jumps 16, landing on 11`, `Man from 19 jumps 15
    and 6, landing on 1, crowned`, with `winning the game` when it leaves the other side no move."""
    who = "King" if position.pieces[move.path[0]].isupper() else "Man"
    start, end = move.path[0], move.path[-1]
    if move.captures:
        text = f"{who} from {start} jumps {listed(move.captures)}, landing on {end}"
    else:
        text = f"{who} from {start} to {end}"
    if replies is None:
        replies = legal_moves(make(position, move) if after is None else after)
    tail = (", crowned" if move.crowns else "") + ("" if replies else ", winning the game")
    if len(text + tail) > WORDS_LONGEST:  # a king's long run of jumps: how many, not which
        text = f"{who} from {start} jumps {NUMBERS[len(move.captures)]} pieces, landing on {end}"
    return text + tail


def seed(position: Position, move: Move) -> int:
    """The move's seed on this board: the same position and move always give the same name."""
    digest = hashlib.sha256(f"{position.fen}:{move.code}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def named(position: Position) -> list[tuple[Move, str, str, str]]:
    """Every legal move in order, each with its emoji, a title no other move here has, and its words."""
    return list(_named(position))


def name(position: Position, move: Move) -> tuple[str, str, str]:
    """The move's emoji, title and words, as the board's list names it."""
    for listed_move, emoji, title_, words_ in _named(position):
        if listed_move == move:
            return emoji, title_, words_
    raise ValueError(f"{move.code} is not a legal move in {position.fen}")


@functools.lru_cache(maxsize=64)
def _named(position: Position) -> tuple[tuple[Move, str, str, str], ...]:
    used: set[str] = set()
    out = []
    for move in legal_moves(position):
        after = make(position, move)
        replies = legal_moves(after)
        reading = read(position, move, after, replies)
        key = theme(reading)
        rng = random.Random(seed(position, move))
        # the move's own theme, then on a board too crowded for it, the plain orders for its piece and whether it jumps
        fallback = "board" if move.captures else "cruise" if reading.kind == "king" else "sail"
        got = title(reading, rng, used, key) or title(reading, rng, used, fallback)
        if got is None:  # no draw found one: the first title in order nobody here has
            got = next(((t, "") for k in (key, fallback) for t in every_title(reading, k) if t not in used), None)
        if got is None:  # every title of both taken, which a board never comes near: the theme's first, urged on
            first = next(every_title(reading, key))
            got = next(((first[:-1] + urge, "") for urge in URGE
                        if first[:-1] + urge not in used and len(first[:-1] + urge) <= LONGEST), (first, ""))
        text, pattern = got
        used |= {text, pattern}
        out.append((move, THEMES[key][0], text, words(position, move, after, replies)))
    return tuple(out)
