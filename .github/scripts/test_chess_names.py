# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every legal move named as players name it and never for what it does to the game: every name, emoji, notation and
words read from a fixed grammar of the move's own facts and checked against the board, no square in any name, a move
that mates or gives the queen away read just as a quiet one, and every name within what the kit takes.

  python3 -m unittest discover -s .github/scripts -p 'test_chess*.py'
"""
from __future__ import annotations

import functools
import random
import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chess_names
from chess_names import LONGEST, WORDS_LONGEST, listing, words
from chess_rules import START, Move, Position, in_check, label, legal_moves, make, san

# What tannergolden/markdown accepts for a move: an emoji, a title and its words (src/domain/elements/chess/game.py),
# and its SAN, here without the marks for check and mate.
KIT_EMOJI = re.compile("[←-⯿\U0001f000-\U0001faff‍️]{1,8}")
KIT_TITLE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9 ,.'!-]{0,46}[A-Za-z0-9,.'!-])?")  # no space at either end
KIT_WORDS = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'-]{0,79}")
PLAIN_SAN = re.compile(r"O-O(?:-O)?|[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|[a-h](?:x[a-h])?[1-8](?:=[QRBN])?")
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]

# What no title, emoji, notation or words may say: a judgement, a consequence or a tactic, a plan with a verdict, or
# an opening the books name.
JUDGED = re.compile(
    r"\b(?:good|bad|safe\w*|sound|strong|weak\w*|win\w*|won|los[et]\w*|draw\w*|save|saves|saved|saving|hold\w*|slip\w*|"
    r"only|best|forc\w*|blunder\w*|mistake\w*|check\w*|mate[sd]?|mating|stalemat\w*|threat\w*|block\w*|fork\w*|"
    r"pin|pins|pinned|skewer\w*|discover\w*|double[ -](?:attack|check)\w*|doubled|trap\w*|shot|sacrific\w*|gambit\w*|"
    r"exchang\w*|"
    r"trad(?:e|es|ed|ing)|swap\w*|attack\w*|defen[cd]\w*|guard\w*|escap\w*|hang\w*|material|next|leaves|lets|rim|"
    r"outpost\w*|open\w*|battery|seventh|passed|luft|fianchetto\w*|seiz\w*|command\w*|control\w*|dog|bridge|"
    r"centre|center|centralis\w*|develop\w*|tempo|danger\w*|protect\w*|support\w*|tactic\w*|greek|gift|book|"
    r"theory|tuck\w*|hide|hidden|legal)\b",
    re.IGNORECASE)
OPENINGS = re.compile(
    r"\b(?:English|Sicilian|French|Caro|Kann|Scandinavian|Alekhine|Pirc|Modern|Dutch|Benoni|Englund|Vienna|Petrov|"
    r"Philidor|Ruy|Lopez|Spanish|Italian|Scotch|Ponziani|Slav|Grunfeld|Indian|Catalan|London|Trompowsky|Najdorf|"
    r"Dragon|Scheveningen|Sveshnikov|Berlin|Giuoco|Evans|Fried|Bird|Polish|Grob|Nimzo|Larsen|Budapest|Benko|Alapin|"
    r"Morra|Rossolimo|Falkbeer|Albin|Chigorin|Staunton|Blackmar|Diemer|Opening|Defence|Defense|System|Variation|"
    r"Attack|Game)\b")
# The emoji that judge or flag a move, all of which the last naming round used, and none of which may come back.
FLAGS = ("⚠", "🏆", "🔑", "🛡", "⚡", "🎯", "💥", "💸", "📌", "🍴", "🎁", "💰", "🔄", "☠", "🤝", "📖", "❗", "☝", "💣",
         "🩸", "🕸", "🏹", "💨", "🎲", "🍢", "🔥", "🚩", "🌩", "🎭", "👻", "⚖", "🔭", "🔓", "🌑", "🌅", "🏃", "🏛",
         "🌬", "🎖", "🗡", "🌠", "🤺", "🔋", "🛣", "🔗", "🏗", "🚶", "↩", "🔀", "❓", "❕", "‼", "⁉")
# The emoji of each kind of move, the same for every move of that kind.
KEY = {"castle": "🏰", "promotion": "👑", "capture": "⚔️", "k": "🤴", "q": "👸", "r": "🗼", "b": "⛪", "n": "🐴",
       "p": "♟️"}
NAMES = {"k": "King", "q": "Queen", "r": "Rook", "b": "Bishop", "n": "Knight", "p": "Pawn"}
LONGEST_NAME = 24  # a name is short: Underpromotion to Bishop is the longest

# Every name is one of these forms, and nothing else: the move's kind as players call it, and no square.
SQ = "[a-h][1-8]"
PIECE = "Queen|Rook|Bishop|Knight"
FORMS = {
    "castle": re.compile(r"(?P<wing>Kingside|Queenside) Castling"),
    "promotion": re.compile(r"Promotion to (?P<new>Queen)"),
    "underpromotion": re.compile(r"Underpromotion to (?P<new>Rook|Bishop|Knight)"),
    "passant": re.compile(r"En Passant"),
    "take": re.compile(rf"(?P<piece>King|{PIECE}|Pawn) Takes (?P<victim>{PIECE}|Pawn)"),
    "push": re.compile(r"Pawn Push"),
    "double-push": re.compile(r"Double Pawn Push"),
    "retreat": re.compile(rf"(?P<piece>{PIECE}) Retreat"),
    "move": re.compile(rf"(?P<piece>King|{PIECE}) Move"),
}
# And the words are one of these.
SAYS = {
    "castle": re.compile(rf"King from (?P<start>{SQ}) to (?P<to>{SQ}), castling (?P<wing>kingside|queenside)"),
    "move": re.compile(rf"(?P<piece>King|Queen|Rook|Bishop|Knight|Pawn) from (?P<start>{SQ}) to (?P<to>{SQ})"
                       r"(?P<two>, two squares)?(?:, becoming a (?P<new>queen|rook|bishop|knight))?"),
    "take": re.compile(rf"(?P<piece>King|Queen|Rook|Bishop|Knight|Pawn) from (?P<start>{SQ}) takes the"
                       rf" (?P<victim>queen|rook|bishop|knight|pawn) on (?P<at>{SQ})(?P<passing>, en passant)?"
                       r"(?:, becoming a (?P<new>queen|rook|bishop|knight))?"),
}

# Boards where a move does something a name must not tell: mates of every kind, a stalemate, the only legal move, a
# move into Fool's Mate, a queen that can be given away, the only move that stops a mate, the books' replies to 1. e4,
# a capture that leaves the kings alone, a double check, forks, a skewer, a pin, the Lucena and the opposition.
TELLING = (
    "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2",
    "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
    "6rk/6pp/8/6N1/8/8/8/K7 w - - 0 1",
    "6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1",
    "7k/5Q2/8/8/8/8/8/K7 w - - 0 1",
    "4k3/8/8/8/8/5q2/8/4K3 w - - 0 1",
    "rnbqkbnr/pppp1ppp/8/4p3/8/5P2/PPPPP1PP/RNBQKBNR w KQkq - 0 2",
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "r1q3r1/2p5/n1b1kBp1/p5p1/2P5/QP2p2N/P3P1BP/3RKR2 b - - 3 27",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "4k3/8/8/8/8/8/3q4/4K3 w - - 0 1",
    "8/4P3/8/8/8/8/k7/4K3 w - - 0 1",
    "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
    "rnbqk1nr/pppp1ppp/8/4p3/1b1PP3/8/PPP2PPP/RNBQKBNR w KQkq - 1 3",
    "4k3/8/8/8/4N3/8/8/K3R3 w - - 0 1",
    "q3k3/8/8/1N6/8/8/8/4K3 w - - 0 1",
    "6q1/8/8/3k4/8/8/8/K2B4 w - - 0 1",
    "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    "4k3/8/2n5/8/8/8/8/4KB2 w - - 0 1",
    "r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1",
    "rnbq1rk1/pppn1ppp/4p3/3pP3/1b1P4/2NB1N2/PPP2PPP/R2QK2R w KQ - 0 1",
    "1K6/1P1k4/8/8/8/8/r7/2R5 w - - 0 1",
    "8/8/4k3/8/8/4K3/4P3/8 w - - 0 1",
)
GAMES, PLIES = 24, 200  # the random games swept, and the longest each runs


@functools.cache
def sweep() -> tuple[tuple[Position, tuple[dict, ...]], ...]:
    """The telling boards, and every board of seeded random games from the start to the end or the 200th move, each
    with its listing. The play leans toward captures and promotions, so that the boards thin out and pawns reach the
    last rank."""
    rng = random.Random(2026)
    out = [(position, tuple(listing(position))) for position in map(Position.from_fen, TELLING)]
    for game in range(1, GAMES + 1):
        position = Position.from_fen(START)
        for ply in range(1, PLIES + 1):
            listed = tuple(listing(position, game, ply))
            if not listed:
                break
            out.append((position, listed))
            moves = [Move.from_uci(m["uci"]) for m in listed]
            takes = [m for m in moves if m.promotion or position.board[m.end]]
            position = make(position, rng.choice(takes if takes and rng.random() < 0.5 else moves))
    return tuple(out)


@dataclass(frozen=True, slots=True)
class Facts:
    """What a title may say about a move, worked out here from the board without the module's help."""
    kind: str  # the piece that moves: k, q, r, b, n or p
    start: str
    to: str
    file: str  # the file it leaves
    wing: str  # Kingside or Queenside, for castling
    victim: str  # what it takes: Queen, Rook, Bishop, Knight or Pawn
    at: str  # where that stands
    passing: bool  # it takes en passant
    new: str  # what a promotion makes
    rise: int  # ranks gained toward the other side, less than nothing going back
    two: bool  # a pawn's two squares


@functools.cache
def rows() -> tuple[tuple[Position, Move, dict, Facts], ...]:
    """Every listed move of the sweep: its board, the move itself, its row, and its facts."""
    return tuple((position, move, row, facts(position, move))
                 for position, listed in sweep() for row in listed for move in (Move.from_uci(row["uci"]),))


def facts(position: Position, move: Move) -> Facts:
    board, white = position.board, position.turn == "w"
    kind = board[move.start].lower()
    forward = 1 if white else -1
    castle = kind == "k" and abs(move.end - move.start) == 2
    passing = kind == "p" and move.start % 8 != move.end % 8 and not board[move.end]
    at = move.end - 8 * forward if passing else move.end if board[move.end] else None
    return Facts(kind=kind, start=label(move.start), to=label(move.end), file=label(move.start)[0],
                 wing=("Kingside" if move.end > move.start else "Queenside") if castle else "",
                 victim=NAMES[board[at].lower()] if at is not None else "",
                 at=label(at) if at is not None else "", passing=passing,
                 new=NAMES[move.promotion] if move.promotion else "", rise=(move.end // 8 - move.start // 8) * forward,
                 two=kind == "p" and abs(move.end - move.start) == 16)


def read(title: str) -> tuple[str, dict]:
    """The title's form and what it says, or a failure when it is in no form."""
    found = [(form, match.groupdict()) for form, pattern in FORMS.items() if (match := pattern.fullmatch(title))]
    if len(found) != 1:
        raise AssertionError(f"{title!r} is in {len(found)} forms")
    return found[0]


def shape(text: str) -> str:
    """The text with its squares left out: its form."""
    return re.sub("[a-h][1-8]", "##", text)


def entry(fen: str, uci: str) -> dict:
    """The listed move, as the board names it."""
    return next(m for m in listing(Position.from_fen(fen)) if m["uci"] == uci)


def titled(fen: str) -> dict[str, str]:
    """Each move's title on the board, by its SAN."""
    return {m["san"]: m["title"] for m in listing(Position.from_fen(fen))}


def mates(position: Position, move: Move) -> bool:
    after = make(position, move)
    return in_check(after) and not legal_moves(after)


class Neutral(unittest.TestCase):
    """No name helps a player choose: every title, emoji, notation and words says what the move is, and a move that
    mates, stalemates or gives the queen away reads just as any other move of its kind."""

    def test_no_name_judges_a_move_or_names_an_opening(self):
        texts = {row[key] for _, _, row, _ in rows() for key in ("title", "words", "san")}
        for text in texts:
            self.assertIsNone(JUDGED.search(text), text)
            self.assertIsNone(OPENINGS.search(text), text)
            self.assertFalse(set(text) & set("+#"), text)
        emoji = {row["emoji"] for _, _, row, _ in rows()}
        self.assertFalse([e for e in emoji if any(flag in e for flag in FLAGS)])

    def test_a_mate_reads_like_a_quiet_move_of_the_same_piece(self):
        for fen, mating, quiet in (
                ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "d1d8", "d1d7"),  # a back-rank mate
                ("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2", "d8h4", "d8g5"),  # Fool's Mate
                ("6rk/6pp/8/6N1/8/8/8/K7 w - - 0 1", "g5f7", "g5e6"),  # a smothered mate
                ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7", "h5e5"),  # Scholar's
        ):
            with self.subTest(fen=fen):
                position = Position.from_fen(fen)
                self.assertTrue(mates(position, Move.from_uci(mating)))
                self.assertFalse(mates(position, Move.from_uci(quiet)))
                one, two = entry(fen, mating), entry(fen, quiet)
                self.assertEqual(one["emoji"], two["emoji"])
                for key in ("title", "san", "words"):
                    self.assertEqual(shape(one[key]), shape(two[key]), (one, two))

    def test_a_move_that_gives_the_queen_away_reads_like_any_other_queen_move(self):
        for fen, given, kept in (
                ("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2", "d8g5", "d8f6"),  # Nxg5 takes it
                ("4k3/8/3p4/8/8/8/8/Q3K3 w - - 0 1", "a1e5", "a1d4"),  # dxe5 takes it
        ):
            with self.subTest(fen=fen):
                position = Position.from_fen(fen)
                for uci, lost in ((given, True), (kept, False)):
                    after = make(position, Move.from_uci(uci))
                    self.assertEqual(any(reply.end == Move.from_uci(uci).end for reply in legal_moves(after)), lost)
                one, two = entry(fen, given), entry(fen, kept)
                self.assertEqual((one["emoji"], one["piece"]), (two["emoji"], two["piece"]))
                for key in ("title", "san", "words"):
                    self.assertEqual(shape(one[key]), shape(two[key]), (one, two))

    def test_the_same_move_reads_the_same_whatever_it_leads_to(self):
        def ends(fen: str, uci: str) -> str:
            after = make(Position.from_fen(fen), Move.from_uci(uci))
            return "mate" if in_check(after) and not legal_moves(after) else "stalemate" if not legal_moves(after) \
                else "lost" if any(reply.end == Move.from_uci(uci).end for reply in legal_moves(after)) else "on"

        for fen, twin, uci, one, two in (
                ("6k1/5ppp/8/8/8/8/8/K2R4 w - - 0 1", "6k1/5pp1/7p/8/8/8/8/K2R4 w - - 0 1", "d1d8", "mate", "on"),
                ("7k/5Q2/8/8/8/8/8/K7 w - - 0 1", "7k/5Q2/8/7p/8/8/8/K7 w - - 0 1", "f7g6", "stalemate", "on"),
                ("4k3/8/3p4/8/8/8/8/Q3K3 w - - 0 1", "4k3/8/8/8/8/8/8/Q3K3 w - - 0 1", "a1e5", "lost", "on"),
                ("r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "4k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "b5c7", "on", "on"),  # a fork
                ("4k3/8/2n5/8/8/8/8/4KB2 w - - 0 1", "4k3/8/8/8/8/8/8/4KB2 w - - 0 1", "f1b5", "on", "on"),  # a pin
                ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",  # the Sicilian, and no opening at all
                 "rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1", "c7c5", "on", "on"),
                ("4k3/8/8/8/8/5q2/8/4K3 w - - 0 1", "4k3/8/8/8/8/8/8/4K3 w - - 0 1", "e1d2", "on", "on"),  # only one
        ):
            with self.subTest(fen=fen, uci=uci):
                self.assertEqual((ends(fen, uci), ends(twin, uci)), (one, two))
                self.assertEqual(entry(fen, uci), entry(twin, uci))
        self.assertEqual(len(legal_moves(Position.from_fen("4k3/8/8/8/8/5q2/8/4K3 w - - 0 1"))), 1)

    def test_naming_plays_nothing_out(self):
        self.assertFalse({"make", "in_check", "attacked", "pseudo_moves", "san"} & set(vars(chess_names)),
                         "a name never looks at the board after its move")

    def test_the_emoji_is_the_kind_of_move(self):
        for _, _, row, seen in rows():
            kind = "castle" if seen.wing else "promotion" if seen.new else "capture" if seen.victim else seen.kind
            self.assertEqual(row["emoji"], KEY[kind], row)


class Truth(unittest.TestCase):
    """A name says only true facts of its move, in one of a few fixed forms."""

    def test_every_title_says_what_its_move_is(self):
        for position, _, row, seen in rows():
            form, said = read(row["title"])
            try:
                self.check(form, said, seen)
            except AssertionError as error:
                raise AssertionError(f"{row['title']!r} on {position.fen}: {error}") from None

    def check(self, form: str, said: dict, seen: Facts) -> None:
        self.assertEqual(said.get("wing") or "", seen.wing)
        if form == "castle":
            return
        self.assertEqual(said.get("new") or "", seen.new)
        if form in ("promotion", "underpromotion"):
            return
        self.assertEqual(form == "passant", seen.passing)
        if form == "passant":
            return
        self.assertEqual(said.get("victim") or "", seen.victim)
        if form == "take":
            self.assertEqual(said["piece"], NAMES[seen.kind])
        elif form in ("push", "double-push"):
            self.assertEqual((seen.kind, seen.two), ("p", form == "double-push"))
        elif form == "retreat":
            self.assertTrue(seen.kind in "nbrq" and seen.rise < 0 and said["piece"] == NAMES[seen.kind])
        else:  # a move: the king's any way but castling, or another piece's forward or along its rank
            self.assertEqual(said["piece"], NAMES[seen.kind])
            self.assertTrue(seen.kind == "k" or (seen.kind in "nbrq" and seen.rise >= 0))

    def test_the_words_say_the_move_exactly(self):
        for _, _, row, seen in rows():
            found = [(form, m.groupdict()) for form, pattern in SAYS.items() if (m := pattern.fullmatch(row["words"]))]
            self.assertEqual(len(found), 1, row)
            form, said = found[0]
            self.assertEqual(said["start"], seen.start, row)
            self.assertEqual((form == "castle", form == "take"), (bool(seen.wing), bool(seen.victim)), row)
            if form == "castle":
                self.assertEqual((said["to"], said["wing"]), (seen.to, seen.wing.lower()), row)
                continue
            self.assertEqual(said["piece"], NAMES[seen.kind], row)
            self.assertEqual(said["new"] or "", seen.new.lower(), row)
            if form == "take":
                self.assertEqual((said["victim"], said["at"], bool(said["passing"])),
                                 (seen.victim.lower(), seen.at, seen.passing), row)
            else:
                self.assertEqual((said["to"], bool(said["two"])), (seen.to, seen.two), row)

    def test_the_notation_is_san_without_check_or_mate(self):
        for _, _, row, seen in rows():
            self.assertTrue(PLAIN_SAN.fullmatch(row["san"]), row)
            self.assertEqual("x" in row["san"], bool(seen.victim), row)
        for position, listed in sweep()[::2]:  # every other board, as the rules' SAN plays each move to mark it
            legal = legal_moves(position)
            for row in listed:
                # the rules' SAN, given no replies, as only its mark for check or mate would need them
                self.assertEqual(row["san"], san(position, Move.from_uci(row["uci"]), legal, []).rstrip("+#"), row)

    def test_no_name_holds_a_square_a_file_or_a_rank(self):
        for title in {row["title"] for _, _, row, _ in rows()}:
            self.assertIsNone(re.search(rf"{SQ}|\b[a-h]-|\b(?:From|to [a-h]|on|file|rank)\b", title), title)

    def test_the_sweep_meets_every_kind_of_move(self):
        self.assertEqual({read(row["title"])[0] for _, _, row, _ in rows()}, set(FORMS))
        telling = set()
        for fen in TELLING:
            position = Position.from_fen(fen)
            for move in legal_moves(position):
                after = make(position, move)
                if in_check(after):
                    telling.add("mate" if not legal_moves(after) else "check")
                elif not legal_moves(after):
                    telling.add("stalemate")
        self.assertEqual(telling, {"mate", "check", "stalemate"}, "and the telling boards every way a move can end")


class Titles(unittest.TestCase):
    def test_every_board_names_every_move_in_what_the_kit_accepts(self):
        for position, listed in sweep():
            self.assertEqual(len(listed), len(legal_moves(position)))
            self.assertTrue(all(set(m) == {"uci", "san", "piece", "emoji", "title", "words"} for m in listed))
        for title in {row["title"] for _, _, row, _ in rows()}:
            self.assertTrue(KIT_TITLE.fullmatch(title) and len(title) <= min(LONGEST, LONGEST_NAME), title)
            self.assertFalse(any(dash in title for dash in DASHES), title)
        for said in {row["words"] for _, _, row, _ in rows()}:
            self.assertTrue(KIT_WORDS.fullmatch(said) and len(said) <= WORDS_LONGEST, said)
            self.assertFalse(any(dash in said for dash in DASHES), said)
        for emoji in {row["emoji"] for _, _, row, _ in rows()}:
            self.assertTrue(KIT_EMOJI.fullmatch(emoji) and emoji in KEY.values(), emoji)

    def test_every_name_is_in_title_case_with_no_mark_a_score_sheet_reads_as_a_verdict(self):
        for title in {row["title"] for _, _, row, _ in rows()}:
            self.assertFalse(set(title) & set("!?"), title)  # an annotator's ! and ? judge a move
            for word in title.split():
                self.assertTrue(word[0].isupper() or word == "to", (title, word))

    def test_the_twenty_opening_moves(self):
        title = titled(START)
        self.assertEqual(len(title), 20)
        self.assertEqual({title[san] for san in ("Na3", "Nc3", "Nf3", "Nh3")}, {"Knight Move"})
        for file in "abcdefgh":
            self.assertEqual(title[f"{file}3"], "Pawn Push")
            self.assertEqual(title[f"{file}4"], "Double Pawn Push")
        start = listing(Position.from_fen(START))
        self.assertEqual({m["emoji"] for m in start if m["piece"] == "knight"}, {"🐴"})
        self.assertEqual({m["emoji"] for m in start if m["piece"] == "pawn"}, {"♟️"})
        replies = titled("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        self.assertEqual((replies["c5"], replies["e5"], replies["e6"], replies["Nf6"]),
                         ("Double Pawn Push", "Double Pawn Push", "Pawn Push", "Knight Move"))

    def test_the_rules_name_castling_promotion_and_en_passant(self):
        castles = {m["san"]: m
                   for m in listing(Position.from_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"))}
        self.assertEqual([castles[s][k] for s in ("O-O", "O-O-O") for k in ("emoji", "title", "words")],
                         ["🏰", "Kingside Castling", "King from e1 to g1, castling kingside",
                          "🏰", "Queenside Castling", "King from e1 to c1, castling queenside"])
        self.assertEqual((castles["Rd1"]["title"], castles["Rf1"]["title"], castles["Kd1"]["title"]),
                         ("Rook Move", "Rook Move", "King Move"))
        crowned = {m["san"]: m for m in listing(Position.from_fen("r3k3/1P6/8/8/8/8/8/4K3 w - - 0 1"))}
        self.assertEqual([crowned[s][k] for s in ("b8=Q", "bxa8=N") for k in ("emoji", "title", "words")],
                         ["👑", "Promotion to Queen", "Pawn from b7 to b8, becoming a queen",
                          "👑", "Underpromotion to Knight", "Pawn from b7 takes the rook on a8, becoming a knight"])
        self.assertEqual({crowned[s]["title"] for s in ("b8=R", "b8=B", "bxa8=R", "bxa8=B")},
                         {"Underpromotion to Rook", "Underpromotion to Bishop"})
        passing = entry("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3", "e5f6")
        self.assertEqual((passing["emoji"], passing["title"], passing["san"], passing["words"]),
                         ("⚔️", "En Passant", "exf6",
                          "Pawn from e5 takes the pawn on f5, en passant"))

    def test_a_capture_reads_as_descriptive_notation_reads_it_and_a_piece_going_back_retreats(self):
        scholar = titled("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
        self.assertEqual((scholar["Qxf7"], scholar["Bxf7"], scholar["Qxe5"], scholar["Qd1"], scholar["Qf5"],
                          scholar["Qg6"], scholar["Bf1"]),
                         ("Queen Takes Pawn", "Bishop Takes Pawn", "Queen Takes Pawn", "Queen Retreat", "Queen Move",
                          "Queen Move", "Bishop Retreat"))
        black = titled("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
        self.assertEqual((black["Bc5"], black["Bb4"], black["Qg5"], black["Ne7"], black["Ke7"]),
                         ("Bishop Move", "Bishop Move", "Queen Move", "Knight Move", "King Move"))
        takers = titled("4k3/8/3n4/1N3N2/8/8/8/4K3 w - - 0 1")
        self.assertEqual((takers["Nbxd6"], takers["Nfxd6"]), ("Knight Takes Knight", "Knight Takes Knight"))

    def test_two_moves_may_share_a_name_and_their_notation_tells_them_apart(self):
        knights = {m["uci"]: (m["title"], m["san"])
                   for m in listing(Position.from_fen("4k3/8/8/8/8/2N3N1/8/4K3 w - - 0 1"))}
        self.assertEqual([knights[uci][0] for uci in ("c3e4", "g3e4", "c3e2", "g3e2", "c3b5")],
                         ["Knight Move", "Knight Move", "Knight Retreat", "Knight Retreat", "Knight Move"])
        self.assertEqual(len({knights[uci][1] for uci in ("c3e4", "g3e4", "c3e2", "g3e2")}), 4,
                         "the notation says which knight goes")
        rooks = {m["san"]: m["title"] for m in listing(Position.from_fen("4k3/8/8/8/8/R6R/8/4K3 w - - 0 1"))}
        self.assertEqual((rooks["Rad3"], rooks["Rhd3"], rooks["Ra8"], rooks["Ra1"]),
                         ("Rook Move", "Rook Move", "Rook Move", "Rook Retreat"))
        for position, listed in sweep()[::5]:
            self.assertEqual(len({m["san"] for m in listed}), len(listed), position.fen)

    def test_the_words_never_say_where_the_move_leads(self):
        said = {uci: words(Position.from_fen(fen), Move.from_uci(uci)) for fen, uci in (
            ("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2", "d8h4"),
            ("7k/5Q2/8/8/8/8/8/K7 w - - 0 1", "f7g6"),
            ("4k3/8/8/8/4N3/8/8/K3R3 w - - 0 1", "e4d6"),
            ("8/4P3/8/8/8/8/k7/4K3 w - - 0 1", "e7e8n"),
            (START, "a2a4"),
            ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "h5f7"),
        )}
        self.assertEqual(said, {"d8h4": "Queen from d8 to h4", "f7g6": "Queen from f7 to g6",
                                "e4d6": "Knight from e4 to d6", "e7e8n": "Pawn from e7 to e8, becoming a knight",
                                "a2a4": "Pawn from a2 to a4, two squares",
                                "h5f7": "Queen from h5 takes the pawn on f7"})

    def test_the_same_position_always_names_its_moves_the_same_way(self):
        position = Position.from_fen(START)
        self.assertEqual(listing(position, 1, 1), listing(position, 2, 41), "whatever the game and move number")
        later = Position.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 6 4")  # the knights went back
        self.assertEqual(listing(position, 1, 1), listing(later, 1, 7), "or the clocks")
        stepped = Position.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        again = Position.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 2 3")
        self.assertEqual(listing(stepped, 1, 2), listing(again, 1, 6), "an en passant square nobody can use is none")

    def test_the_list_runs_from_the_king_to_the_pawns(self):
        for position, listed in sweep():
            moves = [Move.from_uci(m["uci"]) for m in listed]
            self.assertEqual(moves, sorted(moves, key=lambda m: (
                "kqrbnp".index(position.board[m.start].lower()), m.end % 8, -(m.end // 8), m.start,
                "qrbn".index(m.promotion) if m.promotion else 4)))
            self.assertEqual([m["piece"] for m in listed], [NAMES[position.board[m.start].lower()].lower()
                                                            for m in moves])


if __name__ == "__main__":
    unittest.main()
