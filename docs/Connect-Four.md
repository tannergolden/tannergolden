<!--
title: '⚫ CONNECT FOUR'
description: 'How to play Connect Four against @tannergolden on the profile: making a move, the rules the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, connect-four]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# ⚫ CONNECT FOUR

<a name="top"></a>

**@tannergolden drops the white discs. You drop the black, with everyone else on GitHub.**

_Seven columns, six rows, and the first four in a row wins._

</div>

---

## 💡 The Game

Connect Four on the board under Play Against Me on
[@tannergolden's profile](https://github.com/tannergolden). @tannergolden always
drops the white discs ⚪ and GitHub, which is everyone else, always drops the
black ⚫. The Arbiter opens every game for a side drawn at random, with a random
first disc, so either colour can drop first. Four in a row wins.

## 🎯 Making A Move

1. **Open the list under the Connect Four board** on Black's turn. It holds
   every column that still has room, each with a name, the column's number,
   such as `4`, where the disc lands in words, such as _A black disc down column
   4, to row 1_, and a **Play ↗** link.
2. **Follow a move's link.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   move, such as `connectfour: 4 · game 1 · move 2`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can drop the white discs. Anyone else can drop the black,
whoever dropped the last one included, and the first move to reach the game is
the one played. [Games](Games.md) has the rest of what all four games
share: whose turn it is, when a move is turned away, and the clock.

## 📜 The Rules

- **The frame stands seven columns wide and six rows high**, the columns
  numbered 1 to 7 from the left and the rows 1 to 6 from the foot.
- **A disc drops down its column** to the lowest empty cell, and a full column
  takes no more.
- **The Arbiter opens every game**, for a side drawn at random, with a random
  first disc, and that side's colour drops first. Its opening is the game's
  first move and counts for nobody.
- **Four discs of one colour in a row wins**: across, up and down, or on a
  diagonal.
- **A full frame with no four in a row is a draw.**
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

| Where                             | How                                   | Example     |
| :-------------------------------- | :------------------------------------ | :---------- |
| The list and a move's issue title | The column's number                   | `4`         |
| The score sheet                   | The column, with `#` on the winning drop | `4`, `4#` |
| Replies                           | The disc, then the column             | `⚪4`, `⚫4#` |

A finished game is kept as a text record, every drop with who chose it.

## 🗺️ The Board

The sheet beside the frame shows the two sides with the side to move ringed,
whose turn it is and when the move is due, the last drop in notation and in
words with who played it, each side's discs left from its 21, and the latest
rows of the score sheet, with who chose each of Black's drops. Once a game is
won, its four discs are marked.

## ⏰ The Clock

- **Each move is due a week after the move before it.** A side that goes a week
  without moving gets a random legal drop from the Arbiter, which counts for
  nobody.

## 🏁 When A Game Ends

- **The disc that makes four in a row wins**: for @tannergolden when it is
  white, or for the player who dropped the black one. The Arbiter answers it on
  its issue, and the win takes its place in the Hall of Fame.
- **A draw is nobody's win**, and neither is a win the Arbiter's drop made.
- **The final board stays up for two days**, and then a fresh board comes, with
  the Arbiter to open it for a side drawn at random.
- **Every finished game is kept as a text record** in
  `.github/connectfour/games/` in this repository.

---

<div align="center">

**One disc a turn, down any column with room, until four line up.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
