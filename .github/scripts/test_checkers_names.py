# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: what a move is read as, the title and words it is given, and that a board keeps them.

  python3 -m unittest discover -s .github/scripts -p 'test_checkers*.py'
"""
from __future__ import annotations

import random
import re
import string
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checkers_names as names
from checkers_names import OWN_ORDERS, SHORT, THEMES, name, named, read, theme, words
from checkers_rules import START, Position, find, legal_moves, make

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py,
# whose checks every game's moves share).
KIT_EMOJI = re.compile("[\u2190-\u2bff\U0001f000-\U0001faff\u200d\ufe0f]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
# A position for each theme a move can have, with the move that has it.
EXAMPLES = {
    "victory": ("W:WK14:B10", "14x7"),  # the last dark piece taken
    "blockade": ("W:W26,27:B28,K32", "26-23"),  # the square the dark king would jump to, filled
    "crown": ("B:W27:B28", "28-32"),
    "sweep": ("B:W6,15,24,32:B1", "1x10x19x28"),
    "double": ("W:W11,K16:BK19,K21,26", "16x23x30"),
    "flagship": ("W:WK24:B9,K19", "24x15"),  # a king taken
    "board": ("W:WK18:BK13,15", "18x11"),
    "trap": ("B:W14,K16:B2,6", "6-10"),  # 14x7 is forced, and 2x11x20 takes two back
    "bait": ("W:W28:BK20", "28-24"),  # the dark king can jump it
    "threat": ("W:WK4:B11", "4-8"),  # from 8 the king could jump 11
    "escape": ("W:W25:B21", "25-22"),  # the dark man on 21 could jump 25, not 22
    "guard": ("B:W31:B20,K27", "20-24"),  # the light man on 31 could jump the king on 27 to 24, until 24 is filled
    "corner": ("B:WK4:BK32", "32-28"),
    "come-about": ("B:W26:BK29", "29-25"),
    "cruise": ("B:WK2:BK4", "4-8"),
    "landfall": ("B:W26:B21", "21-25"),  # one row short of the crown
    "port": ("W:W29:B19", "29-25"),  # off its own back row
    "coast": ("W:W17:BK3", "17-13"),
    "channel": ("B:W12:B14", "14-18"),
    "sail": ("B:WK18:B5", "5-9"),
}
# The design's orders for checkers (games-preview's samples), every one of which the themes keep.
DESIGN = ("Make Him Admiral!", "Raise the Crown!", "Crown the Captain!", "Rake Their Whole Line!", "Double Broadside!",
          "Clear Their Decks!", "Board Them!", "Take Their Ship!", "Ram Them Amidships!", "Bait the Hook!",
          "Sail Into Their Guns!", "Send In the Fire Ship!", "The Admiral Sails!", "Come About!", "Patrol the Waters!",
          "Hug the Coast!", "Hold the Harbour Wall!", "Drop Anchor!", "Leave Port!", "Weigh Anchor!", "Cast Off!",
          "Full Sail Ahead!", "Steady As She Goes!", "Make Way!", "Take the Wind!", "Hold the Channel!",
          "Trim the Sails!", "Run Before the Wind!", "Into Open Water!", "Ahead Two Thirds!")
# The brief's word for each kind of move: the order, and its emoji.
VOICE = {"sail": ("⛵", "Full Sail Ahead!"), "board": ("⚔️", "Board Them!"), "double": ("💥", "Rake Their Whole Line!"),
         "crown": ("👑", "Make Him Admiral!"), "bait": ("🎣", "Bait the Hook!"), "come-about": ("🧭", "Come About!")}
OPENING = ["11-15", "23-19", "8-11", "22-17", "10-14", "17x10", "7x14", "19x10", "6x15", "24-20", "15-18", "27-24",
           "12-16", "31-27", "3-8", "26-22", "1-6", "22x15", "11x18"]
CROWNED = ["11-15", "23-19", "8-11", "22-17", "10-14", "17x10", "7x14", "19x10", "6x15", "26-22", "3-7", "27-23",
           "4-8", "32-27", "9-13", "22-17", "13x22", "25x18x9", "5x14", "29-25", "1-5", "24-20", "15-18", "23-19",
           "7-10", "27-23", "18x27", "31x24", "11-15", "25-22", "14-18", "22-17", "2-6", "17-14", "10x17", "19x10x1"]
CROWDED = ("B:W32:BK1,K2,K3,K4,K9,K10,K11,K12,K17,K18,K19,K20",  # twelve kings with thirty-five moves between them
           "W:WK13,K14,K15,K16,K21,K22,K23,K24,K29,K30,K31,K32:B1",
           "B:W6,8,9,10,11,13,17,18,19,25,26,27:BK32")  # a king with a dozen ways to take nine


def played(*codes: str, fen: str = "") -> list[Position]:
    positions = [Position.from_fen(fen) if fen else START]
    for code in codes:
        positions.append(make(positions[-1], find(positions[-1], code)))
    return positions


def boards(n: int, seed: int = 7):
    """Every position of `n` games of random legal moves, each with a move to make."""
    rng = random.Random(seed)
    for _ in range(n):
        position = START
        for _ in range(rng.randint(10, 160)):
            moves = legal_moves(position)
            if not moves:
                break
            yield position
            position = make(position, rng.choice(moves))


def fields(pattern: str) -> list[str]:
    return [field for _, field, _, _ in string.Formatter().parse(pattern) if field]


class Reading(unittest.TestCase):
    def test_a_move_is_named_for_the_most_telling_thing_it_does(self):
        self.assertEqual(set(EXAMPLES), set(THEMES), "an example for every theme")
        for want, (fen, code) in EXAMPLES.items():
            with self.subTest(theme=want):
                position = Position.from_fen(fen)
                move = find(position, code)
                self.assertIsNotNone(move)
                self.assertEqual(theme(read(position, move)), want)
                self.assertEqual(name(position, move)[0], THEMES[want][0])

    def test_its_words_say_what_it_does(self):
        self.assertEqual(name(START, find(START, "11-15"))[2], "Man from 11 to 15")
        board = played(*OPENING)[-1]
        self.assertEqual(name(board, find(board, "20x11"))[2], "Man from 20 jumps 16, landing on 11")
        board = played(*CROWNED[:-1])[-1]
        self.assertEqual(name(board, find(board, "19x10x1"))[2], "Man from 19 jumps 15 and 6, landing on 1, crowned")
        said = {code: words(Position.from_fen(fen), find(Position.from_fen(fen), code))
                for fen, code in EXAMPLES.values()}
        self.assertEqual(said["4-8"], "King from 4 to 8")
        self.assertEqual(said["1x10x19x28"], "Man from 1 jumps 6, 15 and 24, landing on 28")
        self.assertEqual(said["14x7"], "King from 14 jumps 10, landing on 7, winning the game")
        self.assertEqual(said["26-23"], "Man from 26 to 23, winning the game")
        self.assertEqual(said["28-32"], "Man from 28 to 32, crowned")

    def test_a_long_run_of_jumps_says_how_many_when_which_would_not_fit(self):
        board = Position.from_fen("B:W6,8,9,10,11,13,17,18,19,25,26,27:BK32")
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps 27, 18, 10, 11, 19, 26, 25, 17 and 9, landing on 5")
        board = Position.from_fen("B:W9,10,11,17,18,19,25,26,27:BK32")  # the same nine, and nothing else left
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps nine pieces, landing on 5, winning the game")

    def test_a_fire_ship_wins_back_more_than_it_gives_and_bait_does_not(self):
        positions = played(*CROWNED)
        for ply, want in ((4, "bait"), (15, "trap"), (33, "trap")):  # 10-14 trades one for one; 22-17 and 17-14 win two
            with self.subTest(move=CROWNED[ply]):
                board = positions[ply]
                self.assertEqual(theme(read(board, find(board, CROWNED[ply]))), want)

    def test_a_man_bears_to_port_or_starboard_from_its_own_heading(self):
        self.assertEqual(read(START, find(START, "11-16")).side, "Port")  # dark heads down the board: its left is east
        self.assertEqual(read(START, find(START, "11-15")).side, "Starboard")
        board = played("11-15")[-1]
        self.assertEqual(read(board, find(board, "22-17")).side, "Port")  # light heads up: its left is west
        self.assertEqual(read(board, find(board, "22-18")).side, "Starboard")
        board = Position.from_fen("B:W32:BK18")
        self.assertEqual(read(board, find(board, "18-22")).side, "", "a king has no heading to turn from")


class Titles(unittest.TestCase):
    def test_every_board_names_every_move_once_in_what_the_kit_accepts(self):
        count = 0
        for position in [*boards(40), *map(Position.from_fen, CROWDED)]:
            listed = named(position)
            self.assertEqual([move for move, _, _, _ in listed], legal_moves(position))
            titles = [title for _, _, title, _ in listed]
            self.assertEqual(len(set(titles)), len(titles), position.fen)
            for move, emoji, title, said in listed:
                count += 1
                self.assertTrue(KIT_EMOJI.fullmatch(emoji), emoji)
                self.assertTrue(KIT_TITLE.fullmatch(title), title)
                self.assertTrue(KIT_WORDS.fullmatch(said), said)
                self.assertEqual(emoji, THEMES[theme(read(position, move))][0], title)
                self.assertFalse(any(dash in title + said for dash in DASHES))
        self.assertGreater(count, 10_000)

    def test_every_title_is_an_order_and_never_names_a_square(self):
        short = total = 0
        for position in boards(40):
            for _, _, title, _ in named(position):
                self.assertTrue(title.endswith("!"), title)
                self.assertNotRegex(title, r"[0-9]", "the code beside it names the squares")
                short, total = short + (len(title) <= SHORT), total + 1
        self.assertGreater(short / total, 0.85, "most orders read at a glance")

    def test_a_crowded_board_still_gives_every_move_its_own_order(self):
        for fen in CROWDED:
            with self.subTest(fen=fen):
                listed = named(Position.from_fen(fen))
                self.assertGreater(len(listed), 6)
                self.assertEqual(len({title for _, _, title, _ in listed}), len(listed))

    def test_the_plain_orders_a_crowded_board_falls_back_on_outnumber_any_board_s_moves(self):
        for fen, code, key in (("", "11-15", "sail"), ("B:W32:BK18", "18-22", "cruise"),
                               ("W:WK18:BK13,15", "18x11", "board")):
            with self.subTest(fallback=key):
                board = Position.from_fen(fen) if fen else START
                titles = list(names.every_title(read(board, find(board, code)), key))
                self.assertGreater(len(set(titles)), 200)
                self.assertTrue(all(KIT_TITLE.fullmatch(title) for title in titles))

    def test_when_every_draw_comes_up_taken_each_move_still_gets_its_own(self):
        draw, every = names.title, names.every_title
        try:
            names.title = lambda *args, **kwargs: None  # no draw finds a title: the titles in order
            names._named.cache_clear()
            for fen in CROWDED:
                titles = [title for _, _, title, _ in named(Position.from_fen(fen))]
                self.assertEqual(len(set(titles)), len(titles))
            names.every_title = lambda reading, key: iter(["Make Way!"])  # and only one of those: urged on
            names._named.cache_clear()
            titles = [title for _, _, title, _ in named(START)]
            self.assertEqual(titles, ["Make Way!", "Make Way, Now!", "Make Way, Again!", "Make Way, Together!",
                                      "Make Way, at Once!", "Make Way, All Hands!", "Make Way, Smartly!"])
        finally:
            names.title, names.every_title = draw, every
            names._named.cache_clear()

    def test_a_board_is_named_the_same_every_time(self):
        position = played(*CROWNED[:20])[-1]
        first = named(position)
        names._named.cache_clear()
        self.assertEqual(named(position), first)
        for move, emoji, title, said in first:
            self.assertEqual(name(position, move), (emoji, title, said))
        with self.assertRaises(ValueError):
            name(START, find(played("11-15")[-1], "22-18"))

    def test_the_titles_run_far_past_any_fixed_list(self):
        fixed = {p for _, patterns in THEMES.values() for p in patterns if "{" not in p}
        fixed |= {p for patterns in OWN_ORDERS.values() for p in patterns if "{" not in p}
        seen = {title for position in boards(40) for _, _, title, _ in named(position)}
        self.assertGreater(len(seen - fixed), len(fixed), "more orders made than every fixed one put together")


class Voice(unittest.TestCase):
    def test_the_design_s_orders_are_all_kept(self):
        kept = {p for _, patterns in THEMES.values() for p in patterns}
        self.assertEqual([order for order in DESIGN if order not in kept], [])
        for key, (emoji, order) in VOICE.items():
            with self.subTest(theme=key):
                self.assertEqual(THEMES[key][0], emoji)
                self.assertIn(order, THEMES[key][1])

    def test_the_opening_board_reads_as_the_design_drew_it(self):
        listed = named(START)
        self.assertEqual([(emoji, move.code) for move, emoji, _, _ in listed],
                         [("⚓", "9-13"), ("⛵", "9-14"), ("⛵", "10-14"), ("⛵", "10-15"), ("⛵", "11-15"),
                          ("⛵", "11-16"), ("⛵", "12-16")])
        self.assertEqual([said for _, _, _, said in listed][:2], ["Man from 9 to 13", "Man from 9 to 14"])

    def test_every_order_fits_the_page_and_fills_from_words_the_fleet_has(self):
        found = names.choices(read(START, find(START, "11-15")), "sail")
        for key, (emoji, patterns) in THEMES.items():
            self.assertTrue(KIT_EMOJI.fullmatch(emoji), key)
            for pattern in patterns + tuple(p for (k, _), ps in OWN_ORDERS.items() if k == key for p in ps):
                with self.subTest(order=pattern):
                    self.assertTrue(pattern.endswith("!"))
                    self.assertTrue(set(fields(pattern)) <= set(found), pattern)
                    if not fields(pattern):
                        self.assertTrue(KIT_TITLE.fullmatch(pattern) and len(pattern) <= names.LONGEST, pattern)
        words_ = [w for group in (*names.SHIPS.values(), *names.CALL.values(), *names.FOES.values(), names.STRIKE,
                                  names.FIERCE, names.SAIL, names.SEND, names.TURN, names.GO) for w in group]
        words_ += [place for group in names.PLACES.values() for word, place in group] + list(names.VOLLEY.values())
        for word in words_:
            self.assertRegex(word, r"^[A-Za-z][A-Za-z ,.'-]*$")


if __name__ == "__main__":
    unittest.main()
