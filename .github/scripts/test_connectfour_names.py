# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every open column named for what its drop plainly is in Connect Four, and for nothing it does to the game: every
board of many random games, both ways round (Black dropping first and White dropping first), held to the owner's rule
that no name may help a player choose, and to what the kit takes.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import connectfour_names as N
import connectfour_rules as R
from connectfour_names import EMOJI, LONGEST, TITLES, WORDS, listing, words

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
FIRSTS = (R.DARK, R.LIGHT)  # Black drops first, then White drops first
SIDE = {R.DARK: "Black", R.LIGHT: "White"}
SWAP = str.maketrans("DL", "LD")  # a frame with the colours the other way round
COLOURS = re.compile(r"\b(?:Black|White|black|white)\b")
PLACES = {1: "the Left Edge", 2: "Column 2", 3: "Column 3", 4: "the Centre Column", 5: "Column 5", 6: "Column 6",
          7: "the Right Edge"}  # each column as a title names it
VERBS = {"Drop", "Send", "Slide", "Lay", "Stack", "Set", "Put", "Land", "Top", "Fill"}  # a commander's short verbs
SMALL = {"a", "an", "and", "at", "by", "in", "of", "on", "or", "the", "to"}  # the words Title Case keeps small

# The owner's rule, as the brief all four games' names share sets it out: nothing a player reads may judge a drop,
# say what it does to the game or what it meets there, carry a verdict of strategy, or name an opening, and no emoji
# may flag one. Connect Four's own words for those are here too: four in a row, the threat and the block, odd and even.
JUDGEMENTS = (
    "good", "bad", "safe", "sound", "strong", "weak", r"win(?:s|ning|ner)?", "won", r"loses?", "losing", "lost",
    r"draw(?:s|n)?", r"saves?", "saving", r"hold(?:s|ing)?", "slip", "only", "best", r"forces?", "forced", "forcing",
    "blunder", "mistake", "must", "key", "dead",
    "check", "mate", "stalemate", r"threat(?:s|en|ens|ening)?", r"block(?:s|ed|ing)?", "fork", "pin", "skewer",
    r"discover(?:s|ed)?", "double", "triple", r"trap(?:s|ped)?", "shot", "sacrifice", "gambit", "exchange", "trade",
    r"attack(?:s|ing)?", r"defen(?:d|ds|ding|ce)", "guard", "escape", r"hang(?:s|ing)?", "next", r"leaves?", "leaving",
    r"lets?", r"connect(?:s|ed|ing)?", "four", "three", "in a row", "zugzwang", "squeeze", "strike", "deny", "stop",
    "cut", "seal", "lock", r"miss(?:es|ed)?", r"pass(?:es|ing)? up", "ignore", "abandon", r"doom(?:ed)?", "aim",
    "press", "answer", "counter", "spend", "cap", "smother", "bury", r"lines?", "across", "diagonal", "up column",
    "rim", "outpost", "battery", "seize", "command", "control", "claim", "bridge", "odd", "even", "parity", "tower",
    "climb", "anchor", "reinforce", "reserve", "bank", "stake", r"open(?:s|ed|ing)?",
)
JUDGED = re.compile(rf"\b(?:{'|'.join(JUDGEMENTS)})\b", re.IGNORECASE)
FLAGS = ("⚠️", "🏆", "🔑", "🛡️", "⚡", "🎯", "💥", "💸", "📌", "🍴", "🎁", "💰", "🔄", "☠️", "🤝", "📖", "⚔️", "📍",
         "❗", "✅", "❌", "👍", "👎", "🔥", "💯", "🚨", "⛔", "🚫", "🥇", "🏅", "💀")


def drop(line: str, first: str = R.DARK) -> R.Position:
    """The position after the drops, `first` the colour that dropped first."""
    position = R.opening(first)
    for col in line:
        position = R.make(position, int(col))
    return position


def frame(text: str, first: str = R.DARK) -> R.Position:
    """The position a frame of D, L and dots describes, `first` the colour that dropped first."""
    return R.Position.from_board(text, first)


def games(n: int, seed: int, long: bool = False) -> list[R.Position]:
    """Every position of `n` games of seeded random play with a drop left to make, every other game White first, each
    read back from its frame as the page's sheet writes it. In a `long` game neither side connects four while it has
    another drop to make, so the frame fills to the top."""
    rng, out = random.Random(seed), []
    for game in range(n):
        first = FIRSTS[game % 2]
        position = R.opening(first)
        while R.legal(position):
            out.append(frame(position.board, first))
            options = R.legal(position)
            if long:
                options = [col for col in options if not R.ending(R.make(position, col))] or options
            position = R.make(position, rng.choice(options))
    return out


BOARDS = games(200, 5) + games(60, 7, long=True)  # many boards, both ways round, and frames filled to the top
NAMED = {position: listing(position, 1, 1) for position in BOARDS}  # every board's names, once for every test


# --- what a drop plainly is, and what it does, read off the frame with nothing of the names module's ----------------
def plain(position: R.Position, col: int) -> tuple[str, int, int, str]:
    """What a drop plainly is, cell by cell: the disc's colour, its column, the row it lands on and what it lands on."""
    row = next(row for row in range(1, R.ROWS + 1) if not position.at(col, row))
    under = position.at(col, row - 1)
    return position.turn, col, row, "floor" if not under else "own" if under == position.turn else "theirs"


def sign(colour: str, col: int, row: int, below: str) -> str:
    """The emoji for a drop's kind: the disc that fills its column, else what it lands on, else the column it starts."""
    if row == R.ROWS:
        return "🔝"
    return "🧱" if below != "floor" else {1: "⬅️", 7: "➡️"}.get(col, "⬇️")


def does(position: R.Position, col: int) -> str:
    """What a drop does to the game, found by making it, which nothing in its name may tell: it connects four, takes
    the cell the other side would connect four on, lets them connect four next, or does none of those."""
    mover, after = position.turn, R.make(position, col)
    end = R.ending(after)
    if end and end.winner == mover:
        return "wins"
    if col in R.threats(position, R.other(mover)):
        return "takes"
    return "hands" if not end and R.threats(after, R.other(mover)) else "nothing"


def title_case(text: str) -> bool:
    """Whether a title is in Title Case: every word capitalised but the small ones after the first, so every word of
    four letters or more."""
    found = re.findall(r"[A-Za-z]+", text)
    return all(word == (word.lower() if i and word.lower() in SMALL else word[:1].upper() + word[1:])
               for i, word in enumerate(found))


def faults(m: dict, colour: str, col: int, row: int, below: str) -> list[str]:
    """What is wrong with a listed drop by the owner's rule and the kit's: nothing, for a name that says only what the
    drop plainly is, in what the kit takes."""
    name, said = m["title"], m["words"]
    under = {"own": SIDE[colour], "theirs": SIDE[R.other(colour)]}.get(below)
    named = [[], [SIDE[colour]]] + ([[SIDE[colour], under]] if under and row < R.ROWS else [])
    goes = f"A {SIDE[colour].lower()} disc down column {col}, to row {row}"
    checks = {
        "the column as its code": m["code"] == str(col),
        "the column alone as its notation": m["notation"] == str(col),
        "the emoji of its kind": m["emoji"] == sign(colour, col, row, below),
        "an emoji the kit takes": bool(KIT_EMOJI.fullmatch(m["emoji"])),
        "a title the kit takes": bool(KIT_TITLE.fullmatch(name)) and len(name) <= LONGEST,
        "words the kit takes": bool(KIT_WORDS.fullmatch(said)) and len(said) <= WORDS,
        "where the disc goes, and nothing more": said == goes,
        "a call of its kind": name in {call.format(**N.facts(N.Drop(colour, col, row, below)))
                                       for call in TITLES["top" if row == R.ROWS else below]},
        "a commander's call": name.endswith("!") and name.split()[0] in VERBS,
        "Title Case": title_case(name),
        "its column and no other": PLACES[col] in name and not any(PLACES[c] in name for c in PLACES if c != col),
        "the disc's colour, then the colour it lands on": COLOURS.findall(name) in named,
        "the row it lands on": all(int(n) == row for n in re.findall(r"\bRow (\d)", name)),
        "the top for the last row alone": (row == R.ROWS) == bool(re.search(r"\b(?:Top|Sixth|Row 6)\b", name)),
        "the floor for the first row alone": row == 1 or not re.search(r"\b(?:First|Floor|Row 1)\b", name),
        "no judgement": not (JUDGED.search(name) or JUDGED.search(said)),
        "no emoji that flags": not any(flag in text for flag in FLAGS for text in (m["emoji"], name, said)),
        "no mark that judges": not {"+", "#"} & set(m["notation"] + name + said),
        "no dash": not any(dash in name + said for dash in DASHES),
        "White and Black": not re.search(r"\b(?:dark|light)\b", f"{name} {said}".lower()),
    }
    return [what for what, ok in checks.items() if not ok]


# Drops to the same kind of place that do different things to the game, each group down one column to one row: the
# column, then the frames, or the drops that make them with Black first, each with what its drop does. Each group lands
# on one colour, but for the disc that fills a column, whose calls never say what it lands on.
ALIKE = {
    "a column's first disc, in the centre": (4, (("112233", "wins"), ("", "nothing"), ("171727", "hands"),
                                                 ("151627", "takes"))),
    "a disc onto its own colour": (3, (("313132", "wins"), ("3331", "nothing"), ("33371717", "hands"))),
    "a disc onto the other side's": (4, (("......./......./......./..DL.../.DLD.../DLDL..L", "wins"),
                                         ("......./......./....LLL/...LDDD/...DLDD/D..LDLL", "takes"),
                                         ("1444", "nothing"))),
    "the disc that fills a column": (2, (("......./.D...../.D...../.D...../.L...../.L....L", "wins"),
                                         ("......./.D...../.D...../.L...../.D...../.L....L", "nothing"),
                                         ("......./.L...../.D...../.D...../.D...../.L....L", "nothing"))),
}
LIVE = "......./......./......./......./......./.....L."  # the profile's game 1: the Arbiter's ⚪6, Black to drop


class Neutral(unittest.TestCase):
    def test_every_board_names_every_open_column_once_for_what_its_drop_plainly_is(self):
        held = set()  # each drop and its name, held to the rule once: `faults` reads nothing else
        for position, named in NAMED.items():
            self.assertEqual([m["code"] for m in named], [str(c) for c in R.legal(position)])
            self.assertEqual(len({m["title"] for m in named}), len(named), position.board)
            for m in named:
                key = plain(position, int(m["code"]))
                if (key, tuple(m.items())) not in held:
                    self.assertEqual(faults(m, *key), [], (position.board, m))
                    held.add((key, tuple(m.items())))
        self.assertEqual({position.first for position in NAMED}, set(FIRSTS), "both ways round")
        self.assertEqual({m["emoji"] for named in NAMED.values() for m in named}, set(EMOJI.values()))

    def test_a_drop_is_named_for_what_it_is_and_never_for_what_it_does(self):
        names, done = {}, defaultdict(set)
        for i, (position, named) in enumerate(NAMED.items()):
            for m in named:
                key = plain(position, int(m["code"]))
                self.assertEqual(m, names.setdefault(key, m), (position.board, key))
                if i % 5 == 0:  # what it does, for a fifth of the boards
                    done[key].add(does(position, int(m["code"])))
        self.assertEqual(len(names), 2 * (7 + 7 * 5 * 2), "every drop there can be, by both colours")
        for what in ("wins", "takes", "hands"):  # and each named alike when it does that and when it does nothing
            self.assertGreater(sum(what in found and "nothing" in found for found in done.values()), 90, what)

    def test_a_winning_drop_and_a_quiet_one_to_the_same_kind_of_place_read_alike(self):
        for name, (col, cases) in ALIKE.items():
            for first in FIRSTS:
                with self.subTest(name, first=SIDE[first]):
                    positions = [frame(case if first == R.DARK else case.translate(SWAP), first) if "/" in case
                                 else drop(case, first) for case, _ in cases]
                    self.assertEqual([does(position, col) for position in positions], [what for _, what in cases])
                    named = [next(m for m in listing(position, 1, 1) if m["code"] == str(col))
                             for position in positions]
                    self.assertEqual(named, [named[0]] * len(named))
                    self.assertEqual(faults(named[0], *plain(positions[0], col)), [])
                    self.assertEqual((R.notation(positions[0], col), named[0]["notation"]), (f"{col}#", str(col)),
                                     "the rules' sheet marks the win, and the list never does")

    def test_the_listed_notation_is_the_column_alone_where_the_score_sheet_marks_a_win(self):
        marked = 0
        for position in NAMED:
            for m in NAMED[position]:
                written = R.notation(position, int(m["code"]))
                self.assertEqual(m["notation"], written.removesuffix("#"))
                marked += written != m["notation"]
        self.assertGreater(marked, 2000, "the sweep holds a drop that wins on most boards")


class Calls(unittest.TestCase):
    def test_every_call_is_true_and_fits_for_every_drop_there_can_be(self):
        self.assertEqual(set(TITLES), {"floor", "own", "theirs", "top"})
        checked = 0
        for colour in FIRSTS:
            for col in range(1, R.COLS + 1):
                for row in range(1, R.ROWS + 1):
                    for below in ("floor",) if row == 1 else ("own", "theirs"):
                        d = N.Drop(colour, col, row, below)
                        for call in TITLES[N.calls(d)]:
                            m = {"code": str(col), "notation": str(col), "emoji": EMOJI[N.kind(d)],
                                 "title": call.format(**N.facts(d)), "words": N.said(d)}
                            self.assertEqual(faults(m, colour, col, row, below), [], m)
                            checked += 1
        self.assertEqual(checked, 2 * 7 * (1 + 5 * 2) * 6)
        for key, options in TITLES.items():
            self.assertEqual(len(set(options)), len(options), key)

    def test_no_two_columns_can_share_a_title(self):
        for colour in FIRSTS:
            said = defaultdict(set)
            for col in range(1, R.COLS + 1):
                for row in range(1, R.ROWS + 1):
                    for below in ("floor",) if row == 1 else ("own", "theirs"):
                        d = N.Drop(colour, col, row, below)
                        said[col] |= {call.format(**N.facts(d)) for call in TITLES[N.calls(d)]}
            for a in range(1, R.COLS + 1):
                for b in range(a + 1, R.COLS + 1):
                    self.assertFalse(said[a] & said[b], (SIDE[colour], a, b))

    def test_each_kind_of_drop_has_an_emoji_of_its_own_and_none_flags_a_drop(self):
        self.assertEqual(set(EMOJI), {"top", "onto", "left", "right", "floor"})
        self.assertEqual(len(set(EMOJI.values())), len(EMOJI))
        for emoji in EMOJI.values():
            self.assertTrue(KIT_EMOJI.fullmatch(emoji), emoji)
            self.assertEqual(len(emoji.replace("\N{VARIATION SELECTOR-16}", "")), 1, "one emoji")
            self.assertNotIn(emoji, FLAGS)

    def test_the_same_position_and_drop_always_get_the_same_name(self):
        for position in list(NAMED)[::40]:
            once = listing(position, 1, 1)
            self.assertEqual(listing(position, 7, 30), once, "the game and the move number name nothing")
            self.assertEqual(listing(frame(position.board, position.first), 2, 9), once)
            self.assertEqual([m["words"] for m in once], [words(position, int(m["code"])) for m in once])
        self.assertEqual([(m["emoji"], m["title"]) for m in listing(frame(LIVE, R.LIGHT), 1, 2)], [
            ("⬅️", "Lay the First Disc on the Left Edge!"), ("⬇️", "Send Black to the Floor in Column 2!"),
            ("⬇️", "Drop Black Down Column 3!"), ("⬇️", "Send Black to the Floor in the Centre Column!"),
            ("⬇️", "Slide Black Down Column 5 to Row 1!"), ("🧱", "Land Black on White in Column 6!"),
            ("➡️", "Drop Black to Row 1 on the Right Edge!")])
        self.assertEqual([m["words"] for m in listing(frame(LIVE, R.LIGHT), 1, 2)][5],
                         "A black disc down column 6, to row 2")

    def test_the_same_drop_on_the_same_frame_is_named_the_same_whichever_colour_drops_it(self):
        for position in list(NAMED)[::25]:
            swapped = frame(position.board.translate(SWAP), R.other(position.first))
            for mine, theirs in zip(listing(position, 1, 1), listing(swapped, 1, 1), strict=True):
                self.assertEqual(mine["emoji"], theirs["emoji"])
                for field in ("title", "words"):  # the same, but for the colours they name
                    self.assertEqual(COLOURS.sub("_", mine[field]), COLOURS.sub("_", theirs[field]))


if __name__ == "__main__":
    unittest.main()
