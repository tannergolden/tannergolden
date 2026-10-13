<!--
title: '🏁 CHECKERS'
description: 'How to play Checkers against @tannergolden on the profile: making a move, the rules of American checkers the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, checkers]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🏁 CHECKERS

<a name="top"></a>

**@tannergolden plays White. You play Black, with everyone else on GitHub.**

_American checkers, where Black moves first, so GitHub opens every game._

</div>

---

## 💡 The Game

American checkers, also called English draughts, on the board under Play
Against Me on [@tannergolden's profile](https://github.com/tannergolden).
@tannergolden always plays White and GitHub, which is everyone else, always
plays Black. Black moves first, so GitHub opens every game. A side that is left
with no move on its turn loses.

## 🎯 Making A Move

1. **Open the list under the Checkers board** on Black's turn. It holds every
   legal move, each with the name a checkers player gives it, such as **Man
   Move**, **Double Jump** or **Crowning Move**, the move in checkers notation,
   such as `9-13`, the same move in words, such as _Man from 9 to 13_, and a
   **Play ↗** link. A name never holds a square, so two moves can share one,
   and the notation tells them apart.
2. **Follow a move's link.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   move, such as `checkers: 9-13 · game 1 · move 1`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can play White's moves. Anyone else can play Black's,
whoever played the last one included, and the first move to reach the game is
the one played. [Games](README.md) has the rest of what all four games
share: whose turn it is, when a move is turned away, and the clock.

## 📜 The Rules

- **The board is the 32 dark squares**, numbered 1 to 32, four to a row, from
  Black's back row (1 to 4) to White's (29 to 32). Black's twelve men start on
  1 to 12 and White's on 21 to 32.
- **A man steps one square diagonally forward**, and a king one square
  diagonally either way.
- **Jumping is compulsory.** A side that can jump must, though it may choose
  which jump, the longest or not. A jump goes over a piece of the other side to
  the empty square beyond, and the taken piece leaves the board.
- **A jump goes on while the piece can take more**, a man jumping only forward
  and a king either way, and no piece is taken twice.
- **A man that reaches the far row is crowned a king**, and its move ends
  there, even if it could jump on.
- **A side with no legal move on its turn loses**, whether it has no piece left
  or none that can move.
- **These draws end a game by themselves**, since nobody is here to agree one:
  the same position with the same side to move for the third time, and forty
  moves by each side, eighty in all, with no capture and no man moved.
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

The same notation everywhere: in the list under the board, in a move's issue
title, in replies, on the score sheet and in the finished game's record.

| Move                        | Written    |
| :-------------------------- | :--------- |
| A step from 11 to 15        | `11-15`    |
| A jump from 22 to 15        | `22x15`    |
| A jump from 22 to 15, on to 8 | `22x15x8` |

A finished game is kept as a PDN record, with Black's score first.

## 🗺️ The Board

Every dark square carries its number. The sheet beside the board shows the two
sides with the side to move ringed, whose turn it is and when the move is due,
the last move in notation and in words with who played it, the men each side
has taken and the kings made, and the latest rows of the score sheet, with who
chose each of Black's moves. When a jump must be taken, the man that has to
jump is marked, and the turn says so.

## ⏰ The Clock

- **Each move is due a week after the move before it**, and Black's opening a
  week after its board opened. A side that goes a week without moving gets a
  random legal move from the Arbiter, which counts for nobody.

## 🏁 When A Game Ends

- **The move that leaves the other side with no move wins**: for @tannergolden
  when White makes it, or for the player who played Black's. The Arbiter
  answers it on its issue, and the win takes its place in the Hall of Fame.
- **A draw is nobody's win**, and neither is a win the Arbiter's move made.
- **The final board stays up for two days**, and then a fresh board comes for
  GitHub to open as Black.
- **Every finished game is kept as a PDN record** in `.github/checkers/games/`
  in this repository.

---

<div align="center">

**Black opens. Jumps are taken. The side with no move left loses.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
