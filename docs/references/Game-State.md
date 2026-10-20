<!--
title: '📦 GAME STATE'
description: 'Every file a game keeps under .github/<game>/, field by field, the records of its finished games and their replays, and the regions of .github/markdown.yaml the games write. Consult it when reading a game''s history, or a run that failed on its state.'
type: reference
keywords: [json, hall-of-fame, pgn, pdn, replay, settings, regions, records]
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 📦 GAME STATE

<a name="top"></a>

**Every file a game keeps, field by field, and the regions it writes for the page.**

_Written by the runs, and replayed on every one._

</div>

---

## 📁 Where It Lives

```bash
.github/<game>/                # chess, checkers, pentago or tictac
├── README.md                  # the folder's log
├── game.json                  # the game on the board
├── hall-of-fame.json          # every finished game, from the first one
└── games/                     # from the first finished game
    ├── game-N.pgn             # Chess; game-N.pdn for Checkers, game-N.txt for the other two
    └── game-N.replay.json     # a game a person's own move won
```

Only the game's own runs and the clock write these, through each engine's
`save`. Every run replays the game from its first move, so a file here that a
run did not write can stop that game and the clock:
[Troubleshooting](../operations/Troubleshooting.md#-a-games-state-will-not-load)
says how to get it back. Times are UTC, written as `2026-10-17T10:55:58Z`, and
the two sides are `house`, the owner, and `github`, everyone else.

---

## 📄 game.json

| Field     | In               | Holds                                                                                |
| :-------- | :--------------- | :----------------------------------------------------------------------------------- |
| `game`    | every game       | The game's number, from 1                                                            |
| `started` | every game       | When its board opened; a fresh board's is the moment the last game's two days are up |
| `fen`     | Chess            | The position on the board, in FEN                                                    |
| `places`  | Pentago, Tic-Tac | The side the Arbiter drew to place the first ghost                                   |
| `ghosts`  | Pentago, Tic-Tac | The two ghosts, each kept as a move is                                               |
| `opens`   | Pentago, Tic-Tac | The side the Arbiter drew to move first, once both ghosts are down                   |
| `moves`   | every game       | Every move played, in order                                                          |
| `ended`   | every game       | The game that just finished, whole, while its final board is up                      |

`ended` stays until the next game's first move, or under the Ghost Rule until
the Arbiter's draw for its first ghost. Each move, and each ghost, holds:

| Field                 | Holds                                                                                                                      |
| :-------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| `uci`, `san`          | Chess: the move as its issue's title carries it, in UCI (`d2d4`), and in SAN (`d4`)                                        |
| `move`, `shown`       | The others: the move as its issue's title carries it (`e5`, `e4-ur-cw`, `11-15`), and as the score sheet writes it (`Xe5`) |
| `player`, `player_id` | The login and account ID of whoever opened the move's issue, or `null` for the Arbiter                                     |
| `issue`               | The move's issue in tannergolden/play, or `null` for the Arbiter                                                           |
| `arbiter`             | `true` for the Arbiter's move or ghost after a week                                                                        |
| `at`                  | When it was played                                                                                                         |

---

## 🏆 hall-of-fame.json

A list with one record for each finished game, oldest first. `hall.py` reads
all four games' lists, and the game on each board, for the Hall of Fame.

| Field                      | Holds                                                                                                                                                                                   |
| :------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `game`, `started`, `ended` | The game's number, and when its board opened and when the game ended                                                                                                                    |
| `result`                   | `1-0`, `0-1` or `1/2-1/2`, the house's score first, but Black's first in Checkers, as PDN writes it                                                                                     |
| `reason`                   | How it ended, from the table below                                                                                                                                                      |
| `winner`                   | The owner's login, `GitHub`, or `null` for a draw                                                                                                                                       |
| `plies`                    | Every turn played, the ghosts included                                                                                                                                                  |
| `deciding`                 | The move that ended it as the score sheet numbers it (`move`), with its `player`, `player_id`, `arbiter` and `issue`; and `own: false` when a Pentago turn made five for the other side |
| `players`                  | Everyone who played for GitHub, most turns first, each with `player`, `player_id` and `moves`                                                                                           |
| `house_moves`              | How many of the house's turns the owner made                                                                                                                                            |
| `final`                    | The final board, in every game but Chess, Checkers' as a FEN                                                                                                                            |
| `line`                     | The winning line: Pentago's five holes, or Tic-Tac's three boards                                                                                                                       |

| Game     | A win is                | A draw is                                                                                                |
| :------- | :---------------------- | :------------------------------------------------------------------------------------------------------- |
| Chess    | `checkmate`             | `stalemate`, `fivefold repetition`, `seventy-five-move rule`, `insufficient material` or `dead position` |
| Checkers | `no move left`          | `repetition` or `forty moves`                                                                            |
| Pentago  | `five in a row`         | `five for both` or `a full board`                                                                        |
| Tic-Tac  | `three boards in a row` | `no line left`                                                                                           |

A win counts for a person only when its deciding move was neither the
Arbiter's nor a Pentago turn that made five for the other side; each game's
series still counts every win for the side that won it.

---

## 📜 The Finished Games

| File                 | Game             | Holds                                                                                                                                                                                                                                                                              |
| :------------------- | :--------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `game-N.pgn`         | Chess            | PGN: the tags `Event`, `Site`, `Date`, `Round`, `White`, `Black`, `Result`, `Termination`, `PlyCount` and `EndDate`, then every move followed by who chose it, such as `{tannergolden}` or `{the Arbiter, after a week}`, a closing comment such as `{Checkmate.}`, and the result |
| `game-N.pdn`         | Checkers         | PDN for English draughts (`GameType` 21): the same tags, Black's before White's and no `Termination`, the moves numbered Black's first, each followed by who chose it, a closing comment such as `{White has no move left.}`, and the result                                       |
| `game-N.txt`         | Pentago, Tic-Tac | Text: the game, its days in EST, who played which side and how the Arbiter drew, the result, then every turn numbered, the ghosts on the `G` row, with who chose it, and the result again, the house's score first                                                                 |
| `game-N.replay.json` | every game       | The facts of a game a person's own move won, for play's Replay workflow: the game, its winner and deciding move, its players, and every turn with its side, notation, words, who chose it, the day and what it did on the board                                                    |

The replay's facts carry `replay: 1`, the version of their shape the kit's
`replay` command reads; `replays.py` says what each game's turns record.

---

## 🧩 The Regions The Games Write

After every run, each engine sets its own board out between its markers under
`elements:` in `.github/markdown.yaml`, and the Hall of Fame of all four
between `# hall:start` and `# hall:end`; the clock sets out all five. The kit
draws each one from there.

| Region                                 | Element        | Written by                                        |
| :------------------------------------- | :------------- | :------------------------------------------------ |
| `# tictac:start` to `# tictac:end`     | `tictac`       | Tic-Tac's runs, through `games.py`, and the clock |
| `# pentago:start` to `# pentago:end`   | `pentago`      | Pentago's runs, through `games.py`, and the clock |
| `# checkers:start` to `# checkers:end` | `checkers`     | Checkers' runs, through `games.py`, and the clock |
| `# chess:start` to `# chess:end`       | `chess`        | Chess's runs, through `chess.py`, and the clock   |
| `# hall:start` to `# hall:end`         | `hall-of-fame` | every game's runs, and the clock                  |

A region is written only when what it holds changed. The fields each element
carries are the ones the kit draws, and the kit's
[Settings](https://github.com/tannergolden/markdown/blob/Development/docs/references/Settings.md#-elements)
reference lists them. What the engines put in them:

- **`note`** is held to 400 characters, the most the kit takes for a line of
  the README: it always says what it must, and each other sentence only where
  it fits.
- **`moves`** holds every move that can be played, or every open square or
  hole while the ghosts go down, each with its emoji, name, notation and words
  and the link that opens its ready-made issue,
  `https://github.com/<owner>/play/issues/new?template=move.yml&title=<the title, URL-encoded>`.
  A Pentago hole carries eight links, one for each turn, and Chess groups its
  moves by piece.
- **While a final board is up**, an element carries `result`, and `next` and
  `next_at`, the day and the moment the fresh board comes, and no moves.
- **`hall-of-fame`** holds `series` (each game's games finished, the house's
  wins, GitHub's wins and the draws), `people` (the leading winners, up to ten
  of them) and `leaders` (the house's row, then up to twenty of GitHub's
  players): twice the places the page shows, each with its account ID, so the
  kit can name players as they are now and fill the place of an account that
  is gone.

---

## 🔗 See also

- [How The Games Run](../technical/How-The-Games-Run.md) - the runs that
  write these files, and the order they rule in
- [Games](../library/Games.md) - the same games, as a player sees them
- [`.github/chess/`](../../.github/chess/README.md) - one game's folder, and
  its log

---

<div align="center">

**The state is the game: change it only by playing.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
