<!--
title: '❌ TIC-TAC'
description: 'How to play Tic-Tac against @tannergolden on the profile: the Ghost Rule, making a move, the rules the board holds to, how moves are written, the clock, and how a game ends.'
tags: [games, how-to-play, tic-tac, ultimate-tic-tac-toe]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# ❌ TIC-TAC

<a name="top"></a>

**@tannergolden plays X. You play O, with everyone else on GitHub.**

_Nine games of Tic-Tac-Toe in one, and every mark says where the next one goes._

</div>

---

## 💡 The Game

Tic-Tac on the board under Play Against Me on
[@tannergolden's profile](https://github.com/tannergolden): Tic-Tac-Toe on nine
boards at once, three a side, the game also known as Ultimate Tic-Tac-Toe.
@tannergolden always plays X and GitHub, which is everyone else, always plays
O. Every game opens under the Ghost Rule: each side first locks one square with
a ghost, and then the Arbiter draws which mark goes first. Three boards won in a
row wins the game.

## 🎯 Making A Move

1. **Open the list under the Tic-Tac board** on O's turn. It holds every square
   O may take, grouped by board when there are more than ten, each named for
   its kind of square, **Centre**, **Corner** or **Edge**, with the move in
   notation, such as `Oe5`, the same move in words, such as _O takes the centre
   of the centre board_, and a **Play ↗** link.
2. **Follow a move's link.** It opens a ready-made issue in
   [tannergolden/play](https://github.com/tannergolden/play), titled with the
   square, such as `tictac: e5 · game 1 · move 7`.
3. **Submit it as it opens, without changing the title.** Within a few minutes
   the Official Arbiter answers on your issue and the board is redrawn.

Only @tannergolden can play X. Anyone else can play O, whoever played the last
O included, and the first move to reach the game is the one played.
[Games](README.md) has the rest of what all four games share: whose turn it
is, when a move is turned away, and the clock.

## 👻 The Ghost Rule

- **Before the first mark, each side places one ghost** on any square it
  chooses. Nobody can take a ghost's square, and no line runs through it.
- **The Arbiter draws which side places the first ghost** when the board
  opens. GitHub's ghost is picked from the list under the board like any move,
  each square named for its kind, such as **Centre Ghost**, its link titled
  with the square, such as `tictac: e5 · game 1 · move 1`.
- **Once both ghosts are down, the Arbiter draws which side makes the first
  mark**, in the same run. The first mark may go on any square of any board.
- **A side that goes a week without placing its ghost** gets one on a random
  square from the Arbiter.

## 📜 The Rules

- **The big board is nine small boards, three a side**, and its 81 squares are
  named as chess names its squares: the files `a` to `i` from the left and the
  ranks `1` to `9` from the bottom, so `a1` is the lower left square and `e5`
  the centre of the centre board. Each small board is named by its place: the
  upper left board, the centre board, the lower right board, and so on.
- **Every mark sends the other side somewhere.** Where a mark goes inside its
  board decides where the reply goes: take a board's upper right corner, and
  the other side must play in the upper right board. The sheet brackets that
  board, and its plate names it.
- **Three in a row inside a board wins that board**, which closes, its winner's
  mark drawn across it. A board whose open squares are all taken without three
  in a row is drawn, and closes too. A ghost's square counts as taken.
- **A side sent to a closed board may play any open square of any open
  board.** Its plate says _any board_.
- **Three boards won in a row wins the game**: across, up and down, or on a
  diagonal of the big board.
- **The game is drawn once neither side can still win three boards in a row.**
- **Nobody can resign or offer a draw.**

## ✍️ How Moves Are Written

| Where                                 | How                                                               | Example        |
| :------------------------------------ | :---------------------------------------------------------------- | :------------- |
| A move's issue title                  | The square                                                        | `e5`           |
| The list, replies and the score sheet | The mark, then the square, with `#` on the mark that wins the game | `Oe5`, `Xc7#` |
| A ghost                               | The square alone, on the score sheet's first row, `G`             | `e5`           |

A title's move number counts the two ghosts, so the first mark is move 3. A
finished game is kept as a text record, every ghost and mark with who chose it.

## 🗺️ The Board

The sheet beside the board shows the two sides with the side to move ringed,
whose turn it is, where it must play and when the move is due, the last move in
notation and in words with who played it, how many boards each side has won,
and the latest rows of the score sheet, with who chose each of O's moves. A
ghost's square is filled and edged in dashes. As the file opens, the last mark
draws itself again; a board it wins is struck through and its winner's mark
drawn across it, and the board the reply goes to is bracketed.

## ⏰ The Clock

- **Each move is due a week after the move before it**, and the first ghost a
  week after the board opens. A side that goes a week without moving gets a
  random legal mark from the Arbiter, or a ghost on a random square, which
  counts for nobody.

## 🏁 When A Game Ends

- **The mark that wins a third board in a row wins the game**: for
  @tannergolden when it is an X, or for the player who placed the O. The Arbiter
  answers it on its issue, and the win counts in the Hall of Fame.
- **A draw is nobody's win**, and neither is a win the Arbiter's mark made.
- **The final board stays up for two days**, with a countdown to the next game,
  and then a fresh board comes, with the Arbiter's draw for its first ghost.
- **Every finished game is kept as a text record** in `.github/tictac/games/`
  in this repository.

---

<div align="center">

**One mark a turn, where the last one sent it, until three boards line up.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
