<!--
title: '❌ TIC-TAC-TOE'
description: 'How to play Tic-Tac-Toe against @tannergolden on the profile: making a move, the rules the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, tic-tac-toe]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# ❌ TIC-TAC-TOE

<a name="top"></a>

**@tannergolden plays X. You play O, with everyone else on GitHub.**

_Nine cells, two marks, and the first three in a row wins._

</div>

---

## 💡 The Game

Tic-Tac-Toe on the board under Play Against Me on
[@tannergolden's profile](https://github.com/tannergolden). @tannergolden always
plays X and GitHub, which is everyone else, always plays O. The Arbiter opens
every game for a side drawn at random, with a random first mark, so either mark
can move first. Three in a row wins.

## 🎯 Making A Move

1. **Open the list under the Tic-Tac-Toe board** on O's turn. It holds every
   open cell, each with a name, the move in notation, such as `Ob2`, the same
   move in words, such as _O takes the centre_, and a **Play ↗** link.
2. **Follow a move's link.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   cell, such as `tictactoe: b2 · game 1 · move 2`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can play X. Anyone else can play O, whoever played the last
O included, and the first move to reach the game is the one played.
[Games](Games.md) has the rest of what all four games share: whose turn it
is, when a move is turned away, and the clock.

## 📜 The Rules

- **The board is three cells a side**, named as chess names its squares: the
  files `a` to `c` from the left and the ranks `1` to `3` from the bottom, so
  `a1` is the lower left corner and `b2` the centre.
- **The Arbiter opens every game**, for a side drawn at random, with a random
  first mark, and that side's mark goes first: in a game opened for GitHub, O
  moves first. Its opening is the game's first move and counts for nobody.
- **The sides take turns**, one mark in one open cell each.
- **Three marks in a row wins**: across, up and down, or on a diagonal.
- **A full board with no three in a row is a draw.**
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

| Where                         | How                                   | Example        |
| :---------------------------- | :------------------------------------ | :------------- |
| A move's issue title          | The cell                              | `b2`           |
| The list, replies and the score sheet | The mark, then the cell, with `#` on the winning mark | `Ob2`, `Xc1#` |

A finished game is kept as a text record, every mark with who chose it.

## 🗺️ The Board

The sheet beside the board shows the two sides with the side to move ringed,
whose turn it is and when the move is due, the last mark in notation and in
words with who played it, each side's marks left, five for the side that moved
first and four for the other, and the latest rows of the score sheet, with who
chose each of O's marks. While a game goes on, the eight lines it can be won on
are drawn faint through the cells, all of them, whatever stands on them, and a
won line is struck through.

## ⏰ The Clock

- **Each move is due a week after the move before it.** A side that goes a week
  without moving gets a random legal mark from the Arbiter, which counts for
  nobody.

## 🏁 When A Game Ends

- **The mark that makes three in a row wins**: for @tannergolden when it is an
  X, or for the player who placed the O. The Arbiter answers it on its issue,
  and the win takes its place in the Hall of Fame.
- **A draw is nobody's win**, and neither is a win the Arbiter's mark made.
- **The final board stays up for two days**, and then a fresh board comes, with
  the Arbiter to open it for a side drawn at random.
- **Every finished game is kept as a text record** in
  `.github/tictactoe/games/` in this repository.

---

<div align="center">

**One mark a turn, until three line up or the board is full.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
