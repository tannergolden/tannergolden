# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named: the openings by their verified moves, what a move is read as, the title and words it is
given and that each is true of it, and that a board keeps them, the same every time and each its own.

  python3 -m unittest discover -s .github/scripts -p 'test_checkers*.py'
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checkers_names as names
from checkers_names import BOOK, OPENINGS, THEMES, name, named, read, theme, words
from checkers_rules import START, Position, find, legal_moves, make

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py,
# whose checks every game's moves share).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "via", "o'"}  # lower in a title
# A board for every reading, with a move that has it and that move's title, each checked against the board by hand.
EXAMPLES = {
    "win": ("B:WK16:BK11", "11x20", "Take Their Last King!"),
    "opening": (START.fen, "10-15", "Open the Kelso!"),
    "blunder": ("W:WK12:BK19", "12-16", "Give Away the King on 16!"),  # the king on 19 jumps it
    "sacrifice": ("B:W21,25,30,31,32:B2,3,4,5,11,12,20,23,28", "23-27", "Give a Man to Break Through!"),
    "losing": ("B:WK14:BK13", "13-9", "Give Up the King on 9!"),  # 13-17 loses it too
    "shot": ("B:W18,K20:B24,K28", "28-32", "Spring the Two-for-One!"),  # 20x27 must be taken, and 32x23x14 follows
    "key": ("W:WK12:BK19", "12-8", "Make the Only Move That Holds!"),
    "crown": ("B:WK9:B27", "27-31", "Make a King on 31!"),
    "exchange": ("B:WK19:BK26,K31", "26-23", "Trade Down While Ahead!"),  # 19x26, then 31x22
    "jump": ("W:WK23:BK19,K28", "23x16", "Take the Forced Jump Over 19!"),
    "double": ("W:W30:B1,19,26", "30x23x16", "Take the Forced Double Jump!"),
    "multi": ("B:W7,K8,16,24,29:BK27", "27x20x11x2", "Take Three for Free!"),
    "drive": ("B:WK1:BK9,K18", "9-5", "Smoke the King Out of the Double Corner!"),  # the king on 1 can't step to 5
    "trap": ("B:WK12:BK15", "15-11", "Trap the King on 12!"),  # 12-8 and 12-16 are both jumped
    "block": ("B:WK14,21:B13,19,K23", "13-17", "Hem In the Man on 21!"),
    "runaway": ("B:WK13:B23", "23-26", "Make the Crown Certain at 26!"),
    "threat": ("W:WK7:BK6", "7-2", "Menace the King on 6!"),
    "escape": ("B:WK13:BK17,K30", "17-21", "Dodge the Jump at 21!"),
    "guard": ("B:WK14:B18,K26", "26-23", "Shore Up the Man on 18!"),  # 14x23 would land on 23
    "only": ("B:WK20:BK29", "29-25", "Make the Only Move There Is!"),
    "hole": ("W:W9,10,25,29:B1,28", "9-5", "Step Into the Dog Hole!"),  # Black's man on 1 holds it there
    "bridge": ("W:WK9,23,27,30,32:B12,22", "32-28", "Break the Bridge!"),
    "back": ("W:W14,25:BK12", "25-21", "Clear the Single Corner to 21!"),
    "refuge": ("B:WK16:BK28", "28-32", "Shuttle in the Double Corner!"),
    "king": ("B:WK16:BK28", "28-24", "Fall Back With the King!"),
    "centre": ("B:WK10:B16", "16-19", "Seize the Centre!"),
    "edge": ("B:WK10:B16", "16-20", "Hug the Edge!"),
    "diagonal": ("W:W15,20:B22", "15-11", "Advance Along the Long Diagonal!"),
    "side": ("B:W14:B20,K28", "20-24", "Push Up the Single-Corner Side!"),
}
# Every named opening's last move and its call: Black's first move opens it, White's reply answers with it, and a
# later move enters the line it names.
CALLS = {
    "9-13": "Open the Edinburgh!", "9-14": "Open the Double Corner!", "10-14": "Open the Denny!",
    "10-15": "Open the Kelso!", "11-15": "Open With Old Faithful!", "11-16": "Open the Bristol!",
    "12-16": "Open the Dundee!",
    "11-15 21-17": "Answer With the Switcher!", "11-15 22-18": "Answer With the Single Corner!",
    "11-15 23-18": "Answer With the Cross!", "11-15 24-19": "Answer With the Second Double Corner!",
    "11-15 24-20": "Answer With the Ayrshire Lassie!", "10-15 23-18": "Answer With the Kelso Cross!",
    "11-16 23-18": "Answer With the Bristol Cross!", "11-16 24-19": "Answer With the Paisley!",
    "11-15 22-17 15-19": "Enter the Dyke!", "11-15 23-19 9-13": "Enter the Will o' the Wisp!",
    "11-16 24-20 16-19": "Complete the Bristol!",
    "11-15 23-19 9-14 27-23": "Answer With the Defiance!", "11-15 23-18 8-11 18-14": "Answer With the Waterloo!",
    "11-15 23-19 8-11 22-17 4-8": "Enter the Old Fourteenth!", "11-15 23-19 8-11 22-17 11-16": "Enter the Glasgow!",
    "11-15 23-19 8-11 22-17 9-13": "Enter the Laird and Lady!", "11-15 23-19 8-11 22-17 3-8": "Enter the Alma!",
    "11-15 23-19 9-14 22-17 5-9": "Enter the Fife!", "11-15 23-19 9-14 22-17 6-9": "Enter the Souter!",
    "11-15 23-19 9-14 22-17 7-11": "Enter the Whilter!",
    "11-15 22-17 8-11 17-13 15-18": "Enter the Maid of the Mill!",
}
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


def at(fen: str, code: str) -> tuple[Position, object]:
    position = Position.from_fen(fen)
    return position, find(position, code)


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


BOARDS = list(boards(40))
NAMED = {position: named(position) for position in BOARDS}  # every board's names, once for every test here


class Openings(unittest.TestCase):
    def test_every_named_opening_is_named_on_the_move_that_completes_it(self):
        self.assertEqual({moves for _, moves in OPENINGS}, set(CALLS))
        for line, call in CALLS.items():
            with self.subTest(opening=line):
                codes = line.split()
                position = played(*codes[:-1])[-1]
                self.assertEqual(name(position, find(position, codes[-1]))[:2], ("📖", call))

    def test_each_opening_is_its_verified_moves_and_no_other(self):
        """The moves are the sources': the names in the docstring are tied to them, and the book holds nothing else."""
        doc = re.sub(r"\s+", " ", names.__doc__)
        for opening, moves in OPENINGS:
            with self.subTest(opening=opening):
                self.assertIn(opening.removeprefix("the "), doc)
                self.assertIn(moves.split()[-1], doc)
        self.assertEqual(len(BOOK), len(OPENINGS))
        self.assertNotIn("Pioneer", " ".join(opening for opening, _ in OPENINGS))

    def test_the_first_move_and_white_s_replies_read_as_the_book_has_them(self):
        self.assertEqual([title for _, _, title, _ in named(START)],
                         ["Open the Edinburgh!", "Open the Double Corner!", "Open the Denny!", "Open the Kelso!",
                          "Open With Old Faithful!", "Open the Bristol!", "Open the Dundee!"])
        replies = {move.code: (emoji, title) for move, emoji, title, _ in named(played("11-15")[-1])}
        self.assertEqual({code for code, (emoji, _) in replies.items() if emoji == "📖"},
                         {"21-17", "22-18", "23-18", "24-19", "24-20"})
        self.assertNotEqual(replies["23-19"][0], "📖", "the most played reply has no name of its own")
        fifth = {move.code: title for move, _, title, _ in named(played("11-15", "23-19", "8-11", "22-17")[-1])}
        self.assertEqual({fifth[code] for code in ("4-8", "11-16", "9-13", "3-8")},
                         {"Enter the Old Fourteenth!", "Enter the Glasgow!", "Enter the Laird and Lady!",
                          "Enter the Alma!"})

    def test_a_position_reached_another_way_is_the_same_opening(self):
        position = played("11-15", "22-17", "8-11", "23-19")[-1]  # the Old Fourteenth's position, by another order
        self.assertEqual(name(position, find(position, "4-8"))[1], "Enter the Old Fourteenth!")

    def test_no_move_off_the_book_is_named_for_an_opening(self):
        for position, listed in NAMED.items():
            for move, emoji, title, _ in listed:
                self.assertEqual(emoji == "📖", (position, move.code) in BOOK, title)


class Readings(unittest.TestCase):
    def test_a_move_is_named_for_the_most_telling_thing_it_does(self):
        self.assertEqual(set(EXAMPLES), set(THEMES), "an example for every reading")
        for want, (fen, code, title) in EXAMPLES.items():
            with self.subTest(theme=want):
                position, move = at(fen, code)
                self.assertEqual(theme(read(position, move)), want)
                self.assertEqual(name(position, move)[:2], (THEMES[want], title))

    def test_its_words_say_what_it_does(self):
        self.assertEqual(name(START, find(START, "11-15"))[2], "Man from 11 to 15")
        board = played(*OPENING)[-1]
        self.assertEqual(name(board, find(board, "20x11"))[2], "Man from 20 jumps 16, landing on 11")
        board = played(*CROWNED[:-1])[-1]
        self.assertEqual(name(board, find(board, "19x10x1"))[2], "Man from 19 jumps 15 and 6, landing on 1, crowned")
        self.assertEqual(words(*at("B:WK16:BK11", "11x20")), "King from 11 jumps 16, landing on 20, winning the game")
        self.assertEqual(words(*at("W:W26,27:B28,K32", "26-23")), "Man from 26 to 23, winning the game")
        self.assertEqual(words(*at("B:WK9:B27", "27-31")), "Man from 27 to 31, crowned")
        self.assertEqual(words(*at("W:WK21:B9,25", "21x30")), "King from 21 jumps 25, landing on 30")

    def test_a_long_run_of_jumps_says_how_many_when_which_would_not_fit(self):
        board = Position.from_fen("B:W6,8,9,10,11,13,17,18,19,25,26,27:BK32")
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps 27, 18, 10, 11, 19, 26, 25, 17 and 9, landing on 5")
        board = Position.from_fen("B:W9,10,11,17,18,19,25,26,27:BK32")  # the same nine, and nothing else left
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps nine pieces, landing on 5, winning the game")

    def test_jumps_say_what_they_take_and_how(self):
        self.assertEqual(name(*at("W:W30:B1,19,26", "30x23x16"))[:2], ("💥", "Take the Forced Double Jump!"))
        self.assertEqual(name(*at("B:W7,K8,16,24,29:BK27", "27x20x11x2"))[0], "🔥")
        position, move = at("W:WK6,14:B10,24,K28", "6x15")  # nothing of theirs can jump back
        self.assertEqual(read(position, move).lost, ())
        self.assertEqual(name(position, move)[:2], ("⚔️", "Take the Man on 10 for Free!"))
        for position, listed in NAMED.items():
            for move, emoji, title, _ in listed:
                reading = read(position, move)
                if "Forced" in title:
                    self.assertEqual(legal_moves(position), [move], title)
                if "for Free" in title:
                    self.assertEqual(reading.lost, (), title)
                if move.captures and emoji in ("⚔️", "💥", "🔥"):
                    self.assertEqual(emoji, {1: "⚔️", 2: "💥"}.get(len(move.captures), "🔥"), title)

    def test_a_man_reaching_the_far_row_is_crowned_by_name(self):
        self.assertEqual(name(*at("W:W9,22:B1,6", "9x2"))[:2], ("👑", "Take a Man and Be Crowned!"))
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("B:WK9:B27"))}
        self.assertEqual(listed, {"27-31": "Make a King on 31!", "27-32": "Make a King on 32!"})
        for listed in NAMED.values():
            for move, emoji, title, said in listed:
                if emoji == "👑":
                    self.assertTrue(move.crowns, title)
                    self.assertIn("crowned", said)

    def test_the_bridge_is_the_men_on_1_and_3_and_on_30_and_32(self):
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(Position.from_fen("B:W22,23:B1,3,9"))}
        self.assertEqual({code for code, (emoji, _) in listed.items() if emoji == "🌉"}, {"1-5", "1-6", "3-7", "3-8"})
        self.assertNotEqual(name(*at("B:W22,23:B1,9", "1-5"))[0], "🌉", "no bridge stands on 1 alone")
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("W:W23,27,30,32:B4,12"))}
        self.assertEqual((listed["30-26"], listed["32-28"]), ("Break the Bridge to 26!", "Break the Bridge From 32!"))
        self.assertEqual(name(*at("W:WK9,23,27,30,32:B12,22", "30-26"))[:2], ("⚠️", "Give Away the Man on 26!"))
        self.assertEqual(name(*at("B:W17,18,22,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,7,8,9,10,11,12,13", "2-6"))[1],
                         "Keep the Bridge, Bring Out a Man!")

    def test_an_exchange_gives_one_and_takes_one(self):
        position, move = at(played("10-15")[-1].fen, "24-19")  # 15x24, then 28x19
        self.assertEqual(name(position, move)[0], "⚖️")
        self.assertEqual((len(read(position, move).lost), len(read(position, move).gained)), (1, 1))
        self.assertEqual(name(*at("B:W22,26:B6,10,15", "15-18"))[:2], ("⚖️", "Trade Down While Ahead!"))

    def test_a_trade_they_threatened_is_accepted_and_one_we_start_is_forced(self):
        position = played("11-16", "24-20")[-1]  # 20x11 is waiting, and 7x16 takes back
        for code in ("9-13", "9-14", "10-14", "10-15"):
            emoji, title, _ = name(position, find(position, code))
            self.assertEqual(emoji, "⚖️")
            self.assertTrue(title.startswith(("Accept the Trade", "Let Them Trade")), title)
        for position, listed in NAMED.items():
            for move, _, title, _ in listed:
                reading = read(position, move)
                if title.startswith(("Force a Trade", "Offer an Even Trade", "Give One, Take One")):
                    self.assertFalse(reading.pending, title)
                if title.startswith(("Accept the Trade", "Let Them Trade")):
                    self.assertTrue(reading.pending, title)
                if "Their Shot" in title or "Their Double Jump" in title or "Their Triple Jump" in title:
                    self.assertGreaterEqual(reading.their_most, 2, title)

    def test_a_shot_gives_one_so_the_forced_reply_opens_a_bigger_jump(self):
        position, move = at("B:W17,18,22,24,25,26,27,28,29,30,31,32:B1,2,3,4,5,7,8,9,10,11,12,13", "9-14")
        self.assertEqual(name(position, move)[:2], ("💣", "Spring the Two-for-One!"))  # 18x9, then 5x14x21
        position, move = at("B:W17,19,22,25,27,29,30,32:B1,3,4,5,6,8,9,10", "10-14")  # 17x10, then 6x15x24x31
        self.assertEqual(name(position, move)[:2], ("💣", "Shoot Through to the King Row!"))
        self.assertEqual((len(read(position, move).lost), len(read(position, move).gained)), (1, 3))

    def test_a_man_left_to_be_jumped_for_nothing_is_the_blunder(self):
        position = Position.from_fen("B:W22:B9,15")
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(position)}
        self.assertEqual(listed["15-18"], ("⚠️", "Throw Away a Man!"))  # 22x15, and nothing takes back
        self.assertEqual(listed["9-13"][0], "🕸️", "the man on 22 then has no safe step")
        position = Position.from_fen("W:WK1,10,23:BK26")
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(position)}
        self.assertEqual(listed["10-6"], ("⚠️", "Leave the Man on 23 to Be Jumped With 10-6!"))
        self.assertEqual({listed["23-18"][0], listed["23-19"][0]}, {"💨"})

    def test_the_blunder_is_called_so_and_no_losing_move_is_praised(self):
        for position, listed in NAMED.items():
            values = {move: read(position, move).value for move, *_ in listed}
            for move, emoji, title, _ in listed:
                reading = read(position, move)
                key = theme(reading)
                with self.subTest(fen=position.fen, move=move.code):
                    if emoji == "⚠️":
                        self.assertTrue(reading.value < 0 and reading.value < max(values.values()), title)
                    elif reading.value < max(values.values()) and reading.value < 0:
                        self.assertIn(key, ("sacrifice", "opening"), title)
                    if key in ("shot", "exchange", "key", "crown", "jump", "double", "multi") and not reading.only:
                        self.assertGreaterEqual(reading.value, 0, title)  # only a forced move may lose and not say so

    def test_the_endgame_drives_a_lone_king_from_the_double_corner_and_traps_it(self):
        position = Position.from_fen("W:WK9,K19:BK1")  # the king on 1 shuttles to 5 until 5 is taken from it
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(position)}
        self.assertEqual(listed["9-5"][0], "🧹")
        self.assertIn("Double Corner", listed["9-5"][1])
        self.assertEqual(listed["9-6"][0], "⚠️", "1x10 takes the king that steps beside it")
        self.assertEqual(name(*at("W:WK15,K16:BK4", "15-11"))[:2], ("🕸️", "Snare the King on 4 From 15!"))

    def test_the_dog_hole_is_5_or_12_for_white_and_28_or_21_for_black(self):
        self.assertEqual(name(*at("W:W9,22:B1,7", "9-5"))[:2], ("🕳️", "Sink Into the Dog Hole!"))
        self.assertNotEqual(name(*at("W:W9,22:B2,7", "9-5"))[0], "🕳️", "with nobody on 1 it is no dog hole")
        self.assertEqual(theme(read(*at("W:W15,16,20,21,30:B3,7,8,13,23,28,K29", "16-12"))), "hole")  # 3 holds 12
        listed = {move.code: emoji for move, emoji, _, _ in named(Position.from_fen("B:W30,32:B17,24"))}
        self.assertEqual((listed["17-21"], listed["24-28"]), ("🕳️", "🕳️"))  # held by 30 and by 32

    def test_threats_escapes_and_guards_name_the_piece_they_are_about(self):
        self.assertEqual(name(*at("W:W25,26:B1,18", "26-22"))[1], "Menace the Man on 18!")
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(Position.from_fen("B:W22,25:B11,18"))}
        self.assertEqual(listed["11-15"], ("🛡️", "Guard the Man on 18!"))
        self.assertEqual(listed["18-23"], ("💨", "Get Clear of the Jump!"))
        self.assertEqual(listed["11-16"][0], "⚠️")
        self.assertEqual(name(*at("W:W12,15,18,25:B3,4,7,9,21,27,K32", "25-22"))[:2],
                         ("🔑", "Save the Man on 25, the Only Way!"))

    def test_every_number_in_a_title_is_a_square_the_move_concerns(self):
        for position, listed in NAMED.items():
            for move, _, title, _ in listed:
                reading = read(position, move)
                concerns = {*move.path, *move.captures, *reading.threats, reading.trapped, reading.blocked,
                            reading.guarded, reading.lost_at}
                for number in map(int, re.findall(r"[0-9]+", title)):
                    self.assertIn(number, concerns, (position.fen, move.code, title))

    def test_a_square_named_in_a_title_holds_what_the_title_says(self):
        for position, listed in NAMED.items():
            for move, _, title, _ in listed:
                for what, square in re.findall(r"\b(Man|King) on ([0-9]+)", title):
                    piece = position.pieces.get(int(square)) or make(position, move).pieces.get(int(square))
                    self.assertIsNotNone(piece, (position.fen, move.code, title))
                    self.assertEqual(names.kind_word(piece), what, (position.fen, move.code, title))


class Titles(unittest.TestCase):
    def test_every_board_names_every_move_once_in_what_the_kit_accepts(self):
        count = 0
        for position in [*BOARDS, *map(Position.from_fen, CROWDED)]:
            listed = NAMED.get(position) or named(position)
            self.assertEqual([move for move, _, _, _ in listed], legal_moves(position))
            titles = [title for _, _, title, _ in listed]
            self.assertEqual(len(set(titles)), len(titles), position.fen)
            for move, emoji, title, said in listed:
                count += 1
                self.assertTrue(KIT_EMOJI.fullmatch(emoji), emoji)
                self.assertTrue(KIT_TITLE.fullmatch(title) and len(title) <= names.LONGEST, title)
                self.assertTrue(KIT_WORDS.fullmatch(said) and len(said) <= names.WORDS_LONGEST, said)
                self.assertEqual(emoji, THEMES[theme(read(position, move))], title)
                self.assertFalse(any(dash in title + said for dash in DASHES))
        self.assertGreater(count, 10_000)

    def test_every_title_is_a_call_in_title_case_and_never_names_a_colour(self):
        for listed in NAMED.values():
            for _, _, title, said in listed:
                self.assertTrue(title.endswith("!"), title)
                self.assertNotRegex(title + said, r"\b(Dark|Light|dark|light)\b")
                for word in re.findall(r"[A-Za-z][A-Za-z'-]*", title):
                    self.assertTrue(word[0].isupper() or word in SMALL or re.fullmatch(r"[0-9x-]+", word), title)

    def test_a_crowded_board_still_gives_every_move_its_own_title(self):
        for fen in CROWDED:
            with self.subTest(fen=fen):
                listed = named(Position.from_fen(fen))
                self.assertGreater(len(listed), 6)
                self.assertEqual(len({title for _, _, title, _ in listed}), len(listed))

    def test_jumps_that_share_both_ends_are_told_apart_by_where_they_go(self):
        listed = named(Position.from_fen(CROWDED[2]))
        nines = [title for move, _, title, _ in listed if len(move.captures) == 9]
        self.assertEqual(len(nines), len(set(nines)))
        self.assertTrue(all(title.startswith("Take Nine") for title in nines), nines)
        self.assertIn("Take Nine in One Move, Fourth Jump to 16!", nines)

    def test_a_board_is_named_the_same_every_time(self):
        position = played(*CROWNED[:20])[-1]
        first = named(position)
        names._named.cache_clear()
        names.survey.cache_clear()
        names.line.cache_clear()
        self.assertEqual(named(position), first)
        for move, emoji, title, said in first:
            self.assertEqual(name(position, move), (emoji, title, said))
        with self.assertRaises(ValueError):
            name(START, find(played("11-15")[-1], "22-18"))
        with self.assertRaises(ValueError):
            read(START, find(played("11-15")[-1], "22-18"))

    def test_the_same_reading_reads_alike_and_differs_by_a_true_detail(self):
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("B:W32:BK1,K2,K3,K4,K9,K10,K11,"
                                                                                    "K12,K17,K18,K19,K20"))}
        self.assertEqual(listed["1-5"], "Hold the Double Corner!")
        self.assertEqual(listed["2-6"], "Send the King Forward From 2 to 6!")
        self.assertEqual(listed["9-13"], "Send the King Forward to 13!")


if __name__ == "__main__":
    unittest.main()
