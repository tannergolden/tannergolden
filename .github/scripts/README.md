<!--
title: '🧰 SCRIPTS'
description: 'Every script the profile's workflows run, from each game's engine and rules to the clock, the notes and the Hall of Fame, with the tests beside them.'
type: index
-->

<div align="center">

# 🧰 SCRIPTS

<a name="top"></a>

**The engines, the rules and everything that draws the page.**

_Standard-library Python, every rule tested._

</div>

---

## 💡 What This Folder Is For

Every script the profile's workflows run, standard-library Python with its
tests beside it, and [`arbiter.sh`](arbiter.sh), through which the Official
Arbiter answers a move on tannergolden/play. Each game has its engine, its rules
(`*_rules.py`) and the names it gives its moves (`*_names.py`):
[`chess.py`](chess.py) plays chess, and [`games.py`](games.py) plays the other
three. The rest keep the clock and draw the page's other parts, from the Hall
of Fame to the Field Notes, and each says what it does in its docstring. How
they fit together, from a move's issue to its ruling, is in
[How The Games Run](../../docs/technical/How-The-Games-Run.md).

Run the tests with the tokens unset, as 🧪 Games Tests runs them:

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u MARKDOWN_TOKEN \
  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```

The tests reach no network: stand-ins only.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                              | Purpose                                                                                                                                                                                                                                                                                                                                                                         |
| :------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`arbiter.sh`](arbiter.sh)                         | Shellcheck shell=bash                                                                                                                                                                                                                                                                                                                                                           |
| [`checkers.py`](checkers.py)                       | Checkers on the profile, the third tier of its four games, played by games.py as chess.py plays chess.                                                                                                                                                                                                                                                                          |
| [`checkers_names.py`](checkers_names.py)           | Every legal move named as checkers players name it: an emoji, a name, and the move in plain words.                                                                                                                                                                                                                                                                              |
| [`checkers_rules.py`](checkers_rules.py)           | The rules of American checkers (English draughts): positions, legal moves, their codes, and how a game ends.                                                                                                                                                                                                                                                                    |
| [`chess.py`](chess.py)                             | The chess game on the profile: one move, or the Arbiter's after a week without one.                                                                                                                                                                                                                                                                                             |
| [`chess_names.py`](chess_names.py)                 | Every legal move named as players name it: an emoji, a name, and the move in plain English.                                                                                                                                                                                                                                                                                     |
| [`chess_rules.py`](chess_rules.py)                 | The rules of chess: positions, legal moves, their names, and how a game ends.                                                                                                                                                                                                                                                                                                   |
| [`clock.py`](clock.py)                             | The one clock for all four games on the profile: once an hour, each game's Arbiter, in a single run.                                                                                                                                                                                                                                                                            |
| [`games.py`](games.py)                             | The three games beside chess on the profile, Tic-Tac, Pentago and Checkers: one engine for all three.                                                                                                                                                                                                                                                                           |
| [`hall.py`](hall.py)                               | The Hall of Fame of all four games on the profile: each game's series, the leading winners, and the leaderboard.                                                                                                                                                                                                                                                                |
| [`issue.py`](issue.py)                             | Pick the README's good first issues: two open issues a newcomer could take this week.                                                                                                                                                                                                                                                                                           |
| [`notes.py`](notes.py)                             | Draw the README's Field Notes: five GitHub alerts, redrawn every Monday.                                                                                                                                                                                                                                                                                                        |
| [`page.py`](page.py)                               | What the profile's four games share with the page they are drawn on: its time, its days and its settings.                                                                                                                                                                                                                                                                       |
| [`pentago.py`](pentago.py)                         | Pentago on the profile, the second tier of its four games, played by games.py as chess.py plays chess.                                                                                                                                                                                                                                                                          |
| [`pentago_names.py`](pentago_names.py)             | Every empty hole named as Pentago players name it: an emoji, a name and its plain words, none of them a verdict.                                                                                                                                                                                                                                                                |
| [`pentago_rules.py`](pentago_rules.py)             | The rules of Pentago: positions, legal moves, a quarter's turn, and how a game ends.                                                                                                                                                                                                                                                                                            |
| [`placards.py`](placards.py)                       | What the placard pickers share: GitHub's API, text the kit can letter, and the settings they write.                                                                                                                                                                                                                                                                             |
| [`README.md`](README.md)                           | This file.                                                                                                                                                                                                                                                                                                                                                                      |
| [`releases.py`](releases.py)                       | Pick the README's latest releases: the two repositories on this account that shipped most recently.                                                                                                                                                                                                                                                                             |
| [`replays.py`](replays.py)                         | A finished game as its replay draws it: every turn, with what it did on the board, who played it and when.                                                                                                                                                                                                                                                                      |
| [`test_checkers.py`](test_checkers.py)             | Checkers on the profile, played offline through the shared engine, as the workflow plays it: every way a move goes.                                                                                                                                                                                                                                                             |
| [`test_checkers_names.py`](test_checkers_names.py) | Every legal move named as checkers players name it and for nothing it does: the emoji and the name by the kind of move, with no square in the name, the words from the move's own pieces and squares, and no name that judges, warns, looks ahead or names an opening, so two moves of one kind read alike whatever follows them.                                               |
| [`test_checkers_rules.py`](test_checkers_rules.py) | The rules of checkers, held to the numbers everyone checks a move generator against.                                                                                                                                                                                                                                                                                            |
| [`test_chess.py`](test_chess.py)                   | The game on the profile, played offline: whole games through the same calls the workflow makes.                                                                                                                                                                                                                                                                                 |
| [`test_chess_names.py`](test_chess_names.py)       | Every legal move named as players name it and never for what it does to the game: every name, emoji, notation and words read from a fixed grammar of the move's own facts and checked against the board, no square in any name, a move that mates or gives the queen away read just as a quiet one, and every name within what the kit takes.                                   |
| [`test_chess_rules.py`](test_chess_rules.py)       | The rules of chess, held to the numbers everyone checks a move generator against.                                                                                                                                                                                                                                                                                               |
| [`test_clock.py`](test_clock.py)                   | The one clock for all four games, run as its workflow runs it: every game ticked, saved, set out and noticed in one run, with one commit.                                                                                                                                                                                                                                       |
| [`test_games.py`](test_games.py)                   | Tic-Tac and Pentago, played offline through the same calls their workflow makes: every way a turn goes, the Ghost Rule's ghosts and the Arbiter's draws among them.                                                                                                                                                                                                             |
| [`test_hall.py`](test_hall.py)                     | The Hall of Fame of all four games: each game's series, the leading winners and the leaderboard, as the kit's `hall-of-fame` kind takes them, from every game's finished games and the game on each board, where a ghost of the Ghost Rule is a turn like any move.                                                                                                             |
| [`test_issue.py`](test_issue.py)                   | The good first issues, offline: GitHub's search answers come from fixtures.                                                                                                                                                                                                                                                                                                     |
| [`test_kit.py`](test_kit.py)                       | Every board the four games write, and the Hall of Fame of all four, held to tannergolden/markdown's own checks: the kit is the judge.                                                                                                                                                                                                                                           |
| [`test_notes.py`](test_notes.py)                   | The Field Notes: the library, the weekly draw, and every open data source, all offline.                                                                                                                                                                                                                                                                                         |
| [`test_page.py`](test_page.py)                     | What the four games share with the page: its days, and the settings' regions each run writes its elements into.                                                                                                                                                                                                                                                                 |
| [`test_pentago_names.py`](test_pentago_names.py)   | Every empty hole named as Pentago players name it and for nothing the move would do: each hole listed once, its eight turns after it, named the Centre, a Corner or an Edge of its quarter with no hole or quarter in the name, the words from the hole and its quarter, and a whole move named once it is made, its turn said in full.                                         |
| [`test_pentago_rules.py`](test_pentago_rules.py)   | The rules of Pentago, held to a second, plainer reading of them over many random games, and to positions set out by hand for every way a quarter turns and a game ends.                                                                                                                                                                                                         |
| [`test_releases.py`](test_releases.py)             | The latest releases, offline: GitHub's answers come from fixtures.                                                                                                                                                                                                                                                                                                              |
| [`test_tictac_names.py`](test_tictac_names.py)     | Every square named as tic-tac-toe players name it and for nothing the mark does: the Centre, a Corner or an Edge of its board, with no square or board in the name, the emoji by the same kind, the words from the square's place and its board's, and a square named alike whatever the game, the move or the marks round it, so a mark that wins the game reads as any other. |
| [`test_tictac_rules.py`](test_tictac_rules.py)     | The rules of Tic-Tac, Tic-Tac-Toe on nine boards at once, held to a second, plainer reading of them over many random games, and to positions set out by hand for every way a mark sends, a board closes and a game ends.                                                                                                                                                        |
| [`tictac.py`](tictac.py)                           | Tic-Tac on the profile, the first tier of its four games, played by games.py as chess.py plays chess.                                                                                                                                                                                                                                                                           |
| [`tictac_names.py`](tictac_names.py)               | Every square named as tic-tac-toe players name it: an emoji, a name and its plain words, none of them a verdict.                                                                                                                                                                                                                                                                |
| [`tictac_rules.py`](tictac_rules.py)               | The rules of Tic-Tac: positions, legal moves, where a mark sends the other side, and how a game ends.                                                                                                                                                                                                                                                                           |

<!-- AUTO-INDEX:END -->

This log is drawn from each script's docstring. Redraw this log in the same
commit as a change to this folder, from a checkout of tannergolden/standards at
`v1`:

```bash
python3 <standards>/.github/scripts/update-doc-indexes.py --tree --write
```

---

<div align="center">

**Every rule in code, every rule tested.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
