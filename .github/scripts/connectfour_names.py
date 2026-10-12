# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named for what its drop does in Connect Four: an emoji, a commander's call, and plain words.

  from connectfour_names import listing

Chess names its moves as orders to an army; Connect Four's are a commander's
calls over the frame, in the game's own words: "Connect Four Across Row 2!"
for the win, "Block Row 2 or Lose!" for the only block, "Plant an Odd Threat
on Row 3!" for a threat that bides its time. A call names a row, a column or
a line where that tells the drop apart, and always ends with "!".

`read` takes a drop apart by brute force, looking up to four discs ahead, so
all it says is exact, and `kind` names the first of these the drop does:

- the win: four in a row, across a row, up a column or on a diagonal;
- the win passed up, when the mover could connect four elsewhere (a warning);
- the block: the disc takes the cell the other side would win on next, and
  with it what the block leaves (a strike back, a double threat of its own,
  or a game it cannot save);
- the draw: the last disc, filling the frame;
- the double threat: whatever the other side drops next, the mover wins on
  the drop after, by two threats at once, one threat over another, or no
  safe drop left to them;
- the blunder (a warning): the other side wins on its next drop, since the
  disc left their threat open or filled the cell under their winning cell;
- the double threat let in (a warning): the other side can answer with a
  double threat of its own;
- the only drop: every other drop loses, one of those two ways;
- the threat spent: the disc fills the cell under the mover's own winning
  cell, so the other side can block it;
- the threat: three in a line with the fourth cell open, either one they must
  block at once, or one that stands, called odd or even only where its row is
  the mover's kind (an odd row for the side that dropped first, an even row
  for the other) and no threat sits under it;
- the height: a disc that tops out a column, stacks on its own disc or caps
  one of theirs;
- the centre column, an edge, or a column's first disc.

Which colour dropped first is read from the position, so every name holds
whichever side the Arbiter opened for. A title depends only on the position
and the drop: a hash of the two picks among true calls, and no two drops on
one board share a title. Words name the discs White and Black, as players
see them. Stdlib only, with connectfour_rules.py beside it.
"""
from __future__ import annotations

import functools
import hashlib
from dataclasses import dataclass, replace

from connectfour_rules import COLS, DARK, LIGHT, ROWS, Position, legal, notation, other

DISC = {DARK: "black", LIGHT: "white"}  # each colour's discs, as a move's words name them
SIDE = {DARK: "Black", LIGHT: "White"}  # and each side, as a call names it
LONGEST = 48  # the longest title tannergolden/markdown takes
WORDS = 80  # the longest words tannergolden/markdown takes
CENTRE, EDGES = 4, {1: "Left", COLS: "Right"}
NUMBER = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}

# --- the frame as bits: column c's row r is bit (c - 1) * 7 + r - 1, with one bit kept clear above each column ----
H = ROWS + 1
BOTTOM = sum(1 << (col * H) for col in range(COLS))  # the foot of every column
FULL = BOTTOM * ((1 << ROWS) - 1)  # every cell of the frame
LINES = {"across": (1, 0), "up": (0, 1), "rising": (1, 1), "falling": (1, -1)}  # a four's four ways along the frame


def _bit(col: int, row: int) -> int:
    return 1 << ((col - 1) * H + row - 1)


def _cell(bit: int) -> tuple[int, int]:
    return (bit.bit_length() - 1) // H + 1, (bit.bit_length() - 1) % H + 1


def _each(bits: int):
    """Each cell a bitboard holds, as a bitboard of its own, column by column from the left."""
    while bits:
        low = bits & -bits
        yield low
        bits ^= low


def _cols(bits: int) -> tuple[int, ...]:
    return tuple(sorted({_cell(bit)[0] for bit in _each(bits)}))


def _playable(mask: int) -> int:
    """The cell the next disc down each column with room lands on."""
    return (mask + BOTTOM) & FULL


def _open(discs: int, mask: int) -> int:
    """The open cells that would complete four for `discs`: three of them in a line, and this cell the fourth."""
    found = (discs << 1) & (discs << 2) & (discs << 3)  # up a column: the three under it
    for step in (H, H - 1, H + 1):  # across a row, then the two diagonals
        pair = (discs << step) & (discs << 2 * step)
        found |= pair & (discs << 3 * step) | pair & (discs >> step)
        pair = (discs >> step) & (discs >> 2 * step)
        found |= pair & (discs >> 3 * step) | pair & (discs << step)
    return found & (FULL ^ mask)


def _forcing(mine: int, theirs: int, mask: int) -> bool:
    """Whether the side whose open cells are `mine`, having just dropped, wins on its next drop whatever the other
    side, whose open cells are `theirs`, drops now."""
    play = _playable(mask)
    if theirs & play or not play:
        return False
    return all(mine & ~reply & _playable(mask | reply) for reply in _each(play))


def _lines(discs: int, col: int, row: int) -> tuple[str, ...]:
    """The ways along the frame that a disc on the cell would connect four with `discs`."""
    found = []
    for name, (dc, dr) in LINES.items():
        count = 1
        for sign in (1, -1):
            c, r = col + sign * dc, row + sign * dr
            while 1 <= c <= COLS and 1 <= r <= ROWS and discs & _bit(c, r):
                count, c, r = count + 1, c + sign * dc, r + sign * dr
        if count >= 4:
            found.append(name)
    return tuple(found)


@functools.lru_cache(maxsize=256)
def _boards(position: Position) -> tuple[int, int]:
    """The discs of the side to drop and of the other side, as bitboards."""
    mine = theirs = 0
    for col in range(1, COLS + 1):
        for row in range(1, ROWS + 1):
            disc = position.at(col, row)
            if disc == position.turn:
                mine |= _bit(col, row)
            elif disc:
                theirs |= _bit(col, row)
    return mine, theirs


def opener(position: Position) -> str:
    """The colour that dropped first this game: the one with a disc more, or with as many, the one to drop now."""
    dark, light = position.cells.count(DARK), position.cells.count(LIGHT)
    return position.turn if dark == light else DARK if dark > light else LIGHT


# --- what a drop does ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Reading:
    """What one drop does, as its name reads it. Cells are (column, row); lines are LINES' names."""
    colour: str  # the mover's, D or L
    col: int
    row: int  # where the disc lands
    opener: bool = False  # the mover's colour dropped first this game
    first: bool = False  # the first disc of the game
    wins: tuple[str, ...] = ()  # the lines it connects four along
    fills: bool = False  # it fills the frame
    missed: tuple[int, ...] = ()  # the columns the mover could have won down instead
    blocks: tuple[str, ...] = ()  # the other side's lines it blocks, taking the cell they would win on next
    leaves: tuple[int, ...] = ()  # columns the other side could win down, still open after it
    opens: tuple[int, ...] = ()  # the column it opens to them, by filling the cell under their winning cell
    forces: str = ""  # how the mover wins on its next drop whatever they drop: "double", "stacked" or "squeeze"
    aims: tuple[tuple[int, int], ...] = ()  # the cells the mover could win on with its next drop
    makes: tuple[int, ...] = ()  # and their columns
    spends: bool = False  # it fills the cell under the mover's own winning cell
    doomed: tuple[int, ...] = ()  # the columns they could answer down with a double threat of their own
    plants: tuple[tuple[int, int], ...] = ()  # new threats that stand, lowest first: cells with an open cell under
    strong: tuple[tuple[int, int], ...] = ()  # those of the mover's kind (odd rows for the opener, even for the
    # other side) with no threat of either side under them in their column
    parity: str = ""  # "odd" or "even" when it plants a strong threat
    marked: tuple[int, int] | None = None  # the planted threat a title names: the lowest strong one, else the lowest
    below: str = ""  # what it lands on: "own", "theirs", or nothing on row 1
    run: int = 0  # how many discs of that colour run down the column under it
    aimed: tuple[str, ...] = ()  # the lines of its one threat to win at once
    only: bool = False  # every other drop on the board loses: the other side wins next, or by a double threat after

    @property
    def loses(self) -> bool:
        """Whether the other side can win on its next drop, or set a double threat with it."""
        return bool(self.leaves or self.opens or self.doomed)


def read(position: Position, col: int) -> Reading:
    """What dropping a disc down the column does, the side to drop being whichever the position says."""
    return readings(position)[col]


@functools.lru_cache(maxsize=64)
def readings(position: Position) -> dict[int, Reading]:
    """What every drop the position allows does, by its column, and which is the only one that does not lose."""
    found = {col: _read(position, col) for col in legal(position)}
    holding = [col for col, r in found.items() if not r.loses]
    tactics = any(r.wins or r.blocks for r in found.values())  # a win to take, or a block to make, says it already
    if len(found) > 1 and len(holding) == 1 and not tactics:
        found[holding[0]] = replace(found[holding[0]], only=True)
    return found


def _read(position: Position, col: int) -> Reading:
    colour, (me, foe) = position.turn, _boards(position)
    mask, row = me | foe, position.height(col) + 1
    cell = _bit(col, row)
    mine, theirs = _open(me, mask), _open(foe, mask)
    base = Reading(colour, col, row, opener=opener(position) == colour, first=not mask)
    if cell & mine:
        return replace(base, wins=_lines(me, col, row))
    mask2 = mask | cell
    play, play2 = _playable(mask), _playable(mask2)
    mine2, theirs2 = _open(me | cell, mask2), theirs & ~cell
    now2, threat, threat2 = mine2 & play2, theirs & play, theirs2 & play2
    fills, forces, doomed = mask2 == FULL, "", ()
    if not (fills or threat2):
        if _forcing(mine2, theirs2, mask2):
            count = now2.bit_count()
            forces = "double" if count > 1 else "stacked" if count else "squeeze"
        else:
            doomed = _cols(sum(reply for reply in _each(play2)
                               if _forcing(_open(foe | reply, mask2 | reply), mine2 & ~reply, mask2 | reply)))
    standing = mine2 & ~mine & ~play2

    def lowest(bit: int) -> bool:  # no threat of either side waits under it in its column
        c, _ = _cell(bit)
        under = (bit - 1) & ((1 << ROWS) - 1) << (c - 1) * H & ~mask2
        return not under & (mine2 | theirs2)

    plants = sorted((_cell(bit) for bit in _each(standing)), key=lambda c: (c[1], c[0]))
    kinds = [c for c in plants if lowest(_bit(*c)) and (c[1] % 2 == 1) == base.opener]
    below = position.at(col, row - 1)
    run = 0
    while run < row - 1 and position.at(col, row - 1 - run) == below:
        run += 1
    aims = tuple(_cell(bit) for bit in _each(now2))
    return replace(base, fills=fills, missed=_cols(mine & play), blocks=_lines(foe, col, row) if cell & threat else (),
                   leaves=_cols(threat2 & threat), opens=_cols(threat2 & ~threat), forces=forces, aims=aims,
                   makes=_cols(now2), spends=bool(cell << 1 & mine), doomed=doomed, plants=tuple(plants),
                   strong=tuple(kinds), parity=("odd" if base.opener else "even") if kinds else "",
                   marked=(kinds or plants or [None])[0], run=run,
                   below="" if row == 1 else "own" if below == colour else "theirs",
                   aimed=_lines(me | cell, *aims[0]) if len(aims) == 1 else ())


def kind(r: Reading) -> str:
    """The most telling thing the drop does, which its title is about: the first of these that it does."""
    if r.wins:
        return "win"
    if r.missed:
        return "missed"
    if r.blocks:
        return ("block draw" if r.fills else "block lost" if r.leaves or r.opens else "block double" if r.forces
                else "block doomed" if r.doomed else "strike" if r.makes else "block plant" if r.plants else "block")
    order = (("draw", r.fills), ("double", r.forces), ("ignore", r.leaves), ("under", r.opens), ("doomed", r.doomed),
             ("only", r.only), ("spend", r.spends), ("threat", r.makes), ("plant", r.plants), ("top", r.row == ROWS),
             ("stack", r.below == "own"), ("cap", r.below == "theirs"), ("opening", r.first),
             ("centre", r.col == CENTRE), ("edge", r.col in EDGES))
    return next((name for name, does in order if does), "open")


# --- the calls -------------------------------------------------------------------------------------------------------
# Each call is a true title for the drop it is kept for: `{row}` is where the disc lands, `{column}` its column
# ("Column 3", "the Centre Column") and `{in_place}` the same as a place ("in Column 3", "on the Left Edge"), `{foe}`
# the other side, and the rest as `_facts` has them. A hash of the position and the drop picks the first call tried,
# and the next free one stands in for a call the board has already given.
EMOJI = {"win": "🏆", "missed": "⚠️", "block": "🛡️", "strike": "⚔️", "block double": "💥", "block plant": "🛡️",
         "block lost": "⚠️", "block doomed": "⚠️", "block draw": "🤝", "draw": "🤝", "double": "💥", "ignore": "⚠️",
         "under": "⚠️", "doomed": "⚠️", "only": "🔑", "spend": "💸", "threat": "🎯", "plant": "📌", "top": "🔝",
         "stack": "🧱", "cap": "🪖", "opening": "⬇️", "centre": "⭐", "edge": "⬅️", "open": "⬇️"}
SIGNS = {"edge": {"Left": "⬅️", "Right": "➡️"}, "opening": {CENTRE: "⭐", 1: "⬅️", COLS: "➡️"}}
TITLES = {
    "win across": ("Connect Four Across Row {row}!", "Strike Four Across Row {row}!", "Seal Row {row} With Four!",
                   "Win It Across Row {row}!", "Take Row {row} and the Game!", "Lock In Four Across Row {row}!",
                   "Sweep Row {row}, Four in a Row!"),
    "win up": ("Connect Four Up Column {col}!", "Strike Four Up Column {col}!", "Top the Tower, Four Up Column {col}!",
               "Win It Up Column {col}!", "Stack the Fourth in Column {col}!", "Lock In Four Up Column {col}!",
               "Crown Column {col} With the Fourth!"),
    "win diagonal": ("Connect Four on the Diagonal!", "Strike Four Along the Diagonal!", "Run the Diagonal to Four!",
                     "Win It on the {diagonal}!", "Seal the {diagonal} With Four!", "Lock In Four on the {diagonal}!",
                     "Take the Game on the {diagonal}!"),
    "win twice": ("Connect Four {along}!", "Strike Four {along}!", "Win It {along}!", "Lock In Four {along}!",
                  "Seal Four {along}!", "Take the Game {along}!", "Take Four {along}!"),
    "win thrice": ("Connect Four {ways} Ways at Once!", "Strike Four {ways} Ways at Once!",
                   "Win It {ways} Ways at Once!", "Lock In Four {ways} Ways at Once!",
                   "Seal {ways} Fours With One Disc!", "Close {ways} Lines With One Disc!",
                   "Take the Game {ways} Ways Over!"),
    "missed": ("Pass Up the Win in {won}!", "Walk Past Your Four!", "Leave the Win in {won}!",
               "Miss Your Four in {won}!", "Skip the Winning Drop!", "Look Past the Win!", "Let the Win Slip Away!",
               "Ignore Your Own Four!"),
    "block across": ("Block Their Four Across Row {row}!", "Shut Down Row {row}!", "Cut Off Row {row}!",
                     "Block Row {row} or Lose!", "Stop Their Four on Row {row}!", "Slam Row {row} Shut!",
                     "Deny Them Row {row}!"),
    "block up": ("Cap Their Three {in_place}!", "Block the Tower {in_place}!", "Stop Their Climb {in_place}!",
                 "Block {column} or Lose!", "Shut Down {column}!", "Top Their Three, Block It!", "Deny Them {column}!"),
    "block diagonal": ("Block Their Diagonal!", "Cut the Diagonal!", "Break Their Diagonal Four!",
                       "Block the Diagonal or Lose!", "Shut Down the Diagonal!", "Deny Them the Diagonal!",
                       "Stop the Diagonal Cold!"),
    "block twice": ("Block Two Fours at Once!", "Stop Both Their Fours!", "Shut Two Lines With One Disc!",
                    "Block Twice With One Disc!", "Kill Two Fours With One Disc!", "Break Two Fours at Once!",
                    "Block Both Lines or Lose!"),
    "block thrice": ("Block {ways} Fours at Once!", "Shut {ways} Lines With One Disc!",
                     "Kill {ways} Fours With One Disc!", "Break {ways} Fours at Once!",
                     "Block All {ways} Lines or Lose!", "Stop {ways} Fours With One Disc!",
                     "Block {ways} Ways at Once!"),
    "strike": ("Block and Strike Back!", "Block and Threaten Column {aim}!", "Block and Counter in Column {aim}!",
               "Turn the Block Into a Threat!", "Block and Make Them Answer!", "Block, Then Aim at Column {aim}!",
               "Block With a Threat on Column {aim}!"),
    "block double": ("Block Into a Double Threat!", "Block and Spring a Double Threat!", "Block and Threaten Twice!",
                     "Block and Win Next Drop!", "Turn Defence Into a Double Threat!", "Block, Then Win, No Escape!",
                     "Block and Set Two Threats!"),
    "block stacked": ("Block Into a Stacked Threat!", "Block and Stack Threat on Threat!", "Block and Threaten Twice!",
                      "Block and Win Next Drop!", "Turn Defence Into a Stacked Threat!",
                      "Block, Then Win, No Escape!", "Block, Then Win in Column {aim}!"),
    "block triple": ("Block Into a Triple Threat!", "Block and Spring a Triple Threat!",
                     "Block and Threaten Three Ways!", "Block and Win Next Drop!", "Turn Defence Into a Triple Threat!",
                     "Block, Then Win, No Escape!", "Block and Set Three Threats!"),
    "block squeeze": ("Block and Leave Them No Safe Drop!", "Block Into Zugzwang!", "Block and Squeeze Them!",
                      "Block and Win Next Drop!", "Turn Defence Into Zugzwang!", "Block, Then Win, No Escape!",
                      "Block and Corner Them!"),
    "block plant odd": ("Block and Plant an {parity} Threat!", "Block and Dig In an {parity} Threat!",
                        "Block, Then Bank an {parity} Threat!", "Block and Set an {parity} Threat on Row {prow}!",
                        "Block and Stake an {parity} Threat!", "Block and Lay an {parity} Threat!",
                        "Block and Hold an {parity} Threat in Reserve!"),
    "block plant": ("Block and Set a Threat on Row {prow}!", "Block and Plant a Threat!", "Block and Dig In a Threat!",
                    "Block, Then Threaten Row {prow}!", "Block and Stake a Threat in Column {pcol}!",
                    "Block and Lay a Threat on Row {prow}!", "Block and Hold a Threat in Reserve!"),
    "block lost two": ("Block One, the Other Still Wins!", "Block What You Can!", "Block One of Their Two Fours!",
                       "Block One, Lose to the Other!", "Plug One Hole of Two!", "Stop One Four, Not Both!",
                       "Block in Vain, Two Fours Stand!"),
    "block lost trap": ("Block Into Their Trap!", "Block and Open the Cell Above!", "Block, but Lift Them to Four!",
                        "Block Under Their Second Threat!", "Block and Hand Them the Cell Above!",
                        "Block Into the Stacked Threat!", "Block Where the Trap Is Set!"),
    "block doomed": ("Block, but a Double Threat Looms!", "Block, Then Brace for Two Threats!",
                     "Block Into Their Double Threat!", "Block It, Their Double Threat Follows!",
                     "Block and Walk Into a Double Threat!", "Block, but Leave a Double Threat!",
                     "Block in Vain, a Double Threat Waits!"),
    "block draw": ("Block the Last Cell for a Draw!", "Block Their Four and Hold the Draw!",
                   "Seal the Frame, Block and Draw!"),
    "draw": ("Fill the Frame for a Draw!", "Drop the Last Disc for a Draw!", "Close the Frame and Call the Draw!",
             "Seal the Draw!", "Take the Last Cell and Draw!"),
    "double": ("Set a Double Threat on {aims}!", "Threaten {aims} at Once!", "Strike Twice, {aims}!",
               "Spring the Double Threat!", "Open Two Wins at Once!", "Make Them Block Two at Once!",
               "Win Next Drop, Two Threats Stand!"),
    "triple": ("Set a Triple Threat!", "Threaten {aims} at Once!", "Open Three Wins at Once!",
               "Strike Three Ways at Once!", "Win Next Drop, Three Threats Stand!", "Spring a Triple Threat!",
               "Make Them Block Three at Once!"),
    "stacked": ("Stack Threat on Threat in Column {aim}!", "Set Two Threats in Column {aim}!",
                "Double the Threat in Column {aim}!", "Spring the Stacked Threat!",
                "Threaten Rows {arow} and {atop} at Once!", "Make Them Block Under Your Win!",
                "Stack the Threats, No Escape!"),
    "squeeze": ("Squeeze Them, Every Drop Loses!", "Force Zugzwang, No Safe Drop!", "Leave Them No Safe Drop!",
                "Lock Them in Zugzwang!", "Squeeze Out Every Safe Drop!", "Win Next Drop by Zugzwang!",
                "Corner Them, Every Drop Loses!"),
    "ignore": ("Leave Their Four Open!", "Ignore the Threat in {threat}!", "Skip the Block in {threat}!",
               "Turn Your Back on {threat}!", "Let {foe} Connect Four!", "Look Away From {threat}!",
               "Abandon {threat} to {foe}!", "Miss the Block!"),
    "under": ("Play Under Their Threat!", "Hand {foe} the Win Above!", "Lift Them Into Four!",
              "Open Their Winning Cell!", "Fill Under Their Four!", "Give {foe} Row {above} of Column {col}!",
              "Prop Up Their Four!", "Set Up Their Four!"),
    "spend": ("Spend Your Threat on Row {above}!", "Cash In Your Threat!", "Burn Your Own Threat!",
              "Fill Under Your Own Four!", "Trade Your Threat for Their Block!", "Play Under Your Own Threat!",
              "Give Up Your Threat on Row {above}!"),
    "doomed": ("Let Them Set a Double Threat!", "Open the Door to a Double Threat!", "Walk Into Their Double Threat!",
               "Allow a Double Threat in {doom}!", "Leave Room for Their Double Threat!", "Give {foe} a Double Threat!",
               "Fall Into Their Double Threat!"),
    "only": ("Take {column} or Lose!", "Drop Here or Lose!", "Thread the Needle, All Else Loses!",
             "Hold Fast {in_place}, All Else Loses!", "Choose {column}, the Rest Lose!", "Slip the Trap {in_place}!",
             "Stand {in_place} or Fall!"),
    "threat": ("Threaten Four in Column {aim}!", "Make Them Block Column {aim}!", "Force the Block in Column {aim}!",
               "Take Aim at Column {aim}!", "Threaten Four {aimed}!", "Line Up Three, Aim at Column {aim}!",
               "Press Column {aim}, Make Them Block!"),
    "plant odd": ("Plant an {parity} Threat on Row {prow}!", "Dig In an {parity} Threat on Row {prow}!",
                  "Set an {parity} Threat in Column {pcol}!", "Stake an {parity} Threat on Row {prow}!",
                  "Lay an {parity} Threat in Column {pcol}!", "Bank an {parity} Threat for Later!",
                  "Hold an {parity} Threat in Reserve!"),
    "plant": ("Set a Threat on Row {prow}!", "Plant a Threat in Column {pcol}!", "Stake a Threat on Row {prow}!",
              "Lay a Threat in Column {pcol}!", "Dig In a Threat on Row {prow}!", "Hold a Threat in Reserve!",
              "Seed a Threat on Row {prow}!"),
    "plant two odd": ("Plant Two {parity} Threats!", "Dig In Two {parity} Threats!", "Bank Two {parity} Threats!",
                      "Stake Two {parity} Threats!", "Lay Two {parity} Threats!",
                      "Hold Two {parity} Threats in Reserve!", "Set Two {parity} Threats at Once!"),
    "plant two": ("Plant Two Threats!", "Dig In Two Threats!", "Set Two Threats at Once!", "Stake Two Threats!",
                  "Lay Two Threats!", "Hold Two Threats in Reserve!", "Seed Two Threats!"),
    "top": ("Top Off {column}!", "Close {column}!", "Seal the Top of {column}!", "Fill {column} to the Top!",
            "Shut {column} for Good!", "Take the Last Cell in {column}!", "Claim the Top of {column}!"),
    "stack": ("Stack Two High {in_place}!", "Double Up {in_place}!", "Build Your Tower {in_place}!",
              "Stack on Your Own Disc!", "Raise {column} to Row {row}!", "Climb {column} to Row {row}!",
              "Reinforce Your Disc {in_place}!"),
    "cap": ("Cap Their Disc {in_place}!", "Top Their Disc on Row {under}!", "Sit on Their Disc!",
            "Land on Their Disc {in_place}!", "Climb Over Their Disc!", "Smother Their Disc {in_place}!",
            "Bury Their Disc {in_place}!"),
    "cap two": ("Cap Their Two {in_place}!", "Cap Their Stack of Two!", "Stop Their Climb {in_place}!",
                "Top Their Tower of Two!", "Smother Their Stack of Two!", "Sit on Their Two-Stack!",
                "Shut Down Their Climb {in_place}!"),
    "opening centre": ("Open Dead Centre!", "Open the Game in the Centre!", "Lead Off in the Centre!",
                       "Seize the Centre From the Start!", "Strike First in the Centre!", "Take the Centre First!",
                       "Open on the Centre Column!"),
    "opening edge": ("Open on the {edge} Edge!", "Lead Off on the {edge} Edge!", "Open the Game on the {edge} Edge!",
                     "Strike First on the {edge} Edge!", "Take the {edge} Edge First!", "Start Out on the {edge} Edge!",
                     "Open Wide on the {edge} Edge!"),
    "opening": ("Open the Game in Column {col}!", "Lead Off in Column {col}!", "Strike First in Column {col}!",
                "Break Ground in Column {col}!", "Open in Column {col}!", "Take Column {col} First!",
                "Start Out in Column {col}!"),
    "centre": ("Seize the Centre!", "Take the Centre Column!", "Claim the Centre!", "Hold the Centre Column!",
               "Drive Into the Centre!", "Own the Centre Column!", "Command the Centre!"),
    "edge": ("Take the {edge} Edge!", "Anchor the {edge} Edge!", "Hold the {edge} Edge!", "Claim the {edge} Edge!",
             "Drop Down the {edge} Edge!", "Work the {edge} Edge!", "Dig In on the {edge} Edge!"),
    "open": ("Break Ground in Column {col}!", "Open Column {col}!", "Claim the Foot of Column {col}!",
             "Start Column {col}!", "Lay the First Disc in Column {col}!", "Stake Out Column {col}!",
             "Take the Foot of Column {col}!"),
    "open near": ("Break Ground in Column {col}!", "Open Column {col}!", "Back the Centre From Column {col}!",
                  "Build Beside the Centre!", "Lay the First Disc in Column {col}!", "Stake Out Column {col}!",
                  "Take the Foot of Column {col}!"),
}
PLACE = {CENTRE: "in the Centre", 1: "on the Left Edge", COLS: "on the Right Edge"}  # a column, said as a place


def calls(r: Reading) -> str:
    """Which of TITLES' calls fit the drop."""
    name = kind(r)
    if name in ("win", "block"):
        found = r.wins or r.blocks
        line = ("thrice" if len(found) > 2 else "twice" if len(found) > 1 else
                "diagonal" if found[0] in ("rising", "falling") else found[0])
        return f"{name} {line}"
    if name in ("double", "block double"):
        key = {"double": "double" if len(r.makes) == 2 else "triple"}.get(r.forces, r.forces)
        return key if name == "double" else f"block {key}"
    if name in ("plant", "block plant"):
        two = name == "plant" and len(r.strong if r.parity else r.plants) > 1
        return f"{name}{' two' if two else ''}{' odd' if r.parity else ''}"
    if name == "block lost":
        return "block lost two" if r.leaves else "block lost trap"
    if name == "cap" and r.run > 1:
        return "cap two"
    if name == "opening":
        return "opening centre" if r.col == CENTRE else "opening edge" if r.col in EDGES else "opening"
    if name == "open" and abs(r.col - CENTRE) == 1:
        return "open near"
    return name


def _facts(r: Reading) -> dict:
    """What a call can name about the drop."""
    column = "the Centre Column" if r.col == CENTRE else f"Column {r.col}"
    in_place = PLACE.get(r.col, f"in Column {r.col}")
    (aim, arow), (pcol, prow) = (r.aims or [(0, 0)])[0], r.marked or (0, 0)
    found = r.wins or r.blocks
    diagonal = ("Rising Diagonal" if "rising" in found else "Falling Diagonal") if len(found) == 1 else "Diagonal"
    return {"row": r.row, "col": r.col, "column": column, "in_place": in_place, "foe": SIDE[other(r.colour)],
            "edge": EDGES.get(r.col, ""), "diagonal": diagonal, "along": _along(r.wins, r.row, r.col, title=True),
            "won": _cols_said(r.missed), "threat": _cols_said(r.leaves), "doom": _cols_said(r.doomed),
            "aim": aim, "arow": arow, "atop": arow + 1, "above": r.row + 1, "under": r.row - 1,
            "aims": _cols_said(r.makes), "aimed": _along(r.aimed, arow, aim, title=True) if r.aimed else "",
            "ways": NUMBER.get(len(r.wins or r.blocks), "").capitalize(),
            "parity": r.parity.capitalize(), "prow": prow, "pcol": pcol}


def _cols_said(found: tuple[int, ...]) -> str:
    """Columns as a title says them: `Column 3`, `Columns 3 and 6`."""
    return columns(found).capitalize() if found else ""


def _along(lines: tuple[str, ...], row: int, col: int, title: bool = False) -> str:
    """The lines a four runs along, as words say them: `across row 2`, `up column 4`, `on a diagonal`, two of them
    joined with `and`, and three or more with the column the disc's own, `up, across row 2 and on a diagonal`; as a
    title says them, `Across Row 2`, `Up Column 4`, `on the Diagonal`."""
    across, up, diagonal = (("Across Row", "Up Column", "on the Diagonal") if title else
                            ("across row", "up column", "on a diagonal"))
    diagonals = [line for line in lines if line in ("rising", "falling")]
    said = [f"{across} {row}"] if "across" in lines else []
    said += [f"{up} {col}"] if "up" in lines else []
    if diagonals:
        said.append(("on Both Diagonals" if title else "on both diagonals") if len(diagonals) > 1 else diagonal)
    if len(said) > 2:  # three ways at once: up the disc's own column, said first and short
        said = ["Up" if title else "up"] + [way for way in said if not way.startswith(up)]
    return _and(said) if said else ""


def title(position: Position, r: Reading, used: set[str]) -> tuple[str, str, str]:
    """The drop's emoji and title, and the call it was made from: the call its hash picks, or while the board has
    given that call already, the next one it has not, and failing that, the next title it has not."""
    name, key, facts = kind(r), calls(r), _facts(r)
    emoji = SIGNS.get(name, {}).get(facts["edge"] if name == "edge" else r.col, EMOJI[name])
    start, options = _seed(position, r.col), TITLES[key]
    order = [options[(start + i) % len(options)] for i in range(len(options))]
    fits = [(call, call.format(**facts)) for call in order if len(call.format(**facts)) <= LONGEST]
    for call, said in [(c, t) for c, t in fits if c not in used] + fits:
        if said not in used:
            return emoji, said, call
    return emoji, f"Drop Down Column {r.col}!", ""  # every call here given already: the column tells it apart


def _seed(position: Position, col: int) -> int:
    """The drop's hash: the same position and column always pick the same call. It reads the frame as the mover sees
    it, its own discs and the other side's, so the same drop on the same frame gets the same call whichever colour
    the mover drops."""
    mover = position.turn
    seen = position.board.replace(mover, "M").replace(other(mover), "F")
    text = f"connectfour:{seen}:{'first' if opener(position) == mover else 'second'}:{col}"
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


# --- the words -------------------------------------------------------------------------------------------------------
def columns(found: tuple[int, ...]) -> str:
    """Columns as a sentence says them: `column 3`, `columns 3 and 6`, `columns 1, 3 and 6`."""
    names = [str(c) for c in found]
    said = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"column{'s' if len(names) > 1 else ''} {said}"


def words(position: Position, col: int) -> str:
    """The drop in plain words: `A white disc down column 4, to row 1`, `A black disc down column 3 blocks on row 2`,
    `A white disc down column 2 connects four on a diagonal`, with what else it does as far as the words have room."""
    return said(read(position, col))


def said(r: Reading) -> str:
    """The words for a reading."""
    disc = f"A {DISC[r.colour]} disc down column {r.col}"
    if r.wins:
        text = f"{disc} connects four {_along(r.wins, r.row, r.col)}"
        return text if len(text) <= WORDS else f"{disc} connects four {len(r.wins)} ways at once"
    head = f"{disc} blocks on row {r.row}" if r.blocks else f"{disc}, to row {r.row}"
    for tail in _tails(r):
        if len(head + tail) <= WORDS:
            return head + tail
    return head


def _tails(r: Reading) -> list[str]:
    """What the words can add to where the disc goes, by what its title is about: the fullest first, then shorter
    ways to say it, then nothing."""
    name, foe = kind(r), SIDE[other(r.colour)]
    if name in ("block draw", "draw"):
        return [", filling the frame for a draw", ""]
    if name == "missed":
        passing = f", passing up the win in {columns(r.missed)}"
        return [passing + tail for tail in (_lost(r, foe) if r.leaves or r.opens else [])] + [passing, ""]
    if name in ("block lost", "ignore", "under"):
        return _lost(r, foe) + [""]
    if name in ("block double", "double"):
        if r.forces == "squeeze":
            return [f", leaving {foe} no safe drop", ""]
        if r.forces == "stacked":
            (aim, arow), = r.aims
            return [f", threatening column {aim} on rows {arow} and {arow + 1}", ""]
        return [f", threatening {columns(r.makes)}", ""]
    if name in ("block doomed", "doomed"):
        return [f", giving {foe} a double threat in {columns(r.doomed)}", f", giving {foe} a double threat", ""]
    if name == "only":
        return [", where every other drop loses", ""]
    if name == "spend":
        return [f", spending {SIDE[r.colour]}'s threat on row {r.row + 1}", ""]
    if name in ("strike", "threat"):
        return [f", threatening {columns(r.makes)}", ""]
    if name in ("block plant", "plant"):
        cells = r.plants
        setting = f", setting {NUMBER[len(cells)]} threats" if len(cells) > 1 else ", setting a threat"
        if len({c for c, _ in cells}) == 1:
            rows = _and([str(row) for _, row in cells])
            return [f", threatening row{'s' if len(cells) > 1 else ''} {rows} of column {cells[0][0]}", setting, ""]
        return [", threatening " + _and([f"row {row} of column {c}" for c, row in cells]), setting, ""]
    return [", filling the column", ""] if name == "top" else [""]


def _lost(r: Reading, foe: str) -> list[str]:
    """How the words say the other side wins on its next drop: the columns left to them and opened to them."""
    left, opened = f"leaving {columns(r.leaves)}" if r.leaves else "", f"opening {columns(r.opens)}" if r.opens else ""
    both = [f", {opened} and {left} to {foe}"] if left and opened else []
    return both + [f", {left or opened} to {foe}"]


def _and(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


# --- the board's list ------------------------------------------------------------------------------------------------
def listing(position: Position, game: int, ply: int) -> list[dict]:
    """Every open column from the left, each with its notation, its words, an emoji and a title no other drop here
    has. The game and the move number name nothing: a board is named by its position alone."""
    return [dict(entry) for entry in _listing(position)]


@functools.lru_cache(maxsize=64)
def _listing(position: Position) -> tuple[dict, ...]:
    used, out = set(), []
    for col in legal(position):
        r = read(position, col)
        emoji, name, call = title(position, r, used)
        used |= {name, call}
        out.append({"code": str(col), "notation": notation(position, col), "emoji": emoji, "title": name,
                    "words": said(r)})
    return tuple(out)
