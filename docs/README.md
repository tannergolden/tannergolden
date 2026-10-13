<!--
title: '🎲 THE GAMES'
description: 'How to play the four games on the profile against @tannergolden: making a move, whose turn it is, the clock and the Arbiter, and what happens when a game ends.'
tags: [games, how-to-play, chess, checkers, connect-four, tic-tac-toe]
category: docs
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🎲 THE GAMES

<a name="top"></a>

**Four games on the profile, each played one move at a time from its board.**

_@tannergolden plays one side. You play the other, with everyone else on GitHub._

</div>

---

## 🧭 The Four Games

| Game            | @tannergolden plays | GitHub plays | Who opens                                | A win is                             | Guide                           |
| :-------------- | :------------------ | :----------- | :--------------------------------------- | :----------------------------------- | :------------------------------ |
| ♟️ Chess        | White               | Black        | @tannergolden                            | checkmate                            | [Chess](Chess.md)               |
| 🏁 Checkers     | White               | Black        | GitHub                                   | leaving the other side with no move  | [Checkers](Checkers.md)         |
| ⚫ Connect Four | White ⚪            | Black ⚫     | the Arbiter, for a side drawn at random  | four discs in a row                  | [Connect Four](Connect-Four.md) |
| ❌ Tic-Tac-Toe  | X                   | O            | the Arbiter, for a side drawn at random  | three marks in a row                 | [Tic-Tac-Toe](Tic-Tac-Toe.md)   |

Each guide has its game's rules, how its moves are written and how its games
end. What all four share is below.

## 🎯 Making A Move

1. **Find the board** under Play Against Me on
   [@tannergolden's profile](https://github.com/tannergolden). Chess is open,
   and the other three open with a click.
2. **Open the list of moves** under the board. On GitHub's turn it lists every
   legal move: a name for it, the move in the game's own notation, the same
   move in plain words, and a **Play ↗** link.
3. **Follow a move's link.** It opens a new issue in
   [tannergolden/play](https://github.com/tannergolden/play) with the move
   already in its title.
4. **Submit the issue as it opens.** The title is all the game reads, so leave
   it exactly as it is. The note box is optional, and only for people: the game
   never reads it.
5. **Give it a few minutes.** A bot checks the move, reacts with 🚀 and closes
   the issue, which means the move was received. Then the game plays it, the
   Official Arbiter answers on your issue, and the board is redrawn.

A move's title reads `game: move · game N · move M`, such as
`chess: e2e4 · game 1 · move 12`. Its move number counts every move both sides
have made, so it can differ from the number on the board: it tells the game
which board your move was picked from.

## ⏱️ Whose Turn It Is

- **Each side is always the same.** @tannergolden plays White in Chess,
  Checkers and Connect Four, and X in Tic-Tac-Toe. GitHub, which is everyone
  else, plays Black, or O.
- **On @tannergolden's turn, only @tannergolden can play.** A move from anyone
  else is turned away with a reply on its issue.
- **On GitHub's turn, anyone but @tannergolden can play**, whoever played
  GitHub's last move included.
- **The first move to reach the game is the one played.** If another got there
  first, yours is turned away, and the reply says which move beat it.

## 🚫 When A Move Is Turned Away

Nothing is played, and the reply on your issue says why. A move is turned away
when:

- it isn't your side's turn;
- it isn't a legal move on the board as it stands;
- the board has moved on since you picked it, or the move is for a game that is
  over or hasn't begun;
- the last game's final board is still up: the reply gives the day the next
  game opens;
- its title was changed, so it no longer reads as a move;
- you have opened more than 30 issues in tannergolden/play in the last hour,
  across the four games together.

To play again, pick a move from the board as it stands now. An issue that isn't
a move is closed with a note on how to play, and an issue opened by a bot
account is never played.

## ⏰ The Clock And The Arbiter

- **Each move is due a week after the move before it**, or a week after its
  game opened if nothing has been played yet. The board says when.
- **A side that goes a week without moving gets a random legal move from the
  Arbiter.** The Arbiter says so on the issue of the move it answers.
- **The clock checks every game twice an hour**, so a move the Arbiter makes
  lands within about half an hour of its deadline, or later when GitHub runs
  the clock late.
- **The Arbiter's moves count for nobody**: its openings, its moves after a
  week, and any win one of them makes.

## 🏁 When A Game Ends

- **A game ends only when its rules end it.** Nobody can resign or agree a draw.
- **The Arbiter answers the move that ended it** with the result, on its issue.
- **The final board stays up for two days.** Nothing can be played until then,
  and the note under the board says when the next game opens.
- **Then a fresh board comes by itself**, opened the way its game always opens.
- **Every finished game is kept**, as PGN for Chess, PDN for Checkers and a
  text record for Connect Four and Tic-Tac-Toe, in `.github/<game>/games/` in
  this repository.

## 🏆 The Hall Of Fame

- **A win counts for the player who made the winning move**: @tannergolden when
  the house wins, or whoever played GitHub's winning move.
- **A draw is nobody's win**, and neither is a win that the Arbiter's move made.
  Each game's series still counts every win for the side that won it, the
  Arbiter's included.
- **The Hall of Fame shows the five players with the most wins** across the four
  games, @tannergolden included, and a leaderboard of @tannergolden and the ten
  GitHub players with the most wins, then the most moves.
- **Players are named by their username as it is now**, and an account that has
  been deleted is left off.

## 👀 Good To Know

- **Your move is public.** It and your username appear on the profile with the
  game's moves, in the Arbiter's replies, in the Hall of Fame and in the
  finished game's record.
- **One move per issue.** To play again, come back on GitHub's next turn and
  pick a new move.

---

<div align="center">

**Pick a move, submit it as it opens, and the board answers.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
