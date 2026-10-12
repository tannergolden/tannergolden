# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named for what it is and for nothing it does: the emoji by the kind of move, the title and words
from the move's own pieces and squares, each title its own on its board, and no name that judges, warns, looks ahead
or names an opening, so two moves of one kind read alike whatever follows them.

  python3 -m unittest discover -s .github/scripts -p 'test_checkers*.py'
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checkers
import checkers_names as names
from checkers_names import name, named, words
from checkers_rules import START, Position, find, legal_moves, make, row_col

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py,
# whose checks every game's moves share).
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
CODE = re.compile(r"[0-9]{1,2}(?:-[0-9]{1,2}|(?:x[0-9]{1,2})+)")  # a move as checkers writes it, with no mark after
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]
SMALL = {"and", "on", "the", "to"}  # the short words a title keeps in lower case
# The emoji of each kind of move, and nothing else.
KINDS = {"step": "👣", "king": "⚜️", "jump": "⚔️", "jumps": "⛓️", "crown": "👑"}
# Emoji that judge or flag a move, the owner's and the last round's, none of which a name may carry.
FLAGS = frozenset(("⚠️", "🏆", "🔑", "🛡️", "⚡", "🎯", "💥", "💸", "📌", "🍴", "🎁", "💰", "🔄", "☠️", "🤝", "📖", "💣",
                   "🩸", "⚖️", "🔥", "🧹", "🕸️", "🚧", "🏃", "🏹", "💨", "☝️", "🕳️", "🌉", "🚪", "🏰", "🧱", "🛤️"))
# What no title, emoji, notation or words may say: a judgement; a consequence or a tactic; a plan with a verdict in
# it; an opening from the books, or the calls that named them; and the rest of what the last round read into a move.
JUDGED = (
    "good", "bad", "safe", "safely", "sound", "strong", "weak", "win", "wins", "winning", "won", "lose", "loses",
    "losing", "lost", "draw", "draws", "drawn", "save", "saves", "saving", "hold", "holds", "slip", "only", "best",
    "force", "forced", "blunder", "mistake",
    "check", "mate", "stalemate", "threat", "threaten", "threatens", "block", "blocks", "fork", "pin", "pinned",
    "skewer", "discovered", "trap", "traps", "shot", "sacrifice", "gambit", "exchange", "trade", "trades", "attack",
    "defence", "defense", "defend", "guard", "escape", "hang", "hangs", "material", "two-for-one", "in a row",
    "next", "leaves", "lets",
    "rim", "outpost", "open file", "half-open", "battery", "seventh rank", "passed pawn", "luft", "fianchetto",
    "seize", "command", "control", "dog hole", "bridge",
    "Edinburgh", "Denny", "Kelso", "Old Faithful", "Bristol", "Dundee", "Switcher", "Cross", "Ayrshire", "Lassie",
    "Paisley", "Dyke", "Wisp", "Defiance", "Waterloo", "Fourteenth", "Glasgow", "Laird", "Alma", "Fife", "Souter",
    "Whilter", "Maid", "Pioneer", "open", "opens", "opening", "answer", "enter",
    "corner", "free", "losses", "lesser", "throw", "give", "key", "drive", "smoke", "snare", "box in", "hem in",
    "race", "run for", "knock", "certain", "break", "menace", "aim at", "go after", "dodge", "get clear", "cover",
    "protect", "back up", "shore up", "refuge", "shelter", "centre", "edge", "diagonal", "press", "clear", "last",
    "shut", "spring", "shoot", "fire", "accept", "offer", "even", "ahead",
)
BANNED = re.compile(rf"\b(?:{'|'.join(JUDGED)})\b", re.IGNORECASE)
CROWDED = ("B:W32:BK1,K2,K3,K4,K9,K10,K11,K12,K17,K18,K19,K20",  # twelve kings with thirty-five moves between them
           "W:WK13,K14,K15,K16,K21,K22,K23,K24,K29,K30,K31,K32:B1",
           "B:W6,8,9,10,11,13,17,18,19,25,26,27:BK32")  # a king with a dozen ways to take nine


def boards(n: int, seed: int = 7):
    """Every position of `n` games of random legal moves, each with a move to make. Black opens every game of
    checkers, so the odd plies are White's turns."""
    rng = random.Random(seed)
    for _ in range(n):
        position = START
        for _ in range(rng.randint(10, 240)):
            moves = legal_moves(position)
            if not moves:
                break
            yield position
            position = make(position, rng.choice(moves))


BOARDS = list(boards(160))
NAMED = {position: named(position) for position in BOARDS}  # every board's names, once for every test here


def at(fen: str, code: str) -> tuple[Position, object]:
    position = Position.from_fen(fen)
    return position, find(position, code)


def mover(position: Position, move) -> str:
    return "King" if position.pieces[move.path[0]].isupper() else "Man"


def kind_of(position: Position, move) -> str:
    """The kind of move, worked out here from the rules' own facts, as the emoji must show it."""
    if move.crowns:
        return "crown"
    if move.captures:
        return "jumps" if len(move.captures) > 1 else "jump"
    return "king" if mover(position, move) == "King" else "step"


def fate(position: Position, move) -> str:
    """What follows the move at once, which no name may show: `wins` when it leaves the other side no move, `loses`
    when the other side then has a jump to take a piece with, and `quiet` otherwise."""
    replies = legal_moves(make(position, move))
    return "wins" if not replies else "loses" if replies[0].captures else "quiet"


def shape(position: Position, move) -> tuple:
    """What a move's form is made of: its kind, the piece that moves, how many it takes and what they are, and for a
    king's step, which way it goes."""
    way = row_col(move.path[-1])[0] > row_col(move.path[0])[0] if not move.captures else None
    return (kind_of(position, move), mover(position, move), tuple(position.pieces[square] for square in move.captures),
            way if mover(position, move) == "King" else None)


def form(text: str) -> str:
    """A title or words with every square struck out, which is all that may tell two moves of one kind apart."""
    return re.sub(r"[0-9]+", "#", text)


class Names(unittest.TestCase):
    def test_every_board_names_every_legal_move_once_in_what_the_kit_accepts(self):
        count = 0
        for position in [*BOARDS, *map(Position.from_fen, CROWDED)]:
            listed = NAMED.get(position) or named(position)
            self.assertEqual([move for move, _, _, _ in listed], legal_moves(position))
            titles = [title for _, _, title, _ in listed]
            self.assertEqual(len(set(titles)), len(titles), position.fen)
            for _, emoji, title, said in listed:
                count += 1
                self.assertTrue(KIT_EMOJI.fullmatch(emoji), emoji)
                self.assertTrue(KIT_TITLE.fullmatch(title) and len(title) <= names.LONGEST, title)
                self.assertTrue(KIT_WORDS.fullmatch(said) and len(said) <= names.WORDS_LONGEST, said)
                self.assertFalse(any(dash in title + said for dash in DASHES), title)
        self.assertGreater(count, 40_000)

    def test_no_name_judges_flags_reads_ahead_or_names_an_opening(self):
        """Every row the board lists, as the engine sets it out: the emoji, the title, the notation and the words."""
        for position in BOARDS:
            for row in checkers.listing(position, 1, 1):
                where = (position.fen, row["code"], row["title"])
                self.assertNotIn(row["emoji"], FLAGS, where)
                self.assertIsNone(BANNED.search(row["title"]), where)
                self.assertIsNone(BANNED.search(row["words"]), where)
                self.assertTrue(CODE.fullmatch(row["notation"]), where)  # no + or #, nor any mark of a verdict
                self.assertEqual(row["notation"], row["code"])

    def test_the_emoji_is_the_kind_of_move_one_to_a_kind(self):
        self.assertEqual(names.EMOJI, KINDS)
        for position, listed in NAMED.items():
            for move, emoji, title, _ in listed:
                self.assertEqual(emoji, KINDS[kind_of(position, move)], title)

    def test_every_title_is_a_call_in_title_case_and_never_names_a_colour(self):
        for listed in NAMED.values():
            for _, _, title, said in listed:
                self.assertTrue(title.endswith("!") and title[0].isupper(), title)
                self.assertNotRegex(title + said, r"\b(Dark|Light|dark|light)\b")
                for word in re.findall(r"[A-Za-z][A-Za-z'-]*", title):
                    self.assertTrue(word[0].isupper() or word in SMALL, title)

    def test_a_step_names_its_piece_and_both_its_squares(self):
        for position, listed in NAMED.items():
            verbs = defaultdict(set)
            for move, _, title, _ in listed:
                if move.captures:
                    continue
                start, end = move.path
                if move.crowns:
                    self.assertEqual(title, f"Crown the Man From {start} on {end}!")
                elif mover(position, move) == "King":
                    side = "White" if row_col(end)[0] > row_col(start)[0] else "Black"
                    self.assertRegex(title, rf"^(Send|Move) the King From {start} to {end} Toward {side}'s Side!$")
                    verbs["King"].add(title.split()[0])
                else:
                    self.assertRegex(title, rf"^(Advance|March|Push) the Man From {start} to {end}!$")
                    verbs["Man"].add(title.split()[0])
            self.assertTrue(all(len(seen) == 1 for seen in verbs.values()), (position.fen, verbs))

    def test_a_jump_names_what_it_takes_and_the_king_when_a_king_jumps(self):
        for position, listed in NAMED.items():
            for move, _, title, _ in listed:
                if not move.captures:
                    continue
                lead = {1: ("Jump the ",), 2: ("Double Jump ", "Jump Two "), 3: ("Triple Jump ", "Jump Three ")}
                self.assertTrue(title.startswith(lead.get(len(move.captures), ("Jump ",))), title)
                self.assertEqual("With the King" in title, mover(position, move) == "King", title)
                self.assertEqual(title.endswith(f", Crowned on {move.path[-1]}!"), move.crowns, title)
                what = title.split(" From ")[0].split(", Crowned")[0]  # what it takes, and nothing of where it goes
                taken = [int(square) for square in re.findall(r"[0-9]+", what)]
                if taken:  # the squares it takes, in the order it takes them
                    self.assertEqual(taken, list(move.captures), title)

    def test_every_number_in_a_title_is_a_square_of_the_move(self):
        for position, listed in NAMED.items():
            for move, _, title, _ in listed:
                for number in map(int, re.findall(r"[0-9]+", title)):
                    self.assertIn(number, {*move.path, *move.captures}, (position.fen, move.code, title))
                for what, square in re.findall(r"\b(Man|King) on ([0-9]+)", title):
                    self.assertIn(int(square), move.captures, (position.fen, move.code, title))
                    self.assertEqual(names.kind_word(position.pieces[int(square)]), what, (position.fen, title))

    def test_the_words_say_the_move_as_a_score_sheet_would(self):
        self.assertEqual(name(START, find(START, "11-15"))[2], "Man from 11 to 15")
        self.assertEqual(words(*at("W:W19,20:B1,16", "20x11")), "Man from 20 jumps 16, landing on 11")
        self.assertEqual(words(*at("W:W30:B1,19,26", "30x23x16")), "Man from 30 jumps 26 and 19, landing on 16")
        self.assertEqual(words(*at("W:W9,22:B1,6", "9x2")), "Man from 9 jumps 6, landing on 2, crowned")
        self.assertEqual(words(*at("B:WK9:B27", "27-31")), "Man from 27 to 31, crowned")
        self.assertEqual(words(*at("W:WK21:B9,25", "21x30")), "King from 21 jumps 25, landing on 30")
        self.assertEqual(words(*at("B:WK16:BK11", "11x20")), "King from 11 jumps 16, landing on 20")  # and wins
        self.assertEqual(words(*at("W:W26,27:B28,K32", "26-23")), "Man from 26 to 23")  # and wins too
        board = Position.from_fen(CROWDED[2])
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps 27, 18, 10, 11, 19, 26, 25, 17 and 9, landing on 5")
        board = Position.from_fen("B:W9,10,11,17,18,19,25,26,27:BK32")  # the same nine, all White has left
        self.assertEqual(words(board, find(board, "32x23x14x7x16x23x30x21x14x5")),
                         "King from 32 jumps 27, 18, 10, 11, 19, 26, 25, 17 and 9, landing on 5")
        for position, listed in NAMED.items():
            for move, _, _, said in listed:
                start, end = move.path[0], move.path[-1]
                taken = re.sub(r", ([0-9]+)$", r" and \1", ", ".join(map(str, move.captures)))
                plain = (f"{mover(position, move)} from {start} jumps {taken}, landing on {end}" if move.captures
                         else f"{mover(position, move)} from {start} to {end}")
                self.assertEqual(said, plain + (", crowned" if move.crowns else ""))

    def test_the_first_move_and_white_s_replies(self):
        self.assertEqual([title for _, _, title, _ in named(START)],
                         ["Push the Man From 9 to 13!", "Push the Man From 9 to 14!", "Push the Man From 10 to 14!",
                          "Push the Man From 10 to 15!", "Push the Man From 11 to 15!", "Push the Man From 11 to 16!",
                          "Push the Man From 12 to 16!"])
        self.assertEqual({emoji for _, emoji, _, _ in named(START)}, {"👣"})
        replies = named(make(START, find(START, "11-15")))
        self.assertEqual([(move.code, title) for move, _, title, _ in replies],
                         [("21-17", "Advance the Man From 21 to 17!"), ("22-17", "Advance the Man From 22 to 17!"),
                          ("22-18", "Advance the Man From 22 to 18!"), ("23-18", "Advance the Man From 23 to 18!"),
                          ("23-19", "Advance the Man From 23 to 19!"), ("24-19", "Advance the Man From 24 to 19!"),
                          ("24-20", "Advance the Man From 24 to 20!")])

    def test_kings_crownings_and_jumps_say_what_they_are(self):
        listed = {move.code: (emoji, title) for move, emoji, title, _ in named(Position.from_fen("W:W6,8,K26:BK11"))}
        self.assertEqual(listed["8-3"], ("👑", "Crown the Man From 8 on 3!"))
        self.assertEqual(listed["26-22"], ("⚜️", "Send the King From 26 to 22 Toward Black's Side!"))
        self.assertEqual(listed["26-30"], ("⚜️", "Send the King From 26 to 30 Toward White's Side!"))
        self.assertEqual(name(*at("W:W9,22:B1,6", "9x2"))[:2], ("👑", "Jump the Man on 6, Crowned on 2!"))
        self.assertEqual(name(*at("W:W30:B1,19,26", "30x23x16"))[:2], ("⛓️", "Double Jump the Men on 26 and 19!"))
        self.assertEqual(name(*at("B:WK16:BK11", "11x20"))[:2], ("⚔️", "Jump the King on 16 With the King!"))
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("W:WK6,14:B10,24,K28"))}
        self.assertEqual(listed, {"6x15": "Jump the Man on 10 With the King!", "14x7": "Jump the Man on 10!"})
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("B:W7,K8,16,24,29:BK27"))}
        self.assertEqual(listed, {"27x20x11x2": "Triple Jump 24, 16 and 7 With the King!",
                                  "27x20x11x4": "Triple Jump 24, 16 and 8 With the King!"})

    def test_jumps_that_take_the_same_piece_say_where_each_starts_and_their_kind_reads_alike(self):
        listed = {move.code: title for move, _, title, _ in named(Position.from_fen("W:W19,20,27:B1,16,23"))}
        self.assertEqual(listed, {"19x12": "Jump the Man on 16 From 19!", "20x11": "Jump the Man on 16 From 20!",
                                  "27x18": "Jump the Man on 23 From 27!"})  # one of their kind, so it says so too

    def test_a_crowded_board_still_gives_every_move_its_own_title(self):
        for fen in CROWDED:
            with self.subTest(fen=fen):
                listed = named(Position.from_fen(fen))
                self.assertGreater(len(listed), 8)
                self.assertEqual(len({title for _, _, title, _ in listed}), len(listed))
                self.assertFalse(any(re.fullmatch(r"Jump [0-9x]+!", title) for _, _, title, _ in listed))
        nines = {move.code: title for move, _, title, _ in named(Position.from_fen(CROWDED[2]))
                 if len(move.captures) == 9}
        self.assertEqual(len(nines), 6)
        self.assertEqual(nines["32x23x14x7x16x23x30x21x14x5"], "Jump 27, 18, 10, 11, 19, 26, 25, 17 and 9!")

    def test_a_board_is_named_the_same_every_time(self):
        for position in BOARDS[::50]:
            first = named(position)
            names._named.cache_clear()
            self.assertEqual(named(position), first)
            for move, emoji, title, said in first:
                self.assertEqual(name(position, move), (emoji, title, said))
        with self.assertRaises(ValueError):
            name(START, find(make(START, find(START, "11-15")), "22-18"))


class ReadAlike(unittest.TestCase):
    """The owner's test: two moves of one kind to like places read alike whether one wins on the spot, loses a man at
    once or does nothing, so nothing in the list tells a player which to choose."""

    def alike(self, fen: str, fates: dict[str, str]) -> None:
        """The moves' fates are as given, and their emoji, titles and words differ only in their squares."""
        position = Position.from_fen(fen)
        rows = {move.code: (emoji, form(title), form(said)) for move, emoji, title, said in named(position)}
        for code, want in fates.items():
            self.assertEqual(fate(position, find(position, code)), want, (fen, code))
        self.assertEqual(len({rows[code] for code in fates}), 1, [(code, rows[code]) for code in fates])

    def test_a_step_that_wins_one_that_loses_a_man_and_a_quiet_one_read_alike(self):
        self.alike("B:W20:B8,16,K30", {"8-11": "wins", "8-12": "loses", "16-19": "quiet"})  # 8-12 lets 20x11 come
        self.alike("W:W26,27:B28,K32", {"26-23": "wins", "26-22": "loses", "27-23": "quiet"})
        self.alike("B:W22:B9,15", {"15-18": "loses", "15-19": "quiet", "9-13": "quiet"})  # 22x15 takes the man

    def test_a_jump_that_wins_one_that_walks_into_a_jump_and_a_quiet_one_read_alike(self):
        self.alike("W:W21,23,24,29:B17,18", {"21x14": "loses", "23x14": "quiet"})
        self.alike("W:W16,17,26,27,28,29,30:B13,25", {"29x22": "wins", "30x21": "loses"})
        self.alike("B:W13,14:B6,9,10,16", {"10x17": "wins", "9x18": "quiet"})
        self.alike("B:WK5,14,15,K19,20,22,23:BK25", {"25x18x9": "loses", "25x18x11": "quiet"})
        self.alike("B:WK22,K24:BK17,K28", {"28x19": "loses", "17x26": "quiet"})

    def test_a_king_s_step_and_a_crowning_read_alike_too(self):
        self.alike("B:WK26:BK27", {"27-23": "loses", "27-24": "quiet"})
        self.alike("W:WK6,18,K32:B28", {"6-1": "wins", "32-27": "quiet"})
        self.alike("W:W6,8,K26:BK11", {"6-1": "loses", "8-3": "quiet"})

    def test_on_every_board_the_moves_of_one_kind_read_in_one_form_whatever_follows(self):
        mixed = 0
        for position, listed in NAMED.items():
            forms, fates = defaultdict(set), defaultdict(set)
            for move, emoji, title, said in listed:
                forms[shape(position, move)].add((emoji, form(title), form(said)))
                fates[shape(position, move)].add(fate(position, move))
            for key, seen in forms.items():
                self.assertEqual(len(seen), 1, (position.fen, key, seen))
                mixed += len(fates[key]) > 1
        self.assertGreater(mixed, 3_000, "moves of one kind with different fates side by side, many times over")


if __name__ == "__main__":
    unittest.main()
