<!--
title: '🌀 PENTAGO'
description: 'How to play Pentago against @tannergolden on the profile: the Ghost Rule, making a move, the rules the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, pentago]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🌀 PENTAGO

<a name="top"></a>

**@tannergolden plays White. You play Black, with everyone else on GitHub.**

_Set a marble, turn a quarter, and the first five in a row wins._

</div>

---

## 💡 The Game

Pentago on the board under Play Against Me on
[@tannergolden's profile](https://github.com/tannergolden). @tannergolden always
sets the white marbles ⚪ and GitHub, which is everyone else, always the black
⚫. A move has two parts: a marble in any empty hole, then a quarter turn of any
of the board's four quarters. Every game opens under the Ghost Rule: each side
first sets one ghost, and then the Arbiter draws which colour goes first. Five
in a row wins.

## 🎯 Making A Move

1. **Open the list under the Pentago board** on Black's turn. It holds every
   empty hole, grouped by quarter when there are more than ten, each named for
   its kind of hole, **Centre**, **Corner** or **Edge**, with the hole, such as
   `e4`, the move in words, such as _A black marble on e4, then a quarter
   turns_, and eight links, one for each turn the move can end with: ↻ turns a
   quarter clockwise and ↺ anticlockwise, and `UL`, `UR`, `LL` and `LR` name the
   upper left, upper right, lower left and lower right quarters.
2. **Follow the link for the turn you want.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   whole move, such as `pentago: e4-ur-cw · game 1 · move 7`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can set the white marbles. Anyone else can set the black,
whoever set the last one included, and the first move to reach the game is the
one played. [Games](README.md) has the rest of what all four games share: whose
turn it is, when a move is turned away, and the clock.

## 👻 The Ghost Rule

- **Before the first marble, each side sets one ghost** in any hole it chooses:
  a marble that is nobody's. No five runs through it, and it turns with its
  quarter like any marble.
- **The Arbiter draws which side sets the first ghost** when the board opens.
  GitHub's ghost is picked from the list under the board like any move, each
  hole named for its kind, such as **Centre Ghost**, one link a hole and no
  turn, its link titled with the hole, such as
  `pentago: b5 · game 1 · move 1`.
- **Once both ghosts are down, the Arbiter draws which side sets the first
  marble**, in the same run.
- **A side that goes a week without setting its ghost** gets one in a random
  hole from the Arbiter.
- **With two holes the ghosts', each side has seventeen marbles.**

## 📜 The Rules

- **The board is six holes a side in four quarters of three by three**, its
  holes named as chess names its squares: the files `a` to `f` from the left
  and the ranks `1` to `6` from the bottom, so `a1` is the lower left hole. The
  quarters are the upper left (`a4` to `c6`), the upper right (`d4` to `f6`),
  the lower left (`a1` to `c3`) and the lower right (`d1` to `f3`).
- **A move sets a marble in an empty hole, then turns one quarter a quarter
  turn**, clockwise or anticlockwise as the board is seen, everything on it
  turning with it. Any quarter may turn, an empty one too, and every move turns
  one.
- **Five marbles of one colour in a row wins**: across, up and down, or on a
  diagonal, once the quarter has turned.
- **A marble that makes five on its own wins at once**, before any quarter
  turns.
- **A turn can win for the other side.** A turn that makes five for the other
  colour alone wins the game for it, and one that makes five for both is a
  draw.
- **A full board with no five in a row is a draw.**
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

| Where                                  | How                                                                                         | Example              |
| :------------------------------------- | :------------------------------------------------------------------------------------------ | :------------------- |
| A move's issue title                   | The hole, the quarter and the way it turns                                                  | `e4-ur-cw`           |
| Replies and the finished game's record | The same, with `#` on the move that wins, or the hole alone with its `#` when the marble made five on its own | `e4-ur-acw#`, `e4#` |
| The sheet beside the board             | The hole, an arrow the way the quarter turned, and the quarter                              | `e4 ↻ UR`            |
| A ghost                                | The hole alone, on the score sheet's first row, `G`                                         | `b5`                 |

In a code, `ul`, `ur`, `ll` and `lr` are the four quarters, and `cw` and `acw`
are clockwise and anticlockwise. A title's move number counts the two ghosts,
so the first marble is move 3. A finished game is kept as a text record, every
ghost and move with who chose it.

## 🗺️ The Board

The sheet beside the board shows the two sides with the side to move ringed,
whose turn it is and when the move is due, the last move in notation and in
words with who played it, each side's marbles left from its seventeen and where
the ghosts stand now, and the latest rows of the score sheet, with who chose
each of Black's moves. A ghost is a marble the board's own colour, ringed in
dashes. As the file opens, the last marble is set again and its quarter turns,
an arrow drawn round the quarter the way it went; once a game is won, its five
are ringed and joined.

## ⏰ The Clock

- **Each move is due a week after the move before it**, and the first ghost a
  week after the board opens. A side that goes a week without moving gets a
  random legal move from the Arbiter, or a ghost in a random hole, which counts
  for nobody.

## 🏁 When A Game Ends

- **The move that makes five in a row wins**: for @tannergolden when the five
  are white and the move was White's, or for the player who chose the black move
  that made five black. The Arbiter answers it on its issue, and the win counts
  in the Hall of Fame.
- **A win the other side's turn made counts for no player**, and neither does a
  draw or a win the Arbiter's move made. The series still counts each win for
  the side that won it.
- **The final board stays up for two days**, with a countdown to the next game,
  and then a fresh board comes, with the Arbiter's draw for its first ghost.
- **Every finished game is kept as a text record** in `.github/pentago/games/`
  in this repository.

---

<div align="center">

**One marble and one quarter turn a move, until five line up.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
