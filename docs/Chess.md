<!--
title: '♟️ CHESS'
description: 'How to play Chess against @tannergolden on the profile: making a move, the rules the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, chess]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# ♟️ CHESS

<a name="top"></a>

**@tannergolden plays White. You play Black, with everyone else on GitHub.**

_Every legal move of chess, played one at a time from the board on the profile._

</div>

---

## 💡 The Game

Standard chess on the board under Play Against Me on
[@tannergolden's profile](https://github.com/tannergolden). @tannergolden always
plays White and opens every game; GitHub, which is everyone else, always plays
Black. Checkmate wins, and a game ends only when the rules of chess end it.

## 🎯 Making A Move

1. **Open the list under the Chess board** on Black's turn. It holds every legal
   move, grouped by piece, each with a name, the move in standard notation, such
   as `Nf6`, the same move in words, such as _Knight from g8 to f6_, and a
   **Play ↗** link.
2. **Follow a move's link.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   move, such as `chess: g8f6 · game 1 · move 2`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can play White's moves. Anyone else can play Black's,
whoever played the last one included, and the first move to reach the game is
the one played. [The Games](README.md) has the rest of what all four games
share: whose turn it is, when a move is turned away, and the clock.

## 📜 The Rules

- **Every legal move can be played**, castling, en passant and promotion
  included, and no move that would leave its own king in check.
- **Castling needs the right still held**, nothing between the king and the
  rook, and a king that is not in check and does not pass through or land on an
  attacked square.
- **A pawn that reaches the far rank becomes the piece its move names**, a
  queen, rook, bishop or knight; the list has each as a move of its own.
- **Checkmate wins.**
- **These draws end a game by themselves**, as FIDE makes them automatic:
  stalemate; the same position five times; 75 moves by each side with no
  capture and no pawn moved; too little material left for either side to mate;
  and a position from which no series of moves could ever mate, such as kings
  shut out behind locked pawns.
- **The threefold repetition and the fifty-move rule never end a game here.**
  In chess they must be claimed, and nobody here claims.
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

| Where                         | How                                        | Example                    |
| :---------------------------- | :----------------------------------------- | :------------------------- |
| The list under the board      | Standard notation, without `+` or `#`      | `Nf3`, `exd5`, `O-O`, `e8=Q` |
| A move's issue title          | The square it leaves and the one it lands on | `g1f3`, `e7e8q`, `e1g1`  |
| Replies and the score sheet   | Numbered, with check and mate marked       | `12. Nf3`, `12... Qh4#`    |
| A finished game's record      | PGN, each move with who chose it           | `1. e4 {tannergolden}`     |

In a title, a promotion adds the piece's letter, so `e7e8q` makes a queen, and
castling is written as the king's move, so `e1g1` castles king's side.

## 🗺️ The Board

The sheet beside the board shows the two sides with the side to move ringed,
whose turn it is and when the move is due, the last move in notation and in
words with who played it, what each side has taken, and the latest rows of the
score sheet, with who chose each of Black's moves. A king in check is marked,
and the turn says so.

## ⏰ The Clock

- **Each move is due a week after the move before it.** A side that goes a week
  without moving gets a random legal move from the Arbiter, which counts for
  nobody.
- **The first game begins with @tannergolden's first move**, and its clock only
  starts then.
- **A later game's board opens two days after the last game ended**, and if
  White's first move hasn't come within a week of that, the Arbiter plays one.

## 🏁 When A Game Ends

- **Checkmate wins**: for @tannergolden when White mates, or for the player who
  played Black's mating move. The Arbiter answers it on its issue, and the win
  takes its place in the Hall of Fame.
- **A draw is nobody's win**, and neither is a mate the Arbiter played after a
  week.
- **The final board stays up for two days**, and then a fresh board comes with
  @tannergolden to open it as White.
- **Every finished game is kept as a PGN** in `.github/chess/games/` in this
  repository.

---

<div align="center">

**White opens. Black answers. Checkmate decides.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
